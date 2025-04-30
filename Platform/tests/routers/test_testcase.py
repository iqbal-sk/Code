import pytest
from httpx import AsyncClient
from fastapi import HTTPException

import Platform.src.problem_management.router.testcasesrouter as tc_router


@pytest.mark.anyio
async def test_list_test_cases_happy_path(async_client: AsyncClient, monkeypatch):
    problem_id = "abcdefabcdefabcdefabcdef"
    fake_payload = [
        {
            "caseId": "tc1",
            "isHidden": False,
            "isRemote": False,
            "input": "1 2\n",
            "expectedOutput": "3\n"
        }
    ]
    calls = {}

    async def fake_ensure(pid, engine):
        calls["ensure"] = pid

    async def fake_get_all(pid, include_hidden, engine):
        calls["get_all"] = (pid, include_hidden)
        return fake_payload

    monkeypatch.setattr(tc_router, "ensure_problem_exists", fake_ensure)
    monkeypatch.setattr(tc_router, "get_all_test_cases", fake_get_all)

    # includeHidden defaults to false, here we override it to true
    response = await async_client.get(
        f"/api/problems/{problem_id}/test-cases?includeHidden=true"
    )
    assert response.status_code == 200
    assert calls["ensure"] == problem_id
    assert calls["get_all"] == (problem_id, True)

    body = response.json()["testCases"]
    assert isinstance(body, list) and len(body) == 1
    assert body[0]["caseId"] == "tc1"
    assert body[0]["input"] == "1 2\n"


@pytest.mark.anyio
async def test_list_test_cases_invalid_id(async_client: AsyncClient):
    # invalid ObjectId → 400
    response = await async_client.get("/api/problems/not-an-id/test-cases")
    assert response.status_code == 400
    assert "Invalid problem ID format" in response.json()["detail"]


@pytest.mark.anyio
async def test_list_test_cases_not_found(async_client: AsyncClient, monkeypatch):
    problem_id = "abcdefabcdefabcdefabcdef"

    async def fake_ensure(pid, engine):
        raise HTTPException(status_code=404, detail="Problem does not exist")

    monkeypatch.setattr(tc_router, "ensure_problem_exists", fake_ensure)

    response = await async_client.get(f"/api/problems/{problem_id}/test-cases")
    assert response.status_code == 404
    assert response.json()["detail"] == "Problem does not exist"


@pytest.mark.anyio
async def test_list_public_test_cases_happy_path(async_client: AsyncClient, monkeypatch):
    problem_id = "abcdefabcdefabcdefabcde"
    fake_public = [
        {"caseId": "pub1", "isRemote": True, "inputPath": "/in/1", "outputPath": "/out/1"},
    ]
    calls = {}

    async def fake_ensure(pid, engine):
        calls["ensure_pub"] = pid

    async def fake_pub(pid, engine):
        calls["get_pub"] = pid
        return fake_public

    monkeypatch.setattr(tc_router, "ensure_problem_exists", fake_ensure)
    monkeypatch.setattr(tc_router, "get_public_test_cases", fake_pub)

    response = await async_client.get(f"/api/problems/{problem_id}/test-cases/public")
    assert response.status_code == 200
    assert calls["ensure_pub"] == problem_id
    assert calls["get_pub"] == problem_id

    body = response.json()["testCases"]
    assert isinstance(body, list) and len(body) == 1
    assert body[0]["caseId"] == "pub1"
    assert body[0]["inputPath"] == "/in/1"


@pytest.mark.anyio
async def test_list_public_test_cases_invalid_id(async_client: AsyncClient):
    response = await async_client.get("/api/problems/bad-id/test-cases/public")
    assert response.status_code == 400
    assert "Invalid problem ID format" in response.json()["detail"]


@pytest.mark.anyio
async def test_list_public_test_cases_not_found(async_client: AsyncClient, monkeypatch):
    problem_id = "vghj"
    async def fake_ensure(pid, engine):
        raise HTTPException(status_code=404, detail="Problem does not exist")

    monkeypatch.setattr(tc_router, "ensure_problem_exists", fake_ensure)

    response = await async_client.get(f"/api/problems/{problem_id}/test-cases/public")
    assert response.status_code == 404
    assert response.json()["detail"] == "Problem does not exist"
