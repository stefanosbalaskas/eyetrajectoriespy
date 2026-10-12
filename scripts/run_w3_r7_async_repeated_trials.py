"""W3 R7: asynchronous repeated-trial observation support with participant weighting.

Research only. 64 fresh independent generating blocks, n=48 participants x
up to 3 repeated trials, curve-specific genuinely jittered times, paired
recording loss and balanced/unbalanced trial support. No time interpolation,
participant deletion, mixed-model inference or API promotion.
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

from eyetrajectoriespy import IrregularTrajectorySet
from eyetrajectoriespy.workflows import (
    FunctionOnScalarWorkflowConfig, run_function_on_scalar_workflow,
)
from scripts.run_w3_r6_asynchronous_basis import basis, TIME, DIMS, truth_coefficients, expit

STUDY="W3_R7_ASYNC_REPEATED_TRIALS_20261012"
SEED=202610122227
BLOCKS=64
N_PARTICIPANTS=48
MAX_TRIALS=3
TRIAL_SCHEMES=("balanced3", "unbalanced1to3")
LOSS_MECHANISMS=("mcar", "latent_response_dependent")
WEIGHTINGS=("sample", "trial", "participant")
GAP=slice(11,19)
MIDPOINT=15
DEGREE=5
TOL=2e-8
MC_DRAWS=2000


def generate(block, trial_scheme, mechanism):
    if type(block) is not int or not 0<=block<BLOCKS:
        raise ValueError("generating block outside independent ledger")
    if trial_scheme not in TRIAL_SCHEMES or mechanism not in LOSS_MECHANISMS:
        raise ValueError("undeclared hierarchical scientific scenario")
    rng=np.random.default_rng(SEED+15443*block)
    x=rng.uniform(-.95,.95,size=N_PARTICIPANTS)
    trials_uniform=rng.uniform(size=N_PARTICIPANTS)
    k=np.full(N_PARTICIPANTS,MAX_TRIALS,dtype=int) if trial_scheme=="balanced3" else (
        1+np.floor(MAX_TRIALS*trials_uniform).astype(int)
    )
    jitter=np.clip(
        rng.normal(0,.006,size=(N_PARTICIPANTS,MAX_TRIALS,len(TIME))),
        -.010,.010
    )
    jitter[:,:,0]=0
    jitter[:,:,-1]=0
    timestamps=TIME[None,None,:]+jitter
    if not np.all(np.diff(timestamps,axis=2)>0):
        raise ValueError("generated nonmonotonic asynchronous timestamps")

    participant_intercept=rng.normal(0,.08,size=(N_PARTICIPANTS,1,1,len(DIMS)))
    participant_slope=rng.normal(0,.045,size=(N_PARTICIPANTS,1,1,len(DIMS)))
    trial_effect=rng.normal(0,.025,size=(N_PARTICIPANTS,MAX_TRIALS,1,len(DIMS)))
    sensor_noise=rng.normal(
        0,.045,size=(N_PARTICIPANTS,MAX_TRIALS,len(TIME),len(DIMS))
    )
    true_mean=np.empty_like(sensor_noise)
    for i in range(N_PARTICIPANTS):
        for j in range(MAX_TRIALS):
            true=truth_coefficients(timestamps[i,j])
            true_mean[i,j]=true[0]+x[i]*true[1]
    # Shared participant random slope/intercept creates dependence between
    # the repeated trials from one participant.
    values=(true_mean
        + participant_intercept * (1+.30*timestamps[...,None])
        + participant_slope*x[:,None,None,None] * (1+.25*timestamps[...,None])
        + trial_effect + sensor_noise)
    loss_uniform=rng.uniform(size=(N_PARTICIPANTS,MAX_TRIALS))
    if mechanism=="mcar":
        drop_probability=np.full((N_PARTICIPANTS,MAX_TRIALS),.30)
    else:
        latent_residual=values[:,:,MIDPOINT,0]-true_mean[:,:,MIDPOINT,0]
        drop_probability=expit(
            -.80+1.15*x[:,None]+2.0*latent_residual/.11
        )
    lost=loss_uniform<drop_probability

    full_times,full_values,observed_times,observed_values=[],[],[],[]
    participants,trial_labels,condition=[],[],[]
    for i in range(N_PARTICIPANTS):
        for j in range(int(k[i])):
            t=timestamps[i,j]
            y=values[i,j]
            mask=np.ones(len(TIME),dtype=bool)
            if lost[i,j]:
                mask[GAP]=False
            full_times.append(t.copy())
            full_values.append(y.copy())
            observed_times.append(t[mask].copy())
            observed_values.append(y[mask].copy())
            participants.append(f"P{i:03d}")
            trial_labels.append(j)
            condition.append(float(x[i]))
    ids=tuple(f"{p}-T{j:02d}" for p,j in zip(participants,trial_labels))
    metadata=pd.DataFrame({"participant_id":participants,"trial_id":trial_labels})
    provenance={"study":STUDY,"block":block,"simulation":True,
                "trial_scheme":trial_scheme,"missing_mechanism":mechanism,
                "interpolation_performed":False,
                "independent_unit":"participant"}
    full=IrregularTrajectorySet(
        time=tuple(full_times),values=tuple(full_values),
        curve_ids=ids,dimension_names=DIMS,metadata=metadata,
        coordinate_system="normalized",time_unit="s",
        provenance={**provenance,"source_observation":"complete"}
    )
    observed=IrregularTrajectorySet(
        time=tuple(observed_times),values=tuple(observed_values),
        curve_ids=ids,dimension_names=DIMS,metadata=metadata,
        coordinate_system="normalized",time_unit="s",
        provenance={**provenance,"source_observation":"recorded_only"}
    )
    return full,observed,np.asarray(condition),tuple(participants),k,lost,x,timestamps,values


def independent_basis_fit(gaze, condition, participant_ids, weighting):
    """Explicit participant membership; QR oracle validates OLS source."""
    if not isinstance(gaze,IrregularTrajectorySet):
        raise TypeError("native irregular source required")
    if weighting not in WEIGHTINGS:
        raise ValueError("undeclared weighting rule")
    if not (len(gaze.curve_ids)==len(condition)==len(participant_ids)):
        raise ValueError("curve-to-participant predictor map mismatch")
    if len(set(participant_ids))!=N_PARTICIPANTS:
        raise ValueError("pseudoreplication or missing source participants")

    trial_counts=pd.Series(list(participant_ids)).value_counts().to_dict()
    obs_blocks, y_blocks, scales=[],[],[]
    for idx,(t,y) in enumerate(zip(gaze.time,gaze.values)):
        if not np.all(np.diff(t)>0) or len(t)<15 or not np.isfinite(y).all():
            raise ValueError("invalid genuine native source observation support")
        B=basis(t)
        xx=float(condition[idx])
        obs_blocks.append(np.concatenate((B,B*xx),axis=1))
        y_blocks.append(np.asarray(y,float))
        if weighting=="sample":
            factor=1.
        elif weighting=="trial":
            factor=1./len(t)
        else:
            factor=1./(len(t)*trial_counts[participant_ids[idx]])
        scales.append(np.full(len(t),np.sqrt(factor)))
    Z=np.vstack(obs_blocks)
    Y=np.vstack(y_blocks)
    S=np.concatenate(scales)
    Zs=Z*S[:,None]
    Ys=Y*S[:,None]
    if np.linalg.matrix_rank(Zs)!=2*(DEGREE+1):
        raise ValueError("basis slope unidentifiable from observed repeated trials")
    theta=np.linalg.lstsq(Zs,Ys,rcond=None)[0]
    q,r=np.linalg.qr(Zs,mode="reduced")
    independent=np.linalg.solve(r,q.T@Ys)
    delta=float(np.max(np.abs(theta-independent)))
    if delta>TOL:
        raise ValueError("independent QR source numerical disagreement")
    B0=basis(TIME)
    fitted=np.stack((B0@theta[:DEGREE+1],B0@theta[DEGREE+1:]))
    return fitted,delta,len(Y),trial_counts


def mc_interval(values,seed):
    if not values:return None
    x=np.asarray(values,float)
    rng=np.random.default_rng(seed)
    indices=rng.integers(0,len(x),size=(MC_DRAWS,len(x)))
    return [float(v) for v in np.quantile(x[indices].mean(axis=1),[.025,.975])]


def evaluate(block,trial_scheme,mechanism):
    row={"study":STUDY,"block":block,"trial_scheme":trial_scheme,
         "mechanism":mechanism,"status":"failed","exception":None,
         "n_independent_participants":N_PARTICIPANTS,
         "n_original_trials":None,"n_original_observations":None,
         "n_observed_native_values":None,"n_trials_with_gaps":None,
         "n_participants_with_gap":None,"minimum_trial_count":None,
         "maximum_trial_count":None,"all_participants_preserved":False,
         "native_times_and_values_unchanged":False,
         "current_dense_W3_rejected_native":False,
         "full_source_slope_rmse":None,
         "sample_slope_rmse":None,"trial_slope_rmse":None,
         "participant_slope_rmse":None,
         "sample_midpoint_shift":None,"trial_midpoint_shift":None,
         "participant_midpoint_shift":None,
         "sample_qr_error":None,"trial_qr_error":None,
         "participant_qr_error":None,
         "method_promoted":False,"hierarchical_inference_qualified":False,
         "uncertainty_calibrated":False,"release_authorized":False}
    try:
        full,observed,cond,units,k,lost,x,times,y=generate(
            block,trial_scheme,mechanism
        )
        record=[(t.copy(),v.copy()) for t,v in zip(observed.time,observed.values)]
        frame=pd.DataFrame({"curve_id":observed.curve_ids,"condition":cond})
        try:
            run_function_on_scalar_workflow(
                observed,frame,config=FunctionOnScalarWorkflowConfig(
                    predictors=("condition",),dimensions=DIMS,unit="participant",
                    participant_column="participant_id")
            )
        except TypeError as exc:
            if "IrregularTrajectorySet" not in str(exc):raise
        else:raise ValueError("W3 dense public workflow fitted unsupported irregular data")

        f,fd,full_n,full_count=independent_basis_fit(full,cond,units,"participant")
        truth=truth_coefficients(TIME)
        outcomes={}
        for mode in WEIGHTINGS:
            fit,delta,obs_n,counts=independent_basis_fit(
                observed,cond,units,mode
            )
            outcomes[mode]={
                "rmse":float(np.sqrt(np.mean((fit[1]-truth[1])**2))),
                "midpoint":float(fit[1,MIDPOINT,0]-f[1,MIDPOINT,0]),
                "qr":delta,
            }
            if obs_n!=sum(len(v) for v in observed.values):
                raise ValueError("native observed support count mismatch")
            if counts!=full_count:
                raise ValueError("participant/trial membership changed with missing gaze")

        # Balanced three-trial design implies the trial and participant
        # objectives differ by a constant scalar only; coefficients identical.
        if trial_scheme=="balanced3":
            if abs(outcomes["trial"]["rmse"]-outcomes["participant"]["rmse"])>TOL:
                raise ValueError("equal-trial participant/trial weighting invariant failed")

        for (old_t,old_v),tt,v in zip(record,observed.time,observed.values):
            if not np.array_equal(old_t,tt) or not np.array_equal(old_v,v):
                raise ValueError("original recorded native source mutated")

        recorded_trial_gap=sum(len(t)<len(TIME) for t in observed.time)
        gap_participants=len({p for p,t in zip(units,observed.time) if len(t)<len(TIME)})
        if len(full.time)!=int(k.sum()) or recorded_trial_gap>int(k.sum()):
            raise ValueError("unequal trial support accounting failed")
        row.update({
            "status":"ok",
            "n_original_trials":int(k.sum()),
            "n_original_observations":int(full_n),
            "n_observed_native_values":int(sum(len(t) for t in observed.time)),
            "n_trials_with_gaps":int(recorded_trial_gap),
            "n_participants_with_gap":int(gap_participants),
            "minimum_trial_count":int(k.min()),
            "maximum_trial_count":int(k.max()),
            "all_participants_preserved":True,
            "native_times_and_values_unchanged":True,
            "current_dense_W3_rejected_native":True,
            "full_source_slope_rmse":float(np.sqrt(np.mean((f[1]-truth[1])**2))),
        })
        for mode in WEIGHTINGS:
            row[f"{mode}_slope_rmse"]=outcomes[mode]["rmse"]
            row[f"{mode}_midpoint_shift"]=outcomes[mode]["midpoint"]
            row[f"{mode}_qr_error"]=outcomes[mode]["qr"]
    except Exception as exc:
        row["exception"]={"type":type(exc).__name__,"message":str(exc)[:950]}
    return row


def audit(rows):
    expected={(b,t,m) for b in range(BLOCKS) for t in TRIAL_SCHEMES
              for m in LOSS_MECHANISMS}
    ids=[(r["block"],r["trial_scheme"],r["mechanism"]) for r in rows]
    if len(ids)!=len(set(ids)) or not set(ids).issubset(expected):
        raise ValueError("duplicate or unplanned independent-block study scenario")
    missing=sorted(f"{b}:{t}:{m}" for b,t,m in expected-set(ids))
    completed=[r for r in rows if r["status"]=="ok"]
    groups={}
    for i,trial_scheme in enumerate(TRIAL_SCHEMES):
        groups[trial_scheme]={}
        for j,mechanism in enumerate(LOSS_MECHANISMS):
            cases=[r for r in completed if r["trial_scheme"]==trial_scheme
                   and r["mechanism"]==mechanism]
            fields=("n_original_trials","n_trials_with_gaps",
                "n_participants_with_gap","full_source_slope_rmse",
                "sample_slope_rmse","trial_slope_rmse","participant_slope_rmse",
                "sample_midpoint_shift","trial_midpoint_shift",
                "participant_midpoint_shift")
            summaries={}
            for name in fields:
                vals=[r[name] for r in cases]
                summaries[name]={"mean":float(np.mean(vals)) if vals else None,
                    "block_bootstrap95":mc_interval(vals,
                        seed=SEED+317*i+123*j+sum(map(ord,name))),
                    "completed_denominator":len(vals),
                    "planned_denominator":BLOCKS}
            groups[trial_scheme][mechanism]={
                "attempted":BLOCKS,"completed":len(cases),
                "n_independent_participants_per_block":N_PARTICIPANTS,
                "support_and_qr_validated":sum(
                    r["all_participants_preserved"]
                    and r["native_times_and_values_unchanged"]
                    and r["current_dense_W3_rejected_native"]
                    and max(r["sample_qr_error"],r["trial_qr_error"],
                            r["participant_qr_error"])<=TOL for r in cases),
                "outcomes":summaries}
    return {"study":STUDY,"seed":SEED,
        "fresh_independent_blocks":BLOCKS,
        "n_independent_participants_per_block":N_PARTICIPANTS,
        "up_to_trials_per_participant":MAX_TRIALS,
        "paired_trials_and_dropout_share_one_source_per_block":True,
        "planned_cases":len(expected),"recorded_cases":len(rows),
        "completed_cases":len(completed),"failed_cases":len(rows)-len(completed),
        "missing_cases":missing,"groups":groups,
        "participant_rather_than_trial_is_independent_source_unit":True,
        "basis_predictions_are_not_imputed_gaze":True,
        "hierarchical_uncertainty_qualified":False,
        "missingness_identification_qualified":False,
        "release_authorized":False}


def original_plot(evidence,path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    x=np.arange(4)
    labels=[f"{t}\n{m}" for t in TRIAL_SCHEMES for m in LOSS_MECHANISMS]
    names=("full_source_slope_rmse","sample_slope_rmse",
        "trial_slope_rmse","participant_slope_rmse")
    title=("Full source participant-balanced","Observed sample-weighted",
        "Observed trial-balanced","Observed participant-balanced")
    fig,ax=plt.subplots(figsize=(11,4.8))
    for name,legend in zip(names,title):
        ys=[evidence["groups"][t][m]["outcomes"][name]["mean"]
            for t in TRIAL_SCHEMES for m in LOSS_MECHANISMS]
        ax.plot(x,ys,marker="o",label=legend)
    ax.set_xticks(x,labels)
    ax.set_ylabel("Mean slope RMSE relative to known truth")
    ax.set_title("W3 R7 repeated trials with genuine asynchronous times")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path,format="svg",metadata={"Date":None})
    plt.close(fig)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    rows=[evaluate(b,t,m) for b in range(BLOCKS)
          for t in TRIAL_SCHEMES for m in LOSS_MECHANISMS]
    evidence=audit(rows)
    for path,obj in (("case-ledger.json",rows),("evidence.json",evidence)):
        (args.out/path).write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")
    original_plot(evidence,args.out/"source-r7-hierarchical-async.svg")
    (args.out/"source-commit.txt").write_text(
        os.getenv("GITHUB_SHA","unverified-local")+"\n")
    files=("case-ledger.json","evidence.json",
           "source-r7-hierarchical-async.svg","source-commit.txt")
    (args.out/"SHA256SUMS").write_text("".join(
        sha256((args.out/f).read_bytes()).hexdigest()+f"  {f}\n" for f in files
    ))
    print("W3 R7 REPEATED TRIALS ASYNC AUDIT:",json.dumps(evidence,sort_keys=True))
    if evidence["failed_cases"] or evidence["missing_cases"]:
        raise SystemExit("original source study incomplete; retain failed cases")
    # No optimal weighting, inference, model validity or release status gate.


if __name__=="__main__":
    main()
