from pydantic import BaseModel, Field, ConfigDict, field_validator
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

class SubmissionSummary(BaseModel):
    id: str = Field(..., alias="id")
    userId: str = Field(..., alias="userId")
    problemId: str = Field(..., alias="problemId")
    pId: int
    status: str
    title: str
    createdAt: Optional[datetime]

    model_config = ConfigDict(
        validate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: lambda oid: str(oid)}
    )

    @field_validator('id', 'problemId', 'userId', mode='before')
    @classmethod
    def _convert_objectid(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        return v

