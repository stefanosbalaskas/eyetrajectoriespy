import matplotlib
matplotlib.use("Agg")

import numpy as np
import pytest

from eyetrajectoriespy.conditional_transfer_entropy import (
    ConditionalTransferEntropyResult,
    conditional_transfer_entropy,
    conditional_transfer_entropy_circular_shift_reporting_text,
    conditional_transfer_entropy_circular_shift_test,
    conditional_transfer_entropy_local_frame,
    conditional_transfer_entropy_reporting_text,
    plot_conditional_transfer_entropy_circular_shift_test,
)


@pytest.mark.parametrize(
    "kwargs,error,match",
    [
        ({"target_history": 0}, ValueError, "target_history must be >= 1"),
        ({"source_history": True}, TypeError, "source_history must be an integer"),
        ({"condition_history": 0}, ValueError, "condition_history must be >= 1"),
        ({"source_lag": 0}, ValueError, "source_lag must be >= 1"),
        ({"condition_lag": False}, TypeError, "condition_lag must be an integer"),
    ],
)
def test_history_and_lag_contracts_fail_closed(kwargs, error, match):
    source = np.array([0, 1, 0, 1, 0, 1])
    target = np.array([0, 0, 1, 0, 1, 0])
    condition = np.array([1, 0, 1, 0, 1, 0])
    parameters = dict(
        target_history=1,
        source_history=1,
        condition_history=1,
        source_lag=1,
        condition_lag=1,
    )
    parameters.update(kwargs)

    with pytest.raises(error, match=match):
        conditional_transfer_entropy(
            source, target, condition, **parameters
        )


def test_discrete_state_length_and_effective_transition_contracts():
    with pytest.raises(TypeError, match="discretize explicitly upstream"):
        conditional_transfer_entropy(
            [0.1, 0.2, 0.3],
            [0, 1, 0],
            [0, 0, 1],
            target_history=1,
            source_history=1,
            condition_history=1,
            source_lag=1,
            condition_lag=1,
        )

    with pytest.raises(ValueError, match="same length"):
        conditional_transfer_entropy(
            [0, 1, 0],
            [0, 1],
            [0, 0, 1],
            target_history=1,
            source_history=1,
            condition_history=1,
            source_lag=1,
            condition_lag=1,
        )

    with pytest.raises(ValueError, match="no effective transitions"):
        conditional_transfer_entropy(
            [0, 1, 0],
            [0, 1, 0],
            [0, 0, 1],
            target_history=4,
            source_history=1,
            condition_history=1,
            source_lag=1,
            condition_lag=1,
        )


@pytest.mark.parametrize(
    "shifts,error,match",
    [
        ((), ValueError, "at least one"),
        ("1,2", TypeError, "non-string"),
        ((1, 1), ValueError, "unique"),
        ((0, 1), ValueError, "1 <= shift"),
        ((1, True), TypeError, "must be an integer"),
    ],
)
def test_source_shift_contracts_fail_closed(shifts, error, match):
    source = np.array([0, 1, 0, 1, 0, 1])
    target = np.array([0, 0, 1, 0, 1, 0])
    condition = np.array([1, 0, 1, 0, 1, 0])

    with pytest.raises(error, match=match):
        conditional_transfer_entropy_circular_shift_test(
            source,
            target,
            condition,
            target_history=1,
            source_history=1,
            condition_history=1,
            source_lag=1,
            condition_lag=1,
            shifts=shifts,
        )


def test_plot_reporting_and_type_guards_preserve_noncausal_scope():
    rng = np.random.default_rng(16)
    n = 500
    source = rng.integers(0, 2, size=n)
    target = np.zeros(n, dtype=int)
    target[1:] = source[:-1]
    condition = np.zeros(n, dtype=int)

    estimate = conditional_transfer_entropy(
        source,
        target,
        condition,
        target_history=1,
        source_history=1,
        condition_history=1,
        source_lag=1,
        condition_lag=1,
    )
    estimate_text = conditional_transfer_entropy_reporting_text(estimate)
    assert "incremental directed predictive information" in estimate_text
    assert "does not establish causal influence" in estimate_text
    assert "unmeasured common drivers" in estimate_text

    shift_test = conditional_transfer_entropy_circular_shift_test(
        source,
        target,
        condition,
        target_history=1,
        source_history=1,
        condition_history=1,
        source_lag=1,
        condition_lag=1,
        shifts=range(30, 40),
    )
    shift_text = conditional_transfer_entropy_circular_shift_reporting_text(
        shift_test
    )
    assert "source-only circular shifts" in shift_text
    assert "Target and conditioning processes were held fixed" in shift_text
    assert "does not establish causal influence" in shift_text

    ax = plot_conditional_transfer_entropy_circular_shift_test(shift_test)
    assert ax.get_xlabel() == "Conditional transfer entropy (bits)"

    with pytest.raises(TypeError):
        conditional_transfer_entropy_local_frame(object())
    with pytest.raises(TypeError):
        conditional_transfer_entropy_reporting_text(object())
    with pytest.raises(TypeError):
        conditional_transfer_entropy_circular_shift_reporting_text(object())
    with pytest.raises(TypeError):
        plot_conditional_transfer_entropy_circular_shift_test(object())


def test_result_provenance_has_no_hidden_causal_or_selection_contract():
    result = conditional_transfer_entropy(
        [0, 1, 0, 1, 0, 1],
        [0, 0, 1, 0, 1, 0],
        [1, 0, 1, 0, 1, 0],
        target_history=1,
        source_history=1,
        condition_history=1,
        source_lag=1,
        condition_lag=1,
    )

    assert isinstance(result, ConditionalTransferEntropyResult)
    assert result.provenance["automatic_discretization"] is False
    assert result.provenance["automatic_history_selection"] is False
    assert result.provenance["automatic_lag_selection"] is False
    assert result.provenance["automatic_support_filtering"] is False
    assert result.provenance["causal_identification_claimed"] is False
