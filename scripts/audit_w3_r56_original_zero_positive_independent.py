"""Independent read-only SHA256 and original-Gaussian R56 case-ledger audit.

DOES NOT import R56 scientific source generator, Gaussian REML optimizer or
CR2 implementation, and DOES NOT rerun scientific source samples. Verifies
original evidence file identities, numerical acceptance/start gates,
true-source metadata, paired original block support/zero states, physical
positive-bound ratios, conditional CR2 inclusion arithmetic and all medians.

A source-only JSON ledger does NOT contain every raw original native y row.
Consequently the exact analytical slope subtraction was tested in R56 source
contract tests but cannot be reconstructed from this read-only ledger alone.
No genuine zero-boundary test, sampling probability or coverage qualification.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from scipy.stats import t as student_t

from scripts.audit_w3_r54_original_active_face_independent import (
    COMPONENTS,validate_fit,close,
)

SOURCE_SHA="ce84ab53bfcbb09000c57b6f232f59a1f86996aa"
CASE_SHA="5ebc77b4144aa595791d9b6435045a431e22949a0d79e4e5502ca9e9317b831c"
SUMMARY_SHA="53bf046cbc9cb38139b4db673be162287f778f154ee6d05cf3e22fed56f2cd11"
MASTER=202610175656
BLOCKS=16
SUPPORT=("ordinary_dependent","extreme_dependent")
STATES=("true_zero","true_positive")
LOW=math.exp(-13.8)
BOUND_TOL=1e-5
TRUE_POSITIVE_VAR=.002025


def verify_archive(path):
    folder=Path(path)
    expected={"cases.json","summary.json","source-commit.txt"}
    lines=(folder/"SHA256SUMS").read_text().splitlines()
    if len(lines)!=3:
        raise ValueError("R56 original SHA256 member count incorrect")
    found={}
    for line in lines:
        h,sep,name=line.partition("  ")
        if not sep or name not in expected or name in found or len(h)!=64:
            raise ValueError("R56 original SHA256 member identity invalid")
        actual=hashlib.sha256((folder/name).read_bytes()).hexdigest()
        if actual!=h:
            raise ValueError("R56 original SHA256 checksum mismatch "+name)
        found[name]=h
    if set(found)!=expected:
        raise ValueError("R56 incomplete original SHA256 source identity")
    if found["cases.json"]!=CASE_SHA or found["summary.json"]!=SUMMARY_SHA:
        raise ValueError("R56 wrong original source case/summary hash")
    if (folder/"source-commit.txt").read_text().strip()!=SOURCE_SHA:
        raise ValueError("R56 wrong original PR merge checkout")
    return found


def audit(folder):
    hashes=verify_archive(folder)
    rows=json.loads((Path(folder)/"cases.json").read_text())
    source_summary=json.loads((Path(folder)/"summary.json").read_text())
    expected={(b,s,z) for b in range(BLOCKS) for s in SUPPORT for z in STATES}
    keys=[(r["block"],r["support"],r["generating_slope_state"]) for r in rows]
    if len(keys)!=64 or set(keys)!=expected:
        raise ValueError("R56 missing, duplicate or unregistered original Gaussian state")
    if (source_summary["new_source_seed"]!=MASTER or
        source_summary["new_independent_Gaussian_primitive_blocks"]!=BLOCKS or
        source_summary["planned_source_slope_state_cases"]!=64 or
        source_summary["recorded_source_slope_state_cases"]!=64 or
        source_summary["planned_original_Gaussian_REML_fit_slots"]!=64 or
        source_summary["planned_original_two_start_optimizer_outcome_slots"]!=128 or
        source_summary["recorded_original_two_start_optimizer_outcome_slots"]!=128 or
        not source_summary["complete_failure_inclusive_original_source_denominator"] or
        source_summary["release_authorized"]):
        raise ValueError("R56 false original independent primitive or fit denominator")

    byid={(r["block"],r["support"],r["generating_slope_state"]):r for r in rows}
    all_stats={}
    all_matched=[]
    for block in range(BLOCKS):
        for support in SUPPORT:
            null=byid[block,support,"true_zero"]
            positive=byid[block,support,"true_positive"]
            if (not null["primitive_design"] or
                null["primitive_design"]!=positive["primitive_design"] or
                not null["primitive_design"]["same_Gaussian_innovations_for_both_slope_states"] or
                not null["primitive_design"]["source_slope_contribution_norm"]>0):
                raise ValueError("R56 false paired raw Gaussian source identity/metadata")
            # The raw observations themselves are absent from immutable JSON.
            # This checks only the source contract claims and matched records,
            # not a second independent proof of exact source-y subtraction.
            for state,row in zip(STATES,(null,positive)):
                label=f"{block}/{support}/{state}"
                if not row["new_independent_innovation_block"] or (
                    not row["slope_states_paired_on_identical_native_source"]):
                    raise ValueError("R56 original independent-vs-paired labels invalid")
                if row["original_source_status"]!="ok":
                    raise ValueError("R56 original Gaussian generation not accepted "+label)
                truthvar=0 if state=="true_zero" else TRUE_POSITIVE_VAR
                close(row["source_truth_slope_variance"],truthvar,
                      label+"/true Gaussian source variance",rtol=1e-12,atol=1e-12)
                fit=row["nuisance_fit"]
                validate_fit(fit,label+"/original strict REML")
                theta=float(fit["components"]["participant_slope"])
                ref=float(fit["reference_variance"])
                if theta<=0 or ref<=0:
                    raise ValueError("R56 numerical positive slope/reference variance false")
                ratio=theta/ref
                close(theta,row["fitted_slope_variance_component"],
                      label+"/positive fitted slope",rtol=1e-11)
                close(ref,row["fitted_slope_to_original_response_reference"],
                      label+"/observed reference",rtol=1e-11)
                close(ratio,row["fitted_slope_ratio"],
                      label+"/ratio",rtol=1e-9)
                expected_floor=(abs(ratio-LOW)<=BOUND_TOL*LOW)
                if expected_floor!=row["source_parameter_ratio_lower_slope_active"]:
                    raise ValueError("R56 false numeric lower positive box decision "+label)
                interval=row["conditional_fitted_CR2"]
                if interval["status"]!="ok":
                    raise ValueError("R56 original conditional CR2 refused "+label)
                if interval["nuisance_estimation_uncertainty_adjusted"] or (
                    interval["pointwise_90pct_coverage_qualified"]):
                    raise ValueError("R56 incorrectly qualified fitted covariance inference")
                if (not float(interval["se"])>0 or
                    not float(interval["conditional_df"])>0):
                    raise ValueError("R56 invalid original CR2 se/df")
                critical=float(student_t.ppf(.95,interval["conditional_df"]))
                close(critical,interval["nominal_90pct_conditional_critical"],
                      label+"/conditional Sat critical",rtol=1e-10)
                included=(abs(interval["estimate"]-
                    row["primitive_design"]["fixed_projected_focal_truth"])<=
                    critical*interval["se"])
                if included!=interval["conditional_90pct_truth_included"]:
                    raise ValueError("R56 false conditional focal truth inclusion "+label)
                all_stats[block,support,state]={
                    "positive_lower_face":expected_floor,
                    "theta":theta,"ratio":ratio,
                    "CR2_truth_included_descriptive_only":included,
                }
            n=all_stats[block,support,"true_zero"]
            p=all_stats[block,support,"true_positive"]
            all_matched.append({
                "block":block,"support":support,
                "difference_fitted_positive_minus_zero":p["theta"]-n["theta"],
                "same_positive_lower_bound":(
                    n["positive_lower_face"]==p["positive_lower_face"]),
                "zero_lower":n["positive_lower_face"],
                "positive_lower":p["positive_lower_face"],
            })

    outcome={}
    for support in SUPPORT:
        for state in STATES:
            values=[all_stats[b,support,state] for b in range(BLOCKS)]
            key=support+"/"+state
            expected_report=source_summary["strata"][key]
            count=sum(x["positive_lower_face"] for x in values)
            coverage=sum(x["CR2_truth_included_descriptive_only"] for x in values)
            median_theta=float(np.median([x["theta"] for x in values]))
            median_ratio=float(np.median([x["ratio"] for x in values]))
            if (count!=expected_report["selected_positive_slope_ratio_lower_bound_count"]
                or coverage!=expected_report["descriptive_conditional_90pct_focal_truth_inclusions"]
                or expected_report["recorded_paired_cases"]!=BLOCKS
                or expected_report["accepted_observed_two_start_REML_fits"]!=BLOCKS
                or expected_report["conditional_fitted_CR2_numerically_accepted"]!=BLOCKS
                or expected_report["population_90pct_coverage_qualified"]):
                raise ValueError("R56 original source stratum numerical counts inconsistent "+key)
            close(median_theta,expected_report["median_fitted_slope_variance"],
                  key+"/median fitted variance",rtol=1e-12)
            close(median_ratio,expected_report["median_fitted_slope_ratio"],
                  key+"/median slope ratio",rtol=1e-12)
            outcome[key]={
                "original_new_independent_primitive_blocks":BLOCKS,
                "accepted_strict_REML_and_CR2":BLOCKS,
                "positive_lower_ratio_selected":count,
                "median_positive_fitted_slope_covariance":median_theta,
                "conditional_90pct_source_inclusions_descriptive_only":coverage,
            }

    pair_stats={}
    for support in SUPPORT:
        matched=[x for x in all_matched if x["support"]==support]
        diffs=[x["difference_fitted_positive_minus_zero"] for x in matched]
        median=float(np.median(diffs))
        reported=source_summary["paired_slope_differences"][support]
        if (reported["complete_observed_two_state_pairs"]!=BLOCKS or
            reported["positive_minus_zero_slopes_are_paired_not_independent"] is not True):
            raise ValueError("R56 invalid original paired differences denominator")
        close(median,reported["median_positive_minus_zero_fitted_slope_variance"],
              support+"/paired median",rtol=1e-12,atol=1e-12)
        pair_stats[support]={
            "matched_original_primitive_blocks":BLOCKS,
            "same_floor_under_zero_positive":sum(
                x["same_positive_lower_bound"] for x in matched),
            "discordant_lower_bound_indicators":sum(
                not x["same_positive_lower_bound"] for x in matched),
            "positive_minus_zero_signed_differences":{
                "positive":sum(v>0 for v in diffs),
                "negative":sum(v<0 for v in diffs),
                "zero":sum(v==0 for v in diffs),
            },
            "median_paired_positive_minus_zero_fitted_variance":median,
            "mean_paired_positive_minus_zero_fitted_variance":float(np.mean(diffs)),
        }
    return {
        "independent_read_only_original_R56_evidence_audit_passed":True,
        "original_source_SHA256s":hashes,
        "matched_original_Gaussian_primitive_blocks":BLOCKS,
        "original_block_support_state_records":len(rows),
        "original_strict_nuisance_fit_numerical_starts_verified":2*len(rows),
        "original_fitted_CR2_descriptive_truth_inclusions_verified":len(rows),
        "group_results":outcome,
        "matched_pair_results":pair_stats,
        "source_native_y_not_present_in_original_JSON":True,
        "zero_slope_subtraction_verified_in_original_source_contract_tests_not_this_read_only_audit":True,
        "no_theta_zero_structural_null_test":True,
        "no_pointwise_or_simultaneous_90pct_coverage_qualification":True,
        "release_authorized":False,
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--original",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    result=audit(args.original)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(args.out.read_text())


if __name__=="__main__":
    main()
