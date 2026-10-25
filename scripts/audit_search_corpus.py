"""Check MkDocs Material's generated search corpus for high-intent research queries.

This is a *corpus retrieval proxy* (not a claim about ranking by browser Lunr).
Checks query-term coverage in indexed titles/contents, and the destination URL.
External search-engine indexing is out of scope.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
from urllib.parse import urljoin

BASE="https://stefanosbalaskas.github.io/eyetrajectoriespy/"
CASES = (
    {"query":"first analysis","terms":("first","analysis"),
     "expected":"start/first-analysis/"},
    {"query":"pymovements","terms":("pymovements",),
     "expected":"integrations/pymovements-handoff/"},
    {"query":"syelink","terms":("syelink",),
     "expected":"integrations/syelink-handoff/"},
    {"query":"sparse fpca","terms":("sparse","fpca"),
     "expected":"guides/sparse-irregular-fpca/"},
    {"query":"trajectory missingness","terms":("missing","gaze"),
     "expected":"methods/limitations/"},
    {"query":"cite software","terms":("citation","software"),
     "expected":"start/cite-and-reproduce/"},
    {"query":"visual methods","terms":("visual","methods"),
     "expected":"tools/figure-storyboard/"},
    {"query":"data integration","terms":("integration","source"),
     "expected":"integrations/navigator/"},
    {"query":"API reference","terms":("api","eyetrajectoriespy"),
     "expected":"reference/api/"},
    {"query":"W3 uncertainty","terms":("w3","inference"),
     "expected":"news/release-status/"},
)


def inspect(site:Path) -> dict:
    index=site/"search/search_index.json"
    report={"index":str(index),"documents":0,"queries":[],"errors":[],
            "scope":"MkDocs index completeness, not live search relevance ranking"}
    if not index.is_file():
        report["errors"].append("Missing Material search/search_index.json")
        return report
    raw=json.loads(index.read_text(encoding="utf-8"))
    docs=raw.get("docs",[])
    report["documents"]=len(docs)
    locations={str(row.get("location","")).split("#")[0].strip("/"):row for row in docs}
    for case in CASES:
        expected=case["expected"].strip("/")
        rows=[v for k,v in locations.items() if k==expected]
        matching=[x for x in rows if all(term.casefold() in
                  (x.get("title","")+" "+x.get("text","")).casefold()
                  for term in case["terms"])]
        # MkDocs may chunk headings separately, so also allow indexed
        # descendants on same page before declaring a corpus miss.
        matching=[x for x in docs if str(x.get("location","")).split("#")[0].strip("/")==expected
                  and all(term.casefold() in
                  (x.get("title","")+" "+x.get("text","")).casefold()
                  for term in case["terms"])]
        exists=bool(rows)
        found=bool(matching)
        report["queries"].append({"query":case["query"],"expected":expected,
                                  "page_indexed":exists,"terms_on_expected_page":found})
        if not exists:
            report["errors"].append(f"No indexed page for {case['query']}: {expected}")
        elif not found:
            # Useful editorial finding, not a false assertion of bad search rank.
            report.setdefault("editorial_warnings",[]).append(
                f"Indexed {expected}, but specific query terms not co-located: {case['terms']}"
            )
    if len(docs)<100:
        report["errors"].append(f"Unexpectedly small full documentation index: {len(docs)} entries")
    report["status"]="pass" if not report["errors"] else "findings"
    return report


def main():
    p=argparse.ArgumentParser();p.add_argument("--site",default="site")
    p.add_argument("--output",default="build/site-search-corpus.json")
    p.add_argument("--strict",action="store_true")
    a=p.parse_args()
    result=inspect(Path(a.site))
    dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2))
    if a.strict and result["errors"]:raise SystemExit(1)
if __name__=="__main__":main()
