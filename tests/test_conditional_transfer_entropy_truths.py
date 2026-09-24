import numpy as np
import pytest

from eyetrajectoriespy.transfer_entropy import discrete_transfer_entropy
from eyetrajectoriespy.conditional_transfer_entropy import (
    ConditionalTransferEntropyCircularShiftTestResult,
    conditional_transfer_entropy,
    conditional_transfer_entropy_circular_shift_test,
    conditional_transfer_entropy_local_frame,
)


def test_constant_condition_reproduces_ordinary_transfer_entropy():
    rng = np.random.default_rng(10)
    source = rng.integers(0, 2, size=1000)
    target = np.zeros(1000, dtype=int)
    target[1:] = source[:-1]
    condition = np.zeros(1000, dtype=int)

    ordinary = discrete_transfer_entropy(
        source, target,
        target_history=1, source_history=1, source_lag=1,
    )
    conditioned = conditional_transfer_entropy(
        source, target, condition,
        target_history=1, source_history=1, condition_history=1,
        source_lag=1, condition_lag=1,
    )

    assert conditioned.conditional_transfer_entropy_bits == pytest.approx(
        ordinary.transfer_entropy_bits, abs=1e-15
    )
    np.testing.assert_allclose(
        conditioned.local_conditional_transfer_entropy_bits,
        ordinary.local_transfer_entropy_bits,
        atol=1e-15,
    )
    np.testing.assert_array_equal(
        conditioned.time_indices, ordinary.time_indices
    )
    assert conditioned.n_condition_states == 1
    assert conditioned.n_condition_histories == 1


def test_common_driver_pairwise_te_collapses_after_conditioning():
    rng = np.random.default_rng(11)
    condition = rng.integers(0, 2, size=4000)
    source = condition.copy()
    target = np.zeros_like(condition)
    target[1:] = condition[:-1]

    pairwise = discrete_transfer_entropy(
        source, target,
        target_history=1, source_history=1, source_lag=1,
    )
    conditioned = conditional_transfer_entropy(
        source, target, condition,
        target_history=1, source_history=1, condition_history=1,
        source_lag=1, condition_lag=1,
    )

    assert pairwise.transfer_entropy_bits > 0.95
    assert conditioned.conditional_transfer_entropy_bits == pytest.approx(
        0.0, abs=1e-12
    )


def test_direct_pathway_remains_after_common_driver_conditioning():
    rng = np.random.default_rng(12)
    n = 5000
    condition = rng.integers(0, 2, size=n)
    innovation = rng.integers(0, 2, size=n)
    source = 2 * condition + innovation
    target = np.zeros(n, dtype=int)
    target[1:] = source[:-1]

    pairwise = discrete_transfer_entropy(
        source, target,
        target_history=1, source_history=1, source_lag=1,
    )
    conditioned = conditional_transfer_entropy(
        source, target, condition,
        target_history=1, source_history=1, condition_history=1,
        source_lag=1, condition_lag=1,
    )

    assert pairwise.transfer_entropy_bits > 1.9
    assert 0.95 < conditioned.conditional_transfer_entropy_bits < 1.05


def test_directionality_is_retained():
    rng = np.random.default_rng(13)
    n = 5000
    source = rng.integers(0, 2, size=n)
    target = np.zeros(n, dtype=int)
    target[1:] = source[:-1]
    condition = np.zeros(n, dtype=int)

    forward = conditional_transfer_entropy(
        source, target, condition,
        target_history=1, source_history=1, condition_history=1,
        source_lag=1, condition_lag=1,
    )
    reverse = conditional_transfer_entropy(
        target, source, condition,
        target_history=1, source_history=1, condition_history=1,
        source_lag=1, condition_lag=1,
    )

    assert forward.conditional_transfer_entropy_bits > 0.95
    assert reverse.conditional_transfer_entropy_bits < 0.01


def test_manual_count_example_is_exact_and_auditable():
    source = np.array([0, 0, 0, 1, 0], dtype=int)
    target = np.array([0, 0, 0, 0, 1], dtype=int)
    condition = np.array([0, 0, 1, 1, 0], dtype=int)

    result = conditional_transfer_entropy(
        source, target, condition,
        target_history=1, source_history=1, condition_history=1,
        source_lag=1, condition_lag=1,
    )

    assert result.conditional_transfer_entropy_bits == pytest.approx(0.5)
    np.testing.assert_allclose(
        result.local_conditional_transfer_entropy_bits,
        [0.0, 0.0, 1.0, 1.0],
    )
    np.testing.assert_array_equal(
        result.target_history_states, [[0], [0], [0], [0]]
    )
    np.testing.assert_array_equal(
        result.source_history_states, [[0], [0], [0], [1]]
    )
    np.testing.assert_array_equal(
        result.condition_history_states, [[0], [0], [1], [1]]
    )
    assert result.n_condition_histories == 2
    assert result.n_source_condition_histories == 3
    assert result.n_joint_histories == 3
    assert result.singleton_joint_history_fraction == pytest.approx(2 / 3)
    assert result.min_joint_history_count == 1
    assert result.max_joint_history_count == 2
    assert result.mean_joint_history_count == pytest.approx(4 / 3)

    frame = conditional_transfer_entropy_local_frame(result)
    assert frame["local_conditional_transfer_entropy_bits"].tolist() == [
        0.0, 0.0, 1.0, 1.0
    ]


def test_sparse_deep_histories_expose_support_collapse():
    rng = np.random.default_rng(14)
    source = rng.integers(0, 2, size=220)
    target = rng.integers(0, 2, size=220)
    condition = rng.integers(0, 2, size=220)

    shallow = conditional_transfer_entropy(
        source, target, condition,
        target_history=1, source_history=1, condition_history=1,
        source_lag=1, condition_lag=1,
    )
    deep = conditional_transfer_entropy(
        source, target, condition,
        target_history=4, source_history=4, condition_history=4,
        source_lag=1, condition_lag=1,
    )

    assert deep.n_effective < shallow.n_effective
    assert deep.n_joint_histories > shallow.n_joint_histories
    assert deep.singleton_joint_history_fraction > 0.8
    assert deep.min_joint_history_count == 1
    assert deep.provenance["automatic_support_filtering"] is False


def test_source_only_circular_shift_null_plus_one_rule():
    rng = np.random.default_rng(15)
    n = 3000
    condition = rng.integers(0, 2, size=n)
    innovation = rng.integers(0, 2, size=n)
    source = 2 * condition + innovation
    target = np.zeros(n, dtype=int)
    target[1:] = source[:-1]
    shifts = tuple(range(80, 120))

    result = conditional_transfer_entropy_circular_shift_test(
        source, target, condition,
        target_history=1, source_history=1, condition_history=1,
        source_lag=1, condition_lag=1, shifts=shifts,
    )

    assert isinstance(
        result, ConditionalTransferEntropyCircularShiftTestResult
    )
    np.testing.assert_array_equal(result.shifts, shifts)
    assert result.observed.conditional_transfer_entropy_bits > 0.95
    assert result.surrogate_mean_bits < 0.02
    assert result.surrogate_centered_conditional_transfer_entropy_bits > 0.9
    assert result.upper_tail_p_value == pytest.approx(1 / 41)
    assert result.p_value_resolution == pytest.approx(1 / 41)
    assert result.provenance["shifted_process"] == "source"
    assert result.provenance["fixed_processes"] == ["target", "condition"]
