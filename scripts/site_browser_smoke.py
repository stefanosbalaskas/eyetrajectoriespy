"""Render and smoke-test the built MkDocs site at its true Pages subpath.

This is a local browser UX audit, not full accessibility or pixel-level
parity testing. Screenshots use existing source-derived scientific SVGs.
Requires Python playwright and the chromium browser installation.
"""
from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading

from site_accessibility import inspect as audit_accessibility

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build/site-browser-audit"
BASE = "/eyetrajectoriespy/"


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass


def run(site: Path) -> dict:
    from playwright.sync_api import sync_playwright
    assert (site / "tools/figure-storyboard/index.html").is_file(), "Build docs before visual audit"
    root = OUT / "webroot"
    root.mkdir(parents=True, exist_ok=True)
    prefix = root / "eyetrajectoriespy"
    if prefix.is_symlink():
        prefix.unlink()
    elif prefix.exists():
        raise RuntimeError("Browser test prefix must be absent or a removable symlink")
    prefix.symlink_to(site.resolve(), target_is_directory=True)
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(root)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    origin = f"http://127.0.0.1:{server.server_port}{BASE}"
    report = {"url_prefix": BASE, "desktop_gallery_count": 0, "filtered_count": None,
              "mobile_gallery_count": 0, "images_loaded": 0, "screenshots": [], "failures": [], "accessibility": []}
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, args=["--disable-dev-shm-usage"])
            try:
                for kind, viewport in (
                    ("desktop", {"width": 1440, "height": 900}),
                    ("mobile", {"width": 390, "height": 844}),
                ):
                    page = browser.new_page(viewport=viewport, device_scale_factor=1)
                    errors = []
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    response = page.goto(origin + "tools/figure-storyboard/", wait_until="domcontentloaded")
                    assert response and response.status == 200, f"gallery HTML missing: {kind}"
                    page.locator(".et-story-card").first.wait_for(timeout=20000)
                    count = page.locator(".et-story-card").count()
                    assert count == 12, f"Expected 12 scientific figure cards, got {count}"
                    # Offscreen images are lazy by design. Trigger their fetches
                    # for this audit rather than treating unopened cards as broken.
                    page.locator(".et-story-card img").evaluate_all(
                        "(nodes) => nodes.forEach(img => { img.loading = 'eager'; })"
                    )
                    page.wait_for_function(
                        "() => [...document.querySelectorAll('.et-story-card img')].every(i => i.complete && i.naturalWidth > 0)",
                        timeout=20000,
                    )
                    report["images_loaded"] = 12
                    if kind == "desktop":
                        report["desktop_gallery_count"] = count
                        page.select_option("#et-story-topic", "fpca")
                        page.wait_for_timeout(100)
                        visible = page.locator(".et-story-card:visible").count()
                        assert visible == 2, f"FPCA filter should show two cards, got {visible}"
                        report["filtered_count"] = visible
                        page.select_option("#et-story-topic", "all")
                    else:
                        report["mobile_gallery_count"] = count
                    shot = OUT / f"{kind}-figure-storyboard.png"
                    page.screenshot(path=str(shot), full_page=True, animations="disabled")
                    report["screenshots"].append(shot.name)
                    report["accessibility"].append(audit_accessibility(page, route="tools/figure-storyboard/", viewport=kind))
                    assert not errors, f"{kind} gallery page JS errors: {errors}"
                    page.close()
                page = browser.new_page(viewport={"width": 1440, "height": 900})
                page.goto(origin + "start/first-analysis/", wait_until="domcontentloaded")
                assert "first" in page.locator("h1").inner_text().lower()
                assert page.locator('a[href*="figure-storyboard"]').count() >= 1
                shot = OUT / "desktop-first-analysis.png"
                page.screenshot(path=str(shot), full_page=True, animations="disabled")
                report["screenshots"].append(shot.name)
                report["accessibility"].append(audit_accessibility(page, route="start/first-analysis/", viewport="desktop"))
                page.goto(origin + "integrations/navigator/", wait_until="domcontentloaded")
                page.locator("#et-package-grid article").first.wait_for(timeout=20000)
                assert page.locator("#et-package-grid article").count() == 14
                page.select_option("#et-package-phase", "preview")
                assert 1 < page.locator("#et-package-grid article").count() < 14
                report["accessibility"].append(audit_accessibility(page, route="integrations/navigator/", viewport="desktop"))
                page.goto(origin + "start/cite-and-reproduce/", wait_until="domcontentloaded")
                assert page.locator("h1").count() >= 1
                report["accessibility"].append(audit_accessibility(page, route="start/cite-and-reproduce/", viewport="desktop"))
                page.goto(origin, wait_until="domcontentloaded")
                assert page.locator("h1").count() >= 1
                report["accessibility"].append(audit_accessibility(page, route="home", viewport="desktop"))
                page.close()
            finally:
                browser.close()
    except Exception as exc:
        report["failures"].append(str(exc))
        raise
    finally:
        server.shutdown()
        server.server_close()
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "browser-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    # The preview workflow is non-deploying. Surface high-severity findings in
    # the report rather than falsely certifying accessibility.
    report["high_impact_total"] = sum(item["highImpact"] for item in report["accessibility"])
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", default="site")
    args = parser.parse_args()
    print(json.dumps(run((ROOT / args.site).resolve()), indent=2))


if __name__ == "__main__":
    main()
