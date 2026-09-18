# Worked example: trajectory → scalar outcome

Use FPCA scores when the goal is a transparent low-dimensional approximation to scalar-on-function regression.

```python
import numpy as np
from eyetrajectoriespy import (
    fit_mfpca,
    fit_scalar_on_function_regression,
    simulate_planar_trajectories,
)

gaze = simulate_planar_trajectories(n_participants=24, trials_per_participant=3)
fit = fit_mfpca(gaze, n_components=5, scaling="dimension_sd")

rng = np.random.default_rng(22)
outcome = 2 + 0.7 * fit.scores[:, 0] + rng.normal(0, 0.2, gaze.n_curves)
model = fit_scalar_on_function_regression(fit, outcome, n_components=3)
print(model.coefficients)
```

!!! warning
    For prediction studies, fit preprocessing and FPCA **inside training folds**. Do not estimate the functional basis on the full dataset before cross-validation.
