import re, requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from slugify import slugify
from markdownify import markdownify as md
from Platform.src.problem_management.models.problem import (
    Problem,
    Description,
    Constraints,
    SampleTestCase,
)


def extract_limits(text: str):
    t = re.search(r"Time limit:\s*([\d.]+)\s*s", text)
    m = re.search(r"Memory limit:\s*([\d.]+)\s*MB", text)
    if not (t and m):
        raise ValueError("Time/Memory limit not found")
    return int(float(t.group(1)) * 1000), int(float(m.group(1)))


def extract_problem_statement(content_div):
    inner_html = content_div.decode_contents()
    end_constraints = re.search(r'</ul>\s*', inner_html, flags=re.I)
    start_input = re.search(r'<h1[^>]*id=["\']input["\']', inner_html, flags=re.I)

    if not (end_constraints and start_input):
        fallback = re.split(r'<h1[^>]*id=["\']input["\']', inner_html,
                            flags=re.I, maxsplit=1)[0]
        return fallback.strip(), md(fallback)

    html_fragment = inner_html[end_constraints.end(): start_input.start()].strip()
    return html_fragment, md(html_fragment)


def extract_image_links(html_fragment, base_url="https://cses.fi/"):
    soup = BeautifulSoup(html_fragment, "html.parser")
    return [urljoin(base_url, img["src"])
            for img in soup.find_all("img") if img.get("src")]


def extract_constraint_bullets(content_div):
    header = content_div.find("h1", id="constraints")
    if not header:
        return []

    list_tag = header.find_next(lambda tag: tag.name in {"ul", "ol"})
    if not list_tag:
        return []

    return [" ".join(li.stripped_strings)
            for li in list_tag.find_all("li", recursive=False)]


def extract_io_blocks(body):
    """Return (input_block, output_block) as plain text."""
    def section(id_):
        h = body.find("h1", id=id_)
        if not h:
            return ""
        parts = []
        for sib in h.find_next_siblings():
            if sib.name == "h1":           # stop at the next section
                break
            parts.append(sib.get_text("\n", strip=True))
        return "\n".join(parts).strip()
    return section("input"), section("output")


def build_problem(task_url: str, title: str) -> dict:
    p_id = int(task_url.rstrip("/").split("/")[-1])
    page = requests.get(task_url, timeout=10)
    page.raise_for_status()
    body = BeautifulSoup(page.text, "html.parser").select_one("div.content")

    html_desc, md_desc = extract_problem_statement(body)
    image_links = extract_image_links(html_desc)

    full_text = body.get_text("\n", strip = True)
    time_ms, mem_mb = extract_limits(full_text)
    input_block, output_block = extract_io_blocks(body)
    bullet_list = extract_constraint_bullets(body)

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

    problem = Problem(
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
        assets=image_links
    )

    return problem
