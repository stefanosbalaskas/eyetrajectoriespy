"""R61 research: fitted-null Gaussian Cholesky simulation/covariance fidelity.

The R60 archive did not save native Gaussian y. This NEW 4-primitive-block
study retains *synthetic* raw observed-design witnesses, fixed-H0 fitted
nuisance theta/GLS beta, and independently seeded whitened-draw diagnostics.
Numerically validates Cholesky covariance and WLS backtransform on EVERY
source participant block. This is generator correctness, NOT null-test size,
parametric bootstrap p-value qualification or fitted CR2 bands.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path

import numpy as np
from scipy.linalg import solve_triangular

from scripts import run_w3_r16_leverage_covariance_factorial as r16
from scripts import run_w3_r17_fresh_feasibility as fresh
from scripts import run_w3_r48_independent_fitted_cr2 as r48
from scripts import run_w3_r57_nested_zero_nonnegative_reml as r57
from scripts import run_w3_r60_nuisance_refit_null_bootstrap as r60

STUDY="W3_R61_GAUSSIAN_FITTED_H0_DRAW_COVARIANCE_FIDELITY"
SOURCE_SEED=202610176161
DRAW_SEED=202610176162
BLOCKS=4
N=24
SUPPORT=("ordinary_dependent","extreme_dependent")
M=1024
PARTICIPANTS_TO_CHECK=(0,23)
SHARDS=((0,1),(1,2),(2,3),(3,4))


def new_source(block,support):
    if type(block) is not int or not 0<=block<BLOCKS or support not in SUPPORT:
        raise ValueError("R61 source outside frozen seed/design")
    case=fresh.fresh_source(
        block,support,n=N,master_seed=SOURCE_SEED,n_blocks=BLOCKS,max_n=N)
    X,y,w,g,t,tr,x,*_=r48.native_data(case)
    slopes=np.asarray(case[0]["participant_slope"],float)[
        np.asarray(g,int),0,0,0]
    remove=r16.SIGMA_RANDOM_SLOPE*slopes*x*(1.+.25*t)
    zero=np.asarray(y,float)-remove
    np.testing.assert_allclose(
        np.asarray(y,float)-zero,remove,rtol=2e-13,atol=2e-13)
    return {"X":X,"y":zero,"w":w,"group":g,"time":t,"trial":tr,"x":x,
            "true_slope_variance":0.,
            "original_slope_contribution_L2":float(np.linalg.norm(remove))}


def design_witness(data):
    return {key:np.asarray(data[key]).tolist()
            for key in ("X","y","w","group","time","trial","x")}


def inspect_H0_fidelity(block,support,draws=M):
    data=new_source(block,support)
    X,y,w,g,t,tr,x=(data[k] for k in
                    ("X","y","w","group","time","trial","x"))
    out={
        "study":STUDY,"block":block,"support":support,
        "new_independent_Gaussian_primitive_block":True,
        "paired_leverage_same_primitive_not_independent":True,
        "source_status":"refused","source_error":None,
        "true_generating_random_slope_variance":0.,
        "original_slope_contribution_L2":data["original_slope_contribution_L2"],
        "observed_fit":None,"fitted_H0_theta":None,"fitted_H0_GLS_beta":None,
        "native_synthetic_source":design_witness(data),
        "n_original_participant_covariances":0,
        "maximum_H0_kernel_to_cholesky_covariance_error":None,
        "fidelity_records":[],
        "null_test_size_or_power_qualified":False,
        "CR2_90pct_pointwise_or_simultaneous_qualified":False,
        "release_authorized":False,
    }
    try:
        fit=r60.nested_on(data)
        out["observed_fit"]=fit
        if fit["status"]!="accepted":
            out["source_error"]="observed_exact_zero_nested_fit_refused"
            return out
        beta,covs,theta=r60.h0_gls_covariance(
            data,fit["null_fit"],fit["observed_reference"])
        out["fitted_H0_theta"]=theta
        out["fitted_H0_GLS_beta"]=beta.tolist()
        prepared=r57.prepare_reml_design(
            X,y,w,g,t,tr,x,slope="predictor_scaled_slope")
        maximum=0.
        for cluster,((idx,L),(Zi,yi,Ks)) in enumerate(zip(covs,prepared)):
            reference_V=sum(float(theta[j])*Ks[j] for j in range(4))
            ref_error=float(np.max(abs(L@L.T-reference_V)))
            if not math.isfinite(ref_error) or ref_error>1e-8:
                raise ValueError("R61 original weighted H0 kernel/Cholesky mismatch")
            maximum=max(maximum,ref_error)
            if cluster not in PARTICIPANTS_TO_CHECK:
                continue
            seed=DRAW_SEED+100003*block+739*SUPPORT.index(support)+cluster
            rng=np.random.default_rng(seed)
            z=rng.standard_normal(size=(draws,len(idx)))
            eps=z@L.T
            backtransform=X[idx]@beta + eps/np.sqrt(w[idx])[None,:]
            recovered=(backtransform-X[idx]@beta)*np.sqrt(w[idx])[None,:]
            whiten=solve_triangular(
                L,recovered.T,lower=True,check_finite=False).T
            algebra=float(np.max(abs(whiten-z)))
            if not math.isfinite(algebra) or algebra>2e-8:
                raise ValueError("R61 weighted Gaussian residual backtransform mismatch")
            center=whiten.mean(axis=0)
            centered=whiten-center[None,:]
            whiten_cov=centered.T@centered/(draws-1)
            d=whiten_cov.shape[0]
            frobenius=float(np.linalg.norm(
                whiten_cov-np.eye(d),ord="fro")/math.sqrt(d))
            mean_rms=float(math.sqrt(np.mean(center**2)))
            if not all(np.isfinite(v) for v in (frobenius,mean_rms)):
                raise ValueError("R61 nonfinite independent empirical moment diagnostic")
            out["fidelity_records"].append({
                "participant":cluster,"native_cluster_rows":int(len(idx)),
                "gaussian_draws":int(draws),"independent_draw_seed":seed,
                "max_weighted_backtransform_whitening_error":algebra,
                "empirical_whitened_mean_RMS":mean_rms,
                "empirical_whitened_covariance_Frobenius_RMS":frobenius,
                "theoretical_approx_Frobenius_RMS":math.sqrt((d+1)/draws),
                "moments_are_descriptive_not_a_null_size_test":True,
            })
        out["n_original_participant_covariances"]=len(covs)
        out["maximum_H0_kernel_to_cholesky_covariance_error"]=maximum
        if len(covs)!=N or len(out["fidelity_records"])!=len(PARTICIPANTS_TO_CHECK):
            raise ValueError("R61 original participant or empirical witness missing")
        out["source_status"]="accepted"
    except Exception as exc:
        out["source_error"]=repr(exc)[:460]
    return out


def summarize(rows):
    expected={(b,s) for b in range(BLOCKS) for s in SUPPORT}
    labels=[(r["block"],r["support"]) for r in rows]
    if len(labels)!=8 or len(set(labels))!=8 or set(labels)!=expected:
        raise ValueError("R61 independent original source identities incomplete")
    successful=[r for r in rows if r["source_status"]=="accepted"]
    return {
        "study":STUDY,"source_seed":SOURCE_SEED,"draw_seed":DRAW_SEED,
        "new_independent_Gaussian_primitive_blocks":BLOCKS,
        "paired_leverage_variants_not_independent":True,
        "planned_source_variants":8,"recorded_source_variants":len(rows),
        "accepted_source_cases":len(successful),
        "refused_source_cases":len(rows)-len(successful),
        "participants_per_primitive_source":N,
        "planned_participant_covariance_identity_checks":8*N,
        "completed_participant_covariance_identity_checks":sum(
            r["n_original_participant_covariances"] for r in successful),
        "planned_empirical_whitened_draw_witnesses":8*len(PARTICIPANTS_TO_CHECK),
        "recorded_empirical_whitened_draw_witnesses":sum(
            len(r["fidelity_records"]) for r in rows),
        "planned_Gaussian_draws_per_witness":M,
        "max_analytic_covariance_identity_error":max(
            (r["maximum_H0_kernel_to_cholesky_covariance_error"]
             for r in successful),default=None),
        "max_exact_weighted_backtransform_whitening_error":max(
            (w["max_weighted_backtransform_whitening_error"]
             for r in successful for w in r["fidelity_records"]),default=None),
        "raw_synthetic_native_y_X_w_group_time_trial_x_archived":True,
        "fitted_H0_theta_and_GLS_beta_archived":True,
        "bootstrap_null_type_I_or_power_qualified":False,
        "pointwise_or_simultaneous_90pct_fitted_CR2_qualified":False,
        "release_authorized":False,
    }


def shard(out,start,stop):
    if (start,stop) not in SHARDS:
        raise ValueError("R61 source shard outside frozen design")
    out.mkdir(parents=True,exist_ok=True)
    rows=[inspect_H0_fidelity(b,s) for b in range(start,stop) for s in SUPPORT]
    raw=json.dumps(rows,sort_keys=True,allow_nan=False,indent=2)+"\n"
    (out/"cases.json").write_text(raw)
    (out/"manifest.json").write_text(json.dumps({
        "study":STUDY,"start":start,"stop":stop,
        "source_seed":SOURCE_SEED,"draw_seed":DRAW_SEED,
        "checkout":os.environ.get("GITHUB_SHA","unverified-local"),
        "rows":len(rows),"sha256_cases":hashlib.sha256(raw.encode()).hexdigest(),
    },sort_keys=True,indent=2)+"\n")


def aggregate(out,parts):
    files=list(parts.glob("*/manifest.json"))
    if len(files)!=len(SHARDS):
        raise ValueError("R61 exact four original raw-native witness shards needed")
    seen=set();rows=[];checkout=os.environ.get("GITHUB_SHA","unverified-local")
    for file in files:
        m=json.loads(file.read_text());key=(m["start"],m["stop"])
        if (key not in SHARDS or key in seen or m["study"]!=STUDY or
            m["source_seed"]!=SOURCE_SEED or m["draw_seed"]!=DRAW_SEED or
            m["checkout"]!=checkout):
            raise ValueError("R61 original source/checkout/seed manifest mismatch")
        seen.add(key)
        raw=(file.parent/"cases.json").read_bytes()
        if hashlib.sha256(raw).hexdigest()!=m["sha256_cases"]:
            raise ValueError("R61 original raw native source SHA256 changed")
        data=json.loads(raw)
        if (len(data)!=m["rows"] or
            {(v["block"],v["support"]) for v in data}!=
            {(b,s) for b in range(*key) for s in SUPPORT}):
            raise ValueError("R61 original raw native source keys incomplete")
        rows+=data
    rows.sort(key=lambda r:(r["block"],SUPPORT.index(r["support"])))
    result=summarize(rows)
    out.mkdir(parents=True,exist_ok=True)
    (out/"cases.json").write_text(json.dumps(
        rows,sort_keys=True,indent=2,allow_nan=False)+"\n")
    (out/"summary.json").write_text(json.dumps(
        result,sort_keys=True,indent=2,allow_nan=False)+"\n")
    (out/"source-commit.txt").write_text(checkout+"\n")
    (out/"SHA256SUMS").write_text("".join(
        hashlib.sha256((out/name).read_bytes()).hexdigest()+"  "+name+"\n"
        for name in ("cases.json","summary.json","source-commit.txt")))
    print(json.dumps(result,sort_keys=True))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",required=True,type=Path)
    mode=ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--start",type=int)
    mode.add_argument("--merge-parts",type=Path)
    ap.add_argument("--stop",type=int)
    args=ap.parse_args()
    if args.merge_parts is not None:aggregate(args.out,args.merge_parts)
    elif args.stop is not None:shard(args.out,args.start,args.stop)
    else:raise SystemExit("R61 --start must be paired with --stop")


if __name__=="__main__":
    main()
