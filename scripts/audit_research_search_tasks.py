"""Observe real Material search results for a curated scientific-task benchmark.

Core cases fail closed at established rank limits. Additional researcher tasks
provide *reported* headroom metrics and failure examples, not an unearned
claim of global relevance. All browsing remains on the localhost Pages mirror.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlsplit

from browser_navigation_pruning import serve_site

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SPEC = ROOT / "scripts/site_search_tasks.json"
DEFAULT_REPORT = ROOT / "build/site-search-task-benchmark.json"
PREFIX = "/eyetrajectoriespy/"


def load_cases(spec: Path, site: Path) -> list[dict]:
    payload = json.loads(spec.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError("Unsupported research task schema")
    cases = payload.get("cases")
    if not isinstance(cases, list) or len(cases) < 20:
        raise ValueError("Research benchmark must cover at least 20 real tasks")
    seen_ids: set[str] = set()
    seen_queries: set[str] = set()
    for case in cases:
        if not all(isinstance(case.get(field), str) and case[field].strip()
                   for field in ("id", "category", "query", "target", "tier")):
            raise ValueError(f"Malformed task: {case}")
        if case["tier"] not in ("regression", "exploratory"):
            raise ValueError(f"Unknown task tier: {case}")
        if case["id"] in seen_ids or case["query"].casefold() in seen_queries:
            raise ValueError(f"Duplicate benchmark identity or query: {case}")
        if not case["target"].startswith("/") or not case["target"].endswith("/") or ".." in case["target"]:
            raise ValueError(f"Unsafe/canonical destination: {case}")
        target = site / case["target"].strip("/") / "index.html"
        if not target.is_file():
            raise ValueError(f"Expected research topic route missing from build: {target}")
        if not isinstance(case.get("max_rank"), int) or case["max_rank"] < 1:
            raise ValueError(f"Invalid regression rank threshold: {case}")
        seen_ids.add(case["id"])
        seen_queries.add(case["query"].casefold())
    if sum(c["tier"] == "regression" for c in cases) != 5:
        raise ValueError("Preserve exactly five original independent regression controls")
    if len({c["category"] for c in cases}) < 5:
        raise ValueError("Benchmark must span at least five scientific reader tasks")
    return cases


def target_rank(page, target: str) -> tuple[int | None, int | None, list[str]]:
    urls = page.locator(".md-search-result__link[href]").evaluate_all(
        "(elements) => elements.map(element => element.href)"
    )
    routes = [urlsplit(url).path for url in urls]
    unique_routes = list(dict.fromkeys(routes))
    canonical = PREFIX.rstrip("/") + target
    raw = next((i + 1 for i, route in enumerate(routes) if route == canonical), None)
    unique = next((i + 1 for i, route in enumerate(unique_routes) if route == canonical), None)
    return raw, unique, unique_routes[:10]


def summary(rows: list[dict]) -> dict:
    counts: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        counts[row["category"]].append(row)

    def aggregate(items: list[dict]) -> dict:
        total = len(items)
        ranks = [row["distinct_page_rank"] for row in items]
        return {
            "tasks": total,
            "found_in_observed_results": sum(rank is not None for rank in ranks),
            "hit_at_1": round(sum(rank is not None and rank <= 1 for rank in ranks) / total, 4),
            "hit_at_3": round(sum(rank is not None and rank <= 3 for rank in ranks) / total, 4),
            "hit_at_5": round(sum(rank is not None and rank <= 5 for rank in ranks) / total, 4),
            "hit_at_10": round(sum(rank is not None and rank <= 10 for rank in ranks) / total, 4),
            "mrr_observed": round(sum(1 / rank for rank in ranks if rank) / total, 4),
        }

    return {
        "all": aggregate(rows),
        "regression": aggregate([row for row in rows if row["tier"] == "regression"]),
        "exploratory": aggregate([row for row in rows if row["tier"] == "exploratory"]),
        "by_category": {category: aggregate(items) for category, items in sorted(counts.items())},
    }


def run(site: Path, spec: Path, output: Path) -> dict:
    from playwright.sync_api import sync_playwright

    cases = load_cases(spec, site)
    report: dict = {
        "schema_version": 1, "status": "fail", "records": [], "metrics": {},
        "regression_failures": [], "limitations": [
            "Observed browser results only. No real-user task completion or source relevance judgments.",
            "Distinct URL rank groups many heading snippets from one page; raw rank is separately recorded.",
            "Exploratory tasks are diagnostic, not yet an enforced quality threshold.",
            "No collected user queries, telemetry, external search service or search request logs.",
        ],
    }
    try:
        with serve_site(site) as origin, sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, args=["--disable-dev-shm-usage"])
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
                for case in cases:
                    response = page.goto(origin, wait_until="domcontentloaded")
                    if response is None or response.status != 200:
                        raise RuntimeError("Failed to open local documentation homepage")
                    field = page.locator("input.md-search__input")
                    field.fill(case["query"])
                    # A result's mere existence doesn't prove its intended URL
                    # is present; inspect browser-rendered search results directly.
                    page.locator(".md-search-result__link[href]").first.wait_for(timeout=30000)
                    raw, unique, top = target_rank(page, case["target"])
                    row = {**case, "result_rank": raw, "distinct_page_rank": unique,
                           "top_ten_distinct_destinations": top}
                    report["records"].append(row)
                    if case["tier"] == "regression" and (
                        unique is None or unique > case["max_rank"]
                    ):
                        report["regression_failures"].append(
                            {"task": case["id"], "expected": case["target"],
                             "rank": unique, "bound": case["max_rank"]}
                        )
                page.close()
            finally:
                browser.close()
        report["metrics"] = summary(report["records"])
        report["status"] = "pass" if not report["regression_failures"] else "review"
    finally:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if report["status"] != "pass":
        raise AssertionError(f"Search regression failures: {report['regression_failures']}")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", default="site")
    parser.add_argument("--spec", default=str(DEFAULT_SPEC))
    parser.add_argument("--output", default=str(DEFAULT_REPORT))
    a = parser.parse_args()
    report = run(Path(a.site).resolve(), Path(a.spec), Path(a.output))
    print(json.dumps({"status": report["status"],
                      "metrics": report["metrics"],
                      "regression_failures": report["regression_failures"],
                      "exploratory_misses": [
                          (r["id"], r["query"], r["target"])
                          for r in report["records"]
                          if r["tier"] == "exploratory" and r["distinct_page_rank"] is None
                      ]}, indent=2))


if __name__ == "__main__":
    main()
