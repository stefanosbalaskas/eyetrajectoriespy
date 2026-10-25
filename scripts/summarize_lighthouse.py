"""Summarize locally produced Lighthouse mobile evidence for reproducibility.

Parses lhr-*.json emitted by pinned @lhci/cli. Numbers are simulated and
single-run, NOT field Core Web Vitals, independently reproduced benchmarks,
or normative performance budgets.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

METRICS={"largest-contentful-paint":"lcp_ms",
         "cumulative-layout-shift":"cls",
         "total-blocking-time":"tbt_ms",
         "speed-index":"speed_index_ms",
         "first-contentful-paint":"fcp_ms"}


def summarize(root:Path)->dict:
    reports=[]
    for file in sorted(root.glob("lhr-*.json")):
        result=json.loads(file.read_text(encoding="utf-8"))
        scores={k:round(v["score"]*100) if v.get("score") is not None else None
                for k,v in result.get("categories",{}).items()
                if k in ("performance","accessibility","best-practices","seo")}
        audits=result.get("audits",{})
        measures={label:audits.get(name,{}).get("numericValue")
                  for name,label in METRICS.items()}
        reports.append({"requested_url":result.get("requestedUrl"),
                        "final_url":result.get("finalUrl"),
                        "scores_0_100":scores,
                        "metrics":measures,
                        "lighthouse_version":result.get("lighthouseVersion")})
    return {"runs":len(reports),"reports":reports,
            "interpretation":"Simulated mobile CI baseline, single run per URL. No real-user CWV or stability claim."}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default=".lighthouseci")
    p.add_argument("--output",default="build/lighthouse-mobile-summary.json")
    a=p.parse_args(); result=summarize(Path(a.input))
    dst=Path(a.output);dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2))
    if result["runs"]!=4:raise SystemExit(f"Expected four local Lighthouse results, got {result['runs']}.")


if __name__=="__main__":
    main()
