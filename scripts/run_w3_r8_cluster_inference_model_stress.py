"""W3 R8 research: independent-participant sandwich uncertainty and basis bias.

Fresh 64 source blocks, n=48 participant clusters, up to three genuinely
asynchronous repeated trials, balanced/unbalanced trial support, paired MCAR
versus latent-outcome-dependent loss, and paired baseline versus localized
non-degree-five coefficient truth. Compares naive point-HC1, trial-cluster CR1,
and participant-cluster CR1 for one preregistered pointwise slope target.
NO simultaneous band, valid MNAR estimator, mixed-model inference or API.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
from scipy.stats import t as student_t

from eyetrajectoriespy import IrregularTrajectorySet
from eyetrajectoriespy.workflows import FunctionOnScalarWorkflowConfig, run_function_on_scalar_workflow
from scripts.run_w3_r6_asynchronous_basis import basis, TIME, DIMS, truth_coefficients, expit

STUDY="W3_R8_ASYNC_PARTICIPANT_CLUSTER_CR1_MODEL_STRESS_20261012"
SEED=202610125903
BLOCKS=64
N=48
MAX_TRIALS=3
SCHEMES=("balanced3","unbalanced1to3")
LOSSES=("mcar","latent_response_dependent")
TRUTHS=("baseline","localized_bump")
METHODS=("naive_hc1","trial_cr1","participant_cr1")
GAP=slice(11,19)
FOCAL_TIME=15
CONFIDENCE=.90
POLY_DEGREE=5
BUMP_AMPLITUDE=.15
BUMP_WIDTH=.055
TOL=3e-8
MC_DRAWS=2000
P=2*(POLY_DEGREE+1)


def bump(t):
    return BUMP_AMPLITUDE*np.exp(-.5*((np.asarray(t)-.5)/BUMP_WIDTH)**2)


def original_source(block,scheme,loss,truth_mode):
    if type(block) is not int or not 0<=block<BLOCKS:
        raise ValueError("block outside fresh independent R8 ledger")
    if scheme not in SCHEMES or loss not in LOSSES or truth_mode not in TRUTHS:
        raise ValueError("scenario not in prespecified W3 R8 factorial")

    rng=np.random.default_rng(SEED+17749*block)
    x=rng.uniform(-.95,.95,N)
    trial_allocation=rng.uniform(size=N)
    k=(np.full(N,3,dtype=int) if scheme=="balanced3"
       else 1+np.floor(3*trial_allocation).astype(int))
    jitter=np.clip(rng.normal(0,.006,size=(N,3,len(TIME))),-.010,.010)
    jitter[:,:,0]=0.;jitter[:,:,-1]=0.
    tnative=TIME[None,None,:]+jitter
    if not np.all(np.diff(tnative,axis=2)>0):
        raise ValueError("nonmonotone native generating times")

    random_intercept=rng.normal(0,.08,size=(N,1,1,len(DIMS)))
    random_slope=rng.normal(0,.045,size=(N,1,1,len(DIMS)))
    trial_random=rng.normal(0,.025,size=(N,3,1,len(DIMS)))
    noise=rng.normal(0,.045,size=(N,3,len(TIME),len(DIMS)))
    means=np.empty_like(noise)
    for i in range(N):
        for j in range(3):
            b=truth_coefficients(tnative[i,j])
            means[i,j]=b[0]+x[i]*b[1]
            if truth_mode=="localized_bump":
                means[i,j,:,0]+=x[i]*bump(tnative[i,j])
    response=(means
        + random_intercept*(1+.30*tnative[...,None])
        + random_slope*x[:,None,None,None]*(1+.25*tnative[...,None])
        + trial_random + noise)

    uniforms=rng.uniform(size=(N,3))
    if loss=="mcar":
        missing_p=np.full((N,3),.30)
    else:
        unobserved_resid=response[:,:,FOCAL_TIME,0]-means[:,:,FOCAL_TIME,0]
        missing_p=expit(-.80+1.15*x[:,None]+2.0*unobserved_resid/.11)
    missing=uniforms<missing_p
    times,values,known_mean,part,trial,predictor=[],[],[],[],[],[]
    for i in range(N):
        for j in range(int(k[i])):
            keep=np.ones(len(TIME),bool)
            if missing[i,j]:
                keep[GAP]=False
            times.append(tnative[i,j,keep].copy())
            values.append(response[i,j,keep].copy())
            known_mean.append(means[i,j,keep].copy())
            part.append(i);trial.append(i*3+j);predictor.append(float(x[i]))
    ids=tuple(f"P{i:03d}-T{v%3:02d}" for i,v in zip(part,trial))
    metadata=pd.DataFrame({"participant_id":[f"P{i:03d}" for i in part],
                           "trial_id":[v%3 for v in trial]})
    recorded=IrregularTrajectorySet(
        time=tuple(times),values=tuple(values),curve_ids=ids,
        dimension_names=DIMS,metadata=metadata,coordinate_system="normalized",
        time_unit="s",provenance={
            "study":STUDY,"source_block":block,"true_model":truth_mode,
            "recording_loss":loss,"independent_unit":"participant",
            "interpolation_performed":False,"simulation":True
        }
    )
    truth=truth_coefficients(TIME)
    if truth_mode=="localized_bump":
        truth=truth.copy();truth[1,:,0]+=bump(TIME)
    return recorded,tuple(known_mean),np.asarray(predictor),np.asarray(part),np.asarray(trial),truth,k,missing


def weighted_source_design(recorded,known_means,x,participant_ids,trial_ids):
    """One independent cluster is a person, never a trial or a time point."""
    if not isinstance(recorded,IrregularTrajectorySet):
        raise TypeError("native irregular source required")
    ncurves=len(recorded.curve_ids)
    if len(known_means)!=ncurves or not (len(x)==len(participant_ids)==len(trial_ids)==ncurves):
        raise ValueError("misaligned recorded trial/participant design")
    if len(np.unique(participant_ids))!=N or len(np.unique(trial_ids))!=ncurves:
        raise ValueError("wrong number of independent participants or trials")
    counts=np.bincount(participant_ids,minlength=N)
    if np.any(counts<1):
        raise ValueError("missing original participant")
    design,y,known,weights,units,trials=[],[],[],[],[],[]
    for i,(time,obs,mu) in enumerate(zip(recorded.time,recorded.values,known_means)):
        if len(time)<15 or not np.all(np.diff(time)>0):
            raise ValueError("invalid genuine native time support")
        B=basis(time)
        design.append(np.concatenate([B,B*x[i]],axis=1))
        y.append(np.asarray(obs[:,0],float))
        known.append(np.asarray(mu[:,0],float))
        weights.append(np.full(len(time),1./(counts[participant_ids[i]]*len(time))))
        units.append(np.full(len(time),participant_ids[i],dtype=int))
        trials.append(np.full(len(time),trial_ids[i],dtype=int))
    X=np.vstack(design); Y=np.concatenate(y); MU=np.concatenate(known)
    w=np.concatenate(weights);u=np.concatenate(units);q=np.concatenate(trials)
    if not np.all(np.isfinite(Y)) or np.any(w<=0):
        raise ValueError("nonfinite weighted original source design")
    if not np.allclose(np.bincount(u,weights=w,minlength=N),1.,atol=1e-12):
        raise ValueError("participant total observation weight not exactly 1")
    return X,Y,MU,w,u,q


def fit_pointwise_cluster_variances(recorded,known_means,x,participant_ids,trial_ids):
    X,Y,MU,w,u,q=weighted_source_design(recorded,known_means,x,participant_ids,trial_ids)
    n=len(Y)
    root=np.sqrt(w);A=X*root[:,None];b=Y*root
    if np.linalg.matrix_rank(A)!=P:
        raise ValueError("declared time basis rank deficient")
    beta=np.linalg.lstsq(A,b,rcond=None)[0]
    qmat,rmat=np.linalg.qr(A,mode="reduced")
    qr=np.linalg.solve(rmat,qmat.T@b)
    qr_delta=float(np.max(np.abs(qr-beta)))
    if qr_delta>TOL:raise ValueError("weighted least squares independent QR mismatch")

    bread=np.linalg.inv(A.T@A)
    residual=b-A@beta
    scores=A*residual[:,None]
    focal=np.zeros(P)
    focal[POLY_DEGREE+1:]=basis(np.array([TIME[FOCAL_TIME]]))[0]
    true_projection=np.linalg.lstsq(A,MU*root,rcond=None)[0]
    known_projection=float(focal@true_projection)
    estimate=float(focal@beta)
    contrast=bread@focal

    std={}
    intervals={}
    for method in METHODS:
        if method=="naive_hc1":
            meat=scores.T@scores*(n/(n-P))
            groups=n
        else:
            group_ids=q if method=="trial_cr1" else u
            uniq,inverse=np.unique(group_ids,return_inverse=True)
            sums=np.zeros((len(uniq),P))
            np.add.at(sums,inverse,scores)
            # Separate slower group-by-group reference, not the same
            # aggregate implementation reused as its oracle.
            independent=np.vstack([scores[group_ids==g].sum(axis=0) for g in uniq])
            if not np.allclose(sums,independent,atol=TOL,rtol=0):
                raise ValueError("independent per-cluster score sum oracle failed")
            groups=len(uniq)
            meat=sums.T@sums*(groups/(groups-1))*((n-1)/(n-P))
        variance=float(contrast@meat@contrast)
        if not np.isfinite(variance) or variance<=0:
            raise ValueError("nonpositive sandwich uncertainty")
        se=np.sqrt(variance)
        df=groups-1
        cutoff=float(student_t.ppf((1+CONFIDENCE)/2,df))
        half=float(cutoff*se)
        std[method]=float(se)
        intervals[method]={
            "lower":estimate-half,"upper":estimate+half,
            "width":2*half,
            "critical":cutoff,
            "groups":int(groups)
        }
    return estimate,known_projection,std,intervals,qr_delta,n


def wilson(success,attempted):
    if not attempted:return None
    from scipy.stats import norm
    z=float(norm.ppf(.975))
    p=success/attempted
    denominator=1+z*z/attempted
    center=(p+z*z/(2*attempted))/denominator
    half=z*np.sqrt(p*(1-p)/attempted+z*z/(4*attempted*attempted))/denominator
    return [float(max(0,center-half)),float(min(1,center+half))]


def evaluate(block,scheme,loss,truth_mode):
    row={"study":STUDY,"block":block,"trial_scheme":scheme,"loss":loss,
        "truth_mode":truth_mode,"status":"failed","exception":None,
        "n_independent_participants":N,"n_trials":None,"n_points":None,
        "pointwise_true_slope":None,"pointwise_estimate":None,
        "model_projection_bias":None,"observed_point_bias":None,
        "native_source_preserved":False,"existing_W3_rejects_native":False,
        "qr_max_discrepancy":None,
        "methods":{},"valid_90pct_simultaneous_band":False,
        "cluster_inference_qualified":False,"release_authorized":False}
    try:
        recorded,known,x,u,q,true,k,missing=original_source(block,scheme,loss,truth_mode)
        source_copy=[(t.copy(),v.copy()) for t,v in zip(recorded.time,recorded.values)]
        frame=pd.DataFrame({"curve_id":recorded.curve_ids,"condition":x})
        try:
            run_function_on_scalar_workflow(recorded,frame,config=FunctionOnScalarWorkflowConfig(
                predictors=("condition",),dimensions=DIMS,unit="participant",
                participant_column="participant_id"))
        except TypeError as exc:
            if "IrregularTrajectorySet" not in str(exc):raise
        else:
            raise ValueError("existing public dense W3 silently fitted irregular gaze")
        est,projection,se,interval,delta,n=fit_pointwise_cluster_variances(
            recorded,known,x,u,q)
        target=float(true[1,FOCAL_TIME,0])
        for method in METHODS:
            v=interval[method]
            row["methods"][method]={
                "se":se[method],"width":v["width"],
                "critical":v["critical"],"n_claimed_clusters":v["groups"],
                "included_known_truth":bool(v["lower"]<=target<=v["upper"]),
            }
        for (a,b),tt,yy in zip(source_copy,recorded.time,recorded.values):
            if not np.array_equal(a,tt) or not np.array_equal(b,yy):
                raise ValueError("native original observations changed")
        row.update({
            "status":"ok","n_trials":len(recorded.curve_ids),"n_points":n,
            "pointwise_true_slope":target,"pointwise_estimate":est,
            "model_projection_bias":projection-target,
            "observed_point_bias":est-target,
            "qr_max_discrepancy":delta,
            "native_source_preserved":True,
            "existing_W3_rejects_native":True
        })
    except Exception as exc:
        row["exception"]={"type":type(exc).__name__,"message":str(exc)[:900]}
    return row


def audit(rows):
    expected={(b,s,l,t) for b in range(BLOCKS) for s in SCHEMES
              for l in LOSSES for t in TRUTHS}
    ids=[(r["block"],r["trial_scheme"],r["loss"],r["truth_mode"]) for r in rows]
    if len(set(ids))!=len(ids) or not set(ids).issubset(expected):
        raise ValueError("duplicate or undeclared original generating source case")
    missing=sorted(f"{b}:{s}:{l}:{t}" for b,s,l,t in expected-set(ids))
    good=[r for r in rows if r["status"]=="ok"]
    groups={}
    for sch in SCHEMES:
        groups[sch]={}
        for loss in LOSSES:
            groups[sch][loss]={}
            for truth in TRUTHS:
                sub=[r for r in good if r["trial_scheme"]==sch and
                     r["loss"]==loss and r["truth_mode"]==truth]
                n=len(sub)
                methods={}
                for method in METHODS:
                    success=sum(bool(r["methods"][method]["included_known_truth"]) for r in sub)
                    methods[method]={
                        "attempted":BLOCKS,"completed":n,
                        "truth_inclusion_count":success,
                        "truth_inclusion_completed_rate":success/n if n else None,
                        "wilson95_completed_only":wilson(success,n),
                        "mean_standard_error":float(np.mean(
                            [r["methods"][method]["se"] for r in sub])) if n else None,
                        "mean_interval_width":float(np.mean(
                            [r["methods"][method]["width"] for r in sub])) if n else None,
                    }
                groups[sch][loss][truth]={
                    "attempted":BLOCKS,"completed":n,
                    "methods":methods,
                    "mean_model_projection_bias":float(np.mean([
                        r["model_projection_bias"] for r in sub])) if n else None,
                    "mean_point_bias":float(np.mean([
                        r["observed_point_bias"] for r in sub])) if n else None,
                    "qr_and_native_integrity_pass":sum(bool(r["native_source_preserved"]
                        and r["existing_W3_rejects_native"]
                        and r["qr_max_discrepancy"]<=TOL) for r in sub),
                }
    return {
        "study":STUDY,"seed":SEED,
        "independent_source_blocks":BLOCKS,
        "n_source_participants":N,
        "paired_truth_trial_dropout_regimes_share_one_source_per_block":True,
        "basis_degree":POLY_DEGREE,
        "localized_nonbasis_slope_bump":BUMP_AMPLITUDE,
        "pointwise_time_index":FOCAL_TIME,
        "pointwise_nominal_confidence":CONFIDENCE,
        "planned_cases":len(expected),"recorded_cases":len(rows),
        "completed_cases":len(good),"failed_cases":len(rows)-len(good),
        "missing_cases":missing,"groups":groups,
        "not_simultaneous_function_coverage":True,
        "independent_unit_is_participant_not_trial":True,
        "no_model_selection_or_release":True,
        "scientific_cluster_calibration_qualified":False,
        "release_authorized":False
    }


def figure(summary,path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    labels=[];naive=[];trial=[];participant=[]
    for scheme in SCHEMES:
        for truth in TRUTHS:
            for loss in LOSSES:
                c=summary["groups"][scheme][loss][truth]["methods"]
                labels.append(f"{scheme[:3]}-{truth[:4]}-{loss[:4]}")
                naive.append(c["naive_hc1"]["truth_inclusion_completed_rate"])
                trial.append(c["trial_cr1"]["truth_inclusion_completed_rate"])
                participant.append(c["participant_cr1"]["truth_inclusion_completed_rate"])
    fig,ax=plt.subplots(figsize=(12,4.6))
    x=np.arange(len(labels))
    ax.plot(x,naive,marker="o",label="Naive observation-level HC1")
    ax.plot(x,trial,marker="s",label="Trial-cluster CR1")
    ax.plot(x,participant,marker="^",label="Participant-cluster CR1")
    ax.axhline(CONFIDENCE,linestyle="--",color="black",label="90% target")
    ax.set_ylim(0,1)
    ax.set_xticks(x,labels,rotation=30,ha="right")
    ax.set_ylabel("Pointwise true slope inclusion / 64 blocks")
    ax.set_title("W3 R8: numerical cluster-uncertainty and mean-model stress")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path,format="svg",metadata={"Date":None})
    plt.close(fig)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    rows=[evaluate(b,s,l,t) for b in range(BLOCKS)
          for s in SCHEMES for l in LOSSES for t in TRUTHS]
    info=audit(rows)
    for filename,content in (("case-ledger.json",rows),("evidence.json",info)):
        (args.out/filename).write_text(json.dumps(content,indent=2,sort_keys=True)+"\n")
    figure(info,args.out/"source-cluster-pointwise.svg")
    (args.out/"source-commit.txt").write_text(os.getenv("GITHUB_SHA","unverified-local")+"\n")
    names=("case-ledger.json","evidence.json","source-cluster-pointwise.svg","source-commit.txt")
    (args.out/"SHA256SUMS").write_text("".join(
        sha256((args.out/f).read_bytes()).hexdigest()+f"  {f}\n" for f in names))
    print("W3 R8 PARTICIPANT CLUSTER STRESS AUDIT:",json.dumps(info,sort_keys=True))
    if info["failed_cases"] or info["missing_cases"]:
        raise SystemExit("incomplete original R8 source—keep failure ledger")
    # No coverage threshold, nominal calibration, winner or release gate.


if __name__=="__main__":
    main()
