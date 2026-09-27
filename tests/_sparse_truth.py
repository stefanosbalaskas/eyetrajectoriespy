"""Private sparse-functional truth generator for 0.10 recovery tests."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SparseTruth:
    mean: callable
    eigenfunctions: tuple[callable, ...]
    eigenvalues: np.ndarray
    scores: np.ndarray
    noise_sd: float


def simulate_sparse_functional_truth(
    *,
    n_curves: int = 48,
    samples_per_curve: int = 12,
    noise_sd: float = 0.12,
    random_state: int = 202610,
):
    """Generate irregular observations from a known two-component process."""

    rng = np.random.default_rng(random_state)

    def mean_function(t):
        t = np.asarray(t, dtype=float)
        return 0.3 + 0.4 * t

    def phi1(t):
        t = np.asarray(t, dtype=float)
        return np.sqrt(2.0) * np.sin(np.pi * t)

    def phi2(t):
        t = np.asarray(t, dtype=float)
        return np.sqrt(2.0) * np.cos(2.0 * np.pi * t)

    eigenvalues = np.array([1.0, 0.35], dtype=float)
    scores = rng.normal(size=(n_curves, 2)) * np.sqrt(eigenvalues)[None, :]

    times = []
    values = []
    for curve in range(n_curves):
        interior = np.sort(
            rng.uniform(0.01, 0.99, size=samples_per_curve - 2)
        )
        time = np.concatenate([[0.0], interior, [1.0]])
        latent = (
            mean_function(time)
            + scores[curve, 0] * phi1(time)
            + scores[curve, 1] * phi2(time)
        )
        observed = latent + rng.normal(
            scale=noise_sd,
            size=time.size,
        )
        times.append(time)
        values.append(observed)

    truth = SparseTruth(
        mean=mean_function,
        eigenfunctions=(phi1, phi2),
        eigenvalues=eigenvalues,
        scores=scores,
        noise_sd=noise_sd,
    )
    return tuple(times), tuple(values), truth
