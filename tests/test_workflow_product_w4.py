import json

import matplotlib
matplotlib.use("Agg")

import numpy as np
import pandas as pd
import pytest

import eyetrajectoriespy as et
from eyetrajectoriespy.workflows import (
    FPCAWorkflowConfig,
    FunctionOnScalarWorkflowConfig,
    PreprocessingPlan,
    PreprocessingStepConfig,
    RecurrenceWorkflowConfig,
    SUPPORTED_WORKFLOW_PLOTS,
    export_workflow_bundle,
    plot_workflow_result,
    run_fpca_workflow,
    run_function_on_scalar_workflow,
    run_recurrence_workflow,
    save_workflow_figure,
)


def _trajectory_set():
    time = np.linspace(0.0, 4.0, 81)
    phase = np.linspace(0.0, 0.6, 8)
    values = []
    for offset in phase:
        x = 0.5 + 0.2 * np.sin(2.0 * np.pi * (time / 2.0 + offset))
        y = 0.5 + 0.15 * np.cos(2.0 * np.pi * (time / 2.0 + offset))
        values.append(np.column_stack((x, y)))
    trajectories = et.TrajectorySet(
        time=time,
        values=np.asarray(values),
        curve_ids=tuple(f"C{i:02d}" for i in range(8)),
        dimension_names=("x", "y"),
        coordinate_system="normalized",
        time_unit="s",
    )
    design = pd.DataFrame(
        {
            "curve_id": trajectories.curve_ids,
            "condition": np.linspace(-1.0, 1.0, trajectories.n_curves),
        }
    )
    return trajectories, design


def test_recurrence_workflow_executes_explicit_m_tau_epsilon_contract():
    trajectories, _ = _trajectory_set()
    result = run_recurrence_workflow(
        trajectories,
        config=RecurrenceWorkflowConfig(
            curve="C00",
            dimensions=("x",),
            embedding_dimension=3,
            delay=2,
            radius=0.12,
            theiler_window=2,
            min_diagonal_length=2,
            min_vertical_length=2,
        ),
    )

    assert result.workflow_contract == "recurrence:v1"
    assert result.embedding.embedding_dimension == 3
    assert result.embedding.delay_samples == 2
    assert result.recurrence.radius == pytest.approx(0.12)
    assert result.recurrence.target_recurrence_rate is None
    assert result.recurrence.theiler_window_samples == 2
    assert result.metrics.min_diagonal_length == 2
    assert result.metrics.min_vertical_length == 2
    assert [step.name for step in result.steps] == [
        "delay_embedding",
        "recurrence",
        "rqa",
    ]
    assert result.decisions["radius"].source == "analyst"
    assert result.decisions["resolved_delay_samples"].source == "derived"
    assert result.provenance["fixed_radius_policy"] is True
    assert result.provenance["target_recurrence_rate_selection_performed"] is False
    assert result.provenance["automatic_embedding_parameter_selection"] is False
    assert result.provenance["automatic_rqa_parameter_selection"] is False
    assert "fixed radius" in result.reports["rqa"]
    assert len(result.tables["rqa_metrics"]) == 1


def test_recurrence_config_and_preprocessing_fail_closed():
    with pytest.raises(ValueError, match="dimensions"):
        RecurrenceWorkflowConfig(
            curve=0,
            dimensions=(),
            embedding_dimension=2,
            delay=1,
            radius=0.1,
        )
    with pytest.raises(ValueError, match="duplicates"):
        RecurrenceWorkflowConfig(
            curve=0,
            dimensions=("x", "x"),
            embedding_dimension=2,
            delay=1,
            radius=0.1,
        )
    with pytest.raises(ValueError, match="embedding_dimension"):
        RecurrenceWorkflowConfig(
            curve=0,
            dimensions=("x",),
            embedding_dimension=0,
            delay=1,
            radius=0.1,
        )
    with pytest.raises(ValueError, match="radius"):
        RecurrenceWorkflowConfig(
            curve=0,
            dimensions=("x",),
            embedding_dimension=2,
            delay=1,
            radius=0.0,
        )
    with pytest.raises(ValueError, match="metric"):
        RecurrenceWorkflowConfig(
            curve=0,
            dimensions=("x",),
            embedding_dimension=2,
            delay=1,
            radius=0.1,
            metric="automatic",
        )
    with pytest.raises(ValueError, match="min_diagonal_length"):
        RecurrenceWorkflowConfig(
            curve=0,
            dimensions=("x",),
            embedding_dimension=2,
            delay=1,
            radius=0.1,
            min_diagonal_length=0,
        )

    trajectories, _ = _trajectory_set()
    config = RecurrenceWorkflowConfig(
        curve=0,
        dimensions=("x",),
        embedding_dimension=2,
        delay=1,
        radius=0.1,
        preprocessing=PreprocessingPlan(
            steps=(
                PreprocessingStepConfig(
                    function="smooth",
                    parameters={"bandwidth": 0.1},
                    scientific_effect="changes the state trajectory",
                ),
            )
        ),
    )
    with pytest.raises(ValueError, match="empty preprocessing"):
        run_recurrence_workflow(trajectories, config=config)
    with pytest.raises(TypeError, match="TrajectorySet"):
        run_recurrence_workflow(object(), config=config)
    with pytest.raises(TypeError, match="RecurrenceWorkflowConfig"):
        run_recurrence_workflow(trajectories, config=object())


def test_workflow_plotting_requires_explicit_scientific_selector(tmp_path):
    trajectories, design = _trajectory_set()
    fpca = run_fpca_workflow(
        trajectories,
        config=FPCAWorkflowConfig(n_components=2, scaling="dimension_sd"),
    )
    fos = run_function_on_scalar_workflow(
        trajectories,
        design,
        config=FunctionOnScalarWorkflowConfig(
            predictors=("condition",),
            dimensions=("x",),
        ),
    )
    recurrence = run_recurrence_workflow(
        trajectories,
        config=RecurrenceWorkflowConfig(
            curve=0,
            dimensions=("x",),
            embedding_dimension=2,
            delay=2,
            radius=0.12,
            theiler_window=1,
        ),
    )

    assert "fpca_component" in SUPPORTED_WORKFLOW_PLOTS
    assert "recurrence" in SUPPORTED_WORKFLOW_PLOTS

    with pytest.raises(ValueError, match="component"):
        plot_workflow_result(fpca, plot="fpca_component")
    with pytest.raises(ValueError, match="dimension"):
        plot_workflow_result(fpca, plot="fpca_component", component=0)
    with pytest.raises(ValueError, match="coefficient"):
        plot_workflow_result(fos, plot="function_on_scalar_coefficient")
    with pytest.raises(ValueError, match="one of"):
        plot_workflow_result(fpca, plot="automatic_best_plot")
    with pytest.raises(TypeError, match="RecurrenceWorkflowResult"):
        plot_workflow_result(fpca, plot="recurrence")

    ax = plot_workflow_result(
        fpca,
        plot="fpca_component",
        component=0,
        dimension="x",
    )
    assert "FPC1" in ax.get_title()
    ax.figure.clf()

    coefficient_ax = plot_workflow_result(
        fos,
        plot="function_on_scalar_coefficient",
        coefficient="condition",
        dimension="x",
    )
    assert "condition" in coefficient_ax.get_title()
    coefficient_ax.figure.clf()

    recurrence_path = save_workflow_figure(
        recurrence,
        tmp_path / "recurrence.svg",
        plot="recurrence",
    )
    assert recurrence_path.is_file()
    assert recurrence_path.stat().st_size > 0

    with pytest.raises(ValueError, match="\.png"):
        save_workflow_figure(
            recurrence,
            tmp_path / "recurrence.txt",
            plot="recurrence",
        )
    with pytest.raises(ValueError, match="dpi"):
        save_workflow_figure(
            recurrence,
            tmp_path / "recurrence.png",
            plot="recurrence",
            dpi=0,
        )


def test_workflow_plot_dispatch_type_and_selector_guards():
    with pytest.raises(TypeError, match="component"):
        plot_workflow_result(
            object(),
            plot="sparse_fpca_component",
            component=True,
        )
    with pytest.raises(TypeError, match="FPCAWorkflowResult"):
        plot_workflow_result(
            object(),
            plot="fpca_component",
            component=0,
        )
    with pytest.raises(TypeError, match="SparseFPCAWorkflowResult"):
        plot_workflow_result(
            object(),
            plot="sparse_fpca_component",
            component=0,
        )
    with pytest.raises(TypeError, match="SparseMFPCAWorkflowResult"):
        plot_workflow_result(
            object(),
            plot="sparse_mfpca_component",
            component=0,
        )
    with pytest.raises(TypeError, match="FunctionOnScalarWorkflowResult"):
        plot_workflow_result(
            object(),
            plot="function_on_scalar_coefficient",
            coefficient="condition",
        )
    with pytest.raises(TypeError, match="FunctionalMixedEffectsWorkflowResult"):
        plot_workflow_result(
            object(),
            plot="functional_mixed_effects_coefficient",
            coefficient="condition",
        )
    with pytest.raises(TypeError, match="GeneralizedFunctionalWorkflowResult"):
        plot_workflow_result(
            object(),
            plot="generalized_functional_coefficient",
            coefficient="condition",
        )


def test_recurrence_workflow_bundle_is_portable_and_auditable(tmp_path):
    trajectories, _ = _trajectory_set()
    result = run_recurrence_workflow(
        trajectories,
        config=RecurrenceWorkflowConfig(
            curve="C00",
            dimensions=("x",),
            embedding_dimension=2,
            delay=2,
            radius=0.12,
            theiler_window=1,
        ),
    )
    destination = export_workflow_bundle(
        result,
        tmp_path / "recurrence-bundle",
    )

    manifest = json.loads(
        (destination / "workflow.json").read_text(encoding="utf-8")
    )
    portable = json.loads(
        (destination / "result" / "manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["workflow_contract"] == "recurrence:v1"
    assert "rqa.txt" in manifest["reports"]
    assert "rqa_metrics.csv" in manifest["tables"]
    assert "config.json" in (destination / "SHA256SUMS").read_text()
    assert any(
        path.endswith(".recurrence.matrix")
        for path in portable["nonportable_fields"]
    )
