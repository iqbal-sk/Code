from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


class TestCase(BaseModel):
    case_id: str = Field(..., alias="caseId")
    is_remote: bool = Field(..., alias="isRemote")
    is_hidden: bool = Field(..., alias="isHidden")
    input_path: Optional[str] = Field(None, alias="inputPath")
    output_path: Optional[str] = Field(None, alias="outputPath")
    test_input: Optional[str] = Field(None, alias='input')
    expected_output: Optional[str] = Field(None, alias='expectedOutput')


    model_config = ConfigDict(
        populate_by_name=True
    )


class AllTestCasesResponse(BaseModel):
    test_cases: List[TestCase] = Field(..., alias="testCases")

    model_config = ConfigDict(
        populate_by_name=True
    )


class PublicTestCase(BaseModel):
    case_id: str = Field(..., alias="caseId")
    is_remote: bool = Field(..., alias="isRemote")
    input_path: Optional[str] = Field(None, alias="inputPath")
    output_path: Optional[str] = Field(None, alias="outputPath")

    model_config = ConfigDict(
        populate_by_name=True
    )


class PublicTestCasesResponse(BaseModel):
    test_cases: List[PublicTestCase] = Field(..., alias="testCases")

    model_config = ConfigDict(
        populate_by_name=True
    )

