"""Optional SyeLink 2.0.0 EyeLink ASC session-object handoff (example only).

IMPORTANT: source samples, calibration, messages and validation objects are
never overwritten. Only explicit RECORD gaze samples for ONE selected eye are
mapped into an existing canonical tabular representation. No interpolation,
fusion of binocular channels, pixel/degree transformation, or device QC.

Run: python -m pip install syelink==2.0.0
     python examples/interop_syelink.py
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from importlib.metadata import version
from typing import Mapping
import math

import pandas as pd

if __package__:
    from .interop_tabular_handoff import TableAudit, canonicalize_gaze_table
else:
    from interop_tabular_handoff import TableAudit, canonicalize_gaze_table

TESTED_SYELINK = "2.0.0"


@dataclass(frozen=True)
class SyeLinkHandoff:
    samples: pd.DataFrame
    audit: TableAudit
    source_version: str
    selected_eye: str
    source_time_unit: str
    source_coordinate_system: str
    all_source_samples: int
    selected_record_samples: int
    excluded_nonrecord_samples: int
    modes_seen: tuple[tuple[str, int], ...]
    status_counts: tuple[tuple[str, int], ...]
    sample_rates_hz: tuple[float, ...]
    recording_blocks: int
    calibration_count: int
    validation_count: int
    message_count: int
    reported_validation_mean_error_deg: tuple[float, ...]
    caveat: str = (
        "Gaze coordinates are EyeLink screen pixels, not RAW camera or HREF units. "
        "Calibration and validation results are provenance, not automated quality acceptance."
    )


def from_syelink_session(
    session: object,
    *,
    participant_id: str,
    segment_to_trial: Mapping[int, str],
    selected_eye: str,
) -> SyeLinkHandoff:
    """Convert a genuine SyeLink SessionData with explicit segment-to-trial IDs.

    Non-RECORD modes are counted but not included in the analysis table.
    No missing gaze points are discarded or synthesized; the shared canonical
    validation refuses rows with both coordinates absent and keeps partial
    missingness marked (thus refusing dense import downstream).
    """
    import syelink

    installed = version("syelink")
    if installed != TESTED_SYELINK:
        raise ValueError(f"Preview tested only with syelink=={TESTED_SYELINK}, found {installed}.")
    if not isinstance(session, syelink.SessionData):
        raise TypeError("Expected a genuine syelink.SessionData, not a dict or CSV export.")
    if selected_eye not in {"left", "right"}:
        raise ValueError("Select exactly one eye: left or right. Binocular averaging is not supported.")
    if not isinstance(participant_id, str) or not participant_id.strip():
        raise ValueError("Explicit nonempty participant_id is required.")
    if not isinstance(segment_to_trial, Mapping) or not segment_to_trial:
        raise ValueError("Explicit segment_to_trial mapping is required; segment is not a trial label.")
    if any(type(k) is not int or k < 1 or not isinstance(v, str) or not v.strip()
           for k, v in segment_to_trial.items()):
        raise ValueError("Segment IDs must be positive integers mapped to nonempty trial IDs.")
    if len(set(segment_to_trial.values())) != len(segment_to_trial):
        raise ValueError("Distinct recording segments must have distinct trial IDs.")
    if session.display_coords is None:
        raise ValueError("Display coordinates missing: cannot verify screen-pixel provenance.")
    display = session.display_coords
    if display.width <= 0 or display.height <= 0:
        raise ValueError("Display geometry must be positive.")
    if not session.gaze_samples:
        raise ValueError("Session contains no gaze samples.")
    from syelink.models import GazeSample
    modes = Counter()
    statuses = Counter()
    rows: list[dict] = []
    selected_segments: set[int] = set()
    rates: set[float] = set()
    for sample in session.gaze_samples:
        if not isinstance(sample, GazeSample):
            raise TypeError("All session gaze samples must be SyeLink GazeSample objects.")
        modes[str(sample.mode)] += 1
        if sample.mode != "RECORD":
            continue
        if type(sample.segment) is not int or sample.segment < 1:
            raise ValueError("RECORD samples require positive integer recording segment IDs.")
        selected_segments.add(sample.segment)
        if sample.segment not in segment_to_trial:
            raise ValueError(f"No explicitly declared trial ID for recording segment {sample.segment}.")
        eye_code = "L" if selected_eye == "left" else "R"
        if sample.eyes_tracked not in {eye_code, "LR"}:
            raise ValueError(f"Segment {sample.segment} does not record selected {selected_eye} eye.")
        t = sample.timestamp
        if isinstance(t, bool) or not isinstance(t, (int, float)) or not math.isfinite(t):
            raise ValueError("Recording timestamps must be finite milliseconds.")
        rate = sample.sample_rate
        if isinstance(rate, bool) or not isinstance(rate, (int, float)) or not math.isfinite(rate) or rate <= 0:
            raise ValueError("Recording sample_rate must be finite and positive (Hz).")
        rates.add(float(rate))
        x = getattr(sample, f"{selected_eye}_gaze_x")
        y = getattr(sample, f"{selected_eye}_gaze_y")
        # The upstream dataclasses allow None; canonicalizer preserves one
        # missing coordinate and rejects rows where both are absent.
        rows.append({
            "participant_id": participant_id, "trial_id": segment_to_trial[sample.segment],
            "time_ms": t, "x_px": x, "y_px": y,
        })
        statuses[str(sample.status)] += 1
    if not rows:
        raise ValueError("No RECORD samples for the selected eye.")
    if set(segment_to_trial) != selected_segments:
        raise ValueError("segment_to_trial includes recording segments without RECORD samples.")
    frame = pd.DataFrame.from_records(rows)
    mapped, audit = canonicalize_gaze_table(
        frame,
        column_map={
            "participant_id": "participant_id", "trial_id": "trial_id",
            "time_s": "time_ms", "x": "x_px", "y": "y_px",
        },
        coordinate_system="pixels", time_unit="ms",
    )
    errors: list[float] = []
    for val in session.validations:
        summary = getattr(val, f"summary_{selected_eye}", None)
        if summary is not None:
            err = getattr(summary, "error_avg_deg", None)
            if isinstance(err, (int, float)) and not isinstance(err, bool) and math.isfinite(err):
                errors.append(float(err))
    return SyeLinkHandoff(
        samples=mapped, audit=audit, source_version=installed,
        selected_eye=selected_eye, source_time_unit="ms",
        source_coordinate_system="pixels",
        all_source_samples=len(session.gaze_samples),
        selected_record_samples=len(rows),
        excluded_nonrecord_samples=len(session.gaze_samples) - len(rows),
        modes_seen=tuple(sorted(modes.items())),
        status_counts=tuple(sorted(statuses.items())),
        sample_rates_hz=tuple(sorted(rates)),
        recording_blocks=len(session.recordings),
        calibration_count=len(session.calibrations),
        validation_count=len(session.validations),
        message_count=len(session.messages),
        reported_validation_mean_error_deg=tuple(errors),
    )


def main() -> None:
    from syelink import SessionData
    from syelink.models import DisplayCoords, GazeSample, RecordingData
    def sample(t: int, segment: int, x: float, y: float) -> GazeSample:
        return GazeSample(
            timestamp=t, segment=segment, mode="RECORD", tracking_mode="P-CR",
            sample_rate=500, eyes_tracked="LR", left_gaze_x=x,
            left_gaze_y=y, left_pupil=400.0, right_gaze_x=x + 1,
            right_gaze_y=y + 1, right_pupil=420.0, status="OK",
        )
    # Invented dataclass fixture: no real participant data and no ASC download.
    session = SessionData(
        gaze_samples=[sample(1000, 1, 200, 210), sample(1002, 1, 202, 211),
                      sample(2000, 2, 220, 212), sample(2002, 2, 222, 213)],
        recordings=[RecordingData(1000, 1002), RecordingData(2000, 2002)],
        display_coords=DisplayCoords(0, 0, 1279, 1023),
    )
    result = from_syelink_session(
        session, participant_id="INVENTED-P01",
        segment_to_trial={1: "trial-one", 2: "trial-two"},
        selected_eye="left",
    )
    print("PASS pinned SyeLink object to explicit gaze table:", result.audit)
    print("Calibration/validation provenance and original session retained; no inference performed.")


if __name__ == "__main__":
    main()
