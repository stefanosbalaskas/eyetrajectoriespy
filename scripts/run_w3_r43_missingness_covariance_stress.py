"""R43: predeclared fresh Gaussian-source numerical KKT stress, not inference.

Four NEW independent primitive blocks; paired n24/n48, ordinary/extreme
dependent support, true zero/positive random slope, complete/anchored random
point dropout, matched predictor-scaled vs misspecified shared-slope *working*
covariance, frozen exact-zero/positive slope profiles, one near-bound nuisance
initializer; old linear L-BFGS-B vs frozen strict restart. All 512 stage slots
preserved. Does not calibrate CR2 or a variance-component boundary test.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts import run_w3_r16_leverage_covariance_factorial as r16
from scripts import run_w3_r17_fresh_feasibility as fresh
from scripts import run_w3_r29_predictor_spread_recovery as counterfactual
from scripts import run_w3_r39_nuisance_coordinate_audit as r39
from scripts import run_w3_r41_targeted_kkt_refinement as r41
from scripts import run_w3_r42_independent_kkt_validation as r42
from scripts.w3_r20_estimated_working_target import observed_weighted_rows
from scripts.w3_r25_gaussian_reml_components import prepare_reml_design

STUDY="W3_R43_FRESH_PAIRED_N_SIZE_DROPOUT_MISSPEC_NUMERIC_STRESS"
MASTER_SEED=202610164343
MASK_SEED=202610164344
BLOCKS=4
SIZES=(24,48)
MAX_N=48
SUPPORT=("ordinary_dependent","extreme_dependent")
STATES=("zero_slope","positive_slope")
OBSERVATION=("complete","anchored_independent_point_dropout")
WORKING=("matched_predictor_scaled","misspecified_shared_slope")
SLOPE_RATIOS=(0.,.75)
INITIALIZER="intercept_near_lower"
START_RATIOS=(r39.LOW*1.01,.5,1.)
STAGES=("original_R40_raw_linear","stricter_LBFGSB_restart")
MCAR_INTERIOR_KEEP_PROBABILITY=.70
MIN_POINTS_PER_NATIVE_TRIAL=4
NLL_TOL=1e-3
KKT_TOL=1e-3
PLANNED_SOURCE_CASES=(BLOCKS*len(SIZES)*len(SUPPORT)*len(STATES)
                      *len(OBSERVATION))
PLANNED_FIT_CELLS=PLANNED_SOURCE_CASES*len(WORKING)*len(SLOPE_RATIOS)
PLANNED_STAGE_RECORDS=PLANNED_FIT_CELLS*len(STAGES)


def gaussian_source(block,n,support,state):
    if (type(block) is not int or block not in range(BLOCKS)
            or n not in SIZES or support not in SUPPORT or state not in STATES):
        raise ValueError("R43 source outside frozen independent design")
    original=fresh.fresh_source(
        block,support,n=n,master_seed=MASTER_SEED,
        n_blocks=BLOCKS,max_n=MAX_N
    )
    if state=="positive_slope":
        return original
    raw=dict(original[0])
    raw["participant_slope"]=np.zeros_like(raw["participant_slope"])
    return counterfactual.rescaled_source((raw,*original[1:]),1.)


def retained_indices_for_case(source_case,block,support):
    """Design-anchored random point loss; independent of response values.

    First and last time anchors remain, with a minimum four native points per
    trial. Only interior Bernoulli draws are stochastic, p=.70 retained.
    The RNG deliberately ignores generating slope state and participant count
    for identically paired/nested masks. Not an empirical gaze-loss model.
    """
    if support not in SUPPORT or block not in range(BLOCKS):
        raise ValueError("outside original R43 mask experiment")
    gaze=source_case[1]
    seed=MASK_SEED+7919*block+101*(support=="extreme_dependent")
    rng=np.random.default_rng(seed)
    selected=[]
    for t in gaze.time:
        k=len(t)
        if k<MIN_POINTS_PER_NATIVE_TRIAL:
            raise ValueError("native trial insufficient for R43 dropout")
        mask=np.zeros(k,dtype=bool)
        mask[[0,-1]]=True
        if k>2:
            mask[1:-1]=rng.random(k-2)<MCAR_INTERIOR_KEEP_PROBABILITY
        if mask.sum()<MIN_POINTS_PER_NATIVE_TRIAL:
            candidates=np.flatnonzero(~mask)
            mask[candidates[:MIN_POINTS_PER_NATIVE_TRIAL-int(mask.sum())]]=True
        selected.append(np.flatnonzero(mask))
    return selected


def condition_source(block,n,support,state,observation):
    if observation not in OBSERVATION:
        raise ValueError("unregistered R43 observation process")
    case=gaussian_source(block,n,support,state)
    if observation=="complete":
        return case
    original=case[1]
    positions=retained_indices_for_case(case,block,support)
    if any(len(ix)<MIN_POINTS_PER_NATIVE_TRIAL for ix in positions):
        raise ValueError("refuse R43 too-few retained native time points")
    gaze=r16.IrregularTrajectorySet(
        time=tuple(np.asarray(t)[idx] for t,idx in zip(original.time,positions)),
        values=tuple(np.asarray(v)[idx,:] for v,idx in zip(original.values,positions)),
        curve_ids=original.curve_ids,
        dimension_names=original.dimension_names,
        time_unit=original.time_unit,
        coordinate_system=original.coordinate_system,
        metadata=original.metadata.copy(),
        provenance={**original.provenance,
                    "research_study":STUDY,
                    "response_dependent_loss":False,
                    "interior_point_retention_probability":
                        MCAR_INTERIOR_KEEP_PROBABILITY,
                    "endpoints_retained_by_design":True,
                    "minimum_native_points_per_trial":MIN_POINTS_PER_NATIVE_TRIAL,
                    "interpolation_performed":False},
    )
    return (None,gaze,case[2],case[3],case[4],case[5])


def prepare_case(block,n,support,state,observation,working):
    if working not in WORKING:
        raise ValueError("unregistered R43 working covariance target")
    case=condition_source(block,n,support,state,observation)
    X,y,weight,cluster,time,trial,x=observed_weighted_rows(
        case,"legendre5"
    )
    slope=("predictor_scaled_slope" if working=="matched_predictor_scaled"
           else "shared_slope")
    prepared=prepare_reml_design(
        X,y,weight,cluster,time,trial,x,slope=slope
    )
    Z=X*np.sqrt(weight)[:,None]
    beta=np.linalg.lstsq(Z,y*np.sqrt(weight),rcond=None)[0]
    ref=max(float(np.mean((y-X@beta)**2)),1e-8)
    if not np.isfinite(ref) or ref<=0:
        raise ValueError("nonpositive observable reference variance")
    nt=sum(len(t) for t in case[1].time)
    return prepared,ref,int(nt),int(len(case[1].time))


def source_evaluation(block,n,support,state,observation):
    row={
        "study":STUDY,
        "primitive_block":int(block),"participants":int(n),
        "support":support,"true_random_slope_state":state,
        "observation_process":observation,
        "source_status":"failed","source_error":None,
        "new_primitive_block_seed":MASTER_SEED,
        "independent_primitive_unit_is_block":True,
        "covariance_working_family_controls_not_new_sources":True,
        "no_coverage_or_release_qualification":True,
        "model_profiles":[],
    }
    for working in WORKING:
        model={"working_family":working,"fit_status":"failed",
               "error":None,"slope_profiles":[]}
        try:
            prepared,ref,points,trials=prepare_case(
                block,n,support,state,observation,working
            )
            model.update(
                fit_status="ok",observed_only_reference_variance=float(ref),
                native_observed_timepoints=points,native_trial_count=trials
            )
            row["source_status"]="ok"
            for slope_ratio in SLOPE_RATIOS:
                profile={"fixed_slope_ratio":float(slope_ratio),
                         "stage_fits":[]}
                try:
                    base=r39.fit_one(
                        prepared,ref,slope_ratio,np.log(np.array(START_RATIOS)),
                        INITIALIZER,"linear_variance_ratios","raw_NLL",0.
                    )
                    if base["status"]=="ok":
                        basefit={
                            "algorithm":STAGES[0],
                            "status":"ok","optimizer_success":True,
                            "error":None,
                            "original_unshifted_NLL":
                                float(base["gaussian_restricted_NLL"]),
                            "physical_KKT_absmax":
                                float(base["shared_ratio_projected_KKT_absmax"]),
                            "nuisance_variance_ratios":
                                base["nuisance_variance_ratios"],
                            "fit_reconstruction_error":
                                float(base["objective_reconstruction_error"]),
                        }
                    else:
                        basefit={
                            "algorithm":STAGES[0],"status":base["status"],
                            "optimizer_success":
                                bool(base.get("optimizer_success",False)),
                            "error":base.get("error"),
                            "optimizer_message":base.get("optimizer_message")
                        }
                    profile["stage_fits"].append(basefit)
                    if base["status"]=="ok":
                        restart=r41.restart(
                            base,prepared,ref,slope_ratio,STAGES[1]
                        )
                        f=restart.get("fit")
                        profile["stage_fits"].append({
                            "algorithm":STAGES[1],
                            "status":restart["status"],
                            "optimizer_success":
                                bool(restart.get("optimizer_success",False)),
                            "error":restart.get("error"),
                            "optimizer_message":restart.get("message"),
                            **({
                                "original_unshifted_NLL":
                                    f["original_unshifted_NLL"],
                                "physical_KKT_absmax":
                                    f["physical_ratio_projected_KKT_absmax"],
                                "nuisance_variance_ratios":
                                    f["nuisance_variance_ratios"],
                                "fit_reconstruction_error":
                                    f["optimizer_objective_reconstruction_abs_error"],
                            } if f is not None else {}),
                        })
                    else:
                        profile["stage_fits"].append({
                            "algorithm":STAGES[1],
                            "status":"not_attempted",
                            "optimizer_success":False,
                            "error":"baseline_failed_preserved",
                        })
                except Exception as exc:
                    profile["stage_fits"].append({
                        "algorithm":STAGES[0],"status":"failed",
                        "optimizer_success":False,
                        "error":{"type":type(exc).__name__,
                                 "message":str(exc)[:500]},
                    })
                    profile["stage_fits"].append({
                        "algorithm":STAGES[1],"status":"not_attempted",
                        "optimizer_success":False,
                        "error":"baseline_exception_preserved",
                    })
                model["slope_profiles"].append(profile)
        except Exception as exc:
            model["error"]={"type":type(exc).__name__,
                            "message":str(exc)[:500]}
            row["source_error"]=model["error"]
        row["model_profiles"].append(model)
    if all(m["fit_status"]=="ok" for m in row["model_profiles"]):
        row["source_status"]="ok"
        row["source_error"]=None
    else:
        row["source_status"]="failed"
    return row


def summarize(rows):
    expected={(b,n,s,t,o)
              for b in range(BLOCKS) for n in SIZES
              for s in SUPPORT for t in STATES for o in OBSERVATION}
    ids=[(r["primitive_block"],r["participants"],r["support"],
          r["true_random_slope_state"],r["observation_process"]) for r in rows]
    if len(ids)!=len(set(ids)) or not set(ids).issubset(expected):
        raise ValueError("R43 source keys duplicated or outside planned design")
    models=[m for r in rows for m in r["model_profiles"]]
    profiles=[p for m in models for p in m["slope_profiles"]]
    stages=[f for p in profiles for f in p["stage_fits"]]
    if any(len(p["stage_fits"])!=len(STAGES) or
           tuple(f["algorithm"] for f in p["stage_fits"])!=STAGES
           for p in profiles):
        raise ValueError("R43 stage order or refused-stage contract violated")
    bymethod={}
    for name in STAGES:
        arr=[f for f in stages if f["algorithm"]==name]
        successful=[f for f in arr
                    if f["status"]=="ok"
                    and "original_unshifted_NLL" in f
                    and "physical_KKT_absmax" in f]
        bymethod[name]={
            "planned_stages":PLANNED_FIT_CELLS,
            "recorded_stages":len(arr),
            "converged_stages":len(successful),
            "failed_nonconverged_or_not_attempted":len(arr)-len(successful),
            "passes_physical_KKT":sum(
                x["physical_KKT_absmax"]<=KKT_TOL for x in successful),
            "fails_physical_KKT":sum(
                x["physical_KKT_absmax"]>KKT_TOL for x in successful),
            "maximum_physical_KKT":max(
                (x["physical_KKT_absmax"] for x in successful),default=None),
        }
    for p in profiles:
        ok=[x for x in p["stage_fits"] if x["status"]=="ok"
            and "original_unshifted_NLL" in x]
        if ok:
            best=min(x["original_unshifted_NLL"] for x in ok)
            for x in ok:
                x["near_best_within_stage_pair"]=bool(
                    x["original_unshifted_NLL"]-best<=NLL_TOL)
    for name in STAGES:
        arr=[f for f in stages if f["algorithm"]==name and f["status"]=="ok"]
        bymethod[name]["near_best_within_pair"] = sum(
            x.get("near_best_within_stage_pair") is True for x in arr)
        bymethod[name]["inferior_to_other_stage_NLL"] = sum(
            x.get("near_best_within_stage_pair") is False for x in arr)
    design_complete=(
        len(rows)==PLANNED_SOURCE_CASES and
        len(models)==PLANNED_SOURCE_CASES*len(WORKING) and
        len(profiles)==PLANNED_FIT_CELLS and
        len(stages)==PLANNED_STAGE_RECORDS
    )
    results={}
    for model_type in WORKING:
        for obs in OBSERVATION:
            subset=[f for r in rows if r["observation_process"]==obs
                    for m in r["model_profiles"] if m["working_family"]==model_type
                    for p in m["slope_profiles"] for f in p["stage_fits"]]
            for stage in STAGES:
                fits=[f for f in subset if f["algorithm"]==stage]
                key=model_type+"/"+obs+"/"+stage
                results[key]={
                    "expected":BLOCKS*len(SIZES)*len(SUPPORT)*len(STATES)*len(SLOPE_RATIOS),
                    "recorded":len(fits),
                    "success":sum(f["status"]=="ok" for f in fits),
                    "KKT_pass":sum(
                        f["status"]=="ok" and
                        f.get("physical_KKT_absmax",float("inf"))<=KKT_TOL
                        for f in fits),
                    "near_best":sum(
                        f["status"]=="ok" and
                        f.get("near_best_within_stage_pair") is True
                        for f in fits),
                }
    gates={
        name:bool(design_complete
                  and all(r["source_status"]=="ok" for r in rows)
                  and bymethod[name]["failed_nonconverged_or_not_attempted"]==0
                  and bymethod[name]["fails_physical_KKT"]==0
                  and bymethod[name]["inferior_to_other_stage_NLL"]==0)
        for name in STAGES
    }
    return {
        "study":STUDY,"new_master_seed":MASTER_SEED,
        "new_independent_primitive_blocks":BLOCKS,
        "nested_participant_sizes":SIZES,
        "covariance_generator_family":"predictor_scaled_slope",
        "matched_and_misspecified_working_targets":WORKING,
        "observation_processes":OBSERVATION,
        "anchored_dropout_is_not_MAR_or_MNAR":True,
        "interior_retention_probability":MCAR_INTERIOR_KEEP_PROBABILITY,
        "planned_source_cases":PLANNED_SOURCE_CASES,
        "recorded_source_cases":len(rows),
        "source_failures":sum(r["source_status"]!="ok" for r in rows),
        "missing_source_cases":len(expected-set(ids)),
        "planned_method_profile_pairs":PLANNED_FIT_CELLS,
        "recorded_method_profile_pairs":len(profiles),
        "planned_optimizer_stage_records":PLANNED_STAGE_RECORDS,
        "recorded_optimizer_stage_records":len(stages),
        "full_design_recorded":bool(design_complete),
        "KKT_threshold":KKT_TOL,"NLL_threshold":NLL_TOL,
        "stages":bymethod,"stratified_diagnostics":results,
        "numerical_only_gates":gates,
        "no_global_certified_estimator":True,
        "no_null_calibration_typeI_or_power":True,
        "no_fitted_covariance_CR2_or_simultaneous_band_inference":True,
        "no_response_dependent_loss_sensitivity":True,
        "release_authorized":False,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    cases=[
        source_evaluation(b,n,s,t,o)
        for b in range(BLOCKS) for n in SIZES for s in SUPPORT
        for t in STATES for o in OBSERVATION
    ]
    summary=summarize(cases)
    for filename,obj in (("cases.json",cases),("summary.json",summary)):
        (args.out/filename).write_text(
            json.dumps(obj,sort_keys=True,indent=2,allow_nan=False)+"\n")
    (args.out/"source-commit.txt").write_text(
        os.environ.get("GITHUB_SHA","unverified-local")+"\n")
    files=("cases.json","summary.json","source-commit.txt")
    (args.out/"SHA256SUMS").write_text("".join(
        hashlib.sha256((args.out/f).read_bytes()).hexdigest()+"  "+f+"\n"
        for f in files))
    print("R43 FRESH STRESS NUMERIC AUDIT",json.dumps(summary,sort_keys=True))
    if (not summary["full_design_recorded"]
            or summary["source_failures"] or summary["missing_source_cases"]):
        raise SystemExit("R43 source/stage integrity refusal; retain case ledger")


if __name__=="__main__":
    main()
