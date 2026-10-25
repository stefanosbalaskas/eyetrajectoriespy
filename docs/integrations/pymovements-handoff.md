---
title: Pinned pymovements Gaze sample handoff
description: Executable 0.28.0 preview adapter for nested pixel and position channels, explicit trial identities and millisecond timestamps.
---

# pymovements 0.28.0 → trajectory samples

**Status: preview repository example, not a supported or released package API.** The verified September 2026 [pymovements 0.28.0](https://pypi.org/project/pymovements/0.28.0/) exposes a Gaze object with a Polars samples table. Its documented ingestion methods convert source timestamps into **milliseconds** and can nest pixel x/y under a two-element pixel column (or degrees under position).

[Source code](https://github.com/stefanosbalaskas/eyetrajectoriespy/blob/main/examples/interop_pymovements.py) · [Compatibility tests](https://github.com/stefanosbalaskas/eyetrajectoriespy/blob/main/scripts/validate_pymovements_interop.py) · [Upstream Gaze documentation](https://pymovements.readthedocs.io/en/stable/reference/api/pymovements.Gaze.html)

## Run the pinned example

~~~bash
python -m pip install -e .
python -m pip install pymovements==0.28.0 polars pyarrow
python examples/interop_pymovements.py
python scripts/validate_pymovements_interop.py
~~~

The executable creates one **invented, non-human dataset** using the real upstream Gaze constructor and checks its representation. No recordings are downloaded and no participant data leave the runtime. The separate test verifies that upstream sample tables remain unchanged.

## Explicit conversion

~~~python
from examples.interop_pymovements import from_pymovements

# Given a pymovements.Gaze constructed and audited upstream:
handoff = from_pymovements(
    gaze,
    participant_id="P01",
    trial_column="trial_key",  # explicitly present in gaze.samples
    coordinate_column="pixel",
    coordinate_system="pixels",
    timestamp_unit="ms",       # pymovements standardizes Gaze.samples.time
)
print(handoff.audit)
print(handoff.source_events_count, handoff.upstream_metadata_keys)
# The original events and other metadata remain on your original gaze object.
~~~

A one-trial recording can instead declare single_trial_id and leave trial_column unset. This example refuses unpinned upstream versions, missing time/component fields, mixed or undeclared channel units, inconsistent trial IDs, malformed nested pairs and duplicate/nonincreasing recorded timestamps. The returned sample table is passed through the previously tested explicit canonicalization rules.

**Native sparse support remains native.** If the output audit indicates unequal per-trial grids or incomplete x/y, do not call the dense importer. Use the [irregular representation guide](../guides/irregular-trajectories.md) with declared observation times.

## Essential provenance

Keep the exact source package and detector versions, raw gaze object, event frame, messages, screen geometry, original sample clock and any resampling history. The example reports event/message **counts** and metadata **key names**, but does not quietly reinterpret fixation events as raw gaze or export an upstream event table. It also does not run pymovements quality checks on the user's behalf.

For upstream quality checks and methods, consult the [Gaze validation reference](https://pymovements.readthedocs.io/en/latest/reference/api/pymovements.Gaze.validate.html). Passing this adapter's smoke tests is not sensor QC, W3 band calibration, or field MNAR identification.

**Compatibility evidence:** pinned genuine pymovements Gaze objects generated from synthetic samples, with platform/version CI. **Still needed for a stable package API:** consent-safe genuinely recorded fixtures from more than one device, hardware time/coordinate contracts, and independent missingness audits.
