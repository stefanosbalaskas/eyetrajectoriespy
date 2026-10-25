"""Compare page-to-page discoverability before/after navigation pruning.

Computes HTML-link graph reachability from the homepage on each complete
generated site (not a crawler, external links and JS-generated links excluded).
A site-wide link audit cannot catch valid-but-orphaned pages; this extra
experiment checks whether pruning creates new *static-link* orphans.
"""
from __future__ import annotations

import argparse
from collections import deque
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

BASE = "https://stefanosbalaskas.github.io/eyetrajectoriespy/"
PREFIX = "/eyetrajectoriespy/"


class Anchors(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self.hrefs.append(href)


def target_path(source: str, href: str) -> str | None:
    url = urlsplit(urljoin(BASE + source.removesuffix("index.html"), href))
    if url.scheme not in ("http", "https") or url.netloc != urlsplit(BASE).netloc:
        return None
    if not url.path.startswith(PREFIX):
        return None
    route = unquote(url.path[len(PREFIX):])
    if not route or route.endswith("/"):
        return route + "index.html"
    if not Path(route).suffix:
        return route + "/index.html"
    if route.endswith(".html"):
        return route
    return None


def graph(site: Path) -> dict[str, set[str]]:
    pages = {
        p.relative_to(site).as_posix(): p for p in site.rglob("*.html")
    }
    edges: dict[str, set[str]] = {}
    for src, path in sorted(pages.items()):
        parsed = Anchors()
        parsed.feed(path.read_text(encoding="utf-8", errors="replace"))
        edges[src] = {
            destination
            for href in parsed.hrefs
            if (destination := target_path(src, href)) in pages
        }
    return edges


def reachable(edges: dict[str, set[str]]) -> set[str]:
    visited: set[str] = set()
    work = deque(["index.html"])
    while work:
        page = work.popleft()
        if page not in edges or page in visited:
            continue
        visited.add(page)
        work.extend(edges[page] - visited)
    return visited


def compare(baseline: Path, candidate: Path) -> dict:
    a = graph(baseline)
    b = graph(candidate)
    before, after = reachable(a), reachable(b)
    newly_orphaned = sorted(before - after)
    return {
        "status": "pass" if not newly_orphaned and set(a) == set(b) else "review",
        "baseline_pages": len(a),
        "candidate_pages": len(b),
        "baseline_reachable": len(before),
        "candidate_reachable": len(after),
        "baseline_already_unreachable": len(set(a) - before),
        "baseline_unreachable_routes": sorted(set(a) - before),
        "candidate_unreachable_routes": sorted(set(b) - after),
        "newly_unreachable_after_pruning": len(newly_orphaned),
        "example_newly_unreachable": newly_orphaned[:80],
        "limitations": (
            "Static HTML hyperlinks only; JavaScript-generated links, "
            "browser search, direct URLs, sitemap crawling and external links "
            "are evaluated separately. A pass is not a usability certification."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", default="build/navigation-baseline-site")
    parser.add_argument("--candidate", default="build/navigation-prune-site")
    parser.add_argument("--output", default="build/navigation-link-reachability.json")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    result = compare(Path(args.baseline), Path(args.candidate))
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if args.strict and result["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
