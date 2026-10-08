from dataclasses import fields

import numpy as np
import pandas as pd
import pytest

import eyetrajectoriespy as et
from eyetrajectoriespy.workflows import (
    FPCAWorkflowConfig,
    FunctionOnScalarWorkflowConfig,
    FunctionalMixedEffectsWorkflowConfig,
    GeneralizedFunctionalWorkflowConfig,
    PreprocessingPlan,
    PreprocessingStepConfig,
    export_workflow_bundle,
    run_fpca_workflow,
    run_function_on_scalar_workflow,
    run_functional_mixed_effects_workflow,
    run_generalized_functional_workflow,
)


def _dense_data(seed=2026):
    rng = np.random.default_rng(seed)
    n = 24
    time = np.linspace(0.0, 1.0, 11)
    condition = np.linspace(-1.0, 1.0, n)
    signal = (
        (0.2 + 0.15 * time)[None, :]
        + condition[:, None] * (0.4 - 0.1 * time)[None, :]
        + rng.normal(0.0, 0.03, size=(n, time.size))
    )
    trajectories = et.TrajectorySet(
        time=time,
        values=np.stack([signal, 1.5 * signal], axis=2),
        curve_ids=tuple(f"C{i:02d}" for i in range(n)),
        dimension_names=("signal", "scaled"),
        coordinate_system="normalized",
        time_unit="s",
    )
    design = pd.DataFrame(
        {"curve_id": trajectories.curve_ids, "condition": condition}
    )
    return trajectories, design


def _mixed_data(seed=2026):
    rng = np.random.default_rng(seed)
    n_participants = 12
    trials = 3
    time = np.linspace(0.0, 1.0, 9)
    participants = np.repeat(
        [f"P{i:02d}" for i in range(n_participants)],
        trials,
    )
    condition = np.tile(np.array([0.0, 1.0, 0.5]), n_participants)
    intercept = 0.20 + 0.15 * time
    condition_effect = 0.15 + 0.40 * time
    covariance = np.array(
        [
            [0.030, 0.004],
            [0.004, 0.020],
        ]
    )
    random_basis_coefficients = rng.multivariate_normal(
        np.zeros(2),
        covariance,
        size=n_participants,
    )
    linear_basis = np.column_stack([1.0 - time, time])

    values = []
    for participant in range(n_participants):
        random_function = (
            random_basis_coefficients[participant] @ linear_basis.T
        )
        for trial in range(trials):
            index = participant * trials + trial
            response = (
                intercept
                + condition[index] * condition_effect
                + random_function
                + rng.normal(0.0, 0.04, size=time.size)
            )
            values.append(response[:, None])
    trajectories = et.TrajectorySet(
        time=time,
        values=np.asarray(values),
        curve_ids=tuple(f"M{i:03d}" for i in range(len(values))),
        dimension_names=("metric",),
        metadata=pd.DataFrame({"participant_id": participants}),
        coordinate_system="normalized",
        time_unit="s",
    )
    design = pd.DataFrame(
        {"curve_id": trajectories.curve_ids, "condition": condition}
    )
    return trajectories, design


def _binary_data(seed=510):
    rng = np.random.default_rng(seed)
    n_participants = 12
    trials = 3
    time = np.linspace(0.0, 1.0, 5)
    condition = np.tile(np.array([-0.7, 0.0, 0.7]), n_participants)
    participants = np.repeat(
        [f"G{i:02d}" for i in range(n_participants)],
        trials,
    )
    eta = (
        (-0.4 + 0.4 * time)[None, :]
        + condition[:, None] * (0.8 - 0.2 * time)[None, :]
    )
    probability = 1.0 / (1.0 + np.exp(-eta))
    response = rng.binomial(1, probability).astype(float)
    trajectories = et.TrajectorySet(
        time=time,
        values=response[:, :, None],
        curve_ids=tuple(f"B{i:03d}" for i in range(response.shape[0])),
        dimension_names=("target_aoi",),
        metadata=pd.DataFrame({"participant_id": participants}),
        coordinate_system="unknown",
        time_unit="s",
    )
    design = pd.DataFrame(
        {"curve_id": trajectories.curve_ids, "condition": condition}
    )
    return trajectories, design


def test_w3_surface_is_module_scoped():
    import eyetrajectoriespy.workflows as workflows

    names = (
        "run_fpca_workflow",
        "run_function_on_scalar_workflow",
        "run_functional_mixed_effects_workflow",
        "run_generalized_functional_workflow",
    )
    assert all(hasattr(workflows, name) for name in names)
    assert all(not hasattr(et, name) for name in names)


def test_fpca_workflow_executes_and_retains_derived_component_count(tmp_path):
    trajectories, _ = _dense_data()
    result = run_fpca_workflow(
        trajectories,
        config=FPCAWorkflowConfig(
            n_components=0.90,
            scaling="dimension_sd",
        ),
    )

    assert result.workflow_contract == "fpca:v1"
    assert result.fit.n_components >= 1
    assert result.decisions["requested_n_components"].source == "analyst"
    assert result.decisions["retained_n_components"].source == "derived"
    assert result.provenance["automatic_model_selection_performed"] is False
    assert [step.name for step in result.steps] == ["fit"]
    assert {"scores", "explained_variance"} <= set(result.tables)

    destination = export_workflow_bundle(result, tmp_path / "dense-fpca")
    assert (destination / "workflow.json").exists()
    assert (destination / "config.json").exists()
    assert (destination / "result" / "manifest.json").exists()
    assert (destination / "tables" / "scores.csv").exists()
    assert (destination / "SHA256SUMS").exists()


def test_function_on_scalar_workflow_executes_without_hidden_model_changes():
    trajectories, design = _dense_data()
    result = run_function_on_scalar_workflow(
        trajectories,
        design,
        config=FunctionOnScalarWorkflowConfig(
            predictors=("condition",),
            dimensions=("signal",),
        ),
    )

    assert result.workflow_contract == "function_on_scalar:v1"
    assert result.fit.predictor_names == ("condition",)
    assert result.decisions["unit"].value == "curve"
    assert result.provenance["automatic_predictor_encoding"] is False
    assert result.provenance["functional_mixed_effects_inferred"] is False
    assert "coefficients" in result.tables
    assert "Function-on-scalar regression" in result.reports["fit"]


def test_function_on_scalar_participant_unit_is_explicit():
    trajectories, design = _mixed_data()
    participant_design = design.copy()
    participant_design["condition"] = np.repeat(
        np.linspace(-1.0, 1.0, 12),
        3,
    )
    result = run_function_on_scalar_workflow(
        trajectories,
        participant_design,
        config=FunctionOnScalarWorkflowConfig(
            predictors=("condition",),
            participant_column="participant_id",
            unit="participant",
        ),
    )

    assert result.fit.unit == "participant"
    assert result.fit.n_units == 12
    assert result.decisions["participant_column"].value == "participant_id"


def test_functional_mixed_effects_workflow_executes_declared_model():
    trajectories, design = _mixed_data()
    result = run_functional_mixed_effects_workflow(
        trajectories,
        design,
        config=FunctionalMixedEffectsWorkflowConfig(
            predictors=("condition",),
            participant_column="participant_id",
            dimension="metric",
            fixed_basis_size=2,
            random_basis_size=2,
            spline_degree=1,
            reml=True,
            method="lbfgs",
            maxiter=500,
        ),
    )

    assert result.workflow_contract == "functional_mixed_effects:v1"
    assert result.fit.n_participants == 12
    assert result.decisions["residual_correlation"].value == "iid"
    assert result.provenance["automatic_random_effect_selection"] is False
    assert result.provenance["automatic_optimizer_fallback"] is False
    assert "coefficients" in result.tables


def test_generalized_workflow_requires_and_retains_explicit_family():
    trajectories, design = _binary_data()
    result = run_generalized_functional_workflow(
        trajectories,
        design,
        config=GeneralizedFunctionalWorkflowConfig(
            predictors=("condition",),
            participant_column="participant_id",
            dimension="target_aoi",
            family="binomial",
            basis_size=2,
            spline_degree=1,
        ),
    )

    assert result.workflow_contract == "generalized_functional:v1"
    assert result.fit.family == "binomial"
    assert result.decisions["family"].value == "binomial"
    assert result.decisions["binomial_denominator_supplied"].value is False
    assert result.decisions["exposure_supplied"].value is False
    assert result.provenance["automatic_family_selection"] is False
    assert result.provenance["binomial_denominator_inferred"] is False
    assert result.provenance["poisson_exposure_inferred"] is False
    assert "population-averaged marginal interpretation" in result.reports["fit"]


def test_generalized_config_preserves_explicit_denominator_as_read_only():
    denominator = np.full((6, 5), 8.0)
    config = GeneralizedFunctionalWorkflowConfig(
        predictors=("condition",),
        participant_column="participant_id",
        dimension="successes",
        family="binomial",
        binomial_denominator=denominator,
    )

    assert config.binomial_denominator is not denominator
    assert config.binomial_denominator.flags.writeable is False
    np.testing.assert_allclose(config.binomial_denominator, denominator)


def test_w3_configs_fail_closed_on_hidden_or_ambiguous_choices():
    with pytest.raises(ValueError, match="explicitly"):
        GeneralizedFunctionalWorkflowConfig(
            predictors=("condition",),
            participant_column="participant_id",
            dimension="metric",
            family="gaussian",
        )
    with pytest.raises(ValueError, match="participant_column"):
        FunctionOnScalarWorkflowConfig(
            predictors=("condition",),
            unit="participant",
        )
    with pytest.raises(ValueError, match="must be None"):
        FunctionOnScalarWorkflowConfig(
            predictors=("condition",),
            unit="curve",
            participant_column="participant_id",
        )
    with pytest.raises(ValueError, match="duplicates"):
        FunctionOnScalarWorkflowConfig(
            predictors=("condition", "condition"),
        )
    with pytest.raises(ValueError, match="scaling"):
        FPCAWorkflowConfig(scaling="automatic")


def test_w3_workflows_fail_closed_on_nonempty_preprocessing():
    trajectories, _ = _dense_data()
    config = FPCAWorkflowConfig(
        n_components=2,
        preprocessing=PreprocessingPlan(
            steps=(
                PreprocessingStepConfig(
                    function="smooth",
                    parameters={"bandwidth": 0.1},
                    scientific_effect="changes the functional response",
                ),
            )
        ),
    )

    with pytest.raises(ValueError, match="requires an empty preprocessing plan"):
        run_fpca_workflow(trajectories, config=config)


def test_w3_config_surfaces_keep_scientific_parameters_explicit():
    mixed_fields = {field.name for field in fields(FunctionalMixedEffectsWorkflowConfig)}
    generalized_fields = {
        field.name for field in fields(GeneralizedFunctionalWorkflowConfig)
    }
    assert {
        "random_slope_predictor",
        "trial_random_effect",
        "residual_correlation",
        "method",
    } <= mixed_fields
    assert {
        "family",
        "binomial_denominator",
        "exposure",
        "exposure_units",
        "working_correlation",
        "covariance_type",
    } <= generalized_fields
