"""R41 targeted (not independent) numerical refinement of original R40 KKT exceptions.

Frozen, outcome-selected R40 targets (18) and matched within-profile controls
(15) from independently generated R40 blocks. No new primitive source blocks.
No automatic pass claims, no inference, no variance significance testing, no CI.
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

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts import run_w3_r40_fresh_source_nuisance as r40
from scripts import run_w3_r39_nuisance_coordinate_audit as r39

STUDY="W3_R41_TARGETED_PHYSICAL_KKT_REFINEMENT_REUSED_R40"
PARENT_CASES_SHA256="7943b6ea869c242ba8b7ee7c00a7025af755f2d9ef7d9e9aaec1e36c4009c349"
# Explicitly selected by original R40 physical KKT > 0.001. Never describe
# these as a random validation sample or newly independent generating blocks.
EXCEPTIONS=(
 (0,"ordinary_dependent","zero_slope",.75,"interior"),
 (1,"ordinary_dependent","zero_slope",.75,"trial_near_lower"),
 (1,"extreme_dependent","zero_slope",0.,"interior"),
 (1,"extreme_dependent","zero_slope",0.,"intercept_near_lower"),
 (1,"extreme_dependent","positive_slope",.75,"interior"),
 (2,"ordinary_dependent","zero_slope",.75,"interior"),
 (2,"ordinary_dependent","zero_slope",.75,"trial_near_lower"),
 (2,"extreme_dependent","zero_slope",.75,"trial_near_lower"),
 (2,"extreme_dependent","positive_slope",.75,"intercept_near_lower"),
 (4,"extreme_dependent","zero_slope",0.,"trial_near_lower"),
 (5,"ordinary_dependent","positive_slope",.75,"trial_near_lower"),
 (5,"extreme_dependent","zero_slope",0.,"intercept_near_lower"),
 (5,"extreme_dependent","positive_slope",0.,"interior"),
 (5,"extreme_dependent","positive_slope",.75,"interior"),
 (6,"ordinary_dependent","positive_slope",.75,"trial_near_lower"),
 (6,"extreme_dependent","positive_slope",0.,"intercept_near_lower"),
 (6,"extreme_dependent","positive_slope",0.,"trial_near_lower"),
 (7,"ordinary_dependent","zero_slope",0.,"intercept_near_lower"),
)
# One original R40 successful lower-KKT companion from each of the 15
# different support/state/fixed-ratio profiles containing an exception.
CONTROLS=(
 (0,"ordinary_dependent","zero_slope",.75,"intercept_near_lower"),
 (1,"ordinary_dependent","zero_slope",.75,"interior"),
 (1,"extreme_dependent","zero_slope",0.,"trial_near_lower"),
 (1,"extreme_dependent","positive_slope",.75,"intercept_near_lower"),
 (2,"ordinary_dependent","zero_slope",.75,"intercept_near_lower"),
 (2,"extreme_dependent","zero_slope",.75,"interior"),
 (2,"extreme_dependent","positive_slope",.75,"interior"),
 (4,"extreme_dependent","zero_slope",0.,"interior"),
 (5,"ordinary_dependent","positive_slope",.75,"interior"),
 (5,"extreme_dependent","zero_slope",0.,"interior"),
 (5,"extreme_dependent","positive_slope",0.,"intercept_near_lower"),
 (5,"extreme_dependent","positive_slope",.75,"intercept_near_lower"),
 (6,"ordinary_dependent","positive_slope",.75,"interior"),
 (6,"extreme_dependent","positive_slope",0.,"interior"),
 (7,"ordinary_dependent","zero_slope",0.,"interior"),
)
METHODS=("original_R40_raw_linear","stricter_LBFGSB_restart","independent_SLSQP_restart")
PLANNED_EVALUATIONS=len(EXCEPTIONS)+len(CONTROLS)
PLANNED_FITS=PLANNED_EVALUATIONS*len(METHODS)
FROZEN_KKT_THRESHOLD=1e-3
NLL_DISAGREEMENT_THRESHOLD=1e-3


def objective(x,prepared,ref,slope):
    return r39.fixed_slope_parameter_objective(
        x,prepared,ref,slope,"linear_variance_ratios",0.
    )


def record_solution(result,prepared,ref,slope,algorithm):
    item={
        "algorithm":algorithm,"status":"failed",
        "optimizer_success":bool(result.success),
        "message":str(result.message),"iterations":int(result.nit),
        "fit":None,"error":None,
    }
    if not (np.isfinite(result.fun) and np.isfinite(result.x).all()):
        item["error"]="nonfinite objective or variance estimates"
        return item
    try:
        x=np.asarray(result.x,dtype=float)
        f,gradient=objective(x,prepared,ref,slope)
        kkt=r39.projected_residual(gradient,x)
        err=abs(float(result.fun)-f)
        item["fit"]={
            "original_unshifted_NLL":float(f),
            "optimizer_objective_reconstruction_abs_error":float(err),
            "nuisance_variance_ratios":[float(a) for a in x],
            "physical_ratio_projected_KKT_absmax":float(np.max(abs(kkt))),
            "passes_frozen_physical_KKT":bool(np.max(abs(kkt))<=FROZEN_KKT_THRESHOLD),
            "active_lower_nuisance_bound":bool(np.any(x<=r39.LOW+1e-8)),
            "active_upper_nuisance_bound":bool(np.any(x>=r39.HIGH-1e-8)),
        }
        item["status"]="ok" if result.success and err<=1e-6 else "nonconverged"
    except Exception as exc:
        item["error"]={"type":type(exc).__name__,"message":str(exc)[:600]}
    return item


def restart(original,prepared,ref,slope,algorithm):
    row={"algorithm":algorithm,"status":"failed","fit":None,"error":None}
    try:
        x0=np.asarray(original["nuisance_variance_ratios"],dtype=float)
        kw={"fun":objective,"x0":x0,"args":(prepared,ref,slope),
            "jac":True,"bounds":[(r39.LOW,r39.HIGH)]*3}
        if algorithm=="stricter_LBFGSB_restart":
            result=minimize(**kw,method="L-BFGS-B",
                            options={"maxiter":450,"ftol":0.,"gtol":1e-10,
                                     "maxls":80,"maxfun":2200})
        elif algorithm=="independent_SLSQP_restart":
            result=minimize(**kw,method="SLSQP",
                            options={"maxiter":450,"ftol":1e-11,"disp":False})
        else:
            raise ValueError("Unregistered optimizer algorithm")
        return record_solution(result,prepared,ref,slope,algorithm)
    except Exception as exc:
        row["error"]={"type":type(exc).__name__,"message":str(exc)[:600]}
        return row


def evaluate_case(spec,is_exception,prepared_cache):
    block,support,state,slope,initial_name=spec
    row={
        "block":block,"support":support,"state":state,
        "fixed_random_slope_ratio":float(slope),
        "initialization":initial_name,
        "original_R40_KKT_exception":bool(is_exception),
        "source_status":"failed", "error":None,"fits":[],
        "was_selected_after_original_R40_outcomes":True,
        "independent_R41_generator_block":False,
        "release_authorized":False,
    }
    try:
        data_key=(block,support,state)
        if data_key not in prepared_cache:
            prepared_cache[data_key]=r40.prepare_case(block,support,state)
        prepared,ref,_=prepared_cache[data_key]
        row["source_status"]="ok"
        original=r39.fit_one(
            prepared,ref,slope,np.log(np.asarray(r40.SEED_RATIOS[initial_name])),
            initial_name,"linear_variance_ratios","raw_NLL",0.
        )
        if original["status"]!="ok":
            row["fits"].append({
                "algorithm":METHODS[0],"status":original["status"],
                "fit":None,"error":original.get("error"),
            })
            return row
        baseline={
            "algorithm":METHODS[0],"status":"ok",
            "optimizer_success":True,
            "message":original["optimizer_message"],
            "iterations":original["iterations"],
            "fit":{
                "original_unshifted_NLL":original["gaussian_restricted_NLL"],
                "nuisance_variance_ratios":original["nuisance_variance_ratios"],
                "physical_ratio_projected_KKT_absmax":
                    original["shared_ratio_projected_KKT_absmax"],
                "passes_frozen_physical_KKT":
                    original["shared_ratio_projected_KKT_absmax"]
                    <=FROZEN_KKT_THRESHOLD,
            },"error":None,
        }
        row["fits"].append(baseline)
        # Reproduction safeguard: the original preselected R40 KKT flag must
        # remain unchanged; an optimizer or numerical source drift is a refusal.
        if bool(not baseline["fit"]["passes_frozen_physical_KKT"]) != is_exception:
            row["error"]="R40 source selection did not reproduce: refusal"
            return row
        for algorithm in METHODS[1:]:
            row["fits"].append(restart(
                original,prepared,ref,slope,algorithm
            ))
        return row
    except Exception as exc:
        row["error"]={"type":type(exc).__name__,"message":str(exc)[:600]}
        return row


def summarize(rows):
    if len({(r["block"],r["support"],r["state"],
             r["fixed_random_slope_ratio"],r["initialization"]) for r in rows})!=len(rows):
        raise ValueError("Duplicate R41 prior-source evaluation")
    expected=set(EXCEPTIONS)|set(CONTROLS)
    actual={(r["block"],r["support"],r["state"],
             r["fixed_random_slope_ratio"],r["initialization"]) for r in rows}
    if not actual<=expected:
        raise ValueError("Unexpected original source condition")
    cells={}
    all_fits=[x for r in rows for x in r["fits"]]
    for algorithm in METHODS:
        arr=[x for x in all_fits if x["algorithm"]==algorithm]
        exception_arr=[
            x for r in rows if r["original_R40_KKT_exception"]
            for x in r["fits"] if x["algorithm"]==algorithm
        ]
        cells[algorithm]={
            "recorded_fits":len(arr),
            "successful_fits":sum(x["status"]=="ok" for x in arr),
            "failed_or_nonconverged":sum(x["status"]!="ok" for x in arr),
            "passing_physical_KKT":sum(
                x.get("fit") is not None and
                x["fit"].get("passes_frozen_physical_KKT") is True
                and x["status"]=="ok" for x in arr
            ),
            "original_R40_exceptions_recorded":len(exception_arr),
            "original_R40_exceptions_now_passing_KKT":sum(
                x.get("fit") is not None and
                x["fit"].get("passes_frozen_physical_KKT") is True
                and x["status"]=="ok" for x in exception_arr
            ),
            "maximum_KKT_for_successful_fits":max(
                (x["fit"]["physical_ratio_projected_KKT_absmax"]
                 for x in arr if x["status"]=="ok" and x["fit"] is not None),
                default=None),
        }
    comparisons={}
    for alg in METHODS[1:]:
        gains=[];losses=[];improved=0;bad=0
        for r in rows:
            if len(r["fits"])!=len(METHODS):continue
            baseline=r["fits"][0]
            candidate=next(f for f in r["fits"] if f["algorithm"]==alg)
            if baseline["status"]!="ok" or candidate["status"]!="ok":continue
            diff=candidate["fit"]["original_unshifted_NLL"]-baseline["fit"]["original_unshifted_NLL"]
            gains.append(float(diff))
            if diff < -NLL_DISAGREEMENT_THRESHOLD:improved+=1
            if diff > NLL_DISAGREEMENT_THRESHOLD:bad+=1
        comparisons[alg]={
            "paired_successful_NLL_comparisons":len(gains),
            "NLL_improvement_greater_than_0_001":improved,
            "NLL_worsening_greater_than_0_001":bad,
            "min_NLL_difference":min(gains,default=None),
            "max_NLL_difference":max(gains,default=None),
        }
    complete=len(rows)==PLANNED_EVALUATIONS and len(all_fits)==PLANNED_FITS
    complete=complete and all(r["source_status"]=="ok" and r["error"] is None
                              for r in rows)
    return {
        "study":STUDY,
        "original_R40_case_ledger_SHA256":PARENT_CASES_SHA256,
        "R40_independent_primitive_blocks_reused":r40.BLOCKS,
        "NEW_independent_primitive_blocks":0,
        "prior_outcome_selected_exceptions":len(EXCEPTIONS),
        "same_original_profile_KKT_controls":len(CONTROLS),
        "planned_profile_start_evaluations":PLANNED_EVALUATIONS,
        "recorded_profile_start_evaluations":len(rows),
        "planned_optimizer_fits":PLANNED_FITS,
        "recorded_optimizer_fits":len(all_fits),
        "source_errors_or_drift":sum(
            r["source_status"]!="ok" or r["error"] is not None for r in rows),
        "incomplete_original_reference_replays":sum(
            len(r["fits"])==0 or r["fits"][0]["status"]!="ok" for r in rows),
        "all_cases_replayed_and_refinements_attempted":bool(complete),
        "methods":cells,"NLL_comparison_to_original":comparisons,
        "numerical_diagnostic_only":True,
        "independently_validated_estimator":False,
        "type_I_power_calibration":False,
        "nuisance_aware_CR2_or_simultaneous_band_qualification":False,
        "release_authorized":False,
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    cache={}
    rows=[
        evaluate_case(spec,which,cache)
        for which,specs in ((True,EXCEPTIONS),(False,CONTROLS))
        for spec in specs
    ]
    summary=summarize(rows)
    for path,obj in (("cases.json",rows),("summary.json",summary)):
        (args.out/path).write_text(json.dumps(
            obj,indent=2,sort_keys=True,allow_nan=False)+"\n")
    (args.out/"source-commit.txt").write_text(
        os.environ.get("GITHUB_SHA","unverified-local")+"\n")
    names=("cases.json","summary.json","source-commit.txt")
    (args.out/"SHA256SUMS").write_text("".join(
        hashlib.sha256((args.out/f).read_bytes()).hexdigest()+"  "+f+"\n"
        for f in names
    ))
    print("R41 TARGETED KKT STUDY",json.dumps(summary,sort_keys=True))
    if not summary["all_cases_replayed_and_refinements_attempted"]:
        raise SystemExit("R41 integrity REFUSAL; preserve all recorded failures")


if __name__=="__main__":
    main()
