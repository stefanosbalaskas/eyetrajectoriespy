"""R35: genuine zero-boundary restricted likelihood profiles for slope variance.

NEW four independent generating blocks, n24, dependent Gaussian covariance,
ordinary/extreme predictor spread. For seven FIXED nonnegative random-slope
variance grid values, including exactly zero, re-optimize other three
strictly-positive Gaussian covariance components using an independent blockwise
REML evaluator with analytic free-coordinate scores. The profile shape is an
identifiability diagnostic, NOT a chi-squared test, CI or model winner.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np
from scipy.linalg import cho_factor, cho_solve
from scipy.optimize import minimize

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts import run_w3_r17_fresh_feasibility as fresh
from scripts import run_w3_r16_leverage_covariance_factorial as r16
from scripts.w3_r20_estimated_working_target import COMPONENTS, observed_weighted_rows
from scripts.w3_r25_gaussian_reml_components import (
    LOWER_LOG_RATIO,UPPER_LOG_RATIO, estimate_reml_components,
    prepare_reml_design,restricted_loglik_and_gradient)

STUDY="W3_R35_NEW_SOURCE_EXACT_ZERO_SLOPE_REML_PROFILES"
MASTER_SEED=202610163535
BLOCKS=4
PARTICIPANTS=24
SUPPORT=("ordinary_dependent","extreme_dependent")
WORKING_FAMILY="predictor_scaled_slope"
SLOPE_VARIANCE_TO_OBSERVED_SCALE=(0.,1e-6,1e-4,.01,.1,1.,10.)
SLOPE_INDEX=COMPONENTS.index("participant_slope")
FREE_INDICES=tuple(i for i in range(len(COMPONENTS)) if i!=SLOPE_INDEX)
PLANNED=BLOCKS*len(SUPPORT)
EXPECTED_POINTS=PLANNED*len(SLOPE_VARIANCE_TO_OBSERVED_SCALE)


def prepare_source(block,support):
    if support not in SUPPORT:
        raise ValueError("unregistered Gaussian covariance source")
    original=fresh.fresh_source(
        block,support,n=PARTICIPANTS,master_seed=MASTER_SEED,
        n_blocks=BLOCKS,max_n=PARTICIPANTS)
    X,y,w,g,t,tr,x=observed_weighted_rows(
        (None,original[1],original[2],original[3],original[4],None),
        "legendre5")
    if support.startswith("extreme"):
        per=np.array([x[np.flatnonzero(g==who)[0]] for who in np.unique(g)])
        if not (per[0]==3. and per[1]==-2.5):
            raise ValueError("extreme leverage source predictor corrupted")
    return X,y,w,g,t,tr,x


def fixed_slope_reml_objective(logfree,prepared,reference,slope_ratio):
    """Restricted Gaussian -loglik at exactly fixed slope theta>=0.

    Independently construct each native participant Gaussian covariance and
    remove GLS mean coefficients. Three free component log ratios have exact
    analytic score. In particular slope_ratio=0 means *exact* zero variance,
    never a floor disguised as a boundary solution.
    """
    logfree=np.asarray(logfree,float)
    if logfree.shape!=(len(FREE_INDICES),) or not np.isfinite(logfree).all():
        raise ValueError("three finite free log variances required")
    if not (np.isfinite(slope_ratio) and slope_ratio>=0):
        raise ValueError("fixed slope variance ratio must be nonnegative")
    theta=np.zeros(len(COMPONENTS))
    theta[list(FREE_INDICES)]=reference*np.exp(logfree)
    theta[SLOPE_INDEX]=reference*float(slope_ratio)
    p=prepared[0][0].shape[1]
    G=np.zeros((p,p));g=np.zeros(p)
    logdet=0.;yinv=0.;chunks=[]
    for Zi,yi,Ki in prepared:
        V=sum(float(theta[k])*K for k,K in enumerate(Ki))
        fac=cho_factor((V+V.T)*.5,lower=True,check_finite=False)
        U=cho_solve(fac,Zi,check_finite=False)
        vy=cho_solve(fac,yi,check_finite=False)
        G+=Zi.T@U;g+=Zi.T@vy
        yinv+=float(yi@vy)
        logdet+=float(2*np.log(np.diag(fac[0])).sum())
        chunks.append((Zi,yi,Ki,fac,U))
    sign,ld=np.linalg.slogdet(G)
    if sign<=0: raise ValueError("Gaussian generalized least squares mean Gram not SPD")
    B=np.linalg.solve(G,np.eye(p));beta=B@g
    obj=.5*(logdet+ld+max(0.,yinv-float(g@beta)))
    grad=np.zeros(len(FREE_INDICES))
    for Zi,yi,Ki,fac,U in chunks:
        residual=yi-Zi@beta
        Py=cho_solve(fac,residual,check_finite=False)
        Vinv=cho_solve(fac,np.eye(len(yi)),check_finite=False)
        for j,k in enumerate(FREE_INDICES):
            K=Ki[k]
            tr1=float(np.sum(Vinv*K))
            tr2=float(np.trace(B@(U.T@K@U)))
            quad=float(Py@K@Py)
            grad[j]+=.5*(tr1-tr2-quad)*theta[k]
    return float(obj),grad


def profile_one(prepared,reference,fit_variances,ratio):
    initial=np.array([np.log(
        np.clip(fit_variances[COMPONENTS[i]]/reference,
                np.exp(LOWER_LOG_RATIO)*1.01,np.exp(UPPER_LOG_RATIO)/1.01))
        for i in FREE_INDICES])
    record={"fixed_slope_variance_to_observed_scale":float(ratio),
            "fixed_slope_variance_is_exact_zero":bool(ratio==0),
            "status":"failed","error":None}
    try:
        r=minimize(fixed_slope_reml_objective,initial,
                   args=(prepared,reference,ratio),
                   method="L-BFGS-B",jac=True,
                   bounds=[(LOWER_LOG_RATIO,UPPER_LOG_RATIO)]*len(FREE_INDICES),
                   options={"maxiter":150,"ftol":1e-10,"gtol":1e-6,"maxls":30})
        record.update({
            "status":"ok" if r.success and np.isfinite(r.fun) else "nonconverged",
            "restricted_negative_loglik":float(r.fun),
            "optimizer_success":bool(r.success),"optimizer_message":str(r.message),
            "iterations":int(r.nit),
            "free_component_estimates":{
                COMPONENTS[k]:float(reference*np.exp(r.x[j]))
                for j,k in enumerate(FREE_INDICES)},
            "active_lower_bounds":{
                COMPONENTS[k]:bool(abs(r.x[j]-LOWER_LOG_RATIO)<1e-4)
                for j,k in enumerate(FREE_INDICES)},
        })
    except Exception as exc:
        record["error"]={"type":type(exc).__name__,"message":str(exc)[:600]}
    return record


def evaluate(block,support):
    row={"study":STUDY,"source_block":block,"support":support,
        "participants":PARTICIPANTS,"source_generated":False,
        "source_failure":None,"observed_only_reml_status":"not_attempted",
        "observed_only_reml_failure":None,"points":[],
        "simulator_true_components_passed_to_nuisance":False,
        "exact_zero_slope_included_in_profile":True,
        "standard_chi_square_boundary_cutoffs_authorized":False,
        "pointwise_coverage_evaluated":False,"release_authorized":False}
    try:
        data=prepare_source(block,support)
        X,y,w,g,t,tr,x=data
        prepared=prepare_reml_design(X,y,w,g,t,tr,x,slope=WORKING_FAMILY)
        row["source_generated"]=True
    except Exception as exc:
        row["source_failure"]={"type":type(exc).__name__,
            "message":str(exc)[:600]}
        return row
    try:
        fit=estimate_reml_components(X,y,w,g,t,tr,x,slope=WORKING_FAMILY)
        row["observed_only_reml_status"]=fit["status"]
        row["original_reml_components"]=fit["variance_components"]
        row["original_reml_near_boundary"]=fit["near_boundary_components"]
        row["original_reml_active_box"]=fit["active_lower_box_components"]
        row["observed_reference_scale"]=float(
            fit["reference_variance_scale_from_observed_residuals"])
        row["original_reml_negative_loglik"]=float(
            fit["restricted_negative_loglik"])
        if fit["status"]!="ok":
            row["observed_only_reml_failure"]={
                "type":"Nonconvergence","message":fit["optimizer_message"]}
            return row
    except Exception as exc:
        row["observed_only_reml_status"]="failed"
        row["observed_only_reml_failure"]={
            "type":type(exc).__name__,"message":str(exc)[:600]}
        return row
    for ratio in SLOPE_VARIANCE_TO_OBSERVED_SCALE:
        row["points"].append(profile_one(
            prepared,row["observed_reference_scale"],
            row["original_reml_components"],ratio))
    accepted=[z for z in row["points"] if z["status"]=="ok"]
    if accepted:
        best=min(accepted,key=lambda z:z["restricted_negative_loglik"])
        base=float(best["restricted_negative_loglik"])
        row["best_evaluated_slope_ratio"]=float(
            best["fixed_slope_variance_to_observed_scale"])
        row["best_evaluated_profile_negative_loglik"]=base
        row["grid_minimum_at_exact_zero"]=bool(
            best["fixed_slope_variance_is_exact_zero"])
        for point in row["points"]:
            point["twice_profile_gap_from_best_grid_point"]=(
                float(2*(point["restricted_negative_loglik"]-base))
                if point["status"]=="ok" else None)
        row["zero_profile_beats_unconstrained_box_fit"]=(
            next((z["restricted_negative_loglik"]<
                       row["original_reml_negative_loglik"]-1e-5
                  for z in accepted
                  if z["fixed_slope_variance_is_exact_zero"]),False))
    return row


def summarize(rows):
    expected={(b,s) for b in range(BLOCKS) for s in SUPPORT}
    identities=[(r["source_block"],r["support"]) for r in rows]
    if len(identities)!=len(set(identities)) or not set(identities).issubset(expected):
        raise ValueError("duplicate or unregistered generating block")
    cells={}
    for sup in SUPPORT:
        selected=[x for x in rows if x["support"]==sup]
        complete=[x for x in selected if len(x["points"])==len(
            SLOPE_VARIANCE_TO_OBSERVED_SCALE)]
        cells[sup]={
            "independent_source_blocks":len(selected),
            "completed_seven_point_profiles":len(complete),
            "zero_slope_grid_minimum_count":sum(
                x.get("grid_minimum_at_exact_zero",False) for x in complete),
            "exact_zero_profile_beats_bounded_reml_count":sum(
                x.get("zero_profile_beats_unconstrained_box_fit",False)
                for x in complete),
            "failed_profile_points":sum(
                z["status"]!="ok" for x in selected for z in x["points"]),
            "source_or_nuisance_failures":sum(
                not x["source_generated"] or
                x["observed_only_reml_status"]!="ok" for x in selected)}
    return {"study":STUDY,"seed":MASTER_SEED,
        "independent_generating_blocks":BLOCKS,
        "n_participants":PARTICIPANTS,
        "source_conditions":SUPPORT,
        "predeclared_fixed_variance_ratios":SLOPE_VARIANCE_TO_OBSERVED_SCALE,
        "planned_source_cases":PLANNED,"recorded_source_cases":len(rows),
        "missing_source_cases":len(expected-set(identities)),
        "source_failures":sum(not x["source_generated"] for x in rows),
        "reml_base_fit_failures":sum(
            x["source_generated"] and x["observed_only_reml_status"]!="ok"
            for x in rows),
        "planned_profile_points":EXPECTED_POINTS,
        "recorded_profile_points":sum(len(x["points"]) for x in rows),
        "profile_optimizer_failure_count":sum(
            z["status"]!="ok" for x in rows for z in x["points"]),
        "profiles_include_exact_zero_variance":True,
        "likelihood_grid_minimum_not_global_optimum":True,
        "no_boundary_lrt_chi_square_cutoff_applied":True,
        "no_functional_coefficient_CI_or_coverage":True,
        "release_authorized":False,"cells":cells}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    rows=[evaluate(b,s) for b in range(BLOCKS) for s in SUPPORT]
    report=summarize(rows)
    for filename,obj in (("cases.json",rows),("summary.json",report)):
        (a.out/filename).write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")
    (a.out/"source-commit.txt").write_text(
        os.getenv("GITHUB_SHA","unverified-local")+"\n")
    names=("cases.json","summary.json","source-commit.txt")
    (a.out/"SHA256SUMS").write_text("".join(
        hashlib.sha256((a.out/n).read_bytes()).hexdigest()+"  "+n+"\n"
        for n in names))
    print("R35 EXACT ZERO PROFILE AUDIT:",json.dumps(
        {k:v for k,v in report.items() if k!="cells"},sort_keys=True))
    for key,value in report["cells"].items():
        print("R35 PROFILE CELL:",json.dumps({"cell":key,**value},sort_keys=True))
    if report["missing_source_cases"] or report["source_failures"]:
        raise SystemExit("R35 source incomplete; original failures preserved")


if __name__=="__main__":
    main()
