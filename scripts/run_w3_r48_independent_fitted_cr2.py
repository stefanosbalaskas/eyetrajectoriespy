"""W3 R48: truly independent Gaussian oracle-vs-fitted CR2 pointwise audit.

Research only: 128 NEW primitive Gaussian blocks, each with exactly n24
participants and genuine positive predictor-dependent random slope. Paired
ordinary vs extreme leverage variants within block, complete native trials.
True generating covariance used only by separate ORACLE. Observed-only REML
fitted covariance plugged into scaled-Cholesky CR2 conditional Satterthwaite
and G-1 t intervals. 128 independent blocks per leverage stratum, never 256
independent draws. Every source, nuisance, numerical refusal and coverage
decision accounted for in prespecified all-planned-block denominator.
No nuisance-estimation-aware Satterthwaite adjustment, no CR2 qualification.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np
from scipy.stats import t as student_t

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts import run_w3_r16_leverage_covariance_factorial as r16
from scripts import run_w3_r17_fresh_feasibility as fresh
from scripts import run_w3_r32_reml_plugin_cr2_feasibility as r32
from scripts import run_w3_r47_independent_pointwise_audit as r47
from scripts.w3_r20_estimated_working_target import observed_weighted_rows
from scripts.w3_r25_gaussian_reml_components import estimate_reml_components
from scripts.w3_r22_scaled_cholesky_cr2 import stable_cr2_blockwise_wls

STUDY="W3_R48_INDEPENDENT_ORACLE_FITTED_TARGET_CR2_POINTWISE_AUDIT"
MASTER_SEED=202610164848
BLOCKS=128
PARTICIPANTS=24
SUPPORT=("ordinary_dependent","extreme_dependent")
GENERATING_SLOPE="positive"
WORKING_FAMILY="predictor_scaled_slope"
TARGETS=("known_source_covariance","fitted_REML_observed_covariance")
REFERENCES=("conditional_satterthwaite","participant_gminus1")
BASIS="legendre5"
NOMINAL=.90
PLANNED_SOURCES=BLOCKS*len(SUPPORT)
PLANNED_TARGETS=PLANNED_SOURCES*len(TARGETS)
PLANNED_INTERVALS=PLANNED_TARGETS*len(REFERENCES)


def original_source(block,support):
    if (type(block) is not int or block not in range(BLOCKS)
            or support not in SUPPORT):
        raise ValueError("R48 source outside frozen independent design")
    return fresh.fresh_source(
        block,support,n=PARTICIPANTS,master_seed=MASTER_SEED,
        n_blocks=BLOCKS,max_n=PARTICIPANTS,
    )


def native_data(case):
    """Fixed observed-only design plus post-fit simulation truth reference."""
    X,y,w,groups,time,trial,x=observed_weighted_rows(
        (None,case[1],case[2],case[3],case[4],None),BASIS)
    Z=X*np.sqrt(w)[:,None]
    mean=np.concatenate(case[5])
    if len(mean)!=len(y):
        raise ValueError("original generating native mean misalignment")
    nb=r16.basis(np.asarray([r16.TIME[r16.FOCAL]]),BASIS)[0]
    c=np.r_[np.zeros(len(nb)),nb]
    coef=np.linalg.lstsq(Z,mean*np.sqrt(w),rcond=None)[0]
    truth=float(c@coef)
    original_truth=float(r16.truth_coefficients(
        np.asarray([r16.TIME[r16.FOCAL]]))[1][0,0])
    if not np.isfinite(truth):
        raise ValueError("R48 nonfinite projected generating truth")
    return (X,y,w,groups,time,trial,x,c,truth,
            original_truth)


def failed(label,error,kind="NumericalRefusal"):
    return {"target":label,"status":"refused",
            "error":{"type":kind,"message":str(error)[:450]},
            "conditional_on_target_only":True,
            "nuisance_estimation_uncertainty_adjusted":False,
            "intervals":[{"reference":x,"status":"refused",
                          "truth_included":False} for x in REFERENCES]}


def target_intervals(label,fit,truth):
    try:
        se=float(fit["cr2_se"])
        df=float(fit["satterthwaite_df"])
        g=int(fit["clusters"])
        est=float(fit["point"])
        if not all(np.isfinite(x) and x>0 for x in (se,df)):
            raise ValueError("nonfinite/nonpositive pointwise CR2 diagnostics")
        out={
            "target":label,"status":"accepted",
            "point":est,"se_cr2":se,
            "conditional_satterthwaite_df":df,
            "max_product_condition":float(
                fit["max_normalized_product_condition"]),
            "max_adjustment_identity_error":float(
                fit["max_relative_adjustment_identity_error"]),
            "conditional_on_target_only":True,
            "nuisance_estimation_uncertainty_adjusted":False,
            "intervals":[],
        }
        for reference,critical_df in (
            (REFERENCES[0],df),(REFERENCES[1],g-1)):
            crit=float(student_t.ppf(.95,critical_df))
            if not np.isfinite(crit) or crit<=0:
                raise ValueError("invalid CR2 t critical value")
            half=crit*se
            out["intervals"].append({
                "reference":reference,"status":"ok",
                "lower":est-half,"upper":est+half,
                "half_width":half,"truth_included":bool(
                    abs(est-truth)<=half),
                "target_is_oracle":label==TARGETS[0],
                "target_estimated_from_same_y":label==TARGETS[1],
            })
        return out
    except Exception as exc:
        return failed(label,exc,type(exc).__name__)


def evaluate(block,support):
    item={
        "study":STUDY,"block":block,"support":support,
        "source_status":"failed","source_error":None,
        "source_seed":MASTER_SEED,
        "independent_primitive_unit_is_block":True,
        "support_conditions_paired_within_block":True,
        "original_positive_gaussian_random_slope":True,
        "participants":PARTICIPANTS,
        "working_covariance_family":WORKING_FAMILY,
        "targets":[],"nuisance_fit":{
            "status":"not_attempted","error":None},
        "release_authorized":False,
    }
    try:
        source=original_source(block,support)
        X,y,w,g,t,tr,x,c,truth,original_truth=native_data(source)
        item["source_status"]="ok"
        item["generating_projected_focal_truth"]=truth
        item["generating_raw_focal_truth"]=original_truth
        item["projection_minus_raw_truth"]=float(truth-original_truth)
        item["native_points"]=len(y)
        item["native_trials"]=len(source[1].time)
        oracle=r32.known_gaussian_blocks(
            g,t,tr,x,w,WORKING_FAMILY)
        # Oracle never enters the fitted REML estimator below.
    except Exception as exc:
        item["source_error"]={"type":type(exc).__name__,
                              "message":str(exc)[:400]}
        item["targets"]=[
            failed(label,item["source_error"],"SourceGenerationRefusal")
            for label in TARGETS]
        return item

    try:
        computed=stable_cr2_blockwise_wls(
            X,y,w,g,c,oracle)
        item["targets"].append(target_intervals(TARGETS[0],computed,truth))
    except Exception as exc:
        item["targets"].append(
            failed(TARGETS[0],exc,type(exc).__name__))

    try:
        reml=estimate_reml_components(
            X,y,w,g,t,tr,x,slope=WORKING_FAMILY)
        item["nuisance_fit"]={
            "status":reml["status"],
            "variance_components":reml["variance_components"],
            "active_lower_box_components":reml["active_lower_box_components"],
            "near_boundary_components":reml["near_boundary_components"],
            "maximum_absolute_logscore":reml["maximum_absolute_logscore"],
            "optimizer_iterations":reml["optimizer_iterations"],
            "optimizer_success":reml["optimizer_success"],
            "fitted_from_observed_y_not_oracle":True,
            "no_global_optimum_or_physical_KKT_certificate":True,
            "nuisance_estimation_uncertainty_included":False,
        }
        if reml["status"]!="ok":
            item["targets"].append(failed(
                TARGETS[1],reml.get("optimizer_message"),
                "REML_nonconverged"))
        else:
            fitted=stable_cr2_blockwise_wls(
                X,y,w,g,c,reml["working_blocks"])
            item["targets"].append(
                target_intervals(TARGETS[1],fitted,truth))
    except Exception as exc:
        item["nuisance_fit"]={
            "status":"failed","error":{
                "type":type(exc).__name__,"message":str(exc)[:400]}}
        item["targets"].append(
            failed(TARGETS[1],exc,type(exc).__name__))
    return item


def wilson(k,n):
    if not isinstance(k,int) or not isinstance(n,int) or not 0<=k<=n or n<1:
        raise ValueError("invalid independent Monte Carlo denominator")
    return r47.wilson(k,n)


def summarize(rows):
    keys=[(r["block"],r["support"]) for r in rows]
    if (len(keys)!=len(set(keys)) or any(
        type(b) is not int or b not in range(BLOCKS) or s not in SUPPORT
        for b,s in keys)):
        raise ValueError("R48 duplicated or unregistered source identity")
    targets=[t for r in rows for t in r["targets"]]
    intervals=[v for t in targets for v in t["intervals"]]
    if any(tuple(t["target"] for t in r["targets"])!=TARGETS
           for r in rows):
        raise ValueError("R48 required target ordering/refusals incomplete")
    if any(tuple(v["reference"] for v in t["intervals"])!=REFERENCES
           for t in targets):
        raise ValueError("R48 conditional t/Sat interval status not retained")
    full=(len(rows)==PLANNED_SOURCES and
          len(targets)==PLANNED_TARGETS and
          len(intervals)==PLANNED_INTERVALS)
    strata={}
    for support in SUPPORT:
        rs=[r for r in rows if r["support"]==support]
        targets_group={}
        for target in TARGETS:
            fits=[t for r in rs for t in r["targets"]
                  if t["target"]==target]
            accepted=[f for f in fits if f["status"]=="accepted"]
            reference_stats={}
            for reference in REFERENCES:
                records=[v for f in fits for v in f["intervals"]
                         if v["reference"]==reference]
                hits=sum(v["status"]=="ok" and v["truth_included"]
                         for v in records)
                reference_stats[reference]={
                    "planned_independent_source_blocks":BLOCKS,
                    "recorded_interval_slots":len(records),
                    "accepted":sum(v["status"]=="ok" for v in records),
                    "failed_or_refused":sum(v["status"]!="ok" for v in records),
                    "truth_included_unconditional_count":hits,
                    "unconditional_truth_inclusion_fraction":hits/BLOCKS,
                    "Wilson95_independent_source":wilson(hits,BLOCKS),
                    "nominal_90_inside_Wilson95":(
                        wilson(hits,BLOCKS)[0]<=NOMINAL<=
                        wilson(hits,BLOCKS)[1]),
                    "mean_successful_half_width":(
                        float(np.mean([v["half_width"] for v in records
                                       if v["status"]=="ok"]))
                        if any(v["status"]=="ok" for v in records)
                        else None),
                }
            targets_group[target]={
                "planned":BLOCKS,"recorded":len(fits),
                "numerically_accepted":len(accepted),
                "refused":len(fits)-len(accepted),
                "median_conditional_Satterthwaite_df":(
                    float(np.median([f["conditional_satterthwaite_df"]
                                     for f in accepted])) if accepted else None),
                "median_CR2_se":(
                    float(np.median([f["se_cr2"] for f in accepted]))
                    if accepted else None),
                "reference_intervals":reference_stats,
            }
        pairs=[]
        for r in rs:
            oracle,plugin=r["targets"]
            if oracle["status"]=="accepted" and plugin["status"]=="accepted":
                o={x["reference"]:x for x in oracle["intervals"]}
                p={x["reference"]:x for x in plugin["intervals"]}
                pairs.append({
                    "oracle_minus_fitted_conditional_df":
                        oracle["conditional_satterthwaite_df"]-
                        plugin["conditional_satterthwaite_df"],
                    "fitted_over_oracle_half_width":
                        p[REFERENCES[0]]["half_width"]/
                        o[REFERENCES[0]]["half_width"],
                    "Sat_inclusion_disagrees":
                        o[REFERENCES[0]]["truth_included"]!=
                        p[REFERENCES[0]]["truth_included"],
                })
        strata[support]={
            "planned_independent_blocks":BLOCKS,
            "recorded_cases":len(rs),
            "source_failures":sum(r["source_status"]!="ok" for r in rs),
            "REML_fit_failures":sum(
                r["nuisance_fit"]["status"]!="ok" for r in rs),
            "median_abs_generating_mean_projection_difference":(
                float(np.median([abs(r["projection_minus_raw_truth"])
                                 for r in rs if r["source_status"]=="ok"]))
                if any(r["source_status"]=="ok" for r in rs) else None),
            "paired_oracle_fitted_accepted":len(pairs),
            "paired_conditional_Sat_decision_disagreements":sum(
                x["Sat_inclusion_disagrees"] for x in pairs),
            "median_fitted_to_oracle_Sat_half_width":(
                float(np.median([x["fitted_over_oracle_half_width"]
                                 for x in pairs])) if pairs else None),
            "targets":targets_group,
        }
    return {
        "study":STUDY,"seed":MASTER_SEED,
        "new_independent_primitive_blocks":BLOCKS,
        "participants_per_block":PARTICIPANTS,
        "paired_leverage_states_not_256_independent_blocks":True,
        "source_family":WORKING_FAMILY,
        "planned_source_cases":PLANNED_SOURCES,
        "recorded_source_cases":len(rows),
        "planned_target_evaluations":PLANNED_TARGETS,
        "recorded_target_evaluations":len(targets),
        "planned_interval_records":PLANNED_INTERVALS,
        "recorded_interval_records":len(intervals),
        "complete_failure_inclusive_numerical_ledger":full,
        "source_failures":sum(r["source_status"]!="ok" for r in rows),
        "fitted_REML_nonconvergence_or_failure":sum(
            r["nuisance_fit"]["status"]!="ok" for r in rows),
        "numerical_CR2_target_refusals":sum(
            t["status"]!="accepted" for t in targets),
        "independent_source_strata":strata,
        "original_oracle_not_used_for_estimated_covariance":True,
        "fitted_nuisance_sampling_uncertainty_NOT_accounted_in_Sat_df":True,
        "observed_REML_KKT_global_certification_not_demonstrated":True,
        "90pct_pointwise_CR2_qualification":False,
        "90pct_simultaneous_function_band_qualification":False,
        "Gaussian_boundary_null_typeI_calibration":False,
        "MNAR_or_whole_participant_selection_identified":False,
        "release_authorized":False,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    rows=[evaluate(b,s) for b in range(BLOCKS) for s in SUPPORT]
    report=summarize(rows)
    for name,obj in (("cases.json",rows),("summary.json",report)):
        (args.out/name).write_text(
            json.dumps(obj,sort_keys=True,indent=2,allow_nan=False)+"\n")
    (args.out/"source-commit.txt").write_text(
        os.environ.get("GITHUB_SHA","unverified-local")+"\n")
    files=("cases.json","summary.json","source-commit.txt")
    (args.out/"SHA256SUMS").write_text("".join(
        hashlib.sha256((args.out/f).read_bytes()).hexdigest()+"  "+f+"\n"
        for f in files))
    print("R48 independent fitted-CR2 Monte Carlo:",json.dumps(
        report,sort_keys=True))
    if (not report["complete_failure_inclusive_numerical_ledger"]):
        raise SystemExit("R48 source/target/interval stage omission; ledger retained")


if __name__=="__main__":
    main()
