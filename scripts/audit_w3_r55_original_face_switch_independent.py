"""W3 R55: independent immutable R53/R55 ORIGINAL Gaussian source path audit.

Read-only: never import the R55 simulator, R49 REML fit, or original CR2.
Recompute identities, hashes, selected fit numerical contracts, original
R53 source replay, positive box face, source-sign-amplitude transition
brackets, studentized CR2 truth-centered pivots and stratum medians.
No new Gaussian generating-block coverage or valid CI is inferred.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from scripts.audit_w3_r54_original_active_face_independent import (
    COMPONENTS,signature,validate_fit,close,
)

SUPPORT=("ordinary_dependent","extreme_dependent")
LEVELS=(0.0005,0.005,0.05,0.25)
SIGNS=(-1,1)
MASTER=202610175353
DIRECTION=202610175555
R53_SOURCE_CHECKOUT="11689d8562b061ebd5ac98103f5be26fd94b228f"
R55_SOURCE_CHECKOUT="1e0ccce56dd2a70d08fcf1b7fba6ed55627a38f5"
R53_ORIGINAL_CASE_SHA="4bcc5be49d90365b25898fa044e23c9704ea2be6de6a68d591fc4ee5b147ba7d"
R55_ORIGINAL_CASE_SHA="febda7e51d09194a337fc3b869f8608e05621e57fa41020c82ea5624818b5a8b"
R55_ORIGINAL_SUMMARY_SHA="94207a0d83ba251ac5480ad38bd73ff02f94bfef717ea0334bcdb26d2b5505b5"
EXPECTED={(b,s) for b in range(4) for s in SUPPORT}


def verify_original(folder,checkout,case_SHA,summary_SHA=None):
    folder=Path(folder)
    manifest=(folder/"SHA256SUMS").read_text().splitlines()
    if len(manifest)!=3:
        raise ValueError("R55 original SHA256 member count incorrect")
    required={"cases.json","summary.json","source-commit.txt"}
    hashes={}
    for line in manifest:
        h,delimiter,file=line.partition("  ")
        if not delimiter or file not in required or file in hashes or len(h)!=64:
            raise ValueError("R55 duplicate/unregistered original SHA256 member")
        actual=hashlib.sha256((folder/file).read_bytes()).hexdigest()
        if actual!=h:
            raise ValueError("R55 original SHA256 checksum mismatch for "+file)
        hashes[file]=h
    if set(hashes)!=required or hashes["cases.json"]!=case_SHA:
        raise ValueError("R55 original Gaussian case source identity/hash mismatch")
    if summary_SHA is not None and hashes["summary.json"]!=summary_SHA:
        raise ValueError("R55 original aggregate summary SHA256 mismatch")
    if (folder/"source-commit.txt").read_text().strip()!=checkout:
        raise ValueError("R55 original PR-merge source checkout mismatch")
    return hashes


def transition_original(nodes,sign):
    ordered=[x for x in nodes if x["sign"]==sign]
    if [(x["level"]) for x in ordered]!=list(LEVELS):
        raise ValueError("R55 missing original signed path amplitude order")
    previous=0.
    for item in ordered:
        if item["status"]!="ok":
            return {
                "status":"unresolved_after_fit_or_CR2_refusal",
                "first_refused_level":item["level"],
                "previous_no_switch_level":previous,
            }
        if item["face_changed_from_original"]:
            return {
                "status":"first_observed_active_face_change_bracket",
                "previous_no_switch_level":previous,
                "first_changed_level":item["level"],
                "true_crossing_time_identified":False,
            }
        previous=item["level"]
    return {
        "status":"no_changed_face_on_frozen_grid",
        "max_checked_level":LEVELS[-1],
        "switch_absence_between_grid_nodes_not_proven":True,
    }


def audit(r53_folder,r55_folder):
    sha53=verify_original(r53_folder,R53_SOURCE_CHECKOUT,R53_ORIGINAL_CASE_SHA)
    sha55=verify_original(
        r55_folder,R55_SOURCE_CHECKOUT,R55_ORIGINAL_CASE_SHA,
        R55_ORIGINAL_SUMMARY_SHA,
    )
    old=json.loads((Path(r53_folder)/"cases.json").read_text())
    new=json.loads((Path(r55_folder)/"cases.json").read_text())
    published=json.loads((Path(r55_folder)/"summary.json").read_text())
    for label,rows in (("R53",old),("R55",new)):
        keys=[(r["block"],r["support"]) for r in rows]
        if len(keys)!=8 or set(keys)!=EXPECTED:
            raise ValueError("R55 missing, duplicated or unexpected "+label+" source IDs")
    if (published["R53_original_innovation_seed_REUSED"]!=MASTER
         or published["R55_independent_response_direction_seed"]!=DIRECTION
         or published["new_independent_Gaussian_primitive_source_count"]!=0
         or published["planned_original_source_cases"]!=8
         or published["recorded_original_source_cases"]!=8
         or published["planned_directions"]!=16
         or published["recorded_direction_cases"]!=16
         or published["planned_signed_perturbed_fit_slots"]!=128
         or published["recorded_signed_perturbed_fit_slots"]!=128
         or published["executed_perturbed_full_REML_fit_attempts"]!=128
         or published["planned_original_plus_perturbed_fit_slots"]!=136
         or published["planned_two_start_optimizer_outcome_slots"]!=272
         or published["recorded_executed_two_start_optimizer_outcomes"]!=272
         or not published["full_failure_inclusive_structural_source_grid"]
         or published["release_authorized"]):
        raise ValueError("R55 original failure-denominator/source ledger corrupted")
    previous={(x["block"],x["support"]):x for x in old}
    case_rows=[]
    all_nodes=[]
    transitions=[]
    fit_start_changes=[]
    for case in new:
        block,support=case["block"],case["support"]
        name=f"{block}:{support}"
        prior=previous[block,support]
        if case["R53_R54_original_source_reused_not_new_independent"] is not True:
            raise ValueError("R55 source replay flag altered "+name)
        current=case["original_fit"]
        old_fit=prior["original_nuisance"]
        validate_fit(current,name+"/original")
        for comp in COMPONENTS:
            close(current["components"][comp],old_fit["components"][comp],
                  name+"/matched source Gaussian nuisance "+comp,
                  rtol=1e-6,atol=2e-10)
        close(current["reference_variance"],old_fit["reference_variance"],
              name+"/matched WLS variance reference",rtol=1e-10,atol=1e-12)
        close(case["projected_generating_focal_truth"],
              prior["projected_truth"],name+"/source generating focal truth",
              rtol=1e-12,atol=1e-10)
        original_sig=signature(current)
        if case["original_signature"]!=original_sig:
            raise ValueError("R55 original active ratio signature corrupted "+name)
        if case["local_face_status"]!="ok":
            raise ValueError("R55 original accepted active-face Jacobian misreported "+name)
        if len(case["directions"])!=2:
            raise ValueError("R55 source direction missing "+name)
        if current["selected_start"]!=old_fit["selected_start"]:
            fit_start_changes.append(name)

        for direction,path in enumerate(case["directions"]):
            label=f"{name}:direction{direction}"
            expected_seed=DIRECTION+100003*block+711*SUPPORT.index(support)+direction
            if path["direction"]!=direction or path["seed"]!=expected_seed:
                raise ValueError("R55 original frozen direction seed mismatch "+label)
            nodes=path["nodes"]
            if len(nodes)!=8 or [(n["level"],n["sign"]) for n in nodes]!=[
                (a,s) for a in LEVELS for s in SIGNS
            ]:
                raise ValueError("R55 missing signed-level identity "+label)
            for sign in SIGNS:
                saved=path["transition_by_sign"][str(sign)]
                computed=transition_original(nodes,sign)
                if saved!=computed:
                    raise ValueError("R55 original signed-path transition bracket incorrect "+label)
                if computed["status"]=="first_observed_active_face_change_bracket":
                    transitions.append({
                        "source":name,"direction":direction,"sign":sign,
                        "previous_no_switch_level":computed["previous_no_switch_level"],
                        "first_changed_level":computed["first_changed_level"],
                    })
            for node in nodes:
                fit=node["fit"]
                if fit is None or node["status"]!="ok":
                    raise ValueError("R55 claimed accepted original fit is missing "+label)
                validate_fit(fit,label+"/signed-"+str(node["sign"])
                             +"/step-"+str(node["level"]))
                active=signature(fit)
                if [node["active_low"],node["active_high"]]!=active:
                    raise ValueError("R55 wrong original selected active face "+label)
                if bool(active!=original_sig)!=node["face_changed_from_original"]:
                    raise ValueError("R55 false active-face transition flag "+label)
                if bool(fit["selected_start"]!=current["selected_start"])!=node[
                    "selected_start_changed_from_original"]:
                    raise ValueError("R55 optimizer start change misreported "+label)
                if (node["weighted_response_step"] is None
                    or not math.isfinite(float(node["weighted_response_step"]))
                    or node["weighted_response_step"]<=0):
                    raise ValueError("R55 invalid original response perturbation "+label)
                close(node["weighted_response_step"],
                      node["level"]*max(float(path["weighted_original_response_RMS"]),.01),
                      label+"/frozen weighted-response step",rtol=1e-12)
                ratios=[
                    fit["components"][comp]/fit["reference_variance"]
                    for comp in COMPONENTS
                ]
                np.testing.assert_allclose(
                    ratios,node["fitted_component_ratios"],
                    rtol=1e-9,atol=1e-10,
                    err_msg="R55 original positive physical variance ratios false")
                point=float(node["observed_focal_CR2_point"])
                se=float(node["observed_focal_CR2_se"])
                if not se>0:
                    raise ValueError("R55 original CR2 SE nonpositive "+label)
                actual=(point-case["projected_generating_focal_truth"])/se
                close(actual,node["observed_studentized_truth_pivot"],
                      label+"/original Gaussian studentized CR2 pivot",rtol=1e-9)
                predicted=float(node["predicted_active_face_pivot"])
                close(abs(predicted-actual),
                      node["absolute_local_pivot_prediction_discrepancy"],
                      label+"/Taylor pivot discrepancy",rtol=1e-9,atol=1e-11)
                expected=np.array(node["theta_component_predicted"],float)
                observed=np.array(node["theta_component_observed"],float)
                fitted=np.array([fit["components"][k] for k in COMPONENTS],float)
                np.testing.assert_allclose(
                    observed,fitted,rtol=1e-9,atol=1e-12,
                    err_msg="R55 original refitted nuisance vector mismatch")
                initial=np.array([
                    current["components"][k] for k in COMPONENTS],float)
                relative=float(np.linalg.norm(expected-observed)/
                    max(np.linalg.norm(initial),np.linalg.norm(observed),1e-12))
                close(relative,node["theta_relative_local_prediction_discrepancy"],
                      label+"/nuisance Taylor discrepancy",rtol=1e-8)
                all_nodes.append({
                    "support":support,"block":block,
                    "level":node["level"],"sign":node["sign"],
                    "face_changed":node["face_changed_from_original"],
                    "start_changed":node["selected_start_changed_from_original"],
                    "pivot_abs_error":abs(predicted-actual),
                })
        case_rows.append({
            "source":name,"original_face":original_sig,
            "R53_matched_original_fit":True,
        })
    if len(all_nodes)!=128 or len(case_rows)!=8 or len(transitions)!=5:
        raise ValueError("R55 original full fixed grid, matches or transitions incorrect")
    strata={}
    for support in SUPPORT:
        group=[n for n in all_nodes if n["support"]==support]
        bylevel={}
        for level in LEVELS:
            subset=[n for n in group if n["level"]==level]
            if len(subset)!=16:
                raise ValueError("R55 original source-level stratification inconsistent")
            record=published["strata"][support]["by_amplitude"][str(level)]
            numchange=sum(n["face_changed"] for n in subset)
            seedchange=sum(n["start_changed"] for n in subset)
            median=float(np.median([n["pivot_abs_error"] for n in subset]))
            median_same=float(np.median([
                n["pivot_abs_error"] for n in subset if not n["face_changed"]
            ]))
            if (numchange!=record["changed_selected_active_face"]
               or seedchange!=record["selected_optimizer_start_changed"]
               or record["accepted_refits_and_CR2"]!=16):
                raise ValueError("R55 original active-face and start-switch aggregate falsified")
            close(median,record["median_abs_local_pivot_prediction_error_among_accepted"],
                  support+":"+str(level)+"/pivot median",rtol=1e-12)
            close(median_same,record["median_abs_local_pivot_prediction_error_stable_face"],
                  support+":"+str(level)+"/same face median",rtol=1e-12)
            bylevel[str(level)]={
                "accepted_refits":16,
                "changed_selected_face":numchange,
                "changed_original_start_label":seedchange,
                "median_absolute_CR2_pivot_prediction_error":median,
                "median_same_face_pivot_prediction_error":median_same,
            }
        observed=sum(t["source"].endswith(support) for t in transitions)
        if observed!=published["strata"][support]["first_transition_brackets_observed"]:
            raise ValueError("R55 original first grid transition bracket count corrupted")
        strata[support]={"first_observed_signed_path_transitions":observed,
                         "by_amplitude":bylevel}
    return {
        "immutable_original_R53_and_R55_audit_passed":True,
        "R53_source_original_SHA256":sha53,
        "R55_source_original_SHA256":sha55,
        "original_R53_source_cases_replayed":len(case_rows),
        "new_independent_primitive_Gaussian_source_blocks":0,
        "original_fit_changed_near_equivalent_selected_start":fit_start_changes,
        "verified_original_signed_fit_records":len(all_nodes),
        "verified_original_optimizer_start_records":2*(8+len(all_nodes)),
        "first_observed_active_face_change_brackets":transitions,
        "R55_per_leverage_source_evidence":strata,
        "grid_bracket_not_true_switch_threshold":True,
        "no_population_switching_probability":True,
        "no_true_zero_slope_variance_boundary_or_90pct_CI_qualification":True,
        "release_authorized":False,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--r53-original",type=Path,required=True)
    p.add_argument("--r55-original",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    a.out.parent.mkdir(parents=True,exist_ok=True)
    report=audit(a.r53_original,a.r55_original)
    a.out.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print(a.out.read_text())


if __name__=="__main__":
    main()
