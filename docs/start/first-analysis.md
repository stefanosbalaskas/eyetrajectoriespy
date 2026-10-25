---
title: First analysis — choose the right path in five minutes
description: New-user orientation to real observational support, reproducible synthetic examples, stable workflows and scientific limitations.
search:
  boost: 1.3
---

# Your first eyetrajectoriespy analysis

The most useful first analysis is **one you can reproduce and interpret**, not the most complicated model that happens to fit. This guide connects your data format to the right starting workflow and its reporting boundaries.

[Explore visual methods](../tools/figure-storyboard.md){ .md-button .md-button--primary }
[Install the stable package](../quickstart.md){ .md-button }
[Choose a Python data integration](../integrations/navigator.md){ .md-button }

## 1. Identify where your gaze came from

<div class="grid cards" markdown>

- **I have a CSV or Parquet file**

  First verify participant/trial identifiers, coordinate meaning, timestamps, recorded gaps and unit semantics. Use the [local, no-upload CSV inspector](../tools/data-readiness.md) for small long-format extracts or the [optional dataframe handoff](../integrations/tabular-handoff.md).

- **I have device exports or BIDS recordings**

  Start with the [integration navigator](../integrations/navigator.md). The pinned pymovements/SyeLink and read-only BIDS code is **example-level**, not released device validation. Preserve the originals and preprocessing record.

- **I have repeated trials or missing x/y observations**

  Declare the participant as a potential independent unit and keep actual coordinate-specific support. Read the [data-to-method guide](data-to-method.md) before fitting.

</div>

## 2. Reproduce one complete example using invented data

The published **1.2.0** version provides three executable quickstarts. These use seeded synthetic demonstrations, *not participant measurements*:

| Your question | Runnable starter | What to inspect |
| --- | --- | --- |
| What are the dominant x/y path modes? | [Dense FPCA example](../quickstart.md#1-common-grid-fpca) | Time grid, scaling, coordinate interpretation |
| What if both coordinates were observed sparsely? | [Paired sparse example](../quickstart.md#2-paired-sparse-planar-fpca) | Actual retained timestamps, covariance and smoothing |
| Does a declared condition vary over time? | [Functional regression example](../quickstart.md#3-functional-regression) | Independent unit, fixed design, estimation target |

Alternatively download the [tiny invented CSV and runnable script](../tutorials/reproducible-starter.md), then inspect the schematic path using the [synthetic trajectory explorer](../tools/trajectory-explorer.md).

## 3. Explore the figure before interpreting a statistic

<div class="grid cards" markdown>

- **FPCA interpretation**

  ![Deterministic synthetic principal component illustration](../assets/gallery/fpca-component.svg)

  Interpret component shapes as modes of variability, not evidence for an unmeasured psychological factor.

  [FPCA guidance](../guides/fpca.md) · [Visual explorer](../tools/figure-storyboard.md)

- **Sparse-support assumptions**

  ![Deterministic synthetic sparse covariance surface](../assets/gallery/sparse-fpca-covariance.svg)

  Retain sparse observations rather than constructing an unexplained common grid.

  [Sparse FPCA](../guides/sparse-irregular-fpca.md) · [Data preparation](../guides/input-schemas.md)

- **Regression and uncertainty**

  ![Deterministic synthetic time-varying regression coefficient](../assets/gallery/function-on-scalar-coefficient.svg)

  Report the target, independent sampling unit and method-specific calibration requirements.

  [Functional regression](../workflows/experimental-functional-regression.md) · [Reporting](../methods/reporting.md)

</div>

## 4. Select the next research-level step

Match your actual question using the [interactive method selector](../tools/method-selector.md) and the [ten-workflow comparison](../tools/workflow-comparison.md). The ten module-scoped W1–W4 workflows are in published stable 1.2.0; E1–E4 research helpers are experimental.

!!! warning "Do not treat an attractive figure as validation"
    A successful fit or illustrative band does not justify whole-function coverage, identify the missing gaze mechanism, or establish device accuracy. Consult the [scientific limitations](../methods/limitations.md) and the unresolved [whole-function inference #289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [missing-gaze #296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) before reporting empirical uncertainty.

## 5. Save a reproducible research trail

Preserve the package version, recorded data provenance, time and coordinate units, participant/trial grouping, exclusions, declared analysis and model settings, diagnostic plots and the [workflow output bundle](../articles/reproducible-workflow-bundles.md).

[Research reporting checklist](../methods/reporting.md) · [Research validation evidence](../research/index.md)
