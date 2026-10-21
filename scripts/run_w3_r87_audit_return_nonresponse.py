"""W3 R87 prospectively frozen observation-process diagnostic (NOT a confidence-band estimator).

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

STUDY="W3_R87_AUDIT_COMPLETION_NONRESPONSE_FALSIFICATION"
SOURCE_SEED=202610218780
OBS_SEED=202610218781
BLOCKS=32
T=np.linspace(0.,1.,31)
DIMS=("x","y")
CONFIGS=("curve_standard","participant_standard")
SUPPORT=("two_anchors",)
VARIANCES=("predictor_heteroskedastic",)
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
RECOVERY_SEED=202610218782
LOSS_MECHANISMS=("MAR","MNAR")
STRATEGIES=("assignment_only","recorded_propensity","outcome_oracle")
RECOVERY_LAWS=("latent",)
AUDIT_LEVELS=(.25,.5)
AUDIT_SEED=202610218783
RECORDS_PER_SOURCE=36
N_RECORDS=N_SOURCES*RECORDS_PER_SOURCE
BASE_RECOVERY=.25


def info(config):
    if config=="curve_standard":
        return 72,1,"curve"
    if config=="participant_standard":
        return 36,3,"participant"
    raise ValueError("R87 unknown native independent-unit configuration")


def ident(block,config,support,variance):
    if (type(block) is not int or block not in range(BLOCKS)
        or config not in CONFIGS or support not in SUPPORT or variance not in VARIANCES):
        raise ValueError("R87 original source identity invalid")


def seed(block,config,support,variance,domain):
    ident(block,config,support,variance)
    ci=CONFIGS.index(config)
    if domain=="source":
        return SOURCE_SEED+100003*block+10007*ci
    if domain=="mask":
        return (OBS_SEED+1000003*block+10007*ci
                +739*SUPPORT.index(support)+97*VARIANCES.index(variance))
    raise ValueError("R87 unknown frozen random stream")


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
        raise ValueError("R87 unknown loss mechanism")
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
    raise AssertionError("R87 public fit silently accepted missing gaze")



def logit_base(X,y):
    n,trials,_,_=y.shape
    trial=np.arange(trials)[None,:,None,None]
    return np.broadcast_to(-2.2+np.abs(X[:,1,None,None,None])/4.
                           +.7*T[None,None,:,None]+.2*trial,y.shape)





def uniform_pair(block,config,support,variance,shape):
    ident(block,config,support,variance)
    offset=1000003*block+10007*CONFIGS.index(config)+739*SUPPORT.index(support)+97*VARIANCES.index(variance)
    return (np.random.default_rng(RECOVERY_SEED+offset).random(shape),
            np.random.default_rng(AUDIT_SEED+offset).random(shape),
            RECOVERY_SEED+offset,AUDIT_SEED+offset)


def original_visible_pilot(X,Y,missing):
    pilot=np.full((31,2,2),np.nan)
    good=np.zeros((31,2),bool)
    units=np.zeros((31,2),int)
    for t in range(31):
        for d in range(2):
            uid,trial=np.nonzero(~missing[:,:,t,d])
            units[t,d]=len(np.unique(uid))
            if units[t,d]<MIN_UNITS:continue
            regress=X[uid]
            if np.linalg.matrix_rank(regress)<2:continue
            pilot[t,d]=np.linalg.lstsq(regress,Y[uid,trial,t,d],rcond=None)[0]
            good[t,d]=True
    return pilot,good,units


def actual_recovery_prob(X,Y):
    beta=truth_coefficients()
    mu=beta[0][None]+X[:,1,None,None]*beta[1][None]
    logits=np.log(.25/.75)+np.tanh((Y-mu[:,None])/.08)
    return 1/(1+np.exp(-logits))


def estimate_recovery_selection(X,Y,missing,initial_success,audited,pilot,allowed,q):
    """Two-parameter model; missing Y used ONLY when recovered in stages 2 or 3."""
    if q==0: return None,None,False,0,None,None,False
    kept=(initial_success|audited)&allowed[None,None,:,:]
    uid,tr,t,d=np.nonzero(kept)
    if len(uid)<20 or not (audited&allowed[None,None,:,:]).any():
        return None,None,False,len(uid),None,None,False
    response=Y[uid,tr,t,d]
    mu=pilot[t,d,0]+pilot[t,d,1]*X[uid,1]
    h=np.tanh((response-mu)/.08)
    mat=np.column_stack((np.ones(len(uid)),h))
    label=initial_success[uid,tr,t,d].astype(float)
    weights=np.where(label>0,1.,1./q)
    param=np.array([np.log(.25/.75),0.],float)
    converged=False
    for iteration in range(45):
        logit=np.clip(mat@param,-45,45)
        p=1/(1+np.exp(-logit))
        score=mat.T@(weights*(label-p))
        fisher=mat.T@((weights*p*(1-p))[:,None]*mat)
        if not np.isfinite(score).all() or not np.isfinite(fisher).all():
            break
        eigen=np.linalg.eigvalsh(fisher)
        if eigen[0]<=1e-10:break
        if np.max(np.abs(score))<1e-8:
            converged=True
            break
        step=np.linalg.solve(fisher,score)
        nxt=np.clip(param+step,[-8.,-4.],[8.,4.])
        if np.max(np.abs(nxt-param))<1e-11:
            param=nxt
            converged=np.max(np.abs(score))<1e-6
            break
        param=nxt
    z=np.clip(mat@param,-45,45)
    p=1/(1+np.exp(-z))
    score=mat.T@(weights*(label-p))
    fisher=mat.T@((weights*p*(1-p))[:,None]*mat)
    if np.max(np.abs(score))<1e-6 and np.linalg.eigvalsh(fisher)[0]>1e-10:
        converged=True
    bound=bool(abs(param[0])>=7.999999 or abs(param[1])>=3.999999)
    if not converged:return None,None,False,len(uid),float(np.max(np.abs(score))),float(np.linalg.eigvalsh(fisher)[0]),bound
    return float(param[0]),float(param[1]),True,len(uid),float(np.max(np.abs(score))),float(np.linalg.eigvalsh(fisher)[0]),bound


def first_stage_delta(X,Y,missing,newly_measured,pilot,allowed,union_probability):
    used=(~missing|newly_measured)&allowed[None,None,:,:]
    uid,tr,t,d=np.nonzero(used)
    if not len(uid) or not (newly_measured&allowed[None,None,:,:]).any():
        return None,False,None,None,0,False
    response=Y[uid,tr,t,d]
    residual=np.tanh((response-(pilot[t,d,0]+pilot[t,d,1]*X[uid,1]))/.08)
    offset=-2.2+np.abs(X[uid,1])/4+.7*T[t]+.2*tr
    m=missing[uid,tr,t,d]
    pi=union_probability[uid,tr,t,d]
    if not np.isfinite(pi).all() or np.any(pi[m]<=0):return None,False,None,None,len(uid),False
    w=np.ones(len(uid))
    w[m]=1./pi[m]
    def calculate(delta):
        p=1/(1+np.exp(-np.clip(offset+delta*residual,-45,45)))
        return float(np.dot(w*residual,m.astype(float)-p)),float(np.dot(w*residual*residual,p*(1-p)))
    lo,hi=-4.,4.
    if calculate(lo)[0]<0 or calculate(hi)[0]>0:
        return None,False,None,None,len(uid),True
    delta=0.
    for _ in range(80):
        delta=(lo+hi)/2
        score,info=calculate(delta)
        if not np.isfinite(score) or not np.isfinite(info) or info<=1e-12:
            return None,False,None,None,len(uid),False
        if abs(score)<1e-9 or (hi-lo)<1e-12:break
        if score>0:lo=delta
        else:hi=delta
    score,info=calculate(delta)
    return float(delta),True,float(score),float(info),len(uid),False


AUDIT_RETURN_SEED=202610218784
RETURN_LAWS=("complete","recorded","outcome")

def completion_probability(X,Y,pilot,law):
    """Probability assigned audits actually *return* a missing outcome.

    Outcome-selective law is privileged to simulator: observed ordinary
    sensor data cannot identify its unreported outcome dependence.
    """
    if law not in RETURN_LAWS:
        raise ValueError("R87 missing audited-response return law")
    if law=="complete":return np.ones_like(Y)
    n,trials,nt,nd=Y.shape
    x=np.abs(X[:,1,None,None,None])
    idx=np.arange(trials)[None,:,None,None]
    recorded=.8-.1*np.clip(x/4.,0,1)-.1*T[None,None,:,None]-.04*idx
    recorded=np.broadcast_to(np.clip(recorded,.15,.95),Y.shape)
    if law=="recorded":return recorded.copy()
    # Same recorded selection plus an outcome-specific discriminator.
    base=np.log(recorded/(1.-recorded))
    generating_beta=truth_coefficients()
    generating_mu=(generating_beta[0][None]
                   +X[:,1,None,None]*generating_beta[1][None])
    residual=np.tanh((Y-generating_mu[:,None])/.08)
    return 1./(1.+np.exp(-np.clip(base+1.35*residual,-35.,35.)))

def return_uniform(block,config,support,variance,shape):
    ident(block,config,support,variance)
    offset=(1000003*block+10007*CONFIGS.index(config)
            +739*SUPPORT.index(support)+97*VARIANCES.index(variance))
    return (np.random.default_rng(AUDIT_RETURN_SEED+offset).random(shape),
            AUDIT_RETURN_SEED+offset)

def propensity_model(X,Y,missing,initial_success,audit_returned,pilot,allowed,sampling_probability):
    """The same two-logit-parameter source model, with explicit audit nonresponse.

    Audit-returned SECONDARY FAILURE labels receive inverse probability
    weights 1/(assignment probability * audit-response probability).
    Primary secondary successes are all observed, weight 1.
    No unrecovered Y enters a score or a fitted pilot.
    """
    kept=(initial_success|audit_returned)&allowed[None,None,:,:]
    uid,tr,t,d=np.nonzero(kept)
    if len(uid)<20 or not (audit_returned&allowed[None,None,:,:]).any():
        return None,None,False,len(uid),None,None,False
    response=Y[uid,tr,t,d]
    mu=pilot[t,d,0]+pilot[t,d,1]*X[uid,1]
    h=np.tanh((response-mu)/.08)
    mat=np.column_stack((np.ones(len(uid)),h))
    label=initial_success[uid,tr,t,d].astype(float)
    pi=sampling_probability[uid,tr,t,d]
    if (not np.isfinite(pi).all() or np.any(pi<=0) or np.any(pi>1)):
        return None,None,False,len(uid),None,None,True
    weights=np.where(label>0,1.,1./pi)
    param=np.array([np.log(.25/.75),0.],float)
    converged=False
    score=np.zeros(2)
    fisher=np.eye(2)
    for _ in range(45):
        p=1/(1+np.exp(-np.clip(mat@param,-45,45)))
        score=mat.T@(weights*(label-p))
        fisher=mat.T@((weights*p*(1-p))[:,None]*mat)
        if (not np.isfinite(score).all() or not np.isfinite(fisher).all()
            or np.linalg.eigvalsh(fisher)[0]<=1e-10):
            break
        if np.max(np.abs(score))<1e-8:
            converged=True
            break
        step=np.linalg.solve(fisher,score)
        nxt=np.clip(param+step,[-8.,-4.],[8.,4.])
        if np.max(np.abs(nxt-param))<1e-11:
            param=nxt
            converged=np.max(np.abs(score))<1e-6
            break
        param=nxt
    p=1/(1+np.exp(-np.clip(mat@param,-45,45)))
    score=mat.T@(weights*(label-p))
    fisher=mat.T@((weights*p*(1-p))[:,None]*mat)
    eigen=np.linalg.eigvalsh(fisher)
    converged=converged or (np.max(np.abs(score))<1e-6 and eigen[0]>1e-10)
    bound=bool(abs(param[0])>=7.999999 or abs(param[1])>=3.999999)
    if not converged:
        return None,None,False,len(uid),float(np.max(np.abs(score))),float(eigen[0]),bound
    return float(param[0]),float(param[1]),True,len(uid),float(np.max(np.abs(score))),float(eigen[0]),bound

def evaluate(block,config,support,variance):
    """36 prospectively paired rows per NEW synthetic source, no replacement."""
    X,Y,beta,_=source(block,config,support,variance)
    masks=common_masks(block,config,support,variance,X,Y)
    U,V,secondary_seed,audit_seed=uniform_pair(block,config,support,variance,Y.shape)
    W,return_seed=return_uniform(block,config,support,variance,Y.shape)
    true_secondary=actual_recovery_prob(X,Y)
    rows=[]
    for mechanism in LOSS_MECHANISMS:
        loss=masks[mechanism]
        if not native_refusal(X,Y,loss,config):
            raise AssertionError("R87 incomplete trajectory unexpectedly accepted by stable API")
        initial=loss&(U<true_secondary)
        pilot,valid,unit_counts=original_visible_pilot(X,Y,loss)
        for q in AUDIT_LEVELS:
            assigned=loss&(~initial)&(V<q)
            for law in RETURN_LAWS:
                complete=completion_probability(X,Y,pilot,law)
                returned=assigned&(W<complete)
                measured=initial|returned
                if np.any(returned&initial) or np.any(returned&~assigned):
                    raise AssertionError("R87 attempted reuse of already measured sample")
                for strategy in STRATEGIES:
                    if strategy=="assignment_only":
                        # Falsification: an audit assignment is assumed to recover all.
                        candidate_return=np.ones_like(Y)
                    elif strategy=="recorded_propensity":
                        candidate_return=completion_probability(X,Y,pilot,"recorded")
                    elif strategy=="outcome_oracle":
                        candidate_return=complete
                    else:
                        raise AssertionError("unregistered estimator strategy")
                    sampled=q*candidate_return
                    a,g,ok,n,score,info_,bound=propensity_model(
                        X,Y,loss,initial,returned,pilot,valid,sampled)
                    if ok:
                        residual=np.tanh(
                            (Y-(pilot[None,None,:,:,0]
                                +X[:,1,None,None,None]*pilot[None,None,:,:,1]))/.08)
                        p_rec=1/(1+np.exp(-np.clip(a+g*residual,-45,45)))
                        union=p_rec+(1-p_rec)*sampled
                        delta,dc,ds,di,nd,db=first_stage_delta(
                            X,Y,loss,measured,pilot,valid,union)
                    else:
                        delta,dc,ds,di,nd,db=(None,False,None,None,0,False)
                    target=0. if mechanism=="MAR" else 1.1
                    rows.append({
                        "study":STUDY,"block":block,"config":config,
                        "support":support,"variance":variance,
                        "mechanism":mechanism,"audit_fraction":q,
                        "audit_return_law":law,"strategy":strategy,
                        "source_seed":seed(block,config,support,variance,"source"),
                        "mask_seed":seed(block,config,support,variance,"mask"),
                        "secondary_seed":secondary_seed,"audit_seed":audit_seed,
                        "return_seed":return_seed,
                        "original_X_digest":digest(X),"original_Y_digest":digest(Y),
                        "original_missing_digest":mask_digest(loss),
                        "original_pilot_digest":digest(np.nan_to_num(pilot,nan=0.)),
                        "secondary_success_digest":mask_digest(initial),
                        "audit_assigned_digest":mask_digest(assigned),
                        "audit_returned_digest":mask_digest(returned),
                        "union_measured_digest":mask_digest(measured),
                        "return_probability_digest":digest(complete),
                        "original_gaze_missing":int(loss.sum()),
                        "secondary_returned":int(initial.sum()),
                        "audit_assigned":int(assigned.sum()),
                        "audit_returned":int(returned.sum()),
                        "audit_failed_return":int((assigned&~returned).sum()),
                        "valid_original_pilot_grid":int(valid.sum()),
                        "recovery_alpha_fit":a,"recovery_gamma_fit":g,
                        "recovery_fit_converged":ok,"n_recovery_likelihood":n,
                        "recovery_fit_score":score,"recovery_fit_information":info_,
                        "recovery_fit_boundary":bound,
                        "first_stage_delta_fit":delta,
                        "first_stage_delta_converged":dc,
                        "first_stage_delta_signed_error":None if delta is None else delta-target,
                        "first_stage_delta_abs_error":None if delta is None else abs(delta-target),
                        "first_stage_score":ds,"first_stage_information":di,
                        "first_stage_n":nd,"first_stage_boundary_refusal":db,
                        "true_secondary_gamma_source_only":1.,
                        "true_first_stage_delta_source_only":target,
                        "audit_assigned_independently":True,
                        "audit_completion_independent_only_for_complete_law":law=="complete",
                        "unreturned_outcomes_not_used_in_fitted_scores":True,
                        "oracle_propensity_is_non_field_identifiable":strategy=="outcome_oracle",
                        "original_missing_trajectories_rejected":True,
                        "confidence_interval_or_band_validated":False,
                        "release_authorized":False,
                    })
    if len(rows)!=RECORDS_PER_SOURCE:
        raise ValueError("R87 original 36-row source factorial truncated")
    return rows

def summary(rows):
    key=lambda x:(x["block"],x["config"],x["support"],x["variance"],
                  x["mechanism"],x["audit_fraction"],x["audit_return_law"],x["strategy"])
    found=[key(z) for z in rows]
    expected={(b,c,s,v,m,q,r,k) for b in range(BLOCKS) for c in CONFIGS
              for s in SUPPORT for v in VARIANCES for m in LOSS_MECHANISMS
              for q in AUDIT_LEVELS for r in RETURN_LAWS for k in STRATEGIES}
    if len(found)!=N_RECORDS or len(set(found))!=N_RECORDS or set(found)!=expected:
        raise ValueError("R87 source identity/independent denominator mismatch")
    result={}
    for c in CONFIGS:
        result[c]={}
        for m in LOSS_MECHANISMS:
            result[c][m]={}
            for q in AUDIT_LEVELS:
                result[c][m][str(q)]={}
                for law in RETURN_LAWS:
                    result[c][m][str(q)][law]={}
                    for strategy in STRATEGIES:
                        cell=[z for z in rows if z["config"]==c and z["mechanism"]==m
                              and z["audit_fraction"]==q and z["audit_return_law"]==law
                              and z["strategy"]==strategy]
                        if (len(cell)!=BLOCKS or
                            len({z["block"] for z in cell})!=BLOCKS):
                            raise ValueError("R87 source cases improperly counted as independent")
                        for z in cell:
                            if (z["study"]!=STUDY or
                                z["release_authorized"] is not False or
                                z["confidence_interval_or_band_validated"] is not False or
                                z["unreturned_outcomes_not_used_in_fitted_scores"] is not True or
                                z["source_seed"]!=seed(z["block"],c,SUPPORT[0],VARIANCES[0],"source") or
                                z["mask_seed"]!=seed(z["block"],c,SUPPORT[0],VARIANCES[0],"mask")):
                                raise ValueError("R87 source provenance or release gate changed")
                        valid=[z for z in cell if z["first_stage_delta_converged"] and z["first_stage_delta_fit"] is not None]
                        recovery=[z for z in cell if z["recovery_fit_converged"] and z["recovery_gamma_fit"] is not None]
                        def avg(field, vals):
                            numbers=[z[field] for z in vals if z[field] is not None]
                            return float(np.mean(numbers)) if numbers else None
                        result[c][m][str(q)][law][strategy]={
                            "independent_original_source_blocks":BLOCKS,
                            "complete_first_stage_delta_fits":len(valid),
                            "complete_secondary_gamma_fits":len(recovery),
                            "mean_third_stage_audit_assigned":avg("audit_assigned",cell),
                            "mean_third_stage_audit_returned":avg("audit_returned",cell),
                            "mean_audit_failed_returns":avg("audit_failed_return",cell),
                            "mean_fitted_gamma":avg("recovery_gamma_fit",recovery),
                            "mean_fitted_first_stage_delta":avg("first_stage_delta_fit",valid),
                            "mean_first_stage_abs_error":avg("first_stage_delta_abs_error",valid),
                            "source_first_stage_fit_refusals":BLOCKS-len(valid),
                        }
    return {
        "study":STUDY,"new_source_seed":SOURCE_SEED,
        "original_mask_seed":OBS_SEED,"secondary_seed":RECOVERY_SEED,
        "audit_assignment_seed":AUDIT_SEED,"audit_completion_seed":AUDIT_RETURN_SEED,
        "primitive_blocks_per_cell":BLOCKS,
        "complete_synthetic_source_conditions":N_SOURCES,
        "MAR_MNAR_source_masks":N_SOURCES*len(LOSS_MECHANISMS),
        "third_stage_strategy_records":N_RECORDS,
        "audit_assignment_levels":list(AUDIT_LEVELS),
        "audit_completion_laws":list(RETURN_LAWS),
        "selection_model_assumptions":list(STRATEGIES),
        "outcome_oracle_not_a_field_method":True,
        "independent_audit_assignment_not_sufficient_if_return_is_selective":True,
        "no_MNAR_point_identification_or_90pct_band_claim":True,
        "release_authorized":False,"results":result
    }

def shard(out,start,stop):
    if (start,stop) not in SHARDS:
        raise ValueError("R87 original four-block shard outside frozen design")
    out.mkdir(parents=True,exist_ok=True)
    rows=[z for b in range(start,stop) for c in CONFIGS for s in SUPPORT
          for v in VARIANCES for z in evaluate(b,c,s,v)]
    raw=(json.dumps(rows,allow_nan=False,sort_keys=True)+"\n").encode("utf-8")
    (out/"cases.json").write_bytes(raw)
    manifest={"study":STUDY,"start":start,"stop":stop,"source_count":len(rows),
              "source_sha256":sha256(raw).hexdigest(),
              "source_seed":SOURCE_SEED,"observation_seed":OBS_SEED,
              "audit_return_seed":AUDIT_RETURN_SEED,
              "checkout":os.environ.get("GITHUB_SHA","unverified-local")}
    (out/"manifest.json").write_bytes((json.dumps(manifest,sort_keys=True)+"\n").encode())

def aggregate(out,parts):
    shards=list(parts.glob("*/manifest.json"))
    if len(shards)!=len(SHARDS):
        raise ValueError("R87 missing original source shards")
    rows=[]
    seen=set()
    checkout=os.environ.get("GITHUB_SHA","unverified-local")
    for f in shards:
        m=json.loads(f.read_bytes())
        identity=(m["start"],m["stop"])
        if (identity not in SHARDS or identity in seen or m["study"]!=STUDY
            or m["source_seed"]!=SOURCE_SEED or m["observation_seed"]!=OBS_SEED
            or m["audit_return_seed"]!=AUDIT_RETURN_SEED or m["checkout"]!=checkout):
            raise ValueError("R87 mixed original source checkpoint or duplicate shard")
        seen.add(identity)
        raw=(f.parent/"cases.json").read_bytes()
        if sha256(raw).hexdigest()!=m["source_sha256"]:
            raise ValueError("R87 original source SHA256 mismatch")
        part=json.loads(raw)
        if len(part)!=(identity[1]-identity[0])*len(CONFIGS)*len(SUPPORT)*len(VARIANCES)*RECORDS_PER_SOURCE:
            raise ValueError("R87 truncated source shard")
        rows.extend(part)
    out.mkdir(parents=True,exist_ok=True)
    report=summary(rows)
    (out/"cases.json").write_bytes((json.dumps(rows,allow_nan=False,sort_keys=True)+"\n").encode())
    (out/"summary.json").write_bytes((json.dumps(report,allow_nan=False,sort_keys=True,indent=2)+"\n").encode())
    (out/"source-commit.txt").write_bytes((checkout+"\n").encode())
    (out/"SHA256SUMS").write_bytes("".join(
        sha256((out/name).read_bytes()).hexdigest()+"  "+name+"\n"
        for name in ("cases.json","summary.json","source-commit.txt")
    ).encode())
    print(json.dumps(report,sort_keys=True))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True,type=Path)
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument("--start",type=int)
    g.add_argument("--merge-parts",type=Path)
    p.add_argument("--stop",type=int)
    a=p.parse_args()
    if a.merge_parts is not None:aggregate(a.out,a.merge_parts)
    elif a.stop is not None:shard(a.out,a.start,a.stop)
    else:raise SystemExit("R87 --start requires --stop")

if __name__=="__main__": main()
