# Population bootstrap for RQA metrics

This example estimates uncertainty in population-average RQA summaries across repeated participant trials.

## 1. Build repeated synthetic trajectories

~~~python
import numpy as np
import pandas as pd
from eyetrajectoriespy import TrajectorySet

time = np.arange(160, dtype=float) * 0.01
values = []
participants = []

for p in range(10):
    for trial in range(3):
        phase = 0.08 * p + 0.04 * trial
        x = np.sin(2 * np.pi * 1.8 * time + phase)
        values.append(x[:, None])
        participants.append(f"P{p + 1:02d}")

gaze = TrajectorySet(
    time=time,
    values=np.asarray(values),
    curve_ids=tuple(f"curve-{i + 1:02d}" for i in range(len(values))),
    dimension_names=("x",),
    metadata=pd.DataFrame({"participant_id": participants}),
    time_unit="s",
    coordinate_system="normalized",
)
~~~

## 2. Estimate participant-level mean RQA uncertainty

~~~python
from eyetrajectoriespy import bootstrap_rqa_metric_means

fit = bootstrap_rqa_metric_means(
    gaze,
    dimensions=("x",),
    metrics=("recurrence_rate", "determinism", "laminarity"),
    radius=0.18,
    theiler_window=2,
    min_diagonal_length=2,
    min_vertical_length=2,
    unit="participant",
    participant_column="participant_id",
    confidence_level=0.95,
    n_bootstrap=1000,
    random_state=27,
)

print(fit.summary_table)
~~~

The inferential sample size is 10 participants, not 30 trials and not the number of recurrence points.

## 3. Inspect the audit tables

~~~python
print(fit.observed_table.head())
print(fit.unit_table)
~~~

`observed_table` contains each curve's realized recurrence radius, recurrence rate, Theiler resolution, and selected metrics.

`unit_table` shows the participant-average RQA metrics actually resampled.

## 4. Plot the intervals

~~~python
from eyetrajectoriespy import plot_rqa_metric_mean_bootstrap

ax = plot_rqa_metric_mean_bootstrap(fit)
~~~

Each interval is marginal for one selected metric. The method does not provide a simultaneous multi-metric familywise band.

## 5. Target-RR mode

If the protocol instead controls recurrence density:

~~~python
targeted = bootstrap_rqa_metric_means(
    gaze,
    dimensions=("x",),
    metrics=("determinism", "laminarity"),
    target_recurrence_rate=0.08,
    theiler_window=2,
    unit="participant",
    participant_column="participant_id",
    n_bootstrap=1000,
    random_state=27,
)

print(targeted.observed_table[[
    "curve_id",
    "resolved_radius",
    "achieved_recurrence_rate",
]])
~~~

Do not include `recurrence_rate` among the inferential outcomes here: it is controlled by the target-RR design.

## 6. Reporting helper

~~~python
from eyetrajectoriespy import rqa_metric_mean_bootstrap_reporting_text

print(rqa_metric_mean_bootstrap_reporting_text(fit))
~~~

## Scope

The result describes between-participant sampling uncertainty in participant-average trial-level RQA summaries.

It does not estimate a confidence interval for RQA inside one single trajectory, and it does not include uncertainty from choosing the radius or other RQA parameters.

The executable counterpart is `examples/rqa_population_bootstrap.py`.
