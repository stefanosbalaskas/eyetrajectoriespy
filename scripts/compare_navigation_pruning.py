"""Compare full baseline and navigation-pruned Material builds without deployment.

Checks actual compressed/uncompressed HTML, route parity, content text,
search-index identity and sidebar-link changes. Browser interactions, external
links and accessibility are qualified separately by the preview workflow.
"""
from __future__ import annotations

import argparse
import gzip
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
from statistics import median

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr"}
SAMPLES = (
    "start/first-analysis/index.html",
    "guides/index.html",
    "guides/sparse-multivariate-fpca/index.html",
    "tutorials/index.html",
    "workflows/index.html",
    "research/index.html",
    "reference/api/index.html",
    "integrations/navigator/index.html",
)


class Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._content_depth = 0
        self._sidebar_depth = 0
        self.main_text: list[str] = []
        self.sidebar_links: list[str] = []
        self.sidebar_items = 0
        self.content_found = False
        self.sidebar_found = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        d = dict(attrs)
        classes = set((d.get("class") or "").split())
        if self._content_depth:
            if tag not in VOID:
                self._content_depth += 1
        elif "md-content__inner" in classes:
            self._content_depth = 1
            self.content_found = True
        if self._sidebar_depth:
            if tag == "a" and d.get("href"):
                self.sidebar_links.append(d["href"] or "")
            if "md-nav__item" in classes:
                self.sidebar_items += 1
            if tag not in VOID:
                self._sidebar_depth += 1
        elif "md-sidebar--primary" in classes:
            self._sidebar_depth = 1
            self.sidebar_found = True

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        # Void nodes never change subtree depth; links inside content do not affect text.
        pass

    def handle_endtag(self, tag: str) -> None:
        if tag in VOID:
            return
        if self._content_depth:
            self._content_depth -= 1
        if self._sidebar_depth:
            self._sidebar_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._content_depth:
            self.main_text.append(data)

    @property
    def content_hash(self) -> str | None:
        if not self.content_found:
            return None
        normalized = " ".join(" ".join(self.main_text).split())
        return sha256(normalized.encode("utf-8")).hexdigest()


def read_page(path: Path) -> tuple[bytes, Page]:
    raw = path.read_bytes()
    parser = Page()
    parser.feed(raw.decode("utf-8"))
    parser.close()
    return raw, parser


def search_entries(site: Path) -> list[tuple[str, str, str]]:
    path = site / "search/search_index.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return sorted(
        (str(row.get("location", "")), str(row.get("title", "")),
         str(row.get("text", "")))
        for row in data.get("docs", [])
    )


def compare(baseline: Path, candidate: Path) -> dict:
    base = {p.relative_to(baseline).as_posix(): p for p in baseline.rglob("*.html")}
    pruned = {p.relative_to(candidate).as_posix(): p for p in candidate.rglob("*.html")}
    errors: list[str] = []
    missing = sorted(set(base) - set(pruned))
    extra = sorted(set(pruned) - set(base))
    if missing or extra:
        errors.append(f"HTML route inventory differs: missing={len(missing)}, extra={len(extra)}")
    if len(base) < 300:
        errors.append(f"Unexpectedly small documentation baseline: {len(base)} pages")
    per_page = []
    checked_hashes = 0
    hash_mismatch = []
    sidebar_reduced = 0
    for route in sorted(set(base) & set(pruned)):
        a_raw, a = read_page(base[route])
        b_raw, b = read_page(pruned[route])
        if a.content_found != b.content_found or (a.content_hash != b.content_hash):
            hash_mismatch.append(route)
        if a.content_found and b.content_found:
            checked_hashes += 1
        if b.sidebar_items < a.sidebar_items:
            sidebar_reduced += 1
        per_page.append({
            "route": route,
            "baseline_bytes": len(a_raw),
            "candidate_bytes": len(b_raw),
            "baseline_gzip_bytes": len(gzip.compress(a_raw, compresslevel=9, mtime=0)),
            "candidate_gzip_bytes": len(gzip.compress(b_raw, compresslevel=9, mtime=0)),
            "baseline_sidebar_items": a.sidebar_items,
            "candidate_sidebar_items": b.sidebar_items,
            "baseline_sidebar_links": len(a.sidebar_links),
            "candidate_sidebar_links": len(b.sidebar_links),
        })
    if hash_mismatch:
        errors.append(f"Main content text differs on {len(hash_mismatch)} pages")
    if checked_hashes < 300:
        errors.append(f"Too few comparable main-content elements: {checked_hashes}")
    if sidebar_reduced < 5:
        errors.append(f"Navigation not measurably pruned: {sidebar_reduced} pages with fewer sidebar items")
    try:
        source_index = search_entries(baseline)
        candidate_index = search_entries(candidate)
        search_equal = source_index == candidate_index
    except (OSError, ValueError, KeyError) as e:
        search_equal = False
        errors.append(f"Search index could not be compared: {e}")
        source_index = []
        candidate_index = []
    if not search_equal:
        errors.append("Search index locations/titles/content changed with pruning")
    baseline_bytes = sum(p["baseline_bytes"] for p in per_page)
    candidate_bytes = sum(p["candidate_bytes"] for p in per_page)
    baseline_gzip = sum(p["baseline_gzip_bytes"] for p in per_page)
    candidate_gzip = sum(p["candidate_gzip_bytes"] for p in per_page)
    if candidate_bytes >= baseline_bytes:
        errors.append("Pruned HTML does not reduce total HTML bytes")
    def savings(before: int, after: int) -> float:
        return round(100 * (before - after) / before, 3) if before else 0.0
    report = {
        "status": "pass" if not errors else "fail",
        "method": "Same-source strict MkDocs Material builds, navigation.prune toggled only",
        "html_pages": len(base),
        "missing_candidate_routes": missing[:25],
        "extra_candidate_routes": extra[:25],
        "content_hashes_checked": checked_hashes,
        "content_mismatch_routes": hash_mismatch[:25],
        "identical_search_index": search_equal,
        "baseline_search_entries": len(source_index),
        "candidate_search_entries": len(candidate_index),
        "pages_with_reduced_sidebar_items": sidebar_reduced,
        "total_html_bytes": {
            "baseline": baseline_bytes, "pruned": candidate_bytes,
            "saving_percent": savings(baseline_bytes, candidate_bytes),
        },
        "total_html_gzip_bytes": {
            "baseline": baseline_gzip, "pruned": candidate_gzip,
            "saving_percent": savings(baseline_gzip, candidate_gzip),
        },
        "median_page_saving_percent": round(median([
            savings(p["baseline_bytes"], p["candidate_bytes"]) for p in per_page
        ]), 3) if per_page else None,
        "representative_pages": [p for p in per_page if p["route"] in SAMPLES],
        "errors": errors,
        "limitations": [
            "Offline compressed HTML sizes are not actual transferred bytes, lab Lighthouse, or real user Core Web Vitals.",
            "Same search index does not prove browser search relevance or usability.",
            "Navigation pruning changes discoverability; live browser/keyboard/a11y checks and section landing pages are separate gates.",
            "No production site is changed or published by this comparison.",
        ],
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", default="build/navigation-baseline-site")
    parser.add_argument("--candidate", default="build/navigation-prune-site")
    parser.add_argument("--output", default="build/navigation-prune-comparison.json")
    args = parser.parse_args()
    result = compare(Path(args.baseline), Path(args.candidate))
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "representative_pages"}, indent=2))
    if result["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
