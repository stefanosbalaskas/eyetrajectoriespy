"""Pinned pymovements 0.28.0 Gaze -> canonical gaze sample table.

Repository-level example, NOT a released eyetrajectoriespy API, vendor
device reader, event converter, or statistical inference qualification.

Requires pymovements==0.28.0, polars, pyarrow, and eyetrajectoriespy 1.2.0.
Never generates sample times or changes the upstream Gaze / event streams.
"""
from __future__ import annotations

from dataclasses import dataclass
from importlib.metadata import version

import pandas as pd

from interop_tabular_handoff import TableAudit, canonicalize_gaze_table

TESTED_PYMOVEMENTS = "0.28.0"


@dataclass(frozen=True)
class GazeHandoff:
    samples: pd.DataFrame
    audit: TableAudit
    source_version: str
    coordinate_column: str
    coordinate_system: str
    source_time_unit: str
    source_events_count: int | None
    source_messages_count: int | None
    upstream_metadata_keys: tuple[str, ...]
    caveat: str = (
        "Input Gaze is retained upstream, with original events and metadata. "
        "No detector, recording QC, time synchronization, or inference is qualified."
    )


def from_pymovements(
    gaze: object,
    *,
    participant_id: str,
    trial_column: str | None = None,
    single_trial_id: str | None = None,
    coordinate_column: str,
    coordinate_system: str,
    timestamp_unit: str,
) -> GazeHandoff:
    """Explicitly flatten documented 0.28.0 nested components.

    pymovements standardizes the Gaze samples time column to milliseconds;
    choose 'pixel' (pixels) OR 'position' (degrees), never mix the two.
    A single Gaze object may contain multiple trials, but requires an
    explicit single trial column here. More elaborate designs must adapt
    IDs upstream without reordering samples.
    """
    import pymovements as pm
    import polars as pl

    pm_version = version("pymovements")
    if pm_version != TESTED_PYMOVEMENTS:
        raise ValueError(
            f"Adapter preview tested only with pymovements=={TESTED_PYMOVEMENTS}; "
            f"found {pm_version}. Requalify before enabling newer versions."
        )
    if not isinstance(gaze, pm.Gaze):
        raise TypeError("Expected a genuine pymovements.Gaze instance.")
    if not isinstance(participant_id, str) or not participant_id.strip():
        raise ValueError("Provide a nonempty explicit participant_id.")
    if timestamp_unit != "ms":
        raise ValueError(
            "pymovements.Gaze.samples.time is standardized to milliseconds. "
            "Explicitly pass timestamp_unit='ms'; do not use the original input unit."
        )
    compatible = {"pixel": "pixels", "position": "degrees"}
    if coordinate_column not in compatible or coordinate_system != compatible.get(coordinate_column):
        raise ValueError("Coordinate selection must be pixel/pixels or position/degrees.")
    if (trial_column is None) == (single_trial_id is None):
        raise ValueError("Specify exactly one of trial_column or single_trial_id.")
    if single_trial_id is not None and (
        not isinstance(single_trial_id, str) or not single_trial_id.strip()
    ):
        raise ValueError("single_trial_id must be a nonempty string.")
    samples = gaze.samples
    if not isinstance(samples, pl.DataFrame):
        raise TypeError("Expected pymovements.Gaze.samples as a Polars DataFrame.")
    if "time" not in samples.columns or coordinate_column not in samples.columns:
        raise ValueError("Missing documented 'time' or selected gaze component column.")
    if trial_column is not None and trial_column not in samples.columns:
        raise ValueError("Declared trial_column is not present in samples.")
    if trial_column in {"time", coordinate_column}:
        raise ValueError("trial_column cannot reuse time or coordinate component.")
    declared_trials = tuple(gaze.trial_columns or ())
    if isinstance(gaze.trial_columns, str):
        declared_trials = (gaze.trial_columns,)
    if trial_column is not None and declared_trials and declared_trials != (trial_column,):
        raise ValueError("Declared trial_column disagrees with upstream Gaze trial_columns.")
    if trial_column is None and declared_trials:
        raise ValueError("Gaze has multiple trial labels: specify its trial column explicitly.")
    # Do not assume all arrays are length 2 or silently turn bad channels
    # into a zero or a scalar. .to_list() supports Polars List and Array.
    coords = samples.get_column(coordinate_column).to_list()
    x: list[float | None] = []
    y: list[float | None] = []
    for i, pair in enumerate(coords):
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            raise ValueError(f"Row {i} coordinate component must be exactly a two-element list.")
        x.append(pair[0])
        y.append(pair[1])
    if samples.height == 0:
        raise ValueError("No recorded gaze samples.")
    flat = pd.DataFrame({
        "source_time_ms": samples.get_column("time").to_list(),
        "source_x": x,
        "source_y": y,
        "source_trial": (
            samples.get_column(trial_column).to_list()
            if trial_column is not None
            else [single_trial_id] * samples.height
        ),
        "source_participant": [participant_id] * samples.height,
    })
    if flat["source_trial"].isna().any():
        raise ValueError("Trial labels cannot be null.")
    mapping = {
        "participant_id": "source_participant", "trial_id": "source_trial",
        "time_s": "source_time_ms", "x": "source_x", "y": "source_y",
    }
    canonical, audit = canonicalize_gaze_table(
        flat, column_map=mapping, time_unit="ms",
        coordinate_system=coordinate_system,
    )
    events = getattr(gaze, "events", None)
    event_frame = getattr(events, "frame", None)
    messages = getattr(gaze, "messages", None)
    metadata = getattr(gaze, "metadata", None)
    return GazeHandoff(
        samples=canonical,
        audit=audit,
        source_version=pm_version,
        coordinate_column=coordinate_column,
        coordinate_system=coordinate_system,
        source_time_unit="ms",
        source_events_count=None if event_frame is None else len(event_frame),
        source_messages_count=None if messages is None else len(messages),
        upstream_metadata_keys=tuple(sorted(str(k) for k in metadata)) if isinstance(metadata, dict) else (),
    )


def main() -> None:
    import pymovements as pm

    frame = pd.DataFrame({
        "time_raw": [0, 10, 20, 0, 10, 20],
        "gaze_x": [160.0, 161.0, 162.0, 200.0, 201.0, 202.0],
        "gaze_y": [120.0, 121.0, 122.0, 140.0, 141.0, 142.0],
        "trial_key": ["a", "a", "a", "b", "b", "b"],
    })
    gaze = pm.gaze.from_pandas(
        frame, trial_columns="trial_key", time_column="time_raw",
        time_unit="ms", pixel_columns=["gaze_x", "gaze_y"],
    )
    handoff = from_pymovements(
        gaze, participant_id="invented-person-01", trial_column="trial_key",
        coordinate_column="pixel", coordinate_system="pixels",
        timestamp_unit="ms",
    )
    print("PASS pymovements Gaze handoff:", handoff.audit)
    print("Events and source metadata remain on the upstream Gaze object; no inference was performed.")


if __name__ == "__main__":
    main()
