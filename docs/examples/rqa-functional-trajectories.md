---
title: RQA-derived functional trajectories
---

# RQA-derived functional trajectories

Version 0.24 makes time-varying recurrence summaries first-class functional data.

The workflow is

$$
\text{continuous trajectory}
\rightarrow
\text{sliding-window RQA}
\rightarrow
F_i(t)=\{RR_i(t),DET_i(t),LAM_i(t),\ldots\}
\rightarrow
\text{FDA}.
$$

This is a package composition, not a claim that overlapping-window RQA curves are independent observations or that a new inferential theorem has been established.

## Build the functional RQA object

```python
from eyetrajectoriespy import windowed_rqa_trajectory_set

dynamic = windowed_rqa_trajectory_set(
    gaze,
    metrics=("recurrence_rate", "determinism", "laminarity"),
    window=2.0,
    step=0.5,
    window_units="seconds",
    step_units="seconds",
    radius=1.0,
    theiler_window=0.1,
    theiler_window_units="seconds",
    dimensions=("x", "y"),
)
```

The returned `WindowedRQAFunctionalResult` contains:

- `trajectories`: a native `TrajectorySet` whose time grid is the window-center grid;
- one functional dimension per explicitly selected RQA metric;
- every original per-curve `WindowedRQAResult`, including the radius used in every window;
- window and step sizes;
- overlap in samples and as a fraction of the window;
- explicit trailing-tail accounting;
- metric-unit metadata;
- the undefined-value policy.

No smoothing or interpolation is introduced.

## Overlap is dependence, not extra sample size

For window length $W$ and step $S$,

$$
\omega=\frac{\max(0,W-S)}{W}.
$$

When $\omega>0$, neighboring functional points reuse source samples. This is often scientifically useful because it gives a smoother time-resolved description, but the window rows are not independent replicates.

Even with non-overlapping windows, the package does not declare window rows independent: the underlying gaze process may remain serially dependent.

Use the source curve or participant as the sampling unit in downstream inference.

## Radius policy matters

With a fixed radius, recurrence rate may legitimately vary over time and across curves.

With `target_recurrence_rate=...`, recurrence density is controlled by construction. Therefore 0.24 refuses to expose `recurrence_rate` itself as a downstream functional outcome under target-rate mode. Metrics such as DET or LAM may still be selected, with the solved radius retained in each underlying window table.

## Undefined RQA metrics

A window may contain no qualifying diagonal or vertical lines. Some metrics are then mathematically undefined.

The default is fail closed:

```python
undefined_policy="raise"
```

To retain those windows explicitly as missing functional values, request:

```python
undefined_policy="keep"
```

No zero-filling or interpolation occurs.

## FDA after functionalization

When selected metrics are finite, the derived object can enter the existing FDA core:

```python
from eyetrajectoriespy import fit_mfpca

fit = fit_mfpca(
    dynamic.trajectories,
    n_components=3,
    scaling="dimension_sd",
)
```

`dimension_sd` is often appropriate when combining metrics with different numerical units, but it remains an explicit scientific choice. RR/DET/LAM are proportions, line lengths are measured in state steps, diagonal entropy is in nats, and CORM is a percentage of sequence length.

## Interpretation

A component of RQA functional trajectories describes how **time-varying recurrence organization differs across source curves**. It does not identify a latent cognitive state automatically.

For overlapping windows, do not report the number of windows as the inferential sample size. Report the number and definition of independent source units separately.

## Reporting

Report at minimum:

- source trajectory dimensions and units;
- window and step, including overlap;
- recurrence norm and radius policy;
- Theiler window;
- line-length thresholds;
- selected RQA functional metrics;
- undefined-value policy;
- source curve/participant sampling unit;
- downstream scaling and FDA model.

See the [nonlinear dynamics guide](../guides/nonlinear-dynamics.md), [reporting checklist](../methods/reporting.md), and [mathematical reference](../methods/mathematical-reference.md#functional-rqa-trajectories).
