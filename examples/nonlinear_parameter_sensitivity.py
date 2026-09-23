"""Declared RQA, Rosenstein-LLE, and Kantz-LLE parameter sensitivity."""

import numpy as np

from eyetrajectoriespy import (
    TrajectorySet,
    kantz_parameter_sensitivity,
    kantz_parameter_sensitivity_reporting_text,
    lyapunov_parameter_sensitivity,
    lyapunov_parameter_sensitivity_reporting_text,
    rqa_parameter_sensitivity,
    rqa_parameter_sensitivity_reporting_text,
)


n = 420
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
    provenance={"example": "nonlinear parameter sensitivity"},
)

rqa = rqa_parameter_sensitivity(
    trajectory,
    curve="logistic",
    dimensions=("x",),
    embedding_dimensions=(2, 3),
    delays=(1,),
    radii=(0.05, 0.10),
    theiler_windows=(2, 6),
    min_diagonal_lengths=(2, 3),
    min_vertical_lengths=(2,),
)

print(
    rqa.summary_table[
        ["metric", "minimum", "median", "maximum", "range", "finite_fraction"]
    ]
)
print(rqa_parameter_sensitivity_reporting_text(rqa))

lle = lyapunov_parameter_sensitivity(
    trajectory,
    curve="logistic",
    dimensions=("x",),
    embedding_dimensions=(2, 3),
    delays=(1,),
    theiler_windows=(6, 10),
    fit_intervals=((1, 4), (2, 5)),
    max_horizon=8,
)

print(
    lle.summary_table[
        [
            "metric",
            "minimum",
            "median",
            "maximum",
            "range",
            "positive_specification_fraction",
        ]
    ]
)
print(lyapunov_parameter_sensitivity_reporting_text(lle))


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

print(
    kantz.summary_table[
        [
            "metric",
            "minimum",
            "median",
            "maximum",
            "range",
            "positive_specification_fraction",
        ]
    ]
)
print(
    kantz.table[
        [
            "specification_id",
            "requested_radius",
            "resolved_radius",
            "min_neighbors",
            "initial_supported_reference_fraction",
            "minimum_reference_count_in_fit",
            "minimum_pair_count_in_fit",
        ]
    ].head()
)
print(kantz_parameter_sensitivity_reporting_text(kantz))
