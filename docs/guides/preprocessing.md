# Preparing trajectories

Functional analysis does not remove eye-tracking preprocessing decisions. It makes some of them more consequential because the whole trajectory is retained.

## Common grid

Grid FPCA assumes curves are evaluated on a common grid. Use `from_irregular_long_dataframe()` or `resample_to_grid()` only after defining a scientifically appropriate grid.

```python
import numpy as np
from eyetrajectoriespy import from_irregular_long_dataframe

grid = np.linspace(0, 2, 121)
gaze = from_irregular_long_dataframe(
    data,
    curve_columns=["participant_id", "trial_id"],
    time_column="time_s",
    grid=grid,
    max_gap=0.10,
)
```

`max_gap` prevents interpolation across long unobserved intervals.

## Missingness

A blink, tracker loss, and a true zero coordinate are different states. Missing values remain `NaN` until the analyst explicitly handles them.

## Smoothing

`smooth_trajectories()` is opt-in and warns because smoothing can attenuate real abrupt changes.

## Time normalization

Normalizing every trial to `[0,1]` changes interpretation from **absolute time** to **trial progress**.

## Coordinate normalization

Scaling pixels to `[0,1]` makes resolution-independent coordinates; it does not make semantically different layouts comparable.
