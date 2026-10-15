"""R26 independent Gaussian REML vs NNLS reliability contracts."""
import numpy as np
import pytest
from scripts import run_w3_r26_independent_reml_recovery as r26
from scripts import run_w3_r17_fresh_feasibility as fresh
from scripts import run_w3_r25_reml_nnls_pilot as r25


def test_independent_research_seed_and_native_nested_participants():
    assert r26.SOURCE_SEED!=r25.MASTER_SEED
    assert r26.BLOCKS==16
    assert r26.SIZES==(24,48,96)
    assert r26.EXPECTED==384
    a=fresh.fresh_source(0,"ordinary_independent",n=24,
        master_seed=r26.SOURCE_SEED,n_blocks=r26.BLOCKS,max_n=96)
    b=fresh.fresh_source(0,"ordinary_independent",n=96,
        master_seed=r26.SOURCE_SEED,n_blocks=r26.BLOCKS,max_n=96)
    for ta,tb,va,vb in zip(a[1].time,b[1].time,a[1].values,b[1].values):
        np.testing.assert_array_equal(ta,tb)
        np.testing.assert_array_equal(va,vb)
    assert not a[1].provenance["interpolation_performed"]


@pytest.mark.parametrize("support,family",[
 ("ordinary_independent","shared_slope"),
 ("ordinary_dependent","predictor_scaled_slope"),
 ("extreme_independent","predictor_scaled_slope"),
])
def test_estimates_from_observed_sources_and_truth_only_postfit(support,family):
    record=r26.evaluate(0,24,support,family)
    assert record["source_generated"],record.get("source_failure")
    assert record["source_truth_provided_to_estimators"] is False
    assert not record["estimated_target_inference_qualified"]
    assert not record["release_authorized"]
    for method in r26.METHODS:
        item=record["method_results"][method]
        assert item["status"] in ("ok","failed","nonconverged")
        if item["status"]=="ok":
            for k in r26.COMPONENTS:
                assert item["component_estimates"][k]>=0
                if record["matched_generating_covariance_shape_postfit"]:
                    assert np.isfinite(item["relative_errors_on_matched_source_only"][k])
                    assert isinstance(
                        item["less_than_5pct_true_component_on_matched_source_only"][k],bool)
                else:
                    assert item["relative_errors_on_matched_source_only"] is None


def test_record_all_cases_including_failed_estimator_results():
    one=r26.evaluate(0,24,"ordinary_independent","shared_slope")
    two=dict(one,working_family="predictor_scaled_slope",method_results={
        "leverage_adjusted_nnls":{"status":"failed"},
        "gaussian_reml":{"status":"nonconverged"}})
    result=r26.summarize([one,two])
    assert result["recorded_cases"]==2
    assert result["missing_cases"]==382
    assert result["fit_failures_by_method"]["gaussian_reml"]>=1
    assert result["pointwise_interval_coverage_evaluated"] is False
    assert not result["public_api_authorized"]
    assert not result["release_authorized"]
    assert not result["paired_source_bootstrap"]["estimator_winner_selected"]


def test_block_bootstrap_not_384_independent_replicates():
    assert r26.BOOTSTRAP_DRAWS==2500
    assert r26.COMMON_TRUE_VARIANCE_RATIO==.05
    result=r26.paired_source_bootstrap([])
    assert not result["complete_pairing_across_all_matched_source_strata"]
    assert result["matched_pair_model_cases"]==0
    assert result["expected_matched_model_cases"]==192
    assert result["resamples_independent_generating_blocks_only"]
