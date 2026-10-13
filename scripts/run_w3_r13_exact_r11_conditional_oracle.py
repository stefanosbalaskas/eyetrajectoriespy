"""R13: exact R11 complete-source reproduction plus independent matched-DGP oracle.

Historical 96 source blocks are regenerated with unchanged R11 source code.
96 fresh independent blocks use the EXACT R11 smooth generator with only
the master seed changed. Both use 48 genuinely asynchronous participants,
unequal 1-3 complete trials, known Gaussian random intercept/slope,
trial effects and sensor noise. Fixed degree-5 Legendre and 13-spline bases.
Compare original participant CR1/t with analytic conditional Gaussian/normal.
Independent generating blocks are the only Monte Carlo replication unit.
Research only, no missingness identification, simultaneous band or API change.
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
from scipy.stats import norm

from scripts.run_w3_r11_paired_observation_process import (
    original_full_source, recorded_case, enforce_observed_source,
    SEED as HISTORICAL_SEED, N_PARTICIPANTS, MAX_TRIALS, TIME, DIMS,
    FOCAL, BLOCKS as HISTORICAL_BLOCKS,
)
from scripts.run_w3_r9_mean_basis_selection_stress import basis, fit_model, truth_coefficients
from scripts.run_w3_r12_complete_cluster_variance_oracle import (
    SIGMA_INTERCEPT, SIGMA_RANDOM_SLOPE, SIGMA_TRIAL, SIGMA_SENSOR,
)
from eyetrajectoriespy.workflows import (
    FunctionOnScalarWorkflowConfig, run_function_on_scalar_workflow,
)

STUDY="W3_R13_R11_EXACT_COMPLETE_COVARIANCE_ORACLE_20261013"
FRESH_SEED=202610139137
COHORTS=("historical_R11","fresh_R11_DGP")
BLOCKS=96
MODELS=("legendre5","cubic_spline13")
METHODS=("participant_cr1_t","conditional_gaussian_oracle_normal")
CONFIDENCE=.90
TOL=4e-7
BOOTSTRAP_DRAWS=3000


def replay_r11_generator(block,master_seed):
    """Exact R11 smooth full-source generator, differing ONLY by master_seed.

    Independent contract tests compare every generated source array at the
    historical master seed to unchanged R11.original_full_source().
    """
    if type(block) is not int or not 0<=block<BLOCKS:
        raise ValueError("original independent block outside planned source")
    rng=np.random.default_rng(master_seed+20533*block)
    x=rng.uniform(-.95,.95,size=N_PARTICIPANTS)
    trial_alloc=rng.uniform(size=N_PARTICIPANTS)
    n_trials=(1+np.floor(MAX_TRIALS*trial_alloc)).astype(int)
    jitter=np.clip(rng.normal(0,.006,size=(N_PARTICIPANTS,MAX_TRIALS,len(TIME))),
                   -.010,.010)
    jitter[:,:,0]=0.;jitter[:,:,-1]=0.
    timestamps=TIME[None,None,:]+jitter
    if not np.all(np.diff(timestamps,axis=2)>0):
        raise ValueError("source time points not strictly increasing")
    p_intercept=rng.normal(0,.08,size=(N_PARTICIPANTS,1,1,len(DIMS)))
    p_slope=rng.normal(0,.045,size=(N_PARTICIPANTS,1,1,len(DIMS)))
    trial_intercept=rng.normal(0,.025,size=(N_PARTICIPANTS,MAX_TRIALS,1,len(DIMS)))
    noise=rng.normal(0,.045,size=(N_PARTICIPANTS,MAX_TRIALS,len(TIME),len(DIMS)))
    conditional_mean=np.empty_like(noise)
    for i in range(N_PARTICIPANTS):
        for j in range(MAX_TRIALS):
            theta=truth_coefficients(timestamps[i,j])
            conditional_mean[i,j]=theta[0]+x[i]*theta[1]
    responses=(conditional_mean
        +p_intercept*(1+.30*timestamps[...,None])
        +p_slope*x[:,None,None,None]*(1+.25*timestamps[...,None])
        +trial_intercept+noise)
    draws=rng.uniform(size=(N_PARTICIPANTS,MAX_TRIALS))
    slope=truth_coefficients(TIME)[1,:,0].copy()
    return {"block":block,"truth_mode":"baseline","x":x,
            "n_trials":n_trials,"time":timestamps,"values":responses,
            "conditional_mean":conditional_mean,
            "dropout_uniforms":draws,"true_slope":slope}


def source(block,cohort):
    if cohort not in COHORTS:
        raise ValueError("undeclared generating cohort")
    if cohort=="historical_R11":
        return original_full_source(block,"baseline")
    return replay_r11_generator(block,FRESH_SEED)


def wls_and_conditional_oracle(rec,model):
    """Compute the R11-fit pointwise variance from KNOWN source covariance.

    Treat participant random intercept and random slope as shared across
    all original trials. Trial intercept shared within the original trial,
    sample noise independent by original timestamp. No latent variance
    is fitted from observed gaze. Validate the source WLS and CR1
    against the separately implemented R9 model fit.
    """
    if model not in MODELS:
        raise ValueError("unplanned model")
    gaze=rec["gaze"];x=rec["x"];participants=rec["units"]
    n=N_PARTICIPANTS
    if len(np.unique(participants))!=n or rec["n_gapped_trials"]!=0:
        raise ValueError("complete independent source participants required")
    n_trials=np.bincount(participants,minlength=n)
    k=basis(TIME,model).shape[1];p=2*k
    Q=np.zeros((n,p,p));V=np.zeros((n,p));QM=np.zeros((n,p))
    known_cov=np.zeros((n,p,p))
    source_X=[];source_Y=[];source_M=[];rootW=[];source_unit=[]
    shared_intercept=np.zeros((n,p))
    shared_slope=np.zeros((n,p))
    npoints=0

    for i,(t,y,mean) in enumerate(zip(gaze.time,gaze.values,rec["mean"])):
        owner=int(participants[i]);xi=float(x[i])
        if len(t)!=len(TIME) or not np.all(np.diff(t)>0):
            raise ValueError("original native complete trial support has changed")
        B=basis(t,model)
        Xi=np.column_stack((B,B*xi))
        w=1/(len(t)*n_trials[owner])
        yi=np.asarray(y[:,0],float)
        mui=np.asarray(mean,float)
        Q[owner]+=w*Xi.T@Xi
        V[owner]+=w*Xi.T@yi
        QM[owner]+=w*Xi.T@mui

        # The shared person effects must be summed BEFORE taking outer products.
        shared_intercept[owner]+=SIGMA_INTERCEPT*w*Xi.T@(1+.30*t)
        shared_slope[owner]+=SIGMA_RANDOM_SLOPE*w*Xi.T@(xi*(1+.25*t))
        # Every trial has an independent random intercept, each timepoint
        # has an independent sensor innovation.
        trial_vec=SIGMA_TRIAL*w*Xi.sum(axis=0)
        known_cov[owner]+=np.outer(trial_vec,trial_vec)
        known_cov[owner]+=(SIGMA_SENSOR*w)**2*(Xi.T@Xi)

        source_X.append(Xi);source_Y.append(yi)
        source_M.append(mui)
        rootW.append(np.full(len(t),np.sqrt(w)))
        source_unit.append(np.full(len(t),owner,dtype=int))
        npoints+=len(t)
    known_cov+=np.einsum("ni,nj->nij",shared_intercept,shared_intercept)
    known_cov+=np.einsum("ni,nj->nij",shared_slope,shared_slope)

    XtX=Q.sum(axis=0)
    XtY=V.sum(axis=0)
    theta=np.linalg.solve(XtX,XtY)
    matrices=np.vstack(source_X)
    responses=np.concatenate(source_Y)
    means=np.concatenate(source_M)
    sqrtw=np.concatenate(rootW)
    units=np.concatenate(source_unit)
    theta_qr=np.linalg.lstsq(matrices*sqrtw[:,None],responses*sqrtw,rcond=None)[0]
    source_delta=float(np.max(np.abs(theta-theta_qr)))
    if source_delta>TOL:
        raise ValueError("original WLS vs independent QR mismatch")
    theta_mu=np.linalg.lstsq(matrices*sqrtw[:,None],means*sqrtw,rcond=None)[0]

    scores=V-np.einsum("nij,j->ni",Q,theta)
    residual=responses-matrices@theta
    reference=np.vstack([
        (matrices[units==i]*(sqrtw[units==i]**2*residual[units==i])[:,None]).sum(axis=0)
        for i in range(n)
    ])
    score_delta=float(np.max(np.abs(scores-reference)))
    if score_delta>TOL:
        raise ValueError("independent participant residual-score oracle mismatch")
    h=np.r_[np.zeros(k),basis(np.array([TIME[FOCAL]]),model)[0]]
    b=np.linalg.inv(XtX)
    fitted=float(h@theta)
    projected=float(h@theta_mu)

    exact_var=float(h@b@known_cov.sum(axis=0)@b@h)
    if exact_var<=0 or not np.isfinite(exact_var):
        raise ValueError("known Gaussian covariance was not positive")
    oracle_se=float(np.sqrt(exact_var))
    factor=(n/(n-1))*((npoints-1)/(npoints-p))
    cr1_var=float(h@b@(scores.T@scores)*factor@b@h)
    if cr1_var<=0 or not np.isfinite(cr1_var):
        raise ValueError("CR1 participant variance not positive")
    cr1_se=float(np.sqrt(cr1_var))

    independent_fit=fit_model(
        gaze,rec["mean"],rec["x"],rec["units"],rec["trials"],model
    )
    max_fit_delta=max(
        abs(fitted-independent_fit["point_estimate"]),
        abs(projected-independent_fit["projection"]),
        abs(cr1_se-independent_fit["se"])
    )
    if max_fit_delta>TOL:
        raise ValueError("R11 numerical point/CR1 not reproduced by independent oracle")
    if len(np.unique(units))!=n or npoints!=rec["n_observed_samples"]:
        raise ValueError("participant/point count inconsistent")

    return {"estimate":fitted,"projection":projected,
            "oracle_se":oracle_se,"cr1_se":cr1_se,
            "r11_width":float(independent_fit["width"]),
            "source_qr_max_diff":source_delta,
            "participant_score_max_diff":score_delta,
            "original_cr1_max_diff":max_fit_delta,
            "n_trials":len(gaze.time),"n_points":npoints}


def case(block,cohort,model):
    out={"study":STUDY,"block":block,"cohort":cohort,"model":model,
         "status":"failed","exception":None,
         "n_independent_participants":N_PARTICIPANTS,
         "n_trials":None,"n_points":None,
         "source_immutable":False,"native_W3_rejected":False,
         "known_truth":None,"estimate":None,"projection_error":None,
         "point_error":None,"standardized_error_oracle":None,
         "standardized_centered_error_oracle":None,
         "methods":{},"scientific_method_qualified":False,
         "simultaneous_inference_qualified":False,"release_authorized":False}
    try:
        s=source(block,cohort)
        recorded=recorded_case(s,"complete")
        enforce_observed_source(s,recorded)
        src_before=[(t.copy(),v.copy()) for t,v in zip(
            recorded["gaze"].time,recorded["gaze"].values)]
        frame=__import__("pandas").DataFrame({
            "curve_id":recorded["gaze"].curve_ids,
            "condition":recorded["x"]
        })
        try:
            run_function_on_scalar_workflow(
                recorded["gaze"],frame,
                config=FunctionOnScalarWorkflowConfig(
                    predictors=("condition",),dimensions=DIMS,
                    unit="participant",participant_column="participant_id"
                ))
        except TypeError as exc:
            if "IrregularTrajectorySet" not in str(exc):
                raise
        else:
            raise ValueError("public W3 incorrectly accepted native source")

        fit=wls_and_conditional_oracle(recorded,model)
        for (t,y),actual_t,actual_y in zip(
            src_before,recorded["gaze"].time,recorded["gaze"].values
        ):
            if not np.array_equal(t,actual_t) or not np.array_equal(y,actual_y):
                raise ValueError("R11 original recorded native data mutated")

        truth=float(s["true_slope"][FOCAL])
        zcrit=float(norm.ppf((1+CONFIDENCE)/2))
        # Existing R11 CR1/t interval is used untouched, except that
        # its endpoints are reconstructed from its independent SE.
        tcrit=float(__import__("scipy").stats.t.ppf((1+CONFIDENCE)/2,
                                                    N_PARTICIPANTS-1))
        for method in METHODS:
            se=fit["cr1_se"] if method=="participant_cr1_t" else fit["oracle_se"]
            critical=tcrit if method=="participant_cr1_t" else zcrit
            half=critical*se
            out["methods"][method]={
                "se":se,"width":float(2*half),
                "known_truth_included":bool(
                    fit["estimate"]-half<=truth<=fit["estimate"]+half
                )
            }
        out.update({
            "status":"ok","n_trials":fit["n_trials"],
            "n_points":fit["n_points"],
            "source_immutable":True,"native_W3_rejected":True,
            "known_truth":truth,"estimate":fit["estimate"],
            "projection_error":fit["projection"]-truth,
            "point_error":fit["estimate"]-truth,
            "standardized_error_oracle":(fit["estimate"]-truth)/fit["oracle_se"],
            "standardized_centered_error_oracle":
                (fit["estimate"]-fit["projection"])/fit["oracle_se"],
            "cr1_oracle_se_ratio":fit["cr1_se"]/fit["oracle_se"],
            "source_qr_max_diff":fit["source_qr_max_diff"],
            "source_grouped_score_max_diff":fit["participant_score_max_diff"],
            "source_r11_fit_max_diff":fit["original_cr1_max_diff"],
        })
    except Exception as exc:
        out["exception"]={"type":type(exc).__name__,"message":str(exc)[:1000]}
    return out


def wilson(k,n):
    if not n:return None
    z=float(norm.ppf(.975));p=k/n;d=1+z*z/n
    c=(p+z*z/(2*n))/d
    half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return [float(max(0,c-half)),float(min(1,c+half))]


def bootstrap_ci(x,seed):
    if not x:return None
    values=np.asarray(x,float)
    rng=np.random.default_rng(seed)
    ii=rng.integers(0,len(values),size=(BOOTSTRAP_DRAWS,len(values)))
    return [float(v) for v in np.quantile(values[ii].mean(axis=1),[.025,.975])]


def audit(rows):
    expected={(b,co,m) for b in range(BLOCKS) for co in COHORTS for m in MODELS}
    keys=[(r["block"],r["cohort"],r["model"]) for r in rows]
    if len(set(keys))!=len(keys) or not set(keys).issubset(expected):
        raise ValueError("duplicate or unplanned original R13 case")
    missing=sorted(f"{b}:{co}:{m}" for b,co,m in expected-set(keys))
    completed=[r for r in rows if r["status"]=="ok"]
    groups={}
    for co in COHORTS:
        groups[co]={}
        for m in MODELS:
            c=sorted((r for r in completed if r["cohort"]==co and
                      r["model"]==m),key=lambda r:r["block"])
            methods={}
            for method in METHODS:
                vals=[r["methods"][method] for r in c]
                ok=sum(v["known_truth_included"] for v in vals)
                methods[method]={
                    "attempted":BLOCKS,"completed":len(vals),
                    "truth_inclusion":ok,"truth_inclusion_rate":ok/len(vals) if vals else None,
                    "wilson95":wilson(ok,len(vals)),
                    "mean_se":float(np.mean([v["se"] for v in vals])) if vals else None,
                    "mean_width":float(np.mean([v["width"] for v in vals])) if vals else None,
                }
            ratios=[r["cr1_oracle_se_ratio"] for r in c]
            centered=[r["standardized_centered_error_oracle"] for r in c]
            groups[co][m]={
                "attempted":BLOCKS,"completed":len(c),
                "all_original_references_pass":sum(
                    r["source_immutable"] and r["native_W3_rejected"] and
                    r["source_qr_max_diff"]<=TOL and
                    r["source_grouped_score_max_diff"]<=TOL and
                    r["source_r11_fit_max_diff"]<=TOL for r in c),
                "mean_true_projection_error":float(np.mean(
                    [r["projection_error"] for r in c])) if c else None,
                "mean_error":float(np.mean(
                    [r["point_error"] for r in c])) if c else None,
                "empirical_error_sd":float(np.std(
                    [r["point_error"] for r in c],ddof=1)) if len(c)>1 else None,
                "mean_oracle_se":methods["conditional_gaussian_oracle_normal"]["mean_se"],
                "mean_cr1_se_divided_by_oracle":float(np.mean(ratios)) if c else None,
                "centered_oracle_z_mean":float(np.mean(centered)) if c else None,
                "centered_oracle_z_sd":float(np.std(centered,ddof=1)) if len(c)>1 else None,
                "methods":methods,
                "paired_oracle_minus_cr1_truth_inclusion":{
                    "mean":float(np.mean([
                        int(r["methods"]["conditional_gaussian_oracle_normal"]["known_truth_included"])
                        -int(r["methods"]["participant_cr1_t"]["known_truth_included"])
                        for r in c])) if c else None,
                    "independent_source_block_bootstrap95":bootstrap_ci([
                        int(r["methods"]["conditional_gaussian_oracle_normal"]["known_truth_included"])
                        -int(r["methods"]["participant_cr1_t"]["known_truth_included"])
                        for r in c],FRESH_SEED+sum(map(ord,co+m))),
                }
            }
    old={m:groups["historical_R11"][m]["methods"]["participant_cr1_t"]["truth_inclusion"]
         for m in MODELS}
    # Scientific reproducibility target was fixed before R13 work from the
    # original *complete/smooth* R11 audit (80/96 and 77/96), not selected
    # based on the new study's outcomes.
    exact_historical_reproduction=(old.get("legendre5")==80 and
                                   old.get("cubic_spline13")==77)
    return {"study":STUDY,"seed_historical":HISTORICAL_SEED,
            "seed_fresh":FRESH_SEED,"independent_blocks_per_cohort":BLOCKS,
            "n_independent_blocks_across_two_cohorts":2*BLOCKS,
            "n_independent_participants_per_block":N_PARTICIPANTS,
            "n_original_source_cases_expected":len(expected),
            "recorded_cases":len(rows),
            "completed_cases":len(completed),
            "failed_cases":len(rows)-len(completed),
            "missing_cases":missing,"groups":groups,
            "historical_original_R11_source_pointwise_cr1_counts":{
                "legendre5":80,"cubic_spline13":77},
            "historical_counts_reproduced":exact_historical_reproduction,
            "known_oracle_is_not_an_empirical_estimator":True,
            "no_simultaneous_bands":True,
            "no_model_selection":True,"release_authorized":False}


def plot(report,path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(10.6,4.5),sharey=True)
    for ax,co in zip(axes,COHORTS):
        x=np.arange(len(MODELS))
        for method in METHODS:
            y=[report["groups"][co][model]["methods"][method]["truth_inclusion_rate"]
               for model in MODELS]
            ax.plot(x,y,marker="o",label=method)
        ax.axhline(.9,linestyle="--",color="black")
        ax.set_xticks(x,("Legendre-5","Cubic spline-13"))
        ax.set_title(co)
        ax.set_ylim(0,1)
        ax.set_ylabel("Pointwise true-slope inclusion / 96 source blocks")
    axes[0].legend(fontsize=8)
    fig.suptitle("R13: R11 source replication and exact Gaussian oracle")
    fig.tight_layout()
    fig.savefig(path,format="svg",metadata={"Date":None})
    plt.close(fig)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    rows=[case(b,co,model) for co in COHORTS for b in range(BLOCKS)
          for model in MODELS]
    result=audit(rows)
    for filename,obj in (("case-ledger.json",rows),("evidence.json",result)):
        (a.out/filename).write_text(json.dumps(obj,sort_keys=True,indent=2)+"\n")
    plot(result,a.out/"source-r11-conditional-oracle.svg")
    (a.out/"source-commit.txt").write_text(os.getenv("GITHUB_SHA","unverified-local")+"\n")
    filenames=("case-ledger.json","evidence.json","source-r11-conditional-oracle.svg",
               "source-commit.txt")
    (a.out/"SHA256SUMS").write_text("".join(
        sha256((a.out/f).read_bytes()).hexdigest()+f"  {f}\n" for f in filenames))
    print("W3 R13 EXACT R11 CONDITIONAL ORACLE AUDIT:",json.dumps(result,sort_keys=True))
    if result["failed_cases"] or result["missing_cases"]:
        raise SystemExit("incomplete R13 original source; full failure ledger retained")
    if not result["historical_counts_reproduced"]:
        raise SystemExit("original R11 historical complete-smooth source counts differ")
    # No empirical coverage threshold, architecture winner or release.


if __name__=="__main__":
    main()
