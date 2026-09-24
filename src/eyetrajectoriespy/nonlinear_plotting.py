"""Plots for nonlinear trajectory dynamics and recurrence diagnostics."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import matplotlib.pyplot as plt
import numpy as np

from .nonlinear_types import (
    EmbeddingDelayDiagnosticResult,
    EmbeddingDimensionDiagnosticResult,
    KantzDivergenceResult,
    KantzParameterSensitivityResult,
    JointRecurrenceResult,
    LargestLyapunovResult,
    LyapunovParameterSensitivityResult,
    LocalDivergenceResult,
    MultivariateIAAFTResult,
    MultivariateSurrogateNonlinearityResult,
    LocalReturnMapResult,
    PoincareCrossingResult,
    RecurrenceRadiusProfileResult,
    RecurrenceResult,
    RQAMeanBootstrapResult,
    RQAParameterSensitivityResult,
    SurrogateNonlinearityResult,
    WindowedRQAFunctionalResult,
    WindowedRQAResult,
    WindowedRQASensitivityResult,
)


def plot_embedding_delay_diagnostics(
    result: EmbeddingDelayDiagnosticResult,
    *,
    ax=None,
):
    """Plot AMI and autocorrelation against lag without selecting a delay."""

    if ax is None:
        _, ax = plt.subplots()
    table = result.table
    ax.plot(table["lag_time"], table["average_mutual_information"], marker="o", label="AMI")
    ax.set_xlabel(f"Lag ({result.time_unit})")
    ax.set_ylabel("Average mutual information")
    ax2 = ax.twinx()
    ax2.plot(table["lag_time"], table["autocorrelation"], linestyle="--", label="ACF")
    ax2.set_ylabel("Autocorrelation")
    marked = table["first_ami_local_minimum"].to_numpy(dtype=bool)
    if np.any(marked):
        ax.scatter(
            table.loc[marked, "lag_time"],
            table.loc[marked, "average_mutual_information"],
            marker="x",
            s=70,
            label="First AMI local minimum",
        )
    ax.set_title(f"Embedding-delay diagnostics: {result.curve_id} / {result.dimension}")
    return ax


def plot_embedding_dimension_diagnostics(
    result: EmbeddingDimensionDiagnosticResult,
    *,
    ax=None,
):
    """Plot false-nearest-neighbor fraction against embedding dimension."""

    if ax is None:
        _, ax = plt.subplots()
    table = result.table
    ax.plot(
        table["embedding_dimension"],
        table["false_neighbor_fraction"],
        marker="o",
    )
    ax.set_xlabel("Embedding dimension")
    ax.set_ylabel("False-nearest-neighbor fraction")
    ax.set_ylim(bottom=0)
    ax.set_title(f"FNN diagnostics: {result.curve_id} / {result.dimension}")
    return ax


def plot_joint_recurrence(
    result: JointRecurrenceResult,
    *,
    max_points: int | None = 200_000,
    ax=None,
):
    """Plot a sparse joint recurrence matrix without densifying it."""

    if not isinstance(result, JointRecurrenceResult):
        raise TypeError("result must be a JointRecurrenceResult")
    if max_points is not None:
        if isinstance(max_points, (bool, np.bool_)) or not isinstance(
            max_points,
            (int, np.integer),
        ):
            raise TypeError("max_points must be an integer or None")
        max_points = int(max_points)
        if max_points < 1:
            raise ValueError("max_points must be positive or None")
        if result.matrix.nnz > max_points:
            raise ValueError(
                "joint recurrence matrix exceeds max_points; increase "
                "max_points explicitly rather than silently subsampling"
            )
    if ax is None:
        _, ax = plt.subplots()
    coo = result.matrix.tocoo()
    ax.scatter(coo.col, coo.row, s=4, marker="s")
    ax.set_xlabel("State index")
    ax.set_ylabel("State index")
    ax.invert_yaxis()
    ax.set_aspect("equal", adjustable="box")
    ax.set_title(
        "Joint recurrence "
        f"(JRR={result.joint_recurrence_rate:.3f}, "
        f"components={result.n_components})"
    )
    return ax


def plot_recurrence(
    result: RecurrenceResult,
    *,
    max_points: int | None = 200_000,
    ax=None,
):
    """Plot the sparse recurrence matrix without densifying it."""

    if max_points is not None and result.matrix.nnz > max_points:
        raise ValueError(
            "recurrence matrix exceeds max_points; increase max_points explicitly "
            "rather than silently subsampling recurrence points"
        )
    if ax is None:
        _, ax = plt.subplots()
    coo = result.matrix.tocoo()
    ax.scatter(coo.col, coo.row, s=4, marker="s")
    ax.set_xlabel("State index B" if result.kind == "cross" else "State index")
    ax.set_ylabel("State index A" if result.kind == "cross" else "State index")
    ax.invert_yaxis()
    ax.set_aspect("equal", adjustable="box")
    ax.set_title(
        f"{'Cross-' if result.kind == 'cross' else ''}recurrence "
        f"(RR={result.achieved_recurrence_rate:.3f})"
    )
    return ax


def plot_recurrence_rate_curve(
    result: RecurrenceRadiusProfileResult,
    *,
    ax=None,
):
    """Plot exact recurrence rate against the declared radius grid."""

    if ax is None:
        _, ax = plt.subplots()
    table = result.table
    ax.plot(
        table["radius"],
        table["recurrence_rate"],
        marker="o",
    )
    ax.set_xlabel(f"Radius ({result.metric} state-space distance)")
    ax.set_ylabel("Recurrence rate")
    ax.set_ylim(bottom=0.0, top=1.0)
    ax.set_title(f"Recurrence radius profile: {result.curve_id}")
    return ax


def plot_rqa_metric_mean_bootstrap(
    result: RQAMeanBootstrapResult,
    *,
    metrics: Sequence[str] | None = None,
    ax=None,
):
    """Plot population-average RQA metrics with percentile-bootstrap intervals."""

    selected_metrics = result.metrics if metrics is None else tuple(metrics)
    if not selected_metrics:
        raise ValueError("metrics must contain at least one RQA metric")
    unknown = [metric for metric in selected_metrics if metric not in result.metrics]
    if unknown:
        raise KeyError(f"Unknown bootstrap RQA metrics: {unknown}")

    table = result.summary_table.set_index("metric").loc[list(selected_metrics)]
    x = np.arange(len(selected_metrics), dtype=float)
    mean = table["mean"].to_numpy(dtype=float)
    lower = table["lower"].to_numpy(dtype=float)
    upper = table["upper"].to_numpy(dtype=float)
    yerr = np.vstack([mean - lower, upper - mean])

    if ax is None:
        _, ax = plt.subplots()
    ax.errorbar(
        x,
        mean,
        yerr=yerr,
        fmt="o",
        capsize=4,
    )
    ax.set_xticks(x, selected_metrics, rotation=30, ha="right")
    ax.set_ylabel("RQA metric")
    ax.set_title(f"RQA population mean ({result.unit}-level bootstrap)")
    return ax


def plot_windowed_rqa(
    result: WindowedRQAResult,
    *,
    metrics: Sequence[str] = ("recurrence_rate", "determinism", "laminarity"),
    ax=None,
):
    """Plot selected time-varying RQA metrics."""

    if not metrics:
        raise ValueError("metrics must contain at least one column")
    missing = [metric for metric in metrics if metric not in result.table.columns]
    if missing:
        raise KeyError(f"Unknown windowed RQA metric columns: {missing}")
    if ax is None:
        _, ax = plt.subplots()
    for metric in metrics:
        ax.plot(result.table["center_time"], result.table[metric], marker="o", label=metric)
    ax.set_xlabel(f"Window center ({result.time_unit})")
    ax.set_ylabel("RQA metric")
    ax.legend()
    ax.set_title("Windowed recurrence dynamics")
    return ax



def plot_windowed_rqa_trajectories(
    result: WindowedRQAFunctionalResult,
    *,
    metric: str,
    show_mean: bool = False,
    max_curves: int | None = None,
    ax=None,
):
    """Plot one functional windowed-RQA metric across source curves."""

    if metric not in result.metrics:
        raise KeyError(f"Unknown functional RQA metric {metric!r}")
    if max_curves is not None:
        if not isinstance(max_curves, int) or max_curves < 1:
            raise ValueError("max_curves must be a positive integer or None")
        n_plot = min(result.n_curves, max_curves)
    else:
        n_plot = result.n_curves
    if ax is None:
        _, ax = plt.subplots()
    values = result.trajectories.dimension(metric)
    time = result.trajectories.time
    for curve_index in range(n_plot):
        ax.plot(time, values[curve_index], alpha=0.45)
    if show_mean:
        ax.plot(
            time,
            np.nanmean(values, axis=0),
            linewidth=2.2,
            label="Across-curve mean",
        )
        ax.legend()
    unit = result.trajectories.provenance.get("metric_units", {}).get(
        metric,
        "metric units",
    )
    ax.set_xlabel(f"Window center ({result.time_unit})")
    ax.set_ylabel(f"{metric} ({unit})")
    ax.set_title(f"Functional windowed RQA: {metric}")
    return ax


def plot_windowed_rqa_sensitivity(
    result: WindowedRQASensitivityResult,
    *,
    curve: int | str,
    metric: str,
    ax=None,
):
    """Overlay one curve/metric across declared window/step specifications."""

    if metric not in result.metrics:
        raise KeyError(f"Unknown functional RQA metric {metric!r}")
    curve_ids = result.analyses[0].trajectories.curve_ids
    if isinstance(curve, str):
        try:
            curve_index = curve_ids.index(curve)
        except ValueError as exc:
            raise KeyError(f"Unknown curve_id {curve!r}") from exc
    elif isinstance(curve, (int, np.integer)):
        curve_index = int(curve)
        if curve_index < 0 or curve_index >= len(curve_ids):
            raise IndexError("curve index is out of range")
    else:
        raise TypeError("curve must be an integer index or curve_id string")

    if ax is None:
        _, ax = plt.subplots()

    specification_ids = tuple(result.provenance["specification_ids"])
    for specification_id, analysis in zip(
        specification_ids, result.analyses, strict=True
    ):
        values = analysis.trajectories.dimension(metric)[curve_index]
        label = (
            f"{specification_id}: W={analysis.window_samples}, "
            f"S={analysis.step_samples}"
        )
        ax.plot(analysis.trajectories.time, values, marker="o", label=label)

    ax.set_xlabel(f"Window center ({result.analyses[0].time_unit})")
    ax.set_ylabel(metric)
    ax.set_title(f"Window/step sensitivity: {curve_ids[curve_index]} / {metric}")
    ax.legend()
    return ax



def _filtered_sensitivity_slice(
    table,
    *,
    parameter: str,
    response: str,
    filters: Mapping[str, object] | None,
):
    if parameter not in table.columns:
        raise KeyError(f"Unknown sensitivity parameter column {parameter!r}")
    if response not in table.columns:
        raise KeyError(f"Unknown sensitivity response column {response!r}")
    selected = table.copy()
    if filters:
        for key, value in filters.items():
            if key not in selected.columns:
                raise KeyError(f"Unknown sensitivity filter column {key!r}")
            selected = selected.loc[selected[key] == value]
    if selected.empty:
        raise ValueError("filters leave no sensitivity specifications")
    if bool(selected.duplicated(subset=[parameter], keep=False).any()):
        raise ValueError(
            "the requested slice contains multiple rows per parameter value; "
            "add filters for the remaining varying parameters. No averaging or "
            "other hidden aggregation is performed."
        )
    return selected.sort_values(parameter)


def plot_rqa_sensitivity(
    result: RQAParameterSensitivityResult,
    *,
    parameter: str,
    metric: str,
    filters: Mapping[str, object] | None = None,
    ax=None,
):
    """Plot one explicit one-parameter slice of an RQA sensitivity grid."""

    if metric not in result.metric_columns:
        raise KeyError(f"Unknown RQA sensitivity metric {metric!r}")
    selected = _filtered_sensitivity_slice(
        result.table,
        parameter=parameter,
        response=metric,
        filters=filters,
    )
    if ax is None:
        _, ax = plt.subplots()
    ax.plot(selected[parameter], selected[metric], marker="o")
    ax.set_xlabel(parameter)
    ax.set_ylabel(metric)
    ax.set_title(f"RQA parameter sensitivity: {result.curve_id}")
    return ax


def plot_kantz_sensitivity(
    result: KantzParameterSensitivityResult,
    *,
    parameter: str,
    response: str = "exponent",
    filters: Mapping[str, object] | None = None,
    ax=None,
):
    """Plot one explicit one-parameter slice of a Kantz sensitivity grid."""

    allowed = {
        "exponent",
        "r_squared",
        "standard_error",
        "n_fit_points",
        "minimum_reference_count_in_fit",
        "minimum_pair_count_in_fit",
        "initial_supported_reference_fraction",
        "total_zero_mean_neighborhood_count_in_fit",
    }
    if response not in allowed:
        raise KeyError(f"Unknown Kantz sensitivity response {response!r}")
    selected = _filtered_sensitivity_slice(
        result.table,
        parameter=parameter,
        response=response,
        filters=filters,
    )
    if ax is None:
        _, ax = plt.subplots()
    ax.plot(selected[parameter], selected[response], marker="o")
    if response == "exponent":
        ax.axhline(0.0, linestyle=":")
    ax.set_xlabel(parameter)
    ax.set_ylabel(
        f"{response} ({result.exponent_unit})"
        if response == "exponent"
        else response
    )
    ax.set_title(f"Kantz sensitivity: {result.curve_id}")
    return ax


def plot_lyapunov_sensitivity(
    result: LyapunovParameterSensitivityResult,
    *,
    parameter: str,
    response: str = "exponent",
    filters: Mapping[str, object] | None = None,
    ax=None,
):
    """Plot one explicit one-parameter slice of an LLE sensitivity grid."""

    allowed = {
        "exponent",
        "r_squared",
        "standard_error",
        "n_fit_points",
        "minimum_pair_count_in_fit",
        "total_zero_distance_count_in_fit",
    }
    if response not in allowed:
        raise KeyError(f"Unknown LLE sensitivity response {response!r}")
    selected = _filtered_sensitivity_slice(
        result.table,
        parameter=parameter,
        response=response,
        filters=filters,
    )
    if ax is None:
        _, ax = plt.subplots()
    ax.plot(selected[parameter], selected[response], marker="o")
    if response == "exponent":
        ax.axhline(0.0, linestyle=":")
    ax.set_xlabel(parameter)
    ax.set_ylabel(
        f"{response} ({result.exponent_unit})"
        if response == "exponent"
        else response
    )
    ax.set_title(f"Rosenstein sensitivity: {result.curve_id}")
    return ax


def plot_local_divergence(
    result: LocalDivergenceResult | KantzDivergenceResult | LargestLyapunovResult,
    *,
    ax=None,
):
    """Plot the mean log-divergence curve and an explicit LLE fit when present."""

    fit = result if isinstance(result, LargestLyapunovResult) else None
    divergence = fit.divergence if fit is not None else result
    if ax is None:
        _, ax = plt.subplots()
    ax.plot(
        divergence.time_lags,
        divergence.mean_log_divergence,
        marker="o",
        label="Mean log divergence",
    )
    if fit is not None:
        mask = (
            (divergence.time_lags >= fit.fit_start)
            & (divergence.time_lags <= fit.fit_end)
            & np.isfinite(divergence.mean_log_divergence)
        )
        normalized = divergence.time_unit.lower()
        if normalized in {"s", "sec", "second", "seconds"}:
            x_fit = divergence.time_lags[mask]
        elif normalized in {"ms", "millisecond", "milliseconds"}:
            x_fit = divergence.time_lags[mask] * 1e-3
        else:
            x_fit = divergence.time_lags[mask]
        y_fit = fit.intercept + fit.exponent * x_fit
        ax.plot(
            divergence.time_lags[mask],
            y_fit,
            linestyle="--",
            label=f"LLE fit: {fit.exponent:.3g} {fit.exponent_unit}",
        )
    ax.set_xlabel(f"Divergence lag ({divergence.time_unit})")
    ax.set_ylabel("Mean log distance")
    ax.legend()
    family = divergence.provenance.get("estimator_family", "local divergence")
    ax.set_title(f"{family}: {divergence.curve_id}")
    return ax


def plot_multivariate_iaaft_diagnostics(
    result: MultivariateIAAFTResult,
    *,
    ax=None,
):
    """Plot per-surrogate power- and cross-spectrum preservation errors."""

    if not isinstance(result, MultivariateIAAFTResult):
        raise TypeError("result must be a MultivariateIAAFTResult")
    if ax is None:
        _, ax = plt.subplots()

    surrogate_index = np.arange(result.n_surrogates, dtype=int)
    ax.plot(
        surrogate_index,
        np.max(result.spectral_errors, axis=1),
        marker="o",
        label="Max power-spectrum error",
    )
    ax.plot(
        surrogate_index,
        np.max(result.cross_spectral_errors, axis=1),
        marker="o",
        label="Max cross-spectrum error",
    )
    ax.set_xlabel("Surrogate index")
    ax.set_ylabel("Relative mismatch")
    ax.set_title(
        "Multivariate IAAFT preservation diagnostics: "
        f"{result.reference_dimension} reference"
    )
    ax.legend()
    return ax


def plot_multivariate_surrogate_nonlinearity(
    result: MultivariateSurrogateNonlinearityResult,
    *,
    bins: int = 20,
    ax=None,
):
    """Plot a multivariate-surrogate statistic distribution."""

    if not isinstance(result, MultivariateSurrogateNonlinearityResult):
        raise TypeError(
            "result must be a MultivariateSurrogateNonlinearityResult"
        )
    if not isinstance(bins, int) or bins < 2:
        raise ValueError("bins must be an integer >= 2")
    if ax is None:
        _, ax = plt.subplots()
    ax.hist(result.surrogate_statistics, bins=bins, alpha=0.7)
    ax.axvline(
        result.observed_statistic,
        linestyle="--",
        label="Observed",
    )
    ax.set_xlabel(result.statistic)
    ax.set_ylabel("Surrogate count")
    ax.set_title(
        "Multivariate IAAFT surrogate test "
        f"(p={result.p_value:.3g})"
    )
    ax.legend()
    return ax


def plot_surrogate_nonlinearity(
    result: SurrogateNonlinearityResult,
    *,
    bins: int = 20,
    ax=None,
):
    """Plot the surrogate statistic distribution and observed statistic."""

    if not isinstance(bins, int) or bins < 2:
        raise ValueError("bins must be an integer >= 2")
    if ax is None:
        _, ax = plt.subplots()
    ax.hist(result.surrogate_statistics, bins=bins, alpha=0.7)
    ax.axvline(result.observed_statistic, linestyle="--", label="Observed")
    ax.set_xlabel(result.statistic)
    ax.set_ylabel("Surrogate count")
    ax.set_title(f"{result.method.upper()} surrogate test (p={result.p_value:.3g})")
    ax.legend()
    return ax


def plot_poincare_return_map(
    crossings: PoincareCrossingResult,
    *,
    fit: LocalReturnMapResult | None = None,
    ax=None,
):
    """Plot a one-dimensional empirical return map x_n -> x_(n+1)."""

    if crossings.states.shape[1] != 1:
        raise ValueError(
            "plot_poincare_return_map currently requires one returned state dimension; "
            "select one state dimension explicitly rather than projecting silently"
        )
    if crossings.n_crossings < 2:
        raise ValueError("at least two crossings are required for a return-map plot")
    x = crossings.states[:-1, 0]
    y = crossings.states[1:, 0]
    if ax is None:
        _, ax = plt.subplots()
    ax.scatter(x, y, label="Successive crossings")
    low = float(min(np.min(x), np.min(y)))
    high = float(max(np.max(x), np.max(y)))
    ax.plot([low, high], [low, high], linestyle=":", label="Identity")
    if fit is not None:
        grid = np.linspace(low, high, 100)
        centered = grid - fit.reference_state[0]
        predicted = (
            fit.reference_state[0]
            + fit.intercept[0]
            + fit.jacobian[0, 0] * centered
        )
        ax.plot(grid, predicted, linestyle="--", label="Local affine fit")
    ax.set_xlabel(f"{crossings.state_dimensions[0]} at crossing n")
    ax.set_ylabel(f"{crossings.state_dimensions[0]} at crossing n+1")
    ax.legend()
    ax.set_title("Empirical Poincare return map")
    return ax
