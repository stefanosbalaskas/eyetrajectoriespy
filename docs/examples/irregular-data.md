# Worked example: irregular sampling and gaps

Irregular data should not be forced onto a common grid by unrestricted interpolation.

```python
import numpy as np
from eyetrajectoriespy import from_irregular_long_dataframe

grid = np.linspace(0, 2, 121)

gaze = from_irregular_long_dataframe(
    samples,
    curve_columns=["participant_id", "trial_id"],
    time_column="time_s",
    grid=grid,
    method="linear",
    max_gap=0.10,
)
```

`max_gap` retains long unobserved intervals as missing. FPCA then refuses unresolved missing values, forcing a study-level decision instead of silently drawing an interpolated line through tracker loss.
