import numpy as np
import pytest

from eyetrajectoriespy import (
    compare_registered_unregistered_fpca,
    fit_phase_fpca,
    phase_landmark_frame,
    phase_trajectory_set,
    register_to_landmarks,
    registration_sensitivity_frame,
    simulate_planar_trajectories,
)


def registered_sample():
    gaze = simulate_planar_trajectories(
        n_participants=8,
        trials_per_participant=2,
        n_time=61,
        duration=2.0,
        random_state=12,
    )
    observed = np.linspace(0.75, 1.25, gaze.n_curves)[:, None]
    result = register_to_landmarks(
        gaze,
        observed,
        reference_landmarks=np.array([1.0]),
    )
    return gaze, result


def test_phase_trajectory_set_displacement_and_warping():
    gaze, registration = registered_sample()
    displacement = phase_trajectory_set(registration, representation="displacement")
    warping = phase_trajectory_set(registration, representation="warping")
    assert displacement.values.shape == (gaze.n_curves, gaze.n_time, 1)
    assert displacement.dimension_names == ("phase_displacement",)
    assert warping.dimension_names == ("warping_time",)
    assert np.allclose(
        warping.values[:, :, 0] - gaze.time[None, :],
        displacement.values[:, :, 0],
    )
    with pytest.raises(ValueError):
        phase_trajectory_set(registration, representation="bad")


def test_phase_fpca_captures_warping_variation():
    _, registration = registered_sample()
    fit = fit_phase_fpca(registration, n_components=2)
    assert fit.n_components == 2
    assert fit.dimension_names == ("phase_displacement",)
    assert np.isfinite(fit.scores).all()


def test_registration_sensitivity_identity_is_maximally_similar():
    gaze = simulate_planar_trajectories(
        n_participants=6,
        trials_per_participant=2,
        n_time=51,
        duration=2.0,
        random_state=4,
    )
    observed = np.full((gaze.n_curves, 1), 1.0)
    registration = register_to_landmarks(
        gaze,
        observed,
        reference_landmarks=np.array([1.0]),
    )
    sensitivity = compare_registered_unregistered_fpca(
        registration,
        n_components=3,
        scaling="dimension_sd",
    )
    assert np.allclose(np.abs(sensitivity.signed_component_similarity), 1.0, atol=1e-7)
    assert np.allclose(np.abs(sensitivity.score_correlations), 1.0, atol=1e-7)
    frame = registration_sensitivity_frame(sensitivity)
    assert len(frame) == 3


def test_registration_sensitivity_returns_finite_comparison():
    _, registration = registered_sample()
    sensitivity = compare_registered_unregistered_fpca(
        registration,
        n_components=3,
        scaling="dimension_sd",
    )
    frame = registration_sensitivity_frame(sensitivity)
    assert np.all((frame["absolute_component_similarity"] >= 0) & (frame["absolute_component_similarity"] <= 1))
    assert np.all(np.isfinite(frame["score_correlation"]))


def test_phase_landmark_frame_retains_curve_level_timing():
    gaze, registration = registered_sample()
    frame = phase_landmark_frame(registration)
    assert len(frame) == gaze.n_curves
    assert set(frame.columns) == {
        "curve_id",
        "landmark",
        "observed_time",
        "reference_time",
        "timing_deviation",
    }
    assert frame["timing_deviation"].min() < 0
    assert frame["timing_deviation"].max() > 0


def test_registration_sensitivity_contract():
    _, registration = registered_sample()
    with pytest.raises(ValueError):
        compare_registered_unregistered_fpca(registration, n_components=0)
