"""Deterministic test for grouped Lighthouse CI evidence; no browser required."""
from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from summarize_lighthouse import EXPECTED_ROUTES, summarize, validate, RUNS_PER_ROUTE


def main() -> None:
    with TemporaryDirectory() as root:
        directory = Path(root)
        for index, route in enumerate(EXPECTED_ROUTES):
            for replicate in range(RUNS_PER_ROUTE):
                payload = {
                    "requestedUrl": "http://localhost" + route,
                    "finalUrl": "http://localhost" + route,
                    "lighthouseVersion": "test",
                    "categories": {
                        "performance": {"score": (60 + replicate * 10) / 100},
                        "accessibility": {"score": 0.95},
                        "seo": {"score": 1.0},
                        "best-practices": {"score": 1.0},
                    },
                    "audits": {
                        "largest-contentful-paint": {
                            "numericValue": 9000 + replicate * 1000
                        },
                        "total-blocking-time": {"numericValue": 400},
                    },
                }
                (directory / f"lhr-{index}-{replicate}.json").write_text(
                    json.dumps(payload), encoding="utf-8"
                )
        result = summarize(directory)
        validate(result)
        assert result["runs"] == 12
        for row in result["routes"].values():
            assert row["scores_0_100"]["performance"]["median"] == 70
            assert row["scores_0_100"]["performance"]["min"] == 60
            assert row["scores_0_100"]["performance"]["max"] == 80
            assert row["metrics"]["lcp_ms"]["median"] == 10000
        (directory / "lhr-0-0.json").unlink()
        try:
            validate(summarize(directory))
        except ValueError:
            pass
        else:
            raise AssertionError("Incomplete Lighthouse run set must fail")
    print("PASS: Lighthouse run grouping, medians, spread and missing-run refusal")


if __name__ == "__main__":
    main()
