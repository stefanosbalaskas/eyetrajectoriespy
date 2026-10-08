from dataclasses import fields
import inspect

import numpy as np
import pandas as pd
import pytest

import eyetrajectoriespy as et
from eyetrajectoriespy._sparse_truth import simulate_sparse_functional_truth
from eyetrajectoriespy.workflows import (
    PreprocessingPlan,
    PreprocessingStepConfig,
    ScoreUncertaintyConfig,
    SparseFPCABandwidthSelectionConfig,
    SparseFPCAWorkflowConfig,
    SparseMFPCAAsyncWorkflowConfig,
    SparseMFPCABandwidthSelectionConfig,
    SparseMFPCAWorkflowConfig,
    SparseMultilevelWorkflowConfig,
    SparsePredictionWorkflowConfig,
    export_workflow_bundle,
    run_sparse_fpca_workflow,
    run_sparse_mfpca_workflow,
    run_sparse_mfpca_async_workflow,
    run_sparse_multilevel_workflow,
    run_sparse_prediction_workflow,
    workflow_reporting_text,
)


def _univariate_dataset():
    times, values, truth = simulate_sparse_functional_truth(
        n_curves=24,
        samples_per_curve=10,
        noise_sd=0.10,
        random_state=12021,
    )
    trajectories = et.IrregularTrajectorySet(
        time=times,
        values=tuple(value[:, None] for value in values),
        curve_ids=tuple(f"U{i:02d}" for i in range(len(times))),
        dimension_names=("x",),
        metadata=pd.DataFrame(
            {"participant_id": [f"P{i:02d}" for i in range(len(times))]}
        ),
        coordinate_system="normalized",
        time_unit="normalized",
    )
    return trajectories, truth


def _paired_dataset():
    n_curves = 12
    time = np.linspace(0.0, 1.0, 17)
    phase = 2.0 * np.pi * np.arange(n_curves) / n_curves
    z = np.sqrt(2.0) * np.cos(phase)
    w = np.sqrt(2.0) * np.sin(phase)
    y_score = 0.6 * z + np.sqrt(1.0 - 0.6**2) * w
    mode = np.sin(np.pi * time)
    values = tuple(
        np.column_stack(
            [
                0.15 + 0.2 * time + z[index] * mode,
                -0.1 + 0.1 * time + y_score[index] * mode,
            ]
        )
        for index in range(n_curves)
    )
    return et.IrregularTrajectorySet(
        time=tuple(time.copy() for _ in range(n_curves)),
        values=values,
        curve_ids=tuple(f"M{i:02d}" for i in range(n_curves)),
        dimension_names=("x", "y"),
        metadata=pd.DataFrame(
            {"participant_id": [f"P{i:02d}" for i in range(n_curves)]}
        ),
        coordinate_system="normalized",
        time_unit="normalized",
    )


def test_w2_surface_is_module_scoped_and_ordered():
    import eyetrajectoriespy.workflows as workflows

    expected = (
        "run_sparse_fpca_workflow",
        "run_sparse_mfpca_workflow",
        "run_sparse_mfpca_async_workflow",
        "run_sparse_multilevel_workflow",
        "run_sparse_prediction_workflow",
    )
    assert all(hasattr(workflows, name) for name in expected)
    assert all(not hasattr(et, name) for name in expected)


def test_sparse_fpca_config_requires_exactly_one_bandwidth_mode():
    base = dict(
        dimension="x",
        n_components=2,
        evaluation_grid=tuple(np.linspace(0.0, 1.0, 17)),
    )
    with pytest.raises(ValueError, match="exactly one bandwidth mode"):
        SparseFPCAWorkflowConfig(**base)
    with pytest.raises(ValueError, match="exactly one bandwidth mode"):
        SparseFPCAWorkflowConfig(
            **base,
            mean_bandwidth=0.2,
            covariance_bandwidth=0.3,
            bandwidth_selection=SparseFPCABandwidthSelectionConfig(
                mean_bandwidths=(0.15, 0.2),
                covariance_bandwidths=(0.25, 0.3),
            ),
        )


def test_paired_config_requires_exactly_one_bandwidth_mode():
    base = dict(
        n_components=2,
        evaluation_grid=tuple(np.linspace(0.0, 1.0, 17)),
        measurement_error="diagonal",
        measurement_error_variance=(0.05, 0.08),
    )
    with pytest.raises(ValueError, match="exactly one bandwidth mode"):
        SparseMFPCAWorkflowConfig(**base)
    config = SparseMFPCAWorkflowConfig(
        **base,
        bandwidth_selection=SparseMFPCABandwidthSelectionConfig(
            mean_bandwidths=(0.25, 0.30),
            covariance_bandwidths=(0.30, 0.35),
        ),
    )
    assert config.mean_bandwidth is None
    assert config.bandwidth_selection is not None


def test_async_and_multilevel_have_no_selector_escape_hatch():
    async_fields = {field.name for field in fields(SparseMFPCAAsyncWorkflowConfig)}
    multilevel_fields = {field.name for field in fields(SparseMultilevelWorkflowConfig)}
    assert "bandwidth_selection" not in async_fields
    assert "bandwidth_selection" not in multilevel_fields


def test_sparse_workflows_fail_closed_on_nonempty_preprocessing():
    trajectories, truth = _univariate_dataset()
    config = SparseFPCAWorkflowConfig(
        dimension="x",
        n_components=2,
        evaluation_grid=tuple(np.linspace(0.0, 1.0, 17)),
        mean_bandwidth=0.25,
        covariance_bandwidth=0.35,
        noise_variance_method="fixed",
        measurement_error_variance=truth.noise_sd**2,
        psd_action="project",
        preprocessing=PreprocessingPlan(
            steps=(
                PreprocessingStepConfig(
                    function="interpolate",
                    parameters={"grid": 17},
                    scientific_effect="would change native sparse support",
                ),
            )
        ),
    )
    with pytest.raises(ValueError, match="requires an empty preprocessing plan"):
        run_sparse_fpca_workflow(trajectories, config=config)


def test_fixed_sparse_fpca_workflow_executes_and_exports(tmp_path):
    trajectories, truth = _univariate_dataset()
    config = SparseFPCAWorkflowConfig(
        dimension="x",
        n_components=2,
        evaluation_grid=tuple(np.linspace(0.0, 1.0, 17)),
        mean_bandwidth=0.25,
        covariance_bandwidth=0.35,
        noise_variance_method="fixed",
        measurement_error_variance=truth.noise_sd**2,
        psd_action="project",
        score_failure_action="retain_nan",
        score_uncertainty=ScoreUncertaintyConfig(failure_action="retain_nan"),
    )
    result = run_sparse_fpca_workflow(trajectories, config=config)

    assert result.workflow_contract == "sparse_fpca:v1"
    assert result.provenance["raw_interpolation_performed"] is False
    assert result.provenance["bandwidth_mode"] == "fixed"
    assert result.decisions["mean_bandwidth"].source == "analyst"
    assert [step.name for step in result.steps] == ["fit", "score_uncertainty"]
    assert result.fit.n_components == 2
    assert result.score_uncertainty is not None
    assert "scores" in result.tables
    assert "score_uncertainty" in result.tables
    assert "hidden" in workflow_reporting_text(result)

    destination = export_workflow_bundle(result, tmp_path / "workflow")
    assert (destination / "workflow.json").exists()
    assert (destination / "steps.csv").exists()
    assert (destination / "result" / "manifest.json").exists()
    assert (destination / "SHA256SUMS").exists()


def test_fixed_paired_sparse_mfpca_workflow_executes():
    trajectories = _paired_dataset()
    config = SparseMFPCAWorkflowConfig(
        n_components=2,
        evaluation_grid=tuple(np.linspace(0.0, 1.0, 17)),
        mean_bandwidth=0.30,
        covariance_bandwidth=0.35,
        measurement_error="diagonal",
        measurement_error_variance=(0.05, 0.08),
        psd_action="project",
        covariance_min_local_pairs=12,
    )
    result = run_sparse_mfpca_workflow(trajectories, config=config)

    assert result.workflow_contract == "sparse_mfpca:v1"
    assert result.provenance["raw_interpolation_performed"] is False
    assert result.provenance["bandwidth_mode"] == "fixed"
    assert result.decisions["covariance_bandwidth"].source == "analyst"
    assert [step.name for step in result.steps] == ["fit"]
    assert result.fit.scores.shape == (trajectories.n_curves, 2)


def test_prediction_signature_requires_explicit_roles():
    parameters = inspect.signature(run_sparse_prediction_workflow).parameters
    assert tuple(parameters)[:3] == (
        "proper_training",
        "calibration",
        "target",
    )
    config_fields = {field.name for field in fields(SparsePredictionWorkflowConfig)}
    assert "training" in config_fields
    assert "history_cutoff" in config_fields
    assert "prediction_grid" in config_fields
    assert "random_state" not in config_fields
    assert "split_fraction" not in config_fields


def test_condition_limits_match_primitive_contract():
    with pytest.raises(ValueError, match="greater than 1"):
        ScoreUncertaintyConfig(condition_limit=1.0)

    training = SparseFPCAWorkflowConfig(
        dimension="x",
        n_components=2,
        evaluation_grid=tuple(np.linspace(0.0, 1.0, 17)),
        mean_bandwidth=0.25,
        covariance_bandwidth=0.35,
    )
    with pytest.raises(ValueError, match="greater than 1"):
        SparsePredictionWorkflowConfig(
            training=training,
            history_cutoff=0.5,
            prediction_grid=(0.6, 0.8, 1.0),
            condition_limit=1.0,
        )


def test_w2_function_order_remains_explicit():
    names = [
        run_sparse_fpca_workflow.__name__,
        run_sparse_mfpca_workflow.__name__,
        run_sparse_mfpca_async_workflow.__name__,
        run_sparse_multilevel_workflow.__name__,
        run_sparse_prediction_workflow.__name__,
    ]
    assert names == [
        "run_sparse_fpca_workflow",
        "run_sparse_mfpca_workflow",
        "run_sparse_mfpca_async_workflow",
        "run_sparse_multilevel_workflow",
        "run_sparse_prediction_workflow",
    ]
