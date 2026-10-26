"""Render and compare four identical source pages across three design builds.

The main production site is also built as a control. Only the two Material
variants can reasonably be expected to retain exact HTML/content/search parity.
Zensical Modern is independently graded and must never be silently marked
equivalent when features/search/URL fidelity differ.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from difflib import SequenceMatcher
import json
from pathlib import Path
from urllib.parse import urlsplit

from browser_navigation_pruning import serve_site
from site_accessibility import inspect as axe_inspect

ROOT = Path(__file__).resolve().parents[1]
ROUTES = {
    "home": "",
    "article": "articles/how-to-read-identification-bounds/",
    "guide": "guides/sparse-irregular-fpca/",
    "api": "reference/api/",
}
VARIANTS = {
    "scientific": "Scientific Research Portal (Material)",
    "developer": "Python Developer Docs (Material)",
    "zensical-modern": "Zensical Modern (alternate generator)",
}
BASE_PATH = "/eyetrajectoriespy/"


def inventory(site: Path) -> set[str]:
    return {p.relative_to(site).as_posix() for p in site.rglob("*.html")} if site.is_dir() else set()


def design_browser(browser, site: Path, name: str, evidence: Path) -> dict:
    record: dict = {"name": name, "routes": [], "search": {}, "mobile": {},
                    "accessibility": [], "js_errors": [], "failure": None}
    with serve_site(site) as base:
        for kind, width, height in (("desktop", 1440, 900), ("mobile", 390, 844)):
            page = browser.new_page(
                viewport={"width": width, "height": height},
                reduced_motion="reduce",
                device_scale_factor=1,
            )
            errors: list[str] = []
            page.on("pageerror", lambda exc: errors.append(str(exc)))
            try:
                for label, route in ROUTES.items():
                    resp = page.goto(base + route, wait_until="domcontentloaded", timeout=45000)
                    ok = resp is not None and resp.status == 200
                    h1 = page.locator("h1").first.inner_text(timeout=8000) if ok and page.locator("h1").count() else ""
                    content = page.evaluate("""() => {
                       const node = document.querySelector('.md-content__inner') ||
                         document.querySelector('main article') || document.querySelector('main');
                       return (node?.innerText || '').replace(/\\s+/g, ' ').trim();
                    }""") if ok else ""
                    entry = {"page": label, "viewport": kind,
                             "status": resp.status if resp else None,
                             "title": h1, "text_length": len(content),
                             "text_excerpt": content[:180],
                             "dom_words": len(content.split())}
                    record["routes"].append(entry)
                    if ok:
                        page.screenshot(
                            path=str(evidence / f"{name}-{label}-{kind}.png"),
                            animations="disabled", full_page=False,
                        )
                    if kind == "desktop" and ok and label in ("home", "guide", "api"):
                        record["accessibility"].append(
                            axe_inspect(page, route=route or "home", viewport=f"{name}-desktop")
                        )
                    if kind == "mobile" and ok and label == "home":
                        toggle = page.locator('.md-header__button[for="__drawer"]')
                        try:
                            record["mobile"]["drawer_control_present"] = toggle.is_visible(timeout=3000)
                            if record["mobile"]["drawer_control_present"]:
                                toggle.click(timeout=3000)
                                record["mobile"]["drawer_opens"] = page.locator("input#__drawer").is_checked()
                                page.keyboard.press("Escape")
                        except Exception as exc:
                            record["mobile"]["drawer_error"] = str(exc)[:220]
                if kind == "desktop":
                    page.goto(base, wait_until="domcontentloaded")
                    search = page.locator("input.md-search__input")
                    if search.count():
                        try:
                            search.fill("sparse fpca", timeout=4000)
                            page.locator(".md-search-result__link[href]").first.wait_for(timeout=20000)
                            urls = page.locator(".md-search-result__link[href]").evaluate_all(
                                "(nodes) => nodes.map(n => new URL(n.href).pathname)"
                            )
                            target = BASE_PATH + "guides/sparse-irregular-fpca/"
                            record["search"] = {
                                "input_present": True, "visible_results": len(urls),
                                "canonical_guide_rank": next(
                                    (i + 1 for i, x in enumerate(urls) if x == target), None
                                ),
                                "top_three": urls[:3],
                            }
                        except Exception as exc:
                            record["search"] = {"input_present": True, "error": str(exc)[:220]}
                    else:
                        # Zensical's modern search intentionally replaces
                        # Material/Lunr's markup. Test its documented Ctrl+K
                        # entry path; do not treat an absent Material input
                        # as proof that Zensical search is broken.
                        try:
                            page.keyboard.press("Control+k")
                            field = page.locator(
                                '[role="dialog"] input:visible, input[type="search"]:visible, '
                                '[role="combobox"]:visible'
                            ).first
                            try:
                                field.wait_for(state="visible", timeout=5000)
                            except Exception:
                                trigger = page.get_by_role("button", name="Search").first
                                trigger.click(timeout=3000)
                                field.wait_for(state="visible", timeout=5000)
                            field.fill("sparse fpca")
                            page.wait_for_timeout(1300)
                            urls = page.locator(
                                '[role="dialog"] a[href]:visible, '
                                '[data-md-component="search-result"] a[href]:visible'
                            ).evaluate_all(
                                "(nodes) => nodes.map(n => new URL(n.href).pathname)"
                            )
                            target = BASE_PATH + "guides/sparse-irregular-fpca/"
                            record["search"] = {
                                "input_present": True,
                                "search_engine": "modern-dialog",
                                "visible_results": len(urls),
                                "canonical_guide_rank": next(
                                    (i + 1 for i, x in enumerate(urls) if x == target), None
                                ),
                                "top_three": urls[:3],
                            }
                        except Exception as exc:
                            record["search"] = {
                                "input_present": False, "search_engine": "modern-dialog",
                                "status": "unverified",
                                "error": str(exc)[:280],
                            }
            except Exception as exc:
                record["failure"] = str(exc)[:650]
            finally:
                record["js_errors"] += errors[:8]
                page.close()
    return record


def compare(base: Path, candidate: Path, record: dict) -> dict:
    source = inventory(base)
    target = inventory(candidate)
    issues: list[str] = []
    if not source:
        raise ValueError("Missing production baseline")
    if not target:
        issues.append("Candidate did not build any HTML output")
    missing = sorted(source - target)
    new = sorted(target - source)
    if missing:
        issues.append(f"Candidate misses {len(missing)} baseline routes")
    page_results = record.get("routes", [])
    for route in ROUTES:
        for viewport in ("desktop", "mobile"):
            entry = next((e for e in page_results if e["page"] == route and e["viewport"] == viewport), None)
            if not entry or entry["status"] != 200 or not entry["title"]:
                issues.append(f"{route}:{viewport} missing title or HTTP 200")
    if record.get("failure"):
        issues.append(record["failure"])
    if record.get("js_errors"):
        issues.append(f"{len(record['js_errors'])} JavaScript errors")
    serious = sum(r.get("highImpact", 0) for r in record.get("accessibility", []))
    if serious:
        issues.append(f"{serious} high-impact axe finding(s) in sampled pages")
    if not record.get("mobile", {}).get("drawer_opens"):
        issues.append("Mobile drawer did not open in browser")
    if record.get("search", {}).get("canonical_guide_rank") is None:
        issues.append("Canonical sparse-FPCA guide not found by live search")
    return {
        "baseline_pages": len(source), "preview_pages": len(target),
        "missing_pages": len(missing), "extra_pages": len(new),
        "missing_sample": missing[:12], "issues": issues,
        "sampled_axe_high_impact": serious,
        "readiness": "pass" if not issues else "review",
    }


def make_contact_sheet(evidence: Path) -> None:
    from PIL import Image, ImageDraw, ImageFont
    width, height, label_h, gap = 800, 500, 55, 24
    margin = 35
    sheet = Image.new("RGB", (margin * 2 + 3 * width + 2 * gap,
                               margin * 2 + 4 * (height + label_h) + 3 * gap + 40), "#e9edf2")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for column, name in enumerate(VARIANTS):
        x = margin + column * (width + gap)
        draw.text((x+10, 12), VARIANTS[name], fill="#15263d", font=font)
        for row, label in enumerate(ROUTES):
            y = margin + 40 + row * (height + label_h + gap)
            draw.rounded_rectangle((x, y, x + width, y + height + label_h), 12, fill="#ffffff")
            draw.text((x + 15, y + 9), label.upper(), font=font, fill="#253f59")
            image_path = evidence / f"{name}-{label}-desktop.png"
            if image_path.exists():
                with Image.open(image_path) as im:
                    im = im.convert("RGB")
                    im.thumbnail((width - 18, height - 12))
                    sheet.paste(im, (x+9, y+label_h))
            else:
                draw.text((x+15,y+90),"BUILD OR BROWSER PREVIEW UNAVAILABLE",font=font,fill="#a02830")
    sheet.save(evidence / "comparison-desktop-4-pages.png", optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", default="site")
    parser.add_argument("--directory", default="build/design-previews")
    args = parser.parse_args()
    baseline = (ROOT / args.baseline).resolve()
    directory = (ROOT / args.directory).resolve()
    output = directory / "evidence"
    output.mkdir(parents=True, exist_ok=True)
    report: dict = {
        "baseline": str(baseline), "variants": {}, "pages": ROUTES,
        "production_change": False,
        "limitations": [
            "Design preference is assessed by reviewing actual screenshot evidence, not fabricated UX scores.",
            "axe-core is an automated screen; human screen-reader review remains open.",
            "Browser checks cover four equal source pages; a Zensical production migration requires whole-site/plugin equivalence.",
            "Search reflects Material/Zensical actual local UI for a single sample query.",
        ],
    }
    from playwright.sync_api import sync_playwright
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, args=["--disable-dev-shm-usage"])
        try:
            for name in VARIANTS:
                site = directory / name
                if not (site / "index.html").is_file():
                    report["variants"][name] = {
                        "name": VARIANTS[name], "status": "build-unavailable",
                        "comparison": {"issues": ["No generated homepage"], "readiness": "review"},
                    }
                    continue
                browser_record = design_browser(browser, site, name, output)
                report["variants"][name] = {
                    "name": VARIANTS[name], "status": "built",
                    "browser": browser_record,
                    "comparison": compare(baseline, site, browser_record),
                }
        finally:
            browser.close()
    make_contact_sheet(output)
    (directory / "design-comparison.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for name, entry in report["variants"].items():
        comparison = entry.get("comparison", {})
        print(f"{name}: {entry['status']}; {comparison.get('readiness')} — "
              f"{comparison.get('preview_pages','?')} pages; issues={comparison.get('issues')}")
    print(f"Screenshots and four-page contact sheet: {output}")
    if any(report["variants"].get(name, {}).get("status") != "built"
           for name in ("scientific", "developer")):
        raise AssertionError("Both same-engine design variants must produce screenshots")


if __name__ == "__main__":
    main()
