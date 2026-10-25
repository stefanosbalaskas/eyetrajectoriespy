"""Fail-closed sampling audit for a *candidate* Zensical documentation build.

This checks representative generated files, links, built CSS/JS and selected
markers, not full browser-level visual or accessibility equivalence.
Never states that migration is production-ready.
"""
from __future__ import annotations

import argparse
from html.parser import HTMLParser
import json
from pathlib import Path

REPRESENTATIVE_ROUTES = (
    "index.html",
    "start/index.html",
    "start/first-analysis/index.html",
    "tools/figure-storyboard/index.html",
    "tools/figure-explorer/index.html",
    "integrations/navigator/index.html",
    "methods/visual-gallery/index.html",
    "methods/mathematical-reference/index.html",
    "reference/api/index.html",
    "workflows/fpca-exploration/index.html",
    "tutorials/index.html",
)
HTML_TOKENS = {
    "tools/figure-storyboard/index.html": ("Synthetic teaching", "FPCA"),
    "start/first-analysis/index.html": ("first", "uncertainty"),
    "integrations/navigator/index.html": ("et-integration-navigator", "source"),
    "reference/api/index.html": ("eyetrajectoriespy",),
}

class Links(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.styles, self.scripts, self.images = [], [], []
        self.title = ""
        self._title = False
    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if tag == "link" and data.get("rel") == "stylesheet":
            self.styles.append(data.get("href", ""))
        elif tag == "script" and "src" in data:
            self.scripts.append(data["src"])
        elif tag == "img":
            self.images.append((data.get("src", ""), data.get("alt")))
        elif tag == "title":
            self._title = True
    def handle_endtag(self, tag):
        if tag == "title": self._title = False
    def handle_data(self, data):
        if self._title: self.title += data


def compare(primary: Path, candidate: Path) -> dict:
    report = {"status": "blocked", "baseline": str(primary), "preview": str(candidate),
              "representative_routes": len(REPRESENTATIVE_ROUTES),
              "checked": [], "errors": [], "warnings": []}
    if not primary.joinpath("index.html").exists():
        report["errors"].append("Production MkDocs baseline missing. Did it build?")
        return report
    if not candidate.joinpath("index.html").exists():
        report["errors"].append("Zensical preview index absent: candidate build did not complete.")
        return report
    for rel in REPRESENTATIVE_ROUTES:
        baseline = primary / rel
        preview = candidate / rel
        if not baseline.is_file() or not preview.is_file():
            report["errors"].append(f"Missing representative route: {rel} "
                                    f"(MkDocs={baseline.is_file()}, Zensical={preview.is_file()})")
            continue
        a, b = baseline.read_text(encoding="utf-8"), preview.read_text(encoding="utf-8")
        aa, bb = Links(), Links()
        aa.feed(a)
        bb.feed(b)
        if not bb.title.strip():
            report["errors"].append(f"Candidate page has empty <title>: {rel}")
        for token in HTML_TOKENS.get(rel, ()):
            if token not in b:
                report["errors"].append(f"Candidate page missing expected content {token}: {rel}")
        for expected in ("integration-navigator", "interactive-explorers"):
            if rel == "integrations/navigator/index.html" and not any(expected in path for path in bb.scripts):
                report["errors"].append(f"Candidate lost custom JavaScript {expected}: {rel}")
        if rel == "tools/figure-storyboard/index.html":
            if len(bb.images) < 12:
                report["errors"].append("Candidate visual explorer has fewer than 12 image elements.")
            if sum(not alt for _,alt in bb.images) > 0:
                report["errors"].append("Candidate visual explorer has images without alt text.")
        if not bb.styles or not bb.scripts:
            report["errors"].append(f"Candidate lost stylesheet or script references: {rel}")
        # Content count may diverge from equivalent plugin/theme transforms; warn, do not assert.
        if abs(len(a) - len(b)) > max(5000, len(a)*0.5):
            report["warnings"].append(f"Substantial HTML byte-count difference: {rel}")
        report["checked"].append({"route": rel, "mkdocs_html_bytes": len(a),
                                  "zensical_html_bytes": len(b),
                                  "mkdocs_images": len(aa.images),
                                  "zensical_images": len(bb.images)})
    # The earlier 11-page sample was a useful smoke test, but not evidence
    # that every legacy deep link can migrate unchanged. Compare full route
    # inventory, and count missing search/asset artifacts before approval.
    baseline_routes = {
        f.relative_to(primary).as_posix() for f in primary.rglob("*.html")
    }
    candidate_routes = {
        f.relative_to(candidate).as_posix() for f in candidate.rglob("*.html")
    }
    missing_routes = sorted(baseline_routes - candidate_routes)
    report["sitewide_route_coverage"] = {
        "mkdocs_html_pages": len(baseline_routes),
        "zensical_html_pages": len(candidate_routes),
        "missing_candidate_routes": len(missing_routes),
        "sample_missing": missing_routes[:50],
    }
    if missing_routes:
        report["errors"].append(
            f"Zensical omits {len(missing_routes)} MkDocs HTML routes."
        )
    if len(candidate_routes) < len(baseline_routes):
        report["warnings"].append("Zensical rendered fewer pages than MkDocs.")
    for asset in ("robots.txt", "sitemap.xml",
                  "javascripts/integration-navigator.js",
                  "javascripts/interactive-explorers.js",
                  "javascripts/gaze-data-readiness.js",
                  "assets/figure-storyboard.css"):
        if (primary / asset).is_file() and not (candidate / asset).is_file():
            report["errors"].append("Zensical missing copied site asset: " + asset)
    # Compare search corpus presence, never equate different search engines'
    # index JSON formats with equivalent user-facing ranking.
    for role, root in (("mkdocs", primary), ("zensical", candidate)):
        search_assets = sorted(f.relative_to(root).as_posix()
            for f in root.rglob("*") if f.is_file()
            and ("search" in f.parts or f.name.startswith("search_index")))
        report.setdefault("search_assets", {})[role] = search_assets[:25]
    report["migration_decision"] = (
        "HOLD: 11-route/static equivalence is not a production migration approval; "
        "browser search, accessibility, performance and instant-navigation "
        "must pass a candidate-specific audit."
    )
    report["status"] = "candidate-pass" if not report["errors"] else "candidate-fail"
    return report


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--baseline", default="site")
    p.add_argument("--candidate", default="build/zensical-preview-site")
    p.add_argument("--output", default="build/zensical-preview-report.json")
    args=p.parse_args()
    result=compare(Path(args.baseline),Path(args.candidate))
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"checked":len(result["checked"]),
                      "errors":result["errors"],"warnings":result["warnings"]},indent=2))
    if result["status"] != "candidate-pass":
        raise SystemExit(1)
if __name__ == "__main__":
    main()
