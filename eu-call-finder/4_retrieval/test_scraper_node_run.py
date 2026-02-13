"""Quick manual test runner for the retrieval scraper node.

Run (recommended):
  python eu-call-finder/4_retrieval/test_scraper_node_run.py

Notes:
- This does NOT require a LangGraph graph.
- It just calls the node function directly with a plain dict state.
"""

from __future__ import annotations

import json
import os
import sys


def _ensure_project_on_syspath() -> None:
    """Allow running this file directly from the repo root."""
    this_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(this_dir, ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)


_ensure_project_on_syspath()

# The folder name `4_retrieval` is not a valid Python identifier, so we import by file path.
import importlib.util  # noqa: E402


def _import_scraper_manager():
    this_dir = os.path.dirname(os.path.abspath(__file__))
    module_path = os.path.join(this_dir, "scraper_manager.py")
    spec = importlib.util.spec_from_file_location("scraper_manager", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {module_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


scraper_manager = _import_scraper_manager()

scrape_topics_node = scraper_manager.scrape_topics_node  # type: ignore[attr-defined]


def main() -> None:
    # Minimal state: rely on DEFAULT_SEARCH_TERMS
    state = {
        "headless": False,
        "max_topics": 2,
        # "search_terms": ["Robotics AND AI"],
        "search_query": {
            "bool": {
                "must": [
                    {"terms": {"type": ["1", "2", "8"]}},
                    {"terms": {"status": ["31094501", "31094502"]}},
                    {"term": {"programmePeriod": "2021 - 2027"}},
                ]
            }
        },
    }

    out = scrape_topics_node(state)
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
