"""
scraping_service.py

Scrapes the CSES Introductory Problems list and upserts each problem document
into MongoDB.  Uses the project-wide logging configuration defined in
Platform.src.config.logging_config.
"""
import sys
import time
import logging
import io
import zipfile
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

from Platform.src.config.config import config, DevConfig
from Platform.src.config.logging_config import configure_logging  # ← your dictConfig
from Platform.src.problem_management.services.utils import build_problem
from Platform.src.problem_management.services.storage_adapters import LocalAdapter

from Platform.src.problem_management.models import Asset
from Platform.src.problem_management.models import TestCase, FileReferences

configure_logging()
logger = logging.getLogger("Platform.scraping_service")


class ScrapingService:
    """Download the CSES ‘Introductory Problems’ list and store each problem."""

    def __init__(self) -> None:
        self.client = MongoClient(config.MONGODB_URI)
        self.db = self.client[config.DB_NAME]
        self.problem_coll = self.db[config.PROBLEM_COLLECTION]
        self.testcases_collection = self.db[config.TESTCASE_COLLECTION]
        self.assets_collection = self.db[config.ASSETS_COLLECTION]
        self.base_url = config.BASE_SITE
        self.listing_url = config.LISTING_URL
        self.session = requests.Session()
        self.session.cookies.set("PHPSESSID", config.SESSION_ID)
        self.storage = LocalAdapter()

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
        tasks = intro_ul.find_all("li", class_="task")[:config.SCRAPE_LIMIT] if intro_ul else []
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
                self.problem_coll.insert_one(
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

    def store_file_and_create_asset(self, file_bytes: bytes, cses_id: str, filename: str, purpose: str):
        path = self.storage.save(file_bytes, filename)
        asset = Asset(
            filename=filename,
            contentType="text/plain",
            size=len(file_bytes),
            isS3=False,
            filePath=path,
            s3Key=None,
            pId=cses_id,
            purpose=purpose,
            isPublic=False
        )
        res = self.assets_collection.insert_one(asset.model_dump())
        return res.inserted_id

    # ——— Fetch & store test cases ———
    def fetch_and_store_testcases(self, cses_id: str):
        logger.info("Requesting test case ZIP for CSES Problem ID: %s", cses_id)
        url = config.TEST_CASES + str(cses_id)
        res = self.session.get(url)
        soup = BeautifulSoup(res.content, "html.parser")
        token = soup.find("input", {"name": "csrf_token"})
        if not token:
            logger.error("CSRF token not found. Are you logged in?")
            return

        download = self.session.post(url, data={"csrf_token": token["value"], "download": "true"})
        if download.status_code != 200:
            logger.error("Failed to download test case ZIP for CSES Problem ID %s – Status %d", cses_id, download.status_code)
            return

        try:
            with zipfile.ZipFile(io.BytesIO(download.content)) as z:
                ins = sorted(f for f in z.namelist() if f.endswith(".in"))
                outs = sorted(f for f in z.namelist() if f.endswith(".out"))
                for i, in_name in enumerate(ins):
                    out_name = outs[i]
                    inp_text = z.read(in_name).decode().strip()
                    out_text = z.read(out_name).decode().strip()
                    inp_b = inp_text.encode()
                    out_b = out_text.encode()
                    is_large = len(inp_b) >= 500 or len(out_b) >= 500

                    if is_large:
                        in_id = self.store_file_and_create_asset(inp_b, cses_id, in_name, "test_input")
                        out_id = self.store_file_and_create_asset(out_b, cses_id, out_name, "test_output")
                        refs = FileReferences(inputFileId=in_id, outputFileId=out_id)
                    else:
                        refs = None

                    tc = TestCase(
                        pId=cses_id,
                        input=None if is_large else inp_text,
                        expectedOutput=None if is_large else out_text,
                        isHidden=True,
                        isLargeFile=is_large,
                        fileReferences=refs,
                    )
                    result = self.testcases_collection.insert_one(tc.model_dump())
                    logger.info("Inserted test case %d for CSES Problem ID %s: %s", i + 1, cses_id, result.inserted_id)
        except zipfile.BadZipFile:
            logger.error("Invalid ZIP format received for CSES Problem ID: %s", cses_id)

    def scrape_test_cases(self):
        res = self.session.get(config.PROBLEM_LIST)
        soup = BeautifulSoup(res.content, "html.parser")
        section = soup.find("h2", string="Introductory Problems")
        lst = section.find_next("ul")
        for task in lst.find_all("li", class_="task")[:config.SCRAPE_LIMIT]:
            href = task.find("a")["href"]
            cses_id = href.rstrip("/").split("/")[-1]
            self.fetch_and_store_testcases(cses_id)
            time.sleep(2)


if __name__ == "__main__":
    # Set DEBUG level when running in development mode
    if isinstance(config, DevConfig):
        logger.setLevel(logging.DEBUG)

    scraping_service = ScrapingService()
    scraping_service.scrape_problems()
    scraping_service.scrape_test_cases()
