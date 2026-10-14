"""R17 independent-seed exploratory finite-sample CR2 feasibility study.

8 fresh independent generating blocks; 24 participants; a 2x2 leverage x
covariance mechanism, 2 prespecified bases, and correctly specified vs
diagonal-misspecified CR2 working targets. Does not establish 90% coverage.
No release or public estimator qualification.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np
from scipy.stats import t as student_t

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts import run_w3_r16_leverage_covariance_factorial as r16
from scripts.w3_r17_cr2_blockwise import cr2_blockwise_wls

STUDY="W3_R17_FRESH_BLOCKWISE_CR2_FEASIBILITY"
R17_SEED=202610141717
BLOCKS=8
N=24
TARGETS=("correct","diagonal_misspecified")
NOMINAL=.90


def fresh_source(block,support,*,n=N,master_seed=R17_SEED,n_blocks=BLOCKS,max_n=None):
    if not isinstance(block,int) or not 0<=block<n_blocks or support not in r16.SUPPORT:
        raise ValueError("outside prespecified R17 independent source")
    if n not in r16.SIZES or (max_n is not None and max_n<n):
        raise ValueError("outside prespecified R17 independent source")
    rng=np.random.default_rng(master_seed+23741*block)
    total_n=max_n if max_n is not None else n
    maxtrials=3
    nt=len(r16.TIME)
    nd=len(r16.DIMS)
    xp=rng.uniform(-.95,.95,size=total_n)
    trials_per=1+np.floor(3*rng.uniform(size=total_n)).astype(int)
    jitter=np.clip(rng.normal(0,.006,size=(total_n,maxtrials,nt)),-.01,.01)
    jitter[:,:,0]=0.
    jitter[:,:,-1]=0.
    times_all=r16.TIME[None,None,:]+jitter
    if not np.all(np.diff(times_all,axis=2)>0):
        raise ValueError("R17 source times not strictly increasing")
    intercept=rng.normal(size=(total_n,1,1,nd))
    slope=rng.normal(size=(total_n,1,1,nd))
    trial_noise=rng.normal(size=(total_n,maxtrials,1,nd))
    sensor=rng.normal(size=(total_n,maxtrials,nt,nd))
    cov_mode=support.split("_")[-1]
    x=xp[:n].copy()
    if support.startswith("extreme_"):
        x[0]=3.
        x[1]=-2.5
    ts=[];ys=[];ms=[];persons=[];trialnums=[]
    for i in range(n):
        for j in range(int(trials_per[i])):
            t=times_all[i,j].copy()
            base=r16.truth_coefficients(t)
            mu=base[0]+x[i]*base[1]
            sig=(mu
                +r16.SIGMA_INTERCEPT*intercept[i,0,0]*(1+.30*t[:,None])
                +r16.SIGMA_RANDOM_SLOPE*slope[i,0,0]*(x[i] if cov_mode=="dependent" else 1.)*(1+.25*t[:,None])
                +r16.SIGMA_TRIAL*trial_noise[i,j,0]
                +r16.SIGMA_SENSOR*sensor[i,j])
            ts.append(t);ys.append(sig);ms.append(mu[:,0].copy())
            persons.append(i);trialnums.append(3*i+j)
    ids=tuple(f"P{i:03d}-T{j%3:02d}" for i,j in zip(persons,trialnums))
    meta=r16.pd.DataFrame({"participant_id":[f"P{i:03d}" for i in persons],
                           "trial_id":[j%3 for j in trialnums]})
    gaze=r16.IrregularTrajectorySet(
        time=tuple(ts),values=tuple(ys),curve_ids=ids,
        dimension_names=r16.DIMS,time_unit="s",coordinate_system="normalized",
        metadata=meta,provenance={"research_study":STUDY,"block":block,
              "support":support,"independent_unit":"participant",
              "all_recordings_complete":True,"interpolation_performed":False,
              "simulation":True,"fresh_master_seed":master_seed})
    raw={"block":block,"x":xp,"n_trials":trials_per,"time":times_all,
         "participant_intercept":intercept,"participant_slope":slope,
         "trial_noise":trial_noise,"sensor_noise":sensor,
         "covariance_mode":cov_mode}
    return raw,gaze,x[np.asarray(persons)],np.asarray(persons),np.asarray(trialnums),tuple(ms)


def prepare(source_case,model):
    raw,gaze,x,person,trial,_=source_case
    groups=np.unique(person)
    counts=np.bincount(person,minlength=len(groups))
    XX=[];YY=[];WW=[];ID=[]
    true_target=[]
    for who in groups:
        curves=np.flatnonzero(person==who)
        Xi=[];Yi=[];Wi=[];tt=[];ji=[]
        for c in curves:
            t=np.asarray(gaze.time[c])
            B=r16.basis(t,model)
            Xi.append(np.column_stack((B,x[c]*B)))
            Yi.append(gaze.values[c][:,0])
            w=1/(counts[who]*len(t))
            Wi.append(np.full(len(t),w))
            tt.append(t)
            ji.append(np.full(len(t),int(trial[c]%3)))
        X_i=np.vstack(Xi);Y_i=np.concatenate(Yi);W_i=np.concatenate(Wi)
        time=np.concatenate(tt);trial_id=np.concatenate(ji)
        xi=float(x[curves[0]])
        ga=r16.SIGMA_INTERCEPT*(1+.30*time)
        gb=r16.SIGMA_RANDOM_SLOPE*(xi if raw["covariance_mode"]=="dependent" else 1.)*(1+.25*time)
        cov=np.outer(ga,ga)+np.outer(gb,gb)
        cov+=(r16.SIGMA_TRIAL**2)*(trial_id[:,None]==trial_id[None,:])
        cov+=(r16.SIGMA_SENSOR**2)*np.eye(len(time))
        root=np.sqrt(W_i)
        Phi=(root[:,None]*cov)*root[None,:]
        true_target.append(Phi)
        XX.append(X_i);YY.append(Y_i);WW.append(W_i)
        ID.append(np.full(len(Y_i),who))
    return (np.vstack(XX),np.concatenate(YY),np.concatenate(WW),
            np.concatenate(ID),true_target)


def evaluate(block,support,model,target,*,n=N,master_seed=R17_SEED,n_blocks=BLOCKS,max_n=None):
    row={"study":STUDY,"block":block,"n_participants":n,
         "support":support,"model":model,"target":target,"status":"failed",
         "error":None,"pointwise_inference_qualified":False,
         "simultaneous_bands_qualified":False,"release_authorized":False}
    try:
        data=fresh_source(block,support,n=n,master_seed=master_seed,n_blocks=n_blocks,max_n=max_n)
        ref=r16.fit(data,model)
        X,y,w,person,Phi=prepare(data,model)
        c=np.r_[np.zeros(r16.basis(np.array([.5]),model).shape[1]),
                 r16.basis(np.array([r16.TIME[r16.FOCAL]]),model)[0]]
        target_phi=Phi if target=="correct" else [np.diag(np.diag(p)) for p in Phi]
        adjusted=cr2_blockwise_wls(X,y,w,person,c,target_phi)
        if abs(adjusted["point"]-ref["point"])>r16.NUMERICAL_TOL:
            raise ValueError("new R17 source coefficient differs from independent R16 WLS reference")
        if target=="correct" and abs(adjusted["theoretical_contrast_variance"]-ref["oracle_se"]**2)>2e-7:
            raise ValueError("new true covariance block disagrees with independent source Gaussian oracle")
        if max(adjusted["expectation_identity_error"],
               adjusted["max_adjustment_covariance_error"],
               adjusted["max_adjustment_asymmetry"])>2e-7:
            raise ValueError("blockwise CR2 mathematical contract failed")
        truth=float(r16.truth_coefficients(r16.TIME)[1,r16.FOCAL,0])
        df=adjusted["satterthwaite_df"]
        if not 0<df<=n+1e-5:
            raise ValueError("invalid Satterthwaite reference df")
        m={"cr1_tGminus1":(ref["cr1_se"],n-1),
           "cr2_tGminus1":(adjusted["cr2_se"],n-1),
           "cr2_satterthwaite":(adjusted["cr2_se"],df),
           "cv3j_tGminus1":(ref["jack_se"],n-1),
           "oracle_tGminus1":(ref["oracle_se"],n-1)}
        covered={key:bool(abs(ref["point"]-truth)<=student_t.ppf(.95,nu)*se)
                 for key,(se,nu) in m.items()}
        row.update({"status":"ok","point":float(ref["point"]),"truth":truth,
                    "satterthwaite_df":df,"cr2_se":adjusted["cr2_se"],
                    "cr2_to_oracle_se":adjusted["cr2_se"]/ref["oracle_se"],
                    "contrast_effective_clusters":ref["contrast_effective_clusters"],
                    "coverage":covered,"n_observations":adjusted["n_observations"],
                    "oracle_agreement_error":abs(adjusted["theoretical_contrast_variance"]-ref["oracle_se"]**2)
                      if target=="correct" else None})
    except Exception as exc:
        row["error"]={"type":type(exc).__name__,"message":str(exc)[:500]}
    return row


def summarize(rows):
    groups={}
    for support in r16.SUPPORT:
        for model in r16.MODELS:
            for target in TARGETS:
                match=[r for r in rows if r["support"]==support and r["model"]==model and r["target"]==target]
                good=[r for r in match if r["status"]=="ok"]
                labels=["cr1_tGminus1","cr2_tGminus1","cr2_satterthwaite",
                        "cv3j_tGminus1","oracle_tGminus1"]
                groups[f"{support}/{model}/{target}"]={
                    "planned":BLOCKS,"completed":len(good),"failed":len(match)-len(good),
                    "coverage_counts":{k:sum(int(v["coverage"][k]) for v in good) for k in labels},
                    "mean_satterthwaite_df":float(np.mean([v["satterthwaite_df"] for v in good])) if good else None,
                    "mean_cr2_to_oracle_se":float(np.mean([v["cr2_to_oracle_se"] for v in good])) if good else None}
    return {"study":STUDY,"r17_master_seed":R17_SEED,
            "independent_generating_blocks":BLOCKS,"n_participants":N,
            "planned_cases":BLOCKS*len(r16.SUPPORT)*len(r16.MODELS)*len(TARGETS),
            "completed_cases":sum(v["status"]=="ok" for v in rows),
            "failed_cases":sum(v["status"]!="ok" for v in rows),
            "groups":groups,"exploratory_feasibility_only":True,
            "calibrated_pointwise_inference":False,
            "simultaneous_inference_qualified":False,"release_authorized":False}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    rows=[evaluate(block,s,m,target)
          for block in range(BLOCKS) for s in r16.SUPPORT
          for m in r16.MODELS for target in TARGETS]
    summary=summarize(rows)
    for filename,obj in [("case-ledger.json",rows),("summary.json",summary)]:
        (args.out/filename).write_text(json.dumps(obj,sort_keys=True,indent=2)+"\n")
    (args.out/"source-commit.txt").write_text(os.environ.get("GITHUB_SHA","unverified-local")+"\n")
    files=["case-ledger.json","summary.json","source-commit.txt"]
    (args.out/"SHA256SUMS").write_text("".join(
       hashlib.sha256((args.out/name).read_bytes()).hexdigest()+"  "+name+"\n"
       for name in files))
    print("R17 FRESH FEASIBILITY:",json.dumps(summary,sort_keys=True))
    if summary["failed_cases"] or summary["completed_cases"]!=summary["planned_cases"]:
        raise SystemExit("R17 original-source failures retained in research ledger")


if __name__=="__main__":
    main()
