"""Specification-sensitivity analysis for discrete transfer entropy."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from itertools import product

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .transfer_entropy import (
    discrete_transfer_entropy,
    transfer_entropy_circular_shift_test,
)


@dataclass(frozen=True)
class TransferEntropySensitivityResult:
    """Declared multiverse of discrete transfer-entropy specifications."""

    table: pd.DataFrame
    summary_table: pd.DataFrame
    parameter_columns: tuple[str, ...]
    metric_columns: tuple[str, ...]
    source_states: np.ndarray
    target_states: np.ndarray
    target_histories: tuple[int, ...]
    source_histories: tuple[int, ...]
    source_lags: tuple[int, ...]
    shifts: np.ndarray | None
    provenance: dict[str, object]

    @property
    def n_specifications(self) -> int:
        return len(self.table)

    @property
    def has_surrogate_inference(self) -> bool:
        return self.shifts is not None


def _positive_integer_grid(
    values: Sequence[int],
    *,
    name: str,
) -> tuple[int, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{name} must be a non-string sequence")
    try:
        supplied = tuple(values)
    except TypeError as exc:
        raise TypeError(f"{name} must be a non-string sequence") from exc
    if not supplied:
        raise ValueError(f"{name} must contain at least one value")

    resolved: list[int] = []
    for value in supplied:
        if isinstance(value, (bool, np.bool_)) or not isinstance(
            value, (int, np.integer)
        ):
            raise TypeError(f"{name} values must be integers")
        integer = int(value)
        if integer < 1:
            raise ValueError(f"{name} values must be >= 1")
        resolved.append(integer)
    if len(set(resolved)) != len(resolved):
        raise ValueError(f"{name} must not contain duplicate values")
    return tuple(resolved)


def _variation_summary(
    table: pd.DataFrame,
    metric_columns: Sequence[str],
) -> pd.DataFrame:
    rows: list[dict[str, float | int | str]] = []
    for metric in metric_columns:
        values = pd.to_numeric(table[metric], errors="coerce").to_numpy(dtype=float)
        finite = values[np.isfinite(values)]
        rows.append(
            {
                "metric": metric,
                "n_specifications": int(values.size),
                "n_finite": int(finite.size),
                "finite_fraction": float(finite.size / values.size),
                "minimum": float(np.min(finite)) if finite.size else float("nan"),
                "q25": float(np.quantile(finite, 0.25)) if finite.size else float("nan"),
                "median": float(np.median(finite)) if finite.size else float("nan"),
                "q75": float(np.quantile(finite, 0.75)) if finite.size else float("nan"),
                "maximum": float(np.max(finite)) if finite.size else float("nan"),
                "range": (
                    float(np.max(finite) - np.min(finite))
                    if finite.size
                    else float("nan")
                ),
                "standard_deviation": (
                    float(np.std(finite, ddof=1))
                    if finite.size > 1
                    else float("nan")
                ),
            }
        )
    return pd.DataFrame(rows)


def transfer_entropy_parameter_sensitivity(
    source: Sequence[int] | np.ndarray,
    target: Sequence[int] | np.ndarray,
    *,
    target_histories: Sequence[int],
    source_histories: Sequence[int],
    source_lags: Sequence[int],
    shifts: Sequence[int] | None = None,
) -> TransferEntropySensitivityResult:
    """Evaluate a predeclared transfer-entropy specification multiverse.

    Every Cartesian-product combination of target history, source history, and
    source lag is evaluated. If shifts are supplied, the exact same
    analyst-declared circular-shift set is used for every specification.

    Invalid specifications abort the analysis with the failing combination
    identified. No failed row is removed, no parameter is selected
    automatically, and the descriptive summaries are not sampling
    distributions or multiplicity-adjusted inference.
    """

    target_grid = _positive_integer_grid(
        target_histories,
        name="target_histories",
    )
    source_grid = _positive_integer_grid(
        source_histories,
        name="source_histories",
    )
    lag_grid = _positive_integer_grid(
        source_lags,
        name="source_lags",
    )

    rows: list[dict[str, float | int]] = []
    source_states: np.ndarray | None = None
    target_states: np.ndarray | None = None
    resolved_shifts: np.ndarray | None = None

    for specification_id, (target_history, source_history, source_lag) in enumerate(
        product(target_grid, source_grid, lag_grid)
    ):
        specification = (
            f"target_history={target_history}, "
            f"source_history={source_history}, "
            f"source_lag={source_lag}"
        )
        try:
            if shifts is None:
                observed = discrete_transfer_entropy(
                    source,
                    target,
                    target_history=target_history,
                    source_history=source_history,
                    source_lag=source_lag,
                )
                surrogate_mean = float("nan")
                surrogate_centered = float("nan")
                upper_tail_p = float("nan")
                p_resolution = float("nan")
                n_shifts = 0
            else:
                shift_test = transfer_entropy_circular_shift_test(
                    source,
                    target,
                    target_history=target_history,
                    source_history=source_history,
                    source_lag=source_lag,
                    shifts=shifts,
                )
                observed = shift_test.observed
                surrogate_mean = shift_test.surrogate_mean_bits
                surrogate_centered = shift_test.surrogate_centered_transfer_entropy_bits
                upper_tail_p = shift_test.upper_tail_p_value
                p_resolution = shift_test.p_value_resolution
                n_shifts = int(shift_test.shifts.size)
                if resolved_shifts is None:
                    resolved_shifts = shift_test.shifts.copy()
                elif not np.array_equal(resolved_shifts, shift_test.shifts):
                    raise RuntimeError(
                        "circular-shift set changed across specifications"
                    )
        except (TypeError, ValueError, RuntimeError) as exc:
            raise ValueError(
                "transfer entropy sensitivity failed for "
                f"{specification}: {exc}"
            ) from exc

        if source_states is None:
            source_states = observed.source_states.copy()
            target_states = observed.target_states.copy()
        elif (
            not np.array_equal(source_states, observed.source_states)
            or target_states is None
            or not np.array_equal(target_states, observed.target_states)
        ):
            raise RuntimeError(
                "source/target states changed across sensitivity specifications"
            )

        rows.append(
            {
                "specification_id": specification_id,
                "target_history": target_history,
                "source_history": source_history,
                "source_lag": source_lag,
                "transfer_entropy_bits": observed.transfer_entropy_bits,
                "n_effective": observed.n_effective,
                "effective_fraction": observed.n_effective / observed.n_observations,
                "n_target_histories": observed.n_target_histories,
                "n_joint_histories": observed.n_joint_histories,
                "singleton_joint_history_fraction": (
                    observed.singleton_joint_history_fraction
                ),
                "min_joint_history_count": observed.min_joint_history_count,
                "max_joint_history_count": observed.max_joint_history_count,
                "mean_joint_history_count": (
                    observed.n_effective / observed.n_joint_histories
                ),
                "surrogate_mean_bits": surrogate_mean,
                "surrogate_centered_transfer_entropy_bits": surrogate_centered,
                "upper_tail_p_value": upper_tail_p,
                "p_value_resolution": p_resolution,
                "n_shifts": n_shifts,
            }
        )

    if source_states is None or target_states is None:
        raise RuntimeError("sensitivity analysis produced no specifications")

    table = pd.DataFrame(rows)
    parameter_columns = ("target_history", "source_history", "source_lag")
    metrics = [
        "transfer_entropy_bits",
        "n_effective",
        "effective_fraction",
        "n_target_histories",
        "n_joint_histories",
        "singleton_joint_history_fraction",
        "min_joint_history_count",
        "mean_joint_history_count",
    ]
    if shifts is not None:
        metrics.extend(
            [
                "surrogate_mean_bits",
                "surrogate_centered_transfer_entropy_bits",
                "upper_tail_p_value",
            ]
        )
    metric_columns = tuple(metrics)
    summary = _variation_summary(table, metric_columns)

    return TransferEntropySensitivityResult(
        table=table,
        summary_table=summary,
        parameter_columns=parameter_columns,
        metric_columns=metric_columns,
        source_states=source_states,
        target_states=target_states,
        target_histories=target_grid,
        source_histories=source_grid,
        source_lags=lag_grid,
        shifts=resolved_shifts,
        provenance={
            "operation": "transfer_entropy_parameter_sensitivity",
            "design": "full_cartesian_product",
            "target_histories": list(target_grid),
            "source_histories": list(source_grid),
            "source_lags_samples": list(lag_grid),
            "n_specifications": int(len(table)),
            "surrogate_inference": shifts is not None,
            "shifts_samples": (
                resolved_shifts.tolist() if resolved_shifts is not None else None
            ),
            "automatic_discretization": False,
            "automatic_history_selection": False,
            "automatic_lag_selection": False,
            "automatic_specification_ranking": False,
            "failed_specification_policy": "raise",
            "summary_interpretation": "descriptive_across_declared_specifications",
        },
    )


def _sensitivity_slice(
    result: TransferEntropySensitivityResult,
    *,
    parameter: str,
    filters: Mapping[str, int] | None,
) -> pd.DataFrame:
    if not isinstance(result, TransferEntropySensitivityResult):
        raise TypeError("result must be a TransferEntropySensitivityResult")
    if parameter not in result.parameter_columns:
        raise KeyError(
            f"parameter must be one of {result.parameter_columns}, got {parameter!r}"
        )
    selected = result.table.copy()
    resolved_filters = {} if filters is None else dict(filters)
    if parameter in resolved_filters:
        raise ValueError("filters must not include the plotted parameter")
    unknown = sorted(set(resolved_filters) - set(result.parameter_columns))
    if unknown:
        raise KeyError(f"Unknown sensitivity filter parameters: {unknown}")

    for name, value in resolved_filters.items():
        if isinstance(value, (bool, np.bool_)) or not isinstance(
            value, (int, np.integer)
        ):
            raise TypeError(f"filter value for {name} must be an integer")
        selected = selected.loc[selected[name] == int(value)]

    if selected.empty:
        raise ValueError("sensitivity filters selected no specifications")

    unresolved = [
        name
        for name in result.parameter_columns
        if name != parameter and selected[name].nunique() > 1
    ]
    if unresolved:
        raise ValueError(
            "plotting refuses hidden averaging; provide filters for "
            f"non-plotted parameters with multiple values: {unresolved}"
        )
    if selected[parameter].duplicated().any():
        raise RuntimeError(
            "sensitivity slice contains duplicate plotted-parameter values"
        )
    return selected.sort_values(parameter)


def plot_transfer_entropy_sensitivity(
    result: TransferEntropySensitivityResult,
    *,
    parameter: str,
    metric: str = "transfer_entropy_bits",
    filters: Mapping[str, int] | None = None,
    ax=None,
):
    """Plot one explicit TE-sensitivity slice without hidden averaging."""

    if not isinstance(result, TransferEntropySensitivityResult):
        raise TypeError("result must be a TransferEntropySensitivityResult")
    if metric not in result.metric_columns:
        raise KeyError(
            f"metric must be one of {result.metric_columns}, got {metric!r}"
        )
    selected = _sensitivity_slice(
        result,
        parameter=parameter,
        filters=filters,
    )
    if ax is None:
        _, ax = plt.subplots()
    ax.plot(selected[parameter], selected[metric], marker="o")
    ax.set_xlabel(parameter.replace("_", " "))
    ax.set_ylabel(metric.replace("_", " "))
    ax.set_title("Transfer-entropy specification sensitivity")
    return ax


def transfer_entropy_parameter_sensitivity_reporting_text(
    result: TransferEntropySensitivityResult,
) -> str:
    """Return manuscript-oriented wording for a TE specification multiverse."""

    if not isinstance(result, TransferEntropySensitivityResult):
        raise TypeError("result must be a TransferEntropySensitivityResult")
    table = result.table
    te = table["transfer_entropy_bits"].to_numpy(dtype=float)
    singleton = table["singleton_joint_history_fraction"].to_numpy(dtype=float)
    support = table["min_joint_history_count"].to_numpy(dtype=float)

    text = (
        f"Transfer-entropy specification sensitivity evaluated "
        f"{result.n_specifications} predeclared combinations of target history "
        f"{result.target_histories}, source history {result.source_histories}, "
        f"and source lag {result.source_lags} sample(s). Empirical TE ranged "
        f"from {np.min(te):.6g} to {np.max(te):.6g} bits "
        f"(median {np.median(te):.6g}). Across specifications, the fraction "
        f"of observed joint histories occurring once ranged from "
        f"{np.min(singleton):.3f} to {np.max(singleton):.3f}, and the minimum "
        f"joint-history cell count ranged from {int(np.min(support))} to "
        f"{int(np.max(support))}."
    )
    if result.has_surrogate_inference:
        centered = table[
            "surrogate_centered_transfer_entropy_bits"
        ].to_numpy(dtype=float)
        pvalues = table["upper_tail_p_value"].to_numpy(dtype=float)
        text += (
            f" The same {result.shifts.size} analyst-declared circular source "
            f"shifts were used for every specification; surrogate-centered TE "
            f"ranged from {np.min(centered):.6g} to {np.max(centered):.6g} "
            f"bits and unadjusted plus-one upper-tail p-values ranged from "
            f"{np.min(pvalues):.6g} to {np.max(pvalues):.6g}."
        )
    return text + (
        " These summaries describe robustness across the declared multiverse; "
        "they are not a sampling distribution, no specification was selected "
        "or ranked automatically, and p-values across specifications are not "
        "multiplicity-adjusted causal evidence."
    )
