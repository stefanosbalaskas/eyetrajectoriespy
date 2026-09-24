"""Visualization helpers for continuous functional gaze analyses."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from .fpca import component_trajectories
from .registration import warping_displacement
from .prediction import summarise_fpca_regression_cv
from .selection import summarise_fpca_cross_validation
from .types import (
    FPCAComponentBandResult,
    FPCAComponentEnvelopeResult,
    FPCACrossValidationResult,
    FPCAInfluenceResult,
    FPCANestedRegressionCVResult,
    FPCARegressionCVResult,
    FPCARegressionPredictionIntervalResult,
    FPCARegressionSlopeBandResult,
    FPCARegressionUncertaintyResult,
    FPCAWildBootstrapProjectionResult,
    FPCAWildBootstrapFamilyTestResult,
    FPCAWildBootstrapMonteCarloDiagnosticResult,
    FPCAWildBootstrapSimultaneousResult,
    FPCAWildBootstrapTruncationScanResult,
    FPCAWildBootstrapTruncationSelectionResult,
    FPCAResult,
    FPCAScoreUncertaintyResult,
    FPCASpectrumUncertaintyResult,
    FPCAStabilityResult,
    FPCASubspaceStabilityResult,
    FunctionalMeanBandResult,
    FunctionalMixedEffectsBandResult,
    FunctionalMixedEffectsResult,
    FunctionOnScalarBandResult,
    FunctionOnScalarResult,
    IrregularTrajectorySet,
    ConformalFunctionalAnomalyResult,
    DynamicTimeWarpingResult,
    FunctionalOutlierResult,
    RegistrationResult,
    TrajectoryDistanceSensitivityResult,
    TrajectorySet,
)


def plot_trajectory_distance_rank_correlations(
    result: TrajectoryDistanceSensitivityResult,
    *,
    ax=None,
):
    """Plot descriptive Spearman agreement among distance specifications."""

    if not isinstance(result, TrajectoryDistanceSensitivityResult):
        raise TypeError(
            "result must be a TrajectoryDistanceSensitivityResult"
        )
    n = result.n_specifications
    matrix = np.eye(n, dtype=float)
    lookup = {
        name: index
        for index, name in enumerate(result.specification_names)
    }
    for row in result.comparison_table.itertuples(index=False):
        left = lookup[row.specification_a]
        right = lookup[row.specification_b]
        value = float(row.spearman_rank_correlation)
        matrix[left, right] = value
        matrix[right, left] = value

    if ax is None:
        _, ax = plt.subplots()
    image = ax.imshow(matrix, vmin=-1.0, vmax=1.0)
    ax.set_xticks(np.arange(n), labels=result.specification_names, rotation=45, ha="right")
    ax.set_yticks(np.arange(n), labels=result.specification_names)
    ax.set_title("Trajectory-distance rank agreement")
    for row in range(n):
        for column in range(n):
            value = matrix[row, column]
            text_value = "nan" if not np.isfinite(value) else f"{value:.2f}"
            ax.text(column, row, text_value, ha="center", va="center")
    ax.figure.colorbar(image, ax=ax, label="Spearman rank correlation")
    return ax


def plot_trajectory_overlay(
    trajectories: TrajectorySet,
    *,
    dimension: str,
    max_curves: int | None = 50,
    alpha: float = 0.25,
    ax=None,
):
    """Overlay one functional dimension against trial time."""
    if dimension not in trajectories.dimension_names:
        raise KeyError(f"Unknown dimension {dimension!r}")
    if ax is None:
        _, ax = plt.subplots()
    index = trajectories.dimension_names.index(dimension)
    n = trajectories.n_curves if max_curves is None else min(max_curves, trajectories.n_curves)
    for i in range(n):
        ax.plot(trajectories.time, trajectories.values[i, :, index], alpha=alpha)
    ax.set_xlabel(f"Time ({trajectories.time_unit})")
    ax.set_ylabel(dimension)
    ax.set_title(f"{dimension}(t): {n} trajectories")
    return ax


def plot_planar_trajectories(
    trajectories: TrajectorySet,
    *,
    max_curves: int | None = 40,
    alpha: float = 0.35,
    invert_y: bool = True,
    ax=None,
):
    """Plot continuous x/y gaze paths in screen space."""
    if trajectories.n_dimensions < 2:
        raise ValueError("Planar plotting requires at least two functional dimensions")
    if ax is None:
        _, ax = plt.subplots()
    n = trajectories.n_curves if max_curves is None else min(max_curves, trajectories.n_curves)
    for i in range(n):
        ax.plot(trajectories.values[i, :, 0], trajectories.values[i, :, 1], alpha=alpha)
    ax.set_xlabel(trajectories.dimension_names[0])
    ax.set_ylabel(trajectories.dimension_names[1])
    ax.set_title(f"Planar gaze trajectories (n={n})")
    ax.set_aspect("equal", adjustable="box")
    if invert_y:
        ax.invert_yaxis()
    return ax


def plot_dynamic_time_warping_alignment(
    result: DynamicTimeWarpingResult,
    *,
    ax=None,
):
    """Plot one audited DTW alignment path in sample-index space."""

    if not isinstance(result, DynamicTimeWarpingResult):
        raise TypeError("result must be a DynamicTimeWarpingResult")
    if ax is None:
        _, ax = plt.subplots()

    path = np.asarray(result.path, dtype=int)
    if path.ndim != 2 or path.shape[1] != 2 or path.shape[0] < 1:
        raise ValueError("result.path must have shape (n_steps, 2)")

    ax.plot(path[:, 1], path[:, 0], marker="o")
    limit = max(result.n_points_a - 1, result.n_points_b - 1)
    ax.plot([0, limit], [0, limit], linestyle="--", label="same index")
    ax.set_xlim(-0.5, max(result.n_points_b - 0.5, 0.5))
    ax.set_ylim(-0.5, max(result.n_points_a - 0.5, 0.5))
    ax.set_xlabel("Sequence B sample index")
    ax.set_ylabel("Sequence A sample index")
    distance_label = (
        f"normalized={result.distance:.4g}"
        if result.provenance.get("normalization_requested", False)
        else f"raw={result.distance:.4g}"
    )
    window_label = (
        "unconstrained"
        if result.window_radius is None
        else f"window={result.window_radius}"
    )
    ax.set_title(
        f"DTW alignment: {result.step_pattern}, {window_label}, {distance_label}"
    )
    ax.legend()
    return ax


def plot_functional_mixed_effects_coefficient(
    result: FunctionalMixedEffectsResult | FunctionalMixedEffectsBandResult,
    *,
    coefficient: str | int,
    ax=None,
):
    """Plot one mixed-effects coefficient with pointwise or simultaneous uncertainty."""

    if isinstance(result, FunctionalMixedEffectsBandResult):
        fit = result.reference
        band = result
    elif isinstance(result, FunctionalMixedEffectsResult):
        fit = result
        band = None
    else:
        raise TypeError(
            "result must be a FunctionalMixedEffectsResult or "
            "FunctionalMixedEffectsBandResult"
        )

    if isinstance(coefficient, str):
        if coefficient not in fit.coefficient_names:
            raise KeyError(f"Unknown coefficient {coefficient!r}")
        coefficient_index = fit.coefficient_names.index(coefficient)
    elif isinstance(coefficient, bool) or not isinstance(
        coefficient,
        (int, np.integer),
    ):
        raise TypeError("coefficient must be a name or integer index")
    else:
        coefficient_index = int(coefficient)
        if coefficient_index < 0 or coefficient_index >= fit.n_coefficients:
            raise IndexError("coefficient index is out of range")

    if ax is None:
        _, ax = plt.subplots()

    estimate = fit.coefficient_functions[coefficient_index]
    if band is None:
        standard_error = fit.coefficient_standard_errors[coefficient_index]
        z_value = 1.959963984540054
        lower = estimate - z_value * standard_error
        upper = estimate + z_value * standard_error
        label = "95% pointwise Wald interval"
    else:
        lower = band.lower[coefficient_index]
        upper = band.upper[coefficient_index]
        label = (
            f"{100 * band.confidence_level:.1f}% simultaneous band "
            f"({band.simultaneous_scope})"
        )

    ax.fill_between(
        fit.time,
        lower,
        upper,
        alpha=0.2,
        label=label,
    )
    ax.plot(
        fit.time,
        estimate,
        label=fit.coefficient_names[coefficient_index],
    )
    ax.axhline(0.0, linestyle="--")
    ax.set_xlabel(f"Time ({fit.time_unit})")
    ax.set_ylabel(f"Coefficient: {fit.dimension_name}")
    ax.set_title(
        "Functional mixed-effects coefficient: "
        f"{fit.coefficient_names[coefficient_index]}"
    )
    ax.legend()
    return ax


def plot_functional_random_effects(
    result: FunctionalMixedEffectsResult,
    *,
    effect: str = "intercept",
    max_participants: int | None = None,
    alpha: float = 0.35,
    ax=None,
):
    """Plot participant BLUP random-intercept or random-slope functions."""

    if not isinstance(result, FunctionalMixedEffectsResult):
        raise TypeError("result must be a FunctionalMixedEffectsResult")
    if effect not in {"intercept", "slope"}:
        raise ValueError("effect must be 'intercept' or 'slope'")
    if max_participants is not None:
        if isinstance(max_participants, bool) or not isinstance(
            max_participants,
            (int, np.integer),
        ):
            raise TypeError("max_participants must be an integer or None")
        if max_participants < 1:
            raise ValueError("max_participants must be positive")
    if not 0 < alpha <= 1:
        raise ValueError("alpha must lie in (0, 1]")

    if effect == "intercept":
        functions = result.random_intercept_functions
        title = "Participant functional random intercepts"
    else:
        if result.random_slope_functions is None:
            raise ValueError(
                "result does not contain a participant random functional slope"
            )
        functions = result.random_slope_functions
        title = (
            "Participant functional random slopes: "
            f"{result.random_slope_predictor}"
        )

    n_participants = result.n_participants
    n_plot = (
        n_participants
        if max_participants is None
        else min(n_participants, int(max_participants))
    )
    if ax is None:
        _, ax = plt.subplots()

    for participant_index in range(n_plot):
        ax.plot(
            result.time,
            functions[participant_index],
            alpha=alpha,
            label=(
                result.participant_ids[participant_index]
                if n_plot <= 12
                else None
            ),
        )
    ax.axhline(0.0, linestyle="--")
    ax.set_xlabel(f"Time ({result.time_unit})")
    ax.set_ylabel(f"Random {effect}: {result.dimension_name}")
    ax.set_title(title)
    if n_plot <= 12:
        ax.legend()
    return ax


def plot_function_on_scalar_coefficients(
    result: FunctionOnScalarResult | FunctionOnScalarBandResult,
    *,
    coefficient: str | int,
    dimension: str | None = None,
    ax=None,
):
    """Plot one function-on-scalar coefficient with an optional simultaneous band."""

    if isinstance(result, FunctionOnScalarBandResult):
        fit = result.reference
        band = result
    elif isinstance(result, FunctionOnScalarResult):
        fit = result
        band = None
    else:
        raise TypeError(
            "result must be a FunctionOnScalarResult or FunctionOnScalarBandResult"
        )

    if isinstance(coefficient, str):
        if coefficient not in fit.coefficient_names:
            raise KeyError(f"Unknown coefficient {coefficient!r}")
        coefficient_index = fit.coefficient_names.index(coefficient)
    elif isinstance(coefficient, bool) or not isinstance(
        coefficient, (int, np.integer)
    ):
        raise TypeError("coefficient must be a name or integer index")
    else:
        coefficient_index = int(coefficient)
        if coefficient_index < 0 or coefficient_index >= fit.n_coefficients:
            raise IndexError("coefficient index is out of range")

    if dimension is None:
        dimension = fit.dimension_names[0]
    if dimension not in fit.dimension_names:
        raise KeyError(f"Unknown dimension {dimension!r}")
    dimension_index = fit.dimension_names.index(dimension)

    if ax is None:
        _, ax = plt.subplots()

    if band is not None:
        ax.fill_between(
            fit.time,
            band.lower[coefficient_index, :, dimension_index],
            band.upper[coefficient_index, :, dimension_index],
            alpha=0.2,
            label=(
                f"{100 * band.confidence_level:.1f}% simultaneous band "
                f"({band.simultaneous_scope})"
            ),
        )

    ax.plot(
        fit.time,
        fit.coefficients[coefficient_index, :, dimension_index],
        label=fit.coefficient_names[coefficient_index],
    )
    ax.axhline(0.0, linestyle="--")
    ax.set_xlabel(f"Time ({fit.time_unit})")
    ax.set_ylabel(f"Coefficient: {dimension}")
    ax.set_title(
        f"Function-on-scalar coefficient: "
        f"{fit.coefficient_names[coefficient_index]}"
    )
    ax.legend()
    return ax


def plot_fpca_variance(result: FPCAResult, *, cumulative: bool = True, ax=None):
    """Plot per-component or cumulative variance explained."""
    if ax is None:
        _, ax = plt.subplots()
    x = np.arange(1, result.n_components + 1)
    y = result.cumulative_explained_variance() if cumulative else result.explained_variance_ratio
    ax.plot(x, 100 * y, marker="o")
    ax.set_xlabel("Functional principal component")
    ax.set_ylabel("Cumulative variance explained (%)" if cumulative else "Variance explained (%)")
    ax.set_xticks(x)
    return ax


def plot_fpca_wild_bootstrap_truncation_scan(
    result,
    *,
    target=0,
    metric="width",
    ax=None,
):
    """Plot interval width or center across candidate wild-bootstrap truncations."""

    if isinstance(result, FPCAWildBootstrapTruncationSelectionResult):
        scan = result.scan
        selection = result
    elif isinstance(result, FPCAWildBootstrapTruncationScanResult):
        scan = result
        selection = None
    else:
        raise TypeError(
            "result must be a wild-bootstrap truncation scan or selection result"
        )

    if isinstance(target, str):
        if target not in scan.target_curve_ids:
            raise ValueError(f"unknown target curve_id {target!r}")
        target_index = scan.target_curve_ids.index(target)
    elif isinstance(target, bool) or not isinstance(target, (int, np.integer)):
        raise TypeError("target must be an integer index or curve_id string")
    else:
        target_index = int(target)
        if target_index < 0 or target_index >= scan.n_targets:
            raise IndexError("target index is outside the scan")

    if metric not in {"width", "center"}:
        raise ValueError("metric must be 'width' or 'center'")
    if ax is None:
        _, ax = plt.subplots()

    values = (
        scan.widths[:, target_index]
        if metric == "width"
        else scan.centers[:, target_index]
    )
    x = np.asarray(scan.candidate_components, dtype=int)
    ax.plot(x, values, marker="o")
    if selection is not None:
        selected = selection.selected_components[target_index]
        if np.isfinite(selected):
            ax.axvline(
                int(selected),
                linestyle="--",
                label=f"selected h={int(selected)}",
            )
            ax.legend()
    ax.set_xlabel("Inference truncation h")
    ax.set_ylabel("Interval width" if metric == "width" else "Interval center")
    ax.set_title(
        f"Wild-bootstrap truncation scan: {scan.target_curve_ids[target_index]}"
    )
    return ax


def plot_fpca_wild_bootstrap_projection(
    result: FPCAWildBootstrapProjectionResult,
    *,
    max_targets: int = 30,
    ax=None,
):
    """Plot target-wise studentized wild-bootstrap FPCR projection intervals."""

    if isinstance(max_targets, bool) or not isinstance(max_targets, (int, np.integer)):
        raise TypeError("max_targets must be an integer")
    if max_targets < 1:
        raise ValueError("max_targets must be positive")
    if ax is None:
        _, ax = plt.subplots()

    n = min(max_targets, result.n_targets)
    x = np.arange(n)
    center = result.reference_projection[:n]
    lower = result.lower[:n]
    upper = result.upper[:n]
    yerr = np.vstack((center - lower, upper - center))
    ax.errorbar(
        x,
        center,
        yerr=yerr,
        marker="o",
        linestyle="none",
        capsize=3,
        label="studentized wild-bootstrap interval",
    )
    ax.axhline(0.0, linestyle="--")
    ax.set_xticks(x)
    ax.set_xticklabels(result.target_curve_ids[:n], rotation=90)
    ax.set_xlabel("Fixed target trajectory")
    ax.set_ylabel("Centered FPCR projection")
    ax.set_title("Heteroscedastic Gaussian FPCR projection inference")
    ax.legend()
    return ax




def plot_fpca_wild_bootstrap_family_test(
    result: FPCAWildBootstrapFamilyTestResult,
    *,
    max_targets: int = 30,
    show_targetwise: bool = True,
    ax=None,
):
    """Plot target-wise and single-step adjusted bootstrap p-values."""

    if not isinstance(result, FPCAWildBootstrapFamilyTestResult):
        raise TypeError("result must be an FPCAWildBootstrapFamilyTestResult")
    if isinstance(max_targets, bool) or not isinstance(max_targets, (int, np.integer)):
        raise TypeError("max_targets must be an integer")
    if max_targets < 1:
        raise ValueError("max_targets must be positive")
    if not isinstance(show_targetwise, bool):
        raise TypeError("show_targetwise must be boolean")
    if ax is None:
        _, ax = plt.subplots()

    n = min(max_targets, result.n_targets)
    x = np.arange(n)
    ax.scatter(x, result.adjusted_p_values[:n], marker="o", label="single-step maxT adjusted")
    if show_targetwise:
        ax.scatter(x, result.targetwise_p_values[:n], marker="x", label="target-wise")
    ax.axhline(
        result.significance_level,
        linestyle="--",
        label=f"alpha={result.significance_level:g}",
    )
    ax.set_xticks(x)
    ax.set_xticklabels(result.projection_result.target_curve_ids[:n], rotation=90)
    ax.set_ylim(-0.02, 1.02)
    ax.set_xlabel("Fixed target trajectory")
    ax.set_ylabel("Bootstrap tail probability")
    ax.set_title("Fixed-family heteroscedastic Gaussian FPCR tests")
    ax.legend()
    return ax



def plot_fpca_wild_bootstrap_monte_carlo_diagnostics(
    result: FPCAWildBootstrapMonteCarloDiagnosticResult,
    *,
    max_targets: int = 30,
    show_targetwise: bool = False,
    ax=None,
):
    """Plot finite-bootstrap tail estimates with exact binomial intervals."""

    if not isinstance(result, FPCAWildBootstrapMonteCarloDiagnosticResult):
        raise TypeError("result must be an FPCAWildBootstrapMonteCarloDiagnosticResult")
    if isinstance(max_targets, bool) or not isinstance(max_targets, (int, np.integer)):
        raise TypeError("max_targets must be an integer")
    if max_targets < 1:
        raise ValueError("max_targets must be positive")
    if not isinstance(show_targetwise, bool):
        raise TypeError("show_targetwise must be boolean")
    if ax is None:
        _, ax = plt.subplots()

    n = min(max_targets, result.n_targets)
    x = np.arange(n)
    adjusted = result.adjusted_tail_probabilities[:n]
    adjusted_yerr = np.vstack(
        (
            adjusted - result.adjusted_interval_lower[:n],
            result.adjusted_interval_upper[:n] - adjusted,
        )
    )
    ax.errorbar(
        x,
        adjusted,
        yerr=adjusted_yerr,
        marker="o",
        linestyle="none",
        capsize=3,
        label="maxT tail probability",
    )

    if show_targetwise:
        targetwise = result.targetwise_tail_probabilities[:n]
        targetwise_yerr = np.vstack(
            (
                targetwise - result.targetwise_interval_lower[:n],
                result.targetwise_interval_upper[:n] - targetwise,
            )
        )
        ax.errorbar(
            x,
            targetwise,
            yerr=targetwise_yerr,
            marker="x",
            linestyle="none",
            capsize=3,
            label="target-wise tail probability",
        )

    alpha = result.significance_level
    ax.axhline(alpha, linestyle="--", label=f"alpha={alpha:g}")
    ax.set_xticks(x)
    ax.set_xticklabels(
        result.family_test_result.projection_result.target_curve_ids[:n],
        rotation=90,
    )
    ax.set_ylim(-0.02, 1.02)
    ax.set_xlabel("Fixed target trajectory")
    ax.set_ylabel("Bootstrap exceedance probability")
    ax.set_title("Monte Carlo precision of fixed-family wild-bootstrap tests")
    ax.legend()
    return ax

def plot_fpca_wild_bootstrap_simultaneous_interval(
    result: FPCAWildBootstrapSimultaneousResult,
    *,
    max_targets: int = 30,
    show_targetwise: bool = True,
    ax=None,
):
    """Plot familywise fixed-target FPCR projection intervals."""

    if not isinstance(result, FPCAWildBootstrapSimultaneousResult):
        raise TypeError("result must be an FPCAWildBootstrapSimultaneousResult")
    if isinstance(max_targets, bool) or not isinstance(max_targets, (int, np.integer)):
        raise TypeError("max_targets must be an integer")
    if max_targets < 1:
        raise ValueError("max_targets must be positive")
    if not isinstance(show_targetwise, bool):
        raise TypeError("show_targetwise must be boolean")
    if ax is None:
        _, ax = plt.subplots()

    base = result.projection_result
    n = min(max_targets, result.n_targets)
    x = np.arange(n)
    center = base.reference_projection[:n]
    simultaneous_lower = result.lower[:n]
    simultaneous_upper = result.upper[:n]
    simultaneous_yerr = np.vstack(
        (center - simultaneous_lower, simultaneous_upper - center)
    )
    ax.errorbar(
        x,
        center,
        yerr=simultaneous_yerr,
        marker="o",
        linestyle="none",
        capsize=3,
        label="familywise simultaneous interval",
    )
    if show_targetwise:
        point_lower = (
            center - result.targetwise_critical_values[:n] * base.reference_se[:n]
        )
        point_upper = (
            center + result.targetwise_critical_values[:n] * base.reference_se[:n]
        )
        point_yerr = np.vstack((center - point_lower, point_upper - center))
        ax.errorbar(
            x,
            center,
            yerr=point_yerr,
            marker=".",
            linestyle="none",
            capsize=2,
            label="target-wise interval",
        )
    ax.axhline(0.0, linestyle="--")
    ax.set_xticks(x)
    ax.set_xticklabels(base.target_curve_ids[:n], rotation=90)
    ax.set_xlabel("Fixed target trajectory")
    ax.set_ylabel("Centered FPCR projection")
    ax.set_title("Familywise heteroscedastic Gaussian FPCR projection inference")
    ax.legend()
    return ax


def plot_fpca_regression_future_prediction_interval(
    result: FPCARegressionPredictionIntervalResult,
    *,
    max_targets: int = 30,
    ax=None,
):
    """Plot marginal future-outcome prediction intervals for fixed targets."""

    if isinstance(max_targets, bool) or not isinstance(max_targets, (int, np.integer)):
        raise TypeError("max_targets must be an integer")
    if max_targets < 1:
        raise ValueError("max_targets must be positive")
    if ax is None:
        _, ax = plt.subplots()

    base = result.regression_uncertainty
    n = min(max_targets, result.n_targets)
    x = np.arange(n)
    median = result.median[:n]
    lower = result.lower[:n]
    upper = result.upper[:n]
    yerr = np.vstack((median - lower, upper - median))
    ax.errorbar(
        x,
        median,
        yerr=yerr,
        marker="o",
        linestyle="none",
        capsize=3,
        label="future-outcome predictive interval",
    )
    ax.scatter(
        x,
        base.reference_mean_predictions[:n],
        marker="x",
        label="full-sample conditional mean",
    )
    ax.set_xticks(x)
    ax.set_xticklabels(base.target_curve_ids[:n], rotation=90)
    ax.set_xlabel("Fixed target trajectory")
    ax.set_ylabel("Scalar response")
    ax.set_title("Gaussian FPCR future-outcome prediction")
    ax.legend()
    return ax


def plot_fpca_regression_slope_band(
    result: FPCARegressionSlopeBandResult,
    *,
    dimension: str | None = None,
    ax=None,
):
    """Plot an observed-grid simultaneous Gaussian FPCR slope band."""

    fpca = result.regression_uncertainty.reference_fpca
    if dimension is None:
        dimension = fpca.dimension_names[0]
    if dimension not in fpca.dimension_names:
        raise KeyError(f"Unknown dimension {dimension!r}")
    if ax is None:
        _, ax = plt.subplots()

    dim = fpca.dimension_names.index(dimension)
    time = fpca.time
    reference = result.regression_uncertainty.reference_slope[:, dim]
    ax.fill_between(
        time,
        result.lower[:, dim],
        result.upper[:, dim],
        alpha=0.2,
        label=(
            f"{100 * result.confidence_level:.1f}% observed-grid "
            f"{result.simultaneous_scope} band"
        ),
    )
    ax.plot(time, reference, label="full-sample FPCR slope")
    ax.axhline(0.0, linestyle="--")
    ax.set_xlabel(f"Time ({fpca.time_unit})")
    ax.set_ylabel(f"Slope for {dimension}")
    ax.set_title("Gaussian FPCR simultaneous slope band")
    ax.legend()
    return ax


def plot_fpca_regression_slope_uncertainty(
    result: FPCARegressionUncertaintyResult,
    *,
    dimension: str | None = None,
    ax=None,
):
    """Plot the Gaussian FPCR slope with pointwise bootstrap uncertainty."""

    if dimension is None:
        dimension = result.reference_fpca.dimension_names[0]
    if dimension not in result.reference_fpca.dimension_names:
        raise KeyError(f"Unknown dimension {dimension!r}")
    if ax is None:
        _, ax = plt.subplots()

    dim = result.reference_fpca.dimension_names.index(dimension)
    time = result.reference_fpca.time
    ax.fill_between(
        time,
        result.slope_lower[:, dim],
        result.slope_upper[:, dim],
        alpha=0.2,
        label=f"{100 * result.level:.1f}% pointwise percentile envelope",
    )
    ax.plot(
        time,
        result.reference_slope[:, dim],
        label="full-sample FPCR slope",
    )
    ax.axhline(0.0, linestyle="--")
    ax.set_xlabel(f"Time ({result.reference_fpca.time_unit})")
    ax.set_ylabel(f"Slope for {dimension}")
    ax.set_title("Gaussian FPCR slope uncertainty")
    ax.legend()
    return ax


def plot_fpca_regression_mean_prediction_uncertainty(
    result: FPCARegressionUncertaintyResult,
    *,
    max_targets: int = 30,
    ax=None,
):
    """Plot fixed-target conditional-mean uncertainty from paired FPCR bootstrap."""

    if isinstance(max_targets, bool) or not isinstance(max_targets, (int, np.integer)):
        raise TypeError("max_targets must be an integer")
    if max_targets < 1:
        raise ValueError("max_targets must be positive")
    if ax is None:
        _, ax = plt.subplots()

    n = min(max_targets, result.n_targets)
    x = np.arange(n)
    median = result.prediction_median[:n]
    lower = result.prediction_lower[:n]
    upper = result.prediction_upper[:n]
    yerr = np.vstack((median - lower, upper - median))
    ax.errorbar(
        x,
        median,
        yerr=yerr,
        marker="o",
        linestyle="none",
        capsize=3,
        label="bootstrap median + conditional-mean envelope",
    )
    ax.scatter(
        x,
        result.reference_mean_predictions[:n],
        marker="x",
        label="full-sample conditional mean",
    )
    ax.set_xticks(x)
    ax.set_xticklabels(result.target_curve_ids[:n], rotation=90)
    ax.set_xlabel("Fixed target trajectory")
    ax.set_ylabel("Conditional mean response")
    ax.set_title("FPCR conditional-mean uncertainty")
    ax.legend()
    return ax


def plot_fpca_score_uncertainty(
    result: FPCAScoreUncertaintyResult,
    *,
    component: int = 0,
    max_targets: int = 30,
    ax=None,
):
    """Plot fixed-target score uncertainty from bootstrap basis re-estimation."""

    if component < 0 or component >= result.n_components:
        raise IndexError("component is outside the score-uncertainty range")
    if isinstance(max_targets, bool) or not isinstance(max_targets, (int, np.integer)):
        raise TypeError("max_targets must be an integer")
    if max_targets < 1:
        raise ValueError("max_targets must be positive")
    if ax is None:
        _, ax = plt.subplots()

    n = min(max_targets, result.n_targets)
    x = np.arange(n)
    median = result.median[:n, component]
    lower = result.lower[:n, component]
    upper = result.upper[:n, component]
    yerr = np.vstack((median - lower, upper - median))
    ax.errorbar(
        x,
        median,
        yerr=yerr,
        marker="o",
        linestyle="none",
        capsize=3,
        label="bootstrap median + percentile envelope",
    )
    ax.scatter(
        x,
        result.reference_scores[:n, component],
        marker="x",
        label="full-sample reference score",
    )
    ax.axhline(0.0, linestyle="--")
    ax.set_xticks(x)
    ax.set_xticklabels(result.target_curve_ids[:n], rotation=90)
    ax.set_xlabel("Target trajectory")
    ax.set_ylabel(f"FPC{component + 1} score")
    ax.set_title("Basis-resampling FPC score uncertainty")
    ax.legend()
    return ax


def plot_fpca_spectrum_uncertainty(
    result: FPCASpectrumUncertaintyResult,
    *,
    metric: str = "explained_variance_ratio",
    ax=None,
):
    """Plot FPCA spectrum estimates with bootstrap-calibrated uncertainty bars."""

    allowed = {
        "eigenvalue",
        "explained_variance_ratio",
        "cumulative_variance_ratio",
    }
    if metric not in allowed:
        raise ValueError(
            "metric must be 'eigenvalue', 'explained_variance_ratio', "
            "or 'cumulative_variance_ratio'"
        )
    if ax is None:
        _, ax = plt.subplots()

    n = result.n_components
    x = np.arange(1, n + 1)
    if metric == "eigenvalue":
        estimate = result.reference.explained_variance[:n]
        lower = result.eigenvalue_lower
        upper = result.eigenvalue_upper
        ylabel = "Eigenvalue"
    elif metric == "explained_variance_ratio":
        estimate = result.reference.explained_variance_ratio[:n]
        lower = result.explained_variance_ratio_lower
        upper = result.explained_variance_ratio_upper
        ylabel = "Explained variance ratio"
    else:
        estimate = np.cumsum(result.reference.explained_variance_ratio[:n])
        lower = result.cumulative_variance_ratio_lower
        upper = result.cumulative_variance_ratio_upper
        ylabel = "Cumulative explained variance ratio"

    yerr = np.vstack((estimate - lower, upper - estimate))
    ax.errorbar(x, estimate, yerr=yerr, marker="o", capsize=3)
    ax.set_xticks(x)
    ax.set_xlabel("Functional principal component")
    ax.set_ylabel(ylabel)
    scope = "familywise" if result.simultaneous_scope == "family" else "component-wise"
    ax.set_title(f"FPCA spectrum uncertainty ({scope})")
    return ax


def plot_fpca_component(
    result: FPCAResult,
    *,
    component: int = 0,
    dimension: str | None = None,
    sd_multiplier: float = 2.0,
    ax=None,
):
    """Plot mean ± one FPC mode for a selected functional dimension."""
    if component < 0 or component >= result.n_components:
        raise IndexError("component is outside the fitted range")
    if dimension is None:
        dimension = result.dimension_names[0]
    if dimension not in result.dimension_names:
        raise KeyError(f"Unknown dimension {dimension!r}")
    if sd_multiplier <= 0:
        raise ValueError("sd_multiplier must be positive")
    if ax is None:
        _, ax = plt.subplots()
    dim = result.dimension_names.index(dimension)
    curves = component_trajectories(result, component, sd_multipliers=(-sd_multiplier, 0.0, sd_multiplier))
    ax.plot(result.time, curves[1, :, dim], label="mean")
    ax.plot(result.time, curves[0, :, dim], label=f"-{sd_multiplier:g} SD")
    ax.plot(result.time, curves[2, :, dim], label=f"+{sd_multiplier:g} SD")
    ax.set_xlabel(f"Time ({result.time_unit})")
    ax.set_ylabel(dimension)
    ax.set_title(f"FPC{component + 1}: {dimension}(t)")
    ax.legend()
    return ax


def plot_registration(
    result: RegistrationResult,
    *,
    dimension: str | None = None,
    max_curves: int = 20,
):
    """Plot original and registered functions on separate axes."""
    if dimension is None:
        dimension = result.original.dimension_names[0]
    if dimension not in result.original.dimension_names:
        raise KeyError(f"Unknown dimension {dimension!r}")
    dim = result.original.dimension_names.index(dimension)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    n = min(max_curves, result.original.n_curves)
    for i in range(n):
        axes[0].plot(result.original.time, result.original.values[i, :, dim], alpha=0.25)
        axes[1].plot(result.registered.time, result.registered.values[i, :, dim], alpha=0.25)
    axes[0].set_title("Original")
    axes[1].set_title("Registered")
    for ax in axes:
        ax.set_xlabel(f"Time ({result.original.time_unit})")
        ax.set_ylabel(dimension)
    return fig, axes


def plot_warping_functions(result: RegistrationResult, *, displacement: bool = False, ax=None):
    """Plot estimated time warpings or displacement from identity."""
    if ax is None:
        _, ax = plt.subplots()
    y = warping_displacement(result) if displacement else result.warping_functions
    for i in range(y.shape[0]):
        ax.plot(result.original.time, y[i], alpha=0.3)
    if not displacement:
        ax.plot(result.original.time, result.original.time, linestyle="--", label="identity")
        ax.legend()
        ax.set_ylabel("Warped source time")
    else:
        ax.axhline(0, linestyle="--")
        ax.set_ylabel("h(t) - t")
    ax.set_xlabel(f"Reference time ({result.original.time_unit})")
    return ax



def plot_fpca_stability(
    result: FPCAStabilityResult,
    *,
    ax=None,
):
    """Plot bootstrap absolute component similarities by reference FPC."""

    if ax is None:
        _, ax = plt.subplots()
    data = [result.similarities[:, k] for k in range(result.reference.n_components)]
    ax.boxplot(data, tick_labels=[f"FPC{k + 1}" for k in range(result.reference.n_components)])
    ax.set_ylim(0, 1.02)
    ax.set_ylabel("Absolute matched functional similarity")
    ax.set_title(f"FPCA bootstrap stability ({result.n_bootstrap} replicates)")
    return ax


def plot_reconstruction_curve(
    reconstruction_summary,
    *,
    ax=None,
):
    """Plot integrated reconstruction error against retained FPC count."""

    required = {"n_components", "mean_integrated_rmse"}
    if not required <= set(reconstruction_summary.columns):
        raise ValueError(
            "reconstruction_summary must contain n_components and mean_integrated_rmse"
        )
    if ax is None:
        _, ax = plt.subplots()
    ax.plot(
        reconstruction_summary["n_components"],
        reconstruction_summary["mean_integrated_rmse"],
        marker="o",
    )
    ax.set_xlabel("Retained functional principal components")
    ax.set_ylabel("Mean integrated RMSE")
    ax.set_title("FPCA reconstruction curve")
    return ax



def plot_conformal_fpca_anomaly(
    result: ConformalFunctionalAnomalyResult,
    *,
    max_targets: int = 50,
    ax=None,
):
    """Plot marginal split-conformal anomaly p-values for target trajectories."""

    if isinstance(max_targets, bool) or not isinstance(max_targets, (int, np.integer)):
        raise TypeError("max_targets must be an integer")
    if max_targets < 1:
        raise ValueError("max_targets must be positive")
    if ax is None:
        _, ax = plt.subplots()

    n = min(max_targets, result.n_targets)
    x = np.arange(n)
    ax.scatter(x, result.p_values[:n])
    ax.axhline(result.alpha, linestyle="--", label=f"alpha={result.alpha:g}")
    ax.set_xticks(x)
    ax.set_xticklabels(result.target_curve_ids[:n], rotation=90)
    ax.set_xlabel("Target trajectory")
    ax.set_ylabel("Marginal conformal p-value")
    ax.set_ylim(0.0, 1.0)
    ax.set_title("Split-conformal FPCA anomaly review")
    ax.legend()
    return ax


def plot_fpca_outlier_diagnostics(
    result: FunctionalOutlierResult,
    *,
    ax=None,
):
    """Plot reconstruction robust-z against score-space Mahalanobis distance."""

    required = {
        "reconstruction_robust_z",
        "score_mahalanobis_sq",
        "score_cutoff",
        "review_flag",
    }
    if not required <= set(result.diagnostics.columns):
        raise ValueError("result does not contain FPCA reconstruction/score diagnostics")
    if ax is None:
        _, ax = plt.subplots()
    frame = result.diagnostics
    ax.scatter(
        frame["reconstruction_robust_z"],
        frame["score_mahalanobis_sq"],
        marker="o",
    )
    threshold = result.provenance.get("reconstruction_z_threshold")
    if threshold is not None:
        ax.axvline(float(threshold), linestyle="--")
    ax.axhline(float(frame["score_cutoff"].iloc[0]), linestyle="--")
    ax.set_xlabel("Reconstruction robust z")
    ax.set_ylabel("Squared Mahalanobis distance in FPC score space")
    ax.set_title("FPCA trajectory review diagnostics")
    return ax


def plot_fpca_influence(
    result: FPCAInfluenceResult,
    *,
    metric: str = "min_abs_component_similarity",
    ax=None,
):
    """Plot leave-one-group-out FPCA influence summaries."""

    if metric not in result.summary.columns:
        raise KeyError(f"Unknown influence metric {metric!r}")
    if ax is None:
        _, ax = plt.subplots()
    x = np.arange(len(result.summary))
    ax.plot(x, result.summary[metric].to_numpy(dtype=float), marker="o")
    ax.set_xticks(x)
    ax.set_xticklabels(result.summary["group"].astype(str), rotation=90)
    ax.set_ylabel(metric.replace("_", " "))
    ax.set_xlabel("Omitted group")
    ax.set_title("Leave-one-group-out FPCA influence")
    return ax



def plot_fpca_cross_validation(
    result: FPCACrossValidationResult,
    *,
    ax=None,
):
    """Plot mean held-out reconstruction RMSE with fold-level SE bars."""

    if ax is None:
        _, ax = plt.subplots()
    summary = summarise_fpca_cross_validation(result)
    ax.errorbar(
        summary["n_components"],
        summary["mean_rmse"],
        yerr=summary["se_rmse"],
        marker="o",
        capsize=3,
    )
    ax.set_xlabel("Retained functional principal components")
    ax.set_ylabel("Held-out integrated RMSE")
    ax.set_title("FPCA reconstruction cross-validation")
    return ax


def plot_fpca_component_envelope(
    result: FPCAComponentEnvelopeResult,
    *,
    component: int = 0,
    dimension: str | None = None,
    ax=None,
):
    """Plot a reference FPC with its descriptive matched-bootstrap envelope."""

    if component < 0 or component >= result.reference.n_components:
        raise IndexError("component is outside the fitted range")
    if dimension is None:
        dimension = result.reference.dimension_names[0]
    if dimension not in result.reference.dimension_names:
        raise KeyError(f"Unknown dimension {dimension!r}")
    if ax is None:
        _, ax = plt.subplots()

    dim = result.reference.dimension_names.index(dimension)
    time = result.reference.time
    ax.fill_between(
        time,
        result.lower[component, :, dim],
        result.upper[component, :, dim],
        alpha=0.2,
        label=f"{100 * result.level:.0f}% pointwise envelope",
    )
    ax.plot(
        time,
        result.median[component, :, dim],
        linestyle="--",
        label="bootstrap median",
    )
    ax.plot(
        time,
        result.reference.components[component, :, dim],
        label="reference FPC",
    )
    ax.set_xlabel(f"Time ({result.reference.time_unit})")
    ax.set_ylabel(f"FPC loading: {dimension}")
    ax.set_title(f"FPC{component + 1} matched-bootstrap envelope")
    ax.legend()
    return ax



def plot_fpca_component_band(
    result: FPCAComponentBandResult,
    *,
    component: int = 0,
    dimension: str | None = None,
    ax=None,
):
    """Plot an FPC with its bootstrap-calibrated simultaneous uncertainty band."""

    if component < 0 or component >= result.n_components:
        raise IndexError("component is outside the banded range")
    if dimension is None:
        dimension = result.reference.dimension_names[0]
    if dimension not in result.reference.dimension_names:
        raise KeyError(f"Unknown dimension {dimension!r}")
    if ax is None:
        _, ax = plt.subplots()

    dim = result.reference.dimension_names.index(dimension)
    time = result.reference.time
    scope = "familywise" if result.simultaneous_scope == "family" else "component-wise"
    ax.fill_between(
        time,
        result.lower[component, :, dim],
        result.upper[component, :, dim],
        alpha=0.2,
        label=f"{100 * result.confidence_level:.1f}% simultaneous band",
    )
    ax.plot(
        time,
        result.reference.components[component, :, dim],
        label="reference FPC",
    )
    ax.set_xlabel(f"Time ({result.reference.time_unit})")
    ax.set_ylabel(f"FPC loading: {dimension}")
    ax.set_title(f"FPC{component + 1} simultaneous band ({scope})")
    ax.legend()
    return ax


def plot_fpca_subspace_stability(
    result: FPCASubspaceStabilityResult,
    *,
    metric: str = "normalized_projector_distance",
    ax=None,
):
    """Plot bootstrap eigenspace stability across resamples."""

    allowed = {
        "normalized_projector_distance",
        "max_principal_angle_degrees",
        "min_principal_cosine",
    }
    if metric not in allowed:
        raise ValueError(
            "metric must be 'normalized_projector_distance', "
            "'max_principal_angle_degrees', or 'min_principal_cosine'"
        )
    if ax is None:
        _, ax = plt.subplots()

    if metric == "normalized_projector_distance":
        values = result.normalized_projector_distance
        ylabel = "Normalized projector distance"
    elif metric == "max_principal_angle_degrees":
        values = np.max(result.principal_angles_degrees, axis=1)
        ylabel = "Maximum principal angle (degrees)"
    else:
        values = np.min(result.principal_cosines, axis=1)
        ylabel = "Minimum principal cosine"

    x = np.arange(1, result.n_bootstrap + 1)
    ax.plot(x, values, marker="o", linestyle="none")
    ax.set_xlabel("Bootstrap replicate")
    ax.set_ylabel(ylabel)
    start = result.component_indices[0] + 1
    end = result.component_indices[-1] + 1
    ax.set_title(f"FPCA subspace stability: FPC{start}–FPC{end}")
    return ax



def plot_sparse_irregular_dimension(
    trajectories: IrregularTrajectorySet,
    *,
    dimension: str,
    ax=None,
):
    """Plot native irregular observations for one functional dimension."""

    if dimension not in trajectories.dimension_names:
        raise KeyError(f"Unknown dimension {dimension!r}")
    if ax is None:
        _, ax = plt.subplots()
    index = trajectories.dimension_names.index(dimension)
    for curve_id, time, values in zip(
        trajectories.curve_ids,
        trajectories.time,
        trajectories.values,
        strict=True,
    ):
        ax.plot(
            time,
            values[:, index],
            marker="o",
            linewidth=1,
            alpha=0.55,
            label=curve_id,
        )
    ax.set_xlabel(f"Time ({trajectories.time_unit})")
    ax.set_ylabel(dimension)
    ax.set_title(f"Native irregular observations: {dimension}")
    if trajectories.n_curves <= 12:
        ax.legend()
    return ax



def plot_functional_mean_band(
    result: FunctionalMeanBandResult,
    *,
    dimension: str | None = None,
    ax=None,
):
    """Plot a functional mean with its simultaneous observed-grid band."""

    if dimension is None:
        dimension = result.dimension_names[0]
    if dimension not in result.dimension_names:
        raise KeyError(f"Unknown dimension {dimension!r}")
    if ax is None:
        _, ax = plt.subplots()

    dim = result.dimension_names.index(dimension)
    level = 100 * result.confidence_level
    ax.fill_between(
        result.time,
        result.lower[:, dim],
        result.upper[:, dim],
        alpha=0.2,
        label=f"{level:.1f}% simultaneous band",
    )
    ax.plot(
        result.time,
        result.mean[:, dim],
        label="functional mean",
    )
    ax.set_xlabel(f"Time ({result.time_unit})")
    ax.set_ylabel(dimension)
    ax.set_title(f"Functional mean band: {dimension}(t)")
    ax.legend()
    return ax



def plot_fpca_regression_cv(
    result: FPCARegressionCVResult,
    *,
    ax=None,
):
    """Plot mean held-out predictive loss against retained FPC count."""

    if ax is None:
        _, ax = plt.subplots()
    summary = summarise_fpca_regression_cv(result)
    ax.errorbar(
        summary["n_components"],
        summary["mean_loss"],
        yerr=summary["se_loss"],
        marker="o",
        capsize=3,
    )
    ax.set_xlabel("Retained functional principal components")
    ax.set_ylabel(f"Held-out {result.loss}")
    ax.set_title(f"Predictive FPCA regression CV ({result.family})")
    return ax


def plot_nested_fpca_regression_cv(
    result: FPCANestedRegressionCVResult,
    *,
    ax=None,
):
    """Plot outer-fold predictive loss from nested FPCA regression CV."""

    if ax is None:
        _, ax = plt.subplots()
    frame = result.outer_folds
    ax.plot(
        frame["outer_fold"] + 1,
        frame["loss"],
        marker="o",
    )
    ax.set_xlabel("Outer fold")
    ax.set_ylabel(f"Outer held-out {result.loss}")
    ax.set_title("Nested predictive FPCA regression")
    return ax
