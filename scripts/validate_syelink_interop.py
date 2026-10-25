"""SyeLink 2.0 object smoke and fail-closed tests using fabricated data."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

from syelink import SessionData
from syelink.models import DisplayCoords, GazeSample, RecordingData, ValidationData, ValidationSummary


def load(name: str, file: str):
    path = Path(__file__).resolve().parents[1] / "examples" / file
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sample(t, segment, *, mode="RECORD", x=200., y=210., eyes="LR", status="OK"):
    return GazeSample(
        timestamp=t, segment=segment, mode=mode, tracking_mode="P-CR",
        sample_rate=500, eyes_tracked=eyes, left_gaze_x=x,
        left_gaze_y=y, left_pupil=400.0, right_gaze_x=250.,
        right_gaze_y=260., right_pupil=420.0, status=status,
    )


def main():
    load("interop_tabular_handoff", "interop_tabular_handoff.py")
    adapter = load("interop_syelink", "interop_syelink.py")
    validation = ValidationData(
        timestamp=900, validation_type="HV9", tracking_mode="P-CR",
        summary_left=ValidationSummary(
            eye="LEFT", result="GOOD", error_avg_deg=.4,
            error_max_deg=.9, offset_deg=.2, offset_pix_x=2., offset_pix_y=3.,
        )
    )
    base = SessionData(
        gaze_samples=[
            sample(900, 1, mode="CALIBRATE"),
            sample(1000, 1, x=200.), sample(1002, 1, x=201.),
            sample(2000, 2, x=210.), sample(2002, 2, x=211.),
        ],
        recordings=[RecordingData(1000,1002), RecordingData(2000,2002)],
        validations=[validation], display_coords=DisplayCoords(0,0,1279,1023),
    )
    original = tuple((s.timestamp,s.mode,s.left_gaze_x) for s in base.gaze_samples)
    def run(obj=base, **kw):
        args=dict(participant_id="P01", segment_to_trial={1:"T1",2:"T2"}, selected_eye="left")
        args.update(kw)
        return adapter.from_syelink_session(obj,**args)
    result=run()
    assert result.source_version=="2.0.0" and result.selected_eye=="left"
    assert result.audit.curves==2 and result.audit.participants==1 and result.audit.repeated_participants
    assert result.audit.common_grid and result.audit.complete_xy
    assert result.selected_record_samples==4 and result.all_source_samples==5
    assert result.excluded_nonrecord_samples==1
    assert result.sample_rates_hz==(500.0,)
    assert result.reported_validation_mean_error_deg==(.4,)
    assert result.samples.time_s.to_list()==[1000.,1002.,2000.,2002.]
    assert original==tuple((s.timestamp,s.mode,s.left_gaze_x) for s in base.gaze_samples)
    def refuse(text,obj=base,**kw):
        try:run(obj,**kw)
        except (TypeError,ValueError) as e: assert text in str(e),(text,str(e))
        else:raise AssertionError("Expected failure: "+text)
    refuse("exactly one eye",selected_eye="both")
    refuse("explicitly declared",segment_to_trial={1:"T1"})
    refuse("distinct trial",segment_to_trial={1:"same",2:"same"})
    refuse("without RECORD",segment_to_trial={1:"T1",2:"T2",3:"T3"})
    bad=SessionData(gaze_samples=[sample(1000,1,x=None,y=None)],
                    recordings=[RecordingData(1000,1000)],
                    display_coords=DisplayCoords(0,0,1000,1000))
    refuse("either coordinate",bad,segment_to_trial={1:"T1"})
    missing_eye=SessionData(gaze_samples=[sample(1000,1,eyes="R")],
                            display_coords=DisplayCoords(0,0,1000,1000))
    refuse("does not record selected",missing_eye,segment_to_trial={1:"T1"})
    duplicate=SessionData(gaze_samples=[sample(1000,1),sample(1000,1)],
                          display_coords=DisplayCoords(0,0,1000,1000))
    refuse("Duplicate timestamps",duplicate,segment_to_trial={1:"T1"})
    nonmonotone=SessionData(gaze_samples=[sample(1002,1),sample(1000,1)],
                           display_coords=DisplayCoords(0,0,1000,1000))
    refuse("Nonincreasing timestamps",nonmonotone,segment_to_trial={1:"T1"})
    partial=SessionData(gaze_samples=[sample(1000,1),sample(1002,1,x=None)],
                        display_coords=DisplayCoords(0,0,1000,1000))
    record=run(partial,segment_to_trial={1:"T1"})
    assert record.audit.complete_xy is False
    print("PASS SyeLink genuine dataclasses; selected eye, segments, ms, provenance, missingness refusals.")


if __name__=="__main__":
    main()
