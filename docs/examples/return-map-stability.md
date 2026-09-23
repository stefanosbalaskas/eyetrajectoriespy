# Worked example: empirical return-map stability

This experimental workflow is for repeated approximate cycles. It deliberately stops short of claiming classical Floquet stability.

## Synthetic decaying cycle

```python
import numpy as np
from eyetrajectoriespy import TrajectorySet

time = np.linspace(0.0, 20.0 * np.pi, 2001)
amplitude = np.exp(-0.02 * time)
x = amplitude * np.sin(time)
y = amplitude * np.cos(time)

cycle = TrajectorySet(
    time=time,
    values=np.stack([x, y], axis=1)[None, :, :],
    curve_ids=("cycle",),
    dimension_names=("x", "y"),
    time_unit="s",
    coordinate_system="arbitrary",
)
```

## Declare the Poincare section

```python
from eyetrajectoriespy import poincare_crossings

crossings = poincare_crossings(
    cycle,
    curve=0,
    section_dimension="x",
    section_value=0.0,
    direction="positive",
    state_dimensions=("y",),
)

print(crossings.n_crossings)
```

The crossing times and returned state values are linearly interpolated rather than snapped to the sample grid.

## Fit a local return map

```python
from eyetrajectoriespy import fit_local_return_map

fit = fit_local_return_map(
    crossings,
    reference="mean",
    n_neighbors=8,
)

print(fit.jacobian)
print(fit.r_squared)
```

A radius-based neighborhood can be used instead, but exactly one neighborhood policy must be declared.

## Summarize contraction or expansion

```python
from eyetrajectoriespy import return_map_stability

stability = return_map_stability(
    fit,
    tolerance=1e-6,
)

print(stability.eigenvalues)
print(stability.spectral_radius)
print(stability.classification)
```

For this deterministic synthetic decaying cycle, the return map is contracting.

## Plot the map

```python
from eyetrajectoriespy import plot_poincare_return_map

plot_poincare_return_map(
    crossings,
    fit=fit,
)
```

## Interpretation boundary

The fitted Jacobian is a local empirical regression coefficient matrix for successive section crossings.

It is **not**:

- a variational-equation state-transition matrix;
- a monodromy matrix;
- a Floquet multiplier computation;
- proof of a deterministic limit cycle in behavioral gaze.

For real gaze, treat the result as an experimental cycle-to-cycle stability descriptor and accompany it with sensitivity analysis for section placement, state definition, neighborhood size, preprocessing, and repeated-cycle count.
