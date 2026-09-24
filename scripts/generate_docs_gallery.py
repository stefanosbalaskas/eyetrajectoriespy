"""Generate deterministic SVG figures used by the documentation gallery."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from eyetrajectoriespy import (
    TrajectorySet,
    bootstrap_function_on_scalar_coefficients,
    bootstrap_rqa_metric_means,
    delay_embed_trajectory,
    dynamic_time_warping_distance,
    estimate_largest_lyapunov_kantz,
    estimate_largest_lyapunov_rosenstein,
    fit_function_on_scalar_regression,
    fit_local_return_map,
    fit_mfpca,
    fpca_wild_bootstrap_family_test_monte_carlo_diagnostics,
    fpca_wild_bootstrap_projection_family_test,
    kantz_divergence_curve,
    kantz_parameter_sensitivity,
    local_divergence_curve,
    multiplier_functional_mean_band,
    plot_dynamic_time_warping_alignment,
    plot_fpca_component,
    plot_fpca_variance,
    plot_fpca_wild_bootstrap_family_test,
    plot_fpca_wild_bootstrap_monte_carlo_diagnostics,
    plot_fpca_wild_bootstrap_projection,
    plot_function_on_scalar_coefficients,
    plot_functional_mean_band,
    plot_kantz_sensitivity,
    plot_local_divergence,
    plot_planar_trajectories,
    plot_trajectory_overlay,
    plot_poincare_return_map,
    plot_recurrence,
    plot_recurrence_rate_curve,
    plot_rqa_metric_mean_bootstrap,
    plot_windowed_rqa,
    plot_windowed_rqa_trajectories,
    plot_warping_functions,
    poincare_crossings,
    recurrence_matrix,
    recurrence_radius_profile,
    function_on_scalar_simultaneous_bands,
    register_to_landmarks,
    signed_curvature_function,
    simulate_planar_trajectories,
    wild_bootstrap_fpca_projection,
    windowed_rqa,
    windowed_rqa_trajectory_set,
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
    matplotlib.rcParams["svg.hashsalt"] = "eyetrajectoriespy-0.24-gallery"

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

    geometry_time = np.linspace(0.0, 2.5, 241)
    geometry_values = np.column_stack(
        [
            geometry_time,
            0.35 * np.sin(2.0 * np.pi * geometry_time / 2.5),
        ]
    )[None, :, :]
    geometry_source = TrajectorySet(
        time=geometry_time,
        values=geometry_values,
        curve_ids=("geometry-demo",),
        dimension_names=("x", "y"),
        time_unit="s",
        coordinate_system="degrees",
    )
    geometry_curvature = signed_curvature_function(
        geometry_source,
        min_speed=0.0,
    )
    ax = plot_trajectory_overlay(
        geometry_curvature,
        dimension="signed_curvature",
        max_curves=None,
        alpha=1.0,
    )
    _save(ax, "trajectory-curvature.svg")

    dtw_a = np.array([[0.0], [0.0], [1.0], [1.5], [2.0]])
    dtw_b = np.array([[0.0], [0.5], [1.0], [2.0]])
    dtw_audit = dynamic_time_warping_distance(
        dtw_a,
        dtw_b,
        step_pattern="symmetric2",
        normalize=True,
        window_radius=2,
        return_path=True,
    )
    ax = plot_dynamic_time_warping_alignment(dtw_audit)
    _save(ax, "dtw-alignment.svg")

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

    fosr_rng = np.random.default_rng(2109)
    fosr_condition = np.repeat([0.0, 1.0], gaze.n_curves // 2)
    fosr_beta = 0.28 * np.exp(-((gaze.time - 1.15) / 0.35) ** 2)
    fosr_response = (
        0.06 * np.sin(2.0 * np.pi * gaze.time / gaze.time[-1])[None, :]
        + fosr_condition[:, None] * fosr_beta[None, :]
        + fosr_rng.normal(0.0, 0.08, size=(gaze.n_curves, gaze.n_time))
    )
    fosr_source = TrajectorySet(
        time=gaze.time.copy(),
        values=fosr_response[:, :, None],
        curve_ids=gaze.curve_ids,
        dimension_names=("metric",),
        time_unit=gaze.time_unit,
        coordinate_system="unknown",
    )
    fosr_design = pd.DataFrame(
        {
            "curve_id": fosr_source.curve_ids,
            "condition": fosr_condition,
        }
    )
    fosr_fit = fit_function_on_scalar_regression(
        fosr_source,
        fosr_design,
        predictors=("condition",),
    )
    fosr_boot = bootstrap_function_on_scalar_coefficients(
        fosr_fit,
        n_bootstrap=100,
        random_state=2109,
    )
    fosr_band = function_on_scalar_simultaneous_bands(
        fosr_boot,
        confidence_level=0.95,
    )
    ax = plot_function_on_scalar_coefficients(
        fosr_band,
        coefficient="condition",
        dimension="metric",
    )
    _save(ax, "function-on-scalar-coefficient.svg")

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

    radius_profile = recurrence_radius_profile(
        embedded,
        curve=0,
        radii=(0.01, 0.02, 0.04, 0.06, 0.08, 0.12, 0.18),
        theiler_window=8,
    )
    ax = plot_recurrence_rate_curve(radius_profile)
    _save(ax, "recurrence-radius-profile.svg")

    rqa_bootstrap_time = np.arange(120, dtype=float) * 0.01
    rqa_bootstrap_values = []
    rqa_bootstrap_participants = []
    for participant_index in range(8):
        for trial_index in range(2):
            phase = 0.10 * participant_index + 0.05 * trial_index
            signal = np.sin(
                2.0 * np.pi * 1.8 * rqa_bootstrap_time + phase
            )
            rqa_bootstrap_values.append(signal[:, None])
            rqa_bootstrap_participants.append(
                f"P{participant_index + 1:02d}"
            )
    rqa_bootstrap_source = TrajectorySet(
        time=rqa_bootstrap_time,
        values=np.asarray(rqa_bootstrap_values, dtype=float),
        curve_ids=tuple(
            f"RB-{index + 1:02d}"
            for index in range(len(rqa_bootstrap_values))
        ),
        dimension_names=("x",),
        metadata=pd.DataFrame(
            {"participant_id": rqa_bootstrap_participants}
        ),
        time_unit="s",
        coordinate_system="normalized",
    )
    rqa_bootstrap = bootstrap_rqa_metric_means(
        rqa_bootstrap_source,
        dimensions=("x",),
        metrics=("recurrence_rate", "determinism", "laminarity"),
        radius=0.18,
        theiler_window=2,
        unit="participant",
        participant_column="participant_id",
        confidence_level=0.95,
        n_bootstrap=160,
        random_state=2108,
    )
    ax = plot_rqa_metric_mean_bootstrap(rqa_bootstrap)
    _save(ax, "rqa-population-bootstrap.svg")

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

    rqa_time = np.arange(240, dtype=float) * 0.01
    rqa_curves = np.asarray(
        [
            np.sin(2.0 * np.pi * (1.5 + 0.08 * index) * rqa_time + 0.18 * index)
            for index in range(6)
        ],
        dtype=float,
    )[:, :, None]
    rqa_source = TrajectorySet(
        time=rqa_time,
        values=rqa_curves,
        curve_ids=tuple(f"RQA-{index + 1:02d}" for index in range(6)),
        dimension_names=("x",),
        time_unit="s",
        coordinate_system="normalized",
    )
    functional_rqa = windowed_rqa_trajectory_set(
        rqa_source,
        metrics=("recurrence_rate",),
        window=80,
        step=40,
        radius=0.22,
        theiler_window=2,
        dimensions=("x",),
    )
    ax = plot_windowed_rqa_trajectories(
        functional_rqa,
        metric="recurrence_rate",
        show_mean=True,
    )
    _save(ax, "functional-rqa-trajectories.svg")

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

    kantz_divergence = kantz_divergence_curve(
        embedded,
        curve=0,
        radius=0.08,
        min_neighbors=2,
        theiler_window=8,
        max_horizon=7,
    )
    kantz_lle = estimate_largest_lyapunov_kantz(
        kantz_divergence,
        fit_start=1,
        fit_end=4,
    )
    ax = plot_local_divergence(kantz_lle)
    _save(ax, "kantz-divergence.svg")

    kantz_sensitivity = kantz_parameter_sensitivity(
        nonlinear,
        curve=0,
        dimensions=("x",),
        embedding_dimensions=(2,),
        delays=(1,),
        radii=(0.04, 0.06, 0.08, 0.10, 0.12),
        min_neighbors=(2,),
        theiler_windows=(8,),
        fit_intervals=((1, 4),),
        max_horizon=7,
    )
    ax = plot_kantz_sensitivity(
        kantz_sensitivity,
        parameter="requested_radius",
        response="exponent",
        filters={
            "embedding_dimension": 2,
            "requested_delay": 1.0,
            "min_neighbors": 2,
            "requested_theiler_window": 8.0,
            "requested_fit_start": 1.0,
            "requested_fit_end": 4.0,
        },
    )
    _save(ax, "kantz-sensitivity.svg")

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
        "trajectory-curvature.svg",
        "registration-warping.svg",
        "functional-mean-band.svg",
        "wild-bootstrap-projections.svg",
        "wild-bootstrap-family-test.svg",
        "monte-carlo-precision.svg",
        "recurrence-plot.svg",
        "recurrence-radius-profile.svg",
        "rqa-population-bootstrap.svg",
        "windowed-rqa.svg",
        "functional-rqa-trajectories.svg",
        "local-divergence.svg",
        "kantz-divergence.svg",
        "kantz-sensitivity.svg",
        "return-map.svg",
    }
    produced = {path.name for path in OUTPUT.glob("*.svg")}
    missing = sorted(expected - produced)
    if missing:
        raise RuntimeError(f"gallery generation missed expected assets: {missing}")


if __name__ == "__main__":
    main()
