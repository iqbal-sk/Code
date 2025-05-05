import json
from redis.asyncio import Redis
from datetime import datetime, timezone
from bson import ObjectId
from typing import AsyncGenerator, List, Tuple

from fastapi import HTTPException, status
from odmantic import AIOEngine

from Platform.src.user_management.models import User
from Platform.src.problem_management.models.problem import Problem
from Platform.src.submission_management.models.submission import Submission
from Platform.src.submission_management.requests import SubmissionCreate
from Platform.src.submission_management.responses import SubmissionSummary

from Platform.src.config.config import config

import logging

logger = logging.getLogger(__name__)


async def create_submission_service(
    payload: SubmissionCreate,
    current_user_id: str,
    engine: AIOEngine,
    redis: Redis,
) -> Submission:
    logger.info(
        "ENTER create_submission_service: user_id=%s problemId=%s language=%s",
        current_user_id, payload.problemId, payload.language
    )

    # 1. Validate ObjectId formats
    try:
        problem_obj_id = ObjectId(payload.problemId)
        logger.debug("Parsed problemId -> ObjectId: %s", problem_obj_id)
    except Exception:
        logger.warning("Invalid problemId format: %s", payload.problemId)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid problemId"
        )

    try:
        user_obj_id = ObjectId(current_user_id)
        logger.debug("Parsed current_user_id -> ObjectId: %s", user_obj_id)
    except Exception:
        logger.warning("Invalid userId format in token: %s", current_user_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid userId in token"
        )

    # 2. Validate language
    if payload.language not in config.ACCEPTED_LANGUAGES:
        logger.error("Unsupported language requested: %s", payload.language)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported language: '{payload.language}'"
        )
    logger.debug("Language validated: %s", payload.language)

    # 3. Check that the user exists
    user = await engine.find_one(User, User.id == user_obj_id)
    if not user:
        logger.error("User not found: %s", user_obj_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    logger.debug("User exists: %s", user_obj_id)

    # 4. Check that the problem exists
    problem = await engine.find_one(Problem, Problem.id == problem_obj_id)
    if not problem:
        logger.error("Problem not found: %s", problem_obj_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )
    logger.debug("Problem exists: %s", problem_obj_id)

    # 5. Build and save submission
    now = datetime.now(timezone.utc)
    sub = Submission(
        userId=user_obj_id,
        problemId=problem_obj_id,
        language=payload.language,
        sourceCode=payload.sourceCode,
        stdin=payload.stdin or "",
        status="pending",
        submittedAt=now,
        createdAt=now,
        updatedAt=now,
        canceled=False,
        timeLimitMs=problem.constraints.timeLimit_ms,
        memoryLimitB=problem.constraints.memoryLimit_mb * 1024 * 1024,
    )
    await engine.save(sub)
    logger.info("Saved submission: submissionId=%s", sub.id)

    # 6. Enqueue execution job
    job = {
        "submissionId": str(sub.id),
        "mongoId": str(sub.id),
        "problemId": payload.problemId,
        "language": sub.language,
        "sourceCode": sub.sourceCode,
        "stdin": sub.stdin or "",
    }
    await redis.lpush(config.SUBMISSION_QUEUE_KEY, json.dumps(job))
    logger.info(
        "Enqueued job to Redis [%s]: %s",
        config.SUBMISSION_QUEUE_KEY, job
    )

    logger.info("EXIT create_submission_service: submissionId=%s", sub.id)
    return sub


async def subscribe_submission_events(
    submission_id: str,
    redis: Redis
) -> AsyncGenerator[dict, None]:
    logger.info("ENTER subscribe_submission_events: submissionId=%s", submission_id)
    pubsub = redis.pubsub()
    await pubsub.subscribe(submission_id)
    logger.debug("Subscribed to channel: %s", submission_id)

    try:
        async for msg in pubsub.listen():
            if msg["type"] != "message":
                continue
            data = json.loads(msg["data"])
            logger.debug(
                "PubSub message [%s]: %s", submission_id, data
            )
            yield data
            if data.get("status") in config.TERMINAL:
                logger.info(
                    "Terminal status '%s' for %s — breaking subscription",
                    data.get("status"), submission_id
                )
                break
    except Exception as e:
        logger.error(
            "Error in subscribe_submission_events [%s]: %s",
            submission_id, e, exc_info=True
        )
        raise
    finally:
        await pubsub.unsubscribe(submission_id)
        logger.info("Unsubscribed from channel: %s", submission_id)
        logger.info("EXIT subscribe_submission_events: submissionId=%s", submission_id)


async def get_user_submissions_for_problem(
    user_id: str,
    problem_id: str,
    engine: AIOEngine,
    page: int = 1,
    limit: int = 10,
) -> Tuple[List[Submission], int]:
    logger.info(
        "ENTER get_user_submissions_for_problem: user_id=%s problem_id=%s page=%d limit=%d",
        user_id, problem_id, page, limit
    )

    # Validate IDs
    try:
        user_obj_id = ObjectId(user_id)
        problem_obj_id = ObjectId(problem_id)
        logger.debug("Parsed IDs: user=%s problem=%s", user_obj_id, problem_obj_id)
    except Exception:
        logger.error("Invalid ID format: user_id=%s problem_id=%s", user_id, problem_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID or problem ID format",
        )

    if page < 1 or limit < 1:
        logger.warning("Invalid pagination params: page=%d limit=%d", page, limit)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="`page` and `limit` must be positive integers",
        )

    filters = [
        Submission.userId == user_obj_id,
        Submission.problemId == problem_obj_id,
    ]
    logger.debug("Query filters: %s", filters)

    # 1) total count
    total = await engine.count(Submission, *filters)
    logger.info("Total submissions count: %d", total)

    # 2) paged fetch
    skip = (page - 1) * limit
    submissions = await engine.find(
        Submission,
        *filters,
        sort=Submission.submittedAt.desc(),
        skip=skip,
        limit=limit,
    )
    logger.info(
        "Fetched %d submissions (skip=%d limit=%d)", len(submissions), skip, limit
    )

    logger.info("EXIT get_user_submissions_for_problem")
    return submissions, total


async def get_user_submissions(
    user_id: str,
    engine: AIOEngine,
    page: int = 1,
    limit: int = 10,
) -> Tuple[List[Submission], int]:
    logger.info(
        "ENTER get_user_submissions: user_id=%s page=%d limit=%d",
        user_id, page, limit
    )

    # Validate IDs
    try:
        user_obj_id = ObjectId(user_id)
        logger.debug("Parsed user ID: %s", user_obj_id)
    except Exception:
        logger.error("Invalid ID format: user_id=%s", user_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format",
        )

    if page < 1 or limit < 1:
        logger.warning("Invalid pagination params: page=%d limit=%d", page, limit)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="`page` and `limit` must be positive integers",
        )

    filters = [
        Submission.userId == user_obj_id,
    ]
    logger.debug("Query filters: %s", filters)

    # 1) total count
    total = await engine.count(Submission, *filters)
    logger.info("Total submissions count: %d", total)

    # 2) paged fetch
    skip = (page - 1) * limit
    submissions = await engine.find(
        Submission,
        *filters,
        sort=Submission.submittedAt.desc(),
        skip=skip,
        limit=limit,
    )
    logger.info(
        "Fetched %d submissions (skip=%d limit=%d)", len(submissions), skip, limit
    )

    logger.info("EXIT get_user_submissions")
    return submissions, total


async def get_user_submissions_response(
    user_id: str,
    engine: AIOEngine,
    page: int = 1,
    limit: int = 10,
) -> List[SubmissionSummary]:
    """
    Fetch paginated submissions for a user and return lightweight DTOs
    including the problem's pId.
    """
    logger.info(
        "ENTER get_user_submissions_response: user_id=%s page=%d limit=%d",
        user_id, page, limit,
    )

    # 1) Delegate ID validation, pagination, and fetch to existing helper
    try:
        submissions, total = await get_user_submissions(user_id, engine, page, limit)
        logger.debug("Fetched %d submissions (total=%d)", len(submissions), total)
    except HTTPException as exc:
        logger.error(
            "Error in get_user_submissions for user_id=%s: %s",
            user_id, exc.detail,
        )
        raise

    # 2) Bulk-load Problems to grab each pId
    problem_ids = {sub.problemId for sub in submissions}
    logger.debug("Loading Problem docs for IDs: %s", problem_ids)
    problems = await engine.find(Problem, Problem.id.in_(problem_ids))
    pId_map = {prob.id: prob.pId for prob in problems}
    problem_title_map = {prob.id: prob.title for prob in problems}
    logger.debug("Built pId map: %s", pId_map)

    # 3) Construct response DTOs
    response: List[SubmissionSummary] = []
    for sub in submissions:
        p_id = pId_map.get(sub.problemId)
        if p_id is None:
            logger.warning(
                "No Problem found for submission.problemId=%s; defaulting pId=0",
                sub.problemId,
            )
            p_id = 0

        dto = SubmissionSummary(
            id=sub.id,
            userId=sub.userId,
            problemId=sub.problemId,
            pId=p_id,
            status=sub.status,
            createdAt=sub.createdAt,
            title=problem_title_map.get(sub.problemId, "Unknown Problem"),
        )
        response.append(dto)
        logger.debug("Appended SubmissionResponse for submission.id=%s", sub.id)

    logger.info(
        "EXIT get_user_submissions_response: returning %d DTOs", len(response)
    )
    return response