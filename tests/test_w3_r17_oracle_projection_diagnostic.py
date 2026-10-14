"""R17 original-source oracle target audit is descriptive and immutable."""
import numpy as np
import pytest
from scripts import run_w3_r17_oracle_projection_diagnostic as diag
from scripts import run_w3_r17_independent_96block_calibration as original


@pytest.mark.parametrize("n,support,model",[
    (24,"extreme_dependent","legendre5"),
    (48,"extreme_independent","cubic_spline13"),
    (96,"ordinary_independent","legendre5"),
    (96,"ordinary_dependent","cubic_spline13"),
])
def test_source_truth_inclusion_identical_to_original_R17(n,support,model):
    x=diag.diagnose(0,n,support,model)
    y=original.run_case(0,n,support,model,"correct")
    assert x["status"]=="ok",x["error"]
    assert y["status"]=="ok",y["error"]
    np.testing.assert_allclose(x["point_estimate"],y["point"],atol=1e-10)
    np.testing.assert_allclose(x["source_midpoint_truth"],y["truth"],atol=1e-10)
    np.testing.assert_allclose(x["oracle_se"],y["cr2_se"]*y["cr2_to_oracle_se"]**-1,
                               rtol=1e-8)
    assert x["oracle_truth_included_t"]==y["coverage"]["oracle_tGminus1"]
    np.testing.assert_allclose(
        x["estimated_point_minus_truth_oracle_se_units"],
        x["estimated_point_minus_projection_oracle_se_units"]+
        x["projection_displacement_oracle_se_units"],rtol=1e-10,atol=1e-10)
    assert x["projection_target_is_new_primary_estimand"] is False


def test_projection_coverage_summary_and_failure_tracking():
    ok=diag.diagnose(0,24,"ordinary_independent","legendre5")
    assert ok["status"]=="ok"
    fail=dict(ok,block=1,status="failed",error={"type":"Fixture","message":"retained"})
    x=diag.summarize([ok,fail])
    assert x["recorded_source_model_diagnostics"]==2
    assert x["missing_source_model_diagnostics"]==2304-2
    assert x["failed_source_model_diagnostics"]==1
    assert x["changes_original_R17_coverage"] is False
    assert not x["production_release_ready"]


def test_identity_target_projection_is_exact_mean_displacement():
    x=diag.diagnose(0,48,"extreme_dependent","legendre5")
    assert x["status"]=="ok",x["error"]
    np.testing.assert_allclose(
        x["projection_minus_truth"],
        x["projection_displacement_oracle_se_units"]*x["oracle_se"],
        rtol=1e-11,atol=1e-11)
