"""Summarize repeated simulated-mobile Lighthouse CI evidence.

Three local CI runs per route capture score spread, rather than using one noisy
point estimate. None of these numbers is field Core Web Vitals or a release
performance guarantee. Externally hosted resources are not uploaded.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
from statistics import median
from urllib.parse import urlsplit

METRICS = {
    "largest-contentful-paint": "lcp_ms",
    "cumulative-layout-shift": "cls",
    "total-blocking-time": "tbt_ms",
    "speed-index": "speed_index_ms",
    "first-contentful-paint": "fcp_ms",
}
CATEGORIES = ("performance", "accessibility", "best-practices", "seo")
EXPECTED_ROUTES = (
    "/eyetrajectoriespy/",
    "/eyetrajectoriespy/start/first-analysis/",
    "/eyetrajectoriespy/tools/figure-storyboard/",
    "/eyetrajectoriespy/integrations/navigator/",
)
RUNS_PER_ROUTE = 3


def spread(values: list[float | int | None]) -> dict:
    observed = [float(v) for v in values if isinstance(v, (int, float))]
    if not observed:
        return {"count": 0, "min": None, "median": None, "max": None}
    return {
        "count": len(observed),
        "min": round(min(observed), 3),
        "median": round(median(observed), 3),
        "max": round(max(observed), 3),
    }


def summarize(root: Path) -> dict:
    reports: list[dict] = []
    grouped: dict[str, list[dict]] = defaultdict(list)
    for file in sorted(root.glob("lhr-*.json")):
        result = json.loads(file.read_text(encoding="utf-8"))
        scores = {
            key: round(value["score"] * 100)
            if value.get("score") is not None else None
            for key, value in result.get("categories", {}).items()
            if key in CATEGORIES
        }
        audits = result.get("audits", {})
        metrics = {label: audits.get(key, {}).get("numericValue")
                   for key, label in METRICS.items()}
        path = urlsplit(result.get("requestedUrl") or "").path
        report = {
            "route": path,
            "requested_url": result.get("requestedUrl"),
            "final_url": result.get("finalUrl"),
            "scores_0_100": scores,
            "metrics": metrics,
            "lighthouse_version": result.get("lighthouseVersion"),
        }
        reports.append(report)
        grouped[path].append(report)
    routes = {}
    for route, values in sorted(grouped.items()):
        routes[route] = {
            "runs": len(values),
            "scores_0_100": {
                cat: spread([x["scores_0_100"].get(cat) for x in values])
                for cat in CATEGORIES
            },
            "metrics": {
                name: spread([x["metrics"].get(name) for x in values])
                for name in METRICS.values()
            },
        }
    return {
        "runs": len(reports),
        "runs_per_route_expected": RUNS_PER_ROUTE,
        "routes": routes,
        "reports": reports,
        "interpretation": (
            "Three simulated-mobile CI runs per route; minima, medians and "
            "maxima show local lab variability, not real-user Core Web Vitals. "
            "Do not set a performance budget or claim improvement before "
            "comparing controlled before/after distributions."
        ),
    }


def validate(result: dict) -> None:
    if set(result["routes"]) != set(EXPECTED_ROUTES):
        raise ValueError("Unexpected or missing audited route in Lighthouse output")
    counts = {route: values["runs"] for route, values in result["routes"].items()}
    if any(count != RUNS_PER_ROUTE for count in counts.values()):
        raise ValueError(f"Expected {RUNS_PER_ROUTE} Lighthouse runs per route: {counts}")
    for route, data in result["routes"].items():
        if data["scores_0_100"]["performance"]["count"] != RUNS_PER_ROUTE:
            raise ValueError(f"Missing performance scores for {route}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=".lighthouseci")
    parser.add_argument("--output", default="build/lighthouse-mobile-summary.json")
    args = parser.parse_args()
    result = summarize(Path(args.input))
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"runs": result["runs"], "routes": result["routes"]}, indent=2))
    validate(result)


if __name__ == "__main__":
    main()
