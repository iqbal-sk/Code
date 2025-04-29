import pytest
from httpx import AsyncClient

@pytest.fixture()
async def user_payload():
    """
    Returns a standard user registration payload.
    """
    return {
        "username": "testuser",
        "email": "testuser@example.com",
        "firstName": "Test",
        "lastName": "User",
        "password": "secretpassword"
    }

@pytest.fixture()
async def register_user(async_client, user_payload, clear_users_collection):
    """
    Registers a user using the registration endpoint and returns the resulting
    user document.
    """
    response = await async_client.post("/users/register", json=user_payload)
    # Ensure the registration was successful.
    assert response.status_code == 200
    return response.json()

@pytest.mark.anyio
async def test_register_user(async_client: AsyncClient, clear_users_collection, user_payload):
    # A fresh "users" collection is ensured by clear_users_collection
    response = await async_client.post("/users/register", json=user_payload)
    assert response.status_code == 200
    data = response.json()
    # Verify that an _id is generated and fields match the user_payload
    assert "_id" in data
    assert data["username"] == user_payload["username"]

@pytest.mark.anyio
async def test_register_duplicate_user(async_client: AsyncClient, clear_users_collection, user_payload):
    # The first registration should succeed.
    response1 = await async_client.post("/users/register", json=user_payload)
    assert response1.status_code == 200

    # A second registration using the same payload should trigger a duplicate error.
    response2 = await async_client.post("/users/register", json=user_payload)
    assert response2.status_code == 400
    error_data = response2.json()
    assert "detail" in error_data

@pytest.mark.anyio
async def test_register_incomplete_data(async_client: AsyncClient, clear_users_collection):
    # Testing registration with missing required data (e.g., missing "password")
    incomplete_data = {
        "username": "incompleteuser",
        "email": "incomplete@example.com",
        "firstName": "Incomplete",
        "lastName": "User"
        # "password" field is intentionally missing.
    }
    response = await async_client.post("/users/register", json=incomplete_data)
    # Expect a 422 status code since Pydantic validation should catch the missing field.
    assert response.status_code == 422

@pytest.mark.anyio
async def test_login_success(async_client: AsyncClient, register_user, user_payload):
    # The register_user fixture registers the user before login.
    login_data = {
        "username": user_payload["username"],
        "password": user_payload["password"]
    }
    login_response = await async_client.post("/users/login", json=login_data)
    assert login_response.status_code == 200
    token_data = login_response.json()
    # Validate the token structure
    assert "access_token" in token_data
    assert token_data.get("token_type") == "bearer"

@pytest.mark.anyio
async def test_login_wrong_password(async_client: AsyncClient, clear_users_collection, user_payload):
    # First, register the user.
    response = await async_client.post("/users/register", json=user_payload)
    assert response.status_code == 200

    # Attempt login with an incorrect password.
    login_data = {
        "username": user_payload["username"],
        "password": "wrongpassword"
    }
    login_response = await async_client.post("/users/login", json=login_data)
    assert login_response.status_code == 401
    error_data = login_response.json()
    assert "detail" in error_data

@pytest.mark.anyio
async def test_login_user_not_found(async_client: AsyncClient, clear_users_collection):
    # Attempt login for a user that is not registered.
    login_data = {
        "username": "nonexistentuser",
        "password": "irrelevant"
    }
    login_response = await async_client.post("/users/login", json=login_data)
    assert login_response.status_code == 404
    error_data = login_response.json()
    assert "detail" in error_data