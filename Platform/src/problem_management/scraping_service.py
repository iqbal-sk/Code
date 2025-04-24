"""
scraping_service.py

Scrapes the CSES Introductory Problems list and upserts each problem document
into MongoDB.  Uses the project-wide logging configuration defined in
Platform.src.config.logging_config.
"""
import sys
import time
import logging
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

from Platform.src.config.config import config, DevConfig
from Platform.src.config.logging_config import configure_logging  # ← your dictConfig
from Platform.src.problem_management.utils import build_problem


# --------------------------------------------------------------------------- #
# Initialise logging (inherit handlers/levels from the “Platform” root logger)
# --------------------------------------------------------------------------- #
configure_logging()
logger = logging.getLogger("Platform.scraping_service")


class ScrapingService:
    """Download the CSES ‘Introductory Problems’ list and store each problem."""

    def __init__(self) -> None:
        self.client = MongoClient(config.MONGODB_URI)
        self.db = self.client[config.DB_NAME]
        self.coll = self.db[config.PROBLEM_COLLECTION]
        self.base_url = config.BASE_SITE
        self.listing_url = config.LISTING_URL

    # --------------------------------------------------------------------- #
    # Main workflow
    # --------------------------------------------------------------------- #
    def scrape_problems(self) -> None:
        """Scrape problems and insert them into MongoDB."""
        try:
            listing_page = requests.get(self.listing_url, timeout=10)
            listing_page.raise_for_status()
            logger.info("Downloaded listing page: %s", self.listing_url)
        except Exception as exc:  # network, timeout, HTTPError, …
            logger.critical("Failed to download problem list (%s)", exc, exc_info=True)
            sys.exit(1)

        soup = BeautifulSoup(listing_page.text, "html.parser")

        intro_h2 = soup.find("h2", string=lambda s: s and "Introductory Problems" in s)
        if not intro_h2:
            logger.critical("Introductory Problems section not found on listing page.")
            sys.exit(1)

        intro_ul = intro_h2.find_next("ul", class_="task-list")
        tasks = intro_ul.find_all("li", class_="task") if intro_ul else []
        if not tasks:
            logger.critical("No tasks found in Introductory Problems.")
            sys.exit(1)

        logger.info("Found %d tasks in Introductory Problems.", len(tasks))

        for li in tasks:
            raw_href = li.a["href"].strip()
            url = urljoin(self.base_url, raw_href)
            title = li.a.text.strip()

            try:
                problem_doc = build_problem(url, title)
                self.coll.insert_one(
                    problem_doc.model_dump(by_alias=True, exclude={"id"}, exclude_none=True)
                )
                logger.info("Inserted '%s'", title)

            except DuplicateKeyError:
                # document with the same pId or slug already exists
                logger.debug("Skipped (already present): '%s'", title)

            except Exception as exc:
                # generic failure—log full traceback for debugging
                logger.error("Failed to insert '%s' — %s", title, exc, exc_info=True)

            time.sleep(5)  # be polite to the CSES server


# --------------------------------------------------------------------------- #
# Entrypoint
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    # Set DEBUG level when running in development mode
    if isinstance(config, DevConfig):
        logger.setLevel(logging.DEBUG)

    ScrapingService().scrape_problems()
