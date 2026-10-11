"""Controlled W3 computational sensitivity, not independent coverage replication."""
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from scripts.run_w3_same_dataset_bootstrap_sensitivity import (
    BLOCKS,DRAWS,MULTIPLIERS,case,audit,bootstrap_seed
)
from scripts.run_w3_fixed_truth_interval_pilot import MASTER_SEED,DESIGNS


def test_same_source_seed_reused_only_for_original_rademacher_199():
    for design in DESIGNS:
        for block in (0,7,15):
            expected=MASTER_SEED + block*317 + (11 if design=="curve" else 29)
            assert bootstrap_seed(block,design,"rademacher")==expected
            assert bootstrap_seed(block,design,"normal")!=expected


@pytest.mark.parametrize("design",DESIGNS)
def test_same_data_four_computational_references_and_nested_prefixes(design):
    result=case(0,design)
    assert result["status"]=="ok",result["exception"]
    assert not result["new_independent_dataset"]
    assert result["oracle_coef_max_delta"] < 2e-10
    assert result["oracle_se_max_delta"] < 2e-10
    assert len(result["cells"])==4
    assert all(result["same_multiplier_199_prefix_matches_999"].values())
    assert all(
        result["cells"][f"{m}_{n}"]["n_multipliers_independent_units"]
        == (36 if design=="participant" else 72)
        for m in MULTIPLIERS for n in DRAWS
    )
    assert result["coverage_qualified"] is False


def test_failure_inclusive_multiplicity_and_design_units():
    result=case(0,"curve")
    incomplete=audit([result])
    assert incomplete["planned_source_datasets"]==32
    assert incomplete["planned_bootstrap_comparisons"]==128
    assert incomplete["completed_datasets"]==1
    assert len(incomplete["missing_datasets"])==31
    assert not incomplete["fresh_independent_replication"]
    assert incomplete["no_method_winner_selected"] is True
    with pytest.raises(ValueError,match="duplicated"):
        audit([result,result])


def test_error_row_retained_for_out_of_ledger_case():
    invalid=case(max(BLOCKS)+1,"curve")
    assert invalid["status"]=="failed"
    assert invalid["exception"]["type"]=="ValueError"
