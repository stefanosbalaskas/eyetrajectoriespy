"""R48 original source, oracle separation, fitted REML and CR2 refusals."""
import numpy as np
import pytest

from scripts import run_w3_r16_leverage_covariance_factorial as r16
from scripts import run_w3_r32_reml_plugin_cr2_feasibility as r32
from scripts import run_w3_r47_independent_pointwise_audit as r47
from scripts import run_w3_r48_independent_fitted_cr2 as r48


def test_prespecified_independent_denominators_and_no_release_gate():
    assert r48.MASTER_SEED!=r47.SOURCE_SEED
    assert r48.BLOCKS==128
    assert r48.PARTICIPANTS==24
    assert r48.SUPPORT==("ordinary_dependent","extreme_dependent")
    assert r48.PLANNED_SOURCES==256
    assert r48.PLANNED_TARGETS==512
    assert r48.PLANNED_INTERVALS==1024
    assert r48.TARGETS==(
        "known_source_covariance","fitted_REML_observed_covariance")
    assert r48.REFERENCES==(
        "conditional_satterthwaite","participant_gminus1")


def test_new_primitive_independence_and_paired_leverage():
    a=r48.original_source(0,r48.SUPPORT[0])
    extreme=r48.original_source(0,r48.SUPPORT[1])
    another=r48.original_source(1,r48.SUPPORT[0])
    prior=r47.generating_source(0)
    np.testing.assert_array_equal(
        a[0]["participant_intercept"],
        extreme[0]["participant_intercept"])
    assert not np.array_equal(
        a[0]["participant_intercept"],
        another[0]["participant_intercept"])
    assert not np.array_equal(
        a[0]["participant_intercept"],
        prior[0]["participant_intercept"])
    # Predictor entries are repeated by native trials, so use the original
    # participant ID rather than assuming the second array row is person 1.
    assert a[2][np.flatnonzero(a[3]==0)[0]] != extreme[2][
        np.flatnonzero(extreme[3]==0)[0]]
    assert extreme[2][np.flatnonzero(extreme[3]==0)[0]]==pytest.approx(3.)
    assert extreme[2][np.flatnonzero(extreme[3]==1)[0]]==pytest.approx(-2.5)
    with pytest.raises(ValueError,match="outside"):
        r48.original_source(128,r48.SUPPORT[0])


def test_generating_projected_truth_separate_from_observed_REML_y():
    source=r48.original_source(0,r48.SUPPORT[0])
    X,y,w,g,t,tr,x,c,truth,raw_truth=r48.native_data(source)
    assert y.shape[0]==len(g)==len(t)==len(tr)==len(x)
    assert X.shape[1]==len(c)
    assert truth==pytest.approx(raw_truth,abs=1e-5)
    oracle=r32.known_gaussian_blocks(
        g,t,tr,x,w,r48.WORKING_FAMILY)
    assert len(oracle)==24
    assert all(np.linalg.eigvalsh(b).min()>0 for b in oracle)
    assert not hasattr(source[1],"truth_satterthwaite")


def test_oracle_AND_fitted_target_execute_same_fixed_source():
    row=r48.evaluate(0,r48.SUPPORT[0])
    assert row["source_status"]=="ok",row["source_error"]
    assert len(row["targets"])==2
    assert row["targets"][0]["target"]==r48.TARGETS[0]
    assert row["targets"][1]["target"]==r48.TARGETS[1]
    assert len(row["targets"][0]["intervals"])==2
    assert len(row["targets"][1]["intervals"])==2
    if row["targets"][1]["status"]=="accepted":
        assert row["nuisance_fit"]["fitted_from_observed_y_not_oracle"]
        assert row["nuisance_fit"][
            "no_global_optimum_or_physical_KKT_certificate"]
        assert not row["targets"][1][
            "nuisance_estimation_uncertainty_adjusted"]
    partial=r48.summarize([row])
    assert partial["recorded_source_cases"]==1
    assert partial["planned_source_cases"]==256
    assert partial["recorded_interval_records"]==4
    assert partial["90pct_pointwise_CR2_qualification"] is False
    assert partial["release_authorized"] is False


def test_unavailable_target_remains_refused_with_both_inclusion_slots():
    miss=r48.failed(r48.TARGETS[1],"unreliable source","test_refusal")
    assert miss["status"]=="refused"
    assert len(miss["intervals"])==2
    assert all(x["truth_included"] is False for x in miss["intervals"])
    assert not miss["nuisance_estimation_uncertainty_adjusted"]


def test_independent_mc_bounds_and_source_deduplication():
    lo,hi=r48.wilson(114,128)
    assert lo<114/128<hi
    with pytest.raises(ValueError):
        r48.wilson(-1,128)
    bad={"block":0,"support":r48.SUPPORT[0],
         "source_status":"failed","nuisance_fit":{"status":"failed"},
         "targets":[
             r48.failed(r48.TARGETS[0],"source"),
             r48.failed(r48.TARGETS[1],"source")]}
    report=r48.summarize([bad])
    assert report["planned_target_evaluations"]==512
    assert report["recorded_interval_records"]==4
    assert not report["complete_failure_inclusive_numerical_ledger"]
    assert not report["90pct_simultaneous_function_band_qualification"]
    assert report["fitted_nuisance_sampling_uncertainty_NOT_accounted_in_Sat_df"]
    with pytest.raises(ValueError,match="duplicated"):
        r48.summarize([bad,bad])


def test_target_sensitivity_is_not_conflated_with_calibrated_CR2():
    fit={
        "cr2_se":.2,"satterthwaite_df":9.,
        "point":.1,"clusters":24,
        "max_normalized_product_condition":100.,
        "max_relative_adjustment_identity_error":1e-10,
    }
    oracle=r48.target_intervals(r48.TARGETS[0],fit,.0)
    plugin=r48.target_intervals(r48.TARGETS[1],fit,.0)
    assert oracle["status"]=="accepted" and plugin["status"]=="accepted"
    assert oracle["intervals"][0]["truth_included"]
    assert plugin["intervals"][0]["truth_included"]
    assert all(v["reference"] in r48.REFERENCES
               for v in oracle["intervals"])
    assert not plugin["nuisance_estimation_uncertainty_adjusted"]
