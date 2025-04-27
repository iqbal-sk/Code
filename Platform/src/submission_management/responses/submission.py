from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime
from typing import Dict, Any, List
from bson import ObjectId

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
    result: Optional[Dict[str, Any]]
    canceled: bool
    createdAt: datetime
    updatedAt: datetime

    model_config = ConfigDict(validate_by_name=True,
                              arbitrary_types_allowed=True,
                              json_encoders={ObjectId: lambda oid: str(oid)})


class SubmissionResponseList(BaseModel):
    submissions: List[SubmissionResponse]
    total: int
    page: int
    limit: int

    model_config = ConfigDict(validate_by_name=True,
                              arbitrary_types_allowed=True,
                              json_encoders={ObjectId: lambda oid: str(oid)})
