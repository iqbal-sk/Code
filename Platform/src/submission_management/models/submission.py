from datetime import datetime
from typing import List, Optional

from bson import ObjectId
from odmantic import Model, Field as ODMField
from pydantic import BaseModel, Field, ConfigDict


class TestDetail(BaseModel):
    test_case_id: str = Field(..., alias="testCaseId")
    verdict: str
    status: str
    stdout: str
    runtime_ms: float = Field(..., alias="runtime_ms")
    memory_bytes: int = Field(..., alias="memory_bytes")
    error_message: Optional[str] = Field(None, alias="errorMessage")

    # allow passing values by field name or by alias
    model_config = ConfigDict(populate_by_name=True)


class SubmissionResult(BaseModel):
    total_tests: int = Field(..., alias="totalTests")
    passed_tests: int = Field(..., alias="passedTests")
    max_runtime_ms: float = Field(..., alias="max_runtime_ms")
    max_memory_bytes: int = Field(..., alias="max_memory_bytes")
    test_details: List[TestDetail] = Field(..., alias="testDetails")

    model_config = ConfigDict(populate_by_name=True)


class Submission(Model):
    userId: ObjectId
    problemId: ObjectId
    language: str
    sourceCode: str
    stdin: Optional[str] = ""
    status: str = ODMField(default="pending")
    submittedAt: datetime
    completedAt: Optional[datetime] = None

    # swap out the Dict for your new model:
    result: Optional[SubmissionResult] = None

    canceled: bool = ODMField(default=False)
    createdAt: datetime
    updatedAt: datetime
    timeLimitMs: int
    memoryLimitB: int