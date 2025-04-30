import pytest
import json
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import HTTPException, status

from Platform.src.submission_management.service import (
    create_submission_service,
    subscribe_submission_events
)
from Platform.src.submission_management.requests import SubmissionCreate
from Platform.src.config.config import config

# Override the default engine_dep autouse fixture from conftest
@pytest.fixture(autouse=True)
async def override_engine_dep(db_client):
    """
    Provide a correct Odmantic AIOEngine based on the test db_client fixture.
    """
    from odmantic import AIOEngine
    test_engine = AIOEngine(
        client=AsyncIOMotorClient(config.MONGODB_URI),
        database=db_client.name,
    )
    yield test_engine

# Stub engine for create_submission_service tests
class StubEngine:
    def __init__(self, user_exists=True, problem_exists=True, problem_constraints=None):
        self.user_exists = user_exists
        self.problem_exists = problem_exists
        self.saved = None
        self._problem_constraints = problem_constraints or {"timeLimit_ms": 1000, "memoryLimit_mb": 64}

    async def find_one(self, model, condition):
        # Return None to simulate missing entity or a dummy object otherwise
        if model.__name__ == 'User':
            return None if not self.user_exists else type('UserObj', (), {})()
        if model.__name__ == 'Problem':
            if not self.problem_exists:
                return None
            # Dummy problem object with constraints attribute
            Constraints = type('C', (), self._problem_constraints)
            return type('ProblemObj', (), {'constraints': Constraints})()
        return None

    async def save(self, submission):
        # submission.id = ObjectId()
        self.saved = submission

# Stub Redis for queue push
class StubRedisQueue:
    def __init__(self):
        self.queued = None

    async def lpush(self, key, value):
        self.queued = (key, value)

# Tests for create_submission_service
@pytest.mark.anyio
async def test_create_submission_invalid_problem_format():
    payload = SubmissionCreate(problemId="invalid_id", language="python", sourceCode="print(1)")
    with pytest.raises(HTTPException) as exc:
        await create_submission_service(payload, "", StubEngine(), StubRedisQueue())
    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.anyio
async def test_create_submission_invalid_user_format():
    valid_problem = str(ObjectId())
    payload = SubmissionCreate(problemId=valid_problem, language="python", sourceCode="print(1)")
    with pytest.raises(HTTPException) as exc:
        await create_submission_service(payload, "bad_user_id", StubEngine(), StubRedisQueue())
    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.anyio
async def test_create_submission_unsupported_language():
    valid_problem = str(ObjectId())
    valid_user = str(ObjectId())
    payload = SubmissionCreate(problemId=valid_problem, language="unsupported_lang", sourceCode="print(1)")
    with pytest.raises(HTTPException) as exc:
        await create_submission_service(payload, valid_user, StubEngine(), StubRedisQueue())
    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.anyio
async def test_create_submission_user_not_found():
    valid_problem = str(ObjectId())
    valid_user = str(ObjectId())
    payload = SubmissionCreate(problemId=valid_problem, language="python", sourceCode="print(1)")
    engine = StubEngine(user_exists=False)
    with pytest.raises(HTTPException) as exc:
        await create_submission_service(payload, valid_user, engine, StubRedisQueue())
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.anyio
async def test_create_submission_problem_not_found():
    valid_problem = str(ObjectId())
    valid_user = str(ObjectId())
    payload = SubmissionCreate(problemId=valid_problem, language="python", sourceCode="print(1)")
    engine = StubEngine(problem_exists=False)
    with pytest.raises(HTTPException) as exc:
        await create_submission_service(payload, valid_user, engine, StubRedisQueue())
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.anyio
async def test_create_submission_success():
    valid_problem = str(ObjectId())
    valid_user = str(ObjectId())
    payload = SubmissionCreate(problemId=valid_problem, language="python", sourceCode="print(1)", stdin="input")
    engine = StubEngine()
    redis = StubRedisQueue()
    submission = await create_submission_service(payload, valid_user, engine, redis)
    assert engine.saved is submission
    assert redis.queued[0] == config.SUBMISSION_QUEUE_KEY
    assert submission.userId == ObjectId(valid_user)
    assert submission.problemId == ObjectId(valid_problem)
    assert submission.language == "python"
    assert submission.sourceCode == "print(1)"
    assert submission.stdin == "input"
    assert submission.status == "pending"
    assert submission.timeLimitMs == engine._problem_constraints['timeLimit_ms']
    assert submission.memoryLimitB == engine._problem_constraints['memoryLimit_mb'] * 1024 * 1024

# Stub for pubsub-based event subscription
class FakePubSub:
    def __init__(self, messages):
        self.messages = messages
        self.subscribed = False
        self.unsubscribed = False

    async def subscribe(self, channel):
        self.subscribed = True

    async def unsubscribe(self, channel):
        self.unsubscribed = True

    async def listen(self):
        for msg in self.messages:
            yield msg

class FakeRedisPubSub:
    def __init__(self, messages):
        self._messages = messages
        self.last_pubsub = None

    def pubsub(self):
        self.last_pubsub = FakePubSub(self._messages)
        return self.last_pubsub

@pytest.mark.anyio
async def test_subscribe_submission_events():
    config.TERMINAL = ['done']
    raw_msgs = [
        {"type": "message", "data": json.dumps({"status": "running"})},
        {"type": "message", "data": json.dumps({"status": "done"})}
    ]
    fake_redis = FakeRedisPubSub(raw_msgs)
    received = []
    async for update in subscribe_submission_events("sub-id", fake_redis):
        received.append(update)
    assert received == [{"status": "running"}, {"status": "done"}]
    # Ensure unsubscribe was called on the actual pubsub instance
    assert fake_redis.last_pubsub is not None and fake_redis.last_pubsub.unsubscribed
