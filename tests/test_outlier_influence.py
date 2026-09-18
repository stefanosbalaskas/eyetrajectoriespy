import numpy as np
import pytest

from eyetrajectoriespy import (
    diagnose_fpca_outliers,
    fit_mfpca,
    leave_one_group_out_fpca_influence,
    simulate_planar_trajectories,
)


def atypical_sample():
    gaze = simulate_planar_trajectories(
        n_participants=16,
        trials_per_participant=3,
        n_time=61,
        duration=2.0,
        random_state=33,
    )
    values = gaze.values.copy()
    u = gaze.time / gaze.time[-1]
    values[-1, :, 0] = np.clip(0.10 + 0.80 * np.sin(np.pi * u) ** 2, 0, 1)
    values[-1, :, 1] = np.clip(0.90 - 0.70 * u, 0, 1)
    return gaze.with_values(
        values,
        provenance_update={"synthetic_atypical_curve": gaze.curve_ids[-1]},
    )


def test_fpca_outlier_diagnostics_flag_injected_atypical_curve_for_review():
    gaze = atypical_sample()
    fit = fit_mfpca(gaze, n_components=4, scaling="dimension_sd")
    result = diagnose_fpca_outliers(
        fit,
        gaze,
        n_components=4,
        score_covariance="robust",
        random_state=0,
    )
    assert len(result.diagnostics) == gaze.n_curves
    assert bool(result.diagnostics.iloc[-1]["review_flag"])
    assert bool(result.diagnostics.iloc[-1]["score_flag"])
    assert "scientific_warning" in result.provenance


def test_outlier_diagnostics_are_deterministic():
    gaze = atypical_sample()
    fit = fit_mfpca(gaze, n_components=4, scaling="dimension_sd")
    a = diagnose_fpca_outliers(fit, gaze, n_components=4, random_state=19)
    b = diagnose_fpca_outliers(fit, gaze, n_components=4, random_state=19)
    assert np.allclose(
        a.diagnostics["score_mahalanobis_sq"],
        b.diagnostics["score_mahalanobis_sq"],
    )
    assert np.array_equal(a.diagnostics["review_flag"], b.diagnostics["review_flag"])


def test_participant_level_influence_identifies_injected_participant():
    gaze = atypical_sample()
    result = leave_one_group_out_fpca_influence(
        gaze,
        group_column="participant_id",
        n_components=3,
        scaling="dimension_sd",
    )
    ranked = result.summary.sort_values("influence_score", ascending=False)
    assert ranked.iloc[0]["group"] == "P016"
    assert len(result.components) == 16 * 3


def test_curve_level_influence_has_one_row_per_curve():
    gaze = simulate_planar_trajectories(
        n_participants=4,
        trials_per_participant=2,
        n_time=31,
        random_state=5,
    )
    result = leave_one_group_out_fpca_influence(
        gaze,
        n_components=2,
        scaling="dimension_sd",
    )
    assert len(result.summary) == gaze.n_curves
    assert set(result.summary["group"]) == set(gaze.curve_ids)


def test_outlier_and_influence_contract_errors():
    gaze = atypical_sample()
    fit = fit_mfpca(gaze, n_components=4, scaling="dimension_sd")
    with pytest.raises(ValueError):
        diagnose_fpca_outliers(fit, gaze, reconstruction_z_threshold=0)
    with pytest.raises(ValueError):
        diagnose_fpca_outliers(fit, gaze, score_alpha=1)
    with pytest.raises(ValueError):
        diagnose_fpca_outliers(fit, gaze, score_covariance="mystery")
    with pytest.raises(ValueError):
        leave_one_group_out_fpca_influence(gaze, group_column="missing")
    with pytest.raises(TypeError):
        leave_one_group_out_fpca_influence(gaze, n_components=True)
