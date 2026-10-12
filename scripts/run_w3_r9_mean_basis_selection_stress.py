"""W3 R9 prespecified mean-basis sensitivity under native participant clusters.

64 NEW independent blocks of 48 participants each. Eight paired scenarios
(balanced/unbalanced trials x MCAR/outcome-dependent loss x smooth/local
slope truth), each analyzed with three fixed, *non-selected* mean bases:
Legendre degree 5, Legendre degree 11 and cubic B-splines with interior
knots fixed at 0.1,...,0.9. Participant CR1 pointwise uncertainty only.

This is NOT a new public estimator, calibrated functional confidence band,
causal missingness adjustment, or evidence for automatic model selection.
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
from scipy.interpolate import BSpline
from scipy.stats import t as student_t, norm

from eyetrajectoriespy import IrregularTrajectorySet
from eyetrajectoriespy.workflows import FunctionOnScalarWorkflowConfig, run_function_on_scalar_workflow
from scripts.run_w3_r6_asynchronous_basis import TIME, DIMS, truth_coefficients

STUDY="W3_R9_PRESPECIFIED_MEAN_BASIS_FRESH_SOURCE_20261012"
SEED=202610129917
BLOCKS=64
N=48
SCHEMES=("balanced3","unbalanced1to3")
LOSSES=("mcar","latent_response_dependent")
TRUTHS=("baseline","localized_bump")
MODELS=("legendre5","legendre11","cubic_spline13")
FOCAL=15
GAP=slice(11,19)
BUMP_AMP=.15
BUMP_SIGMA=.055
CONFIDENCE=.9
MC_DRAWS=2000
TOL=4e-7
KNOTS=np.r_[np.repeat(0.,4), np.linspace(.1,.9,9),np.repeat(1.,4)]
N_SPLINE=len(KNOTS)-4


def localized_bump(t):
    return BUMP_AMP*np.exp(-.5*((np.asarray(t)-.5)/BUMP_SIGMA)**2)


def basis(t,model):
    t=np.asarray(t,float)
    if model=="legendre5":
        return np.polynomial.legendre.legvander(2*t-1,5)
    if model=="legendre11":
        return np.polynomial.legendre.legvander(2*t-1,11)
    if model=="cubic_spline13":
        return BSpline.design_matrix(t,KNOTS,3,extrapolate=False).toarray()
    raise ValueError("unplanned basis model")


def source(block,scheme,loss,truth_mode):
    if type(block) is not int or not 0<=block<BLOCKS:
        raise ValueError("source block outside preregistered independent generator")
    if scheme not in SCHEMES or loss not in LOSSES or truth_mode not in TRUTHS:
        raise ValueError("unplanned R9 source scenario")
    rng=np.random.default_rng(SEED+17659*block)
    x=rng.uniform(-.95,.95,size=N)
    trial_uniform=rng.uniform(size=N)
    counts=(np.full(N,3,dtype=int) if scheme=="balanced3"
            else 1+np.floor(3*trial_uniform).astype(int))
    jitter=np.clip(rng.normal(0,.006,size=(N,3,len(TIME))),-.010,.010)
    jitter[:,:,0]=0;jitter[:,:,-1]=0
    native_times=TIME[None,None,:]+jitter
    if not np.all(np.diff(native_times,axis=2)>0):
        raise ValueError("generated native timestamps not strictly monotone")
    p_intercept=rng.normal(0,.08,size=(N,1,1,len(DIMS)))
    p_slope=rng.normal(0,.045,size=(N,1,1,len(DIMS)))
    trial_random=rng.normal(0,.025,size=(N,3,1,len(DIMS)))
    innovations=rng.normal(0,.045,size=(N,3,len(TIME),len(DIMS)))
    mean=np.empty_like(innovations)
    for i in range(N):
        for j in range(3):
            b=truth_coefficients(native_times[i,j])
            mean[i,j]=b[0]+x[i]*b[1]
            if truth_mode=="localized_bump":
                mean[i,j,:,0]+=x[i]*localized_bump(native_times[i,j])
    response=(mean+p_intercept*(1+.30*native_times[...,None])
              +p_slope*x[:,None,None,None]*(1+.25*native_times[...,None])
              +trial_random+innovations)
    draw=rng.uniform(size=(N,3))
    if loss=="mcar":
        dropout_p=np.full((N,3),.30)
    else:
        residual=response[:,:,FOCAL,0]-mean[:,:,FOCAL,0]
        linear=-.80+1.15*x[:,None]+2.0*residual/.11
        dropout_p=1/(1+np.exp(-np.clip(linear,-35,35)))
    gaps=draw<dropout_p

    obs_times=[];obs_y=[];observed_mu=[];individual=[];trial_ids=[];condition=[]
    for i in range(N):
        for j in range(int(counts[i])):
            keep=np.ones(len(TIME),bool)
            if gaps[i,j]:
                keep[GAP]=False
            obs_times.append(native_times[i,j,keep].copy())
            obs_y.append(response[i,j,keep].copy())
            observed_mu.append(mean[i,j,keep,0].copy())
            individual.append(i);trial_ids.append(3*i+j);condition.append(x[i])
    ids=tuple(f"P{i:03d}-T{(q%3):02d}" for i,q in zip(individual,trial_ids))
    metadata=pd.DataFrame({"participant_id":[f"P{i:03d}" for i in individual],
                           "trial_id":[j%3 for j in trial_ids]})
    gaze=IrregularTrajectorySet(
        time=tuple(obs_times),values=tuple(obs_y),curve_ids=ids,
        dimension_names=DIMS,coordinate_system="normalized",time_unit="s",
        metadata=metadata,provenance={"study":STUDY,"source_block":block,
            "generating_truth":truth_mode,"mechanism":loss,
            "independent_unit":"participant","interpolation_performed":False}
    )
    truth=truth_coefficients(TIME)[1,:,0].copy()
    if truth_mode=="localized_bump":
        truth+=localized_bump(TIME)
    return gaze,tuple(observed_mu),np.asarray(condition),np.asarray(individual),np.asarray(trial_ids),truth,counts


def fit_model(gaze,source_mu,x,participant,trial,model):
    if model not in MODELS:
        raise ValueError("unplanned model")
    ncurves=len(gaze.curve_ids)
    if not(len(source_mu)==len(x)==len(participant)==len(trial)==ncurves):
        raise ValueError("independent participant/trial map mismatch")
    if len(np.unique(participant))!=N or len(np.unique(trial))!=ncurves:
        raise ValueError("independent participants or trial identities lost")
    trial_counts=np.bincount(participant,minlength=N)
    designs=[];y=[];mu=[];weights=[];units=[]
    original=[(t.copy(),v.copy()) for t,v in zip(gaze.time,gaze.values)]
    for i,(t,v,m) in enumerate(zip(gaze.time,gaze.values,source_mu)):
        if len(t)<15 or not np.all(np.diff(t)>0) or not np.isfinite(v).all():
            raise ValueError("native observed source support invalid")
        B=basis(t,model)
        designs.append(np.column_stack((B,B*float(x[i]))))
        y.append(np.asarray(v[:,0]))
        mu.append(np.asarray(m))
        weight=1/(len(t)*trial_counts[participant[i]])
        weights.append(np.full(len(t),weight))
        units.append(np.full(len(t),participant[i],dtype=int))
    X=np.vstack(designs)
    Y=np.concatenate(y);MU=np.concatenate(mu);w=np.concatenate(weights)
    u=np.concatenate(units)
    if not np.allclose(np.bincount(u,weights=w,minlength=N),1.,atol=1e-12):
        raise ValueError("participant total weight must be one")
    scale=np.sqrt(w);A=X*scale[:,None];Bobs=Y*scale
    n,p=A.shape
    if np.linalg.matrix_rank(A)<p:
        raise ValueError("prespecified basis rank deficient on observed data")
    theta=np.linalg.lstsq(A,Bobs,rcond=None)[0]
    Q,R=np.linalg.qr(A,mode="reduced")
    independent_theta=np.linalg.solve(R,Q.T@Bobs)
    oracle_delta=float(np.max(np.abs(theta-independent_theta)))
    if oracle_delta>TOL:
        raise ValueError("independent QR least squares reference mismatch")
    beta_mu=np.linalg.lstsq(A,MU*scale,rcond=None)[0]
    n_basis=p//2
    basis_eval=basis(TIME,model)
    slope=basis_eval@theta[n_basis:]
    true_projection=basis_eval@beta_mu[n_basis:]
    contrast=np.zeros(p)
    contrast[n_basis:]=basis_eval[FOCAL]
    estimate=float(contrast@theta)
    projection=float(contrast@beta_mu)
    residual=Bobs-A@theta
    scores=A*residual[:,None]
    group_sums=np.zeros((N,p))
    np.add.at(group_sums,u,scores)
    independent_scores=np.vstack([scores[u==i].sum(axis=0) for i in range(N)])
    score_delta=float(np.max(np.abs(group_sums-independent_scores)))
    if score_delta>TOL:
        raise ValueError("independent participant-score sum oracle mismatch")
    bread=np.linalg.inv(A.T@A)
    group_cr1=(N/(N-1))*((n-1)/(n-p))
    meat=(group_sums.T@group_sums)*group_cr1
    v=float(contrast@bread@meat@bread@contrast)
    if not np.isfinite(v) or v<=0:
        raise ValueError("nonpositive original participant-cluster variance")
    se=float(np.sqrt(v))
    critical=float(student_t.ppf((1+CONFIDENCE)/2,N-1))
    half=critical*se
    if any(not np.array_equal(t,tt) or not np.array_equal(vv,v)
           for (t,vv),tt,v in zip(original,gaze.time,gaze.values)):
        raise ValueError("native source mutated during model fitting")
    return {"point_estimate":estimate,"projection":projection,
            "se":se,"width":2*half,"lower":estimate-half,
            "upper":estimate+half,"slope":slope.tolist(),
            "slope_projection":true_projection.tolist(),
            "qr_error":oracle_delta,"cluster_score_error":score_delta,
            "number_coefficients":p,"number_points":n}


def wilson(success,n):
    if n<1:return None
    z=float(norm.ppf(.975))
    q=success/n;denom=1+z*z/n
    center=(q+z*z/(2*n))/denom
    delta=z*np.sqrt(q*(1-q)/n+z*z/(4*n*n))/denom
    return [float(max(0,center-delta)),float(min(1,center+delta))]


def paired_interval(differences,seed):
    if not differences:return None
    d=np.asarray(differences,float)
    random=np.random.default_rng(seed)
    idx=random.integers(0,len(d),size=(MC_DRAWS,len(d)))
    return [float(v) for v in np.quantile(d[idx].mean(axis=1),[.025,.975])]


def evaluate(block,scheme,loss,truth_mode):
    row={"study":STUDY,"block":block,"scheme":scheme,"loss":loss,
         "truth_mode":truth_mode,"status":"failed","exception":None,
         "n_independent_participants":N,"n_trials":None,
         "n_source_observed_points":None,"true_slope_midpoint":None,
         "native_irregular_rejected_by_supported_W3":False,
         "all_recorded_source_values_preserved":False,
         "models":{},"pointwise_only":True,
         "simultaneous_calibration_qualified":False,
         "model_winner_selected":False,"release_authorized":False}
    try:
        gaze,mu,x,participant,trial,truth,counts=source(
            block,scheme,loss,truth_mode
        )
        original=[(t.copy(),v.copy()) for t,v in zip(gaze.time,gaze.values)]
        frame=pd.DataFrame({"curve_id":gaze.curve_ids,"condition":x})
        try:
            run_function_on_scalar_workflow(
                gaze,frame,config=FunctionOnScalarWorkflowConfig(
                    predictors=("condition",),dimensions=DIMS,
                    unit="participant",participant_column="participant_id"
                )
            )
        except TypeError as exc:
            if "IrregularTrajectorySet" not in str(exc):raise
            row["native_irregular_rejected_by_supported_W3"]=True
        else:raise ValueError("supported W3 unexpectedly accepted native irregular source")
        for name in MODELS:
            fit=fit_model(gaze,mu,x,participant,trial,name)
            slope=np.asarray(fit.pop("slope"),float)
            proj_slope=np.asarray(fit.pop("slope_projection"),float)
            fit["true_point_included"]=bool(
                fit["lower"]<=truth[FOCAL]<=fit["upper"]
            )
            fit["point_error"]=fit["point_estimate"]-truth[FOCAL]
            fit["projection_bias"]=fit["projection"]-truth[FOCAL]
            fit["slope_rmse"]=float(np.sqrt(np.mean((slope-truth)**2)))
            fit["projection_slope_rmse"]=float(
                np.sqrt(np.mean((proj_slope-truth)**2))
            )
            row["models"][name]=fit
        for (before_t,before_v),after_t,after_v in zip(
            original,gaze.time,gaze.values
        ):
            if not np.array_equal(before_t,after_t) or not np.array_equal(before_v,after_v):
                raise ValueError("genuine native source was changed")
        row.update({"status":"ok","n_trials":len(gaze.curve_ids),
                    "n_source_observed_points":int(sum(map(len,gaze.time))),
                    "true_slope_midpoint":float(truth[FOCAL]),
                    "all_recorded_source_values_preserved":True})
    except Exception as e:
        row["exception"]={"type":type(e).__name__,"message":str(e)[:1000]}
    return row


def audit(rows):
    expected={(b,s,l,t) for b in range(BLOCKS) for s in SCHEMES
              for l in LOSSES for t in TRUTHS}
    ids=[(r["block"],r["scheme"],r["loss"],r["truth_mode"]) for r in rows]
    if len(set(ids))!=len(ids) or not set(ids).issubset(expected):
        raise ValueError("duplicate or unplanned original generating case")
    missing=sorted(f"{b}:{s}:{l}:{t}" for b,s,l,t in expected-set(ids))
    completed=[r for r in rows if r["status"]=="ok"]
    groups={}
    for si,s in enumerate(SCHEMES):
        groups[s]={}
        for li,l in enumerate(LOSSES):
            groups[s][l]={}
            for ti,t in enumerate(TRUTHS):
                cell=sorted((r for r in completed if r["scheme"]==s and
                            r["loss"]==l and r["truth_mode"]==t),
                            key=lambda r:r["block"])
                method={}
                for mi,m in enumerate(MODELS):
                    records=[r["models"][m] for r in cell]
                    k=sum(bool(x["true_point_included"]) for x in records)
                    method[m]={
                        "attempted":BLOCKS,"completed":len(records),
                        "true_point_coverage_count":k,
                        "pointwise_coverage_rate_completed":k/len(records) if records else None,
                        "wilson95_completed":wilson(k,len(records)),
                        **{key:float(np.mean([v[key] for v in records])) if records else None
                           for key in ("se","width","point_error","projection_bias",
                                       "slope_rmse","projection_slope_rmse")},
                        "all_qr_and_cluster_oracles_pass":all(
                            r["qr_error"]<=TOL and
                            r["cluster_score_error"]<=TOL for r in records
                        ),
                    }
                paired={}
                if len(cell)==BLOCKS:
                    ref="legendre5"
                    for m in MODELS[1:]:
                        for field in ("projection_bias","slope_rmse"):
                            d=[r["models"][m][field]-r["models"][ref][field] for r in cell]
                            paired[f"{m}_minus_legendre5_{field}"]={
                                "mean":float(np.mean(d)),
                                "block_bootstrap95":paired_interval(
                                    d,seed=SEED+1001*si+131*li+31*ti+
                                    sum(map(ord,m+field))
                                ),
                                "independent_source_blocks":BLOCKS,
                            }
                        d=[float(r["models"][m]["true_point_included"])-
                           float(r["models"][ref]["true_point_included"]) for r in cell]
                        paired[f"{m}_minus_legendre5_point_coverage"]={
                            "mean":float(np.mean(d)),
                            "block_bootstrap95":paired_interval(d,
                                seed=SEED+1011*si+151*li+41*ti+
                                sum(map(ord,m))
                            ),
                            "independent_source_blocks":BLOCKS,
                        }
                groups[s][l][t]={"attempted":BLOCKS,"completed":len(cell),
                                "methods":method,"paired_differences":paired}
    return {"study":STUDY,"seed":SEED,
            "independent_generating_blocks":BLOCKS,
            "independent_participants_per_block":N,
            "paired_source_regimes_share_random_effects_and_recording_draws":True,
            "predeclared_models":list(MODELS),
            "spline_knots":KNOTS.tolist(),
            "pointwise_confidence_level":CONFIDENCE,
            "planned_cases":len(expected),"recorded_cases":len(rows),
            "completed_cases":len(completed),
            "failed_cases":len(rows)-len(completed),
            "missing_cases":missing,"groups":groups,
            "nominal_simultaneous_functional_inference_qualified":False,
            "selected_optimal_basis":False,
            "missingness_correction_qualified":False,
            "release_authorized":False}


def figure(evidence,path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(12,4.6))
    xs=np.arange(len(MODELS))
    for t,ax in zip(TRUTHS,axes):
        for s in SCHEMES:
            for l in LOSSES:
                rates=[evidence["groups"][s][l][t]["methods"][m][
                    "pointwise_coverage_rate_completed"] for m in MODELS]
                ax.plot(xs,rates,marker="o",label=f"{s}/{l}")
        ax.axhline(CONFIDENCE,color="black",linestyle="--")
        ax.set_ylim(0,1)
        ax.set_xticks(xs,("Legendre-5","Legendre-11","Cubic spline-13"))
        ax.set_ylabel("90% pointwise truth inclusion (64 blocks)")
        ax.set_title(f"Known truth: {t}")
    axes[1].legend(fontsize=7,loc="lower right")
    fig.suptitle("W3 R9: fixed rich-basis sensitivity, participant CR1")
    fig.tight_layout()
    fig.savefig(path,format="svg",metadata={"Date":None})
    plt.close(fig)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    rows=[evaluate(b,s,l,t) for b in range(BLOCKS)
          for s in SCHEMES for l in LOSSES for t in TRUTHS]
    results=audit(rows)
    for name,obj in (("case-ledger.json",rows),("evidence.json",results)):
        (args.out/name).write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")
    figure(results,args.out/"original-mean-basis-coverage.svg")
    (args.out/"source-commit.txt").write_text(os.getenv("GITHUB_SHA","unverified-local")+"\n")
    files=("case-ledger.json","evidence.json",
           "original-mean-basis-coverage.svg","source-commit.txt")
    (args.out/"SHA256SUMS").write_text("".join(
        sha256((args.out/f).read_bytes()).hexdigest()+f"  {f}\n" for f in files))
    print("W3 R9 ORIGINAL BASIS STRESS AUDIT:",json.dumps(results,sort_keys=True))
    if results["failed_cases"] or results["missing_cases"] or results["completed_cases"]!=len(expected_cases()):
        raise SystemExit("original source study incomplete; retain failure evidence")


def expected_cases():
    return [(b,s,l,t) for b in range(BLOCKS)
            for s in SCHEMES for l in LOSSES for t in TRUTHS]


if __name__=="__main__":
    main()
