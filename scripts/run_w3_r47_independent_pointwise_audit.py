"""W3 R47 independent-source, failure-inclusive exploratory pointwise audit.

256 NEW Gaussian primitive generating blocks, ONE source condition per block:
n24, ordinary dependent predictor support, positive Gaussian random slope.
This gives 256 truly independent source replicates in each fixed observation
regime, unlike earlier studies' paired variants. Complete, additive-logit
observed-design MAR and weak-overlap MAR are PAIRED across blocks.
Predeclared 79 full-participant bootstrap refits per MAR block/regime.
Fixed generating truth; 90% exploratory focal intervals and 95% Wilson MC
uncertainty for independent-block inclusion counts. No fitted-covariance
CR2, simultaneous bands, boundary null test, or public API promotion.
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
from scipy.stats import norm

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import run_w3_r16_leverage_covariance_factorial as r16
from scripts import run_w3_r17_fresh_feasibility as fresh
from scripts import run_w3_r46_propensity_bootstrap as r46

STUDY="W3_R47_NEW_INDEPENDENT_PRIMITIVES_FAILURE_INCLUSIVE_POINTWISE_AUDIT"
SOURCE_SEED=202610164747
OBSERVATION_SEED=202610164748
RESAMPLE_SEED=202610164749
BLOCKS=256
PARTICIPANTS=24
SUPPORT="ordinary_dependent"
TRUE_SLOPE="positive_slope"
REGIMES=("complete", "matched_observed_design_logit",
         "weak_overlap_observed_design_logit")
METHODS={
    "complete":("complete_WLS_CR1",),
    "matched_observed_design_logit":(
        "MAR_naive_WLS_CR1",
        "MAR_fitted_IPW_fixed_CR1",
        "MAR_fitted_IPW_refit_pairs_percentile",
    ),
    "weak_overlap_observed_design_logit":(
        "MAR_naive_WLS_CR1",
        "MAR_fitted_IPW_fixed_CR1",
        "MAR_fitted_IPW_refit_pairs_percentile",
    ),
}
BOOT_REPS=79
NOMINAL=.90
MC_CONFIDENCE=.95
PLANNED_SOURCE_CASES=BLOCKS
PLANNED_REGIME_CASES=BLOCKS*len(REGIMES)
PLANNED_INTERVALS=BLOCKS*sum(len(x) for x in METHODS.values())
PLANNED_REPLICATES=BLOCKS*(len(REGIMES)-1)*BOOT_REPS
FOCAL_TIME=float(r16.TIME[r16.FOCAL])


def generating_source(block):
    if type(block) is not int or not 0<=block<BLOCKS:
        raise ValueError("outside R47 independently frozen block set")
    # R17's simulator forbids unregistered participant counts. n=24 is
    # inherited without extending or weakening its original contract.
    return fresh.fresh_source(
        block,SUPPORT,n=PARTICIPANTS,master_seed=SOURCE_SEED,
        n_blocks=BLOCKS,max_n=PARTICIPANTS,
    )


def observed_panel(case,block,regime):
    """Observed-only regression input plus full native scheduled R,x,t.

    True Bernoulli probability is used ONLY to simulate retention.
    Original missing gaze y is explicitly replaced by NaN in every panel.
    """
    if regime not in REGIMES:
        raise ValueError("R47 unregistered observation regime")
    _,gaze,predictor,people,trials,_=case
    frames=[]
    points=0
    retained=0
    interior=0
    kept_interior=0
    for j,(time,values) in enumerate(zip(gaze.time,gaze.values)):
        t=np.asarray(time,float)
        person=int(people[j])
        trial=int(trials[j])
        y=np.asarray(values,float)[:,0]
        if regime=="complete":
            mask=np.ones(len(t),dtype=bool)
        else:
            original_p=r46.retention_probability(
                t,float(predictor[j]),regime)
            # Distinct R47 observation RNG; matched and weak loss are
            # reproducible but not labelled independent primitive draws.
            seed=(OBSERVATION_SEED + 100003*block +
                  7919*person + 151*trial +
                  1009*REGIMES.index(regime))
            mask=np.random.default_rng(seed).random(len(t))<original_p
            mask[0]=mask[-1]=True
        obs=np.full(len(t),np.nan)
        obs[mask]=y[mask]
        frames.append({
            "participant":person,
            "trial":trial,
            "predictor":float(predictor[j]),
            "scheduled_native_time":t,
            "observed_indicator":mask,
            "observed_gaze_NaN_if_missing":obs,
        })
        points+=len(t)
        retained+=int(mask.sum())
        interior+=len(t)-2
        kept_interior+=int(mask[1:-1].sum())
    if len({x["participant"] for x in frames})!=PARTICIPANTS:
        raise ValueError("R47 unexpectedly omitted a primitive source unit")
    return frames,{
        "original_participants":PARTICIPANTS,
        "observed_participants":PARTICIPANTS,
        "original_native_points":points,
        "observed_native_points":retained,
        "native_point_retention_fraction":float(retained/points),
        "interior_retention_fraction":float(kept_interior/interior),
        "only_observed_R_x_t_enter_fitted_propensity":True,
        "original_missing_y_set_to_NaN":True,
    }


def failure(method,kind,error):
    return {
        "method":method,"status":"failed",
        "error":{"kind":kind,"description":str(error)[:350]},
        "truth_included":False,
        "not_validated_nominal_coverage":True,
    }


def interval_row(method,fit):
    return {
        "method":method,"status":"ok",
        "estimate":float(fit["estimate"]),
        "lower":float(fit["lower"]),
        "upper":float(fit["upper"]),
        "width":float(fit["width"]),
        "truth_included":bool(fit["contains_fixed_generating_truth"]),
        "not_validated_nominal_coverage":True,
    }


def refit_bootstrap_once(panel,ids,seed):
    # Whole-participant resampling refits BOTH propensity and focal WLS.
    rep_panel=r46.bootstrap_once(panel,ids,seed)
    rep_theta,_=r46.fit_propensity(rep_panel)
    value,_=r46.focal_wls(rep_panel,"ipw",rep_theta)
    if not np.isfinite(value):
        raise ValueError("nonfinite refitted bootstrap focal estimate")
    return float(value)


def evaluate_source(block):
    result={
        "primitive_block":block,"source_status":"failed","source_error":None,
        "source_seed":SOURCE_SEED,
        "source_is_independent_of_other_R47_blocks":True,
        "source_count_one_design_not_four_paired_variants":True,
        "generating_truth":None,"regimes":[],
        "release_authorized":False,
    }
    try:
        source=generating_source(block)
        truth=float(
            r16.truth_coefficients(np.array([FOCAL_TIME]))[1][0,0]
        )
        result["generating_truth"]=truth
        result["source_status"]="ok"
    except Exception as exc:
        result["source_error"]={
            "type":type(exc).__name__,"message":str(exc)[:350]}
        return result
    for regime in REGIMES:
        item={
            "regime":regime,"observation_status":"failed",
            "observation_error":None,
            "retention":None,
            "intervals":[],
            "bootstrap_attempts":[],
            "full_source_denominator_retained":True,
        }
        try:
            panel,retention=observed_panel(source,block,regime)
            item["retention"]=retention
            item["observation_status"]="ok"
        except Exception as exc:
            item["observation_error"]={
                "type":type(exc).__name__,
                "message":str(exc)[:350],
            }
            for method in METHODS[regime]:
                item["intervals"].append(failure(
                    method,"observation_refusal",item["observation_error"]))
            if regime!="complete":
                for k in range(BOOT_REPS):
                    item["bootstrap_attempts"].append({
                        "replicate":k,"status":"not_attempted",
                        "error":"observation_refusal"})
            result["regimes"].append(item)
            continue
        if regime=="complete":
            method=METHODS[regime][0]
            try:
                v=r46.cr1_pointwise(panel,"naive",None,truth)
                item["intervals"].append(interval_row(method,v))
            except Exception as exc:
                item["intervals"].append(failure(
                    method,type(exc).__name__,str(exc)))
            result["regimes"].append(item)
            continue
        # Fit each method independently: failure of IPW must not erase
        # a still-computable naïve interval, and vice versa.
        naive=METHODS[regime][0]
        try:
            v=r46.cr1_pointwise(panel,"naive",None,truth)
            item["intervals"].append(interval_row(naive,v))
        except Exception as exc:
            item["intervals"].append(failure(
                naive,type(exc).__name__,str(exc)))
        theta=None
        try:
            theta,prop_diag=r46.fit_propensity(panel)
            item["fitted_propensity_information"]=prop_diag
            v=r46.cr1_pointwise(panel,"ipw",theta,truth)
            item["intervals"].append(interval_row(METHODS[regime][1],v))
        except Exception as exc:
            item["intervals"].append(failure(
                METHODS[regime][1],type(exc).__name__,str(exc)))
        ids=np.array(sorted({x["participant"] for x in panel}),int)
        samples=[]
        for k in range(BOOT_REPS):
            seed=(RESAMPLE_SEED+100003*block+
                  1009*REGIMES.index(regime)+k)
            record={"replicate":k,"seed":seed,"status":"failed",
                    "estimate":None,"error":None}
            try:
                estimate=refit_bootstrap_once(panel,ids,seed)
                record.update(status="ok",estimate=estimate)
                samples.append(estimate)
            except Exception as exc:
                record["error"]={"type":type(exc).__name__,
                                 "message":str(exc)[:300]}
            item["bootstrap_attempts"].append(record)
        method=METHODS[regime][2]
        if theta is not None and len(samples)==BOOT_REPS:
            try:
                central,_=r46.focal_wls(panel,"ipw",theta)
                lo,hi=np.quantile(
                    np.asarray(samples,float),[.05,.95],method="linear")
                if not (np.isfinite(lo) and np.isfinite(hi) and lo<=hi):
                    raise ValueError("invalid interval limits")
                item["intervals"].append({
                    "method":method,"status":"ok",
                    "estimate":float(central),
                    "lower":float(lo),"upper":float(hi),
                    "width":float(hi-lo),
                    "truth_included":bool(lo<=truth<=hi),
                    "successful_refits":BOOT_REPS,
                    "point_estimate_matches_fitted_ipw":True,
                    "not_validated_nominal_coverage":True,
                })
            except Exception as exc:
                item["intervals"].append(failure(
                    method,type(exc).__name__,str(exc)))
        else:
            item["intervals"].append(failure(
                method,"incomplete_bootstrap_or_propensity",
                "all original resamples and original propensity fit required"))
        result["regimes"].append(item)
    return result


def wilson(successes,denominator,confidence=MC_CONFIDENCE):
    """Independent primitive-block binomial diagnostic, no pooled pairs."""
    if not isinstance(successes,int) or not 0<=successes<=denominator:
        raise ValueError("invalid Wilson successes")
    if denominator<1:
        raise ValueError("independent simulation denominator must be >0")
    z=float(norm.ppf((1+confidence)/2))
    p=successes/denominator
    d=1+z*z/denominator
    mid=(p+z*z/(2*denominator))/d
    half=z/d*np.sqrt(p*(1-p)/denominator+z*z/(4*denominator**2))
    return [float(mid-half),float(mid+half)]


def summarize(rows):
    keys=[x["primitive_block"] for x in rows]
    if len(set(keys))!=len(keys) or any(
        not isinstance(k,int) or not 0<=k<BLOCKS for k in keys
    ):
        raise ValueError("R47 duplicate or unregistered source blocks")
    obs=[o for r in rows for o in r["regimes"]]
    slots=[f for o in obs for f in o["intervals"]]
    boot=[f for o in obs for f in o["bootstrap_attempts"]]
    if any(
        tuple(f["method"] for f in o["intervals"])!=METHODS[o["regime"]]
        or len(o["bootstrap_attempts"])!=(
            0 if o["regime"]=="complete" else BOOT_REPS)
        or {f["replicate"] for f in o["bootstrap_attempts"]}!=(
            set() if o["regime"]=="complete" else set(range(BOOT_REPS)))
        for o in obs
    ):
        raise ValueError("R47 interval or bootstrap slot integrity failure")
    complete=(len(rows)==PLANNED_SOURCE_CASES
              and len(obs)==PLANNED_REGIME_CASES
              and len(slots)==PLANNED_INTERVALS
              and len(boot)==PLANNED_REPLICATES
              and all(r["source_status"]=="ok" for r in rows)
              and all(o["observation_status"]=="ok" for o in obs))
    strata={}
    for regime in REGIMES:
        selection=[o for o in obs if o["regime"]==regime]
        methods={}
        for method in METHODS[regime]:
            items=[f for o in selection for f in o["intervals"]
                   if f["method"]==method]
            success=[f for f in items if f["status"]=="ok"]
            hits=sum(f["truth_included"] for f in success)
            all_n=PLANNED_SOURCE_CASES
            methods[method]={
                "planned_independent_primitive_blocks":all_n,
                "recorded_interval_slots":len(items),
                "successful_intervals":len(success),
                "failed_or_refused_intervals":len(items)-len(success),
                "truth_included_numerator":hits,
                "truth_included_all_planned_independent_blocks_denominator":all_n,
                "all_block_truth_inclusion_fraction_failure_as_not_covered":
                    hits/all_n,
                "all_block_truth_inclusion_Wilson95":wilson(hits,all_n),
                "nominal_0_90_inside_Wilson95":(
                    wilson(hits,all_n)[0]<=NOMINAL<=
                    wilson(hits,all_n)[1]),
                "successful_only_truth_inclusion_fraction":(
                    hits/len(success) if success else None),
                "mean_abs_error_vs_generator":(
                    float(np.mean([
                        abs(f["estimate"]-source_truth)
                        for f in success for source_truth in [
                            float(rows[0]["generating_truth"])
                        ]
                    ])) if success and rows[0]["generating_truth"] is not None
                    else None),
                "mean_interval_width":(
                    float(np.mean([f["width"] for f in success]))
                    if success else None),
                "not_established_CR2_or_nominal_coverage":True,
            }
        attempts=[f for o in selection for f in o["bootstrap_attempts"]]
        retained=[o["retention"] for o in selection if o["retention"]]
        strata[regime]={
            "planned_independent_source_cases":BLOCKS,
            "recorded_source_cases":len(selection),
            "mean_interior_native_retention":(
                float(np.mean([r["interior_retention_fraction"]
                               for r in retained]))
                if retained else None),
            "planned_bootstrap_attempts":(
                0 if regime=="complete" else BLOCKS*BOOT_REPS),
            "recorded_bootstrap_attempts":len(attempts),
            "failed_or_refused_bootstrap_attempts":sum(
                f["status"]!="ok" for f in attempts),
            "method_results":methods,
        }
    return {
        "study":STUDY,"seed":SOURCE_SEED,
        "source_condition":"n24,ordinary_dependent,true_positive_random_slope",
        "new_independent_primitive_blocks":BLOCKS,
        "paired_observation_regimes_not_independent_sources":True,
        "nominal_pointwise_target":NOMINAL,
        "Monte_Carlo_Wilson_interval_confidence":MC_CONFIDENCE,
        "bootstrap_refits_per_MAR_case":BOOT_REPS,
        "planned_source_cases":PLANNED_SOURCE_CASES,
        "recorded_source_cases":len(rows),
        "planned_observation_regime_cases":PLANNED_REGIME_CASES,
        "recorded_observation_regime_cases":len(obs),
        "planned_interval_records":PLANNED_INTERVALS,
        "recorded_interval_records":len(slots),
        "planned_bootstrap_attempts":PLANNED_REPLICATES,
        "recorded_bootstrap_attempts":len(boot),
        "source_failures":sum(r["source_status"]!="ok" for r in rows),
        "observation_failures":sum(o["observation_status"]!="ok" for o in obs),
        "complete_failure_inclusive_source_design":bool(complete),
        "results":strata,
        "Wilson_MC_intervals_are_not_confidence_interval_procedure_validation":True,
        "no_fitted_working_covariance_CR2_or_Satterthwaite_inference":True,
        "no_simultaneous_whole_function_band":True,
        "no_boundary_variance_component_null_test":True,
        "no_MNAR_or_latent_participant_selection_identification":True,
        "release_authorized":False,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    rows=[evaluate_source(i) for i in range(BLOCKS)]
    summary=summarize(rows)
    for file_name,record in (
        ("cases.json",rows),("summary.json",summary)
    ):
        (args.out/file_name).write_text(
            json.dumps(record,indent=2,sort_keys=True,allow_nan=False)+"\n")
    (args.out/"source-commit.txt").write_text(
        os.environ.get("GITHUB_SHA","unverified-local")+"\n")
    names=("cases.json","summary.json","source-commit.txt")
    (args.out/"SHA256SUMS").write_text("".join(
        hashlib.sha256((args.out/n).read_bytes()).hexdigest()+"  "+n+"\n"
        for n in names))
    print("R47 independent pointwise Monte Carlo audit:",
          json.dumps(summary,sort_keys=True))
    if not summary["complete_failure_inclusive_source_design"]:
        raise SystemExit("R47 incomplete original source design, preserving failures")


if __name__=="__main__":
    main()
