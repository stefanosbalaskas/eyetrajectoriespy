"""Generate deterministic SVG figures used by the documentation gallery."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from eyetrajectoriespy import (
    TrajectorySet,
    delay_embed_trajectory,
    estimate_largest_lyapunov_rosenstein,
    fit_local_return_map,
    fit_mfpca,
    fpca_wild_bootstrap_family_test_monte_carlo_diagnostics,
    fpca_wild_bootstrap_projection_family_test,
    local_divergence_curve,
    multiplier_functional_mean_band,
    plot_fpca_component,
    plot_fpca_variance,
    plot_fpca_wild_bootstrap_family_test,
    plot_fpca_wild_bootstrap_monte_carlo_diagnostics,
    plot_fpca_wild_bootstrap_projection,
    plot_functional_mean_band,
    plot_local_divergence,
    plot_planar_trajectories,
    plot_poincare_return_map,
    plot_recurrence,
    plot_windowed_rqa,
    plot_warping_functions,
    poincare_crossings,
    recurrence_matrix,
    register_to_landmarks,
    simulate_planar_trajectories,
    wild_bootstrap_fpca_projection,
    windowed_rqa,
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
    matplotlib.rcParams["svg.hashsalt"] = "eyetrajectoriespy-0.23-gallery"

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

    ax = plot_fpca_variance(fpca, cumulative=True)
    _save(ax, "fpca-variance.svg")

    landmark_rng = np.random.default_rng(2107)
    observed_landmarks = np.column_stack(
        [
            np.clip(landmark_rng.normal(0.65, 0.06, gaze.n_curves), 0.35, 0.95),
            np.clip(landmark_rng.normal(1.35, 0.07, gaze.n_curves), 1.05, 1.65),
        ]
    )
    registration = register_to_landmarks(gaze, observed_landmarks)
    ax = plot_warping_functions(registration, displacement=True)
    _save(ax, "registration-warping.svg")

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
    ax = plot_fpca_wild_bootstrap_family_test(
        family,
        max_targets=5,
        show_targetwise=True,
    )
    _save(ax, "wild-bootstrap-family-test.svg")

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

    nonlinear_time = np.arange(360, dtype=float) * 0.01
    nonlinear_x = np.empty(nonlinear_time.size, dtype=float)
    nonlinear_x[0] = 0.217
    for i in range(nonlinear_x.size - 1):
        nonlinear_x[i + 1] = 4.0 * nonlinear_x[i] * (1.0 - nonlinear_x[i])
    nonlinear = TrajectorySet(
        time=nonlinear_time,
        values=nonlinear_x[None, :, None],
        curve_ids=("nonlinear-demo",),
        dimension_names=("x",),
        time_unit="s",
        coordinate_system="arbitrary",
    )
    embedded = delay_embed_trajectory(
        nonlinear,
        embedding_dimension=2,
        delay=1,
        dimensions=("x",),
    )
    recurrence = recurrence_matrix(
        embedded,
        curve=0,
        target_recurrence_rate=0.05,
        theiler_window=8,
    )
    ax = plot_recurrence(recurrence)
    _save(ax, "recurrence-plot.svg")

    dynamic_rqa = windowed_rqa(
        nonlinear,
        curve=0,
        window=100,
        step=50,
        radius=0.05,
        theiler_window=8,
        dimensions=("x",),
    )
    ax = plot_windowed_rqa(dynamic_rqa)
    _save(ax, "windowed-rqa.svg")

    divergence = local_divergence_curve(
        embedded,
        curve=0,
        theiler_window=8,
        max_horizon=7,
    )
    lle = estimate_largest_lyapunov_rosenstein(
        divergence,
        fit_start=1,
        fit_end=4,
    )
    ax = plot_local_divergence(lle)
    _save(ax, "local-divergence.svg")

    cycle_time = np.linspace(0.0, 20.0 * np.pi, 2001)
    cycle_amplitude = np.exp(-0.02 * cycle_time)
    cycle = TrajectorySet(
        time=cycle_time,
        values=np.stack(
            [
                cycle_amplitude * np.sin(cycle_time),
                cycle_amplitude * np.cos(cycle_time),
            ],
            axis=1,
        )[None, :, :],
        curve_ids=("cycle-demo",),
        dimension_names=("x", "y"),
        time_unit="s",
        coordinate_system="arbitrary",
    )
    crossings = poincare_crossings(
        cycle,
        curve=0,
        section_dimension="x",
        section_value=0.0,
        direction="positive",
        state_dimensions=("y",),
    )
    return_fit = fit_local_return_map(
        crossings,
        reference="mean",
        n_neighbors=8,
    )
    ax = plot_poincare_return_map(crossings, fit=return_fit)
    _save(ax, "return-map.svg")

    expected = {
        "planar-trajectories.svg",
        "fpca-component.svg",
        "fpca-variance.svg",
        "registration-warping.svg",
        "functional-mean-band.svg",
        "wild-bootstrap-projections.svg",
        "wild-bootstrap-family-test.svg",
        "monte-carlo-precision.svg",
        "recurrence-plot.svg",
        "windowed-rqa.svg",
        "local-divergence.svg",
        "return-map.svg",
    }
    produced = {path.name for path in OUTPUT.glob("*.svg")}
    missing = sorted(expected - produced)
    if missing:
        raise RuntimeError(f"gallery generation missed expected assets: {missing}")


if __name__ == "__main__":
    main()
