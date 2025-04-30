from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from bson import ObjectId

from Platform.src.submission_management.models import SubmissionResult  # adjust this import to your package structure

class SubmissionResponse(BaseModel):
    submissionId: str = Field(..., alias="id")
    userId: str
    problemId: str
    language: str
    sourceCode: str
    stdin: Optional[str]
    status: str
    submittedAt: datetime
    completedAt: Optional[datetime]
    result: Optional[SubmissionResult]
    canceled: bool
    createdAt: datetime
    updatedAt: datetime

    model_config = ConfigDict(
        validate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: lambda oid: str(oid)}
    )


class SubmissionResponseList(BaseModel):
    submissions: List[SubmissionResponse]
    total: int
    page: int
    limit: int

    model_config = ConfigDict(
        validate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: lambda oid: str(oid)}
    )

