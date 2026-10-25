"""Tests for narrow, read-only Eye-Tracking-BIDS metadata/profile audit."""
from __future__ import annotations

import gzip
import importlib.util
import json
import sys
import tempfile
from pathlib import Path


def load():
    file = Path(__file__).resolve().parents[1] / "examples/inspect_eye_tracking_bids.py"
    spec = importlib.util.spec_from_file_location("inspect_eye_tracking_bids", file)
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    assert spec.loader is not None
    spec.loader.exec_module(m)
    return m


def main() -> None:
    m = load()
    sidecar = {
        "PhysioType": "eyetrack", "SamplingFrequency": 250, "StartTime": -0.5,
        "Columns": ["timestamp", "x_coordinate", "y_coordinate", "pupil_size"],
        "RecordedEye": "left", "SampleCoordinateSystem": "screen",
        "x_coordinate": {"Units": "px"}, "y_coordinate": {"Units": "px"},
    }
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "sub-01_task-demo_recording-eye1_physio.json"
        gz = p.with_suffix(".tsv.gz")
        def save(data):
            p.write_text(json.dumps(data), encoding="utf-8")
        save(sidecar)
        with gzip.open(gz, "wt", encoding="utf-8", newline="") as f:
            f.write("0\t200\t250\t3\n4\t201\t251\t3\n8\t202\t252\t3\n")
        report = m.inspect_sidecar(p, physio_path=gz)
        assert report.inspected_tsv_rows == 3 and report.inspection_truncated is False
        assert report.sampling_frequency_hz == 250 and report.start_time_s == -0.5
        assert report.recorded_eye == "left"
        assert not report.warnings
        bound = m.inspect_sidecar(p, physio_path=gz, max_rows=2)
        assert bound.inspected_tsv_rows == 2 and bound.inspection_truncated
        def rejects(field, value, message):
            bad = dict(sidecar)
            bad[field] = value
            save(bad)
            try:
                m.inspect_sidecar(p)
            except ValueError as exc:
                assert message in str(exc), (message, str(exc))
            else:
                raise AssertionError(f"Expected fail closed metadata field {field}")
        rejects("PhysioType", "ecg", "PhysioType")
        rejects("SamplingFrequency", 0, "SamplingFrequency")
        rejects("SamplingFrequency", True, "SamplingFrequency")
        rejects("StartTime", "0.0", "StartTime")
        rejects("RecordedEye", "both", "RecordedEye")
        rejects("Columns", ["x_coordinate", "y_coordinate", "timestamp"], "first columns")
        rejects("SampleCoordinateSystem", "", "SampleCoordinateSystem")
        save(sidecar)
        with gzip.open(gz, "wt", encoding="utf-8") as f:
            f.write("0\t200\t250\n")
        try:
            m.inspect_sidecar(p, physio_path=gz)
        except ValueError as exc:
            assert "fields" in str(exc)
        else:
            raise AssertionError("Broken TSV column count should refuse.")
    print("PASS BIDS read-only metadata, bounded TSV shape and fail-closed tests")


if __name__ == "__main__":
    main()
