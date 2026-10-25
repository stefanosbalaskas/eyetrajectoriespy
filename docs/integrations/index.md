---
title: Python ecosystem integrations
description: Optional pandas and Polars interoperability examples, and evidence-based candidate connections to eye-tracking and functional-data packages.
---

# Python ecosystem integrations

**Interoperate instead of duplicating upstream data processing.** eyetrajectoriespy 1.2.0 already has optional scikit-fda, FDApy and elastic-function integrations. This section adds an **example-level** pandas/Polars table bridge and documents research-safe handoffs from acquisition and data-quality ecosystems.

[Runnable table bridge](tabular-handoff.md){ .md-button .md-button--primary }
[External packages and BIDS](acquisition-and-bids.md){ .md-button }
[Qualification roadmap](roadmap.md){ .md-button }

## Verified roles and present integration status

| External ecosystem | Verified capability | Status in this repository |
| --- | --- | --- |
| [pymovements](https://pymovements.readthedocs.io/en/latest/) | Public datasets, sample processing, event detection; its Gaze.samples is a Polars DataFrame | **Documented candidate handoff**, not a directly qualified adapter |
| [Polars](https://docs.pola.rs/api/python/stable/reference/dataframe/api/polars.DataFrame.to_pandas.html) + PyArrow | Parquet I/O and dataframe conversion | **Repository example implemented**, optional, outside stable API |
| [Pandera](https://pandera.readthedocs.io/en/latest/dataframe_schemas.html) | Dataframe schema validation and explicit nullable columns | Proposed opt-in validation layer |
| [PyNeon](https://ncc-brain.github.io/PyNeon/) | Neon recording, gaze/IMU/video/event processing, BIDS-oriented export | Proposed source handoff; no direct adapter |
| [Eye-Tracking-BIDS / eye2bids](https://bids.neuroimaging.io/extensions/beps.html) | Standardized acquisition data and metadata organization | Metadata guidance only; not a BIDS validator |
| [eyekit](https://pypi.org/project/eyekit/) | Reading fixations and text interest areas | Potential companion analyses; not an importer |
| [PupEyes](https://pupeyes.readthedocs.io/en/latest/) | Pupil-size preprocessing and interactive eye-tracking views | Potential companion; not an importer |
| [scikit-fda](https://fda.readthedocs.io/en/stable/) / [FDApy](https://fdapy.readthedocs.io/en/latest/) | Functional representations, sparse smoothing and FPCA | **Existing optional package integration/comparator**, not new |

## What the new example actually does

The [table handoff](tabular-handoff.md) accepts pandas or an optional Polars dataframe after researchers identify source fields and recorded units. It checks duplicate or out-of-order timestamps, coordinate ranges under a declared normalized scale, and participant/trial hierarchy. It **refuses** complete-grid conversion if x/y observations are missing or per-curve time grids differ.

It does not interpolate, harmonize clock origins, detect fixations, ingest vendor formats, claim missing-gaze identification, or validate inferential bands. This is a recipe under examples/ with independent smoke/rejection tests, not a new import under the released eyetrajectoriespy package.

## Prioritize provenance over convenient coercion

- Preserve **acquisition-native timestamps**, source coordinate units, masks, hardware/clock metadata, participant/trial IDs and original recordings.
- Treat event sequences, fixation summaries, AOI labels and pupillometry as separate derived outcomes, not replacements for planar sample trajectories.
- For incomplete, paired-sparse or coordinate-asynchronous observations, use the corresponding [native sparse guide](../guides/sparse-multivariate-fpca.md) rather than manufacturing dense arrays.
- Data compatibility is not statistical qualification; issues [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) remain open.

See the [data-to-method guide](../start/data-to-method.md) and [package API stability policy](../reference/api-stability.md).
