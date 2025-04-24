from odmantic import AIOEngine
from motor.motor_asyncio import AsyncIOMotorClient
from Platform.src.config.config import config

_client: AsyncIOMotorClient | None = None
_engine: AIOEngine | None = None

def get_motor_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(config.MONGODB_URI)
    return _client

def get_engine() -> AIOEngine:
    global _engine
    if _engine is None:
        _engine = AIOEngine(client=get_motor_client(), database=config.DB_NAME)
    return _engine

# For FastAPI
def engine_dep() -> AIOEngine:
    return get_engine()
