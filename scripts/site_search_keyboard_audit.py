"""Browser-observed search relevance and keyboard-only smoke test.

Run under the site's true GitHub Pages prefix. Results are *observed search
positions*, not claims about opaque ranking internals or human user testing.
Automated focus/axe checks do not substitute for a manual screen-reader review.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from browser_navigation_pruning import serve_site
from site_accessibility import inspect as audit_accessibility

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build/site-search-keyboard"
INTENTS = (
    {"query": "SyeLink", "target": "/integrations/syelink-handoff/", "max_rank": 12},
    {"query": "first analysis", "target": "/start/first-analysis/", "max_rank": 12},
    {"query": "cite software", "target": "/start/cite-and-reproduce/", "max_rank": 20},
    {"query": "sparse fpca", "target": "/guides/sparse-irregular-fpca/", "max_rank": 20},
    {"query": "research evidence", "target": "/research/", "max_rank": 20},
)


def target_rank(page, origin: str, target: str) -> tuple[int | None, int | None, list[str]]:
    links = page.locator(".md-search-result__link[href]")
    urls = links.evaluate_all("(nodes) => nodes.map(n => n.href)")
    paths = [urlsplit(urljoin(origin, url)).path for url in urls]
    suffix = "/eyetrajectoriespy" + target
    ranks = [i + 1 for i, path in enumerate(paths) if path == suffix]
    # Material may emit multiple heading snippets from the same URL. Report
    # both the raw result rank and the unique-page rank, not just a number
    # inflated by identical destination URLs.
    distinct = list(dict.fromkeys(paths))
    page_ranks = [i + 1 for i, path in enumerate(distinct) if path == suffix]
    return (min(ranks) if ranks else None), (min(page_ranks) if page_ranks else None), paths[:25]


def run(site: Path) -> dict:
    from playwright.sync_api import sync_playwright

    OUT.mkdir(parents=True, exist_ok=True)
    report = {"intents": [], "keyboard": {}, "accessibility": [],
              "failures": [], "status": "fail",
              "limits": ["Rank = visible Material browser result position for tested query; no guarantee of future ranking.",
                         "No manual screen-reader or keyboard-only user study performed."]}
    try:
        with serve_site(site) as origin, sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, args=["--disable-dev-shm-usage"])
            try:
                desktop = browser.new_page(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
                desktop.goto(origin + "start/find-a-topic/", wait_until="domcontentloaded")
                assert desktop.locator(".md-content h1").inner_text().startswith("Find the right"), "Topic index missing"
                assert desktop.locator('.md-content a[href*="sparse-irregular-fpca"]').count() >= 1
                report["accessibility"].append(
                    audit_accessibility(desktop, route="start/find-a-topic/", viewport="desktop")
                )
                # Search queries must execute in a real browser, never inferred
                # from words present somewhere in search_index.json.
                for intent in INTENTS:
                    desktop.goto(origin, wait_until="domcontentloaded")
                    field = desktop.locator("input.md-search__input")
                    field.fill(intent["query"])
                    desktop.locator(".md-search-result__link[href]").first.wait_for(timeout=30000)
                    rank, page_rank, sample = target_rank(desktop, origin, intent["target"])
                    record = {**intent, "rank": rank, "distinct_page_rank": page_rank, "visible_result_count": len(sample),
                              "top_five_paths": sample[:5]}
                    report["intents"].append(record)
                    assert rank is not None and rank <= intent["max_rank"], (
                        f"Intent {intent['query']!r}: target {intent['target']!r} rank "
                        f"{rank}, allowed first {intent['max_rank']}; results={sample[:15]}"
                    )

                # Use real keys for shortcut, focus, result activation, Escape,
                # not a synthetic click pretending to be keyboard navigation.
                desktop.goto(origin, wait_until="domcontentloaded")
                desktop.keyboard.press("Tab")
                first_focus = desktop.evaluate(
                    "() => ({tag:document.activeElement?.tagName, "
                    "href:document.activeElement?.getAttribute('href')})"
                )
                report["keyboard"]["first_tab_focus"] = first_focus
                assert first_focus["tag"] == "A", "Tab did not reach an actual link"
                desktop.keyboard.press("Escape")
                desktop.keyboard.press("/")
                desktop.wait_for_function(
                    "() => document.activeElement?.classList.contains('md-search__input')",
                    timeout=10000,
                )
                report["keyboard"]["slash_focuses_search"] = True
                desktop.keyboard.type("SyeLink")
                desktop.locator('.md-search-result__link[href*="syelink-handoff"]').first.wait_for(timeout=30000)
                desktop.keyboard.press("ArrowDown")
                desktop.keyboard.press("Enter")
                desktop.wait_for_function(
                    "() => location.pathname !== '/eyetrajectoriespy/'", timeout=12000
                )
                report["keyboard"]["down_enter_opens_result"] = desktop.url
                desktop.goto(origin, wait_until="domcontentloaded")
                desktop.keyboard.press("/")
                desktop.keyboard.type("SyeLink")
                desktop.locator('.md-search-result__link[href*="syelink-handoff"]').first.wait_for(timeout=30000)
                report["accessibility"].append(
                    audit_accessibility(desktop, route="search-overlay", viewport="desktop")
                )
                desktop.keyboard.press("Escape")
                close_state = desktop.evaluate(
                    "() => ({focused: document.activeElement?.classList.contains('md-search__input'), "
                    "value: document.querySelector('input.md-search__input')?.value, "
                    "visibleResults: [...document.querySelectorAll('.md-search-result__link')].filter("
                    "node => node.getClientRects().length).length})"
                )
                report["keyboard"]["escape_state"] = close_state
                assert not close_state["focused"] or not close_state["value"], (
                    "Escape did not close or clear the search control"
                )
                desktop.screenshot(path=str(OUT / "search-keyboard-desktop.png"),
                                   animations="disabled")
                desktop.close()

                mobile = browser.new_page(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
                mobile.goto(origin + "start/find-a-topic/", wait_until="domcontentloaded")
                assert mobile.locator('.md-content a[href*="sparse-irregular-fpca"]').count() > 0
                report["accessibility"].append(
                    audit_accessibility(mobile, route="start/find-a-topic/", viewport="mobile")
                )
                # Native drawer is still operated by its visible toggle. This
                # automation does not claim that a screen reader can operate it.
                mobile.locator('.md-header__button[for="__drawer"]').click()
                assert mobile.locator("input#__drawer").is_checked()
                report["keyboard"]["mobile_drawer_opens"] = True
                mobile.screenshot(path=str(OUT / "topic-mobile.png"),
                                  animations="disabled")
                mobile.close()
            finally:
                browser.close()
        if any(item["highImpact"] for item in report["accessibility"]):
            raise AssertionError("Axe found serious/critical findings in search/topic samples")
        report["status"] = "pass"
    except Exception as exc:
        report["failures"].append(str(exc))
        raise
    finally:
        (OUT / "search-keyboard-report.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--site", default="site")
    a = p.parse_args()
    print(json.dumps(run((ROOT / a.site).resolve()), indent=2))


if __name__ == "__main__":
    main()
