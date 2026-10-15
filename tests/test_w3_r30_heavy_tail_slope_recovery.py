"""R30 heavy-tailed random-slope covariance source and paired-fit contracts."""
import numpy as np
import pytest
from scipy.stats import t as student_t

from scripts import run_w3_r17_fresh_feasibility as fresh
from scripts import run_w3_r29_predictor_spread_recovery as r29
from scripts import run_w3_r30_heavy_tail_slope_recovery as r30


def source():
    return fresh.fresh_source(0,"ordinary_dependent",n=24,
        master_seed=r30.SOURCE_SEED,
        n_blocks=r30.INDEPENDENT_BLOCKS,max_n=max(r30.SIZES))


def test_same_gaussian_source_is_exact_baseline_control():
    original=source()
    expected=r29.rescaled_source(original,1.)
    actual=r30.source_for_law(original,"gaussian",1.)
    np.testing.assert_array_equal(actual[2],expected[2])
    for before,after,t_before,t_after in zip(
        expected[1].values,actual[1].values,
        expected[1].time,actual[1].time):
        np.testing.assert_array_equal(before,after)
        np.testing.assert_array_equal(t_before,t_after)


def test_standardized_student_t5_is_deterministic_finite_and_unit_variance():
    z=np.random.default_rng(202610153033).standard_normal(15000)
    changed=r30.primitive_slope_transformation(z,"standardized_t5")
    assert np.isfinite(changed).all()
    assert abs(np.mean(changed))<.06
    assert abs(np.var(changed)-1.)<.12
    assert not np.allclose(changed,z)
    assert abs(float(student_t.var(df=5))/(5/3)-1)<1e-12
    with pytest.raises(ValueError,match="unregistered"):
        r30.primitive_slope_transformation(z,"student_t_undefined")


def test_only_slope_primitive_changes_and_native_observation_grid_preserved():
    a=source()
    b=r30.source_for_law(a,"standardized_t5",2.)
    c=r30.source_for_law(a,"gaussian",2.)
    np.testing.assert_allclose(b[2],c[2],rtol=0,atol=0)
    np.testing.assert_array_equal(b[3],c[3])
    np.testing.assert_array_equal(b[4],c[4])
    for before,after in zip(b[1].time,c[1].time):
        np.testing.assert_array_equal(before,after)
    assert any(not np.array_equal(x,y) for x,y in zip(b[1].values,c[1].values))
    assert b[1].provenance["interpolation_performed"] is False


@pytest.mark.parametrize("law",r30.SLOPE_LAWS)
def test_observed_only_estimators_record_failures_and_diagnostics(law):
    out=r30.evaluate(0,24,"ordinary_dependent",2.,law)
    assert out["source_generated"],out["source_error"]
    assert out["covariance_component_truth_passed_to_estimators"] is False
    assert not out["coverage_evaluated"]
    assert not out["release_authorized"]
    assert out["matched_working_covariance_family"]=="predictor_scaled_slope"
    for method in r30.METHODS:
        result=out["methods"][method]
        assert result["status"] in ("ok","failed","nonconverged")
        if result["status"]=="ok":
            assert len(result["postfit_component_relative_errors"])==4
            assert np.isfinite(result["postfit_slope_relative_error"])


def test_require_all_counterfactual_cases_for_paired_stress_contrast():
    one=r30.evaluate(0,24,"ordinary_independent",1.,"gaussian")
    test=r30.paired_stress_contrast(
        [one],24,"ordinary_independent","gaussian_reml")
    assert test["complete_paired_blocks"]==0
    assert test["whole_block_bootstrap_95pct"] is None
    summary=r30.summarize([one])
    assert summary["planned_cases"]==192
    assert summary["recorded_cases"]==1
    assert summary["missing_cases"]==191
    assert summary["independent_generating_blocks"]==12
    assert summary["no_confidence_interval_coverage_computed"]
    assert not summary["release_authorized"]
