"""Qualification gate for proposed Scientific Research Portal production style.

This is an exact-source MkDocs Material candidate build. Record four route
screenshots on desktop/mobile in light/dark, check scientific content,
navigation, search, API label contrast and sampled axe. Not human WCAG proof.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit

from browser_navigation_pruning import serve_site
from site_accessibility import inspect as axe_inspect

ROOT = Path(__file__).resolve().parents[1]
PAGES = {
    "home": "",
    "article": "articles/how-to-read-identification-bounds/",
    "guide": "guides/sparse-irregular-fpca/",
    "api": "reference/api/",
}
REPO_BASE = "/eyetrajectoriespy/"
OUT = ROOT / "build/scientific-portal-qualification"


def audit(site: Path, output: Path) -> dict:
    from playwright.sync_api import sync_playwright
    output.mkdir(parents=True, exist_ok=True)
    report: dict = {
        "scheme_checks": [], "search": None,
        "routes": [], "screenshots": [], "issues": [],
        "status": "fail",
        "limitations": [
            "Automated axe-core is not complete WCAG or screen-reader conformance.",
            "Comparison is on the local repository path, not deployed Pages.",
            "Perceptual aesthetics require human design review.",
        ],
    }
    try:
        paths = {p.relative_to(site).as_posix() for p in site.rglob("*.html")}
        assert len(paths) >= 370, f"Unexpected loss of documentation pages: {len(paths)}"
        assert (site / "assets/site-design-scientific-portal.css").is_file(), "Style was not copied"
        report["page_count"] = len(paths)
        with serve_site(site) as origin, sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, args=["--disable-dev-shm-usage"])
            try:
                for scheme in ("light", "dark"):
                    for device, width, height in (("desktop", 1440, 900), ("mobile", 390, 844)):
                        context = browser.new_context(
                            viewport={"width": width, "height": height},
                            color_scheme=scheme, reduced_motion="reduce",
                        )
                        page = context.new_page()
                        errors: list[str] = []
                        page.on("pageerror", lambda err: errors.append(str(err)))
                        for name, route in PAGES.items():
                            resp = page.goto(origin + route, wait_until="domcontentloaded")
                            assert resp and resp.status == 200, (scheme, device, name, "HTTP 200")
                            assert page.locator("h1").first.is_visible(), (scheme, device, name, "h1")
                            bounds = page.evaluate("""() => ({
                              viewport: innerWidth, scroll: document.documentElement.scrollWidth,
                              theme: document.body?.getAttribute('data-md-color-scheme'),
                              hasStyle: [...document.styleSheets].some(s => (s.href || '').includes('site-design-scientific-portal')),
                            })""")
                            assert bounds["hasStyle"], (scheme, name, "stylesheet not loaded")
                            assert bounds["scroll"] <= width + 3, (scheme,device,name,"horizontal overflow", bounds)
                            result = {"scheme":scheme,"device":device,"page":name,"theme":bounds["theme"],
                                      "response":resp.status, "horizontal_overflow":False}
                            report["routes"].append(result)
                            shot = output / f"{name}-{device}-{scheme}.png"
                            page.screenshot(path=str(shot), animations="disabled")
                            report["screenshots"].append(shot.name)
                            # Capture API contrast diagnostic BEFORE axe can raise.
                            # This identifies specificity, palette scope or CSS-asset
                            # problems instead of blindly changing color declarations.
                            if name == "api" and device == "desktop":
                                diagnostic = page.evaluate("""() => {
                                  const node = document.querySelector('.doc-labels.doc code');
                                  if (!node) return {error: 'mkdocstrings code node missing'};
                                  const styles = [...document.styleSheets];
                                  const own = styles.filter(s => (s.href || '').includes('site-design-scientific-portal'));
                                  const rules = own.flatMap(s => {
                                    try { return [...s.cssRules].filter(r =>
                                      (r.cssText || '').includes('doc-labels')).map(r => r.cssText.slice(0, 360)); }
                                    catch { return []; }
                                  });
                                  return {
                                    color: getComputedStyle(node).color,
                                    element: node.outerHTML.slice(0, 300),
                                    parent: node.parentElement?.outerHTML.slice(0, 400),
                                    match_plain: node.matches('.doc-labels.doc code'),
                                    match_typeset: node.matches('.md-typeset .doc-labels.doc code'),
                                    schemes: {body: document.body?.getAttribute('data-md-color-scheme'),
                                              html: document.documentElement.getAttribute('data-md-color-scheme')},
                                    ownStylesheets: own.length, rules,
                                    variable: getComputedStyle(node).getPropertyValue('--md-default-fg-color').trim(),
                                  };
                                }""")
                                report["scheme_checks"].append({
                                  "scheme": scheme, "api_preaxe_diagnostic": diagnostic
                                })
                                print("API_CSS_DIAGNOSTIC=" + json.dumps(diagnostic), flush=True)
                            # Sampled axe with actual palette and target scientific route.
                            if (device, name) in (("desktop","home"), ("desktop","guide"),
                                                  ("desktop","api"), ("mobile","article")):
                                result["axe"] = axe_inspect(
                                    page, route=route or "home", viewport=f"{device}-{scheme}"
                                )
                                assert result["axe"]["highImpact"] == 0, (
                                    scheme, device, name, result["axe"].get("issues")
                                )
                            if name == "api" and device == "desktop":
                                code = page.locator(".doc-labels.doc code").first
                                assert code.count(), "Mkdocstrings API labels missing"
                                computed = code.evaluate("""node => ({
                                   color: getComputedStyle(node).color,
                                   bg: getComputedStyle(node).backgroundColor,
                                   scheme: document.body?.getAttribute('data-md-color-scheme')
                                })""")
                                report["scheme_checks"].append({"scheme": scheme, "api_label": computed})
                        if device == "mobile":
                            menu = page.locator('.md-header__button[for="__drawer"]')
                            assert menu.is_visible(), "Responsive menu button missing"
                            menu.click()
                            assert page.locator("input#__drawer").is_checked(), "Mobile drawer not functional"
                            report["scheme_checks"].append({"scheme":scheme,"mobile_drawer":"pass"})
                        if device == "desktop" and scheme == "light":
                            page.goto(origin, wait_until="domcontentloaded")
                            field = page.locator("input.md-search__input")
                            field.fill("sparse fpca")
                            page.locator(".md-search-result__link[href]").first.wait_for(timeout=30000)
                            urls = page.locator(".md-search-result__link[href]").evaluate_all(
                               "(nodes) => nodes.map(n => new URL(n.href).pathname)"
                            )
                            target = REPO_BASE + "guides/sparse-irregular-fpca/"
                            rank = next((i+1 for i,p in enumerate(urls) if p == target), None)
                            report["search"] = {"query":"sparse fpca","rank":rank,
                                                "results":len(urls)}
                            assert rank is not None and rank <= 3, report["search"]
                        assert not errors, (scheme,device,errors[:6])
                        context.close()
            finally:
                browser.close()
        report["status"] = "pass"
    except Exception as exc:
        report["issues"].append(str(exc))
        raise
    finally:
        (output / "scientific-portal-report.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", default="site")
    parser.add_argument("--output", default=str(OUT))
    args = parser.parse_args()
    report = audit(Path(args.site).resolve(), Path(args.output).resolve())
    print(json.dumps({"status":report["status"], "pages":report["page_count"],
                      "screenshots":len(report["screenshots"]),
                      "axe_samples":sum("axe" in r for r in report["routes"]),
                      "search":report["search"],
                      "api_color":report["scheme_checks"]},indent=2))


if __name__ == "__main__":
    main()
