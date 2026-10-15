"""R27 analytic Gaussian REML information and finite-innovation score audit.

Frozen ORIGINAL R26 native observation designs: blocks 0,15; n24,n96;
ordinary independent/dependent covariance; matched covariance family.
Uses source-known component variances only in this ORACLE INFORMATION audit.
128 independent conditional Gaussian innovations per frozen design.
No estimator selection, coefficient coverage or release qualification.
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

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts import run_w3_r17_fresh_feasibility as source
from scripts import run_w3_r26_independent_reml_recovery as r26
from scripts.w3_r20_estimated_working_target import (
    COMPONENTS,_kernels,observed_weighted_rows)

STUDY="W3_R27_GAUSSIAN_REML_VARIANCE_COMPONENT_INFORMATION_AUDIT"
ORIGINAL_BLOCKS=(0,15)
ORIGINAL_N=(24,96)
ORIGINAL_SUPPORT=("ordinary_independent","ordinary_dependent")
CONDITIONAL_DRAWS=128
DRAW_SEED=202610153727
EXPECTED=len(ORIGINAL_BLOCKS)*len(ORIGINAL_N)*len(ORIGINAL_SUPPORT)
THETA=np.asarray([r26.TRUE_COMPONENTS[k] for k in COMPONENTS],float)


def information_for_original_design(block,n,support):
    """Independent blockwise Fisher information, avoiding dense N×N matrices.

    Expected REML information for variance components:
       I_jk=.5 tr(P K_j P K_k)
    where P=V^-1 - V^-1 Z (Z'V^-1Z)^-1 Z'V^-1,
    and K_j are component covariance derivative blocks.
    """
    family=("predictor_scaled_slope" if support.endswith("_dependent")
            else "shared_slope")
    case=source.fresh_source(
        block,support,n=n,master_seed=r26.SOURCE_SEED,
        n_blocks=r26.BLOCKS,max_n=max(r26.SIZES))
    X,y,w,ids,t,tr,x=observed_weighted_rows(
        (None,case[1],case[2],case[3],case[4],None),r26.BASIS)
    Z=X*np.sqrt(w)[:,None]
    design=[]
    G=np.zeros((X.shape[1],X.shape[1]))
    M=[np.zeros_like(G) for _ in COMPONENTS]
    t0=np.zeros((len(COMPONENTS),len(COMPONENTS)))
    t1=np.zeros_like(t0)
    trace_first=np.zeros(len(COMPONENTS))
    participants=np.unique(ids)
    for who in participants:
        ix=np.flatnonzero(ids==who)
        Zi=Z[ix]
        kernels=_kernels(t[ix],tr[ix],x[ix],w[ix],family)
        V=sum(float(theta)*k for theta,k in zip(THETA,kernels))
        fac=cho_factor((V+V.T)*.5,lower=True,check_finite=False)
        Vinv=cho_solve(fac,np.eye(len(ix)),check_finite=False)
        U=Vinv@Zi
        G+=Zi.T@U
        for k,K in enumerate(kernels):
            M[k]+=U.T@K@U
            trace_first[k]+=float(np.sum(Vinv*K))
        VK=[Vinv@K for K in kernels]
        for j in range(len(COMPONENTS)):
            for k in range(len(COMPONENTS)):
                t0[j,k]+=float(np.trace(VK[j]@VK[k]))
                # T1 needs final GLS bread B, accumulated below.
        design.append((ix,Zi,kernels,fac,U,V,Vinv,VK))
    B=np.linalg.solve(G,np.eye(len(G)))
    t1[:]=0.
    for ix,Zi,Ks,fac,U,V,Vinv,VK in design:
        for j in range(len(COMPONENTS)):
            for k in range(len(COMPONENTS)):
                t1[j,k]+=float(np.trace(B@(U.T@Ks[j]@Vinv@Ks[k]@U)))
    t2=np.asarray([[float(np.trace(B@M[j]@B@M[k]))
                   for k in range(len(COMPONENTS))]
                  for j in range(len(COMPONENTS))])
    info=.5*(t0-t1-t1.T+t2)
    info=(info+info.T)*.5
    info_log=(THETA[:,None]*info)*THETA[None,:]
    eig=np.linalg.eigvalsh(info_log)
    if not np.isfinite(eig).all() or eig[0]<=0:
        raise ValueError("restricted-likelihood population component Fisher information not SPD")
    inv=np.linalg.solve(info_log,np.eye(len(COMPONENTS)))
    relative_se=np.sqrt(np.diag(inv))
    condition=float(eig[-1]/eig[0])
    corr=info_log/np.sqrt(np.outer(np.diag(info_log),np.diag(info_log)))
    expected_score_variance=np.diag(info_log)
    observed_source_beta=np.linalg.solve(G,sum(
        (Zi.T@cho_solve(fac,y[ix]*np.sqrt(w[ix]),check_finite=False)
         for ix,Zi,Ks,fac,U,V,Vinv,VK in design),start=np.zeros(X.shape[1])))
    # Diagnostic score observed only; source truth is used in this oracle
    # reference evaluation, never a public covariance estimator.
    return {
        "block":block,"n":n,"support":support,"family":family,
        "design":design,"B":B,"M":M,"G":G,"theta":THETA,
        "trace_first":trace_first,"info_theta":info,
        "info_log":info_log,
        "expected_score_variance":expected_score_variance,
        "relative_local_component_SE":relative_se,
        "information_eigen_condition":condition,
        "information_correlation":corr,
        "observed_source_gls_beta":observed_source_beta,
        "original_source_design_only":True,
    }


def score_for_gaussian_innovations(reference,innovations):
    """Analytic REML log-variance score at the generating covariance."""
    designs=reference["design"]
    B=reference["B"]
    M=reference["M"]
    trace_first=reference["trace_first"]
    g=np.zeros(len(B))
    split=[]
    offset=0
    for ix,Zi,Ks,fac,U,V,Vinv,VK in designs:
        eps=innovations[offset:offset+len(ix)]
        offset+=len(ix)
        g+=U.T@eps
        split.append(eps)
    if offset!=len(innovations):
        raise ValueError("innovation vector does not match fixed source design")
    beta=B@g
    quad=np.zeros(len(COMPONENTS))
    for (ix,Zi,Ks,fac,U,V,Vinv,VK),eps in zip(designs,split):
        projected=cho_solve(fac,eps-Zi@beta,check_finite=False)
        for k,K in enumerate(Ks):
            quad[k]+=float(projected@K@projected)
    tr=np.asarray([trace_first[k]-np.trace(B@M[k])
                   for k in range(len(COMPONENTS))])
    return .5*(quad-tr)*reference["theta"]


def simulate(reference):
    rng=np.random.default_rng(
        DRAW_SEED+reference["block"]*113+reference["n"]*17+
        (1 if reference["support"].endswith("_dependent") else 0)*507)
    roots=[np.linalg.cholesky(item[5]) for item in reference["design"]]
    scores=[]
    for _ in range(CONDITIONAL_DRAWS):
        innovations=np.concatenate([
            L@rng.standard_normal(len(L)) for L in roots])
        scores.append(score_for_gaussian_innovations(reference,innovations))
    scores=np.stack(scores)
    empirical=np.cov(scores,rowvar=False,ddof=1)
    information=reference["info_log"]
    ratios=np.diag(empirical)/np.diag(information)
    if not np.isfinite(ratios).all():
        raise ValueError("nonfinite empirical score information agreement")
    return {
        "original_source_block":reference["block"],
        "participants":reference["n"],
        "source_support":reference["support"],
        "matched_family":reference["family"],
        "conditional_gaussian_innovations":CONDITIONAL_DRAWS,
        "local_relative_component_standard_errors":dict(zip(
            COMPONENTS,map(float,reference["relative_local_component_SE"]))),
        "information_eigen_condition":reference["information_eigen_condition"],
        "max_abs_information_correlation":float(
            np.max(np.abs(reference["information_correlation"]-np.eye(len(COMPONENTS))))),
        "gaussian_score_mean":dict(zip(COMPONENTS,map(float,scores.mean(axis=0)))),
        "score_variance_over_expected_information":dict(zip(COMPONENTS,map(float,ratios))),
        "expected_score_information_diagonal":dict(zip(COMPONENTS,map(
            float,np.diag(reference["info_log"])))),
        "smallest_log_information_eigenvalue":float(
            np.linalg.eigvalsh(reference["info_log"])[0]),
        "sampled_score_covariance_is_not_new_source_blocks":True,
        "no_nuisance_reml_fit_coverage_calculated":True,
        "release_authorized":False,
    }


def summarize(rows):
    return {"study":STUDY,
        "original_R26_source_seed":r26.SOURCE_SEED,
        "frozen_original_source_blocks":ORIGINAL_BLOCKS,
        "frozen_participant_sizes":ORIGINAL_N,
        "frozen_supports":ORIGINAL_SUPPORT,
        "completed_fixed_designs":len(rows),
        "prespecified_fixed_designs":EXPECTED,
        "conditional_draws_per_fixed_design":CONDITIONAL_DRAWS,
        "new_independent_source_designs":0,
        "conditional_innovation_vectors":len(rows)*CONDITIONAL_DRAWS,
        "all_design_information_spd":all(
             x["smallest_log_information_eigenvalue"]>0 for x in rows),
        "no_interval_coverage_computed":True,
        "gaussian_assumption_reference_only":True,
        "estimated_working_covariance_inference_qualified":False,
        "simultaneous_bands_qualified":False,
        "release_authorized":False,
        "cells":rows}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    rows=[simulate(information_for_original_design(b,n,s))
          for b in ORIGINAL_BLOCKS for n in ORIGINAL_N for s in ORIGINAL_SUPPORT]
    summary=summarize(rows)
    for name,obj in (("summary.json",summary),("case-ledger.json",rows)):
        (args.out/name).write_text(json.dumps(obj,sort_keys=True,indent=2)+"\n")
    (args.out/"source-commit.txt").write_text(os.getenv("GITHUB_SHA","unverified-local")+"\n")
    names=("summary.json","case-ledger.json","source-commit.txt")
    (args.out/"SHA256SUMS").write_text("".join(
        hashlib.sha256((args.out/name).read_bytes()).hexdigest()+"  "+name+"\n"
        for name in names))
    print("R27 REML INFORMATION AUDIT:",json.dumps(
        {k:v for k,v in summary.items() if k!="cells"},sort_keys=True))
    for x in rows:
        print("R27 FISHER CELL:",json.dumps(x,sort_keys=True))
    if summary["completed_fixed_designs"]!=EXPECTED:
        raise SystemExit("R27 fixed-source Fisher information audit incomplete")


if __name__=="__main__":
    main()
