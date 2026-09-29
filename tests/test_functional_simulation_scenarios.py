import numpy as np
import pytest

from eyetrajectoriespy import (
    FunctionalRecoveryAssessment,
    FunctionalRecoveryRecord,
    FunctionalRecoveryResult,
    FunctionalRecoveryValue,
    FunctionalSimulationScenario,
    expand_functional_simulation_scenarios,
    functional_recovery_failure_frame,
    functional_recovery_frame,
    functional_recovery_metric_catalog,
    functional_recovery_summary_frame,
    functional_simulation_scenario_frame,
    run_functional_recovery_scenarios,
    simulate_aoi_probability_trajectories,
    simulate_functional_process,
    simulate_functional_scenario,
    simulate_planar_trajectories,
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


@pytest.mark.parametrize(
    ("updates", "message"),
    [
        ({"name": " "}, "name"),
        ({"truth_grid": [0.0, 0.5, 0.4]}, "truth_grid"),
        ({"eigenvalues": ()}, "non-empty"),
        ({"eigenvalues": (1.0, -0.1)}, "positive"),
        ({"eigenvalues": (0.5, 1.0)}, "descending"),
        ({"n_participants": 0}, "n_participants"),
        ({"trials_per_participant": 0}, "trials_per_participant"),
        ({"replicates": 0}, "replicates"),
        ({"seed_start": 2.5}, "seed_start"),
        ({"dimension_names": ("",)}, "dimension_names"),
        ({"dimension_names": ("x", "x")}, "unique"),
        ({"observation_design": "unsupported"}, "observation_design"),
        ({"samples_per_curve": 4}, "only defined for irregular"),
        ({"participant_eigenvalues": (0.2, 0.1)}, "one value per component"),
        ({"participant_eigenvalues": (-0.1,)}, "non-negative"),
        ({"score_distribution": "laplace"}, "score_distribution"),
        (
            {"score_distribution": "student_t", "score_df": 2.0},
            "score_df",
        ),
        ({"orthonormal_tolerance": 0.0}, "orthonormal_tolerance"),
    ],
)
def test_scenario_declaration_fail_closed_contracts(updates, message):
    with pytest.raises((TypeError, ValueError), match=message):
        _base_scenario(**updates)


@pytest.mark.parametrize(
    "samples",
    [1, (1, 4), (5, 4), (2, 3, 4)],
)
def test_irregular_sample_count_contracts(samples):
    with pytest.raises(ValueError, match="samples_per_curve"):
        _base_scenario(
            observation_design="irregular",
            samples_per_curve=samples,
        )


@pytest.mark.parametrize(
    ("noise_sd", "covariance", "message"),
    [
        ((0.1, 0.2), None, "one value per dimension"),
        ((np.nan,), None, "finite"),
        (None, np.ones((2, 2)), "number of dimensions"),
        (None, np.array([[np.nan]]), "finite"),
    ],
)
def test_scenario_noise_shape_and_finiteness_contracts(
    noise_sd,
    covariance,
    message,
):
    with pytest.raises(ValueError, match=message):
        _base_scenario(
            measurement_noise_sd=noise_sd,
            measurement_noise_covariance=covariance,
        )


def test_scenario_noise_covariance_symmetry_and_audit_fields():
    with pytest.raises(ValueError, match="symmetric"):
        FunctionalSimulationScenario(
            name="asymmetric",
            truth_grid=np.linspace(0.0, 1.0, 21),
            eigenvalues=(1.0,),
            n_participants=4,
            dimension_names=("x", "y"),
            measurement_noise_sd=None,
            measurement_noise_covariance=np.array(
                [[1.0, 0.4], [0.2, 1.0]]
            ),
        )

    covariance = np.array([[0.04, 0.01], [0.01, 0.09]])
    scenario = FunctionalSimulationScenario(
        name="multichannel",
        truth_grid=np.linspace(0.0, 1.0, 21),
        eigenvalues=(1.0,),
        n_participants=4,
        dimension_names=("x", "y"),
        participant_eigenvalues=(0.2,),
        trial_eigenvalues=(0.1,),
        measurement_noise_sd=None,
        measurement_noise_covariance=covariance,
        missingness={"kind": "mcar", "probability": 0.1},
        phase_variation={"kind": "power", "sd": 0.1},
    )
    frame = functional_simulation_scenario_frame([scenario])
    assert frame.loc[0, "participant_eigenvalues"] == "[0.2]"
    assert frame.loc[0, "trial_eigenvalues"] == "[0.1]"
    assert frame.loc[0, "measurement_noise_covariance"] is not None
    assert frame.loc[0, "missingness"] is not None
    assert frame.loc[0, "phase_variation"] is not None


def test_irregular_scalar_sample_count_is_audited():
    scenario = _base_scenario(
        name="irregular-fixed",
        observation_design="irregular",
        samples_per_curve=6,
    )
    frame = functional_simulation_scenario_frame([scenario])
    assert frame.loc[0, "samples_per_curve_min"] == 6
    assert frame.loc[0, "samples_per_curve_max"] == 6


def test_recovery_object_and_runner_invalid_inputs_fail_closed():
    with pytest.raises(ValueError, match="at least one record"):
        FunctionalRecoveryResult(records=())
    with pytest.raises(ValueError, match="non-empty"):
        FunctionalRecoveryRecord(
            scenario_name="bad",
            replicate=0,
            seed=1,
            metrics={},
        )
    with pytest.raises(TypeError, match="FunctionalSimulationScenario"):
        simulate_functional_scenario(
            "not-a-scenario",
            mean=_mean,
            eigenfunctions=(_phi1,),
        )

    scenario = _base_scenario(replicates=1)
    with pytest.raises(ValueError, match="outside"):
        simulate_functional_scenario(
            scenario,
            mean=_mean,
            eigenfunctions=(_phi1,),
            replicate=1,
        )
    with pytest.raises(ValueError, match="non-empty"):
        run_functional_recovery_scenarios(
            [],
            mean=_mean,
            eigenfunctions=(_phi1,),
            estimator=lambda observations, declared: observations,
            recovery=lambda fitted, truth, declared: {"ok": 1.0},
        )
    with pytest.raises(TypeError, match="callable"):
        run_functional_recovery_scenarios(
            [scenario],
            mean=_mean,
            eigenfunctions=(_phi1,),
            estimator=None,
            recovery=lambda fitted, truth, declared: {"ok": 1.0},
        )
    with pytest.raises(TypeError, match="every scenario"):
        run_functional_recovery_scenarios(
            ["bad"],
            mean=_mean,
            eigenfunctions=(_phi1,),
            estimator=lambda observations, declared: observations,
            recovery=lambda fitted, truth, declared: {"ok": 1.0},
        )


def test_audit_frames_reject_wrong_object_types():
    with pytest.raises(TypeError, match="FunctionalRecoveryResult"):
        functional_recovery_frame("bad")
    with pytest.raises(TypeError, match="every scenario"):
        functional_simulation_scenario_frame(["bad"])


def test_scenario_expansion_fail_closed_and_slug_paths():
    with pytest.raises(TypeError, match="FunctionalSimulationScenario"):
        expand_functional_simulation_scenarios(
            "bad",
            {"n_participants": (4, 8)},
        )

    base = _base_scenario()
    with pytest.raises(ValueError, match="non-empty"):
        expand_functional_simulation_scenarios(base, {})
    with pytest.raises(ValueError, match="seed_policy"):
        expand_functional_simulation_scenarios(
            base,
            {"n_participants": (4,)},
            seed_policy="automatic",
        )
    with pytest.raises(TypeError, match="sequence of levels"):
        expand_functional_simulation_scenarios(
            base,
            {"score_distribution": "normal"},
        )
    with pytest.raises(ValueError, match="at least one level"):
        expand_functional_simulation_scenarios(
            base,
            {"n_participants": ()},
        )

    mapping = expand_functional_simulation_scenarios(
        base,
        {"missingness": ({"kind": "mcar", "probability": 0.1},)},
    )
    array = expand_functional_simulation_scenarios(
        base,
        {"measurement_noise_covariance": (np.array([[0.0]]),)},
    )
    long_sequence = expand_functional_simulation_scenarios(
        base,
        {"dimension_names": (("a", "b", "c", "d", "e"),)},
    )
    assert "mcar" in mapping[0].name
    assert "array1" in array[0].name
    assert "seq5" in long_sequence[0].name


def test_existing_synthetic_generators_fail_closed_on_invalid_sizes():
    with pytest.raises(ValueError, match="at least 2 participants"):
        simulate_planar_trajectories(n_participants=1)
    with pytest.raises(ValueError, match="at least 2 curves"):
        simulate_aoi_probability_trajectories(n_curves=1)


def _public_simulation_kwargs(**updates):
    values = {
        "mean": _mean,
        "eigenfunctions": (_phi1,),
        "eigenvalues": (1.0,),
        "truth_grid": np.linspace(0.0, 1.0, 21),
        "n_participants": 4,
        "measurement_noise_sd": 0.0,
        "random_state": 19,
    }
    values.update(updates)
    return values


def test_scenario_additional_noise_and_tuple_audit_paths():
    with pytest.raises(ValueError, match="finite and non-negative"):
        _base_scenario(measurement_noise_sd=-0.1)

    multichannel = FunctionalSimulationScenario(
        name="vector-noise",
        truth_grid=np.linspace(0.0, 1.0, 21),
        eigenvalues=(1.0,),
        n_participants=4,
        dimension_names=("x", "y"),
        measurement_noise_sd=(0.1, 0.2),
    )
    assert multichannel.measurement_noise_sd == (0.1, 0.2)

    irregular = _base_scenario(
        name="irregular-range",
        observation_design="irregular",
        samples_per_curve=(5, 8),
    )
    frame = functional_simulation_scenario_frame([irregular])
    assert frame.loc[0, "samples_per_curve_min"] == 5
    assert frame.loc[0, "samples_per_curve_max"] == 8


@pytest.mark.parametrize(
    ("updates", "message"),
    [
        ({"n_participants": 0}, "n_participants"),
        ({"trials_per_participant": 0}, "trials_per_participant"),
        ({"dimension_names": ("value", "value")}, "dimension_names"),
        (
            {"observation_design": "dense", "samples_per_curve": 5},
            "dense observation_design",
        ),
        (
            {
                "observation_design": "irregular",
                "observation_times": (
                    np.array([0.0, 0.5, 1.0]),
                ) * 4,
                "samples_per_curve": 3,
            },
            "specify observation_times or samples_per_curve",
        ),
        ({"observation_design": "unsupported"}, "observation_design"),
        ({"phase_variation": "bad"}, "phase_variation"),
        ({"phase_variation": {"kind": "unknown"}}, "supports only"),
        (
            {"phase_variation": {"kind": "power", "sd": -0.1}},
            "finite and non-negative",
        ),
        ({"missingness": "bad"}, "missingness"),
        (
            {"missingness": {"kind": "mcar", "probability": 1.0}},
            "probability",
        ),
        (
            {"missingness": {"kind": "block", "fraction": 1.0}},
            "fraction",
        ),
        ({"missingness": {"kind": "unknown"}}, "supports"),
    ],
)
def test_public_functional_simulator_fail_closed_paths(updates, message):
    with pytest.raises((TypeError, ValueError), match=message):
        simulate_functional_process(
            **_public_simulation_kwargs(**updates)
        )


def test_recovery_runner_accepts_structured_semantic_assessment():
    scenario = _base_scenario(replicates=2, seed_start=1700)
    metric = next(
        metric
        for metric in functional_recovery_metric_catalog()
        if metric.name == "mean_ise"
    )

    def estimator(observations, declared_scenario):
        return float(np.mean(observations.values))

    def recovery(fitted, truth, declared_scenario):
        return FunctionalRecoveryAssessment(
            values=(
                FunctionalRecoveryValue(
                    metric=metric,
                    value=abs(
                        fitted
                        - float(np.mean(truth.latent_on_truth_grid))
                    ),
                ),
            ),
            provenance={"evaluator": "structured-test"},
        )

    result = run_functional_recovery_scenarios(
        [scenario],
        mean=_mean,
        eigenfunctions=(_phi1,),
        estimator=estimator,
        recovery=recovery,
    )
    assert len(result.metric_definitions) == 1
    frame = functional_recovery_frame(result)
    assert set(frame["metric"]) == {"mean_ise"}
    assert set(frame["direction"]) == {"lower_is_better"}
    assert set(frame["quantity"]) == {"population mean function"}
    assert all(record.status == "ok" for record in result.records)
    assert all(
        record.assessment_provenance["evaluator"]
        == "structured-test"
        for record in result.records
    )


def test_stress_failure_recording_is_explicit_and_has_mcse():
    scenario = _base_scenario(replicates=4, seed_start=1800)

    def failing_estimator(observations, declared_scenario):
        if declared_scenario.name == "dense":
            raise RuntimeError("declared stress failure")
        return observations

    result = run_functional_recovery_scenarios(
        [scenario],
        mean=_mean,
        eigenfunctions=(_phi1,),
        estimator=failing_estimator,
        recovery=lambda fitted, truth, declared: {"ok": 1.0},
        failure_action="record",
    )

    assert all(record.status == "fit_failed" for record in result.records)
    assert functional_recovery_frame(result).empty
    failure = functional_recovery_failure_frame(result).iloc[0]
    assert failure["n_total"] == 4
    assert failure["n_failed"] == 4
    assert failure["failure_proportion"] == pytest.approx(1.0)
    assert failure["failure_mcse"] == pytest.approx(0.0)

    with pytest.raises(RuntimeError, match="declared stress failure"):
        run_functional_recovery_scenarios(
            [scenario],
            mean=_mean,
            eigenfunctions=(_phi1,),
            estimator=failing_estimator,
            recovery=lambda fitted, truth, declared: {"ok": 1.0},
        )


def test_recovery_summary_retains_distribution_and_failure_statistics():
    metric = next(
        metric
        for metric in functional_recovery_metric_catalog()
        if metric.name == "score_rmse"
    )
    records = tuple(
        FunctionalRecoveryRecord(
            scenario_name="summary",
            replicate=index,
            seed=2000 + index,
            metrics={f"score_rmse.component_1": value},
            metric_values=(
                FunctionalRecoveryValue(
                    metric=metric,
                    value=value,
                    component=0,
                ),
            ),
        )
        for index, value in enumerate((1.0, 2.0, 3.0, 4.0))
    )
    result = FunctionalRecoveryResult(
        records=records,
        metric_definitions=(metric,),
    )
    summary = functional_recovery_summary_frame(result).iloc[0]
    assert summary["n"] == 4
    assert summary["mean"] == pytest.approx(2.5)
    assert summary["median"] == pytest.approx(2.5)
    assert summary["sd"] == pytest.approx(np.std([1, 2, 3, 4], ddof=1))
    assert summary["iqr"] == pytest.approx(1.5)
    assert summary["mcse_mean"] == pytest.approx(
        np.std([1, 2, 3, 4], ddof=1) / 2.0
    )
    assert summary["failure_proportion"] == pytest.approx(0.0)


def test_recovery_record_failure_contracts_and_action_validation():
    with pytest.raises(ValueError, match="unknown"):
        FunctionalRecoveryRecord(
            scenario_name="bad",
            replicate=0,
            seed=1,
            metrics={"x": 1.0},
            status="mystery",
        )
    with pytest.raises(ValueError, match="must not contain"):
        FunctionalRecoveryRecord(
            scenario_name="bad",
            replicate=0,
            seed=1,
            metrics={"x": 1.0},
            status="fit_failed",
            error_type="RuntimeError",
            error_message="failure",
        )
    with pytest.raises(ValueError, match="require error"):
        FunctionalRecoveryRecord(
            scenario_name="bad",
            replicate=0,
            seed=1,
            metrics={},
            status="fit_failed",
        )
    with pytest.raises(ValueError, match="failure_action"):
        run_functional_recovery_scenarios(
            [_base_scenario(replicates=1)],
            mean=_mean,
            eigenfunctions=(_phi1,),
            estimator=lambda observations, declared: observations,
            recovery=lambda fitted, truth, declared: {"ok": 1.0},
            failure_action="ignore",
        )


def test_recovery_result_rejects_duplicate_metric_definitions():
    metric = next(iter(functional_recovery_metric_catalog()))
    record = FunctionalRecoveryRecord(
        scenario_name="x",
        replicate=0,
        seed=1,
        metrics={"x": 1.0},
    )
    with pytest.raises(ValueError, match="unique"):
        FunctionalRecoveryResult(
            records=(record,),
            metric_definitions=(metric, metric),
        )


def test_stress_runner_records_simulation_and_recovery_failures():
    scenario = _base_scenario(replicates=1, seed_start=2100)

    def failing_mean(time):
        raise RuntimeError("declared simulation failure")

    simulation_failure = run_functional_recovery_scenarios(
        [scenario],
        mean=failing_mean,
        eigenfunctions=(_phi1,),
        estimator=lambda observations, declared: observations,
        recovery=lambda fitted, truth, declared: {"ok": 1.0},
        failure_action="record",
    )
    simulation_record = simulation_failure.records[0]
    assert simulation_record.status == "simulation_failed"
    assert simulation_record.error_type == "RuntimeError"
    assert simulation_record.error_message == "declared simulation failure"

    def failing_recovery(fitted, truth, declared):
        raise RuntimeError("declared recovery failure")

    recovery_failure = run_functional_recovery_scenarios(
        [scenario],
        mean=_mean,
        eigenfunctions=(_phi1,),
        estimator=lambda observations, declared: observations,
        recovery=failing_recovery,
        failure_action="record",
    )
    recovery_record = recovery_failure.records[0]
    assert recovery_record.status == "recovery_failed"
    assert recovery_record.error_type == "RuntimeError"
    assert recovery_record.error_message == "declared recovery failure"

    failure_frame = functional_recovery_failure_frame(
        recovery_failure
    ).iloc[0]
    assert failure_frame["n_failed"] == 1
    assert failure_frame["failure_proportion"] == pytest.approx(1.0)


def test_stress_runner_fail_fast_preserves_simulation_and_recovery_errors():
    scenario = _base_scenario(replicates=1, seed_start=2200)

    def failing_mean(time):
        raise RuntimeError("simulation fail-fast")

    with pytest.raises(RuntimeError, match="simulation fail-fast"):
        run_functional_recovery_scenarios(
            [scenario],
            mean=failing_mean,
            eigenfunctions=(_phi1,),
            estimator=lambda observations, declared: observations,
            recovery=lambda fitted, truth, declared: {"ok": 1.0},
        )

    def failing_recovery(fitted, truth, declared):
        raise RuntimeError("recovery fail-fast")

    with pytest.raises(RuntimeError, match="recovery fail-fast"):
        run_functional_recovery_scenarios(
            [scenario],
            mean=_mean,
            eigenfunctions=(_phi1,),
            estimator=lambda observations, declared: observations,
            recovery=failing_recovery,
        )
