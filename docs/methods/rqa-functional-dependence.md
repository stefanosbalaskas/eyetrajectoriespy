# Functional RQA sensitivity and dependence

Version 0.25 treats the sliding-window choices behind functional RQA as part of the scientific estimand rather than as hidden tuning constants.

The workflow is

```text
source gaze curve
    -> declared sliding-window RQA specification
    -> RQA metric function on window centers
    -> sensitivity across predeclared window/step specifications
    -> downstream functional analysis or unit-level inference
```

This layer does **not** select a universally optimal window width or step. Window width changes the temporal scale over which recurrence structure is summarized; step changes the grid on which the derived RQA function is observed and, when smaller than the window, changes deterministic sample reuse.

## Why window and step need sensitivity analysis

A sliding-window RQA profile is conditional on its window geometry. A shorter window can localize changes more sharply but contains fewer state pairs and line structures. A wider window pools a larger time region and can smooth or delay local changes. A smaller step produces a denser output grid but usually reuses more source samples.

The package therefore keeps these quantities distinct:

- **window span** — the observed time span summarized by one RQA estimate;
- **profile-grid spacing** — the temporal distance between successive derived RQA estimates;
- **sample overlap** — the fraction of source samples shared by adjacent windows;
- **sample-reuse diagnostics** — how many analyzed samples occur in multiple windows and their mean/maximum window memberships;
- **statistical independence** — a property of the scientific sampling units, not something inferred from the quantities above.

In particular, profile-grid spacing is **not** reported as an effective independent temporal resolution or an effective sample size.

## Declared sensitivity grid

Use `windowed_rqa_sensitivity()` with an explicit set of scientifically meaningful window/step pairs.

```python
from eyetrajectoriespy import windowed_rqa_sensitivity

sensitivity = windowed_rqa_sensitivity(
    gaze,
    metrics=("recurrence_rate", "determinism", "laminarity"),
    window_step_pairs=((40, 20), (40, 10), (60, 20)),
    radius=0.35,
    theiler_window=2,
    dimensions=("x", "y"),
)
```

The function returns every complete `WindowedRQAFunctionalResult`; it does not collapse the grid to a preferred specification.

### Design table

`design_table` records, for each declared specification:

- requested and resolved window/step values;
- window span in source time;
- derived-profile grid spacing;
- number of complete windows;
- sample overlap and overlap fraction;
- analyzed source-sample coverage;
- fraction of analyzed source samples reused by more than one window;
- mean and maximum window memberships;
- derived functional support;
- explicit trailing-tail count.

These are design/dependence diagnostics. They are not inferential degrees of freedom.

### Descriptive summaries

`summary_table` gives per-curve/per-metric means, standard deviations, minima, maxima, and finite-window counts for each specification. These summaries are deliberately descriptive.

### Pairwise profile comparisons

`pairwise_table` compares specifications only at **exact shared window-center times**. No interpolation is used to make two specifications appear commensurate.

For each curve and metric it reports, when defined:

- number of exact shared centers;
- RMSE;
- mean absolute difference;
- maximum absolute difference;
- correlation.

If two specifications have no exact common centers, the count is zero and comparison statistics remain undefined. The package does not invent an alignment grid.

## Dependence-aware mean inference

When the scientific target is the population mean of a derived RQA function, use `windowed_rqa_functional_mean_band()`.

```python
from eyetrajectoriespy import windowed_rqa_functional_mean_band

band = windowed_rqa_functional_mean_band(
    gaze,
    metrics=("determinism", "laminarity"),
    window=40,
    step=20,
    unit="participant",
    participant_column="participant_id",
    radius=0.35,
    theiler_window=2,
    dimensions=("x", "y"),
    confidence_level=0.95,
    n_multiplier=2000,
    random_state=42,
)
```

The function first constructs the complete RQA-derived functional curves and then reuses the package's existing studentized Gaussian multiplier band.

The important sampling rule is:

> **complete source-curve or participant-level functions are the inference units; individual sliding windows are never resampled as if independent.**

With `unit="participant"`, repeated trial-level RQA functions are first averaged within participant and participants receive equal weight. With `unit="curve"`, each source curve is assumed to be an independent sampling unit; that option is appropriate only when the study design supports it.

One random multiplier is applied to each independent residual function across its full time-by-metric grid. Thus the within-function temporal shape is retained in each bootstrap draw rather than decomposed into independent window observations.

## What the band does and does not cover

The returned band is simultaneous over the **observed RQA window-center grid and selected metric dimensions** for the chosen window/step and recurrence specification.

It does not automatically include uncertainty from:

- selecting the window/step after seeing the data;
- choosing the radius or target recurrence rate;
- selecting embedding parameters;
- preprocessing choices;
- participant sampling designs not represented by the declared unit;
- a single long trajectory with no independent curves/participants;
- within-trajectory block-length selection.

A true moving/block bootstrap within one long gaze trajectory is a separate method with its own stationarity, block construction, and block-length contract. Version 0.25 does not label the whole-function participant/curve bootstrap as such.

## Pre-specification

For confirmatory use, predeclare:

1. the primary window/step pair;
2. the sensitivity grid;
3. recurrence-state dimensions and any embedding;
4. radius versus target-RR policy;
5. metric and Theiler window;
6. minimum diagonal and vertical line lengths;
7. selected RQA functional outcomes;
8. independent inference unit;
9. participant column when repeated trials exist;
10. confidence level, multiplier count, and seed.

The sensitivity grid should diagnose how conclusions depend on temporal aggregation. It should not be searched until a visually convenient answer appears.

## Current evidence boundary

Sliding-window RQA is an established way to obtain time-varying recurrence summaries, and recent eye-tracking work has explicitly highlighted the sensitivity of gaze recurrence profiles to fixed window choices. The stronger contribution of this package is narrower: retain continuous-trajectory provenance, make window/step dependence inspectable, and connect the derived RQA functions to functional-data analysis while keeping inference at the independent source-unit level.

See the [worked example](../examples/rqa-functional-sensitivity.md), [nonlinear guide](../guides/nonlinear-dynamics.md), [limitations](limitations.md), and [RQA software conventions](rqa-software-conventions.md).
