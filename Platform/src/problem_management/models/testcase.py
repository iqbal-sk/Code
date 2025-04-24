from pydantic import ConfigDict
from datetime import datetime
from typing import Optional
from bson import ObjectId
from odmantic import Model, Field, EmbeddedModel

class FileReferences(EmbeddedModel):
    inputFileId: ObjectId
    outputFileId: ObjectId

    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )

class TestCase(Model):
    pId: str
    input: Optional[str] = None
    expectedOutput: Optional[str] = None
    isHidden: bool = False
    isLargeFile: bool = False
    fileReferences: Optional[FileReferences] = None
    createdAt: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        collection="test_cases"
    )
