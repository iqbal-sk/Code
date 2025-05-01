from typing import List, Dict, Any
import logging

from fastapi import APIRouter, Depends, Query, HTTPException
from bson import ObjectId
from bson.errors import InvalidId
from odmantic import AIOEngine

from Platform.src.core.dependencies import engine_dep
from Platform.src.problem_management.models.problem import Problem
from Platform.src.problem_management.services.testcase_service import (
    get_all_test_cases,
    get_public_test_cases,
)
from Platform.src.problem_management.responses.testcases import (
    AllTestCasesResponse,
    PublicTestCasesResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/problems/{problem_id}/test-cases",
    tags=["test-cases"],
)


async def ensure_problem_exists(problem_id: str, engine: AIOEngine):
    # 1) Validate & convert incoming ID
    try:
        oid = ObjectId(problem_id)
    except (InvalidId, TypeError):
        logger.error(f"Invalid problem ID format: {problem_id}")
        raise HTTPException(status_code=400, detail="Invalid problem ID format")

    # 2) Check database for existence
    problem = await engine.find_one(
        Problem,
        Problem.id == oid
    )
    if not problem:
        logger.warning(f"Problem not found in DB: {oid}")
        raise HTTPException(status_code=404, detail="Problem does not exist")


@router.get("", response_model=AllTestCasesResponse)
async def list_test_cases(
    problem_id: str,
    include_hidden: bool = Query(False, alias="includeHidden"),
    engine: AIOEngine = Depends(engine_dep),
) -> AllTestCasesResponse:
    await ensure_problem_exists(problem_id, engine)
    data: List[Dict[str, Any]] = await get_all_test_cases(
        problem_id, include_hidden, engine
    )
    return AllTestCasesResponse(testCases=data)


@router.get("/public", response_model=PublicTestCasesResponse)
async def list_public_test_cases(
    problem_id: str,
    engine: AIOEngine = Depends(engine_dep),
) -> PublicTestCasesResponse:
    await ensure_problem_exists(problem_id, engine)
    data: List[Dict[str, Any]] = await get_public_test_cases(problem_id, engine)
    return PublicTestCasesResponse(testCases=data)

