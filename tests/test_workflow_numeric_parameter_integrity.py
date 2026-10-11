"""W2/W4 model complexity and recurrence thresholds must not be truncated."""
from dataclasses import replace
import numpy as np
import pytest
from eyetrajectoriespy.workflows import (
    RecurrenceWorkflowConfig, SparseFPCAWorkflowConfig, SparseMFPCAWorkflowConfig,
    SparseMFPCAAsyncWorkflowConfig, SparseMultilevelWorkflowConfig,
)
from eyetrajectoriespy.workflows._sparse_shared import require_positive_integer


@pytest.mark.parametrize("value", [1, 2, np.int64(3), np.int32(4)])
def test_python_and_numpy_integer_values_remain_exact(value):
    assert require_positive_integer(value, name="n_components") == int(value)


@pytest.mark.parametrize("value", [True, np.bool_(True), 1.9, 2.0, "2", 0, -1, float("nan")])
def test_discrete_scientific_parameters_reject_implicit_conversion(value):
    with pytest.raises(ValueError, match="must be a positive integer"):
        require_positive_integer(value, name="n_components")


@pytest.fixture
def affected_configs():
    grid=(0.0, 0.5, 1.0)
    return (
        (SparseFPCAWorkflowConfig(
            dimension="x", n_components=2, evaluation_grid=grid,
            mean_bandwidth=.25, covariance_bandwidth=.30), "n_components"),
        (SparseMFPCAWorkflowConfig(
            n_components=2, evaluation_grid=grid, measurement_error="diagonal",
            measurement_error_variance=(.04,.05),
            mean_bandwidth=.25, covariance_bandwidth=.30), "n_components"),
        (SparseMFPCAAsyncWorkflowConfig(
            n_components=2, evaluation_grid=grid, measurement_error="diagonal",
            measurement_error_variance=(.04,.05),
            mean_bandwidth=.25, covariance_bandwidth=.30), "n_components"),
        (SparseMultilevelWorkflowConfig(
            dimension="x", participant_column="participant_id",
            participant_components=2, trial_components=1, evaluation_grid=grid,
            mean_bandwidth=.25, total_covariance_bandwidth=.30,
            between_covariance_bandwidth=.35), "participant_components"),
        (SparseMultilevelWorkflowConfig(
            dimension="x", participant_column="participant_id",
            participant_components=1, trial_components=2, evaluation_grid=grid,
            mean_bandwidth=.25, total_covariance_bandwidth=.30,
            between_covariance_bandwidth=.35), "trial_components"),
        (RecurrenceWorkflowConfig(
            curve=0, dimensions=("x",), embedding_dimension=2, delay=2,
            radius=.15, min_diagonal_length=2), "min_diagonal_length"),
        (RecurrenceWorkflowConfig(
            curve=0, dimensions=("x",), embedding_dimension=2, delay=2,
            radius=.15, min_vertical_length=2), "min_vertical_length"),
    )


@pytest.mark.parametrize("bad", [1.9, 2.0, "2", True, 0, np.nan])
def test_each_affected_workflow_fails_closed(affected_configs, bad):
    for config, field in affected_configs:
        with pytest.raises(ValueError, match=field + " must be a positive integer"):
            replace(config, **{field:bad})


def test_no_integer_parameter_drift_on_valid_inputs(affected_configs):
    for config, field in affected_configs:
        original=getattr(config,field)
        assert original in (1,2)
        updated=replace(config, **{field:np.int64(3)})
        assert type(getattr(updated,field)) is int
        assert getattr(updated,field)==3
