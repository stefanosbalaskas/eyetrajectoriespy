"""R30: Gaussian-vs-heavy-tailed participant-slope robustness at fixed source.

Twelve new independent generating blocks, n24/96, ordinary independent /
dependent source covariance, 1x/2x participant predictor span, matched
Gaussian covariance working families. Couple original primitive normal draws
to standardized Student-t5 participant-slope effects by an inverse CDF map.
This preserves their theoretical variance but violates Gaussian likelihood.
All other source primitives, observations times and trial IDs are held fixed
within block. Both NNLS and REML use observed outcomes only; source truth is
post-fit diagnostic only. No confidence interval coverage or API promotion.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np
from scipy.stats import norm, t as student_t

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts import run_w3_r17_fresh_feasibility as fresh
from scripts import run_w3_r29_predictor_spread_recovery as r29
from scripts.w3_r20_estimated_working_target import (
    COMPONENTS,observed_weighted_rows,estimate_feasible_working_target)
from scripts.w3_r25_gaussian_reml_components import estimate_reml_components

STUDY="W3_R30_HEAVY_TAILED_SLOPE_PREDICTOR_SPREAD_ROBUSTNESS"
SOURCE_SEED=202610153030
BOOTSTRAP_SEED=202610153032
INDEPENDENT_BLOCKS=12
SIZES=(24,96)
SUPPORT=r29.SUPPORT
SPREAD=(1.,2.)
SLOPE_LAWS=("gaussian","standardized_t5")
DF=5
METHODS=r29.METHODS
TRUE_COMPONENTS=r29.TRUE_COMPONENTS
PLANNED=INDEPENDENT_BLOCKS*len(SIZES)*len(SUPPORT)*len(SPREAD)*len(SLOPE_LAWS)
BOOTSTRAP_DRAWS=2000


def primitive_slope_transformation(z,law):
    values=np.asarray(z,float)
    if law=="gaussian":
        return values.copy()
    if law!="standardized_t5":
        raise ValueError("unregistered innovation distribution")
    probabilities=np.clip(norm.cdf(values),1e-12,1-1e-12)
    # Student-t5 has population variance df/(df-2); scale to unit variance.
    return student_t.ppf(probabilities,df=DF)/np.sqrt(DF/(DF-2))


def source_for_law(original,law,multiplier):
    if law not in SLOPE_LAWS:
        raise ValueError("unregistered source law")
    raw=dict(original[0])
    raw["participant_slope"]=primitive_slope_transformation(
        raw["participant_slope"],law)
    modified=(raw,*original[1:])
    return r29.rescaled_source(modified,multiplier)


def evaluate(block,n,support,multiplier,law):
    record={"study":STUDY,"block":block,"participants":n,
            "source_support":support,"predictor_multiplier":float(multiplier),
            "slope_innovation_law":law,"source_generated":False,
            "source_error":None,"methods":{},"original_source_is_gaussian":law=="gaussian",
            "same_latent_normal_primitives_across_conditions":True,
            "covariance_component_truth_passed_to_estimators":False,
            "coverage_evaluated":False,"release_authorized":False}
    family=("predictor_scaled_slope" if support.endswith("_dependent")
            else "shared_slope")
    record["matched_working_covariance_family"]=family
    try:
        base=fresh.fresh_source(
            block,support,n=n,master_seed=SOURCE_SEED,
            n_blocks=INDEPENDENT_BLOCKS,max_n=max(SIZES))
        source=source_for_law(base,law,multiplier)
        X,y,w,g,t,tr,x=observed_weighted_rows(
            (None,source[1],source[2],source[3],source[4],None),
            r29.BASIS)
        record["source_generated"]=True
        record["native_points"]=len(y)
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
            "status":"ok","variance_components":est,
            "sensor_floor_applied":moment["sensor_floor_applied"]}
    except Exception as exc:
        record["methods"]["leverage_adjusted_nnls"]={
            "status":"failed",
            "error":{"type":type(exc).__name__,"message":str(exc)[:500]}}
    try:
        reml=estimate_reml_components(
            X,y,w,g,t,tr,x,slope=family,
            initializer=(moment["variance_components"] if moment else None))
        record["methods"]["gaussian_reml"]={
            "status":reml["status"],
            "variance_components":reml["variance_components"],
            "active_lower_bound":reml["active_lower_box_components"],
            "optimizer_success":reml["optimizer_success"],
            "optimizer_message":reml["optimizer_message"]}
    except Exception as exc:
        record["methods"]["gaussian_reml"]={
            "status":"failed",
            "error":{"type":type(exc).__name__,"message":str(exc)[:500]}}
    for method in METHODS:
        fit=record["methods"][method]
        if fit["status"]=="ok":
            estimates=fit["variance_components"]
            fit["postfit_slope_relative_error"]=float(
                abs(estimates["participant_slope"]/TRUE_COMPONENTS["participant_slope"]-1))
            fit["postfit_component_relative_errors"]={
                key:float(abs(estimates[key]/TRUE_COMPONENTS[key]-1))
                for key in COMPONENTS}
            fit["postfit_slope_below_5pct_truth"]=bool(
                estimates["participant_slope"]<
                .05*TRUE_COMPONENTS["participant_slope"])
        else:
            fit["postfit_slope_relative_error"]=None
            fit["postfit_component_relative_errors"]=None
            fit["postfit_slope_below_5pct_truth"]=None
    return record


def paired_stress_contrast(rows,n,support,method):
    grouped={}
    for row in rows:
        if row["participants"]==n and row["source_support"]==support:
            grouped.setdefault(row["block"],{})[
                (row["slope_innovation_law"],row["predictor_multiplier"])]=row
    values=[]
    for block in range(INDEPENDENT_BLOCKS):
        cells=grouped.get(block,{})
        keys=[(law,m) for law in SLOPE_LAWS for m in SPREAD]
        if not all(key in cells for key in keys):
            continue
        fits={key:cells[key]["methods"].get(method,{}) for key in keys}
        if not all(v.get("status")=="ok" for v in fits.values()):
            continue
        gauss=(fits[("gaussian",2.)]["postfit_slope_relative_error"]-
               fits[("gaussian",1.)]["postfit_slope_relative_error"])
        heavy=(fits[("standardized_t5",2.)]["postfit_slope_relative_error"]-
               fits[("standardized_t5",1.)]["postfit_slope_relative_error"])
        values.append((gauss,heavy,heavy-gauss))
    if not values:
        return {"complete_paired_blocks":0,"mean_heavy_minus_gaussian_spread_benefit":None,
                "whole_block_bootstrap_95pct":None}
    a=np.asarray(values)
    rng=np.random.default_rng(BOOTSTRAP_SEED+SIZES.index(n)*100+
                              SUPPORT.index(support)*10+METHODS.index(method))
    sims=rng.choice(a[:,2],size=(BOOTSTRAP_DRAWS,len(a)),replace=True).mean(axis=1)
    return {
        "complete_paired_blocks":len(a),
        "mean_gaussian_2x_minus_1x_error":float(np.mean(a[:,0])),
        "mean_heavy_2x_minus_1x_error":float(np.mean(a[:,1])),
        "mean_heavy_minus_gaussian_spread_benefit":float(np.mean(a[:,2])),
        "whole_block_bootstrap_95pct":np.quantile(sims,[.025,.975]).tolist(),
        "independent_unit":"source_block",
    }


def summarize(rows):
    expected={(b,n,s,m,l) for b in range(INDEPENDENT_BLOCKS) for n in SIZES
              for s in SUPPORT for m in SPREAD for l in SLOPE_LAWS}
    observed=[(x["block"],x["participants"],x["source_support"],
        x["predictor_multiplier"],x["slope_innovation_law"]) for x in rows]
    if len(observed)!=len(set(observed)) or not set(observed).issubset(expected):
        raise ValueError("duplicate or unregistered robustness source case")
    cells={}
    for n in SIZES:
        for support in SUPPORT:
            for law in SLOPE_LAWS:
                for spread in SPREAD:
                    subset=[x for x in rows if x["participants"]==n and
                        x["source_support"]==support and
                        x["slope_innovation_law"]==law and
                        x["predictor_multiplier"]==spread]
                    methods={}
                    for method in METHODS:
                        ok=[x["methods"][method] for x in subset if
                            x["source_generated"] and
                            x["methods"].get(method,{}).get("status")=="ok"]
                        methods[method]={
                            "successful_fits":len(ok),
                            "failed_or_nonconverged_fits":len(subset)-len(ok),
                            "slope_near_zero_count":sum(
                                x["postfit_slope_below_5pct_truth"] for x in ok),
                            "median_slope_absolute_relative_error":(
                                float(np.median([x["postfit_slope_relative_error"]
                                                 for x in ok])) if ok else None),
                            "mean_slope_absolute_relative_error":(
                                float(np.mean([x["postfit_slope_relative_error"]
                                               for x in ok])) if ok else None),
                        }
                    cells[f"n{n}/{support}/{law}/x{spread}"]={
                        "independent_source_blocks":len(subset),
                        "methods":methods}
    contrasts={f"n{n}/{support}/{method}":paired_stress_contrast(
        rows,n,support,method)
        for n in SIZES for support in SUPPORT for method in METHODS}
    return {
        "study":STUDY,"seed":SOURCE_SEED,
        "independent_generating_blocks":INDEPENDENT_BLOCKS,
        "participant_sizes":SIZES,"source_supports":SUPPORT,
        "spread_multipliers":SPREAD,"slope_laws":SLOPE_LAWS,
        "true_t_df":DF,"standardized_t_population_variance":1.,
        "planned_cases":PLANNED,"recorded_cases":len(rows),
        "missing_cases":len(expected-set(observed)),
        "source_failures":sum(not x["source_generated"] for x in rows),
        "method_failures":{method:sum(
            x["methods"].get(method,{}).get("status")!="ok" for x in rows)
            for method in METHODS},
        "cells":cells,"paired_heavy_tail_sensitivity":contrasts,
        "bootstrap_draws":BOOTSTRAP_DRAWS,
        "no_confidence_interval_coverage_computed":True,
        "no_estimated_covariance_inference_qualified":True,
        "release_authorized":False,
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",required=True,type=Path)
    args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    rows=[evaluate(b,n,s,m,l) for b in range(INDEPENDENT_BLOCKS)
          for n in SIZES for s in SUPPORT for m in SPREAD for l in SLOPE_LAWS]
    report=summarize(rows)
    for name,obj in (("case-ledger.json",rows),("summary.json",report)):
        (args.out/name).write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")
    (args.out/"source-commit.txt").write_text(os.getenv("GITHUB_SHA","unverified-local")+"\n")
    filenames=("case-ledger.json","summary.json","source-commit.txt")
    (args.out/"SHA256SUMS").write_text("".join(
        hashlib.sha256((args.out/name).read_bytes()).hexdigest()+"  "+name+"\n"
        for name in filenames))
    print("R30 HEAVY TAIL SOURCE AUDIT:",json.dumps(
        {k:v for k,v in report.items() if k!="cells"},sort_keys=True))
    for key,x in report["cells"].items():
        print("R30 ROBUSTNESS CELL:",json.dumps({"cell":key,**x},sort_keys=True))
    if report["source_failures"] or report["missing_cases"]:
        raise SystemExit("Original heavy-tail source incomplete; preserve all failures")


if __name__=="__main__":
    main()
