---
title: Download and run a complete 1.2.0 gaze starter
description: A small fixed synthetic CSV and executable Python analysis script for common-grid planar trajectories.
---

# Downloadable runnable tutorial

Use a **deterministic, invented synthetic eye-tracking teaching dataset**, not recordings from humans. The CSV and Python runner are version-controlled in the same repository. This is a first execution/format test, not a validation dataset for inference.

<div class="grid cards" markdown>

- **Dataset: 12 trajectories × 41 common-grid times**

  Normalized horizontal and vertical coordinates for 12 invented independent participant curves, with time in seconds and one synthetic trial per participant.

  [Download CSV](../downloads/synthetic-gaze-common-grid.csv){ .md-button }

- **Runnable Python script**

  Loads the CSV, checks grid and coordinate contracts, imports with the documented stable API and fits descriptive planar MFPCA.

  [Download Python source](../downloads/run_synthetic_gaze.py){ .md-button }

</div>

## Install and execute

Save both files in the **same directory** and run:

~~~bash
python -m pip install eyetrajectoriespy==1.2.0 pandas
python run_synthetic_gaze.py
~~~

The runner checks 12 curves × 41 ordered samples, finite nonmissing normalized coordinates and a common grid, calls the documented <code>from_long_dataframe()</code> import, then fits <code>fit_mfpca()</code> with a fixed two-component setting. It prints a descriptive fitted-variance summary. No random selection, hidden interpolation or inferred statistical coverage is involved.

## What to try next

1. Compare the CSV's two coordinate columns in their recorded units and time support.
2. Inspect the exact schema and metadata before changing the number of curves.
3. Follow the [complete production-style dense workflow](../quickstart.md) for module-scoped 1.2 orchestration, reporting and a reproducible component SVG.
4. For paired sparse or coordinate-asynchronous data, **use the corresponding native representation instead of removing CSV rows and pretending the sample times are equivalent**.

!!! warning "Scope"
    This small fixture is pedagogical. Twelve independent invented curves cannot establish method power, general FPC consistency, confidence-band coverage, participant-level population claims or performance on recorded gaze. The W3 whole-function and missingness restrictions in [the research library](../research/index.md) remain unchanged.

[Workflow method selector](../tools/method-selector.md) · [Input schema guide](../guides/input-schemas.md) · [Examples in GitHub](https://github.com/stefanosbalaskas/eyetrajectoriespy/tree/main/examples)
