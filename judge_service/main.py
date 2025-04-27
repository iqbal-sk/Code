import asyncio

# 1) configure logging exactly once, at startup
from judge_service.config.logging_config import configure_logging
configure_logging()

from judge_service.core.dependencies import get_engine, get_redis
from judge_service.job_processor import process_job
import httpx
import logging

logger = logging.getLogger(__name__)

async def main():
    logger.info("Starting Judge Worker application")
    # Initialize dependencies
    logger.debug("Initializing database engine")
    engine = get_engine()
    logger.info("Database engine configured successfully")

    logger.debug("Connecting to Redis server")
    redis = await get_redis()
    logger.info("Connected to Redis server at %s", redis.address if hasattr(redis, 'address') else 'unknown')

    logger.debug("Creating HTTP client for Docker execution service")
    http_client = httpx.AsyncClient()
    logger.info("HTTP client initialized")

    logger.info("Judge Worker started, waiting for jobs...")
    try:
        while True:
            logger.debug("Polling for next job from Redis queue")
            try:
                await process_job(engine, redis, http_client)
                logger.info("Job processed successfully")
            except Exception as job_err:
                logger.exception("Error processing job: %s", job_err)
    except asyncio.CancelledError:
        logger.warning("Judge Worker cancelled, shutting down...")
    except Exception as fatal_err:
        logger.exception("Unexpected error in main loop: %s", fatal_err)
    finally:
        logger.info("Cleaning up resources and shutting down HTTP client")
        await http_client.aclose()
        logger.info("Judge Worker shutdown complete")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as run_err:
        logger.exception("Fatal error running Judge Worker: %s", run_err)
