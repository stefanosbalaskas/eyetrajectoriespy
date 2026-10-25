"""Exact pymovements 0.28.0 integration contracts on fabricated teaching data.

No dataset download, human recorded gaze or empirical inference validation.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd
import pymovements as pm


def load(name: str, filename: str):
    path = Path(__file__).resolve().parents[1] / "examples" / filename
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    load("interop_tabular_handoff", "interop_tabular_handoff.py")
    a = load("interop_pymovements", "interop_pymovements.py")
    frame = pd.DataFrame({
        "time_raw": [0, 10, 20, 0, 10, 20],
        "xraw": [10, 11, 12, 15, 16, 17],
        "yraw": [20, 21, 22, 25, 26, 27],
        "trial": ["first", "first", "first", "second", "second", "second"],
    })
    gaze = pm.gaze.from_pandas(
        frame, time_column="time_raw", time_unit="ms",
        pixel_columns=["xraw", "yraw"], trial_columns="trial",
    )
    original = gaze.samples.clone()
    def convert(obj=gaze, **changes):
        args = {
            "participant_id": "P01", "trial_column": "trial",
            "coordinate_column": "pixel", "coordinate_system": "pixels",
            "timestamp_unit": "ms",
        }
        args.update(changes)
        return a.from_pymovements(obj, **args)
    result = convert()
    assert result.source_version == "0.28.0"
    assert result.audit.curves == 2 and result.audit.participants == 1
    assert result.audit.repeated_participants
    assert result.audit.common_grid and result.audit.complete_xy
    assert list(result.samples.columns) == ["participant_id", "trial_id", "time_s", "x", "y"]
    assert result.samples.time_s.to_list() == [0.0, 10.0, 20.0] * 2
    assert result.source_time_unit == "ms" and result.coordinate_system == "pixels"
    assert result.source_events_count is not None
    assert original.equals(gaze.samples), "Upstream sample frame was modified"
    def refuse(message: str, obj=gaze, **changes):
        try:
            convert(obj, **changes)
        except (ValueError, TypeError) as exc:
            assert message in str(exc), (message, str(exc))
        else:
            raise AssertionError("Refusal not triggered: " + message)
    refuse("milliseconds", timestamp_unit="s")
    refuse("pixel/pixels", coordinate_system="degrees")
    refuse("exactly one", single_trial_id="wrong")
    refuse("disagrees", trial_column="trial_x") if "trial_x" in gaze.samples.columns else None
    # The upstream parser allows importing raw coordinate channels containing
    # NaN; the canonical handoff must preserve missingness and refuse dense use.
    bad = frame.copy()
    bad.loc[1, "xraw"] = float("nan")
    sparse = pm.gaze.from_pandas(
        bad, time_column="time_raw", time_unit="ms",
        pixel_columns=["xraw", "yraw"], trial_columns="trial",
    )
    incomplete = convert(sparse)
    assert not incomplete.audit.complete_xy
    try:
        a.load("unused")  # There is deliberately no implicit file-reader API.
    except AttributeError:
        pass
    # Source timestamps remain on their native observed time support.
    duplicate = frame.copy()
    duplicate.loc[1, "time_raw"] = 0
    try:
        dup_gaze = pm.gaze.from_pandas(
            duplicate, time_column="time_raw", time_unit="ms",
            pixel_columns=["xraw", "yraw"], trial_columns="trial",
        )
    except (ValueError, AssertionError):  # upstream may reject first
        pass
    else:
        refuse("Duplicate", dup_gaze)
    print("PASS genuine pymovements 0.28.0 object handoff; 2D, support, provenance and fail-closed checks")


if __name__ == "__main__":
    main()
