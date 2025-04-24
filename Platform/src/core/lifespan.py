from contextlib import asynccontextmanager
from Platform.src.core.dependencies import get_motor_client, get_engine
from Platform.src.config.logging_config import configure_logging

@asynccontextmanager
async def lifespan(app):
    configure_logging()
    get_motor_client()
    get_engine()

    yield

    get_motor_client().close()
