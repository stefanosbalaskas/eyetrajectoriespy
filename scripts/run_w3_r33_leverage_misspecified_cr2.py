"""R33 experimental high-leverage and working-family CR2 falsification.

NEW 24 independent generating blocks; nested 24/96 participants; ordinary vs
two-extreme-predictor support crossed with predictor-independent/dependent
Gaussian covariance. For each source fit both prespecified covariance
families, correct and deliberately wrong. Compare each observed-only REML
plug-in CR2 result to the independently reconstructed generating-target CR2,
including numerical refusals, boundary flags and 90%-nominal pointwise truth
inclusion. Scientific research only, NEVER public inferential qualification.

The 384 (24*2*4*2) paired-model rows contain 24 independently seeded generating
blocks, not 384 independent Monte Carlo source experiments.
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

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import run_w3_r16_leverage_covariance_factorial as r16
from scripts import run_w3_r17_fresh_feasibility as fresh
from scripts import run_w3_r32_reml_plugin_cr2_feasibility as r32
from scripts.w3_r20_estimated_working_target import COMPONENTS, MODELS, observed_weighted_rows
from scripts.w3_r25_gaussian_reml_components import estimate_reml_components
from scripts.w3_r22_scaled_cholesky_cr2 import stable_cr2_blockwise_wls

STUDY = "W3_R33_INDEPENDENT_LEVERAGE_MISSPECIFIED_CR2_FALSIFICATION"
MASTER_SEED = 202610153333
BLOCKS = 24
SIZES = (24, 96)
SUPPORT = r16.SUPPORT
WORKING_FAMILIES = MODELS
BASIS = "legendre5"
TARGETS = ("known_source_covariance", "observed_reml_working_covariance")
PLANNED = BLOCKS * len(SIZES) * len(SUPPORT) * len(WORKING_FAMILIES)
NOMINAL = .90


def wilson(k, n):
    if n <= 0:
        return None
    z = float(norm.ppf(.975))
    p = float(k)/n
    den = 1 + z*z/n
    center = (p + z*z/(2*n))/den
    half = z*np.sqrt(p*(1-p)/n + z*z/(4*n*n))/den
    return [0.0 if k==0 else float(max(0,center-half)),
            1.0 if k==n else float(min(1,center+half))]


def source_working_family(support):
    if support not in SUPPORT:
        raise ValueError("unregistered original source support")
    return "predictor_scaled_slope" if support.endswith("_dependent") else "shared_slope"


def original_source(block, n, support):
    return fresh.fresh_source(block,support,n=n,master_seed=MASTER_SEED,
                              n_blocks=BLOCKS,max_n=max(SIZES))


def native_problem(block,n,support):
    original=original_source(block,n,support)
    observed=(None,original[1],original[2],original[3],original[4],None)
    X,y,w,groups,time,trial,x=observed_weighted_rows(observed,BASIS)
    mean=np.concatenate(original[5])
    if mean.shape!=y.shape:
        raise ValueError("generating native mean alignment contract")
    Z=X*np.sqrt(w)[:,None]
    nb=r16.basis(np.asarray([r16.TIME[r16.FOCAL]],float),BASIS)[0]
    contrast=np.r_[np.zeros(len(nb)),nb]
    coef=np.linalg.lstsq(Z,mean*np.sqrt(w),rcond=None)[0]
    truth=float(contrast@coef)
    source_mode=source_working_family(support)
    oracle=r32.known_gaussian_blocks(groups,time,trial,x,w,source_mode)
    x_participant=np.array([x[np.flatnonzero(groups==g)[0]]
                            for g in np.unique(groups)])
    if support.startswith("extreme"):
        if not (np.isclose(x_participant[0],3.) and
                np.isclose(x_participant[1],-2.5)):
            raise ValueError("original high-leverage predictor source lost")
    else:
        if np.max(np.abs(x_participant))>1:
            raise ValueError("ordinary predictor control unexpected")
    return {
      "X":X,"y":y,"w":w,"groups":groups,"time":time,"trial":trial,"x":x,
      "contrast":contrast,"truth":truth,"oracle":oracle,
      "original_focal_truth":float(r16.truth_coefficients(r16.TIME)[1,r16.FOCAL,0]),
      "original_sample_points":len(y),
      "extreme_predictor_count":int(np.sum(np.abs(x_participant)>1.)),
      "participants":n,
    }


def cr2_interval(p,target):
    out={"status":"failed", "satterthwaite_included":None,
         "t_gminus1_included":None,"nuisance_estimation_uncertainty_included":False,
         "numerical_refusal":None}
    try:
        f=stable_cr2_blockwise_wls(
            p["X"],p["y"],p["w"],p["groups"],p["contrast"],target)
        se=float(f["cr2_se"])
        df=float(f["satterthwaite_df"])
        g=int(p["participants"])
        sat=float(student_t.ppf(.95,df))
        conventional=float(student_t.ppf(.95,g-1))
        if not all(np.isfinite(v) and v>0 for v in (se,df,sat,conventional)):
            raise ValueError("invalid finite CR2 uncertainty/critical value")
        miss=abs(float(f["point"])-p["truth"])
        out.update({
            "status":"accepted","numerical_refusal":False,
            "point":float(f["point"]),"cr2_se":se,
            "satterthwaite_df_conditional_on_target":df,
            "satterthwaite_90pct_half_width":float(sat*se),
            "t_gminus1_90pct_half_width":float(conventional*se),
            "satterthwaite_included":bool(miss<=sat*se),
            "t_gminus1_included":bool(miss<=conventional*se),
            "maximum_product_condition":float(f["max_normalized_product_condition"]),
            "maximum_adjustment_identity_error":float(f["max_relative_adjustment_identity_error"]),
            "mean_projection_error":float(miss),
        })
    except Exception as exc:
        out["status"]="refused"
        out["numerical_refusal"]=True
        out["refusal"]={"type":type(exc).__name__,"message":str(exc)[:650]}
    return out


def evaluate(block,n,support,family):
    item={"study":STUDY,"source_block":block,"participants":n,
          "source_support":support,"fitted_working_family":family,
          "covariance_model_matched":family==source_working_family(support),
          "source_generated":False,"source_failure":None,
          "rem_likelihood_status":"not_attempted",
          "rem_likelihood_failure":None,
          "estimated_variances_from_observed_only":True,
          "simulation_truth_not_passed_to_rem_likelihood":True,
          "targets":{},
          "no_statistical_coverage_qualification":True,
          "release_authorized":False}
    if family not in WORKING_FAMILIES:
        raise ValueError("undeclared working covariance")
    try:
        p=native_problem(block,n,support)
        item.update(
          source_generated=True,
          source_native_points=p["original_sample_points"],
          extreme_predictor_count=p["extreme_predictor_count"],
          original_true_functional_slope=p["original_focal_truth"],
          projected_truth=p["truth"],
          projection_discrepancy=p["truth"]-p["original_focal_truth"])
    except Exception as exc:
        item["source_failure"]={"type":type(exc).__name__,"message":str(exc)[:650]}
        return item
    # Generator covariance is deliberately NEVER supplied to the REML fitter.
    item["targets"]["known_source_covariance"]=cr2_interval(p,p["oracle"])
    try:
        rem=estimate_reml_components(p["X"],p["y"],p["w"],p["groups"],
             p["time"],p["trial"],p["x"],slope=family)
        item["rem_likelihood_status"]=rem["status"]
        item["observed_variance_components"]=rem["variance_components"]
        item["near_lower_variance_boundary"]=rem["near_boundary_components"]
        item["active_numerical_lower_bounds"]=rem["active_lower_box_components"]
        item["rem_likelihood_optimizer_success"]=rem["optimizer_success"]
        if rem["status"]=="ok":
            item["targets"]["observed_reml_working_covariance"]=cr2_interval(
                p,rem["working_blocks"])
        else:
            item["rem_likelihood_failure"]={
              "type":"Nonconvergence","message":rem["optimizer_message"]}
    except Exception as exc:
        item["rem_likelihood_status"]="failed"
        item["rem_likelihood_failure"]={
            "type":type(exc).__name__,"message":str(exc)[:650]}
    if "observed_reml_working_covariance" not in item["targets"]:
        item["targets"]["observed_reml_working_covariance"]={
          "status":"nuisance_estimation_failure",
          "numerical_refusal":None,
          "satterthwaite_included":None,
          "t_gminus1_included":None,
          "nuisance_estimation_uncertainty_included":False}
    item["both_targets_accepted"]=all(
        item["targets"][label]["status"]=="accepted" for label in TARGETS)
    if item["both_targets_accepted"]:
        a=item["targets"]["known_source_covariance"]
        b=item["targets"]["observed_reml_working_covariance"]
        item["pair_diagnostics"]={
          "satterthwaite_inclusion_disagrees":a["satterthwaite_included"]!=b["satterthwaite_included"],
          "t_gminus1_inclusion_disagrees":a["t_gminus1_included"]!=b["t_gminus1_included"],
          "plug_in_to_oracle_cr2_se_ratio":float(b["cr2_se"]/a["cr2_se"]),
          "plug_in_minus_oracle_satterthwaite_df":float(
              b["satterthwaite_df_conditional_on_target"]-
              a["satterthwaite_df_conditional_on_target"]),
          "plug_in_to_oracle_90pct_halfwidth_ratio":float(
              b["satterthwaite_90pct_half_width"]/a["satterthwaite_90pct_half_width"]),
        }
    else:
        item["pair_diagnostics"]=None
    if item["covariance_model_matched"] and item["rem_likelihood_status"]=="ok":
        item["matched_source_slope_below_5pct_truth_postfit_only"]=bool(
          item["observed_variance_components"]["participant_slope"]<
           .05*r32.SOURCE_VARIANCES["participant_slope"])
    else:
        item["matched_source_slope_below_5pct_truth_postfit_only"]=None
    return item


def aggregate(rows):
    expected={(b,n,s,f) for b in range(BLOCKS) for n in SIZES
              for s in SUPPORT for f in WORKING_FAMILIES}
    keys=[(x["source_block"],x["participants"],x["source_support"],
           x["fitted_working_family"]) for x in rows]
    if len(keys)!=len(set(keys)) or not set(keys).issubset(expected):
        raise ValueError("duplicate/unregistered original source-model pairing")
    strata={}
    for n in SIZES:
        for s in SUPPORT:
            for family in WORKING_FAMILIES:
                cases=[x for x in rows if x["participants"]==n and
                       x["source_support"]==s and x["fitted_working_family"]==family]
                targets={}
                for label in TARGETS:
                    fits=[x["targets"].get(label,{}) for x in cases]
                    accepted=[z for z in fits if z.get("status")=="accepted"]
                    hits=sum(z["satterthwaite_included"] for z in accepted)
                    targets[label]={
                      "total_original_block_cases":len(cases),
                      "computations_accepted":len(accepted),
                      "numerically_refused":sum(z.get("status")=="refused" for z in fits),
                      "nuisance_estimator_failed":sum(
                          z.get("status")=="nuisance_estimation_failure" for z in fits),
                      "computation_wilson_95pct":wilson(len(accepted),len(cases)),
                      "conditional_on_success_satterthwaite_hits":hits,
                      "conditional_on_success_inclusion_rate":(
                        float(hits/len(accepted)) if accepted else None),
                      "inclusion_wilson_95pct":wilson(hits,len(accepted)),
                      "joint_numerical_acceptance_and_inclusion_rate":(
                        float(hits/len(cases)) if cases else None),
                      "median_conditional_df":(
                        float(np.median([z["satterthwaite_df_conditional_on_target"]
                          for z in accepted])) if accepted else None),
                      "median_cr2_se":(
                        float(np.median([z["cr2_se"] for z in accepted])) if accepted else None),
                      "inferential_coverage_qualified":False}
                paired=[x for x in cases if x.get("both_targets_accepted")]
                deltas=[x["pair_diagnostics"] for x in paired]
                strata[f"n{n}/{s}/{family}"]={
                   "independent_original_source_blocks":len(cases),
                   "covariance_model_matches_generator":family==source_working_family(s),
                   "reml_optimizer_failures":sum(
                       x["source_generated"] and x["rem_likelihood_status"]!="ok"
                       for x in cases),
                   "source_generation_failures":sum(not x["source_generated"] for x in cases),
                   "rem_slope_near_zero_matched_only":(
                       sum(x.get("matched_source_slope_below_5pct_truth_postfit_only") is True
                           for x in cases) if family==source_working_family(s) else None),
                   "both_targets_accepted":len(paired),
                   "inclusion_disagreements":sum(
                       z["satterthwaite_inclusion_disagrees"] for z in deltas),
                   "median_plugin_to_oracle_se_ratio":(
                       float(np.median([z["plug_in_to_oracle_cr2_se_ratio"] for z in deltas]))
                       if deltas else None),
                   "median_plugin_to_oracle_halfwidth_ratio":(
                       float(np.median([z["plug_in_to_oracle_90pct_halfwidth_ratio"]
                           for z in deltas])) if deltas else None),
                   "targets":targets,
                   "source_cases_not_independent_across_working_family":True}
    return {
      "study":STUDY,"master_seed":MASTER_SEED,
      "independently_generated_source_blocks":BLOCKS,
      "nested_participant_sizes":SIZES,
      "source_design_conditions":SUPPORT,
      "fitted_working_covariance_families":WORKING_FAMILIES,
      "planned_model_source_evaluations":PLANNED,
      "recorded_model_source_evaluations":len(rows),
      "missing_model_source_evaluations":len(expected-set(keys)),
      "source_failures":sum(not x["source_generated"] for x in rows),
      "reml_optimizer_failures":sum(
           x["source_generated"] and x["rem_likelihood_status"]!="ok"
           for x in rows),
      "oracle_refusals":sum(
           x["targets"].get("known_source_covariance",{}).get("status")=="refused"
           for x in rows),
      "fitted_target_cr2_refusals":sum(
           x["targets"].get("observed_reml_working_covariance",{}).get("status")=="refused"
           for x in rows),
      "model_families_share_original_response_in_each_source_case":True,
      "strata":strata,
      "nominal_inclusion_reference":NOMINAL,
      "paired_truth_inclusion_is_not_nominal_calibration":True,
      "all_source_outcomes_including_refusals_preserved":True,
      "estimated_covariance_uncertainty_included_in_satterthwaite_df":False,
      "pointwise_coverage_qualified":False,
      "whole_function_simultaneous_bands_qualified":False,
      "public_api_authorized":False,
      "release_authorized":False,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    rows=[evaluate(b,n,s,f) for b in range(BLOCKS)
          for n in SIZES for s in SUPPORT for f in WORKING_FAMILIES]
    report=aggregate(rows)
    for name,obj in (("case-ledger.json",rows),("summary.json",report)):
        (args.out/name).write_text(json.dumps(obj,sort_keys=True,indent=2)+"\n")
    (args.out/"source-commit.txt").write_text(
        os.getenv("GITHUB_SHA","unverified-local")+"\n")
    names=("case-ledger.json","summary.json","source-commit.txt")
    (args.out/"SHA256SUMS").write_text("".join(
        hashlib.sha256((args.out/name).read_bytes()).hexdigest()+"  "+name+"\n"
        for name in names))
    print("R33 LEVERAGE MIS-SPECIFIED INFERENCE AUDIT:",json.dumps(
        {k:v for k,v in report.items() if k!="strata"},sort_keys=True))
    for key,v in report["strata"].items():
        print("R33 INFERENCE CELL:",json.dumps({"cell":key,**v},sort_keys=True))
    if report["missing_model_source_evaluations"] or report["source_failures"]:
        raise SystemExit("R33 original source missing; retain failures as evidence")


if __name__=="__main__":
    main()
