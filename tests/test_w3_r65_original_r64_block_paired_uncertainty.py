"""R65 deterministic source-block resampling and frozen R64 grid contracts."""
from __future__ import annotations

import pytest

from scripts import run_w3_r65_original_r64_block_paired_uncertainty as r65


def _grid():
    # 32 independent primitive blocks; every support×level reuses the same
    # block. Frozen toy decisions mimic the real R64 discordance counts,
    # but are fake fixtures; real results require original archive audit.
    yes = {
        ("ordinary_dependent","zero"):{0,1,2},
        ("ordinary_dependent","half"):{0,1,2},
        ("ordinary_dependent","full"):{0,1,2,3},
        ("extreme_dependent","zero"):{0,15},
        ("extreme_dependent","half"):{0,1,2,17},
        ("extreme_dependent","full"):{0,1,2,3,4,5,6,7},
    }
    result=[]
    for b in range(r65.R64_BLOCKS):
        for s in r65.SUPPORT:
            for l in r65.LEVELS:
                detected=b in yes[(s,l)]
                result.append({
                    "block":b,"support":s,"level":l,
                    "conditional_bootstrap_p":0.03125 if detected else 0.125,
                    "bootstrap_5pct_exceedance":detected,
                })
    return result


def test_original_grid_is_192_paired_cases_not_independent_samples():
    outcomes=r65.original_binary_grid(_grid())
    assert len(outcomes)==192
    assert len({block for block,_,_ in outcomes})==32
    assert r65.ORIGINAL_R64_CHECKOUT=="ebe731c3db6a491f1d6b494d91d05143ecc9ee35"
    assert r65._difference(False,True)==1
    assert r65._difference(True,False)==-1
    assert r65._difference(True,True)==0
    assert r65._difference(None,True) is None


def test_frozen_block_paired_original_discordance_and_descriptive_interaction():
    x=r65.analyze_paired(r65.original_binary_grid(_grid()),n_resamples=200,seed=7)
    assert x["new_independent_source_blocks"]==0
    assert x["paired_source_cases_carried_over_from_R64"]==192
    assert x["paired_primitive_block_bootstrap_resamples"]==200
    ordinary=x["paired_level_contrasts"]["ordinary_dependent/zero_to_full"]
    extreme=x["paired_level_contrasts"]["extreme_dependent/zero_to_full"]
    assert ordinary["matched_positive_only_at_later_level"]==1
    assert ordinary["matched_positive_only_at_earlier_level"]==0
    assert ordinary["matched_agreement"]==31
    assert ordinary["difference_in_candidate_rejection_rate_complete"]==1/32
    assert extreme["matched_positive_only_at_later_level"]==7
    assert extreme["matched_positive_only_at_earlier_level"]==1
    assert extreme["difference_in_candidate_rejection_rate_complete"]==6/32
    did=x["paired_leverage_interaction_diagnostic"]
    assert did["extreme_minus_ordinary_full_vs_zero_rate_change_complete"]==5/32
    assert did["complete_matched_primitive_blocks"]==32
    assert not x["release_authorized"]
    assert x["no_validated_5pct_type_I_control_or_statistical_power"]


def test_deterministic_resampling_keeps_all_32_independent_blocks_together():
    outcomes=r65.original_binary_grid(_grid())
    a=r65.analyze_paired(outcomes,n_resamples=400,seed=123)
    b=r65.analyze_paired(outcomes,n_resamples=400,seed=123)
    assert a==b
    different=r65.analyze_paired(outcomes,n_resamples=400,seed=124)
    assert a["paired_leverage_interaction_diagnostic"][
        "posthoc_paired_block_bootstrap_percentile95"
    ]!=different["paired_leverage_interaction_diagnostic"][
        "posthoc_paired_block_bootstrap_percentile95"
    ] or a["paired_level_contrasts"]!=different["paired_level_contrasts"]
    for record in a["paired_level_contrasts"].values():
        lower,upper=record["posthoc_paired_block_bootstrap_percentile95"]
        assert -1<=lower<=upper<=1
    lower,upper=a["paired_leverage_interaction_diagnostic"][
        "posthoc_paired_block_bootstrap_percentile95"
    ]
    assert -2<=lower<=upper<=2


def test_incomplete_original_source_is_not_silently_dropped():
    outcomes=r65.original_binary_grid(_grid())
    outcomes[(0,"extreme_dependent","full")]=None
    a=r65.analyze_paired(outcomes,n_resamples=200,seed=11)
    e=a["paired_level_contrasts"]["extreme_dependent/zero_to_full"]
    assert e["numerically_incomplete_blocks"]==1
    assert e["complete_matched_blocks"]==31
    assert e["posthoc_paired_block_bootstrap_percentile95"] is None
    assert e["failure_inclusive_lower_if_missing_contrasts_negative"]<=e[
        "failure_inclusive_upper_if_missing_contrasts_positive"
    ]
    assert a["paired_leverage_interaction_diagnostic"][
        "posthoc_paired_block_bootstrap_percentile95"] is None


def test_missing_or_falsified_original_rank_refused_and_duplicate_grid_fail_closed():
    rows=_grid()
    rows[0]["conditional_bootstrap_p"]=0.031
    with pytest.raises(ValueError,match="rank grid"):
        r65.original_binary_grid(rows)
    rows=_grid()
    rows[0]["bootstrap_5pct_exceedance"]=False
    with pytest.raises(ValueError,match="differs"):
        r65.original_binary_grid(rows)
    rows=_grid()
    rows[0]["conditional_bootstrap_p"]=None
    with pytest.raises(ValueError,match="refused"):
        r65.original_binary_grid(rows)
    with pytest.raises(ValueError,match="six-cell grid"):
        r65.original_binary_grid(_grid()[:-1])


def test_unsupported_confidence_budget_is_rejected():
    with pytest.raises(ValueError,match="sample budget"):
        r65.analyze_paired(r65.original_binary_grid(_grid()),n_resamples=99)
    with pytest.raises(ValueError,match="percentile"):
        r65._quantile([],0.5)
