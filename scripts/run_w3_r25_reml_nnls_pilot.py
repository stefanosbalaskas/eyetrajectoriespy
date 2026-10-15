"""R25 paired numerical pilot: original moment NNLS vs Gaussian REML.

Four independent source blocks, n24/48, all four leverage/covariance modes,
Legendre-5 basis, both predefined working covariance families. Both
estimators see identical observed native data, never true source variances.
Source truth is used AFTER both fits, and ONLY for matched-family recovery.
This is a 64-case exploratory numerical pilot, not CI coverage qualification.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np
from scipy.stats import norm

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts import run_w3_r16_leverage_covariance_factorial as r16
from scripts import run_w3_r17_fresh_feasibility as source
from scripts.w3_r20_estimated_working_target import (
    COMPONENTS,MODELS,observed_weighted_rows,estimate_feasible_working_target)
from scripts.w3_r25_gaussian_reml_components import estimate_reml_components

STUDY="W3_R25_FRESH_PAIRED_COVARIANCE_ESTIMATORS_NUMERICAL_PILOT"
MASTER_SEED=202610153525
BLOCKS=4
SIZES=(24,48)
SUPPORT=r16.SUPPORT
BASIS="legendre5"
FAMILIES=MODELS
METHODS=("leverage_adjusted_nnls","gaussian_reml")
EXPECTED=BLOCKS*len(SIZES)*len(SUPPORT)*len(FAMILIES)
TRUE_COMPONENTS=dict(zip(COMPONENTS,(
    float(r16.SIGMA_INTERCEPT**2),
    float(r16.SIGMA_RANDOM_SLOPE**2),
    float(r16.SIGMA_TRIAL**2),
    float(r16.SIGMA_SENSOR**2),
)))


def evaluate(block,n,support,family):
    record={"study":STUDY,"block":block,"participants":n,
            "support":support,"working_family":family,"basis":BASIS,
            "source_generated":False,
            "methods":{},
            "truth_passed_to_estimator":False,
            "no_inferential_coverage_evaluated":True,
            "release_authorized":False}
    try:
        data=source.fresh_source(
            block,support,n=n,master_seed=MASTER_SEED,
            n_blocks=BLOCKS,max_n=max(SIZES))
        record["source_generated"]=True
        observed=(None,data[1],data[2],data[3],data[4],None)
        X,y,w,ids,t,tr,x=observed_weighted_rows(observed,BASIS)
    except Exception as exc:
        record["source_error"]={"type":type(exc).__name__,"message":str(exc)[:500]}
        return record
    moment=None
    try:
        moment=estimate_feasible_working_target(X,y,w,ids,t,tr,x,slope=family)
        components=moment["variance_components"]
        record["methods"]["leverage_adjusted_nnls"]={
            "status":"ok",
            "variance_components":components,
            "boundary_components":{k:float(components[k])==0 for k in COMPONENTS},
            "sensor_floor":bool(moment["sensor_floor_applied"]),
            "moment_condition_number":moment["component_condition_number"],
            "moment_residual":moment["nnls_normalized_residual"],
            "estimated_from_observed_data":True}
    except Exception as exc:
        record["methods"]["leverage_adjusted_nnls"]={
            "status":"failed",
            "error":{"type":type(exc).__name__,"message":str(exc)[:500]}}
    try:
        candidate=estimate_reml_components(
            X,y,w,ids,t,tr,x,slope=family,
            initializer=moment["variance_components"] if moment is not None else None)
        record["methods"]["gaussian_reml"]={
            "status":candidate["status"],
            "variance_components":candidate["variance_components"],
            "boundary_components":candidate["near_boundary_components"],
            "active_lower_box_components":candidate["active_lower_box_components"],
            "restricted_negative_loglik":candidate["restricted_negative_loglik"],
            "optimizer_iterations":candidate["optimizer_iterations"],
            "optimizer_evaluations":candidate["optimizer_evaluations"],
            "optimizer_success":candidate["optimizer_success"],
            "maximum_absolute_logscore":candidate["maximum_absolute_logscore"],
            "optimizer_message":candidate["optimizer_message"],
            "estimated_from_observed_data":candidate["estimated_from_observed_responses"]}
    except Exception as exc:
        record["methods"]["gaussian_reml"]={
            "status":"failed",
            "error":{"type":type(exc).__name__,"message":str(exc)[:500]}}
    matched=(family==("predictor_scaled_slope" if support.endswith("_dependent") else "shared_slope"))
    record["working_family_matches_generator_for_diagnostic_only"]=matched
    record["true_variances_for_post_fit_diagnostic_only"]=TRUE_COMPONENTS
    for method in METHODS:
        detail=record["methods"][method]
        if detail["status"]=="ok" and matched:
            detail["absolute_relative_component_errors_matched_only"]={
                k:abs(detail["variance_components"][k]-TRUE_COMPONENTS[k])/TRUE_COMPONENTS[k]
                for k in COMPONENTS}
        else:
            detail["absolute_relative_component_errors_matched_only"]=None
    return record


def wilson(k,n):
    if n<=0:return None
    z=float(norm.ppf(.975));p=k/n;den=1+z*z/n
    mid=(p+z*z/(2*n))/den
    delta=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [0. if k==0 else float(max(0.,mid-delta)),
            1. if k==n else float(min(1.,mid+delta))]


def summarize(rows):
    expected={(b,n,s,f) for b in range(BLOCKS) for n in SIZES
              for s in SUPPORT for f in FAMILIES}
    observed={(x["block"],x["participants"],x["support"],x["working_family"])
              for x in rows}
    if len(observed)!=len(rows):
        raise ValueError("duplicate paired research case")
    if not observed.issubset(expected):
        raise ValueError("unregistered source experiment")
    cells={}
    for n in SIZES:
        for support in SUPPORT:
            for family in FAMILIES:
                name=f"n{n}/{support}/{family}"
                paired=[x for x in rows if x["participants"]==n and
                        x["support"]==support and x["working_family"]==family]
                detail={}
                matched=family==("predictor_scaled_slope"
                                if support.endswith("_dependent") else "shared_slope")
                for method in METHODS:
                    ok=[x["methods"][method] for x in paired
                        if x["source_generated"] and x["methods"].get(method,{}).get("status")=="ok"]
                    counts={k:sum(x["boundary_components"][k] for x in ok)
                            for k in COMPONENTS}
                    errors={
                        k:(float(np.median([
                            x["absolute_relative_component_errors_matched_only"][k]
                            for x in ok])) if ok and matched else None)
                        for k in COMPONENTS}
                    detail[method]={
                        "successful_fits":len(ok),
                        "failed_or_nonconverged_fits":len(paired)-len(ok),
                        "success_wilson_95pct":wilson(len(ok),len(paired)),
                        "near_boundary_component_counts":counts,
                        "component_median_absolute_relative_errors_if_matched":errors,
                        "optimizer_iterations_median":(
                            float(np.median([x["optimizer_iterations"] for x in ok]))
                            if ok and method=="gaussian_reml" else None),
                    }
                cells[name]={
                    "source_blocks":len(paired),
                    "family_matches_generator_for_diagnostic_only":matched,
                    "methods":detail,
                    "paired_source_design":True}
    return {"study":STUDY,"source_seed":MASTER_SEED,
            "independent_generating_blocks":BLOCKS,"sizes":SIZES,
            "source_mechanisms":SUPPORT,"prespecified_working_families":FAMILIES,
            "fixed_mean_basis":BASIS,
            "planned_cases":EXPECTED,"recorded_cases":len(rows),
            "missing_cases":len(expected-observed),
            "source_generation_failures":sum(not x["source_generated"] for x in rows),
            "methods":METHODS,"cells":cells,
            "no_coverage_computed":True,
            "nuisance_estimation_inference_qualified":False,
            "simultaneous_band_qualified":False,
            "public_api_authorized":False,"release_authorized":False}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    rows=[evaluate(b,n,s,f) for b in range(BLOCKS) for n in SIZES
          for s in SUPPORT for f in FAMILIES]
    summary=summarize(rows)
    for name,obj in (("case-ledger.json",rows),("summary.json",summary)):
        (args.out/name).write_text(json.dumps(obj,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    (args.out/"source-commit.txt").write_text(os.getenv("GITHUB_SHA","unverified-local")+"\n")
    names=("case-ledger.json","summary.json","source-commit.txt")
    (args.out/"SHA256SUMS").write_text("".join(
        hashlib.sha256((args.out/name).read_bytes()).hexdigest()+"  "+name+"\n"
        for name in names))
    print("R25 PAIRED ESTIMATOR AUDIT:",json.dumps(
        {k:v for k,v in summary.items() if k!="cells"},sort_keys=True))
    for key,item in summary["cells"].items():
        print("R25 ESTIMATOR CELL:",json.dumps({"cell":key,**item},sort_keys=True))
    if summary["missing_cases"] or summary["source_generation_failures"]:
        raise SystemExit("Incomplete original-source experiment; cannot claim completed pilot")
    # Estimator and optimizer failures are RESULTS, not reasons to discard a cell.


if __name__=="__main__":
    main()
