"""W3 R84 prospectively frozen observation-process diagnostic (NOT a confidence-band estimator).

Synthetic R81-family complete source, 4 independently specified observation laws,
pointwise available-case OLS, rank/anchor refuse gates, immutable 32-block archive.
The public package correctly rejects NaN trajectories. No MNAR adjustment or release.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import warnings

import numpy as np
import pandas as pd

from eyetrajectoriespy import TrajectorySet
from eyetrajectoriespy.function_on_scalar import fit_function_on_scalar_regression

STUDY="W3_R84_EXTERNAL_OUTCOME_VALIDATION_FOR_MNAR"
SOURCE_SEED=202610218480
OBS_SEED=202610218481
BLOCKS=32
T=np.linspace(0.,1.,31)
DIMS=("x","y")
CONFIGS=("curve_standard","participant_standard")
SUPPORT=("two_anchors","sixteen_anchors")
VARIANCES=("constant","predictor_heteroskedastic")
MECHANISMS=("complete","MCAR","MAR","MNAR")
ANCHORS={"two_anchors":2,"sixteen_anchors":16}
SHARDS=tuple((a,a+4) for a in range(0,32,4))
N_SOURCES=BLOCKS*len(CONFIGS)*len(SUPPORT)*len(VARIANCES)
N_CASES=N_SOURCES*len(MECHANISMS)
MIN_UNITS=8
MIN_NEG_POS_ANCHORS=1
DELTA=(-1.1,-.55,0.,.55,1.1)
WEIGHT_POSITIVITY=.02
METHODS=("COMPLETE","MCAR_known","MAR_sensitivity","MNAR_sensitivity","MNAR_oracle")
RECOVERY_SEED=202610218482
RECOVERY_LEVELS=(0.,.25,.50)
LOSS_MECHANISMS=("MAR","MNAR")
RECORDS_PER_SOURCE=6
N_RECORDS=N_SOURCES*RECORDS_PER_SOURCE


def info(config):
    if config=="curve_standard":
        return 72,1,"curve"
    if config=="participant_standard":
        return 36,3,"participant"
    raise ValueError("R84 unknown native independent-unit configuration")


def ident(block,config,support,variance):
    if (type(block) is not int or block not in range(BLOCKS)
        or config not in CONFIGS or support not in SUPPORT or variance not in VARIANCES):
        raise ValueError("R84 original source identity invalid")


def seed(block,config,support,variance,domain):
    ident(block,config,support,variance)
    ci=CONFIGS.index(config)
    if domain=="source":
        return SOURCE_SEED+100003*block+10007*ci
    if domain=="mask":
        return (OBS_SEED+1000003*block+10007*ci
                +739*SUPPORT.index(support)+97*VARIANCES.index(variance))
    raise ValueError("R84 unknown frozen random stream")


def truth_coefficients():
    intercept=np.stack((.35+.08*T,.25-.04*T),axis=1)
    slope=np.stack((.40+.11*np.cos(np.pi*T),-.28+.13*np.sin(np.pi*T)),axis=1)
    return np.stack((intercept,slope),axis=0)


def trial_time_sd():
    return .04*(.70+.60*T)


def trial_chol():
    ix=np.arange(len(T))
    return np.linalg.cholesky(.72**np.abs(ix[:,None]-ix[None,:]))


def mix_trials(z):
    q=(.15+.65*T)[None,None,:,None]
    out=np.empty_like(z)
    out[...,0]=z[...,0]
    qq=.15+.65*T
    out[...,1]=qq[None,None,:]*z[...,0]+np.sqrt(1-qq*qq)[None,None,:]*z[...,1]
    return out


def source(block,config,support,variance):
    """New independent X/Y, constant across all four loss mechanisms."""
    n,trials,design=info(config)
    rng=np.random.default_rng(seed(block,config,support,variance,"source"))
    x=rng.uniform(-.95,.95,size=n)
    half=ANCHORS[support]//2
    x[:half]=-4.
    x[-half:]=4.
    scale=np.ones(n) if variance=="constant" else 1.+.75*np.abs(x)
    beta=truth_coefficients()
    mean=beta[0][None]+x[:,None,None]*beta[1][None]
    latent=np.zeros((n,len(T),2))
    if design=="participant":
        g=rng.normal(0,1,size=(n,1,2))
        m=np.empty_like(g)
        m[...,0]=g[...,0]
        m[...,1]=.45*g[...,0]+np.sqrt(1.-.45**2)*g[...,1]
        latent=.065*(1.+.35*T[None,:,None])*m
    white=rng.normal(0,1,size=(n,trials,len(T),2))
    trial_noise=np.einsum("tu,njud->njtd",trial_chol(),white,optimize=True)
    trial_noise=mix_trials(trial_noise)*trial_time_sd()[None,None,:,None]
    radial=np.sqrt(3./rng.chisquare(5,size=n))
    indicator=(rng.random(n)<.08).astype(float)-.08
    profile=(.75+.25*T[:,None])*np.array([1.,-.65])[None]
    shock=.16*indicator[:,None,None]*profile[None]
    y=(mean[:,None]+scale[:,None,None,None]*
       (radial[:,None,None,None]*(latent[:,None]+trial_noise)+shock[:,None]))
    return np.column_stack((np.ones(n),x)),y,beta,scale


def probabilities(x,y,mechanism):
    n,trials,nt,nd=y.shape
    if mechanism=="complete":
        return np.zeros(y.shape,dtype=float)
    if mechanism=="MCAR":
        return np.full_like(y,.12,dtype=float)
    idx=np.arange(trials)[None,:,None,None]
    linear=(-2.2+np.abs(x[:,1,None,None,None])/4.
            +.7*T[None,None,:,None]+.2*idx)
    if mechanism=="MNAR":
        beta=truth_coefficients()
        means=(beta[0][None]+x[:,1,None,None]*beta[1][None])
        linear=linear+1.1*np.tanh((y-means[:,None])/.08)
    elif mechanism!="MAR":
        raise ValueError("R84 unknown loss mechanism")
    return np.broadcast_to(1/(1+np.exp(-linear)),y.shape).copy()


def common_masks(block,config,support,variance, X,y):
    rng=np.random.default_rng(seed(block,config,support,variance,"mask"))
    uniforms=rng.random(y.shape)
    return {m: uniforms<probabilities(X,y,m) for m in MECHANISMS}


def as_independent_units(y,mask,config):
    """No imputation: mean only observed trials in each native independent unit."""
    count=np.sum(~mask,axis=1)
    summ=np.where(~mask,y,0.).sum(axis=1)
    unit=np.divide(summ,count,out=np.full_like(summ,np.nan),where=count>0)
    return unit,np.any(~mask,axis=1)


def pointwise_diagnostic(X,y,mask,config,beta):
    """Grid-wise *diagnostic*, never a missingness-robust confidence estimator."""
    native,available=as_independent_units(y,mask,config)
    est=np.full((len(T),2),np.nan)
    nobs=np.sum(available,axis=0)
    refused=np.zeros((len(T),2),bool)
    neg=np.zeros((len(T),2),int)
    pos=np.zeros((len(T),2),int)
    for t in range(len(T)):
        for d in range(2):
            keep=available[:,t,d]
            xx=X[keep]
            neg[t,d]=int(np.sum(xx[:,1]==-4.))
            pos[t,d]=int(np.sum(xx[:,1]==4.))
            if (len(xx)<MIN_UNITS or neg[t,d]<MIN_NEG_POS_ANCHORS or
                pos[t,d]<MIN_NEG_POS_ANCHORS or
                np.linalg.matrix_rank(xx)<2):
                refused[t,d]=True
                continue
            est[t,d]=np.linalg.lstsq(xx,native[keep,t,d],rcond=None)[0][1]
    valid=~refused
    error=est[valid]-beta[1][valid]
    return {"pointwise_slope":[[float(v) if np.isfinite(v) else None for v in row]
                               for row in est],
            "observed_unit_counts":nobs.astype(int).tolist(),
            "negative_anchor_counts":neg.tolist(),
            "positive_anchor_counts":pos.tolist(),
            "grid_refused":refused.tolist(),
            "grid_refused_count":int(np.sum(refused)),
            "grid_estimable_count":int(np.sum(valid)),
            "mean_abs_slope_error":float(np.mean(np.abs(error))) if error.size else None,
            "max_abs_slope_error":float(np.max(np.abs(error))) if error.size else None,
            "mean_signed_slope_error":float(np.mean(error)) if error.size else None,
            "min_independent_units":int(np.min(nobs)),
            "min_negative_anchors":int(np.min(neg)),
            "min_positive_anchors":int(np.min(pos))}


def digest(arr,decimals=9):
    x=np.asarray(arr,float)
    return sha256(np.round(x,decimals).astype("<f8").tobytes(order="C")).hexdigest()


def mask_digest(mask):
    return sha256(np.asarray(mask,dtype=np.uint8).tobytes(order="C")).hexdigest()


def native_refusal(X,y,mask,config):
    """A public NaN acceptance is a research gate FAILURE, not an inference result."""
    if not mask.any():
        return False
    n,trials,_=y.shape[:3]
    ids=tuple(f"P{i:03d}-T{j:02d}" for i in range(n) for j in range(trials))
    val=np.where(mask,np.nan,y).reshape(n*trials,len(T),2)
    meta=pd.DataFrame({"participant_id":[f"P{i:03d}" for i in range(n) for _ in range(trials)],
                       "trial_id":[j for _ in range(n) for j in range(trials)]})
    gaze=TrajectorySet(time=T.copy(),values=val,curve_ids=ids,
                       dimension_names=DIMS,coordinate_system="normalized",
                       time_unit="s",metadata=meta)
    frame=pd.DataFrame({"curve_id":ids,"condition":np.repeat(X[:,1],trials)})
    try:
        fit_function_on_scalar_regression(
            gaze,frame,("condition",),dimensions=DIMS,
            unit="participant" if trials>1 else "curve",
            participant_column="participant_id" if trials>1 else None)
    except ValueError as exc:
        if "missing" in str(exc).lower() or "finite complete" in str(exc).lower():
            return True
        raise
    raise AssertionError("R84 public fit silently accepted missing gaze")



def logit_base(X,y):
    n,trials,_,_=y.shape
    trial=np.arange(trials)[None,:,None,None]
    return np.broadcast_to(-2.2+np.abs(X[:,1,None,None,None])/4.
                           +.7*T[None,None,:,None]+.2*trial,y.shape)



def recovery_uniforms(block,config,support,variance,y):
    ident(block,config,support,variance)
    ci=CONFIGS.index(config)
    key=(RECOVERY_SEED+1000003*block+10007*ci
         +739*SUPPORT.index(support)+97*VARIANCES.index(variance))
    return np.random.default_rng(key).random(y.shape),key


def observed_pilot(X,y,mask):
    """Only actually visible Y (never oracle or external recovery) enters pilot."""
    fitted=np.full((31,2,2),np.nan)
    admissible=np.zeros((31,2),bool)
    counts=np.zeros((31,2),int)
    for t in range(31):
        for d in range(2):
            uid,tr=np.nonzero(~mask[:,:,t,d])
            counts[t,d]=len(np.unique(uid))
            if counts[t,d]<MIN_UNITS:
                continue
            xx=X[uid]
            if np.linalg.matrix_rank(xx)<2:
                continue
            fitted[t,d]=np.linalg.lstsq(xx,y[uid,tr,t,d],rcond=None)[0]
            admissible[t,d]=True
    return fitted,admissible,counts


def recover_delta(X,y,mask,recovery,pilot,pilot_valid,rate):
    """Pooled scalar selection coefficient estimated from visible and externally recovered Y.

    The missing Y is touched only where independently recovered; missing and
    not externally recovered values are never included in the weighted score.
    No variance/interval/band estimated.
    """
    if rate<=0:
        return {"identified_with_external_validation":False,
                "delta_estimate":None,"delta_abs_error":None,
                "converged":False,"newton_iterations":0,
                "weighted_score_residual":None,
                "pseudo_likelihood_information":None,
                "boundary_saturated":False,"included_measured_responses":0}
    visible=~mask
    validated=mask & recovery
    included=(visible|validated)&pilot_valid[None,None,:,:]
    rows,trials,times,coords=np.nonzero(included)
    if not len(rows) or not np.any(validated&pilot_valid[None,None,:,:]):
        return {"identified_with_external_validation":False,
                "delta_estimate":None,"delta_abs_error":None,
                "converged":False,"newton_iterations":0,
                "weighted_score_residual":None,
                "pseudo_likelihood_information":None,
                "boundary_saturated":False,"included_measured_responses":int(len(rows))}
    response=y[rows,trials,times,coords]
    predicted=(pilot[times,coords,0]+pilot[times,coords,1]*X[rows,1])
    h=np.tanh((response-predicted)/.08)
    offset=(-2.2+np.abs(X[rows,1])/4.+.7*T[times]+.2*trials)
    m=mask[rows,trials,times,coords].astype(float)
    w=np.where(m.astype(bool),1./rate,1.)
    delta=0.
    converged=False
    iterations=0
    for iteration in range(1,36):
        eta=np.clip(offset+delta*h,-45,45)
        p=1./(1+np.exp(-eta))
        score=float(np.dot(w*h,m-p))
        info=float(np.dot(w*h*h,p*(1.-p)))
        iterations=iteration
        if not np.isfinite(score) or not np.isfinite(info) or info<=1.e-12:
            break
        if abs(score)<1e-8:
            converged=True
            break
        new=float(np.clip(delta+score/info,-4.,4.))
        if abs(new-delta)<1e-11:
            delta=new
            converged=abs(score)<1e-6
            break
        delta=new
    eta=np.clip(offset+delta*h,-45,45)
    p=1./(1+np.exp(-eta))
    score=float(np.dot(w*h,m-p))
    information=float(np.dot(w*h*h,p*(1.-p)))
    if not np.isfinite(score) or information<=1e-12:
        converged=False
    if not converged and abs(score)<1e-7 and information>1e-12:
        converged=True
    return {"identified_with_external_validation":bool(converged),
            "delta_estimate":float(delta) if converged else None,
            "delta_abs_error":None, "converged":bool(converged),
            "newton_iterations":iterations,
            "weighted_score_residual":float(score),
            "pseudo_likelihood_information":float(information),
            "boundary_saturated":bool(abs(delta)>=3.999999),
            "included_measured_responses":int(len(rows))}


def evaluate(block,config,support,variance):
    ident(block,config,support,variance)
    X,y,beta,unit_scale=source(block,config,support,variance)
    masks=common_masks(block,config,support,variance,X,y)
    recovered_uniform,key=recovery_uniforms(block,config,support,variance,y)
    rows=[]
    for mechanism in LOSS_MECHANISMS:
        mask=masks[mechanism]
        if not native_refusal(X,y,mask,config):
            raise AssertionError("R84 original stable public complete-grid fit accepted incomplete gaze")
        pilot,pilot_valid,pilot_counts=observed_pilot(X,y,mask)
        missing_total=int(mask.sum())
        for rate in RECOVERY_LEVELS:
            validation=mask&(recovered_uniform<rate)
            est=recover_delta(X,y,mask,validation,pilot,pilot_valid,rate)
            true_delta=0. if mechanism=="MAR" else 1.1
            if est["delta_estimate"] is not None:
                est["delta_abs_error"]=abs(est["delta_estimate"]-true_delta)
            rows.append({
                "study":STUDY,"block":block,"config":config,"support":support,
                "variance":variance,"mechanism":mechanism,
                "recovery_rate":rate,"true_source_delta_simulator_only":true_delta,
                "source_seed":seed(block,config,support,variance,"source"),
                "mask_seed":seed(block,config,support,variance,"mask"),
                "recovery_seed":key,
                "source_X_digest":digest(X),"source_Y_digest":digest(y),
                "original_mask_digest":mask_digest(mask),
                "recovered_missing_mask_digest":mask_digest(validation),
                "native_public_missing_gaze_refused":True,
                "source_independent_units":len(X),"trials_per_independent_unit":y.shape[1],
                "original_missing_count":missing_total,
                "original_observed_fraction":float((~mask).mean()),
                "externally_recovered_count":int(validation.sum()),
                "pilot_grid_refused_count":int((~pilot_valid).sum()),
                "pilot_min_distinct_observed_units":int(pilot_counts.min()),
                "observed_only_pilot_digest":digest(np.nan_to_num(pilot,nan=0.)),
                "source_known_truth_used_by_estimator":False,
                "recoveries_independent_given_original_missing":True,
                "no_interval_no_band_no_mnar_nonparametric_identification":True,
                "release_authorized":False,**est
            })
    assert len(rows)==RECORDS_PER_SOURCE
    return rows


def summary(rows):
    expect={(b,c,s,v,m,r) for b in range(BLOCKS) for c in CONFIGS
            for s in SUPPORT for v in VARIANCES
            for m in LOSS_MECHANISMS for r in RECOVERY_LEVELS}
    ids=[(z["block"],z["config"],z["support"],z["variance"],
          z["mechanism"],z["recovery_rate"]) for z in rows]
    if len(rows)!=N_RECORDS or set(ids)!=expect or len(set(ids))!=N_RECORDS:
        raise ValueError("R84 source-condition or recovery grid incomplete/duplicated")
    report={}
    for config in CONFIGS:
        report[config]={}
        for support in SUPPORT:
            report[config][support]={}
            for variance in VARIANCES:
                report[config][support][variance]={}
                for mechanism in LOSS_MECHANISMS:
                    report[config][support][variance][mechanism]={}
                    for rate in RECOVERY_LEVELS:
                        sel=[z for z in rows if z["config"]==config and z["support"]==support and z["variance"]==variance
                             and z["mechanism"]==mechanism and z["recovery_rate"]==rate]
                        if len(sel)!=BLOCKS or len({z["block"] for z in sel})!=BLOCKS:
                            raise ValueError("R84 true primitive independent source denominator changed")
                        for z in sel:
                            if (z["study"]!=STUDY or z["release_authorized"] is not False
                                or z["source_known_truth_used_by_estimator"] is not False
                                or z["no_interval_no_band_no_mnar_nonparametric_identification"] is not True
                                or z["source_seed"]!=seed(z["block"],config,support,variance,"source")
                                or z["mask_seed"]!=seed(z["block"],config,support,variance,"mask")
                                or (rate==0 and (z["delta_estimate"] is not None or z["identified_with_external_validation"]))):
                                raise ValueError("R84 source-truth leakage/unauthorized identification/report")
                        valid=[z for z in sel if z["converged"] and z["delta_estimate"] is not None]
                        def avg(k,data=sel):
                            a=[z[k] for z in data if z[k] is not None]
                            return float(np.mean(a)) if a else None
                        report[config][support][variance][mechanism][str(rate)]={
                            "independent_source_blocks":BLOCKS,
                            "converged_sources":len(valid),
                            "mean_missing_fraction":1-avg("original_observed_fraction"),
                            "mean_recovered_missing_count":avg("externally_recovered_count"),
                            "mean_refused_pilot_grid":avg("pilot_grid_refused_count"),
                            "mean_delta_estimate_converged_only":avg("delta_estimate",valid),
                            "mean_absolute_delta_error_converged_only":avg("delta_abs_error",valid),
                            "boundary_saturated_sources":sum(z["boundary_saturated"] for z in sel)
                        }
    return {"study":STUDY,"new_source_seed":SOURCE_SEED,"new_mask_seed":OBS_SEED,
            "new_recovery_seed":RECOVERY_SEED,"true_independent_blocks_per_cell":BLOCKS,
            "complete_XY_source_conditions":N_SOURCES,
            "original_mask_conditions":N_SOURCES*len(LOSS_MECHANISMS),
            "diagnostic_recovery_evaluations":N_RECORDS,
            "recovery_fractions":list(RECOVERY_LEVELS),
            "mechanisms":list(LOSS_MECHANISMS),
            "no_validation_identifies_delta":False,
            "nonparametric_MNAR_identification":False,
            "any_confidence_interval_or_band":False,"release_authorized":False,
            "results":report}


def shard(out,start,stop):
    if (start,stop) not in SHARDS:raise ValueError("R84 shard not pre-registered")
    out.mkdir(parents=True,exist_ok=True)
    rows=[r for b in range(start,stop) for c in CONFIGS for s in SUPPORT
          for v in VARIANCES for r in evaluate(b,c,s,v)]
    raw=(json.dumps(rows,sort_keys=True,allow_nan=False)+"\n").encode()
    (out/"cases.json").write_bytes(raw)
    manifest={"study":STUDY,"start":start,"stop":stop,"cases":len(rows),
              "sha256":sha256(raw).hexdigest(),
              "source_checkout":os.environ.get("GITHUB_SHA","unverified-local")}
    (out/"manifest.json").write_text(json.dumps(manifest,sort_keys=True)+"\n")


def aggregate(out,parts):
    rows=[]
    for a,b in SHARDS:
        p=parts/f"w3-r84-original-validation-shard-{a}"
        raw=(p/"cases.json").read_bytes()
        manifest=json.loads((p/"manifest.json").read_text())
        if (manifest["study"]!=STUDY or manifest["start"]!=a or manifest["stop"]!=b
            or manifest["cases"]!=(b-a)*len(CONFIGS)*len(SUPPORT)*len(VARIANCES)*RECORDS_PER_SOURCE
            or manifest["sha256"]!=sha256(raw).hexdigest()):
            raise ValueError("R84 original source part SHA256/identity mismatch")
        rows.extend(json.loads(raw))
    report=summary(rows)
    out.mkdir(parents=True,exist_ok=True)
    content={"source_checkout":os.environ.get("GITHUB_SHA","unverified-local"),
             "source_evaluations":rows,"aggregate":report}
    (out/"evidence.json").write_text(json.dumps(content,sort_keys=True,allow_nan=False)+"\n")
    (out/"source-commit.txt").write_text(content["source_checkout"]+"\n")
    (out/"SHA256SUMS").write_text("".join(
        sha256((out/k).read_bytes()).hexdigest()+"  "+k+"\n"
        for k in ("evidence.json","source-commit.txt")))
    print(json.dumps(report,sort_keys=True,allow_nan=False))


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument("--start",type=int)
    g.add_argument("--merge-parts",type=Path)
    p.add_argument("--stop",type=int)
    a=p.parse_args()
    if a.merge_parts is not None:aggregate(a.out,a.merge_parts)
    elif a.stop is not None:shard(a.out,a.start,a.stop)
    else:raise SystemExit("R84 require --stop with --start")


if __name__=="__main__":
    main()
