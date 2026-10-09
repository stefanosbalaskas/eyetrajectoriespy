"""F5 baseline-duration study preserves pairing and unknown-dependence fail-closed gates."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

import numpy as np
import pytest

from eyetrajectoriespy.research.functional_changepoints_baseline_ar1 import (
    infer_ordered_functional_changepoint_baseline_ar1 as infer,
)
from scripts.run_f5_unknown_phi_independent_baseline_validation import _series
from scripts.run_f5_baseline_duration_nuisance_ablation import (
    _seed,study,BASELINE_LENGTHS,COEFFICIENT_POLICIES
)


def test_baseline_uncertainty_is_unchanged_and_plugin_is_explicit_ablation():
    baseline=_series(77,"ar1_strong",n=80,truth="null",prefix="B77")
    test=_series(79,"ar1_strong",n=36,truth="null",prefix="T79")
    kwargs=dict(independent_stationary_baseline=baseline,
        n_parameter_bootstrap=99,n_null_simulations=99,random_state=8)
    original=infer(test,**kwargs)
    explicit=infer(test,**kwargs,null_coefficient_policy="baseline_uncertainty")
    np.testing.assert_array_equal(original.null_statistics,explicit.null_statistics)
    assert original.p_value_experimental==explicit.p_value_experimental
    plugin=infer(test,**kwargs,null_coefficient_policy="baseline_plugin")
    assert plugin.evidence["null_coefficient_policy"]=="baseline_plugin"
    assert plugin.evidence["plugin_is_unqualified_nuisance_ablation"]
    assert plugin.evidence["parameter_fitted_on_test_series"] is False
    assert plugin.evidence["nominal_false_positive_calibration_qualified"] is False
    assert plugin.evidence["scientific_inference_qualified"] is False
    assert plugin.evidence["release_authorized"] is False
    assert not np.array_equal(original.null_statistics,plugin.null_statistics)
    with pytest.raises(ValueError,match="coefficient policy"):
        infer(test,**kwargs,null_coefficient_policy="oracle")


def test_study_baseline_and_test_seed_are_independent_and_held_fixed():
    seed=20261205
    test_id=_seed(seed,"ar1_strong","null",4,"test")
    assert test_id==_seed(seed,"ar1_strong","null",4,"test")
    for n in BASELINE_LENGTHS:
        baseline_id=_seed(seed,"ar1_strong","null",4,f"independent_baseline_length_{n}")
        assert test_id!=baseline_id
    assert len(COEFFICIENT_POLICIES)==2
    assert set(BASELINE_LENGTHS)=={40,80,160}


def test_small_fully_fitted_design_produces_two_ablation_variants_and_retains_gates():
    cases,evidence=study(null_replicates=2,alternative_replicates=2,
        bootstrap=99,phi_bootstrap=99,master_seed=17376,
        scenario_subset=("iid",))
    assert evidence["method_attempts"]==24
    assert evidence["independent_test_datasets"]==4
    assert evidence["same_test_curves_across_baseline_lengths"]
    assert evidence["same_baseline_between_policies"]
    assert evidence["same_null_bootstrap_random_stream_between_policies"]
    assert evidence["no_threshold_tuning"]
    assert not evidence["power_or_calibration_qualified"]
    assert not evidence["production_release_authorized"]
    assert len(evidence["scenario_results"])==12
    assert cases.groupby(["scenario","truth","replicate"]).size().eq(6).all()
    assert cases.groupby(["scenario","truth","replicate","n_baseline"]).test_seed.nunique().eq(1).all()
    assert cases.groupby(["scenario","truth","replicate","n_baseline"]).baseline_seed.nunique().eq(1).all()
    assert len(set(cases.test_seed))==4
    assert len(set(cases.baseline_seed))==12
    assert set(cases.policy)==set(COEFFICIENT_POLICIES)
    assert cases.calibrated_inference.eq(False).all()
    assert cases.status.isin(["ok","failed"]).all()
    assert not cases.loc[cases.status=="ok","p_value"].isna().any()
