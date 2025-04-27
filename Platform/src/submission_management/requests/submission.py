from pydantic import BaseModel, Field
from bson import ObjectId
from typing import Optional

class SubmissionCreate(BaseModel):
    problemId: str = Field(..., description="MongoDB ObjectId as hex string")
    language: str
    sourceCode: str
    stdin: Optional[str] = ""