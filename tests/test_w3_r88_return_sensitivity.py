"""R88 frozen independent-source, observed-outcome, and evidence gates."""
import numpy as np
import pytest

from scripts import run_w3_r87_audit_return_nonresponse as r87
from scripts import run_w3_r88_return_sensitivity as r88


def test_frozen_factorial_new_sources_and_streams():
    assert r88.BLOCKS == 32
    assert r88.CONFIGS == ("curve_standard", "participant_standard")
    assert r88.ASSUMED_GAMMAS == (0., .675, 1.35, 2.025)
    assert r88.GENERATING_GAMMA == 1.35
    assert r88.ROWS_PER_BLOCK_CONFIG == 16
    assert r88.N_SOURCES == 64
    assert r88.N_RECORDS == 1024
    assert len(r88.SHARDS) == 8
    assert set(r88.SOURCES.values()).isdisjoint({
        r87.SOURCE_SEED, r87.OBS_SEED, r87.RECOVERY_SEED,
        r87.AUDIT_SEED, r87.AUDIT_RETURN_SEED
    })
    assert len(set(r88.SOURCES.values())) == 5
    with pytest.raises(ValueError, match="primitive block"):
        r88.new_source(32, "curve_standard")
    with pytest.raises(ValueError, match="configuration"):
        r88.stream_seed(0, "curve_standard", "nonexistent")


def test_fresh_source_and_nonreturn_completeness():
    X, Y = r88.new_source(0, "curve_standard")
    X2, Y2 = r88.new_source(0, "curve_standard")
    _, old_y, _, _ = r87.source(0, "curve_standard",
                               "two_anchors", "predictor_heteroskedastic")
    assert X.shape == (72, 2)
    assert Y.shape == (72, 1, 31, 2)
    np.testing.assert_array_equal(X, X2)
    np.testing.assert_array_equal(Y, Y2)
    assert not np.array_equal(Y, old_y)
    assert np.isfinite(Y).all()
    assert not np.array_equal(r88.new_source(0, "participant_standard")[1], Y)


def test_observed_only_scores_ignore_unreturned_hidden_y():
    c = "curve_standard"
    X, Y, U, V, A, W = r88.prepare(0, c)
    missing = U < r87.probabilities(X, Y, "MNAR")
    pilot, valid, _ = r87.original_visible_pilot(X, Y, missing)
    assert np.all(valid)
    initial = missing & (V < r87.actual_recovery_prob(X, Y))
    assigned = missing & ~initial & (A < .5)
    returned = assigned & (
        W < r88.return_probability(X, Y, pilot, r88.GENERATING_GAMMA)
    )
    hidden = missing & ~initial & ~returned
    assert np.any(hidden)
    assert np.sum(returned) <= np.sum(assigned)
    assert not np.any(returned & ~assigned)
    original = r88.fit_assumption(
        X, Y, missing, initial, returned, pilot, valid, .5, .675
    )
    corrupted = Y.copy()
    corrupted[hidden] += 1.e4
    changed = r88.fit_assumption(
        X, corrupted, missing, initial, returned, pilot, valid, .5, .675
    )
    assert original == changed
    for g in r88.ASSUMED_GAMMAS:
        p = r88.return_probability(X, Y, pilot, g)
        assert np.all((p > 0.) & (p < 1.))
    with pytest.raises(ValueError, match="sensitivity support"):
        r88.return_probability(X, Y, pilot, 7.)


def test_complete_one_primitive_block_pair_no_release():
    rows = r88.evaluate(0, "curve_standard")
    assert len(rows) == r88.ROWS_PER_BLOCK_CONFIG
    assert len({r["complete_Y_sha256"] for r in rows}) == 1
    assert len({r["original_missing_sha256"] for r in rows}) == 2
    for m in r88.MECHANISMS:
        for q in r88.AUDIT_LEVELS:
            sub = [r for r in rows if r["mechanism"] == m
                   and r["audit_fraction"] == q]
            assert len(sub) == len(r88.ASSUMED_GAMMAS)
            assert len({r["returned_sha256"] for r in sub}) == 1
            assert len({r["audit_returned_n"] for r in sub}) == 1
            assert all(r["release_authorized"] is False for r in sub)
            assert all(r["unreturned_Y_used_by_fitted_score"] is False for r in sub)
            assert all(r["nominal_confidence_band_claim"] is False for r in sub)


def test_strict_shard_and_aggregate_refuse_incomplete(tmp_path):
    with pytest.raises(ValueError, match="outside frozen"):
        r88.shard(tmp_path / "invalid", 1, 5)
    with pytest.raises(ValueError, match="all eight"):
        r88.aggregate(tmp_path / "out", tmp_path / "empty")
    with pytest.raises(ValueError, match="source denominator"):
        r88.summarize([])
