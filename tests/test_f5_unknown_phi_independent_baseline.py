"""Finite-baseline nuisance uncertainty and F5 no-test-leakage contracts."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import pytest

from eyetrajectoriespy.research.functional_changepoints_baseline_ar1 import (
    infer_ordered_functional_changepoint_baseline_ar1 as unknown_phi,
    _baseline_phi_ols,
)
from eyetrajectoriespy.types import TrajectorySet
from scripts.run_f5_unknown_phi_independent_baseline_validation import _series,SCENARIOS


def test_unknown_phi_is_fitted_only_on_distinct_stationary_baseline():
    baseline=_series(17,"ar1_strong",n=80,truth="null",prefix="baseline")
    tested=_series(19,"ar1_strong",n=36,truth="null",prefix="test")
    assert abs(_baseline_phi_ols(baseline.values))<.98
    fit=unknown_phi(tested,independent_stationary_baseline=baseline,
        n_parameter_bootstrap=99,n_null_simulations=99,random_state=17)
    assert 0<fit.p_value_experimental<=1
    assert len(fit.null_statistics)==99
    assert 6<=fit.split_index<=30
    assert fit.evidence["unknown_phi_not_oracle"]
    assert fit.evidence["parameter_fitted_on_test_series"] is False
    assert fit.evidence["innovation_samples_from_test_series"] is False
    assert fit.evidence["baseline_n_ordered_curves"]==80
    assert fit.evidence["test_n_ordered_curves"]==36
    assert not fit.evidence["nominal_false_positive_calibration_qualified"]
    assert not fit.evidence["release_authorized"]
    assert not fit.evidence["scientific_inference_qualified"]
    q=fit.evidence["approximate_phi_uncertainty_quantiles_025_50_975"]
    assert len(q)==3 and -1<q[0]<=q[1]<=q[2]<1


def test_strict_determinism_and_never_oracle_phi():
    baseline=_series(312,"ar1_weak",n=60,truth="null",prefix="B")
    tested=_series(313,"ar1_weak",n=36,truth="one_break",prefix="T")
    kw=dict(independent_stationary_baseline=baseline,
            n_null_simulations=99,n_parameter_bootstrap=99,
            random_state=393)
    a=unknown_phi(tested,**kw)
    b=unknown_phi(tested,**kw)
    np.testing.assert_array_equal(a.null_statistics,b.null_statistics)
    assert a.p_value_experimental==b.p_value_experimental
    assert a.evidence["baseline_pooled_phi_ols"]==b.evidence["baseline_pooled_phi_ols"]


def test_baseline_metadata_and_disjoint_identity_fail_closed():
    baseline=_series(212,"iid",n=80,truth="null",prefix="B")
    tested=_series(213,"iid",n=36,truth="null",prefix="T")
    common=dict(independent_stationary_baseline=baseline,
                n_null_simulations=99,n_parameter_bootstrap=99)
    altered=TrajectorySet(
        time=tested.time,values=tested.values,curve_ids=tested.curve_ids,
        dimension_names=tested.dimension_names,
        coordinate_system=tested.coordinate_system,time_unit=tested.time_unit,
        metadata=pd.DataFrame({"participant_id":[f"B-{i}" for i in range(len(tested.values))]}))
    with pytest.raises(ValueError,match="disjoint"):
        unknown_phi(altered,**common)
    with pytest.raises(ValueError,match="99"):
        unknown_phi(tested,independent_stationary_baseline=baseline,
                    n_parameter_bootstrap=90,n_null_simulations=99)
    with pytest.raises(ValueError,match="99"):
        unknown_phi(tested,independent_stationary_baseline=baseline,
                    n_parameter_bootstrap=99,n_null_simulations=90)
    short=_series(9,"iid",n=18,truth="null",prefix="short")
    with pytest.raises(ValueError,match="at least 24"):
        unknown_phi(tested,independent_stationary_baseline=short,
                    n_parameter_bootstrap=99,n_null_simulations=99)
    with pytest.raises(ValueError,match="invalid min_segment"):
        unknown_phi(tested,**common,min_segment=35)


def test_actual_AR2_and_heavy_tail_misspecification_not_mislabeled_as_qualified():
    assert SCENARIOS["ar2_misspecified"]["kind"]=="ar2"
    assert SCENARIOS["heavy_tail_ar1"]["heavy_tail"]
    for s in ("ar2_misspecified","heavy_tail_ar1"):
        baseline=_series(27,s,n=80,truth="null",prefix=f"b{s}")
        tested=_series(29,s,n=36,truth="null",prefix=f"t{s}")
        result=unknown_phi(tested,independent_stationary_baseline=baseline,
               n_parameter_bootstrap=99,n_null_simulations=99,random_state=77)
        assert result.evidence["non_AR1_dependence_qualified"] is False
        assert result.evidence["baseline_transferability_qualified"] is False
        assert np.isfinite(result.null_statistics).all()
