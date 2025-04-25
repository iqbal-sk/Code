from pydantic import ConfigDict
from datetime import datetime
from typing import Optional, Dict, Any
from odmantic import Model, Field, ObjectId

class TestCase(Model):
    pId: int
    problemId: ObjectId
    input: Optional[str] = None
    expectedOutput: Optional[str] = None
    isHidden: bool = False
    isLargeFile: bool = False
    fileReferences: Optional[Dict[str, Any]] = None
    createdAt: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        collection="test_cases"
    )
