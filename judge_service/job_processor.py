import json
from datetime import datetime, timezone
from typing import Any, Dict, List
import httpx
from bson import ObjectId
from odmantic import AIOEngine
from fastapi import HTTPException, status

from judge_service.config.config import config
from judge_service.testcase_client import fetch_testcases
from judge_service.sandbox import run_in_sandbox
from redis.asyncio import Redis
from Platform.src.submission_management.models import Submission, TestDetail, SubmissionResult

import logging
logger = logging.getLogger(__name__)

async def process_job(
    engine: AIOEngine,
    redis: Redis,
    http_client: httpx.AsyncClient
) -> None:
    # Stage 1: Wait for next job
    logger.info("Stage 1: Waiting for next job")
    _, raw = await redis.brpop(config.QUEUE_KEY)
    job: Dict[str, Any] = json.loads(raw)
    logger.info("Stage 1: Received job: %s", job)

    submission_id = job["submissionId"]
    problem_id = job["problemId"]
    source = job.get("sourceCode")
    language = job.get("language")
    stdin_data = job.get("stdin", "")

    obj_id = ObjectId(submission_id)
    now = datetime.now(timezone.utc)

    # Stage 2: Mark running in Mongo and notify
    logger.info("Stage 2: Marking submission %s as running", submission_id)
    submission = await engine.find_one(Submission, Submission.id == obj_id)
    if submission:
        submission.status = "running"
        submission.updatedAt = now
        await engine.save(submission)
        logger.debug("Stage 2: Mongo status set to 'running' for %s", submission_id)
    await redis.publish(submission_id, json.dumps({"status": "running"}))
    logger.debug("Stage 2: Published 'running' to Redis channel %s", submission_id)

    # Stage 3: Fetch test cases
    logger.info("Stage 3: Fetching test cases for problem %s", problem_id)
    try:
        testcases = await fetch_testcases(http_client, problem_id)
        logger.info("Stage 3: Retrieved %d test cases", len(testcases))
        logger.info("Stage 3: Test cases: %s", testcases)
    except Exception as error:
        logger.error("Stage 3: Failed to fetch test cases for problem %s: %s", problem_id, error, exc_info=True)
        # Mark failed in Mongo and notify
        submission = await engine.find_one(Submission, Submission.id == obj_id)

        now2 = datetime.now(timezone.utc)
        if submission:
            # wrap the fetch error in a single TestDetail
            err_detail = TestDetail(
                test_case_id="fetch_error",
                verdict="error",
                status="failed",
                stdout="",
                runtime_ms=0.0,
                memory_bytes=0,
                error_message=f"Could not fetch test cases: {error}"
            )
            result_model = SubmissionResult(
                total_tests=0,
                passed_tests=0,
                max_runtime_ms=0.0,
                max_memory_bytes=0,
                test_details=[err_detail],
            )

            submission.status = "failed"
            submission.result = result_model
            submission.completedAt = now2
            submission.updatedAt = now2
            await engine.save(submission)
            logger.debug("Stage 3: Saved fetch-error result for %s", submission_id)

        # notify frontend that we're in a terminal failed state
        await redis.publish(submission_id, json.dumps({"status": "failed"}))
        logger.debug("Stage 3: Published 'failed' to Redis channel %s", submission_id)
        return

    # Stage 4: Execute test cases
    logger.info("Stage 4: Executing %d test cases in sandbox", len(testcases))
    details = []
    all_passed = True

    for idx, tc in enumerate(testcases, start=1):
        case_id = ObjectId(tc["caseId"])
        logger.debug("Stage 4: Running test %d/%d (caseId=%s)", idx, len(testcases), case_id)
        details: List[TestDetail] = []

        if not tc.get("isRemote", False):
            inp = tc.get("input", "")
            exp = tc.get("expectedOutput", "")
        else:
            input_path = tc.get("inputPath", "")
            expected_path = tc.get("outputPath", "")

            try:
                with open(input_path, 'r') as f:
                    inp = f.read()
                logger.debug("Loaded input from %s", input_path)
            except Exception as e:
                logger.error("Failed to read input file %s: %s", input_path, e)
                inp = ""

            try:
                with open(expected_path, 'r') as f:
                    exp = f.read()
                logger.debug("Loaded expected output from %s", expected_path)
            except Exception as e:
                logger.error("Failed to read expected output file %s: %s", expected_path, e)
                exp = ""
        logger.debug("Stage 4: Input: %s", inp)
        logger.debug("Stage 4: Expected Output: %s", exp)
        try:
            result = await run_in_sandbox(
                language=language,
                source_code=source,
                stdin=inp,
                timeout_sec=submission.timeLimitMs / 1000,
                memory_bytes=submission.memoryLimitB,
            )

            logger.info("Stage 4: Test %d/%d executed, result=%s", idx, len(testcases), result)

            # post-process memory-limit verdict...
            verdict = result.get("verdict")
            passed = (
                    verdict == "OK"
                    and result.get("stdout", "").strip() == exp.strip()
            )
            logger.info("Stage 4: Test %d verdict=%s passed=%s", idx, verdict, passed)

            details.append(
                TestDetail(
                    test_case_id=str(case_id),
                    verdict=verdict or "",
                    status="passed" if passed else "failed",
                    stdout=result.get("stdout", ""),
                    runtime_ms=result.get("runtime_ms", 0.0),
                    memory_bytes=result.get("memory_bytes", 0),
                    error_message=result.get("stderr", None),
                )
            )
        except Exception as error:
            passed = False
            result = {
                "exitCode": -1,
                "stdout": "",
                "stderr": str(error),
                "runtime_ms": 0,
                "memory_bytes": 0
            }
            logger.error("Stage 4: Error executing test %d for submission %s: %s", idx, submission_id, error, exc_info=True)

            # build a TestDetail model (uses your aliases under the hood)
            details.append(
                TestDetail(
                    test_case_id=str(case_id),
                    verdict=verdict or "",
                    status="passed" if passed else "failed",
                    stdout=result.get("stdout", ""),
                    runtime_ms=result.get("runtime_ms", 0.0),
                    memory_bytes=result.get("memory_bytes", 0),
                    error_message=result.get("stderr", None),
                )
            )

        if not passed:
            all_passed = False
            break

    # Stage 5: Aggregate and write final result
    final_status = "success" if all_passed else "failed"
    logger.info("Stage 5: Aggregating results, final status=%s", final_status)

    result_model = SubmissionResult(
        total_tests=len(testcases),
        passed_tests=sum(1 for d in details if d.status == "passed"),
        max_runtime_ms=max((d.runtime_ms for d in details), default=0.0),
        max_memory_bytes=max((d.memory_bytes for d in details), default=0),
        test_details=details,
    )

    now2 = datetime.now(timezone.utc)
    submission = await engine.find_one(Submission, Submission.id == obj_id)
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found when writing result"
        )

    submission.status = final_status
    submission.result = result_model  # <— typed, validated model
    submission.completedAt = now2
    submission.updatedAt = now2
    await engine.save(submission)
    logger.debug("Stage 5: Saved final result for submission %s", submission_id)

    # Stage 6: Notify terminal state
    logger.info(
        "Stage 6: Publishing final status '%s' to Redis channel %s",
        final_status, submission_id
    )
    await redis.publish(submission_id, json.dumps({"status": final_status}))
    logger.info("Stage 6: Completed processing job %s", submission_id)
