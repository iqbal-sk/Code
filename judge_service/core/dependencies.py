from redis.asyncio import Redis
from motor.motor_asyncio import AsyncIOMotorClient
from odmantic import AIOEngine
from judge_service.config.config import config


_engine: AIOEngine | None = None

def get_engine() -> AIOEngine:
    global _engine
    if _engine is None:
        client = AsyncIOMotorClient(config.MONGO_URI)
        _engine = AIOEngine(client=client, database=config.DB_NAME)
    return _engine

async def get_redis() -> Redis:
    return await Redis.from_url(config.REDIS_URL)
