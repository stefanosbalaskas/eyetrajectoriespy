"""R67 read-only, failure-inclusive diagnostics of immutable ORIGINAL R66.

No Gaussian source or pseudodraw reruns, no estimator/threshold edits, no
recovered/bootstrap percentile CI. Import the independent R66-A auditor,
not the original R66 simulation or source summary.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from scripts.audit_w3_r66_original_positive_slope_independent import (
    BLOCKS, B, SOURCE_CASES, SOURCE_DRAWS, LEVELS, SUPPORT, audit_original
)

STUDY="W3_R67_READONLY_ORIGINAL_R66_NUMERICAL_REFUSAL_PROVENANCE"
ORIGINAL_RUN=39162296955
ORIGINAL_ARTIFACT=12153256485
ORIGINAL_SHA="6e462b2b59609327f15c76b838c1743c20f20f9a"
EXPECTED_REFUSED_DRAWS=2
EXPECTED_ACCEPTED_DRAWS=SOURCE_DRAWS-EXPECTED_REFUSED_DRAWS


def refusal_reason(draw: dict) -> dict:
    """Classify archived status without rerunning or repairing a failed fit."""
    nested=draw["nested"]
    if nested["status"]=="accepted":
        raise ValueError("R67 cannot label accepted original Gaussian fit refused")
    base={
        "draw":draw["draw"],
        "draw_status":draw["status"],
        "draw_seed":draw.get("seed"),
        "nested_status":nested["status"],
        "source_exception":draw.get("error"),
        "raw_deviance":nested.get("raw_deviance"),
        "nonnegative_deviance":nested.get("nonnegative_deviance"),
    }
    for key in ("null_fit","alternative_fit"):
        fit=nested[key]
        original_starts=fit["original_starts"]
        base[key]={
            "status":fit["status"],
            "model":fit.get("model"),
            "best_observed_multistart_NLL":fit.get("best_observed_multistart_NLL"),
            "selected_start":fit.get("selected_start"),
            "selected_physical_KKT":fit.get("selected_physical_KKT"),
            "optimizer_start_status_counts":dict(sorted(Counter(
                z["status"] for z in original_starts).items())),
            "optimizer_success_by_start":[{
                "label":z["label"],
                "status":z["status"],
                "optimizer_success":z.get("optimizer_success"),
                "physical_projected_KKT":z.get("physical_projected_KKT"),
                "objective_reconstruction_error":z.get("objective_reconstruction_error"),
                "negative_loglik":z.get("negative_loglik"),
            } for z in original_starts],
        }
    a=base["null_fit"]["status"]
    b=base["alternative_fit"]["status"]
    if nested["status"]=="not_attempted":
        base["mechanism"]="unattempted"
    elif draw.get("error") is not None:
        base["mechanism"]="source_or_draw_exception"
    elif a!="accepted" and b!="accepted":
        base["mechanism"]="both_models_not_accepted"
    elif a!="accepted":
        base["mechanism"]="null_model_not_accepted"
    elif b!="accepted":
        base["mechanism"]="alternative_model_not_accepted"
    else:
        base["mechanism"]="nested_likelihood_comparison_refused"
    return base


def summarize_refusals(cases: list[dict], independent_audit: dict) -> dict:
    if (independent_audit.get("R66_independent_original_numerical_archive_reproduced")
            is not True
        or independent_audit.get("original_source_checkout") != ORIGINAL_SHA):
        raise ValueError("R67 cannot inspect source before immutable R66-A independent provenance audit")
    identities=[(x["block"],x["support"],x["level"]) for x in cases]
    expected={(b,s,l) for b in range(BLOCKS) for s in SUPPORT for l in LEVELS}
    if (len(cases)!=SOURCE_CASES or len(set(identities))!=SOURCE_CASES
        or set(identities)!=expected):
        raise ValueError("R67 full original immutable source grid missing/duplicated")
    failures=[]
    all_draws=0
    original_refused=0
    for row in cases:
        orig=row["observed"]
        if orig["status"]!="accepted":
            original_refused+=1
        draws=row["bootstrap"]
        if [z["draw"] for z in draws]!=list(range(B)):
            raise ValueError("R67 incorrect original bootstrap draw order/denominator")
        all_draws+=len(draws)
        for d in draws:
            if d["nested"]["status"]=="accepted":
                continue
            rec=refusal_reason(d)
            rec.update({
                "block":row["block"],
                "support":row["support"],
                "level":row["level"],
                "source_status":row["source_status"],
                "source_error":row.get("source_error"),
                "observed_status":orig["status"],
                "original_source_H0_theta":row.get("fitted_null_theta"),
                "candidate_decision_withheld":row.get("bootstrap_5pct_exceedance") is None,
                "conditional_bootstrap_p":row.get("conditional_bootstrap_p"),
            })
            failures.append(rec)
    if all_draws!=SOURCE_DRAWS:
        raise ValueError("R67 changed original full 48384-draw Gaussian denominator")
    if len(failures)!=EXPECTED_REFUSED_DRAWS:
        raise ValueError("R67 original two numerical refusal slots not preserved")
    if original_refused!=0:
        raise ValueError("R67 original 768 source H0/H1 fits were all accepted")
    block_ids=sorted({x["block"] for x in failures})
    if len(block_ids)!=EXPECTED_REFUSED_DRAWS:
        raise ValueError("R67 two refused Gaussian draws must remain in distinct source blocks")
    if {x["support"] for x in failures}!={"extreme_dependent"}:
        raise ValueError("R67 recorded refusals not exclusively in original extreme-leverage support")
    if {x["level"] for x in failures}!={"half","full"}:
        raise ValueError("R67 missing original extreme half/full refused cases")
    primary=independent_audit["prospective_paired_primitive_block_audit"]
    if (primary["complete_matched_blocks"]!=BLOCKS-2
        or primary["refused_incomplete_blocks"]!=2
        or primary["paired_diagnostics"]["extreme_minus_ordinary_zero_to_full"][
          "prospective_95pct_primitive_block_bootstrap_percentile"] is not None):
        raise ValueError("R67 must preserve withheld original prospective primary matched-block CI")
    return {
        "study":STUDY,
        "original_run_id":ORIGINAL_RUN,
        "original_archive_artifact_id":ORIGINAL_ARTIFACT,
        "original_scientific_checkout":ORIGINAL_SHA,
        "independent_R66_A_original_numerical_evidence_reverified":True,
        "original_SHA256_entries_reverified":independent_audit["original_sha256_entries_verified"],
        "independent_primitive_generating_blocks":BLOCKS,
        "source_cases":SOURCE_CASES,
        "original_source_nested_fit_refusals":original_refused,
        "original_gaussian_bootstrap_draw_slots":all_draws,
        "accepted_original_conditional_draws":all_draws-len(failures),
        "refused_original_conditional_draws":len(failures),
        "affected_primitive_blocks":block_ids,
        "failure_category_counts":dict(sorted(Counter(
            x["mechanism"] for x in failures).items())),
        "refusal_records":sorted(failures,key=lambda x:(x["block"],x["support"],x["level"],x["draw"])),
        "prospective_primary_paired_complete_blocks":primary["complete_matched_blocks"],
        "prospective_primary_paired_incomplete_blocks":primary["refused_incomplete_blocks"],
        "prospective_primary_pct95_interval_correctly_withheld":True,
        "new_original_source_generating_blocks":0,
        "new_covariance_fits":0,
        "no_original_refusal_repair_or_unfrozen_inference":True,
        "not_calibrated_5pct_power_or_fitted_CR2_90pct_coverage":True,
        "release_authorized":False,
    }


def run(original: Path) -> dict:
    evidence=audit_original(original,expected_original_checkout=ORIGINAL_SHA)
    cases=json.loads((original/"cases.json").read_bytes())
    return summarize_refusals(cases,evidence)


def main() -> None:
    cli=argparse.ArgumentParser()
    cli.add_argument("--original",type=Path,required=True)
    cli.add_argument("--out",type=Path,required=True)
    args=cli.parse_args()
    result=run(args.original)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_bytes((json.dumps(result,indent=2,sort_keys=True)+"\n").encode("utf-8"))
    brief={
        "study":STUDY,
        "refused_conditional_Gaussian_draw_slots":result["refused_original_conditional_draws"],
        "affected_blocks":result["affected_primitive_blocks"],
        "failure_category_counts":result["failure_category_counts"],
        "refusal_summary":[{
            "block":x["block"],"support":x["support"],"level":x["level"],
            "draw":x["draw"],"mechanism":x["mechanism"],
            "null_model_status":x["null_fit"]["status"],
            "alternative_model_status":x["alternative_fit"]["status"],
            "exception":x["source_exception"]
        } for x in result["refusal_records"]],
        "prospective_ci_withheld":True,
        "release_authorized":False,
    }
    print(json.dumps(brief,sort_keys=True))


if __name__=="__main__":
    main()
