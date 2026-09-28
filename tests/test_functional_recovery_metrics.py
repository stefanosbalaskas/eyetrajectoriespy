import numpy as np
import pandas as pd
import pytest

from eyetrajectoriespy import (
    FPCAResult,
    FunctionalMixedEffectsResult,
    FunctionalRecoveryAssessment,
    FunctionalRecoveryMetric,
    FunctionalRecoveryValue,
    FunctionalSimulationScenario,
    RegistrationResult,
    SparseFPCAResult,
    evaluate_fpca_recovery,
    evaluate_functional_mixed_effects_recovery,
    evaluate_hierarchy_truth_recovery,
    evaluate_registration_recovery,
    evaluate_sparse_fpca_recovery,
    functional_recovery_assessment_frame,
    functional_recovery_metric_catalog,
    functional_recovery_metric_catalog_frame,
    functional_trapezoid_weights,
    simulate_functional_scenario,
)


def _mean(time):
    time = np.asarray(time, dtype=float)
    return (0.25 + 0.30 * time)[:, None]


def _phi1(time):
    time = np.asarray(time, dtype=float)
    return (np.sqrt(2.0) * np.sin(np.pi * time))[:, None]


def _phi2(time):
    time = np.asarray(time, dtype=float)
    return (np.sqrt(2.0) * np.sin(2.0 * np.pi * time))[:, None]


def _phi3(time):
    time = np.asarray(time, dtype=float)
    return (np.sqrt(2.0) * np.sin(3.0 * np.pi * time))[:, None]


def _simulation(*, eigenvalues=(1.0, 0.35), eigenfunctions=(_phi1, _phi2)):
    scenario = FunctionalSimulationScenario(
        name="metric-truth",
        truth_grid=np.linspace(0.0, 1.0, 81),
        eigenvalues=eigenvalues,
        n_participants=40,
        measurement_noise_sd=0.0,
        replicates=1,
        seed_start=512,
    )
    return simulate_functional_scenario(
        scenario,
        mean=_mean,
        eigenfunctions=eigenfunctions,
    )


def _exact_fpca_result(simulation, *, order=(0, 1), signs=(1.0, 1.0)):
    truth = simulation.truth
    grid = truth.truth_grid
    weights = functional_trapezoid_weights(grid)
    order = np.asarray(order, dtype=int)
    signs = np.asarray(signs, dtype=float)
    return FPCAResult(
        mean=truth.mean.copy(),
        components=(
            truth.eigenfunctions[order]
            * signs[:, None, None]
        ),
        scores=(
            truth.scores[:, order]
            * signs[None, :]
        ),
        explained_variance=truth.eigenvalues[order].copy(),
        explained_variance_ratio=(
            truth.eigenvalues[order]
            / np.sum(truth.eigenvalues[order])
        ),
        time=grid.copy(),
        dimension_names=truth.dimension_names,
        coordinate_system=truth.coordinate_system,
        time_unit=truth.time_unit,
        curve_ids=tuple(
            f"curve_{index:03d}"
            for index in range(truth.scores.shape[0])
        ),
        weights=weights,
        scale=np.ones(1, dtype=float),
        provenance={"fpca": {"scaling": "none"}},
    )


def test_metric_catalog_has_explicit_semantics():
    catalog = functional_recovery_metric_catalog()
    assert catalog
    assert len({metric.name for metric in catalog}) == len(catalog)
    assert {
        "mean_ise",
        "eigenvalue_relative_error",
        "component_absolute_similarity",
        "subspace_principal_cosine",
        "score_rmse",
        "noise_variance_relative_error",
    } <= {metric.name for metric in catalog}

    frame = functional_recovery_metric_catalog_frame()
    assert {
        "metric",
        "quantity",
        "direction",
        "units",
        "scope",
        "description",
    } <= set(frame.columns)
    assert set(frame["direction"]) <= {
        "higher_is_better",
        "lower_is_better",
    }


def test_metric_and_assessment_contracts_fail_closed():
    with pytest.raises(ValueError, match="non-empty"):
        FunctionalRecoveryMetric(
            name=" ",
            quantity="q",
            direction="lower_is_better",
            units="u",
            scope="s",
            description="d",
        )
    with pytest.raises(ValueError, match="direction"):
        FunctionalRecoveryMetric(
            name="x",
            quantity="q",
            direction="unknown",
            units="u",
            scope="s",
            description="d",
        )
    metric = functional_recovery_metric_catalog()[0]
    with pytest.raises(ValueError, match="finite"):
        FunctionalRecoveryValue(metric=metric, value=np.nan)
    with pytest.raises(ValueError, match="non-negative"):
        FunctionalRecoveryValue(
            metric=metric,
            value=1.0,
            component=-1,
        )
    value = FunctionalRecoveryValue(metric=metric, value=1.0)
    with pytest.raises(ValueError, match="duplicate"):
        FunctionalRecoveryAssessment(values=(value, value))


def test_dense_fpca_recovery_is_sign_and_permutation_invariant():
    simulation = _simulation()
    fitted = _exact_fpca_result(
        simulation,
        order=(1, 0),
        signs=(-1.0, 1.0),
    )
    assessment = evaluate_fpca_recovery(
        fitted,
        simulation.truth,
    )
    frame = functional_recovery_assessment_frame(assessment)

    similarities = frame.loc[
        frame["metric"] == "component_absolute_similarity",
        "value",
    ].to_numpy()
    score_correlations = frame.loc[
        frame["metric"] == "score_correlation",
        "value",
    ].to_numpy()
    score_rmse = frame.loc[
        frame["metric"] == "score_rmse",
        "value",
    ].to_numpy()
    cosines = frame.loc[
        frame["metric"] == "subspace_principal_cosine",
        "value",
    ].to_numpy()

    np.testing.assert_allclose(similarities, 1.0, atol=1e-10)
    np.testing.assert_allclose(score_correlations, 1.0, atol=1e-10)
    np.testing.assert_allclose(score_rmse, 0.0, atol=1e-10)
    np.testing.assert_allclose(cosines, 1.0, atol=1e-10)
    assert assessment.provenance["matched_truth_components"] == [1, 0]


def test_dense_fpca_recovery_requires_exact_grid_and_unscaled_coordinates():
    simulation = _simulation()
    fitted = _exact_fpca_result(simulation)

    shifted = FPCAResult(
        **{
            **fitted.__dict__,
            "time": fitted.time + 1e-6,
        }
    )
    with pytest.raises(ValueError, match="truth_grid"):
        evaluate_fpca_recovery(shifted, simulation.truth)

    scaled = FPCAResult(
        **{
            **fitted.__dict__,
            "scale": np.array([2.0]),
            "provenance": {"fpca": {"scaling": "dimension_sd"}},
        }
    )
    with pytest.raises(ValueError, match="scaling='none'"):
        evaluate_fpca_recovery(scaled, simulation.truth)


def test_sparse_recovery_uses_full_fitted_covariance_not_returned_rank():
    simulation = _simulation(
        eigenvalues=(1.0, 0.35, 0.12),
        eigenfunctions=(_phi1, _phi2, _phi3),
    )
    truth = simulation.truth
    grid = truth.truth_grid
    weights = functional_trapezoid_weights(grid)
    phi = truth.eigenfunctions[:, :, 0]
    full_covariance = sum(
        float(eigenvalue) * np.outer(component, component)
        for eigenvalue, component in zip(
            truth.eigenvalues,
            phi,
            strict=True,
        )
    )

    result = SparseFPCAResult(
        scores=truth.scores[:, :2].copy(),
        eigenvalues=truth.eigenvalues[:2].copy(),
        dimension="value",
        curve_ids=tuple(
            f"curve_{index:03d}"
            for index in range(truth.scores.shape[0])
        ),
        metadata=pd.DataFrame(
            {"participant_id": np.arange(truth.scores.shape[0])}
        ),
        coordinate_system=truth.coordinate_system,
        time_unit=truth.time_unit,
        n_components=2,
        fit_method="native_covariance",
        fit_smoothing="local_linear_epanechnikov",
        score_method="PACE",
        score_smoothing=None,
        tolerance=1e-10,
        normalize=False,
        provenance={
            "sparse_fpca": {
                "noise_variance_method": "fixed",
                "measurement_error_variance_supplied": 0.0,
            }
        },
        evaluation_grid=grid.copy(),
        mean=truth.mean[:, 0].copy(),
        covariance=full_covariance,
        eigenfunctions=phi[:2].copy(),
        noise_variance=0.0,
        quadrature_weights=weights,
        score_diagnostics=pd.DataFrame(
            {
                "status_code": ["ok"] * truth.scores.shape[0],
                "condition_number": np.linspace(
                    10.0,
                    100.0,
                    truth.scores.shape[0],
                ),
            }
        ),
        covariance_diagnostics={
            "applied_action": "none",
            "relative_operator_correction_frobenius_norm": 0.0,
        },
    )

    assessment = evaluate_sparse_fpca_recovery(result, truth)
    frame = functional_recovery_assessment_frame(assessment)
    covariance_ise = float(
        frame.loc[frame["metric"] == "covariance_ise", "value"].iloc[0]
    )
    assert covariance_ise == pytest.approx(0.0, abs=1e-12)
    assert {
        "score_condition_number_median",
        "score_condition_number_q95",
        "score_condition_number_max",
        "psd_repair_applied",
        "noise_variance_absolute_error",
    } <= set(frame["metric"])


def test_sparse_recovery_preserves_fixed_vs_estimated_noise_semantics():
    simulation = _simulation()
    truth = simulation.truth
    grid = truth.truth_grid
    weights = functional_trapezoid_weights(grid)
    phi = truth.eigenfunctions[:, :, 0]
    covariance = sum(
        float(eigenvalue) * np.outer(component, component)
        for eigenvalue, component in zip(
            truth.eigenvalues,
            phi,
            strict=True,
        )
    )

    def make_result(method):
        provenance = {
            "sparse_fpca": {
                "noise_variance_method": method,
            }
        }
        if method == "fixed":
            provenance["sparse_fpca"][
                "measurement_error_variance_supplied"
            ] = 0.0
        return SparseFPCAResult(
            scores=truth.scores.copy(),
            eigenvalues=truth.eigenvalues.copy(),
            dimension="value",
            curve_ids=tuple(
                f"curve_{index:03d}"
                for index in range(truth.scores.shape[0])
            ),
            metadata=pd.DataFrame(index=np.arange(truth.scores.shape[0])),
            coordinate_system=truth.coordinate_system,
            time_unit=truth.time_unit,
            n_components=2,
            fit_method="native_covariance",
            fit_smoothing="local_linear_epanechnikov",
            score_method="PACE",
            score_smoothing=None,
            tolerance=1e-10,
            normalize=False,
            provenance=provenance,
            evaluation_grid=grid.copy(),
            mean=truth.mean[:, 0].copy(),
            covariance=covariance,
            eigenfunctions=phi.copy(),
            noise_variance=0.0,
            quadrature_weights=weights,
            score_diagnostics=pd.DataFrame(),
            covariance_diagnostics={
                "applied_action": "none",
                "relative_operator_correction_frobenius_norm": 0.0,
            },
        )

    fixed = evaluate_sparse_fpca_recovery(
        make_result("fixed"),
        truth,
    )
    estimated = evaluate_sparse_fpca_recovery(
        make_result("diagonal_difference"),
        truth,
    )
    assert fixed.provenance["noise_variance_method"] == "fixed"
    assert fixed.provenance[
        "measurement_error_variance_supplied"
    ] == 0.0
    assert (
        estimated.provenance["noise_variance_method"]
        == "diagonal_difference"
    )
    assert estimated.provenance[
        "measurement_error_variance_supplied"
    ] is None


def test_hierarchy_truth_recovery_keeps_sources_separate():
    scenario = FunctionalSimulationScenario(
        name="hierarchy",
        truth_grid=np.linspace(0.0, 1.0, 41),
        eigenvalues=(1.0, 0.35),
        n_participants=30,
        trials_per_participant=3,
        participant_eigenvalues=(0.20, 0.08),
        trial_eigenvalues=(0.10, 0.04),
        measurement_noise_sd=0.0,
        replicates=1,
        seed_start=91,
    )
    simulation = simulate_functional_scenario(
        scenario,
        mean=_mean,
        eigenfunctions=(_phi1, _phi2),
    )
    assessment = evaluate_hierarchy_truth_recovery(
        simulation.truth
    )
    frame = functional_recovery_assessment_frame(assessment)
    assert set(frame["source"]) == {
        "curve",
        "participant",
        "trial",
    }
    assert set(frame["metric"]) == {
        "source_variance_absolute_error",
        "source_variance_relative_error",
    }


def test_registration_recovery_targets_inverse_simulator_warp():
    scenario = FunctionalSimulationScenario(
        name="phase-truth",
        truth_grid=np.linspace(0.0, 1.0, 81),
        eigenvalues=(1.0,),
        n_participants=12,
        measurement_noise_sd=0.0,
        phase_variation={"kind": "power", "sd": 0.20},
        replicates=1,
        seed_start=812,
    )
    simulation = simulate_functional_scenario(
        scenario,
        mean=_mean,
        eigenfunctions=(_phi1,),
    )
    grid = simulation.truth.truth_grid
    generated = simulation.truth.phase_warps_on_truth_grid
    inverse = np.stack(
        [
            np.interp(grid, generated[curve], grid)
            for curve in range(generated.shape[0])
        ],
        axis=0,
    )
    result = RegistrationResult(
        registered=simulation.observations,
        original=simulation.observations,
        warping_functions=inverse,
        reference_landmarks=np.array([0.5]),
        observed_landmarks=inverse[:, [len(grid) // 2]],
        method="known_truth_test",
    )
    assessment = evaluate_registration_recovery(
        result,
        simulation.truth,
    )
    frame = functional_recovery_assessment_frame(assessment)
    assert set(frame["metric"]) == {
        "phase_warp_ise",
        "phase_warp_max_absolute_error",
    }
    np.testing.assert_allclose(frame["value"], 0.0, atol=1e-12)
    assert assessment.provenance["truth_target"] == "inverse_phase_warp"


def _exact_mixed_effects_result(truth, *, include_trial=True):
    result = object.__new__(FunctionalMixedEffectsResult)
    object.__setattr__(result, "time", truth.truth_grid.copy())
    object.__setattr__(result, "dimension_name", "value")
    object.__setattr__(result, "coefficient_names", ("Intercept",))
    object.__setattr__(
        result,
        "coefficient_functions",
        truth.mean[:, 0][None, :].copy(),
    )
    basis = truth.eigenfunctions[:, :, 0].T.copy()
    object.__setattr__(result, "random_basis", basis)
    object.__setattr__(
        result,
        "random_intercept_covariance",
        np.diag(truth.participant_eigenvalues),
    )
    object.__setattr__(result, "random_slope_predictor", None)
    object.__setattr__(
        result,
        "trial_random_effect",
        "functional_intercept" if include_trial else None,
    )
    object.__setattr__(
        result,
        "trial_random_basis",
        basis if include_trial else None,
    )
    object.__setattr__(
        result,
        "trial_random_effect_covariance",
        (
            np.diag(truth.trial_eigenvalues)
            if include_trial
            else None
        ),
    )
    return result


def test_mixed_effects_recovery_compares_time_domain_variance_functions():
    scenario = FunctionalSimulationScenario(
        name="mixed-truth",
        truth_grid=np.linspace(0.0, 1.0, 81),
        eigenvalues=(1.0, 0.35),
        n_participants=20,
        trials_per_participant=3,
        participant_eigenvalues=(0.20, 0.08),
        trial_eigenvalues=(0.10, 0.04),
        measurement_noise_sd=0.0,
        replicates=1,
        seed_start=991,
    )
    simulation = simulate_functional_scenario(
        scenario,
        mean=_mean,
        eigenfunctions=(_phi1, _phi2),
    )
    fitted = _exact_mixed_effects_result(
        simulation.truth,
        include_trial=True,
    )
    assessment = evaluate_functional_mixed_effects_recovery(
        fitted,
        simulation.truth,
    )
    frame = functional_recovery_assessment_frame(assessment)
    assert {
        "coefficient_function_ise",
        "source_variance_function_ise",
        "source_integrated_variance_absolute_error",
        "source_integrated_variance_relative_error",
    } <= set(frame["metric"])
    assert set(frame["source"]) == {
        "intercept",
        "participant",
        "trial",
    }
    np.testing.assert_allclose(frame["value"], 0.0, atol=1e-12)
    assert (
        assessment.provenance[
            "basis_covariance_compared_directly_to_kl_eigenvalues"
        ]
        is False
    )


def test_mixed_effects_recovery_rejects_missing_declared_trial_level():
    scenario = FunctionalSimulationScenario(
        name="mixed-trial-truth",
        truth_grid=np.linspace(0.0, 1.0, 41),
        eigenvalues=(1.0,),
        n_participants=10,
        trials_per_participant=2,
        participant_eigenvalues=(0.2,),
        trial_eigenvalues=(0.1,),
        measurement_noise_sd=0.0,
        replicates=1,
        seed_start=992,
    )
    simulation = simulate_functional_scenario(
        scenario,
        mean=_mean,
        eigenfunctions=(_phi1,),
    )
    fitted = _exact_mixed_effects_result(
        simulation.truth,
        include_trial=False,
    )
    with pytest.raises(ValueError, match="trial functional variance"):
        evaluate_functional_mixed_effects_recovery(
            fitted,
            simulation.truth,
        )
