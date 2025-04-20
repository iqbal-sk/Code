# File: conftest.py
import os
import asyncio
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

# Set the environment to test before importing any application modules
os.environ["ENV_STATE"] = "test"

from Platform.src.main import app

from motor.motor_asyncio import AsyncIOMotorClient
from Platform.src.config.config import config


@pytest.fixture()
def anyio_backend():
    return "asyncio"

@pytest.fixture()
def client():
    yield TestClient(app)


@pytest.fixture()
async def async_client(client):
    async with AsyncClient(transport=ASGITransport(app), base_url=client.base_url) as ac:
        yield ac

@pytest.fixture(scope="function")
async def db_client():
    """
    Provides an instance of the Motor database client.
    """
    client = AsyncIOMotorClient(config.MONGODB_URI)
    yield client[config.DB_NAME]

@pytest.fixture(scope="function")
async def clear_users_collection(db_client):
    """
    Clears only the 'users' collection before and after each test.
    """
    # Clear the users collection before the test
    await db_client.users.delete_many({})
    yield
