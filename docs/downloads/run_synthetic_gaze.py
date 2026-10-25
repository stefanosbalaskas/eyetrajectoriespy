"""Reproducible small teaching fixture for eyetrajectoriespy 1.2.0.

Runs one descriptive common-grid planar FPCA demonstration. Not a statistical
power study, confidence-band calibration or instrument validation exercise.

Usage:
    python -m pip install eyetrajectoriespy==1.2.0 pandas
    python run_synthetic_gaze.py
"""
from pathlib import Path

import pandas as pd
from eyetrajectoriespy import (
    fit_mfpca,
    from_long_dataframe,
    summarise_trajectory_set,
)

DATA_PATH = Path(__file__).with_name("synthetic-gaze-common-grid.csv")


def main() -> None:
    frame = pd.read_csv(DATA_PATH)
    required = {"participant_id", "trial_id", "condition", "time_s", "x", "y"}
    if not required.issubset(frame.columns):
        raise ValueError("The teaching CSV does not contain the declared schema.")
    if frame[["x", "y", "time_s"]].isna().any().any():
        raise ValueError("Unexpected missing values in a complete-grid teaching fixture.")
    if not frame[["x", "y"]].ge(0).all().all() or not frame[["x", "y"]].le(1).all().all():
        raise ValueError("Coordinates must remain normalized in [0,1].")
    times_per_curve = frame.groupby(["participant_id", "trial_id"])["time_s"].nunique()
    if len(times_per_curve) != 12 or not times_per_curve.eq(41).all():
        raise ValueError("Fixture must contain 12 curves with 41 distinct timestamps.")
    reference_grid = frame.loc[frame["participant_id"] == 1, "time_s"].to_numpy()
    for (_, _), group in frame.groupby(["participant_id", "trial_id"], sort=True):
        if not (group["time_s"].to_numpy() == reference_grid).all():
            raise ValueError("Expected identical ordered observation grids across curves.")

    gaze = from_long_dataframe(
        frame,
        curve_columns=["participant_id", "trial_id"],
        time_column="time_s",
        value_columns=["x", "y"],
        metadata_columns=["condition"],
        coordinate_system="normalized",
        time_unit="s",
    )
    print("Input summary:", summarise_trajectory_set(gaze))
    fit = fit_mfpca(gaze, n_components=2, scaling="dimension_sd")
    print("Descriptive synthetic retained variance:", fit.explained_variance_ratio)
    print("PASS: 1.2.0 synthetic teaching fixture (no calibration claim)")


if __name__ == "__main__":
    main()
