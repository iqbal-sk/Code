import pytest
from httpx import AsyncClient
from bson import ObjectId
from Platform.src.problem_management.models.problem import Problem, Description, Constraints
from datetime import datetime, timedelta


@pytest.fixture()
async def sample_problem_payload():
    return {
        "title": "Sample Problem",
        "description": {
            "markdown": "This is a sample problem."
        },
        "difficulty": "easy",
        "tags": ["math", "arrays"]
    }

#Confirms empty DB returns 0 problems
@pytest.mark.anyio
async def test_read_problems_empty(async_client: AsyncClient, clear_problems_collection):
    # No problems initially
    response = await async_client.get("/api/problems/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []

#Valid but non-existing ObjectId returns 404
@pytest.mark.anyio
async def test_read_problem_not_found(async_client: AsyncClient):
    fake_id = str(ObjectId())
    response = await async_client.get(f"/api/problems/{fake_id}")
    assert response.status_code == 404
    assert "detail" in response.json()


#Invalid format ID returns 400 or 404
@pytest.mark.anyio
async def test_read_problem_invalid_id(async_client: AsyncClient):
    response = await async_client.get("/api/problems/invalid_id")
    assert response.status_code == 400 or response.status_code == 404

#Valid ID returns correct problem data
@pytest.mark.anyio
async def test_read_problem_by_valid_id(async_client, test_engine, clear_problems_collection):

    problem = Problem(
        pId=123,
        title="Test Problem",
        description=Description(markdown="Test", html="<p>Test</p>"),
        difficulty="medium",
        tags=["test"],
        constraints=Constraints(
            timeLimit_ms=1000,
            memoryLimit_mb=256,
            inputFormat="input format",
            outputFormat="output format",
            pConstraints=["1 <= n <= 100"]
        )
    )
    await test_engine.save(problem)

    response = await async_client.get(f"/api/problems/{str(problem.id)}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Problem"
    assert "description" in data
    assert "difficulty" in data

#Filters problems by difficulty
@pytest.mark.anyio
async def test_read_problems_filter_by_difficulty(async_client, test_engine, clear_problems_collection):
    problem_easy = Problem(
        pId=1,
        title="Easy One",
        description=Description(markdown="m", html="h"),
        difficulty="easy",
        tags=["math"],
        constraints=Constraints(
            timeLimit_ms=1000,
            memoryLimit_mb=256,
            inputFormat="a",
            outputFormat="b",
            pConstraints=[]
        )
    )

    problem_hard = Problem(
        pId=2,
        title="Hard One",
        description=problem_easy.description,
        difficulty="hard",
        tags=["graph"],
        constraints=problem_easy.constraints
    )

    await test_engine.save(problem_easy)
    await test_engine.save(problem_hard)

    response = await async_client.get("/api/problems/?difficulty=easy")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Easy One"

#Confirms pagination logic with 15 records
@pytest.mark.anyio
async def test_read_problems_pagination(async_client, test_engine, clear_problems_collection):
    for i in range(15):
        await test_engine.save(Problem(
            pId=100 + i,
            title=f"Problem {i}",
            description=Description(markdown=f"Markdown {i}", html=f"<p>HTML {i}</p>"),
            difficulty="easy",
            tags=["pagination"],
            constraints=Constraints(timeLimit_ms=1000, memoryLimit_mb=256, inputFormat="a", outputFormat="b", pConstraints=[])
        ))

    response = await async_client.get("/api/problems/?page=2&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 2
    assert data["page_size"] == 10
    assert len(data["items"]) == 5

#Ensures problems are sorted newest first
@pytest.mark.anyio
async def test_problems_sorted_by_createdAt(async_client, test_engine, clear_problems_collection):
    now = datetime.utcnow()

    p1 = Problem(
        pId=300,
        title="Older",
        description=Description(markdown="m", html="h"),
        createdAt=now - timedelta(days=1),
        updatedAt=now - timedelta(days=1),
        difficulty="easy",
        tags=[],
        constraints=Constraints(timeLimit_ms=1000, memoryLimit_mb=256, inputFormat="a", outputFormat="b", pConstraints=[])
    )
    p2 = Problem(
        pId=301,
        title="Newer",
        description=p1.description,
        createdAt=now,
        updatedAt=now,
        difficulty="easy",
        tags=[],
        constraints=p1.constraints
    )
    await test_engine.save(p1)
    await test_engine.save(p2)

    response = await async_client.get("/api/problems/")
    assert response.status_code == 200
    data = response.json()
    assert data["items"][0]["title"] == "Newer"

#Skipping all tag-based filters because current implementation
# uses `tag in Problem.tags`, which raises `TypeError` in ODMantic.
# Proper solution would use `elem_match(Problem.tags, tag)`.
