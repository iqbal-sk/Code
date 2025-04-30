import os
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from odmantic import AIOEngine
os.environ["ENV_STATE"] = "test"

from Platform.src.main import app
from Platform.src.config.config import config
from motor.motor_asyncio import AsyncIOMotorClient

from Platform.src.core.dependencies import engine_dep
from Platform.src.problem_management.models.problem import Problem

@pytest.fixture(autouse=True)
def override_engine_dep(db_client):
    """
    Override engine_dep so FastAPI uses our test MongoDB engine
    rather than the real one.
    """
    from odmantic import AIOEngine

    # Build a test engine from the raw Motor client/DB you already provide
    test_engine = AIOEngine(
        client=AsyncIOMotorClient(config.MONGODB_URI),
        database=db_client.name,
    )

    async def _fake_engine_dep():
        return test_engine

    # Tell FastAPI to use _fake_engine_dep whenever engine_dep is requested
    app.dependency_overrides[engine_dep] = _fake_engine_dep
    yield _fake_engine_dep
    app.dependency_overrides.clear()


@pytest.fixture()
def client():
    # Now that the override is in place, instantiating TestClient will
    # pick it up in the lifespan hook and in the route deps.
    yield TestClient(app)


@pytest.fixture()
async def async_client(client):
    async with AsyncClient(
        transport=ASGITransport(app), base_url=client.base_url
    ) as ac:
        yield ac


@pytest.fixture()
def anyio_backend():
    return "asyncio"

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

@pytest.fixture
async def clear_problems_collection(override_engine_dep):
    """
    Clears the 'problems' collection before and after each test using the overridden engine.
    """
    # Grab the engine that override_engine_dep installs
    engine: AIOEngine = await override_engine_dep()

    await engine.remove(Problem)
    yield
    await engine.remove(Problem)

@pytest.fixture(scope="function")
async def test_engine(override_engine_dep):
    return await override_engine_dep()