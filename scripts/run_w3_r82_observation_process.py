"""W3 R82 prospectively frozen observation-process diagnostic (NOT a confidence-band estimator).

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

STUDY="W3_R82_NEW_OBSERVATION_PROCESS_MCAR_MAR_MNAR"
SOURCE_SEED=202610208280
OBS_SEED=202610208281
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


def info(config):
    if config=="curve_standard":
        return 72,1,"curve"
    if config=="participant_standard":
        return 36,3,"participant"
    raise ValueError("R82 unknown native independent-unit configuration")


def ident(block,config,support,variance):
    if (type(block) is not int or block not in range(BLOCKS)
        or config not in CONFIGS or support not in SUPPORT or variance not in VARIANCES):
        raise ValueError("R82 original source identity invalid")


def seed(block,config,support,variance,domain):
    ident(block,config,support,variance)
    ci=CONFIGS.index(config)
    if domain=="source":
        return SOURCE_SEED+100003*block+10007*ci
    if domain=="mask":
        return (OBS_SEED+1000003*block+10007*ci
                +739*SUPPORT.index(support)+97*VARIANCES.index(variance))
    raise ValueError("R82 unknown frozen random stream")


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
        raise ValueError("R82 unknown loss mechanism")
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
    raise AssertionError("R82 public fit silently accepted missing gaze")


def evaluate(block,config,support,variance):
    ident(block,config,support,variance)
    X,y,beta,scale=source(block,config,support,variance)
    masks=common_masks(block,config,support,variance,X,y)
    complete=pointwise_diagnostic(X,y,masks["complete"],config,beta)
    records=[]
    for mechanism in MECHANISMS:
        mask=masks[mechanism]
        d=pointwise_diagnostic(X,y,mask,config,beta)
        est=np.array([[v if v is not None else np.nan for v in row]
                      for row in d["pointwise_slope"]])
        full=np.array(complete["pointwise_slope"],dtype=float)
        allowed=np.isfinite(est)
        delta=est[allowed]-full[allowed]
        records.append({
            "study":STUDY,"block":block,"config":config,"support":support,
            "variance":variance,"mechanism":mechanism,
            "source_seed":seed(block,config,support,variance,"source"),
            "observation_seed":seed(block,config,support,variance,"mask"),
            "native_independent_units":int(len(X)),"source_trials":int(y.shape[1]),
            "source_X_digest":digest(X),"source_Y_digest":digest(y),
            "true_slope_digest":digest(beta[1]),"observed_mask_digest":mask_digest(mask),
            "observed_gaze_samples":int(np.size(mask)-np.sum(mask)),
            "missing_gaze_samples":int(np.sum(mask)),
            "gaze_observation_fraction":float(np.mean(~mask)),
            "fully_observed_curves":int(np.sum(np.all(~mask,axis=(2,3)))),
            "fully_observed_independent_units":int(np.sum(np.all(~mask,axis=(1,2,3)))),
            "native_missingness_refusal":native_refusal(X,y,mask,config),
            "mean_available_minus_full_slope":float(np.mean(delta)) if delta.size else None,
            "mean_abs_available_minus_full_slope":float(np.mean(np.abs(delta))) if delta.size else None,
            "not_an_MNAR_adjustment":True,"no_band_calibration":True,
            "release_authorized":False,**d
        })
    return records


def summary(rows):
    expect={(b,c,s,v,m) for b in range(BLOCKS) for c in CONFIGS
            for s in SUPPORT for v in VARIANCES for m in MECHANISMS}
    identity=[(r["block"],r["config"],r["support"],r["variance"],r["mechanism"]) for r in rows]
    if len(rows)!=N_CASES or len(set(identity))!=N_CASES or set(identity)!=expect:
        raise ValueError("R82 independent block/mechanism grid missing or duplicated")
    results={}
    for c in CONFIGS:
        results[c]={}
        for s in SUPPORT:
            results[c][s]={}
            for v in VARIANCES:
                results[c][s][v]={}
                for m in MECHANISMS:
                    g=[r for r in rows if (r["config"],r["support"],r["variance"],r["mechanism"])==(c,s,v,m)]
                    if len(g)!=BLOCKS:raise ValueError("R82 block denominator invalid")
                    for z in g:
                        if (z["study"]!=STUDY or not z["not_an_MNAR_adjustment"]
                           or not z["no_band_calibration"] or z["release_authorized"]
                           or z["source_seed"]!=seed(z["block"],c,s,v,"source")
                           or z["observation_seed"]!=seed(z["block"],c,s,v,"mask")):
                            raise ValueError("R82 source, method or withheld calibration provenance forged")
                    def mean(k):
                        vals=[z[k] for z in g if z[k] is not None]
                        return float(np.mean(vals)) if vals else None
                    results[c][s][v][m]={
                        "independent_source_blocks":BLOCKS,
                        "mean_observed_fraction":mean("gaze_observation_fraction"),
                        "mean_grid_estimable":mean("grid_estimable_count"),
                        "mean_grid_refused":mean("grid_refused_count"),
                        "mean_abs_slope_error":mean("mean_abs_slope_error"),
                        "mean_signed_slope_error":mean("mean_signed_slope_error"),
                        "mean_abs_available_minus_full_slope":mean("mean_abs_available_minus_full_slope"),
                        "mean_fully_observed_units":mean("fully_observed_independent_units"),
                        "native_refused_sources":sum(z["native_missingness_refusal"] for z in g)
                    }
    return {"study":STUDY,"source_seed":SOURCE_SEED,"mask_seed":OBS_SEED,
            "new_independent_primitive_blocks":BLOCKS,
            "original_source_cases":N_SOURCES,"mechanism_evaluations":N_CASES,
            "observation_mechanisms":list(MECHANISMS),"configs":list(CONFIGS),
            "supports":list(SUPPORT),"variances":list(VARIANCES),
            "min_estimable_native_units":MIN_UNITS,
            "native_requires_complete":True,"imputation_performed":False,
            "MNAR_correction_performed":False,"90percent_band_calibration_performed":False,
            "release_authorized":False,"results":results}


def shard(out,start,stop):
    if (start,stop) not in SHARDS:raise ValueError("R82 shard not pre-registered")
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
        p=parts/f"part-{a:02d}-{b:02d}"
        raw=(p/"cases.json").read_bytes()
        manifest=json.loads((p/"manifest.json").read_text())
        if (manifest["study"]!=STUDY or manifest["start"]!=a or manifest["stop"]!=b
            or manifest["cases"]!=(b-a)*len(CONFIGS)*len(SUPPORT)*len(VARIANCES)*len(MECHANISMS)
            or manifest["sha256"]!=sha256(raw).hexdigest()):
            raise ValueError("R82 original source part SHA256/identity mismatch")
        rows.extend(json.loads(raw))
    report=summary(rows)
    out.mkdir(parents=True,exist_ok=True)
    content={"source_checkout":os.environ.get("GITHUB_SHA","unverified-local"),
             "source_evaluations":rows,
             "aggregate":report}
    (out/"evidence.json").write_text(json.dumps(content,sort_keys=True,allow_nan=False)+"\n")
    (out/"source-commit.txt").write_text(content["source_checkout"]+"\n")
    for name in ("evidence.json","source-commit.txt"):
        (out/"SHA256SUMS").write_text(
            "".join(sha256((out/k).read_bytes()).hexdigest()+"  "+k+"\n"
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
    else:raise SystemExit("R82 require --stop with --start")


if __name__=="__main__":
    main()
