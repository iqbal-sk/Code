import json
import time
import logging

from fastapi import APIRouter, Depends, status, Query
from odmantic import AIOEngine
from redis.asyncio import Redis
from typing import List
from sse_starlette.sse import EventSourceResponse

from Platform.src.core.dependencies import engine_dep, get_redis
from Platform.src.auth.dependencies import get_current_user
from Platform.src.submission_management.requests import SubmissionCreate
from Platform.src.submission_management.responses import (
    SubmissionResponse,
    SubmissionResponseList,
)
from Platform.src.submission_management.service import (
    create_submission_service,
    subscribe_submission_events,
    get_user_submissions_for_problem,
)

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/api/v1/submissions",
    tags=["submissions"]
)


@router.post(
    "",
    response_model=SubmissionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue a new code submission"
)
async def create_submission(
    payload: SubmissionCreate,
    current_user=Depends(get_current_user),
    engine: AIOEngine = Depends(engine_dep),
    redis: Redis = Depends(get_redis)
):
    logger.info(
        "START create_submission – user=%s problem=%s language=%s",
        current_user.id, payload.problemId, payload.language
    )
    start_ts = time.monotonic()

    # validate minimal payload
    if not payload.sourceCode.strip():
        logger.warning("Empty sourceCode received from user=%s", current_user.id)

    try:
        sub = await create_submission_service(
            payload, current_user.id, engine, redis
        )
        elapsed = time.monotonic() - start_ts
        logger.info(
            "ENQUEUED submission – id=%s user=%s duration=%.3fs",
            sub.id, sub.userId, elapsed
        )
    except Exception as e:
        elapsed = time.monotonic() - start_ts
        logger.error(
            "ERROR enqueue submission – user=%s problem=%s duration=%.3fs exception=%s",
            current_user.id, payload.problemId, elapsed, e, exc_info=True
        )
        raise

    response = SubmissionResponse(
        submissionId=str(sub.id),
        userId=str(sub.userId),
        problemId=str(sub.problemId),
        language=sub.language,
        sourceCode=sub.sourceCode,
        stdin=sub.stdin,
        status=sub.status,
        submittedAt=sub.submittedAt,
        completedAt=sub.completedAt,
        result=sub.result,
        canceled=sub.canceled,
        createdAt=sub.createdAt,
        updatedAt=sub.updatedAt
    )
    logger.debug("Prepared response payload: %r", response)
    logger.info("END create_submission – submissionId=%s", response.submissionId)
    return response


@router.get(
    "/{submission_id}/events",
    summary="Stream live status updates for a submission"
)
async def submission_events(
    submission_id: str,
    redis=Depends(get_redis)
):
    logger.info("Client CONNECTED to SSE – submissionId=%s", submission_id)
    start_ts = time.monotonic()

    async def event_generator():
        try:
            async for update in subscribe_submission_events(submission_id, redis):
                logger.debug(
                    "SSE UPDATE – submissionId=%s update=%s",
                    submission_id, update
                )
                yield {
                    "event": "status",
                    "data": json.dumps(update)
                }
        except Exception as e:
            logger.error(
                "SSE ERROR – submissionId=%s exception=%s",
                submission_id, e, exc_info=True
            )
        finally:
            elapsed = time.monotonic() - start_ts
            logger.info(
                "Client DISCONNECTED from SSE – submissionId=%s duration=%.3fs",
                submission_id, elapsed
            )

    return EventSourceResponse(event_generator())


@router.get(
    "/problems/{problem_id}",
    response_model=SubmissionResponseList,
    summary="List your submissions for a specific problem (paginated)",
)
async def list_my_submissions_for_problem(
    problem_id: str,
    page: int = Query(1, ge=1, description="Page number, starting from 1"),
    limit: int = Query(5, ge=1, le=100, description="Items per page"),
    current_user=Depends(get_current_user),
    engine: AIOEngine = Depends(engine_dep),
):
    logger.info(
        "START list_submissions – user=%s problem=%s page=%d limit=%d",
        current_user.id, problem_id, page, limit
    )
    start_ts = time.monotonic()

    docs, total = await get_user_submissions_for_problem(
        user_id=current_user.id,
        problem_id=problem_id,
        engine=engine,
        page=page,
        limit=limit,
    )

    if not docs:
        logger.warning(
            "No submissions found – user=%s problem=%s",
            current_user.id, problem_id
        )

    subs_payload = []
    for sub in docs:
        d = sub.model_dump(by_alias=True)
        d["id"] = str(sub.id)
        d["userId"] = str(sub.userId)
        d["problemId"] = str(sub.problemId)
        subs_payload.append(d)
    elapsed = time.monotonic() - start_ts
    logger.info(
        "Fetched %d submissions out of %d – duration=%.3fs",
        len(subs_payload), total, elapsed
    )

    response = SubmissionResponseList(
        submissions=subs_payload,
        total=total,
        page=page,
        limit=limit,
    )
    logger.debug("Response body: %r", response)
    logger.info("END list_submissions – user=%s", current_user.id)
    return response
