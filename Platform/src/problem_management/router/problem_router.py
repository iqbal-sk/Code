# File: Platform/src/problem_management/router.py
from typing import List, Optional, Any
from fastapi import APIRouter, Depends, Query
from odmantic import AIOEngine

from Platform.src.core.dependencies import engine_dep
from Platform.src.problem_management.services.problem_service import list_problems, get_problem
from Platform.src.problem_management.responses.problem import ProblemDetailResponse
from Platform.src.problem_management.responses.problem_list import ProblemListResponse

router = APIRouter(
    prefix="/api/v1/problems",
    tags=["problems"],
)

@router.get("/", response_model=ProblemListResponse)
async def read_problems(
    page: int = Query(1, ge=1, description="Page number, starting from 1"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty level"),
    tags: Optional[List[str]] = Query(None, description="Filter by tag(s)"),
    text: Optional[str] = Query(None, description="Text search on title and description"),
    engine: AIOEngine = Depends(engine_dep),
) -> Any:
    """
    List problems with optional filters and pagination.
    """
    items, total = await list_problems(
        engine,
        page=page,
        page_size=page_size,
        difficulty=difficulty,
        tags=tags,
        text=text,
    )

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items,
    }

@router.get("/{problem_id}", response_model=ProblemDetailResponse)
async def read_problem(
    problem_id: str,
    engine: AIOEngine = Depends(engine_dep),
) -> Any:
    """
    Retrieve a single problem by its ID.
    """
    problem = await get_problem(engine, problem_id)
    return problem
