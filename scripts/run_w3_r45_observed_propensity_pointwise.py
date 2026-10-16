"""R45: prospective, observed-design propensity IPW and CR1 pointwise pilot.

Research only: a new independently seeded Gaussian 12-block study, nested
n=24/48, paired ordinary/extreme and zero/positive-slope source states.
Four observation mechanisms; only conditionally observable time/x-driven
point missingness is eligible for feasible propensity adjustment. MNAR and
unobserved whole-participant selection: explicitly NO IDENTIFIED correction.

Every source/observation/method WLS+participant-CR1 90% interval retained.
CR1 pilot is NOT CR2 or validated nominal coverage; 12 primitive blocks do
not support a formal 90% calibration claim. No simultaneous bands or release.
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

STUDY="W3_R45_NEW_SOURCE_OBSERVED_PROPENSITY_IPW_CR1_PILOT"
MASTER_SEED=202610164545
SELECTION_SEED=202610164546
BLOCKS=12
SIZES=(24,48)
MAX_N=48
SUPPORT=("ordinary_dependent","extreme_dependent")
STATES=("zero_slope","positive_slope")
PROCESSES=("complete","observed_time_x_MAR_point",
           "missing_y_MNAR_point","latent_y_whole_participant_selection")
METHODS={
    "complete":("observed_WLS_CR1",),
    "observed_time_x_MAR_point":(
        "observed_WLS_CR1",
        "fitted_observed_propensity_IPW_CR1",
        "known_design_propensity_IPW_CR1_benchmark",
    ),
    "missing_y_MNAR_point":("observed_WLS_CR1",),
    "latent_y_whole_participant_selection":("observed_WLS_CR1",),
}
N_SOURCE=BLOCKS*len(SIZES)*len(SUPPORT)*len(STATES)
N_OBSERVATION=N_SOURCE*len(PROCESSES)
N_INTERVALS=N_SOURCE*sum(len(x) for x in METHODS.values())
FOCAL_TIME=float(r16.TIME[r16.FOCAL])
NOMINAL=.90
MIN_PARTICIPANTS=6
MIN_PROPENSITY=.05
LOGIT_RIDGE=1e-5
MAX_NEWTON_STEPS=45


def gaussian_source(block,n,support,state):
    if (type(block) is not int or block not in range(BLOCKS) or n not in SIZES
            or support not in SUPPORT or state not in STATES):
        raise ValueError("outside frozen R45 primitive Gaussian design")
    case=fresh.fresh_source(
        block,support,n=n,master_seed=MASTER_SEED,
        n_blocks=BLOCKS,max_n=MAX_N
    )
    if state=="positive_slope":
        return case
    raw=dict(case[0])
    raw["participant_slope"]=np.zeros_like(raw["participant_slope"])
    return counterfactual.rescaled_source((raw,*case[1:]),1.)


def _rng(block,support,person,trial,process):
    # Independent selection uniforms reproducibly nested by native
    # participant/trial identifiers, separate from Gaussian generator.
    code=(SELECTION_SEED+100003*block+7919*person+151*trial
          +17*SUPPORT.index(support)+871*PROCESSES.index(process))
    return np.random.default_rng(code)


def point_probabilities(t,x,y,process):
    time=np.asarray(t,float)
    predictor=np.abs(float(x))/(1.+np.abs(float(x)))
    if process=="observed_time_x_MAR_point":
        p=expit(1.2-.9*predictor-.7*time)
    elif process=="missing_y_MNAR_point":
        p=expit(1.1-1.2*np.tanh(np.asarray(y,float)))
    else:
        raise ValueError("point probability requires MAR or MNAR process")
    p=np.asarray(p,float)
    if not np.isfinite(p).all() or np.any((p<=0)|(p>=1)):
        raise ValueError("invalid point probabilities")
    p[0]=p[-1]=1.
    return p


def observation_panel(case,block,support,process):
    """Return what estimator may use, no missing or excluded y leakage.

    A panel row with R=0 retains only native (x,t,person,trial), never y.
    For selection of an *entire* participant no missing-unit schedule enters
    the estimator's data, though the original cohort is counted in summary.
    """
    if process not in PROCESSES:
        raise ValueError("unregistered R45 observation process")
    _,gaze,x,person,trial,_=case
    x=np.asarray(x,float);person=np.asarray(person,int)
    trial=np.asarray(trial,int)
    groups=np.unique(person)
    retained={int(w):True for w in groups}
    if process=="latent_y_whole_participant_selection":
        for who in groups:
            curves=np.flatnonzero(person==who)
            full=np.concatenate([
                np.asarray(gaze.values[j])[:,0] for j in curves
            ])
            probability=float(expit(.4-.8*np.mean(full)))
            retained[int(who)]=bool(
                _rng(block,support,int(who),0,process).random()<probability
            )
    rows=[]
    full_native=sum(len(t) for t in gaze.time)
    native_trial_count=len(gaze.time)
    for j, (times,values) in enumerate(zip(gaze.time,gaze.values)):
        who=int(person[j]);tid=int(trial[j])
        if not retained[who]:
            continue
        t=np.asarray(times,float)
        potential_y=np.asarray(values,float)[:,0]
        if process in ("observed_time_x_MAR_point","missing_y_MNAR_point"):
            p=point_probabilities(t,x[j],potential_y,process)
            r=_rng(block,support,who,tid,process).random(len(t))<p
            r[0]=r[-1]=True
        else:
            p=np.ones(len(t));r=np.ones(len(t),dtype=bool)
        y=np.full(len(t),np.nan)
        y[r]=potential_y[r]
        rows.append({
            "person":who,"trial":tid,"predictor":float(x[j]),
            "native_time":t,
            "retained_indicator":r,
            "observed_y_nan_if_missing":y,
            "known_design_p_for_benchmark":(
                p if process=="observed_time_x_MAR_point" else None),
        })
    retained_people=len({z["person"] for z in rows})
    if retained_people<MIN_PARTICIPANTS:
        raise ValueError("fewer than six observed independent participants")
    observed=sum(int(v["retained_indicator"].sum()) for v in rows)
    return rows,{
        "source_participants":int(len(groups)),
        "retained_participants":retained_people,
        "excluded_participants":int(len(groups)-retained_people),
        "source_trials":native_trial_count,
        "retained_trials":len(rows),
        "source_native_points":int(full_native),
        "retained_native_points":observed,
        "retained_native_point_fraction":float(observed/full_native),
        "retained_participant_fraction":float(retained_people/len(groups)),
        "original_full_cohort_denominator_preserved":True,
        "selection_uses_potentially_missing_y":
            process in PROCESSES[2:],
        "excluded_unit_schedule_unavailable_to_estimator":
            process==PROCESSES[3],
    }


def fit_observed_logistic_propensity(panel):
    """Estimate selection using indicators and scheduled observed (x,t) only.

    Trial endpoints have known p=1 and are excluded from logistic fitting.
    No observed gaze y, missing gaze y, or simulated true probability enters
    this fitted-propensity function. A full scheduled x/t frame is an explicit
    auxiliary-data assumption and must not be silently generalized.
    """
    xfeatures=[];indicators=[]
    for trial in panel:
        t=trial["native_time"]
        q=abs(trial["predictor"])/(1.+abs(trial["predictor"]))
        for j in range(1,len(t)-1):
            xfeatures.append([1.,q,float(t[j])])
            indicators.append(float(trial["retained_indicator"][j]))
    F=np.asarray(xfeatures,float)
    R=np.asarray(indicators,float)
    if len(np.unique(R))<2 or np.linalg.matrix_rank(F)<3:
        raise ValueError("R45 observed-only propensity not estimable")
    theta=np.zeros(3)
    for step in range(MAX_NEWTON_STEPS):
        p=np.clip(expit(F@theta),1e-8,1.-1e-8)
        grad=F.T@(p-R)+LOGIT_RIDGE*np.r_[0.,theta[1:]]
        A=F.T@((p*(1.-p))[:,None]*F)
        A+=LOGIT_RIDGE*np.diag([0.,1.,1.])
        delta=np.linalg.solve(A,grad)
        theta-=delta
        if np.max(abs(delta))<1e-9:
            break
    p=np.clip(expit(F@theta),MIN_PROPENSITY,1.)
    return theta,{
        "training_scheduled_interior_points":int(len(R)),
        "training_observed_interior_points":int(R.sum()),
        "no_outcome_data_in_propensity_model":True,
        "minimum_predicted_interior_probability":float(p.min()),
        "maximum_predicted_interior_probability":float(p.max()),
        "logistic_newton_iterations":int(step+1),
    }


def construct_estimator_rows(panel,method):
    if method not in tuple(x for values in METHODS.values() for x in values):
        raise ValueError("unregistered R45 estimator")
    theta=None;diagnostics=None
    if method=="fitted_observed_propensity_IPW_CR1":
        theta,diagnostics=fit_observed_logistic_propensity(panel)
    trials_per={}
    for trial in panel:
        who=trial["person"];trials_per[who]=trials_per.get(who,0)+1
    allX=[];allY=[];allW=[];allG=[]
    for trial in panel:
        t=trial["native_time"]
        r=trial["retained_indicator"]
        if not r.any():
            continue
        who=trial["person"];x=trial["predictor"]
        B=r16.basis(t[r],"legendre5")
        X=np.column_stack((B,x*B))
        y=trial["observed_y_nan_if_missing"][r]
        if not np.isfinite(y).all():
            raise ValueError("missing gaze leaked to regression input")
        if method=="observed_WLS_CR1":
            weights=np.full(len(y),1/(trials_per[who]*len(y)))
        else:
            if method=="known_design_propensity_IPW_CR1_benchmark":
                p=trial["known_design_p_for_benchmark"]
                if p is None:
                    raise ValueError("known MAR design probability unavailable")
                prob=p[r]
            elif method=="fitted_observed_propensity_IPW_CR1":
                q=abs(x)/(1.+abs(x))
                prob=np.clip(
                    expit(theta[0]+theta[1]*q+theta[2]*t[r]),
                    MIN_PROPENSITY,1.,
                )
                # Endpoint observations have probability exactly 1 by design.
                loc=np.flatnonzero(r)
                prob[loc==0]=1.
                prob[loc==len(t)-1]=1.
            else:
                raise ValueError("invalid method")
            weights=1/(trials_per[who]*len(t)*prob)
        allX.append(X);allY.append(y);allW.append(weights)
        allG.append(np.full(len(y),who,int))
    return (np.vstack(allX),np.concatenate(allY),np.concatenate(allW),
            np.concatenate(allG)),diagnostics


def pointwise_cluster_CR1(panel,method,true_focal,realized_full_focal):
    (X,y,w,participant),propensity=construct_estimator_rows(panel,method)
    p=X.shape[1]
    unique=np.unique(participant)
    g=len(unique)
    n=len(y)
    if g<MIN_PARTICIPANTS or n<=p:
        raise ValueError("insufficient observed independent units or rank")
    A=X.T@(w[:,None]*X)
    if np.linalg.matrix_rank(A)<p:
        raise ValueError("rank deficient original focal mean model")
    beta=np.linalg.solve(A,X.T@(w*y))
    residual=y-X@beta
    scores=np.vstack([
        X[participant==who].T@(
            w[participant==who]*residual[participant==who]
        ) for who in unique
    ])
    V=np.linalg.solve(A,np.eye(p))
    correction=(g/(g-1))*((n-1)/(n-p))
    cov=correction*V@(scores.T@scores)@V
    cov=.5*(cov+cov.T)
    B=r16.basis(np.array([FOCAL_TIME]),"legendre5")
    c=np.r_[np.zeros(B.shape[1]),B[0]]
    est=float(c@beta)
    v=float(c@cov@c)
    if not np.isfinite(v) or v<=0:
        raise ValueError("invalid cluster CR1 focal variance")
    se=float(np.sqrt(v))
    half=float(student_t.ppf((1+NOMINAL)/2,g-1)*se)
    interval=(est-half,est+half)
    return {
        "method":method,"status":"ok",
        "point":est,"cluster_CR1_se":se,"lower_90":interval[0],
        "upper_90":interval[1],"participant_cluster_df":g-1,
        "observed_participant_count":g,"observed_native_points":n,
        "generating_true_focal_slope":true_focal,
        "realized_complete_cohort_focal_slope":realized_full_focal,
        "point_minus_generating_truth":float(est-true_focal),
        "point_minus_realized_full_cohort":float(est-realized_full_focal),
        "pointwise_interval_contains_generating_truth":bool(
            interval[0]<=true_focal<=interval[1]),
        "pointwise_interval_contains_realized_complete_focal":bool(
            interval[0]<=realized_full_focal<=interval[1]),
        "fitted_propensity_diagnostics":propensity,
        "CR1_not_CR2":True,
        "nominal_90_not_qualified":True,
        "no_simultaneous_band":True,
    }


def evaluate(block,n,support,state):
    row={
        "study":STUDY,"primitive_block":block,"full_participants":n,
        "support":support,"true_slope_state":state,
        "independent_unit_is_primitive_block":True,
        "new_source_seed":MASTER_SEED,
        "source_status":"failed","source_error":None,
        "full_cohort_reference":None,"observation_cases":[],
        "release_authorized":False,
    }
    try:
        case=gaussian_source(block,n,support,state)
        true=float(
            r16.truth_coefficients(np.asarray([FOCAL_TIME]))[1][0,0]
        )
        complete,cohort=observation_panel(case,block,support,"complete")
        ref=pointwise_cluster_CR1(
            complete,"observed_WLS_CR1",true,0.
        )["point"]
        row["full_cohort_reference"]={
            "generating_true_focal_slope":true,
            "realized_complete_cohort_focal_slope":ref,
            "full_source_participants":n,
            "full_source_native_points":cohort["source_native_points"],
        }
        row["source_status"]="ok"
    except Exception as exc:
        row["source_error"]={
            "type":type(exc).__name__,"message":str(exc)[:500]
        }
        return row

    for mechanism in PROCESSES:
        item={
            "observation_process":mechanism,"status":"failed",
            "error":None,"retention":None,"interval_results":[],
            "no_inference_from_MNAR_or_unit_selection":True,
        }
        try:
            panel,retention=observation_panel(
                case,block,support,mechanism
            )
            item["retention"]=retention
            item["status"]="ok"
            for method in METHODS[mechanism]:
                try:
                    fit=pointwise_cluster_CR1(
                        panel,method,true,ref
                    )
                except Exception as exc:
                    fit={
                        "method":method,"status":"failed",
                        "error":{"type":type(exc).__name__,
                                 "message":str(exc)[:500]},
                        "nominal_90_not_qualified":True,
                    }
                item["interval_results"].append(fit)
        except Exception as exc:
            item["error"]={
                "type":type(exc).__name__,"message":str(exc)[:500]
            }
            item["interval_results"]=[
                {"method":method,"status":"not_attempted",
                 "error":"observation_mechanism_failed"}
                for method in METHODS[mechanism]
            ]
        row["observation_cases"].append(item)
    return row


def summarize(rows):
    expected={(b,n,s,t) for b in range(BLOCKS) for n in SIZES
              for s in SUPPORT for t in STATES}
    keys=[(r["primitive_block"],r["full_participants"],
           r["support"],r["true_slope_state"]) for r in rows]
    if len(set(keys))!=len(keys) or not set(keys).issubset(expected):
        raise ValueError("duplicate or unregistered primitive source")
    cases=[c for r in rows for c in r["observation_cases"]]
    fits=[fit for c in cases for fit in c["interval_results"]]
    cells={}
    for mech in PROCESSES:
        relevant=[c for c in cases if c["observation_process"]==mech]
        pool=[c["retention"] for c in relevant if c["retention"] is not None]
        methods={}
        for m in METHODS[mech]:
            rows_m=[z for c in relevant for z in c["interval_results"]
                    if z["method"]==m]
            ok=[z for z in rows_m if z["status"]=="ok"]
            methods[m]={
                "expected_source_variants":N_SOURCE,
                "recorded_fit_records":len(rows_m),
                "successful_interval_fits":len(ok),
                "failed_or_refused":len(rows_m)-len(ok),
                "empirical_truth_inclusion_numerator":sum(
                    z["pointwise_interval_contains_generating_truth"]
                    for z in ok),
                "empirical_truth_inclusion_denominator":len(ok),
                "mean_absolute_point_minus_generating_truth":(
                    float(np.mean([abs(z["point_minus_generating_truth"])
                                   for z in ok])) if ok else None),
                "mean_absolute_point_minus_realized_full_cohort":(
                    float(np.mean([abs(z["point_minus_realized_full_cohort"])
                                   for z in ok])) if ok else None),
                "mean_pointwise_interval_width":(
                    float(np.mean([z["upper_90"]-z["lower_90"]
                                   for z in ok])) if ok else None),
                "independent_primitive_block_count":BLOCKS,
                "NOT_a_validated_nominal_90_coverage_rate":True,
            }
        cells[mech]={
            "expected_cases":N_SOURCE,
            "recorded_cases":len(relevant),
            "mean_retained_participants":(
                float(np.mean([x["retained_participants"]
                               for x in pool])) if pool else None),
            "mean_retained_native_fraction":(
                float(np.mean([x["retained_native_point_fraction"]
                               for x in pool])) if pool else None),
            "mean_retained_participant_fraction":(
                float(np.mean([x["retained_participant_fraction"]
                               for x in pool])) if pool else None),
            "methods":methods,
        }
    full=(len(rows)==N_SOURCE and len(cases)==N_OBSERVATION
          and len(fits)==N_INTERVALS
          and all(r["source_status"]=="ok" for r in rows)
          and all(c["status"]=="ok" for c in cases))
    return {
        "study":STUDY,
        "new_master_seed":MASTER_SEED,
        "independent_primitive_blocks":BLOCKS,
        "nested_participant_counts":SIZES,
        "paired_supports_and_source_states":True,
        "scheduled_time_and_predictor_are_observed_for_MAR_point_loss":True,
        "IPW_feasible_only_under_observed_design_point_selection":True,
        "IPW_not_assumed_identified_under_MNAR_or_unit_selection":True,
        "planned_source_variant_rows":N_SOURCE,
        "recorded_source_variant_rows":len(rows),
        "planned_observation_cases":N_OBSERVATION,
        "recorded_observation_cases":len(cases),
        "planned_pointwise_interval_records":N_INTERVALS,
        "recorded_pointwise_interval_records":len(fits),
        "complete_original_design_recorded":bool(full),
        "source_errors":sum(r["source_status"]!="ok" for r in rows),
        "observation_errors":sum(c["status"]!="ok" for c in cases),
        "method_cases":cells,
        "CR1_cluster_pointwise_pilot_only":True,
        "CR2_nuisance_estimation_not_qualified":True,
        "no_90_pointwise_coverage_qualification":True,
        "no_90_simultaneous_whole_function_band_qualification":True,
        "no_typeI_or_power_boundary_variance_test":True,
        "release_authorized":False,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    cases=[evaluate(b,n,s,t) for b in range(BLOCKS) for n in SIZES
           for s in SUPPORT for t in STATES]
    summary=summarize(cases)
    for filename,obj in (("cases.json",cases),("summary.json",summary)):
        (args.out/filename).write_text(
            json.dumps(obj,sort_keys=True,indent=2,allow_nan=False)+"\n")
    (args.out/"source-commit.txt").write_text(
        os.environ.get("GITHUB_SHA","unverified-local")+"\n")
    names=("cases.json","summary.json","source-commit.txt")
    (args.out/"SHA256SUMS").write_text("".join(
        hashlib.sha256((args.out/n).read_bytes()).hexdigest()+"  "+n+"\n"
        for n in names))
    print("R45 OBSERVED-PROPENSITY AND CR1 PILOT:",
          json.dumps(summary,sort_keys=True))
    if not summary["complete_original_design_recorded"]:
        raise SystemExit("R45 source integrity or observation refusal; negative evidence retained")


if __name__=="__main__":
    main()
