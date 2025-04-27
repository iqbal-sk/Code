import json
from datetime import datetime, timezone
from typing import Any, Dict
import httpx
from bson import ObjectId
from odmantic import AIOEngine

from judge_service.config.config import config
from judge_service.testcase_client import fetch_testcases
from judge_service.sandbox import run_in_sandbox
from redis.asyncio import Redis
from Platform.src.submission_management.models.submission import Submission

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
    except Exception as error:
        logger.error("Stage 3: Failed to fetch test cases for problem %s: %s", problem_id, error, exc_info=True)
        # Mark failed in Mongo and notify
        submission = await engine.find_one(Submission, Submission.id == obj_id)
        if submission:
            submission.status = "failed"
            submission.result = {"compileError": f"Could not fetch test cases: {error}"}
            submission.completedAt = now
            submission.updatedAt = now
            await engine.save(submission)
            logger.debug("Stage 3: Mongo status set to 'failed' for %s", submission_id)
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

        if not tc.get("isRemote", False):
            inp = tc.get("input", "")
            exp = tc.get("expectedOutput", "")
        else:
            inp = ""
            exp = ""

        try:
            result = await run_in_sandbox(
                language=language,
                source_code=source,
                stdin=inp,
                timeout_sec=submission.timeLimitMs / 1000,
                memory_bytes=submission.memoryLimitB,
            )
            if result.get('verdict') == 'OK' and submission.memoryLimitB < result.get('memory_bytes', 0):
                result['verdict'] = 'MemoryLimitExceeded'
            verdict = result.get('verdict')
            passed = (verdict == 'OK' and result.get('stdout', '').strip() == exp.strip())
            logger.debug("Stage 4: Test %d verdict=%s passed=%s", idx, verdict, passed)
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

        details.append({
            "testCaseId": str(case_id),
            "verdict": result.get("verdict", ""),
            "status": "passed" if passed else "failed",
            "stdout": result.get("stdout", ""),
            "runtime_ms": result.get("runtime_ms", 0),
            "memory_bytes": result.get("memory_bytes", 0),
            "errorMessage": result.get("stderr", "")
        })

        if not passed:
            all_passed = False
            break

    # Stage 5: Aggregate and write final result
    final_status = "success" if all_passed else "failed"
    logger.info("Stage 5: Aggregating results, final status=%s", final_status)
    result_doc = {
        "totalTests": len(testcases),
        "passedTests": sum(1 for d in details if d["status"] == "passed"),
        "max_runtime_ms": max((d["runtime_ms"] for d in details), default=0),
        "max_memory_bytes": max((d["memory_bytes"] for d in details), default=0),
        "testDetails": details,
    }

    now2 = datetime.now(timezone.utc)
    submission = await engine.find_one(Submission, Submission.id == obj_id)
    if submission:
        submission.status = final_status
        submission.result = result_doc
        submission.completedAt = now2
        submission.updatedAt = now2
        await engine.save(submission)
        logger.debug("Stage 5: Saved final result for submission %s", submission_id)

    # Stage 6: Notify terminal state
    logger.info("Stage 6: Publishing final status '%s' to Redis channel %s", final_status, submission_id)
    await redis.publish(submission_id, json.dumps({"status": final_status}))
    logger.info("Stage 6: Completed processing job %s", submission_id)
