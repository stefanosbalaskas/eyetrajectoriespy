"""W3 R55: prospective multi-amplitude Gaussian REML active-face SWITCH profile.

Research-only diagnostic, reusing EXACT R53/R54 independent Gaussian primitive
source blocks; these are NOT new independent simulations or coverage trials.
The original positive ratio box, observed reference scaling, two-start strict
Gaussian REML/KKT/NLL solver and R22 CR2 remain UNMODIFIED.

Along two frozen Gaussian response directions per original block/support,
observe signed refits on a FIXED grid of weighted-response RMS perturbations:
.0005, .005, .05, .25. Retain every +/- fit, both optimizer starts,
Gaussian covariance face, fit refusal, studentized CR2 change and original
stable-face local prediction. Switching is the observed change in the
optimizer's selected POSITIVE ratio-box active face; a selected initialization
change by itself is NOT a proof of local root switching.

These are finite deterministic stress paths, not distributional sampling
probabilities, true zero variance boundary tests, calibrated 90% CIs or a
supported API. Never tune the grid after results or condition on successes.
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
from scripts import run_w3_r49_nuisance_refit_bootstrap_t as r49
from scripts import run_w3_r53_local_reml_influence as r53
from scripts import run_w3_r54_boundary_active_set_influence as r54
from scripts.w3_r20_estimated_working_target import COMPONENTS

STUDY="W3_R55_FIXED_DIRECTION_GAUSSIAN_REML_ACTIVE_FACE_SWITCH_PROFILE"
REUSED_SOURCE_SEED=r53.SOURCE_SEED
DIRECTION_SEED=202610175555
PARTICIPANTS=r53.PARTICIPANTS
BLOCKS=r53.BLOCKS
SUPPORT=r53.SUPPORT
DIRECTIONS=2
LEVELS=(0.0005,0.005,0.05,0.25)
SIGNS=(-1,1)
SHARDS=((0,2),(2,4))
N_ORIGINAL=BLOCKS*len(SUPPORT)
N_DIRECTIONS=N_ORIGINAL*DIRECTIONS
N_NODES=N_DIRECTIONS*len(LEVELS)*len(SIGNS)
N_FITS=N_ORIGINAL+N_NODES
N_STARTS=N_FITS*len(r49.START_RATIOS)


def data_for(block,support):
    if type(block) is not int or block not in range(BLOCKS) or support not in SUPPORT:
        raise ValueError("R55 unregistered original R53 Gaussian source")
    return r53.problem(block,support)


def _plain(x):
    return r53._json_plain(x)


def selected_fit(fit):
    """Full original two-start outcome ledger without large covariance blocks."""
    return {k:_plain(v) for k,v in fit.items() if k!="working_blocks"}


def node_template(level,sign):
    return {
        "level":level,"sign":sign,"status":"not_attempted",
        "reason":None,"weighted_response_step":None,
        "fit":None,"active_low":None,"active_high":None,
        "face_changed_from_original":None,
        "selected_start_changed_from_original":None,
        "fitted_component_ratios":None,
        "observed_focal_CR2_point":None,
        "observed_focal_CR2_se":None,
        "observed_studentized_truth_pivot":None,
        "predicted_active_face_pivot":None,
        "absolute_local_pivot_prediction_discrepancy":None,
        "theta_component_predicted":None,
        "theta_component_observed":None,
        "theta_relative_local_prediction_discrepancy":None,
    }


def direction_vector(block,support,direction,n):
    if direction not in range(DIRECTIONS) or n<=0:
        raise ValueError("R55 direction outside frozen universe")
    seed=DIRECTION_SEED+100003*block+711*SUPPORT.index(support)+direction
    rng=np.random.default_rng(seed)
    d=rng.standard_normal(n)
    d/=np.linalg.norm(d)/np.sqrt(n)
    if not np.isfinite(d).all():
        raise ValueError("R55 nonfinite Gaussian response direction")
    return d,int(seed)


def profile_transition(nodes,sign):
    """Report *observed discrete grid bracket*, not true switch threshold."""
    selected=[n for n in nodes if n["sign"]==sign]
    if [n["level"] for n in selected]!=list(LEVELS):
        raise ValueError("R55 incomplete fixed-level ordered sign path")
    previous=0.
    for n in selected:
        if n["status"]!="ok":
            return {
                "status":"unresolved_after_fit_or_CR2_refusal",
                "first_refused_level":n["level"],
                "previous_no_switch_level":previous,
            }
        if n["face_changed_from_original"]:
            return {
                "status":"first_observed_active_face_change_bracket",
                "previous_no_switch_level":previous,
                "first_changed_level":n["level"],
                "true_crossing_time_identified":False,
            }
        previous=n["level"]
    return {
        "status":"no_changed_face_on_frozen_grid",
        "max_checked_level":LEVELS[-1],
        "switch_absence_between_grid_nodes_not_proven":True,
    }


def evaluate(block,support):
    row={
        "study":STUDY,"block":block,"support":support,
        "R53_R54_original_source_reused_not_new_independent":True,
        "source_status":"failed","source_error":None,
        "original_fit":None,"original_signature":None,
        "local_face_status":"not_attempted",
        "local_face_reason":None,"directions":[],
        "released_as_supported_inference":False,
    }
    data=None
    try:
        data=data_for(block,support)
        row["source_status"]="ok"
        row["projected_generating_focal_truth"]=float(data["truth"])
        row["native_observation_count"]=int(len(data["y"]))
    except Exception as exc:
        row["source_error"]=repr(exc)[:380]
    if data is None:
        fit={"status":"not_attempted","numerical_starts":[
            {"label":label,"status":"not_attempted"}
            for label,_ in r49.START_RATIOS]}
        local={"status":"refused","reason":"source_unavailable"}
        baseline_face=None
    else:
        fit=r49.fit_nuisance(data)
        row["original_fit"]=selected_fit(fit)
        baseline_face=r54.active_signature(fit)
        local=r54.local_active_face(data,fit)
    if row["original_fit"] is None:
        row["original_fit"]=selected_fit(fit)
    row["original_signature"]=_plain(baseline_face)
    row["local_face_status"]=local["status"]
    row["local_face_reason"]=local.get("reason")
    for direction in range(DIRECTIONS):
        path={
            "direction":direction,"seed":None,
            "weighted_original_response_RMS":None,
            "nodes":[],"transition_by_sign":{},
        }
        if data is not None:
            d,seed=direction_vector(block,support,direction,len(data["y"]))
            path["seed"]=seed
            rms=float(np.sqrt(np.mean((data["y"]*np.sqrt(data["w"]))**2)))
            path["weighted_original_response_RMS"]=rms
        for level in LEVELS:
            for sign in SIGNS:
                node=node_template(level,sign)
                if data is None:
                    node["reason"]="original_source_unavailable"
                elif fit["status"]!="accepted":
                    node["reason"]="original_REML_numerical_refusal"
                else:
                    step=level*max(rms,.01)
                    node["weighted_response_step"]=float(step)
                    try:
                        perturbed={**data,"y":data["y"]+
                            sign*step*d/np.sqrt(data["w"])}
                        fitted=r49.fit_nuisance(perturbed)
                        node["fit"]=selected_fit(fitted)
                        if fitted["status"]!="accepted":
                            node["status"]="refused"
                            node["reason"]="perturbed_full_REML_numerical_refusal"
                        else:
                            face=r54.active_signature(fitted)
                            node["active_low"]=_plain(face[0])
                            node["active_high"]=_plain(face[1])
                            node["face_changed_from_original"]=bool(face!=baseline_face)
                            node["selected_start_changed_from_original"]=bool(
                                fitted["selected_start"]!=fit["selected_start"])
                            reference=float(fitted["reference_variance"])
                            ratios=np.array([
                                fitted["components"][k]/reference
                                for k in COMPONENTS],float)
                            node["fitted_component_ratios"]=ratios.tolist()
                            result=r49.cr2_on(perturbed,fitted["working_blocks"])
                            node["observed_focal_CR2_point"]=float(result["point"])
                            node["observed_focal_CR2_se"]=float(result["cr2_se"])
                            pivot=float(
                                (result["point"]-data["truth"])/result["cr2_se"])
                            if not np.isfinite(pivot):
                                raise ValueError("R55 nonfinite CR2 truth-centered pivot")
                            node["observed_studentized_truth_pivot"]=pivot
                            if local["status"]=="ok":
                                theta=np.array(local["theta"],float)
                                delta=sign*step*(local["theta_response_jacobian"]@d)
                                tpred=float(local["original_studentized_pivot"]+
                                    sign*step*(
                                      local["CR2_pivot_total_response_gradient"]@d))
                                actual=np.array([
                                    fitted["components"][k] for k in COMPONENTS],float)
                                predicted=theta+delta
                                node["predicted_active_face_pivot"]=tpred
                                node["absolute_local_pivot_prediction_discrepancy"]=float(
                                    abs(tpred-pivot))
                                node["theta_component_predicted"]=predicted.tolist()
                                node["theta_component_observed"]=actual.tolist()
                                node["theta_relative_local_prediction_discrepancy"]=float(
                                    np.linalg.norm(predicted-actual)/
                                    max(np.linalg.norm(theta),
                                        np.linalg.norm(actual),1e-12))
                            node["status"]="ok"
                    except Exception as exc:
                        node["status"]="refused"
                        node["reason"]=repr(exc)[:390]
                path["nodes"].append(node)
        path["transition_by_sign"]={
            str(s):profile_transition(path["nodes"],s) for s in SIGNS
        }
        row["directions"].append(path)
    return row


def summary(rows):
    universe={(b,s) for b in range(BLOCKS) for s in SUPPORT}
    ids=[(r["block"],r["support"]) for r in rows]
    if len(ids)!=len(set(ids)) or not set(ids).issubset(universe):
        raise ValueError("R55 source duplicated or unregistered")
    all_nodes=[]
    executed=0
    for row in rows:
        if len(row["directions"])!=DIRECTIONS:
            raise ValueError("R55 missing frozen direction slot")
        if len(row["original_fit"]["numerical_starts"])!=2:
            raise ValueError("R55 missing two-start original numerical evidence")
        for direction,path in enumerate(row["directions"]):
            if path["direction"]!=direction or len(path["nodes"])!=len(LEVELS)*2:
                raise ValueError("R55 missing frozen signed amplitude grid")
            expected=[(level,sign) for level in LEVELS for sign in SIGNS]
            if [(n["level"],n["sign"]) for n in path["nodes"]]!=expected:
                raise ValueError("R55 source grid out of order")
            if set(path["transition_by_sign"])!={str(s) for s in SIGNS}:
                raise ValueError("R55 signed path transition ledger missing")
            for n in path["nodes"]:
                fit=n["fit"]
                if fit is not None:
                    executed+=1
                    if len(fit["numerical_starts"])!=2:
                        raise ValueError("R55 missing numerical fit starts")
                all_nodes.append(n)
    results={}
    for support in SUPPORT:
        cases=[r for r in rows if r["support"]==support]
        nodes=[x for r in cases for d in r["directions"] for x in d["nodes"]]
        by_level={}
        for level in LEVELS:
            group=[n for n in nodes if n["level"]==level]
            ok=[n for n in group if n["status"]=="ok"]
            stable=[n for n in ok if not n["face_changed_from_original"]]
            by_level[str(level)]={
                "planned_signed_fit_slots":len(cases)*DIRECTIONS*len(SIGNS),
                "recorded_signed_fit_slots":len(group),
                "accepted_refits_and_CR2":len(ok),
                "fit_or_CR2_refusals":sum(n["status"]=="refused" for n in group),
                "not_attempted":sum(n["status"]=="not_attempted" for n in group),
                "changed_selected_active_face":sum(n["face_changed_from_original"] is True
                                                      for n in ok),
                "selected_optimizer_start_changed":sum(
                    n["selected_start_changed_from_original"] is True for n in ok),
                "median_abs_local_pivot_prediction_error_among_accepted":(
                    float(np.median([
                        n["absolute_local_pivot_prediction_discrepancy"]
                        for n in ok if n["absolute_local_pivot_prediction_discrepancy"]
                        is not None])) if any(
                        n["absolute_local_pivot_prediction_discrepancy"] is not None
                        for n in ok) else None),
                "median_abs_local_pivot_prediction_error_stable_face":(
                    float(np.median([
                        n["absolute_local_pivot_prediction_discrepancy"]
                        for n in stable if n["absolute_local_pivot_prediction_discrepancy"]
                        is not None])) if stable else None),
            }
        paths=[d for c in cases for d in c["directions"]]
        transitions=[d["transition_by_sign"][str(sign)]
                     for d in paths for sign in SIGNS]
        results[support]={
            "matched_original_R53_primitive_blocks":BLOCKS,
            "original_source_cases_recorded":len(cases),
            "original_Gaussian_nuisance_fits_accepted":sum(
                c["original_fit"]["status"]=="accepted" for c in cases),
            "original_strict_stable_face_derivatives_accepted":sum(
                c["local_face_status"]=="ok" for c in cases),
            "first_transition_brackets_observed":sum(
                x["status"]=="first_observed_active_face_change_bracket"
                for x in transitions),
            "paths_with_no_changed_face_on_grid":sum(
                x["status"]=="no_changed_face_on_frozen_grid"
                for x in transitions),
            "paths_unresolved_by_fit_refusal":sum(
                x["status"]=="unresolved_after_fit_or_CR2_refusal"
                for x in transitions),
            "by_amplitude":by_level,
        }
    return {
        "study":STUDY,
        "R53_original_innovation_seed_REUSED":REUSED_SOURCE_SEED,
        "R55_independent_response_direction_seed":DIRECTION_SEED,
        "new_independent_Gaussian_primitive_source_count":0,
        "replayed_independent_original_R53_primitive_blocks":BLOCKS,
        "paired_support_variants_not_independent":True,
        "planned_original_source_cases":N_ORIGINAL,
        "recorded_original_source_cases":len(rows),
        "planned_directions":N_DIRECTIONS,
        "recorded_direction_cases":sum(len(r["directions"]) for r in rows),
        "frozen_signed_amplitude_grid":list(LEVELS),
        "planned_signed_perturbed_fit_slots":N_NODES,
        "recorded_signed_perturbed_fit_slots":len(all_nodes),
        "executed_perturbed_full_REML_fit_attempts":executed,
        "planned_original_plus_perturbed_fit_slots":N_FITS,
        "planned_two_start_optimizer_outcome_slots":N_STARTS,
        "recorded_executed_two_start_optimizer_outcomes":(
            2*len(rows)+2*executed),
        "full_failure_inclusive_structural_source_grid":(
            len(rows)==N_ORIGINAL
            and len(all_nodes)==N_NODES
            and sum(len(r["directions"]) for r in rows)==N_DIRECTIONS),
        "stable_face_local_linear_prediction_not_finite_global_sampling_law":True,
        "grid_brackets_not_exact_crossing_thresholds":True,
        "same_face_at_grid_points_does_not_exclude_intermediate_switch":True,
        "selected_optimizer_start_change_not_proof_of_root_switch":True,
        "positive_ratio_box_not_true_variance_zero":True,
        "no_population_switch_probability_estimated":True,
        "no_validated_90pct_pointwise_or_simultaneous_function_intervals":True,
        "no_variance_boundary_null_typeI_power_calibration":True,
        "no_MNAR_or_whole_participant_selection_identification":True,
        "release_authorized":False,
        "strata":results,
    }


def _write(file,obj):
    file.write_text(json.dumps(
        _plain(obj),sort_keys=True,indent=2,allow_nan=False)+"\n")


def shard(out,start,stop):
    if (start,stop) not in SHARDS:
        raise ValueError("R55 unregistered original source shard")
    out.mkdir(parents=True,exist_ok=True)
    records=[evaluate(block,support) for block in range(start,stop)
             for support in SUPPORT]
    _write(out/"cases.json",records)
    _write(out/"manifest.json",{
        "study":STUDY,"start":start,"stop":stop,
        "source_seed_reused":REUSED_SOURCE_SEED,
        "direction_seed":DIRECTION_SEED,
        "source_checkout":os.environ.get("GITHUB_SHA","unverified-local"),
        "SHA256_cases":hashlib.sha256((out/"cases.json").read_bytes()).hexdigest(),
        "cases":len(records),
    })


def aggregate(out,parts):
    manifests=list(parts.glob("*/manifest.json"))
    if len(manifests)!=len(SHARDS):
        raise ValueError("R55 incomplete original source shards")
    checkout=os.environ.get("GITHUB_SHA","unverified-local")
    found=set()
    cases=[]
    for path in manifests:
        item=json.loads(path.read_text())
        part=(item["start"],item["stop"])
        if (part not in SHARDS or part in found or item["study"]!=STUDY
            or item["source_seed_reused"]!=REUSED_SOURCE_SEED
            or item["direction_seed"]!=DIRECTION_SEED
            or item["source_checkout"]!=checkout):
            raise ValueError("R55 original shard provenance mismatch")
        found.add(part)
        raw=(path.parent/"cases.json").read_bytes()
        if hashlib.sha256(raw).hexdigest()!=item["SHA256_cases"]:
            raise ValueError("R55 original source shard checksum mismatch")
        subset=json.loads(raw)
        expected={(b,s) for b in range(*part) for s in SUPPORT}
        if (len(subset)!=item["cases"] or
            {(r["block"],r["support"]) for r in subset}!=expected):
            raise ValueError("R55 unexpected shard primitive source identities")
        cases.extend(subset)
    if found!=set(SHARDS):
        raise ValueError("R55 missing original independent Gaussian primitive IDs")
    cases.sort(key=lambda x:(x["block"],SUPPORT.index(x["support"])))
    report=summary(cases)
    if not report["full_failure_inclusive_structural_source_grid"]:
        raise ValueError("R55 original source/direction/amplitude slots absent")
    out.mkdir(parents=True,exist_ok=True)
    _write(out/"cases.json",cases)
    _write(out/"summary.json",report)
    (out/"source-commit.txt").write_text(checkout+"\n")
    keys=("cases.json","summary.json","source-commit.txt")
    (out/"SHA256SUMS").write_text("".join(
        hashlib.sha256((out/key).read_bytes()).hexdigest()+"  "+key+"\n"
        for key in keys))
    print("R55 fixed path active face switch audit:",
          json.dumps(report,sort_keys=True))


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument("--start",type=int)
    group.add_argument("--merge-parts",type=Path)
    p.add_argument("--stop",type=int)
    args=p.parse_args()
    if args.merge_parts is not None:
        aggregate(args.out,args.merge_parts)
    elif args.stop is not None:
        shard(args.out,args.start,args.stop)
    else:
        raise SystemExit("R55 requires registered --start and --stop")


if __name__=="__main__":
    main()
