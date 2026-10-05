import numpy as np
import pandas as pd
import pandas.testing as pdt
import pytest

from eyetrajectoriespy.observation_process import (
    diagnose_observation_process,
    observation_process_data,
    observation_process_frame,
)


def test_time_summary_uses_selected_after_observed_risk_set():
    frame = pd.DataFrame(
        {
            "curve": ["c1"] * 4,
            "time": [0.0, 1.0, 2.0, 3.0],
            "observed": [1, 0, 0, 1],
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
        risk_set="after_observed",
        time_basis=None,
        time_bins=(0.0, 1.5, 3.0),
        association_bins=None,
    )

    assert int(result.global_summary.iloc[0]["risk_candidate_count"]) == 1
    assert int(result.time_summary["candidate_count"].sum()) == 1
    assert int(result.time_summary["observed_count"].sum()) == 0
    assert result.provenance["time_summary_uses_selected_risk_set"] is True


def test_support_summary_retains_curve_regions_with_no_candidate_support():
    frame = pd.DataFrame(
        {
            "curve": ["early", "early", "late", "late"],
            "participant": ["p1", "p1", "p2", "p2"],
            "time": [0.0, 1.0, 3.0, 4.0],
            "observed": [1, 1, 1, 1],
        }
    )
    process = observation_process_data(
        frame,
        curve_column="curve",
        time_column="time",
        observed_column="observed",
        group_column="participant",
    )

    result = diagnose_observation_process(
        process,
        predictors=(),
        time_basis=None,
        time_bins=(0.0, 2.0, 4.0),
        association_bins=None,
    )
    support = result.support_summary

    early_late = support[
        (support["scope"] == "curve")
        & (support["scope_id"] == "early")
        & (support["lower"] >= 2.0 - 1e-12)
    ].iloc[0]
    late_early = support[
        (support["scope"] == "curve")
        & (support["scope_id"] == "late")
        & (support["upper"] <= 2.0 + 1e-12)
    ].iloc[0]

    assert early_late["candidate_count"] == 0
    assert bool(early_late["no_candidate_support"])
    assert np.isnan(early_late["observed_fraction"])
    assert late_early["candidate_count"] == 0
    assert bool(late_early["no_candidate_support"])

    group_rows = support[support["scope"] == "group"]
    assert set(group_rows["scope_id"]) == {"p1", "p2"}
    assert len(group_rows) == 4
    assert result.provenance["support_summary_uses_full_candidate_denominator"] is True


def test_support_summary_flags_zero_and_near_zero_retention():
    frame = pd.DataFrame(
        {
            "curve": ["zero"] * 10 + ["low"] * 10,
            "time": list(np.linspace(0.0, 0.9, 10)) * 2,
            "observed": [0] * 10 + [1] + [0] * 9,
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
        time_basis=None,
        time_bins=(0.0, 0.45, 0.9),
        association_bins=None,
        low_support_threshold=0.20,
    )
    support = result.support_summary

    zero_rows = support[(support["scope"] == "curve") & (support["scope_id"] == "zero")]
    assert zero_rows["zero_observed_support"].all()
    assert zero_rows["near_zero_observed_support"].all()

    low_first = support[
        (support["scope"] == "curve")
        & (support["scope_id"] == "low")
        & (support["lower"] < 0.45)
    ].iloc[0]
    assert low_first["candidate_count"] == 5
    assert low_first["observed_count"] == 1
    assert low_first["observed_fraction"] == pytest.approx(0.20)
    assert not bool(low_first["near_zero_observed_support"])

    assert result.low_support_threshold == pytest.approx(0.20)
    assert result.provenance["low_support_threshold"] == pytest.approx(0.20)


def test_support_table_helper_returns_defensive_copy():
    frame = pd.DataFrame(
        {
            "curve": ["c1", "c1", "c2", "c2"],
            "time": [0.0, 1.0, 0.0, 1.0],
            "observed": [1, 0, 1, 1],
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
        time_basis=None,
        time_bins=(0.0, 0.5, 1.0),
        association_bins=None,
    )

    copied = observation_process_frame(result, table="support")
    original = result.support_summary.copy(deep=True)
    copied.loc[0, "candidate_count"] = 999

    pdt.assert_frame_equal(result.support_summary, original)


def test_low_support_threshold_validation_fails_closed():
    frame = pd.DataFrame(
        {"curve": ["c1", "c1"], "time": [0.0, 1.0], "observed": [1, 0]}
    )
    process = observation_process_data(
        frame,
        curve_column="curve",
        time_column="time",
        observed_column="observed",
    )

    for value in (-0.01, 1.01, np.nan, np.inf):
        with pytest.raises(ValueError, match="low_support_threshold"):
            diagnose_observation_process(
                process,
                predictors=(),
                time_basis=None,
                association_bins=None,
                low_support_threshold=value,
            )


def test_unobserved_raw_coordinate_must_be_nan_not_infinite():
    frame = pd.DataFrame(
        {
            "curve": ["c1", "c1"],
            "time": [0.0, 1.0],
            "observed": [1, 0],
            "x": [0.2, np.inf],
            "y": [0.3, np.nan],
        }
    )

    with pytest.raises(ValueError, match="contains values on unobserved rows"):
        observation_process_data(
            frame,
            curve_column="curve",
            time_column="time",
            observed_column="observed",
            coordinate_columns=("x", "y"),
        )


def test_numeric_standardized_difference_uses_pooled_within_group_sd():
    frame = pd.DataFrame(
        {
            "curve": [f"c{i}" for i in range(4)],
            "time": [0.0] * 4,
            "observed": [1, 1, 0, 0],
            "predictor": [0.0, 2.0, 4.0, 8.0],
        }
    )
    process = observation_process_data(
        frame,
        curve_column="curve",
        time_column="time",
        observed_column="observed",
        candidate_predictors=("predictor",),
    )

    result = diagnose_observation_process(
        process,
        predictors=("predictor",),
        time_basis=None,
        association_bins=None,
    )
    row = result.associations.iloc[0]

    observed = np.array([0.0, 2.0])
    missing = np.array([4.0, 8.0])
    pooled_sd = np.sqrt(
        ((len(observed) - 1) * np.var(observed, ddof=1)
         + (len(missing) - 1) * np.var(missing, ddof=1))
        / (len(observed) + len(missing) - 2)
    )
    expected = (observed.mean() - missing.mean()) / pooled_sd

    assert row["standardized_mean_difference"] == pytest.approx(expected)
