import numpy as np

from eyetrajectoriespy import (
    FunctionalSimulationResult,
    FunctionalSimulationTruth,
    IrregularTrajectorySet,
    TrajectorySet,
    simulate_functional_process,
)


def _mean(time):
    time = np.asarray(time, dtype=float)
    return 0.2 + 0.2 * time


def _phi1(time):
    time = np.asarray(time, dtype=float)
    return np.sqrt(2.0) * np.sin(np.pi * time)


def _phi2(time):
    time = np.asarray(time, dtype=float)
    return np.sqrt(2.0) * np.sin(2.0 * np.pi * time)


def test_public_functional_simulator_returns_observations_and_truth():
    result = simulate_functional_process(
        mean=_mean,
        eigenfunctions=(_phi1, _phi2),
        eigenvalues=(1.0, 0.3),
        truth_grid=np.linspace(0.0, 1.0, 81),
        n_participants=6,
        trials_per_participant=2,
        participant_eigenvalues=(0.2, 0.05),
        trial_eigenvalues=(0.1, 0.02),
        measurement_noise_sd=0.05,
        random_state=810,
    )

    assert isinstance(result, FunctionalSimulationResult)
    assert isinstance(result.truth, FunctionalSimulationTruth)
    assert isinstance(result.observations, TrajectorySet)
    assert result.observations.n_curves == 12
    assert result.truth.scores.shape == (12, 2)
    assert result.truth.provenance["score_distribution"] == "normal"
    assert result.truth.provenance[
        "raw_dense_to_irregular_interpolation_performed"
    ] is False


def test_public_irregular_simulator_preserves_native_schedule_contract():
    result = simulate_functional_process(
        mean=_mean,
        eigenfunctions=(_phi1, _phi2),
        eigenvalues=(1.0, 0.3),
        truth_grid=np.linspace(0.0, 1.0, 81),
        n_participants=8,
        observation_design="irregular",
        samples_per_curve=(5, 9),
        irregular_time_design="boundary_poor",
        missingness={"kind": "mcar", "probability": 0.1},
        phase_variation={"kind": "power", "sd": 0.15},
        measurement_noise_sd=0.04,
        random_state=811,
    )

    assert isinstance(result.observations, IrregularTrajectorySet)
    assert result.truth.observation_design == "irregular"
    assert result.truth.provenance[
        "raw_dense_to_irregular_interpolation_performed"
    ] is False
    assert result.truth.provenance["missingness_kind"] == "mcar"
    assert result.truth.provenance["phase_variation_kind"] == "power"


def test_student_t_scores_are_variance_matched_and_audited():
    result = simulate_functional_process(
        mean=_mean,
        eigenfunctions=(_phi1, _phi2),
        eigenvalues=(1.0, 0.25),
        truth_grid=np.linspace(0.0, 1.0, 31),
        n_participants=1500,
        score_distribution="student_t",
        score_df=6.0,
        measurement_noise_sd=0.0,
        random_state=812,
    )

    empirical = np.var(
        result.truth.curve_scores,
        axis=0,
        ddof=0,
    )
    np.testing.assert_allclose(
        empirical,
        np.array([1.0, 0.25]),
        rtol=0.15,
        atol=0.0,
    )
    assert result.truth.score_distribution == "student_t"
    assert result.truth.score_distribution_parameters == {
        "kind": "student_t",
        "df": 6.0,
    }


def test_student_t_requires_finite_variance_degrees_of_freedom():
    try:
        simulate_functional_process(
            mean=_mean,
            eigenfunctions=(_phi1, _phi2),
            eigenvalues=(1.0, 0.25),
            truth_grid=np.linspace(0.0, 1.0, 31),
            n_participants=5,
            score_distribution="student_t",
            score_df=2.0,
        )
    except ValueError as exc:
        assert "greater than 2" in str(exc)
    else:
        raise AssertionError("Expected invalid Student-t score_df to fail")
