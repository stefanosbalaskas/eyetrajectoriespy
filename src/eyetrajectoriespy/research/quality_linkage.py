"""Link independently measured gaze validation evidence to experimental curves.

Requires exact participant, device and session identifiers supplied by the
analyst; neither time proximity nor calibration validity is ever inferred.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from eyetrajectoriespy.types import TrajectorySet, IrregularTrajectorySet
from .measurement_quality import GazeMeasurementQualityAudit


def link_gaze_validation_sessions(
    gaze: TrajectorySet | IrregularTrajectorySet,
    audit: GazeMeasurementQualityAudit,
    *,
    gaze_session_column: str = "session_id",
    gaze_device_column: str = "device_id",
    validation_session_column: str = "validation_session_id",
    validation_device_column: str = "device_id",
    participant_column: str = "participant_id",
    require_all: bool = False,
) -> pd.DataFrame:
    """Exact identity-based linkage without interpolation or time inference.

    A linked record establishes identifier agreement only, not how recently
    a target validation was run, whether drift occurred, or whether a device
    met a measurement-quality threshold.
    """
    if not isinstance(gaze, (TrajectorySet, IrregularTrajectorySet)):
        raise TypeError("gaze must be functional trajectory set")
    if not isinstance(audit, GazeMeasurementQualityAudit):
        raise TypeError("audit must be target/calibration evidence audit")
    md = gaze.metadata.reset_index(drop=True).copy()
    left_cols = [participant_column, gaze_session_column, gaze_device_column]
    right_cols = [participant_column, validation_session_column, validation_device_column]
    for col in left_cols:
        if col not in md:
            raise ValueError(f"gaze metadata missing exact linkage field {col}")
    validation = audit.records.copy()
    for col in right_cols:
        if col not in validation:
            raise ValueError(f"validation records missing exact linkage field {col}")
    for frame, cols in ((md,left_cols),(validation,right_cols)):
        for col in cols:
            if frame[col].isna().any() or (
                frame[col].astype(str).str.strip() == ""
            ).any():
                raise ValueError(f"{col} cannot be missing in session linkage")
    if len(validation) and validation[right_cols].duplicated().any():
        raise ValueError("validation session/device/participant evidence is ambiguous")
    md["curve_id"] = gaze.curve_ids
    left = md[left_cols+["curve_id"]].copy()
    right = validation.copy().rename(columns={
        validation_session_column: gaze_session_column,
        validation_device_column: gaze_device_column,
    })
    link = left.merge(
        right, how="left", on=left_cols, validate="many_to_one",
        indicator=True, sort=False,
    )
    link["link_status"] = link.pop("_merge").map(
        {"both": "exact_identifier_match", "left_only": "not_linked",
         "right_only": "not_linked"}
    ).astype(str)
    if len(link) != gaze.n_curves:
        raise RuntimeError("session linkage unexpectedly changed curve count")
    if require_all and (link["link_status"] != "exact_identifier_match").any():
        raise ValueError("some gaze trials have no exact validation session/device match")
    link["calibration_time_proximity_verified"] = False
    link["calibration_accuracy_from_free_viewing"] = False
    return link
