"""Discrete transfer-entropy analysis with explicit scientific contracts."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class DiscreteTransferEntropyResult:
    """Empirical plug-in transfer entropy for two discrete state sequences."""

    transfer_entropy_bits: float
    local_transfer_entropy_bits: np.ndarray
    time_indices: np.ndarray
    source_states: np.ndarray
    target_states: np.ndarray
    target_history: int
    source_history: int
    source_lag: int
    n_observations: int
    n_effective: int
    n_source_states: int
    n_target_states: int
    n_target_histories: int
    n_joint_histories: int
    singleton_joint_history_fraction: float
    min_joint_history_count: int
    max_joint_history_count: int
    provenance: dict[str, object]


@dataclass(frozen=True)
class TransferEntropyCircularShiftTestResult:
    """Circular-shift surrogate test for one declared discrete TE contract."""

    observed: DiscreteTransferEntropyResult
    shifts: np.ndarray
    surrogate_transfer_entropy_bits: np.ndarray
    surrogate_mean_bits: float
    surrogate_centered_transfer_entropy_bits: float
    upper_tail_p_value: float
    p_value_resolution: float
    provenance: dict[str, object]


def _positive_integer(value: int, name: str) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
        raise TypeError(f"{name} must be an integer")
    resolved = int(value)
    if resolved < 1:
        raise ValueError(f"{name} must be >= 1")
    return resolved


def _discrete_states(values: Sequence[int] | np.ndarray, name: str) -> np.ndarray:
    array = np.asarray(values)
    if array.ndim != 1:
        raise ValueError(f"{name} must be one-dimensional")
    if array.size == 0:
        raise ValueError(f"{name} must not be empty")
    if array.dtype.kind in "iub":
        return array.astype(np.int64, copy=True)
    if array.dtype.kind == "f":
        if not np.all(np.isfinite(array)):
            raise ValueError(f"{name} must not contain missing or non-finite values")
        if not np.all(array == np.floor(array)):
            raise TypeError(
                f"{name} must contain discrete integer-coded states; "
                "discretize explicitly upstream"
            )
        return array.astype(np.int64)
    raise TypeError(
        f"{name} must contain discrete integer-coded states; "
        "discretize explicitly upstream"
    )


def _history_records(
    source: np.ndarray,
    target: np.ndarray,
    *,
    target_history: int,
    source_history: int,
    source_lag: int,
) -> tuple[int, list[tuple[int, tuple[int, ...], tuple[int, ...]]]]:
    first_index = max(target_history, source_lag + source_history - 1)
    if source.size - first_index < 1:
        raise ValueError("history and lag settings leave no effective transitions")
    records = []
    for time_index in range(first_index, source.size):
        target_past = tuple(
            int(target[time_index - offset])
            for offset in range(1, target_history + 1)
        )
        source_past = tuple(
            int(source[time_index - source_lag - offset])
            for offset in range(source_history)
        )
        records.append((int(target[time_index]), target_past, source_past))
    return first_index, records


def discrete_transfer_entropy(
    source: Sequence[int] | np.ndarray,
    target: Sequence[int] | np.ndarray,
    *,
    target_history: int,
    source_history: int,
    source_lag: int,
) -> DiscreteTransferEntropyResult:
    """Estimate empirical discrete transfer entropy from source to target.

    The estimator is empirical plug-in conditional mutual information in bits.
    History lengths and source lag are required sample-index settings. Continuous
    observations are never binned, rounded, scaled, smoothed, or interpolated.
    A positive estimate is not interpreted as proof of causal influence.
    """

    source_states = _discrete_states(source, "source")
    target_states = _discrete_states(target, "target")
    if source_states.shape != target_states.shape:
        raise ValueError("source and target must have the same length")

    target_history = _positive_integer(target_history, "target_history")
    source_history = _positive_integer(source_history, "source_history")
    source_lag = _positive_integer(source_lag, "source_lag")
    first_index, records = _history_records(
        source_states,
        target_states,
        target_history=target_history,
        source_history=source_history,
        source_lag=source_lag,
    )

    transition_counts = Counter(records)
    joint_history_counts = Counter(
        (target_past, source_past)
        for _, target_past, source_past in records
    )
    target_transition_counts = Counter(
        (target_state, target_past)
        for target_state, target_past, _ in records
    )
    target_history_counts = Counter(
        target_past for _, target_past, _ in records
    )

    local = np.empty(len(records), dtype=float)
    for index, (target_state, target_past, source_past) in enumerate(records):
        numerator = (
            transition_counts[(target_state, target_past, source_past)]
            * target_history_counts[target_past]
        )
        denominator = (
            joint_history_counts[(target_past, source_past)]
            * target_transition_counts[(target_state, target_past)]
        )
        local[index] = np.log2(numerator / denominator)

    joint_support = np.asarray(list(joint_history_counts.values()), dtype=int)
    return DiscreteTransferEntropyResult(
        transfer_entropy_bits=float(np.mean(local)),
        local_transfer_entropy_bits=local,
        time_indices=np.arange(first_index, source_states.size, dtype=int),
        source_states=source_states.copy(),
        target_states=target_states.copy(),
        target_history=target_history,
        source_history=source_history,
        source_lag=source_lag,
        n_observations=int(source_states.size),
        n_effective=int(local.size),
        n_source_states=int(np.unique(source_states).size),
        n_target_states=int(np.unique(target_states).size),
        n_target_histories=int(len(target_history_counts)),
        n_joint_histories=int(len(joint_history_counts)),
        singleton_joint_history_fraction=float(np.mean(joint_support == 1)),
        min_joint_history_count=int(joint_support.min()),
        max_joint_history_count=int(joint_support.max()),
        provenance={
            "operation": "discrete_transfer_entropy",
            "estimator": "empirical_plugin_conditional_mutual_information",
            "log_base": 2,
            "target_history": target_history,
            "source_history": source_history,
            "source_lag_samples": source_lag,
            "state_representation": "analyst_supplied_integer_codes",
            "automatic_discretization": False,
            "automatic_history_selection": False,
            "automatic_lag_selection": False,
        },
    )


def transfer_entropy_local_frame(result: DiscreteTransferEntropyResult) -> pd.DataFrame:
    """Return local TE contributions and the histories used for each row."""

    if not isinstance(result, DiscreteTransferEntropyResult):
        raise TypeError("result must be a DiscreteTransferEntropyResult")
    rows = []
    for time_index, local_value in zip(
        result.time_indices,
        result.local_transfer_entropy_bits,
        strict=True,
    ):
        target_past = tuple(
            int(result.target_states[time_index - offset])
            for offset in range(1, result.target_history + 1)
        )
        source_past = tuple(
            int(result.source_states[time_index - result.source_lag - offset])
            for offset in range(result.source_history)
        )
        rows.append(
            {
                "time_index": int(time_index),
                "target_state": int(result.target_states[time_index]),
                "target_history": target_past,
                "source_history": source_past,
                "local_transfer_entropy_bits": float(local_value),
            }
        )
    return pd.DataFrame(rows)


def transfer_entropy_circular_shift_test(
    source: Sequence[int] | np.ndarray,
    target: Sequence[int] | np.ndarray,
    *,
    target_history: int,
    source_history: int,
    source_lag: int,
    shifts: Sequence[int],
) -> TransferEntropyCircularShiftTestResult:
    """Compare observed TE with analyst-declared circular source shifts.

    The shift set is mandatory and is never generated or optimized. The returned
    p-value is the plus-one upper-tail Monte Carlo value. Circular shifts require
    a defensible wrap-around/stationarity assumption and do not establish causality.
    """

    source_states = _discrete_states(source, "source")
    target_states = _discrete_states(target, "target")
    if source_states.shape != target_states.shape:
        raise ValueError("source and target must have the same length")
    if isinstance(shifts, (str, bytes)):
        raise TypeError("shifts must be a non-string sequence of integers")
    try:
        supplied_shifts = tuple(shifts)
    except TypeError as exc:
        raise TypeError("shifts must be a non-string sequence of integers") from exc
    if not supplied_shifts:
        raise ValueError("shifts must contain at least one circular shift")

    resolved_shifts = []
    for shift in supplied_shifts:
        if isinstance(shift, (bool, np.bool_)) or not isinstance(shift, (int, np.integer)):
            raise TypeError("each circular shift must be an integer")
        resolved = int(shift)
        if not 1 <= resolved < source_states.size:
            raise ValueError(
                "each circular shift must satisfy 1 <= shift < series length"
            )
        resolved_shifts.append(resolved)
    if len(set(resolved_shifts)) != len(resolved_shifts):
        raise ValueError("circular shifts must be unique")

    observed = discrete_transfer_entropy(
        source_states,
        target_states,
        target_history=target_history,
        source_history=source_history,
        source_lag=source_lag,
    )
    surrogate = np.asarray(
        [
            discrete_transfer_entropy(
                np.roll(source_states, shift),
                target_states,
                target_history=target_history,
                source_history=source_history,
                source_lag=source_lag,
            ).transfer_entropy_bits
            for shift in resolved_shifts
        ],
        dtype=float,
    )
    surrogate_mean = float(np.mean(surrogate))
    upper_tail = float(
        (1 + np.count_nonzero(surrogate >= observed.transfer_entropy_bits))
        / (surrogate.size + 1)
    )
    return TransferEntropyCircularShiftTestResult(
        observed=observed,
        shifts=np.asarray(resolved_shifts, dtype=int),
        surrogate_transfer_entropy_bits=surrogate,
        surrogate_mean_bits=surrogate_mean,
        surrogate_centered_transfer_entropy_bits=float(
            observed.transfer_entropy_bits - surrogate_mean
        ),
        upper_tail_p_value=upper_tail,
        p_value_resolution=float(1.0 / (surrogate.size + 1)),
        provenance={
            "operation": "transfer_entropy_circular_shift_test",
            "null": "analyst_declared_circular_source_shifts",
            "tail": "upper",
            "p_value": "plus_one_monte_carlo",
            "shifts_samples": list(resolved_shifts),
            "observed_contract": dict(observed.provenance),
            "automatic_shift_generation": False,
        },
    )


def plot_transfer_entropy_circular_shift_test(
    result: TransferEntropyCircularShiftTestResult,
    *,
    ax=None,
    bins: int | str = "auto",
):
    """Plot the circular-shift null distribution and observed TE."""

    if not isinstance(result, TransferEntropyCircularShiftTestResult):
        raise TypeError("result must be a TransferEntropyCircularShiftTestResult")
    if ax is None:
        _, ax = plt.subplots()
    ax.hist(result.surrogate_transfer_entropy_bits, bins=bins)
    ax.axvline(result.observed.transfer_entropy_bits, linestyle="--")
    ax.set_xlabel("Transfer entropy (bits)")
    ax.set_ylabel("Circular-shift surrogates")
    ax.set_title("Transfer-entropy circular-shift test")
    return ax


def transfer_entropy_reporting_text(result: DiscreteTransferEntropyResult) -> str:
    """Return compact manuscript-oriented text for a TE estimate."""

    if not isinstance(result, DiscreteTransferEntropyResult):
        raise TypeError("result must be a DiscreteTransferEntropyResult")
    return (
        "Discrete empirical transfer entropy from source to target was "
        f"{result.transfer_entropy_bits:.6g} bits using target history "
        f"k={result.target_history}, source history l={result.source_history}, "
        f"and source lag d={result.source_lag} sample(s), based on "
        f"{result.n_effective} effective transitions. Joint-history support "
        f"included {result.n_joint_histories} observed states, with "
        f"{result.singleton_joint_history_fraction:.3f} occurring once. "
        "The estimate is conditional on the declared discrete state representation "
        "and does not by itself establish causal influence."
    )


def transfer_entropy_circular_shift_reporting_text(
    result: TransferEntropyCircularShiftTestResult,
) -> str:
    """Return compact reporting text for a circular-shift TE test."""

    if not isinstance(result, TransferEntropyCircularShiftTestResult):
        raise TypeError("result must be a TransferEntropyCircularShiftTestResult")
    return (
        f"Observed transfer entropy was {result.observed.transfer_entropy_bits:.6g} bits; "
        f"the mean across {result.shifts.size} analyst-declared circular source shifts "
        f"was {result.surrogate_mean_bits:.6g} bits, giving a surrogate-centered "
        f"difference of {result.surrogate_centered_transfer_entropy_bits:.6g} bits. "
        f"The plus-one upper-tail Monte Carlo p-value was {result.upper_tail_p_value:.6g} "
        f"(minimum attainable resolution {result.p_value_resolution:.6g}). "
        "The null preserves the source marginal and circular auto-dependence but assumes "
        "the declared wrap-around shifts are scientifically defensible; the test does not "
        "establish causality."
    )
