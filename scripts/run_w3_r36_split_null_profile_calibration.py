"""R36 split-source empirical calibration of an EXACT-ZERO Gaussian REML profile GRID.

Sixteen NEW independent primitive Gaussian generating blocks; first eight are
null calibration and last eight are strictly independent held-out evaluation
blocks. n24 and ordinary/extreme predictor-dependent covariance; true random
slope Gaussian innovation is exactly removed for the null source, while
positive source preserves its originally drawn slope. At each source, seven
predeclared slope variance grid points (including mathematical zero) have
their other three Gaussian components reoptimized (R35).

This calibrates ONLY the specifically defined finite-grid profile statistic;
not the continuous-slope likelihood-ratio test and not a chi-square reference.
Eight training null blocks per design cannot qualify nominal type-I error.
No regression-coefficient confidence intervals, no covariance-adjusted CR2,
no simultaneous bands, no stable API or package release.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts import run_w3_r16_leverage_covariance_factorial as r16
from scripts import run_w3_r17_fresh_feasibility as fresh
from scripts import run_w3_r29_predictor_spread_recovery as counterfactual
from scripts import run_w3_r35_slope_boundary_profiles as r35
from scripts.w3_r20_estimated_working_target import observed_weighted_rows
from scripts.w3_r25_gaussian_reml_components import (
    estimate_reml_components, prepare_reml_design)

STUDY="W3_R36_SPLIT_SOURCE_ZERO_SLOPE_PROFILE_GRID_CALIBRATION"
MASTER_SEED=202610163636
BLOCKS=16
N_CALIBRATION=8
PARTICIPANTS=24
SUPPORT=("ordinary_dependent","extreme_dependent")
STATES=("zero_slope","positive_slope")
GRID=r35.SLOPE_VARIANCE_TO_OBSERVED_SCALE
N_GRID=len(GRID)
PLANNED_SOURCE_CASES=2*BLOCKS+2*(BLOCKS-N_CALIBRATION)
PLANNED_GRID_OPTIMIZATIONS=PLANNED_SOURCE_CASES*N_GRID
TARGET_NULL_TAIL=.10
TRUE_POSITIVE_SLOPE_VARIANCE=float(r16.SIGMA_RANDOM_SLOPE**2)


def source(block,support,state):
    """Null and positive share all primitive draws, native times and predictors."""
    if support not in SUPPORT or state not in STATES:
        raise ValueError("unregistered source support or slope state")
    original=fresh.fresh_source(
        block,support,n=PARTICIPANTS,master_seed=MASTER_SEED,
        n_blocks=BLOCKS,max_n=PARTICIPANTS)
    if state=="positive_slope":
        return original
    raw=dict(original[0])
    raw["participant_slope"]=np.zeros_like(raw["participant_slope"])
    # The R29 reconstruction rebuilds actual observed outcomes, not only X.
    # It preserves the native timestamps, trial labels and other primitives.
    return counterfactual.rescaled_source(
        (raw,*original[1:]),1.0)


def evaluate(block,support,state):
    row={"block":block,"source_support":support,"true_slope_state":state,
         "sample_partition":"calibration" if block<N_CALIBRATION else "heldout",
         "independent_unit":"original_generating_block",
         "generating_slope_variance":(
             0.0 if state=="zero_slope" else TRUE_POSITIVE_SLOPE_VARIANCE),
         "source_generated":False,"source_error":None,
         "reml_status":"not_attempted","reml_error":None,
         "profile_points":[],"profile_status":"not_attempted",
         "grid_statistic":None,"test_decision":None,
         "no_unrestricted_global_mle_claim":True,
         "calibration_is_for_fixed_grid_statistic_only":True,
         "pointwise_functional_coefficient_coverage_evaluated":False,
         "release_authorized":False}
    if state=="positive_slope" and block<N_CALIBRATION:
        raise ValueError("positive alternative calibration blocks excluded by protocol")
    try:
        original=source(block,support,state)
        X,y,w,g,t,tr,x=observed_weighted_rows(
            (None,original[1],original[2],original[3],original[4],None),
            "legendre5")
        prepared=prepare_reml_design(
            X,y,w,g,t,tr,x,slope="predictor_scaled_slope")
        row["source_generated"]=True
        row["native_points"]=len(y)
        row["original_trial_count"]=len(original[1].time)
        if len(np.unique(g))!=PARTICIPANTS:
            raise ValueError("participant source mapping failed")
        if support.startswith("extreme"):
            per=np.asarray([x[np.flatnonzero(g==k)[0]] for k in np.unique(g)])
            if not (per[0]==3. and per[1]==-2.5):
                raise ValueError("extreme original predictor source not preserved")
    except Exception as exc:
        row["source_error"]={"type":type(exc).__name__,
                            "message":str(exc)[:600]}
        return row
    try:
        f=estimate_reml_components(
            X,y,w,g,t,tr,x,slope="predictor_scaled_slope")
        row["reml_status"]=f["status"]
        row["reml_component_near_boundary"]=f["near_boundary_components"]
        row["reml_slope_estimate"]=float(
            f["variance_components"]["participant_slope"])
        row["observed_residual_variance_reference"]=float(
            f["reference_variance_scale_from_observed_residuals"])
        if f["status"]!="ok":
            row["reml_error"]={"type":"NonConvergence",
                               "message":f["optimizer_message"]}
            return row
    except Exception as exc:
        row["reml_status"]="failed"
        row["reml_error"]={"type":type(exc).__name__,
                           "message":str(exc)[:600]}
        return row
    for ratio in GRID:
        point=r35.profile_one(
            prepared,row["observed_residual_variance_reference"],
            f["variance_components"],ratio)
        row["profile_points"].append(point)
    failed=sum(q["status"]!="ok" for q in row["profile_points"])
    if failed:
        row["profile_status"]="incomplete"
        return row
    zero=row["profile_points"][0]
    if not zero["fixed_slope_variance_is_exact_zero"]:
        raise ValueError("frozen grid first point is not exactly zero")
    best=min(q["restricted_negative_loglik"] for q in row["profile_points"])
    nll0=float(zero["restricted_negative_loglik"])
    # The statistic belongs to the FROZEN SEVEN-POINT GRID, not an
    # unrestricted continuous slope-variance likelihood-ratio procedure.
    statistic=float(max(0.,2*(nll0-best)))
    row["grid_statistic"]=statistic
    row["profile_status"]="complete"
    row["zero_is_grid_minimum"]=bool(np.isclose(nll0,best,atol=1e-8,rtol=0))
    row["best_grid_ratio"]=float(min(
        row["profile_points"],
        key=lambda q:q["restricted_negative_loglik"])[
        "fixed_slope_variance_to_observed_scale"])
    return row


def frozen_threshold(values):
    """A discrete empirical upper-tail threshold, no parametric chi-square.

    With eight calibration null values, the frozen conservative upper 90%
    empirical quantile is the largest order statistic. Strict '>' rejection
    avoids falsely rejecting on an exact-zero atom.
    """
    a=np.asarray(values,float)
    if a.shape!=(N_CALIBRATION,) or not np.isfinite(a).all() or np.any(a<0):
        raise ValueError("requires eight completed nonnegative independent null profile statistics")
    return float(np.quantile(a,1-TARGET_NULL_TAIL,method="higher"))


def wilson(k,n):
    if n<=0:
        return None
    from scipy.stats import norm
    z=float(norm.ppf(.975))
    ph=k/n
    den=1+z*z/n
    center=(ph+z*z/(2*n))/den
    width=z*np.sqrt(ph*(1-ph)/n+z*z/(4*n*n))/den
    return [float(max(0,center-width)),float(min(1,center+width))]


def summarize(rows):
    expected={(b,s,"zero_slope") for b in range(BLOCKS) for s in SUPPORT}
    expected|={(b,s,"positive_slope")
              for b in range(N_CALIBRATION,BLOCKS) for s in SUPPORT}
    ids=[(q["block"],q["source_support"],q["true_slope_state"]) for q in rows]
    if len(ids)!=len(set(ids)) or not set(ids).issubset(expected):
        raise ValueError("duplicate or undeclared source calibration identity")
    cells={}
    for support in SUPPORT:
        calibration=[r for r in rows if
            r["source_support"]==support and
            r["true_slope_state"]=="zero_slope" and
            r["sample_partition"]=="calibration"]
        okcal=[r for r in calibration if r["profile_status"]=="complete"]
        threshold=frozen_threshold([r["grid_statistic"] for r in okcal]) if (
            len(okcal)==N_CALIBRATION and len(calibration)==N_CALIBRATION) else None
        outcomes={}
        for state in STATES:
            held=[r for r in rows if
                  r["source_support"]==support and
                  r["sample_partition"]=="heldout" and
                  r["true_slope_state"]==state]
            good=[r for r in held if r["profile_status"]=="complete"]
            hits=sum(r["grid_statistic"]>threshold for r in good) if threshold is not None else None
            outcomes[state]={
                "independent_heldout_blocks":len(held),
                "complete_profile_grid":len(good),
                "failed_or_nonconverged_profile_grid":len(held)-len(good),
                "strict_tail_rejections":hits,
                "rejection_fraction_conditional_on_complete":(
                    float(hits/len(good)) if hits is not None and good else None),
                "rejection_wilson_95pct":wilson(hits,len(good)) if hits is not None else None,
                "joint_success_and_rejection_fraction":(
                    float(hits/len(held)) if hits is not None and held else None),
                "exact_zero_grid_minima":sum(r.get("zero_is_grid_minimum",False) for r in good),
                "not_statistical_calibration_qualified":True}
        cells[support]={
            "null_calibration_independent_blocks":len(calibration),
            "null_calibration_completed":len(okcal),
            "heldout_independent_blocks_per_state":BLOCKS-N_CALIBRATION,
            "empirical_90pct_grid_statistic_threshold":threshold,
            "threshold_unavailable_due_to_failed_calibration":threshold is None,
            "calibration_null_grid_statistic_max":(
                max([r["grid_statistic"] for r in okcal]) if okcal else None),
            "outcomes":outcomes}
    return {"study":STUDY,"seed":MASTER_SEED,
        "independent_original_generating_blocks":BLOCKS,
        "calibration_block_ids":list(range(N_CALIBRATION)),
        "heldout_block_ids":list(range(N_CALIBRATION,BLOCKS)),
        "paired_heldout_null_and_positive_use_same_latent_blocks":True,
        "supports":SUPPORT,"sample_size":PARTICIPANTS,
        "predeclared_fixed_slope_grid_ratios":GRID,
        "true_positive_slope_variance":TRUE_POSITIVE_SLOPE_VARIANCE,
        "planned_original_source_cases":PLANNED_SOURCE_CASES,
        "recorded_original_source_cases":len(rows),
        "missing_source_cases":len(expected-set(ids)),
        "planned_constrained_profile_optimizations":PLANNED_GRID_OPTIMIZATIONS,
        "recorded_profile_points":sum(len(r["profile_points"]) for r in rows),
        "failed_profile_points":sum(
            x["status"]!="ok" for r in rows for x in r["profile_points"]),
        "source_failures":sum(not r["source_generated"] for r in rows),
        "base_reml_failures":sum(r["source_generated"] and
                r["reml_status"]!="ok" for r in rows),
        "profile_grid_completeness_refusals":sum(
            r["source_generated"] and r["reml_status"]=="ok" and
            r["profile_status"]!="complete" for r in rows),
        "cells":cells,"null_calibration_and_heldout_independent":True,
        "statistic_is_finite_profile_grid_not_continuous_mle":True,
        "no_standard_chisquare_or_mixture_reference_used":True,
        "nominal_type_i_error_qualified":False,
        "nuisance_adjusted_regression_CI_qualified":False,
        "simultaneous_functional_bands_qualified":False,
        "release_authorized":False}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    cases=[evaluate(b,s,"zero_slope")
           for b in range(BLOCKS) for s in SUPPORT]
    cases += [evaluate(b,s,"positive_slope")
              for b in range(N_CALIBRATION,BLOCKS) for s in SUPPORT]
    report=summarize(cases)
    for name,obj in (("case-ledger.json",cases),("summary.json",report)):
        (a.out/name).write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")
    (a.out/"source-commit.txt").write_text(
        os.getenv("GITHUB_SHA","unverified-local")+"\n")
    files=("case-ledger.json","summary.json","source-commit.txt")
    (a.out/"SHA256SUMS").write_text("".join(
        hashlib.sha256((a.out/name).read_bytes()).hexdigest()+"  "+name+"\n"
        for name in files))
    print("R36 SPLIT NULL PROFILE GRID AUDIT:",json.dumps(
        {k:v for k,v in report.items() if k!="cells"},sort_keys=True))
    for s,v in report["cells"].items():
        print("R36 NULL AND POSITIVE CELL:",json.dumps(
            {"support":s,**v},sort_keys=True))
    if report["source_failures"] or report["missing_source_cases"]:
        raise SystemExit("original source ledger incomplete; preserve recorded failures")


if __name__=="__main__":
    main()
