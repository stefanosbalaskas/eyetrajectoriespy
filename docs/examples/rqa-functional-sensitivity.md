# Functional RQA sensitivity and participant-level inference

This example shows a complete 0.25 workflow for a repeated-trial design.

The goal is not to find a window size automatically. We predeclare several plausible window/step specifications, inspect their consequences, then fit inference for one separately justified primary specification.

## Synthetic repeated-trial data

```python
import numpy as np
import pandas as pd

from eyetrajectoriespy import TrajectorySet

time = np.arange(180, dtype=float) * 0.01
values = []
participants = []
curve_ids = []

for participant_index in range(6):
    participant_id = f"P{participant_index + 1:02d}"
    for trial in range(2):
        phase = 0.18 * participant_index + 0.08 * trial
        signal = (
            np.sin(2 * np.pi * 1.7 * time + phase)
            + 0.12 * np.sin(2 * np.pi * 0.55 * time + 0.4 * phase)
        )
        values.append(signal)
        participants.append(participant_id)
        curve_ids.append(f"{participant_id}_T{trial + 1}")

gaze = TrajectorySet(
    time=time,
    values=np.asarray(values)[:, :, None],
    curve_ids=tuple(curve_ids),
    dimension_names=("x",),
    metadata=pd.DataFrame({"participant_id": participants}),
    coordinate_system="normalized",
    time_unit="s",
)
```

## 1. Declare a sensitivity grid

```python
from eyetrajectoriespy import windowed_rqa_sensitivity

sensitivity = windowed_rqa_sensitivity(
    gaze,
    metrics=("recurrence_rate", "determinism", "laminarity"),
    window_step_pairs=((40, 20), (40, 10), (60, 20)),
    radius=0.35,
    theiler_window=2,
    dimensions=("x",),
)
```

Nothing in this function chooses among the three specifications.

Inspect the design consequences:

```python
print(
    sensitivity.design_table[
        [
            "specification_id",
            "window_samples",
            "step_samples",
            "overlap_fraction",
            "profile_grid_spacing_time",
            "fraction_analyzed_samples_reused",
            "mean_window_memberships_per_analyzed_sample",
            "max_window_memberships",
        ]
    ]
)
```

For the same 40-sample window, moving from a 20-sample step to a 10-sample step makes the derived functional grid denser and increases source-sample reuse. It does **not** create twice as many independent observations.

## 2. Compare profiles without interpolation

```python
print(
    sensitivity.pairwise_table[
        [
            "specification_a",
            "specification_b",
            "curve_id",
            "metric",
            "n_common_centers",
            "rmse",
            "correlation",
        ]
    ].head()
)
```

Comparisons are restricted to exact shared centers. If different window widths shift all centers relative to one another, `n_common_centers` can be zero. The package leaves the corresponding RMSE/correlation undefined instead of silently interpolating.

A visual sensitivity overlay is also available:

```python
from eyetrajectoriespy import plot_windowed_rqa_sensitivity

ax = plot_windowed_rqa_sensitivity(
    sensitivity,
    curve="P01_T1",
    metric="determinism",
)
```

## 3. Infer a mean at the participant level

Suppose the 40/20 specification was the predeclared primary analysis. Because each participant contributes two trials, the independent inference unit should be the participant rather than the twelve trial curves.

```python
from eyetrajectoriespy import windowed_rqa_functional_mean_band

mean_band = windowed_rqa_functional_mean_band(
    gaze,
    metrics=("recurrence_rate", "determinism", "laminarity"),
    window=40,
    step=20,
    unit="participant",
    participant_column="participant_id",
    radius=0.35,
    theiler_window=2,
    dimensions=("x",),
    confidence_level=0.95,
    n_multiplier=2000,
    random_state=42,
)
```

The six participants, not the window rows and not the twelve repeated trial curves, are the six independent units used by the band.

```python
print(mean_band.band.n_units)
print(mean_band.band.unit_ids)
```

Within each multiplier draw, each participant residual function remains a complete time-by-metric object. This preserves the observed within-function covariance structure used by the maximum statistic.

## 4. Reporting

```python
from eyetrajectoriespy import (
    windowed_rqa_mean_band_reporting_text,
    windowed_rqa_sensitivity_reporting_text,
)

print(windowed_rqa_sensitivity_reporting_text(sensitivity))
print(windowed_rqa_mean_band_reporting_text(mean_band))
```

Report the sensitivity grid even when it does not change the substantive conclusion. If profiles differ materially across specifications, that dependency is part of the result rather than a nuisance to hide.

## Boundaries

This workflow does not justify treating overlapping windows as independent. It also does not implement a moving/block bootstrap inside a single participant trajectory. If there is only one long time series and the inferential target depends on within-series resampling, a separate time-series resampling contract is required.

The executable version is `examples/rqa_functional_sensitivity.py`.
