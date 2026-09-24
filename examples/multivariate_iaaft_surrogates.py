"""Cross-spectrum-aware multivariate IAAFT surrogate example."""

import matplotlib.pyplot as plt
import numpy as np

from eyetrajectoriespy import (
    TrajectorySet,
    generate_multivariate_iaaft_surrogates,
    multivariate_iaaft_diagnostics_frame,
    multivariate_iaaft_reporting_text,
    plot_multivariate_iaaft_diagnostics,
)


rng = np.random.default_rng(12)
n = 180
x = np.empty(n, dtype=float)
y = np.empty(n, dtype=float)
x[0] = rng.normal()
y[0] = rng.normal()

for index in range(1, n):
    x[index] = 0.82 * x[index - 1] + rng.normal(0.0, 0.55)
    y[index] = (
        0.55 * y[index - 1]
        + 0.65 * x[index - 1]
        + rng.normal(0.0, 0.35)
    )

gaze = TrajectorySet(
    time=np.arange(n, dtype=float) * 0.01,
    values=np.column_stack([x, y])[None, :, :],
    curve_ids=("coupled",),
    dimension_names=("x", "y"),
    coordinate_system="unknown",
    time_unit="s",
)

result = generate_multivariate_iaaft_surrogates(
    gaze,
    curve="coupled",
    dimensions=("x", "y"),
    reference_dimension="x",
    n_surrogates=3,
    max_iterations=500,
    tolerance=1e-6,
    random_state=2026,
)

for surrogate in result.surrogates:
    for dimension_index in range(2):
        np.testing.assert_allclose(
            np.sort(surrogate[:, dimension_index]),
            np.sort(result.source_values[:, dimension_index]),
        )

diagnostics = multivariate_iaaft_diagnostics_frame(result)
assert diagnostics.shape[0] == result.n_surrogates
assert np.isfinite(result.spectral_errors).all()
assert np.isfinite(result.cross_spectral_errors).all()

ax = plot_multivariate_iaaft_diagnostics(result)
plt.close(ax.figure)

print(multivariate_iaaft_reporting_text(result))
print(diagnostics.to_string(index=False))
