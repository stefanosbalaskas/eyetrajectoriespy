"""Runnable self-contained Eye-Tracking-BIDS subset and calibration evidence demo.

Produces a synthetic BIDS fixture under output/fixture. Not an official
bids-validator conformance result and never synchronizes instrument clocks.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from eyetrajectoriespy.types import TrajectorySet
from eyetrajectoriespy.research import (
    audit_bids_eyetracking_dataset, from_bids_eyetracking,
    summarize_gaze_validation_targets, audit_gaze_measurement_quality,
    link_gaze_validation_sessions, measurement_quality_reporting_frame,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = args.out/"fixture"
    location = root/"sub-01"/"func"
    location.mkdir(parents=True, exist_ok=True)
    prefix = "sub-01_task-visualSearch"
    stream = location/(prefix+"_recording-eye1_physio.tsv.gz")
    pd.DataFrame([
        [1000, .45, .50, 4600],
        [1010, .46, .51, 4590],
        [1020, np.nan, np.nan, 4602],
        [1030, .44, .49, 4599],
    ]).to_csv(
        stream, sep="\t", index=False, header=False, compression="gzip",
        na_rep="n/a"
    )
    sidecar = {
        "Columns": ["timestamp","x_coordinate","y_coordinate","pupil_size"],
        "SamplingFrequency": 100, "StartTime": -1.0,
        "PhysioType":"eyetrack", "RecordedEye":"left",
        "SampleCoordinateSystem":"gaze-on-screen",
        "timestamp":{"Units":"ms","Origin":"Device startup"},
        "x_coordinate":{"Units":"1"},
        "y_coordinate":{"Units":"1"},
        "pupil_size":{"Units":"arbitrary"},
    }
    stream.with_name(stream.name.removesuffix(".tsv.gz")+".json").write_text(
        json.dumps(sidecar,indent=2)+"\n"
    )
    (location/(prefix+"_events.json")).write_text(json.dumps({
        "StimulusPresentation": {
            "ScreenDistance":.6,
            "ScreenOrigin":["top","left"],
            "ScreenResolution":[1920,1080],
            "ScreenSize":[.52,.29],
        }
    },indent=2)+"\n")
    scanned = audit_bids_eyetracking_dataset(root)
    assert scanned.group_checks.group_valid.all()
    original = from_bids_eyetracking(stream, sidecar=sidecar)
    gaze = TrajectorySet(
        time=original.time, values=original.values,
        curve_ids=original.curve_ids,
        dimension_names=original.dimension_names,
        coordinate_system=original.coordinate_system,
        time_unit=original.time_unit,
        metadata=pd.DataFrame({
            "participant_id":["sub-01"],
            "session_id":["ses-01"],
            "device_id":["synthetic-tracker"],
        }),
        provenance=original.provenance,
    )
    samples = pd.DataFrame({
        "participant_id":["sub-01"]*4,
        "validation_session_id":["ses-01"]*4,
        "target_id":["A","A","B","B"],
        "target_x_deg":[0,0,3,3],
        "target_y_deg":[0,0,1,1],
        "gaze_x_deg":[.3,.7,3.3,3.7],
        "gaze_y_deg":[0,0,1,1],
    })
    measured = summarize_gaze_validation_targets(
        samples, evidence_source="synthetic_target_grid"
    )
    measured["device_id"] = "synthetic-tracker"
    quality = audit_gaze_measurement_quality(
        gaze, validation_records=measured,
        source_description="self-contained synthetic calibration",
    )
    links = link_gaze_validation_sessions(gaze,quality,require_all=True)
    assert links.link_status.eq("exact_identifier_match").all()
    args.out.mkdir(parents=True, exist_ok=True)
    scanned.files.to_csv(args.out/"bids-files.csv",index=False)
    scanned.group_checks.to_csv(args.out/"bids-groups.csv",index=False)
    measured.to_csv(args.out/"validation-targets.csv",index=False)
    measurement_quality_reporting_frame(quality).to_csv(
        args.out/"quality-summary.csv", index=False,
    )
    links.to_csv(args.out/"session-linkage.csv",index=False)
    (args.out/"provenance.json").write_text(json.dumps({
        "synthetic_fixture":True,
        "import_contract": original.provenance["import_contract"],
        "raw_device_timestamp_unit":original.provenance["source_timestamp_unit"],
        "official_bids_validator_executed":False,
        "clock_alignment_performed":False,
        "calibration_recency_verified":False,
    },indent=2)+"\n")
    print("PASS: synthetic BIDS subset and exact validation linkage; no conformance guarantee")


if __name__ == "__main__":
    main()
