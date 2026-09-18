# Worked example: compositional AOI trajectories

```python
import numpy as np
from eyetrajectoriespy import (
    fit_compositional_fpca,
    reconstruct_compositional_fpca,
    simulate_aoi_probability_trajectories,
)

probs = simulate_aoi_probability_trajectories(
    n_curves=80,
    n_time=101,
    n_aoi=4,
)

fit = fit_compositional_fpca(
    probs,
    reference_dimension=3,
    epsilon=1e-8,
    n_components=0.95,
)

reconstructed = reconstruct_compositional_fpca(fit)
assert np.allclose(reconstructed.sum(axis=2), 1.0)
```

The reconstruction remains a valid probability composition at every time point.
