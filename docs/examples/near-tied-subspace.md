# Worked example: stable subspace, unstable FPC labels

This example shows why near-tied FPCs should sometimes be interpreted as an eigenspace rather than as individually fixed axes.

## Fit a reference MFPCA

```python
import numpy as np
from dataclasses import replace

from eyetrajectoriespy import (
    compare_fpca_subspaces,
    fit_mfpca,
    fpca_eigenvalue_gap_table,
    simulate_planar_trajectories,
)

gaze = simulate_planar_trajectories(
    n_participants=12,
    trials_per_participant=3,
    n_time=61,
    random_state=42,
)

fit = fit_mfpca(
    gaze,
    n_components=4,
    scaling="dimension_sd",
)
```

Inspect the retained adjacent eigengaps:

```python
print(fpca_eigenvalue_gap_table(fit))
```

No near-tie label is created unless you explicitly provide a threshold.

## Rotate FPC1 and FPC2 without changing their span

A 45-degree rotation creates new basis axes inside the same two-dimensional space:

```python
theta = np.pi / 4
rotation = np.array([
    [np.cos(theta), -np.sin(theta)],
    [np.sin(theta),  np.cos(theta)],
])

components = fit.components.copy()
components[:2] = np.einsum(
    "ab,btd->atd",
    rotation,
    fit.components[:2],
)

scores = fit.scores.copy()
scores[:, :2] = fit.scores[:, :2] @ rotation.T

rotated = replace(
    fit,
    components=components,
    scores=scores,
)
```

## Compare one FPC versus the two-FPC span

```python
fpc1 = compare_fpca_subspaces(
    fit,
    rotated,
    start_component=0,
    n_components=1,
)

pair = compare_fpca_subspaces(
    fit,
    rotated,
    start_component=0,
    n_components=2,
)

print(fpc1.principal_cosines)
print(pair.principal_cosines)
```

For a 45-degree rotation, FPC1 alone has cosine similarity about 0.707.

The two-dimensional span is unchanged, so both principal cosines are approximately 1 and the normalized projector distance is approximately 0.

That is the central distinction:

> an individual FPC axis can move while the scientifically relevant eigenspace remains stable.

## Bootstrap the observed eigenspace

```python
from eyetrajectoriespy import (
    bootstrap_fpca_subspace_stability,
    fpca_subspace_stability_reporting_text,
    plot_fpca_subspace_stability,
    summarise_fpca_subspace_stability,
)

stability = bootstrap_fpca_subspace_stability(
    gaze,
    start_component=0,
    n_components=2,
    n_bootstrap=200,
    scaling="dimension_sd",
    resample_unit="participant",
    participant_column="participant_id",
    random_state=42,
)

print(summarise_fpca_subspace_stability(stability))
print(fpca_subspace_stability_reporting_text(stability))
plot_fpca_subspace_stability(stability)
```

## Interpretation

If individual FPC1/FPC2 matching is weak but the two-dimensional subspace is stable, report the block-level result and avoid assigning rigid psychological meanings to the orientation of each axis.

If the subspace is also unstable, interpret the entire low-dimensional structure cautiously and inspect sample size, influential participants, preprocessing, and the retention boundary.

## Failure cases

The API rejects:

- component blocks outside the common fitted range;
- mismatched grids, dimensions, coordinate systems, or time units;
- invalid bootstrap counts or resampling units;
- component blocks exceeding the non-zero sample rank;
- missing participant IDs in participant-level bootstrap.
