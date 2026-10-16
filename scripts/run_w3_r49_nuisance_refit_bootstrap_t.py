"""R49: prospective Gaussian REML-nuisance refit parametric bootstrap-t pilot.

Research only; 8 NEW independently seeded Gaussian innovation blocks, n24;
ordinary/extreme predictor leverage variants are paired within each block.
One correctly specified positive predictor-dependent Gaussian covariance family.
Fitted four-component physical-positive REML likelihood: two fixed starts,
strict first-order projected KKT <= 0.001, NLL difference <= 0.001 from best
observed candidate. No global optimum proof. Original and each of the 31
parametric synthetic resamples refit REML and recompute original scaled
Cholesky CR2 SE and conditional Satterthwaite moments. Parametric draws use
only observed-data fitted Gaussian covariance, observed native design and
original fitted WLS mean, NEVER generating truth or oracle parameters.
Bootstrap-t critical is 90th percentile of absolute refitted studentized
focal errors; any failed refit causes explicit whole-interval refusal.
An exploratory feasibility pilot, not calibrated nominal pointwise or
simultaneous whole-function 90% inference, and NOT a supported package API.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np
from scipy.optimize import minimize
from scipy.stats import t as student_t

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import run_w3_r17_fresh_feasibility as fresh
from scripts import run_w3_r39_nuisance_coordinate_audit as r39
from scripts import run_w3_r48_independent_fitted_cr2 as r48
from scripts.w3_r20_estimated_working_target import COMPONENTS
from scripts.w3_r25_gaussian_reml_components import (
    prepare_reml_design,restricted_loglik_and_gradient,
)
from scripts.w3_r22_scaled_cholesky_cr2 import stable_cr2_blockwise_wls

STUDY="W3_R49_GAUSSIAN_NUISANCE_REFIT_PARAMETRIC_STUDENTIZED_PILOT"
SOURCE_SEED=202610164949
DRAW_SEED=202610164950
BLOCKS=8
PARTICIPANTS=24
SUPPORT=("ordinary_dependent","extreme_dependent")
SLOPE_FAMILY="predictor_scaled_slope"
N_BOOT=31
NOMINAL=.90
KKT_TOL=.001
NLL_TOL=.001
RECONSTRUCTION_TOL=1e-6
BOUND_LOW=float(r39.LOW)
BOUND_HIGH=float(r39.HIGH)
START_RATIOS=(
    ("interior",(.1,.1,.1,1.)),
    ("spread",(.6,.3,.3,1.)),
)
TARGETS=(
    "known_oracle_conditional_Satterthwaite",
    "fitted_REML_conditional_Satterthwaite",
    "fitted_REML_parametric_refit_bootstrap_t",
)
N_SOURCES=BLOCKS*len(SUPPORT)
N_INTERVALS=N_SOURCES*len(TARGETS)
N_BOOT_ATTEMPTS=N_SOURCES*N_BOOT
N_NUMERICAL_STARTS=(N_SOURCES+N_BOOT_ATTEMPTS)*len(START_RATIOS)


def source(block,support):
    if (type(block) is not int or block not in range(BLOCKS)
            or support not in SUPPORT):
        raise ValueError("R49 source outside predeclared Gaussian design")
    return fresh.fresh_source(
        block,support,n=PARTICIPANTS,master_seed=SOURCE_SEED,
        n_blocks=BLOCKS,max_n=PARTICIPANTS,
    )


def original_problem(block,support):
    src=source(block,support)
    X,y,w,g,t,tr,x,c,truth,raw_truth=r48.native_data(src)
    oracle=r48.r32.known_gaussian_blocks(g,t,tr,x,w,SLOPE_FAMILY)
    return {
        "X":X,"y":y,"w":w,"group":g,"time":t,"trial":tr,"x":x,
        "contrast":c,"projected_truth":truth,
        "raw_generating_truth":raw_truth,
        "oracle_covariance":oracle,
    }


def _objective(ratios,prepared,reference):
    v=np.asarray(ratios,float)
    if v.shape!=(len(COMPONENTS),) or not np.isfinite(v).all():
        raise ValueError("four finite physical variance ratios required")
    if np.any(v<BOUND_LOW*(1.-1e-7)) or np.any(v>BOUND_HIGH*(1.+1e-7)):
        raise ValueError("variance ratio outside frozen positive box")
    f,glog=restricted_loglik_and_gradient(
        np.log(v),prepared,reference)
    return float(f),np.asarray(glog,float)/v


def _physical_kkt(gradient,ratios):
    # Shared R38/R39 projected-gradient convention, generalized to four
    # freely estimated physical positive variance ratios.
    return r39.r38.projected_gradient(
        np.asarray(gradient,float),np.asarray(ratios,float),
        [(BOUND_LOW,BOUND_HIGH)]*len(COMPONENTS),edge_tol=1e-9,
    )


def fit_nuisance(data):
    """Two prespecified physical-variance starts, all outcomes retained.

    The 4D numerical gate is a NEW pilot contract. It does not establish
    a global optimum or the distributional validity of the bootstrap-t.
    """
    X,y,w,g,t,tr,x=(data[z] for z in (
        "X","y","w","group","time","trial","x"))
    stages=[]
    chosen=None
    try:
        prep=prepare_reml_design(
            X,y,w,g,t,tr,x,slope=SLOPE_FAMILY)
        Z=X*np.sqrt(w)[:,None]
        coef=np.linalg.lstsq(Z,y*np.sqrt(w),rcond=None)[0]
        reference=max(float(np.mean((y-X@coef)**2)),1e-8)
    except Exception as exc:
        return {
            "status":"refused","reason":"source_preparation",
            "exception":repr(exc)[:450],
            "numerical_starts":[
                {"label":label,"status":"not_attempted",
                 "error":"preparation_failed"} for label,_ in START_RATIOS],
            "components":None,"working_blocks":None,
        }
    for label,start in START_RATIOS:
        stage={
            "label":label,"status":"failed",
            "optimizer_success":False,"negative_loglik":None,
            "physical_projected_KKT":None,
            "ratios":None,"error":None,
        }
        try:
            solution=minimize(
                _objective,x0=np.array(start,float),
                args=(prep,reference),
                method="L-BFGS-B",jac=True,
                bounds=[(BOUND_LOW,BOUND_HIGH)]*len(COMPONENTS),
                options={"maxiter":450,"ftol":0.,"gtol":1e-10,
                         "maxls":80,"maxfun":2400},
            )
            stage["optimizer_success"]=bool(solution.success)
            stage["iterations"]=int(solution.nit)
            stage["message"]=str(solution.message)
            stage["ratios"]=[float(z) for z in solution.x]
            if np.isfinite(solution.x).all() and np.isfinite(solution.fun):
                f,gradient=_objective(solution.x,prep,reference)
                kkt=float(np.max(abs(_physical_kkt(gradient,solution.x))))
                stage.update(
                    negative_loglik=float(f),
                    physical_projected_KKT=kkt,
                    objective_reconstruction_error=float(
                        abs(f-solution.fun)),
                    status=("ok" if solution.success and
                        abs(f-solution.fun)<=RECONSTRUCTION_TOL
                        else "nonconverged"),
                )
        except Exception as exc:
            stage["error"]=repr(exc)[:450]
        stages.append(stage)
    evaluated=[z for z in stages if z["negative_loglik"] is not None
               and np.isfinite(z["negative_loglik"])]
    if evaluated:
        best_nll=min(z["negative_loglik"] for z in evaluated)
        good=[z for z in evaluated if z["status"]=="ok" and
              z["physical_projected_KKT"] is not None and
              z["physical_projected_KKT"]<=KKT_TOL and
              z["negative_loglik"]-best_nll<=NLL_TOL]
        if good:
            chosen=min(good,key=lambda z:z["negative_loglik"])
    else:
        best_nll=None
    if chosen is None:
        return {
            "status":"refused","reason":"physical_KKT_or_NLL_or_solver",
            "reference_variance":reference,
            "best_observed_NLL":best_nll,
            "numerical_starts":stages,
            "components":None,"working_blocks":None,
        }
    ratios=np.asarray(chosen["ratios"],float)
    theta=reference*ratios
    blocks=[]
    try:
        for _,_,kernels in prep:
            V=sum(float(theta[j])*kernels[j]
                  for j in range(len(COMPONENTS)))
            V=(V+V.T)/2
            np.linalg.cholesky(V)
            blocks.append(V)
    except Exception as exc:
        return {
            "status":"refused","reason":"fitted_covariance_not_SPD",
            "error":repr(exc)[:400],
            "numerical_starts":stages,
            "components":None,"working_blocks":None,
        }
    return {
        "status":"accepted","reason":None,
        "reference_variance":reference,
        "best_observed_NLL":float(best_nll),
        "selected_NLL":chosen["negative_loglik"],
        "selected_start":chosen["label"],
        "physical_projected_KKT":chosen["physical_projected_KKT"],
        "numerical_starts":stages,
        "components":{k:float(theta[j]) for j,k in enumerate(COMPONENTS)},
        "working_blocks":blocks,
        "nuisance_estimated_from_observed_outcome":True,
        "global_optimum_proven":False,
    }


def parametric_draw(data,working_blocks,block,support,rep):
    """Conditional Gaussian draw from fitted observed-only covariance.

    Given source observed WLS mean X beta, draw sqrt(w)*(y*-X beta)
    independently per participant from N(0, fitted working block).
    This is the Gaussian parametric assumption; no original oracle inputs.
    """
    groups=np.unique(data["group"])
    if len(groups)!=len(working_blocks):
        raise ValueError("fitted covariance block length mismatch")
    X,y,w=data["X"],data["y"],data["w"]
    Z=X*np.sqrt(w)[:,None]
    b=np.linalg.lstsq(Z,y*np.sqrt(w),rcond=None)[0]
    simulated=(X@b).copy()
    seed=(DRAW_SEED+100003*block+711*SUPPORT.index(support)+rep)
    rng=np.random.default_rng(seed)
    for group,V in zip(groups,working_blocks):
        idx=np.flatnonzero(data["group"]==group)
        L=np.linalg.cholesky(V)
        eps=L@rng.normal(size=len(idx))
        simulated[idx]+=eps/np.sqrt(w[idx])
    if not np.isfinite(simulated).all():
        raise ValueError("nonfinite Gaussian pseudoresponses")
    return simulated,seed


def cr2_on(data,blocks):
    return stable_cr2_blockwise_wls(
        data["X"],data["y"],data["w"],data["group"],
        data["contrast"],blocks,
    )


def interval_record(label,point,se,critical,truth,method):
    if not all(np.isfinite(z) and z>0 for z in (se,critical)):
        raise ValueError("invalid CR2/parametric bootstrap critical")
    half=float(critical*se)
    return {
        "method":method,"status":"ok","estimate":float(point),
        "lower":float(point-half),"upper":float(point+half),
        "half_width":half,"critical":float(critical),
        "truth_included":bool(abs(point-truth)<=half),
        "refuses_if_incomplete_bootstrap":method==TARGETS[2],
    }


def refused_interval(method,reason):
    return {"method":method,"status":"refused","error":str(reason)[:400],
            "truth_included":False}


def evaluate(block,support):
    row={
        "study":STUDY,"block":block,"support":support,
        "source_status":"failed","source_error":None,
        "one_independent_unit_is_a_primitive_block":True,
        "original_numerical_fit":None,
        "intervals":[],
        "bootstrap_attempts":[],
        "no_coverage_qualification":True,"release_authorized":False,
    }
    data=None
    try:
        data=original_problem(block,support)
        truth=data["projected_truth"]
        row["source_status"]="ok"
        row["projected_generating_focal_truth"]=truth
        row["basis_projection_minus_raw_truth"]=float(
            truth-data["raw_generating_truth"])
        oracle=cr2_on(data,data["oracle_covariance"])
        se=float(oracle["cr2_se"])
        critical=float(student_t.ppf(.95,oracle["satterthwaite_df"]))
        row["intervals"].append(interval_record(
            TARGETS[0],oracle["point"],se,critical,truth,TARGETS[0]))
    except Exception as exc:
        row["source_error"]=repr(exc)[:450]
        row["intervals"].append(
            refused_interval(TARGETS[0],row["source_error"]))
    fit=None
    if data is not None:
        fit=fit_nuisance(data)
        row["original_numerical_fit"]={
            k:v for k,v in fit.items() if k!="working_blocks"}
    else:
        row["original_numerical_fit"]={
            "status":"not_attempted",
            "numerical_starts":[
                {"label":l,"status":"not_attempted"} for l,_ in START_RATIOS],
        }
    cr2=None
    if fit is not None and fit["status"]=="accepted":
        try:
            cr2=cr2_on(data,fit["working_blocks"])
            critical=float(student_t.ppf(
                .95,cr2["satterthwaite_df"]))
            row["intervals"].append(interval_record(
                TARGETS[1],cr2["point"],float(cr2["cr2_se"]),
                critical,truth,TARGETS[1]))
            row["conditional_satterthwaite_df"]=float(
                cr2["satterthwaite_df"])
        except Exception as exc:
            row["intervals"].append(
                refused_interval(TARGETS[1],repr(exc)))
    else:
        row["intervals"].append(refused_interval(
            TARGETS[1],"original physical REML numerical refusal"))
    pivots=[]
    for rep in range(N_BOOT):
        attempt={
            "replicate":rep,"status":"not_attempted",
            "error":None,"seed":None,"studentized_pivot":None,
            "numerical_starts":[
                {"label":l,"status":"not_attempted"} for l,_ in START_RATIOS],
        }
        if fit is not None and fit["status"]=="accepted" and cr2 is not None:
            try:
                simulated,seed=parametric_draw(
                    data,fit["working_blocks"],block,support,rep)
                attempt["seed"]=seed
                other={**data,"y":simulated}
                refit=fit_nuisance(other)
                attempt["numerical_starts"]=refit["numerical_starts"]
                if refit["status"]!="accepted":
                    raise ValueError("bootstrap REML numerical KKT/NLL refusal")
                se_b=cr2_on(other,refit["working_blocks"])
                pivot=float(
                    (se_b["point"]-cr2["point"])/se_b["cr2_se"])
                if not np.isfinite(pivot):
                    raise ValueError("nonfinite refitted studentized pivot")
                pivots.append(pivot)
                attempt.update(status="ok",studentized_pivot=pivot)
            except Exception as exc:
                attempt["status"]="refused"
                attempt["error"]=repr(exc)[:400]
        row["bootstrap_attempts"].append(attempt)
    if cr2 is not None and len(pivots)==N_BOOT:
        critical=float(np.quantile(np.abs(pivots),NOMINAL,
                                   method="linear"))
        try:
            row["intervals"].append(interval_record(
                TARGETS[2],cr2["point"],float(cr2["cr2_se"]),
                critical,truth,TARGETS[2]))
        except Exception as exc:
            row["intervals"].append(
                refused_interval(TARGETS[2],repr(exc)))
    else:
        row["intervals"].append(refused_interval(
            TARGETS[2],
            f"incomplete_frozen_bootstrap:{len(pivots)}/{N_BOOT}"))
    return row


def summarize(rows):
    expected={(b,s) for b in range(BLOCKS) for s in SUPPORT}
    keys=[(r["block"],r["support"]) for r in rows]
    if len(keys)!=len(set(keys)) or not set(keys).issubset(expected):
        raise ValueError("R49 duplicate/unregistered independent block")
    if any(tuple(v["method"] for v in r["intervals"])!=TARGETS or
           len(r["bootstrap_attempts"])!=N_BOOT or
           {v["replicate"] for v in r["bootstrap_attempts"]}!=
           set(range(N_BOOT)) or
           len(r["original_numerical_fit"]["numerical_starts"])!=
           len(START_RATIOS) or
           any(len(v["numerical_starts"])!=len(START_RATIOS)
               for v in r["bootstrap_attempts"])
           for r in rows):
        raise ValueError("R49 prespecified original/bootstrap/refusal slots absent")
    intervals=[v for r in rows for v in r["intervals"]]
    boots=[v for r in rows for v in r["bootstrap_attempts"]]
    all_starts=sum(len(r["original_numerical_fit"]["numerical_starts"])
                   for r in rows)+sum(len(v["numerical_starts"])
                                      for v in boots)
    cells={}
    for support in SUPPORT:
        sample=[r for r in rows if r["support"]==support]
        methods={}
        for method in TARGETS:
            fits=[v for r in sample for v in r["intervals"]
                  if v["method"]==method]
            valid=[v for v in fits if v["status"]=="ok"]
            hits=sum(v["truth_included"] for v in valid)
            methods[method]={
                "independent_blocks_planned":BLOCKS,
                "intervals_recorded":len(fits),
                "accepted":len(valid),
                "refused":len(fits)-len(valid),
                "truth_included":hits,
                "all_block_truth_inclusion":hits/BLOCKS,
                "Wilson95_MC":r48.wilson(int(hits),BLOCKS),
                "mean_half_width_success_only":(
                    float(np.mean([v["half_width"] for v in valid]))
                    if valid else None),
            }
        attempts=[v for r in sample for v in r["bootstrap_attempts"]]
        cells[support]={
            "independent_blocks":BLOCKS,
            "source_records":len(sample),
            "accepted_original_physical_nuisance":sum(
                r["original_numerical_fit"]["status"]=="accepted"
                for r in sample),
            "bootstrap_attempts":len(attempts),
            "bootstrap_successes":sum(v["status"]=="ok" for v in attempts),
            "bootstrap_numerical_refusals":sum(
                v["status"]=="refused" for v in attempts),
            "bootstrap_not_attempted":sum(
                v["status"]=="not_attempted" for v in attempts),
            "methods":methods,
        }
    return {
        "study":STUDY,"new_source_seed":SOURCE_SEED,
        "new_independent_gaussian_primitive_blocks":BLOCKS,
        "n_participants_per_block":PARTICIPANTS,
        "paired_leverage_supports_not_independent":True,
        "bootstrap_draws_use_only_fitted_gaussian_covariance":True,
        "fitted_gaussian_nuisance_refit_per_draw":True,
        "frozen_physical_projected_KKT_tolerance":KKT_TOL,
        "frozen_observed_NLL_tolerance":NLL_TOL,
        "frozen_num_bootstrap_draws":N_BOOT,
        "planned_source_cases":N_SOURCES,
        "recorded_source_cases":len(rows),
        "planned_interval_records":N_INTERVALS,
        "recorded_interval_records":len(intervals),
        "planned_bootstrap_attempts":N_BOOT_ATTEMPTS,
        "recorded_bootstrap_attempts":len(boots),
        "planned_nuisance_solver_start_slots":N_NUMERICAL_STARTS,
        "recorded_nuisance_solver_start_slots":all_starts,
        "complete_failure_inclusive_ledger":(
            len(rows)==N_SOURCES and len(intervals)==N_INTERVALS
            and len(boots)==N_BOOT_ATTEMPTS and
            all_starts==N_NUMERICAL_STARTS),
        "original_source_failures":sum(
            r["source_status"]!="ok" for r in rows),
        "strata":cells,
        "pointwise_90_nominal_NOT_qualified":True,
        "parametric_bootstrap_t_method_is_exploratory":True,
        "simultaneous_90_function_band_NOT_qualified":True,
        "boundary_variance_null_typeI_NOT_qualified":True,
        "MNAR_and_latent_whole_participant_selection_NOT_identified":True,
        "release_authorized":False,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    rows=[evaluate(b,s) for b in range(BLOCKS) for s in SUPPORT]
    summary=summarize(rows)
    for filename,obj in (("cases.json",rows),("summary.json",summary)):
        (args.out/filename).write_text(
            json.dumps(obj,sort_keys=True,indent=2,allow_nan=False)+"\n")
    (args.out/"source-commit.txt").write_text(
        os.environ.get("GITHUB_SHA","unverified-local")+"\n")
    files=("cases.json","summary.json","source-commit.txt")
    (args.out/"SHA256SUMS").write_text("".join(
        hashlib.sha256((args.out/f).read_bytes()).hexdigest()+"  "+f+"\n"
        for f in files))
    print("R49 prospective nuisance-refit parametric bootstrap-t:",
          json.dumps(summary,sort_keys=True))
    if not summary["complete_failure_inclusive_ledger"]:
        raise SystemExit("R49 original required slots missing; refused")


if __name__=="__main__":
    main()
