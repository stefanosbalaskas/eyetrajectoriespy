import numpy as np
import pandas as pd
import pandas.testing as pdt
import pytest

from eyetrajectoriespy.observation_process import (
    ObservationProcessData,
    ObservationProcessDiagnosticResult,
    diagnose_observation_process,
    observation_process_data,
    observation_process_frame,
    observation_process_reporting_text,
)


def _frame():
    return pd.DataFrame(
        {
            "curve": ["c1"] * 6 + ["c2"] * 6,
            "participant": ["p1"] * 6 + ["p2"] * 6,
            "time": list(range(6)) * 2,
            "observed": [1, 1, 0, 0, 1, 1, 1, 0, 1, 0, 1, 0],
            "design": [0.0, 0.2, 0.4, 0.6, 0.8, 1.0] * 2,
            "condition": ["A"] * 6 + ["B"] * 6,
            "x": [0.0, 1.0, np.nan, np.nan, 4.0, 5.0, 10.0, np.nan, 12.0, np.nan, 14.0, np.nan],
            "y": [0.0, 0.0, np.nan, np.nan, 0.0, 0.0, 0.0, np.nan, 0.0, np.nan, 0.0, np.nan],
        }
    )


def _process():
    return observation_process_data(
        _frame(),
        curve_column="curve",
        time_column="time",
        observed_column="observed",
        group_column="participant",
        candidate_predictors=("design", "condition"),
        predictor_sources={"design": "design", "condition": "design"},
        coordinate_columns=("x", "y"),
        time_unit="s",
        coordinate_system="normalized",
    )


def test_explicit_denominator_contract_and_provenance():
    process = _process()

    assert isinstance(process, ObservationProcessData)
    assert process.n_candidates == 12
    assert process.n_observed == 7
    assert process.n_missing == 5
    assert process.observed_fraction == pytest.approx(7 / 12)
    assert process.curve_ids == ("c1", "c2")
    assert process.provenance["denominator_source"] == "explicit_candidate_rows"
    assert process.provenance["denominator_reconstructed_from_retained_timestamps"] is False
    assert process.provenance["nominal_sampling_rate_used_to_infer_missing_rows"] is False
    assert process.provenance["current_missing_gaze_imputed"] is False


def test_input_frame_is_not_modified():
    frame = _frame()
    original = frame.copy(deep=True)

    observation_process_data(
        frame,
        curve_column="curve",
        time_column="time",
        observed_column="observed",
        candidate_predictors=("design",),
    )

    pdt.assert_frame_equal(frame, original)


def test_duplicate_candidate_rows_fail_closed():
    frame = _frame()
    frame.loc[1, "time"] = frame.loc[0, "time"]

    with pytest.raises(ValueError, match="unique within curve/time"):
        observation_process_data(
            frame,
            curve_column="curve",
            time_column="time",
            observed_column="observed",
        )


def test_nonmonotone_candidate_schedule_fails_closed():
    frame = _frame()
    frame.loc[1, "time"] = 2.5
    frame.loc[2, "time"] = 2.0

    with pytest.raises(ValueError, match="strictly increasing"):
        observation_process_data(
            frame,
            curve_column="curve",
            time_column="time",
            observed_column="observed",
        )


def test_nonbinary_observation_indicator_fails_closed():
    frame = _frame()
    frame.loc[0, "observed"] = 2

    with pytest.raises(ValueError, match="binary"):
        observation_process_data(
            frame,
            curve_column="curve",
            time_column="time",
            observed_column="observed",
        )


def test_candidate_predictor_must_exist_for_missing_rows():
    frame = _frame()
    frame.loc[2, "design"] = np.nan

    with pytest.raises(ValueError, match="unavailable on some candidate rows"):
        observation_process_data(
            frame,
            curve_column="curve",
            time_column="time",
            observed_column="observed",
            candidate_predictors=("design",),
        )


def test_current_missing_gaze_cannot_be_smuggled_in_as_raw_coordinate():
    frame = _frame()
    frame.loc[2, "x"] = 99.0

    with pytest.raises(ValueError, match="contains values on unobserved rows"):
        observation_process_data(
            frame,
            curve_column="curve",
            time_column="time",
            observed_column="observed",
            coordinate_columns=("x", "y"),
        )


def test_curve_and_group_summaries_are_exact():
    result = diagnose_observation_process(
        _process(),
        predictors=(),
        time_basis=None,
        association_bins=None,
    )

    assert isinstance(result, ObservationProcessDiagnosticResult)
    global_row = result.global_summary.iloc[0]
    assert global_row["candidate_count"] == 12
    assert global_row["observed_count"] == 7
    assert global_row["missing_count"] == 5
    assert global_row["curve_count"] == 2
    assert global_row["group_count"] == 2

    c1 = result.curve_summary.set_index("curve_id").loc["c1"]
    assert c1["candidate_count"] == 6
    assert c1["observed_count"] == 4
    assert c1["missing_count"] == 2
    assert c1["longest_observed_run"] == 2
    assert c1["longest_missing_run"] == 2
    assert c1["candidate_median_interval"] == pytest.approx(1.0)
    assert c1["observed_median_interval"] == pytest.approx(1.0)

    groups = result.group_summary.set_index("group_id")
    assert groups.loc["p1", "candidate_count"] == 6
    assert groups.loc["p2", "missing_count"] == 3


def test_time_block_loss_has_negative_descriptive_time_association():
    frame = pd.DataFrame(
        {
            "curve": np.repeat(["c1", "c2", "c3"], 10),
            "time": np.tile(np.arange(10, dtype=float), 3),
            "observed": np.tile([1, 1, 1, 1, 1, 1, 0, 0, 0, 0], 3),
        }
    )
    process = observation_process_data(
        frame,
        curve_column="curve",
        time_column="time",
        observed_column="observed",
    )

    result = diagnose_observation_process(
        process,
        predictors=(),
        time_basis="linear",
        time_bins=(0.0, 3.0, 6.0, 9.0),
        association_bins=None,
    )

    row = result.associations.set_index("predictor").loc["time"]
    assert row["status_code"] == "ok"
    assert row["spearman_rho"] < -0.7
    assert result.time_summary.iloc[0]["observed_fraction"] > result.time_summary.iloc[-1]["observed_fraction"]


def test_numeric_and_categorical_candidate_predictors_are_described_without_p_values():
    result = diagnose_observation_process(
        _process(),
        time_basis=None,
        association_bins=3,
    )

    associations = result.associations.set_index("predictor")
    assert associations.loc["design", "predictor_type"] == "numeric"
    assert associations.loc["condition", "predictor_type"] == "categorical"
    assert associations.loc["condition", "observed_fraction_range"] > 0
    assert "p_value" not in result.associations.columns
    assert result.provenance["iid_sample_level_inference_performed"] is False
    assert result.provenance["p_values_reported"] is False


def test_history_uses_only_information_available_before_current_candidate():
    process = _process()
    result = diagnose_observation_process(
        process,
        predictors=(),
        history_predictors=(
            "previous_observed_x",
            "previous_observed_speed",
            "time_since_last_observed",
            "preceding_observed_run_length",
            "preceding_missing_run_length",
        ),
        time_basis=None,
        association_bins=None,
    )

    candidates = result.candidate_frame
    c1 = candidates[candidates["curve"] == "c1"].reset_index(drop=True)

    assert np.isnan(c1.loc[0, "previous_observed_x"])
    assert c1.loc[1, "previous_observed_x"] == pytest.approx(0.0)
    assert c1.loc[2, "previous_observed_x"] == pytest.approx(1.0)
    assert c1.loc[2, "previous_observed_speed"] == pytest.approx(1.0)
    assert c1.loc[2, "time_since_last_observed"] == pytest.approx(1.0)
    assert c1.loc[3, "time_since_last_observed"] == pytest.approx(2.0)
    assert c1.loc[2, "preceding_observed_run_length"] == 2
    assert c1.loc[3, "preceding_missing_run_length"] == 1

    # The row at t=4 is observed at x=4, but its predictor must still describe
    # the last retained gaze before t=4 (x=1), not the current value x=4.
    assert c1.loc[4, "previous_observed_x"] == pytest.approx(1.0)
    assert result.provenance["history_uses_past_information_only"] is True
    assert result.provenance["current_missing_gaze_imputed"] is False


def test_eccentricity_requires_explicit_reference_definition():
    result = diagnose_observation_process(
        _process(),
        predictors=(),
        history_predictors=("previous_observed_eccentricity",),
        time_basis=None,
        association_bins=None,
    )

    assert result.associations.empty
    failure = result.failures.iloc[0]
    assert failure["item"] == "previous_observed_eccentricity"
    assert failure["status_code"] == "reference_definition_required"


def test_eccentricity_history_uses_declared_reference():
    result = diagnose_observation_process(
        _process(),
        predictors=(),
        history_predictors=("previous_observed_eccentricity",),
        eccentricity_reference=(0.0, 0.0),
        time_basis=None,
        association_bins=None,
    )

    c1 = result.candidate_frame[result.candidate_frame["curve"] == "c1"].reset_index(drop=True)
    assert c1.loc[2, "previous_observed_eccentricity"] == pytest.approx(1.0)
    assert result.provenance["eccentricity_reference"] == [0.0, 0.0]


def test_missing_coordinate_history_is_retained_as_explicit_failure():
    frame = _frame().drop(columns=["x", "y"])
    process = observation_process_data(
        frame,
        curve_column="curve",
        time_column="time",
        observed_column="observed",
    )

    result = diagnose_observation_process(
        process,
        predictors=(),
        history_predictors=("previous_observed_speed",),
        time_basis=None,
        association_bins=None,
    )

    assert result.failures.iloc[0]["status_code"] == "history_coordinates_unavailable"


def test_after_observed_risk_set_is_explicit_and_reproducible():
    process = _process()

    first = diagnose_observation_process(
        process,
        predictors=(),
        history_predictors=("time_since_last_observed",),
        risk_set="after_observed",
        time_basis=None,
        association_bins=None,
    )
    second = diagnose_observation_process(
        process,
        predictors=(),
        history_predictors=("time_since_last_observed",),
        risk_set="after_observed",
        time_basis=None,
        association_bins=None,
    )

    assert first.global_summary.iloc[0]["risk_candidate_count"] == 5
    pdt.assert_frame_equal(first.associations, second.associations)
    assert first.provenance["risk_set"] == "after_observed"


def test_all_observed_outcome_retains_nonestimable_association_status():
    frame = pd.DataFrame(
        {
            "curve": ["c1", "c1", "c1", "c2", "c2", "c2"],
            "time": [0, 1, 2, 0, 1, 2],
            "observed": [1, 1, 1, 1, 1, 1],
            "design": [0, 1, 2, 0, 1, 2],
        }
    )
    process = observation_process_data(
        frame,
        curve_column="curve",
        time_column="time",
        observed_column="observed",
        candidate_predictors=("design",),
    )

    result = diagnose_observation_process(
        process,
        time_basis="linear",
        association_bins=None,
    )

    assert set(result.associations["status_code"]) == {"outcome_constant"}
    assert result.global_summary.iloc[0]["missing_count"] == 0


def test_frame_helper_returns_defensive_copy():
    result = diagnose_observation_process(
        _process(),
        predictors=(),
        time_basis=None,
        association_bins=None,
    )

    copied = observation_process_frame(result, table="curves")
    copied.loc[0, "candidate_count"] = 999

    assert result.curve_summary.loc[0, "candidate_count"] == 6
    with pytest.raises(ValueError, match="table must be one of"):
        observation_process_frame(result, table="unknown")


def test_reporting_text_states_descriptive_scope_and_no_correction():
    result = diagnose_observation_process(
        _process(),
        history_predictors=("previous_observed_speed",),
        time_bins=3,
        association_bins=3,
    )

    text = observation_process_reporting_text(result)

    assert "explicit denominator of 12 candidate samples" in text
    assert "5 samples (41.7%) were not retained" in text
    assert "descriptive observation-process associations only" in text
    assert "MAR/MNAR" in text
    assert "inverse-probability/intensity correction" in text
    assert result.provenance["inverse_probability_weighting_performed"] is False
    assert result.provenance["inverse_intensity_correction_performed"] is False
    assert result.provenance["sparse_estimator_modified"] is False
