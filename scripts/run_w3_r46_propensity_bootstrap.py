"""R46: prospective participant-bootstrap propensity-uncertainty pilot.

Thirty-two NEW independently seeded Gaussian primitive source blocks (n36),
paired ordinary/extreme supports and true-zero/positive Gaussian slope
states. Three observed-design MAR retention regimes: matched logistic, omitted
interaction/nonlinear propensity, and low-overlap/positivity stress.
Compare observed WLS-CR1, fitted MAR-IPW fixed-weight CR1, and full
participant-pairs percentile bootstrap refitting the logistic propensity.
No missing gaze y enters propensity. All 79 predeclared bootstrap replicate
statuses retained, including explicit failures; no success-conditioned CI.

Exploratory pointwise truth inclusion is not validated nominal 90% CR2
coverage or a simultaneous functional band; R45 negative result is preserved.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np
from scipy.special import expit
from scipy.stats import t as student_t

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts import run_w3_r16_leverage_covariance_factorial as r16
from scripts import run_w3_r17_fresh_feasibility as fresh
from scripts import run_w3_r29_predictor_spread_recovery as counterfactual

STUDY="W3_R46_PROSPECTIVE_REFIT_PROPENSITY_PARTICIPANT_BOOTSTRAP"
SOURCE_SEED=202610164646
MASK_SEED=202610164647
BOOTSTRAP_SEED=202610164648
BLOCKS=32
N_PARTICIPANTS=36
SUPPORT=("ordinary_dependent","extreme_dependent")
STATES=("zero_slope","positive_slope")
REGIMES=(
    "matched_observed_design_logit",
    "misspecified_nonlinear_time_predictor_logit",
    "weak_overlap_observed_design_logit",
)
METHODS=(
    "naive_observed_WLS_CR1",
    "fitted_MAR_IPW_fixed_weight_CR1",
    "fitted_MAR_IPW_refit_pairs_bootstrap_percentile",
)
B_REPS=79
NOMINAL=.90
PROPENSITY_MIN=.05
RIDGE=1e-5
MAX_NEWTON=45
MIN_PARTICIPANTS=8
FOCAL_TIME=float(r16.TIME[r16.FOCAL])
N_SOURCE_VARIANTS=BLOCKS*len(SUPPORT)*len(STATES)
N_SOURCE_REGIMES=N_SOURCE_VARIANTS*len(REGIMES)
N_INTERVALS=N_SOURCE_REGIMES*len(METHODS)
N_BOOT_ATTEMPTS=N_SOURCE_REGIMES*B_REPS


def independent_source(block,support,state):
    if (type(block) is not int or block not in range(BLOCKS)
            or support not in SUPPORT or state not in STATES):
        raise ValueError("outside frozen R46 Gaussian source factorial")
    base=fresh.fresh_source(
        block,support,n=N_PARTICIPANTS,master_seed=SOURCE_SEED,
        n_blocks=BLOCKS,max_n=N_PARTICIPANTS,
    )
    if state=="positive_slope":
        return base
    raw=dict(base[0])
    raw["participant_slope"]=np.zeros_like(raw["participant_slope"])
    return counterfactual.rescaled_source((raw,*base[1:]),1.)


def _q(x):
    return abs(float(x))/(1.+abs(float(x)))


def retention_probability(t,x,regime):
    """All MAR mechanisms condition only on externally observed (x,t).

    Trial endpoints are deterministically observed. The true Bernoulli
    probability is NEVER made available to fitted propensity estimation.
    """
    if regime not in REGIMES:
        raise ValueError("R46 unregistered MAR regime")
    tt=np.asarray(t,float)
    q=_q(x)
    if regime==REGIMES[0]:
        logit=1.2-.9*q-.7*tt
    elif regime==REGIMES[1]:
        logit=1.2-.9*q-.7*tt-2.0*(q*tt)-1.4*(tt-.5)**2
    else:
        logit=-1.5-2.0*q-2.5*tt
    prob=np.asarray(expit(logit),float)
    if np.any((prob<=0)|(prob>=1)) or not np.isfinite(prob).all():
        raise ValueError("R46 invalid observed-only design probability")
    prob[0]=prob[-1]=1.
    return prob


def observation_panel(case,block,support,regime):
    """A missing y is genuinely NaN; x, native time and R are available."""
    if regime not in REGIMES:
        raise ValueError("unregistered observation regime")
    _,gaze,predictor,people,trial,_=case
    rows=[]
    total=0;observed=0;observed_interior=0;interior=0
    for j,(times,values) in enumerate(zip(gaze.time,gaze.values)):
        who=int(people[j]);tr=int(trial[j]);t=np.asarray(times,float)
        ytruth=np.asarray(values,float)[:,0]
        p=retention_probability(t,float(predictor[j]),regime)
        seed=(MASK_SEED+100003*block+7919*who+151*tr
              +61*SUPPORT.index(support)+1079*REGIMES.index(regime))
        rng=np.random.default_rng(seed)
        keep=rng.random(len(t))<p
        keep[0]=keep[-1]=True
        obs=np.full(len(t),np.nan)
        obs[keep]=ytruth[keep]
        rows.append({
            "participant":who,
            "trial":tr,
            "predictor":float(predictor[j]),
            "scheduled_native_time":t,
            "observed_indicator":keep,
            "observed_gaze_NaN_if_missing":obs,
        })
        total+=len(t);observed+=int(keep.sum())
        interior+=len(t)-2;observed_interior+=int(keep[1:-1].sum())
    if len({z["participant"] for z in rows})!=N_PARTICIPANTS:
        raise ValueError("R46 point loss unexpectedly excluded a participant")
    return rows,{
        "native_original_points":total,
        "native_observed_points":observed,
        "original_cohort_participants":N_PARTICIPANTS,
        "retained_participants":N_PARTICIPANTS,
        "overall_point_retained_fraction":float(observed/total),
        "interior_point_retained_fraction":float(
            observed_interior/interior
        ),
        "original_native_gaze_absent_from_estimation_if_R_zero":True,
        "selection_depends_only_on_observed_x_t":True,
        "endpoint_inclusion_known_exactly_one":True,
    }


def _linear_predictor_features(panel):
    xx=[];yy=[]
    for trial in panel:
        t=trial["scheduled_native_time"]
        q=_q(trial["predictor"])
        xx.extend((1.,q,float(t[j])) for j in range(1,len(t)-1))
        yy.extend(
            float(trial["observed_indicator"][j])
            for j in range(1,len(t)-1)
        )
    return np.asarray(xx,float),np.asarray(yy,float)


def fit_propensity(panel):
    """Fitted Bernoulli GLM sees only recorded R, x and native scheduled t."""
    F,r=_linear_predictor_features(panel)
    if F.shape[0]<10 or len(np.unique(r))<2:
        raise ValueError("R46 no fitted-propensity variation")
    theta=np.zeros(3)
    for iteration in range(MAX_NEWTON):
        p=np.clip(expit(F@theta),1e-9,1.-1e-9)
        grad=F.T@(p-r)+RIDGE*np.r_[0.,theta[1:]]
        H=F.T@((p*(1.-p))[:,None]*F)
        H+=RIDGE*np.diag([0.,1.,1.])
        delta=np.linalg.solve(H,grad)
        theta-=delta
        if np.max(np.abs(delta))<1e-9:
            break
    if not np.isfinite(theta).all():
        raise ValueError("R46 nonfinite fitted propensity parameters")
    return theta,{
        "observed_only_indicator_predictor_time_features":True,
        "interior_scheduled_rows":len(r),
        "observed_interior_rows":int(r.sum()),
        "iterations":iteration+1,
        "coefficient_logit":theta.tolist(),
        "fitted_propensity_does_not_see_missing_or_observed_gaze":True,
    }


def _design(panel,method,theta=None):
    if method not in ("naive","ipw"):
        raise ValueError("unknown R46 weighted regression method")
    trials_per={}
    for row in panel:
        key=row["participant"]
        trials_per[key]=trials_per.get(key,0)+1
    allX=[];allY=[];allW=[];allG=[]
    minimum_p=1.
    maximum_ipw=1.
    for row in panel:
        t=row["scheduled_native_time"]
        retain=row["observed_indicator"]
        idx=np.flatnonzero(retain)
        if not len(idx):
            continue
        x=row["predictor"]
        B=r16.basis(t[idx],"legendre5")
        X=np.column_stack([B,x*B])
        y=row["observed_gaze_NaN_if_missing"][idx]
        if not np.isfinite(y).all():
            raise ValueError("R46 missing gaze response leaked to WLS")
        if method=="naive":
            weights=np.full(
                len(y),1/(trials_per[row["participant"]]*len(idx))
            )
        else:
            if theta is None:
                raise ValueError("propensity theta absent")
            q=_q(x)
            pred=np.asarray(expit(
                theta[0]+theta[1]*q+theta[2]*t[idx]),float)
            pred[idx==0]=1.
            pred[idx==len(t)-1]=1.
            minimum_p=min(minimum_p,float(pred.min()))
            propensity=np.clip(pred,PROPENSITY_MIN,1.)
            inv=1./propensity
            maximum_ipw=max(maximum_ipw,float(inv.max()))
            weights=inv/(trials_per[row["participant"]]*len(t))
        allX.append(X);allY.append(y);allW.append(weights)
        allG.append(np.full(len(y),row["participant"],int))
    if not allX:
        raise ValueError("R46 no retained observation points")
    return (
        np.vstack(allX),np.concatenate(allY),
        np.concatenate(allW),np.concatenate(allG),
        {"minimum_raw_fitted_propensity_at_retained_point":minimum_p,
         "maximum_clipped_inverse_weight":maximum_ipw,
         "effective_observation_weight_count":int(sum(len(x) for x in allY))}
    )


def focal_wls(panel,method="ipw",theta=None):
    X,y,w,cluster,diagnostics=_design(panel,method,theta)
    p=X.shape[1]
    if len(y)<=p:
        raise ValueError("R46 insufficient observed WLS rows")
    A=X.T@(w[:,None]*X)
    if np.linalg.matrix_rank(A)<p:
        raise ValueError("R46 mean function-on-scalar design rank deficient")
    beta=np.linalg.solve(A,X.T@(w*y))
    B=r16.basis(np.array([FOCAL_TIME]),"legendre5")
    contrast=np.r_[np.zeros(B.shape[1]),B[0]]
    return float(contrast@beta),(X,y,w,cluster,beta,contrast,diagnostics)


def cr1_pointwise(panel,method,theta,truth):
    estimate,(X,y,w,cluster,beta,c,diagnostics)=focal_wls(
        panel,method,theta
    )
    g=len(np.unique(cluster));n=len(y);p=X.shape[1]
    if g<MIN_PARTICIPANTS:
        raise ValueError("R46 too few independent participant clusters")
    A=X.T@(w[:,None]*X)
    V=np.linalg.solve(A,np.eye(p))
    r=y-X@beta
    scores=np.vstack([
        X[cluster==who].T@(w[cluster==who]*r[cluster==who])
        for who in np.unique(cluster)
    ])
    covariance=(g/(g-1))*((n-1)/(n-p))*V@(scores.T@scores)@V
    v=float(c@covariance@c)
    if not np.isfinite(v) or v<=0:
        raise ValueError("R46 nonpositive CR1 focal variance")
    half=float(student_t.ppf(.95,g-1)*np.sqrt(v))
    return {
        "estimate":estimate,"lower":float(estimate-half),
        "upper":float(estimate+half),
        "width":float(2*half),
        "contains_fixed_generating_truth":bool(
            estimate-half<=truth<=estimate+half),
        "cr1_standard_error":float(np.sqrt(v)),
        "observed_participant_df":g-1,
        "estimated_propensity_treated_as_fixed":method=="ipw",
        "numerical_propensity_diagnostics":diagnostics,
    }


def bootstrap_once(panel,ids,seed):
    """Whole-participant pairs, including all native scheduled (R,x,t,y)."""
    rng=np.random.default_rng(seed)
    picked=rng.choice(ids,size=len(ids),replace=True)
    selected=[]
    for new_unit,original_unit in enumerate(picked):
        for t in panel:
            if t["participant"]==int(original_unit):
                row=dict(t)
                row["participant"]=int(new_unit)
                selected.append(row)
    if len({x["participant"] for x in selected})!=len(ids):
        raise ValueError("R46 resampled participant identity collapsed")
    return selected


def evaluate(block,support,state):
    row={
        "study":STUDY,"block":block,"support":support,
        "generating_slope_state":state,"seed":SOURCE_SEED,
        "independent_unit_is_primitive_block":True,
        "source_status":"failed","source_error":None,
        "generating_fixed_focal_slope_truth":None,"scenarios":[],
        "inference_or_release_qualified":False,
    }
    try:
        original=independent_source(block,support,state)
        truth=float(
            r16.truth_coefficients(np.array([FOCAL_TIME]))[1][0,0]
        )
        row["generating_fixed_focal_slope_truth"]=truth
        row["source_status"]="ok"
    except Exception as exc:
        row["source_error"]={
            "type":type(exc).__name__,"message":str(exc)[:500]
        }
        return row
    for regime in REGIMES:
        scenario={
            "regime":regime,"source_status":"failed",
            "error":None,"retention":None,
            "pointwise_interval_records":[],
            "bootstrap_replicate_records":[],
            "missing_response_absent_from_propensity":True,
        }
        try:
            panel,retention=observation_panel(original,block,support,regime)
            scenario["retention"]=retention
            theta,prop_diag=fit_propensity(panel)
            scenario["observed_only_propensity_fit"]=prop_diag
            scenario["source_status"]="ok"
            ids=np.asarray(sorted({t["participant"] for t in panel}),int)
            point_naive=cr1_pointwise(panel,"naive",None,truth)
            point_fixed=cr1_pointwise(panel,"ipw",theta,truth)
            scenario["pointwise_interval_records"].append({
                "method":METHODS[0],"status":"ok",**point_naive,
                "not_validated_nominal_90":True,
            })
            scenario["pointwise_interval_records"].append({
                "method":METHODS[1],"status":"ok",**point_fixed,
                "not_validated_nominal_90":True,
            })
            boot_points=[]
            for rep in range(B_REPS):
                seed=(BOOTSTRAP_SEED+100003*block
                      +731*SUPPORT.index(support)
                      +137*STATES.index(state)
                      +1709*REGIMES.index(regime)+rep)
                one={"replicate":rep,"seed":seed,"status":"failed",
                     "error":None,"estimated_focal_slope":None,
                     "propensity_refitted":False}
                try:
                    selected=bootstrap_once(panel,ids,seed)
                    th,_=fit_propensity(selected)
                    val,_=focal_wls(selected,"ipw",th)
                    if not np.isfinite(val):
                        raise ValueError("nonfinite bootstrap estimate")
                    one.update(status="ok",estimated_focal_slope=float(val),
                               propensity_refitted=True)
                    boot_points.append(float(val))
                except Exception as exc:
                    one["error"]={"type":type(exc).__name__,
                                  "message":str(exc)[:300]}
                scenario["bootstrap_replicate_records"].append(one)
            if len(boot_points)==B_REPS:
                lower,upper=np.quantile(
                    np.asarray(boot_points),[.05,.95],method="linear"
                )
                scenario["pointwise_interval_records"].append({
                    "method":METHODS[2],"status":"ok",
                    "estimate":point_fixed["estimate"],
                    "lower":float(lower),"upper":float(upper),
                    "width":float(upper-lower),
                    "contains_fixed_generating_truth":bool(
                        lower<=truth<=upper),
                    "successful_bootstrap_replicates":len(boot_points),
                    "failed_bootstrap_replicates":0,
                    "propensity_refitted_in_every_bootstrap_replicate":True,
                    "percentile_not_studentized_or_CR2":True,
                    "not_validated_nominal_90":True,
                })
            else:
                scenario["pointwise_interval_records"].append({
                    "method":METHODS[2],"status":"failed",
                    "error":"incomplete_frozen_bootstrap_replicate_denominator",
                    "successful_bootstrap_replicates":len(boot_points),
                    "failed_bootstrap_replicates":B_REPS-len(boot_points),
                    "not_validated_nominal_90":True,
                })
        except Exception as exc:
            scenario["error"]={"type":type(exc).__name__,
                               "message":str(exc)[:400]}
            existing={x["method"] for x in scenario["pointwise_interval_records"]}
            for method in METHODS:
                if method not in existing:
                    scenario["pointwise_interval_records"].append({
                        "method":method,"status":"not_attempted",
                        "error":"source_or_propensity_stage_refusal",
                    })
            already={r["replicate"] for r in scenario["bootstrap_replicate_records"]}
            for rep in range(B_REPS):
                if rep not in already:
                    scenario["bootstrap_replicate_records"].append({
                        "replicate":rep,"status":"not_attempted",
                        "error":"source_or_propensity_stage_refusal",
                        "estimated_focal_slope":None,
                        "propensity_refitted":False,
                    })
        row["scenarios"].append(scenario)
    return row


def summarize(rows):
    expected={(b,s,t) for b in range(BLOCKS)
              for s in SUPPORT for t in STATES}
    ids=[(r["block"],r["support"],r["generating_slope_state"])
         for r in rows]
    if len(ids)!=len(set(ids)) or not set(ids).issubset(expected):
        raise ValueError("R46 duplicate or unregistered source variant")
    cases=[z for r in rows for z in r["scenarios"]]
    fits=[fit for z in cases for fit in z["pointwise_interval_records"]]
    reps=[r for z in cases for r in z["bootstrap_replicate_records"]]
    if any(
        tuple(x["method"] for x in c["pointwise_interval_records"])!=METHODS
        or len(c["bootstrap_replicate_records"])!=B_REPS
        or {b["replicate"] for b in c["bootstrap_replicate_records"]}!=set(range(B_REPS))
        for c in cases
    ):
        raise ValueError("R46 incomplete or swapped prespecified method/bootstrap slots")
    full=(len(rows)==N_SOURCE_VARIANTS
          and len(cases)==N_SOURCE_REGIMES
          and len(fits)==N_INTERVALS
          and len(reps)==N_BOOT_ATTEMPTS
          and all(r["source_status"]=="ok" for r in rows)
          and all(c["source_status"]=="ok" for c in cases))
    cells={}
    for regime in REGIMES:
        subset=[c for c in cases if c["regime"]==regime]
        reg={
            "prespecified_source_variants":N_SOURCE_VARIANTS,
            "recorded_source_variants":len(subset),
            "mean_interior_retention_fraction":(
                float(np.mean([c["retention"]["interior_point_retained_fraction"]
                               for c in subset if c["retention"]]))
                if any(c["retention"] for c in subset) else None),
            "model_is_misspecified":regime==REGIMES[1],
            "weak_overlap_design":regime==REGIMES[2],
            "method_cells":{},
        }
        for method in METHODS:
            group=[f for c in subset for f in c["pointwise_interval_records"]
                   if f["method"]==method]
            ok=[x for x in group if x["status"]=="ok"]
            reg["method_cells"][method]={
                "planned_intervals":N_SOURCE_VARIANTS,
                "recorded":len(group),
                "successful_intervals":len(ok),
                "failed_or_refused":len(group)-len(ok),
                "truth_inclusion_count_not_calibrated_coverage":sum(
                    x["contains_fixed_generating_truth"] for x in ok
                ),
                "mean_absolute_error":(
                    float(np.mean([abs(x["estimate"]-rows[0]["generating_fixed_focal_slope_truth"])
                                   for x in ok])) if ok else None),
                "mean_interval_width":(
                    float(np.mean([x["width"] for x in ok])) if ok else None),
            }
        boot=[r for c in subset for r in c["bootstrap_replicate_records"]]
        reg["bootstrap_replicate_attempts"]=len(boot)
        reg["bootstrap_failed_or_refused"]=sum(
            r["status"]!="ok" for r in boot)
        cells[regime]=reg
    return {
        "study":STUDY,"new_independent_primitive_blocks":BLOCKS,
        "participants_per_source":N_PARTICIPANTS,
        "paired_source_conditions_not_independent_draws":True,
        "master_primitive_seed":SOURCE_SEED,
        "retention_processes":REGIMES,"methods":METHODS,
        "fixed_bootstrap_replicates_per_source_case":B_REPS,
        "planned_source_variant_rows":N_SOURCE_VARIANTS,
        "recorded_source_variant_rows":len(rows),
        "planned_source_regime_cases":N_SOURCE_REGIMES,
        "recorded_source_regime_cases":len(cases),
        "planned_interval_records":N_INTERVALS,
        "recorded_interval_records":len(fits),
        "planned_bootstrap_replicate_attempts":N_BOOT_ATTEMPTS,
        "recorded_bootstrap_replicate_attempts":len(reps),
        "source_errors":sum(r["source_status"]!="ok" for r in rows),
        "selection_errors":sum(c["source_status"]!="ok" for c in cases),
        "complete_failure_inclusive_design":bool(full),
        "by_observable_MAR_regime":cells,
        "bootstrap_refits_propensity_from_observed_schedule_only":True,
        "no_MNAR_or_whole_unit_identification":True,
        "not_CR2_nuisance_estimation_aware":True,
        "not_validated_nominal_90_pointwise_or_simultaneous_coverage":True,
        "release_authorized":False,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    cases=[evaluate(b,s,t) for b in range(BLOCKS)
           for s in SUPPORT for t in STATES]
    summary=summarize(cases)
    for name,obj in (("cases.json",cases),("summary.json",summary)):
        (args.out/name).write_text(
            json.dumps(obj,sort_keys=True,indent=2,allow_nan=False)+"\n")
    (args.out/"source-commit.txt").write_text(
        os.environ.get("GITHUB_SHA","unverified-local")+"\n")
    files=("cases.json","summary.json","source-commit.txt")
    (args.out/"SHA256SUMS").write_text("".join(
        hashlib.sha256((args.out/f).read_bytes()).hexdigest()+"  "+f+"\n"
        for f in files))
    print("R46 BOOTSTRAP PROPENSITY-UNCERTAINTY PILOT:",
          json.dumps(summary,sort_keys=True))
    if not summary["complete_failure_inclusive_design"]:
        raise SystemExit("R46 source or replicate accounting refusal")


if __name__=="__main__":
    main()
