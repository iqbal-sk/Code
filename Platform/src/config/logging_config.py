from logging.config import dictConfig
from Platform.src.config.config import config
from Platform.src.config.config import DevConfig

handlers = ["default", "rotating_file"]
if config.ENV_STATE == "prod":
    handlers = ["default", "rotating_file"]

def configure_logging() -> None:
    dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "correlation_id": {
                "()": "asgi_correlation_id.CorrelationIdFilter",
                "uuid_length": 16 if isinstance(config, DevConfig) else 32,
                "default_value": "-",
            },
        },
        "formatters": {
            "console": {
                "class": "logging.Formatter",
                "datefmt": "%Y-%m-%dT%H:%M:%S",
                "format": "%(asctime)s %(levelname)s (%(correlation_id)s) %(name)s:%(lineno)d - %(message)s",
            },
            "file": {
                "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "datefmt": "%Y-%m-%dT%H:%M:%S",
                "format": "%(asctime)s %(msecs)03d %(levelname)s %(correlation_id)s %(name)s %(lineno)d %(message)s",
            },
        },
        "handlers": {
            "default": {
                "class": "logging.StreamHandler",  # Alternatively use logging.StreamHandler
                "level": "DEBUG",
                "formatter": "console",
                "filters": ["correlation_id"],
            },
            "rotating_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "file",
                "filters": ["correlation_id"],
                "filename": "main-app.log",
                "maxBytes": 1024 * 1024,  # 1 MB
                "backupCount": 2,
                "encoding": "utf8",
            },
        },
        "loggers": {
            "uvicorn": {"handlers": ["default", "rotating_file"], "level": "INFO"},
            "Platform": {
                "handlers": handlers,
                "level": "DEBUG" if isinstance(config, DevConfig) else "INFO",
                "propagate": False,
            },
        },
    })
