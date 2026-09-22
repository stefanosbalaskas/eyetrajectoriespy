"""CI-small empirical return-map stability workflow."""

import numpy as np

from eyetrajectoriespy import (
    TrajectorySet,
    fit_local_return_map,
    poincare_crossings,
    return_map_stability,
)


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

crossings = poincare_crossings(
    cycle,
    curve=0,
    section_dimension="x",
    section_value=0.0,
    direction="positive",
    state_dimensions=("y",),
)
fit = fit_local_return_map(
    crossings,
    reference="mean",
    n_neighbors=8,
)
stability = return_map_stability(fit)

assert crossings.n_crossings >= 8
assert fit.jacobian.shape == (1, 1)
assert 0 < stability.spectral_radius < 1
assert stability.classification == "contracting"

print("crossings:", crossings.n_crossings)
print("return-map spectral radius:", stability.spectral_radius)
