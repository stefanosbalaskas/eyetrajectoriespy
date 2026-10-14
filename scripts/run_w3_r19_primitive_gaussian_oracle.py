"""R19 exact primitive-innovation audit of original R18 Gaussian-source oracle.

Reuses 192 R18 source blocks and all 768 prespecified source/model cases.
Independently reconstructs focal WLS estimator noise and its conditional
variance from intercept, slope, trial and sensor primitive Gaussian draws.
Frozen R18 coverage counts must remain identical. Conditional Gaussian draws
at twelve fixed original designs are descriptive mathematical sanity checks.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np
from scipy.stats import norm, t as student_t

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts import run_w3_r16_leverage_covariance_factorial as r16
from scripts import run_w3_r17_fresh_feasibility as r17
from scripts import run_w3_r18_independent_gaussian_oracle as original

STUDY="W3_R19_ORIGINAL_R18_GAUSSIAN_PRIMITIVE_INNOVATION_AUDIT"
FROZEN_BLOCKS=(0,37,191)
DRAW_SEED=202610142723
DRAW_PER_FIXED_DESIGN=1024
NORMAL_CRITICAL=float(norm.ppf(.95))
T_CRITICAL=float(student_t.ppf(.95,original.PARTICIPANTS-1))


def primitive_contrast(data,model):
    raw,gaze,x,person,trials,means=data
    n=original.PARTICIPANTS
    X,y,w,group,Phi=r17.prepare(data,model)
    basis=r16.basis(np.asarray([r16.TIME[r16.FOCAL]]),model)[0]
    c=np.r_[np.zeros(len(basis)),basis]
    bread_direction=np.linalg.solve(X.T@(X*w[:,None]),c)
    q=w*(X@bread_direction)
    a=np.zeros(n)
    b=np.zeros(n)
    tr=np.zeros((n,3))
    sensor_coeff=np.zeros(len(q))
    sensor_realization=np.zeros(len(q))
    offset=0
    for curve,(time,who0,trial0,xi0) in enumerate(zip(gaze.time,person,trials,x)):
        who=int(who0)
        jj=int(trial0%3)
        time=np.asarray(time)
        m=len(time)
        ww=q[offset:offset+m]
        a[who]+=float(np.dot(ww,r16.SIGMA_INTERCEPT*(1+.30*time)))
        multiplier=float(xi0) if raw["covariance_mode"]=="dependent" else 1.
        b[who]+=float(np.dot(ww,r16.SIGMA_RANDOM_SLOPE*multiplier*(1+.25*time)))
        tr[who,jj]+=float(r16.SIGMA_TRIAL*np.sum(ww))
        sensor_coeff[offset:offset+m]=r16.SIGMA_SENSOR*ww
        sensor_realization[offset:offset+m]=raw["sensor_noise"][who,jj,:m,0]
        offset+=m
    if offset!=len(q):
        raise ValueError("source curve/native observation alignment changed")
    primitive_noise=(
        float(a@raw["participant_intercept"][:n,0,0,0])
       +float(b@raw["participant_slope"][:n,0,0,0])
       +float(np.sum(tr*raw["trial_noise"][:n,:,0,0]))
       +float(sensor_coeff@sensor_realization)
    )
    primitive_variance=float(a@a+b@b+np.sum(tr*tr)+sensor_coeff@sensor_coeff)
    mu=np.concatenate([np.asarray(v) for v in means])
    direct_observation_noise=float(q@(y-mu))
    weights=np.concatenate([a,b,tr.ravel(),sensor_coeff])
    return {"primitive_realized_noise":primitive_noise,
            "direct_observation_realized_noise":direct_observation_noise,
            "primitive_conditional_variance":primitive_variance,
            "n_primitive_innovations":len(weights),
            "standardized_primitive_weight_norm":float(np.linalg.norm(weights)),
            "gaussian_primitive_coefficients":weights}


def fixed_design_draws(weights,seed):
    rng=np.random.default_rng(seed)
    sigma=float(np.linalg.norm(weights))
    if sigma<=0 or not np.isfinite(sigma):
        raise ValueError("invalid primitive Gaussian coefficient norm")
    z=[]
    for _ in range(DRAW_PER_FIXED_DESIGN//64):
        innovations=rng.normal(size=(64,len(weights)))
        z.extend(((innovations@weights)/sigma).tolist())
    v=np.asarray(z)
    if len(v)!=DRAW_PER_FIXED_DESIGN:
        raise ValueError("conditional Gaussian fixed design sample count changed")
    return {
        "draws":len(v),
        "independent_innovation_seed":seed,
        "mean_standardized":float(v.mean()),
        "sd_standardized":float(v.std(ddof=1)),
        "mean_square_standardized":float(np.mean(v*v)),
        "90pct_normal_truth_inclusion_given_fixed_projection":int(np.sum(np.abs(v)<=NORMAL_CRITICAL)),
        "conditional_simulation_is_new_independent_source_blocks":False
    }


def diagnose(block,support,model):
    out={"study":STUDY,"block":block,"support":support,"model":model,
         "status":"failed","exception":None,"changes_original_R18":False,
         "release_authorized":False}
    try:
        data=original.generate(block,support)
        ref=r16.fit(data,model)
        primitive=primitive_contrast(data,model)
        source_noise=float(ref["point"]-ref["project"])
        variance=float(ref["oracle_se"]**2)
        if abs(source_noise-primitive["primitive_realized_noise"])>2e-8:
            raise ValueError("primitive innovations fail to reconstruct fitted Gaussian contrast")
        if abs(source_noise-primitive["direct_observation_realized_noise"])>2e-8:
            raise ValueError("native observation residual fails to reconstruct fitted contrast")
        if abs(variance-primitive["primitive_conditional_variance"])>2e-7:
            raise ValueError("primitive independent Gaussian variance conflicts with source oracle")
        se=float(ref["oracle_se"])
        truth=float(ref["known_mid_slope"])
        proj=float(ref["project"])
        zt=float((ref["point"]-truth)/se)
        zp=float((ref["point"]-proj)/se)
        out.update(status="ok",
            reconstructed_error_delta=abs(source_noise-primitive["primitive_realized_noise"]),
            native_residual_error_delta=abs(source_noise-primitive["direct_observation_realized_noise"]),
            primitive_oracle_variance_difference=abs(variance-primitive["primitive_conditional_variance"]),
            primitive_count=primitive["n_primitive_innovations"],
            z_projected=zp,z_truth=zt,
            truth_included_normal=bool(abs(zt)<=NORMAL_CRITICAL),
            projection_included_normal=bool(abs(zp)<=NORMAL_CRITICAL),
            truth_included_tGminus1=bool(abs(zt)<=T_CRITICAL),
            projection_included_tGminus1=bool(abs(zp)<=T_CRITICAL),
            original_R18_outcome_preserved=True)
        if block in FROZEN_BLOCKS:
            seed=DRAW_SEED+block*41+original.SUPPORT.index(support)*7+original.BASES.index(model)
            out["conditional_fixed_design_gaussian_draws"]=fixed_design_draws(
                primitive["gaussian_primitive_coefficients"],seed)
    except Exception as exc:
        out["exception"]={"type":type(exc).__name__,"message":str(exc)[:600]}
    return out


def summarize(rows):
    contract_path=Path(__file__).resolve().parents[1]/"docs/development/w3-r18-original-gaussian-oracle-coverage-contract.json"
    frozen=json.loads(contract_path.read_text(encoding="utf-8"))
    if frozen["master_seed"]!=original.MASTER_SEED or frozen["independent_blocks"]!=original.BLOCKS:
        raise ValueError("frozen original R18 source contract altered")
    names=["truth_included_normal","truth_included_tGminus1",
           "projection_included_normal","projection_included_tGminus1"]
    keys={(i,s,m) for i in range(original.BLOCKS) for s in original.SUPPORT for m in original.BASES}
    actual={(x["block"],x["support"],x["model"]) for x in rows}
    if len(actual)!=len(rows):raise ValueError("duplicate original source diagnostic cases")
    cells={}
    mismatches=[]
    for support in original.SUPPORT:
        for model in original.BASES:
            key=f"{support}/{model}"
            subset=[x for x in rows if x["support"]==support and x["model"]==model]
            good=[x for x in subset if x["status"]=="ok"]
            original_counts=frozen["coverage_counts"][key]
            counts={name:sum(int(x[name]) for x in good) for name in names}
            if len(good)!=original.BLOCKS or counts!=original_counts:
                mismatches.append({"cell":key,"expected":original_counts,
                                   "observed":counts,"completed":len(good)})
            fixed=[x["conditional_fixed_design_gaussian_draws"] for x in good
                   if "conditional_fixed_design_gaussian_draws" in x]
            cells[key]={"completed_source_blocks":len(good),"failed_cases":len(subset)-len(good),
                "original_truth_and_projection_inclusion_counts":counts,
                "max_realized_error_delta":float(max(x["reconstructed_error_delta"] for x in good)) if good else None,
                "max_native_residual_error_delta":float(max(x["native_residual_error_delta"] for x in good)) if good else None,
                "max_primitive_variance_delta":float(max(x["primitive_oracle_variance_difference"] for x in good)) if good else None,
                "conditional_fixed_design_samples":fixed}
    return {"study":STUDY,"original_source_master_seed":original.MASTER_SEED,
        "original_192_independent_source_blocks":original.BLOCKS,
        "source_commit":frozen["source_commit"],
        "planned_original_source_cases":len(keys),
        "recorded_original_source_cases":len(rows),
        "completed_original_source_cases":sum(x["status"]=="ok" for x in rows),
        "failed_original_source_cases":sum(x["status"]!="ok" for x in rows),
        "missing_original_source_cases":len(keys-actual),
        "original_R18_coverage_contract_all_four_cells_exact":not mismatches,
        "original_R18_contract_mismatches":mismatches,
        "fixed_design_indices":FROZEN_BLOCKS,
        "conditional_draws_per_fixed_design":DRAW_PER_FIXED_DESIGN,
        "cells":cells,
        "source_data_unchanged":True,
        "inference_qualified":False,"simultaneous_bands_qualified":False,
        "production_release_ready":False}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    rows=[diagnose(b,s,m) for b in range(original.BLOCKS)
          for s in original.SUPPORT for m in original.BASES]
    summary=summarize(rows)
    for name,obj in (("case-ledger.json",rows),("summary.json",summary)):
        (args.out/name).write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (args.out/"source-commit.txt").write_text(os.getenv("GITHUB_SHA","unverified-local")+"\n")
    files=("case-ledger.json","summary.json","source-commit.txt")
    (args.out/"SHA256SUMS").write_text("".join(hashlib.sha256((args.out/name).read_bytes()).hexdigest()+"  "+name+"\n" for name in files))
    head={k:v for k,v in summary.items() if k!="cells"}
    print("R19 PRIMITIVE SOURCE AUDIT:",json.dumps(head,sort_keys=True))
    for name,values in summary["cells"].items():
        print("R19 PRIMITIVE SOURCE CELL:",json.dumps({"name":name,**values},sort_keys=True))
    if (summary["missing_original_source_cases"] or summary["failed_original_source_cases"] or
        not summary["original_R18_coverage_contract_all_four_cells_exact"]):
        raise SystemExit("original R18 source or primitive Gaussian variance contract failed")


if __name__=="__main__":
    main()
