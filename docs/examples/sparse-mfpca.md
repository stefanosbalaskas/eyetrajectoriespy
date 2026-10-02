# Sparse planar MFPCA / joint PACE

This worked example creates paired irregular x/y samples, fits the stable 0.12 native sparse multivariate estimator, and inspects joint PACE outputs without interpolating raw curves to a common grid.

```python
import numpy as np
import pandas as pd

from eyetrajectoriespy import (
    IrregularTrajectorySet,
    fit_sparse_mfpca,
    sparse_mfpca_reporting_text,
    sparse_mfpca_score_frame,
)

rng = np.random.default_rng(12012)
times = []
values = []
curve_ids = []
participants = []

for i in range(30):
    t = np.sort(np.r_[0.0, rng.uniform(0.03, 0.97, 8), 1.0])
    z1, z2 = rng.normal(size=2)
    x = 0.30 + 0.35 * t + 0.42 * z1 * np.sin(np.pi * t) + 0.08 * z2 * np.sin(2 * np.pi * t)
    y = 0.55 - 0.20 * t + 0.24 * z1 * np.cos(np.pi * t) - 0.18 * z2 * np.sin(2 * np.pi * t)
    xy = np.column_stack([x, y]) + rng.normal(0.0, 0.05, size=(t.size, 2))
    times.append(t)
    values.append(xy)
    curve_ids.append(f"P{i + 1:02d}|1")
    participants.append(f"P{i + 1:02d}")

irregular = IrregularTrajectorySet(
    time=tuple(times),
    values=tuple(values),
    curve_ids=tuple(curve_ids),
    dimension_names=("x", "y"),
    metadata=pd.DataFrame({"participant_id": participants}),
    coordinate_system="normalized",
    time_unit="s",
)

fit = fit_sparse_mfpca(
    irregular,
    dimensions=("x", "y"),
    n_components=2,
    evaluation_grid=np.linspace(0.0, 1.0, 41),
    mean_bandwidth=0.20,
    covariance_bandwidth=0.30,
    measurement_error="diagonal",
    measurement_error_variance=(0.0025, 0.0025),
    psd_action="project",
    score_ridge=0.0,
    score_failure_action="retain_nan",
)

print(sparse_mfpca_score_frame(fit).head())
print(sparse_mfpca_reporting_text(fit))
```

## What was *not* done

```text
native sparse sample
    !=
raw-trajectory interpolation

fitted population function evaluated at native time
    !=
raw-trajectory interpolation
```

The evaluation grid represents the fitted population mean/covariance/eigenfunctions. It is not a fabricated dense observation record for each participant.

## Inspect the joint structure

```python
print(fit.covariance_cxx.shape)
print(fit.covariance_cxy.shape)
print(fit.covariance_cyx.shape)
print(fit.covariance_cyy.shape)
print(fit.measurement_error_covariance)
print(fit.score_diagnostics.head())
```

For directional cross-covariance, `covariance_cyx` is the transpose-direction counterpart of `covariance_cxy`; do not assume C_xy(s,t) is itself symmetric.

## Continue

- [Sparse planar guide](../guides/sparse-multivariate-fpca.md)
- [Mathematical contract](../methods/mathematical-reference.md#sparse-mfpca-joint-pace)
- [Recovery evidence](../validation/sparse-mfpca-recovery.md)
- [Comparator sensitivity](../validation/sparse-mfpca-comparator-sensitivity.md)
