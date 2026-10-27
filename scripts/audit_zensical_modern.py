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

def check_visible_top_tabs(page) -> dict:
    """Block white-on-white Zensical desktop menus even when axe misses them."""
    data = page.evaluate("""() => {
      const tabs = [...document.querySelectorAll('.md-tabs__link')].filter(e =>
        e.getClientRects().length &&
        getComputedStyle(e).display !== 'none' &&
        getComputedStyle(e).visibility !== 'hidden' &&
        (e.textContent || '').trim()
      );
      const lightContrast = css => {
        const m = (css || '').match(/rgba?\\(([^)]+)\\)/);
        if (!m) return 0;
        const rgb = m[1].split(',').slice(0, 3).map(Number);
        const values = rgb.map(x => {
          const s = x / 255;
          return s <= .04045 ? s / 12.92 : ((s + .055) / 1.055) ** 2.4;
        });
        const lum = .2126*values[0] + .7152*values[1] + .0722*values[2];
        return Number((1.05 / (lum + .05)).toFixed(2));
      };
      return tabs.map(e => ({
        label: (e.textContent || '').trim().slice(0, 50),
        color: getComputedStyle(e).color,
        contrast_on_white: lightContrast(getComputedStyle(e).color)
      }));
    }""")
    return {"count": len(data), "labels": data[:12],
            "min_contrast_on_white": min(
                (x["contrast_on_white"] for x in data), default=0)}

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
                // Zensical's Disco search dialog lives inside an open
                // shadow root. document.querySelectorAll alone cannot see it.
                const allRoots = [document];
                for (let i = 0; i < allRoots.length; i++) {
                  for (const el of allRoots[i].querySelectorAll('*')) {
                    if (el.shadowRoot) allRoots.push(el.shadowRoot);
                  }
                }
                const roots = allRoots.flatMap(root => Array.from(
                  root.querySelectorAll('dialog, [role="dialog"], '
                    + '[data-md-component="search"], .md-search, [role="listbox"]')
                )).filter(e => e.getBoundingClientRect().width > 0);
                const focusedHost = document.activeElement;
                const field = focusedHost?.shadowRoot?.activeElement || focusedHost;
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
                result_links = [c for c in state["candidates"] if
                                c.get("role") == "option" and
                                "/eyetrajectoriespy/" in (c.get("href") or "")]
                assert result_links, "Native search did not expose linked results"
                canonical_rank = next((i + 1 for i, c in enumerate(result_links)
                                       if TARGET in (c.get("href") or "")), None)
                report["search"] = {
                    "status": "verified-result-visible", "query": "sparse fpca",
                    "matching": result_links[:5], "result_count": len(result_links),
                    "canonical_guide_rank_sampled": canonical_rank,
                    "tries": len(outcomes)
                }
                # Real Zensical native search ranks some validation/plot pages
                # above the sparse-FPCA guide. Verify a relevant real result
                # opens correctly; do not require identical Lunr ranking.
                first = page.locator('a[role="option"][href*="/eyetrajectoriespy/"]').first
                assert first.count() and first.is_visible(), (
                    "Search did not expose a clickable link", result_links[:5]
                )
                first.click(timeout=7000)
                page.wait_for_function(
                    "() => location.pathname !== '/eyetrajectoriespy/' "
                    "&& location.pathname.startsWith('/eyetrajectoriespy/')",
                    timeout=15000
                )
                visited = page.evaluate("() => location.pathname")
                assert ("sparse" in visited or "fpca" in visited), visited
                report["search"]["navigation"] = "pass"
                report["search"]["opened_path"] = visited
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
            browser = p.chromium.launch(channel="chrome", headless=True,
                                        args=["--disable-dev-shm-usage"])
            try:
                for scheme in ("light", "dark"):
                    for device, width, height in (("desktop", 1440, 900),
                                                  ("mobile", 390, 844)):
                        ctx = browser.new_context(viewport={"width": width, "height": height},
                                                  color_scheme=scheme, reduced_motion="reduce")
                        page = ctx.new_page()
                        errors = []
                        page.on("pageerror", lambda error: errors.append(str(error)))
                        try:
                            for name, route in ROUTES.items():
                                response = page.goto(origin + route,
                                                     wait_until="domcontentloaded",
                                                     timeout=60000)
                                assert response and response.status == 200, (name, device, scheme)
                                palette = page.locator("body").get_attribute(
                                    "data-md-color-scheme"
                                )
                                if scheme == "dark" and palette != "slate":
                                    toggle = page.locator(
                                        'label[for^="__palette"], '
                                        '.md-header__button[for^="__palette"]'
                                    )
                                    if toggle.count() and toggle.first.is_visible():
                                        toggle.first.click(timeout=2500)
                                    palette = page.locator("body").get_attribute(
                                        "data-md-color-scheme"
                                    )
                                if scheme == "dark":
                                    assert palette == "slate", (
                                        "Dark palette did not activate", palette
                                    )
                                title = page.locator("h1").first.inner_text()
                                assert title.strip(), (scheme, device, name, "heading missing")
                                overflow = page.evaluate(
                                   "() => document.documentElement.scrollWidth > innerWidth + 2")
                                assert not overflow, (scheme,device,name,"horizontal overflow")
                                row = {"scheme":scheme,"device":device,"page":name,
                                       "title":title[:95],"status":response.status}
                                if device == "desktop" and name == "home":
                                    tabs = check_visible_top_tabs(page)
                                    row["top_navigation"] = tabs
                                    assert tabs["count"] >= 3, (
                                        "Missing desktop top navigation", tabs
                                    )
                                    if scheme == "light":
                                        assert tabs["min_contrast_on_white"] >= 4.5, (
                                            "Invisible light-mode Zensical top tabs", tabs
                                        )
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
