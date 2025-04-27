from datetime import datetime
from pydantic import ConfigDict
from odmantic import Model, Field as ODMField
from typing import Optional, Dict, Any
from bson import ObjectId

class Submission(Model):
    userId: ObjectId
    problemId: ObjectId
    language: str
    sourceCode: str
    stdin: Optional[str] = ""
    status: str = ODMField(default="pending")
    submittedAt: datetime
    completedAt: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    canceled: bool = ODMField(default=False)
    createdAt: datetime
    updatedAt: datetime
    timeLimitMs: int
    memoryLimitB: int

    model_config = ConfigDict(collection="submissions")