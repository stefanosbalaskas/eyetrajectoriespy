"""Browser-check both Material navigation modes on the real Pages URL prefix.

This experiment does not deploy either build. It tests desktop/mobile paths,
instant navigation from search, section landing-page discoverability, a mobile
drawer/keyboard interaction, and locally scanned serious a11y findings.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import tempfile
import threading

from site_accessibility import inspect as axe_inspect

ROOT = Path(__file__).resolve().parents[1]
ROUTES = (
    "start/first-analysis/",
    "guides/",
    "guides/sparse-multivariate-fpca/",
    "tutorials/",
    "workflows/",
    "research/",
    "reference/api/",
    "integrations/navigator/",
)
PREFIX = "/eyetrajectoriespy/"


class SilentHandler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass


@contextmanager
def serve_site(site: Path):
    with tempfile.TemporaryDirectory(prefix="nav-pruning-") as tmp:
        root = Path(tmp)
        (root / "eyetrajectoriespy").symlink_to(site.resolve(), target_is_directory=True)
        server = ThreadingHTTPServer(
            ("127.0.0.1", 0), partial(SilentHandler, directory=str(root))
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}{PREFIX}"
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


def inspect_browser(browser, site: Path, label: str, output: Path) -> dict:
    checks = {"build": label, "routes": [], "mobile": {}, "search": False,
              "section_gateway": False, "a11y": [], "errors": []}
    with serve_site(site) as origin:
        for kind, viewport in (("desktop", {"width": 1440, "height": 900}),
                               ("mobile", {"width": 390, "height": 844})):
            page = browser.new_page(viewport=viewport, reduced_motion="reduce")
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            try:
                for path in ROUTES:
                    response = page.goto(origin + path, wait_until="domcontentloaded")
                    assert response and response.status == 200, (label, kind, path, "HTTP")
                    assert page.locator(".md-content h1").count() >= 1, (label, kind, path, "heading")
                    if kind == "desktop":
                        checks["routes"].append(path)
                # A user should be able to reach a deep guide from its section
                # landing page, even when its nested sidebar is collapsed.
                page.goto(origin + "guides/", wait_until="domcontentloaded")
                gateway = page.locator(".md-content a[href*='sparse-multivariate-fpca']").first
                assert gateway.count() == 1, (label, kind, "guide gateway absent")
                gateway.click()
                page.wait_for_url("**/guides/sparse-multivariate-fpca/", timeout=15000)
                checks["section_gateway"] = True

                # Exercises Material's live search index, and instant navigation.
                page.goto(origin + "start/first-analysis/", wait_until="domcontentloaded")
                page.locator("input.md-search__input").fill("SyeLink")
                result = page.locator(
                    '.md-search-result__link[href*="syelink-handoff"]'
                ).first
                result.wait_for(timeout=30000)
                result.click()
                page.wait_for_url("**/integrations/syelink-handoff/*", timeout=15000)
                checks["search"] = True

                # Accessibility audit is local and does not assert WCAG conformance.
                page.goto(origin + "guides/", wait_until="domcontentloaded")
                checks["a11y"].append(axe_inspect(page, route="guides/", viewport=kind))
                if kind == "desktop":
                    assert page.locator(".md-sidebar--primary a[href]").count() > 0, (
                        label, "desktop navigation unexpectedly missing"
                    )
                else:
                    # The mobile navigation drawer must remain keyboard operable.
                    page.locator('.md-header__button[for="__drawer"]').click()
                    drawer = page.locator("input#__drawer")
                    assert drawer.is_checked(), (label, "mobile navigation drawer did not open")
                    assert page.locator(".md-sidebar--primary a[href]").count() > 0, (
                        label, "mobile navigation empty"
                    )
                    page.keyboard.press("Escape")
                    checks["mobile"]["drawer_opened"] = True
                shot = output / f"{label}-{kind}-guides.png"
                page.screenshot(path=str(shot), full_page=False, animations="disabled")
                checks["mobile"]["guide_screenshot"] = shot.name if kind == "mobile" else checks["mobile"].get("guide_screenshot")
                assert not errors, (label, kind, errors[:5])
            except Exception as exc:
                checks["errors"].append(f"{kind}: {exc}")
                raise
            finally:
                page.close()
    checks["high_impact"] = sum(r["highImpact"] for r in checks["a11y"])
    if checks["high_impact"]:
        raise AssertionError(f"{label}: {checks['high_impact']} serious/critical axe results")
    return checks


def main() -> None:
    from playwright.sync_api import sync_playwright

    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", default="build/navigation-baseline-site")
    parser.add_argument("--candidate", default="build/navigation-prune-site")
    parser.add_argument("--output", default="build/navigation-prune-browser.json")
    a = parser.parse_args()
    out = Path(a.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    report: dict = {"checks": [], "result": "fail"}
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True, args=["--disable-dev-shm-usage"]
            )
            try:
                for label, path in (("baseline", a.baseline), ("pruned", a.candidate)):
                    report["checks"].append(
                        inspect_browser(browser, Path(path), label, out.parent)
                    )
            finally:
                browser.close()
        report["result"] = "pass"
    finally:
        out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
