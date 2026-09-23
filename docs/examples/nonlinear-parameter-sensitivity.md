# Nonlinear parameter sensitivity

This worked example evaluates the same synthetic nonlinear signal under multiple defensible analysis specifications. The purpose is to inspect robustness, not to choose the combination that produces the largest effect.

## Data

```python
import numpy as np
from eyetrajectoriespy import TrajectorySet

n = 520
x = np.empty(n, dtype=float)
x[0] = 0.217

for i in range(n - 1):
    x[i + 1] = 4.0 * x[i] * (1.0 - x[i])

trajectory = TrajectorySet(
    time=np.arange(n, dtype=float) * 0.01,
    values=x[None, :, None],
    curve_ids=("logistic",),
    dimension_names=("x",),
    time_unit="s",
    coordinate_system="arbitrary",
)
```

The logistic map is used here only because it produces a compact deterministic example. It is not a model of gaze behavior.

## 1. RQA sensitivity

```python
from eyetrajectoriespy import rqa_parameter_sensitivity

rqa = rqa_parameter_sensitivity(
    trajectory,
    curve="logistic",
    dimensions=("x",),
    embedding_dimensions=(2, 3),
    delays=(1, 2),
    radii=(0.05, 0.10),
    theiler_windows=(2, 6),
    min_diagonal_lengths=(2, 3),
    min_vertical_lengths=(2,),
)
```

This evaluates the complete Cartesian product. Nothing is selected automatically.

```python
print(rqa.n_specifications)
print(
    rqa.table[
        [
            "specification_id",
            "embedding_dimension",
            "delay_samples",
            "requested_radius",
            "theiler_window_samples",
            "min_diagonal_length",
            "recurrence_rate",
            "determinism",
            "laminarity",
        ]
    ]
)
```

The descriptive range table is available directly:

```python
print(
    rqa.summary_table[
        [
            "metric",
            "n_finite",
            "minimum",
            "q25",
            "median",
            "q75",
            "maximum",
            "range",
        ]
    ]
)
```

A narrow range across a scientifically defensible grid is evidence that the numerical summary is less sensitive to those declared choices. It is not a confidence interval.

## 2. Plot one explicit RQA slice

```python
from eyetrajectoriespy import plot_rqa_sensitivity

ax = plot_rqa_sensitivity(
    rqa,
    parameter="requested_radius",
    metric="determinism",
    filters={
        "embedding_dimension": 2,
        "requested_delay": 1.0,
        "requested_theiler_window": 2.0,
        "min_diagonal_length": 2,
        "min_vertical_length": 2,
    },
)
```

The filters matter. Without them, many combinations would share the same radius value. The plotting helper refuses to average those combinations silently.

## 3. Rosenstein-LLE sensitivity

```python
from eyetrajectoriespy import lyapunov_parameter_sensitivity

lle = lyapunov_parameter_sensitivity(
    trajectory,
    curve="logistic",
    dimensions=("x",),
    embedding_dimensions=(2, 3),
    delays=(1, 2),
    theiler_windows=(6, 10),
    fit_intervals=((1, 4), (2, 5)),
    max_horizon=8,
)
```

Inspect the reconstruction and fit choices alongside the result:

```python
print(
    lle.table[
        [
            "specification_id",
            "embedding_dimension",
            "delay_samples",
            "theiler_window_samples",
            "fit_start_samples",
            "fit_end_samples",
            "exponent",
            "r_squared",
            "standard_error",
            "minimum_pair_count_in_fit",
        ]
    ]
)
```

## 4. Interpret sign robustness carefully

```python
exponent_summary = (
    lle.summary_table
    .set_index("metric")
    .loc["exponent"]
)

print(exponent_summary["minimum"])
print(exponent_summary["maximum"])
print(exponent_summary["positive_specification_fraction"])
```

The positive-specification fraction is not a p-value, posterior probability, or chaos probability. It simply answers:

> Across the analysis choices I declared, how often did the fitted local-divergence slope remain positive?

The more important diagnostic is the complete table: whether sign, magnitude, fit quality, or usable-pair support changes materially when the reconstruction or fit interval changes.

## 5. Kantz-LLE sensitivity

The neighborhood-based estimator adds radius and minimum-neighbor choices to the multiverse.

```python
from eyetrajectoriespy import kantz_parameter_sensitivity

kantz = kantz_parameter_sensitivity(
    trajectory,
    curve="logistic",
    dimensions=("x",),
    embedding_dimensions=(2, 3),
    delays=(1,),
    radii=(0.05, 0.08),
    min_neighbors=(1, 2),
    theiler_windows=(6, 10),
    fit_intervals=((1, 4), (2, 5)),
    max_horizon=8,
)
```

Inspect the scientific settings and support together:

```python
print(
    kantz.table[
        [
            "specification_id",
            "embedding_dimension",
            "radius",
            "min_neighbors",
            "theiler_window_samples",
            "fit_start_samples",
            "fit_end_samples",
            "exponent",
            "r_squared",
            "initial_supported_reference_fraction",
            "minimum_reference_count_in_fit",
            "minimum_pair_count_in_fit",
        ]
    ]
)
```

Plotting still requires a fully declared one-parameter slice:

```python
from eyetrajectoriespy import plot_kantz_sensitivity

ax = plot_kantz_sensitivity(
    kantz,
    parameter="radius",
    response="exponent",
    filters={
        "embedding_dimension": 2,
        "requested_delay": 1.0,
        "min_neighbors": 2,
        "requested_theiler_window": 6.0,
        "requested_fit_start": 1.0,
        "requested_fit_end": 4.0,
    },
)
```

The supported-reference fraction is not a model weight or uncertainty estimate. It only shows how much of the reconstructed state set satisfies the declared neighborhood rule.

## 6. Reporting text


```python
from eyetrajectoriespy import (
    kantz_parameter_sensitivity_reporting_text,
    lyapunov_parameter_sensitivity_reporting_text,
    rqa_parameter_sensitivity_reporting_text,
)

print(rqa_parameter_sensitivity_reporting_text(rqa))
print(lyapunov_parameter_sensitivity_reporting_text(lle))
print(kantz_parameter_sensitivity_reporting_text(kantz))
```

## What this example does not do

It does not:

- optimize a recurrence radius;
- select an embedding dimension;
- select an LLE fit interval;
- select a Kantz radius or minimum-neighbor rule;
- turn sensitivity-grid frequencies into inferential probabilities;
- bootstrap uncertainty;
- prove deterministic chaos.

The executable counterpart is `examples/nonlinear_parameter_sensitivity.py`.
