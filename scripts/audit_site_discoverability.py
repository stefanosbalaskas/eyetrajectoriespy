"""Verify published site discovery, schema and source-citation contracts.

Runs AFTER MkDocs has built the real website. This narrow check does not
claim that search engines have indexed a page or that all metadata are valid.
"""
from __future__ import annotations

from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
URL = "https://stefanosbalaskas.github.io/eyetrajectoriespy/"
PAGES = (
    "index.html",
    "start/first-analysis/index.html",
    "start/cite-and-reproduce/index.html",
    "tools/figure-storyboard/index.html",
    "integrations/navigator/index.html",
    "news/release-status/index.html",
)


class Metadata(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.title_on = False
        self.descriptions = []
        self.canonicals = []
        self.json_ld = []
        self.json_script = False
        self.json_buffer = []
    def handle_starttag(self, tag, attrs):
        v = dict(attrs)
        if tag == "title": self.title_on = True
        if tag == "meta" and v.get("name") == "description":
            self.descriptions.append(v.get("content", ""))
        if tag == "link" and v.get("rel") == "canonical":
            self.canonicals.append(v.get("href", ""))
        if tag == "script" and v.get("type") == "application/ld+json":
            self.json_script = True
            self.json_buffer = []
    def handle_endtag(self, tag):
        if tag == "title": self.title_on = False
        if tag == "script" and self.json_script:
            self.json_ld.append("".join(self.json_buffer))
            self.json_script = False
    def handle_data(self, text):
        if self.title_on: self.title += text
        if self.json_script: self.json_buffer.append(text)


def main() -> None:
    assert SITE.is_dir(), "Build MkDocs before checking public metadata."
    cff = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version: 1.2.0' in cff
    assert re.search(r'(?m)^version\s*=\s*"1\.2\.0"', pyproject)
    robots = (SITE / "robots.txt").read_text(encoding="utf-8")
    assert "Sitemap: " + URL + "sitemap.xml" in robots
    sitemap = ET.parse(SITE / "sitemap.xml").getroot()
    locations = {node.text for node in sitemap.iter() if node.tag.endswith("}loc")}
    assert locations and all(x.startswith(URL) for x in locations)
    for path in PAGES:
        fp = SITE / path
        assert fp.is_file(), "Missing indexed page: " + path
        parsed = Metadata()
        parsed.feed(fp.read_text(encoding="utf-8"))
        assert parsed.title.strip(), "Empty page title: " + path
        # Theme can place description in its meta template rather than raw markdown.
        assert parsed.descriptions and all(d.strip() for d in parsed.descriptions), (
            "Missing nonempty description: " + path
        )
        assert len(parsed.canonicals) == 1, "Expected one canonical URL: " + path
        actual = parsed.canonicals[0]
        assert actual.startswith(URL), "Wrong canonical website base: " + actual
        expected = URL if path == "index.html" else URL + path.removesuffix("index.html")
        assert actual.rstrip("/") == expected.rstrip("/"), (
            "Noncanonical destination: " + path + " -> " + actual
        )
        assert expected in locations, "Published sitemap omits page: " + path
        if path == "index.html":
            schemas = [json.loads(raw) for raw in parsed.json_ld]
            matches = [obj for obj in schemas if isinstance(obj, dict)
                       and obj.get("@type") == "SoftwareSourceCode"]
            assert len(matches) == 1, "Exactly one SoftwareSourceCode item expected"
            item = matches[0]
            assert item["name"] == "eyetrajectoriespy"
            assert item["softwareVersion"] == "1.2.0"
            assert item["codeRepository"] == "https://github.com/stefanosbalaskas/eyetrajectoriespy"
            assert item["license"] == "https://opensource.org/licenses/MIT"
            assert item["author"]["name"] == "Stefanos Balaskas"
            assert "doi" not in json.dumps(item).lower(), "No DOI has been declared in source metadata"
    print("PASS: six canonical docs pages, sitemap, robots and CFF-aligned SoftwareSourceCode metadata")


if __name__ == "__main__":
    main()
