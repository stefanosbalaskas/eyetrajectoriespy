"""R34: local REML-nuisance information and conditional CR2 width sensitivity.

Research-only finite-difference diagnostic on FOUR NEW independent Gaussian
generating blocks. Compare ordinary/extreme predictor leverage and correctly
matched vs deliberately wrong covariance families at n24. For each observed-
only REML fit, independently reconstruct perturbed working covariance blocks,
recompute original stable R22 CR2/Satterthwaite and the restricted-likelihood
observed log-component Hessian. Preserve matrix and CR2 refusals.

An observed Hessian inverse and interval-halfwidth derivative give ONLY a
local nuisance-parameter sensitivity diagnostic. They do NOT propagate all
REML uncertainty into coefficient inference or qualify nominal CI coverage.
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
from scripts import run_w3_r33_leverage_misspecified_cr2 as r33
from scripts.w3_r20_estimated_working_target import COMPONENTS,MODELS,_kernels,observed_weighted_rows
from scripts.w3_r25_gaussian_reml_components import (
    estimate_reml_components, prepare_reml_design, restricted_loglik_and_gradient)
from scripts.w3_r22_scaled_cholesky_cr2 import stable_cr2_blockwise_wls

STUDY="W3_R34_NEW_SOURCE_REML_NUISANCE_LOCAL_INFORMATION"
MASTER_SEED=202610163434
BLOCKS=4
PARTICIPANTS=24
SUPPORT=("ordinary_dependent","extreme_dependent")
FAMILIES=MODELS
LOG_STEPS=(.02,.01)
PLANNED=BLOCKS*len(SUPPORT)*len(FAMILIES)
MAX_OBSERVED_INFORMATION_CONDITION=1e9


def observed_native_problem(block,support):
    original=fresh.fresh_source(block,support,n=PARTICIPANTS,
        master_seed=MASTER_SEED,n_blocks=BLOCKS,max_n=PARTICIPANTS)
    X,y,w,g,t,tr,x=observed_weighted_rows(
        (None,original[1],original[2],original[3],original[4],None),
        "legendre5")
    B=r16.basis(np.asarray([r16.TIME[r16.FOCAL]]),"legendre5")[0]
    c=np.r_[np.zeros(len(B)),B]
    if support.startswith("extreme"):
        subjects=np.unique(g)
        v=np.array([x[np.flatnonzero(g==i)[0]] for i in subjects])
        if not (np.isclose(v[0],3.) and np.isclose(v[1],-2.5)):
            raise ValueError("extreme-leverage source no longer has fixed predictors")
    return X,y,w,g,t,tr,x,c


def covariance_from_components(groups,time,trial,x,weights,family,theta):
    if family not in FAMILIES:
        raise ValueError("undeclared working covariance")
    theta=np.asarray(theta,float)
    if theta.shape!=(len(COMPONENTS),) or np.any(theta<=0) or not np.isfinite(theta).all():
        raise ValueError("four strictly positive finite variance components required")
    out=[]
    for who in np.unique(groups):
        ix=np.flatnonzero(groups==who)
        kernels=_kernels(time[ix],trial[ix],x[ix],weights[ix],family)
        V=sum(float(theta[k])*K for k,K in enumerate(kernels))
        out.append((V+V.T)*.5)
    return out


def cr2_local_metric(data,family,logtheta):
    X,y,w,g,t,tr,x,c=data
    blocks=covariance_from_components(g,t,tr,x,w,family,np.exp(logtheta))
    fitted=stable_cr2_blockwise_wls(X,y,w,g,c,blocks)
    se=float(fitted["cr2_se"])
    df=float(fitted["satterthwaite_df"])
    crit=float(student_t.ppf(.95,df))
    if not (np.isfinite([se,df,crit]).all() and min(se,df,crit)>0):
        raise ValueError("invalid conditional CR2 half-width / df")
    return {"conditional_df":df,"cr2_se":se,
            "halfwidth_90":float(crit*se),
            "log_halfwidth_90":float(np.log(crit*se)),
            "max_adjustment_identity_error":float(
                fitted["max_relative_adjustment_identity_error"])}


def rem_likelihood_curvature(data,family,logtheta,step):
    X,y,w,g,t,tr,x,c=data
    prepared=prepare_reml_design(X,y,w,g,t,tr,x,slope=family)
    p=len(COMPONENTS)
    matrix=np.empty((p,p))
    for k in range(p):
        d=np.zeros(p);d[k]=step
        _,gp=restricted_loglik_and_gradient(logtheta+d,prepared,1.)
        _,gm=restricted_loglik_and_gradient(logtheta-d,prepared,1.)
        matrix[:,k]=(gp-gm)/(2*step)
    asymmetry=float(np.linalg.norm(matrix-matrix.T,ord="fro")/
                    max(np.linalg.norm(matrix,ord="fro"),1e-14))
    return (matrix+matrix.T)*.5,asymmetry


def evaluate(block,support,family):
    row={"study":STUDY,"block":block,"participants":PARTICIPANTS,
         "source_support":support,"working_family":family,
         "covariance_family_correct":family==r33.source_working_family(support),
         "generated":False,"source_error":None,"reml_status":"not_attempted",
         "reml_error":None,"local_metric_status":"not_attempted",
         "local_metric_error":None,"observed_information_status":"not_attempted",
         "observed_information_error":None,
         "true_generating_covariance_not_supplied_to_nuisance_fit":True,
         "uncertainty_aware_coefficient_inference_qualified":False,
         "pointwise_or_simultaneous_coverage_evaluated":False,
         "release_authorized":False}
    try:
        data=observed_native_problem(block,support)
        row["generated"]=True
    except Exception as exc:
        row["source_error"]={"type":type(exc).__name__,"message":str(exc)[:500]}
        return row
    X,y,w,g,t,tr,x,c=data
    try:
        fit=estimate_reml_components(X,y,w,g,t,tr,x,slope=family)
        row["reml_status"]=fit["status"]
        row["near_boundary_components"]=fit["near_boundary_components"]
        row["active_lower_box_components"]=fit["active_lower_box_components"]
        row["components_observed_only"]=fit["variance_components"]
        if fit["status"]!="ok":
            row["reml_error"]={"type":"Nonconverged","message":fit["optimizer_message"]}
            return row
        logtheta=np.log(np.array([fit["variance_components"][k] for k in COMPONENTS]))
    except Exception as exc:
        row["reml_status"]="failed"
        row["reml_error"]={"type":type(exc).__name__,"message":str(exc)[:500]}
        return row
    try:
        original=cr2_local_metric(data,family,logtheta)
        grads=[]
        dfs=[]
        change=[]
        for eps in LOG_STEPS:
            ghalf=np.zeros(len(COMPONENTS))
            gdf=np.zeros(len(COMPONENTS))
            for k in range(len(COMPONENTS)):
                unit=np.zeros(len(COMPONENTS));unit[k]=eps
                plus=cr2_local_metric(data,family,logtheta+unit)
                minus=cr2_local_metric(data,family,logtheta-unit)
                ghalf[k]=(plus["log_halfwidth_90"]-minus["log_halfwidth_90"])/(2*eps)
                gdf[k]=(plus["conditional_df"]-minus["conditional_df"])/(2*eps)
            grads.append(ghalf)
            dfs.append(gdf)
        row["local_metric_status"]="ok"
        row["conditional_cr2_at_reml"]=original
        row["log_ci_halfwidth_derivative_by_component"]={
            key:float(v) for key,v in zip(COMPONENTS,grads[0])}
        row["df_derivative_by_component"]={
            key:float(v) for key,v in zip(COMPONENTS,dfs[0])}
        row["gradient_step_relative_deviation"]=float(
            np.linalg.norm(grads[0]-grads[1])/
            max(1.,np.linalg.norm(grads[1])))
        row["max_abs_df_derivative"]=float(np.max(np.abs(dfs[0])))
        if not np.isfinite(grads).all() or row["gradient_step_relative_deviation"]>.10:
            raise ValueError("unstable numerical CR2 halfwidth derivatives")
    except Exception as exc:
        row["local_metric_status"]="refused"
        row["local_metric_error"]={"type":type(exc).__name__,
                                  "message":str(exc)[:500]}
        return row
    try:
        h,asym=rem_likelihood_curvature(data,family,logtheta,LOG_STEPS[0])
        half,asym2=rem_likelihood_curvature(data,family,logtheta,LOG_STEPS[1])
        symmetry_change=float(np.linalg.norm(h-half,ord="fro")/
                              max(1.,np.linalg.norm(half,ord="fro")))
        eig=np.linalg.eigvalsh(h)
        row["hessian_min_eigenvalue"]=float(eig[0])
        row["hessian_condition_abs"]=float(
            np.max(np.abs(eig))/max(np.min(np.abs(eig)),1e-30))
        row["hessian_gradient_asymmetry"]=float(max(asym,asym2))
        row["hessian_step_relative_change"]=symmetry_change
        row["regular_interior_fit"]=bool(
            not any(row["active_lower_box_components"].values()) and
            not any(row["near_boundary_components"].values()))
        if not row["regular_interior_fit"]:
            raise ValueError("boundary variance component: regular Hessian inverse disallowed")
        if eig[0]<=0:
            raise ValueError("observed REML log-variance information not positive definite")
        if row["hessian_condition_abs"]>MAX_OBSERVED_INFORMATION_CONDITION:
            raise ValueError("observed REML log-variance information severely conditioned")
        if max(asym,asym2)>.05 or symmetry_change>.1:
            raise ValueError("unstable observed-information finite difference")
        ghalf=np.asarray(grads[0])
        nuisance_var=float(ghalf@np.linalg.solve(h,ghalf))
        if not np.isfinite(nuisance_var) or nuisance_var<0:
            raise ValueError("invalid nuisance variance delta diagnostic")
        row["local_log_ci_halfwidth_nuisance_delta_sd"]=float(np.sqrt(nuisance_var))
        row["observed_information_status"]="usable_for_local_diagnostic"
    except Exception as exc:
        row["observed_information_status"]="refused"
        row["observed_information_error"]={
            "type":type(exc).__name__,"message":str(exc)[:500]}
        row["local_log_ci_halfwidth_nuisance_delta_sd"]=None
    return row


def summarize(rows):
    expected={(b,s,f) for b in range(BLOCKS) for s in SUPPORT for f in FAMILIES}
    ids=[(r["block"],r["source_support"],r["working_family"]) for r in rows]
    if len(ids)!=len(set(ids)) or not set(ids).issubset(expected):
        raise ValueError("duplicate or undeclared original nuisance information source")
    cells={}
    for sup in SUPPORT:
        for fam in FAMILIES:
            group=[r for r in rows if r["source_support"]==sup and r["working_family"]==fam]
            ok=[r for r in group if r["local_metric_status"]=="ok"]
            good=[r for r in ok if r["observed_information_status"]=="usable_for_local_diagnostic"]
            cells[f"{sup}/{fam}"]={
                "generating_blocks_recorded":len(group),
                "matched_model":fam==r33.source_working_family(sup),
                "local_cr2_derivative_success":len(ok),
                "local_cr2_derivative_refusals":sum(r["local_metric_status"]=="refused" for r in group),
                "observed_information_local_diagnostic_accepted":len(good),
                "observed_information_refusals":sum(r["observed_information_status"]=="refused" for r in group),
                "median_max_abs_df_derivative":(
                    float(np.median([r["max_abs_df_derivative"] for r in ok])) if ok else None),
                "median_local_log_halfwidth_nuisance_delta_sd":(
                    float(np.median([r["local_log_ci_halfwidth_nuisance_delta_sd"]
                         for r in good])) if good else None),
            }
    return {"study":STUDY,"new_independent_generating_blocks":BLOCKS,
      "original_seed":MASTER_SEED,"n_participants":PARTICIPANTS,
      "source_conditions":SUPPORT,"working_families":FAMILIES,
      "planned_original_source_model_cases":PLANNED,
      "recorded_cases":len(rows),"missing_cases":len(expected-set(ids)),
      "source_failures":sum(not r["generated"] for r in rows),
      "nuisance_estimator_failures":sum(r["generated"] and r["reml_status"]!="ok" for r in rows),
      "cr2_derivative_refusals":sum(r["local_metric_status"]=="refused" for r in rows),
      "observed_nuisance_information_refusals":sum(
          r["observed_information_status"]=="refused" for r in rows),
      "small_diagnostic_not_independent_coverage_replication":True,
      "observed_curvature_delta_sd_not_coefficient_ci_correction":True,
      "conditional_satterthwaite_excludes_fitted_nuisance_uncertainty":True,
      "pointwise_coverage_qualified":False,"simultaneous_bands_qualified":False,
      "release_authorized":False,"cells":cells}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    rows=[evaluate(b,s,f) for b in range(BLOCKS) for s in SUPPORT for f in FAMILIES]
    report=summarize(rows)
    for name,obj in (("cases.json",rows),("summary.json",report)):
        (args.out/name).write_text(json.dumps(obj,sort_keys=True,indent=2)+"\n")
    (args.out/"source-commit.txt").write_text(
        os.environ.get("GITHUB_SHA","unverified-local")+"\n")
    names=("cases.json","summary.json","source-commit.txt")
    (args.out/"SHA256SUMS").write_text("".join(
        hashlib.sha256((args.out/n).read_bytes()).hexdigest()+"  "+n+"\n"
        for n in names))
    print("R34 NUISANCE INFORMATION AUDIT:",json.dumps(
        {k:v for k,v in report.items() if k!="cells"},sort_keys=True))
    for name,v in report["cells"].items():
        print("R34 NUISANCE CELL:",json.dumps({"cell":name,**v},sort_keys=True))
    if report["missing_cases"] or report["source_failures"]:
        raise SystemExit("R34 source generation incomplete; preserve original failed cases")


if __name__=="__main__":
    main()
