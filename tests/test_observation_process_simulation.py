import numpy as np
import pytest

from eyetrajectoriespy._observation_process_simulation import (
    ObservationProcessSimulationTruth,
    observation_process_from_functional_simulation,
    simulate_informative_time_retention,
)
from eyetrajectoriespy.simulate import simulate_functional_process


def _mean(time):
    time = np.asarray(time, dtype=float)
    return np.column_stack((0.4 + 0.1 * time, 0.6 - 0.05 * time))


def _phi_x(time):
    time = np.asarray(time, dtype=float)
    return np.column_stack((np.ones_like(time), np.zeros_like(time)))


def _phi_y(time):
    time = np.asarray(time, dtype=float)
    return np.column_stack((np.zeros_like(time), np.ones_like(time)))


def _simulation(*, missingness=None, random_state=41):
    return simulate_functional_process(
        mean=_mean,
        eigenfunctions=(_phi_x, _phi_y),
        eigenvalues=(0.05, 0.02),
        truth_grid=np.linspace(0.0, 1.0, 11),
        n_participants=4,
        trials_per_participant=2,
        dimension_names=("x", "y"),
        coordinate_system="normalized",
        time_unit="normalized",
        observation_design="dense",
        measurement_noise_sd=(0.01, 0.01),
        missingness=missingness,
        random_state=random_state,
    )


def test_mcar_functional_truth_converts_to_exact_candidate_denominator():
    simulation = _simulation(missingness={"kind": "mcar", "probability": 0.25})
    truth = observation_process_from_functional_simulation(simulation)

    assert isinstance(truth, ObservationProcessSimulationTruth)
    assert truth.mechanism == "mcar"
    assert truth.n_candidates == 4 * 2 * 11
    assert truth.n_missing == sum(mask.sum() for mask in simulation.truth.missingness_mask)
    assert truth.process.n_candidates == truth.n_candidates
    assert truth.process.n_missing == truth.n_missing
    assert truth.retention_probability is not None
    for probability in truth.retention_probability:
        np.testing.assert_allclose(probability, 0.75)
    assert truth.process.group_column == "participant_id"
    assert truth.process.candidate_predictors == ("trial_id",)
    assert truth.process.coordinate_columns == ("x", "y")
    assert truth.provenance["functional_truth_reused"] is True


def test_raw_coordinates_are_retained_only_when_candidate_is_observed():
    truth = observation_process_from_functional_simulation(
        _simulation(missingness={"kind": "mcar", "probability": 0.35})
    )
    frame = truth.process.frame
    observed = frame["observed"].to_numpy(dtype=bool)

    assert np.all(np.isfinite(frame.loc[observed, ["x", "y"]].to_numpy(dtype=float)))
    assert np.all(np.isnan(frame.loc[~observed, ["x", "y"]].to_numpy(dtype=float)))


def test_block_truth_retains_exact_realized_mask_without_fake_probabilities():
    simulation = _simulation(missingness={"kind": "block", "fraction": 0.30})
    truth = observation_process_from_functional_simulation(simulation)

    assert truth.mechanism == "block"
    assert truth.retention_probability is None
    assert truth.specification == {"kind": "block", "fraction": 0.30}
    assert all(int(mask.sum()) == 3 for mask in truth.missingness_mask)


def test_complete_functional_truth_has_unit_retention_probability():
    truth = observation_process_from_functional_simulation(_simulation())

    assert truth.mechanism == "none"
    assert truth.n_missing == 0
    assert truth.retention_probability is not None
    for probability in truth.retention_probability:
        np.testing.assert_array_equal(probability, np.ones(11))


def test_informative_time_retention_keeps_exact_probability_and_replays():
    simulation = _simulation()
    first = simulate_informative_time_retention(
        simulation,
        intercept=0.8,
        slope=-2.4,
        random_state=166,
    )
    second = simulate_informative_time_retention(
        simulation,
        intercept=0.8,
        slope=-2.4,
        random_state=166,
    )

    assert first.mechanism == "logistic_candidate_time"
    assert first.retention_probability is not None
    assert first.specification["slope"] == pytest.approx(-2.4)
    assert first.provenance["simulation_only"] is True
    assert first.provenance["public_correction_estimator"] is False
    for p_first, p_second, mask_first, mask_second in zip(
        first.retention_probability,
        second.retention_probability,
        first.missingness_mask,
        second.missingness_mask,
        strict=True,
    ):
        np.testing.assert_allclose(p_first, p_second)
        np.testing.assert_array_equal(mask_first, mask_second)
        assert p_first[0] > p_first[-1]

    time = simulation.truth.pre_missing_observation_times[0]
    z = 2.0 * (time - time[0]) / (time[-1] - time[0]) - 1.0
    expected = 1.0 / (1.0 + np.exp(-(0.8 - 2.4 * z)))
    np.testing.assert_allclose(first.retention_probability[0], expected)


def test_informative_retention_does_not_modify_functional_simulation_truth():
    simulation = _simulation()
    original_masks = tuple(mask.copy() for mask in simulation.truth.missingness_mask)

    informative = simulate_informative_time_retention(simulation, random_state=166)

    assert informative.n_missing > 0
    for original, after in zip(original_masks, simulation.truth.missingness_mask, strict=True):
        np.testing.assert_array_equal(original, after)
        assert not np.any(after)


def test_informative_retention_requires_complete_base_truth():
    simulation = _simulation(missingness={"kind": "mcar", "probability": 0.2})
    with pytest.raises(ValueError, match="without prior missingness"):
        simulate_informative_time_retention(simulation)


def test_simulation_truth_validation_fail_closed():
    with pytest.raises(TypeError, match="FunctionalSimulationResult"):
        observation_process_from_functional_simulation(object())

    simulation = _simulation()
    with pytest.raises(ValueError, match="finite"):
        simulate_informative_time_retention(simulation, intercept=np.nan)
    with pytest.raises(TypeError, match="integer"):
        simulate_informative_time_retention(simulation, random_state=True)
