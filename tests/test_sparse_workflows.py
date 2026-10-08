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


def _async_dataset():
    union = np.linspace(0.0, 1.0, 9)
    x_mask = np.array([True, False, True, True, False, True, True, False, True])
    y_mask = np.array([True, True, False, True, True, False, True, True, True])
    times = []
    values = []
    participants = []
    for index in range(18):
        z1 = -1.5 + 3.0 * index / 17.0
        z2 = np.cos(0.7 * (index + 1))
        x_truth = (
            0.1
            + 0.2 * union
            + z1 * np.sin(np.pi * union)
            + 0.22 * z2 * np.cos(2.0 * np.pi * union)
        )
        y_truth = (
            -0.05
            + 0.1 * union
            + 0.70 * z1 * np.cos(np.pi * union)
            + 0.18 * z2 * np.sin(2.0 * np.pi * union)
        )
        observed = np.full((union.size, 2), np.nan, dtype=float)
        observed[x_mask, 0] = x_truth[x_mask]
        observed[y_mask, 1] = y_truth[y_mask]
        times.append(union.copy())
        values.append(observed)
        participants.append(f"P{index // 3:02d}")
    return et.IrregularTrajectorySet(
        time=tuple(times),
        values=tuple(values),
        curve_ids=tuple(f"A{index:02d}" for index in range(18)),
        dimension_names=("x", "y"),
        metadata=pd.DataFrame({"participant_id": participants}),
        coordinate_system="normalized",
        time_unit="s",
    )


def _multilevel_dataset():
    rng = np.random.default_rng(174)
    times = []
    values = []
    curve_ids = []
    participant_ids = []
    participant_scores = np.linspace(-1.4, 1.4, 12)
    for participant in range(12):
        for trial in range(2):
            base = np.linspace(0.0, 1.0, 11)
            jitter = rng.normal(0.0, 0.012, size=base.size)
            time = np.clip(base + jitter, 0.0, 1.0)
            time[0] = 0.0
            time[-1] = 1.0
            time = np.maximum.accumulate(time)
            for index in range(1, time.size):
                if time[index] <= time[index - 1]:
                    time[index] = min(1.0, time[index - 1] + 1e-5)
            time[-1] = 1.0
            trial_score = rng.normal(0.0, 0.55)
            observed = (
                0.15
                + 0.10 * time
                + participant_scores[participant]
                * np.sqrt(2.0)
                * np.sin(np.pi * time)
                + trial_score * np.sqrt(2.0) * np.sin(2.0 * np.pi * time)
                + rng.normal(0.0, 0.10, size=time.size)
            )
            times.append(time)
            values.append(observed[:, None])
            curve_ids.append(f"p{participant:02d}_t{trial:02d}")
            participant_ids.append(f"p{participant:02d}")
    return et.IrregularTrajectorySet(
        time=tuple(times),
        values=tuple(values),
        curve_ids=tuple(curve_ids),
        dimension_names=("x",),
        metadata=pd.DataFrame({"participant_id": participant_ids}),
        coordinate_system="normalized",
        time_unit="normalized",
    )


def _prediction_roles():
    grid = np.asarray([0.0, 0.25, 0.5, 0.75, 1.0])

    def build(ids, scores, prefix):
        values = []
        for score in scores:
            curve = (
                0.1
                + 0.15 * grid
                + float(score) * np.sin(np.pi * grid)
                + 0.15 * float(score) * np.sin(2.0 * np.pi * grid)
            )
            values.append(curve[:, None])
        return et.IrregularTrajectorySet(
            time=tuple(grid.copy() for _ in ids),
            values=tuple(values),
            curve_ids=tuple(ids),
            dimension_names=("x",),
            metadata=pd.DataFrame(
                {"participant_id": [f"{prefix}-{index}" for index in range(len(ids))]}
            ),
            coordinate_system="normalized",
            time_unit="s",
        )

    training_ids = tuple(f"train-{index}" for index in range(12))
    calibration_ids = tuple(f"cal-{index}" for index in range(4))
    training = build(training_ids, np.linspace(-1.5, 1.5, 12), "train-p")
    calibration = build(calibration_ids, (-0.9, -0.3, 0.4, 1.0), "cal-p")
    target = build(("target-0",), (0.25,), "target-p")
    return training, calibration, target


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


def test_async_sparse_mfpca_workflow_executes():
    trajectories = _async_dataset()
    result = run_sparse_mfpca_async_workflow(
        trajectories,
        config=SparseMFPCAAsyncWorkflowConfig(
            n_components=1,
            evaluation_grid=tuple(np.linspace(0.0, 1.0, 7)),
            mean_bandwidth=0.45,
            covariance_bandwidth=0.55,
            measurement_error="fixed_matrix",
            measurement_error_covariance=np.array(
                [[0.02, 0.004], [0.004, 0.025]]
            ),
            psd_action="project",
            score_failure_action="retain_nan",
        ),
    )

    assert result.workflow_contract == "sparse_mfpca_async:v1"
    assert result.provenance["raw_interpolation_performed"] is False
    assert result.provenance["raw_synchronization_performed"] is False
    assert result.provenance["paired_bandwidth_selector_reused"] is False
    assert [step.name for step in result.steps] == ["fit"]
    assert result.fit.scores.shape == (18, 1)


def test_sparse_multilevel_workflow_executes():
    trajectories = _multilevel_dataset()
    result = run_sparse_multilevel_workflow(
        trajectories,
        config=SparseMultilevelWorkflowConfig(
            dimension="x",
            participant_column="participant_id",
            participant_components=1,
            trial_components=1,
            evaluation_grid=tuple(np.linspace(0.10, 0.90, 9)),
            mean_bandwidth=0.35,
            total_covariance_bandwidth=0.45,
            between_covariance_bandwidth=0.45,
            analysis_support_action="restrict",
            noise_variance_method="fixed",
            measurement_error_variance=0.01,
            psd_action="project",
            score_ridge=1e-6,
        ),
    )

    assert result.workflow_contract == "sparse_multilevel:v1"
    assert result.provenance["bandwidth_mode"] == "fixed"
    assert result.provenance["bandwidth_selector_available"] is False
    assert [step.name for step in result.steps] == ["fit"]
    assert len(result.fit.participant_ids) == 12
    assert len(result.fit.curve_ids) == 24


def test_sparse_prediction_workflow_executes_explicit_roles():
    training, calibration, target = _prediction_roles()
    training_config = SparseFPCAWorkflowConfig(
        dimension="x",
        n_components=1,
        evaluation_grid=(0.0, 0.25, 0.5, 0.75, 1.0),
        mean_bandwidth=0.50,
        covariance_bandwidth=0.55,
        noise_variance_method="fixed",
        measurement_error_variance=0.02,
        psd_action="project",
        score_failure_action="retain_nan",
    )
    result = run_sparse_prediction_workflow(
        training,
        calibration,
        target,
        config=SparsePredictionWorkflowConfig(
            training=training_config,
            history_cutoff=0.5,
            prediction_grid=(0.75, 1.0),
            alpha=0.4,
        ),
    )

    assert result.workflow_contract == "sparse_prediction:v1"
    assert result.provenance["random_role_split_performed"] is False
    assert result.decisions["role_assignment"].source == "analyst"
    assert result.calibration.n_calibration_curves == 4
    assert result.band.prediction.curve_id == "target-0"
    assert [step.name for step in result.steps][-2:] == [
        "conformal_calibration",
        "target_prediction",
    ]


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


def test_selector_condition_limits_match_primitive_contract():
    with pytest.raises(ValueError, match="greater than 1"):
        SparseFPCABandwidthSelectionConfig(
            mean_bandwidths=(0.2,),
            covariance_bandwidths=(0.3,),
            predictive_condition_limit=1.0,
        )
    with pytest.raises(ValueError, match="greater than 1"):
        SparseMFPCABandwidthSelectionConfig(
            mean_bandwidths=(0.2,),
            covariance_bandwidths=(0.3,),
            predictive_condition_limit=1.0,
        )


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
