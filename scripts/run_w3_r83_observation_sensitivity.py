"""W3 R83 prospectively frozen observation-process diagnostic (NOT a confidence-band estimator).

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

STUDY="W3_R83_NEW_MNAR_SENSITIVITY_IDENTIFIABILITY"
SOURCE_SEED=202610218380
OBS_SEED=202610218381
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
RECORDS_PER_SOURCE=13
N_RECORDS=N_SOURCES*RECORDS_PER_SOURCE


def info(config):
    if config=="curve_standard":
        return 72,1,"curve"
    if config=="participant_standard":
        return 36,3,"participant"
    raise ValueError("R83 unknown native independent-unit configuration")


def ident(block,config,support,variance):
    if (type(block) is not int or block not in range(BLOCKS)
        or config not in CONFIGS or support not in SUPPORT or variance not in VARIANCES):
        raise ValueError("R83 original source identity invalid")


def seed(block,config,support,variance,domain):
    ident(block,config,support,variance)
    ci=CONFIGS.index(config)
    if domain=="source":
        return SOURCE_SEED+100003*block+10007*ci
    if domain=="mask":
        return (OBS_SEED+1000003*block+10007*ci
                +739*SUPPORT.index(support)+97*VARIANCES.index(variance))
    raise ValueError("R83 unknown frozen random stream")


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
        raise ValueError("R83 unknown loss mechanism")
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
    raise AssertionError("R83 public fit silently accepted missing gaze")



def logit_base(X,y):
    n,trials,_,_=y.shape
    trial=np.arange(trials)[None,:,None,None]
    return np.broadcast_to(-2.2+np.abs(X[:,1,None,None,None])/4.
                           +.7*T[None,None,:,None]+.2*trial,y.shape)


def weighted_pointwise(X,y,mask,mechanism,delta,oracle=False):
    """Descriptive weighted LS; one native unit id per participant; no SE or CI.

    The observed-only pilot is unweighted trial-level OLS, not the simulator
    generating mean. The true-mean oracle is separately labeled unusable.
    """
    n,trials,_,_=y.shape
    beta=truth_coefficients()
    truth_mean=beta[0][None]+X[:,1,None,None]*beta[1][None]
    base=logit_base(X,y)
    slope=np.full((31,2),np.nan)
    pilot_slope=np.full((31,2),np.nan)
    refused=np.zeros((31,2),bool)
    observed_unit_counts=np.zeros((31,2),int)
    neg=np.zeros((31,2),int)
    pos=np.zeros((31,2),int)
    ess=np.full((31,2),np.nan)
    weight_max=np.full((31,2),np.nan)
    for t in range(31):
        for d in range(2):
            avail=~mask[:,:,t,d]
            units=np.any(avail,axis=1)
            xx=X[units]
            observed_unit_counts[t,d]=int(units.sum())
            neg[t,d]=int(np.count_nonzero(xx[:,1]==-4.))
            pos[t,d]=int(np.count_nonzero(xx[:,1]==4.))
            if (units.sum()<MIN_UNITS or neg[t,d]<1 or pos[t,d]<1
                or np.linalg.matrix_rank(xx)<2):
                refused[t,d]=True
                continue
            rowids,colids=np.nonzero(avail)
            trial_x=X[rowids]
            response=y[rowids,colids,t,d]
            if np.linalg.matrix_rank(trial_x)<2:
                refused[t,d]=True
                continue
            pilot=np.linalg.lstsq(trial_x,response,rcond=None)[0]
            pilot_slope[t,d]=pilot[1]
            if mechanism=="MCAR":
                obs_p=np.full(len(response),.88)
            else:
                mu=(truth_mean[rowids,t,d] if oracle
                    else (pilot[0]+pilot[1]*X[rowids,1]))
                logits=base[rowids,colids,t,d]+delta*np.tanh((response-mu)/.08)
                missing_p=1/(1+np.exp(-logits))
                obs_p=1-missing_p
            if (np.any(~np.isfinite(obs_p)) or np.min(obs_p)<WEIGHT_POSITIVITY):
                refused[t,d]=True
                continue
            w=1/obs_p
            root=np.sqrt(w)
            mat=trial_x*root[:,None]
            if np.linalg.matrix_rank(mat)<2:
                refused[t,d]=True
                continue
            slope[t,d]=np.linalg.lstsq(mat,response*root,rcond=None)[0][1]
            cluster=np.bincount(rowids,weights=w,minlength=n)
            ess[t,d]=float(cluster.sum()**2/np.dot(cluster,cluster))
            weight_max[t,d]=float(w.max())
    return slope,pilot_slope,refused,observed_unit_counts,neg,pos,ess,weight_max


def rounded_grid(arr):
    z=np.asarray(arr,float)
    return [[None if not np.isfinite(v) else float(v) for v in line] for line in z]


def observations_record(block,config,support,variance,mechanism,method,delta,
                        X,y,beta,mask,complete,oracle=False):
    n,trials,design=info(config)
    if method=="COMPLETE":
        d=pointwise_diagnostic(X,y,mask,config,beta)
        slope=np.array(d["pointwise_slope"],float)
        pilot=slope.copy()
        refus=np.array(d["grid_refused"],bool)
        units=np.array(d["observed_unit_counts"],int)
        neg=np.array(d["negative_anchor_counts"],int)
        pos=np.array(d["positive_anchor_counts"],int)
        eff=np.full((31,2),float(n))
        maxwt=np.ones((31,2))
    else:
        slope,pilot,refus,units,neg,pos,eff,maxwt=weighted_pointwise(
            X,y,mask,mechanism,delta,oracle)
    valid=~refus
    difference=slope[valid]-complete[valid]
    error=slope[valid]-beta[1][valid]
    return {
        "study":STUDY,"block":block,"config":config,"support":support,
        "variance":variance,"observation_mechanism":mechanism,
        "method":method,"assumed_mnar_delta":float(delta),
        "simulator_only_oracle":bool(oracle),
        "source_seed":seed(block,config,support,variance,"source"),
        "observation_seed":seed(block,config,support,variance,"mask"),
        "native_independent_units":int(n),"trials_per_unit":int(trials),
        "source_X_digest":digest(X),"source_Y_digest":digest(y),
        "truth_slope_digest":digest(beta[1]),"observation_mask_digest":mask_digest(mask),
        "observed_fraction":float(np.mean(~mask)),
        "missing_samples":int(mask.sum()),
        "native_nan_refusal":bool(mask.any()),
        "pointwise_slopes":rounded_grid(slope),
        "observed_only_pilot_slopes":rounded_grid(pilot),
        "observed_unit_counts":units.tolist(),
        "negative_anchor_counts":neg.tolist(),
        "positive_anchor_counts":pos.tolist(),
        "grid_refused":refus.tolist(),
        "grid_refused_count":int(refus.sum()),
        "grid_estimable_count":int(valid.sum()),
        "min_observed_independent_units":int(units.min()),
        "mean_effective_cluster_n":(float(np.nanmean(eff[valid])) if valid.any() else None),
        "max_inverse_observation_weight":(float(np.nanmax(maxwt[valid])) if valid.any() else None),
        "mean_abs_slope_error":float(np.mean(np.abs(error))) if valid.any() else None,
        "mean_signed_slope_error":float(np.mean(error)) if valid.any() else None,
        "mean_abs_shift_from_complete":float(np.mean(np.abs(difference))) if valid.any() else None,
        "mnar_endpoint_mean_abs_slope_spread":None,
        "not_identified_mnar_delta":True,
        "no_missingness_corrected_confidence_band":True,
        "no_90percent_calibration":True,
        "release_authorized":False
    }


def evaluate(block,config,support,variance):
    ident(block,config,support,variance)
    X,y,beta,unit_sd=source(block,config,support,variance)
    masks=common_masks(block,config,support,variance,X,y)
    for mechanism in MECHANISMS[1:]:
        if not native_refusal(X,y,masks[mechanism],config):
            raise AssertionError("R83 stable public regression did not refuse missing gaze")
    full=pointwise_diagnostic(X,y,masks["complete"],config,beta)
    original=np.array(full["pointwise_slope"],float)
    if full["grid_refused_count"]!=0:
        raise ValueError("R83 original complete full-grid support unexpectedly refused")
    records=[observations_record(block,config,support,variance,"complete","COMPLETE",0.,
                                 X,y,beta,masks["complete"],original)]
    records.append(observations_record(
        block,config,support,variance,"MCAR","MCAR_known",0.,
        X,y,beta,masks["MCAR"],original))
    for mechanism in ("MAR","MNAR"):
        for delta in DELTA:
            records.append(observations_record(
                block,config,support,variance,mechanism,
                mechanism+"_sensitivity",delta,
                X,y,beta,masks[mechanism],original))
    records.append(observations_record(
        block,config,support,variance,"MNAR","MNAR_oracle",1.1,
        X,y,beta,masks["MNAR"],original,oracle=True))
    endpoints=[q for q in records if q["method"]=="MNAR_sensitivity"
               and q["assumed_mnar_delta"] in (-1.1,1.1)]
    assert len(endpoints)==2 and len(records)==RECORDS_PER_SOURCE
    a=np.array([[np.nan if z is None else z for z in line]
                for line in endpoints[0]["pointwise_slopes"]])
    b=np.array([[np.nan if z is None else z for z in line]
                for line in endpoints[1]["pointwise_slopes"]])
    same=np.isfinite(a)&np.isfinite(b)
    spread=float(np.mean(np.abs(a[same]-b[same]))) if same.any() else None
    for q in records:
        if q["method"] in ("MNAR_sensitivity","MNAR_oracle"):
            q["mnar_endpoint_mean_abs_slope_spread"]=spread
    return records


def summary(rows):
    def expected(b,c,s,v):
        return ([(b,c,s,v,"complete","COMPLETE",0.),
                 (b,c,s,v,"MCAR","MCAR_known",0.)]
                +[(b,c,s,v,m,m+"_sensitivity",float(d)) for m in ("MAR","MNAR")
                  for d in DELTA]
                +[(b,c,s,v,"MNAR","MNAR_oracle",1.1)])
    needed={key for b in range(BLOCKS) for c in CONFIGS for s in SUPPORT
            for v in VARIANCES for key in expected(b,c,s,v)}
    ids=[(z["block"],z["config"],z["support"],z["variance"],
          z["observation_mechanism"],z["method"],z["assumed_mnar_delta"])
         for z in rows]
    if len(rows)!=N_RECORDS or len(set(ids))!=N_RECORDS or set(ids)!=needed:
        raise ValueError("R83 independent source/delta/method evaluations missing or duplicated")
    results={}
    for c in CONFIGS:
        results[c]={}
        for s in SUPPORT:
            results[c][s]={}
            for v in VARIANCES:
                results[c][s][v]={}
                for method in METHODS:
                    delta_values=DELTA if method in ("MAR_sensitivity","MNAR_sensitivity") else ((1.1,) if method=="MNAR_oracle" else (0.,))
                    results[c][s][v][method]={}
                    for delta in delta_values:
                        sub=[z for z in rows if z["config"]==c and z["support"]==s
                             and z["variance"]==v and z["method"]==method
                             and z["assumed_mnar_delta"]==delta]
                        if len(sub)!=BLOCKS:
                            raise ValueError("R83 independent source denominator unequal 32")
                        for z in sub:
                            b=z["block"]
                            if (z["study"]!=STUDY or z["source_seed"]!=seed(b,c,s,v,"source")
                                or z["observation_seed"]!=seed(b,c,s,v,"mask")
                                or z["release_authorized"] is not False
                                or z["not_identified_mnar_delta"] is not True
                                or z["no_missingness_corrected_confidence_band"] is not True
                                or z["no_90percent_calibration"] is not True
                                or z["grid_refused_count"]+z["grid_estimable_count"]!=62):
                                raise ValueError("R83 original source or no-release provenance mismatch")
                        def avg(field):
                            observed=[z[field] for z in sub if z[field] is not None]
                            return float(np.mean(observed)) if observed else None
                        results[c][s][v][method][str(float(delta))]={
                            "new_independent_primitive_blocks":BLOCKS,
                            "mean_observed_fraction":avg("observed_fraction"),
                            "mean_refused_grid":avg("grid_refused_count"),
                            "mean_abs_slope_error":avg("mean_abs_slope_error"),
                            "mean_abs_shift_from_complete":avg("mean_abs_shift_from_complete"),
                            "mean_effective_cluster_n":avg("mean_effective_cluster_n"),
                            "mean_max_observation_weight":avg("max_inverse_observation_weight"),
                            "mean_MNAR_endpoint_slope_spread":avg("mnar_endpoint_mean_abs_slope_spread"),
                            "native_nan_refusal_sources":sum(z["native_nan_refusal"] for z in sub)}
    return {"study":STUDY,"new_source_seed":SOURCE_SEED,"new_mask_seed":OBS_SEED,
            "independent_primitive_blocks_per_cell":BLOCKS,
            "original_complete_source_conditions":N_SOURCES,
            "paired_original_observation_masks":N_SOURCES*len(MECHANISMS),
            "pointwise_diagnostic_records":N_RECORDS,
            "sensitivity_delta_grid":list(DELTA),
            "oracle_unavailable_in_observed_data":True,
            "observation_model_identified":False,
            "confidence_band_calibration":False,
            "release_authorized":False,
            "results":results}


def shard(out,start,stop):
    if (start,stop) not in SHARDS:raise ValueError("R83 shard not pre-registered")
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
        p=parts/f"w3-r83-original-sensitivity-shard-{a}"
        raw=(p/"cases.json").read_bytes()
        manifest=json.loads((p/"manifest.json").read_text())
        if (manifest["study"]!=STUDY or manifest["start"]!=a or manifest["stop"]!=b
            or manifest["cases"]!=(b-a)*len(CONFIGS)*len(SUPPORT)*len(VARIANCES)*RECORDS_PER_SOURCE
            or manifest["sha256"]!=sha256(raw).hexdigest()):
            raise ValueError("R83 original source part SHA256/identity mismatch")
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
    else:raise SystemExit("R83 require --stop with --start")


if __name__=="__main__":
    main()
