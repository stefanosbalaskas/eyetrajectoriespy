"""F3: narrow Eye-Tracking-BIDS physio adapter, not full BIDS compliance.

Version basis: BEP020/Szinte et al. 2026 and the declared sidecar fields.
Never infers clock alignment, events, calibration accuracy, or missing samples.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Mapping
import numpy as np
import pandas as pd
from eyetrajectoriespy.types import TrajectorySet

_REQUIRED = ("Columns", "SamplingFrequency", "StartTime", "PhysioType",
             "RecordedEye", "SampleCoordinateSystem")
_UNIT_MAP = {"px": "pixels", "pixel": "pixels", "pixels": "pixels",
             "degree": "degrees", "degrees": "degrees", "deg": "degrees",
             "1": "normalized", "normalized": "normalized"}

def validate_eyetracking_metadata(
    metadata: Mapping[str, Any],
    *,
    sampling_tolerance: float = 0.01,
) -> dict[str, Any]:
    """Strict subset validator; NOT a formal BIDS conformance certificate."""
    if not isinstance(metadata, Mapping):
        raise TypeError("sidecar must be a mapping")
    missing = [key for key in _REQUIRED if key not in metadata]
    if missing:
        raise ValueError(f"missing required eye-tracking metadata: {missing}")
    if metadata["PhysioType"] != "eyetrack":
        raise ValueError("PhysioType must equal eyetrack")
    columns = metadata["Columns"]
    if not isinstance(columns, list) or len(columns) < 3 or (
        columns[:3] != ["timestamp", "x_coordinate", "y_coordinate"]
    ) or len(set(columns)) != len(columns):
        raise ValueError("Columns must begin with timestamp, x_coordinate, y_coordinate and be unique")
    if metadata["RecordedEye"] not in {"left", "right", "cyclopean"}:
        raise ValueError("RecordedEye must specify a single supported recording")
    frequency = float(metadata["SamplingFrequency"])
    start = float(metadata["StartTime"])
    if not np.isfinite(frequency) or frequency <= 0 or not np.isfinite(start):
        raise ValueError("SamplingFrequency must be positive and StartTime finite")
    if not np.isfinite(sampling_tolerance) or not 0 <= sampling_tolerance < 0.5:
        raise ValueError("sampling_tolerance must be between 0 and 0.5")
    system = metadata["SampleCoordinateSystem"]
    if not isinstance(system, str) or not system.strip():
        raise ValueError("SampleCoordinateSystem must be documented")
    units = []
    for col in ("x_coordinate", "y_coordinate"):
        info = metadata.get(col)
        if not isinstance(info, Mapping) or "Units" not in info:
            raise ValueError(f"metadata for {col} requires Units")
        units.append(str(info["Units"]).lower())
    if units[0] != units[1] or units[0] not in _UNIT_MAP:
        raise ValueError("coordinate units must agree and be explicitly supported")
    time_info = metadata.get("timestamp", {})
    if not isinstance(time_info, Mapping) or time_info.get("Units", "s") != "s":
        raise ValueError("this narrow adapter requires timestamp units in seconds")
    return {
        "specification_basis": "BEP020_2026_subset_not_full_BIDS_conformance",
        "recorded_eye": metadata["RecordedEye"],
        "coordinate_system": _UNIT_MAP[units[0]],
        "sample_coordinate_system_original": system,
        "sampling_frequency_hz": frequency,
        "start_time_seconds": start,
        "column_names": tuple(columns),
        "validated_subset_only": True,
        "clock_alignment_performed": False,
    }

def from_bids_eyetracking(
    tsv_gz: str | Path,
    *,
    sidecar: str | Path | Mapping[str, Any],
    curve_id: str | None = None,
    sampling_tolerance: float = 0.01,
) -> TrajectorySet:
    """Read one uniformly sampled BIDS eye stream as one unaltered planar curve.

    TSV is headerless; missing values stay missing. No device clock alignment,
    resampling, interpolation, or across-trial segmentation is performed.
    """
    path = Path(tsv_gz)
    if not path.name.endswith("_physio.tsv.gz"):
        raise ValueError("requires a *_physio.tsv.gz file")
    if isinstance(sidecar, Mapping):
        meta = dict(sidecar)
    else:
        meta = json.loads(Path(sidecar).read_text(encoding="utf-8"))
    audit = validate_eyetracking_metadata(meta, sampling_tolerance=sampling_tolerance)
    frame = pd.read_csv(path, sep="\t", compression="gzip", header=None,
                        names=list(audit["column_names"]), na_values=["n/a"])
    times = pd.to_numeric(frame["timestamp"], errors="coerce").to_numpy(float)
    if len(times) < 2 or not np.isfinite(times).all() or not np.all(np.diff(times) > 0):
        raise ValueError("timestamps must contain at least two strictly increasing finite samples")
    dt = np.diff(times)
    expected = 1.0 / audit["sampling_frequency_hz"]
    if not np.all(np.abs(dt / expected - 1.0) <= sampling_tolerance):
        raise ValueError("nonuniform or incompatible timestamps; no hidden resampling")
    coords = frame[["x_coordinate", "y_coordinate"]].apply(
        pd.to_numeric, errors="coerce"
    ).to_numpy(float)
    if np.isinf(coords).any():
        raise ValueError("infinite gaze coordinates are not supported")
    return TrajectorySet(
        time=times, values=coords[None, :, :],
        curve_ids=(curve_id or path.name.removesuffix("_physio.tsv.gz"),),
        dimension_names=("x", "y"),
        coordinate_system=audit["coordinate_system"], time_unit="s",
        provenance={
            "import_contract": "BEP020_2026_subset", "source_path": str(path),
            "recorded_eye": audit["recorded_eye"],
            "sample_coordinate_system": audit["sample_coordinate_system_original"],
            "sampling_frequency_hz": audit["sampling_frequency_hz"],
            "start_time_seconds": audit["start_time_seconds"],
            "clock_alignment_performed": False,
            "interpolation_performed": False,
            "full_bids_conformance_tested": False,
        },
    )
