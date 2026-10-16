"""R44: response-dependent gaze loss versus whole-participant selection.

Research-only prospective Gaussian source experiment. Four NEW independent
primitive blocks; nested n24/n48; paired support and generating random-slope
states. Compare complete, predictor/time-dependent MAR-like point retention,
missing-value-dependent MNAR point retention, and latent-response-dependent
whole-participant selection. Retain original full-cohort denominators and
contrast full-vs-retained mean-model estimands descriptively. Numerical REML
KKT qualification is separate from selection/coverage validation.
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
from scripts.w3_r20_estimated_working_target import observed_weighted_rows
from scripts.w3_r25_gaussian_reml_components import prepare_reml_design

STUDY="W3_R44_INDEPENDENT_RESPONSE_DEPENDENT_SELECTION_ORACLE"
MASTER_SEED=202610164444
OBSERVATION_SEED=202610164445
BLOCKS=4
SIZES=(24,48)
MAX_N=48
SUPPORT=("ordinary_dependent","extreme_dependent")
STATES=("zero_slope","positive_slope")
PROCESSES=(
    "complete",
    "predictor_time_conditioned_MAR_point",
    "unobserved_outcome_dependent_MNAR_point",
    "latent_outcome_dependent_participant_selection",
)
SLOPE_RATIOS=(0.,.75)
INITIALIZER="intercept_near_lower"
START_RATIOS=(r39.LOW*1.01,.5,1.)
STAGES=("original_R40_raw_linear","stricter_LBFGSB_restart")
MIN_POINTS_PER_RETAINED_TRIAL=4
KKT_TOL=1e-3
NLL_TOL=1e-3
N_SOURCE_CELLS=BLOCKS*len(SIZES)*len(SUPPORT)*len(STATES)*len(PROCESSES)
N_PROFILE_CELLS=N_SOURCE_CELLS*len(SLOPE_RATIOS)
N_STAGES=N_PROFILE_CELLS*len(STAGES)
FOCAL_TIME=float(r16.TIME[r16.FOCAL])


def gaussian_source(block,n,support,state):
    if (type(block) is not int or not 0<=block<BLOCKS or n not in SIZES
            or support not in SUPPORT or state not in STATES):
        raise ValueError("R44 generating source outside frozen factorial")
    original=fresh.fresh_source(
        block,support,n=n,master_seed=MASTER_SEED,
        n_blocks=BLOCKS,max_n=MAX_N
    )
    if state=="positive_slope":
        return original
    raw=dict(original[0])
    raw["participant_slope"]=np.zeros_like(raw["participant_slope"])
    return counterfactual.rescaled_source((raw,*original[1:]),1.)


def _uniforms(block,support,who,trial_id,n):
    """Participant/trial-indexed uniforms; unchanged for nested source prefixes.

    Separate generator stream for point and participant exclusion. This
    coupling is across outcome states too; *probabilities* may differ
    because outcome-dependent retention really depends on observed y.
    """
    code=(OBSERVATION_SEED+100003*block+7919*int(who)
          +151*int(trial_id)
          +3*(support=="extreme_dependent"))
    return np.random.default_rng(code).random(n)


def _point_retention(time,y,x,block,support,who,trial,mechanism):
    if mechanism not in PROCESSES[1:3]:
        raise ValueError("unknown point-loss mechanism")
    k=len(time)
    if k<MIN_POINTS_PER_RETAINED_TRIAL:
        raise ValueError("trial not long enough to preserve R44 source")
    if mechanism=="predictor_time_conditioned_MAR_point":
        # Native time and predictor observed even when a gaze y is missing.
        prob=.76-.12*(abs(float(x))/(1.+abs(float(x))))-.12*np.asarray(time)
    else:
        # MNAR with respect to analysis dataset: missing y itself drives R.
        # No generator truth or other hidden simulation innovation is used.
        prob=.70-.25*np.tanh(np.asarray(y,float))
    if not (np.isfinite(prob).all() and ((prob>0)&(prob<1)).all()):
        raise ValueError("R44 prespecified probability outside (0,1)")
    u=_uniforms(block,support,who,trial,k)
    mask=u<prob
    mask[0]=mask[-1]=True
    if mask.sum()<MIN_POINTS_PER_RETAINED_TRIAL:
        candidates=np.flatnonzero(~mask)
        mask[candidates[:MIN_POINTS_PER_RETAINED_TRIAL-int(mask.sum())]]=True
    return np.flatnonzero(mask), np.asarray(prob,float)


def _participant_keep_probability(full_native_values):
    mean_value=float(np.mean(np.concatenate(full_native_values)))
    # This selects on the full latent participant outcome, including the
    # potential trajectories of excluded participants (unobserved in fit).
    return float(.60-.30*np.tanh(mean_value))


def apply_observation_process(case,block,support,mechanism):
    if mechanism not in PROCESSES:
        raise ValueError("unregistered R44 observation process")
    _,gaze,x,participant,trials,oracle_mean=case
    participant=np.asarray(participant,int)
    trials=np.asarray(trials,int)
    x=np.asarray(x,float)
    cohort=np.unique(participant)
    keep_participant={int(who):True for who in cohort}
    selection_probability={}
    if mechanism=="latent_outcome_dependent_participant_selection":
        for who in cohort:
            idx=np.flatnonzero(participant==who)
            values=[np.asarray(gaze.values[j],float)[:,0] for j in idx]
            p=_participant_keep_probability(values)
            # One frozen independent selection uniform for each participant;
            # no replacement draws if a selected cohort is too small.
            u=_uniforms(block,support,who,0,1)[0]
            selection_probability[int(who)]=p
            keep_participant[int(who)]=bool(u<p)
    else:
        selection_probability={int(who):1. for who in cohort}

    tids=[];vls=[];ids=[];metadata_rows=[];newx=[];newpeople=[];newtrials=[]
    total_native=0;observed_native=0; retained_trials=0
    retention_probabilities=[]
    for j,(times,values) in enumerate(zip(gaze.time,gaze.values)):
        who=int(participant[j])
        t=np.asarray(times,float)
        v=np.asarray(values,float)
        total_native+=len(t)
        if not keep_participant[who]:
            continue
        if mechanism in PROCESSES[1:3]:
            positions,prob=_point_retention(
                t,v[:,0],x[j],block,support,who,int(trials[j]),mechanism
            )
            retention_probabilities.extend(prob.tolist())
        else:
            positions=np.arange(len(t))
        if len(positions)<MIN_POINTS_PER_RETAINED_TRIAL:
            raise ValueError("R44 returned less than four true native timestamps")
        tids.append(t[positions])
        vls.append(v[positions])
        ids.append(gaze.curve_ids[j])
        metadata_rows.append(j)
        newx.append(x[j])
        newpeople.append(who)
        newtrials.append(int(trials[j]))
        observed_native+=len(positions)
        retained_trials+=1
    nretained=len({int(a) for a in newpeople})
    if nretained<6:
        raise ValueError("R44 retained fewer than six independent participants")
    newgaze=r16.IrregularTrajectorySet(
        time=tuple(tids),values=tuple(vls),curve_ids=tuple(ids),
        dimension_names=gaze.dimension_names,time_unit=gaze.time_unit,
        coordinate_system=gaze.coordinate_system,
        metadata=gaze.metadata.iloc[metadata_rows].reset_index(drop=True),
        provenance={
            **gaze.provenance,
            "research_study":STUDY,
            "observation_process":mechanism,
            "full_primitive_block":int(block),
            "complete_cohort_count":int(len(cohort)),
            "retained_participant_count":nretained,
            "latent_outcome_dependent":
                mechanism in PROCESSES[2:],
            "participant_selection_uses_full_latent_outcome":
                mechanism==PROCESSES[3],
            "native_points_only":True,
            "interpolation_performed":False,
        },
    )
    return (
        (None,newgaze,np.asarray(newx,float),np.asarray(newpeople,int),
         np.asarray(newtrials,int),None),
        {
            "original_participants":int(len(cohort)),
            "retained_participants":nretained,
            "excluded_participants":int(len(cohort)-nretained),
            "original_native_trials":len(gaze.time),
            "retained_native_trials":retained_trials,
            "original_native_timepoints":int(total_native),
            "retained_native_timepoints":int(observed_native),
            "point_retention_fraction":float(observed_native/total_native),
            "participant_retention_fraction":float(nretained/len(cohort)),
            "selection_probability_min":float(
                min(selection_probability.values())),
            "selection_probability_max":float(
                max(selection_probability.values())),
            "point_probability_mean":(
                float(np.mean(retention_probabilities))
                if retention_probabilities else None),
            "response_dependent_loss":
                mechanism in PROCESSES[2:],
            "true_population_full_cohort_is_preserved_as_reference":True,
        }
    )


def observed_mean_slope_contrast(case):
    """Descriptive observed weighted-regression slope at prespecified focal t.

    Not a fitted-covariance CR2 estimator and not a confidence interval.
    """
    X,y,w,person,t,tr,x=observed_weighted_rows(case,"legendre5")
    Z=X*np.sqrt(w)[:,None]
    beta=np.linalg.lstsq(Z,y*np.sqrt(w),rcond=None)[0]
    B=r16.basis(np.asarray([FOCAL_TIME]),"legendre5")
    p=B.shape[1]
    c=np.r_[np.zeros(p),B[0]]
    return float(c@beta)


def prepare_case(case):
    X,y,w,person,t,tr,x=observed_weighted_rows(case,"legendre5")
    prepared=prepare_reml_design(
        X,y,w,person,t,tr,x,slope="predictor_scaled_slope")
    Z=X*np.sqrt(w)[:,None]
    beta=np.linalg.lstsq(Z,y*np.sqrt(w),rcond=None)[0]
    ref=max(float(np.mean((y-X@beta)**2)),1e-8)
    if not (np.isfinite(ref) and ref>0):
        raise ValueError("invalid observed-only REML reference")
    return prepared,ref


def _run_stage(prepared,reference,slope):
    records=[]
    try:
        raw=r39.fit_one(
            prepared,reference,slope,np.log(np.asarray(START_RATIOS,float)),
            INITIALIZER,"linear_variance_ratios","raw_NLL",0.
        )
        if raw["status"]=="ok":
            records.append({
                "algorithm":STAGES[0],"status":"ok",
                "raw_original_NLL":float(raw["gaussian_restricted_NLL"]),
                "physical_KKT_absmax":
                    float(raw["shared_ratio_projected_KKT_absmax"]),
                "retained_nuisance_ratios":raw["nuisance_variance_ratios"],
                "optimizer_message":raw.get("optimizer_message"),
            })
            follow=r41.restart(raw,prepared,reference,slope,STAGES[1])
            if follow["status"]=="ok" and follow.get("fit"):
                fit=follow["fit"]
                records.append({
                    "algorithm":STAGES[1],"status":"ok",
                    "raw_original_NLL":float(fit["original_unshifted_NLL"]),
                    "physical_KKT_absmax":
                        float(fit["physical_ratio_projected_KKT_absmax"]),
                    "retained_nuisance_ratios":fit["nuisance_variance_ratios"],
                    "optimizer_message":follow.get("message"),
                })
            else:
                records.append({
                    "algorithm":STAGES[1],"status":follow["status"],
                    "error":follow.get("error"),
                    "optimizer_message":follow.get("message"),
                })
        else:
            records.append({
                "algorithm":STAGES[0],"status":raw["status"],
                "error":raw.get("error"),"optimizer_message":
                    raw.get("optimizer_message")
            })
            records.append({
                "algorithm":STAGES[1],"status":"not_attempted",
                "error":"original_baseline_refused",
            })
    except Exception as exc:
        records=[
            {"algorithm":STAGES[0],"status":"failed",
             "error":{"type":type(exc).__name__,
                      "message":str(exc)[:600]}},
            {"algorithm":STAGES[1],"status":"not_attempted",
             "error":"original_baseline_exception"},
        ]
    successes=[f for f in records if f["status"]=="ok"]
    if successes:
        best=min(f["raw_original_NLL"] for f in successes)
        for f in successes:
            f["near_best_within_same_profile_pair"]=bool(
                f["raw_original_NLL"]-best<=NLL_TOL)
            f["passes_frozen_KKT"]=bool(
                f["physical_KKT_absmax"]<=KKT_TOL)
    return records


def evaluate(block,n,support,state):
    """One primitive block/size/support/state, all four observation processes."""
    original=gaussian_source(block,n,support,state)
    row={
        "block":block,"participants_full_cohort":n,"support":support,
        "true_random_slope_state":state,
        "new_source_seed":MASTER_SEED,
        "independent_primitive_block_not_each_condition":True,
        "full_cohort_population_estimand":
            "generating_predictor_slope_at_fixed_focal_time",
        "full_cohort_source_full_cohort_slope_estimate":None,
        "generating_true_focal_slope":float(
            r16.truth_coefficients(np.asarray([FOCAL_TIME]))[1][0,0]),
        "source_status":"failed","source_error":None,
        "observation_processes":[],
        "no_null_test_or_CR2_coverage_qualification":True,
        "release_authorized":False,
    }
    try:
        full_slope=observed_mean_slope_contrast(
            (None,original[1],original[2],original[3],original[4],None)
        )
        row["full_cohort_source_full_cohort_slope_estimate"]=full_slope
    except Exception as exc:
        row["source_error"]={"type":type(exc).__name__,
                             "message":str(exc)[:500]}
        return row
    for process in PROCESSES:
        a={
            "observation_process":process,"status":"failed",
            "error":None,"retention":None,
            "observed_focal_slope_estimate":None,
            "observed_minus_full_cohort_focal_slope":None,
            "observed_minus_generating_true_focal_slope":None,
            "profiles":[],
            "original_full_cohort_retained_in_ledger":True,
            "not_CR2_or_coverage":True,
        }
        try:
            observed,stats=apply_observation_process(
                original,block,support,process
            )
            a["retention"]=stats
            a["observed_focal_slope_estimate"]=(
                observed_mean_slope_contrast(observed)
            )
            a["observed_minus_full_cohort_focal_slope"]=float(
                a["observed_focal_slope_estimate"]-full_slope
            )
            a["observed_minus_generating_true_focal_slope"]=float(
                a["observed_focal_slope_estimate"]
                -row["generating_true_focal_slope"]
            )
            prep,ref=prepare_case(observed)
            a["status"]="ok"
            for slope in SLOPE_RATIOS:
                a["profiles"].append({
                    "fixed_random_slope_variance_ratio":float(slope),
                    "stage_fits":_run_stage(prep,ref,slope),
                })
        except Exception as exc:
            a["error"]={"type":type(exc).__name__,
                        "message":str(exc)[:500]}
        row["observation_processes"].append(a)
    if len(row["observation_processes"])==len(PROCESSES) and all(
        a["status"]=="ok" for a in row["observation_processes"]
    ):
        row["source_status"]="ok"
    else:
        row["source_error"]="an observation mechanism failed; explicit refusal"
    return row


def summarize(rows):
    expected={(b,n,s,t) for b in range(BLOCKS) for n in SIZES
              for s in SUPPORT for t in STATES}
    ids=[(r["block"],r["participants_full_cohort"],r["support"],
          r["true_random_slope_state"]) for r in rows]
    if len(set(ids))!=len(ids) or not set(ids).issubset(expected):
        raise ValueError("R44 duplicated or unregistered primitive source condition")
    mechanisms=[a for r in rows for a in r["observation_processes"]]
    profiles=[p for a in mechanisms for p in a["profiles"]]
    fits=[f for p in profiles for f in p["stage_fits"]]
    if any(len(p["stage_fits"])!=len(STAGES)
           or tuple(f["algorithm"] for f in p["stage_fits"])!=STAGES
           for p in profiles):
        raise ValueError("R44 stage identity mismatch")
    cells={}
    for proc in PROCESSES:
        cases=[a for a in mechanisms if a["observation_process"]==proc]
        subset=[f for a in cases for p in a["profiles"] for f in p["stage_fits"]]
        retention=[
            a["retention"] for a in cases if a.get("retention") is not None
        ]
        shift=[a["observed_minus_full_cohort_focal_slope"]
               for a in cases if a["status"]=="ok"]
        bystage={}
        for stage in STAGES:
            matching=[f for f in subset if f["algorithm"]==stage]
            successes=[f for f in matching if f["status"]=="ok"]
            bystage[stage]={
                "expected":BLOCKS*len(SIZES)*len(SUPPORT)*len(STATES)
                           *len(SLOPE_RATIOS),
                "recorded":len(matching),
                "successful":len(successes),
                "failed_refused_nonconverged":
                    len(matching)-len(successes),
                "near_best_nll":sum(
                    f["near_best_within_same_profile_pair"]
                    for f in successes),
                "physical_KKT_pass":sum(
                    f["passes_frozen_KKT"] for f in successes),
                "physical_KKT_fail":sum(
                    not f["passes_frozen_KKT"] for f in successes),
                "max_physical_KKT":max(
                    (f["physical_KKT_absmax"] for f in successes),
                    default=None),
            }
        cells[proc]={
            "planned_paired_condition_rows":
                BLOCKS*len(SIZES)*len(SUPPORT)*len(STATES),
            "recorded_paired_condition_rows":len(cases),
            "mean_point_retention_fraction":(
                float(np.mean([r["point_retention_fraction"]
                               for r in retention]))
                if retention else None),
            "mean_participant_retention_fraction":(
                float(np.mean([r["participant_retention_fraction"]
                               for r in retention]))
                if retention else None),
            "mean_observed_minus_full_cohort_focal_slope":(
                float(np.mean(shift)) if shift else None),
            "mean_absolute_observed_vs_full_cohort_slope_shift":(
                float(np.mean(np.abs(shift))) if shift else None),
            "mean_observed_focal_slope_error_is_descriptive_not_inference":True,
            "stage_diagnostics":bystage,
        }
    complete=(
        len(rows)==len(expected)
        and len(mechanisms)==N_SOURCE_CELLS
        and len(profiles)==N_PROFILE_CELLS
        and len(fits)==N_STAGES
        and all(r["source_status"]=="ok" for r in rows)
    )
    numerical_gates={
        stage:bool(complete and all(
            cells[proc]["stage_diagnostics"][stage]["successful"]==
            cells[proc]["stage_diagnostics"][stage]["expected"]
            and cells[proc]["stage_diagnostics"][stage]["near_best_nll"]==
            cells[proc]["stage_diagnostics"][stage]["expected"]
            and cells[proc]["stage_diagnostics"][stage]["physical_KKT_pass"]==
            cells[proc]["stage_diagnostics"][stage]["expected"]
            for proc in PROCESSES))
        for stage in STAGES
    }
    return {
        "study":STUDY,"new_master_seed":MASTER_SEED,
        "new_independent_primitive_blocks":BLOCKS,
        "nested_participant_sizes":SIZES,
        "full_cohort_is_reference_even_when_entire_participant_excluded":True,
        "MAR_like_predictor_time_probability_is_observed_data_based":True,
        "MNAR_point_probability_depends_on_potentially_missing_response":True,
        "unit_selection_depends_on_full_latent_response":True,
        "observation_processes":PROCESSES,
        "planned_source_variant_rows":BLOCKS*len(SIZES)*len(SUPPORT)*len(STATES),
        "recorded_source_variant_rows":len(rows),
        "planned_observation_process_rows":N_SOURCE_CELLS,
        "recorded_observation_process_rows":len(mechanisms),
        "planned_fixed_profile_rows":N_PROFILE_CELLS,
        "recorded_fixed_profile_rows":len(profiles),
        "planned_optimizer_stage_records":N_STAGES,
        "recorded_optimizer_stage_records":len(fits),
        "source_or_observation_process_errors":sum(
            r["source_status"]!="ok" for r in rows),
        "complete_original_design_including_failures":complete,
        "prespecified_frozen_physical_KKT_tolerance":KKT_TOL,
        "prespecified_within_pair_NLL_tolerance":NLL_TOL,
        "mechanism_cells":cells,
        "preliminary_numerical_only_gates":numerical_gates,
        "descriptive_selection_differences_not_causal_or_coverage_claims":True,
        "no_validity_claim_for_MNAR_or_selected_CR2_inference":True,
        "no_variance_component_boundary_typeI_or_power_calibration":True,
        "no_90pct_pointwise_or_simultaneous_band_qualification":True,
        "release_authorized":False,
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    rows=[evaluate(b,n,s,t)
          for b in range(BLOCKS) for n in SIZES
          for s in SUPPORT for t in STATES]
    report=summarize(rows)
    for name,obj in (("cases.json",rows),("summary.json",report)):
        (args.out/name).write_text(
            json.dumps(obj,sort_keys=True,indent=2,allow_nan=False)+"\n")
    (args.out/"source-commit.txt").write_text(
        os.environ.get("GITHUB_SHA","unverified-local")+"\n")
    files=("cases.json","summary.json","source-commit.txt")
    (args.out/"SHA256SUMS").write_text("".join(
        hashlib.sha256((args.out/f).read_bytes()).hexdigest()+"  "+f+"\n"
        for f in files))
    print("R44 RESPONSE DEPENDENT SOURCE SELECTION AUDIT",json.dumps(
        report,sort_keys=True))
    if not report["complete_original_design_including_failures"]:
        raise SystemExit("R44 source or stage integrity refusal; case ledger retained")


if __name__=="__main__":
    main()
