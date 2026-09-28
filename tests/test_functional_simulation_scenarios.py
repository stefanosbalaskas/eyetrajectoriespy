import numpy as np
import pytest

from eyetrajectoriespy import (
    FunctionalRecoveryRecord,
    FunctionalSimulationScenario,
    expand_functional_simulation_scenarios,
    functional_recovery_frame,
    functional_simulation_scenario_frame,
    run_functional_recovery_scenarios,
    simulate_functional_scenario,
)


def _mean(time):
    time = np.asarray(time, dtype=float)
    return 0.25 + 0.30 * time


def _phi1(time):
    time = np.asarray(time, dtype=float)
    return np.sqrt(2.0) * np.sin(np.pi * time)


def _base_scenario(**updates):
    values = {
        "name": "dense",
        "truth_grid": np.linspace(0.0, 1.0, 41),
        "eigenvalues": (1.0,),
        "n_participants": 8,
        "measurement_noise_sd": 0.0,
        "replicates": 2,
        "seed_start": 700,
        "labels": {"purpose": "unit-test"},
    }
    values.update(updates)
    return FunctionalSimulationScenario(**values)


def test_scenario_seeds_and_audit_frame_are_explicit():
    scenario = _base_scenario()
    assert scenario.seeds() == (700, 701)
    frame = functional_simulation_scenario_frame([scenario])
    assert frame.loc[0, "scenario"] == "dense"
    assert frame.loc[0, "n_curves"] == 8
    assert frame.loc[0, "samples_per_curve_min"] == 41
    assert frame.loc[0, "samples_per_curve_max"] == 41
    assert frame.loc[0, "replicates"] == 2


def test_irregular_scenario_requires_declared_sample_counts():
    with pytest.raises(ValueError, match="require samples_per_curve"):
        _base_scenario(observation_design="irregular")

    scenario = _base_scenario(
        name="irregular",
        observation_design="irregular",
        samples_per_curve=(5, 8),
    )
    assert scenario.samples_per_curve == (5, 8)


def test_scenario_matrix_has_explicit_shared_and_disjoint_seed_policies():
    base = _base_scenario(replicates=2, seed_start=100)
    factors = {
        "measurement_noise_sd": (0.0, 0.1),
        "n_participants": (8, 12),
    }

    shared = expand_functional_simulation_scenarios(
        base,
        factors,
        seed_policy="shared",
    )
    disjoint = expand_functional_simulation_scenarios(
        base,
        factors,
        seed_policy="disjoint",
    )

    assert len(shared) == 4
    assert all(scenario.seeds() == (100, 101) for scenario in shared)
    assert [scenario.seeds() for scenario in disjoint] == [
        (100, 101),
        (102, 103),
        (104, 105),
        (106, 107),
    ]
    assert len({scenario.name for scenario in shared}) == 4


def test_simulate_scenario_stamps_design_provenance_deterministically():
    scenario = _base_scenario(replicates=1, seed_start=314)

    first = simulate_functional_scenario(
        scenario,
        mean=_mean,
        eigenfunctions=(_phi1,),
    )
    second = simulate_functional_scenario(
        scenario,
        mean=_mean,
        eigenfunctions=(_phi1,),
    )

    assert np.array_equal(
        first.observations.values,
        second.observations.values,
    )
    assert first.truth.provenance["scenario_name"] == "dense"
    assert first.truth.provenance["scenario_replicate"] == 0
    assert first.truth.provenance["scenario_seed"] == 314
    assert first.truth.provenance["scenario_labels"] == {
        "purpose": "unit-test"
    }


def test_recovery_runner_keeps_truth_out_of_estimator_callback():
    scenario = _base_scenario(replicates=2, seed_start=900)
    estimator_inputs = []

    def estimator(observations, declared_scenario):
        estimator_inputs.append((observations, declared_scenario))
        return float(np.mean(observations.values))

    def recovery(fitted, truth, declared_scenario):
        assert declared_scenario.name == "dense"
        assert truth.provenance["scenario_name"] == "dense"
        return {
            "fit_mean": fitted,
            "truth_mean": float(np.mean(truth.latent_on_truth_grid)),
        }

    result = run_functional_recovery_scenarios(
        [scenario],
        mean=_mean,
        eigenfunctions=(_phi1,),
        estimator=estimator,
        recovery=recovery,
    )

    assert len(estimator_inputs) == 2
    assert all(len(entry) == 2 for entry in estimator_inputs)
    assert len(result.records) == 2

    frame = functional_recovery_frame(result)
    assert set(frame["metric"]) == {"fit_mean", "truth_mean"}
    assert frame.shape[0] == 4



def test_scenario_rejects_conflicting_or_invalid_noise_declarations():
    with pytest.raises(ValueError, match="cannot both specify non-zero noise"):
        _base_scenario(
            measurement_noise_sd=0.1,
            measurement_noise_covariance=np.array([[0.04]]),
        )
    with pytest.raises(ValueError, match="positive semidefinite"):
        FunctionalSimulationScenario(
            name="bad-covariance",
            truth_grid=np.linspace(0.0, 1.0, 21),
            eigenvalues=(1.0,),
            n_participants=4,
            dimension_names=("x", "y"),
            measurement_noise_sd=None,
            measurement_noise_covariance=np.array(
                [[1.0, 2.0], [2.0, 1.0]]
            ),
        )

def test_recovery_metrics_fail_closed_on_nonfinite_values():
    with pytest.raises(ValueError, match="finite"):
        FunctionalRecoveryRecord(
            scenario_name="bad",
            replicate=0,
            seed=1,
            metrics={"rmse": np.nan},
        )


def test_scenario_matrix_rejects_unknown_factors_and_implicit_seed_changes():
    base = _base_scenario()
    with pytest.raises(ValueError, match="unknown scenario factor"):
        expand_functional_simulation_scenarios(
            base,
            {"does_not_exist": (1, 2)},
        )
    with pytest.raises(ValueError, match="seed_start is controlled"):
        expand_functional_simulation_scenarios(
            base,
            {"seed_start": (10, 20)},
        )
