import httpx
from typing import Any, Dict, List
import logging

from judge_service.config.config import config

logger = logging.getLogger(__name__)

async def fetch_testcases(
    client: httpx.AsyncClient,
    problem_id: str
) -> List[Dict[str, Any]]:
    """
    Fetches the list of test cases for the given problem ID.
    """
    # Entry log
    logger.info("Starting fetch_testcases for problem_id=%s", problem_id)

    # Build URL
    url = config.TESTCASE_API_FORMAT.format(problemId=problem_id)
    logger.debug("Testcases URL: %s", url)

    # Send request
    try:
        resp = await client.get(url)
        logger.debug("HTTP GET to %s returned status %d", url, resp.status_code)
        resp.raise_for_status()
    except Exception as e:
        logger.error(
            "HTTP error fetching testcases for problem_id=%s: %s",
            problem_id, e, exc_info=True
        )
        raise

    # Parse JSON
    try:
        data = resp.json()
        logger.debug(
            "Parsed %d test cases for problem_id=%s",
            len(data), problem_id
        )
    except Exception as e:
        logger.error(
            "JSON parse error for testcases response for problem_id=%s: %s",
            problem_id, e, exc_info=True
        )
        raise

    # Completion log
    logger.info("Completed fetch_testcases for problem_id=%s", problem_id)
    return data['testCases']
