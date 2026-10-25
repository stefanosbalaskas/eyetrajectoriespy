---
title: Eye-tracking packages, event detection and BIDS
description: Integration boundaries for pymovements, PyNeon, eyekit, PupEyes, and Eye-Tracking-BIDS.
---

# Upstream recording and event ecosystems

These packages can prepare or annotate eye-tracking data **before** eyetrajectoriespy functional analysis. No external detector or device importer is promoted to a validated estimator.

| Tool | Potential scientific handoff | Required decisions |
| --- | --- | --- |
| [pymovements](https://pymovements.readthedocs.io/en/latest/) | Sample table, events, public datasets | Preserve original sample times, x/y, eye/channel and detection settings; events are derived |
| [PyNeon](https://ncc-brain.github.io/PyNeon/) | Pupil Labs Neon, epochs and multimodal data | Explicit clock synchronization, geometry, calibration and device metadata |
| [eyekit](https://pypi.org/project/eyekit/) | Reading text blocks, interest areas and fixation sequences | Keep text/fixation objects distinct from raw whole-path gaze |
| [PupEyes](https://pupeyes.readthedocs.io/en/latest/) | Pupil processing, blink handling and interactive review | Preserve masks, pupil units and trial alignment |

## Eye-Tracking-BIDS and metadata provenance

The [BIDS eye-tracking extension directory](https://bids.neuroimaging.io/extensions/beps.html) and [2026 Eye-Tracking-BIDS paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC12889726/) describe how eye-position/pupil data and sidecar metadata can be organized. The publication discusses recorded-eye identity, coordinate-system metadata, acquisition sampling/timing, and auxiliary event streams.

**This website is not an Eye-Tracking-BIDS validator or exporter.** Verify the current specification version, device conventions and required fields for each recording. Upstream [eye2bids](https://github.com/bids-standard/eye2bids) and PyNeon may assist for supported devices; no device-wide compatibility claim is made here.

~~~mermaid
flowchart LR
    A[Device export and sidecar] --> B[Upstream parser and QC]
    B --> C[Retain raw sample and event provenance]
    C --> D[Explicit table mapping and support audit]
    D --> E{Recorded grid}
    E -->|Complete common x/y| F[Dense functional trajectory]
    E -->|Sparse / asynchronous| G[Native sparse and asynchronous route]
    F --> H[Audited downstream analysis]
    G --> H
~~~

The key is retaining source information, not converting every gaze record into dense common-grid data at any cost.

[Tabular example](tabular-handoff.md) · [Integration roadmap](roadmap.md)
