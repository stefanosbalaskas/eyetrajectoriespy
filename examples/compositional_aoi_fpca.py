"""Simplex-preserving functional analysis of AOI probability trajectories."""

import numpy as np

from eyetrajectoriespy import (
    fit_compositional_fpca,
    reconstruct_compositional_fpca,
    simulate_aoi_probability_trajectories,
)


def main() -> None:
    probs = simulate_aoi_probability_trajectories(n_curves=60, n_time=81, n_aoi=4)
    result = fit_compositional_fpca(probs, reference_dimension=3, n_components=0.95)
    reconstructed = reconstruct_compositional_fpca(result)
    assert np.allclose(reconstructed.sum(axis=2), 1.0)
    print("retained components:", result.fpca.n_components)
    print("minimum reconstructed probability:", reconstructed.min())


if __name__ == "__main__":
    main()
