"""R42 fresh independent Gaussian-source numerical evaluation of frozen R41 restarts.

Eight NEW independent primitive Gaussian generating blocks. Complete factorial
on the exact R40 support/state/fixed-slope/observed-blind-start design, raw
physical positive nuisance variance ratios. Every stage's status is retained.
No fitted-covariance CR2 inference, boundary significance test, or release.
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
from scripts import run_w3_r39_nuisance_coordinate_audit as r39
from scripts import run_w3_r40_fresh_source_nuisance as r40
from scripts import run_w3_r41_targeted_kkt_refinement as r41
from scripts.w3_r20_estimated_working_target import observed_weighted_rows
from scripts.w3_r25_gaussian_reml_components import prepare_reml_design

STUDY = "W3_R42_FRESH_INDEPENDENT_FULL_FACTORIAL_KKT_RESTART_CROSSCHECK"
MASTER_SEED = 202610164242
BLOCKS = 8
PARTICIPANTS = 24
SUPPORT = r40.SUPPORT
STATES = r40.STATES
SLOPE_RATIOS = r40.SLOPE_RATIOS
SEED_RATIOS = r40.SEED_RATIOS
METHODS = r41.METHODS
KKT_TOL = 1e-3
NLL_TOL = 1e-3
RECONSTRUCTION_TOL = 1e-6
PLANNED_CASES = BLOCKS * len(SUPPORT) * len(STATES)
PLANNED_PROFILES = PLANNED_CASES * len(SLOPE_RATIOS)
PLANNED_STARTS = PLANNED_PROFILES * len(SEED_RATIOS)
PLANNED_FITS = PLANNED_STARTS * len(METHODS)


def independent_source(block, support, state):
    """Only eight independent *primitive* blocks; variants share innovations."""
    if (type(block) is not int or block not in range(BLOCKS)
            or support not in SUPPORT or state not in STATES):
        raise ValueError("R42 independent source outside frozen design")
    original = fresh.fresh_source(
        block, support, n=PARTICIPANTS, master_seed=MASTER_SEED,
        n_blocks=BLOCKS, max_n=PARTICIPANTS,
    )
    if state == "positive_slope":
        return original
    raw = dict(original[0])
    raw["participant_slope"] = np.zeros_like(raw["participant_slope"])
    return counterfactual.rescaled_source((raw, *original[1:]), 1.)


def prepare_case(block, support, state):
    case = independent_source(block, support, state)
    X, y, w, g, t, tr, x = observed_weighted_rows(
        (None, case[1], case[2], case[3], case[4], None), "legendre5"
    )
    prepared = prepare_reml_design(
        X, y, w, g, t, tr, x, slope="predictor_scaled_slope",
    )
    Z = X * np.sqrt(w)[:, None]
    beta = np.linalg.lstsq(Z, y * np.sqrt(w), rcond=None)[0]
    ref = max(float(np.mean((y - X @ beta) ** 2)), 1e-8)
    if not np.isfinite(ref) or ref <= 0:
        raise ValueError("invalid observed-only R42 Gaussian residual reference")
    return prepared, ref, len(y)


def failed_stage(name, code):
    return {
        "algorithm": name, "status": "not_attempted",
        "optimizer_success": False,
        "message": code, "fit": None,
        "error": code,
    }


def original_fit(prepared, reference, slope, start_name):
    raw = r39.fit_one(
        prepared, reference, slope,
        np.log(np.asarray(SEED_RATIOS[start_name], dtype=float)),
        start_name, "linear_variance_ratios", "raw_NLL", 0.,
    )
    if raw["status"] != "ok":
        return {
            "algorithm": METHODS[0], "status": raw["status"],
            "optimizer_success": bool(raw.get("optimizer_success", False)),
            "message": raw.get("optimizer_message", ""),
            "fit": None, "error": raw.get("error"),
        }, None
    baseline = {
        "algorithm": METHODS[0], "status": "ok",
        "optimizer_success": True,
        "message": raw.get("optimizer_message", ""),
        "iterations": raw.get("iterations"),
        "error": None,
        "fit": {
            "original_unshifted_NLL": raw["gaussian_restricted_NLL"],
            "optimizer_objective_reconstruction_abs_error":
                raw["objective_reconstruction_error"],
            "nuisance_variance_ratios": raw["nuisance_variance_ratios"],
            "physical_ratio_projected_KKT_absmax":
                raw["shared_ratio_projected_KKT_absmax"],
            "passes_frozen_physical_KKT": bool(
                raw["shared_ratio_projected_KKT_absmax"] <= KKT_TOL
            ),
        },
    }
    return baseline, raw


def evaluate(block, support, state):
    row = {
        "study": STUDY, "block": block,
        "support": support, "source_state": state,
        "independent_primitive_block_count": BLOCKS,
        "NEW_master_seed": MASTER_SEED,
        "paired_within_block_not_independent_across_conditions": True,
        "source_status": "failed", "source_error": None,
        "profiles": [], "no_estimator_or_release_qualification": True,
    }
    try:
        prep, ref, n = prepare_case(block, support, state)
        row.update(
            source_status="ok", observed_only_reference_variance=float(ref),
            native_observed_points=int(n),
        )
    except Exception as exc:
        row["source_error"] = {
            "type": type(exc).__name__, "message": str(exc)[:500],
        }
        return row

    for slope in SLOPE_RATIOS:
        profile = {
            "fixed_slope_variance_ratio": float(slope),
            "starting_configurations": [],
        }
        for start_name in SEED_RATIOS:
            trial = {"initialization": start_name, "fits": []}
            try:
                baseline, original = original_fit(prep, ref, slope, start_name)
            except Exception as exc:
                baseline = {
                    "algorithm": METHODS[0], "status": "failed",
                    "optimizer_success": False, "fit": None,
                    "error": {"type": type(exc).__name__,
                              "message": str(exc)[:500]},
                }
                original = None
            trial["fits"].append(baseline)
            for method in METHODS[1:]:
                if original is None:
                    trial["fits"].append(
                        failed_stage(method, "baseline_failed_explicit_refusal")
                    )
                else:
                    trial["fits"].append(
                        r41.restart(original, prep, ref, slope, method)
                    )
            profile["starting_configurations"].append(trial)

        all_fits = [
            f for trial in profile["starting_configurations"]
            for f in trial["fits"]
        ]
        successful = [
            f for f in all_fits
            if f["status"] == "ok" and f.get("fit") is not None
            and np.isfinite(f["fit"]["original_unshifted_NLL"])
        ]
        profile["successful_optimization_count"] = len(successful)
        profile["failed_nonconverged_or_refused_count"] = (
            len(all_fits) - len(successful)
        )
        if successful:
            best = min(
                f["fit"]["original_unshifted_NLL"] for f in successful
            )
            profile["best_observed_unshifted_NLL"] = float(best)
            for f in all_fits:
                if f["status"] == "ok" and f.get("fit") is not None:
                    score = f["fit"]
                    score["NLL_gap_from_best_observed"] = float(
                        score["original_unshifted_NLL"] - best
                    )
                    score["near_best_observed_NLL"] = bool(
                        score["NLL_gap_from_best_observed"] <= NLL_TOL
                    )
        row["profiles"].append(profile)
    return row


def summarize(rows):
    expected = {
        (block, support, state)
        for block in range(BLOCKS)
        for support in SUPPORT for state in STATES
    }
    keys = [(r["block"], r["support"], r["source_state"]) for r in rows]
    if len(keys) != len(set(keys)) or not set(keys).issubset(expected):
        raise ValueError("unregistered or duplicated R42 source condition")
    trial_records = [
        t for r in rows for p in r["profiles"]
        for t in p["starting_configurations"]
    ]
    fits = [f for t in trial_records for f in t["fits"]]
    if any(
        len(t["fits"]) != len(METHODS) or
        tuple(f["algorithm"] for f in t["fits"]) != METHODS
        for t in trial_records
    ):
        raise ValueError("R42 stage selection or ordering contract violated")
    cells = {}
    for method in METHODS:
        selected = [
            f for f in fits if f["algorithm"] == method
        ]
        successful = [
            f for f in selected
            if f["status"] == "ok" and f.get("fit") is not None
        ]
        cells[method] = {
            "planned_fit_count": PLANNED_STARTS,
            "recorded_fit_count": len(selected),
            "successful_fit_count": len(successful),
            "nonconverged_failed_or_refused_count":
                len(selected) - len(successful),
            "near_best_observed_count": sum(
                f["fit"].get("near_best_observed_NLL") is True
                for f in successful
            ),
            "worse_than_NLL_0_001_count": sum(
                f["fit"].get("near_best_observed_NLL") is False
                for f in successful
            ),
            "passed_physical_KKT_0_001_count": sum(
                f["fit"]["passes_frozen_physical_KKT"]
                for f in successful
            ),
            "failed_physical_KKT_0_001_count": sum(
                not f["fit"]["passes_frozen_physical_KKT"]
                for f in successful
            ),
            "max_physical_projected_KKT_among_successes": max(
                (f["fit"]["physical_ratio_projected_KKT_absmax"]
                 for f in successful), default=None
            ),
        }
    pairings = {}
    for method in METHODS[1:]:
        differences = []
        for trial in trial_records:
            baseline = trial["fits"][0]
            follow = next(f for f in trial["fits"] if f["algorithm"] == method)
            if baseline["status"] == follow["status"] == "ok":
                differences.append(float(
                    follow["fit"]["original_unshifted_NLL"]
                    - baseline["fit"]["original_unshifted_NLL"]
                ))
        pairings[method] = {
            "paired_successful_comparisons": len(differences),
            "improved_baseline_NLL_by_more_than_0_001": sum(
                d < -NLL_TOL for d in differences
            ),
            "worsened_baseline_NLL_by_more_than_0_001": sum(
                d > NLL_TOL for d in differences
            ),
            "max_signed_difference": max(differences, default=None),
            "min_signed_difference": min(differences, default=None),
        }

    full = (
        len(rows) == PLANNED_CASES
        and len(trial_records) == PLANNED_STARTS
        and len(fits) == PLANNED_FITS
        and all(r["source_status"] == "ok" for r in rows)
    )
    strict_by_method = {
        method: bool(
            full
            and stats["nonconverged_failed_or_refused_count"] == 0
            and stats["worse_than_NLL_0_001_count"] == 0
            and stats["failed_physical_KKT_0_001_count"] == 0
        )
        for method, stats in cells.items()
    }
    return {
        "study": STUDY,
        "fresh_primitive_master_seed": MASTER_SEED,
        "new_independent_primitive_blocks": BLOCKS,
        "participants_per_block": PARTICIPANTS,
        "paired_support_conditions": SUPPORT,
        "paired_true_slope_states": STATES,
        "fixed_slope_variance_ratios": SLOPE_RATIOS,
        "prespecified_start_ratios": SEED_RATIOS,
        "planned_source_conditions": PLANNED_CASES,
        "recorded_source_conditions": len(rows),
        "missing_source_conditions": len(expected - set(keys)),
        "failed_source_conditions": sum(
            r["source_status"] != "ok" for r in rows
        ),
        "planned_start_evaluations": PLANNED_STARTS,
        "recorded_start_evaluations": len(trial_records),
        "planned_optimizer_stage_records": PLANNED_FITS,
        "recorded_optimizer_stage_records": len(fits),
        "all_source_conditions_and_stages_recorded": bool(full),
        "prespecified_raw_physical_KKT_tolerance": KKT_TOL,
        "prespecified_NLL_tolerance": NLL_TOL,
        "method_cells": cells,
        "same_start_paired_NLL_comparisons": pairings,
        "preliminary_numerical_gates": strict_by_method,
        "preliminary_numerical_only_not_statistical": True,
        "no_global_optimizer_certificate": True,
        "no_boundary_variance_test_calibration": True,
        "no_fitted_covariance_CR2_functional_CI": True,
        "no_simultaneous_functional_band_qualification": True,
        "release_authorized": False,
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
    summary = summarize(rows)
    for name, object_value in (
        ("cases.json", rows), ("summary.json", summary)
    ):
        (args.out / name).write_text(
            json.dumps(object_value, indent=2, sort_keys=True,
                       allow_nan=False) + "\n"
        )
    (args.out / "source-commit.txt").write_text(
        os.environ.get("GITHUB_SHA", "unverified-local") + "\n"
    )
    names = ("cases.json", "summary.json", "source-commit.txt")
    (args.out / "SHA256SUMS").write_text("".join(
        hashlib.sha256((args.out / n).read_bytes()).hexdigest()
        + "  " + n + "\n" for n in names
    ))
    print("R42 INDEPENDENT SOURCE KKT AUDIT:",
          json.dumps(summary, sort_keys=True))
    if not summary["all_source_conditions_and_stages_recorded"]:
        raise SystemExit("R42 source or stage integrity refusal; evidence retained")


if __name__ == "__main__":
    main()
