"""R39: log-vs-linear nuisance and raw-vs-centered REML optimizer diagnostics.

Strictly numerical study, REUSING the R37 Gaussian source block 2 from R38.
Four paired support/state cases, five frozen random-slope-variance ratios,
three fixed nuisance seeds, two parameterizations, two objective offsets:
4 x 5 x 3 x 2 x 2 = 240 original constrained optimizations. No source replication.
All optimization outcomes are recorded, including failed/false convergence.
No variance test, coefficient confidence intervals, functional bands or release.
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
from scripts import run_w3_r38_dualseed_profile_geometry as r38
from scripts.w3_r20_estimated_working_target import observed_weighted_rows
from scripts.w3_r25_gaussian_reml_components import (
    LOWER_LOG_RATIO, UPPER_LOG_RATIO, prepare_reml_design,
)

STUDY = "W3_R39_SAME_SOURCE_NUISANCE_PARAMETERIZATION_AND_OFFSET"
REUSED_MASTER_SEED = r37.MASTER_SEED
REUSED_BLOCK = r38.BLOCK
SUPPORT = r37.SUPPORT
STATES = r37.STATES
RATIOS = (0., 0.1, 0.75, 1.75, 3.5)
SEEDS = ("R37_best", "R37_worst", "geometric_midpoint")
COORDINATES = ("log_variances", "linear_variance_ratios")
OFFSETS = ("raw_NLL", "common_centered_NLL")
SLOPE_GRID_POINTS = len(RATIOS)
PLANNED_CASES = len(SUPPORT)*len(STATES)
PLANNED_FITS = PLANNED_CASES*SLOPE_GRID_POINTS*len(SEEDS)*len(COORDINATES)*len(OFFSETS)
DISAGREEMENT_NLL = 1e-3
LOW = float(np.exp(LOWER_LOG_RATIO))
HIGH = float(np.exp(UPPER_LOG_RATIO))


def fixed_slope_parameter_objective(v, prepared, ref, ratio,
                                    coordinate, common_center=0.):
    """Same Gaussian restricted likelihood expressed in two coordinates.

    The linear variance *ratios* retain the exact positive nuisance limits of
    the log-variance model, not an implicit new zero-variance model. A constant
    subtractive objective offset has no analytical effect on the gradient.
    """
    p = np.asarray(v, dtype=float)
    if p.shape != (3,) or not np.isfinite(p).all():
        raise ValueError("three finite nuisance variance parameters required")
    if coordinate == "log_variances":
        logs = p
        if np.any(p < LOWER_LOG_RATIO-1e-7) or np.any(p > UPPER_LOG_RATIO+1e-7):
            raise ValueError("log variance outside original box")
    elif coordinate == "linear_variance_ratios":
        if np.any(p < LOW*(1.-1e-7)) or np.any(p > HIGH*(1.+1e-7)):
            raise ValueError("linear nuisance ratio outside original box")
        logs = np.log(p)
    else:
        raise ValueError("unknown nuisance coordinate")
    objective, log_gradient = r35.fixed_slope_reml_objective(
        logs, prepared, ref, float(ratio)
    )
    gradient = (log_gradient if coordinate == "log_variances"
                else log_gradient / p)
    if not np.isfinite(objective) or not np.isfinite(gradient).all():
        raise ValueError("nonfinite nuisance objective or score")
    return float(objective-common_center), np.asarray(gradient,float)


def initial_log_seeds(r37_record, reference):
    successes = [x for x in r37_record["optimizations"] if x["status"] == "ok"]
    if len(successes) != len(r37.RATIO_STARTS):
        raise ValueError("R37 independent starts incomplete; do not select survivors")
    best = min(successes, key=lambda x:x["objective"])
    worst = max(successes, key=lambda x:x["objective"])

    def free_log_ratios(start):
        return np.array([
            np.log(float(start["free_component_estimates"][r37.COMPONENTS[k]])
                   /reference) for k in r37.FREE
        ],dtype=float)
    a = free_log_ratios(best)
    b = free_log_ratios(worst)
    return {
        "R37_best":a,
        "R37_worst":b,
        "geometric_midpoint":.5*(a+b),
    }


def projected_residual(gradient, ratios):
    """Raw first-order KKT residual in the shared linear physical coordinates."""
    return r38.projected_gradient(
        np.asarray(gradient,float), np.asarray(ratios,float),
        [(LOW,HIGH)]*3, edge_tol=1e-9,
    )


def fit_one(prepared, reference, slope_ratio, start_log, label,
            coordinate, offset, common_center):
    row = {
        "fixed_slope_ratio":float(slope_ratio),
        "nuisance_start":label,
        "parameterization":coordinate,
        "objective_offset":offset,
        "status":"failed",
        "error":None,
    }
    try:
        x0 = (start_log if coordinate == "log_variances"
              else np.exp(start_log))
        bounds = ([(LOWER_LOG_RATIO,UPPER_LOG_RATIO)]*3
                  if coordinate == "log_variances" else [(LOW,HIGH)]*3)
        amount = (0. if offset == "raw_NLL" else float(common_center))
        result = minimize(
            fixed_slope_parameter_objective,
            x0, args=(prepared,reference,slope_ratio,coordinate,amount),
            jac=True,method="L-BFGS-B",bounds=bounds,
            options={"maxiter":250,"ftol":1e-12,"gtol":1e-8,"maxls":45},
        )
        finite = (np.isfinite(result.fun) and np.isfinite(result.x).all()
                  and np.isfinite(result.jac).all())
        row.update(
            status=("ok" if result.success and finite else "nonconverged"),
            optimizer_success=bool(result.success),
            optimizer_message=str(result.message),
            iterations=int(result.nit),
        )
        if finite:
            fitted_log = (result.x if coordinate == "log_variances"
                          else np.log(result.x))
            actual_nll, log_gradient = r35.fixed_slope_reml_objective(
                fitted_log,prepared,reference,slope_ratio
            )
            ratios = np.exp(fitted_log)
            physical_gradient = log_gradient / ratios
            projected = projected_residual(physical_gradient,ratios)
            row.update(
                gaussian_restricted_NLL=float(actual_nll),
                optimizer_objective_unshifted=float(result.fun+amount),
                objective_reconstruction_error=float(abs(
                    actual_nll-(result.fun+amount))),
                nuisance_variance_ratios=[float(v) for v in ratios],
                participant_intercept_variance_ratio=float(
                    ratios[r37.FREE.index(r37.COMPONENTS.index(
                        "participant_intercept"))]),
                shared_ratio_projected_KKT_absmax=float(
                    np.max(np.abs(projected))),
                gradient_in_log_coordinates_absmax=float(
                    np.max(np.abs(log_gradient))),
                active_positive_nuisance_lower_box=bool(
                    np.any(np.abs(fitted_log-LOWER_LOG_RATIO)<1e-5)),
                active_positive_nuisance_upper_box=bool(
                    np.any(np.abs(fitted_log-UPPER_LOG_RATIO)<1e-5)),
            )
    except Exception as exc:
        row["error"] = {"type":type(exc).__name__,
                        "message":str(exc)[:600]}
    return row


def source_and_prepared(support,state):
    case = r37.source(REUSED_BLOCK,support,state)
    X,y,w,g,t,tr,x = observed_weighted_rows(
        (None,case[1],case[2],case[3],case[4],None),"legendre5"
    )
    return prepare_reml_design(
        X,y,w,g,t,tr,x,slope="predictor_scaled_slope"
    )


def evaluate(support,state):
    row = {
        "study":STUDY, "original_R37_block":REUSED_BLOCK,
        "support":support, "true_state":state,
        "reuses_R37_R38_primitives":True,
        "independent_replication":False,
        "source_status":"failed", "error":None,
        "profiles":[], "no_test_calibration_or_CI":True,
        "release_authorized":False,
    }
    try:
        original = r37.evaluate(REUSED_BLOCK,support,state)
        if original["continuous_reference_status"] != "computed":
            row["error"]="original R37 re-evaluation incomplete; explicit refusal"
            return row
        prepared = source_and_prepared(support,state)
        reference = float(original["reference_variance"])
        initials = initial_log_seeds(original,reference)
        row["source_status"]="ok"
        row["original_R37_objective_spread"]=float(
            original["max_objective_spread_over_starts"])
        row["original_R37_best_NLL"]=float(
            original["best_multistart_likelihood"])
        for slope in RATIOS:
            center, _ = r35.fixed_slope_reml_objective(
                initials["R37_best"],prepared,reference,slope
            )
            point={
                "fixed_slope_ratio":float(slope),
                "common_subtractive_center_NLL":float(center),
                "fits":[],
            }
            for name,start in initials.items():
                for coordinate in COORDINATES:
                    for offset in OFFSETS:
                        point["fits"].append(fit_one(
                            prepared,reference,slope,start,name,
                            coordinate,offset,center))
            successes=[x for x in point["fits"] if x["status"]=="ok"]
            if successes:
                best=min(x["gaussian_restricted_NLL"] for x in successes)
                point["best_successful_NLL"]=float(best)
                point["successful_objective_spread"]=float(
                    max(x["gaussian_restricted_NLL"] for x in successes)-best)
                point["material_objective_disagreement"]=bool(
                    point["successful_objective_spread"]>DISAGREEMENT_NLL)
                for z in successes:
                    z["within_1e_3_of_best_observed_this_ratio"]=bool(
                        z["gaussian_restricted_NLL"] <= best+DISAGREEMENT_NLL)
            row["profiles"].append(point)
    except Exception as exc:
        row["error"]={"type":type(exc).__name__,"message":str(exc)[:600]}
    return row


def summarize(rows):
    expected={(a,b) for a in SUPPORT for b in STATES}
    identities=[(r["support"],r["true_state"]) for r in rows]
    if len(identities)!=len(set(identities)) or not set(identities).issubset(expected):
        raise ValueError("duplicate or unknown source condition")
    fits=[f for r in rows for p in r["profiles"] for f in p["fits"]]
    cells={}
    for coord in COORDINATES:
        for offset in OFFSETS:
            relevant=[f for f in fits if f["parameterization"]==coord
                      and f["objective_offset"]==offset]
            cells[coord+"/"+offset]={
                "expected_fits":PLANNED_CASES*len(RATIOS)*len(SEEDS),
                "recorded_fits":len(relevant),
                "successful_fits":sum(x["status"]=="ok" for x in relevant),
                "failed_or_nonconverged":sum(x["status"]!="ok" for x in relevant),
                "within_best_observed_1e_3":sum(
                    x.get("within_1e_3_of_best_observed_this_ratio",False)
                    for x in relevant),
                "largest_reconstruction_error":(
                    max((x.get("objective_reconstruction_error",0.)
                         for x in relevant),default=None)),
            }
    return {
        "study":STUDY,
        "reused_original_master_seed":REUSED_MASTER_SEED,
        "independent_new_generating_blocks":0,
        "reused_original_R37_generating_blocks":1,
        "planned_paired_source_cases":PLANNED_CASES,
        "recorded_paired_source_cases":len(rows),
        "missing_source_cases":len(expected-set(identities)),
        "failed_source_cases":sum(x["source_status"]!="ok" for x in rows),
        "predeclared_fixed_slope_ratios":RATIOS,
        "predeclared_nuisance_initializations":SEEDS,
        "predeclared_parameterizations":COORDINATES,
        "predeclared_objective_offsets":OFFSETS,
        "planned_nuisance_fits":PLANNED_FITS,
        "recorded_nuisance_fits":len(fits),
        "failed_or_nonconverged_nuisance_fits":sum(
            x["status"]!="ok" for x in fits),
        "paired_fixed_profile_points":sum(
            len(x["profiles"]) for x in rows),
        "source_profile_points_with_optimizer_disagreement":sum(
            p.get("material_objective_disagreement",False)
            for x in rows for p in x["profiles"]),
        "numerical_parameterization_diagnostic_only":True,
        "no_global_optimality_certificate":True,
        "no_statistical_calibration_or_typeI_power":True,
        "no_working_covariance_CR2_coefficient_intervals":True,
        "no_simultaneous_functional_bands":True,
        "release_authorized":False,
        "cells":cells,
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    a=parser.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    rows=[evaluate(s,t) for s in SUPPORT for t in STATES]
    report=summarize(rows)
    for filename,obj in (("cases.json",rows),("summary.json",report)):
        (a.out/filename).write_text(
            json.dumps(obj,sort_keys=True,indent=2,allow_nan=False)+"\n"
        )
    (a.out/"source-commit.txt").write_text(
        os.environ.get("GITHUB_SHA","unverified-local")+"\n"
    )
    names=("cases.json","summary.json","source-commit.txt")
    (a.out/"SHA256SUMS").write_text("".join(
        hashlib.sha256((a.out/n).read_bytes()).hexdigest()+"  "+n+"\n"
        for n in names))
    print("R39 NUISANCE COORDINATE AND OBJECTIVE OFFSET AUDIT:",
          json.dumps(report,sort_keys=True))
    if (report["missing_source_cases"] or report["failed_source_cases"]
        or report["recorded_nuisance_fits"]!=PLANNED_FITS):
        raise SystemExit("R39 study incomplete; retain original ledger and refusals")


if __name__=="__main__":
    main()
