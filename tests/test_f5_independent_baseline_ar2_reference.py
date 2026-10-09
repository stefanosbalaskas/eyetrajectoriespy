"""Independent AR2 baseline dependence contract, null reference and fail-closed checks."""
from __future__ import annotations
import numpy as np
import pytest

from eyetrajectoriespy.research.functional_changepoints_baseline_ar2 import (
    infer_ordered_functional_changepoint_baseline_ar2,
    _ar2_coefficients,_stationary,_simulate,
)
from eyetrajectoriespy.types import TrajectorySet
from scripts.run_f5_unknown_phi_independent_baseline_validation import _series


def test_true_ar2_baseline_and_independent_test_give_finite_exploratory_null():
    train=_series(1193,"ar2_misspecified",n=80,truth="null",prefix="base-1193")
    tested=_series(1194,"ar2_misspecified",n=36,truth="null",prefix="test-1194")
    fit=infer_ordered_functional_changepoint_baseline_ar2(
        tested,independent_stationary_baseline=train,
        n_parameter_bootstrap=99,n_null_simulations=99,random_state=771)
    assert len(fit.null_statistics)==99
    assert 0<fit.p_value_experimental<=1
    assert len(fit.evidence["estimated_ar2_coefficient"])==2
    assert fit.evidence["nuisance_estimated_from_test_series"] is False
    assert fit.evidence["n_valid_parameter_draws"]>=70
    assert not fit.evidence["unknown_dependence_inference_qualified"]
    assert not fit.evidence["release_authorized"]
    again=infer_ordered_functional_changepoint_baseline_ar2(
        tested,independent_stationary_baseline=train,
        n_parameter_bootstrap=99,n_null_simulations=99,random_state=771)
    np.testing.assert_array_equal(fit.null_statistics,again.null_statistics)
    assert fit.p_value_experimental==again.p_value_experimental


def test_stationarity_guard_and_pooled_AR2_coefficients():
    assert _stationary(np.array([.64,.24]))
    assert _stationary(np.array([.8,0]))
    assert not _stationary(np.array([1.02,0]))
    assert not _stationary(np.array([.5,.9]))
    assert not _stationary(np.array([np.nan,0]))
    x=np.random.default_rng(31).normal(size=(50,6,2))
    assert _ar2_coefficients(x).shape==(2,)
    with pytest.raises(ValueError,match="rank-deficient"):
        _ar2_coefficients(np.ones((50,5,2)))
    with pytest.raises(ValueError,match="stationary"):
        _simulate(x,x[2:],np.array([1.1,0]),36,np.random.default_rng(2))


def test_ar2_rejects_duplicate_baseline_participants_and_invalid_counts():
    train=_series(402,"ar2_misspecified",n=80,truth="null",prefix="T")
    tested=_series(403,"ar2_misspecified",n=36,truth="null",prefix="T")
    with pytest.raises(ValueError,match="disjoint"):
        infer_ordered_functional_changepoint_baseline_ar2(
            tested,independent_stationary_baseline=train,
            n_parameter_bootstrap=99,n_null_simulations=99)
    tested=_series(403,"ar2_misspecified",n=36,truth="null",prefix="B")
    with pytest.raises(ValueError,match="99"):
        infer_ordered_functional_changepoint_baseline_ar2(
            tested,independent_stationary_baseline=train,
            n_parameter_bootstrap=98,n_null_simulations=99)
