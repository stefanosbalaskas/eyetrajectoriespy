"""R23 research-only reliability study of an *estimated* working covariance.

A fresh seed is used for 12 independent generating blocks, nested 24/48/96
participants, four source mechanisms, two prespecified mean bases and two
candidate nuisance covariance families. Source truth is used only for
simulation diagnostics AFTER the observation-only estimator is fitted.

No interval coverage is computed; an estimator or CR2 numerical refusal is
recorded as an outcome, never filtered out. No statistical/API qualification.
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
from scripts.w3_r22_scaled_cholesky_cr2 import (
    UnstableCR2Adjustment,stable_cr2_blockwise_wls)

STUDY="W3_R23_NEW_SEED_WORKING_COVARIANCE_IDENTIFIABILITY"
MASTER_SEED=202610153301
BLOCKS=12
SIZES=(24,48,96)
SUPPORT=r16.SUPPORT
BASES=r16.MODELS
WORKING_FAMILIES=MODELS
PLANNED=BLOCKS*len(SIZES)*len(SUPPORT)*len(BASES)*len(WORKING_FAMILIES)
SOURCE_VARIANCES=dict(zip(COMPONENTS,(
    float(r16.SIGMA_INTERCEPT**2),float(r16.SIGMA_RANDOM_SLOPE**2),
    float(r16.SIGMA_TRIAL**2),float(r16.SIGMA_SENSOR**2))))


def binomial_wilson(k,n):
    if n==0:
        return None
    z=float(norm.ppf(.975))
    p=k/n
    d=1+z*z/n
    center=(p+z*z/(2*n))/d
    half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return [0.0 if k==0 else float(max(0.,center-half)),
            1.0 if k==n else float(min(1.,center+half))]


def evaluate(block,n,support,model,family):
    record={
        "study":STUDY,"block":block,"n_participants":n,
        "source_support":support,"mean_basis":model,"working_family":family,
        "source_generated":False,
        "estimator_status":"failed",
        "numerical_cr2_status":"not_attempted",
        "estimator_error":None,"numerical_error":None,
        "generated_truth_passed_to_estimator":False,
        "simultaneous_bands_qualified":False,
        "estimated_target_inference_qualified":False,
        "release_authorized":False,
    }
    try:
        data=source.fresh_source(
            block,support,n=n,master_seed=MASTER_SEED,
            n_blocks=BLOCKS,max_n=max(SIZES))
        record["source_generated"]=True
        # Give the estimator neither the source oracle, nor source means,
        # primitive source innovations, nor known covariance coefficients.
        observed=(None,data[1],data[2],data[3],data[4],None)
        X,y,w,g,t,tr,x=observed_weighted_rows(observed,model)
        nuisance=estimate_feasible_working_target(
            X,y,w,g,t,tr,x,slope=family)
        estimates=nuisance["variance_components"]
        record.update({
            "estimator_status":"ok",
            "component_variances":estimates,
            "component_rank":nuisance["component_rank"],
            "component_condition_number":nuisance["component_condition_number"],
            "normalized_residual_moment_fit":nuisance["nnls_normalized_residual"],
            "sensor_floor_applied":nuisance["sensor_floor_applied"],
            "zero_component_count":sum(float(estimates[k])==0. for k in COMPONENTS),
            "estimated_from_outcomes":nuisance["estimated_from_outcomes"],
            "working_target_is_simulation_oracle":False,
            "covariance_estimation_uncertainty_accounted_for":False,
            "observation_count":nuisance["observations"],
        })
        # Simulation-only annotation must occur AFTER outcome-only estimation.
        source_family=("predictor_scaled_slope"
                       if support.endswith("_dependent") else "shared_slope")
        same_structure=(family==source_family)
        record["matches_generating_covariance_shape_for_audit_only"]=same_structure
        record["known_generating_component_variances_for_audit_only"]=SOURCE_VARIANCES
        record["relative_component_errors_for_matched_family_only"]=(
            {k:abs(float(estimates[k])-SOURCE_VARIANCES[k])/SOURCE_VARIANCES[k]
             for k in COMPONENTS} if same_structure else None)
        k=r16.basis(np.asarray([.5]),model).shape[1]
        c=np.r_[np.zeros(k),r16.basis(
            np.asarray([r16.TIME[r16.FOCAL]]),model)[0]]
        try:
            adjusted=stable_cr2_blockwise_wls(
                X,y,w,g,c,nuisance["working_blocks"])
            record["numerical_cr2_status"]="accepted"
            record["maximum_product_condition"]=adjusted["max_normalized_product_condition"]
            record["relative_cr2_identity_error"]=adjusted["max_relative_adjustment_identity_error"]
            record["pointwise_coverage_evaluated"]=False
        except (UnstableCR2Adjustment, ValueError,
                np.linalg.LinAlgError) as exc:
            record["numerical_cr2_status"]="refused"
            record["numerical_error"]={"type":type(exc).__name__,
                                      "message":str(exc)[:500]}
    except Exception as exc:
        record["estimator_error"]={"type":type(exc).__name__,
                                    "message":str(exc)[:500]}
    return record


def summarize(rows):
    expected={(b,n,s,m,f) for b in range(BLOCKS) for n in SIZES
              for s in SUPPORT for m in BASES for f in WORKING_FAMILIES}
    actual=[(x["block"],x["n_participants"],x["source_support"],
             x["mean_basis"],x["working_family"]) for x in rows]
    if len(actual)!=len(set(actual)):
        raise ValueError("duplicate independent-source case")
    if any(x not in expected for x in actual):
        raise ValueError("unregistered experiment cell")
    groups={}
    for n in SIZES:
        for support in SUPPORT:
            for model in BASES:
                for family in WORKING_FAMILIES:
                    name=f"n{n}/{support}/{model}/{family}"
                    cell=[x for x in rows if x["n_participants"]==n
                          and x["source_support"]==support
                          and x["mean_basis"]==model
                          and x["working_family"]==family]
                    fitted=[x for x in cell if x["estimator_status"]=="ok"]
                    accepted=[x for x in fitted if x["numerical_cr2_status"]=="accepted"]
                    floors=sum(bool(x["sensor_floor_applied"]) for x in fitted)
                    boundaries={k:sum(float(x["component_variances"][k])==0.
                                      for x in fitted) for k in COMPONENTS}
                    matched=bool(fitted[0]["matches_generating_covariance_shape_for_audit_only"]) if fitted else (
                        family==("predictor_scaled_slope" if support.endswith("_dependent") else "shared_slope"))
                    recover={
                        k:(float(np.median([x["relative_component_errors_for_matched_family_only"][k]
                                         for x in fitted])) if fitted and matched else None)
                        for k in COMPONENTS
                    }
                    groups[name]={
                        "planned_independent_blocks":BLOCKS,
                        "recorded":len(cell),
                        "estimator_successes":len(fitted),
                        "estimator_failures":len(cell)-len(fitted),
                        "numerical_cr2_acceptances":len(accepted),
                        "numerical_cr2_refusals":sum(
                            x["numerical_cr2_status"]=="refused" for x in fitted),
                        "sensor_floor_cases":floors,
                        "estimator_success_wilson_95pct":binomial_wilson(len(fitted),len(cell)),
                        "unconditional_numerical_acceptance_wilson_95pct":binomial_wilson(len(accepted),len(cell)),
                        "sensor_floor_among_estimated_wilson_95pct":binomial_wilson(floors,len(fitted)),
                        "mean_component_rank":float(np.mean([x["component_rank"] for x in fitted])) if fitted else None,
                        "median_component_condition":float(np.median([x["component_condition_number"] for x in fitted])) if fitted else None,
                        "median_residual_moment_fit":float(np.median([x["normalized_residual_moment_fit"] for x in fitted])) if fitted else None,
                        "component_zero_counts_among_estimated":boundaries,
                        "matching_generating_shape_for_diagnostics_only":matched,
                        "median_relative_component_errors_if_matching_only":recover,
                        "no_inferential_coverage_computed":True,
                    }
    return {
        "study":STUDY,"master_seed":MASTER_SEED,"independent_generating_blocks":BLOCKS,
        "participant_sizes":SIZES,"source_supports":SUPPORT,"mean_bases":BASES,
        "prespecified_covariance_families":WORKING_FAMILIES,
        "planned_evaluations":PLANNED,"recorded_evaluations":len(rows),
        "missing_evaluations":len(expected-set(actual)),
        "source_generation_failures":sum(not x["source_generated"] for x in rows),
        "estimator_failures":sum(x["estimator_status"]!="ok" for x in rows),
        "numerical_cr2_refusals":sum(x["numerical_cr2_status"]=="refused" for x in rows),
        "numerical_cr2_acceptances":sum(x["numerical_cr2_status"]=="accepted" for x in rows),
        "groups":groups,
        "only_identifiability_and_numerical_feasibility":True,
        "pointwise_coverage_evaluated":False,
        "covariance_estimation_uncertainty_qualified":False,
        "simultaneous_bands_qualified":False,
        "release_authorized":False,
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    rows=[evaluate(b,n,s,m,f)
          for b in range(BLOCKS) for n in SIZES
          for s in SUPPORT for m in BASES for f in WORKING_FAMILIES]
    report=summarize(rows)
    for name,obj in (("case-ledger.json",rows),("summary.json",report)):
        (args.out/name).write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (args.out/"source-commit.txt").write_text(os.getenv("GITHUB_SHA","unverified-local")+"\n")
    filenames=("case-ledger.json","summary.json","source-commit.txt")
    (args.out/"SHA256SUMS").write_text("".join(
        hashlib.sha256((args.out/name).read_bytes()).hexdigest()+"  "+name+"\n"
        for name in filenames))
    print("R23 IDENTIFIABILITY AUDIT:",json.dumps(
        {k:v for k,v in report.items() if k!="groups"},sort_keys=True))
    for name,group in report["groups"].items():
        print("R23 CELL:",json.dumps({"cell":name,**group},sort_keys=True))
    if (report["missing_evaluations"] or report["recorded_evaluations"]!=PLANNED
        or report["source_generation_failures"]):
        raise SystemExit("Incomplete original research source; preserve all failures")
    # NOTE: estimator failures and numerical refusals are reported but are
    # NOT CI errors; this study measures their frequency rather than hiding them.


if __name__=="__main__":
    main()
