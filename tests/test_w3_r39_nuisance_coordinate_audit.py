"""R39 observed-data nuisance reparameterization and subtraction contracts."""
import numpy as np
import pytest

from scripts import run_w3_r39_nuisance_coordinate_audit as r39


def test_frozen_study_dimensions_and_no_pseudo_replication():
    assert r39.REUSED_MASTER_SEED == 202610163737
    assert r39.REUSED_BLOCK == 2
    assert r39.PLANNED_CASES == 4
    assert r39.RATIOS == (0., 0.1, 0.75, 1.75, 3.5)
    assert r39.PLANNED_FITS == 240
    assert len(r39.SEEDS) == 3
    assert len(r39.COORDINATES) == len(r39.OFFSETS) == 2


@pytest.mark.parametrize("slope",[0.,0.75])
def test_fixed_gaussian_reml_invariance_under_coordinate_and_offset(slope):
    prepared=r39.source_and_prepared(
        "ordinary_dependent", "zero_slope"
    )
    reference=1.
    logs=np.array([-.8,-3.,-1.2])
    ratios=np.exp(logs)
    f_log,g_log=r39.fixed_slope_parameter_objective(
        logs,prepared,reference,slope,"log_variances"
    )
    f_linear,g_linear=r39.fixed_slope_parameter_objective(
        ratios,prepared,reference,slope,"linear_variance_ratios"
    )
    np.testing.assert_allclose(f_log,f_linear,atol=1e-8,rtol=1e-11)
    np.testing.assert_allclose(g_log,g_linear*ratios,atol=1e-6,rtol=1e-8)
    for coordinate,p in (
        ("log_variances",logs),
        ("linear_variance_ratios",ratios),
    ):
        centered, gradient=r39.fixed_slope_parameter_objective(
            p,prepared,reference,slope,coordinate,common_center=f_log
        )
        direct, original_gradient=r39.fixed_slope_parameter_objective(
            p,prepared,reference,slope,coordinate,common_center=0.
        )
        assert centered == pytest.approx(0.,abs=1e-7)
        assert direct == pytest.approx(f_log,abs=1e-8)
        np.testing.assert_allclose(gradient,original_gradient,atol=1e-10)


def test_log_vs_linear_gradient_finite_difference_interior():
    prepared=r39.source_and_prepared(
        "ordinary_dependent","zero_slope"
    )
    log_r=np.array([-.75,-2.5,-1.])
    r=np.exp(log_r)
    _,gradient=r39.fixed_slope_parameter_objective(
        r,prepared,1.,0.1,"linear_variance_ratios"
    )
    h=1e-5
    numeric=[]
    for j in range(3):
        a=r.copy();b=r.copy()
        a[j]+=h;b[j]-=h
        x,_=r39.fixed_slope_parameter_objective(
            a,prepared,1.,0.1,"linear_variance_ratios"
        )
        y,_=r39.fixed_slope_parameter_objective(
            b,prepared,1.,0.1,"linear_variance_ratios"
        )
        numeric.append((x-y)/(2*h))
    np.testing.assert_allclose(gradient,numeric,atol=2e-3,rtol=1e-3)


def test_invalid_coordinate_and_bounds_fail_without_silent_clipping():
    prepared=r39.source_and_prepared(
        "ordinary_dependent","zero_slope"
    )
    with pytest.raises(ValueError):
        r39.fixed_slope_parameter_objective(
            np.ones(3),prepared,1.,0.,"unknown_coordinate"
        )
    with pytest.raises(ValueError):
        r39.fixed_slope_parameter_objective(
            np.array([0.,1.,1.]),prepared,1.,0.,"linear_variance_ratios"
        )
    with pytest.raises(ValueError):
        r39.fixed_slope_parameter_objective(
            np.array([r39.LOWER_LOG_RATIO-1.,0.,0.]),
            prepared,1.,0.,"log_variances"
        )


def test_failure_inclusive_summary_and_closed_release_gates():
    rows=[{
        "support":"ordinary_dependent","true_state":"zero_slope",
        "source_status":"failed","profiles":[],
    }]
    result=r39.summarize(rows)
    assert result["missing_source_cases"] == 3
    assert result["failed_source_cases"] == 1
    assert result["recorded_nuisance_fits"] == 0
    assert result["independent_new_generating_blocks"] == 0
    assert result["no_statistical_calibration_or_typeI_power"]
    assert result["no_working_covariance_CR2_coefficient_intervals"]
    assert not result["release_authorized"]
