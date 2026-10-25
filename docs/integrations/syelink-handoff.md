---
title: SyeLink 2.0 EyeLink ASC interoperability
description: A pinned, source-preserving SyeLink SessionData sample handoff with independent-eye selection, segment boundaries and calibration provenance.
---

# EyeLink ASC → functional gaze: SyeLink

**Integration status: repository example only; not a released eyetrajectoriespy API.** [SyeLink 2.0.0](https://pypi.org/project/syelink/2.0.0/) reads EyeLink ASC exports and exposes session dataclasses for gaze samples, recording blocks, validations, calibrations, display geometry and experiment messages. Its [GazeSample contract](https://syelink.readthedocs.io/en/latest/api/models.html) includes acquisition timestamps (milliseconds), per-sample recording mode, segment number and left/right pixel gaze fields.

This example **does not convert EDF**, operate a physical EyeLink tracker, read raw corneal-reflection coordinates as gaze, or claim that reported validation errors qualify a trajectory for inference.

[Run example source](https://github.com/stefanosbalaskas/eyetrajectoriespy/blob/main/examples/interop_syelink.py){ .md-button .md-button--primary }
[Review negative tests](https://github.com/stefanosbalaskas/eyetrajectoriespy/blob/main/scripts/validate_syelink_interop.py){ .md-button }

## Installation and synthetic execution

~~~bash
python -m pip install -e .
python -m pip install syelink==2.0.0
python examples/interop_syelink.py
python scripts/validate_syelink_interop.py
~~~

The tests use **genuine SyeLink Python dataclasses with completely invented values**. They do not contain a recorded person's gaze and do not test the complete vendor ASC parser on a real recording.

## Handoff from an upstream ASC session

~~~python
from syelink import parse_asc_file
from examples.interop_syelink import from_syelink_session

session = parse_asc_file("my_eyelink_export.asc")

handoff = from_syelink_session(
    session,
    participant_id="P001",
    segment_to_trial={
        1: "baseline_trial",
        2: "stimulus_trial",
    },
    selected_eye="left",
)
print(handoff.audit)
print(handoff.modes_seen, handoff.status_counts)
print(handoff.reported_validation_mean_error_deg)

# handoff.samples: canonical participant_id, trial_id, time_s, x, y
# The column named time_s retains its explicitly declared audit.time_unit == "ms".
# Never interpret its numeric values as seconds without an explicit conversion.
~~~

The mapping of *segment* to *trial* is intentionally required and must be one-to-one. SyeLink's segment numbers are not necessarily your experiment's trial labels. The example copies **RECORD** samples only and reports excluded non-record modes explicitly. A left-eye sample is never averaged with the right eye; binocular source channels are not implicitly fused.

### What survives the conversion?

| Information | Treatment |
| --- | --- |
| Raw absolute timestamps | Preserved in numeric values; declared **milliseconds** in audit |
| Screen gaze x/y | Explicit left or right selected; retained as **pixels** |
| Recording segment | Explicit one-to-one mapping to trial_id; no inferred real trial meaning |
| CALIBRATE / VALIDATE / OFFLINE samples | Excluded from analysis table but **counted by source mode** |
| Invalid/status-flagged rows | Status values **counted**, not automatically deleted or marked clean |
| Missing gaze x/y | No substitution; both absent refuses, partially missing retained with dense-import refusal |
| Calibration/validation objects | Stay in original session; counts and reported mean errors retained only as metadata |
| Messages and raw pupil/CR and HREF fields | Stay on the original SyeLink object; not misrepresented as screen gaze coordinates |

### The critical data-support distinction

A pair of recording blocks with acquisition timestamps 1000–1002 ms and 2000–2002 ms **does not constitute an aligned trial-relative grid**. This preview intentionally **does not reset the clock**. A research analyst must declare any independently justified trial-origin shift and audit its effects before calling a complete-grid estimator.

~~~mermaid
flowchart LR
  A[EyeLink EDF] --> B[User exports gaze ASC]
  B --> C[SyeLink SessionData]
  C --> D[Preserve validations and messages]
  C --> E[Explicit left or right RECORD samples]
  E --> F[Map segment to trial; retain absolute ms]
  F --> G{Observed support}
  G -->|Complete aligned x/y| H[Existing dense importer]
  G -->|Unequal or missing| I[Native irregular pathway]
  H --> J[Interpretation and source audit]
  I --> J
~~~

### Why calibration values are not acceptance criteria

SyeLink's validation summaries may include average error in degrees and per-eye outcomes. Reporting these raw values does not establish the permitted threshold for your research question, visual angle conversion, drift correction, or data completeness. The adapter does not auto-accept a GOOD result, and does not smooth or interpolate across blinks.

**Next qualification gates:** independently shareable anonymized real EyeLink recordings, ASC parser fixture tests, eye/clock/segment checks across tracker configurations, calibration and validation audit across genuine sessions, and publication-quality method studies. See [integration roadmap](roadmap.md) and [scientific limitations](../methods/limitations.md).
