from dataclasses import replace

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from eyetrajectoriespy import (
    FPCAWildBootstrapTruncationScanResult,
    FPCAWildBootstrapTruncationSelectionResult,
    fpca_wild_bootstrap_truncation_reporting_text,
    fpca_wild_bootstrap_truncation_scan_frame,
    fpca_wild_bootstrap_truncation_selection_frame,
    plot_fpca_wild_bootstrap_truncation_scan,
    scan_wild_bootstrap_fpca_truncations,
    select_fpca_wild_bootstrap_truncation,
    simulate_planar_trajectories,
    wild_bootstrap_fpca_projection,
)


def sample():
    gaze = simulate_planar_trajectories(
        n_participants=38,
        trials_per_participant=1,
        n_time=31,
        random_state=171,
    )
    from eyetrajectoriespy import fit_mfpca

    fpca = fit_mfpca(gaze, n_components=4, scaling="dimension_sd")
    rng = np.random.default_rng(171)
    s1 = fpca.scores[:, 0]
    s2 = fpca.scores[:, 1]
    sd = 0.20 + 0.25 * np.abs(s1) / max(np.std(s1, ddof=1), 1e-8)
    outcome = 0.7 + 0.9 * s1 - 0.35 * s2 + rng.normal(0.0, sd)
    return gaze, outcome


def test_scan_contract_reproducibility_and_highest_candidate_matches_standalone():
    gaze, outcome = sample()
    targets = gaze.subset([0, 2, 4])
    scan = scan_wild_bootstrap_fpca_truncations(
        gaze,
        outcome,
        targets=targets,
        candidate_components=(2, 3, 4),
        n_bootstrap=24,
        residual_components=2,
        scaling="dimension_sd",
        multiplier="normal",
        confidence_level=0.95,
        independent_unit_column="participant_id",
        random_state=17,
    )
    again = scan_wild_bootstrap_fpca_truncations(
        gaze,
        outcome,
        targets=targets,
        candidate_components=(2, 3, 4),
        n_bootstrap=24,
        residual_components=2,
        scaling="dimension_sd",
        multiplier="normal",
        confidence_level=0.95,
        independent_unit_column="participant_id",
        random_state=17,
    )
    standalone = wild_bootstrap_fpca_projection(
        gaze,
        outcome,
        targets=targets,
        n_bootstrap=24,
        residual_components=2,
        inference_components=4,
        scaling="dimension_sd",
        multiplier="normal",
        confidence_level=0.95,
        independent_unit_column="participant_id",
        random_state=17,
    )

    assert isinstance(scan, FPCAWildBootstrapTruncationScanResult)
    assert scan.studentized_roots.shape == (3, 24, 3)
    assert scan.n_candidates == 3
    assert scan.n_bootstrap == 24
    assert scan.n_targets == 3
    assert np.allclose(scan.studentized_roots, again.studentized_roots)
    assert np.allclose(scan.widths, again.widths)
    assert np.allclose(scan.reference_projections[-1], standalone.reference_projection)
    assert np.allclose(scan.reference_se[-1], standalone.reference_se)
    assert np.allclose(scan.studentized_roots[-1], standalone.studentized_roots)
    assert np.allclose(scan.lower[-1], standalone.lower)
    assert np.allclose(scan.upper[-1], standalone.upper)
    assert scan.provenance["fpca_wild_bootstrap_truncation_scan"][
        "shared_multiplier_draws_across_h"
    ] is True


def test_stabilized_volatility_selection_exact_synthetic_truth():
    gaze, outcome = sample()
    base = scan_wild_bootstrap_fpca_truncations(
        gaze,
        outcome,
        targets=gaze.subset([0, 1]),
        candidate_components=(2, 3, 4, 5, 6),
        n_bootstrap=20,
        residual_components=2,
        random_state=7,
    )
    widths = np.array(
        [
            [2.00, 2.00],
            [1.05, 1.70],
            [1.00, 1.45],
            [0.98, 1.20],
            [0.97, 0.95],
        ]
    )
    centers = np.array(
        [
            [0.00, 0.00],
            [0.50, 0.25],
            [0.52, 0.50],
            [0.53, 0.75],
            [0.54, 1.00],
        ]
    )
    synthetic = replace(
        base,
        widths=widths,
        centers=centers,
        lower=centers - widths / 2.0,
        upper=centers + widths / 2.0,
    )

    selected = select_fpca_wild_bootstrap_truncation(
        synthetic,
        width_threshold=0.10,
        center_threshold=0.05,
        stability_run=1,
        on_failure="ignore",
    )
    assert isinstance(selected, FPCAWildBootstrapTruncationSelectionResult)
    assert selected.selected_components[0] == 3
    assert np.isnan(selected.selected_components[1])
    assert selected.stable_both[:, 0].tolist() == [False, True, True, True]
    assert not np.any(selected.stable_both[:, 1])

    with pytest.raises(RuntimeError, match="no qualifying run"):
        select_fpca_wild_bootstrap_truncation(
            synthetic,
            width_threshold=0.10,
            center_threshold=0.05,
            stability_run=1,
        )


def test_thresholds_run_and_candidate_grid_validation():
    gaze, outcome = sample()
    with pytest.raises(ValueError, match="consecutive"):
        scan_wild_bootstrap_fpca_truncations(
            gaze,
            outcome,
            candidate_components=(2, 4),
            n_bootstrap=20,
            residual_components=2,
        )
    with pytest.raises(ValueError, match="greater than or equal"):
        scan_wild_bootstrap_fpca_truncations(
            gaze,
            outcome,
            candidate_components=(1, 2, 3),
            n_bootstrap=20,
            residual_components=2,
        )

    scan = scan_wild_bootstrap_fpca_truncations(
        gaze,
        outcome,
        targets=gaze.subset([0]),
        candidate_components=(2, 3, 4),
        n_bootstrap=20,
        residual_components=2,
        random_state=9,
    )
    with pytest.raises(ValueError, match="strictly positive"):
        select_fpca_wild_bootstrap_truncation(
            scan,
            width_threshold=0,
            center_threshold=0.1,
            stability_run=0,
        )
    with pytest.raises(ValueError, match="more consecutive"):
        select_fpca_wild_bootstrap_truncation(
            scan,
            width_threshold=1,
            center_threshold=1,
            stability_run=2,
        )
    with pytest.raises(ValueError, match="on_failure"):
        select_fpca_wild_bootstrap_truncation(
            scan,
            width_threshold=1,
            center_threshold=1,
            stability_run=0,
            on_failure="largest",
        )


def test_frames_plot_and_reporting():
    gaze, outcome = sample()
    scan = scan_wild_bootstrap_fpca_truncations(
        gaze,
        outcome,
        targets=gaze.subset([0, 1]),
        candidate_components=(2, 3, 4),
        n_bootstrap=20,
        residual_components=2,
        random_state=13,
    )
    scan_frame = fpca_wild_bootstrap_truncation_scan_frame(scan)
    assert len(scan_frame) == 6
    assert {"curve_id", "inference_components", "center", "width"} <= set(
        scan_frame.columns
    )

    selection = select_fpca_wild_bootstrap_truncation(
        scan,
        width_threshold=1e9,
        center_threshold=1e9,
        stability_run=0,
    )
    selected_frame = fpca_wild_bootstrap_truncation_selection_frame(selection)
    assert len(selected_frame) == 2
    assert np.all(selection.selected_components == 2)

    text = fpca_wild_bootstrap_truncation_reporting_text(selection)
    assert "shared-multiplier" in text
    assert "r=0" in text
    assert "analyst supplied" in text
    assert "no 0.01 default" in text

    assert plot_fpca_wild_bootstrap_truncation_scan(
        selection,
        target=0,
        metric="width",
    ) is not None
    assert plot_fpca_wild_bootstrap_truncation_scan(
        scan,
        target=scan.target_curve_ids[0],
        metric="center",
    ) is not None
    with pytest.raises(ValueError, match="metric"):
        plot_fpca_wild_bootstrap_truncation_scan(scan, metric="variance")
    plt.close("all")
