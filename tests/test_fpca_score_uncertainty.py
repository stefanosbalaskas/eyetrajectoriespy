from dataclasses import replace

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from eyetrajectoriespy import (
    FPCAScoreUncertaintyResult,
    bootstrap_fpca_score_uncertainty,
    fpca_score_uncertainty_frame,
    fpca_score_uncertainty_reporting_text,
    plot_fpca_score_uncertainty,
    simulate_planar_trajectories,
)


def sample():
    return simulate_planar_trajectories(
        n_participants=12,
        trials_per_participant=2,
        n_time=31,
        random_state=61,
    )


def test_training_score_uncertainty_is_reproducible_and_reference_scores_match():
    gaze = sample()
    first = bootstrap_fpca_score_uncertainty(
        gaze,
        n_bootstrap=20,
        n_components=2,
        scaling="dimension_sd",
        random_state=7,
    )
    second = bootstrap_fpca_score_uncertainty(
        gaze,
        n_bootstrap=20,
        n_components=2,
        scaling="dimension_sd",
        random_state=7,
    )
    assert isinstance(first, FPCAScoreUncertaintyResult)
    assert first.bootstrap_scores.shape == (20, gaze.n_curves, 2)
    assert first.lower.shape == (gaze.n_curves, 2)
    assert first.median.shape == first.lower.shape
    assert first.upper.shape == first.lower.shape
    assert first.score_se.shape == first.lower.shape
    assert first.assignments.shape == (20, 2)
    assert first.similarities.shape == (20, 2)
    assert first.n_bootstrap == 20
    assert first.n_targets == gaze.n_curves
    assert first.n_components == 2
    assert first.target_source == "training"
    assert np.allclose(first.reference_scores, first.reference.scores[:, :2])
    assert np.all(first.lower <= first.median)
    assert np.all(first.median <= first.upper)
    assert np.all(first.score_se >= 0)
    assert np.all((first.similarities >= 0) & (first.similarities <= 1 + 1e-12))
    assert np.allclose(first.bootstrap_scores, second.bootstrap_scores)


def test_external_targets_are_fixed_and_curve_ids_are_preserved():
    gaze = sample()
    targets = gaze.subset([0, 3, 5])
    result = bootstrap_fpca_score_uncertainty(
        gaze,
        targets=targets,
        n_bootstrap=20,
        n_components=2,
        random_state=3,
    )
    assert result.target_source == "external"
    assert result.target_curve_ids == targets.curve_ids
    assert result.bootstrap_scores.shape == (20, 3, 2)
    assert result.provenance["fpca_score_uncertainty"]["target_curves_fixed"] is True
    assert (
        result.provenance["fpca_score_uncertainty"][
            "includes_future_curve_sampling_variability"
        ]
        is False
    )


def test_participant_basis_resampling_and_tidy_frame():
    gaze = sample()
    result = bootstrap_fpca_score_uncertainty(
        gaze,
        targets=gaze.subset([0, 1, 2, 3]),
        n_bootstrap=20,
        n_components=2,
        scaling="dimension_sd",
        resample_unit="participant",
        participant_column="participant_id",
        random_state=9,
    )
    assert result.resampling_unit == "participant"
    assert result.participant_column == "participant_id"
    frame = fpca_score_uncertainty_frame(result)
    assert len(frame) == 4 * 2
    assert {
        "curve_id",
        "component",
        "reference_score",
        "bootstrap_median",
        "bootstrap_se",
        "lower",
        "upper",
        "median_matched_abs_similarity",
    } == set(frame.columns)


def test_incompatible_targets_fail_explicitly():
    gaze = sample()
    targets = gaze.subset([0, 1])
    shifted_time = replace(targets, time=targets.time + 0.001)
    with pytest.raises(ValueError, match="time grid"):
        bootstrap_fpca_score_uncertainty(
            gaze, targets=shifted_time, n_bootstrap=20, n_components=2
        )

    changed_dimensions = replace(targets, dimension_names=("horizontal", "vertical"))
    with pytest.raises(ValueError, match="dimension names"):
        bootstrap_fpca_score_uncertainty(
            gaze, targets=changed_dimensions, n_bootstrap=20, n_components=2
        )

    changed_coordinates = replace(targets, coordinate_system="degrees")
    with pytest.raises(ValueError, match="coordinate_system"):
        bootstrap_fpca_score_uncertainty(
            gaze, targets=changed_coordinates, n_bootstrap=20, n_components=2
        )

    changed_time_unit = replace(targets, time_unit="seconds")
    with pytest.raises(ValueError, match="time_unit"):
        bootstrap_fpca_score_uncertainty(
            gaze, targets=changed_time_unit, n_bootstrap=20, n_components=2
        )


def test_score_uncertainty_contract_failures_are_explicit():
    gaze = sample()
    empty_targets = gaze.subset([])
    with pytest.raises(ValueError, match="at least one trajectory"):
        bootstrap_fpca_score_uncertainty(
            gaze, targets=empty_targets, n_bootstrap=20, n_components=2
        )
    infinite_training_values = gaze.values.copy()
    infinite_training_values[0, 0, 0] = np.inf
    infinite_training = replace(gaze, values=infinite_training_values)
    with pytest.raises(ValueError, match="training trajectories must contain only finite"):
        bootstrap_fpca_score_uncertainty(
            infinite_training, n_bootstrap=20, n_components=2
        )
    infinite_target_values = gaze.subset([0, 1]).values.copy()
    infinite_target_values[0, 0, 0] = np.inf
    infinite_targets = replace(gaze.subset([0, 1]), values=infinite_target_values)
    with pytest.raises(ValueError, match="targets must contain only finite"):
        bootstrap_fpca_score_uncertainty(
            gaze, targets=infinite_targets, n_bootstrap=20, n_components=2
        )
    with pytest.raises(ValueError):
        bootstrap_fpca_score_uncertainty(gaze, n_bootstrap=19)
    with pytest.raises(TypeError):
        bootstrap_fpca_score_uncertainty(gaze, n_bootstrap=True)
    with pytest.raises(ValueError):
        bootstrap_fpca_score_uncertainty(gaze, n_components=0)
    with pytest.raises(TypeError):
        bootstrap_fpca_score_uncertainty(gaze, n_components=True)
    with pytest.raises(ValueError):
        bootstrap_fpca_score_uncertainty(gaze, level=1.0)
    with pytest.raises(ValueError):
        bootstrap_fpca_score_uncertainty(gaze, resample_unit="participant")
    with pytest.raises(ValueError):
        bootstrap_fpca_score_uncertainty(
            gaze,
            resample_unit="curve",
            participant_column="participant_id",
        )
    with pytest.raises(ValueError):
        bootstrap_fpca_score_uncertainty(gaze, resample_unit="other")


def test_reporting_and_plotting_state_basis_only_scope():
    gaze = sample()
    result = bootstrap_fpca_score_uncertainty(
        gaze,
        targets=gaze.subset([0, 1, 2]),
        n_bootstrap=20,
        n_components=2,
        random_state=11,
    )
    text = fpca_score_uncertainty_reporting_text(result)
    assert "basis estimation" in text
    assert "fixed external target" in text
    assert "do not include target measurement error" in text
    assert "full downstream-model uncertainty propagation" in text
    assert plot_fpca_score_uncertainty(result, component=0, max_targets=3) is not None
    with pytest.raises(IndexError):
        plot_fpca_score_uncertainty(result, component=5)
    with pytest.raises(TypeError):
        plot_fpca_score_uncertainty(result, max_targets=True)
    with pytest.raises(ValueError):
        plot_fpca_score_uncertainty(result, max_targets=0)
    plt.close("all")
