# Worked example: 2-D evidence inspection

This example treats the whole x/y gaze path as the functional observation.

```python
from eyetrajectoriespy import (
    fit_mfpca,
    fpca_reporting_text,
    plot_fpca_component,
    simulate_planar_trajectories,
)

gaze = simulate_planar_trajectories(
    n_participants=30,
    trials_per_participant=6,
    n_time=121,
    random_state=7,
)

fit = fit_mfpca(
    gaze,
    n_components=0.95,
    scaling="dimension_sd",
)

print(fpca_reporting_text(fit))
plot_fpca_component(fit, component=0, dimension="x")
plot_fpca_component(fit, component=0, dimension="y")
```

## Interpretation workflow

1. Inspect the mean trajectory.
2. Plot x and y modes for every retained component.
3. Map spatial excursions onto known stimulus geometry.
4. Inspect score distributions by condition only after the trajectory mode is understood.
5. Avoid naming an FPC as a psychological construct without validation.

## Reporting example

> Joint multivariate functional PCA was fitted to normalized horizontal and vertical gaze coordinates over the 2-s trial window. Functional dimensions were scaled to equal integrated variance before decomposition. Components were retained to explain at least 95% of fitted functional variance. Component interpretation used mean ±2 score-SD trajectories in both coordinate dimensions.
