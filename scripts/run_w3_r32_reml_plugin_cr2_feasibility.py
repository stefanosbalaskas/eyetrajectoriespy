"""R32 exploratory failure-inclusive CR2 with specified vs fitted covariance.

NEW 16 independent Gaussian source blocks, native complete versus observed-time
MAR point deletion, n24/n96, two covariance-generating mechanisms, fixed
Legendre5 mean basis. Each source comparison fits original REML nuisance
components from only observed data, and constructs a separate simulation-TRUE
Gaussian covariance target only for the ORACLE reference computation.

Uses a projected known generating mean contrast as the estimand, removing
mean-basis approximation from the *definition* of truth (without asserting a
correct mean model). Evaluates exploratory 90%-nominal pointwise inclusion,
explicit numerical refusal and failures, NOT statistical qualification.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np
from scipy.stats import t as student_t, norm

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts import run_w3_r16_leverage_covariance_factorial as r16
from scripts import run_w3_r17_fresh_feasibility as fresh
from scripts import run_w3_r31_observation_process_recovery as r31
from scripts.w3_r20_estimated_working_target import (
    COMPONENTS,_kernels,observed_weighted_rows)
from scripts.w3_r25_gaussian_reml_components import estimate_reml_components
from scripts.w3_r22_scaled_cholesky_cr2 import stable_cr2_blockwise_wls

STUDY="W3_R32_FRESH_REML_PLUGIN_CR2_POINTWISE_FEASIBILITY"
SOURCE_SEED=202610153232
BLOCKS=16
SIZES=(24,96)
SUPPORT=("ordinary_independent","ordinary_dependent")
OBSERVATION=("complete","time_mar_20")
BASIS="legendre5"
TARGETS=("known_gaussian_target","reml_estimated_target")
NOMINAL=.90
SOURCE_VARIANCES=r31.TRUE_COMPONENTS
PLANNED=BLOCKS*len(SIZES)*len(SUPPORT)*len(OBSERVATION)


def wilson(k,n):
    if n<=0:return None
    z=float(norm.ppf(.975));p=k/n;den=1+z*z/n
    mid=(p+z*z/(2*n))/den
    delta=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [float(max(0,mid-delta)),float(min(1,mid+delta))]


def known_gaussian_blocks(cluster,time,trial,x,w,family):
    indices=[np.flatnonzero(cluster==label) for label in np.unique(cluster)]
    blocks=[]
    for ix in indices:
        K=_kernels(time[ix],trial[ix],x[ix],w[ix],family)
        V=sum(float(SOURCE_VARIANCES[name])*K[j]
              for j,name in enumerate(COMPONENTS))
        blocks.append((V+V.T)/2)
    return blocks


def evaluate(block,n,support,mode):
    result={"study":STUDY,"block":block,"participants":n,
        "support":support,"observation_process":mode,
        "source_generated":False,"source_failure":None,
        "reml_nuisance_status":"not_attempted",
        "reml_nuisance_error":None,
        "targets":{},
        "true_covariance_given_to_nuisance_estimator":False,
        "pointwise_inference_qualified":False,
        "simultaneous_functional_bands_qualified":False,
        "release_authorized":False}
    try:
        generated=fresh.fresh_source(block,support,n=n,
            master_seed=SOURCE_SEED,n_blocks=BLOCKS,max_n=max(SIZES))
        observed,account=r31._native_observation_transform(
            generated,mode,block=block,support=support)
        X,y,w,g,t,tr,x=observed_weighted_rows(
            (None,observed[1],observed[2],observed[3],observed[4],None),BASIS)
        means=np.concatenate(observed[5])
        if means.shape!=y.shape:
            raise ValueError("known generating means misaligned with retained native rows")
        Z=X*np.sqrt(w)[:,None]
        k=r16.basis(np.array([.5]),BASIS).shape[1]
        c=np.r_[np.zeros(k),r16.basis(np.array([r16.TIME[r16.FOCAL]]),BASIS)[0]]
        beta_projected=np.linalg.lstsq(Z,means*np.sqrt(w),rcond=None)[0]
        estimand=float(c@beta_projected)
        original_focal=float(r16.truth_coefficients(
            r16.TIME)[1,r16.FOCAL,0])
        family=("predictor_scaled_slope" if support.endswith("_dependent")
                else "shared_slope")
        oracle=known_gaussian_blocks(g,t,tr,x,w,family)
        result.update({
            "source_generated":True,
            "recorded_original_native_points":account["original_native_points"],
            "retained_native_points":account["retained_native_points"],
            "missing_fraction":account["missing_point_fraction"],
            "known_true_projected_coefficient":estimand,
            "original_functional_slope_at_focal":original_focal,
            "mean_basis_projection_minus_original_focal":estimand-original_focal,
            "working_family":family,
            "observed_input_only":True})
    except Exception as exc:
        result["source_failure"]={"type":type(exc).__name__,
            "message":str(exc)[:500]}
        return result
    targets={"known_gaussian_target":oracle}
    try:
        reml=estimate_reml_components(
            X,y,w,g,t,tr,x,slope=family)
        result["reml_nuisance_status"]=reml["status"]
        result["estimated_component_variances"]=reml["variance_components"]
        result["reml_near_boundary_components"]=reml["near_boundary_components"]
        result["reml_active_lower_bounds"]=reml["active_lower_box_components"]
        if reml["status"]=="ok":
            targets["reml_estimated_target"]=reml["working_blocks"]
        else:
            result["reml_nuisance_error"]={
                "type":"OptimizationNonconverged",
                "message":reml["optimizer_message"]}
    except Exception as exc:
        result["reml_nuisance_status"]="failed"
        result["reml_nuisance_error"]={"type":type(exc).__name__,
            "message":str(exc)[:500]}
    for label in TARGETS:
        item={"status":"not_attempted",
              "numerical_refusal":None,
              "satterthwaite_truth_included":None,
              "t_gminus1_truth_included":None,
              "df_includes_covariance_estimation_uncertainty":False,
              "original_90pct_nominal_qualification":False}
        if label not in targets:
            item["status"]="nuisance_estimator_failed"
            result["targets"][label]=item
            continue
        try:
            fit=stable_cr2_blockwise_wls(
                X,y,w,g,c,targets[label])
            if abs(fit["point"]-estimand)>1e6:
                raise ValueError("nonsensical source coefficient")
            se=float(fit["cr2_se"])
            df=float(fit["satterthwaite_df"])
            crit_sat=float(student_t.ppf(.95,df))
            crit_g=float(student_t.ppf(.95,n-1))
            if not all(np.isfinite(v) and v>0
                       for v in (se,df,crit_sat,crit_g)):
                raise ValueError("invalid fitted CR2 SE or degrees of freedom")
            item.update({
                "status":"accepted",
                "point":float(fit["point"]),
                "cr2_se":se,
                "conditional_satterthwaite_df":df,
                "critical_value_satterthwaite":crit_sat,
                "critical_value_t_gminus1":crit_g,
                "satterthwaite_truth_included":bool(
                    abs(fit["point"]-estimand)<=crit_sat*se),
                "t_gminus1_truth_included":bool(
                    abs(fit["point"]-estimand)<=crit_g*se),
                "maximum_normalized_product_condition":fit[
                    "max_normalized_product_condition"],
                "max_adjustment_identity_error":fit[
                    "max_relative_adjustment_identity_error"],
                "numerical_refusal":False,
            })
        except Exception as exc:
            item.update({
                "status":"refused",
                "numerical_refusal":True,
                "refusal":{"type":type(exc).__name__,
                    "message":str(exc)[:500]},
            })
        result["targets"][label]=item
    return result


def summarize(rows):
    expected={(b,n,s,m) for b in range(BLOCKS) for n in SIZES
              for s in SUPPORT for m in OBSERVATION}
    identities=[(x["block"],x["participants"],x["support"],
                 x["observation_process"]) for x in rows]
    if len(identities)!=len(set(identities)) or not set(identities).issubset(expected):
        raise ValueError("unregistered or duplicate source case")
    strata={}
    for n in SIZES:
        for s in SUPPORT:
            for mode in OBSERVATION:
                matching=[x for x in rows if x["participants"]==n
                    and x["support"]==s and x["observation_process"]==mode]
                outcomes={}
                for target in TARGETS:
                    fit=[x["targets"].get(target,{}) for x in matching]
                    accepted=[x for x in fit if x.get("status")=="accepted"]
                    ksat=sum(x["satterthwaite_truth_included"] for x in accepted)
                    kg=sum(x["t_gminus1_truth_included"] for x in accepted)
                    outcomes[target]={
                        "independent_original_blocks":len(matching),
                        "computationally_accepted":len(accepted),
                        "refused_after_nuisance":sum(
                            x.get("status")=="refused" for x in fit),
                        "nuisance_estimation_failure":sum(
                            x.get("status")=="nuisance_estimator_failed"
                            for x in fit),
                        "acceptance_wilson_95pct":wilson(len(accepted),len(matching)),
                        "satterthwaite_truth_included_among_accepted":ksat,
                        "satterthwaite_inclusion_fraction_conditional_on_acceptance":(
                            float(ksat/len(accepted)) if accepted else None),
                        "satterthwaite_conditional_wilson_95pct":wilson(ksat,len(accepted)),
                        "joint_success_and_truth_inclusion_fraction":(
                            float(ksat/len(matching)) if matching else None),
                        "t_gminus1_truth_included_among_accepted":kg,
                        "t_gminus1_fraction_conditional_on_acceptance":(
                            float(kg/len(accepted)) if accepted else None),
                        "median_satterthwaite_df":(
                            float(np.median([v["conditional_satterthwaite_df"]
                                for v in accepted])) if accepted else None),
                        "median_cr2_standard_error":(
                            float(np.median([v["cr2_se"] for v in accepted])) if accepted else None),
                        "coverage_method_qualified":False}
                strata[f"n{n}/{s}/{mode}"]={
                    "source_cases":len(matching),
                    "reml_nuisance_failures":sum(x["reml_nuisance_status"]!="ok"
                                                for x in matching),
                    "mean_missing_fraction":(
                        float(np.mean([x["missing_fraction"]
                            for x in matching if x["source_generated"]]))
                        if any(x["source_generated"] for x in matching) else None),
                    "known_basis_projection_deviation_median":(
                        float(np.median([abs(x["mean_basis_projection_minus_original_focal"])
                            for x in matching if x["source_generated"]]))
                        if any(x["source_generated"] for x in matching) else None),
                    "targets":outcomes}
    return {
        "study":STUDY,"master_seed":SOURCE_SEED,
        "independent_generating_blocks":BLOCKS,
        "sizes":SIZES,"source_covariance_modes":SUPPORT,
        "observation_processes":OBSERVATION,
        "nominal_reference":NOMINAL,
        "planned_cases":PLANNED,"recorded_cases":len(rows),
        "missing_cases":len(expected-set(identities)),
        "source_failures":sum(not x["source_generated"] for x in rows),
        "reml_nuisance_failures":sum(x["source_generated"] and
            x["reml_nuisance_status"]!="ok" for x in rows),
        "targets":TARGETS,
        "strata":strata,
        "conditional_on_success_inclusion_not_unconditional_coverage":True,
        "known_projected_estimand_not_raw_functional_slope":True,
        "nuisance_estimation_uncertainty_not_in_conditional_satterthwaite":True,
        "pointwise_nominal_coverage_qualified":False,
        "simultaneous_functional_bands_qualified":False,
        "release_authorized":False,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    rows=[evaluate(b,n,s,m) for b in range(BLOCKS)
          for n in SIZES for s in SUPPORT for m in OBSERVATION]
    summary=summarize(rows)
    for filename,obj in (("case-ledger.json",rows),("summary.json",summary)):
        (args.out/filename).write_text(
            json.dumps(obj,sort_keys=True,indent=2)+"\n")
    (args.out/"source-commit.txt").write_text(
        os.getenv("GITHUB_SHA","unverified-local")+"\n")
    names=("case-ledger.json","summary.json","source-commit.txt")
    (args.out/"SHA256SUMS").write_text("".join(
        hashlib.sha256((args.out/name).read_bytes()).hexdigest()+"  "+name+"\n"
        for name in names))
    print("R32 FITTED-TARGET INFERENCE FEASIBILITY:",json.dumps(
        {k:v for k,v in summary.items() if k!="strata"},sort_keys=True))
    for k,v in summary["strata"].items():
        print("R32 INFERENCE CELL:",json.dumps({"cell":k,**v},sort_keys=True))
    if summary["source_failures"] or summary["missing_cases"]:
        raise SystemExit("R32 original-source cases missing; all failures preserved")


if __name__=="__main__":
    main()
