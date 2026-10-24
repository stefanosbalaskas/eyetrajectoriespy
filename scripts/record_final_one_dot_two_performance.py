"""Convert a real, exact-version GitHub benchmark run into a versioned evidence ledger.

Only accepts the JSON emitted by scripts/run_performance_qualification.py.
Does not execute benchmarks, invent measurements, infer missing metadata, or
rename a previously measured prerelease result to final 1.2.0.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

VERSION = "1.2.0"
CASES = {
    "fpca_bootstrap", "mixed_full_refit_bootstrap",
    "nested_mixed_fit", "generalized_gee_bootstrap",
    "recurrence_rqa", "nonlinear_sensitivity",
}
THREADS = ("MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS")


def convert(raw: dict, *, original_sha256: str) -> dict:
    if not isinstance(raw, dict) or raw.get("schema_version") != 1:
        raise RuntimeError("Unrecognized raw performance format")
    env = raw.get("environment", {})
    if (raw.get("profile") != "ci-qualification"
        or raw.get("benchmark_kind") != "single-package performance envelope"
        or raw.get("comparative_benchmark") is not False):
        raise RuntimeError("Only the genuine single-package CI benchmark qualifies")
    if env.get("packages", {}).get("eyetrajectoriespy") != VERSION:
        raise RuntimeError("Performance source package is not literal final 1.2.0")
    commit = env.get("source_commit")
    run_id = env.get("github_run_id")
    if (not isinstance(commit, str) or len(commit) != 40
        or any(c not in "0123456789abcdef" for c in commit)):
        raise RuntimeError("No real exact-source GitHub commit in benchmark")
    if not str(run_id).isdigit() or int(run_id) < 1:
        raise RuntimeError("No genuine GitHub performance workflow run ID")
    if env.get("thread_limits") != {name: "1" for name in THREADS}:
        raise RuntimeError("Benchmark numerical thread limits differ")
    if env.get("system") != "Linux" or env.get("github_runner_environment") != "github-hosted":
        raise RuntimeError("Benchmark must identify GitHub-hosted Linux environment")
    if not isinstance(original_sha256, str) or len(original_sha256) != 64 or any(c not in "0123456789abcdef" for c in original_sha256):
        raise RuntimeError("Original raw artifact SHA256 required")
    rows = raw.get("results")
    if not isinstance(rows, list) or {row.get("case") for row in rows} != CASES or len(rows) != len(CASES):
        raise RuntimeError("Exact six-workload qualification required")
    converted = []
    for row in rows:
        times = row.get("runtime_seconds")
        memory = row.get("peak_memory_mib")
        if (row.get("repeats", 0) < 3
            or not isinstance(times, dict) or not isinstance(memory, dict)
            or len(times.get("all", [])) != row["repeats"]
            or len(memory.get("all", [])) != row["repeats"]):
            raise RuntimeError("Incomplete repeated benchmark evidence")
        if any(not isinstance(v, (int, float)) or not math.isfinite(v) or v <= 0 for v in times["all"] + memory["all"]):
            raise RuntimeError("Nonfinite/invalid benchmark measurement")
        converted.append({
            "case": row["case"], "repeats": row["repeats"],
            "scale": row["scale"],
            "observed": {"runtime_seconds": times, "peak_memory_mib": memory},
        })
    return {
        "schema_version": 1, "package_version": VERSION,
        "benchmark_kind": raw["benchmark_kind"],
        "comparative_benchmark": False, "profile": raw["profile"],
        "status": "qualified",
        "qualification_commit": commit, "qualification_run_id": int(run_id),
        "raw_artifact_member_sha256": original_sha256,
        "environment": env, "results": converted,
        "interpretation": raw.get("interpretation",
            "Observed single-package runtime/peak RSS only, not comparative speed evidence."),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, required=True,
                        help="Verbatim performance-envelope.json from successful final-version CI run")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    raw_bytes = args.raw.read_bytes()
    obj = json.loads(raw_bytes)
    record = convert(obj, original_sha256=hashlib.sha256(raw_bytes).hexdigest())
    args.out.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Final 1.2.0 measured performance imported from run {record['qualification_run_id']}; exact source {record['qualification_commit']}; no publication performed")


if __name__ == "__main__":
    main()
