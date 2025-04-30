from pydantic import BaseModel, ConfigDict
from typing import List
from Platform.src.problem_management.responses.problem import ProblemSummaryResponse


class ProblemListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    total: int
    page: int
    page_size: int
    items: List[ProblemSummaryResponse]