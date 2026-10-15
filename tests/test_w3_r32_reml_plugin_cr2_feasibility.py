"""R32 known-vs-estimated Gaussian target CR2 exploratory inference contracts."""
import numpy as np
import pytest

from scripts import run_w3_r17_fresh_feasibility as fresh
from scripts import run_w3_r31_observation_process_recovery as loss
from scripts import run_w3_r32_reml_plugin_cr2_feasibility as study
from scripts.w3_r20_estimated_working_target import observed_weighted_rows


@pytest.mark.parametrize("support",study.SUPPORT)
def test_oracle_covariance_reconstruction_matches_independent_R17_source(support):
    original=fresh.fresh_source(0,support,n=24,
        master_seed=study.SOURCE_SEED,n_blocks=study.BLOCKS,max_n=96)
    X,y,w,g,Phi=fresh.prepare(original,study.BASIS)
    observed=(None,original[1],original[2],original[3],original[4],None)
    X2,y2,w2,g2,time,tr,x=observed_weighted_rows(observed,study.BASIS)
    np.testing.assert_allclose(X,X2,rtol=0,atol=0)
    np.testing.assert_allclose(y,y2,rtol=0,atol=0)
    np.testing.assert_allclose(w,w2,rtol=0,atol=0)
    np.testing.assert_array_equal(g,g2)
    family=("predictor_scaled_slope" if support.endswith("_dependent")
            else "shared_slope")
    blocks=study.known_gaussian_blocks(g2,time,tr,x,w2,family)
    for actual,reference in zip(blocks,Phi):
        np.testing.assert_allclose(actual,reference,rtol=5e-12,atol=2e-12)


def test_incomplete_oracle_covariance_matches_native_retained_blocks():
    original=fresh.fresh_source(0,"ordinary_dependent",n=24,
        master_seed=study.SOURCE_SEED,n_blocks=study.BLOCKS,max_n=96)
    retained,meta=loss._native_observation_transform(
        original,"time_mar_20",block=0,support="ordinary_dependent")
    X,y,w,g,time,trial,x=observed_weighted_rows(
        (None,retained[1],retained[2],retained[3],retained[4],None),
        study.BASIS)
    target=study.known_gaussian_blocks(
        g,time,trial,x,w,"predictor_scaled_slope")
    assert len(target)==24
    assert meta["retained_native_points"]<meta["original_native_points"]
    assert all(np.linalg.eigvalsh(p)[0]>0 for p in target)
    assert len(np.concatenate(retained[5]))==len(y)


@pytest.mark.parametrize("support,mode",[
    ("ordinary_independent","complete"),
    ("ordinary_dependent","time_mar_20"),
])
def test_source_truth_excluded_from_reml_and_result_status_preserved(support,mode):
    row=study.evaluate(0,24,support,mode)
    assert row["source_generated"],row["source_failure"]
    assert row["true_covariance_given_to_nuisance_estimator"] is False
    assert not row["pointwise_inference_qualified"]
    assert not row["simultaneous_functional_bands_qualified"]
    assert not row["release_authorized"]
    assert abs(row["mean_basis_projection_minus_original_focal"])<.5
    assert row["reml_nuisance_status"] in ("ok","nonconverged","failed")
    assert set(row["targets"])==set(study.TARGETS)
    for target in study.TARGETS:
        item=row["targets"][target]
        assert item["status"] in ("accepted","refused","nuisance_estimator_failed")
        assert not item["df_includes_covariance_estimation_uncertainty"]
        if item["status"]=="accepted":
            assert item["cr2_se"]>0
            assert item["conditional_satterthwaite_df"]>0
            assert isinstance(item["satterthwaite_truth_included"],bool)
            assert isinstance(item["t_gminus1_truth_included"],bool)


def test_stratum_reports_success_and_inclusion_separately():
    case=study.evaluate(0,24,"ordinary_independent","complete")
    report=study.summarize([case])
    assert report["planned_cases"]==128
    assert report["recorded_cases"]==1
    assert report["missing_cases"]==127
    assert report["conditional_on_success_inclusion_not_unconditional_coverage"]
    assert report["known_projected_estimand_not_raw_functional_slope"]
    assert report["nuisance_estimation_uncertainty_not_in_conditional_satterthwaite"]
    assert not report["pointwise_nominal_coverage_qualified"]
    assert not report["release_authorized"]
    item=report["strata"]["n24/ordinary_independent/complete"]["targets"]
    for target in study.TARGETS:
        x=item[target]
        assert x["computationally_accepted"]<=x["independent_original_blocks"]
        assert x["coverage_method_qualified"] is False


def test_wilson_boundaries_and_no_zero_division():
    assert study.wilson(0,0) is None
    for k in (0,1,8,16):
        low,high=study.wilson(k,16)
        assert 0<=low<=k/16<=high<=1
