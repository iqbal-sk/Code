#!/usr/bin/env python3

import sys
import io
import zipfile
import logging
import asyncio
from bson import ObjectId
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from typing import List
import Platform.src.problem_management.models
from Platform.src.config.config import config, DevConfig
from Platform.src.config.logging_config import configure_logging
from Platform.src.core.dependencies import get_engine
from Platform.src.problem_management.services.storage_adapters import LocalAdapter
from Platform.src.problem_management.models import Problem, Asset, TestCase
from Platform.src.problem_management.services.utils import *
# ─── Setup logging ───────────────────────────────────────────────────────────────
configure_logging()
logger = logging.getLogger("Platform.scraping_service")
if isinstance(config, DevConfig):
    logger.setLevel(logging.DEBUG)

class ScrapingService:
    def __init__(self):
        self.engine = get_engine()  # type: ignore
        self.base_url = config.BASE_SITE
        self.listing_url = config.LISTING_URL
        self.session = requests.Session()
        self.session.cookies.set("PHPSESSID", config.SESSION_ID)
        self.storage = LocalAdapter()

    async def build_problem(self, task_url: str, title: str) -> Problem:
        """Scrape a single CSES problem page, store any images as Assets, and return a Problem."""
        # Extract problem ID from the URL
        p_id = int(task_url.rstrip("/").split("/")[-1])

        # Fetch the problem HTML
        resp = requests.get(task_url, timeout=10)
        resp.raise_for_status()
        body = BeautifulSoup(resp.text, "html.parser").select_one("div.content")

        # Parse description and markdown
        html_desc, md_desc = extract_problem_statement(body)
        image_links = extract_image_links(html_desc)

        # Extract resource limits, I/O blocks, and constraint bullets
        full_text = body.get_text("\n", strip=True)
        time_ms, mem_mb = extract_limits(full_text)
        input_block, output_block = extract_io_blocks(body)
        bullet_list = extract_constraint_bullets(body)

        problemId = ObjectId()

        # Build sample test cases from <pre> tags
        pres = body.select("pre")
        samples: list[SampleTestCase] = []
        for i in range(0, len(pres), 2):
            if i + 1 >= len(pres):
                break
            samples.append(
                SampleTestCase(
                    input=pres[i].get_text("\n").rstrip(),
                    expectedOutput=pres[i + 1].get_text("\n").rstrip(),
                    explanation="",
                )
            )

        # Save each image URL as an Asset and collect their ObjectIds
        asset_ids: list[ObjectId] = []
        for url in image_links:
            asset = Asset(
                filename=url.split("/")[-1],
                contentType="image/png",  # or detect MIME dynamically
                size=0,  # optionally fetch Content-Length
                isS3=False,
                filePath=url,
                s3Key=None,
                pId=p_id,
                purpose="problem-image",
                isPublic=True,
                problemId=problemId
            )
            saved_asset = await self.engine.save(asset)
            asset_ids.append(saved_asset.id)

        # Construct and return the Problem document
        return Problem(
            id=problemId,
            pId=p_id,
            title=title,
            slug=slugify(title),
            description=Description(markdown=md_desc, html=html_desc),
            constraints=Constraints(
                timeLimit_ms=time_ms,
                memoryLimit_mb=mem_mb,
                inputFormat=input_block,
                outputFormat=output_block,
                pConstraints=bullet_list,
            ),
            sampleTestCases=samples,
            tags=None,
            visibility="public",
            assets=asset_ids,
        )

    async def scrape_problems(self) -> None:
        """Fetch CSES Intro Problems & insert each Problem only once."""
        try:
            resp = requests.get(self.listing_url, timeout=10)
            resp.raise_for_status()
        except Exception as exc:
            logger.critical("Failed to download problem list: %s", exc, exc_info=True)
            sys.exit(1)

        soup = BeautifulSoup(resp.text, "html.parser")
        intro_h2 = soup.find("h2", string=lambda s: s and "Introductory Problems" in s)
        if not intro_h2:
            logger.critical("‘Introductory Problems’ header not found.")
            sys.exit(1)

        tasks = intro_h2.find_next("ul", class_="task-list") \
                       .find_all("li", class_="task")[: config.SCRAPE_LIMIT]

        for li in tasks:
            url = urljoin(self.base_url, li.a["href"].strip())
            title = li.a.text.strip()
            problem_doc = await self.build_problem(url, title)

            # 1) Check if this problem already exists
            existing = await self.engine.find_one(
                Problem, Problem.pId == problem_doc.pId
            )
            if existing:
                logger.debug("Skipped Problem '%s' (already exists)", title)
            else:
                # 2) Insert new
                saved = await self.engine.save(problem_doc)
                logger.info("Saved new Problem '%s' → %s", title, saved.id)

            await asyncio.sleep(5)


    async def store_file_and_create_asset(
        self,
        file_bytes: bytes,
        cses_id: str,
        filename: str,
        purpose: str
    ) -> object:
        """Persist a large test-case file as an Asset, return its ObjectId."""
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

        # Check asset uniqueness (e.g. by path & pId & purpose)
        existing = await self.engine.find_one(
            Asset,
            Asset.filePath == path,
            Asset.pId == cses_id,
            Asset.purpose == purpose
        )
        if existing:
            return existing.id

        saved_asset = await self.engine.save(asset)
        return saved_asset.id


    async def fetch_and_store_testcases(self, cses_id: str) -> None:
        """Download, unzip & store all testcases, skipping duplicates."""
        logger.info("Downloading test ZIP for %s", cses_id)
        url = config.TEST_CASES + str(cses_id)
        entry = self.session.get(url)
        soup = BeautifulSoup(entry.content, "html.parser")
        token_el = soup.find("input", {"name": "csrf_token"})
        if not token_el:
            logger.error("No CSRF token; are you logged in?")
            return

        download = self.session.post(url, data={
            "csrf_token": token_el["value"],
            "download": "true"
        })
        if download.status_code != 200:
            logger.error("Failed to download ZIP (%d)", download.status_code)
            return

        # get the raw Motor collection for TestCase
        tc_coll = self.engine.get_collection(TestCase)

        with zipfile.ZipFile(io.BytesIO(download.content)) as z:
            ins = sorted(f for f in z.namelist() if f.endswith(".in"))
            outs = sorted(f for f in z.namelist() if f.endswith(".out"))

            for idx, in_name in enumerate(ins):
                inp = z.read(in_name).decode().strip()
                out = z.read(outs[idx]).decode().strip()
                inp_b, out_b = inp.encode(), out.encode()
                is_large = len(inp_b) >= 500 or len(out_b) >= 500

                if is_large:
                    in_id = await self.store_file_and_create_asset(
                        inp_b, cses_id, in_name, "test_input"
                    )
                    out_id = await self.store_file_and_create_asset(
                        out_b, cses_id, outs[idx], "test_output"
                    )
                    refs = {"inputFileId": in_id, "outputFileId": out_id}

                    # raw Mongo filter for dict sub-field
                    filter_q = {
                        "pId": cses_id,
                        "isLargeFile": True,
                        "fileReferences.inputFileId": in_id
                    }

                else:
                    refs = None
                    filter_q = {
                        "pId": cses_id,
                        "isLargeFile": False,
                        "input": inp,
                        "expectedOutput": out
                    }

                existing_tc = await tc_coll.find_one(filter_q)
                if existing_tc:
                    logger.debug("Skipped TC %d for %s (already exists)", idx + 1, cses_id)
                else:
                    tc = TestCase(
                        pId=cses_id,
                        input=None if is_large else inp,
                        expectedOutput=None if is_large else out,
                        isHidden=True,
                        isLargeFile=is_large,
                        fileReferences=refs,
                    )
                    saved_tc = await self.engine.save(tc)
                    logger.info("Saved TC %d for %s → %s", idx + 1, cses_id, saved_tc.id)

        await asyncio.sleep(2)

    async def scrape_test_cases(self) -> None:
        """Walk the Intro Problems list & fetch testcases for each."""
        resp = self.session.get(config.PROBLEM_LIST)
        soup = BeautifulSoup(resp.content, "html.parser")
        section = soup.find("h2", string="Introductory Problems")
        tasks = section.find_next("ul") \
                       .find_all("li", class_="task")[: config.SCRAPE_LIMIT]

        for task in tasks:
            cses_id = task.find("a")["href"].rstrip("/").split("/")[-1]
            await self.fetch_and_store_testcases(cses_id)


# ─── Entrypoint ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    svc = ScrapingService()

    async def main():
        await svc.scrape_problems()
        await svc.scrape_test_cases()

    asyncio.run(main())
