"""R40 independent-source and failure-inclusive Gaussian REML numerical contracts."""
import numpy as np
import pytest

from scripts import run_w3_r16_leverage_covariance_factorial as r16
from scripts import run_w3_r37_continuous_boundary_reml as r37
from scripts import run_w3_r40_fresh_source_nuisance as r40


def test_prespecified_independent_block_count_and_exact_names():
    assert r40.MASTER_SEED not in (r37.MASTER_SEED, 202610163939)
    assert r40.BLOCKS == 8
    assert r40.PLANNED_CASES == 32
    assert r40.PLANNED_PROFILE_CELLS == 64
    assert r40.PLANNED_FITS == 384
    assert r40.SLOPE_RATIOS == (0., .75)
    assert len(r40.SEED_RATIOS) == 3
    assert set(r40.METHODS) == {
        "log_variances", "linear_variance_ratios"
    }
    assert r40.OBJECTIVE_OFFSET == "raw_NLL"


def test_new_independent_primitive_blocks_and_paired_exact_zero_source():
    positive = r40.independent_source(
        0, "extreme_dependent", "positive_slope"
    )
    null = r40.independent_source(
        0, "extreme_dependent", "zero_slope"
    )
    second = r40.independent_source(
        1, "extreme_dependent", "positive_slope"
    )
    assert positive[0]["block"] == 0
    assert second[0]["block"] == 1
    assert not np.array_equal(
        positive[0]["sensor_noise"], second[0]["sensor_noise"]
    )
    assert null[0] is None
    np.testing.assert_array_equal(positive[2],null[2])
    np.testing.assert_array_equal(positive[3],null[3])
    for curve in range(min(4,len(positive[1].time))):
        time = positive[1].time[curve]
        who = int(positive[3][curve])
        x = float(positive[2][curve])
        slope_draw = positive[0]["participant_slope"][who,0,0]
        expected = (r16.SIGMA_RANDOM_SLOPE*slope_draw*x
                    *(1.+.25*time[:,None]))
        np.testing.assert_allclose(
            positive[1].values[curve]-null[1].values[curve],
            expected,rtol=1e-10,atol=1e-10
        )
    with pytest.raises(ValueError,match="outside frozen"):
        r40.independent_source(8,"extreme_dependent","zero_slope")


def test_observed_only_reference_variance_and_model_preparation():
    prepared,reference,points = r40.prepare_case(
        0,"ordinary_dependent","zero_slope"
    )
    assert reference>0 and np.isfinite(reference)
    assert points>0 and len(prepared)==r40.PARTICIPANTS
    for Z,y,kernels in prepared:
        assert Z.shape[0]==len(y)
        assert len(kernels)==4


def test_no_favorable_case_selection_on_unfinished_source():
    partial=[{
        "source_block":0,"source_support":"ordinary_dependent",
        "true_slope_state":"zero_slope","source_status":"failed",
        "profiles":[],
    }]
    s=r40.summarize(partial)
    assert s["recorded_source_cases"] == 1
    assert s["missing_source_cases"] == 31
    assert s["source_errors"] == 1
    assert s["recorded_optimizer_fits"] == 0
    assert not s["failure_inclusive_numerical_gate_passed"]
    assert not s["public_API_or_release_authorized"]
    assert s["independent_primitive_generating_blocks"] == 8
    assert s["global_optimization_certified"] is False


def test_one_pair_is_retained_even_when_solver_disagrees():
    row=r40.evaluate(0,"ordinary_dependent","zero_slope")
    assert row["source_status"]=="ok",row["source_error"]
    assert len(row["profiles"])==2
    assert all(len(p["fits"])==6 for p in row["profiles"])
    for point in row["profiles"]:
        assert len({(x["parameterization"],x["nuisance_start"])
                    for x in point["fits"]})==6
        assert point["successful_fit_count"] + (
            point["failed_or_nonconverged_count"])==6
    single=r40.summarize([row])
    assert single["recorded_optimizer_fits"]==12
    assert single["missing_source_cases"]==31
    assert not single["failure_inclusive_numerical_gate_passed"]
