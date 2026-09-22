"""Executable checks linking package calculations to the documented equations."""

import numpy as np

from eyetrajectoriespy import (
    alr_transform,
    fit_mfpca,
    functional_l2_distance,
    functional_trapezoid_weights,
    inverse_alr,
    reconstruct_fpca,
    simulate_aoi_probability_trajectories,
    simulate_planar_trajectories,
)

gaze = simulate_planar_trajectories(
    n_participants=8,
    trials_per_participant=1,
    n_time=31,
    random_state=2105,
)

weights = functional_trapezoid_weights(gaze.time)
assert np.isclose(weights.sum(), gaze.time[-1] - gaze.time[0])

fit = fit_mfpca(gaze, n_components=3, scaling="dimension_sd")
manual_reconstruction = fit.mean[None, :, :] + np.einsum(
    "nk,ktd->ntd",
    fit.scores[:, :2],
    fit.components[:2],
)
api_reconstruction = reconstruct_fpca(fit, n_components=2)
assert np.allclose(manual_reconstruction, api_reconstruction)

d_ab = functional_l2_distance(
    gaze.values[0],
    gaze.values[1],
    time=gaze.time,
)
d_ba = functional_l2_distance(
    gaze.values[1],
    gaze.values[0],
    time=gaze.time,
)
assert np.isclose(d_ab, d_ba)

aoi = simulate_aoi_probability_trajectories(
    n_curves=8,
    n_time=31,
    n_aoi=4,
    random_state=2106,
)
z = alr_transform(aoi.values, reference_dimension=3, epsilon=1e-8)
restored = inverse_alr(z, reference_dimension=3, n_dimensions=4)
assert np.allclose(restored.sum(axis=2), 1.0)
assert np.allclose(restored, aoi.values)

print("quadrature domain:", weights.sum())
print("two-FPC reconstruction shape:", api_reconstruction.shape)
print("functional L2 distance:", d_ab)
print("ALR round-trip max error:", np.max(np.abs(restored - aoi.values)))
