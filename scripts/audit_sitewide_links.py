"""Offline, rendered-site-wide link, fragment and asset audit.

Reads generated HTML locally. Does NOT fetch external websites, nor claim that
dynamic navigation/JavaScript links were exhaustively evaluated.
Report distinguishes broken local targets from optional cross-site resources.
"""
from __future__ import annotations
import argparse
from collections import Counter
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

BASE = "https://stefanosbalaskas.github.io/eyetrajectoriespy/"
PREFIX = "/eyetrajectoriespy/"
LINK_TAGS = {"a": "href", "link": "href", "script": "src", "img": "src", "source": "src"}
SCHEMES = {"mailto", "tel", "data", "blob", "javascript"}
class Links(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.anchors = set()
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.anchors.add(a["id"])
        if tag == "a" and a.get("name"):
            self.anchors.add(a["name"])
        attr = LINK_TAGS.get(tag)
        if attr and a.get(attr):
            self.links.append((tag, a[attr]))


def inspect(site: Path, *, sample_limit: int = 100) -> dict:
    site = site.resolve()
    files = sorted(site.rglob("*.html"))
    report = {
        "site":str(site), "html_pages":len(files), "links_seen":0,
        "local_links_checked":0, "external_links_skipped":0,
        "local_broken_count":0, "fragment_missing_count":0,
        "broken_examples":[], "fragment_examples":[],
        "unparsed_dynamic_links": "This offline audit does not execute JavaScript.",
    }
    if not (site / "index.html").is_file():
        report["local_broken_count"] = 1
        report["broken_examples"] = ["No generated index.html at site root"]
        return report
    parsed = {}
    for file in files:
        page = Links()
        page.feed(file.read_text(encoding="utf-8", errors="replace"))
        parsed[file] = page
    def push(kind, src, link, detail):
        key = "local_broken_count" if kind == "broken" else "fragment_missing_count"
        examples = "broken_examples" if kind == "broken" else "fragment_examples"
        report[key] += 1
        if len(report[examples]) < sample_limit:
            report[examples].append({"source":src.relative_to(site).as_posix(),
                                     "url":link,"reason":detail})
    for file, html in parsed.items():
        source = BASE + file.relative_to(site).as_posix()
        # index.html URLs are served as directories; relative paths resolve there.
        if source.endswith("/index.html"):
            source = source.removesuffix("index.html")
        for tag, link in html.links:
            report["links_seen"] += 1
            if link.startswith("//"):
                report["external_links_skipped"] += 1; continue
            info = urlsplit(link)
            if info.scheme.lower() in SCHEMES:
                report["external_links_skipped"] += 1; continue
            absolute = urlsplit(urljoin(source, link))
            if absolute.scheme not in ("http", "https") or absolute.netloc != urlsplit(BASE).netloc:
                report["external_links_skipped"] += 1; continue
            # Root-relative links outside this repo's Pages prefix are not ours.
            if not absolute.path.startswith(PREFIX):
                report["external_links_skipped"] += 1; continue
            rel = unquote(absolute.path[len(PREFIX):])
            target = (site / rel).resolve()
            if not target.is_relative_to(site):
                push("broken",file,link,"Escapes built site"); continue
            if target.is_dir():
                target = target / "index.html"
            elif not target.exists() and not target.suffix:
                target = target / "index.html"
            report["local_links_checked"] += 1
            if not target.is_file():
                push("broken",file,link,f"Missing {target.relative_to(site)}")
                continue
            fragment = unquote(absolute.fragment)
            # Only verify named anchors on HTML, not deep links to binary resources.
            if fragment and target.suffix == ".html":
                anchor_doc = parsed.get(target)
                if anchor_doc is None:
                    anchor_doc = Links()
                    anchor_doc.feed(target.read_text(encoding="utf-8", errors="replace"))
                    parsed[target] = anchor_doc
                if fragment not in anchor_doc.anchors:
                    push("fragment", file, link, f"Missing #{fragment}")
    report["status"] = "pass" if not report["local_broken_count"] and not report["fragment_missing_count"] else "findings"
    return report


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--site",default="site")
    a.add_argument("--output",default="build/sitewide-links.json")
    a.add_argument("--strict",action="store_true")
    args = a.parse_args()
    result = inspect(Path(args.site))
    target=Path(args.output); target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k not in {"broken_examples","fragment_examples"}},indent=2))
    print("Broken examples:",json.dumps(result["broken_examples"][:20],indent=2))
    print("Fragment examples:",json.dumps(result["fragment_examples"][:20],indent=2))
    if args.strict and result["status"] != "pass":
        raise SystemExit(1)
if __name__ == "__main__":
    main()
