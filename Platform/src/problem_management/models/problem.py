from datetime import datetime
from typing import List, Optional
from odmantic import Field, Model, EmbeddedModel
from pydantic import ConfigDict, field_validator, model_validator
from slugify import slugify


class Description(EmbeddedModel):
    markdown: str
    html: str


class Constraints(EmbeddedModel):
    timeLimit_ms: int
    memoryLimit_mb: int
    inputFormat: str
    outputFormat: str
    pConstraints: List[str] = Field(default_factory=list)


class SampleTestCase(EmbeddedModel):
    input: str
    expectedOutput: str
    explanation: str = ""


class Statistics(EmbeddedModel):
    submissions: int = 0
    accepted: int = 0


class Problem(Model):
    pId: int
    title: str
    slug: str = Field(default="")
    description: Description
    difficulty: Optional[str] = None
    constraints: Constraints
    sampleTestCases: List[SampleTestCase] = Field(default_factory=list)
    tags: Optional[List[str]] = None
    statistics: Statistics = Field(default_factory=Statistics)
    visibility: str = Field(default="public")
    assets: Optional[List[str]] = None
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )

    # ─── validators ─────────────────────────────
    @field_validator("slug", mode="before")
    @classmethod
    def _slug_from_title(cls, v: str | None, info):
        return v or slugify(info.data.get("title", ""))

    @model_validator(mode="before")
    def _touch_updated(cls, values):
        values["updatedAt"] = datetime.utcnow()
        return values

    # derived metric
    @property
    def acceptanceRate(self) -> float:
        s = self.statistics
        return 0.0 if s.submissions == 0 else s.accepted / s.submissions * 100
