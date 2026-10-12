"""W3 R10: fresh independent participant pairs-bootstrap uncertainty validation.

64 fresh generating blocks; 48 participants with truly asynchronous one-to-
three repeated trials; paired MCAR/MNAR x smooth/localized-bump truths.
Compare fixed Legendre-5 vs fixed 13-function cubic-spline participant-level
CR1 t interval, cluster-pairs percentile and basic intervals, exactly 199
prespecified whole-participant resamples per model/case.

Original source recorded observations are immutable. Confidence is pointwise
at t=.5 only; results do NOT qualify a simultaneous band or method winner.
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
from scipy.stats import norm, t as t_distribution

from eyetrajectoriespy import IrregularTrajectorySet
from eyetrajectoriespy.workflows import FunctionOnScalarWorkflowConfig, run_function_on_scalar_workflow
from scripts.run_w3_r9_mean_basis_selection_stress import (
    basis, TIME, DIMS, truth_coefficients, localized_bump
)

STUDY="W3_R10_FRESH_PARTICIPANT_PAIRS_BOOTSTRAP_20261012"
SEED=20261012105731
BLOCKS=64
N_PARTICIPANTS=48
SCHEMES=("balanced3","unbalanced1to3")
LOSSES=("mcar","latent_response_dependent")
TRUTHS=("baseline","localized_bump")
MODELS=("legendre5","cubic_spline13")
INTERVALS=("participant_cr1","pairs_percentile","pairs_basic")
FOCAL=15
GAP=slice(11,19)
CONFIDENCE=.90
BOOTSTRAP_DRAWS=199
TOL=4e-7
MC_DRAWS=2000


def source(block,scheme,loss,truth_mode):
    if type(block) is not int or not 0<=block<BLOCKS:
        raise ValueError("block outside independently prespecified source")
    if scheme not in SCHEMES or loss not in LOSSES or truth_mode not in TRUTHS:
        raise ValueError("unplanned R10 source scenario")
    rng=np.random.default_rng(SEED+17041*block)
    x=rng.uniform(-.95,.95,size=N_PARTICIPANTS)
    trial_allocation=rng.uniform(size=N_PARTICIPANTS)
    n_trials=(np.full(N_PARTICIPANTS,3,dtype=int) if scheme=="balanced3"
              else 1+np.floor(3*trial_allocation).astype(int))
    jitter=np.clip(rng.normal(0,.006,size=(N_PARTICIPANTS,3,len(TIME))),-.01,.01)
    jitter[:,:,0]=0.;jitter[:,:,-1]=0.
    times=TIME[None,None,:]+jitter
    if not np.all(np.diff(times,axis=2)>0):
        raise ValueError("jittered genuine timestamps must be monotonic")
    p_intercept=rng.normal(0,.08,size=(N_PARTICIPANTS,1,1,len(DIMS)))
    p_slope=rng.normal(0,.045,size=(N_PARTICIPANTS,1,1,len(DIMS)))
    trial_effect=rng.normal(0,.025,size=(N_PARTICIPANTS,3,1,len(DIMS)))
    noise=rng.normal(0,.045,size=(N_PARTICIPANTS,3,len(TIME),len(DIMS)))
    mean=np.empty_like(noise)
    for i in range(N_PARTICIPANTS):
        for j in range(3):
            b=truth_coefficients(times[i,j])
            mean[i,j]=b[0]+x[i]*b[1]
            if truth_mode=="localized_bump":
                mean[i,j,:,0]+=x[i]*localized_bump(times[i,j])
    response=(mean+p_intercept*(1+.30*times[...,None])
              +p_slope*x[:,None,None,None]*(1+.25*times[...,None])
              +trial_effect+noise)
    uniforms=rng.uniform(size=(N_PARTICIPANTS,3))
    if loss=="mcar":
        prob=np.full((N_PARTICIPANTS,3),.30)
    else:
        latent=response[:,:,FOCAL,0]-mean[:,:,FOCAL,0]
        z=-.80+1.15*x[:,None]+2.0*latent/.11
        prob=1/(1+np.exp(-np.clip(z,-35,35)))
    gap=uniforms<prob
    measured_t=[];measured_y=[];conditional_mean=[]
    units=[];trials=[];conditions=[]
    for i in range(N_PARTICIPANTS):
        for j in range(int(n_trials[i])):
            keep=np.ones(len(TIME),bool)
            if gap[i,j]:
                keep[GAP]=False
            measured_t.append(times[i,j,keep].copy())
            measured_y.append(response[i,j,keep].copy())
            conditional_mean.append(mean[i,j,keep,0].copy())
            units.append(i)
            trials.append(3*i+j)
            conditions.append(float(x[i]))
    ids=tuple(f"P{i:03d}-T{j%3:02d}" for i,j in zip(units,trials))
    meta=pd.DataFrame({"participant_id":[f"P{i:03d}" for i in units],
                       "trial_id":[j%3 for j in trials]})
    recorded=IrregularTrajectorySet(
        time=tuple(measured_t),values=tuple(measured_y),
        curve_ids=ids,dimension_names=DIMS,time_unit="s",
        coordinate_system="normalized",metadata=meta,
        provenance={"study":STUDY,"block":block,"recording_loss":loss,
                    "truth_mode":truth_mode,"independent_unit":"participant",
                    "interpolation_performed":False,"simulation":True}
    )
    generating_truth=truth_coefficients(TIME)[1,:,0].copy()
    if truth_mode=="localized_bump":
        generating_truth+=localized_bump(TIME)
    return (recorded,tuple(conditional_mean),np.asarray(conditions),
            np.asarray(units,dtype=int),np.asarray(trials,dtype=int),
            generating_truth,n_trials)


def source_crossproducts(recorded,means,x,units,trials,model):
    """Construct original independent participant blocks, never trial blocks."""
    n_curves=len(recorded.curve_ids)
    if model not in MODELS or not(len(means)==len(x)==len(units)==len(trials)==n_curves):
        raise ValueError("invalid participant source/model map")
    if len(np.unique(units))!=N_PARTICIPANTS or len(np.unique(trials))!=n_curves:
        raise ValueError("missing or duplicated source participant/trial identity")
    counts=np.bincount(units,minlength=N_PARTICIPANTS)
    d=2*basis(np.array([.5]),model).shape[1]
    gram=np.zeros((N_PARTICIPANTS,d,d))
    cross=np.zeros((N_PARTICIPANTS,d))
    full_obs=[]
    full_design=[]
    full_y=[]
    full_mu=[]
    full_sqrt_w=[]
    all_times=[]
    for i,(tt,yy,mu) in enumerate(zip(recorded.time,recorded.values,means)):
        if not (len(tt)>=15 and np.all(np.diff(tt)>0) and np.isfinite(yy).all()):
            raise ValueError("original native source incomplete or nonmonotonic")
        B=basis(tt,model)
        X=np.concatenate((B,B*x[i]),axis=1)
        y=np.asarray(yy[:,0],float)
        w=1/(counts[units[i]]*len(tt))
        gram[units[i]]+=w*(X.T@X)
        cross[units[i]]+=w*(X.T@y)
        full_obs.append(np.asarray(tt))
        full_design.append(X)
        full_y.append(y)
        full_mu.append(np.asarray(mu))
        full_sqrt_w.append(np.full(len(tt),np.sqrt(w)))
        all_times.append(np.full(len(tt),units[i],dtype=int))
    A=np.vstack(full_design)
    Y=np.concatenate(full_y)
    MU=np.concatenate(full_mu)
    S=np.concatenate(full_sqrt_w)
    participants=np.concatenate(all_times)
    weights=S*S
    if not np.allclose(np.bincount(participants,weights=weights,minlength=N_PARTICIPANTS),
                       1.,atol=1e-12):
        raise ValueError("original participant total numerical weights incorrect")
    Q=gram.sum(axis=0)
    v=cross.sum(axis=0)
    theta=np.linalg.solve(Q,v)
    reference=np.linalg.lstsq(A*S[:,None],Y*S,rcond=None)[0]
    source_delta=float(np.max(np.abs(theta-reference)))
    if source_delta>TOL:
        raise ValueError("independent original weighted OLS numerical oracle mismatch")
    f=basis(np.array([TIME[FOCAL]]),model)[0]
    contrast=np.r_[np.zeros(len(f)),f]
    beta_known=np.linalg.lstsq(A*S[:,None],MU*S,rcond=None)[0]
    known_projection=float(contrast@beta_known)
    fitted=float(contrast@theta)
    residual=Y-A@theta
    # Independent group contribution reference: v_i - Q_i beta should
    # agree with sum of weighted original observation scores per participant.
    scores=cross-np.einsum("gij,j->gi",gram,theta)
    obs_scores=(A*(weights*residual)[:,None])
    independent=np.vstack([obs_scores[participants==g].sum(axis=0)
                           for g in range(N_PARTICIPANTS)])
    delta=float(np.max(np.abs(scores-independent)))
    if delta>TOL:
        raise ValueError("independent participant sandwich score oracle mismatch")
    return (gram,cross,contrast,theta,fitted,known_projection,
            source_delta,delta,int(len(Y)))


def cluster_bootstrap(gram,cross,contrast,estimate,seed,draws=BOOTSTRAP_DRAWS):
    """Whole-participant pairs draws, preserving all trials of each person.

    A replicated participant brings all of their original recorded source
    trials/time coordinates and retains the original within-participant
    weight normalization. Never resample individual timepoints or trials.
    """
    g=len(gram)
    if g!=N_PARTICIPANTS or draws<10:
        raise ValueError("invalid participant-resampling source unit/draw budget")
    rng=np.random.default_rng(seed)
    original_draws=rng.integers(0,g,size=(draws,g))
    copies=np.zeros((draws,g),dtype=float)
    np.add.at(copies,(np.arange(draws)[:,None],original_draws),1)
    q=np.einsum("bg,gij->bij",copies,gram)
    b=copies@cross
    try:
        fits=np.linalg.solve(q,b)
    except np.linalg.LinAlgError as exc:
        raise ValueError("one or more participant bootstrap refits rank deficient") from exc
    estimates=fits@contrast
    if not np.isfinite(estimates).all():
        raise ValueError("nonfinite participant bootstrap source estimates")
    alpha=(1-CONFIDENCE)/2
    lo,hi=np.quantile(estimates,(alpha,1-alpha))
    return {
        "percentile":[float(lo),float(hi)],
        "basic":[float(2*estimate-hi),float(2*estimate-lo)],
        "n_refits_completed":int(len(estimates)),
        "n_refits_planned":int(draws),
        "original_draw_indices_first":original_draws[0].tolist(),
        "original_draw_multiplicity_first":copies[0].astype(int).tolist(),
        "first_refit_estimate":float(estimates[0]),
        "bootstrap_estimate_mean":float(np.mean(estimates)),
        "bootstrap_estimate_sd":float(np.std(estimates,ddof=1)),
    }


def wilson(success,n):
    if not n:return None
    z=float(norm.ppf(.975));p=success/n
    den=1+z*z/n
    center=(p+z*z/(2*n))/den
    half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [float(max(0,center-half)),float(min(1,center+half))]


def evaluate(block,scheme,loss,truth_mode):
    row={"study":STUDY,"block":block,"scheme":scheme,
         "loss":loss,"truth_mode":truth_mode,
         "status":"failed","exception":None,
         "n_independent_participants":N_PARTICIPANTS,
         "n_supported_trials":None,"n_native_samples":None,
         "native_source_unchanged":False,"dense_W3_rejected_native":False,
         "models":{},"familywise_functional_coverage_qualified":False,
         "bootstrap_inference_qualified":False,
         "method_winner_selected":False,"release_authorized":False}
    try:
        recorded,means,x,units,trials,truth,k=source(
            block,scheme,loss,truth_mode
        )
        originals=[(tt.copy(),v.copy()) for tt,v in zip(recorded.time,recorded.values)]
        frame=pd.DataFrame({"curve_id":recorded.curve_ids,"condition":x})
        try:
            run_function_on_scalar_workflow(recorded,frame,
                config=FunctionOnScalarWorkflowConfig(
                    predictors=("condition",),dimensions=DIMS,
                    unit="participant",participant_column="participant_id"
                ))
        except TypeError as exc:
            if "IrregularTrajectorySet" not in str(exc):
                raise
        else:
            raise ValueError("existing dense W3 silently fit native irregular data")

        for mi,model in enumerate(MODELS):
            gram,cross,contrast,theta,estimate,projection,oracle,score_delta,nobs=(
                source_crossproducts(recorded,means,x,units,trials,model)
            )
            g=N_PARTICIPANTS
            bread=np.linalg.inv(gram.sum(axis=0))
            scores=cross-np.einsum("gij,j->gi",gram,theta)
            ncoef=len(theta)
            var=(g/(g-1))*((nobs-1)/(nobs-ncoef))*(
                contrast@bread@(scores.T@scores)@bread@contrast
            )
            if not np.isfinite(var) or var<=0:
                raise ValueError("nonpositive original participant CR1 variance")
            se=float(np.sqrt(var))
            crit=float(t_distribution.ppf((1+CONFIDENCE)/2,g-1))
            half=crit*se
            seed=int(SEED+9791*block+100000*SCHEMES.index(scheme)+
                     10000*LOSSES.index(loss)+1000*TRUTHS.index(truth_mode)+
                     101*mi)
            bootstrap=cluster_bootstrap(gram,cross,contrast,estimate,seed)
            bounds={
                "participant_cr1":[float(estimate-half),float(estimate+half)],
                "pairs_percentile":bootstrap["percentile"],
                "pairs_basic":bootstrap["basic"],
            }
            model_data={
                "estimate":estimate,"known_projection":projection,
                "projection_bias":float(projection-truth[FOCAL]),
                "point_error":float(estimate-truth[FOCAL]),
                "n_coefficients":ncoef,
                "source_qr_oracle_delta":oracle,
                "source_cluster_score_oracle_delta":score_delta,
                "mean_interval_width":None,
                "participant_cr1_se":se,
                "bootstrap_mean":bootstrap["bootstrap_estimate_mean"],
                "bootstrap_sd":bootstrap["bootstrap_estimate_sd"],
                "bootstrap_planned":bootstrap["n_refits_planned"],
                "bootstrap_completed":bootstrap["n_refits_completed"],
                "first_resampled_source_cluster_indices":
                    bootstrap["original_draw_indices_first"],
                "first_resampled_multiplicity":
                    bootstrap["original_draw_multiplicity_first"],
                "first_resampled_fitted_slope":
                    bootstrap["first_refit_estimate"],
                "intervals":{},
            }
            for method,(lo,hi) in bounds.items():
                model_data["intervals"][method]={
                    "lower":lo,"upper":hi,"width":hi-lo,
                    "known_truth_included":bool(lo<=truth[FOCAL]<=hi),
                }
            row["models"][model]=model_data

        for (tt,v),after_t,after_y in zip(
            originals,recorded.time,recorded.values
        ):
            if not np.array_equal(tt,after_t) or not np.array_equal(v,after_y):
                raise ValueError("original native source coordinates mutated")
        row.update({"status":"ok","n_supported_trials":len(recorded.curve_ids),
                    "n_native_samples":int(sum(len(tt) for tt in recorded.time)),
                    "native_source_unchanged":True,"dense_W3_rejected_native":True})
    except Exception as exc:
        row["exception"]={"type":type(exc).__name__,"message":str(exc)[:950]}
    return row


def audit(rows):
    expected={(b,s,l,t) for b in range(BLOCKS) for s in SCHEMES
              for l in LOSSES for t in TRUTHS}
    ids=[(r["block"],r["scheme"],r["loss"],r["truth_mode"]) for r in rows]
    if len(ids)!=len(set(ids)) or not set(ids).issubset(expected):
        raise ValueError("duplicate or undeclared original source scenario")
    missing=sorted(f"{b}:{s}:{l}:{t}" for b,s,l,t in expected-set(ids))
    good=[r for r in rows if r["status"]=="ok"]
    grouped={}
    for s in SCHEMES:
        grouped[s]={}
        for l in LOSSES:
            grouped[s][l]={}
            for t in TRUTHS:
                cell=sorted(
                    [r for r in good if (r["scheme"],r["loss"],r["truth_mode"])==(s,l,t)],
                    key=lambda r:r["block"])
                models={}
                for m in MODELS:
                    candidates=[r["models"][m] for r in cell]
                    methods={}
                    for name in INTERVALS:
                        success=sum(a["intervals"][name]["known_truth_included"]
                                    for a in candidates)
                        methods[name]={
                            "planned_cases":BLOCKS,"completed_cases":len(candidates),
                            "truth_count":success,
                            "pointwise_truth_rate":success/len(candidates) if candidates else None,
                            "wilson95":wilson(success,len(candidates)),
                            "mean_width":float(np.mean(
                                [a["intervals"][name]["width"] for a in candidates]
                            )) if candidates else None,
                        }
                    models[m]={
                        "methods":methods,
                        "n_bootstrap_refits_planned":BLOCKS*BOOTSTRAP_DRAWS,
                        "n_bootstrap_refits_completed":sum(
                            a["bootstrap_completed"] for a in candidates),
                        "mean_projection_bias":float(np.mean(
                            [a["projection_bias"] for a in candidates]
                        )) if candidates else None,
                        "mean_point_error":float(np.mean(
                            [a["point_error"] for a in candidates]
                        )) if candidates else None,
                        "source_oracle_passes":sum(
                            r["source_qr_oracle_delta"]<=TOL
                            and r["source_cluster_score_oracle_delta"]<=TOL
                            for r in candidates),
                    }
                grouped[s][l][t]={"attempted":BLOCKS,
                                   "completed":len(cell),"models":models}
    return {"study":STUDY,"seed":SEED,
            "n_fresh_independent_source_blocks":BLOCKS,
            "n_independent_participants_per_block":N_PARTICIPANTS,
            "paired_source_scenarios_share_generating_innovations":True,
            "bootstrap_draws_per_model_case":BOOTSTRAP_DRAWS,
            "whole_participant_resampling_only":True,
            "planned_cases":len(expected),
            "recorded_cases":len(rows),
            "completed_cases":len(good),
            "failed_cases":len(rows)-len(good),
            "missing_cases":missing,
            "groups":grouped,
            "pointwise_nominal_level":CONFIDENCE,
            "not_simultaneous_coverage":True,
            "participant_bootstrap_calibration_qualified":False,
            "missingness_correction_qualified":False,
            "basis_selection_qualified":False,
            "release_authorized":False}


def figure(report,path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    cells=[(s,l,t) for s in SCHEMES for t in TRUTHS for l in LOSSES]
    labels=[f"{s[:3]}-{t[:4]}-{l[:4]}" for s,l,t in cells]
    fig,axes=plt.subplots(2,1,figsize=(12,7.3),sharex=True)
    for ax,model in zip(axes,MODELS):
        for method in INTERVALS:
            y=[report["groups"][s][l][t]["models"][model]["methods"][method][
                "pointwise_truth_rate"] for s,l,t in cells]
            ax.plot(np.arange(len(cells)),y,marker="o",label=method)
        ax.axhline(CONFIDENCE,color="black",linestyle="--")
        ax.set_ylim(0,1)
        ax.set_ylabel("Pointwise truth inclusion")
        ax.set_title(model)
    axes[0].legend(fontsize=9)
    axes[-1].set_xticks(np.arange(len(labels)),labels,rotation=35,ha="right")
    fig.suptitle("W3 R10: 90% participant-cluster versus pairs-bootstrap pointwise intervals")
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
    for name,obj in (("case-ledger.json",rows),("evidence.json",info)):
        (args.out/name).write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")
    figure(info,args.out/"source-pairs-bootstrap-pointwise.svg")
    (args.out/"source-commit.txt").write_text(os.getenv("GITHUB_SHA","unverified-local")+"\n")
    names=("case-ledger.json","evidence.json",
           "source-pairs-bootstrap-pointwise.svg","source-commit.txt")
    (args.out/"SHA256SUMS").write_text("".join(
        sha256((args.out/f).read_bytes()).hexdigest()+f"  {f}\n" for f in names))
    print("W3 R10 ORIGINAL PARTICIPANT BOOTSTRAP AUDIT:",
          json.dumps(info,sort_keys=True))
    if info["failed_cases"] or info["missing_cases"]:
        raise SystemExit("incomplete original cluster-pairs research ledger")
    # Scientific coverage is NOT a CI pass threshold.


if __name__=="__main__":
    main()
