"""R24 population operator and conditional Gaussian noise reference contracts."""
import numpy as np
import pytest

from scripts import run_w3_r24_expected_moment_noise as study
from scripts import run_w3_r23_estimated_target_identifiability as r23


@pytest.mark.parametrize("block,n,support",[
    (0,24,"ordinary_independent"),
    (0,96,"ordinary_dependent"),
    (7,24,"ordinary_dependent"),
])
def test_population_moments_recover_source_components(block,n,support):
    d=study.operator_for_original_design(block,n,support)
    assert d["contract_relative_error"]<5e-9
    assert d["population_nnls_relative_error"]<5e-8
    assert d["moment_operator_condition"]>=1.
    assert d["theoretical_outer_product_noise_to_signal_rms"]>0
    assert len(d["indices"])==n
    assert d["observed_component_estimates"]
    assert d["A"].shape[1]==4
    assert d["A"].shape[0]>len(d["X"])


def test_conditional_innovations_are_not_new_independent_source_blocks():
    d=study.operator_for_original_design(0,24,"ordinary_independent")
    r=study.simulate(d)
    assert r["conditional_draws"]==128
    assert not r["extra_draws_are_new_independent_source_designs"]
    assert not r["inference_qualified"]
    for label in study.COMPONENTS:
        assert 0<=r["conditional_zero_counts"][label]<=128
        lo,hi=r["conditional_zero_wilson_95pct"][label]
        assert lo<=r["conditional_zero_counts"][label]/128<=hi
    assert r["population_component_recovery_max_relative_error"]<5e-8


def test_predeclared_frozen_designs_and_failure_summary():
    assert study.FROZEN_BLOCKS==(0,7)
    assert study.FROZEN_SIZES==(24,96)
    assert study.CONDITIONAL_DRAWS==128
    assert study.EXPECTED==8
    assert study.DRAW_SEED!=r23.MASTER_SEED
    case=study.simulate(study.operator_for_original_design(0,24,"ordinary_independent"))
    summary=study.summary([case])
    assert summary["new_independent_source_designs"]==0
    assert summary["new_conditional_innovation_vectors"]==128
    assert summary["completed_designs"]==1
    assert summary["changes_original_R23_results"] is False
    assert summary["pointwise_coverage_qualified"] is False
    assert not summary["release_authorized"]
