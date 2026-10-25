---
title: Python EyeLink parsing and acquisition ecosystem
description: Evidence-based comparison of SyeLink, PyeLink, EyeLinkIO and eyelinkparser for reproducible source acquisition.
---

# Choosing an EyeLink acquisition interface

EyeLink acquisition control, EDF reading, ASC parsing, event detection and functional inference are different problems. Do not install a hardware-control library as a dependency of scientific trajectory analysis.

| External tool | Verified scope | Appropriate use | eyetrajectoriespy status |
| --- | --- | --- | --- |
| [SyeLink 2.0](https://syelink.readthedocs.io/en/latest/) | ASC parsing, gaze/calibration/validation/session records, messages, CSV/JSON exports | Offline ASC parser and metadata-preserving sample handoff | **Pinned 2.0.0 synthetic-object example and regression CI**; real ASC qualification pending |
| [PyeLink](https://pyelink.readthedocs.io/en/latest/) | Tracker connection, calibration, recording and real-time data | EyeLink hardware-control applications | Documentation only; **hardware and separate SR Research SDK required** |
| [EyeLinkIO](https://pypi.org/project/eyelinkio/) | Binary EDF reader, optional pandas/MNE export | Alternative EDF ingestion without edf2asc | Proposed only; pre-alpha caveat and native binary considerations |
| [eyelinkparser](https://github.com/open-cogsci/eyelinkparser) | EyeLink ASC extraction around python-datamatrix | Alternative research ASC analysis | Proposed comparison; project describes limited documentation |

## Recommended separation of duties

1. Preserve the original EDF file and precise conversion settings.
2. Parse *offline* into explicit recording segments, gaze channels and calibration/validation metadata.
3. Keep detector/event annotations separate from original sample support.
4. Declare participant identity, experimental trial mapping, timestamp origin and coordinate units.
5. Only then use [the SyeLink sample bridge](syelink-handoff.md), the [pandas/Polars boundary](tabular-handoff.md) and the native dense/sparse analysis guides.

SyeLink distinguishes three spaces: **screen gaze pixels**, **raw camera pupil/CR pixels**, and **HREF angular units**. Raw/HREF fields must not be used as screen x/y without a validated transformation. See the [upstream coordinate guide](https://syelink.readthedocs.io/en/latest/getting_started.html).

### Priorities for independent validation

A scientifically responsible next stage would compare SyeLink-parsed ASC samples with a separate EDF reference extraction on consent-cleared recordings. Check timestamp preservation, eye selection, recording-block boundaries, statuses, event timestamps and validation records. If both implementations agree on sample counts, that alone still cannot qualify statistical confidence-band coverage or identify field MNAR.

[Python integrations](index.md) · [Research evidence](../research/index.md) · [Eye-Tracking-BIDS metadata inspector](bids-metadata-inspector.md).
