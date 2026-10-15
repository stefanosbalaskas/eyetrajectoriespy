"""R38: independent fixed-slope profile audit of R37 multistart disagreements.

A DETERMINISTIC DIAGNOSTIC REUSE of R37 seed/block 2, not a new simulation,
inference test, independent replication, confidence interval, or release gate.
Two genuine R37 disagreements are preserved as unfiltered input. At each
predeclared slope ratio, reoptimize nuisance variances from TWO empirically
different R37 starting configurations, retaining every fit and score.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np
from scipy.optimize import minimize

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import run_w3_r35_slope_boundary_profiles as r35
from scripts import run_w3_r37_continuous_boundary_reml as r37
from scripts.w3_r20_estimated_working_target import observed_weighted_rows
from scripts.w3_r25_gaussian_reml_components import (
    LOWER_LOG_RATIO, UPPER_LOG_RATIO, prepare_reml_design,
)

STUDY = "W3_R38_R37_SAME_SOURCE_DUAL_SEED_PROFILE_GEOMETRY"
REUSED_SEED = r37.MASTER_SEED
BLOCK = 2  # The sole original block with both R37 positive-source discrepancies.
SUPPORT = r37.SUPPORT
STATES = r37.STATES
# Fixed before running: both R37 problematic ratios 1.73204 and 3.55363
# fall within the profiled interval. Not adaptively extended after seeing R38.
PROFILE_RATIOS = (
    0., 0.001, 0.01, 0.05, 0.1, 0.2, 0.4, 0.6, 0.7, 0.75,
    1., 1.5, 1.75, 2., 2.5, 3., 3.5, 4., 6., 10.,
)
SEED_LABELS = ("best_r37", "worst_r37")
PLANNED_CASES = len(SUPPORT) * len(STATES)
PLANNED_FITS = PLANNED_CASES * len(PROFILE_RATIOS) * len(SEED_LABELS)
OBJECTIVE_DISAGREEMENT_TOL = 1e-3
GLOBAL_REFERENCE_TOL = 1e-4
KKT_DIAGNOSTIC_TOL = 1e-4


def projected_gradient(gradient, location, bounds, edge_tol=1e-7):
    """KKT residual for minimizing with coordinatewise box constraints."""
    g = np.asarray(gradient, dtype=float)
    x = np.asarray(location, dtype=float)
    if g.shape != x.shape or len(bounds) != len(g):
        raise ValueError("KKT vector/bounds shape mismatch")
    out = g.copy()
    for j, (lower, upper) in enumerate(bounds):
        if x[j] < lower-edge_tol or x[j] > upper+edge_tol:
            raise ValueError("KKT location violates optimization bounds")
        if x[j] <= lower+edge_tol:
            out[j] = min(g[j], 0.)
        elif x[j] >= upper-edge_tol:
            out[j] = max(g[j], 0.)
    return out


def parameters_from_start(start, reference):
    """Reconstitute an R37 full-parameter candidate from observed-only output."""
    return np.array([
        np.log(float(start["free_component_estimates"][r37.COMPONENTS[k]]) / reference)
        for k in r37.FREE
    ] + [float(start["slope_variance_to_reference"])], dtype=float)


def examine_continuous_candidate(start, prepared, reference):
    pars = parameters_from_start(start, reference)
    value, grad = r37.continuous_reml_objective(pars, prepared, reference)
    bounds = [(LOWER_LOG_RATIO, UPPER_LOG_RATIO)] * 3 + [(0., r37.MAX_RATIO)]
    kkt = projected_gradient(grad, pars, bounds)
    return {
        "R37_initial_ratio": start["initial_slope_ratio"],
        "R37_optimizer_success": start["optimizer_success"],
        "R37_objective": start["objective"],
        "recomputed_objective": float(value),
        "objective_reconstruction_absolute_difference": abs(value-start["objective"]),
        "candidate_slope_ratio": float(pars[3]),
        "slope_score": float(grad[3]),
        "max_projected_KKT_residual": float(np.max(np.abs(kkt))),
        "KKT_under_predeclared_tolerance": bool(np.max(np.abs(kkt)) <= KKT_DIAGNOSTIC_TOL),
    }


def profile_once(prepared, reference, ratio, nuisance_start, seed_label):
    """Independent R35 fixed-slope likelihood/score with explicit seed."""
    out = {
        "fixed_slope_ratio": float(ratio), "nuisance_seed": seed_label,
        "status": "failed", "error": None,
    }
    try:
        start = np.array([
            np.log(np.clip(
                float(nuisance_start["free_component_estimates"][r37.COMPONENTS[k]])/reference,
                np.exp(LOWER_LOG_RATIO)*1.01,
                np.exp(UPPER_LOG_RATIO)/1.01,
            )) for k in r37.FREE
        ])
        res = minimize(
            r35.fixed_slope_reml_objective, start,
            args=(prepared, reference, float(ratio)),
            method="L-BFGS-B", jac=True,
            bounds=[(LOWER_LOG_RATIO, UPPER_LOG_RATIO)]*3,
            options={"maxiter":200, "ftol":1e-11, "gtol":1e-7, "maxls":35},
        )
        finite = bool(np.isfinite(res.fun) and np.isfinite(res.x).all() and
                      np.isfinite(res.jac).all())
        out.update(
            status="ok" if res.success and finite else "nonconverged",
            optimizer_success=bool(res.success),
            optimizer_message=str(res.message),
            iterations=int(res.nit),
            negative_restricted_loglik=float(res.fun) if finite else None,
            slope_score=None,
            max_projected_nuisance_KKT_residual=None,
        )
        if finite:
            full = np.r_[res.x, ratio]
            obj, grad = r37.continuous_reml_objective(full, prepared, reference)
            proj = projected_gradient(
                grad[:3], res.x, [(LOWER_LOG_RATIO, UPPER_LOG_RATIO)]*3
            )
            out.update(
                independently_recomputed_objective=float(obj),
                absolute_objective_crosscheck=float(abs(obj-res.fun)),
                slope_score=float(grad[3]),
                max_projected_nuisance_KKT_residual=float(np.max(np.abs(proj))),
                free_log_variance_ratios=[float(v) for v in res.x],
                nuisance_bounds_active=bool(
                    np.any(np.abs(res.x-LOWER_LOG_RATIO) < 1e-6) or
                    np.any(np.abs(res.x-UPPER_LOG_RATIO) < 1e-6)),
            )
    except Exception as exc:
        out["error"] = {"type": type(exc).__name__, "message": str(exc)[:500]}
    return out


def evaluate(support, state):
    row = {
        "study": STUDY, "source_block": BLOCK,
        "support": support, "true_state": state,
        "reuses_R37_original_gaussian_source": True,
        "independent_replication": False,
        "base_status": "failed", "base_error": None,
        "original_starts": [], "profile_points": [],
        "candidate_diagnostics": [],
        "no_global_optimum_certification": True,
        "no_statistical_test_or_coefficient_CI": True,
        "release_authorized": False,
    }
    try:
        original = r37.evaluate(BLOCK, support, state)
        row["original_starts"] = original["optimizations"]
        row["original_r37_status"] = original["continuous_reference_status"]
        if original["continuous_reference_status"] != "computed":
            row["base_error"] = "R37 reference incomplete; no selected-only repair"
            return row
        case = r37.source(BLOCK, support, state)
        X,y,w,g,t,tr,x = observed_weighted_rows(
            (None,case[1],case[2],case[3],case[4],None), "legendre5"
        )
        prepared = prepare_reml_design(
            X,y,w,g,t,tr,x,slope="predictor_scaled_slope"
        )
        reference = float(original["reference_variance"])
        successes = [v for v in original["optimizations"] if v["status"] == "ok"]
        if len(successes) != len(r37.RATIO_STARTS):
            row["base_error"] = "one or more R37 starts incomplete"
            return row
        best = min(successes, key=lambda z:z["objective"])
        worst = max(successes, key=lambda z:z["objective"])
        for start in successes:
            row["candidate_diagnostics"].append(
                examine_continuous_candidate(start, prepared, reference)
            )
        row["base_status"] = "ok"
        row["R37_objective_spread"] = float(worst["objective"]-best["objective"])
        row["R37_best_objective"] = float(best["objective"])
        row["R37_worst_objective"] = float(worst["objective"])
        row["R37_best_ratio"] = float(best["slope_variance_to_reference"])
        row["R37_worst_ratio"] = float(worst["slope_variance_to_reference"])
        for ratio in PROFILE_RATIOS:
            points = [
                profile_once(prepared, reference, ratio, seed, label)
                for label,seed in zip(SEED_LABELS,(best,worst))
            ]
            valid = [p for p in points if p["status"] == "ok"]
            diff = (abs(points[0]["negative_restricted_loglik"] -
                        points[1]["negative_restricted_loglik"])
                    if len(valid) == 2 else None)
            row["profile_points"].append({
                "fixed_slope_ratio":float(ratio),
                "fits":points,
                "best_fitted_objective":min(
                    (p["negative_restricted_loglik"] for p in valid),default=None
                ),
                "dual_nuisance_start_objective_difference":diff,
                "dual_seed_disagreement":(
                    bool(diff > OBJECTIVE_DISAGREEMENT_TOL)
                    if diff is not None else None
                ),
            })
        good = [z["best_fitted_objective"] for z in row["profile_points"]
                if z["best_fitted_objective"] is not None]
        row["profile_complete"] = all(
            all(z["status"] == "ok" for z in p["fits"])
            for p in row["profile_points"]
        )
        row["best_evaluated_fixed_slope_nll"] = min(good) if good else None
        row["fixed_profile_beats_R37_best"] = (
            bool(min(good) < best["objective"]-GLOBAL_REFERENCE_TOL)
            if good else None
        )
        row["dual_seed_disagreement_count"] = sum(
            x["dual_seed_disagreement"] is True for x in row["profile_points"]
        )
    except Exception as exc:
        row["base_error"] = {"type":type(exc).__name__, "message":str(exc)[:600]}
    return row


def summarize(rows):
    keys = [(r["source_block"],r["support"],r["true_state"]) for r in rows]
    expected = {(BLOCK,s,t) for s in SUPPORT for t in STATES}
    if len(set(keys)) != len(keys) or not set(keys).issubset(expected):
        raise ValueError("duplicate or unregistered R38 source cell")
    all_points = [p for r in rows for p in r["profile_points"]]
    all_fits = [x for p in all_points for x in p["fits"]]
    return {
        "study":STUDY, "reused_R37_original_seed":REUSED_SEED,
        "independent_generating_blocks_in_R38":0,
        "original_source_blocks_reused":1, "source_block":BLOCK,
        "planned_paired_cases":PLANNED_CASES, "recorded_paired_cases":len(rows),
        "missing_cases":len(expected-set(keys)),
        "base_failure_count":sum(r["base_status"] != "ok" for r in rows),
        "predeclared_profile_ratios":PROFILE_RATIOS,
        "planned_dual_seed_profile_fits":PLANNED_FITS,
        "recorded_profile_fits":len(all_fits),
        "failed_or_nonconverged_profile_fits":sum(
            x["status"] != "ok" for x in all_fits
        ),
        "dual_seed_disagreement_points":sum(
            p["dual_seed_disagreement"] is True for p in all_points
        ),
        "fixed_profiles_better_than_R37_best_count":sum(
            r.get("fixed_profile_beats_R37_best") is True for r in rows
        ),
        "R37_continuous_start_disagreement_cases":sum(
            r.get("R37_objective_spread",0.) > OBJECTIVE_DISAGREEMENT_TOL
            for r in rows
        ),
        "projected_KKT_failures_among_R37_candidates":sum(
            not z["KKT_under_predeclared_tolerance"]
            for r in rows for z in r["candidate_diagnostics"]
        ),
        "numerical_diagnostic_only":True,
        "no_certified_global_optimum":True,
        "no_type_I_or_power_inference":True,
        "no_CR2_or_functional_CI":True, "release_authorized":False,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    rows = [evaluate(s,t) for s in SUPPORT for t in STATES]
    summary = summarize(rows)
    for filename,obj in (("cases.json",rows),("summary.json",summary)):
        (a.out/filename).write_text(json.dumps(
            obj,indent=2,sort_keys=True,allow_nan=False)+"\n")
    (a.out/"source-commit.txt").write_text(
        os.environ.get("GITHUB_SHA","unverified-local")+"\n")
    names = ("cases.json","summary.json","source-commit.txt")
    (a.out/"SHA256SUMS").write_text("".join(
        hashlib.sha256((a.out/f).read_bytes()).hexdigest()+"  "+f+"\n"
        for f in names
    ))
    print("R38 DUAL START PROFILE AUDIT:",json.dumps(summary,sort_keys=True))
    if summary["missing_cases"] or summary["base_failure_count"] or (
        summary["recorded_profile_fits"] != PLANNED_FITS
    ):
        raise SystemExit("R38 incomplete; retain failure artifacts")


if __name__ == "__main__":
    main()
