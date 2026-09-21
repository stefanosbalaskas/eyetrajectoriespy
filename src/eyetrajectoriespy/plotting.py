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
    FPCAResult,
    FPCAStabilityResult,
    FPCASubspaceStabilityResult,
    FunctionalMeanBandResult,
    IrregularTrajectorySet,
    FunctionalOutlierResult,
    RegistrationResult,
    TrajectorySet,
)


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
