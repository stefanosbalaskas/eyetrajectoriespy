"""W3 R12: conditional variance oracle versus cluster CR1 and jackknife CR3.

RESEARCH ONLY: 96 independently seeded generating blocks, 24/48/96
independent participants, nested sample sizes, broadly/narrowly dispersed
observed predictors, all COMPLETE genuinely asynchronous repeated trials,
fixed degree-five Legendre slope mean function. No missingness, model
selection, model misspecification experiment or release qualification.

The conditional Gaussian variance oracle uses known simulation random
intercept/slope, trial effect, and sensor noise variances. It is NOT
estimable from human gaze without additional assumptions. The same point
estimate receives four nominal 90% *pointwise* intervals: CR1/t,
CR1/normal, leave-one-PARTICIPANT-out jackknife/t, known oracle/normal.
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
from scipy.stats import norm, t as student_t

from eyetrajectoriespy import IrregularTrajectorySet
from eyetrajectoriespy.workflows import FunctionOnScalarWorkflowConfig, run_function_on_scalar_workflow
from scripts.run_w3_r9_mean_basis_selection_stress import basis, TIME, DIMS, truth_coefficients

STUDY="W3_R12_COMPLETE_SOURCE_CLUSTER_VARIANCE_ORACLE_20261013"
SEED=202610131212
BLOCKS=96
SIZES=(24,48,96)
PREDICTOR_SCALES={"broad":.95,"narrow":.35}
MAX_N=max(SIZES)
MAX_TRIALS=3
MODEL="legendre5"
FOCAL=15
NOMINAL=.90
SIGMA_INTERCEPT=.08
SIGMA_RANDOM_SLOPE=.045
SIGMA_TRIAL=.025
SIGMA_SENSOR=.045
METHODS=("cr1_t","cr1_normal","cluster_jackknife_t","known_gaussian_oracle")
TOL=3e-8
MC_DRAWS=3000


def source(block,scale):
    if type(block) is not int or not 0<=block<BLOCKS:
        raise ValueError("independent source block outside planned range")
    if scale not in PREDICTOR_SCALES:
        raise ValueError("undeclared predictor-support source design")
    rng=np.random.default_rng(SEED+18503*block)
    x=PREDICTOR_SCALES[scale]*rng.uniform(-1,1,MAX_N)
    trial_alloc=rng.uniform(size=MAX_N)
    n_trials=(1+np.floor(MAX_TRIALS*trial_alloc)).astype(int)
    jitter=np.clip(rng.normal(0,.006,size=(MAX_N,MAX_TRIALS,len(TIME))),-.01,.01)
    jitter[:,:,0]=0
    jitter[:,:,-1]=0
    native_t=TIME[None,None,:]+jitter
    if not np.all(np.diff(native_t,axis=2)>0):
        raise ValueError("complete native time source must be increasing")
    rand_intercept=rng.normal(size=MAX_N)
    rand_slope=rng.normal(size=MAX_N)
    trial_random=rng.normal(size=(MAX_N,MAX_TRIALS))
    point_noise=rng.normal(size=(MAX_N,MAX_TRIALS,len(TIME)))
    ys=np.zeros_like(native_t)
    mu=np.zeros_like(native_t)
    for i in range(MAX_N):
        for j in range(MAX_TRIALS):
            t=native_t[i,j]
            f=truth_coefficients(t)
            mean=f[0,:,0]+x[i]*f[1,:,0]
            mu[i,j]=mean
            ys[i,j]=(mean+SIGMA_INTERCEPT*rand_intercept[i]*(1+.30*t)
                     +SIGMA_RANDOM_SLOPE*rand_slope[i]*x[i]*(1+.25*t)
                     +SIGMA_TRIAL*trial_random[i,j]
                     +SIGMA_SENSOR*point_noise[i,j])
    return {"time":native_t,"values":ys,"conditional_mean":mu,
            "x":x,"n_trials":n_trials,"block":block,"scale":scale,
            "true_slope":float(truth_coefficients(TIME)[1,FOCAL,0])}


def case_data(src,n):
    if n not in SIZES:
        raise ValueError("unplanned independent participant size")
    times=[]; values=[]; ids=[]; part=[]; trial=[]; condition=[]; means=[]
    for i in range(n):
        for j in range(int(src["n_trials"][i])):
            t=src["time"][i,j].copy()
            y=np.column_stack((src["values"][i,j],
                               np.zeros_like(src["values"][i,j])))
            times.append(t)
            values.append(y)
            ids.append(f"P{i:03d}-T{j:02d}")
            part.append(i);trial.append(3*i+j)
            condition.append(src["x"][i])
            means.append(src["conditional_mean"][i,j].copy())
    meta=pd.DataFrame({"participant_id":[f"P{i:03d}" for i in part],
                       "trial_id":[j%3 for j in trial]})
    gaze=IrregularTrajectorySet(
        time=tuple(times),values=tuple(values),
        curve_ids=tuple(ids),dimension_names=DIMS,
        coordinate_system="normalized",time_unit="s",
        metadata=meta,provenance={"research_study":STUDY,"source_block":src["block"],
                                  "predictor_spread":src["scale"],
                                  "all_original_samples_retained":True,
                                  "independent_unit":"participant",
                                  "interpolation_performed":False})
    return gaze,np.asarray(condition),np.asarray(part),np.asarray(trial),tuple(means)


def sufficient_statistics(gaze,x,part,means,n):
    """Independent-participant normal equations AND known-score covariance."""
    p=12
    grams=np.zeros((n,p,p))
    crosses=np.zeros((n,p))
    means_cross=np.zeros((n,p))
    oracle_score_cov=np.zeros((n,p,p))
    all_x=[];all_y=[];all_mu=[];all_s=[];all_pid=[]
    if len(np.unique(part))!=n or len(gaze.time)!=len(x) or len(means)!=len(x):
        raise ValueError("participant vs trial source map mismatch")
    trial_counts=np.bincount(part,minlength=n)
    for curve,(t,y,mu) in enumerate(zip(gaze.time,gaze.values,means)):
        who=part[curve]
        x_i=float(x[curve])
        if len(t)!=len(TIME) or not np.all(np.diff(t)>0) or not np.isfinite(y).all():
            raise ValueError("complete asynchronous original sensor timepoints altered")
        B=basis(t,MODEL)
        Z=np.column_stack((B,B*x_i))
        w=1/(trial_counts[who]*len(t))
        observed=np.asarray(y[:,0])
        grams[who]+=w*Z.T@Z
        crosses[who]+=w*Z.T@observed
        means_cross[who]+=w*Z.T@mu
        # Known conditional participant intercept and slope random effects
        # are shared across all person's trials.
        ai=SIGMA_INTERCEPT*w*Z.T@(1+.30*t)
        bi=SIGMA_RANDOM_SLOPE*w*Z.T@(x_i*(1+.25*t))
        # We store sums via additional latent score vectors below:
        oracle_score_cov[who]+=SIGMA_TRIAL**2*np.outer(
            w*Z.sum(axis=0),w*Z.sum(axis=0))
        oracle_score_cov[who]+=(SIGMA_SENSOR*w)**2*(Z.T@Z)
        all_x.append(Z);all_y.append(observed)
        all_mu.append(mu);all_s.append(np.full(len(t),np.sqrt(w)))
        all_pid.append(np.full(len(t),who,int))
    # Participant-wide terms accumulate over trials before outer products.
    for who in range(n):
        rows=np.where(part==who)[0]
        total_a=np.zeros(p);total_b=np.zeros(p)
        for curve in rows:
            t=gaze.time[curve];B=basis(t,MODEL)
            Z=np.column_stack((B,B*float(x[curve])))
            w=1/(trial_counts[who]*len(t))
            total_a+=SIGMA_INTERCEPT*w*Z.T@(1+.30*t)
            total_b+=SIGMA_RANDOM_SLOPE*w*Z.T@(float(x[curve])*(1+.25*t))
        oracle_score_cov[who]+=np.outer(total_a,total_a)+np.outer(total_b,total_b)
    X=np.vstack(all_x);Y=np.concatenate(all_y)
    MU=np.concatenate(all_mu);S=np.concatenate(all_s)
    group=np.concatenate(all_pid)
    Q=grams.sum(axis=0);v=crosses.sum(axis=0)
    theta=np.linalg.solve(Q,v)
    qr=np.linalg.lstsq(X*S[:,None],Y*S,rcond=None)[0]
    if np.max(np.abs(theta-qr))>TOL:
        raise ValueError("independent original weighted QR oracle mismatch")
    theta_mu=np.linalg.lstsq(X*S[:,None],MU*S,rcond=None)[0]
    scores=crosses-np.einsum("nij,j->ni",grams,theta)
    residual=Y-X@theta
    independent=np.vstack([
        (X[group==i]*(S[group==i]**2*residual[group==i])[:,None]).sum(axis=0)
        for i in range(n)
    ])
    if np.max(np.abs(scores-independent))>TOL:
        raise ValueError("independent participant score sum oracle failed")
    h=np.r_[np.zeros(6),basis(np.array([TIME[FOCAL]]),MODEL)[0]]
    return grams,crosses,means_cross,oracle_score_cov,Q,theta,theta_mu,h,len(Y)


def evaluate(block,scale,n):
    row={"study":STUDY,"block":block,"predictor_support":scale,
         "n_participants":n,"status":"failed","exception":None,
         "all_complete_native_source":False,"dense_W3_rejected_irregular":False,
         "n_trials":None,"n_gaze_samples":None,"model_projection_error":None,
         "point_error":None,"oracle_gaussian_se":None,"methods":{},
         "no_simultaneous_inference":True,"method_qualified":False,
         "release_authorized":False}
    try:
        src=source(block,scale)
        gaze,x,part,trial,means=case_data(src,n)
        for idx,(t,y) in enumerate(zip(gaze.time,gaze.values)):
            who=part[idx];j=trial[idx]%3
            np.testing.assert_array_equal(t,src["time"][who,j])
            np.testing.assert_array_equal(y[:,0],src["values"][who,j])
        df=pd.DataFrame({"curve_id":gaze.curve_ids,"condition":x})
        try:
            run_function_on_scalar_workflow(gaze,df,
                config=FunctionOnScalarWorkflowConfig(
                    predictors=("condition",),dimensions=DIMS,
                    unit="participant",participant_column="participant_id"))
        except TypeError as e:
            if "IrregularTrajectorySet" not in str(e):raise
        else:
            raise ValueError("public dense W3 accepted genuinely async source")

        grams,cross,mu_cross,cov,Q,theta,theta_mu,h,nrows=sufficient_statistics(
            gaze,x,part,means,n)
        B=np.linalg.inv(Q)
        point=float(h@theta)
        true=src["true_slope"]
        proj=float(h@theta_mu-true)
        oracle_variance=float(h@B@cov.sum(axis=0)@B@h)
        if oracle_variance<=0 or not np.isfinite(oracle_variance):
            raise ValueError("conditional generating-source variance invalid")

        scores=cross-np.einsum("nij,j->ni",grams,theta)
        cr1_meat=(scores.T@scores)*(n/(n-1))*((nrows-1)/(nrows-len(theta)))
        cr1_var=float(h@B@cr1_meat@B@h)
        if cr1_var<=0:raise ValueError("nonpositive participant CR1")
        cr1=np.sqrt(cr1_var)
        q_leave=Q[None,:,:]-grams
        v_leave=cross.sum(axis=0)[None,:]-cross
        leave=np.linalg.solve(q_leave,v_leave[...,None])[...,0]
        leave_point=leave@h
        jack_var=float((n-1)/n*np.sum((leave_point-leave_point.mean())**2))
        if jack_var<=0 or not np.isfinite(jack_var):
            raise ValueError("nonpositive participant jackknife CR3")
        jack=np.sqrt(jack_var)
        oracle=np.sqrt(oracle_variance)
        if not np.isfinite([cr1,jack,oracle]).all():
            raise ValueError("nonfinite participant uncertainty")

        z=float(norm.ppf((1+NOMINAL)/2))
        tcrit=float(student_t.ppf((1+NOMINAL)/2,n-1))
        comparisons={
            "cr1_t":(cr1,tcrit),
            "cr1_normal":(cr1,z),
            "cluster_jackknife_t":(jack,tcrit),
            "known_gaussian_oracle":(oracle,z)
        }
        for key,(se,critical) in comparisons.items():
            half=se*critical
            row["methods"][key]={
                "se":float(se),"half_width":float(half),
                "width":float(2*half),
                "truth_included":bool(point-half<=true<=point+half),
                "se_divided_by_oracle":float(se/oracle)
            }
        row.update({"status":"ok","all_complete_native_source":True,
                    "dense_W3_rejected_irregular":True,
                    "n_trials":len(gaze.time),"n_gaze_samples":nrows,
                    "model_projection_error":proj,
                    "point_error":float(point-true),
                    "oracle_gaussian_se":float(oracle)})
    except Exception as e:
        row["exception"]={"type":type(e).__name__,"message":str(e)[:900]}
    return row


def wilson(k,n):
    if not n:return None
    z=float(norm.ppf(.975));p=k/n;d=1+z*z/n
    c=(p+z*z/(2*n))/d
    h=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return [float(max(0,c-h)),float(min(1,c+h))]


def paired_bootstrap(x,seed):
    if not x:return None
    v=np.asarray(x,float)
    gen=np.random.default_rng(seed)
    ii=gen.integers(0,len(v),size=(MC_DRAWS,len(v)))
    return [float(a) for a in np.quantile(v[ii].mean(axis=1),[.025,.975])]


def audit(rows):
    expected={(b,s,n) for b in range(BLOCKS)
              for s in PREDICTOR_SCALES for n in SIZES}
    ids=[(r["block"],r["predictor_support"],r["n_participants"]) for r in rows]
    if len(ids)!=len(set(ids)) or not set(ids).issubset(expected):
        raise ValueError("duplicated or unplanned scientific source case")
    missing=sorted(f"{b}:{s}:{n}" for b,s,n in expected-set(ids))
    complete=[r for r in rows if r["status"]=="ok"]
    groups={}
    for support in PREDICTOR_SCALES:
        groups[support]={}
        for n in SIZES:
            cell=sorted((r for r in complete if
                r["predictor_support"]==support and
                r["n_participants"]==n),key=lambda r:r["block"])
            measures={}
            for model in METHODS:
                m=[r["methods"][model] for r in cell]
                successes=sum(x["truth_included"] for x in m)
                measures[model]={
                    "completed":len(m),"planned":BLOCKS,
                    "true_point_count":successes,
                    "true_point_rate":successes/len(m) if m else None,
                    "wilson95":wilson(successes,len(m)),
                    "mean_interval_width":float(np.mean([x["width"] for x in m])) if m else None,
                    "mean_se_ratio_vs_conditional_oracle":float(np.mean([
                        x["se_divided_by_oracle"] for x in m])) if m else None,
                }
            contrasts={}
            if len(cell)==BLOCKS:
                for key in ("cluster_jackknife_t","known_gaussian_oracle","cr1_normal"):
                    d=[int(r["methods"][key]["truth_included"])-
                       int(r["methods"]["cr1_t"]["truth_included"]) for r in cell]
                    contrasts[key+"_minus_cr1_t_coverage"]={
                        "mean":float(np.mean(d)),
                        "paired_block_bootstrap95":paired_bootstrap(
                            d,seed=SEED+1051*n+sum(map(ord,support+key)))
                    }
            groups[support][str(n)]={
                "attempted":BLOCKS,"completed":len(cell),
                "source_pass":sum(r["all_complete_native_source"] and
                    r["dense_W3_rejected_irregular"] for r in cell),
                "mean_estimate_error":float(np.mean([
                    r["point_error"] for r in cell])) if cell else None,
                "empirical_estimate_error_sd":float(np.std([
                    r["point_error"] for r in cell],ddof=1)) if len(cell)>1 else None,
                "mean_source_oracle_se":float(np.mean([
                    r["oracle_gaussian_se"] for r in cell])) if cell else None,
                "mean_model_projection_error":float(np.mean([
                    r["model_projection_error"] for r in cell])) if cell else None,
                "methods":measures,"paired_intervals":contrasts
            }
    return {"study":STUDY,"seed":SEED,
            "independent_generating_blocks":BLOCKS,
            "nested_participant_sizes":list(SIZES),
            "independent_units_are_participants":True,
            "source_all_recordings_complete":True,
            "no_missingness":True,
            "true_conditional_gaussian_covariance_available_only_in_simulation":True,
            "pointwise_nominal_level":NOMINAL,
            "planned_cases":len(expected),"recorded_cases":len(rows),
            "completed_cases":len(complete),
            "failed_cases":len(rows)-len(complete),
            "missing_cases":missing,"groups":groups,
            "no_simultaneous_bands_qualified":True,
            "release_authorized":False}


def plot(report,path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(11,5))
    x=np.arange(len(SIZES))
    for support in PREDICTOR_SCALES:
        for method in METHODS:
            vals=[report["groups"][support][str(n)]["methods"][method]["true_point_rate"]
                  for n in SIZES]
            ax.plot(x,vals,marker="o",label=f"{support} {method}")
    ax.axhline(NOMINAL,linestyle="--",color="black")
    ax.set_xticks(x,[str(n) for n in SIZES])
    ax.set_xlabel("Independent participants, not trial/observation count")
    ax.set_ylabel("Known-truth pointwise inclusion per 96 source blocks")
    ax.set_ylim(0,1)
    ax.set_title("W3 R12: conditional oracle versus finite-cluster variance methods")
    ax.legend(fontsize=7,ncol=2)
    fig.tight_layout()
    fig.savefig(path,format="svg",metadata={"Date":None})
    plt.close(fig)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    a=parser.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    rows=[evaluate(b,s,n) for b in range(BLOCKS)
          for s in PREDICTOR_SCALES for n in SIZES]
    report=audit(rows)
    for name,obj in (("case-ledger.json",rows),("evidence.json",report)):
        (a.out/name).write_text(json.dumps(obj,sort_keys=True,indent=2)+"\n")
    plot(report,a.out/"source-complete-cluster-oracle.svg")
    (a.out/"source-commit.txt").write_text(os.getenv("GITHUB_SHA","unverified-local")+"\n")
    names=("case-ledger.json","evidence.json",
           "source-complete-cluster-oracle.svg","source-commit.txt")
    (a.out/"SHA256SUMS").write_text("".join(
        sha256((a.out/name).read_bytes()).hexdigest()+f"  {name}\n" for name in names))
    print("W3 R12 COMPLETE SOURCE CONDITIONAL VARIANCE AUDIT:",
          json.dumps(report,sort_keys=True))
    if report["failed_cases"] or report["missing_cases"]:
        raise SystemExit("failure-inclusive source ledger incomplete")


if __name__=="__main__":
    main()
