"""R36 true boundary source, heldout data split and profile statistic contracts."""
import numpy as np
import pytest

from scripts import run_w3_r36_split_null_profile_calibration as r36
from scripts import run_w3_r16_leverage_covariance_factorial as r16


@pytest.mark.parametrize("support",r36.SUPPORT)
def test_true_zero_source_preserves_other_gaussian_primitives_exactly(support):
    zero=r36.source(0,support,"zero_slope")
    positive=r36.source(0,support,"positive_slope")
    for a,b in zip(zero[1].time,positive[1].time):
        np.testing.assert_array_equal(a,b)
    np.testing.assert_array_equal(zero[2],positive[2])
    np.testing.assert_array_equal(zero[3],positive[3])
    np.testing.assert_array_equal(zero[4],positive[4])
    for curve,(a,b,t) in enumerate(zip(
            zero[1].values,positive[1].values,zero[1].time)):
        who=int(zero[3][curve])
        x=float(zero[2][curve])
        random_slope=(r16.SIGMA_RANDOM_SLOPE*
            positive[0]["participant_slope"][who,0,0]*
            x*(1+.25*t[:,None]))
        np.testing.assert_allclose(
            b-a,random_slope,rtol=0,atol=2e-13)
    assert zero[0] is None # rebuilt original observations, no latent oracle attached


def test_null_grid_calibration_is_strictly_heldout_and_monotone():
    assert r36.MASTER_SEED!=202610163535
    assert r36.BLOCKS==16 and r36.N_CALIBRATION==8
    assert r36.PLANNED_SOURCE_CASES==48
    assert r36.PLANNED_GRID_OPTIMIZATIONS==336
    assert r36.GRID[0]==0.
    assert len(r36.GRID)==7
    x=r36.frozen_threshold([0,0,.01,.03,.2,.5,.7,1.2])
    assert x==1.2
    with pytest.raises(ValueError,match="eight"):
        r36.frozen_threshold([0,.1])
    with pytest.raises(ValueError,match="calibration"):
        r36.evaluate(0,"ordinary_dependent","positive_slope")
    for block in range(16):
        state="calibration" if block<8 else "heldout"
        assert state==("calibration" if block<r36.N_CALIBRATION else "heldout")


def test_exact_zero_statistic_and_diagnostic_not_chisquare():
    row=r36.evaluate(0,"ordinary_dependent","zero_slope")
    assert row["source_generated"],row["source_error"]
    assert row["reml_status"] in ("ok","failed","nonconverged")
    assert row["calibration_is_for_fixed_grid_statistic_only"]
    assert not row["release_authorized"]
    if row["profile_status"]=="complete":
        assert len(row["profile_points"])==7
        assert row["profile_points"][0]["fixed_slope_variance_is_exact_zero"]
        assert row["grid_statistic"]>=0
        min_nll=min(q["restricted_negative_loglik"] for q in row["profile_points"])
        nll0=row["profile_points"][0]["restricted_negative_loglik"]
        np.testing.assert_allclose(row["grid_statistic"],2*(nll0-min_nll),
                                   rtol=0,atol=2e-7)
    report=r36.summarize([row])
    assert report["recorded_original_source_cases"]==1
    assert report["missing_source_cases"]==47
    assert report["cells"]["ordinary_dependent"]["threshold_unavailable_due_to_failed_calibration"]
    assert report["no_standard_chisquare_or_mixture_reference_used"]
    assert not report["nominal_type_i_error_qualified"]
    assert not report["nuisance_adjusted_regression_CI_qualified"]


def test_failed_calibration_cannot_silently_set_nominal_threshold():
    # Partial/failed calibration must not fabricate an observed 90th quantile.
    a=r36.evaluate(0,"ordinary_dependent","zero_slope")
    b=dict(a,block=1,profile_status="incomplete",profile_points=[])
    report=r36.summarize([a,b])
    c=report["cells"]["ordinary_dependent"]
    assert c["null_calibration_independent_blocks"]==2
    assert c["empirical_90pct_grid_statistic_threshold"] is None
    assert c["threshold_unavailable_due_to_failed_calibration"]
    assert not report["release_authorized"]
