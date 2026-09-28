import numpy as np
import pytest

from eyetrajectoriespy._functional_simulation import (
    simulate_functional_process_core,
)
from eyetrajectoriespy.types import IrregularTrajectorySet, TrajectorySet


def _mean(time):
    time = np.asarray(time, dtype=float)
    return 0.25 + 0.2 * time


def _phi1(time):
    time = np.asarray(time, dtype=float)
    return np.sqrt(2.0) * np.sin(np.pi * time)


def _phi2(time):
    time = np.asarray(time, dtype=float)
    return np.sqrt(2.0) * np.sin(2.0 * np.pi * time)


def _vector_mean(time):
    time = np.asarray(time, dtype=float)
    return np.column_stack(
        [0.4 + 0.1 * time, 0.6 - 0.1 * time]
    )


def _vector_phi1(time):
    time = np.asarray(time, dtype=float)
    values = np.sin(np.pi * time)
    return np.column_stack([values, values])


def _vector_phi2(time):
    time = np.asarray(time, dtype=float)
    values = np.sin(2.0 * np.pi * time)
    return np.column_stack([values, -values])


def test_hierarchical_scores_are_retained_and_sum_to_total_scores():
    grid = np.linspace(0.0, 1.0, 101)
    result = simulate_functional_process_core(
        mean=_mean,
        eigenfunctions=(_phi1, _phi2),
        eigenvalues=(0.8, 0.3),
        participant_eigenvalues=(0.4, 0.1),
        trial_eigenvalues=(0.2, 0.05),
        truth_grid=grid,
        n_participants=4,
        trials_per_participant=3,
        measurement_noise_sd=0.0,
        random_state=701,
    )
    truth = result.truth

    participant_index = np.repeat(np.arange(4), 3)
    expected_total = (
        truth.curve_scores
        + truth.participant_scores[participant_index]
        + truth.trial_scores
    )
    np.testing.assert_allclose(truth.scores, expected_total)

    reconstructed = (
        truth.mean[None, :, :]
        + np.einsum(
            "ik,ktd->itd",
            truth.scores,
            truth.eigenfunctions,
        )
    )
    np.testing.assert_allclose(
        truth.latent_on_truth_grid,
        reconstructed,
    )
    assert truth.participant_scores.shape == (4, 2)
    assert truth.trial_scores.shape == (12, 2)


def test_dense_mcar_missingness_is_explicit_nan_and_retains_pre_missing_truth():
    result = simulate_functional_process_core(
        mean=_mean,
        eigenfunctions=(_phi1, _phi2),
        eigenvalues=(1.0, 0.25),
        truth_grid=np.linspace(0.0, 1.0, 61),
        n_participants=4,
        missingness={"kind": "mcar", "probability": 0.25},
        measurement_noise_sd=0.05,
        random_state=702,
    )

    assert isinstance(result.observations, TrajectorySet)
    total_missing = 0
    for curve, mask in enumerate(result.truth.missingness_mask):
        total_missing += int(np.count_nonzero(mask))
        observed_missing = np.isnan(
            result.observations.values[curve, :, 0]
        )
        np.testing.assert_array_equal(observed_missing, mask)
        assert np.all(
            np.isfinite(result.truth.observed_pre_missing[curve])
        )
    assert total_missing > 0
    assert result.truth.provenance["missingness_kind"] == "mcar"


def test_irregular_block_missingness_removes_samples_but_keeps_full_truth():
    result = simulate_functional_process_core(
        mean=_mean,
        eigenfunctions=(_phi1, _phi2),
        eigenvalues=(1.0, 0.25),
        truth_grid=np.linspace(0.0, 1.0, 81),
        n_participants=3,
        observation_design="irregular",
        samples_per_curve=8,
        missingness={"kind": "block", "fraction": 0.25},
        measurement_noise_sd=0.0,
        random_state=703,
    )

    assert isinstance(result.observations, IrregularTrajectorySet)
    for curve, mask in enumerate(result.truth.missingness_mask):
        pre_time = result.truth.pre_missing_observation_times[curve]
        final_time = result.truth.observation_times[curve]
        np.testing.assert_array_equal(final_time, pre_time[~mask])
        np.testing.assert_allclose(
            result.observations.values[curve],
            result.truth.observed_pre_missing[curve][~mask],
        )
        assert len(pre_time) == 8
        assert len(final_time) == 6


def test_irregular_missingness_fails_closed_when_too_few_samples_remain():
    with pytest.raises(ValueError, match="fewer than two irregular"):
        simulate_functional_process_core(
            mean=_mean,
            eigenfunctions=(_phi1, _phi2),
            eigenvalues=(1.0, 0.25),
            truth_grid=np.linspace(0.0, 1.0, 51),
            n_participants=3,
            observation_design="irregular",
            samples_per_curve=2,
            missingness={"kind": "block", "fraction": 0.5},
            random_state=704,
        )


def test_power_phase_warps_are_monotone_and_retained_as_truth():
    grid = np.linspace(0.0, 1.0, 101)
    result = simulate_functional_process_core(
        mean=_mean,
        eigenfunctions=(_phi1, _phi2),
        eigenvalues=(1.0, 0.25),
        truth_grid=grid,
        n_participants=5,
        phase_variation={"kind": "power", "sd": 0.30},
        measurement_noise_sd=0.0,
        random_state=705,
    )
    truth = result.truth

    assert truth.provenance["phase_variation_kind"] == "power"
    assert not np.allclose(
        truth.phase_warps_on_truth_grid,
        np.tile(grid, (5, 1)),
    )
    for warp in truth.phase_warps_on_truth_grid:
        assert warp[0] == pytest.approx(0.0)
        assert warp[-1] == pytest.approx(1.0)
        assert np.all(np.diff(warp) > 0)

    curve = 0
    warped = truth.phase_warps_on_truth_grid[curve]
    expected = (
        _mean(warped)[:, None]
        + truth.scores[curve, 0] * _phi1(warped)[:, None]
        + truth.scores[curve, 1] * _phi2(warped)[:, None]
    )
    np.testing.assert_allclose(
        truth.latent_on_truth_grid[curve],
        expected,
    )


def test_correlated_multichannel_measurement_noise_is_retained_and_recovered():
    covariance = np.array(
        [
            [0.04, 0.018],
            [0.018, 0.09],
        ]
    )
    result = simulate_functional_process_core(
        mean=_vector_mean,
        eigenfunctions=(_vector_phi1, _vector_phi2),
        eigenvalues=(0.8, 0.3),
        truth_grid=np.linspace(0.0, 1.0, 101),
        n_participants=30,
        dimension_names=("x", "y"),
        measurement_noise_covariance=covariance,
        random_state=706,
    )

    np.testing.assert_allclose(
        result.truth.measurement_noise_covariance,
        covariance,
    )
    realized = np.concatenate(
        result.truth.measurement_noise,
        axis=0,
    )
    empirical = np.cov(realized, rowvar=False, ddof=0)
    np.testing.assert_allclose(
        empirical,
        covariance,
        atol=0.01,
        rtol=0.0,
    )
    assert result.truth.provenance[
        "measurement_noise_covariance"
    ] == covariance.tolist()


def test_vector_modes_can_induce_cross_channel_latent_covariance():
    result = simulate_functional_process_core(
        mean=_vector_mean,
        eigenfunctions=(_vector_phi1, _vector_phi2),
        eigenvalues=(1.0, 0.4),
        truth_grid=np.linspace(0.0, 1.0, 101),
        n_participants=200,
        dimension_names=("x", "y"),
        measurement_noise_sd=0.0,
        random_state=707,
    )

    midpoint = 35
    latent = result.truth.latent_on_truth_grid[:, midpoint, :]
    covariance = np.cov(latent, rowvar=False, ddof=0)
    assert abs(covariance[0, 1]) > 0.05


def test_noise_sd_and_covariance_cannot_both_be_nonzero():
    with pytest.raises(ValueError, match="cannot both specify"):
        simulate_functional_process_core(
            mean=_vector_mean,
            eigenfunctions=(_vector_phi1, _vector_phi2),
            eigenvalues=(0.8, 0.3),
            truth_grid=np.linspace(0.0, 1.0, 101),
            n_participants=3,
            dimension_names=("x", "y"),
            measurement_noise_sd=(0.1, 0.1),
            measurement_noise_covariance=np.eye(2) * 0.01,
        )


def test_invalid_measurement_noise_covariance_fails_instead_of_being_repaired():
    with pytest.raises(ValueError, match="positive semidefinite"):
        simulate_functional_process_core(
            mean=_vector_mean,
            eigenfunctions=(_vector_phi1, _vector_phi2),
            eigenvalues=(0.8, 0.3),
            truth_grid=np.linspace(0.0, 1.0, 101),
            n_participants=3,
            dimension_names=("x", "y"),
            measurement_noise_covariance=np.array(
                [[1.0, 2.0], [2.0, 1.0]]
            ),
        )
