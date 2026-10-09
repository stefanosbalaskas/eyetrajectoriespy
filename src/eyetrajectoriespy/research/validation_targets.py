"""F2 opt-in validation-target accuracy and spatial precision calculations.

Accuracy and precision are calculated exclusively from user-supplied target
coordinates paired with observed validation gaze coordinates, all in degrees
of visual angle. Free-viewing gaze must not be used for absolute accuracy.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

_REQUIRED = (
    "participant_id", "validation_session_id", "target_id",
    "target_x_deg", "target_y_deg", "gaze_x_deg", "gaze_y_deg",
)


def summarize_gaze_validation_targets(
    samples: pd.DataFrame, *,
    evidence_source: str,
) -> pd.DataFrame:
    """Summarize per-session planar-angle target error, precision and loss.

    Gaze missingness is measured from paired target samples; all targets must
    have known finite coordinates. Accuracy is the mean sample-level Euclidean
    angular-plane error; precision is pooled within-target radial RMS of
    deviations from each observed gaze centroid. These are descriptive
    validation measurements, not whole-field 3-D angular calibration.
    """
    if not isinstance(samples, pd.DataFrame):
        raise TypeError("samples must be a DataFrame")
    if not isinstance(evidence_source, str) or not evidence_source.strip():
        raise ValueError("evidence_source must identify the validation recording")
    absent = [field for field in _REQUIRED if field not in samples]
    if absent:
        raise ValueError(f"validation target fields missing: {absent}")
    if samples.empty:
        raise ValueError("validation samples must be nonempty")
    table = samples.copy()
    for key in _REQUIRED[:3]:
        if table[key].isna().any() or (table[key].astype(str).str.strip() == "").any():
            raise ValueError(f"{key} requires nonmissing identifiers")
        table[key] = table[key].astype(str)
    for key in _REQUIRED[3:]:
        values = pd.to_numeric(table[key], errors="coerce")
        raw = table[key]
        if (raw.notna() & values.isna()).any() or np.isinf(values.to_numpy(float)).any():
            raise ValueError(f"{key} requires numeric finite observed values or missing gaze")
        if key.startswith("target_") and values.isna().any():
            raise ValueError(f"{key} may not be missing")
        table[key] = values
    rows = []
    for (participant, session), frame in table.groupby(
        ["participant_id", "validation_session_id"], sort=True
    ):
        expected = len(frame)
        x, y = frame["gaze_x_deg"], frame["gaze_y_deg"]
        valid = x.notna() & y.notna()
        observed = frame.loc[valid]
        missing_fraction = float(1.0 - len(observed) / expected)
        groups = []
        for target, target_rows in frame.groupby("target_id", sort=True):
            target_coordinates = target_rows[["target_x_deg", "target_y_deg"]].drop_duplicates()
            if len(target_coordinates) != 1:
                raise ValueError(
                    f"validation target {target!r} has inconsistent target coordinates"
                )
            valid_rows = target_rows.loc[
                target_rows["gaze_x_deg"].notna() & target_rows["gaze_y_deg"].notna()
            ]
            if len(valid_rows):
                groups.append(valid_rows)
        if groups:
            valid_all = pd.concat(groups)
            dx = valid_all["gaze_x_deg"].to_numpy(float) - valid_all["target_x_deg"].to_numpy(float)
            dy = valid_all["gaze_y_deg"].to_numpy(float) - valid_all["target_y_deg"].to_numpy(float)
            accuracy = float(np.mean(np.hypot(dx, dy)))
        else:
            accuracy = np.nan
        squared_residuals = []
        for valid_rows in groups:
            if len(valid_rows) < 2:
                continue
            points = valid_rows[["gaze_x_deg", "gaze_y_deg"]].to_numpy(float)
            deviations = points - points.mean(axis=0, keepdims=True)
            squared_residuals.extend(np.sum(deviations**2, axis=1))
        precision = float(np.sqrt(np.mean(squared_residuals))) if squared_residuals else np.nan
        rows.append({
            "participant_id": participant,
            "validation_session_id": session,
            "accuracy_deg": accuracy,
            "precision_deg": precision,
            "validation_points": len(groups) if groups else np.nan,
            "data_loss_fraction": missing_fraction,
            "validation_samples_total": int(expected),
            "validation_samples_valid": int(len(observed)),
            "accuracy_calculation": "mean_Euclidean_2D_angular_target_error",
            "precision_calculation": "within_target_radial_RMS",
            "validation_coordinate_unit": "degrees",
            "evidence_source": evidence_source.strip(),
        })
    return pd.DataFrame(rows)
