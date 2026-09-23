import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from eyetrajectoriespy import (
    TrajectorySet,
    plot_windowed_rqa_sensitivity,
    windowed_rqa_functional_mean_band,
    windowed_rqa_mean_band_reporting_text,
    windowed_rqa_sensitivity,
    windowed_rqa_sensitivity_reporting_text,
)


def _repeated_gaze(n=160):
    time = np.arange(n, dtype=float) * 0.01
    values = []
    participants = []
    curve_ids = []
    for participant_index, participant in enumerate(("A", "B", "C")):
        for trial in range(2):
            phase = 0.22 * participant_index + 0.11 * trial
            signal = (
                np.sin(2 * np.pi * 1.8 * time + phase)
                + 0.15 * np.sin(2 * np.pi * 0.6 * time + 0.5 * phase)
            )
            values.append(signal)
            participants.append(participant)
            curve_ids.append(f"{participant}{trial + 1}")
    return TrajectorySet(
        time=time,
        values=np.asarray(values, dtype=float)[:, :, None],
        curve_ids=tuple(curve_ids),
        dimension_names=("x",),
        metadata=pd.DataFrame({"participant_id": participants}),
        coordinate_system="normalized",
        time_unit="s",
        provenance={"source": "synthetic-repeated"},
    )


def test_sensitivity_quantifies_window_overlap_and_profile_resolution():
    gaze = _repeated_gaze()
    result = windowed_rqa_sensitivity(
        gaze,
        metrics=("recurrence_rate", "determinism"),
        window_step_pairs=((40, 20), (40, 10), (60, 20)),
        radius=0.35,
        theiler_window=2,
        dimensions=("x",),
    )

    assert result.n_specifications == 3
    design = result.design_table.set_index("specification_id")
    assert design.loc["spec_1", "n_windows"] == 7
    assert design.loc["spec_1", "overlap_fraction"] == pytest.approx(0.5)
    assert design.loc["spec_2", "overlap_fraction"] == pytest.approx(0.75)
    assert design.loc["spec_3", "overlap_fraction"] == pytest.approx(40 / 60)
    assert design.loc["spec_1", "profile_grid_spacing_time"] == pytest.approx(0.2)
    assert design.loc["spec_2", "profile_grid_spacing_time"] == pytest.approx(0.1)
    assert design.loc["spec_2", "max_window_memberships"] == 4
    assert design.loc["spec_2", "fraction_analyzed_samples_reused"] > 0
    assert result.provenance["no_automatic_specification_selection"] is True
    assert result.provenance["interpolation_used_for_sensitivity_comparison"] is False


def test_pairwise_sensitivity_uses_exact_shared_centers_without_interpolation():
    gaze = _repeated_gaze()
    result = windowed_rqa_sensitivity(
        gaze,
        metrics=("recurrence_rate",),
        window_step_pairs=((40, 20), (40, 10), (60, 20)),
        radius=0.35,
        dimensions=("x",),
    )

    rows = result.pairwise_table
    same_window = rows[
        (rows["specification_a"] == "spec_1")
        & (rows["specification_b"] == "spec_2")
        & (rows["curve_id"] == "A1")
        & (rows["metric"] == "recurrence_rate")
    ].iloc[0]
    assert same_window["n_common_centers"] == 7
    assert same_window["rmse"] == pytest.approx(0.0)
    assert same_window["mean_absolute_difference"] == pytest.approx(0.0)

    shifted_centers = rows[
        (rows["specification_a"] == "spec_1")
        & (rows["specification_b"] == "spec_3")
        & (rows["curve_id"] == "A1")
        & (rows["metric"] == "recurrence_rate")
    ].iloc[0]
    assert shifted_centers["n_common_centers"] == 0
    assert np.isnan(shifted_centers["rmse"])


def test_sensitivity_rejects_duplicate_resolved_specifications():
    gaze = _repeated_gaze()
    with pytest.raises(ValueError, match="same sample counts"):
        windowed_rqa_sensitivity(
            gaze,
            metrics=("recurrence_rate",),
            window_step_pairs=((40, 20), (40, 20)),
            radius=0.35,
            dimensions=("x",),
        )


def test_sensitivity_does_not_bypass_target_rr_outcome_contract():
    gaze = _repeated_gaze()
    with pytest.raises(ValueError, match="controlled by design"):
        windowed_rqa_sensitivity(
            gaze,
            metrics=("recurrence_rate", "determinism"),
            window_step_pairs=((40, 20), (60, 20)),
            target_recurrence_rate=0.08,
            dimensions=("x",),
        )


def test_participant_level_band_uses_complete_participant_functions():
    gaze = _repeated_gaze()
    result = windowed_rqa_functional_mean_band(
        gaze,
        metrics=("recurrence_rate", "determinism"),
        window=40,
        step=20,
        unit="participant",
        participant_column="participant_id",
        radius=0.35,
        theiler_window=2,
        dimensions=("x",),
        n_multiplier=150,
        random_state=17,
    )

    values = result.functional_rqa.trajectories.values
    participant = gaze.metadata["participant_id"].astype(str).to_numpy()
    participant_means = np.stack(
        [
            np.mean(values[participant == participant_id], axis=0)
            for participant_id in ("A", "B", "C")
        ],
        axis=0,
    )
    expected = np.mean(participant_means, axis=0)

    assert result.band.n_units == 3
    assert result.band.unit_ids == ("A", "B", "C")
    np.testing.assert_allclose(result.band.mean, expected)
    assert result.provenance["window_rows_resampled_as_independent"] is False
    assert result.provenance["whole_function_resampling_contract"] is True
    assert result.provenance["within_function_temporal_dependence_preserved"] is True
    assert result.provenance["within_source_curve_block_bootstrap"] is False


def test_band_unit_contract_fails_closed_for_repeated_design_metadata():
    gaze = _repeated_gaze()
    with pytest.raises(ValueError, match="participant_column"):
        windowed_rqa_functional_mean_band(
            gaze,
            metrics=("recurrence_rate",),
            window=40,
            step=20,
            unit="participant",
            radius=0.35,
            dimensions=("x",),
            n_multiplier=100,
        )
    with pytest.raises(ValueError, match="must be None"):
        windowed_rqa_functional_mean_band(
            gaze,
            metrics=("recurrence_rate",),
            window=40,
            step=20,
            unit="curve",
            participant_column="participant_id",
            radius=0.35,
            dimensions=("x",),
            n_multiplier=100,
        )


def test_sensitivity_plot_and_reporting_keep_dependence_boundaries_visible():
    gaze = _repeated_gaze()
    sensitivity = windowed_rqa_sensitivity(
        gaze,
        metrics=("recurrence_rate",),
        window_step_pairs=((40, 20), (40, 10)),
        radius=0.35,
        dimensions=("x",),
    )
    ax = plot_windowed_rqa_sensitivity(
        sensitivity,
        curve="A1",
        metric="recurrence_rate",
    )
    assert "Window/step sensitivity" in ax.get_title()

    sensitivity_text = windowed_rqa_sensitivity_reporting_text(sensitivity)
    assert "no interpolation" in sensitivity_text
    assert "no automatic selection" in sensitivity_text
    assert "effective independent sample size" in sensitivity_text

    band = windowed_rqa_functional_mean_band(
        gaze,
        metrics=("recurrence_rate",),
        window=40,
        step=20,
        unit="participant",
        participant_column="participant_id",
        radius=0.35,
        dimensions=("x",),
        n_multiplier=100,
        random_state=5,
    )
    band_text = windowed_rqa_mean_band_reporting_text(band)
    assert "not window rows" in band_text
    assert "within-function temporal dependence" in band_text
    assert "block-bootstrap" in band_text
    plt.close("all")
