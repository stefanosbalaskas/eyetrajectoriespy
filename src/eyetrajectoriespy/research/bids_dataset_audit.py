"""Dataset-level Eye-Tracking-BIDS file/metadata audit (BIDS v1.11.2).

This checks only the package's documented one-stream adapter subset and
declared linkage across files. It is NOT an official bids-validator result.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
import json
import re
import pandas as pd
from .bids_interchange import validate_eyetracking_metadata

_STREAM_PATTERN = re.compile(r"^(?P<prefix>.+)_recording-(?P<label>[A-Za-z0-9]+)_physio\.tsv\.gz$")

@dataclass(frozen=True)
class BIDSEyeTrackingDatasetAudit:
    files: pd.DataFrame
    group_checks: pd.DataFrame
    provenance: Mapping[str, Any]


def audit_bids_eyetracking_dataset(
    dataset_root: str | Path,
    *,
    require_screen_metadata: bool = True,
) -> BIDSEyeTrackingDatasetAudit:
    """Audit filenames, sidecars, recorded eyes and gaze-on-screen event metadata.

    Never joins the sample clocks or asserts globally compliant BIDS datasets.
    """
    root = Path(dataset_root)
    if not root.is_dir():
        raise ValueError("dataset_root must be an existing directory")
    streams = sorted(root.rglob("*_physio.tsv.gz"))
    rows = []
    for stream in streams:
        match = _STREAM_PATTERN.match(stream.name)
        if not match:
            continue
        relative = stream.relative_to(root).as_posix()
        sidecar = stream.with_name(stream.name.removesuffix(".tsv.gz") + ".json")
        row: dict[str, Any] = {
            "relative_path": relative,
            "stream_group": str(stream.parent.relative_to(root) / match.group("prefix")),
            "recording_label": match.group("label"),
            "recorded_eye": None,
            "sample_coordinate_system": None,
            "sampling_frequency_hz": None,
            "sidecar_found": sidecar.exists(),
            "subset_metadata_valid": False,
            "screen_metadata_valid": False,
            "status": "invalid",
            "reason": None,
        }
        try:
            if not sidecar.exists():
                raise ValueError("corresponding physio.json sidecar missing")
            metadata = json.loads(sidecar.read_text(encoding="utf-8"))
            result = validate_eyetracking_metadata(metadata)
            row["recorded_eye"] = result["recorded_eye"]
            row["sample_coordinate_system"] = result["sample_coordinate_system_original"]
            row["sampling_frequency_hz"] = result["sampling_frequency_hz"]
            row["subset_metadata_valid"] = True
            if result["sample_coordinate_system_original"] == "gaze-on-screen":
                events = stream.parent / (match.group("prefix") + "_events.json")
                if events.exists():
                    event_meta = json.loads(events.read_text(encoding="utf-8"))
                    presentation = event_meta.get("StimulusPresentation", {})
                    required = (
                        "ScreenDistance", "ScreenOrigin",
                        "ScreenResolution", "ScreenSize",
                    )
                    row["screen_metadata_valid"] = all(
                        key in presentation for key in required
                    )
                if require_screen_metadata and not row["screen_metadata_valid"]:
                    raise ValueError(
                        "gaze-on-screen requires event-sidecar StimulusPresentation "
                        "ScreenDistance, ScreenOrigin, ScreenResolution, ScreenSize"
                    )
            else:
                row["screen_metadata_valid"] = True
            row["status"] = "valid_subset"
        except (ValueError, TypeError, OSError, json.JSONDecodeError) as error:
            row["reason"] = str(error)
        rows.append(row)
    files = pd.DataFrame(rows)
    if files.empty:
        raise ValueError("no *recording-<label>_physio.tsv.gz eye streams found")
    groups = []
    for name, group in files.groupby("stream_group", sort=True):
        eyes = group["recorded_eye"].dropna().tolist()
        labels = group["recording_label"].tolist()
        no_duplicate_eyes = len(eyes) == len(set(eyes))
        no_duplicate_labels = len(labels) == len(set(labels))
        all_valid = bool((group.status == "valid_subset").all())
        groups.append({
            "stream_group": name,
            "n_recordings": len(group),
            "distinct_eye_labels": no_duplicate_eyes,
            "distinct_recording_entities": no_duplicate_labels,
            "all_subsets_valid": all_valid,
            "group_valid": no_duplicate_eyes and no_duplicate_labels and all_valid,
            "clock_alignment_verified": False,
            "binocular_sample_synchronization_verified": False,
        })
    return BIDSEyeTrackingDatasetAudit(
        files=files, group_checks=pd.DataFrame(groups),
        provenance={
            "specification": "BIDS_1.11.2_eyetracking_subset",
            "official_bids_validator_executed": False,
            "sample_clocks_compared": False,
            "synchronization_performed": False,
            "sample_content_scanned": False,
            "root": str(root),
            "experimental": True,
        }
    )
