import numpy as np
import pytest

from eyetrajectoriespy._functional_simulation import (
    simulate_functional_process_core,
)
from eyetrajectoriespy.types import (
    IrregularTrajectorySet,
    TrajectorySet,
)


def _scalar_mean(time):
    time = np.asarray(time, dtype=float)
    return 0.2 + 0.3 * time


def _scalar_phi1(time):
    time = np.asarray(time, dtype=float)
    return np.sqrt(2.0) * np.sin(np.pi * time)


def _scalar_phi2(time):
    time = np.asarray(time, dtype=float)
    return np.sqrt(2.0) * np.sin(2.0 * np.pi * time)


def _vector_mean(time):
    time = np.asarray(time, dtype=float)
    return np.column_stack(
        [
            0.4 + 0.1 * time,
            0.6 - 0.1 * time,
        ]
    )


def _vector_phi_x(time):
    time = np.asarray(time, dtype=float)
    values = np.sqrt(2.0) * np.sin(np.pi * time)
    return np.column_stack([values, np.zeros_like(values)])


def _vector_phi_y(time):
    time = np.asarray(time, dtype=float)
    values = np.sqrt(2.0) * np.sin(np.pi * time)
    return np.column_stack([np.zeros_like(values), values])


def test_dense_core_reconstructs_exact_latent_process_without_noise():
    grid = np.linspace(0.0, 1.0, 101)
    result = simulate_functional_process_core(
        mean=_scalar_mean,
        eigenfunctions=(_scalar_phi1, _scalar_phi2),
        eigenvalues=(1.0, 0.25),
        truth_grid=grid,
        n_participants=4,
        trials_per_participant=2,
        measurement_noise_sd=0.0,
        random_state=123,
    )

    assert isinstance(result.observations, TrajectorySet)
    assert result.observations.values.shape == (8, 101, 1)
    assert result.truth.latent_on_truth_grid.shape == (8, 101, 1)
    np.testing.assert_allclose(
        result.observations.values,
        result.truth.latent_on_truth_grid,
    )

    reconstructed = (
        result.truth.mean[None, :, :]
        + np.einsum(
            "ik,ktd->itd",
            result.truth.scores,
            result.truth.eigenfunctions,
        )
    )
    np.testing.assert_allclose(
        reconstructed,
        result.truth.latent_on_truth_grid,
    )
    assert result.observations.provenance[
        "raw_dense_to_irregular_interpolation_performed"
    ] is False


def test_measurement_noise_is_fully_accounted_in_truth():
    result = simulate_functional_process_core(
        mean=_scalar_mean,
        eigenfunctions=(_scalar_phi1, _scalar_phi2),
        eigenvalues=(1.0, 0.25),
        truth_grid=np.linspace(0.0, 1.0, 51),
        n_participants=3,
        trials_per_participant=2,
        measurement_noise_sd=0.2,
        random_state=77,
    )

    for observed, latent, noise in zip(
        result.truth.observed_pre_missing,
        result.truth.latent_at_observation_times,
        result.truth.measurement_noise,
        strict=True,
    ):
        np.testing.assert_allclose(observed, latent + noise)
    assert any(
        np.any(np.abs(noise) > 0)
        for noise in result.truth.measurement_noise
    )


def test_irregular_core_generates_native_schedules_without_dense_interpolation():
    result = simulate_functional_process_core(
        mean=_scalar_mean,
        eigenfunctions=(_scalar_phi1, _scalar_phi2),
        eigenvalues=(1.0, 0.25),
        truth_grid=np.linspace(0.0, 1.0, 81),
        n_participants=5,
        trials_per_participant=1,
        observation_design="irregular",
        samples_per_curve=(4, 8),
        irregular_time_design="center_clustered",
        measurement_noise_sd=0.05,
        random_state=91,
    )

    assert isinstance(result.observations, IrregularTrajectorySet)
    assert result.observations.sample_counts.min() >= 4
    assert result.observations.sample_counts.max() <= 8
    assert result.truth.observation_design == "irregular"
    assert result.truth.provenance[
        "raw_dense_to_irregular_interpolation_performed"
    ] is False

    for observed_time, truth_time in zip(
        result.observations.time,
        result.truth.observation_times,
        strict=True,
    ):
        np.testing.assert_array_equal(observed_time, truth_time)
        assert np.all(np.diff(observed_time) > 0)


def test_dense_and_irregular_outputs_agree_when_declared_schedules_coincide():
    grid = np.linspace(0.0, 1.0, 61)
    common = dict(
        mean=_scalar_mean,
        eigenfunctions=(_scalar_phi1, _scalar_phi2),
        eigenvalues=(1.0, 0.25),
        truth_grid=grid,
        n_participants=3,
        trials_per_participant=2,
        measurement_noise_sd=0.1,
        random_state=204,
    )
    dense = simulate_functional_process_core(**common)
    irregular = simulate_functional_process_core(
        **common,
        observation_design="irregular",
        observation_times=tuple(
            grid.copy() for _ in range(6)
        ),
    )

    assert isinstance(dense.observations, TrajectorySet)
    assert isinstance(irregular.observations, IrregularTrajectorySet)
    for curve in range(6):
        np.testing.assert_allclose(
            dense.observations.values[curve],
            irregular.observations.values[curve],
        )
        np.testing.assert_allclose(
            dense.truth.measurement_noise[curve],
            irregular.truth.measurement_noise[curve],
        )
        np.testing.assert_allclose(
            dense.truth.latent_at_observation_times[curve],
            irregular.truth.latent_at_observation_times[curve],
        )


def test_vector_valued_modes_preserve_multichannel_truth():
    result = simulate_functional_process_core(
        mean=_vector_mean,
        eigenfunctions=(_vector_phi_x, _vector_phi_y),
        eigenvalues=(0.8, 0.4),
        truth_grid=np.linspace(0.0, 1.0, 101),
        n_participants=4,
        trials_per_participant=1,
        dimension_names=("x", "y"),
        coordinate_system="normalized",
        measurement_noise_sd=(0.02, 0.03),
        random_state=14,
    )

    assert result.observations.n_dimensions == 2
    assert result.truth.eigenfunctions.shape == (2, 101, 2)
    assert result.truth.mean.shape == (101, 2)
    assert result.truth.dimension_names == ("x", "y")
    assert result.truth.coordinate_system == "normalized"
    assert result.truth.provenance["measurement_noise_sd"] == [0.02, 0.03]


def test_simulation_is_reproducible_for_identical_seed():
    kwargs = dict(
        mean=_scalar_mean,
        eigenfunctions=(_scalar_phi1, _scalar_phi2),
        eigenvalues=(1.0, 0.25),
        truth_grid=np.linspace(0.0, 1.0, 51),
        n_participants=4,
        trials_per_participant=2,
        observation_design="irregular",
        samples_per_curve=(5, 9),
        measurement_noise_sd=0.08,
    )
    first = simulate_functional_process_core(
        **kwargs,
        random_state=300,
    )
    second = simulate_functional_process_core(
        **kwargs,
        random_state=300,
    )
    third = simulate_functional_process_core(
        **kwargs,
        random_state=301,
    )

    np.testing.assert_allclose(first.truth.scores, second.truth.scores)
    for left, right in zip(
        first.observations.time,
        second.observations.time,
        strict=True,
    ):
        np.testing.assert_array_equal(left, right)
    for left, right in zip(
        first.observations.values,
        second.observations.values,
        strict=True,
    ):
        np.testing.assert_allclose(left, right)

    assert not np.allclose(first.truth.scores, third.truth.scores)


def test_nonorthonormal_modes_fail_instead_of_being_silently_repaired():
    def duplicate_mode(time):
        return _scalar_phi1(time)

    with pytest.raises(ValueError, match="orthonormal"):
        simulate_functional_process_core(
            mean=_scalar_mean,
            eigenfunctions=(_scalar_phi1, duplicate_mode),
            eigenvalues=(1.0, 0.25),
            truth_grid=np.linspace(0.0, 1.0, 101),
            n_participants=3,
        )


def test_irregular_contract_requires_explicit_sampling_specification():
    with pytest.raises(ValueError, match="requires observation_times"):
        simulate_functional_process_core(
            mean=_scalar_mean,
            eigenfunctions=(_scalar_phi1, _scalar_phi2),
            eigenvalues=(1.0, 0.25),
            truth_grid=np.linspace(0.0, 1.0, 51),
            n_participants=3,
            observation_design="irregular",
        )


def test_metadata_retains_participant_and_trial_hierarchy_labels():
    result = simulate_functional_process_core(
        mean=_scalar_mean,
        eigenfunctions=(_scalar_phi1, _scalar_phi2),
        eigenvalues=(1.0, 0.25),
        truth_grid=np.linspace(0.0, 1.0, 51),
        n_participants=3,
        trials_per_participant=2,
        random_state=41,
    )

    metadata = result.truth.metadata
    assert list(metadata.columns) == ["participant_id", "trial_id"]
    assert metadata["participant_id"].nunique() == 3
    assert metadata["trial_id"].tolist() == [1, 2, 1, 2, 1, 2]
    assert result.observations.curve_ids[0] == "P001|T01"
