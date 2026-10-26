"""Desktop header overflow and mobile-navigation regression for MkDocs Material.

Tests the actual compiled site with its GitHub Pages /eyetrajectoriespy/
prefix. The original 16 navigation tabs overflowed a 1545px desktop capture.
The compact configuration must preserve access while fitting the visible row.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from browser_navigation_pruning import serve_site

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_TABS = (
    "Home", "Start here", "Explore", "Integrations", "Workflows",
    "Guides", "Research", "Figures", "News", "API", "Releases", "About",
)
SITE_ROUTES = (
    "development/website-quality/",
    "development/sitewide-experience-audit/",
    "development/accessibility-manual-review/",
    "development/zensical-preview/",
    "contributing/",
)


def audit(site: Path, output: Path) -> dict:
    from playwright.sync_api import sync_playwright

    output.mkdir(parents=True, exist_ok=True)
    report: dict = {"desktop": [], "mobile": [], "page_routes": [],
                    "status": "fail", "errors": [],
                    "limitations": [
                        "Measurements use a headless Chromium layout, not manual UX testing.",
                        "Tests the responsive tab bar, not every assistive technology or zoom level.",
                    ]}
    try:
        with serve_site(site) as origin, sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True, args=["--disable-dev-shm-usage"])
            try:
                for width in (1250, 1280, 1366, 1440, 1545, 1920):
                    page = browser.new_page(
                        viewport={"width": width, "height": 900},
                        reduced_motion="reduce",
                    )
                    response = page.goto(origin, wait_until="domcontentloaded")
                    assert response and response.status == 200, f"{width}: homepage failed"
                    result = page.evaluate("""() => {
                      const tabs = document.querySelector(".md-tabs");
                      const inner = document.querySelector(".md-tabs__inner");
                      const entries = [...document.querySelectorAll(".md-tabs__link")];
                      const repo = document.querySelector(".md-source__repository");
                      if (!tabs || !inner) throw new Error("Desktop tab controls missing");
                      const box = inner.getBoundingClientRect();
                      const rects = entries.map(el => el.getBoundingClientRect());
                      return {
                        labels: entries.map(el => el.textContent.trim().replace(/\\s+/g, " ")),
                        is_visible: getComputedStyle(tabs).display !== "none",
                        inner_width: inner.clientWidth,
                        inner_scroll_width: inner.scrollWidth,
                        first_left: rects[0]?.left,
                        last_right: rects[rects.length - 1]?.right,
                        container_left: box.left,
                        container_right: box.right,
                        repo_text: repo?.textContent?.trim() || null,
                        repo_overflow: repo ? repo.scrollWidth > repo.clientWidth + 2 : null,
                        body_scroll_width: document.documentElement.scrollWidth,
                        window_width: innerWidth
                      };
                    }""")
                    result["viewport_width"] = width
                    report["desktop"].append(result)
                    assert result["is_visible"], f"{width}: desktop tabs unexpectedly hidden"
                    assert result["labels"] == list(EXPECTED_TABS), (
                        f"{width}: missing/reordered top level tabs: {result['labels']}"
                    )
                    assert result["inner_scroll_width"] <= result["inner_width"] + 2, (
                        f"{width}: horizontally overflowing tabs"
                    )
                    assert result["first_left"] >= result["container_left"] - 2, (
                        f"{width}: leftmost tab clipped"
                    )
                    assert result["last_right"] <= result["container_right"] + 2, (
                        f"{width}: rightmost tab clipped"
                    )
                    assert result["repo_text"] == "Source on GitHub", (
                        f"{width}: repository label not compact"
                    )
                    assert result["repo_overflow"] is False, (
                        f"{width}: repository label truncated"
                    )
                    assert result["body_scroll_width"] <= width + 2, (
                        f"{width}: viewport horizontal scrollbar"
                    )
                    if width in (1280, 1545):
                        page.screenshot(
                            path=str(output / f"desktop-header-{width}.png"),
                            animations="disabled",
                        )
                    page.close()

                for width in (390, 820, 1150):
                    page = browser.new_page(
                        viewport={"width": width, "height": 844},
                        reduced_motion="reduce",
                    )
                    response = page.goto(origin, wait_until="domcontentloaded")
                    assert response and response.status == 200
                    hidden = not page.locator(".md-tabs").is_visible()
                    button = page.locator('.md-header__button[for="__drawer"]')
                    assert hidden, f"{width}: desktop tab list unexpectedly visible"
                    assert button.is_visible(), f"{width}: mobile menu control hidden"
                    button.click()
                    assert page.locator("input#__drawer").is_checked(), (
                        f"{width}: mobile drawer failed to open"
                    )
                    assert page.locator(".md-sidebar--primary .md-nav__link").count() > 0, (
                        f"{width}: empty mobile section navigation"
                    )
                    report["mobile"].append(
                        {"viewport_width": width, "tabs_hidden": hidden, "drawer_opened": True}
                    )
                    if width == 390:
                        page.screenshot(
                            path=str(output / "mobile-drawer-390.png"),
                            animations="disabled",
                        )
                    page.close()

                page = browser.new_page(viewport={"width": 1440, "height": 900})
                for route in SITE_ROUTES:
                    response = page.goto(origin + route, wait_until="domcontentloaded")
                    status = response.status if response else None
                    report["page_routes"].append({"route": route, "http_status": status})
                    assert status == 200, f"Preserved documentation route broken: {route}"
                page.close()
            finally:
                browser.close()
        report["status"] = "pass"
    except Exception as exc:
        report["errors"].append(str(exc))
        raise
    finally:
        (output / "header-layout-report.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", default="site")
    parser.add_argument("--output", default="build/header-layout")
    args = parser.parse_args()
    result = audit(Path(args.site).resolve(), Path(args.output).resolve())
    print(json.dumps({"result": result["status"],
                      "desktop": len(result["desktop"]),
                      "mobile": len(result["mobile"]),
                      "routes": len(result["page_routes"])}, indent=2))


if __name__ == "__main__":
    main()
