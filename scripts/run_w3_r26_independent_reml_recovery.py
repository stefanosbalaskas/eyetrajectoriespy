"""R26 independent-source, failure-inclusive covariance estimation replication.

Sixteen NEW independent generating blocks and nested n24/n48/n96. Four
prespecified source structures × both candidate nuisance families, with one
Legendre-5 mean basis. Both Gaussian REML and original NNLS see identical
native observations; generating covariance used solely AFTER estimation
for matched-family recovery and common 5%-of-truth boundary diagnostics.

No confidence interval, CR2 coverage or Satterthwaite inference is computed.
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

STUDY="W3_R26_INDEPENDENT_REM_LIKELIHOOD_VS_NNLS_RECOVERY"
SOURCE_SEED=202610153626
BOOTSTRAP_SEED=202610153628
BLOCKS=16
SIZES=(24,48,96)
SUPPORT=r16.SUPPORT
WORKING_FAMILIES=MODELS
BASIS="legendre5"
METHODS=("leverage_adjusted_nnls","gaussian_reml")
COMMON_TRUE_VARIANCE_RATIO=.05
BOOTSTRAP_DRAWS=2500
EXPECTED=BLOCKS*len(SIZES)*len(SUPPORT)*len(WORKING_FAMILIES)
TRUE_COMPONENTS=dict(zip(COMPONENTS,(
    float(r16.SIGMA_INTERCEPT**2),
    float(r16.SIGMA_RANDOM_SLOPE**2),
    float(r16.SIGMA_TRIAL**2),
    float(r16.SIGMA_SENSOR**2),
)))


def wilson(k,n):
    if not n:return None
    z=float(norm.ppf(.975));p=k/n;den=1+z*z/n
    center=(p+z*z/(2*n))/den
    half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [float(max(0,center-half)),float(min(1,center+half))]


def evaluate(block,n,support,family):
    row={"study":STUDY,"block":block,"participants":n,"source":support,
         "working_family":family,"model":BASIS,
         "source_generated":False,"method_results":{},
         "source_truth_provided_to_estimators":False,
         "estimated_target_inference_qualified":False,
         "release_authorized":False}
    try:
        data=source.fresh_source(block,support,n=n,master_seed=SOURCE_SEED,
                 n_blocks=BLOCKS,max_n=max(SIZES))
        row["source_generated"]=True
        observed=(None,data[1],data[2],data[3],data[4],None)
        X,y,w,g,t,trial,x=observed_weighted_rows(observed,BASIS)
    except Exception as exc:
        row["source_failure"]={"type":type(exc).__name__,"message":str(exc)[:500]}
        return row
    nnls=None
    try:
        nnls=estimate_feasible_working_target(X,y,w,g,t,trial,x,slope=family)
        estimates=nnls["variance_components"]
        row["method_results"]["leverage_adjusted_nnls"]={
            "status":"ok","component_estimates":estimates,
            "literal_zero_components":{k:bool(estimates[k]==0) for k in COMPONENTS},
            "estimator_sensor_floor":bool(nnls["sensor_floor_applied"]),
            "nuisance_operator_condition":nnls["component_condition_number"],
            "normalized_moment_residual":nnls["nnls_normalized_residual"]}
    except Exception as exc:
        row["method_results"]["leverage_adjusted_nnls"]={
            "status":"failed","error":{"type":type(exc).__name__,
                                       "message":str(exc)[:500]}}
    try:
        fit=estimate_reml_components(
             X,y,w,g,t,trial,x,slope=family,
             initializer=nnls["variance_components"] if nnls else None)
        row["method_results"]["gaussian_reml"]={
            "status":fit["status"],
            "component_estimates":fit["variance_components"],
            "near_boundary_relative_residual_reference":fit["near_boundary_components"],
            "active_lower_optimization_bound":fit["active_lower_box_components"],
            "iterations":fit["optimizer_iterations"],
            "logscore":fit["maximum_absolute_logscore"],
            "optimizer_success":fit["optimizer_success"],
            "optimizer_message":fit["optimizer_message"]}
    except Exception as exc:
        row["method_results"]["gaussian_reml"]={
            "status":"failed","error":{"type":type(exc).__name__,
                                       "message":str(exc)[:500]}}
    family_correct=(family==("predictor_scaled_slope"
                       if support.endswith("_dependent") else "shared_slope"))
    row["matched_generating_covariance_shape_postfit"]=family_correct
    row["generator_component_variances_postfit_only"]=TRUE_COMPONENTS
    for method in METHODS:
        fit=row["method_results"][method]
        if fit["status"]=="ok" and family_correct:
            est=fit["component_estimates"]
            fit["relative_errors_on_matched_source_only"]={
                k:float(abs(est[k]/TRUE_COMPONENTS[k]-1)) for k in COMPONENTS}
            fit["less_than_5pct_true_component_on_matched_source_only"]={
                k:bool(est[k]<COMMON_TRUE_VARIANCE_RATIO*TRUE_COMPONENTS[k])
                for k in COMPONENTS}
        else:
            fit["relative_errors_on_matched_source_only"]=None
            fit["less_than_5pct_true_component_on_matched_source_only"]=None
    return row


def paired_source_bootstrap(rows):
    matched=[x for x in rows if x.get("matched_generating_covariance_shape_postfit")]
    pair=[x for x in matched if all(
        x["method_results"][m]["status"]=="ok" for m in METHODS)]
    complete=(len(pair)==BLOCKS*len(SIZES)*len(SUPPORT))
    results={}
    for k in COMPONENTS:
        by_block=[]
        for b in range(BLOCKS):
            cases=[x for x in pair if x["block"]==b]
            if not cases:
                continue
            if complete and len(cases)!=len(SIZES)*len(SUPPORT):
                raise ValueError("complete block has insufficient paired strata")
            diffs=[x["method_results"]["gaussian_reml"][
                       "relative_errors_on_matched_source_only"][k]
                 -x["method_results"]["leverage_adjusted_nnls"][
                       "relative_errors_on_matched_source_only"][k] for x in cases]
            by_block.append(float(np.mean(diffs)))
        if not by_block:
            results[k]={"source_blocks":0,"paired_mean_error_difference":None,
                        "block_bootstrap_95pct":None}
            continue
        values=np.asarray(by_block)
        rng=np.random.default_rng(BOOTSTRAP_SEED+COMPONENTS.index(k))
        draws=rng.choice(values,size=(BOOTSTRAP_DRAWS,len(values)),replace=True).mean(axis=1)
        results[k]={"source_blocks":len(values),
            "paired_mean_error_difference_reml_minus_nnls":float(values.mean()),
            "block_bootstrap_95pct":np.quantile(draws,[.025,.975]).tolist()}
    return {"complete_pairing_across_all_matched_source_strata":complete,
            "matched_pair_model_cases":len(pair),
            "expected_matched_model_cases":BLOCKS*len(SIZES)*len(SUPPORT),
            "bootstrap_draws":BOOTSTRAP_DRAWS,
            "resamples_independent_generating_blocks_only":True,
            "component_results":results,
            "estimator_winner_selected":False}


def summarize(rows):
    expected={(b,n,s,f) for b in range(BLOCKS) for n in SIZES
              for s in SUPPORT for f in WORKING_FAMILIES}
    recorded={(x["block"],x["participants"],x["source"],x["working_family"]) for x in rows}
    if len(recorded)!=len(rows):
        raise ValueError("duplicate source/model identity")
    if not recorded.issubset(expected):
        raise ValueError("unknown source/model identity")
    strata={}
    for n in SIZES:
        for source_type in SUPPORT:
            for family in WORKING_FAMILIES:
                name=f"n{n}/{source_type}/{family}"
                subset=[x for x in rows if x["participants"]==n
                        and x["source"]==source_type and x["working_family"]==family]
                matching=(family==("predictor_scaled_slope"
                           if source_type.endswith("_dependent") else "shared_slope"))
                methods={}
                for method in METHODS:
                    fits=[x["method_results"].get(method,{}) for x in subset]
                    good=[x for x in fits if x.get("status")=="ok"]
                    matched_true={
                        k:sum(x["less_than_5pct_true_component_on_matched_source_only"][k]
                              for x in good) if matching else None
                        for k in COMPONENTS}
                    relative={
                        k:(float(np.median([x["relative_errors_on_matched_source_only"][k]
                                           for x in good])) if matching and good else None)
                        for k in COMPONENTS}
                    methods[method]={
                        "completed_fits":len(good),"failed_or_nonconverged":len(subset)-len(good),
                        "fit_success_wilson_95pct":wilson(len(good),len(subset)),
                        "common_true_relative_near_zero_counts_matched_only":matched_true,
                        "median_relative_recovery_error_matched_only":relative,
                        "near_box_bound_count":sum(
                            any(x.get("active_lower_optimization_bound",{}).values()) for x in good)
                            if method=="gaussian_reml" else None,
                        "literal_zero_trial_cases":sum(x.get("literal_zero_components",{}).get("trial",False)
                            for x in good) if method=="leverage_adjusted_nnls" else None}
                strata[name]={"independent_source_blocks":len(subset),
                    "matching_generator_for_postfit_diagnostics":matching,
                    "methods":methods}
    return {"study":STUDY,"source_seed":SOURCE_SEED,
        "independent_generating_blocks":BLOCKS,"sizes":SIZES,"source_conditions":SUPPORT,
        "working_families":WORKING_FAMILIES,"mean_basis":BASIS,
        "planned_paired_cases":EXPECTED,"recorded_cases":len(rows),
        "missing_cases":len(expected-recorded),
        "source_generation_failures":sum(not x["source_generated"] for x in rows),
        "fit_failures_by_method":{m:sum(
            x["method_results"].get(m,{}).get("status")!="ok" for x in rows)
            for m in METHODS},
        "source_case_strata":strata,
        "paired_source_bootstrap":paired_source_bootstrap(rows),
        "uses_generator_values_in_estimator":False,
        "pointwise_interval_coverage_evaluated":False,
        "estimated_covariance_satterthwaite_qualified":False,
        "public_api_authorized":False,"release_authorized":False}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    rows=[evaluate(b,n,s,f) for b in range(BLOCKS) for n in SIZES
          for s in SUPPORT for f in WORKING_FAMILIES]
    info=summarize(rows)
    for filename,obj in (("case-ledger.json",rows),("summary.json",info)):
        (args.out/filename).write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (args.out/"source-commit.txt").write_text(os.getenv("GITHUB_SHA","unverified-local")+"\n")
    names=("case-ledger.json","summary.json","source-commit.txt")
    (args.out/"SHA256SUMS").write_text("".join(
       hashlib.sha256((args.out/name).read_bytes()).hexdigest()+"  "+name+"\n" for name in names))
    print("R26 INDEPENDENT RECOVERY AUDIT:",json.dumps(
        {k:v for k,v in info.items() if k!="source_case_strata"},sort_keys=True))
    for name,item in info["source_case_strata"].items():
        print("R26 RECOVERY CELL:",json.dumps({"cell":name,**item},sort_keys=True))
    if info["missing_cases"] or info["source_generation_failures"]:
        raise SystemExit("R26 independent study source incomplete; retain failures")


if __name__=="__main__":
    main()
