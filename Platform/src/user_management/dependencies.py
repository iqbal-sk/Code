from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from odmantic import AIOEngine
from Platform.src.config.config import config

def create_motor_client() -> AsyncIOMotorClient:
    """Create a new Motor client instance."""
    return AsyncIOMotorClient(config.MONGODB_URI)

def get_db(client: AsyncIOMotorClient) -> AsyncIOMotorDatabase:
    """Get the database instance from the provided client."""
    return client[config.DB_NAME]

def create_engine(client: AsyncIOMotorClient) -> AIOEngine:
    """Create a new ODMantic engine instance using the new client."""
    return AIOEngine(client=client, database=config.DB_NAME)

def get_users_collection(db: AsyncIOMotorDatabase) -> AsyncIOMotorCollection:
    """Return the 'users' collection from the provided database."""
    return db.users
