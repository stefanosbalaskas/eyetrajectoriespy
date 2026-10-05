import numpy as np
import pandas as pd
import pytest

from eyetrajectoriespy.observation_process import (
    ObservationProcessData,
    ObservationProcessDiagnosticsResult,
    diagnose_observation_process,
    observation_process_data,
    observation_process_history_frame,
    observation_process_reporting_text,
)


def _small_frame():
    return pd.DataFrame(
        {
            "curve_id": ["c1"] * 4 + ["c2"] * 4,
            "participant": ["p1"] * 8,
            "time": [0.0, 1.0, 2.0, 3.0] * 2,
            "observed": [1, 1, 0, 0, 1, 0, 1, 1],
            "external": [-1.0, -0.5, 0.0, 0.5, -0.8, -0.2, 0.4, 0.9],
        }
    )


def test_explicit_denominator_and_curve_group_accounting_are_exact():
    process = observation_process_data(
        _small_frame(),
        curve_column="curve_id",
        time_column="time",
        observed_column="observed",
        group_column="participant",
        predictor_kinds={"external": "externally_supplied"},
        provenance={"source": "unit_test_candidate_schedule"},
    )
    result = diagnose_observation_process(
        process,
        time_bins=[0.0, 2.0, 4.0],
        predictors=("external",),
    )

    assert isinstance(process, ObservationProcessData)
    assert isinstance(result, ObservationProcessDiagnosticsResult)
    assert result.denominator_rows == 8
    assert result.observed_rows == 5
    assert result.missing_rows == 3
    assert result.missing_fraction == pytest.approx(3 / 8)
    assert result.status_code == "ok"

    curves = result.curve_summary.set_index("curve_id")
    assert curves.loc["c1", "longest_observed_run"] == 2
    assert curves.loc["c1", "longest_missing_run"] == 2
    assert curves.loc["c2", "longest_observed_run"] == 2
    assert curves.loc["c2", "longest_missing_run"] == 1

    assert result.group_summary is not None
    group = result.group_summary.iloc[0]
    assert group["participant"] == "p1"
    assert group["n_curves"] == 2
    assert group["n_candidates"] == 8
    assert group["n_observed"] == 5
    assert "longest_missing_run" not in result.group_summary.columns
    assert "candidate_dt_median" not in result.group_summary.columns
    assert result.provenance["group_summary_contains_sequence_run_metrics"] is False

    first_bin = result.time_summary.iloc[0]
    second_bin = result.time_summary.iloc[1]
    assert first_bin["n_candidates"] == 4
    assert first_bin["n_observed"] == 3
    assert first_bin["observed_fraction"] == pytest.approx(0.75)
    assert second_bin["n_candidates"] == 4
    assert second_bin["n_observed"] == 2
    assert second_bin["observed_fraction"] == pytest.approx(0.50)


def test_denominator_validation_rejects_nonbinary_duplicates_and_missing_predictor():
    frame = _small_frame()
    bad_binary = frame.copy()
    bad_binary.loc[0, "observed"] = 2
    with pytest.raises(ValueError, match="bool/0/1"):
        observation_process_data(
            bad_binary,
            curve_column="curve_id",
            time_column="time",
            observed_column="observed",
        )

    duplicated = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="unique by curve and time"):
        observation_process_data(
            duplicated,
            curve_column="curve_id",
            time_column="time",
            observed_column="observed",
        )

    missing_predictor = frame.copy()
    missing_predictor.loc[2, "external"] = np.nan
    with pytest.raises(ValueError, match="must be finite on every candidate row"):
        observation_process_data(
            missing_predictor,
            curve_column="curve_id",
            time_column="time",
            observed_column="observed",
            predictor_kinds={"external": "externally_supplied"},
        )


def test_nonmonotone_candidate_schedule_fails_closed():
    frame = _small_frame()
    frame.loc[1, "time"] = 2.5
    frame.loc[2, "time"] = 1.5
    with pytest.raises(ValueError, match="strictly increasing"):
        observation_process_data(
            frame,
            curve_column="curve_id",
            time_column="time",
            observed_column="observed",
        )


def test_descriptive_logistic_recovers_direction_without_iid_inference():
    rng = np.random.default_rng(166)
    rows = []
    for curve in range(12):
        predictor = np.linspace(-2.0, 2.0, 24)
        probabilities = 1.0 / (1.0 + np.exp(-(-0.2 + 1.1 * predictor)))
        observed = rng.random(predictor.size) < probabilities
        for index, (value, kept) in enumerate(zip(predictor, observed, strict=True)):
            rows.append(
                {
                    "curve_id": f"c{curve:02d}",
                    "time": float(index),
                    "observed": bool(kept),
                    "availability_score": float(value),
                }
            )
    process = observation_process_data(
        pd.DataFrame(rows),
        curve_column="curve_id",
        time_column="time",
        observed_column="observed",
        predictor_kinds={"availability_score": "externally_supplied"},
    )
    result = diagnose_observation_process(
        process,
        predictors=("availability_score",),
        include_linear_time_association=False,
        time_bins=6,
    )
    row = result.predictor_summary.iloc[0]

    assert row["predictor"] == "availability_score"
    assert row["status_code"] == "ok"
    assert row["standardized_coefficient"] > 0.5
    assert row["odds_ratio_per_sd"] > 1.0
    assert row["probability_at_plus_1sd"] > row["probability_at_minus_1sd"]
    assert result.provenance["iid_standard_errors_reported"] is False
    assert result.provenance["p_values_reported"] is False
    assert result.provenance["causal_interpretation_supported"] is False
    assert result.provenance["mar_mnar_classification_supported"] is False


def test_complete_separation_is_retained_as_status_not_false_precision():
    frame = pd.DataFrame(
        {
            "curve_id": ["c1"] * 8,
            "time": np.arange(8, dtype=float),
            "observed": [0, 0, 0, 0, 1, 1, 1, 1],
            "external": np.arange(8, dtype=float),
        }
    )
    process = observation_process_data(
        frame,
        curve_column="curve_id",
        time_column="time",
        observed_column="observed",
        predictor_kinds={"external": "externally_supplied"},
    )
    result = diagnose_observation_process(
        process,
        predictors=("external",),
        include_linear_time_association=False,
        time_bins=2,
    )

    row = result.predictor_summary.iloc[0]
    assert row["status_code"] == "complete_separation"
    assert np.isnan(row["standardized_coefficient"])
    assert np.isnan(row["odds_ratio_per_sd"])


def test_history_uses_only_prior_observed_gaze_and_ignores_missing_row_coordinates():
    frame = pd.DataFrame(
        {
            "curve_id": ["c1"] * 5,
            "time": [0.0, 1.0, 2.0, 3.0, 4.0],
            "observed": [1, 1, 0, 1, 0],
            "x": [0.0, 1.0, 99.0, 3.0, 88.0],
            "y": [0.0, 0.0, 99.0, 0.0, 88.0],
        }
    )
    process = observation_process_data(
        frame,
        curve_column="curve_id",
        time_column="time",
        observed_column="observed",
    )
    history = observation_process_history_frame(
        process,
        x_column="x",
        y_column="y",
        reference_center=(0.0, 0.0),
    )

    assert np.isnan(history.loc[0, "previous_observed_x"])
    assert history.loc[1, "previous_observed_x"] == pytest.approx(0.0)
    assert history.loc[2, "previous_observed_x"] == pytest.approx(1.0)
    assert history.loc[3, "previous_observed_x"] == pytest.approx(1.0)
    assert history.loc[4, "previous_observed_x"] == pytest.approx(3.0)
    assert history.loc[3, "previous_observed_x"] != 99.0
    assert history.loc[4, "previous_observed_x"] != 88.0

    assert np.isnan(history.loc[1, "previous_observed_speed"])
    assert history.loc[2, "previous_observed_speed"] == pytest.approx(1.0)
    assert history.loc[3, "previous_observed_speed"] == pytest.approx(1.0)
    assert history.loc[4, "previous_observed_speed"] == pytest.approx(1.0)
    assert history.loc[3, "time_since_last_observed"] == pytest.approx(2.0)
    assert history.loc[3, "preceding_observed_run_length"] == 0
    assert history.loc[3, "preceding_missing_run_length"] == 1
    assert history.loc[4, "previous_observed_eccentricity"] == pytest.approx(3.0)


def test_history_diagnostics_retain_ineligible_early_rows():
    frame = pd.DataFrame(
        {
            "curve_id": ["c1"] * 6 + ["c2"] * 6,
            "time": list(np.arange(6, dtype=float)) * 2,
            "observed": [1, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1],
            "x": [0, 1, np.nan, 3, 4, np.nan, 0, np.nan, 2, 3, np.nan, 5],
            "y": [0, 0, np.nan, 0, 0, np.nan, 1, np.nan, 1, 1, np.nan, 1],
        }
    )
    process = observation_process_data(
        frame,
        curve_column="curve_id",
        time_column="time",
        observed_column="observed",
    )
    result = diagnose_observation_process(
        process,
        time_bins=3,
        include_linear_time_association=False,
        history_predictors=("previous_observed_speed", "time_since_last_observed"),
        x_column="x",
        y_column="y",
    )

    summary = result.predictor_summary.set_index("predictor")
    assert summary.loc["previous_observed_speed", "n_excluded"] > 0
    assert summary.loc["time_since_last_observed", "n_excluded"] > 0
    assert result.provenance["history_uses_past_information_only"] is True
    assert result.provenance["missing_gaze_imputation_performed"] is False


def test_eccentricity_history_requires_explicit_reference_center():
    frame = pd.DataFrame(
        {
            "curve_id": ["c1"] * 4,
            "time": [0.0, 1.0, 2.0, 3.0],
            "observed": [1, 1, 0, 1],
            "x": [0.0, 1.0, np.nan, 2.0],
            "y": [0.0, 0.0, np.nan, 0.0],
        }
    )
    process = observation_process_data(
        frame,
        curve_column="curve_id",
        time_column="time",
        observed_column="observed",
    )
    with pytest.raises(ValueError, match="explicit reference_center"):
        diagnose_observation_process(
            process,
            time_bins=2,
            include_linear_time_association=False,
            history_predictors=("previous_observed_eccentricity",),
            x_column="x",
            y_column="y",
        )


def test_all_observed_is_described_but_association_inference_is_not_fabricated():
    frame = pd.DataFrame(
        {
            "curve_id": ["c1"] * 5,
            "time": np.arange(5, dtype=float),
            "observed": [1] * 5,
        }
    )
    process = observation_process_data(
        frame,
        curve_column="curve_id",
        time_column="time",
        observed_column="observed",
    )
    result = diagnose_observation_process(process, time_bins=2)

    assert result.status_code == "all_observed"
    assert result.missing_rows == 0
    assert result.predictor_summary.iloc[0]["status_code"] == "outcome_constant"
    text = observation_process_reporting_text(result)
    assert "without iid standard errors or p-values" in text
    assert "do not classify MAR/MNAR" in text
    assert "No missing gaze was imputed" in text
    assert "no inverse-probability or inverse-intensity correction" in text
