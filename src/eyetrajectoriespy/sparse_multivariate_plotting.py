"""Visualization helpers for native sparse multivariate FPCA / joint PACE."""

from __future__ import annotations

from numbers import Real

import matplotlib.pyplot as plt
import numpy as np

from .types import SparseMFPCAResult


def _require_result(result: SparseMFPCAResult) -> SparseMFPCAResult:
    if not isinstance(result, SparseMFPCAResult):
        raise TypeError("result must be a SparseMFPCAResult")
    return result


def _require_stage(stage: str) -> str:
    if stage not in {"used", "smoothed"}:
        raise ValueError("stage must be 'used' or 'smoothed'")
    return stage


def _covariance_blocks(result: SparseMFPCAResult, stage: str):
    prefix = "covariance" if stage == "used" else "smoothed"
    return (
        np.asarray(getattr(result, f"{prefix}_cxx"), dtype=float),
        np.asarray(getattr(result, f"{prefix}_cxy"), dtype=float),
        np.asarray(getattr(result, f"{prefix}_cyx"), dtype=float),
        np.asarray(getattr(result, f"{prefix}_cyy"), dtype=float),
    )


def _heatmap_extent(result: SparseMFPCAResult) -> list[float]:
    grid = np.asarray(result.evaluation_grid, dtype=float)
    return [float(grid[0]), float(grid[-1]), float(grid[0]), float(grid[-1])]


def _symmetric_limit(arrays) -> float:
    vmax = max(float(np.nanmax(np.abs(array))) for array in arrays)
    return vmax if np.isfinite(vmax) and vmax > 0.0 else 1.0


def plot_sparse_mfpca_component(
    result: SparseMFPCAResult,
    *,
    component: int = 0,
    sd_multiplier: float = 2.0,
    axes=None,
):
    """Plot the planar mean plus/minus one retained sparse-MFPCA mode."""

    result = _require_result(result)
    if isinstance(component, bool) or not isinstance(component, int):
        raise TypeError("component must be an integer")
    if component < 0 or component >= result.n_components:
        raise IndexError("component is outside the retained sparse-MFPCA range")
    if isinstance(sd_multiplier, bool) or not isinstance(sd_multiplier, Real):
        raise TypeError("sd_multiplier must be a real scalar")
    sd_multiplier = float(sd_multiplier)
    if not np.isfinite(sd_multiplier) or sd_multiplier <= 0.0:
        raise ValueError("sd_multiplier must be finite and > 0")

    if axes is None:
        _, axes = plt.subplots(1, 2, figsize=(9.0, 3.6), sharex=True)
    axes = np.asarray(axes, dtype=object).reshape(-1)
    if axes.size != 2:
        raise ValueError("axes must contain exactly two Matplotlib axes")

    grid = np.asarray(result.evaluation_grid, dtype=float)
    mean = np.asarray(result.mean, dtype=float)
    mode = np.asarray(result.eigenfunctions[component], dtype=float)
    scale = sd_multiplier * np.sqrt(float(result.eigenvalues[component]))

    for dimension, ax in enumerate(axes):
        center = mean[:, dimension]
        displacement = scale * mode[:, dimension]
        label = str(result.dimensions[dimension])
        ax.plot(grid, center, label="mean")
        ax.plot(grid, center + displacement, label=f"mean + {sd_multiplier:g} SD mode")
        ax.plot(grid, center - displacement, label=f"mean - {sd_multiplier:g} SD mode")
        ax.set_title(f"{label}: component {component + 1}")
        ax.set_xlabel(f"time ({result.time_unit})")
        ax.set_ylabel(label)
    axes[0].legend(fontsize=8)
    return axes


def plot_sparse_mfpca_covariance_blocks(
    result: SparseMFPCAResult,
    *,
    stage: str = "used",
    axes=None,
):
    """Plot the full 2x2 sparse planar covariance operator."""

    result = _require_result(result)
    stage = _require_stage(stage)
    blocks = _covariance_blocks(result, stage)
    if axes is None:
        _, axes = plt.subplots(
            2,
            2,
            figsize=(8.2, 6.8),
            sharex=True,
            sharey=True,
            layout="constrained",
        )
    axes = np.asarray(axes, dtype=object)
    if axes.size != 4:
        raise ValueError("axes must contain exactly four Matplotlib axes")
    axes = axes.reshape(2, 2)

    d0, d1 = map(str, result.dimensions)
    titles = (
        rf"$C_{{{d0}{d0}}}(s,t)$",
        rf"$C_{{{d0}{d1}}}(s,t)$",
        rf"$C_{{{d1}{d0}}}(s,t)$",
        rf"$C_{{{d1}{d1}}}(s,t)$",
    )
    extent = _heatmap_extent(result)
    vmax = _symmetric_limit(blocks)
    image = None
    for ax, block, title in zip(axes.flat, blocks, titles, strict=True):
        image = ax.imshow(
            block,
            origin="lower",
            aspect="auto",
            extent=extent,
            vmin=-vmax,
            vmax=vmax,
            cmap="coolwarm",
        )
        ax.set_title(title)
        ax.set_xlabel(f"t ({result.time_unit})")
        ax.set_ylabel(f"s ({result.time_unit})")
    if image is not None:
        axes[0, 0].figure.colorbar(
            image,
            ax=axes.ravel().tolist(),
            shrink=0.82,
            label="covariance",
        )
    axes[0, 0].figure.suptitle(f"Sparse MFPCA covariance blocks ({stage})")
    return axes


def plot_sparse_mfpca_score_diagnostics(
    result: SparseMFPCAResult,
    *,
    ax=None,
):
    """Plot joint-PACE conditioning against paired native observations."""

    result = _require_result(result)
    diagnostics = result.score_diagnostics
    required = {"n_time_points", "condition_number", "status_code"}
    missing = sorted(required - set(diagnostics.columns))
    if missing:
        raise ValueError(f"score_diagnostics is missing required columns: {missing}")
    if ax is None:
        _, ax = plt.subplots(figsize=(6.2, 4.2))

    x = diagnostics["n_time_points"].to_numpy(dtype=float)
    condition = diagnostics["condition_number"].to_numpy(dtype=float)
    statuses = diagnostics["status_code"].astype(str).to_numpy()
    finite = np.isfinite(x) & np.isfinite(condition)
    ok = statuses == "ok"

    good = finite & ok
    flagged = finite & ~ok
    if np.any(good):
        ax.scatter(x[good], condition[good], label="joint PACE solved")
    if np.any(flagged):
        ax.scatter(x[flagged], condition[flagged], marker="x", label="flagged solve")
    if np.any(~finite):
        ax.scatter([], [], marker="x", label="non-finite / failed")

    ax.set_xlabel("paired native observations")
    ax.set_ylabel("conditional-system condition number")
    ax.set_title("Sparse MFPCA joint-PACE score diagnostics")
    if ax.collections:
        ax.legend(fontsize=8)
    return ax


def plot_sparse_mfpca_cross_covariance(
    result: SparseMFPCAResult,
    *,
    stage: str = "used",
    axes=None,
):
    """Plot directional cross-covariance blocks ``C_xy`` and ``C_yx``."""

    result = _require_result(result)
    stage = _require_stage(stage)
    _, cxy, cyx, _ = _covariance_blocks(result, stage)
    if axes is None:
        _, axes = plt.subplots(
            1,
            2,
            figsize=(8.5, 3.7),
            sharex=True,
            sharey=True,
            layout="constrained",
        )
    axes = np.asarray(axes, dtype=object).reshape(-1)
    if axes.size != 2:
        raise ValueError("axes must contain exactly two Matplotlib axes")

    d0, d1 = map(str, result.dimensions)
    blocks = (cxy, cyx)
    titles = (rf"$C_{{{d0}{d1}}}(s,t)$", rf"$C_{{{d1}{d0}}}(s,t)$")
    extent = _heatmap_extent(result)
    vmax = _symmetric_limit(blocks)
    image = None
    for ax, block, title in zip(axes, blocks, titles, strict=True):
        image = ax.imshow(
            block,
            origin="lower",
            aspect="auto",
            extent=extent,
            vmin=-vmax,
            vmax=vmax,
            cmap="coolwarm",
        )
        ax.set_title(title)
        ax.set_xlabel(f"t ({result.time_unit})")
        ax.set_ylabel(f"s ({result.time_unit})")
    if image is not None:
        axes[0].figure.colorbar(
            image,
            ax=axes.tolist(),
            shrink=0.82,
            label="cross-covariance",
        )
    axes[0].figure.suptitle(
        f"Sparse MFPCA directional cross-covariance ({stage})"
    )
    return axes
