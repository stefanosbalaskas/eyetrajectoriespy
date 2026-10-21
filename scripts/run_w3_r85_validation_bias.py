"""W3 R85 prospectively frozen observation-process diagnostic (NOT a confidence-band estimator).

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

STUDY="W3_R85_VALIDATION_ASCERTAINMENT_BIAS"
SOURCE_SEED=202610218580
OBS_SEED=202610218581
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
RECOVERY_SEED=202610218582
LOSS_MECHANISMS=("MAR","MNAR")
STRATEGIES=("independent_known","recorded_naive","recorded_correct","latent_naive","latent_oracle")
RECOVERY_LAWS=("independent","recorded","latent")
RECORDS_PER_SOURCE=10
N_RECORDS=N_SOURCES*RECORDS_PER_SOURCE
BASE_RECOVERY=.25


def info(config):
    if config=="curve_standard":
        return 72,1,"curve"
    if config=="participant_standard":
        return 36,3,"participant"
    raise ValueError("R85 unknown native independent-unit configuration")


def ident(block,config,support,variance):
    if (type(block) is not int or block not in range(BLOCKS)
        or config not in CONFIGS or support not in SUPPORT or variance not in VARIANCES):
        raise ValueError("R85 original source identity invalid")


def seed(block,config,support,variance,domain):
    ident(block,config,support,variance)
    ci=CONFIGS.index(config)
    if domain=="source":
        return SOURCE_SEED+100003*block+10007*ci
    if domain=="mask":
        return (OBS_SEED+1000003*block+10007*ci
                +739*SUPPORT.index(support)+97*VARIANCES.index(variance))
    raise ValueError("R85 unknown frozen random stream")


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
        raise ValueError("R85 unknown loss mechanism")
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
    raise AssertionError("R85 public fit silently accepted missing gaze")



def logit_base(X,y):
    n,trials,_,_=y.shape
    trial=np.arange(trials)[None,:,None,None]
    return np.broadcast_to(-2.2+np.abs(X[:,1,None,None,None])/4.
                           +.7*T[None,None,:,None]+.2*trial,y.shape)




def rescue_uniforms(block,config,support,variance,y):
    ident(block,config,support,variance)
    key=(RECOVERY_SEED+1000003*block+10007*CONFIGS.index(config)
         +739*SUPPORT.index(support)+97*VARIANCES.index(variance))
    return np.random.default_rng(key).random(y.shape),key


def recovery_probabilities(X,Y,kind):
    if kind=="independent":
        return np.full(Y.shape,BASE_RECOVERY)
    logit=np.log(BASE_RECOVERY/(1-BASE_RECOVERY))
    offset=logit+.7*np.abs(X[:,1,None,None,None])/4.+.7*T[None,None,:,None]
    if kind=="recorded":
        return np.broadcast_to(1/(1+np.exp(-offset)),Y.shape).copy()
    if kind=="latent":
        beta=truth_coefficients()
        true_mean=beta[0][None]+X[:,1,None,None]*beta[1][None]
        eta=offset-.7*np.abs(X[:,1,None,None,None])/4.-.7*T[None,None,:,None]
        eta=eta+1.0*np.tanh((Y-true_mean[:,None])/.08)
        return 1/(1+np.exp(-eta))
    raise ValueError("R85 invalid validation process")


def original_visible_pilot(X,Y,missing):
    pilot=np.full((31,2,2),np.nan)
    valid=np.zeros((31,2),bool)
    units=np.zeros((31,2),int)
    for t in range(31):
        for d in range(2):
            idx,tr=np.nonzero(~missing[:,:,t,d])
            units[t,d]=len(np.unique(idx))
            if units[t,d]<MIN_UNITS:
                continue
            cov=X[idx]
            if np.linalg.matrix_rank(cov)<2:
                continue
            pilot[t,d]=np.linalg.lstsq(cov,Y[idx,tr,t,d],rcond=None)[0]
            valid[t,d]=True
    return pilot,valid,units


def weighted_delta(X,Y,missing,recovered,pilot,pilot_valid,assumed_recovery):
    observed=~missing
    included=(observed|recovered)&pilot_valid[None,None,:,:]
    rows,trials,times,dims=np.nonzero(included)
    if not len(rows) or not (recovered&pilot_valid[None,None,:,:]).any():
        return None,False,None,None,0,False
    y=Y[rows,trials,times,dims]
    fitted=pilot[times,dims,0]+pilot[times,dims,1]*X[rows,1]
    h=np.tanh((y-fitted)/.08)
    off=-2.2+np.abs(X[rows,1])/4.+.7*T[times]+.2*trials
    m=missing[rows,trials,times,dims]
    prop=assumed_recovery[rows,trials,times,dims]
    if np.any(~np.isfinite(prop)) or np.any(prop[m]<=0):
        return None,False,None,None,int(len(rows)),False
    weights=np.ones(len(rows),float)
    weights[m]=1./prop[m]
    def calc(delta):
        eta=np.clip(off+delta*h,-45.,45.)
        p=1./(1+np.exp(-eta))
        score=float(np.dot(weights*h,m.astype(float)-p))
        info=float(np.dot(weights*h*h,p*(1.-p)))
        return score,info
    left,right=-4.,4.
    lscore,linfo=calc(left);rscore,rinfo=calc(right)
    if (not np.isfinite(lscore) or not np.isfinite(rscore)
        or not np.isfinite(linfo) or not np.isfinite(rinfo)
        or lscore<0 or rscore>0):
        return None,False,None,None,int(len(rows)),True
    delta=0.
    for i in range(80):
        delta=(left+right)/2.
        score,info=calc(delta)
        if not np.isfinite(score) or not np.isfinite(info) or info<=1e-12:
            return None,False,None,None,int(len(rows)),False
        if abs(score)<1e-9 or right-left<1e-12:break
        if score>0:left=delta
        else:right=delta
    score,info=calc(delta)
    return float(delta),True,float(score),float(info),int(len(rows)),False


def evaluate(block,config,support,variance):
    X,Y,beta,scale=source(block,config,support,variance)
    missing=common_masks(block,config,support,variance,X,Y)
    uniforms,recovery_seed=rescue_uniforms(block,config,support,variance,Y)
    probs={law:recovery_probabilities(X,Y,law) for law in RECOVERY_LAWS}
    rows=[]
    for mechanism in LOSS_MECHANISMS:
        mask=missing[mechanism]
        if not native_refusal(X,Y,mask,config):
            raise AssertionError("R85 stable regression did not reject original incomplete gaze")
        pilot,pilot_valid,unit_counts=original_visible_pilot(X,Y,mask)
        validations={law:mask&(uniforms<probs[law]) for law in RECOVERY_LAWS}
        for strategy in STRATEGIES:
            kind=("independent" if strategy=="independent_known" else
                  "recorded" if strategy.startswith("recorded") else "latent")
            recovered=validations[kind]
            if strategy.endswith("naive"):
                assumed=np.full(Y.shape,BASE_RECOVERY)
            else:
                assumed=probs[kind]
            oracle=(strategy=="latent_oracle")
            est,converged,score,info,count,bound=weighted_delta(
                X,Y,mask,recovered,pilot,pilot_valid,assumed)
            truth=0. if mechanism=="MAR" else 1.1
            rows.append({
                "study":STUDY,"block":block,"config":config,"support":support,
                "variance":variance,"mechanism":mechanism,"strategy":strategy,
                "validation_law":kind,
                "true_first_stage_delta_simulator_only":truth,
                "source_seed":seed(block,config,support,variance,"source"),
                "original_mask_seed":seed(block,config,support,variance,"mask"),
                "validation_uniform_seed":recovery_seed,
                "source_X_digest":digest(X),"source_Y_digest":digest(Y),
                "original_missing_mask_digest":mask_digest(mask),
                "original_visible_only_pilot_digest":digest(np.nan_to_num(pilot,nan=0.)),
                "validation_mask_digest":mask_digest(recovered),
                "validation_probability_digest":digest(probs[kind]),
                "n_original_missing":int(mask.sum()),
                "n_recovered":int(recovered.sum()),
                "original_observed_fraction":float(np.mean(~mask)),
                "pilot_refused_grid":int(np.sum(~pilot_valid)),
                "pilot_min_native_units":int(unit_counts.min()),
                "original_public_regression_refused":True,
                "validated_outcomes_not_imputed":True,
                "oracle_validation_propensity_used":oracle,
                "true_mean_only_used_for_latent_oracle_weight":oracle,
                "true_first_stage_delta_not_used_for_fitting":True,
                "no_inference_or_calibration_claim":True,"release_authorized":False,
                "delta_estimate":est,"converged":converged,"weighted_score":score,
                "pseudo_information":info,"included_measured_outcomes":count,
                "boundary_refused":bound,
                "delta_error_signed":None if est is None else float(est-truth),
                "delta_error_absolute":None if est is None else float(abs(est-truth))
            })
    if len(rows)!=RECORDS_PER_SOURCE:raise AssertionError("R85 strategy denominator mismatch")
    return rows


def summary(rows):
    identity=[(r["block"],r["config"],r["support"],r["variance"],r["mechanism"],r["strategy"]) for r in rows]
    expected={(b,c,s,v,m,k) for b in range(BLOCKS) for c in CONFIGS
              for s in SUPPORT for v in VARIANCES for m in LOSS_MECHANISMS for k in STRATEGIES}
    if len(rows)!=N_RECORDS or len(set(identity))!=N_RECORDS or set(identity)!=expected:
        raise ValueError("R85 original source and strategy denominator missing or duplicated")
    result={}
    for c in CONFIGS:
        result[c]={}
        for s in SUPPORT:
            result[c][s]={}
            for v in VARIANCES:
                result[c][s][v]={}
                for m in LOSS_MECHANISMS:
                    result[c][s][v][m]={}
                    for k in STRATEGIES:
                        q=[z for z in rows if z["config"]==c and z["support"]==s and z["variance"]==v
                           and z["mechanism"]==m and z["strategy"]==k]
                        if len(q)!=BLOCKS or len({z["block"] for z in q})!=BLOCKS:
                            raise ValueError("R85 lost independent source primitive block")
                        for z in q:
                            if (z["study"]!=STUDY or z["release_authorized"] or
                                z["no_inference_or_calibration_claim"] is not True or
                                z["true_first_stage_delta_not_used_for_fitting"] is not True or
                                z["source_seed"]!=seed(z["block"],c,s,v,"source") or
                                z["original_mask_seed"]!=seed(z["block"],c,s,v,"mask") or
                                z["oracle_validation_propensity_used"] is not (k=="latent_oracle")):
                                raise ValueError("R85 frozen experiment provenance or release boundary violated")
                        yes=[z for z in q if z["converged"] and z["delta_estimate"] is not None]
                        def avg(field,data=q):
                            a=[z[field] for z in data if z[field] is not None]
                            return float(np.mean(a)) if a else None
                        result[c][s][v][m][k]={
                            "primitive_blocks":BLOCKS,"converged_sources":len(yes),
                            "mean_recovered":avg("n_recovered"),
                            "mean_original_missing":avg("n_original_missing"),
                            "mean_pilot_refused":avg("pilot_refused_grid"),
                            "mean_estimated_delta":avg("delta_estimate",yes),
                            "mean_signed_delta_error":avg("delta_error_signed",yes),
                            "mean_abs_delta_error":avg("delta_error_absolute",yes),
                            "mean_pseudo_information":avg("pseudo_information",yes),
                            "boundary_refused_sources":sum(z["boundary_refused"] for z in q)}
    return {"study":STUDY,"new_source_seed":SOURCE_SEED,
            "original_mask_seed":OBS_SEED,"new_validation_seed":RECOVERY_SEED,
            "primitive_independent_blocks_per_cell":BLOCKS,
            "complete_source_conditions":N_SOURCES,
            "original_MAR_MNAR_masks":N_SOURCES*len(LOSS_MECHANISMS),
            "source_strategy_rows":N_RECORDS,"strategies":list(STRATEGIES),
            "validation_laws":list(RECOVERY_LAWS),
            "nonrandom_validation_can_be_identified_from_original_missing_gaze":False,
            "simulator_only_validation_oracle_is_deployable":False,
            "confidence_bands_evaluated":False,"release_authorized":False,"results":result}


def shard(out,start,stop):
    if (start,stop) not in SHARDS:raise ValueError("R85 shard not prespecified")
    out.mkdir(parents=True,exist_ok=True)
    records=[r for b in range(start,stop) for c in CONFIGS for s in SUPPORT for v in VARIANCES
             for r in evaluate(b,c,s,v)]
    body=(json.dumps(records,sort_keys=True,allow_nan=False)+"\n").encode()
    (out/"cases.json").write_bytes(body)
    meta={"study":STUDY,"start":start,"stop":stop,"cases":len(records),
          "sha256":sha256(body).hexdigest(),"checkout":os.environ.get("GITHUB_SHA","local-unverified")}
    (out/"manifest.json").write_text(json.dumps(meta,sort_keys=True)+"\n")


def aggregate(out,parts):
    all_records=[]
    for a,b in SHARDS:
        p=parts/f"w3-r85-original-validation-shard-{a}"
        raw=(p/"cases.json").read_bytes()
        meta=json.loads((p/"manifest.json").read_text())
        if (meta["study"]!=STUDY or meta["start"]!=a or meta["stop"]!=b or
            meta["cases"]!=(b-a)*len(CONFIGS)*len(SUPPORT)*len(VARIANCES)*RECORDS_PER_SOURCE or
            meta["sha256"]!=sha256(raw).hexdigest()):
            raise ValueError("R85 original source SHA256/shard identity mismatch")
        all_records.extend(json.loads(raw))
    report=summary(all_records)
    out.mkdir(parents=True,exist_ok=True)
    checkout=os.environ.get("GITHUB_SHA","local-unverified")
    (out/"evidence.json").write_text(json.dumps(
        {"original_checkout":checkout,"source_evaluations":all_records,"aggregate":report},
        sort_keys=True,allow_nan=False)+"\n")
    (out/"source-commit.txt").write_text(checkout+"\n")
    (out/"SHA256SUMS").write_text("".join(
        sha256((out/name).read_bytes()).hexdigest()+"  "+name+"\n"
        for name in ("evidence.json","source-commit.txt")))
    print(json.dumps(report,sort_keys=True,allow_nan=False))


def main():
    p=argparse.ArgumentParser()
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument("--start",type=int)
    g.add_argument("--merge-parts",type=Path)
    p.add_argument("--stop",type=int)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    if a.merge_parts is not None:aggregate(a.out,a.merge_parts)
    elif a.stop is not None:shard(a.out,a.start,a.stop)
    else:raise SystemExit("R85 must provide --start and --stop together")

if __name__=="__main__":
    main()
