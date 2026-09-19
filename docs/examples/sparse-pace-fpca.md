# Worked example: sparse PACE FPCA without interpolation

This example uses synthetic sparse observations with a different native time grid for every curve.

The goal is to estimate variation in the latent x(t) process **without first interpolating every curve to a shared grid**.

## Generate sparse irregular trajectories

```python
import numpy as np
import pandas as pd

from eyetrajectoriespy import IrregularTrajectorySet

rng = np.random.default_rng(2026)
dense_time = np.linspace(0.0, 1.0, 41)

times = []
values = []
curve_ids = []
participants = []

for i in range(18):
    keep = np.sort(
        rng.choice(
            len(dense_time),
            size=12,
            replace=False,
        )
    )
    time = dense_time[keep]

    amplitude = rng.normal(scale=0.25)
    x = (
        np.sin(2 * np.pi * time)
        + amplitude * np.cos(np.pi * time)
        + rng.normal(scale=0.05, size=len(time))
    )

    times.append(time)
    values.append(x[:, None])
    curve_ids.append(f"P{i + 1:02d}|1")
    participants.append(f"P{i + 1:02d}")

gaze = IrregularTrajectorySet(
    time=tuple(times),
    values=tuple(values),
    curve_ids=tuple(curve_ids),
    dimension_names=("x",),
    metadata=pd.DataFrame(
        {"participant_id": participants}
    ),
    coordinate_system="normalized",
    time_unit="s",
)
```

No common grid has been constructed.

## Audit the observation design

```python
from eyetrajectoriespy import (
    plot_sparse_irregular_dimension,
    sparse_dimension_summary,
)

summary = sparse_dimension_summary(
    gaze,
    dimension="x",
)

print(summary)
plot_sparse_irregular_dimension(
    gaze,
    dimension="x",
)
```

Before fitting, check:

- number of observations per curve;
- domain coverage;
- large observed intervals;
- non-finite placeholders.

A sparse estimator is not permission to ignore poor or systematically missing observation designs.

## Fit FDApy UFPCA and recover PACE scores

Install the optional dependency:

```bash
pip install -e ".[sparse]"
```

Use Python 3.11 or 3.12 for this optional backend under the current FDApy/NumPy dependency line. The eyetrajectoriespy core remains available on Python 3.13.

Then fit:

```python
from eyetrajectoriespy import fit_sparse_fpca_fdapy

result = fit_sparse_fpca_fdapy(
    gaze,
    dimension="x",
    n_components=3,
    fit_smoothing="PS",
    score_smoothing="LP",
    tol=1e-4,
    normalize=False,
    evaluation_grid=np.unique(np.concatenate(gaze.time)),
)
```

The function:

1. verifies that the selected dimension contains finite observed values;
2. converts each curve-specific grid directly to FDApy `IrregularFunctionalData`;
3. fits covariance-operator `UFPCA`;
4. obtains scores with `method="PACE"`;
5. evaluates the fitted functional structure on the explicit FDApy-compatible pooled observed grid;
6. preserves estimator settings and sample counts in provenance;
7. stores the FDApy model, sparse backend data, and reconstructed backend object.

No interpolation-to-common-grid step is inserted.

## Join scores to study metadata

```python
from eyetrajectoriespy import sparse_fpca_score_frame

scores = sparse_fpca_score_frame(result)
print(scores.head())
```

Because metadata are retained, participant, condition, or stimulus fields can be carried into a downstream analysis without rebuilding joins by row order.

## Reporting helper

```python
from eyetrajectoriespy import sparse_fpca_reporting_text

print(sparse_fpca_reporting_text(result))
```

The helper explicitly records:

- selected dimension;
- covariance-operator FDApy estimator;
- fitting and score smoothing;
- PACE scoring;
- component count;
- observation-count range;
- retained eigenvalues;
- tolerance;
- absence of common-grid interpolation.

## Sensitivity analysis

At minimum, consider whether conclusions change under plausible alternatives for:

- `n_components`;
- mean/covariance smoothing;
- score smoothing;
- PACE tolerance;
- whether the FDApy-compatible pooled evaluation grid was supplied explicitly;
- mean/covariance smoothing keyword parameters;
- inclusion criteria for extremely sparse curves.

Do not tune these settings only after inspecting downstream condition effects.

## Important interpretation boundary

This analysis estimates sparse FPCA for **x(t)** only.

Running the same workflow separately for y(t) does not create a joint x/y sparse MFPCA. If the research question concerns coupled two-dimensional gaze geometry, report the univariate limitation or use a separately validated multivariate sparse estimator.

## Failure case: NaN placeholders

```python
bad_values = list(gaze.values)
bad_values[0] = bad_values[0].copy()
bad_values[0][2, 0] = np.nan
```

The sparse adapter rejects this representation.

The adapter also rejects an evaluation grid outside the pooled observed support **or different from the sorted pooled observed sample-time grid**, and rejects component counts above the centered sample rank `n_curves - 1`.

The intended fix is not automatic interpolation. Resolve whether that row is an absent observation, invalid tracker sample, or another missing-data mechanism before fitting.

## Next steps

- [Sparse irregular FPCA guide](../guides/sparse-irregular-fpca.md)
- [Native irregular trajectories](../guides/irregular-trajectories.md)
- [Assumptions and diagnostics](../methods/assumptions.md)
- [Reporting checklist](../methods/reporting.md)
