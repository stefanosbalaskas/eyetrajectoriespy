import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from eyetrajectoriespy import (
    functional_simulation_reporting_text,
    functional_simulation_truth_frame,
    plot_functional_simulation_curve,
    plot_functional_simulation_phase_warps,
    plot_functional_simulation_score_variances,
    simulate_functional_process,
)


def _mean(time):
    time = np.asarray(time, dtype=float)
    return 0.2 + 0.2 * time


def _phi1(time):
    time = np.asarray(time, dtype=float)
    return np.sqrt(2.0) * np.sin(np.pi * time)


def _phi2(time):
    time = np.asarray(time, dtype=float)
    return np.sqrt(2.0) * np.sin(2.0 * np.pi * time)


def _audited_simulation():
    return simulate_functional_process(
        mean=_mean,
        eigenfunctions=(_phi1, _phi2),
        eigenvalues=(1.0, 0.3),
        truth_grid=np.linspace(0.0, 1.0, 81),
        n_participants=8,
        trials_per_participant=2,
        observation_design="irregular",
        samples_per_curve=(7, 10),
        irregular_time_design="center_clustered",
        participant_eigenvalues=(0.20, 0.05),
        trial_eigenvalues=(0.10, 0.02),
        measurement_noise_sd=0.04,
        missingness={"kind": "mcar", "probability": 0.10},
        phase_variation={"kind": "power", "sd": 0.15},
        random_state=821,
    )


def test_functional_simulation_truth_frame_retains_curve_audit():
    result = _audited_simulation()
    frame = functional_simulation_truth_frame(result)

    assert len(frame) == result.observations.n_curves
    assert {
        "curve_id",
        "participant_id",
        "trial_id",
        "n_pre_missing_samples",
        "n_observed_samples",
        "n_missing_by_design",
        "max_phase_displacement",
        "score_total_1",
        "score_curve_1",
        "score_participant_1",
        "score_trial_1",
    } <= set(frame.columns)
    np.testing.assert_array_equal(
        frame["n_pre_missing_samples"].to_numpy()
        - frame["n_missing_by_design"].to_numpy(),
        frame["n_observed_samples"].to_numpy(),
    )
    assert np.max(frame["max_phase_displacement"]) > 0


def test_functional_simulation_reporting_text_is_explicit_about_mechanisms():
    text = functional_simulation_reporting_text(_audited_simulation())

    assert "16 curves" in text
    assert "irregular" in text
    assert "participant-level variances" in text
    assert "trial-level variances" in text
    assert "mcar" in text
    assert "power" in text
    assert "No dense-to-irregular raw-trajectory interpolation" in text
    assert "Exact latent curves" in text


def test_functional_simulation_diagnostic_plots_render_truth_objects():
    result = _audited_simulation()

    ax = plot_functional_simulation_curve(
        result,
        curve=0,
        dimension="value",
        show_pre_missing=True,
    )
    assert "truth audit" in ax.get_title().lower()
    assert len(ax.lines) >= 1
    plt.close(ax.figure)

    ax = plot_functional_simulation_phase_warps(
        result,
        max_curves=6,
    )
    assert "phase warps" in ax.get_title().lower()
    assert len(ax.lines) == 7
    plt.close(ax.figure)

    ax = plot_functional_simulation_score_variances(result)
    assert "variance audit" in ax.get_title().lower()
    assert len(ax.patches) == 12
    plt.close(ax.figure)
