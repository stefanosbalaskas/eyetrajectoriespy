"""Original R18 Gaussian primitive innovation identities and frozen coverage."""
import numpy as np
import pytest

from scripts import run_w3_r19_primitive_gaussian_oracle as r19
from scripts import run_w3_r18_independent_gaussian_oracle as original


@pytest.mark.parametrize("support,model",[
    ("ordinary_independent","legendre5"),
    ("ordinary_independent","cubic_spline13"),
    ("ordinary_dependent","legendre5"),
    ("ordinary_dependent","cubic_spline13"),
])
def test_frozen_original_source_primitive_noise_exact(support,model):
    x=r19.diagnose(0,support,model)
    y=original.evaluate(0,support,model)
    assert x["status"]=="ok",x["exception"]
    assert y["status"]=="ok",y["exception"]
    np.testing.assert_allclose(x["z_projected"],y["gaussian_error_z_projected"],atol=2e-8,rtol=0)
    np.testing.assert_allclose(x["z_truth"],y["gaussian_error_z_continuous_truth"],atol=2e-8,rtol=0)
    assert x["reconstructed_error_delta"]<2e-8
    assert x["native_residual_error_delta"]<2e-8
    assert x["primitive_oracle_variance_difference"]<2e-7
    for outcome in ("truth_included_normal","projection_included_normal",
                    "truth_included_tGminus1","projection_included_tGminus1"):
        assert x[outcome] == y[outcome]
    frozen=x["conditional_fixed_design_gaussian_draws"]
    assert frozen["draws"]==r19.DRAW_PER_FIXED_DESIGN
    assert 0.85<frozen["sd_standardized"]<1.15
    assert frozen["conditional_simulation_is_new_independent_source_blocks"] is False


def test_fixed_original_block_contract_and_failure_accounting():
    assert r19.FROZEN_BLOCKS==(0,37,191)
    assert r19.DRAW_PER_FIXED_DESIGN==1024
    a=r19.diagnose(0,"ordinary_independent","legendre5")
    b=dict(a,block=1,status="failed",exception={"type":"Fixture","message":"retained"})
    summary=r19.summarize([a,b])
    assert summary["planned_original_source_cases"]==768
    assert summary["recorded_original_source_cases"]==2
    assert summary["completed_original_source_cases"]==1
    assert summary["failed_original_source_cases"]==1
    assert summary["missing_original_source_cases"]==766
    assert not summary["original_R18_coverage_contract_all_four_cells_exact"]
    assert summary["original_R18_contract_mismatches"]
    assert not summary["production_release_ready"]
