import matplotlib
matplotlib.use("Agg")

import numpy as np
import pytest

from eyetrajectoriespy import (
    DiscreteTransferEntropyResult,
    TransferEntropyCircularShiftTestResult,
    discrete_transfer_entropy,
    plot_transfer_entropy_circular_shift_test,
    transfer_entropy_circular_shift_reporting_text,
    transfer_entropy_circular_shift_test,
    transfer_entropy_local_frame,
    transfer_entropy_reporting_text,
)


def test_transfer_entropy_matches_reference_example():
    source = np.array([0, 1, 1, 1, 1, 0, 0, 0, 0])
    target = np.array([0, 0, 1, 1, 1, 1, 0, 0, 0])
    result = discrete_transfer_entropy(
        source, target, target_history=2, source_history=1, source_lag=1
    )
    assert isinstance(result, DiscreteTransferEntropyResult)
    assert result.transfer_entropy_bits == pytest.approx(0.6792696431662097)
    np.testing.assert_allclose(
        result.local_transfer_entropy_bits,
        [1.0, 0.0, 0.5849625007211562, 0.5849625007211562,
         1.584962500721156, 0.0, 1.0],
    )
    assert result.n_effective == 7
    assert result.provenance["automatic_discretization"] is False


def test_transfer_entropy_reference_direction_is_asymmetric():
    source = np.array([0, 1, 1, 1, 1, 0, 0, 0, 0])
    target = np.array([0, 0, 1, 1, 1, 1, 0, 0, 0])
    reverse = discrete_transfer_entropy(
        target, source, target_history=2, source_history=1, source_lag=1
    )
    assert reverse.transfer_entropy_bits == pytest.approx(0.0)


def test_local_frame_retains_declared_histories():
    source = np.array([0, 1, 1, 1, 1, 0, 0, 0, 0])
    target = np.array([0, 0, 1, 1, 1, 1, 0, 0, 0])
    result = discrete_transfer_entropy(
        source, target, target_history=2, source_history=1, source_lag=1
    )
    frame = transfer_entropy_local_frame(result)
    assert frame.columns.tolist() == [
        "time_index", "target_state", "target_history",
        "source_history", "local_transfer_entropy_bits",
    ]
    assert frame.iloc[0]["time_index"] == 2
    assert frame.iloc[0]["target_history"] == (0, 0)
    assert frame.iloc[0]["source_history"] == (1,)
    assert frame.iloc[0]["local_transfer_entropy_bits"] == pytest.approx(1.0)


def _synthetic_directional_data():
    rng = np.random.default_rng(7)
    n = 1500
    source = rng.integers(0, 2, size=n)
    target = np.zeros(n, dtype=int)
    noise = rng.random(n) < 0.08
    target[1:] = np.bitwise_xor(source[:-1], noise[1:].astype(int))
    return source, target


def test_delayed_binary_source_has_larger_forward_than_reverse_te():
    source, target = _synthetic_directional_data()
    forward = discrete_transfer_entropy(
        source, target, target_history=1, source_history=1, source_lag=1
    )
    reverse = discrete_transfer_entropy(
        target, source, target_history=1, source_history=1, source_lag=1
    )
    assert forward.transfer_entropy_bits > 0.5
    assert reverse.transfer_entropy_bits < 0.01
    assert forward.transfer_entropy_bits > reverse.transfer_entropy_bits


def test_circular_shift_test_is_explicit_reproducible_and_plus_one():
    source, target = _synthetic_directional_data()
    shifts = tuple(range(50, 100))
    first = transfer_entropy_circular_shift_test(
        source, target, target_history=1, source_history=1, source_lag=1,
        shifts=shifts,
    )
    second = transfer_entropy_circular_shift_test(
        source, target, target_history=1, source_history=1, source_lag=1,
        shifts=shifts,
    )
    assert isinstance(first, TransferEntropyCircularShiftTestResult)
    np.testing.assert_array_equal(first.shifts, shifts)
    np.testing.assert_allclose(
        first.surrogate_transfer_entropy_bits,
        second.surrogate_transfer_entropy_bits,
    )
    assert first.observed.transfer_entropy_bits > first.surrogate_mean_bits
    assert first.surrogate_centered_transfer_entropy_bits > 0.5
    assert first.upper_tail_p_value == pytest.approx(1 / 51)
    assert first.p_value_resolution == pytest.approx(1 / 51)
    assert first.provenance["automatic_shift_generation"] is False


def test_reporting_and_plotting_preserve_scope_boundary():
    source, target = _synthetic_directional_data()
    result = discrete_transfer_entropy(
        source, target, target_history=1, source_history=1, source_lag=1
    )
    test = transfer_entropy_circular_shift_test(
        source, target, target_history=1, source_history=1, source_lag=1,
        shifts=(50, 75, 100),
    )
    assert "does not by itself establish causal influence" in transfer_entropy_reporting_text(result)
    assert "does not establish causality" in transfer_entropy_circular_shift_reporting_text(test)
    ax = plot_transfer_entropy_circular_shift_test(test)
    assert ax.get_xlabel() == "Transfer entropy (bits)"


@pytest.mark.parametrize(
    "values,error",
    [
        (np.array([0.1, 1.2, 2.3]), TypeError),
        (np.array([0.0, np.nan, 1.0]), ValueError),
        (np.array([[0, 1], [1, 0]]), ValueError),
        (np.array([], dtype=int), ValueError),
        (np.array(["a", "b"]), TypeError),
    ],
)
def test_discrete_state_validation_fails_closed(values, error):
    with pytest.raises(error):
        discrete_transfer_entropy(
            values, values, target_history=1, source_history=1, source_lag=1
        )


def test_transfer_entropy_rejects_invalid_lengths_histories_and_types():
    source = np.array([0, 1, 0, 1, 0])
    target = np.array([0, 1, 1, 0, 1])
    with pytest.raises(ValueError, match="same length"):
        discrete_transfer_entropy(
            source[:-1], target, target_history=1, source_history=1, source_lag=1
        )
    for name, kwargs in [
        ("target_history", dict(target_history=0, source_history=1, source_lag=1)),
        ("source_history", dict(target_history=1, source_history=0, source_lag=1)),
        ("source_lag", dict(target_history=1, source_history=1, source_lag=0)),
    ]:
        with pytest.raises(ValueError, match=name):
            discrete_transfer_entropy(source, target, **kwargs)
    with pytest.raises(TypeError, match="target_history"):
        discrete_transfer_entropy(
            source, target, target_history=True, source_history=1, source_lag=1
        )
    with pytest.raises(ValueError, match="no effective transitions"):
        discrete_transfer_entropy(
            source, target, target_history=5, source_history=1, source_lag=1
        )


def test_circular_shift_validation_fails_closed():
    source = np.tile([0, 1], 10)
    target = np.roll(source, 1)
    common = dict(target_history=1, source_history=1, source_lag=1)
    with pytest.raises(TypeError, match="non-string"):
        transfer_entropy_circular_shift_test(source, target, shifts="1,2", **common)
    with pytest.raises(ValueError, match="at least one"):
        transfer_entropy_circular_shift_test(source, target, shifts=(), **common)
    with pytest.raises(ValueError, match="1 <= shift"):
        transfer_entropy_circular_shift_test(source, target, shifts=(0,), **common)
    with pytest.raises(ValueError, match="1 <= shift"):
        transfer_entropy_circular_shift_test(source, target, shifts=(len(source),), **common)
    with pytest.raises(TypeError, match="must be an integer"):
        transfer_entropy_circular_shift_test(source, target, shifts=(1.5,), **common)
    with pytest.raises(ValueError, match="unique"):
        transfer_entropy_circular_shift_test(source, target, shifts=(3, 3), **common)


def test_helper_type_validation():
    with pytest.raises(TypeError):
        transfer_entropy_local_frame(object())
    with pytest.raises(TypeError):
        transfer_entropy_reporting_text(object())
    with pytest.raises(TypeError):
        transfer_entropy_circular_shift_reporting_text(object())
    with pytest.raises(TypeError):
        plot_transfer_entropy_circular_shift_test(object())
