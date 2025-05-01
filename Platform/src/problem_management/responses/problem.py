# File: Platform/src/problem_management/responses/problem.py
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import List, Dict, Any, Optional
from bson import ObjectId

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
    model_config = ConfigDict(from_attributes=True,
                              arbitrary_types_allowed=True,
                              json_encoders={ObjectId: lambda oid: str(oid)},
                              )
    id: str = Field(alias='id')
    pId: int = Field(alias='pId')
    title: str
    slug: str
    difficulty: Optional[str]
    tags: Optional[List[str]]
    acceptance_rate: Optional[float] = Field(default=None, alias='acceptanceRate')

    @field_validator('id', mode='before')
    @classmethod
    def _convert_objectid(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        return v

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

    model_config = ConfigDict(from_attributes=True,
                              arbitrary_types_allowed=True
                              )

    @field_validator('id', mode='before')
    @classmethod
    def _convert_objectid_id(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        return v

    @field_validator('assets', mode='before')
    @classmethod
    def _convert_objectid_assets(cls, v):
        if isinstance(v, list) and all(isinstance(i, ObjectId) for i in v):
            a = [ str(i) for i in v]
            return [ str(i) for i in v]
        return v