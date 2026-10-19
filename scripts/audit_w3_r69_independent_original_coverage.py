"""R69-A independent archived source/block and paired band decision audit.

Does not import R69's original source generator, fitter, 999-draw bootstrap
or original aggregate. Reconstructs finite-source coverage and paired tables
from the immutable numerical archive, NOT the unarchived wild weight streams.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path

STUDY="W3_R69_NEW_INDEPENDENT_FIXED_TRUTH_BAND_MULTIPLIER_BUDGET_DIAGNOSTIC"
AUDIT="W3_R69_A_INDEPENDENT_ORIGINAL_SOURCE_LEVEL_BAND_SUMMARY_AUDIT"
CHECKOUT="72f7acf6fac9f973ec96b672e30e926a6ec63c75"
SEED=202610196969
BLOCKS=16
DESIGNS=("curve","participant")
MULT=("rademacher","normal")
BUDGETS=(199,999)
MAXB=999
DRAW_STREAMS=BLOCKS*len(DESIGNS)*len(MULT)*MAXB
ATOL=2e-10


def _same(a,b,label):
    if a is None or b is None:
        if a is not None or b is not None:
            raise ValueError("R69-A invalid null comparison "+label)
    elif isinstance(a,(int,float)) and isinstance(b,(int,float)):
        if not math.isclose(float(a),float(b),rel_tol=0,abs_tol=2e-11):
            raise ValueError("R69-A numerical source ledger mismatch "+label)
    elif a!=b:
        raise ValueError("R69-A source ledger mismatch "+label)


def _wilson(k,n,z=1.95996398454):
    if n==0:
        return None
    p=k/n
    d=1+z*z/n
    middle=(p+z*z/(2*n))/d
    radius=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return [max(0.,min(p,middle-radius)),min(1.,max(p,middle+radius))]


def _pair(rows,design,left,right):
    sub=[x for x in rows if x["design"]==design and x["completed"]]
    missing=BLOCKS-len(sub)
    deltas=[
        int(x["conditions"][right]["truth_slope_simultaneous_all_grid"])-
        int(x["conditions"][left]["truth_slope_simultaneous_all_grid"])
        for x in sub
    ]
    critical=[
        x["conditions"][right]["critical_slope"]-
        x["conditions"][left]["critical_slope"]
        for x in sub
    ]
    return {
        "matched_complete_primitive_generating_blocks":len(sub),
        "missing_or_failed_primitive_blocks":missing,
        "later_only_truth_included":sum(x==1 for x in deltas),
        "earlier_only_truth_included":sum(x==-1 for x in deltas),
        "both_agree":sum(x==0 for x in deltas),
        "mean_paired_critical_change_complete":sum(critical)/len(critical) if critical else None,
        "observed_truth_inclusion_change_complete":sum(deltas)/len(deltas) if deltas else None,
        "failure_inclusive_lower":(sum(deltas)-missing)/BLOCKS,
        "failure_inclusive_upper":(sum(deltas)+missing)/BLOCKS,
        "exploratory_not_confirmatory_superiority":True,
    }


def check_archive(folder:Path,expected_checkout:str=CHECKOUT):
    files=("cases.json","summary.json","source-commit.txt")
    sums=(folder/"SHA256SUMS").read_text().splitlines()
    expected=[sha256((folder/file).read_bytes()).hexdigest()+"  "+file for file in files]
    if sums!=expected:
        raise ValueError("R69-A original archive SHA256 integrity mismatch")
    original_sha=(folder/"source-commit.txt").read_text().strip()
    if original_sha!=expected_checkout:
        raise ValueError("R69-A exact original 16-block science checkout differs")
    cases=json.loads((folder/"cases.json").read_bytes())
    summary=json.loads((folder/"summary.json").read_bytes())
    identities=[(r["block"],r["design"]) for r in cases]
    complete_ids={(b,d) for b in range(BLOCKS) for d in DESIGNS}
    if len(identities)!=32 or set(identities)!=complete_ids or len(set(identities))!=32:
        raise ValueError("R69-A duplicated/missing original primitive generating block identities")
    for key,value in {
        "study":STUDY,"source_seed":SEED,
        "independent_primitive_generating_blocks":BLOCKS,
        "datasets_paired_within_primitive_block":2,
        "total_source_dataset_records":32,
        "same_fitted_data_across_four_multiplier_budget_cells":True,
        "original_full_bootstrap_draws_generated_not_prefixes":DRAW_STREAMS,
        "Rademacher_and_normal_multipliers":list(MULT),
        "original_199_prefix_nested_inside_999draw_stream":True,
        "nominal_confidence_target":.90,
        "original_fixed_truth_HC1_oracle_tolerance":ATOL,
        "planned_source_records_complete":True,
        "no_calibrated_90pct_simultaneous_coverage_claim":True,
        "no_realistic_MNAR_identification":True,
        "release_authorized":False,
    }.items():
        _same(summary.get(key),value,key)
    allcell={f"{m}/{b}" for m in MULT for b in BUDGETS}
    for case in cases:
        b,design=case["block"],case["design"]
        n=72 if design=="curve" else 36
        if (case["study"]!=STUDY or case["source_seed"]!=SEED+10007*b+DESIGNS.index(design)
            or case["independent_units"]!=n or case["total_observed_curves"]!=(72 if design=="curve" else 108)
            or case["new_primitive_source_blocks"]!=BLOCKS
            or case["bootstrap_draws_are_not_independent_source_units"] is not True
            or case["simultaneous_90pct_coverage_qualified"] is not False
            or case["release_authorized"] is not False):
            raise ValueError("R69-A original source unit or false calibration/release statement")
        if case["completed"]:
            if (case["exception"] is not None
                or case["max_beta_oracle_error"] is None
                or case["max_HC1_oracle_error"] is None
                or case["max_beta_oracle_error"]>ATOL
                or case["max_HC1_oracle_error"]>ATOL
                or set(case["conditions"])!=allcell):
                raise ValueError("R69-A completed source oracle/conditions invalid")
            for name,c in case["conditions"].items():
                m= c["multiplier"]; budget=c["draws"]
                seed=SEED+1000003*b+10007*DESIGNS.index(design)+557*MULT.index(m)+41
                if (name!=f"{m}/{budget}" or budget not in BUDGETS or
                    c["seed"]!=seed or c["source_units"]!=n or
                    c["bootstrap_prefix_of_same_999draw_stream"] is not True
                    or not math.isfinite(c["critical_slope"]) or
                    not math.isfinite(c["critical_family"]) or
                    c["critical_slope"]<0 or c["critical_family"]<c["critical_slope"]-1e-10
                    or type(c["truth_slope_simultaneous_all_grid"]) is not bool
                    or type(c["truth_joint_family_simultaneous_all_grid"]) is not bool
                    or c["truth_joint_family_simultaneous_all_grid"] and
                       not c["truth_slope_simultaneous_all_grid"]):
                    raise ValueError("R69-A wild source condition rank/seed/critical contract violated")
        elif case["exception"] is None:
            raise ValueError("R69-A noncompleted source missing original error")
    cell_results={}
    pairs={}
    for design in DESIGNS:
        obs=[x for x in cases if x["design"]==design and x["completed"]]
        ref=summary["per_design"][design]
        for key,expect in {"attempted":BLOCKS,"complete":len(obs),
                           "failed":BLOCKS-len(obs)}.items():
            _same(ref[key],expect,f"{design}/{key}")
        pointwise=sum(x["mean_slope_pointwise_truth_inclusion"] for x in obs)/len(obs) if obs else None
        _same(ref["mean_pointwise_slope_cell_truth_fraction"],pointwise,f"{design}/pointwise")
        cell_results[design]={}
        for name in sorted(allcell):
            k=sum(x["conditions"][name]["truth_slope_simultaneous_all_grid"] for x in obs)
            family=sum(x["conditions"][name]["truth_joint_family_simultaneous_all_grid"] for x in obs)
            crit=sum(x["conditions"][name]["critical_slope"] for x in obs)/len(obs) if obs else None
            expected_record={
                "independent_generating_blocks_attempted":BLOCKS,
                "independent_generating_blocks_completed":len(obs),
                "slope_simultaneous_truth_inclusions":k,
                "joint_family_truth_inclusions":family,
                "slope_complete_case_rate":k/len(obs) if obs else None,
                "slope_full_denominator_lower":k/BLOCKS,
                "slope_full_denominator_upper":(k+BLOCKS-len(obs))/BLOCKS,
                "slope_Wilson95_completed_only":_wilson(k,len(obs)),
                "average_slope_wild_critical":crit,
                "not_90pct_coverage_calibrated":True,
            }
            target=ref["conditions"][name]
            for field,want in expected_record.items():
                if isinstance(want,list):
                    if not isinstance(target[field],list) or len(target[field])!=len(want):
                        raise ValueError("R69-A wrong source Wilson interval format")
                    for a,b in zip(target[field],want):
                        _same(a,b,design+"/"+name+"/"+field)
                else:
                    _same(target[field],want,design+"/"+name+"/"+field)
            cell_results[design][name]={"numerator":k,"denominator":BLOCKS,
                                        "complete_sources":len(obs),
                                        "joint_family_inclusions":family,
                                        "mean_critical":crit}
        for m in MULT:
            key=f"{design}/{m}/199_to_999"
            rec=_pair(cases,design,f"{m}/199",f"{m}/999")
            for col,value in rec.items():
                _same(summary["paired_diagnostics"][key][col],value,key+"/"+col)
            pairs[key]=rec
        for budget in BUDGETS:
            key=f"{design}/{budget}/rademacher_to_normal"
            rec=_pair(cases,design,f"rademacher/{budget}",f"normal/{budget}")
            for col,value in rec.items():
                _same(summary["paired_diagnostics"][key][col],value,key+"/"+col)
            pairs[key]=rec
    return {
        "study":AUDIT,
        "original_source_checkout":original_sha,
        "original_source_archive_SHA256_verified":3,
        "actual_original_source_level_evidence_independently_reconstructed":True,
        "independent_primitive_generating_blocks_per_design":BLOCKS,
        "new_original_source_datasets":32,
        "original_conditionally_generated_wild_draws":DRAW_STREAMS,
        "original_999draw_reference_max_statistic_arrays_unarchived":True,
        "conditional_bootstrap_critical_values_not_independently_recomputed_from_raw_wild_draws":True,
        "independent_source_coverage":cell_results,
        "original_source_paired_contrasts":pairs,
        "nominal_90pct_coverage_not_qualified":True,
        "response_dependent_gaze_loss_not_addressed":True,
        "release_authorized":False,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original",type=Path,required=True)
    p.add_argument("--expected-original-checkout",default=CHECKOUT)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=check_archive(a.original,expected_checkout=a.expected_original_checkout)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps(result,sort_keys=True))
if __name__=="__main__":
    main()
