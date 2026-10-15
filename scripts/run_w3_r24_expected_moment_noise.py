"""R24 research-only population moment versus finite-Gaussian-innovation study.

Eight frozen source-design configurations built from TWO original generating
blocks (0,7) of R23, participant sizes n24/n96, and two *matching* nuisance
families. Each design has 128 independently generated conditional innovation
vectors. Those 1024 conditional draws are NOT independent source-design
replications. No pointwise or simultaneous confidence-interval coverage.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np
from scipy.optimize import nnls
from scipy.stats import norm

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts import run_w3_r17_fresh_feasibility as source
from scripts import run_w3_r23_estimated_target_identifiability as r23
from scripts.w3_r20_estimated_working_target import (
    COMPONENTS,_kernels,observed_weighted_rows,estimate_feasible_working_target)

STUDY="W3_R24_ORIGINAL_DESIGN_POPULATION_MOMENT_VERSUS_FINITE_NOISE"
FROZEN_BLOCKS=(0,7)
FROZEN_SIZES=(24,96)
FROZEN_SUPPORT=("ordinary_independent","ordinary_dependent")
BASIS="legendre5"
CONDITIONAL_DRAWS=128
DRAW_SEED=202610153401
EXPECTED=len(FROZEN_BLOCKS)*len(FROZEN_SIZES)*len(FROZEN_SUPPORT)
TRUE_COMPONENTS=np.array([r23.SOURCE_VARIANCES[k] for k in COMPONENTS])


def wilson(k,n):
    if n==0:return None
    z=float(norm.ppf(.975));p=k/n;den=1+z*z/n
    mean=(p+z*z/(2*n))/den
    delta=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [0.0 if k==0 else float(max(0.,mean-delta)),
            1.0 if k==n else float(min(1.,mean+delta))]


def operator_for_original_design(block,n,support):
    family=("predictor_scaled_slope" if support.endswith("_dependent")
            else "shared_slope")
    case=source.fresh_source(block,support,n=n,
        master_seed=r23.MASTER_SEED,n_blocks=r23.BLOCKS,max_n=max(r23.SIZES))
    observed=(None,case[1],case[2],case[3],case[4],None)
    X,y,w,ids,time,trial,x=observed_weighted_rows(observed,BASIS)
    Z=X*np.sqrt(w)[:,None]
    G=Z.T@Z
    invG=np.linalg.solve(G,np.eye(X.shape[1]))
    indices=[np.flatnonzero(ids==label) for label in np.unique(ids)]
    true_cov=source.prepare(case,BASIS)[-1]
    components=[]
    moments=[np.zeros_like(G) for _ in COMPONENTS]
    for ix in indices:
        kernels=_kernels(time[ix],trial[ix],x[ix],w[ix],family)
        components.append(kernels)
        zi=Z[ix]
        for k,K in enumerate(kernels):
            moments[k]+=zi.T@K@zi
    design_chunks=[]
    expected=[]
    totalM=np.zeros_like(G)
    for ix,phi in zip(indices,true_cov):
        totalM+=Z[ix].T@phi@Z[ix]
    for ix,phi,ki in zip(indices,true_cov,components):
        zi=Z[ix];H=zi@invG@zi.T
        matrices=[]
        for k,K in enumerate(ki):
            D=(K-H@K-K@H+zi@invG@moments[k]@invG@zi.T)
            matrices.append(((D+D.T)/2).ravel())
        design_chunks.append(np.column_stack(matrices))
        true_block=(phi-H@phi-phi@H+zi@invG@totalM@invG@zi.T)
        expected.append(((true_block+true_block.T)/2).ravel())
    A=np.vstack(design_chunks)
    expected=np.concatenate(expected)
    projected=A@TRUE_COMPONENTS
    contract=float(np.linalg.norm(projected-expected)/np.linalg.norm(expected))
    if contract>5e-9:
        raise ValueError("independently derived expected moments disagree with source covariance")
    norm=np.linalg.norm(A,axis=0)
    if np.min(norm)<=0:
        raise ValueError("moment components not represented in fixed design")
    As=A/norm
    if np.linalg.matrix_rank(As)!=len(COMPONENTS):
        raise ValueError("fixed design moment operator rank deficient")
    pop,_=nnls(As,projected,maxiter=1000)
    pop=pop/norm
    poperror=float(np.max(abs(pop-TRUE_COMPONENTS)/TRUE_COMPONENTS))
    if poperror>5e-8:
        raise ValueError("nonnegative population moments do not recover the true components")
    original=estimate_feasible_working_target(
        X,y,w,ids,time,trial,x,slope=family)
    rhs_obs=[]
    ew=(y-X@np.linalg.solve(G,Z.T@(y*np.sqrt(w))))*np.sqrt(w)
    for ix in indices:
        rhs_obs.append(np.outer(ew[ix],ew[ix]).ravel())
    observed_raw,_=nnls(As,np.concatenate(rhs_obs),maxiter=1000)
    observed_raw=observed_raw/norm
    observed_estimates=np.array([original["variance_components"][k] for k in COMPONENTS])
    # The original observation-only fitter is permitted to apply a stated
    # strictly positive numerical floor to the sensor component.
    sensor_floor=max(1e-8,2e-10/float(np.min(w)))
    observed_raw[-1]=max(observed_raw[-1],sensor_floor)
    if not np.allclose(observed_raw,observed_estimates,rtol=1e-8,atol=1e-9):
        raise ValueError("oracle design operator fails to reproduce observable-only NNLS fit")
    signal_squared=float(np.sum(expected*expected))
    # Exact Gaussian formula: E ||e_i e_i'-D_i||_F^2
    # = tr(D_i)^2 + tr(D_i^2) for e_i ~ N(0,D_i).
    expected_noise_squared=0.
    for v in np.split(expected, np.cumsum([len(ix)**2 for ix in indices])[:-1]):
        m=int(np.sqrt(len(v)))
        D=v.reshape(m,m)
        expected_noise_squared+=float(np.trace(D)**2+np.sum(D*D))
    return {
        "block":block,"participants":n,"support":support,"family":family,
        "X":X,"y":y,"w":w,"Z":Z,"invG":invG,"indices":indices,
        "Phi":true_cov,"A":A,"As":As,"norm":norm,"expected":expected,
        "contract_relative_error":contract,
        "population_nnls_relative_error":poperror,
        "moment_operator_condition":float(np.linalg.cond(As)),
        "observed_component_estimates":original["variance_components"],
        "observed_zero_components":[k for k in COMPONENTS
                                   if original["variance_components"][k]==0.],
        "theoretical_outer_product_noise_to_signal_rms":float(
            np.sqrt(expected_noise_squared/signal_squared)),
    }


def simulate(frozen):
    ixlist=frozen["indices"]
    Z=frozen["Z"]
    invG=frozen["invG"]
    As=frozen["As"]
    normalization=frozen["norm"]
    rng=np.random.default_rng(
        DRAW_SEED+int(frozen["block"])*31+int(frozen["participants"])*17
        +(["ordinary_independent","ordinary_dependent"].index(frozen["support"]))*107)
    roots=[np.linalg.cholesky(phi) for phi in frozen["Phi"]]
    sample=[]
    for _ in range(CONDITIONAL_DRAWS):
        innovations=np.concatenate([
            root@rng.normal(size=len(ix))
            for root,ix in zip(roots,ixlist)])
        residual=innovations-Z@(invG@(Z.T@innovations))
        rhs=np.concatenate([np.outer(residual[ix],residual[ix]).ravel()
                            for ix in ixlist])
        coef,_=nnls(As,rhs,maxiter=1000)
        sample.append(coef/normalization)
    values=np.vstack(sample)
    boundaries=np.sum(values==0.,axis=0)
    return {
        "source_block":frozen["block"],
        "participants":frozen["participants"],
        "source_support":frozen["support"],
        "matched_working_family":frozen["family"],
        "fixed_mean_basis":BASIS,
        "population_component_recovery_max_relative_error":frozen["population_nnls_relative_error"],
        "true_source_covariance_operator_identity_error":frozen["contract_relative_error"],
        "moment_operator_condition":frozen["moment_operator_condition"],
        "theoretical_gaussian_moment_noise_to_signal_rms":frozen["theoretical_outer_product_noise_to_signal_rms"],
        "original_observed_zero_components":frozen["observed_zero_components"],
        "conditional_draws":CONDITIONAL_DRAWS,
        "conditional_zero_counts":dict(zip(COMPONENTS,map(int,boundaries))),
        "conditional_zero_wilson_95pct":dict(zip(COMPONENTS,[
            wilson(int(k),CONDITIONAL_DRAWS) for k in boundaries])),
        "conditional_median_relative_component_errors":dict(zip(COMPONENTS,[
            float(np.median(abs(values[:,i]-TRUE_COMPONENTS[i])/TRUE_COMPONENTS[i]))
            for i in range(len(COMPONENTS))])),
        "conditional_component_mean_over_true":dict(zip(COMPONENTS,[
            float(np.mean(values[:,i])/TRUE_COMPONENTS[i]) for i in range(len(COMPONENTS))])),
        "extra_draws_are_new_independent_source_designs":False,
        "inference_qualified":False,
        "release_authorized":False,
    }


def summary(cells):
    return {
       "study":STUDY,
       "original_R23_seed":r23.MASTER_SEED,
       "frozen_original_source_blocks":FROZEN_BLOCKS,
       "frozen_sample_sizes":FROZEN_SIZES,
       "frozen_source_covariance_modes":FROZEN_SUPPORT,
       "expected_designs":EXPECTED,
       "completed_designs":len(cells),
       "conditional_draws_per_frozen_design":CONDITIONAL_DRAWS,
       "new_independent_source_designs":0,
       "new_conditional_innovation_vectors":len(cells)*CONDITIONAL_DRAWS,
       "max_population_recovery_relative_error":max(
           x["population_component_recovery_max_relative_error"] for x in cells),
       "max_operator_contract_relative_error":max(
           x["true_source_covariance_operator_identity_error"] for x in cells),
       "cells":cells,
       "changes_original_R23_results":False,
       "pointwise_coverage_qualified":False,
       "simultaneous_bands_qualified":False,
       "release_authorized":False,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    cells=[simulate(operator_for_original_design(b,n,s))
           for b in FROZEN_BLOCKS for n in FROZEN_SIZES for s in FROZEN_SUPPORT]
    result=summary(cells)
    for name,obj in (("summary.json",result),("case-ledger.json",cells)):
        (args.out/name).write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")
    (args.out/"source-commit.txt").write_text(os.getenv("GITHUB_SHA","unverified-local")+"\n")
    files=("summary.json","case-ledger.json","source-commit.txt")
    (args.out/"SHA256SUMS").write_text("".join(
        hashlib.sha256((args.out/name).read_bytes()).hexdigest()+"  "+name+"\n"
        for name in files))
    print("R24 MOMENT NOISE AUDIT:",json.dumps(
          {k:v for k,v in result.items() if k!="cells"},sort_keys=True))
    for cell in cells:
        print("R24 FIXED DESIGN:",json.dumps(cell,sort_keys=True))
    if result["completed_designs"]!=EXPECTED:
        raise SystemExit("R24 fixed-design cases incomplete")


if __name__=="__main__":
    main()
