"""R15: FRESH independent participant finite-cluster and high-leverage stress.

RESEARCH ONLY. 96 NEW independent simulation-generating blocks, nested 24/48/96
participants, baseline predictor support vs two prespecified high-leverage
participants, fixed Legendre-5 and fixed cubic-spline-13 means. Every recorded
trial/timepoint is complete and genuinely asynchronous. Participant-level
CR1 and delete-one-person jackknife are compared with the analytic Gaussian
conditional-variance oracle under BOTH normal and t references where relevant.
No estimator selection, simultaneous bands, MNAR adjustment or release.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
from scipy.stats import norm,t as student_t
from eyetrajectoriespy import IrregularTrajectorySet
from eyetrajectoriespy.workflows import FunctionOnScalarWorkflowConfig,run_function_on_scalar_workflow
from scripts.run_w3_r9_mean_basis_selection_stress import basis,TIME,DIMS,truth_coefficients
from scripts.run_w3_r12_complete_cluster_variance_oracle import (
    SIGMA_INTERCEPT,SIGMA_RANDOM_SLOPE,SIGMA_TRIAL,SIGMA_SENSOR,
)

STUDY="W3_R15_FRESH_CLUSTER_LEVERAGE_VALIDATION_20261013"
SEED=202610131515
BLOCKS=96
SIZES=(24,48,96)
SUPPORT=("ordinary","two_extreme_predictors")
MODELS=("legendre5","cubic_spline13")
METHODS=("cr1_t","cr1_normal","cluster_jackknife_t","oracle_t","oracle_normal")
MAX_N=96
MAX_TRIALS=3
FOCAL=15
NOMINAL=.90
NUMERICAL_TOL=4e-7
MC_BOOTSTRAP_DRAWS=3000


def generating_block(block):
    if type(block) is not int or not 0<=block<BLOCKS:
        raise ValueError("independent source block not predeclared")
    rng=np.random.default_rng(SEED+23741*block)
    x=rng.uniform(-.95,.95,size=MAX_N)
    n_trials=1+np.floor(3*rng.uniform(size=MAX_N)).astype(int)
    jitter=np.clip(rng.normal(0,.006,size=(MAX_N,MAX_TRIALS,len(TIME))),-.01,.01)
    jitter[:,:,0]=0.
    jitter[:,:,-1]=0.
    t=TIME[None,None,:]+jitter
    if not np.all(np.diff(t,axis=2)>0):
        raise ValueError("original asynchronous timestamps not strictly monotonic")
    intercept=rng.normal(size=(MAX_N,1,1,len(DIMS)))
    slope=rng.normal(size=(MAX_N,1,1,len(DIMS)))
    trial=rng.normal(size=(MAX_N,MAX_TRIALS,1,len(DIMS)))
    noise=rng.normal(size=(MAX_N,MAX_TRIALS,len(TIME),len(DIMS)))
    return {"block":block,"x":x,"n_trials":n_trials,"time":t,
            "participant_intercept":intercept,"participant_slope":slope,
            "trial_noise":trial,"sensor_noise":noise}


def source(block,n,support):
    if n not in SIZES or support not in SUPPORT:
        raise ValueError("undeclared size or leverage experiment")
    src=generating_block(block)
    x=src["x"][:n].copy()
    if support=="two_extreme_predictors":
        x[0]=3.0
        x[1]=-2.5
    times=[];values=[];means=[];persons=[];trials=[]
    for i in range(n):
        for j in range(int(src["n_trials"][i])):
            tt=src["time"][i,j].copy()
            v=truth_coefficients(tt)
            mu=v[0]+x[i]*v[1]
            yy=(mu
                + SIGMA_INTERCEPT*src["participant_intercept"][i,0,0]*(1+.30*tt[:,None])
                + SIGMA_RANDOM_SLOPE*src["participant_slope"][i,0,0]*x[i]*(1+.25*tt[:,None])
                + SIGMA_TRIAL*src["trial_noise"][i,j,0]
                + SIGMA_SENSOR*src["sensor_noise"][i,j])
            times.append(tt);values.append(yy)
            means.append(mu[:,0].copy());persons.append(i);trials.append(3*i+j)
    ids=tuple(f"P{i:03d}-T{j%3:02d}" for i,j in zip(persons,trials))
    meta=pd.DataFrame({"participant_id":[f"P{i:03d}" for i in persons],
                       "trial_id":[j%3 for j in trials]})
    gaze=IrregularTrajectorySet(
        time=tuple(times),values=tuple(values),curve_ids=ids,
        dimension_names=DIMS,time_unit="s",coordinate_system="normalized",
        metadata=meta,provenance={
            "research_study":STUDY,"block":block,"support":support,
            "independent_unit":"participant","all_recordings_complete":True,
            "interpolation_performed":False,"simulation":True
        })
    return (src,gaze,np.asarray(x)[np.asarray(persons)],np.asarray(persons),
            np.asarray(trials),tuple(means))


def fit(source_case,model):
    if model not in MODELS:
        raise ValueError("undeclared fixed time mean basis")
    raw,gaze,x,person,trial,means=source_case
    n=len(np.unique(person))
    if n not in SIZES:
        raise ValueError("invalid source number of independent participants")
    counts=np.bincount(person,minlength=n)
    k=basis(np.asarray([.5]),model).shape[1]
    p=2*k
    Q=np.zeros((n,p,p));V=np.zeros((n,p))
    covariance=np.zeros((n,p,p))
    shared_a=np.zeros((n,p));shared_b=np.zeros((n,p))
    all_x=[];all_y=[];all_mu=[];all_weights=[];all_unit=[]
    if len(gaze.time)!=len(x):
        raise ValueError("original source curve map mismatch")
    for c,(tt,yy,mean) in enumerate(zip(gaze.time,gaze.values,means)):
        who=int(person[c]);xi=float(x[c]);j=int(trial[c]%3)
        if len(tt)!=len(TIME) or not np.array_equal(tt,raw["time"][who,j]):
            raise ValueError("original native time source was modified")
        if not np.all(np.diff(tt)>0) or not np.isfinite(yy).all():
            raise ValueError("nonfinite source or nonmonotonic time")
        B=basis(tt,model)
        X=np.column_stack((B,B*xi))
        w=1/(counts[who]*len(tt))
        Q[who]+=w*(X.T@X)
        V[who]+=w*X.T@yy[:,0]
        shared_a[who]+=SIGMA_INTERCEPT*w*X.T@(1+.30*tt)
        shared_b[who]+=SIGMA_RANDOM_SLOPE*w*X.T@(xi*(1+.25*tt))
        z=SIGMA_TRIAL*w*X.sum(axis=0)
        covariance[who]+=np.outer(z,z)
        covariance[who]+=(SIGMA_SENSOR*w)**2*(X.T@X)
        all_x.append(X);all_y.append(np.asarray(yy[:,0]))
        all_mu.append(np.asarray(mean))
        all_weights.append(np.full(len(tt),w))
        all_unit.append(np.full(len(tt),who,dtype=int))
    covariance+=np.einsum("ni,nj->nij",shared_a,shared_a)
    covariance+=np.einsum("ni,nj->nij",shared_b,shared_b)
    Xall=np.vstack(all_x);Y=np.concatenate(all_y)
    M=np.concatenate(all_mu); W=np.concatenate(all_weights)
    units=np.concatenate(all_unit)
    original_total=np.bincount(units,weights=W,minlength=n)
    if not np.allclose(original_total,np.ones(n),atol=2e-12,rtol=0):
        raise ValueError("unequal total participant weight")
    totalQ=Q.sum(axis=0);totalV=V.sum(axis=0)
    theta=np.linalg.solve(totalQ,totalV)
    independent=np.linalg.lstsq(Xall*np.sqrt(W)[:,None],Y*np.sqrt(W),rcond=None)[0]
    qr_delta=float(np.max(np.abs(theta-independent)))
    if qr_delta>NUMERICAL_TOL:
        raise ValueError("source regression QR oracle mismatch")
    mu_theta=np.linalg.lstsq(Xall*np.sqrt(W)[:,None],M*np.sqrt(W),rcond=None)[0]
    group_score=V-np.einsum("nij,j->ni",Q,theta)
    residual=Y-Xall@theta
    independent_score=np.vstack([
        (Xall[units==i]*(W[units==i]*residual[units==i])[:,None]).sum(axis=0)
        for i in range(n)
    ])
    score_delta=float(np.max(np.abs(group_score-independent_score)))
    if score_delta>NUMERICAL_TOL:
        raise ValueError("source participant score oracle mismatch")
    contrast=np.r_[np.zeros(k),basis(np.asarray([TIME[FOCAL]]),model)[0]]
    b=np.linalg.inv(totalQ)
    point=float(contrast@theta)
    projection=float(contrast@mu_theta)
    oracle_var=float(contrast@b@covariance.sum(axis=0)@b@contrast)
    factor=(n/(n-1))*((len(Y)-1)/(len(Y)-p))
    cr1_var=float(contrast@b@(group_score.T@group_score)*factor@b@contrast)
    if min(oracle_var,cr1_var)<=0 or not np.isfinite([oracle_var,cr1_var]).all():
        raise ValueError("nonpositive source covariance")
    leaveQ=totalQ[None,:,:]-Q
    leaveV=totalV[None,:]-V
    leaveTheta=np.linalg.solve(leaveQ,leaveV[...,None])[...,0]
    leavePoint=leaveTheta@contrast
    jack_var=float((n-1)/n*np.sum((leavePoint-leavePoint.mean())**2))
    if jack_var<=0 or not np.isfinite(jack_var):
        raise ValueError("nonpositive leave-person jackknife variance")
    # Leverage in the participant WLS information geometry. We compute
    # the maximum eigenvalue of inv(Q)^(1/2) Q_i inv(Q)^(1/2).
    ch=np.linalg.cholesky(b)
    eigen=np.asarray([np.linalg.eigvalsh(ch.T@Qi@ch).max() for Qi in Q])
    if eigen.min()<-1e-8 or eigen.max()>1+1e-7:
        raise ValueError("invalid original participant block leverage")
    return {"point":point,"project":projection,
            "cr1_se":float(np.sqrt(cr1_var)),
            "jack_se":float(np.sqrt(jack_var)),
            "oracle_se":float(np.sqrt(oracle_var)),
            "known_mid_slope":float(truth_coefficients(TIME)[1,FOCAL,0]),
            "max_block_leverage":float(np.max(eigen)),
            "first_two_mean_block_leverage":float(np.mean(eigen[:2])),
            "mean_block_leverage":float(np.mean(eigen)),
            "qr_delta":qr_delta,"score_delta":score_delta,
            "native_points":len(Y),"native_trials":len(gaze.time)}


def evaluate(block,n,support,model):
    out={"study":STUDY,"block":block,"n_participants":n,
         "support":support,"model":model,"status":"failed",
         "exception":None,"methods":{},"complete_native_source":False,
         "public_dense_W3_rejects_async":False,
         "simultaneous_bands_qualified":False,
         "method_winner_selected":False,"release_authorized":False}
    try:
        source_case=source(block,n,support)
        src,gaze,x,person,trials,means=source_case
        # Source data are copied from the generating block, never imputed.
        original=[(t.copy(),v.copy()) for t,v in zip(gaze.time,gaze.values)]
        frame=pd.DataFrame({"curve_id":gaze.curve_ids,"condition":x})
        try:
            run_function_on_scalar_workflow(
                gaze,frame,config=FunctionOnScalarWorkflowConfig(
                    predictors=("condition",),dimensions=DIMS,unit="participant",
                    participant_column="participant_id"))
        except TypeError as exc:
            if "IrregularTrajectorySet" not in str(exc):raise
        else:
            raise ValueError("public W3 incorrectly fitted native async input")
        d=fit(source_case,model)
        if any(not np.array_equal(t,t2) or not np.array_equal(v,v2)
               for (t,v),t2,v2 in zip(original,gaze.time,gaze.values)):
            raise ValueError("original complete source observations mutated")
        tcrit=float(student_t.ppf((1+NOMINAL)/2,n-1))
        zcrit=float(norm.ppf((1+NOMINAL)/2))
        specs={
            "cr1_t":(d["cr1_se"],tcrit),
            "cr1_normal":(d["cr1_se"],zcrit),
            "cluster_jackknife_t":(d["jack_se"],tcrit),
            "oracle_t":(d["oracle_se"],tcrit),
            "oracle_normal":(d["oracle_se"],zcrit),
        }
        for key,(se,crit) in specs.items():
            half=float(se*crit)
            out["methods"][key]={"se":se,"width":2*half,
                "truth_included":bool(abs(d["point"]-d["known_mid_slope"])<=half)}
        out.update({"status":"ok","complete_native_source":True,
                    "public_dense_W3_rejects_async":True,
                    "point_estimate":d["point"],
                    "point_error":d["point"]-d["known_mid_slope"],
                    "known_mean_projection_error":d["project"]-d["known_mid_slope"],
                    "max_block_leverage":d["max_block_leverage"],
                    "first_two_mean_block_leverage":d["first_two_mean_block_leverage"],
                    "mean_block_leverage":d["mean_block_leverage"],
                    "jackknife_se_to_oracle":d["jack_se"]/d["oracle_se"],
                    "cr1_se_to_oracle":d["cr1_se"]/d["oracle_se"],
                    "native_points":d["native_points"],
                    "native_trials":d["native_trials"],
                    "source_qr_delta":d["qr_delta"],
                    "source_grouped_score_delta":d["score_delta"]})
    except Exception as e:
        out["exception"]={"type":type(e).__name__,"message":str(e)[:900]}
    return out


def wilson(k,n):
    if not n:return None
    z=float(norm.ppf(.975));p=k/n;v=1+z*z/n
    center=(p+z*z/(2*n))/v
    half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/v
    return [float(max(0,center-half)),float(min(1,center+half))]


def mc_interval(values,seed):
    if not values:return None
    z=np.asarray(values,float)
    rng=np.random.default_rng(seed)
    draw=rng.integers(0,len(z),size=(MC_BOOTSTRAP_DRAWS,len(z)))
    return [float(x) for x in np.quantile(z[draw].mean(axis=1),[.025,.975])]


def audit(rows):
    planned={(b,n,s,m) for b in range(BLOCKS) for n in SIZES
             for s in SUPPORT for m in MODELS}
    keys=[(r["block"],r["n_participants"],r["support"],r["model"]) for r in rows]
    if len(set(keys))!=len(keys) or not set(keys).issubset(planned):
        raise ValueError("duplicate or unplanned source record")
    missing=sorted(f"{b}:{n}:{s}:{m}" for b,n,s,m in planned-set(keys))
    success=[r for r in rows if r["status"]=="ok"]
    groups={}
    for n in SIZES:
        groups[str(n)]={}
        for s in SUPPORT:
            groups[str(n)][s]={}
            for model in MODELS:
                c=sorted((r for r in success if r["n_participants"]==n
                         and r["support"]==s and r["model"]==model),
                         key=lambda r:r["block"])
                measures={}
                for method in METHODS:
                    k=sum(r["methods"][method]["truth_included"] for r in c)
                    measures[method]={
                        "planned":BLOCKS,"completed":len(c),
                        "truth_count":k,
                        "pointwise_inclusion_rate":k/len(c) if c else None,
                        "wilson95":wilson(k,len(c)),
                        "mean_width":float(np.mean([r["methods"][method]["width"]
                                                    for r in c])) if c else None,
                    }
                contrasts={}
                for label,left,right in (
                    ("jackknife_minus_cr1_at_t","cluster_jackknife_t","cr1_t"),
                    ("oracle_minus_cr1_at_t","oracle_t","cr1_t"),
                    ("oracle_minus_cr1_at_normal","oracle_normal","cr1_normal"),
                    ("critical_t_minus_normal_at_cr1","cr1_t","cr1_normal"),
                ):
                    vec=[int(r["methods"][left]["truth_included"])-
                         int(r["methods"][right]["truth_included"]) for r in c]
                    contrasts[label]={
                        "mean":float(np.mean(vec)) if vec else None,
                        "paired_block_MC95":mc_interval(
                            vec,SEED+971*n+sum(map(ord,s+model+label)))
                    }
                groups[str(n)][s][model]={
                    "planned":BLOCKS,"completed":len(c),
                    "source_integrity_passed":sum(
                        r["complete_native_source"] and
                        r["public_dense_W3_rejects_async"] and
                        r["source_qr_delta"]<=NUMERICAL_TOL and
                        r["source_grouped_score_delta"]<=NUMERICAL_TOL for r in c),
                    "mean_max_cluster_leverage":float(np.mean(
                        [r["max_block_leverage"] for r in c])) if c else None,
                    "mean_first_two_leverage":float(np.mean(
                        [r["first_two_mean_block_leverage"] for r in c])) if c else None,
                    "mean_cr1_se_divided_by_oracle":float(np.mean(
                        [r["cr1_se_to_oracle"] for r in c])) if c else None,
                    "mean_jackknife_se_divided_by_oracle":float(np.mean(
                        [r["jackknife_se_to_oracle"] for r in c])) if c else None,
                    "mean_projection_error":float(np.mean(
                        [r["known_mean_projection_error"] for r in c])) if c else None,
                    "mean_true_point_error":float(np.mean(
                        [r["point_error"] for r in c])) if c else None,
                    "methods":measures,"paired_contrasts":contrasts}
    return {"study":STUDY,"master_seed":SEED,
            "fresh_independent_generating_blocks":BLOCKS,
            "nested_sizes":list(SIZES),"two_predictor_extremes":(3.0,-2.5),
            "same_latent_source_within_stress_pair":True,
            "complete_native_support":True,
            "participant_is_independent_unit":True,
            "pointwise_nominal_level":NOMINAL,
            "planned_cases":len(planned),"recorded_cases":len(rows),
            "completed_cases":len(success),
            "failed_cases":len(rows)-len(success),
            "missing_cases":missing,"groups":groups,
            "known_covariance_is_simulation_only":True,
            "no_simultaneous_band_qualification":True,
            "no_method_winner":True,"release_authorized":False}


def plot(report,path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(11,5),sharey=True)
    for axis,s in zip(axes,SUPPORT):
        for method in ("cr1_t","cluster_jackknife_t","oracle_t"):
            for model in MODELS:
                vals=[report["groups"][str(n)][s][model]["methods"][method][
                    "pointwise_inclusion_rate"] for n in SIZES]
                axis.plot(SIZES,vals,marker="o",label=f"{model} / {method}")
        axis.axhline(NOMINAL,color="black",linestyle="--")
        axis.set_title(s.replace("_"," "))
        axis.set_xlabel("Independent participants")
        axis.set_ylim(0,1)
        axis.set_ylabel("90% pointwise known-truth inclusion")
        axis.legend(fontsize=6)
    fig.suptitle("W3 R15: new source finite participants × original predictor leverage")
    fig.tight_layout()
    fig.savefig(path,format="svg",metadata={"Date":None})
    plt.close(fig)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    rows=[evaluate(b,n,s,m) for b in range(BLOCKS) for n in SIZES
          for s in SUPPORT for m in MODELS]
    report=audit(rows)
    for name,obj in (("case-ledger.json",rows),("evidence.json",report)):
        (args.out/name).write_text(json.dumps(obj,sort_keys=True,indent=2)+"\n")
    plot(report,args.out/"source-fresh-cluster-leverage.svg")
    (args.out/"source-commit.txt").write_text(os.getenv("GITHUB_SHA","unverified-local")+"\n")
    names=("case-ledger.json","evidence.json","source-fresh-cluster-leverage.svg",
           "source-commit.txt")
    (args.out/"SHA256SUMS").write_text("".join(
        sha256((args.out/f).read_bytes()).hexdigest()+f"  {f}\n" for f in names))
    print("W3 R15 FRESH LEVERAGE SCIENCE AUDIT:",json.dumps(report,sort_keys=True))
    if report["failed_cases"] or report["missing_cases"]:
        raise SystemExit("R15 original scientific fitting/reference failures retained")


if __name__=="__main__":
    main()
