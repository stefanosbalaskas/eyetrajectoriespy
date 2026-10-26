"""Qualification for the actual rightmost Zensical Modern design.

Rejects route loss, broken search, serious/critical axe findings, browser
exceptions, or unusable mobile navigation before any production migration.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_navigation_pruning import serve_site
from site_accessibility import inspect as axe_inspect

ROOT = Path(__file__).resolve().parents[1]
ROUTES = {
    "home": "",
    "article": "articles/how-to-read-identification-bounds/",
    "guide": "guides/sparse-irregular-fpca/",
    "api": "reference/api/",
}
TARGET = "/eyetrajectoriespy/guides/sparse-irregular-fpca/"

def inventory(site: Path) -> set[str]:
    return {p.relative_to(site).as_posix() for p in site.rglob("*.html")}

def check_search(page, origin: str, report: dict) -> None:
    page.goto(origin, wait_until="domcontentloaded")
    page.wait_for_timeout(500)
    search = page.get_by_role("button", name="Search").first
    try:
        if search.count() and search.is_visible():
            search.click(timeout=7000)
        else:
            page.keyboard.press("Control+k")
        field = page.locator(
            'dialog:visible input:visible, [role="dialog"]:visible input:visible, '
            'input[type="search"]:visible, [role="combobox"]:visible, '
            'input.md-search__input:visible'
        ).first
        field.wait_for(state="visible", timeout=9000)
        field.fill("sparse fpca")
        outcomes = []
        for _ in range(12):
            page.wait_for_timeout(900)
            state = page.evaluate("""() => {
                const roots = [
                  ...document.querySelectorAll('dialog, [role="dialog"], '
                    + '[data-md-component="search"], .md-search, [role="listbox"]')
                ].filter(e => e.getBoundingClientRect().width > 0);
                const field = document.activeElement;
                const matches = roots.flatMap(root => Array.from(
                  root.querySelectorAll('a[href], [role="option"], button')
                )).filter(e => e.getBoundingClientRect().width > 0).map(e => ({
                  text: (e.innerText || e.textContent || '').trim().slice(0, 120),
                  href: e.getAttribute('href'),
                  role: e.getAttribute('role'),
                }));
                return {active: field?.outerHTML?.slice(0, 350),
                        roots: roots.map(r => ({
                           tag: r.tagName, role: r.getAttribute('role'),
                           cls: String(r.className).slice(0, 100),
                           text: (r.innerText || '').slice(0, 500)})),
                        candidates: matches.slice(0, 60)};
            }""")
            outcomes.append(state)
            links = [c for c in state["candidates"] if
                     TARGET in (c.get("href") or "") or
                     (("sparse" in (c.get("text") or "").lower())
                      and ("fpca" in (c.get("text") or "").lower()))]
            if links:
                report["search"] = {"status": "verified-result-visible",
                                    "query": "sparse fpca", "matching": links[:5],
                                    "tries": len(outcomes)}
                # Follow a real result link when the result exposes one.
                matching_links = [c for c in links if TARGET in (c.get("href") or "")]
                if matching_links:
                    locator = page.locator('a[href*="sparse-irregular-fpca"]').filter(
                        visible=True
                    )
                    # Use a search-root scoping selector, not a sidebar link.
                    in_search = page.locator(
                      'dialog a[href*="sparse-irregular-fpca"], '
                      '[role="dialog"] a[href*="sparse-irregular-fpca"], '
                      '.md-search a[href*="sparse-irregular-fpca"]'
                    ).first
                    if in_search.count() and in_search.is_visible():
                        in_search.click(timeout=5000)
                        page.wait_for_url("**/guides/sparse-irregular-fpca/*",
                                          timeout=10000)
                        report["search"]["navigation"] = "pass"
                return
        report["search"] = {"status": "unverified",
                            "query": "sparse fpca",
                            "diagnostic": outcomes[-1] if outcomes else {},
                            "observations": len(outcomes)}
        raise AssertionError("Zensical native search failed to expose sparse FPCA result")
    except Exception as exc:
        report.setdefault("search", {"status": "failed",
                                     "diagnostic": page.locator("body").inner_text()[-2500:]})
        report["search"]["error"] = str(exc)
        raise

def qualify(baseline: Path, candidate: Path, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    result = {"status": "failed", "routes": [], "screenshots": [],
              "browser_errors": [], "axe_findings": [], "issues": [], "search": {}}
    old, new = inventory(baseline), inventory(candidate)
    result["route_parity"] = {"baseline": len(old), "candidate": len(new),
                              "missing": sorted(old-new)[:30],
                              "extra": sorted(new-old)[:30]}
    try:
        assert len(old) >= 370 and old == new, result["route_parity"]
        with serve_site(candidate) as origin, sync_playwright() as p:
            browser = p.chromium.launch(headless=True,
                                        args=["--disable-dev-shm-usage"])
            try:
                for scheme in ("light", "dark"):
                    for device, width, height in (("desktop", 1440, 900),
                                                  ("mobile", 390, 844)):
                        ctx = browser.new_context(viewport={"width": width, "height": height},
                                                  reduced_motion="reduce")
                        page = ctx.new_page()
                        errors = []
                        page.on("pageerror", lambda error: errors.append(str(error)))
                        try:
                            for name, route in ROUTES.items():
                                response = page.goto(origin + route,
                                                     wait_until="domcontentloaded",
                                                     timeout=60000)
                                assert response and response.status == 200, (name, device, scheme)
                                if scheme == "dark":
                                    # The template exposes a palette switch; test
                                    # dark variant only when it can truly activate.
                                    toggle = page.locator('label[for="__palette_1"], '
                                           'label[for="__palette_2"], '
                                           '.md-header__button[for^="__palette"]')
                                    if toggle.count() and toggle.first.is_visible():
                                        toggle.first.click(timeout=2500)
                                    else:
                                        # Do not mark untested dark mode as verified.
                                        raise AssertionError("Dark palette toggle not available")
                                title = page.locator("h1").first.inner_text()
                                assert title.strip(), (scheme, device, name, "heading missing")
                                overflow = page.evaluate(
                                   "() => document.documentElement.scrollWidth > innerWidth + 2")
                                assert not overflow, (scheme,device,name,"horizontal overflow")
                                row = {"scheme":scheme,"device":device,"page":name,
                                       "title":title[:95],"status":response.status}
                                a11y = axe_inspect(page, route=route or "home",
                                                     viewport=device+"-"+scheme)
                                row["axe_high_impact"] = a11y["highImpact"]
                                if a11y["highImpact"]:
                                    result["axe_findings"].append(
                                        {"page":name,"scheme":scheme,
                                         "device":device,"issues":a11y["issues"]})
                                result["routes"].append(row)
                                path=out / f"zensical-{name}-{device}-{scheme}.png"
                                page.screenshot(path=str(path), animations="disabled")
                                result["screenshots"].append(path.name)
                            if device == "mobile":
                                page.goto(origin, wait_until="domcontentloaded")
                                menu=page.locator('.md-header__button[for="__drawer"]')
                                assert menu.count() and menu.is_visible(), "Mobile menu missing"
                                menu.click()
                                assert page.locator("input#__drawer").is_checked(), "Drawer failed"
                            if device == "desktop" and scheme == "light":
                                check_search(page, origin, result)
                        finally:
                            result["browser_errors"].extend(errors[:8])
                            ctx.close()
            finally:
                browser.close()
        assert not result["axe_findings"], result["axe_findings"]
        assert not result["browser_errors"], result["browser_errors"]
        assert result["search"].get("status") == "verified-result-visible"
        result["status"] = "pass"
    except Exception as exc:
        result["issues"].append(str(exc)[:4000])
        raise
    finally:
        (out / "qualification.json").write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", default="site")
    parser.add_argument("--candidate", default="build/zensical-modern")
    parser.add_argument("--output", default="build/zensical-modern-evidence")
    args=parser.parse_args()
    report=qualify(Path(args.baseline).resolve(),
                   Path(args.candidate).resolve(),Path(args.output).resolve())
    print(json.dumps({"status":report["status"],
                      "route_parity":report["route_parity"],
                      "views":len(report["routes"]),
                      "search":report["search"]},indent=2))
