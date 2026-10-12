"""W3 R11: paired complete vs MCAR/MAR/MNAR observation support at native times.

RESEARCH ONLY. Original 96 generating blocks of 48 independent people with
unequal 1-3 asynchronous trials. Each source block and mean truth generates
identical complete responses, participants, time jitter and dropout uniforms
across complete/MCAR/observed-x MAR/latent-residual MNAR. No imputation or
reverse reconstruction. Existing complete-grid W3 remains fail-closed.

Evaluate two predeclared fixed mean bases via the independent source-only
R9 reference: degree-five Legendre and 13-function cubic spline. Separately
record true-source projection error, complete-support error, loss-induced
paired estimator displacement, and nominal 90% *pointwise* participant CR1
truth inclusion. No method selection, MAR identification, calibrated bands
or production API. Coverage is not a CI-success threshold.
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
from scipy.stats import norm

from eyetrajectoriespy import IrregularTrajectorySet
from eyetrajectoriespy.workflows import FunctionOnScalarWorkflowConfig, run_function_on_scalar_workflow
from scripts.run_w3_r9_mean_basis_selection_stress import (
    fit_model, TIME, DIMS, truth_coefficients, localized_bump
)

STUDY="W3_R11_PAIRED_OBSERVATION_PROCESS_DECOMPOSITION_20261013"
SEED=202610131107
BLOCKS=96
N_PARTICIPANTS=48
MAX_TRIALS=3
TRUTHS=("baseline","localized_bump")
OBSERVATION=("complete","mcar","mar_observed_x","latent_mnar")
MODELS=("legendre5","cubic_spline13")
FOCAL=15
GAP=slice(11,19)
CONFIDENCE=.9
MC_BOOTSTRAP_DRAWS=3000
NUMERICAL_TOL=4e-7


def logistic(z):
    z=np.asarray(z,float)
    return 1/(1+np.exp(-np.clip(z,-35,35)))


def original_full_source(block,truth_mode):
    """Return generated *complete* trajectories before observation masking."""
    if type(block) is not int or not 0<=block<BLOCKS:
        raise ValueError("original block outside predeclared R11 ledger")
    if truth_mode not in TRUTHS:
        raise ValueError("unplanned mean generating truth")
    rng=np.random.default_rng(SEED+20533*block)
    x=rng.uniform(-.95,.95,size=N_PARTICIPANTS)
    trial_alloc=rng.uniform(size=N_PARTICIPANTS)
    n_trials=(1+np.floor(MAX_TRIALS*trial_alloc)).astype(int)
    if not (np.all(n_trials>=1) and np.all(n_trials<=MAX_TRIALS)):
        raise ValueError("source trial support outside declared 1-3")

    jitter=np.clip(rng.normal(0,.006,size=(N_PARTICIPANTS,MAX_TRIALS,len(TIME))),
                   -.010,.010)
    jitter[:,:,0]=0.;jitter[:,:,-1]=0.
    timestamps=TIME[None,None,:]+jitter
    if not np.all(np.diff(timestamps,axis=2)>0):
        raise ValueError("nonmonotonic native source timestamps")
    p_intercept=rng.normal(0,.08,size=(N_PARTICIPANTS,1,1,len(DIMS)))
    p_slope=rng.normal(0,.045,size=(N_PARTICIPANTS,1,1,len(DIMS)))
    trial_intercept=rng.normal(0,.025,size=(N_PARTICIPANTS,MAX_TRIALS,1,len(DIMS)))
    noise=rng.normal(0,.045,size=(N_PARTICIPANTS,MAX_TRIALS,len(TIME),len(DIMS)))
    conditional_mean=np.empty_like(noise)
    for i in range(N_PARTICIPANTS):
        for j in range(MAX_TRIALS):
            theta=truth_coefficients(timestamps[i,j])
            conditional_mean[i,j]=theta[0]+x[i]*theta[1]
            if truth_mode=="localized_bump":
                conditional_mean[i,j,:,0]+=x[i]*localized_bump(timestamps[i,j])

    responses=(conditional_mean
        + p_intercept*(1+.30*timestamps[...,None])
        + p_slope*x[:,None,None,None]*(1+.25*timestamps[...,None])
        + trial_intercept+noise)
    dropout_draws=rng.uniform(size=(N_PARTICIPANTS,MAX_TRIALS))
    real_truth=truth_coefficients(TIME)[1,:,0].copy()
    if truth_mode=="localized_bump":
        real_truth+=localized_bump(TIME)
    return {"block":block,"truth_mode":truth_mode,"x":x,
            "n_trials":n_trials,"time":timestamps,"values":responses,
            "conditional_mean":conditional_mean,
            "dropout_uniforms":dropout_draws,"true_slope":real_truth}


def recorded_case(src,mechanism):
    if mechanism not in OBSERVATION:
        raise ValueError("unplanned observation mechanism")
    x=src["x"]
    if mechanism=="complete":
        probability=np.zeros_like(src["dropout_uniforms"])
    elif mechanism=="mcar":
        probability=np.full_like(src["dropout_uniforms"],.30)
    elif mechanism=="mar_observed_x":
        probability=np.broadcast_to(logistic(-.85+1.2*x)[:,None],
                                     src["dropout_uniforms"].shape)
    else:
        hidden=(src["values"][:,:,FOCAL,0]-
                src["conditional_mean"][:,:,FOCAL,0])
        probability=logistic(-.85+1.2*x[:,None]+2.0*hidden/.11)
    lost=src["dropout_uniforms"]<probability
    native_t=[];native_y=[];mu=[];units=[];trials=[];condition=[]
    observed_mask=[]
    for i in range(N_PARTICIPANTS):
        for j in range(int(src["n_trials"][i])):
            keep=np.ones(len(TIME),dtype=bool)
            if lost[i,j]:
                keep[GAP]=False
            native_t.append(src["time"][i,j,keep].copy())
            native_y.append(src["values"][i,j,keep].copy())
            mu.append(src["conditional_mean"][i,j,keep,0].copy())
            units.append(i);trials.append(i*MAX_TRIALS+j);condition.append(x[i])
            observed_mask.append(keep)
    ids=tuple(f"P{i:03d}-T{j%MAX_TRIALS:02d}" for i,j in zip(units,trials))
    metadata=pd.DataFrame({
        "participant_id":[f"P{i:03d}" for i in units],
        "trial_id":[j%MAX_TRIALS for j in trials]
    })
    gaze=IrregularTrajectorySet(
        time=tuple(native_t),values=tuple(native_y),curve_ids=ids,
        dimension_names=DIMS,time_unit="s",coordinate_system="normalized",
        metadata=metadata,provenance={
            "study":STUDY,"original_block":src["block"],
            "generating_truth":src["truth_mode"],"observation":mechanism,
            "independent_unit":"participant","interpolation_performed":False,
            "simulation":True
        }
    )
    return {"gaze":gaze,"mean":tuple(mu),"x":np.asarray(condition),
            "units":np.asarray(units,dtype=int),
            "trials":np.asarray(trials,dtype=int),
            "mask":tuple(observed_mask),"n_gapped_trials":int(sum(
                len(t)<len(TIME) for t in gaze.time)),
            "n_observed_samples":int(sum(map(len,gaze.time)))}


def enforce_observed_source(src,rec):
    i=0
    for participant in range(N_PARTICIPANTS):
        for trial in range(int(src["n_trials"][participant])):
            mask=rec["mask"][i]
            if not np.array_equal(rec["gaze"].time[i],
                                  src["time"][participant,trial,mask]):
                raise ValueError("native observation timestamps changed")
            if not np.array_equal(rec["gaze"].values[i],
                                  src["values"][participant,trial,mask]):
                raise ValueError("native observed coordinates changed")
            if not np.array_equal(rec["mean"][i],
                                  src["conditional_mean"][participant,trial,mask,0]):
                raise ValueError("known-source means changed")
            i+=1
    if i!=len(rec["gaze"].time) or len(set(rec["units"]))!=N_PARTICIPANTS:
        raise ValueError("source participant/trial membership incomplete")


def interval_of_mean_paired(values,seed):
    if not values:
        return None
    v=np.asarray(values,float)
    rng=np.random.default_rng(seed)
    inds=rng.integers(0,len(v),size=(MC_BOOTSTRAP_DRAWS,len(v)))
    return [float(a) for a in np.quantile(v[inds].mean(axis=1),[.025,.975])]


def wilson(success,n):
    if not n:return None
    z=float(norm.ppf(.975));p=success/n
    den=1+z*z/n
    mid=(p+z*z/(2*n))/den
    spread=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [float(max(0,mid-spread)),float(min(1,mid+spread))]


def block_evidence(block,truth_mode):
    src=original_full_source(block,truth_mode)
    original=recorded_case(src,"complete")
    enforce_observed_source(src,original)
    if original["n_gapped_trials"]!=0:
        raise ValueError("complete original source should have no missing recorded gaps")
    benchmark={}
    for model in MODELS:
        f=fit_model(original["gaze"],original["mean"],original["x"],
                    original["units"],original["trials"],model)
        benchmark[model]=f
    rows=[]
    for mechanism in OBSERVATION:
        row={"study":STUDY,"block":block,"truth_mode":truth_mode,
             "observation":mechanism,"status":"failed","exception":None,
             "n_independent_participants":N_PARTICIPANTS,
             "n_trials":None,"n_gapped_trials":None,
             "n_observed_samples":None,"supported_dense_w3_rejected":False,
             "source_unchanged":False,"models":{},
             "is_model_selection":False,"uncertainty_qualified":False,
             "release_authorized":False}
        try:
            rec=recorded_case(src,mechanism)
            enforce_observed_source(src,rec)
            frame=pd.DataFrame({"curve_id":rec["gaze"].curve_ids,
                                "condition":rec["x"]})
            try:
                run_function_on_scalar_workflow(
                    rec["gaze"],frame,config=FunctionOnScalarWorkflowConfig(
                        predictors=("condition",),dimensions=DIMS,
                        unit="participant",participant_column="participant_id"
                    ))
            except TypeError as exc:
                if "IrregularTrajectorySet" not in str(exc):
                    raise
            else:
                raise ValueError("native irregular data unexpectedly accepted by W3")

            target=float(src["true_slope"][FOCAL])
            for model in MODELS:
                result=fit_model(rec["gaze"],rec["mean"],rec["x"],
                                  rec["units"],rec["trials"],model)
                full=benchmark[model]
                if (result["qr_error"]>NUMERICAL_TOL or
                    result["cluster_score_error"]>NUMERICAL_TOL):
                    raise ValueError("regression/numerical-score reference failed")
                if mechanism=="complete":
                    for key in ("point_estimate","projection","width"):
                        if abs(result[key]-full[key])>NUMERICAL_TOL:
                            raise ValueError("complete reference not exactly paired")
                row["models"][model]={
                    "true_mid_slope":target,
                    "point_estimate":float(result["point_estimate"]),
                    "pointwise_90pct_true_included":bool(
                        result["lower"]<=target<=result["upper"]),
                    "se":float(result["se"]),
                    "width":float(result["width"]),
                    "true_point_error":float(result["point_estimate"]-target),
                    "known_mean_projection_error":float(result["projection"]-target),
                    "paired_loss_point_shift_vs_complete":float(
                        result["point_estimate"]-full["point_estimate"]),
                    "paired_loss_projection_shift_vs_complete":float(
                        result["projection"]-full["projection"]),
                    "slope_rmse":float(np.sqrt(np.mean(
                        (np.asarray(result["slope"])-src["true_slope"])**2))),
                    "qr_oracle":float(result["qr_error"]),
                    "score_oracle":float(result["cluster_score_error"]),
                }
            row.update({"status":"ok","n_trials":len(rec["gaze"].curve_ids),
                        "n_gapped_trials":rec["n_gapped_trials"],
                        "n_observed_samples":rec["n_observed_samples"],
                        "supported_dense_w3_rejected":True,"source_unchanged":True})
        except Exception as exc:
            row["exception"]={"type":type(exc).__name__,"message":str(exc)[:900]}
        rows.append(row)
    return rows


def audit(rows):
    expected={(b,t,m) for b in range(BLOCKS) for t in TRUTHS for m in OBSERVATION}
    ids=[(r["block"],r["truth_mode"],r["observation"]) for r in rows]
    if len(set(ids))!=len(ids) or not set(ids).issubset(expected):
        raise ValueError("duplicate or unplanned original R11 source cases")
    missing=sorted(f"{b}:{t}:{m}" for b,t,m in expected-set(ids))
    success=[r for r in rows if r["status"]=="ok"]
    groups={}
    for truth in TRUTHS:
        groups[truth]={}
        for ob in OBSERVATION:
            pool=sorted((r for r in success if r["truth_mode"]==truth
                         and r["observation"]==ob),key=lambda v:v["block"])
            group={"planned_blocks":BLOCKS,"completed_blocks":len(pool),
                   "n_observed_samples_mean":float(np.mean(
                       [v["n_observed_samples"] for v in pool])) if pool else None,
                   "n_gapped_trials_mean":float(np.mean(
                       [v["n_gapped_trials"] for v in pool])) if pool else None,
                   "source_contracts_passed":sum(v["source_unchanged"] and
                        v["supported_dense_w3_rejected"] and
                        all(u["qr_oracle"]<=NUMERICAL_TOL and
                            u["score_oracle"]<=NUMERICAL_TOL
                            for u in v["models"].values()) for v in pool),
                   "models":{}}
            for model in MODELS:
                ms=[v["models"][model] for v in pool]
                n=len(ms)
                covered=sum(k["pointwise_90pct_true_included"] for k in ms)
                fields=("true_point_error","known_mean_projection_error",
                        "paired_loss_point_shift_vs_complete",
                        "paired_loss_projection_shift_vs_complete",
                        "width","slope_rmse")
                measures={}
                for field in fields:
                    values=[v[field] for v in ms]
                    measures[field]={
                        "mean":float(np.mean(values)) if values else None,
                        "paired_independent_block_bootstrap95":interval_of_mean_paired(
                            values,seed=SEED+101*sum(map(ord,truth))+
                            131*sum(map(ord,ob))+17*sum(map(ord,model))+
                            sum(map(ord,field))
                        ),
                        "completed_denominator":n,
                        "planned_denominator":BLOCKS,
                    }
                group["models"][model]={
                    "attempted":BLOCKS,"completed":n,
                    "pointwise_true_count":covered,
                    "pointwise_true_rate_completed":covered/n if n else None,
                    "wilson95_completed":wilson(covered,n),
                    "metrics":measures}
            groups[truth][ob]=group
    return {
        "study":STUDY,"seed":SEED,
        "independent_generating_blocks":BLOCKS,
        "n_independent_participants_per_block":N_PARTICIPANTS,
        "matched_underlying_data_across_observation_mechanisms":True,
        "only_matched_mechanism_masks_differ_within_truth":True,
        "pointwise_nominal_level":CONFIDENCE,
        "original_mean_bases":list(MODELS),
        "original_observation_mechanisms":list(OBSERVATION),
        "planned_cases":len(expected),"recorded_cases":len(rows),
        "completed_cases":len(success),"failed_cases":len(rows)-len(success),
        "missing_cases":missing,"groups":groups,
        "no_imputation_or_missingness_identification":True,
        "simultaneous_band_qualified":False,"no_general_method_selection":True,
        "release_authorized":False
    }


def source_plot(evidence,path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(11,5))
    x=np.arange(len(OBSERVATION))
    for truth in TRUTHS:
        for model in MODELS:
            y=[evidence["groups"][truth][ob]["models"][model][
                "pointwise_true_rate_completed"] for ob in OBSERVATION]
            ax.plot(x,y,marker="o",label=f"{truth} / {model}")
    ax.axhline(CONFIDENCE,linestyle="--",color="black",label="90% pointwise nominal")
    ax.set_ylim(0,1)
    ax.set_xticks(x,("Complete","MCAR","Observed-x MAR","Latent MNAR"))
    ax.set_ylabel("Known-truth 90% pointwise interval inclusion")
    ax.set_title("W3 R11: exact same source trajectories, observation mechanisms varied")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path,format="svg",metadata={"Date":None})
    plt.close(fig)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    rows=[]
    for block in range(BLOCKS):
        for truth in TRUTHS:
            rows.extend(block_evidence(block,truth))
    report=audit(rows)
    for name,obj in (("case-ledger.json",rows),("evidence.json",report)):
        (args.out/name).write_text(json.dumps(obj,sort_keys=True,indent=2)+"\n")
    source_plot(report,args.out/"source-paired-observation-process.svg")
    (args.out/"source-commit.txt").write_text(os.getenv("GITHUB_SHA","unverified-local")+"\n")
    filenames=("case-ledger.json","evidence.json",
               "source-paired-observation-process.svg","source-commit.txt")
    (args.out/"SHA256SUMS").write_text("".join(
        sha256((args.out/f).read_bytes()).hexdigest()+f"  {f}\n"
        for f in filenames))
    print("W3 R11 PAIRED OBSERVATION PROCESS AUDIT:",
          json.dumps(report,sort_keys=True))
    if report["failed_cases"] or report["missing_cases"]:
        raise SystemExit("original source incomplete: failures retained in ledger")


if __name__=="__main__":
    main()
