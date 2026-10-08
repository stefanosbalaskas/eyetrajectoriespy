import numpy as np
import pandas as pd
import pytest

import eyetrajectoriespy as et
from eyetrajectoriespy.workflows import (
    FPCAWorkflowConfig,
    FunctionOnScalarWorkflowConfig,
    FunctionalMixedEffectsWorkflowConfig,
    GeneralizedFunctionalWorkflowConfig,
    ObservationDiagnosticConfig,
    PreprocessingPlan,
    ScoreUncertaintyConfig,
    SparseFPCAWorkflowConfig,
    SparseMultilevelWorkflowConfig,
    SparsePredictionWorkflowConfig,
    WorkflowDecisionRecord,
    WorkflowStepRecord,
    run_fpca_workflow,
    run_function_on_scalar_workflow,
    run_functional_mixed_effects_workflow,
    run_generalized_functional_workflow,
    run_sparse_multilevel_workflow,
    run_sparse_prediction_workflow,
    workflow_config_to_dict,
    workflow_reporting_text,
    workflow_summary_frame,
)
from eyetrajectoriespy.workflows._core import PreprocessingStepConfig
from eyetrajectoriespy.workflows._sparse_shared import (
    normalized_grid,
    positive_candidates,
    require_empty_sparse_preprocessing,
    run_observation_diagnostics,
    timed_step,
)


def _dense():
    time = np.linspace(0.0, 1.0, 5)
    values = np.stack(
        [
            np.column_stack((time + i, 2.0 * time + i))
            for i in range(4)
        ]
    )
    trajectories = et.TrajectorySet(
        time=time,
        values=values,
        curve_ids=("a", "b", "c", "d"),
        dimension_names=("x", "y"),
    )
    design = pd.DataFrame(
        {
            "curve_id": trajectories.curve_ids,
            "condition": (-1.0, -0.5, 0.5, 1.0),
        }
    )
    return trajectories, design


def _irregular(n_curves=2):
    time = tuple(np.array([0.0, 1.0]) for _ in range(n_curves))
    values = tuple(np.array([[0.0], [1.0]]) for _ in range(n_curves))
    return et.IrregularTrajectorySet(
        time=time,
        values=values,
        curve_ids=tuple(f"i{i}" for i in range(n_curves)),
        dimension_names=("x",),
        metadata=pd.DataFrame(
            {"participant_id": [f"p{i}" for i in range(n_curves)]}
        ),
    )


def _sparse_training_config(**updates):
    values = dict(
        dimension="x",
        n_components=1,
        evaluation_grid=(0.0, 0.5, 1.0),
        mean_bandwidth=0.3,
        covariance_bandwidth=0.4,
    )
    values.update(updates)
    return SparseFPCAWorkflowConfig(**values)


def _multilevel_config(**updates):
    values = dict(
        dimension="x",
        participant_column="participant_id",
        participant_components=1,
        trial_components=1,
        evaluation_grid=(0.0, 0.5, 1.0),
        mean_bandwidth=0.3,
        total_covariance_bandwidth=0.4,
        between_covariance_bandwidth=0.4,
    )
    values.update(updates)
    return SparseMultilevelWorkflowConfig(**values)


def test_core_decision_and_step_contract_failures():
    with pytest.raises(ValueError, match="source"):
        WorkflowDecisionRecord(value=1, source="unknown")
    with pytest.raises(ValueError, match="criterion"):
        WorkflowDecisionRecord(value=1, source="audited_selector")
    with pytest.raises(ValueError, match="non-finite"):
        WorkflowDecisionRecord(value=float("nan"), source="analyst")

    with pytest.raises(ValueError, match="name"):
        WorkflowStepRecord(
            name="",
            function="f",
            status="completed",
            parameters={},
            elapsed_seconds=0.0,
        )
    with pytest.raises(ValueError, match="function"):
        WorkflowStepRecord(
            name="x",
            function="",
            status="completed",
            parameters={},
            elapsed_seconds=0.0,
        )
    with pytest.raises(ValueError, match="status"):
        WorkflowStepRecord(
            name="x",
            function="f",
            status="mystery",
            parameters={},
            elapsed_seconds=0.0,
        )
    with pytest.raises(ValueError, match="elapsed_seconds"):
        WorkflowStepRecord(
            name="x",
            function="f",
            status="completed",
            parameters={},
            elapsed_seconds=-1.0,
        )
    with pytest.raises(TypeError, match="non-string"):
        WorkflowStepRecord(
            name="x",
            function="f",
            status="completed",
            parameters={1: "bad"},
            elapsed_seconds=0.0,
        )


def test_core_preprocessing_and_generic_result_guards():
    with pytest.raises(ValueError, match="function"):
        PreprocessingStepConfig(
            function="",
            parameters={},
            scientific_effect="effect",
        )
    with pytest.raises(ValueError, match="scientific_effect"):
        PreprocessingStepConfig(
            function="smooth",
            parameters={},
            scientific_effect="",
        )
    with pytest.raises(TypeError, match="dataclass"):
        workflow_config_to_dict(object())
    with pytest.raises(TypeError, match="dataclass"):
        workflow_summary_frame(object())
    with pytest.raises(TypeError, match="dataclass"):
        workflow_reporting_text(object())


def test_sparse_shared_config_and_helper_edges():
    valid = ScoreUncertaintyConfig(
        condition_limit=2.0,
        failure_action="retain_nan",
    )
    assert valid.condition_limit == 2.0
    with pytest.raises(ValueError, match="failure_action"):
        ScoreUncertaintyConfig(failure_action="bad")

    diagnostic = ObservationDiagnosticConfig(
        predictors=["condition"],
        history_predictors=["previous_observed_x"],
        eccentricity_reference=(0.0, 0.0),
        low_support_threshold=0.2,
    )
    assert diagnostic.predictors == ("condition",)
    assert diagnostic.history_predictors == ("previous_observed_x",)
    assert diagnostic.eccentricity_reference == (0.0, 0.0)

    with pytest.raises(ValueError, match="eccentricity_reference"):
        ObservationDiagnosticConfig(eccentricity_reference=(0.0,))
    with pytest.raises(ValueError, match="low_support_threshold"):
        ObservationDiagnosticConfig(low_support_threshold=1.1)
    with pytest.raises(ValueError, match="strictly increasing"):
        normalized_grid((0.0, 0.0), name="grid")
    with pytest.raises(ValueError, match="at least one"):
        positive_candidates((), name="candidates")
    with pytest.raises(ValueError, match="positive"):
        positive_candidates((0.0, 1.0), name="candidates")
    with pytest.raises(TypeError, match="PreprocessingPlan"):
        require_empty_sparse_preprocessing(
            object(),
            workflow_contract="test:v1",
        )


def test_timed_step_and_observation_dispatch_fail_closed():
    def fail():
        raise RuntimeError("expected")

    with pytest.raises(RuntimeError, match="expected"):
        timed_step(
            name="failure",
            function="fail",
            parameters={"x": 1},
            call=fail,
        )
    with pytest.raises(ValueError, match="without an explicit"):
        run_observation_diagnostics(
            process=object(),
            config=None,
        )
    with pytest.raises(ValueError, match="requires a separately supplied"):
        run_observation_diagnostics(
            process=None,
            config=ObservationDiagnosticConfig(),
        )


def test_w3_config_edge_validation():
    with pytest.raises(ValueError, match="at least one"):
        FunctionOnScalarWorkflowConfig(predictors=())
    with pytest.raises(ValueError, match="dimensions"):
        FunctionOnScalarWorkflowConfig(
            predictors=("condition",),
            dimensions=(),
        )
    with pytest.raises(ValueError, match="dimensions"):
        FunctionOnScalarWorkflowConfig(
            predictors=("condition",),
            dimensions=("x", "x"),
        )
    with pytest.raises(ValueError, match="unit"):
        FunctionOnScalarWorkflowConfig(
            predictors=("condition",),
            unit="automatic",
        )

    with pytest.raises(TypeError, match="n_components"):
        FPCAWorkflowConfig(n_components=True)
    with pytest.raises(ValueError, match="positive"):
        FPCAWorkflowConfig(n_components=0)
    with pytest.raises(ValueError, match="variance proportion"):
        FPCAWorkflowConfig(n_components=1.2)

    with pytest.raises(ValueError, match="participant_column"):
        FunctionalMixedEffectsWorkflowConfig(
            predictors=("condition",),
            participant_column="",
            dimension="x",
        )
    with pytest.raises(ValueError, match="dimension"):
        FunctionalMixedEffectsWorkflowConfig(
            predictors=("condition",),
            participant_column="participant_id",
            dimension="",
        )
    with pytest.raises(ValueError, match="participant_column"):
        GeneralizedFunctionalWorkflowConfig(
            predictors=("condition",),
            participant_column="",
            dimension="x",
            family="binomial",
        )
    with pytest.raises(ValueError, match="dimension"):
        GeneralizedFunctionalWorkflowConfig(
            predictors=("condition",),
            participant_column="participant_id",
            dimension="",
            family="binomial",
        )
    with pytest.raises(ValueError, match="finite"):
        GeneralizedFunctionalWorkflowConfig(
            predictors=("condition",),
            participant_column="participant_id",
            dimension="x",
            family="poisson",
            exposure=(np.nan,),
        )


def test_w3_run_type_guards():
    trajectories, design = _dense()
    fpca = FPCAWorkflowConfig(n_components=1)
    fos = FunctionOnScalarWorkflowConfig(predictors=("condition",))
    mixed = FunctionalMixedEffectsWorkflowConfig(
        predictors=("condition",),
        participant_column="participant_id",
        dimension="x",
    )
    generalized = GeneralizedFunctionalWorkflowConfig(
        predictors=("condition",),
        participant_column="participant_id",
        dimension="x",
        family="poisson",
    )

    with pytest.raises(TypeError, match="TrajectorySet"):
        run_fpca_workflow(object(), config=fpca)
    with pytest.raises(TypeError, match="FPCAWorkflowConfig"):
        run_fpca_workflow(trajectories, config=object())
    with pytest.raises(TypeError, match="TrajectorySet"):
        run_function_on_scalar_workflow(object(), design, config=fos)
    with pytest.raises(TypeError, match="pandas"):
        run_function_on_scalar_workflow(trajectories, object(), config=fos)
    with pytest.raises(TypeError, match="FunctionOnScalarWorkflowConfig"):
        run_function_on_scalar_workflow(trajectories, design, config=object())
    with pytest.raises(TypeError, match="TrajectorySet"):
        run_functional_mixed_effects_workflow(object(), design, config=mixed)
    with pytest.raises(TypeError, match="pandas"):
        run_functional_mixed_effects_workflow(
            trajectories,
            object(),
            config=mixed,
        )
    with pytest.raises(TypeError, match="FunctionalMixedEffectsWorkflowConfig"):
        run_functional_mixed_effects_workflow(
            trajectories,
            design,
            config=object(),
        )
    with pytest.raises(TypeError, match="TrajectorySet"):
        run_generalized_functional_workflow(
            object(),
            design,
            config=generalized,
        )
    with pytest.raises(TypeError, match="pandas"):
        run_generalized_functional_workflow(
            trajectories,
            object(),
            config=generalized,
        )
    with pytest.raises(TypeError, match="GeneralizedFunctionalWorkflowConfig"):
        run_generalized_functional_workflow(
            trajectories,
            design,
            config=object(),
        )


def test_w3_preprocessing_type_guard():
    trajectories, _ = _dense()
    config = FPCAWorkflowConfig(
        n_components=1,
        preprocessing=object(),
    )
    with pytest.raises(TypeError, match="PreprocessingPlan"):
        run_fpca_workflow(trajectories, config=config)


def test_sparse_multilevel_config_edges_and_run_guards():
    with pytest.raises(ValueError, match="dimension"):
        _multilevel_config(dimension="")
    with pytest.raises(ValueError, match="participant_column"):
        _multilevel_config(participant_column="")
    with pytest.raises(ValueError, match="positive integer"):
        _multilevel_config(participant_components=True)
    with pytest.raises(ValueError, match="finite and positive"):
        _multilevel_config(mean_bandwidth=0.0)
    with pytest.raises(ValueError, match="noise_bandwidth"):
        _multilevel_config(noise_bandwidth=0.0)
    with pytest.raises(ValueError, match="noise_support"):
        _multilevel_config(noise_support=(1.0, 0.0))

    config = _multilevel_config()
    with pytest.raises(TypeError, match="IrregularTrajectorySet"):
        run_sparse_multilevel_workflow(object(), config=config)
    with pytest.raises(TypeError, match="SparseMultilevelWorkflowConfig"):
        run_sparse_multilevel_workflow(_irregular(), config=object())


def test_sparse_prediction_config_edges_and_run_guards():
    training = _sparse_training_config()
    with pytest.raises(TypeError, match="SparseFPCAWorkflowConfig"):
        SparsePredictionWorkflowConfig(
            training=object(),
            history_cutoff=0.5,
            prediction_grid=(0.75, 1.0),
        )
    with pytest.raises(ValueError, match="history_cutoff"):
        SparsePredictionWorkflowConfig(
            training=training,
            history_cutoff=np.nan,
            prediction_grid=(0.75, 1.0),
        )
    with pytest.raises(ValueError, match="strictly within"):
        SparsePredictionWorkflowConfig(
            training=training,
            history_cutoff=0.5,
            prediction_grid=(0.75, 1.0),
            alpha=1.0,
        )
    with pytest.raises(ValueError, match="positive integer"):
        SparsePredictionWorkflowConfig(
            training=training,
            history_cutoff=0.5,
            prediction_grid=(0.75, 1.0),
            min_history_observations=0,
        )
    with pytest.raises(ValueError, match="greater than 1"):
        SparsePredictionWorkflowConfig(
            training=training,
            history_cutoff=0.5,
            prediction_grid=(0.75, 1.0),
            condition_limit=1.0,
        )
    with pytest.raises(ValueError, match="non-negative"):
        SparsePredictionWorkflowConfig(
            training=training,
            history_cutoff=0.5,
            prediction_grid=(0.75, 1.0),
            history_ridge=-1.0,
        )

    config = SparsePredictionWorkflowConfig(
        training=training,
        history_cutoff=0.5,
        prediction_grid=(0.75, 1.0),
        alpha=0.5,
    )
    with pytest.raises(TypeError, match="proper_training"):
        run_sparse_prediction_workflow(
            object(),
            _irregular(),
            _irregular(1),
            config=config,
        )
    with pytest.raises(TypeError, match="config"):
        run_sparse_prediction_workflow(
            _irregular(),
            _irregular(),
            _irregular(1),
            config=object(),
        )
    with pytest.raises(ValueError, match="exactly one"):
        run_sparse_prediction_workflow(
            _irregular(),
            _irregular(),
            _irregular(2),
            config=config,
        )
