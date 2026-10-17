"""Experimental measured quality audit; absolute accuracy is never gaze-derived."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping
import numpy as np
import pandas as pd
from eyetrajectoriespy.types import TrajectorySet, IrregularTrajectorySet

@dataclass(frozen=True)
class GazeMeasurementQualityAudit:
    records: pd.DataFrame
    observed_support: pd.DataFrame
    provenance: Mapping[str, Any]
    warnings: tuple[str, ...]

_MEASURED = ("accuracy_deg", "precision_deg", "validation_points", "data_loss_fraction")

def audit_gaze_measurement_quality(
    gaze: TrajectorySet | IrregularTrajectorySet,
    *,
    validation_records: pd.DataFrame | None = None,
    participant_column: str = "participant_id",
    source_description: str | None = None,
) -> GazeMeasurementQualityAudit:
    """Use only externally measured calibration/validation; retain missing values."""
    if not isinstance(gaze, (TrajectorySet, IrregularTrajectorySet)):
        raise TypeError("gaze must be a TrajectorySet or IrregularTrajectorySet")
    md = gaze.metadata.reset_index(drop=True)
    names = md[participant_column].astype(str) if participant_column in md else pd.Series(gaze.curve_ids)
    rows = []
    for i, curve_id in enumerate(gaze.curve_ids):
        v = gaze.values[i]
        total = int(v.size)
        observed = int(np.isfinite(v).sum())
        rows.append({
            "curve_id": str(curve_id),
            "participant_id": str(names.iloc[i]),
            "coordinate_system": gaze.coordinate_system,
            "time_unit": gaze.time_unit,
            "observed_coordinate_values": observed,
            "missing_coordinate_values": total - observed,
            "observed_fraction": observed / total,
        })
    support = pd.DataFrame(rows)
    if validation_records is None:
        records = pd.DataFrame(columns=[participant_column, *_MEASURED, "evidence_source"])
        warning = ("No calibration/validation records; accuracy and precision unmeasured.",)
    else:
        records = validation_records.copy().reset_index(drop=True)
        if participant_column not in records.columns:
            raise ValueError("validation records require participant identifiers")
        if records[participant_column].isna().any():
            raise ValueError("validation participant identifiers missing")
        if "evidence_source" not in records or records["evidence_source"].isna().any() or (
            records["evidence_source"].astype(str).str.strip() == ""
        ).any():
            raise ValueError("quality records require documented evidence_source")
        if not set(records[participant_column].astype(str)).issubset(set(support.participant_id)):
            raise ValueError("unknown validation participants")
        for metric in _MEASURED:
            if metric not in records:
                records[metric] = np.nan
            raw = records[metric]
            parsed = pd.to_numeric(raw, errors="coerce")
            if (raw.notna() & parsed.isna()).any():
                raise ValueError(f"{metric} must be numeric")
            if np.isinf(parsed.to_numpy(float)).any() or (parsed.dropna() < 0).any():
                raise ValueError(f"{metric} must be finite and nonnegative")
            if metric == "data_loss_fraction" and (parsed.dropna() > 1).any():
                raise ValueError("data loss fraction out of range")
            if metric == "validation_points" and (
                (parsed.dropna() < 1) | (parsed.dropna() % 1 != 0)
            ).any():
                raise ValueError("validation points must be positive integers")
            records[metric] = parsed
        warning = ("Externally measured quality; validation targets not independently verified.",)
    return GazeMeasurementQualityAudit(
        records=records, observed_support=support, warnings=warning,
        provenance={"source_description": source_description,
                    "participant_column": participant_column,
                    "absolute_accuracy_inferred_from_gaze": False,
                    "calibration_target_verification": "not_performed",
                    "experimental": True},
    )

def measurement_quality_reporting_frame(audit: GazeMeasurementQualityAudit) -> pd.DataFrame:
    """Distinguish measured external quality, unavailable quality, and sample support."""
    if not isinstance(audit, GazeMeasurementQualityAudit):
        raise TypeError("expected GazeMeasurementQualityAudit")
    rows = []
    for metric in _MEASURED:
        measured = audit.records[metric].dropna() if metric in audit.records else pd.Series(dtype=float)
        rows.append({"metric": metric,
                     "evidence": "measured_external" if len(measured) else "not_available",
                     "n_records": int(len(measured)),
                     "mean": float(measured.mean()) if len(measured) else np.nan,
                     "unit": "degrees" if metric in ("accuracy_deg", "precision_deg")
                             else ("fraction" if metric == "data_loss_fraction" else "points")})
    rows.append({"metric": "observed_coordinate_fraction",
                 "evidence": "sample_support_not_absolute_accuracy",
                 "n_records": len(audit.observed_support),
                 "mean": float(audit.observed_support.observed_fraction.mean()),
                 "unit": "fraction"})
    return pd.DataFrame(rows)
