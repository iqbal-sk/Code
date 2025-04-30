# File: Platform/src/problem_management/services/problem_service.py
from typing import List, Optional, Tuple
from odmantic import AIOEngine
from odmantic.query import QueryExpression, desc
from bson import ObjectId
from fastapi import HTTPException, status

from Platform.src.problem_management.models.problem import Problem


class ProblemQueryBuilder:
    """
    Builder for accumulating query filters in an Open/Closed-friendly way.
    """
    def __init__(self):
        self._filters: List[QueryExpression] = []

    def add_difficulty(self, difficulty: Optional[str]) -> 'ProblemQueryBuilder':
        if difficulty:
            self._filters.append(Problem.difficulty == difficulty)
        return self

    def add_tags(self, tags: Optional[List[str]]) -> 'ProblemQueryBuilder':
        if tags:
            for tag in tags:
                # filter problems containing the specified tag
                self._filters.append(Problem.tags.contains(tag))

        return self

    def add_text(self, text: Optional[str]) -> 'ProblemQueryBuilder':
        if text:
            expr = (
                Problem.title.match(f'.*{text}.*', options='i') |
                Problem.description.markdown.match(f'.*{text}.*', options='i')

            )
            self._filters.append(expr)
        return self

    def build(self) -> List[QueryExpression]:
        return list(self._filters)


async def get_problem(engine: AIOEngine, problem_id: str) -> Problem:
    """
    Fetch a single Problem by its string ID, raising HTTPException on errors.
    """
    try:
        oid = ObjectId(problem_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid problem ID format"
        )

    problem = await engine.find_one(Problem, Problem.id == oid)
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )
    return problem


async def list_problems(
    engine: AIOEngine,
    page: int = 1,
    page_size: int = 10,
    difficulty: Optional[str] = None,
    tags: Optional[List[str]] = None,
    text: Optional[str] = None,
) -> Tuple[List[Problem], int]:
    """
    Return a paginated list of Problems and the total count, applying filters.
    """
    # Build query filters
    filters = (ProblemQueryBuilder()
               .add_difficulty(difficulty)
               .add_tags(tags)
               .add_text(text)
               .build())

    # Total count matching filters
    total = await engine.count(Problem, *filters)

    # Pagination parameters
    skip = (page - 1) * page_size

    # Fetch slice sorted by creation date descending
    items = await engine.find(
        Problem,
        *filters,
        sort=desc(Problem.createdAt),  # use desc from odmantic.engine
        skip=skip,
        limit=page_size
    )
    return items, total
