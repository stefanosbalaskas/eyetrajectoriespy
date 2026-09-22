"""Generate deterministic SVG figures used by the documentation gallery."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from eyetrajectoriespy import (
    fit_mfpca,
    fpca_wild_bootstrap_family_test_monte_carlo_diagnostics,
    fpca_wild_bootstrap_projection_family_test,
    multiplier_functional_mean_band,
    plot_fpca_component,
    plot_fpca_wild_bootstrap_monte_carlo_diagnostics,
    plot_fpca_wild_bootstrap_projection,
    plot_functional_mean_band,
    plot_planar_trajectories,
    simulate_planar_trajectories,
    wild_bootstrap_fpca_projection,
)


OUTPUT = Path("docs/assets/gallery")


def _save(ax, filename: str) -> None:
    ax.figure.tight_layout()
    ax.figure.savefig(
        OUTPUT / filename,
        format="svg",
        bbox_inches="tight",
        metadata={"Date": None, "Creator": "eyetrajectoriespy docs gallery"},
    )
    plt.close(ax.figure)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    matplotlib.rcParams["svg.hashsalt"] = "eyetrajectoriespy-0.21-gallery"

    gaze = simulate_planar_trajectories(
        n_participants=32,
        trials_per_participant=1,
        n_time=61,
        random_state=2101,
    )

    ax = plot_planar_trajectories(gaze, max_curves=24, alpha=0.32)
    _save(ax, "planar-trajectories.svg")

    fpca = fit_mfpca(gaze, n_components=3, scaling="dimension_sd")
    ax = plot_fpca_component(
        fpca,
        component=0,
        dimension=fpca.dimension_names[0],
    )
    _save(ax, "fpca-component.svg")

    mean_band = multiplier_functional_mean_band(
        gaze,
        confidence_level=0.95,
        n_multiplier=240,
        unit="curve",
        random_state=2102,
    )
    ax = plot_functional_mean_band(
        mean_band,
        dimension=gaze.dimension_names[0],
    )
    _save(ax, "functional-mean-band.svg")

    rng = np.random.default_rng(2103)
    score1 = fpca.scores[:, 0]
    score2 = fpca.scores[:, 1]
    noise_sd = 0.20 + 0.22 * (
        np.abs(score1) / max(np.std(score1, ddof=1), 1e-8)
    )
    outcome = (
        0.5
        + 0.9 * score1
        - 0.30 * score2
        + rng.normal(0.0, noise_sd)
    )

    wild = wild_bootstrap_fpca_projection(
        gaze,
        outcome,
        targets=gaze.subset([0, 1, 2, 3, 4]),
        n_bootstrap=59,
        residual_components=2,
        inference_components=3,
        scaling="dimension_sd",
        multiplier="normal",
        random_state=2104,
    )
    ax = plot_fpca_wild_bootstrap_projection(wild, max_targets=5)
    _save(ax, "wild-bootstrap-projections.svg")

    family = fpca_wild_bootstrap_projection_family_test(
        wild,
        null_values=0.0,
        significance_level=0.05,
        pvalue_correction="plus_one",
    )
    precision = fpca_wild_bootstrap_family_test_monte_carlo_diagnostics(
        family,
        confidence_level=0.95,
    )
    ax = plot_fpca_wild_bootstrap_monte_carlo_diagnostics(
        precision,
        max_targets=5,
        show_targetwise=True,
    )
    _save(ax, "monte-carlo-precision.svg")

    expected = {
        "planar-trajectories.svg",
        "fpca-component.svg",
        "functional-mean-band.svg",
        "wild-bootstrap-projections.svg",
        "monte-carlo-precision.svg",
    }
    produced = {path.name for path in OUTPUT.glob("*.svg")}
    missing = sorted(expected - produced)
    if missing:
        raise RuntimeError(f"gallery generation missed expected assets: {missing}")


if __name__ == "__main__":
    main()
