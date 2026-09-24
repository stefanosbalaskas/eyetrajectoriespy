"""Function-on-scalar regression with simultaneous coefficient bands."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from eyetrajectoriespy import (
    TrajectorySet,
    bootstrap_function_on_scalar_coefficients,
    fit_function_on_scalar_regression,
    function_on_scalar_coefficient_frame,
    function_on_scalar_reporting_text,
    function_on_scalar_simultaneous_bands,
    plot_function_on_scalar_coefficients,
)


rng = np.random.default_rng(2026)
n = 36
time = np.linspace(0.0, 1.5, 61)
condition = np.repeat([0.0, 1.0], n // 2)

beta0 = 0.2 * np.sin(2.0 * np.pi * time / 1.5)
beta_condition = 0.35 * np.exp(-((time - 0.8) / 0.25) ** 2)
noise = rng.normal(0.0, 0.12, size=(n, time.size))
response = (
    beta0[None, :]
    + condition[:, None] * beta_condition[None, :]
    + noise
)

trajectories = TrajectorySet(
    time=time,
    values=response[:, :, None],
    curve_ids=tuple(f"C{i:02d}" for i in range(n)),
    dimension_names=("metric",),
    coordinate_system="arbitrary",
    time_unit="s",
)
design = pd.DataFrame(
    {
        "curve_id": trajectories.curve_ids,
        "condition": condition,
    }
)

fit = fit_function_on_scalar_regression(
    trajectories,
    design,
    predictors=("condition",),
)
boot = bootstrap_function_on_scalar_coefficients(
    fit,
    n_bootstrap=120,
    multiplier="rademacher",
    random_state=2026,
)
band = function_on_scalar_simultaneous_bands(
    boot,
    confidence_level=0.95,
    simultaneous_scope="coefficient",
)

table = function_on_scalar_coefficient_frame(fit, band=band)
assert fit.coefficient_names == ("Intercept", "condition")
assert band.lower.shape == fit.coefficients.shape
assert table.shape[0] == 2 * time.size
assert np.all(band.lower <= fit.coefficients)
assert np.all(fit.coefficients <= band.upper)

ax = plot_function_on_scalar_coefficients(
    band,
    coefficient="condition",
    dimension="metric",
)
plt.close(ax.figure)

print(function_on_scalar_reporting_text(fit, band=band))
print(table.query("coefficient == 'condition'").head().to_string(index=False))
