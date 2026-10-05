import numpy as np
import pytest

from eyetrajectoriespy._sparse_multilevel import (
    evaluate_fitted_cross_covariance,
    raw_cross_trial_covariance_pairs,
    sparse_multilevel_blup_scores,
)
from eyetrajectoriespy._sparse_native import SparseNativeError


def test_cross_trial_pairs_use_only_distinct_trials_within_participant():
    times = (
        np.asarray([0.0, 1.0]),
        np.asarray([0.25, 0.75]),
        np.asarray([0.0, 1.0]),
    )
    residuals = (
        np.asarray([1.0, 2.0]),
        np.asarray([3.0, 5.0]),
        np.asarray([100.0, 200.0]),
    )
    participants = ("p1", "p1", "p2")

    pairs = raw_cross_trial_covariance_pairs(
        times,
        residuals,
        participants,
        include_mirror=True,
    )

    # p1 contributes 2 x 2 products, each mirrored. The single-trial p2
    # contributes no between-level covariance products.
    assert pairs.n_pairs == 8
    assert set(pairs.curve_index.tolist()) == {0}
    np.testing.assert_allclose(
        np.sort(pairs.products),
        np.sort(np.repeat([3.0, 5.0, 6.0, 10.0], 2)),
    )
    assert not np.any(np.abs(pairs.products) >= 100.0)


def test_cross_trial_pair_participant_indices_are_deterministic_first_seen_order():
    times = tuple(np.asarray([0.0, 1.0]) for _ in range(4))
    residuals = (
        np.asarray([1.0, 1.0]),
        np.asarray([2.0, 2.0]),
        np.asarray([3.0, 3.0]),
        np.asarray([4.0, 4.0]),
    )
    participants = ("b", "a", "b", "a")

    pairs = raw_cross_trial_covariance_pairs(times, residuals, participants)

    # First-seen participant order is b -> 0, a -> 1.
    assert set(pairs.curve_index.tolist()) == {0, 1}
    assert np.count_nonzero(pairs.curve_index == 0) == 8
    assert np.count_nonzero(pairs.curve_index == 1) == 8


def test_cross_trial_pairs_fail_when_repeated_support_is_insufficient():
    times = (np.asarray([0.0]), np.asarray([0.5]), np.asarray([1.0]))
    residuals = (np.asarray([1.0]), np.asarray([2.0]), np.asarray([3.0]))

    with pytest.raises(SparseNativeError) as error:
        raw_cross_trial_covariance_pairs(
            times,
            residuals,
            ("p1", "p2", "p3"),
        )
    assert error.value.code == "insufficient_between_covariance_pairs"


def test_cross_covariance_evaluation_respects_left_right_native_times():
    grid = np.asarray([0.0, 0.5, 1.0])
    # Symmetric bilinear surface K(s,t) = 1 + s + t + 2 s t.
    s, t = np.meshgrid(grid, grid, indexing="ij")
    covariance = 1.0 + s + t + 2.0 * s * t
    left = np.asarray([0.0, 0.5])
    right = np.asarray([0.25, 1.0])

    evaluated = evaluate_fitted_cross_covariance(
        grid,
        covariance,
        left,
        right,
    )
    expected = 1.0 + left[:, None] + right[None, :] + 2.0 * (
        left[:, None] * right[None, :]
    )
    np.testing.assert_allclose(evaluated, expected, atol=1e-12)


def test_joint_multilevel_blup_matches_direct_two_trial_calculation():
    grid = np.asarray([0.0, 1.0])
    curve_ids = ("t1", "t2")
    participant_ids = ("p1", "p1")
    times = (np.asarray([0.0]), np.asarray([1.0]))
    values = (np.asarray([1.0]), np.asarray([2.0]))
    constant = np.ones((2, 2), dtype=float)
    functions = np.ones((1, 2), dtype=float)

    result = sparse_multilevel_blup_scores(
        curve_ids,
        participant_ids,
        times,
        values,
        evaluation_grid=grid,
        fitted_mean=np.zeros(2),
        between_covariance=constant,
        within_covariance=2.0 * constant,
        participant_eigenvalues=np.asarray([1.0]),
        participant_eigenfunctions=functions,
        trial_eigenvalues=np.asarray([2.0]),
        trial_eigenfunctions=functions,
        noise_variance=1.0,
        participant_components=1,
        trial_components=1,
    )

    sigma = np.asarray([[4.0, 1.0], [1.0, 4.0]])
    solved = np.linalg.solve(sigma, np.asarray([1.0, 2.0]))
    expected_participant = solved.sum()
    expected_trials = 2.0 * solved

    np.testing.assert_allclose(
        result.participant_scores[:, 0],
        [expected_participant],
        atol=1e-12,
    )
    np.testing.assert_allclose(
        result.trial_scores[:, 0],
        expected_trials,
        atol=1e-12,
    )
    assert result.covariance_source == "full_fitted_between_plus_within_plus_noise"
    assert result.diagnostics.loc[0, "status_code"] == "ok"
    assert result.diagnostics.loc[0, "n_trials"] == 2
    assert result.diagnostics.loc[0, "n_samples"] == 2


def test_blup_observation_covariance_is_not_rank_truncated():
    grid = np.asarray([0.0, 1.0])
    times = (np.asarray([0.0]), np.asarray([1.0]))
    values = (np.asarray([1.0]), np.asarray([2.0]))
    functions = np.ones((1, 2), dtype=float)

    # The retained score eigenvalues are deliberately not equal to the full
    # fitted covariance amplitudes. A rank-K reconstruction would therefore
    # produce a different score system.
    result = sparse_multilevel_blup_scores(
        ("t1", "t2"),
        ("p1", "p1"),
        times,
        values,
        evaluation_grid=grid,
        fitted_mean=np.zeros(2),
        between_covariance=5.0 * np.ones((2, 2)),
        within_covariance=7.0 * np.ones((2, 2)),
        participant_eigenvalues=np.asarray([1.0]),
        participant_eigenfunctions=functions,
        trial_eigenvalues=np.asarray([2.0]),
        trial_eigenfunctions=functions,
        noise_variance=1.0,
        participant_components=1,
        trial_components=1,
    )

    full_sigma = np.asarray([[13.0, 5.0], [5.0, 13.0]])
    solved_full = np.linalg.solve(full_sigma, np.asarray([1.0, 2.0]))
    rank_k_sigma = np.asarray([[4.0, 1.0], [1.0, 4.0]])
    solved_rank_k = np.linalg.solve(rank_k_sigma, np.asarray([1.0, 2.0]))

    np.testing.assert_allclose(
        result.participant_scores[0, 0],
        solved_full.sum(),
        atol=1e-12,
    )
    assert not np.isclose(
        result.participant_scores[0, 0],
        solved_rank_k.sum(),
    )


def test_trial_score_blocks_do_not_leak_across_trials():
    grid = np.asarray([0.0, 1.0])
    functions = np.ones((1, 2), dtype=float)
    common = dict(
        curve_ids=("t1", "t2"),
        participant_ids=("p1", "p1"),
        curve_times=(np.asarray([0.0]), np.asarray([1.0])),
        evaluation_grid=grid,
        fitted_mean=np.zeros(2),
        between_covariance=np.ones((2, 2)),
        within_covariance=2.0 * np.ones((2, 2)),
        participant_eigenvalues=np.asarray([1.0]),
        participant_eigenfunctions=functions,
        trial_eigenvalues=np.asarray([2.0]),
        trial_eigenfunctions=functions,
        noise_variance=1.0,
        participant_components=1,
        trial_components=1,
    )

    base = sparse_multilevel_blup_scores(
        curve_values=(np.asarray([1.0]), np.asarray([0.0])),
        **common,
    )
    changed = sparse_multilevel_blup_scores(
        curve_values=(np.asarray([1.0]), np.asarray([3.0])),
        **common,
    )

    # Changing trial 2 affects the shared participant solve, so trial 1 can
    # change through Sigma^{-1}; however, the trial-1 cross-covariance itself
    # is its own block. The direct formula is 2 * solved[0].
    sigma = np.asarray([[4.0, 1.0], [1.0, 4.0]])
    solved_base = np.linalg.solve(sigma, np.asarray([1.0, 0.0]))
    solved_changed = np.linalg.solve(sigma, np.asarray([1.0, 3.0]))
    np.testing.assert_allclose(base.trial_scores[0, 0], 2.0 * solved_base[0])
    np.testing.assert_allclose(changed.trial_scores[0, 0], 2.0 * solved_changed[0])
    np.testing.assert_allclose(changed.trial_scores[1, 0], 2.0 * solved_changed[1])


def test_single_trial_participant_can_be_scored_after_population_fit():
    grid = np.asarray([0.0, 1.0])
    functions = np.ones((1, 2), dtype=float)

    result = sparse_multilevel_blup_scores(
        ("p1_t1", "p1_t2", "p2_t1"),
        ("p1", "p1", "p2"),
        (np.asarray([0.0]), np.asarray([1.0]), np.asarray([0.5, 1.0])),
        (np.asarray([1.0]), np.asarray([2.0]), np.asarray([0.5, 1.0])),
        evaluation_grid=grid,
        fitted_mean=np.zeros(2),
        between_covariance=np.ones((2, 2)),
        within_covariance=2.0 * np.ones((2, 2)),
        participant_eigenvalues=np.asarray([1.0]),
        participant_eigenfunctions=functions,
        trial_eigenvalues=np.asarray([2.0]),
        trial_eigenfunctions=functions,
        noise_variance=1.0,
        participant_components=1,
        trial_components=1,
    )

    assert result.participant_ids == ("p1", "p2")
    assert np.all(np.isfinite(result.participant_scores))
    assert np.all(np.isfinite(result.trial_scores))
    assert result.diagnostics.loc[1, "n_trials"] == 1


def test_multilevel_blup_retain_nan_preserves_failed_participant_rows():
    grid = np.asarray([0.0, 1.0])
    functions = np.ones((1, 2), dtype=float)

    result = sparse_multilevel_blup_scores(
        ("t1", "t2"),
        ("p1", "p1"),
        (np.asarray([0.0]), np.asarray([1.0])),
        (np.asarray([1.0]), np.asarray([2.0])),
        evaluation_grid=grid,
        fitted_mean=np.zeros(2),
        between_covariance=np.zeros((2, 2)),
        within_covariance=np.zeros((2, 2)),
        participant_eigenvalues=np.asarray([1.0]),
        participant_eigenfunctions=functions,
        trial_eigenvalues=np.asarray([1.0]),
        trial_eigenfunctions=functions,
        noise_variance=0.0,
        participant_components=1,
        trial_components=1,
        failure_action="retain_nan",
    )

    assert result.diagnostics.loc[0, "status_code"] == (
        "multilevel_score_covariance_not_positive_definite"
    )
    assert np.isnan(result.participant_scores).all()
    assert np.isnan(result.trial_scores).all()


def test_multilevel_blup_error_mode_fails_closed():
    grid = np.asarray([0.0, 1.0])
    functions = np.ones((1, 2), dtype=float)

    with pytest.raises(SparseNativeError) as error:
        sparse_multilevel_blup_scores(
            ("t1", "t2"),
            ("p1", "p1"),
            (np.asarray([0.0]), np.asarray([1.0])),
            (np.asarray([1.0]), np.asarray([2.0])),
            evaluation_grid=grid,
            fitted_mean=np.zeros(2),
            between_covariance=np.zeros((2, 2)),
            within_covariance=np.zeros((2, 2)),
            participant_eigenvalues=np.asarray([1.0]),
            participant_eigenfunctions=functions,
            trial_eigenvalues=np.asarray([1.0]),
            trial_eigenfunctions=functions,
            noise_variance=0.0,
            participant_components=1,
            trial_components=1,
            failure_action="error",
        )
    assert error.value.code == "multilevel_score_covariance_not_positive_definite"
