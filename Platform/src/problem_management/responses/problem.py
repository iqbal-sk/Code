# File: Platform/src/problem_management/responses/problem.py
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Dict, Any, Optional

# ─── Nested DTOs for embedded models ────────────────────────────
class DescriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    markdown: str
    html: str

class ConstraintsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    time_limit_ms: int = Field(alias='timeLimit_ms')
    memory_limit_mb: int = Field(alias='memoryLimit_mb')
    input_format: str = Field(alias='inputFormat')
    output_format: str = Field(alias='outputFormat')
    p_constraints: List[str] = Field(alias='pConstraints')

class SampleTestCaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    input: str
    expected_output: str = Field(alias='expectedOutput')
    explanation: str

class StatisticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    submissions: int
    accepted: int

# ─── Summary and Detail DTOs ────────────────────────────────────
class ProblemSummaryResponse(BaseModel):
    """
    Lightweight view for listing problems.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(alias='pId')
    title: str
    slug: str
    difficulty: Optional[str]
    tags: Optional[List[str]]
    acceptance_rate: Optional[float] = Field(default=None, alias='acceptanceRate')

class ProblemDetailResponse(ProblemSummaryResponse):
    """
    Full detail view for a single problem.
    """
    description: DescriptionResponse
    constraints: ConstraintsResponse
    sample_test_cases: List[SampleTestCaseResponse] = Field(alias='sampleTestCases')
    statistics: StatisticsResponse
    assets: Optional[List[str]]
    visibility: str
