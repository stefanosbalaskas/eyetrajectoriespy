---
title: Eye-Tracking-BIDS metadata inspector
description: Narrow read-only sidecar and optional TSV.GZ shape checks under the 2026 Eye-Tracking-BIDS physical sampling profile.
---

# Read-only Eye-Tracking-BIDS inspection

The [2026 Eye-Tracking-BIDS specification paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC12889726/) describes continuous gaze recordings in headerless compressed TSV files with accompanying physio JSON sidecars. This **repository-level preview inspector** checks a deliberately narrow portion of those fields and optionally reads a bounded set of rows from the corresponding physio.tsv.gz.

**This is not the official BIDS validator, a BIDS writer, a time-series importer or a substitute for device qualification.** In particular, no gaze time is reconstructed from SamplingFrequency or StartTime and no geometry conversion is attempted.

## Check a sidecar without changing the source

~~~bash
python examples/inspect_eye_tracking_bids.py path/to/sub-01_task-demo_recording-eye1_physio.json
~~~

Optionally inspect the declared columns against the first 10,000 physical rows of a paired file:

~~~bash
python examples/inspect_eye_tracking_bids.py path/to/sub-01_task-demo_recording-eye1_physio.json --tsv-gz path/to/sub-01_task-demo_recording-eye1_physio.tsv.gz
~~~

The auditor requires these fields for its **restricted eyetrack profile**: PhysioType=eyetrack, finite positive SamplingFrequency, finite StartTime (negative allowed), ordered Columns starting with timestamp/x_coordinate/y_coordinate, RecordedEye left/right/cyclopean, and nonblank SampleCoordinateSystem. It reports the original x/y Units declarations when present and warns if they are missing or disagree.

The file is opened read-only. A bounded TSV check does not establish that the entire recording conforms, has no dropped samples, contains only one eye, or preserves a uniform acquisition rate. Its output retains the sidecar basename and aggregate descriptors rather than copying gaze coordinates.

[Read the implementation](https://github.com/stefanosbalaskas/eyetrajectoriespy/blob/main/examples/inspect_eye_tracking_bids.py) · [Review negative tests](https://github.com/stefanosbalaskas/eyetrajectoriespy/blob/main/scripts/validate_eye_tracking_bids.py) · [Official BIDS specification](https://bids-specification.readthedocs.io/en/latest/modality-specific-files/physiological-recordings/)

!!! warning "Why no automatic data import?"
    BIDS sampling frequency and offset concern the continuous acquisition; timestamps may represent device-specific timing. Declared coordinate system and units still require study-specific interpretation. Transforming these sidecars directly into a model-ready common grid could silently erase missingness, clock offsets and independent-unit structure.

[Python integration hub](index.md) · [pymovements handoff](pymovements-handoff.md) · [Scientific limitations](../methods/limitations.md).
