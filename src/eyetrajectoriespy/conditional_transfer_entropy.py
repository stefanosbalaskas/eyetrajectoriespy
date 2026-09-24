"""Discrete conditional transfer entropy with explicit scientific contracts."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .transfer_entropy import _discrete_states, _positive_integer


@dataclass(frozen=True)
class ConditionalTransferEntropyResult:
    """Empirical plug-in conditional transfer entropy for discrete sequences."""

    conditional_transfer_entropy_bits: float
    local_conditional_transfer_entropy_bits: np.ndarray
    time_indices: np.ndarray
    source_states: np.ndarray
    target_states: np.ndarray
    condition_states: np.ndarray
    target_history_states: np.ndarray
    source_history_states: np.ndarray
    condition_history_states: np.ndarray
    target_history: int
    source_history: int
    condition_history: int
    source_lag: int
    condition_lag: int
    n_observations: int
    n_effective: int
    n_source_states: int
    n_target_states: int
    n_condition_states: int
    n_target_histories: int
    n_condition_histories: int
    n_target_condition_histories: int
    n_source_condition_histories: int
    n_joint_histories: int
    singleton_joint_history_fraction: float
    min_joint_history_count: int
    max_joint_history_count: int
    mean_joint_history_count: float
    provenance: dict[str, object]


@dataclass(frozen=True)
class ConditionalTransferEntropyCircularShiftTestResult:
    """Source-only circular-shift test for one declared conditional-TE contract."""

    observed: ConditionalTransferEntropyResult
    shifts: np.ndarray
    surrogate_conditional_transfer_entropy_bits: np.ndarray
    surrogate_mean_bits: float
    surrogate_centered_conditional_transfer_entropy_bits: float
    upper_tail_p_value: float
    p_value_resolution: float
    provenance: dict[str, object]


def _conditional_history_records(
    source: np.ndarray,
    target: np.ndarray,
    condition: np.ndarray,
    *,
    target_history: int,
    source_history: int,
    condition_history: int,
    source_lag: int,
    condition_lag: int,
) -> tuple[
    int,
    list[
        tuple[
            int,
            tuple[int, ...],
            tuple[int, ...],
            tuple[int, ...],
        ]
    ],
]:
    first_index = max(
        target_history,
        source_lag + source_history - 1,
        condition_lag + condition_history - 1,
    )
    if source.size - first_index < 1:
        raise ValueError(
            "history and lag settings leave no effective transitions"
        )

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
        condition_past = tuple(
            int(condition[time_index - condition_lag - offset])
            for offset in range(condition_history)
        )
        records.append(
            (
                int(target[time_index]),
                target_past,
                source_past,
                condition_past,
            )
        )
    return first_index, records


def conditional_transfer_entropy(
    source: Sequence[int] | np.ndarray,
    target: Sequence[int] | np.ndarray,
    condition: Sequence[int] | np.ndarray,
    *,
    target_history: int,
    source_history: int,
    condition_history: int,
    source_lag: int,
    condition_lag: int,
) -> ConditionalTransferEntropyResult:
    """Estimate empirical discrete conditional transfer entropy in bits.

    The estimand is the conditional mutual information between the declared
    source history and the next target state, conditional on both the target
    history and the declared conditioning-process history.

    Input state sequences must be analyst-supplied integer codes. No automatic
    discretization, smoothing, scaling, interpolation, history selection, lag
    selection, support filtering, or causal interpretation is introduced.
    """

    source_states = _discrete_states(source, "source")
    target_states = _discrete_states(target, "target")
    condition_states = _discrete_states(condition, "condition")
    if not (
        source_states.shape == target_states.shape == condition_states.shape
    ):
        raise ValueError(
            "source, target, and condition must have the same length"
        )

    target_history = _positive_integer(target_history, "target_history")
    source_history = _positive_integer(source_history, "source_history")
    condition_history = _positive_integer(
        condition_history, "condition_history"
    )
    source_lag = _positive_integer(source_lag, "source_lag")
    condition_lag = _positive_integer(condition_lag, "condition_lag")

    first_index, records = _conditional_history_records(
        source_states,
        target_states,
        condition_states,
        target_history=target_history,
        source_history=source_history,
        condition_history=condition_history,
        source_lag=source_lag,
        condition_lag=condition_lag,
    )

    full_transition_counts = Counter(records)
    full_history_counts = Counter(
        (target_past, source_past, condition_past)
        for _, target_past, source_past, condition_past in records
    )
    conditioned_transition_counts = Counter(
        (target_state, target_past, condition_past)
        for target_state, target_past, _, condition_past in records
    )
    target_condition_history_counts = Counter(
        (target_past, condition_past)
        for _, target_past, _, condition_past in records
    )
    target_history_counts = Counter(
        target_past
        for _, target_past, _, _ in records
    )
    condition_history_counts = Counter(
        condition_past
        for _, _, _, condition_past in records
    )
    source_condition_history_counts = Counter(
        (source_past, condition_past)
        for _, _, source_past, condition_past in records
    )

    local = np.empty(len(records), dtype=float)
    target_history_states = np.empty(
        (len(records), target_history),
        dtype=np.int64,
    )
    source_history_states = np.empty(
        (len(records), source_history),
        dtype=np.int64,
    )
    condition_history_states = np.empty(
        (len(records), condition_history),
        dtype=np.int64,
    )

    for index, (
        target_state,
        target_past,
        source_past,
        condition_past,
    ) in enumerate(records):
        numerator = (
            full_transition_counts[
                (target_state, target_past, source_past, condition_past)
            ]
            * target_condition_history_counts[
                (target_past, condition_past)
            ]
        )
        denominator = (
            full_history_counts[
                (target_past, source_past, condition_past)
            ]
            * conditioned_transition_counts[
                (target_state, target_past, condition_past)
            ]
        )
        local[index] = np.log2(numerator / denominator)
        target_history_states[index] = target_past
        source_history_states[index] = source_past
        condition_history_states[index] = condition_past

    joint_support = np.asarray(
        list(full_history_counts.values()),
        dtype=int,
    )
    return ConditionalTransferEntropyResult(
        conditional_transfer_entropy_bits=float(np.mean(local)),
        local_conditional_transfer_entropy_bits=local,
        time_indices=np.arange(
            first_index,
            source_states.size,
            dtype=int,
        ),
        source_states=source_states.copy(),
        target_states=target_states.copy(),
        condition_states=condition_states.copy(),
        target_history_states=target_history_states,
        source_history_states=source_history_states,
        condition_history_states=condition_history_states,
        target_history=target_history,
        source_history=source_history,
        condition_history=condition_history,
        source_lag=source_lag,
        condition_lag=condition_lag,
        n_observations=int(source_states.size),
        n_effective=int(local.size),
        n_source_states=int(np.unique(source_states).size),
        n_target_states=int(np.unique(target_states).size),
        n_condition_states=int(np.unique(condition_states).size),
        n_target_histories=int(len(target_history_counts)),
        n_condition_histories=int(len(condition_history_counts)),
        n_target_condition_histories=int(
            len(target_condition_history_counts)
        ),
        n_source_condition_histories=int(
            len(source_condition_history_counts)
        ),
        n_joint_histories=int(len(full_history_counts)),
        singleton_joint_history_fraction=float(
            np.mean(joint_support == 1)
        ),
        min_joint_history_count=int(joint_support.min()),
        max_joint_history_count=int(joint_support.max()),
        mean_joint_history_count=float(np.mean(joint_support)),
        provenance={
            "operation": "conditional_transfer_entropy",
            "estimator": (
                "empirical_plugin_conditional_mutual_information"
            ),
            "log_base": 2,
            "target_history": target_history,
            "source_history": source_history,
            "condition_history": condition_history,
            "source_lag_samples": source_lag,
            "condition_lag_samples": condition_lag,
            "state_representation": "analyst_supplied_integer_codes",
            "conditioning_interpretation": (
                "incremental_directed_predictive_information"
            ),
            "automatic_discretization": False,
            "automatic_history_selection": False,
            "automatic_lag_selection": False,
            "automatic_support_filtering": False,
            "causal_identification_claimed": False,
        },
    )


def conditional_transfer_entropy_local_frame(
    result: ConditionalTransferEntropyResult,
) -> pd.DataFrame:
    """Return local conditional-TE contributions and exact histories."""

    if not isinstance(result, ConditionalTransferEntropyResult):
        raise TypeError(
            "result must be a ConditionalTransferEntropyResult"
        )

    rows = []
    for index, time_index in enumerate(result.time_indices):
        rows.append(
            {
                "time_index": int(time_index),
                "target_state": int(
                    result.target_states[time_index]
                ),
                "target_history": tuple(
                    int(value)
                    for value in result.target_history_states[index]
                ),
                "source_history": tuple(
                    int(value)
                    for value in result.source_history_states[index]
                ),
                "condition_history": tuple(
                    int(value)
                    for value in result.condition_history_states[index]
                ),
                "local_conditional_transfer_entropy_bits": float(
                    result.local_conditional_transfer_entropy_bits[index]
                ),
            }
        )
    return pd.DataFrame(rows)


def _resolve_shifts(
    shifts: Sequence[int],
    *,
    n_observations: int,
) -> np.ndarray:
    if isinstance(shifts, (str, bytes)):
        raise TypeError(
            "shifts must be a non-string sequence of integers"
        )
    try:
        supplied = tuple(shifts)
    except TypeError as exc:
        raise TypeError(
            "shifts must be a non-string sequence of integers"
        ) from exc
    if not supplied:
        raise ValueError(
            "shifts must contain at least one circular shift"
        )

    resolved = []
    for shift in supplied:
        if isinstance(shift, (bool, np.bool_)) or not isinstance(
            shift,
            (int, np.integer),
        ):
            raise TypeError("each circular shift must be an integer")
        integer = int(shift)
        if not 1 <= integer < n_observations:
            raise ValueError(
                "each circular shift must satisfy "
                "1 <= shift < series length"
            )
        resolved.append(integer)
    if len(set(resolved)) != len(resolved):
        raise ValueError("circular shifts must be unique")
    return np.asarray(resolved, dtype=int)


def conditional_transfer_entropy_circular_shift_test(
    source: Sequence[int] | np.ndarray,
    target: Sequence[int] | np.ndarray,
    condition: Sequence[int] | np.ndarray,
    *,
    target_history: int,
    source_history: int,
    condition_history: int,
    source_lag: int,
    condition_lag: int,
    shifts: Sequence[int],
) -> ConditionalTransferEntropyCircularShiftTestResult:
    """Test conditional TE using analyst-declared source-only circular shifts.

    Only the source sequence is shifted. Target and conditioning sequences stay
    fixed. The returned p-value is the plus-one upper-tail Monte Carlo value.
    This is a predictive-information null under a declared circular-shift
    construction, not a causal-identification test.
    """

    source_states = _discrete_states(source, "source")
    target_states = _discrete_states(target, "target")
    condition_states = _discrete_states(condition, "condition")
    if not (
        source_states.shape == target_states.shape == condition_states.shape
    ):
        raise ValueError(
            "source, target, and condition must have the same length"
        )
    resolved_shifts = _resolve_shifts(
        shifts,
        n_observations=source_states.size,
    )

    observed = conditional_transfer_entropy(
        source_states,
        target_states,
        condition_states,
        target_history=target_history,
        source_history=source_history,
        condition_history=condition_history,
        source_lag=source_lag,
        condition_lag=condition_lag,
    )
    surrogate = np.asarray(
        [
            conditional_transfer_entropy(
                np.roll(source_states, shift),
                target_states,
                condition_states,
                target_history=target_history,
                source_history=source_history,
                condition_history=condition_history,
                source_lag=source_lag,
                condition_lag=condition_lag,
            ).conditional_transfer_entropy_bits
            for shift in resolved_shifts
        ],
        dtype=float,
    )
    surrogate_mean = float(np.mean(surrogate))
    upper_tail = float(
        (
            1
            + np.count_nonzero(
                surrogate
                >= observed.conditional_transfer_entropy_bits
            )
        )
        / (surrogate.size + 1)
    )

    return ConditionalTransferEntropyCircularShiftTestResult(
        observed=observed,
        shifts=resolved_shifts,
        surrogate_conditional_transfer_entropy_bits=surrogate,
        surrogate_mean_bits=surrogate_mean,
        surrogate_centered_conditional_transfer_entropy_bits=float(
            observed.conditional_transfer_entropy_bits - surrogate_mean
        ),
        upper_tail_p_value=upper_tail,
        p_value_resolution=float(1.0 / (surrogate.size + 1)),
        provenance={
            "operation": (
                "conditional_transfer_entropy_circular_shift_test"
            ),
            "null": (
                "analyst_declared_source_only_circular_shifts"
            ),
            "tail": "upper",
            "p_value": "plus_one_monte_carlo",
            "shifts_samples": resolved_shifts.tolist(),
            "shifted_process": "source",
            "fixed_processes": ["target", "condition"],
            "observed_contract": dict(observed.provenance),
            "automatic_shift_generation": False,
            "causal_identification_claimed": False,
        },
    )


def plot_conditional_transfer_entropy_circular_shift_test(
    result: ConditionalTransferEntropyCircularShiftTestResult,
    *,
    ax=None,
    bins: int | str = "auto",
):
    """Plot the source-shift null distribution and observed conditional TE."""

    if not isinstance(
        result,
        ConditionalTransferEntropyCircularShiftTestResult,
    ):
        raise TypeError(
            "result must be a "
            "ConditionalTransferEntropyCircularShiftTestResult"
        )
    if ax is None:
        _, ax = plt.subplots()
    ax.hist(
        result.surrogate_conditional_transfer_entropy_bits,
        bins=bins,
    )
    ax.axvline(
        result.observed.conditional_transfer_entropy_bits,
        linestyle="--",
    )
    ax.set_xlabel("Conditional transfer entropy (bits)")
    ax.set_ylabel("Source-only circular-shift surrogates")
    ax.set_title("Conditional-TE circular-shift test")
    return ax


def conditional_transfer_entropy_reporting_text(
    result: ConditionalTransferEntropyResult,
) -> str:
    """Return compact manuscript-oriented text for conditional TE."""

    if not isinstance(result, ConditionalTransferEntropyResult):
        raise TypeError(
            "result must be a ConditionalTransferEntropyResult"
        )
    return (
        "Discrete empirical conditional transfer entropy from source to target "
        f"given the declared conditioning process was "
        f"{result.conditional_transfer_entropy_bits:.6g} bits using target "
        f"history k={result.target_history}, source history "
        f"l={result.source_history}, conditioning history "
        f"m={result.condition_history}, source lag d={result.source_lag}, "
        f"and conditioning lag c={result.condition_lag} sample(s), based on "
        f"{result.n_effective} effective transitions. Full joint-history "
        f"support contained {result.n_joint_histories} observed states, with "
        f"{result.singleton_joint_history_fraction:.3f} occurring once "
        f"(minimum/mean/maximum cell count "
        f"{result.min_joint_history_count}/"
        f"{result.mean_joint_history_count:.3g}/"
        f"{result.max_joint_history_count}). "
        "This measures incremental directed predictive information after "
        "conditioning on the explicitly supplied process; it does not "
        "establish causal influence or guarantee adjustment for unmeasured "
        "common drivers."
    )


def conditional_transfer_entropy_circular_shift_reporting_text(
    result: ConditionalTransferEntropyCircularShiftTestResult,
) -> str:
    """Return compact reporting text for a source-shift conditional-TE test."""

    if not isinstance(
        result,
        ConditionalTransferEntropyCircularShiftTestResult,
    ):
        raise TypeError(
            "result must be a "
            "ConditionalTransferEntropyCircularShiftTestResult"
        )

    return (
        "Observed conditional transfer entropy was "
        f"{result.observed.conditional_transfer_entropy_bits:.6g} bits; "
        f"the mean across {result.shifts.size} analyst-declared source-only "
        f"circular shifts was {result.surrogate_mean_bits:.6g} bits, giving "
        "a surrogate-centered difference of "
        f"{result.surrogate_centered_conditional_transfer_entropy_bits:.6g} "
        "bits. The plus-one upper-tail Monte Carlo p-value was "
        f"{result.upper_tail_p_value:.6g} (minimum attainable resolution "
        f"{result.p_value_resolution:.6g}). Target and conditioning processes "
        "were held fixed while only the source was shifted. The null concerns "
        "additional directed predictive information under the declared "
        "conditioning and wrap-around assumptions; it does not establish "
        "causal influence."
    )
