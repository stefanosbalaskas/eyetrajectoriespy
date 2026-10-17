"""W3 R57 — exact theta_slope=0 nested Gaussian REML likelihood pilot.

Two *genuinely nested* candidate parameter sets:
  H0: theta_participant_slope == 0 EXACTLY, all other components positive.
  H1: theta_participant_slope >= 0, all other components positive.
Use the EXISTING independently crosschecked R35 fixed-slope-zero and R37
continuous nonnegative-slope Gaussian restricted likelihood/analytic scores.
New original independent Gaussian generating blocks are PAIRED within block
across predictor leverage and true-zero/positive source slope, never counted
as 4x independent draws.

Every numerical start is retained. Strict physical-ratio-coordinate
projected-gradient KKT and near-best two/multi-start objective gates apply
BOTH to H0 and H1. A nonnegative nested *deviance*, when numerically
accepted, is DESCRIPTIVE ONLY. There are NO p-values, nominal reference
cutoffs, Type-I/power/pointwise CI claims, or supported API in this study.
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

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts import run_w3_r16_leverage_covariance_factorial as r16
from scripts import run_w3_r17_fresh_feasibility as fresh
from scripts import run_w3_r35_slope_boundary_profiles as r35
from scripts import run_w3_r37_continuous_boundary_reml as r37
from scripts import run_w3_r38_dualseed_profile_geometry as r38
from scripts import run_w3_r48_independent_fitted_cr2 as r48
from scripts import run_w3_r49_nuisance_refit_bootstrap_t as r49
from scripts import run_w3_r53_local_reml_influence as r53
from scripts.w3_r25_gaussian_reml_components import (
    prepare_reml_design,LOWER_LOG_RATIO,UPPER_LOG_RATIO,
)
from scripts.w3_r20_estimated_working_target import COMPONENTS

STUDY="W3_R57_NEW_INDEPENDENT_NESTED_TRUE_ZERO_NONNEGATIVE_REML"
MASTER_SEED=202610175757
BLOCKS=8
PARTICIPANTS=24
SUPPORT=("ordinary_dependent","extreme_dependent")
STATES=("true_zero","true_positive")
SHARDS=((0,2),(2,4),(4,6),(6,8))
KKT_TOL=.001
NLL_TOL=.001
RECONSTRUCTION_TOL=1e-6
NESTED_MONOTONIC_TOL=1e-5
BOUND_LOW=r49.BOUND_LOW
BOUND_HIGH=r49.BOUND_HIGH
SLOPE_UPPER=r37.MAX_RATIO
FREE_INDICES=r35.FREE_INDICES
SLOPE_INDEX=r35.SLOPE_INDEX
NULL_STARTS=(
    ("null_compact",(.1,.1,1.)),
    ("null_spread",(.6,.3,1.)),
)
ALT_STARTS=(
    ("alt_at_exact_zero",(.1,.1,1.,0.)),
    ("alt_tiny_positive",(.6,.3,1.,.01)),
    ("alt_positive",(.1,.1,1.,1.)),
    ("alt_wide",(.6,.3,1.,10.)),
)
N_SOURCE_CASES=BLOCKS*len(SUPPORT)*len(STATES)
N_MODEL_FITS=N_SOURCE_CASES*2
N_SOLVER_STARTS=N_SOURCE_CASES*(len(NULL_STARTS)+len(ALT_STARTS))


def independent_source(block,support):
    if (type(block) is not int or block not in range(BLOCKS)
            or support not in SUPPORT):
        raise ValueError("R57 source outside independent generating design")
    return fresh.fresh_source(
        block,support,n=PARTICIPANTS,master_seed=MASTER_SEED,
        n_blocks=BLOCKS,max_n=PARTICIPANTS,
    )


def pair_data(block,support):
    src=independent_source(block,support)
    X,y,w,g,t,tr,x,c,truth,raw_truth=r48.native_data(src)
    ui=np.asarray(src[0]["participant_slope"],float)[
        np.asarray(g,int),0,0,0]
    contribution=r16.SIGMA_RANDOM_SLOPE*ui*x*(1.+.25*t)
    if not np.isfinite(contribution).all() or contribution.shape!=y.shape:
        raise ValueError("R57 source slope innovation misaligned")
    common={"X":X,"w":w,"group":g,"time":t,"trial":tr,"x":x,
            "contrast":c,"truth":float(truth)}
    state={
        "true_zero":{**common,"y":np.asarray(y,float)-contribution},
        "true_positive":{**common,"y":np.asarray(y,float).copy()},
    }
    np.testing.assert_allclose(
        state["true_positive"]["y"]-state["true_zero"]["y"],
        contribution,rtol=2e-13,atol=2e-13,
    )
    info={
        "source_slope_component_L2":float(np.linalg.norm(contribution)),
        "source_slope_component_mean_absolute":float(np.mean(abs(contribution))),
        "native_rows":len(y),"native_trials":len(src[1].time),
        "same_native_design_mean_and_non_slope_innovations":True,
    }
    return state,info


def _reference(data):
    X,y,w=(np.asarray(data[k],float) for k in ("X","y","w"))
    Z=X*np.sqrt(w)[:,None]
    b=np.linalg.lstsq(Z,y*np.sqrt(w),rcond=None)[0]
    return max(float(np.mean((y-X@b)**2)),1e-8)


def _parameters(start,model):
    q=np.asarray(start,float)
    if model=="exact_zero":
        if q.shape!=(3,) or np.any(q<=0):
            raise ValueError("R57 null free start requires three positive ratios")
        return np.log(q)
    if model=="nonnegative":
        if q.shape!=(4,) or np.any(q[:3]<=0) or q[3]<0:
            raise ValueError("R57 alternative start outside nested cone")
        return np.r_[np.log(q[:3]),q[3]]
    raise ValueError("R57 unknown nested Gaussian likelihood model")


def objective(parameters,prepared,reference,model):
    """Return (NLL, gradient in optimizer parameters).

    H0 is R35 exact fixed-zero. H1 is R37 nonnegative *linear* slope
    ratio including exactly zero; both use identical observed kernels and
    likelihood normalization.
    """
    v=np.asarray(parameters,float)
    if model=="exact_zero":
        if v.shape!=(3,):
            raise ValueError("R57 null parameter dimension")
        return r35.fixed_slope_reml_objective(v,prepared,reference,0.)
    if model=="nonnegative":
        if v.shape!=(4,) or v[3]<0:
            raise ValueError("R57 nonnegative alternative requires theta>=0")
        return r37.continuous_reml_objective(v,prepared,reference)
    raise ValueError("R57 unknown nested model")


def physical_projected_kkt(parameters,gradient,model):
    """KKT in original PHYSICAL variance-ratio coordinates, including zero."""
    pars=np.asarray(parameters,float)
    grad=np.asarray(gradient,float)
    if model=="exact_zero":
        ratios=np.exp(pars)
        physical=grad/ratios
        bounds=[(BOUND_LOW,BOUND_HIGH)]*3
    elif model=="nonnegative":
        ratios=np.r_[np.exp(pars[:3]),pars[3]]
        physical=np.r_[grad[:3]/ratios[:3],grad[3]]
        bounds=[(BOUND_LOW,BOUND_HIGH)]*3+[(0.,SLOPE_UPPER)]
    else:
        raise ValueError("R57 unknown KKT model")
    if not np.isfinite(physical).all():
        raise ValueError("R57 nonfinite physical Gaussian score")
    projected=r38.projected_gradient(
        physical,ratios,bounds,edge_tol=1e-9)
    return float(np.max(np.abs(projected))),ratios,physical


def numerical_start(label,start,model,prepared,reference):
    stage={
        "label":label,"status":"failed","optimizer_success":False,
        "negative_loglik":None,"reconstructed_loglik":None,
        "objective_reconstruction_error":None,
        "physical_projected_KKT":None,
        "ratios":None,"physical_score":None,
        "optimizer_iterations":None,"optimizer_message":None,
        "error":None,
    }
    try:
        if model=="exact_zero":
            bounds=[(LOWER_LOG_RATIO,UPPER_LOG_RATIO)]*3
        elif model=="nonnegative":
            bounds=[(LOWER_LOG_RATIO,UPPER_LOG_RATIO)]*3+[(0.,SLOPE_UPPER)]
        else:
            raise ValueError("unknown R57 candidate model")
        x0=_parameters(start,model)
        result=minimize(
            objective,x0,args=(prepared,reference,model),
            jac=True,method="L-BFGS-B",bounds=bounds,
            options={"maxiter":450,"ftol":0.,"gtol":1e-10,
                     "maxls":80,"maxfun":2400},
        )
        stage["optimizer_success"]=bool(result.success)
        stage["optimizer_iterations"]=int(result.nit)
        stage["optimizer_message"]=str(result.message)
        if np.isfinite(result.x).all() and np.isfinite(result.fun):
            value,gradient=objective(result.x,prepared,reference,model)
            kkt,ratios,phys=physical_projected_kkt(result.x,gradient,model)
            diff=float(abs(value-result.fun))
            stage.update(
                status=("ok" if result.success and
                        diff<=RECONSTRUCTION_TOL else "nonconverged"),
                negative_loglik=float(result.fun),
                reconstructed_loglik=float(value),
                objective_reconstruction_error=diff,
                physical_projected_KKT=kkt,
                ratios=ratios.tolist(),
                physical_score=phys.tolist(),
            )
    except Exception as exc:
        stage["error"]=repr(exc)[:420]
    return stage


def fit_model(prepared,reference,model):
    starts=NULL_STARTS if model=="exact_zero" else ALT_STARTS
    stages=[numerical_start(k,x,model,prepared,reference)
            for k,x in starts]
    evaluated=[z for z in stages if z["negative_loglik"] is not None
               and np.isfinite(z["negative_loglik"])]
    best=min((z["negative_loglik"] for z in evaluated),default=None)
    qualified=[z for z in evaluated if
               z["status"]=="ok" and
               z["physical_projected_KKT"]<=KKT_TOL and
               z["negative_loglik"]-best<=NLL_TOL]
    chosen=min(qualified,key=lambda q:q["negative_loglik"]) if qualified else None
    out={
        "model":model,"status":"accepted" if chosen else "refused",
        "reason":None if chosen else "numerical_KKT_NLL_or_optimizer_refusal",
        "original_starts":stages,
        "best_observed_multistart_NLL":best,
        "selected_NLL":chosen["negative_loglik"] if chosen else None,
        "selected_start":chosen["label"] if chosen else None,
        "selected_physical_KKT":chosen["physical_projected_KKT"] if chosen else None,
        "selected_free_component_variance_ratios":chosen["ratios"][:3] if chosen else None,
        "selected_slope_ratio":(
            0. if model=="exact_zero" else chosen["ratios"][3]) if chosen else None,
        "null_includes_exact_zero_variance":model=="exact_zero",
        "alternative_includes_structural_zero":model=="nonnegative",
        "global_optimum_proven":False,
    }
    return out


def empty_case(block,support,state):
    return {
        "study":STUDY,"block":block,"support":support,
        "generating_state":state,
        "new_independent_source_primitive_block":True,
        "paired_across_support_and_true_slope_states":True,
        "source_status":"failed","source_error":None,
        "source_info":None,
        "generating_slope_variance":(
            0. if state=="true_zero" else r16.SIGMA_RANDOM_SLOPE**2),
        "null_fit":None,"alternative_fit":None,
        "nested_comparison":{
            "status":"not_attempted","reason":None,
            "raw_twice_null_minus_alternative_NLL":None,
            "nonnegative_twice_profile_NLL_gap":None,
            "alternative_estimated_slope_at_structural_zero":None,
            "reference_probability_not_specified":True,
            "p_value":None,"hypothesis_rejection":None,
        },
        "not_a_calibrated_boundary_test":True,
        "pointwise_and_simultaneous_90pct_CI_qualified":False,
        "release_authorized":False,
    }


def _not_attempted_model(model):
    st=NULL_STARTS if model=="exact_zero" else ALT_STARTS
    return {
        "model":model,"status":"not_attempted",
        "reason":"source_unavailable",
        "original_starts":[{"label":k,"status":"not_attempted"}
                           for k,_ in st],
        "selected_NLL":None,"selected_slope_ratio":None,
    }


def evaluate_pair(block,support):
    output=[empty_case(block,support,s) for s in STATES]
    try:
        cases,info=pair_data(block,support)
    except Exception as exc:
        for row in output:
            row["source_error"]=repr(exc)[:430]
            row["null_fit"]=_not_attempted_model("exact_zero")
            row["alternative_fit"]=_not_attempted_model("nonnegative")
        return output
    for row in output:
        data=cases[row["generating_state"]]
        row["source_status"]="ok"
        row["source_info"]=info
        try:
            X,y,w,g,t,tr,x=(data[k] for k in
                            ("X","y","w","group","time","trial","x"))
            prepared=prepare_reml_design(
                X,y,w,g,t,tr,x,slope="predictor_scaled_slope")
            ref=_reference(data)
            row["observed_only_reference_scale"]=ref
            row["null_fit"]=fit_model(prepared,ref,"exact_zero")
            row["alternative_fit"]=fit_model(prepared,ref,"nonnegative")
        except Exception as exc:
            row["null_fit"]=_not_attempted_model("exact_zero")
            row["alternative_fit"]=_not_attempted_model("nonnegative")
            row["nested_comparison"]["reason"]="source_or_optimization_exception:"+repr(exc)[:380]
        a=row["null_fit"];b=row["alternative_fit"]
        if a["status"]=="accepted" and b["status"]=="accepted":
            raw=float(2*(a["selected_NLL"]-b["selected_NLL"]))
            row["nested_comparison"]["raw_twice_null_minus_alternative_NLL"]=raw
            if raw< -NESTED_MONOTONIC_TOL:
                row["nested_comparison"].update(
                    status="refused",
                    reason="nested_monotonicity_violated_by_observed_optimizers",
                )
            elif not np.isfinite(raw):
                row["nested_comparison"].update(
                    status="refused",reason="nonfinite_nested_deviance")
            else:
                row["nested_comparison"].update(
                    status="ok",reason=None,
                    nonnegative_twice_profile_NLL_gap=float(max(0.,raw)),
                    alternative_estimated_slope_at_structural_zero=bool(
                        b["selected_slope_ratio"]<=1e-10),
                )
        elif row["nested_comparison"]["reason"] is None:
            row["nested_comparison"]["reason"]="null_or_alternative_fit_refused"
    return output


def summarize(cases):
    possible={(b,s,state) for b in range(BLOCKS) for s in SUPPORT for state in STATES}
    keys=[(z["block"],z["support"],z["generating_state"]) for z in cases]
    if len(keys)!=len(set(keys)) or not set(keys).issubset(possible):
        raise ValueError("R57 duplicate/unregistered independent Gaussian source")
    if any(len(r["null_fit"]["original_starts"])!=len(NULL_STARTS)
           or len(r["alternative_fit"]["original_starts"])!=len(ALT_STARTS)
           for r in cases):
        raise ValueError("R57 original nested Gaussian optimizer starts missing")
    cells={}
    for s in SUPPORT:
        for state in STATES:
            rows=[c for c in cases if c["support"]==s
                  and c["generating_state"]==state]
            good=[c for c in rows if c["nested_comparison"]["status"]=="ok"]
            gaps=[c["nested_comparison"]["nonnegative_twice_profile_NLL_gap"]
                  for c in good]
            cells[s+"/"+state]={
                "planned_independent_primitive_blocks":BLOCKS,
                "recorded_source_variants":len(rows),
                "source_failures":sum(c["source_status"]!="ok" for c in rows),
                "null_two_start_accepted":sum(
                    c["null_fit"]["status"]=="accepted" for c in rows),
                "nonnegative_four_start_accepted":sum(
                    c["alternative_fit"]["status"]=="accepted" for c in rows),
                "strictly_numerically_accepted_nested_gaps":len(good),
                "nested_deviance_numerical_refusals":len(rows)-len(good),
                "alternative_selected_exact_zero_variance":sum(
                    c["nested_comparison"]["alternative_estimated_slope_at_structural_zero"]
                    is True for c in good),
                "median_exploratory_nonnegative_deviance":(
                    float(np.median(gaps)) if gaps else None),
                "no_null_typeI_or_power_claim":True,
            }
    return {
        "study":STUDY,
        "master_new_independent_source_seed":MASTER_SEED,
        "new_independent_Gaussian_primitive_blocks":BLOCKS,
        "n_participants":PARTICIPANTS,
        "paired_support_and_slope_states_not_independent_source":True,
        "genuine_nested_H0_theta_slope_equals_zero":True,
        "genuine_nested_H1_theta_slope_nonnegative_including_zero":True,
        "planned_source_state_cases":N_SOURCE_CASES,
        "recorded_source_state_cases":len(cases),
        "planned_nested_Gaussian_likelihood_fits":N_MODEL_FITS,
        "recorded_nested_Gaussian_likelihood_fit_slots":2*len(cases),
        "planned_numerical_optimizer_start_slots":N_SOLVER_STARTS,
        "recorded_numerical_optimizer_start_slots":sum(
            len(r["null_fit"]["original_starts"]) +
            len(r["alternative_fit"]["original_starts"]) for r in cases),
        "complete_failure_inclusive_source_and_start_ledger":(
            len(cases)==N_SOURCE_CASES and
            sum(len(r["null_fit"]["original_starts"])+
                len(r["alternative_fit"]["original_starts"]) for r in cases)
                ==N_SOLVER_STARTS),
        "boundary_null_reference_distribution_qualified":False,
        "no_asymptotic_chibar_chisquare_or_p_values":True,
        "no_TypeI_or_power_calibration":True,
        "no_pointwise_or_simultaneous_90pct_CR2_CI_qualification":True,
        "no_MNAR_or_excluded_whole_participant_identification":True,
        "release_authorized":False,
        "strata":cells,
    }


def _write(path,obj):
    path.write_text(json.dumps(
        r53._json_plain(obj),sort_keys=True,indent=2,allow_nan=False)+"\n")


def shard(out,start,stop):
    if (start,stop) not in SHARDS:
        raise ValueError("R57 source shard unregistered")
    out.mkdir(parents=True,exist_ok=True)
    rows=[c for b in range(start,stop) for s in SUPPORT
          for c in evaluate_pair(b,s)]
    _write(out/"cases.json",rows)
    _write(out/"manifest.json",{
        "study":STUDY,"start":start,"stop":stop,
        "new_source_seed":MASTER_SEED,
        "original_checkout":os.environ.get("GITHUB_SHA","unverified-local"),
        "records":len(rows),
        "SHA256_cases":hashlib.sha256((out/"cases.json").read_bytes()).hexdigest(),
    })


def aggregate(out,parts):
    files=list(parts.glob("*/manifest.json"))
    if len(files)!=len(SHARDS):
        raise ValueError("R57 original independent source shard absent")
    sha=os.environ.get("GITHUB_SHA","unverified-local")
    found=set();rows=[]
    for path in files:
        j=json.loads(path.read_text());key=(j["start"],j["stop"])
        if (key not in SHARDS or key in found or j["study"]!=STUDY or
            j["new_source_seed"]!=MASTER_SEED or j["original_checkout"]!=sha):
            raise ValueError("R57 original source shard/check-out mismatch")
        found.add(key)
        raw=(path.parent/"cases.json").read_bytes()
        if hashlib.sha256(raw).hexdigest()!=j["SHA256_cases"]:
            raise ValueError("R57 original shard case SHA256 mismatch")
        batch=json.loads(raw)
        expected={(b,s,state) for b in range(*key)
                  for s in SUPPORT for state in STATES}
        if (len(batch)!=j["records"] or
            {(v["block"],v["support"],v["generating_state"])
             for v in batch}!=expected):
            raise ValueError("R57 shard Gaussian source identities invalid")
        rows.extend(batch)
    if found!=set(SHARDS):
        raise ValueError("R57 original source shards incomplete")
    rows.sort(key=lambda x:(x["block"],SUPPORT.index(x["support"]),
                             STATES.index(x["generating_state"])))
    report=summarize(rows)
    if not report["complete_failure_inclusive_source_and_start_ledger"]:
        raise ValueError("R57 refused missing original source/start denominator")
    out.mkdir(parents=True,exist_ok=True)
    _write(out/"cases.json",rows)
    _write(out/"summary.json",report)
    (out/"source-commit.txt").write_text(sha+"\n")
    names=("cases.json","summary.json","source-commit.txt")
    (out/"SHA256SUMS").write_text("".join(
        hashlib.sha256((out/x).read_bytes()).hexdigest()+"  "+x+"\n"
        for x in names))
    print("R57 original nested exact-zero/nonnegative Gaussian REML:",
          json.dumps(report,sort_keys=True))


def main():
    a=argparse.ArgumentParser()
    a.add_argument("--out",required=True,type=Path)
    g=a.add_mutually_exclusive_group(required=True)
    g.add_argument("--start",type=int)
    g.add_argument("--merge-parts",type=Path)
    a.add_argument("--stop",type=int)
    args=a.parse_args()
    if args.merge_parts is not None:
        aggregate(args.out,args.merge_parts)
    elif args.stop is not None:
        shard(args.out,args.start,args.stop)
    else:
        raise SystemExit("R57 requires original block start/stop")


if __name__=="__main__":
    main()
