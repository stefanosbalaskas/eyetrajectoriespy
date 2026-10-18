"""R65 read-only original R64 matched-block detection-contrast uncertainty.

Not a new experiment, confirmatory interaction hypothesis, or qualified 5%
test. Audits the immutable original R64 source archive before using outcomes.
Resamples 32 independent primitive Gaussian BLOCKS as intact six-cell clusters,
never its 192 correlated source cases or 12,096 conditional H0 pseudodraws.
"""
from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path

from scripts.audit_w3_r64_original_positive_slope_independent import audit_original

STUDY = "W3_R65_READONLY_ORIGINAL_R64_BLOCK_PAIRED_DETECTION_DIAGNOSTIC"
ORIGINAL_R64_CHECKOUT = "ebe731c3db6a491f1d6b494d91d05143ecc9ee35"
R64_BLOCKS = 32
SUPPORT = ("ordinary_dependent", "extreme_dependent")
LEVELS = ("zero", "half", "full")
CONTRASTS = (("zero", "half"), ("half", "full"), ("zero", "full"))
RESAMPLE_SEED = 202610186565
RESAMPLES = 20_000
PERCENTILE = (0.025, 0.975)


def _quantile(sorted_values: list[float], p: float) -> float:
    if not sorted_values or not 0 <= p <= 1:
        raise ValueError("R65 invalid empirical percentile")
    z = p * (len(sorted_values)-1)
    lo = int(math.floor(z))
    hi = int(math.ceil(z))
    return sorted_values[lo] + (z-lo)*(sorted_values[hi]-sorted_values[lo])


def original_binary_grid(cases: list[dict]) -> dict[tuple[int,str,str], bool | None]:
    expected = {(b,s,l) for b in range(R64_BLOCKS) for s in SUPPORT for l in LEVELS}
    found = [(r["block"],r["support"],r["level"]) for r in cases]
    if len(found)!=192 or len(set(found))!=192 or set(found)!=expected:
        raise ValueError("R65 original complete 32 independent source block six-cell grid required")
    outcomes = {}
    for r in cases:
        p = r.get("conditional_bootstrap_p")
        detected = r.get("bootstrap_5pct_exceedance")
        if p is None:
            if detected is not None:
                raise ValueError("R65 refused source cannot claim detection")
            outcome = None
        else:
            if type(detected) is not bool or not isinstance(p,(float,int)) or p<=0 or p>1:
                raise ValueError("R65 conditional original bootstrap p/detection missing")
            if not math.isclose(64*p,round(64*p),abs_tol=1e-11):
                raise ValueError("R65 changed conditional original Gaussian rank grid")
            if detected is not (p<=0.05):
                raise ValueError("R65 original source detection differs from fixed p-grid")
            outcome = detected
        outcomes[(r["block"],r["support"],r["level"])] = outcome
    return outcomes


def _difference(a: bool | None, b: bool | None) -> int | None:
    # Delta from a to b; preserve missing/refused numerical source positions.
    return None if a is None or b is None else int(b)-int(a)


def _paired_ledger(outcomes: dict, support: str, left: str, right: str) -> dict:
    if support not in SUPPORT or left not in LEVELS or right not in LEVELS or left == right:
        raise ValueError("R65 contrast outside frozen paired source design")
    changes = [_difference(outcomes[(b,support,left)],
                           outcomes[(b,support,right)]) for b in range(R64_BLOCKS)]
    complete = [x for x in changes if x is not None]
    missing = R64_BLOCKS-len(complete)
    neg = sum(x == -1 for x in complete)
    pos = sum(x == 1 for x in complete)
    same = sum(x == 0 for x in complete)
    return {
        "support":support,
        "from_level":left,
        "to_level":right,
        "independent_source_blocks":R64_BLOCKS,
        "complete_matched_blocks":len(complete),
        "numerically_incomplete_blocks":missing,
        "matched_positive_only_at_later_level":pos,
        "matched_positive_only_at_earlier_level":neg,
        "matched_agreement":same,
        "difference_in_candidate_rejection_rate_complete":sum(complete)/len(complete) if complete else None,
        "failure_inclusive_lower_if_missing_contrasts_negative":(sum(complete)-missing)/R64_BLOCKS,
        "failure_inclusive_upper_if_missing_contrasts_positive":(sum(complete)+missing)/R64_BLOCKS,
        "per_primitive_block_changes":changes,
    }


def analyze_paired(outcomes: dict, *, n_resamples=RESAMPLES, seed=RESAMPLE_SEED) -> dict:
    if not isinstance(n_resamples,int) or n_resamples<100 or not isinstance(seed,int):
        raise ValueError("R65 invalid fixed block-bootstrap sample budget")
    expected = {(b,s,l) for b in range(R64_BLOCKS) for s in SUPPORT for l in LEVELS}
    if set(outcomes)!=expected:
        raise ValueError("R65 source-level six-cell original grid incomplete")
    ledgers={}
    vectors={}
    for support in SUPPORT:
        for left,right in CONTRASTS:
            key=f"{support}/{left}_to_{right}"
            ledger=_paired_ledger(outcomes,support,left,right)
            ledgers[key]=ledger
            vectors[key]=ledger["per_primitive_block_changes"]
    ordinary = vectors[f"{SUPPORT[0]}/zero_to_full"]
    extreme = vectors[f"{SUPPORT[1]}/zero_to_full"]
    interaction=[
        None if a is None or b is None else b-a
        for a,b in zip(ordinary,extreme)
    ]
    interaction_known=[x for x in interaction if x is not None]
    missing_interaction=R64_BLOCKS-len(interaction_known)
    interaction_record={
        "independent_matched_primitive_blocks":R64_BLOCKS,
        "complete_matched_primitive_blocks":len(interaction_known),
        "incomplete_matched_primitive_blocks":missing_interaction,
        "extreme_minus_ordinary_full_vs_zero_rate_change_complete":
            sum(interaction_known)/len(interaction_known) if interaction_known else None,
        # A missing two-support contrast could lie in [-2,+2].
        "failure_inclusive_lower":(sum(interaction_known)-2*missing_interaction)/R64_BLOCKS,
        "failure_inclusive_upper":(sum(interaction_known)+2*missing_interaction)/R64_BLOCKS,
        "blockwise_difference_in_differences":interaction,
    }
    # All six contrasts and interaction resample THE SAME primitive blocks
    # per replicate. Never resample source cases or original H0 draws.
    rng=random.Random(seed)
    boot={key:[] for key in ledgers}
    boot["extreme_minus_ordinary_full_vs_zero"]=[]
    all_complete=all(x is not None for row in vectors.values() for x in row) and all(x is not None for x in interaction)
    if all_complete:
        for _ in range(n_resamples):
            indexes=[rng.randrange(R64_BLOCKS) for _ in range(R64_BLOCKS)]
            for key,row in vectors.items():
                boot[key].append(sum(row[b] for b in indexes)/R64_BLOCKS)
            boot["extreme_minus_ordinary_full_vs_zero"].append(
                sum(interaction[b] for b in indexes)/R64_BLOCKS)
        for key,measurements in boot.items():
            order=sorted(measurements)
            ci=[_quantile(order,PERCENTILE[0]),_quantile(order,PERCENTILE[1])]
            if key in ledgers:
                ledgers[key]["posthoc_paired_block_bootstrap_percentile95"]=ci
            else:
                interaction_record["posthoc_paired_block_bootstrap_percentile95"]=ci
    else:
        for ledger in ledgers.values():
            ledger["posthoc_paired_block_bootstrap_percentile95"]=None
        interaction_record["posthoc_paired_block_bootstrap_percentile95"]=None
    return {
        "study":STUDY,
        "no_new_sources_or_nuisance_REML_fits":True,
        "original_R64_source_checkout":ORIGINAL_R64_CHECKOUT,
        "new_independent_source_blocks":0,
        "source_blocks_carried_over_from_R64":R64_BLOCKS,
        "paired_source_cases_carried_over_from_R64":192,
        "H0_bootstrap_source_draws_are_NOT_MC_units":True,
        "paired_primitive_block_bootstrap_resamples":n_resamples,
        "paired_primitive_block_bootstrap_seed":seed,
        "bootstrap_intervals_are_exploratory_posthoc_not_confirmatory":True,
        "paired_level_contrasts":ledgers,
        "paired_leverage_interaction_diagnostic":interaction_record,
        "original_binary_grid_complete":len(outcomes)==192,
        "no_validated_5pct_type_I_control_or_statistical_power":True,
        "no_fitted_CR2_90pct_pointwise_or_simultaneous_confidence_qualification":True,
        "release_authorized":False,
    }


def analyze_immutable_original(folder: Path) -> dict:
    audit=audit_original(folder,expected_original_checkout=ORIGINAL_R64_CHECKOUT)
    if not audit["R64_independent_original_numerical_archive_reproduced"]:
        raise ValueError("R65 independently verified original R64 numerical evidence required")
    original=json.loads((Path(folder)/"cases.json").read_bytes())
    out=analyze_paired(original_binary_grid(original))
    out["original_source_sha256_entries_reverified"]=audit["original_sha256_entries_verified"]
    out["original_nested_model_fit_slots_reverified"]=audit["nested_model_fit_positions"]
    out["original_optimizer_start_records_reverified"]=audit["optimizer_start_positions"]
    out["original_projected_KKT_max_reverified"]=audit["largest_selected_projected_KKT"]
    return out


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--original",required=True,type=Path)
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args()
    report=analyze_immutable_original(args.original)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_bytes((json.dumps(report,sort_keys=True,indent=2)+"\n").encode("utf-8"))
    concise={
        "study":STUDY,
        "original_source_sha256_entries_reverified":report["original_source_sha256_entries_reverified"],
        "contrasts":{
            name:{"rate_change":row["difference_in_candidate_rejection_rate_complete"],
                  "CI":row["posthoc_paired_block_bootstrap_percentile95"],
                  "full_only":row["matched_positive_only_at_later_level"],
                  "zero_only":row["matched_positive_only_at_earlier_level"]}
            for name,row in report["paired_level_contrasts"].items()},
        "interaction":report["paired_leverage_interaction_diagnostic"],
        "release_authorized":False,
    }
    print(json.dumps(concise,sort_keys=True))


if __name__=="__main__":
    main()
