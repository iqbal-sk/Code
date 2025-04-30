import os
import logging
import logging.config
import sys
import uuid
import contextvars

from logging.config import dictConfig
from judge_service.config.config import config

if not config.LOG_DIR or not isinstance(config.LOG_DIR, str) or not config.LOG_DIR.strip():
    config.LOG_DIR = os.path.join(os.getcwd(), "logs")  # Default to a "logs" directory in the current working directory
    print(f"Warning: 'config.LOG_DIR' is not set or invalid. Using default: {config.LOG_DIR}", file=sys.stderr)
os.makedirs(config.LOG_DIR, exist_ok=True)

# Context variable to hold a request/job ID
request_id_ctx_var = contextvars.ContextVar('request_id', default='-')


class RequestIdFilter(logging.Filter):
    """
    Injects a unique request_id into log records, pulled from the context variable.
    """
    def filter(self, record):
        record.request_id = request_id_ctx_var.get()
        return True


def configure_logging() -> None:
    """
    Configure logging with a console and rotating file handler, each including a request_id.
    """
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'filters': {
            'request_id': {
                '()': RequestIdFilter,
            },
        },
        'formatters': {
            'default': {
                'format': '[%(asctime)s] [%(levelname)s] [%(name)s] [req_id=%(request_id)s] %(message)s',
                'datefmt': '%Y-%m-%dT%H:%M:%S%z',
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'default',
                'filters': ['request_id'],
                'stream': sys.stdout,
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'default',
                'filters': ['request_id'],
                'filename': config.LOG_FILE_PATH,
                'maxBytes': 10 * 1024 * 1024,
                'backupCount': 5,
                'encoding': 'utf8',
            },
        },
        'root': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if getattr(config, 'ENV_STATE', None) == 'dev' else 'INFO',
        },
    }
    dictConfig(LOGGING)


def set_request_id(req_id: str = None) -> None:
    """
    Helper to set the current request/job ID for logging context.
    If not provided, generates a new UUID4 hex.
    """
    if req_id is None:
        req_id = uuid.uuid4().hex
    request_id_ctx_var.set(req_id)
