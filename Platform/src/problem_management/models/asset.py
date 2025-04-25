import datetime
from typing import Optional
from pydantic import ConfigDict
from odmantic import Model, Field, ObjectId
class Asset(Model):
    problemId: ObjectId
    filename: str
    contentType: str
    size: int
    isS3: bool
    filePath: str
    s3Key: Optional[str]
    pId: Optional[int]
    purpose: str
    isPublic: bool
    uploadedAt: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

    model_config = ConfigDict(collection="assets", arbitrary_types_allowed=True)
