"""R29: prospective finite-Gaussian recovery under counterfactual predictor spread.

12 NEW independent generating blocks; nested n=24/96 participants; ordinary
predictor-independent/dependent source mechanisms. Reuse the SAME primitive
Gaussian innovations, exact native trial/time grids, and participant labels
within each block across predictor multiples .5, 1, 2, 4. Recompute the
source regression mean AND predictor-dependent random-slope contribution,
not merely rescale an old fitted x vector.

Fit both observed-only NNLS and Gaussian REML under the prespecified matching
working covariance family. Generator true components are only postfit
diagnostics. No coefficient confidence intervals, inferred estimator winner,
public API or release qualification.
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
from scripts import run_w3_r26_independent_reml_recovery as prior
from scripts.w3_r20_estimated_working_target import (
    COMPONENTS,observed_weighted_rows,estimate_feasible_working_target)
from scripts.w3_r25_gaussian_reml_components import estimate_reml_components

STUDY="W3_R29_FRESH_PAIRED_PREDICTOR_SPREAD_COVARIANCE_RECOVERY"
SOURCE_SEED=202610152929
BOOTSTRAP_SEED=202610152931
BLOCKS=12
SIZES=(24,96)
SUPPORT=("ordinary_independent","ordinary_dependent")
MULTIPLIERS=(.5,1.,2.,4.)
BASIS="legendre5"
METHODS=("leverage_adjusted_nnls","gaussian_reml")
TRUE_COMPONENTS=prior.TRUE_COMPONENTS
PLANNED=BLOCKS*len(SIZES)*len(SUPPORT)*len(MULTIPLIERS)
BOOTSTRAP_DRAWS=2000


def rescaled_source(original,multiplier):
    """Create genuine counterfactual observations from identical source draws."""
    multiplier=float(multiplier)
    if not np.isfinite(multiplier) or multiplier<=0 or multiplier not in MULTIPLIERS:
        raise ValueError("outside frozen predictor-spread multipliers")
    raw,gaze,trial_x,participant,trialnums,_=original
    independent=(raw["covariance_mode"]=="independent")
    new_values=[];new_means=[];new_predictor=[]
    for curve,(time,who,num) in enumerate(zip(gaze.time,participant,trialnums)):
        who=int(who);trial=int(num%3)
        x=float(trial_x[curve])*multiplier
        time=np.asarray(time,float)
        truth=r16.truth_coefficients(time)
        mu=truth[0]+x*truth[1]
        sig=(mu
             +r16.SIGMA_INTERCEPT*raw["participant_intercept"][who,0,0]*(1+.30*time[:,None])
             +r16.SIGMA_RANDOM_SLOPE*raw["participant_slope"][who,0,0]*
               (1. if independent else x)*(1+.25*time[:,None])
             +r16.SIGMA_TRIAL*raw["trial_noise"][who,trial,0]
             +r16.SIGMA_SENSOR*raw["sensor_noise"][who,trial])
        new_values.append(sig)
        new_means.append(mu[:,0].copy())
        new_predictor.append(x)
    result=r16.IrregularTrajectorySet(
        time=tuple(np.asarray(t).copy() for t in gaze.time),
        values=tuple(new_values),
        curve_ids=gaze.curve_ids,
        dimension_names=r16.DIMS,
        time_unit="s",
        coordinate_system="normalized",
        metadata=gaze.metadata.copy(),
        provenance={**gaze.provenance,
                    "research_study":STUDY,
                    "counterfactual_predictor_multiplier":multiplier,
                    "new_independent_observation":False,
                    "same_primitive_gaussian_innovations":True,
                    "interpolation_performed":False})
    return (None,result,np.asarray(new_predictor,float),
            np.asarray(participant).copy(),np.asarray(trialnums).copy(),
            tuple(new_means))


def evaluate(block,n,support,multiplier):
    record={
        "study":STUDY,"block":block,"participants":n,
        "source_support":support,"predictor_multiplier":float(multiplier),
        "source_generated":False,"source_error":None,"methods":{},
        "independent_unit":"generating_block",
        "counterfactual_within_block":True,
        "truth_passed_to_estimators":False,
        "confidence_interval_coverage_evaluated":False,
        "release_authorized":False,
    }
    family=("predictor_scaled_slope" if support.endswith("_dependent")
            else "shared_slope")
    record["prespecified_matching_covariance_family"]=family
    try:
        original=fresh.fresh_source(
            block,support,n=n,master_seed=SOURCE_SEED,
            n_blocks=BLOCKS,max_n=max(SIZES))
        data=rescaled_source(original,multiplier)
        X,y,w,g,t,tr,x=observed_weighted_rows(
            (None,data[1],data[2],data[3],data[4],None),BASIS)
        record["source_generated"]=True
        record["original_native_trajectory_count"]=len(original[1].time)
        record["original_native_point_count"]=len(y)
    except Exception as exc:
        record["source_error"]={"type":type(exc).__name__,
                               "message":str(exc)[:500]}
        return record
    moment=None
    try:
        moment=estimate_feasible_working_target(
            X,y,w,g,t,tr,x,slope=family)
        est=moment["variance_components"]
        record["methods"]["leverage_adjusted_nnls"]={
            "status":"ok","component_estimates":est,
            "literal_zero":{k:bool(est[k]==0.) for k in COMPONENTS},
            "sensor_floor_applied":moment["sensor_floor_applied"],
            "moment_operator_condition":moment["component_condition_number"]}
    except Exception as exc:
        record["methods"]["leverage_adjusted_nnls"]={
            "status":"failed",
            "error":{"type":type(exc).__name__,"message":str(exc)[:500]}}
    try:
        fit=estimate_reml_components(
            X,y,w,g,t,tr,x,slope=family,
            initializer=(moment["variance_components"] if moment else None))
        record["methods"]["gaussian_reml"]={
            "status":fit["status"],
            "component_estimates":fit["variance_components"],
            "optimizer_success":fit["optimizer_success"],
            "active_lower_bounds":fit["active_lower_box_components"],
            "iterations":fit["optimizer_iterations"],
            "optimizer_message":fit["optimizer_message"]}
    except Exception as exc:
        record["methods"]["gaussian_reml"]={
            "status":"failed",
            "error":{"type":type(exc).__name__,"message":str(exc)[:500]}}
    for method in METHODS:
        fit=record["methods"][method]
        if fit["status"]=="ok":
            est=fit["component_estimates"]
            # True Gaussian source variance appears only AFTER both fits.
            fit["postfit_relative_error"]={
                k:float(abs(est[k]/TRUE_COMPONENTS[k]-1)) for k in COMPONENTS}
            fit["postfit_below_5pct_true"]={
                k:bool(est[k]<.05*TRUE_COMPONENTS[k]) for k in COMPONENTS}
        else:
            fit["postfit_relative_error"]=None
            fit["postfit_below_5pct_true"]=None
    return record


def bootstrap_block_difference(rows,n,support,method,component,new_scale=2.):
    """Paired change in absolute-relative component error vs 1x within blocks."""
    groups={}
    for record in rows:
        if record["participants"]==n and record["source_support"]==support:
            groups.setdefault(record["block"],{})[record["predictor_multiplier"]]=record
    values=[]
    for block in range(BLOCKS):
        variants=groups.get(block,{})
        if 1. not in variants or new_scale not in variants:
            continue
        a=variants[1.]["methods"].get(method,{})
        b=variants[new_scale]["methods"].get(method,{})
        if a.get("status")=="ok" and b.get("status")=="ok":
            values.append(
                b["postfit_relative_error"][component]-
                a["postfit_relative_error"][component])
    if not values:
        return {"paired_blocks":0,"mean_2x_minus_1x_error":None,
                "whole_block_bootstrap_95pct":None}
    v=np.asarray(values,float)
    rng=np.random.default_rng(
        BOOTSTRAP_SEED+SIZES.index(n)*100+
        SUPPORT.index(support)*10+METHODS.index(method)*5+
        COMPONENTS.index(component))
    b=rng.choice(v,size=(BOOTSTRAP_DRAWS,len(v)),replace=True).mean(axis=1)
    return {"paired_blocks":len(v),"mean_2x_minus_1x_error":float(v.mean()),
            "whole_block_bootstrap_95pct":np.quantile(b,[.025,.975]).tolist()}


def summarize(rows):
    expected={(b,n,s,m) for b in range(BLOCKS) for n in SIZES
              for s in SUPPORT for m in MULTIPLIERS}
    actual=[(r["block"],r["participants"],r["source_support"],
             r["predictor_multiplier"]) for r in rows]
    if len(actual)!=len(set(actual)) or not set(actual).issubset(expected):
        raise ValueError("duplicate or unregistered counterfactual source")
    strata={}
    for n in SIZES:
        for support in SUPPORT:
            for multiplier in MULTIPLIERS:
                cases=[r for r in rows if r["participants"]==n
                       and r["source_support"]==support
                       and r["predictor_multiplier"]==multiplier]
                methods={}
                for method in METHODS:
                    successes=[r["methods"][method] for r in cases
                        if r["source_generated"] and
                        r["methods"].get(method,{}).get("status")=="ok"]
                    methods[method]={
                        "successful_fits":len(successes),
                        "failed_or_nonconverged_fits":len(cases)-len(successes),
                        "below_5pct_true_counts":{
                            k:sum(x["postfit_below_5pct_true"][k] for x in successes)
                            for k in COMPONENTS},
                        "median_absolute_relative_error":{
                            k:(float(np.median(
                                [x["postfit_relative_error"][k] for x in successes]))
                               if successes else None) for k in COMPONENTS},
                        "optimization_lower_bound_cases":(
                            sum(any(x["active_lower_bounds"].values())
                                for x in successes)
                            if method=="gaussian_reml" else None),
                    }
                strata[f"n{n}/{support}/x{multiplier}"]={
                    "original_independent_generating_blocks":len(cases),
                    "methods":methods}
    contrasts={}
    for n in SIZES:
        for support in SUPPORT:
            for method in METHODS:
                contrasts[f"n{n}/{support}/{method}"]=bootstrap_block_difference(
                    rows,n,support,method,"participant_slope")
    return {
        "study":STUDY,"master_seed":SOURCE_SEED,
        "independent_generating_blocks":BLOCKS,
        "participant_sizes":SIZES,"source_supports":SUPPORT,
        "predictor_multipliers":MULTIPLIERS,
        "planned_counterfactual_cases":PLANNED,
        "recorded_cases":len(rows),
        "missing_cases":len(expected-set(actual)),
        "source_failures":sum(not r["source_generated"] for r in rows),
        "estimator_failure_counts":{
            method:sum(r["methods"].get(method,{}).get("status")!="ok"
                       for r in rows) for method in METHODS},
        "strata":strata,
        "slope_error_2x_minus_1x_paired_block_bootstrap":contrasts,
        "bootstrap_draws":BOOTSTRAP_DRAWS,
        "new_observations_are_independent_across_multiplier":False,
        "new_independent_generating_blocks":BLOCKS,
        "no_confidence_interval_coverage_computed":True,
        "no_method_winner_selected":True,
        "fitted_covariance_satterthwaite_qualified":False,
        "release_authorized":False,
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    rows=[evaluate(b,n,s,m) for b in range(BLOCKS)
          for n in SIZES for s in SUPPORT for m in MULTIPLIERS]
    summary=summarize(rows)
    for name,obj in (("case-ledger.json",rows),("summary.json",summary)):
        (a.out/name).write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")
    (a.out/"source-commit.txt").write_text(
        os.getenv("GITHUB_SHA","unverified-local")+"\n")
    files=("case-ledger.json","summary.json","source-commit.txt")
    (a.out/"SHA256SUMS").write_text("".join(
        hashlib.sha256((a.out/name).read_bytes()).hexdigest()+"  "+name+"\n"
        for name in files))
    print("R29 PREDICTOR SOURCE RECOVERY:",json.dumps(
          {k:v for k,v in summary.items() if k!="strata"},sort_keys=True))
    for key,item in summary["strata"].items():
        print("R29 RECOVERY CELL:",json.dumps({"cell":key,**item},sort_keys=True))
    if summary["missing_cases"] or summary["source_failures"]:
        raise SystemExit("Original prospective source incomplete; retain all failed cases")


if __name__=="__main__":
    main()
