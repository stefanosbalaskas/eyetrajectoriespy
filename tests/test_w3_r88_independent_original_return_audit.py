"""R88-A independent implementation contracts; real archive replay is mandatory CI."""
import numpy as np
import pytest

from scripts import audit_w3_r88_original_return_sensitivity_independent as independent
from scripts import run_w3_r88_return_sensitivity as original
from scripts import run_w3_r87_audit_return_nonresponse as r87


def test_independent_source_rebuild_seed_and_identity():
    assert independent.EXPECTED_ROWS == 1024
    assert independent.BLOCKS == 32
    assert independent.SOURCES == original.SOURCES
    assert independent.ORIGINAL_CHECKOUT == (
        "194d00a14ac35b85cf25864ed5e099d0c7ffb02c"
    )
    for config in independent.CONFIGS:
        X, Y, slopes = independent.replay_XY(
            0, config, "two_anchors", "predictor_heteroskedastic"
        )
        source_X, source_Y = original.new_source(0, config)
        np.testing.assert_array_equal(X, source_X)
        np.testing.assert_allclose(Y, source_Y, atol=1e-12, rtol=1e-12)
        assert independent.digest(Y) == r87.digest(source_Y)
        assert slopes.shape == (31, 2)
    with pytest.raises(ValueError, match="invalid source"):
        independent.stream_seed(32, "curve_standard", "mask")


def test_independent_audit_return_and_selection_score():
    block, c = 0, "curve_standard"
    X,Y,U,V,A,W = original.prepare(block,c)
    independent_masks = independent.masks(
        X,Y,block,c,"two_anchors","predictor_heteroskedastic"
    )
    missing = independent_masks["MNAR"]
    np.testing.assert_array_equal(
        missing,U<r87.probabilities(X,Y,"MNAR")
    )
    pilot,valid,_=independent.visible_pilot_independently(X,Y,missing)
    source_pilot,source_valid,_=r87.original_visible_pilot(X,Y,missing)
    np.testing.assert_array_equal(valid,source_valid)
    np.testing.assert_allclose(pilot,source_pilot,atol=1e-12,rtol=1e-12)
    initial=missing&(V<independent.true_secondary_recovery(X,Y))
    q=.25
    assigned=missing&~initial&(A<q)
    p_true=independent.logit_probability(X,Y,pilot,1.35)
    p_original=original.return_probability(X,Y,source_pilot,1.35)
    np.testing.assert_allclose(p_true,p_original,atol=1e-12,rtol=1e-12)
    returned=assigned&(W<p_true)
    for g in independent.ASSUMED_GAMMAS:
        candidate=independent.independent_fit(
            X,Y,missing,initial,returned,pilot,valid,q,g)
        expected=original.fit_assumption(
            X,Y,missing,initial,returned,source_pilot,source_valid,q,g)
        assert candidate["delta_converged"] == expected["delta_converged"]
        assert candidate["recovery_converged"] == expected["recovery_converged"]
        independent.close(candidate["first_stage_delta"],
                          expected["first_stage_delta"],"delta",tol=2e-6)
        independent.close(candidate["recovery_gamma"],
                          expected["recovery_gamma"],"gamma",tol=2e-6)


def test_tamper_and_mandatory_actual_original(tmp_path):
    with pytest.raises(ValueError,match="archive missing"):
        independent.audit_original(tmp_path)
    with pytest.raises(ValueError,match="unfrozen gamma"):
        X,Y=original.new_source(0,"curve_standard")
        independent.logit_probability(X,Y,np.zeros((31,2,2)),7.)
    with pytest.raises(ValueError,match="invalid source stream"):
        independent.stream_seed(0,"curve_standard","unknown")
    with pytest.raises(ValueError,match="original numerical mismatch"):
        independent.close(.1,.4,"intentionally tampered number")
