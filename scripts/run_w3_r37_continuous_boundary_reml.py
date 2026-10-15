"""R37: continuously optimized nonnegative random-slope Gaussian REML reference.

New independently generated Gaussian trajectories under exact-zero and
positive participant random slope variance, ordinary/extreme leverage. A
four-variable smooth positive-nuisance / EXACT-ZERO-ALLOWED slope optimization
uses analytic restricted-Gaussian gradients, multiple predeclared starts,
and crosschecks both R25 positive-variance score and R35 fixed-grid profile.
No chi-square reference, LRT p-value, coefficient CI or release qualification.
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
from scripts import run_w3_r16_leverage_covariance_factorial as r16
from scripts import run_w3_r17_fresh_feasibility as fresh
from scripts import run_w3_r29_predictor_spread_recovery as counterfactual
from scripts import run_w3_r35_slope_boundary_profiles as prior
from scripts.w3_r20_estimated_working_target import COMPONENTS,observed_weighted_rows
from scripts.w3_r25_gaussian_reml_components import (
    LOWER_LOG_RATIO,UPPER_LOG_RATIO,estimate_reml_components,
    prepare_reml_design,restricted_loglik_and_gradient)

STUDY="W3_R37_NEW_SOURCE_CONTINUOUS_NONNEGATIVE_SLOPE_REML"
MASTER_SEED=202610163737
BLOCKS=4
PARTICIPANTS=24
SUPPORT=("ordinary_dependent","extreme_dependent")
STATES=("zero_slope","positive_slope")
RATIO_STARTS=(0.,.01,1.,10.)
MAX_RATIO=100.
PLANNED=BLOCKS*len(SUPPORT)*len(STATES)
GRID=prior.SLOPE_VARIANCE_TO_OBSERVED_SCALE
FREE=prior.FREE_INDICES
SLOPE=prior.SLOPE_INDEX


def source(block,support,state):
    if support not in SUPPORT or state not in STATES:
        raise ValueError("unregistered continuous profile source")
    original=fresh.fresh_source(
        block,support,n=PARTICIPANTS,master_seed=MASTER_SEED,
        n_blocks=BLOCKS,max_n=PARTICIPANTS)
    if state=="positive_slope":
        return original
    raw=dict(original[0])
    raw["participant_slope"]=np.zeros_like(raw["participant_slope"])
    return counterfactual.rescaled_source((raw,*original[1:]),1.)


def continuous_reml_objective(parameters,prepared,reference):
    """Analytic -restricted-LL score at exactly zero or positive slope variance.

    First three parameters are log positive variance ratios (intercept/trial/
    sensor); fourth is a LINEAR NONNEGATIVE slope variance ratio. A derivative
    with respect to the fourth is meaningful at exactly zero; no log(0) hack.
    """
    v=np.asarray(parameters,float)
    if v.shape!=(4,) or not np.isfinite(v).all() or v[3]<0:
        raise ValueError("three log variances and one finite nonnegative slope ratio required")
    theta=np.zeros(len(COMPONENTS))
    theta[list(FREE)]=reference*np.exp(v[:3])
    theta[SLOPE]=reference*v[3]
    q=prepared[0][0].shape[1]
    G=np.zeros((q,q))
    u=np.zeros(q)
    yvy=0.
    logdet=0.
    parts=[]
    for Zi,yi,Ks in prepared:
        Vi=sum(float(theta[j])*K for j,K in enumerate(Ks))
        factor=cho_factor((Vi+Vi.T)*.5,lower=True,check_finite=False)
        VinvZi=cho_solve(factor,Zi,check_finite=False)
        Vinvy=cho_solve(factor,yi,check_finite=False)
        G+=Zi.T@VinvZi
        u+=Zi.T@Vinvy
        yvy+=float(yi@Vinvy)
        logdet+=float(2*np.log(np.diag(factor[0])).sum())
        parts.append((Zi,yi,Ks,factor,VinvZi))
    sign,gramlog=np.linalg.slogdet(G)
    if sign<=0:
        raise ValueError("Gaussian REML fixed-effect Gram not SPD")
    B=np.linalg.solve(G,np.eye(q))
    beta=B@u
    objective=.5*(logdet+gramlog+max(0.,yvy-float(u@beta)))
    grad=np.zeros(4)
    for Zi,yi,Ks,factor,VinvZi in parts:
        py=cho_solve(factor,yi-Zi@beta,check_finite=False)
        vinv=cho_solve(factor,np.eye(len(yi)),check_finite=False)
        for j,K in enumerate(Ks):
            score=.5*(float(np.sum(vinv*K))-
                      float(np.trace(B@(VinvZi.T@K@VinvZi)))-
                      float(py@K@py))
            if j==SLOPE:
                grad[3]+=score*reference
            else:
                grad[FREE.index(j)]+=score*theta[j]
    if not np.isfinite(objective) or not np.isfinite(grad).all():
        raise ValueError("nonfinite continuous Gaussian boundary objective")
    return float(objective),grad


def run_start(prepared,reference,nuisance_components,slope_ratio):
    start=np.array([
        np.log(np.clip(float(nuisance_components[COMPONENTS[k]])/reference,
               np.exp(LOWER_LOG_RATIO)*1.02,np.exp(UPPER_LOG_RATIO)/1.02))
        for k in FREE]+[float(slope_ratio)])
    out={"initial_slope_ratio":float(slope_ratio),"status":"failed","error":None}
    try:
        fit=minimize(continuous_reml_objective,start,args=(prepared,reference),
            jac=True,method="L-BFGS-B",
            bounds=[(LOWER_LOG_RATIO,UPPER_LOG_RATIO)]*len(FREE)+[(0.,MAX_RATIO)],
            options={"maxiter":200,"ftol":1e-11,"gtol":1e-7,"maxls":35})
        out.update(
            status="ok" if fit.success and np.isfinite(fit.fun) else "nonconverged",
            objective=float(fit.fun),
            iterations=int(fit.nit),
            optimizer_success=bool(fit.success),
            optimizer_message=str(fit.message),
            log_score_max_abs=float(np.max(np.abs(fit.jac))),
            slope_variance_to_reference=float(fit.x[3]),
            exact_zero_slope_solution=bool(fit.x[3]<=1e-12),
            slope_upper_bound_hit=bool(fit.x[3]>=MAX_RATIO-1e-5),
            free_component_estimates={
                COMPONENTS[k]:float(reference*np.exp(fit.x[j]))
                for j,k in enumerate(FREE)})
    except Exception as exc:
        out["error"]={"type":type(exc).__name__,"message":str(exc)[:600]}
    return out


def evaluate(block,support,state):
    row={"study":STUDY,"source_block":block,"support":support,"true_state":state,
         "generating_slope_variance":(
             0. if state=="zero_slope" else float(r16.SIGMA_RANDOM_SLOPE**2)),
         "source_ok":False,"source_error":None,"original_reml_status":"not_attempted",
         "original_reml_error":None,"optimizations":[],"grid_points":[],
         "continuous_reference_status":"not_attempted",
         "no_global_optimality_guarantee":True,
         "no_asymptotic_lrt_reference_qualified":True,
         "no_coefficient_confidence_interval_evaluated":True,
         "release_authorized":False}
    try:
        case=source(block,support,state)
        X,y,w,g,t,tr,x=observed_weighted_rows(
            (None,case[1],case[2],case[3],case[4],None),"legendre5")
        prepared=prepare_reml_design(X,y,w,g,t,tr,x,slope="predictor_scaled_slope")
        row["source_ok"]=True
        row["native_observed_points"]=len(y)
        if support.startswith("extreme"):
            subjects=np.array([x[np.flatnonzero(g==who)[0]] for who in np.unique(g)])
            if subjects[0]!=3. or subjects[1]!=-2.5:
                raise ValueError("extreme support contract failed")
    except Exception as exc:
        row["source_error"]={"type":type(exc).__name__,
                             "message":str(exc)[:600]}
        return row
    try:
        init=estimate_reml_components(
            X,y,w,g,t,tr,x,slope="predictor_scaled_slope")
        row["original_reml_status"]=init["status"]
        row["original_reml_variances"]=init["variance_components"]
        row["original_reml_slope_bound"]=init["active_lower_box_components"][
            "participant_slope"]
        row["reference_variance"]=float(
            init["reference_variance_scale_from_observed_residuals"])
        if init["status"]!="ok":
            row["original_reml_error"]={
                "type":"NonConvergence","message":init["optimizer_message"]}
            return row
    except Exception as exc:
        row["original_reml_status"]="failed"
        row["original_reml_error"]={"type":type(exc).__name__,
                                    "message":str(exc)[:600]}
        return row
    ref=row["reference_variance"]
    for slope_start in RATIO_STARTS:
        row["optimizations"].append(run_start(
            prepared,ref,init["variance_components"],slope_start))
    for fixed_ratio in GRID:
        row["grid_points"].append(prior.profile_one(
            prepared,ref,init["variance_components"],fixed_ratio))
    success=[x for x in row["optimizations"] if x["status"]=="ok"]
    gridok=[x for x in row["grid_points"] if x["status"]=="ok"]
    if len(success)!=len(RATIO_STARTS) or len(gridok)!=len(GRID):
        row["continuous_reference_status"]="incomplete"
        return row
    best=min(success,key=lambda z:z["objective"])
    best_grid=min(gridok,key=lambda z:z["restricted_negative_loglik"])
    improvement=2*(best_grid["restricted_negative_loglik"]-best["objective"])
    row.update(
        continuous_reference_status="computed",
        best_multistart_slope_ratio=best["slope_variance_to_reference"],
        best_multistart_likelihood=float(best["objective"]),
        best_multistart_zero=best["exact_zero_slope_solution"],
        best_multistart_upper_hit=best["slope_upper_bound_hit"],
        best_grid_ratio=float(best_grid["fixed_slope_variance_to_observed_scale"]),
        best_grid_nll=float(best_grid["restricted_negative_loglik"]),
        two_times_grid_to_continuous_nll_gain=float(improvement),
        no_evidence_continuous_worse_than_grid=bool(improvement>=-2e-4),
        max_objective_spread_over_starts=float(
            max(z["objective"] for z in success)-min(z["objective"] for z in success)),
        starts_disagree_substantially=bool(
            max(z["objective"] for z in success)-min(z["objective"] for z in success)>1e-3))
    return row


def summarize(rows):
    expected={(b,s,t) for b in range(BLOCKS) for s in SUPPORT for t in STATES}
    keys=[(q["source_block"],q["support"],q["true_state"]) for q in rows]
    if len(keys)!=len(set(keys)) or not set(keys).issubset(expected):
        raise ValueError("unregistered or duplicate R37 original Gaussian source")
    cells={}
    for support in SUPPORT:
        for state in STATES:
            x=[r for r in rows if r["support"]==support and r["true_state"]==state]
            ok=[r for r in x if r["continuous_reference_status"]=="computed"]
            cells[f"{support}/{state}"]={
                "independent_original_generating_blocks":len(x),
                "complete_multistart_and_grid":len(ok),
                "continuous_boundary_solution_count":sum(
                    r["best_multistart_zero"] for r in ok),
                "finite_grid_zero_minimum_count":sum(
                    r["best_grid_ratio"]==0 for r in ok),
                "best_objective_violates_grid_reference":sum(
                    not r["no_evidence_continuous_worse_than_grid"] for r in ok),
                "multistart_objective_disagreements":sum(
                    r["starts_disagree_substantially"] for r in ok),
                "slope_upper_bound_hit":sum(
                    r["best_multistart_upper_hit"] for r in ok),
                "median_continuous_vs_grid_nll_gain_twice":(
                    float(np.median([r["two_times_grid_to_continuous_nll_gain"]
                                     for r in ok])) if ok else None)}
    return {"study":STUDY,"source_seed":MASTER_SEED,
        "independent_generating_blocks":BLOCKS,"participants":PARTICIPANTS,
        "source_supports":SUPPORT,"generating_slope_states":STATES,
        "planned_source_cases":PLANNED,"recorded_source_cases":len(rows),
        "missing_source_cases":len(expected-set(keys)),
        "source_failures":sum(not q["source_ok"] for q in rows),
        "original_reml_failures":sum(q["source_ok"] and
                                    q["original_reml_status"]!="ok" for q in rows),
        "planned_continuous_optimization_starts":PLANNED*len(RATIO_STARTS),
        "completed_continuous_optimization_starts":sum(
            len(x["optimizations"]) for x in rows),
        "failed_or_nonconverged_continuous_starts":sum(
            t["status"]!="ok" for x in rows for t in x["optimizations"]),
        "planned_fixed_grid_point_fits":PLANNED*len(GRID),
        "completed_fixed_grid_point_fits":sum(len(x["grid_points"]) for x in rows),
        "failed_grid_point_fits":sum(
            p["status"]!="ok" for x in rows for p in x["grid_points"]),
        "boundary_included_as_exact_zero":True,
        "no_global_optimizer_certificate":True,
        "no_chisquare_mixture_or_test_calibration":True,
        "no_coefficient_CI_or_coverage":True,"release_authorized":False,
        "cells":cells}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    rows=[evaluate(b,s,t) for b in range(BLOCKS)
          for s in SUPPORT for t in STATES]
    report=summarize(rows)
    for name,obj in (("cases.json",rows),("summary.json",report)):
        (a.out/name).write_text(json.dumps(obj,sort_keys=True,indent=2)+"\n")
    (a.out/"source-commit.txt").write_text(
        os.getenv("GITHUB_SHA","unverified-local")+"\n")
    names=("cases.json","summary.json","source-commit.txt")
    (a.out/"SHA256SUMS").write_text("".join(
        hashlib.sha256((a.out/n).read_bytes()).hexdigest()+"  "+n+"\n"
        for n in names))
    print("R37 CONTINUOUS ZERO BOUNDARY AUDIT:",json.dumps(
        {k:v for k,v in report.items() if k!="cells"},sort_keys=True))
    for key,x in report["cells"].items():
        print("R37 BOUNDARY CELL:",json.dumps({"cell":key,**x},sort_keys=True))
    if report["source_failures"] or report["missing_source_cases"]:
        raise SystemExit("R37 new Gaussian source incomplete; retain all failures")


if __name__=="__main__":
    main()
