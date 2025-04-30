# File: Platform/src/problem_management/services/testcase_service.py

from typing import List, Dict, Any, Optional
from bson import ObjectId
from odmantic import AIOEngine

from Platform.src.problem_management.models.testcase import TestCase as TestCaseDoc
from Platform.src.problem_management.models.asset import Asset as AssetDoc


async def fetch_testcase_docs(
        problem_id: str,
        include_hidden: bool,
        engine: AIOEngine
) -> List[TestCaseDoc]:
    """
    Retrieve all TestCaseDoc instances for a given problem_id.
    Honors include_hidden to filter out hidden cases.
    """
    # convert to ObjectId and filter on the renamed field
    oid = ObjectId(problem_id)
    filters = [TestCaseDoc.problemId == oid]
    if not include_hidden:
        filters.append(TestCaseDoc.isHidden == False)
    return await engine.find(TestCaseDoc, *filters)


async def serialize_test_case(
        tc: TestCaseDoc,
        engine: AIOEngine
) -> Dict[str, Any]:
    """
    Build a dict representation of one TestCase:
      - If tc.fileReferences is None → inline small payload
      - If tc.fileReferences is a dict → fetch assets by ID
    """
    result: Dict[str, Any] = {
        "caseId": str(tc.id),
        "isHidden": tc.isHidden,
    }

    if tc.fileReferences:
        fr = tc.fileReferences  # type: Dict[str, Any]
        input_id = fr.get("inputFileId")
        output_id = fr.get("outputFileId")

        inp: Optional[AssetDoc] = await engine.find_one(
            AssetDoc, AssetDoc.id == ObjectId(input_id)  # type: ignore
        ) if input_id else None

        out: Optional[AssetDoc] = await engine.find_one(
            AssetDoc, AssetDoc.id == ObjectId(output_id)  # type: ignore
        ) if output_id else None

        result.update({
            "isRemote": True,
            "inputPath": inp.filePath if inp else None,
            "outputPath": out.filePath if out else None,
        })
    else:
        result.update({
            "isRemote": False,
            "input": tc.input,
            "expectedOutput": tc.expectedOutput,
        })

    return result


async def get_all_test_cases(
        problem_id: str,
        include_hidden: bool,
        engine: AIOEngine
) -> List[Dict[str, Any]]:
    raw_docs = await fetch_testcase_docs(problem_id, include_hidden, engine)
    return [await serialize_test_case(tc, engine) for tc in raw_docs]


async def get_public_test_cases(
        problem_id: str,
        engine: AIOEngine
) -> List[Dict[str, Any]]:
    serialized = await get_all_test_cases(problem_id, False, engine)
    for item in serialized:
        item.pop("isHidden", None)
    return serialized
