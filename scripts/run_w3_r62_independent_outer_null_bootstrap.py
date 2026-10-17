"""R62 research-only: conditional Gaussian H0 nuisance-REFITTED bootstrap pilot.

Each of 32 NEW independent structural-zero Gaussian primitive blocks supplies
paired ordinary/extreme leverage source observations; 63 fixed-design
Gaussian H0 bootstrap pseudoresponses per paired source. Every draw fits
BOTH original nested Gaussian REML models, refitting nuisance components.
This is a outer-source external-seed Monte Carlo size pilot, NOT established null
calibration, Type-I evidence, hypothesis-test power, or a public API.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path

import numpy as np
from scipy.linalg import cho_factor, cho_solve

from scripts import run_w3_r16_leverage_covariance_factorial as r16
from scripts import run_w3_r17_fresh_feasibility as fresh
from scripts import run_w3_r48_independent_fitted_cr2 as r48
from scripts import run_w3_r57_nested_zero_nonnegative_reml as r57
from scripts import run_w3_r58_boundary_null_reference as r58

STUDY="W3_R62_INDEPENDENT_OUTER_NULL_NUISANCE_REFIT_GAUSSIAN_PILOT"
MASTER_SEED=202610186262
DRAW_SEED=202610186263
BLOCKS=32
PARTICIPANTS=24
SUPPORT=("ordinary_dependent","extreme_dependent")
B=63
SHARDS=tuple((i,i+4) for i in range(0,BLOCKS,4))
SOURCE_SLOTS=BLOCKS*len(SUPPORT)
BOOT_SLOTS=SOURCE_SLOTS*B
FITS=2*(SOURCE_SLOTS+BOOT_SLOTS)
OPTIMIZER_START_SLOTS=(SOURCE_SLOTS+BOOT_SLOTS)*6
ORIGINAL_ALPHA=.05
ORIGINAL_CUTOFF=r58.CRITICAL


def source(block,support):
    if type(block) is not int or not 0<=block<BLOCKS or support not in SUPPORT:
        raise ValueError("R62 outside preregistered Gaussian source universe")
    original=fresh.fresh_source(
        block,support,n=PARTICIPANTS,master_seed=MASTER_SEED,
        n_blocks=BLOCKS,max_n=PARTICIPANTS)
    X,y,w,g,t,tr,x, *_=r48.native_data(original)
    slopes=np.asarray(original[0]["participant_slope"],float)[
        np.asarray(g,int),0,0,0]
    component=r16.SIGMA_RANDOM_SLOPE*slopes*x*(1.+.25*t)
    if not np.isfinite(component).all() or component.shape!=y.shape:
        raise ValueError("R62 invalid Gaussian slope innovation")
    return {
        "X":X,"y":np.asarray(y,float)-component,"w":w,
        "group":g,"time":t,"trial":tr,"x":x,
        "removed_slope_L2":float(np.linalg.norm(component)),
        "true_slope_variance":0.,
    }


def nested_on(data):
    """Numerical failures are explicit; retain all original start positions."""
    out={"status":"refused","error":None,
         "null_fit":r57._not_attempted_model("exact_zero"),
         "alternative_fit":r57._not_attempted_model("nonnegative"),
         "raw_deviance":None,"nonnegative_deviance":None}
    try:
        X,y,w,g,t,tr,x=(data[k] for k in
                        ("X","y","w","group","time","trial","x"))
        prep=r57.prepare_reml_design(X,y,w,g,t,tr,x,
                 slope="predictor_scaled_slope")
        ref=r57._reference(data)
        out["observed_reference"]=float(ref)
        out["null_fit"]=r57.fit_model(prep,ref,"exact_zero")
        out["alternative_fit"]=r57.fit_model(prep,ref,"nonnegative")
        a=out["null_fit"];b=out["alternative_fit"]
        if a["status"]!="accepted" or b["status"]!="accepted":
            out["error"]="H0_or_H1_refused_by_original_numerical_gates"
            return out
        raw=2*(a["selected_NLL"]-b["selected_NLL"])
        out["raw_deviance"]=float(raw)
        if not np.isfinite(raw) or raw < -r57.NESTED_MONOTONIC_TOL:
            out["error"]="nonfinite_or_nonmonotone_nested_gap"
            return out
        out.update(status="accepted",nonnegative_deviance=float(max(0.,raw)))
    except Exception as exc:
        out["error"]=repr(exc)[:450]
    return out


def h0_gls_covariance(data,null_fit,observed_reference):
    """Build V_i from the fitted *H0* component ratios (slope EXACTLY 0).

    Input is the ORIGINAL observed source only. WLS scale is respected:
    K_i and pseudo-residual draws are in sqrt(weight) * y units.
    """
    if null_fit["status"]!="accepted":
        raise ValueError("R62 requires accepted H0 source fit")
    free=np.asarray(null_fit["selected_free_component_variance_ratios"],float)
    if free.shape!=(3,) or (free<=0).any() or not np.isfinite(free).all():
        raise ValueError("R62 invalid original fitted H0 variance components")
    # Component order: participant_intercept, participant_slope, trial, sensor.
    theta=float(observed_reference)*np.array(
        [free[0],0.,free[1],free[2]],float)
    X,y,w,g,t,tr,x=(data[k] for k in
                    ("X","y","w","group","time","trial","x"))
    prepared=r57.prepare_reml_design(
        X,y,w,g,t,tr,x,slope="predictor_scaled_slope")
    labels=np.unique(g)
    if len(labels)!=len(prepared):
        raise ValueError("R62 original cluster design / H0 covariance mismatch")
    q=X.shape[1]
    gram=np.zeros((q,q));score=np.zeros(q);covs=[]
    for label,(Zi,yi,Ks) in zip(labels,prepared):
        indexes=np.flatnonzero(g==label)
        expected=X[indexes]*np.sqrt(w[indexes])[:,None]
        np.testing.assert_allclose(Zi,expected,atol=1e-11,rtol=1e-11)
        V=sum(float(theta[i])*Ks[i] for i in range(4))
        V=(V+V.T)*.5
        fac=cho_factor(V,lower=True,check_finite=False)
        gram+=Zi.T@cho_solve(fac,Zi,check_finite=False)
        score+=Zi.T@cho_solve(fac,yi,check_finite=False)
        # Cholesky factor returned in lower triangle by cho_factor.
        L=np.tril(fac[0])
        covs.append((indexes,L))
    beta=np.linalg.solve(gram,score)
    if not np.isfinite(beta).all():
        raise ValueError("R62 GLS fitted fixed mean is nonfinite")
    return beta,covs,theta.tolist()


def pseudo_under_h0(data,beta,covs,block,support,draw):
    """One draw, independent of original source and all other pseudo-draws."""
    if not (0<=draw<BLOCKS*B and 0<=block<BLOCKS and support in SUPPORT):
        raise ValueError("R62 unregistered bootstrap draw")
    # Crucially seed BOTH block and support and replicate.
    seed=DRAW_SEED+100003*block+739*SUPPORT.index(support)+draw
    rng=np.random.default_rng(seed)
    simulated=np.asarray(data["X"]@beta,float).copy()
    w=np.asarray(data["w"],float)
    reached=np.zeros(len(simulated),bool)
    for idx,L in covs:
        if np.any(reached[idx]): raise ValueError("R62 duplicate cluster bootstrap indexes")
        reached[idx]=True
        simulated[idx]+=(L@rng.normal(size=len(idx)))/np.sqrt(w[idx])
    if not np.all(reached) or not np.isfinite(simulated).all():
        raise ValueError("R62 incomplete or nonfinite H0 bootstrap response")
    return {**data,"y":simulated},seed


def empty_case(block,support):
    return {
        "study":STUDY,"block":block,"support":support,
        "true_slope_variance":0.,
        "source_status":"refused","source_error":None,
        "observed":nested_on_invalid(),
        "fitted_null_theta":None,"bootstrap":[],
        "planned_bootstrap_slots":B,
        "conditional_bootstrap_p":None,
        "candidate_5pct_exceedance":None,
        "bootstrap_5pct_exceedance":None,
        "null_calibration_qualified":False,
        "pointwise_or_simultaneous_90pct_CR2_qualified":False,
        "release_authorized":False,
    }


def nested_on_invalid():
    return {"status":"not_attempted","error":"source_unavailable",
            "null_fit":r57._not_attempted_model("exact_zero"),
            "alternative_fit":r57._not_attempted_model("nonnegative"),
            "raw_deviance":None,"nonnegative_deviance":None}


def empty_draw(draw):
    return {
        "draw":draw,"status":"not_attempted","seed":None,
        "nested":nested_on_invalid(),
    }


def evaluate(block,support):
    out=empty_case(block,support)
    out["bootstrap"]=[empty_draw(i) for i in range(B)]
    try:
        data=source(block,support)
        out["source_status"]="ok"
        out["source_removed_slope_L2"]=data["removed_slope_L2"]
        out["observed"]=nested_on(data)
        if out["observed"]["status"]!="accepted":
            return out
        b,covs,theta=h0_gls_covariance(
            data,out["observed"]["null_fit"],
            out["observed"]["observed_reference"])
        out["fitted_null_theta"]=theta
        out["candidate_5pct_exceedance"]=bool(
            out["observed"]["nonnegative_deviance"]>ORIGINAL_CUTOFF)
        for draw in range(B):
            try:
                pseudo,seed=pseudo_under_h0(data,b,covs,block,support,draw)
                fit=nested_on(pseudo)
                out["bootstrap"][draw]={
                    "draw":draw,"status":fit["status"],
                    "seed":seed,"nested":fit}
            except Exception as exc:
                out["bootstrap"][draw]={"draw":draw,
                    "status":"refused","seed":None,"nested":nested_on_invalid(),
                    "error":repr(exc)[:450]}
        passed=[v for v in out["bootstrap"]
                if v["nested"]["status"]=="accepted"]
        if len(passed)==B:
            stat=out["observed"]["nonnegative_deviance"]
            exceed=sum(v["nested"]["nonnegative_deviance"]>=stat
                       for v in passed)
            # Finite-MC add-one exact-rank convention (no bootstrap=observed shortcut).
            out["conditional_bootstrap_p"]=(1+exceed)/(B+1)
            out["bootstrap_5pct_exceedance"]=bool(
                out["conditional_bootstrap_p"]<=ORIGINAL_ALPHA)
    except Exception as exc:
        out["source_error"]=repr(exc)[:450]
    return out


def summarize(rows):
    """Failure-inclusive NEW 32-independent-block Gaussian source null pilot.

    Source-level Monte Carlo uncertainty is measured over the 32 primitive
    independent blocks PER support, not over 4032 within-source bootstrap
    draws. Bootstrap p-values are conditional plug-in, unvalidated.
    """
    expected={(i,s) for i in range(BLOCKS) for s in SUPPORT}
    keys=[(r["block"],r["support"]) for r in rows]
    if len(keys)!=SOURCE_SLOTS or len(set(keys))!=SOURCE_SLOTS or set(keys)!=expected:
        raise ValueError("R62 missing or duplicated NEW independent source blocks")
    slots=sum(len(r["bootstrap"]) for r in rows)
    if slots!=BOOT_SLOTS or any(
        [v["draw"] for v in r["bootstrap"]]!=list(range(B)) for r in rows
    ):
        raise ValueError("R62 original Gaussian H0 draw denominator incomplete")
    starts=sum(len(f["null_fit"]["original_starts"])+
               len(f["alternative_fit"]["original_starts"])
               for r in rows for f in [r["observed"]]+
               [v["nested"] for v in r["bootstrap"]])
    if starts!=OPTIMIZER_START_SLOTS:
        raise ValueError("R62 numerical optimizer start ledger incomplete")
    strata={}
    for support in SUPPORT:
        subset=[r for r in rows if r["support"]==support]
        complete=[r for r in subset if r["conditional_bootstrap_p"] is not None]
        n=len(complete)
        rejected=sum(r["bootstrap_5pct_exceedance"] is True for r in complete)
        refused=BLOCKS-n
        original_fit=[r for r in subset if r["observed"]["status"]=="accepted"]
        classical=sum(r["candidate_5pct_exceedance"] is True for r in original_fit)
        strata[support]={
            "independent_source_blocks":BLOCKS,
            "recorded_source_cases":len(subset),
            "original_sources_numerically_accepted":len(original_fit),
            "planned_bootstrap_draw_slots":BLOCKS*B,
            "recorded_bootstrap_draw_slots":sum(len(r["bootstrap"]) for r in subset),
            "accepted_bootstrap_draws":sum(
                v["nested"]["status"]=="accepted"
                for r in subset for v in r["bootstrap"]),
            "source_cases_with_all_63_numerical_bootstrap_refits":n,
            "source_cases_with_refused_or_incomplete_bootstrap":refused,
            "conditional_bootstrap_p_values":[
                {"block":r["block"],"p":r["conditional_bootstrap_p"]}
                for r in complete],
            "bootstrap_candidate_nominal_005_rejections_complete_sources":rejected,
            "bootstrap_candidate_nominal_005_fraction_complete_sources":
                rejected/n if n else None,
            "bootstrap_candidate_nominal_005_Wilson95_complete_sources":
                r58.wilson_95(rejected,n),
            "bootstrap_all_source_lower_refusals_as_nonrejection":rejected/BLOCKS,
            "bootstrap_all_source_upper_refusals_as_rejection":
                (rejected+refused)/BLOCKS,
            "classical_candidate_exceedances_accepted_sources":classical,
            "classical_candidate_Wilson95_accepted_sources":
                r58.wilson_95(classical,len(original_fit)),
            "calibrated_type_I_rate_or_power_qualified":False,
        }
    paired={(r["block"],r["support"]):r for r in rows}
    jointly=[(paired[(b,SUPPORT[0])],paired[(b,SUPPORT[1])])
             for b in range(BLOCKS)]
    accepted_pairs=[(a["bootstrap_5pct_exceedance"],
                     b["bootstrap_5pct_exceedance"])
                    for a,b in jointly
                    if a["conditional_bootstrap_p"] is not None and
                    b["conditional_bootstrap_p"] is not None]
    both=sum(a and b for a,b in accepted_pairs)
    only_ordinary=sum(a and not b for a,b in accepted_pairs)
    only_extreme=sum(b and not a for a,b in accepted_pairs)
    neither=sum(not a and not b for a,b in accepted_pairs)
    return {
        "study":STUDY,
        "new_source_seed":MASTER_SEED,"new_draw_seed":DRAW_SEED,
        "independent_Gaussian_source_blocks":BLOCKS,
        "participants_per_source":PARTICIPANTS,
        "leverage_cases_paired_not_independent":True,
        "planned_source_cases":SOURCE_SLOTS,"recorded_source_cases":len(rows),
        "bootstrap_draws_per_source":B,
        "planned_H0_bootstrap_draw_slots":BOOT_SLOTS,
        "recorded_H0_bootstrap_draw_slots":slots,
        "planned_fitted_nested_model_slots":FITS,
        "planned_optimizer_start_slots":OPTIMIZER_START_SLOTS,
        "recorded_optimizer_start_slots":starts,
        "bootstrap_refits_both_H0_and_H1_with_new_nuisance":True,
        "bootstrap_conditioned_on_source_fitted_H0_and_original_design":True,
        "candidate_add_one_bootstrap_rank_grid_denominator":B+1,
        "no_prior_source_used_for_critical_tuning":True,
        "outer_new_source_Gaussian_null_evaluation_exploratory_only":True,
        "paired_both_complete":len(accepted_pairs),
        "paired_bootstrap_ordinary_only_exceedances":only_ordinary,
        "paired_bootstrap_extreme_only_exceedances":only_extreme,
        "paired_bootstrap_both_exceedances":both,
        "paired_bootstrap_neither_exceedances":neither,
        "no_validated_type_I_reference":True,
        "no_pointwise_or_simultaneous_90pct_CR2_inference":True,
        "release_authorized":False,"strata":strata}


def shard(out,start,stop):
    if (start,stop) not in SHARDS:
        raise ValueError("R62 unauthorized bootstrap source shard")
    out.mkdir(parents=True,exist_ok=True)
    rows=[evaluate(b,s) for b in range(start,stop) for s in SUPPORT]
    payload=json.dumps(rows,sort_keys=True,default=r58.r57.r53._json_plain,
                       allow_nan=False,indent=2)+"\n"
    (out/"cases.json").write_text(payload)
    (out/"manifest.json").write_text(json.dumps(
        {"study":STUDY,"start":start,"stop":stop,
         "new_source_seed":MASTER_SEED,"new_draw_seed":DRAW_SEED,
         "checkout":os.environ.get("GITHUB_SHA","unverified-local"),
         "source_count":len(rows),
         "sha256_cases":hashlib.sha256(payload.encode()).hexdigest()},
        sort_keys=True,indent=2)+"\n")


def aggregate(out,parts):
    files=list(parts.glob("*/manifest.json"))
    if len(files)!=len(SHARDS):
        raise ValueError("R62 exact eight original source parts required")
    commit=os.environ.get("GITHUB_SHA","unverified-local")
    rows=[];seen=set()
    for f in files:
        item=json.loads(f.read_text());key=(item["start"],item["stop"])
        if (key not in SHARDS or key in seen or
            item["study"]!=STUDY or item["new_source_seed"]!=MASTER_SEED or
            item["new_draw_seed"]!=DRAW_SEED or item["checkout"]!=commit):
            raise ValueError("R62 source manifest cannot merge")
        seen.add(key)
        raw=(f.parent/"cases.json").read_bytes()
        if hashlib.sha256(raw).hexdigest()!=item["sha256_cases"]:
            raise ValueError("R62 source artifact SHA256 mismatch")
        batch=json.loads(raw)
        if (len(batch)!=item["source_count"] or
            {(r["block"],r["support"]) for r in batch} !=
            {(b,s) for b in range(*key) for s in SUPPORT}):
            raise ValueError("R62 shard cases incomplete or mislabeled")
        rows+=batch
    rows.sort(key=lambda x:(x["block"],SUPPORT.index(x["support"])))
    report=summarize(rows)
    out.mkdir(parents=True,exist_ok=True)
    (out/"cases.json").write_text(json.dumps(
        rows,sort_keys=True,indent=2,allow_nan=False)+"\n")
    (out/"summary.json").write_text(json.dumps(
        report,sort_keys=True,indent=2,allow_nan=False)+"\n")
    (out/"source-commit.txt").write_text(commit+"\n")
    (out/"SHA256SUMS").write_text("".join(
        hashlib.sha256((out/name).read_bytes()).hexdigest()+"  "+name+"\n"
        for name in ("cases.json","summary.json","source-commit.txt")))
    print(json.dumps(report,sort_keys=True))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",required=True,type=Path)
    mode=ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--start",type=int)
    mode.add_argument("--merge-parts",type=Path)
    ap.add_argument("--stop",type=int)
    a=ap.parse_args()
    if a.merge_parts is not None:aggregate(a.out,a.merge_parts)
    elif a.stop is not None:shard(a.out,a.start,a.stop)
    else:raise SystemExit("R62 must specify --start and --stop")

if __name__=="__main__":
    main()
