"""R40: independent-Gaussian-source numerical falsification of R39's optimizer result.

Eight new independent primitive generating blocks, not eight per paired condition.
R39 raw NLL, positive log nuisance ratios vs positive linear nuisance ratios.
All fixed-slope fits, solver exceptions, near-best and KKT failures are outcomes.
No LRT, statistical confidence interval, simultaneous band or release authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import run_w3_r17_fresh_feasibility as fresh
from scripts import run_w3_r29_predictor_spread_recovery as counterfactual
from scripts import run_w3_r39_nuisance_coordinate_audit as prior
from scripts.w3_r20_estimated_working_target import observed_weighted_rows
from scripts.w3_r25_gaussian_reml_components import prepare_reml_design

STUDY = "W3_R40_FRESH_SOURCE_LINEAR_VS_LOG_NUISANCE_REML"
MASTER_SEED = 202610164040
BLOCKS = 8
PARTICIPANTS = 24
SUPPORT = ("ordinary_dependent", "extreme_dependent")
STATES = ("zero_slope", "positive_slope")
SLOPE_RATIOS = (0., .75)
# Frozen observed-data-blind starts, in ratio to each source's observed variance.
SEED_RATIOS = {
    "interior": (.2, .2, 1.),
    "intercept_near_lower": (prior.LOW * 1.01, .5, 1.),
    "trial_near_lower": (.5, prior.LOW * 1.01, 1.),
}
METHODS = ("log_variances", "linear_variance_ratios")
OBJECTIVE_OFFSET = "raw_NLL"
NLL_NEAR_BEST = 1e-3
PHYSICAL_PROJECTED_KKT_TOL = 1e-3
PLANNED_CASES = BLOCKS * len(SUPPORT) * len(STATES)
PLANNED_PROFILE_CELLS = PLANNED_CASES * len(SLOPE_RATIOS)
PLANNED_FITS = PLANNED_PROFILE_CELLS * len(SEED_RATIOS) * len(METHODS)


def independent_source(block, support, state):
    """Reconstruct paired genuine null/positive trajectories from fresh primitives."""
    if (type(block) is not int or block not in range(BLOCKS)
            or support not in SUPPORT or state not in STATES):
        raise ValueError("R40 source outside frozen independent design")
    original = fresh.fresh_source(
        block, support, n=PARTICIPANTS, master_seed=MASTER_SEED,
        n_blocks=BLOCKS, max_n=PARTICIPANTS
    )
    if state == "positive_slope":
        return original
    raw = dict(original[0])
    raw["participant_slope"] = np.zeros_like(raw["participant_slope"])
    return counterfactual.rescaled_source((raw, *original[1:]), 1.)


def prepare_case(block, support, state):
    case = independent_source(block, support, state)
    X, y, weight, cluster, time, trial, x = observed_weighted_rows(
        (None, case[1], case[2], case[3], case[4], None), "legendre5"
    )
    prepared = prepare_reml_design(
        X, y, weight, cluster, time, trial, x, slope="predictor_scaled_slope"
    )
    Z = X * np.sqrt(weight)[:, None]
    beta = np.linalg.lstsq(Z, y * np.sqrt(weight), rcond=None)[0]
    reference = max(float(np.mean((y - X @ beta) ** 2)), 1e-8)
    if not np.isfinite(reference) or reference <= 0:
        raise ValueError("nonfinite observable reference variance")
    return prepared, reference, len(y)


def evaluate(block, support, state):
    row = {
        "study": STUDY, "source_block": block,
        "source_support": support, "true_slope_state": state,
        "fresh_master_seed": MASTER_SEED,
        "primitive_block_not_independent_across_paired_cells": True,
        "observed_data_only_used_for_estimation": True,
        "source_status": "failed", "source_error": None, "profiles": [],
        "global_optimum_certified": False,
        "nominal_CI_or_test_evaluated": False,
        "release_authorized": False,
    }
    try:
        prep, ref, n = prepare_case(block, support, state)
        row.update(
            source_status="ok", reference_observed_variance=float(ref),
            native_observed_points=int(n)
        )
    except Exception as exc:
        row["source_error"] = {
            "type": type(exc).__name__, "message": str(exc)[:600]
        }
        return row

    for slope_ratio in SLOPE_RATIOS:
        profile = {"slope_variance_ratio": float(slope_ratio), "fits": []}
        for start_name, start_ratios in SEED_RATIOS.items():
            for method in METHODS:
                try:
                    out = prior.fit_one(
                        prep, ref, slope_ratio, np.log(np.asarray(start_ratios)),
                        start_name, method, OBJECTIVE_OFFSET, 0.
                    )
                except Exception as exc:
                    out = {
                        "fixed_slope_ratio": float(slope_ratio),
                        "nuisance_start": start_name,
                        "parameterization": method,
                        "objective_offset": OBJECTIVE_OFFSET,
                        "status": "failed",
                        "error": {
                            "type": type(exc).__name__,
                            "message": str(exc)[:600]
                        }
                    }
                profile["fits"].append(out)

        ok = [
            z for z in profile["fits"]
            if z.get("status") == "ok"
            and np.isfinite(z.get("gaussian_restricted_NLL", np.nan))
        ]
        profile["successful_fit_count"] = len(ok)
        profile["failed_or_nonconverged_count"] = (
            len(profile["fits"]) - len(ok)
        )
        if ok:
            best = min(z["gaussian_restricted_NLL"] for z in ok)
            profile["best_observed_successful_NLL"] = float(best)
            for fit in profile["fits"]:
                if fit.get("status") == "ok":
                    gap = float(fit["gaussian_restricted_NLL"] - best)
                    fit["NLL_gap_from_best_observed"] = gap
                    fit["within_frozen_near_best_tolerance"] = bool(
                        gap <= NLL_NEAR_BEST
                    )
                    fit["passes_physical_KKT_diagnostic"] = bool(
                        fit["shared_ratio_projected_KKT_absmax"]
                        <= PHYSICAL_PROJECTED_KKT_TOL
                    )
        row["profiles"].append(profile)
    return row


def summarize(rows):
    expected = {
        (b, support, state)
        for b in range(BLOCKS) for support in SUPPORT for state in STATES
    }
    keys = [
        (z["source_block"], z["source_support"], z["true_slope_state"])
        for z in rows
    ]
    if len(set(keys)) != len(keys) or not set(keys).issubset(expected):
        raise ValueError("duplicate or unregistered R40 independent block")
    fits = [
        f for r in rows for profile in r["profiles"]
        for f in profile["fits"]
    ]
    statuses = {"ok", "nonconverged", "failed"}
    if any(f["status"] not in statuses for f in fits):
        raise ValueError("unregistered R40 optimizer status")
    cells = {}
    for method in METHODS:
        relevant = [f for f in fits if f["parameterization"] == method]
        cells[method] = {
            "planned_fit_count": PLANNED_FITS // len(METHODS),
            "recorded_fit_count": len(relevant),
            "converged_count": sum(x["status"] == "ok" for x in relevant),
            "optimizer_failure_or_nonconvergence_count": sum(
                x["status"] != "ok" for x in relevant
            ),
            "converged_near_best_observed_count": sum(
                x.get("within_frozen_near_best_tolerance") is True
                for x in relevant
            ),
            "converged_inferior_NLL_count": sum(
                x.get("within_frozen_near_best_tolerance") is False
                for x in relevant if x["status"] == "ok"
            ),
            "converged_exceeding_physical_KKT_tolerance_count": sum(
                x.get("passes_physical_KKT_diagnostic") is False
                for x in relevant if x["status"] == "ok"
            ),
        }

    both_fit_pairs = []
    for r in rows:
        for prof in r["profiles"]:
            for start in SEED_RATIOS:
                pair = {
                    method: next(
                        (z for z in prof["fits"]
                         if z["parameterization"] == method
                         and z["nuisance_start"] == start), None
                    ) for method in METHODS
                }
                if (all(v is not None and v["status"] == "ok"
                        for v in pair.values())):
                    both_fit_pairs.append(
                        float(pair["linear_variance_ratios"][
                            "gaussian_restricted_NLL"
                        ] - pair["log_variances"]["gaussian_restricted_NLL"])
                    )

    full = (
        len(rows) == PLANNED_CASES
        and len(fits) == PLANNED_FITS
        and all(r["source_status"] == "ok" for r in rows)
    )
    strict_gate = (
        full and all(
            v["optimizer_failure_or_nonconvergence_count"] == 0
            and v["converged_inferior_NLL_count"] == 0
            and v["converged_exceeding_physical_KKT_tolerance_count"] == 0
            for v in cells.values()
        )
    )
    return {
        "study": STUDY,
        "source_seed": MASTER_SEED,
        "independent_primitive_generating_blocks": BLOCKS,
        "participant_count_per_source": PARTICIPANTS,
        "paired_support_conditions": SUPPORT,
        "paired_true_slope_states": STATES,
        "planned_source_cases": PLANNED_CASES,
        "recorded_source_cases": len(rows),
        "missing_source_cases": len(expected-set(keys)),
        "source_errors": sum(r["source_status"] != "ok" for r in rows),
        "prespecified_slope_variance_ratios": SLOPE_RATIOS,
        "prespecified_observed_data_blind_nuisance_start_ratios": SEED_RATIOS,
        "planned_fixed_profile_cells": PLANNED_PROFILE_CELLS,
        "recorded_fixed_profile_cells": sum(len(r["profiles"]) for r in rows),
        "planned_optimizer_fits": PLANNED_FITS,
        "recorded_optimizer_fits": len(fits),
        "paired_same_start_cases_both_converged": len(both_fit_pairs),
        "paired_linear_minus_log_NLL_median": (
            float(np.median(both_fit_pairs)) if both_fit_pairs else None
        ),
        "paired_linear_lower_NLL_count": sum(
            x < -NLL_NEAR_BEST for x in both_fit_pairs
        ),
        "paired_log_lower_NLL_count": sum(
            x > NLL_NEAR_BEST for x in both_fit_pairs
        ),
        "failure_inclusive_numerical_gate_passed": bool(strict_gate),
        "gate_is_preliminary_numerical_not_statistical": True,
        "global_optimization_certified": False,
        "boundary_variance_test_calibrated": False,
        "covariance_estimation_aware_functional_CR2_CI": False,
        "simultaneous_functional_bands_calibrated": False,
        "public_API_or_release_authorized": False,
        "method_cells": cells,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    rows = [
        evaluate(block, support, state)
        for block in range(BLOCKS)
        for support in SUPPORT for state in STATES
    ]
    report = summarize(rows)
    for filename, contents in (
        ("cases.json", rows), ("summary.json", report)
    ):
        (args.out / filename).write_text(
            json.dumps(contents, indent=2, sort_keys=True, allow_nan=False) + "\n"
        )
    (args.out / "source-commit.txt").write_text(
        os.getenv("GITHUB_SHA", "unverified-local") + "\n"
    )
    files = ("cases.json", "summary.json", "source-commit.txt")
    (args.out / "SHA256SUMS").write_text(
        "".join(
            hashlib.sha256((args.out / f).read_bytes()).hexdigest()
            + "  " + f + "\n"
            for f in files
        )
    )
    print("R40 INDEPENDENT SOURCE NUMERICAL AUDIT:",
          json.dumps(report, sort_keys=True))
    if (report["missing_source_cases"] or report["source_errors"]
            or report["recorded_optimizer_fits"] != PLANNED_FITS):
        raise SystemExit("R40 source integrity failed; original failures retained")


if __name__ == "__main__":
    main()
