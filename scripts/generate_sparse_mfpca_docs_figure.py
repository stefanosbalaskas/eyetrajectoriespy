"""Generate deterministic documentation-only sparse-MFPCA SVG figures.

These figures are built from stable 0.12 public result arrays. They do not add
plotting functions to the 0.12 public API.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from eyetrajectoriespy import IrregularTrajectorySet, fit_sparse_mfpca

OUT = Path("docs/assets/gallery")


def _fit_sparse_planar():
    rng = np.random.default_rng(12012)
    times = []
    values = []
    ids = []
    participants = []
    for i in range(30):
        t = np.sort(np.r_[0.0, rng.uniform(0.03, 0.97, 8), 1.0])
        z1, z2 = rng.normal(size=2)
        x = (
            0.30
            + 0.35 * t
            + 0.42 * z1 * np.sin(np.pi * t)
            + 0.08 * z2 * np.sin(2.0 * np.pi * t)
        )
        y = (
            0.55
            - 0.20 * t
            + 0.24 * z1 * np.cos(np.pi * t)
            - 0.18 * z2 * np.sin(2.0 * np.pi * t)
        )
        xy = np.column_stack([x, y]) + rng.normal(
            0.0,
            0.05,
            size=(t.size, 2),
        )
        times.append(t)
        values.append(xy)
        ids.append(f"P{i + 1:02d}|1")
        participants.append(f"P{i + 1:02d}")

    irregular = IrregularTrajectorySet(
        time=tuple(times),
        values=tuple(values),
        curve_ids=tuple(ids),
        dimension_names=("x", "y"),
        metadata=pd.DataFrame({"participant_id": participants}),
        coordinate_system="normalized",
        time_unit="s",
    )
    return fit_sparse_mfpca(
        irregular,
        dimensions=("x", "y"),
        n_components=2,
        evaluation_grid=np.linspace(0.0, 1.0, 41),
        mean_bandwidth=0.20,
        covariance_bandwidth=0.30,
        measurement_error="diagonal",
        measurement_error_variance=(0.0025, 0.0025),
        psd_action="project",
        score_ridge=0.0,
        score_failure_action="retain_nan",
    )


def _save(fig, name: str) -> None:
    fig.tight_layout()
    fig.savefig(
        OUT / name,
        format="svg",
        bbox_inches="tight",
        metadata={"Date": None, "Creator": "eyetrajectoriespy docs"},
    )
    plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    matplotlib.rcParams["svg.hashsalt"] = "eyetrajectoriespy-sparse-mfpca-docs"
    fit = _fit_sparse_planar()

    extent = [
        fit.evaluation_grid[0],
        fit.evaluation_grid[-1],
        fit.evaluation_grid[0],
        fit.evaluation_grid[-1],
    ]
    blocks = (
        (fit.covariance_cxx, r"$C_{xx}(s,t)$"),
        (fit.covariance_cxy, r"$C_{xy}(s,t)$"),
        (fit.covariance_cyx, r"$C_{yx}(s,t)$"),
        (fit.covariance_cyy, r"$C_{yy}(s,t)$"),
    )
    fig, axes = plt.subplots(2, 2, figsize=(8.0, 6.4))
    vmax = max(float(np.nanmax(np.abs(block))) for block, _ in blocks)
    image = None
    for ax, (block, title) in zip(axes.flat, blocks, strict=True):
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
        ax.set_xlabel("t")
        ax.set_ylabel("s")
    assert image is not None
    fig.colorbar(
        image,
        ax=axes.ravel().tolist(),
        shrink=0.80,
        label="covariance",
    )
    _save(fig, "sparse-mfpca-covariance-blocks.svg")

    fig, axes = plt.subplots(1, 2, figsize=(8.0, 3.4))
    scale = np.sqrt(fit.eigenvalues[0])
    for dimension, ax in enumerate(axes):
        ax.plot(fit.evaluation_grid, fit.mean[:, dimension], label="mean")
        ax.plot(
            fit.evaluation_grid,
            fit.mean[:, dimension]
            + scale * fit.eigenfunctions[0, :, dimension],
            label="mean + 1 SD mode",
        )
        ax.plot(
            fit.evaluation_grid,
            fit.mean[:, dimension]
            - scale * fit.eigenfunctions[0, :, dimension],
            label="mean - 1 SD mode",
        )
        ax.set_title(fit.dimensions[dimension])
        ax.set_xlabel("time")
        ax.set_ylabel("coordinate")
    axes[0].legend(fontsize=8)
    _save(fig, "sparse-mfpca-eigenfunction.svg")


if __name__ == "__main__":
    main()
