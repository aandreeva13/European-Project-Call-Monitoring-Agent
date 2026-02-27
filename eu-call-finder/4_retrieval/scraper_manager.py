import json
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# NOTE:
# This module used to execute scraping immediately at import time.
# It has been refactored into pure functions + a LangGraph node factory.


# --- DEFAULTS (safe to override via node input) ---
DEFAULT_SEARCH_TERMS: List[str] = [
    "AI AND Manufacturing",
    "Robotics AND AI",
    "Cyber-Physical Systems",
]

DEFAULT_HEADLESS_MODE = False


def resolve_search_terms(search_terms: Optional[List[str]]) -> List[str]:
    """Resolve terms from in-memory input; fall back to module defaults."""
    if search_terms and len(search_terms) > 0:
        return [str(t) for t in search_terms]
    return DEFAULT_SEARCH_TERMS


def clean_text(text: Optional[str]) -> str:
    if not text:
        return "N/A"
    return text.replace("Show more", "").replace("Show less", "").strip()


def extract_section(full_text: str, start_marker: str, end_markers: List[str]) -> str:
    """Slice text starting after start_marker and ending before the first end_marker."""
    try:
        if start_marker not in full_text:
            return "N/A"
        parts = full_text.split(start_marker)
        content = parts[-1]
        best_end_index = len(content)
        for marker in end_markers:
            idx = content.find(marker)
            if idx != -1 and idx < best_end_index:
                best_end_index = idx
        return content[:best_end_index].strip()
    except Exception:
        return "N/A"


def extract_description_smart(full_text: str) -> str:
    """Extractor for description that ignores 'Topic updates'."""
    if "Topic description" not in full_text:
        return "N/A"
    content_part = full_text.split("Topic description")[-1]
    end_markers = ["Topic destination", "Topic conditions and documents"]
    best_end_index = len(content_part)
    for marker in end_markers:
        idx = content_part.find(marker)
        if idx != -1 and idx < best_end_index:
            best_end_index = idx
    return clean_text(content_part[:best_end_index])


def scrape_partners(driver: webdriver.Chrome) -> List[Dict[str, str]]:
    partners: List[Dict[str, str]] = []
    try:
        wait = WebDriverWait(driver, 5)
        partner_btn = wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//div[contains(text(), 'Partner search announcements')]/ancestor::div[contains(@class, 'eui-card')]//a[contains(text(), 'View / Edit') or contains(@href, 'partner-search')]",
                )
            )
        )

        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", partner_btn
        )
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", partner_btn)

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))
        time.sleep(2)

        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) >= 3:
                partners.append(
                    {
                        "organization": cols[0].text.strip(),
                        "country": cols[1].text.strip(),
                        "type": cols[2].text.strip(),
                        "expertise": cols[3].text.strip() if len(cols) > 3 else "N/A",
                    }
                )

        driver.back()
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "eui-page-content")))
        time.sleep(1)
    except Exception:
        # Common for topics not to have partners
        pass
    return partners


def _api_search_topics(
    search_terms: List[str], query_data: Dict[str, Any]
) -> List[Dict[str, str]]:
    """Return unique topics from the EU search API as list of {identifier, title}."""
    unique_topics_map: Dict[str, Dict[str, str]] = {}

    search_url = "https://api.tech.ec.europa.eu/search-api/prod/rest/search"
    headers = {"User-Agent": "Mozilla/5.0"}

    for term in search_terms:
        params = {"apiKey": "SEDIA", "text": term, "pageSize": "50", "pageNumber": "1"}

        files = {
            "query": ("blob", json.dumps(query_data), "application/json"),
            "displayFields": (
                "blob",
                json.dumps(["identifier", "title"]),
                "application/json",
            ),
        }

        response = requests.post(
            search_url, params=params, files=files, headers=headers, timeout=30
        )
        response.raise_for_status()

        raw_results = response.json().get("results", [])
        for item in raw_results:
            meta = item.get("metadata", {})
            identifiers = meta.get("identifier", [])
            if identifiers:
                t_id = identifiers[0]
                if t_id not in unique_topics_map:
                    unique_topics_map[t_id] = {
                        "identifier": t_id,
                        "title": (meta.get("title", [""]) or [""])[0],
                    }

        time.sleep(1)  # be polite

    return list(unique_topics_map.values())


def _make_driver(headless: bool) -> webdriver.Chrome:
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )

    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options,
    )


def default_search_query() -> Dict[str, Any]:
    """Default EU search API query.

    Override by passing `state['search_query']` into [`scrape_topics_node()`](eu-call-finder/4_retrieval/scraper_manager.py:294).
    """

    return {
        "bool": {
            "must": [
                {"terms": {"type": ["1", "2", "8"]}},
                {"terms": {"status": ["31094501", "31094502"]}},
                {"term": {"programmePeriod": "2021 - 2027"}},
            ]
        }
    }


# ---------------------------------------------------------------------------
# Budget / contribution helpers (pure-text, no Selenium needed)
# ---------------------------------------------------------------------------
def _extract_budget_amount(topic_id: str, budget_text: str) -> str:
    """Extract the specific budget amount for this topic from the budget table.

    Strategy:
    - Find the line containing the topic_id
    - Prefer the first *large* number (>= 10k) near that line (same line or next few)
    - Avoid years / row numbers (common noise)
    """
    if not budget_text or topic_id not in budget_text:
        return "N/A"

    lines = budget_text.split("\n")
    for i, line in enumerate(lines):
        if topic_id not in line:
            continue

        window = "\n".join(lines[i : min(i + 4, len(lines))])
        raw_nums = re.findall(r"\d[\d\s,]*\d|\d+", window)

        candidates: list[int] = []
        for raw in raw_nums:
            digits = raw.replace(" ", "").replace(",", "")
            try:
                n = int(digits)
            except Exception:
                continue
            if n < 10000:
                continue
            if 1900 <= n <= 2100:
                continue
            candidates.append(n)

        if not candidates:
            return "N/A"

        num = max(candidates)
        if num >= 1000000:
            return f"€{num / 1000000:.1f}M"
        elif num >= 1000:
            return f"€{num / 1000:.0f}K"
        else:
            return f"€{num}"

    return "N/A"


def _extract_contribution_amount(topic_id: str, budget_text: str) -> str:
    """Extract indicative per-project contribution for this topic.

    The 'Budget overview' section usually contains a 'Contributions' column.
    We try to capture patterns like:
    - around 17500000
    - 4800000 to 5600000
    - around 4 000 000
    """
    if not budget_text or topic_id not in budget_text:
        return "N/A"

    lines = [ln.strip() for ln in budget_text.split("\n") if ln.strip()]
    for i, line in enumerate(lines):
        if topic_id not in line:
            continue

        window = "\n".join(lines[i : min(i + 8, len(lines))]).lower()

        m_range = re.search(r"(\d[\d\s,]{3,})\s*to\s*(\d[\d\s,]{3,})", window)
        if m_range:
            a_digits = re.sub(r"\D", "", m_range.group(1))
            b_digits = re.sub(r"\D", "", m_range.group(2))
            if not a_digits or not b_digits:
                return "N/A"
            a, b = int(a_digits), int(b_digits)
            lo, hi = min(a, b), max(a, b)
            return f"€{lo/1_000_000:.1f}M–€{hi/1_000_000:.1f}M"

        m_around = re.search(r"around\s*(\d[\d\s,]{3,})", window)
        if m_around:
            n_digits = re.sub(r"\D", "", m_around.group(1))
            if not n_digits:
                return "N/A"
            n = int(n_digits)
            return f"~€{n/1_000_000:.1f}M" if n >= 1_000_000 else f"~€{n}"

        nums = [
            int(re.sub(r"\D", "", x))
            for x in re.findall(r"\d[\d\s,]{4,}", window)
            if re.sub(r"\D", "", x)
        ]
        nums = [n for n in nums if n >= 100000 and not (1900 <= n <= 2100)]
        if nums:
            n = max(nums)
            return f"€{n/1_000_000:.1f}M" if n >= 1_000_000 else f"€{n}"

    return "N/A"


# ---------------------------------------------------------------------------
# Per-topic worker (runs in its own thread with its own Chrome driver)
# ---------------------------------------------------------------------------
def _scrape_single_topic(
    item: Dict[str, str], headless: bool, worker_id: int = 0
) -> Optional[Dict[str, Any]]:
    """Scrape one EU topic page in an isolated browser instance.

    Designed to be submitted to a ThreadPoolExecutor — each call owns its own
    Selenium WebDriver and is fully independent of any other call.
    """
    tag = f"[SCRAPER-W{worker_id}]"
    topic_id = item["identifier"]
    url = (
        "https://ec.europa.eu/info/funding-tenders/opportunities/portal/"
        f"screen/opportunities/topic-details/{topic_id}"
    )

    driver = _make_driver(headless=headless)
    try:
        print(f"{tag} Scraping {topic_id} …")
        driver.get(url)
        wait = WebDriverWait(driver, 20)
        wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "eui-page-content"))
        )

        # Remove common overlays
        try:
            driver.execute_script(
                "var blockers=document.querySelectorAll("
                "'.cck-cookie-banner, .eui-app-header'"
                ");blockers.forEach(el=>el.remove());"
            )
        except Exception:
            pass

        # Expand "Show more"
        time.sleep(1.5)
        expand_triggers = driver.find_elements(
            By.XPATH, "//*[contains(text(), 'Show more')]"
        )
        for trigger in expand_triggers:
            try:
                driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", trigger
                )
                time.sleep(0.1)
                driver.execute_script("arguments[0].click();", trigger)
                time.sleep(0.1)
            except Exception:
                pass
        time.sleep(1)

        full_text = driver.find_element(By.TAG_NAME, "body").text

        # --- text extraction (pure string ops, no Selenium) ----
        desc_text = extract_description_smart(full_text)
        dest_text = extract_section(
            full_text,
            "Topic destination",
            ["Topic conditions and documents", "Budget overview"],
        )
        cond_text = extract_section(
            full_text,
            "Topic conditions and documents",
            ["Budget overview", "Partner search"],
        )
        budget_text = extract_section(
            full_text,
            "Budget overview",
            [
                "Partner search announcements",
                "Start submission",
                "Topic Q&As",
                "Get support",
            ],
        )

        def get_val(label: str) -> str:
            match = re.search(
                rf"{re.escape(label)}\s*\n([^\n]+)", full_text, re.IGNORECASE
            )
            return match.group(1).strip() if match else "N/A"

        budget_amount = _extract_budget_amount(topic_id, budget_text)
        contribution_amount = _extract_contribution_amount(topic_id, budget_text)

        # Partners — uses this worker's own driver
        partners_data = scrape_partners(driver)

        record: Dict[str, Any] = {
            "id": topic_id,
            "title": item.get("title", ""),
            "url": url,
            "status": "Forthcoming" if "Forthcoming" in full_text else "Open",
            "general_info": {
                "programme": get_val("Programme"),
                "call": get_val("Call"),
                "action_type": get_val("Type of action"),
                "deadline_model": get_val("Deadline model"),
                "dates": {
                    "opening": get_val("Planned opening date"),
                    "deadline": get_val("Deadline date"),
                },
            },
            "content": {
                "description": clean_text(desc_text),
                "destination": clean_text(dest_text),
                "conditions": clean_text(cond_text),
                "budget_overview": clean_text(budget_text),
            },
            "partners": partners_data,
            "budget": budget_amount,
            "contribution": contribution_amount,
        }
        print(f"{tag} ✓ Done {topic_id}")
        return record

    except Exception as e:
        print(f"{tag} ✗ Error scraping {topic_id}: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        try:
            driver.quit()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Main entry point — parallel via ThreadPoolExecutor
# ---------------------------------------------------------------------------
DEFAULT_MAX_WORKERS = 4


def scrape_topics_to_json(
    *,
    search_terms: Optional[List[str]] = None,
    search_query: Optional[Dict[str, Any]] = None,
    headless: bool = DEFAULT_HEADLESS_MODE,
    max_topics: Optional[int] = None,
    abort_event: Optional[Any] = None,
    max_workers: int = DEFAULT_MAX_WORKERS,
) -> List[Dict[str, Any]]:
    """Run API search + parallel Selenium scraping.

    Each topic is scraped in its own thread with its own Chrome instance,
    giving up to *max_workers*× speed-up over the old sequential approach.
    """
    search_terms = resolve_search_terms(search_terms)
    query = search_query or default_search_query()

    topics_to_scrape = _api_search_topics(search_terms, query)
    if max_topics is not None:
        topics_to_scrape = topics_to_scrape[: max(0, int(max_topics))]

    if not topics_to_scrape:
        return []

    # Clamp workers to the number of topics (no point spawning idle threads)
    n_workers = min(max_workers, len(topics_to_scrape))
    print(
        f"\n[SCRAPER] Parallel scrape: {len(topics_to_scrape)} topics "
        f"with {n_workers} workers"
    )

    final_data: List[Dict[str, Any]] = []
    # Thread-safe counter to assign worker IDs for logging
    _worker_counter = iter(range(len(topics_to_scrape)))

    with ThreadPoolExecutor(max_workers=n_workers) as pool:
        future_to_topic = {
            pool.submit(
                _scrape_single_topic, item, headless, next(_worker_counter)
            ): item
            for item in topics_to_scrape
        }

        for future in as_completed(future_to_topic):
            if abort_event and abort_event.is_set():
                print("\n[SCRAPER] Abort requested — cancelling remaining tasks")
                # Cancel futures that haven't started yet
                for f in future_to_topic:
                    f.cancel()
                break

            try:
                result = future.result()
                if result is not None:
                    final_data.append(result)
            except Exception as e:
                topic = future_to_topic[future]
                print(f"[SCRAPER] Worker exception for {topic.get('identifier','?')}: {e}")

    print(f"[SCRAPER] Parallel scrape complete: {len(final_data)}/{len(topics_to_scrape)} topics")
    return final_data


def scrape_topics_node(state: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """LangGraph node — parallel scraping variant.

    Optional state keys:
    - search_terms: list[str]
    - search_query: dict (EU search API query payload)
    - headless: bool
    - max_topics: int
    - max_workers: int  (default 4)

    Returns:
    - scraped_topics: list[dict]
    """

    search_terms = state.get("search_terms")
    search_query = state.get("search_query")
    headless = bool(state.get("headless", DEFAULT_HEADLESS_MODE))
    max_topics = state.get("max_topics")
    max_workers = int(state.get("max_workers", DEFAULT_MAX_WORKERS))

    config = kwargs.get("config", {})
    configurable = config.get("configurable", {})
    abort_event = configurable.get("abort_event")

    data = scrape_topics_to_json(
        search_terms=search_terms,
        search_query=search_query,
        headless=headless,
        max_topics=max_topics,
        abort_event=abort_event,
        max_workers=max_workers,
    )

    return {"scraped_topics": data}
