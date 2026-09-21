import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from eyetrajectoriespy import (
    ConformalFunctionalAnomalyResult,
    TrajectorySet,
    conformal_fpca_anomaly_frame,
    conformal_fpca_anomaly_reporting_text,
    fit_mfpca,
    plot_conformal_fpca_anomaly,
    simulate_planar_trajectories,
    split_conformal_fpca_anomaly,
)


def partitions():
    gaze = simulate_planar_trajectories(
        n_participants=36,
        trials_per_participant=1,
        n_time=41,
        random_state=151,
    )
    proper = gaze.subset(np.arange(0, 20))
    calibration = gaze.subset(np.arange(20, 30))
    targets = gaze.subset(np.arange(30, 36))
    return proper, calibration, targets


def test_reconstruction_conformal_formula_and_extreme_shape_truth():
    proper, calibration, targets = partitions()
    values = targets.values.copy()
    wave = np.where(np.arange(targets.n_time) % 2 == 0, 1.0, -1.0)
    values[0, :, 0] += 8.0 * wave
    distorted = targets.with_values(values)

    result = split_conformal_fpca_anomaly(
        proper,
        calibration,
        distorted,
        n_components=3,
        scaling="dimension_sd",
        nonconformity="reconstruction_rmse",
        alpha=0.10,
    )
    assert isinstance(result, ConformalFunctionalAnomalyResult)
    assert result.n_calibration == calibration.n_curves
    assert result.n_targets == distorted.n_curves
    assert result.minimum_attainable_p == pytest.approx(1 / 11)
    expected = (
        1
        + np.sum(
            result.calibration_scores[None, :] >= result.target_scores[:, None],
            axis=1,
        )
    ) / 11
    assert np.allclose(result.p_values, expected)
    assert np.allclose(
        result.p_values * (result.n_calibration + 1),
        np.round(result.p_values * (result.n_calibration + 1)),
    )
    assert result.p_values[0] == pytest.approx(result.minimum_attainable_p)
    assert result.review_flags[0]


def test_score_mahalanobis_detects_extreme_in_span_target():
    proper, calibration, targets = partitions()
    reference = fit_mfpca(proper, n_components=3, scaling="dimension_sd")
    extreme_values = reference.mean[None, :, :].copy()
    extreme_values += (
        12.0
        * np.sqrt(reference.explained_variance[0])
        * reference.components[0][None, :, :]
    )
    extreme = TrajectorySet(
        time=proper.time,
        values=extreme_values,
        curve_ids=("external_extreme",),
        dimension_names=proper.dimension_names,
        coordinate_system=proper.coordinate_system,
        time_unit=proper.time_unit,
    )
    result = split_conformal_fpca_anomaly(
        proper,
        calibration,
        extreme,
        n_components=3,
        scaling="dimension_sd",
        nonconformity="score_mahalanobis",
        mahalanobis_covariance="empirical",
        alpha=0.10,
    )
    assert result.p_values[0] == pytest.approx(result.minimum_attainable_p)
    assert result.review_flags[0]
    assert result.mahalanobis_covariance == "empirical"


def test_robust_mahalanobis_is_seeded_and_explicit():
    proper, calibration, targets = partitions()
    first = split_conformal_fpca_anomaly(
        proper,
        calibration,
        targets,
        n_components=2,
        nonconformity="score_mahalanobis",
        mahalanobis_covariance="robust",
        random_state=7,
    )
    second = split_conformal_fpca_anomaly(
        proper,
        calibration,
        targets,
        n_components=2,
        nonconformity="score_mahalanobis",
        mahalanobis_covariance="robust",
        random_state=7,
    )
    assert np.allclose(first.calibration_scores, second.calibration_scores)
    assert np.allclose(first.target_scores, second.target_scores)
    assert np.allclose(first.p_values, second.p_values)


def test_validation_rejects_leakage_incompatibility_and_hidden_choices():
    proper, calibration, targets = partitions()

    overlap = TrajectorySet(
        time=targets.time,
        values=targets.values.copy(),
        curve_ids=(proper.curve_ids[0],) + targets.curve_ids[1:],
        dimension_names=targets.dimension_names,
        metadata=targets.metadata.reset_index(drop=True),
        coordinate_system=targets.coordinate_system,
        time_unit=targets.time_unit,
    )
    with pytest.raises(ValueError, match="disjoint"):
        split_conformal_fpca_anomaly(proper, calibration, overlap)

    shifted_grid = targets.with_values(
        targets.values,
        time=targets.time + 0.001,
    )
    with pytest.raises(ValueError, match="time grid"):
        split_conformal_fpca_anomaly(proper, calibration, shifted_grid)

    with pytest.raises(ValueError, match="requires explicit"):
        split_conformal_fpca_anomaly(
            proper,
            calibration,
            targets,
            nonconformity="score_mahalanobis",
        )
    with pytest.raises(ValueError, match="must be None"):
        split_conformal_fpca_anomaly(
            proper,
            calibration,
            targets,
            nonconformity="reconstruction_rmse",
            mahalanobis_covariance="empirical",
        )
    with pytest.raises(ValueError):
        split_conformal_fpca_anomaly(
            proper,
            calibration,
            targets,
            alpha=1.0,
        )


def test_frame_plot_reporting_and_review_not_exclusion():
    proper, calibration, targets = partitions()
    result = split_conformal_fpca_anomaly(
        proper,
        calibration,
        targets,
        n_components=3,
        alpha=0.20,
    )
    frame = conformal_fpca_anomaly_frame(result)
    assert len(frame) == targets.n_curves
    assert {
        "curve_id",
        "nonconformity_score",
        "conformal_p_value",
        "alpha",
        "review_flag",
        "minimum_attainable_p",
    } == set(frame.columns)

    text = conformal_fpca_anomaly_reporting_text(result)
    assert "not automatic exclusions" in text
    assert "exchangeability" in text
    assert "No calibration-conditional" in text
    assert "FDR guarantee" in text

    assert plot_conformal_fpca_anomaly(result, max_targets=4) is not None
    with pytest.raises(TypeError):
        plot_conformal_fpca_anomaly(result, max_targets=True)
    with pytest.raises(ValueError):
        plot_conformal_fpca_anomaly(result, max_targets=0)
    plt.close("all")

    settings = result.provenance["split_conformal_fpca_anomaly"]
    assert settings["automatic_exclusion"] is False
    assert settings["fdr_control_claimed"] is False
    assert settings["tie_rule"] == "greater_equal_conservative"
