"""Targeted longer-budget refit of B6 stage-0 replicate 1, NOT a new SBC dataset.

Research only. Preserve the original prior-generated dataset, report all fitting
attempts, separate sampler convergence from conditional truth inclusion, and
never promote posterior calibration from this one diagnostic investigation.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np

from scripts.run_b6_rank1_prior_sbc_pilot import (
    SEED as PILOT_MASTER_SEED, fresh_seed, rank_in_posterior,
)
from scripts.run_b6_population_calibration_grid import (
    _known_truth, GRID, MEAN_PRIOR_SD, N_BASIS,
)
from scripts.run_b6_b7_independent_pymc_nuts import _pymc_marginal
from scripts.run_b6_b7_four_chain_reference import (
    identified_functionals, numerical_reference_diagnostics,
)

STUDY = "B6_RANK1_SBC_R2_FIXED_DATASET_LONG_BUDGET_V1"
SOURCE_RUN = "https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38087405506"
SOURCE_ARTIFACT = 11683660208
TARGET_REPLICATE = 1
CONFIG = {"chains": 4, "cores": 2, "warmup_per_chain": 1200,
          "draws_per_chain": 800, "target_accept": 0.94}
PRIMARY = ("x_mean_midpoint", "x_variance_midpoint")
PILOT_REFERENCE = {"worst_rank_rhat": 1.0158, "min_bulk_ess_rounded": 543,
                   "passed_exploratory_screen": False,
                   "source_run": SOURCE_RUN, "artifact_id": SOURCE_ARTIFACT}


def original_dataset_seed() -> int:
    """Reproduce the predeclared stage-0 replicate-1 generating seed exactly."""
    return fresh_seed(PILOT_MASTER_SEED, TARGET_REPLICATE)


def summarize_reliability(rows: list[dict]) -> dict:
    """Three separate descriptive denominators; no one-fit calibration claims."""
    if not rows:
        raise ValueError("at least one attempted dataset is needed")
    n = len(rows)
    complete = [r for r in rows if r["status"] == "ok"]
    adequate = [r for r in complete if r["all_functional_screen_passed"]]
    report = {
        "attempts": n, "completed_fits": len(complete),
        "fitting_exceptions": n-len(complete),
        "computational_screen_passes": len(adequate),
        "computational_reliability_denominator": n,
        "conditional_calibration_denominator": len(adequate),
        "end_to_end_reliability_denominator": n,
        "research_only_not_an_independent_sbc_replication": True,
        "posterior_calibration_qualified": False,
        "fixed_parameter_coverage_studied": False,
        "release_authorized": False,
        "targets": {},
    }
    for target in PRIMARY:
        for collection in (complete, adequate):
            if any(target not in r.get("primary_targets", {}) for r in collection):
                raise ValueError("completed attempt lacks prespecified target")
        successes = lambda collection: sum(
            bool(r["primary_targets"][target]["interval_contains_truth"])
            for r in collection)
        report["targets"][target] = {
            "truth_in_interval_completed_fits": successes(complete),
            "truth_in_interval_adequately_sampled": successes(adequate),
            "end_to_end_screen_and_interval_successes": successes(adequate),
            "failed_or_nonconverged_not_dropped_from_end_to_end_denominator": True,
        }
    return report


def run_one() -> dict:
    seed = original_dataset_seed()
    result = {
        "study": STUDY, "replicate": TARGET_REPLICATE, "generation_seed": seed,
        "dataset_identity": "EXACT stage-0 replicate 1, NOT a fresh dataset",
        "original_source": PILOT_REFERENCE, "sample_configuration": CONFIG,
        "status": "failed", "error_type": None, "error": None,
        "all_functional_screen_passed": None,
        "primary_targets": {}, "all_functional_diagnostics": {},
        "fit_wall_seconds_including_compilation": None,
        "posterior_calibration_qualified": False, "release_authorized": False,
    }
    try:
        gaze, truth_mean, truth_cov, _, _ = _known_truth(seed, "matched_rank1")
        began = time.perf_counter()
        idata = _pymc_marginal(
            gaze, dimensions=("x",), noise_sd=(.05,), q=N_BASIS, k=1,
            mean_sd=MEAN_PRIOR_SD, load_sd=.20, draws=CONFIG["draws_per_chain"],
            warmup=CONFIG["warmup_per_chain"], chains=CONFIG["chains"],
            cores=CONFIG["cores"], random_state=seed+202)
        elapsed = time.perf_counter()-began
        functionals = identified_functionals(
            np.asarray(idata.posterior["mean"]),
            np.asarray(idata.posterior["load"]),
            GRID, ("x",), truth_mean[:, None], truth_cov)
        checks = numerical_reference_diagnostics(idata, functionals)
        targets = {}
        for j, target in enumerate(PRIMARY):
            samples, truth = functionals[target]
            targets[target] = {
                "truth": float(truth),
                "truth_rank": rank_in_posterior(samples, truth, seed+4862+j),
                "interval_contains_truth": bool(checks["functionals"][target][
                    "single_dataset_90pct_interval_contains_truth"]),
                "functional_screen_passed": bool(checks["functionals"][target][
                    "passes_declared_functional_screen"]),
            }
        result.update(
            status="ok", primary_targets=targets, all_functional_diagnostics=checks,
            all_functional_screen_passed=bool(checks[
                "all_identified_functionals_pass_exploratory_screen"]),
            fit_wall_seconds_including_compilation=float(elapsed))
    except Exception as exc:
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)[:800]
    return result


def preserve(row: dict, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    summary = summarize_reliability([row])
    evidence = {
        "study": STUDY, "original_dataset_identity_verified_by_seed": True,
        "generating_seed": original_dataset_seed(),
        "sampling_budgets_not_compute_matched": True,
        "comparison_is_diagnostic_not_independent_calibration": True,
        "attempts": 1, "fit_failures": int(row["status"] != "ok"),
        "screen_failures": int(row["status"] == "ok" and
                               not row["all_functional_screen_passed"]),
        "source_sha": os.environ.get("GITHUB_SHA"),
        "posterior_calibration_qualified": False,
        "publication_authorized": False, "release_authorized": False,
    }
    for name, obj in (("case.json", row), ("reliability.json", summary),
                      ("evidence.json", evidence)):
        (out/name).write_text(json.dumps(obj, indent=2, sort_keys=True)+"\n")
    (out/"SHA256SUMS").write_text("".join(
        f"{sha256((out/name).read_bytes()).hexdigest()}  {name}\n"
        for name in ("case.json", "reliability.json", "evidence.json")))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    row = run_one()
    report = preserve(row, args.out)
    print("B6 R2 SAME-DATASET LONG-BUDGET REFIT:",
          json.dumps({"case": row, "reliability": report}, sort_keys=True))
    if row["status"] != "ok":
        raise SystemExit("fitting exception: source artifacts retained")


if __name__ == "__main__":
    main()
