"""Private sparse-functional truth generator for 0.10 validation tests."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SparseFunctionalTruth:
    """Known latent structure for private sparse-FPCA recovery tests."""

    mean: Callable[[np.ndarray], np.ndarray]
    eigenfunctions: tuple[Callable[[np.ndarray], np.ndarray], ...]
    eigenvalues: np.ndarray
    scores: np.ndarray
    noise_sd: float
    sample_counts: np.ndarray
    observation_design: str


def _resolve_sample_counts(
    *,
    n_curves: int,
    samples_per_curve: int | tuple[int, int],
    rng: np.random.Generator,
) -> np.ndarray:
    if isinstance(samples_per_curve, bool):
        raise TypeError(
            "samples_per_curve must be an integer or (minimum, maximum) tuple"
        )
    if isinstance(samples_per_curve, int):
        if samples_per_curve < 2:
            raise ValueError("samples_per_curve must be at least 2")
        return np.full(n_curves, samples_per_curve, dtype=int)
    if (
        not isinstance(samples_per_curve, tuple)
        or len(samples_per_curve) != 2
    ):
        raise TypeError(
            "samples_per_curve must be an integer or (minimum, maximum) tuple"
        )
    lower, upper = samples_per_curve
    if (
        isinstance(lower, bool)
        or isinstance(upper, bool)
        or not isinstance(lower, int)
        or not isinstance(upper, int)
    ):
        raise TypeError("sample-count bounds must be integers")
    if lower < 2 or upper < lower:
        raise ValueError(
            "sample-count bounds must satisfy 2 <= minimum <= maximum"
        )
    return rng.integers(lower, upper + 1, size=n_curves)


def _sample_observation_times(
    *,
    n_samples: int,
    observation_design: str,
    rng: np.random.Generator,
) -> np.ndarray:
    n_interior = n_samples - 2
    if n_interior == 0:
        return np.array([0.0, 1.0], dtype=float)

    if observation_design == "uniform":
        interior = rng.uniform(0.01, 0.99, size=n_interior)
    elif observation_design == "center_clustered":
        interior = 0.01 + 0.98 * rng.beta(4.0, 4.0, size=n_interior)
    elif observation_design == "boundary_poor":
        interior = rng.uniform(0.15, 0.85, size=n_interior)
    else:
        raise ValueError(
            "observation_design must be 'uniform', 'center_clustered', "
            "or 'boundary_poor'"
        )
    return np.concatenate([[0.0], np.sort(interior), [1.0]])


def simulate_sparse_functional_truth(
    *,
    n_curves: int = 48,
    samples_per_curve: int | tuple[int, int] = 12,
    noise_sd: float = 0.12,
    eigenvalues: tuple[float, float] = (1.0, 0.35),
    observation_design: str = "uniform",
    random_state: int = 202610,
) -> tuple[
    tuple[np.ndarray, ...],
    tuple[np.ndarray, ...],
    SparseFunctionalTruth,
]:
    """Generate irregular observations from a known two-component process.

    This remains private validation infrastructure rather than a public
    simulation API. Variable per-curve sample counts, eigenvalue separation,
    observation-time concentration, and measurement noise are explicit so the
    0.10 estimator can be stress-tested across difficult sparse regimes.
    """

    if n_curves < 3:
        raise ValueError("n_curves must be at least 3")
    if noise_sd < 0 or not np.isfinite(noise_sd):
        raise ValueError("noise_sd must be finite and non-negative")
    eigenvalue_array = np.asarray(eigenvalues, dtype=float)
    if (
        eigenvalue_array.shape != (2,)
        or not np.all(np.isfinite(eigenvalue_array))
        or np.any(eigenvalue_array <= 0)
    ):
        raise ValueError(
            "eigenvalues must contain exactly two finite positive values"
        )
    if eigenvalue_array[0] < eigenvalue_array[1]:
        raise ValueError("eigenvalues must be supplied in descending order")
    if observation_design not in {
        "uniform",
        "center_clustered",
        "boundary_poor",
    }:
        raise ValueError(
            "observation_design must be 'uniform', 'center_clustered', "
            "or 'boundary_poor'"
        )

    rng = np.random.default_rng(random_state)

    def mean_function(t: np.ndarray) -> np.ndarray:
        t = np.asarray(t, dtype=float)
        return 0.3 + 0.4 * t

    def phi1(t: np.ndarray) -> np.ndarray:
        t = np.asarray(t, dtype=float)
        return np.sqrt(2.0) * np.sin(np.pi * t)

    def phi2(t: np.ndarray) -> np.ndarray:
        t = np.asarray(t, dtype=float)
        return np.sqrt(2.0) * np.sin(2.0 * np.pi * t)

    scores = (
        rng.normal(size=(n_curves, 2))
        * np.sqrt(eigenvalue_array)[None, :]
    )
    sample_counts = _resolve_sample_counts(
        n_curves=n_curves,
        samples_per_curve=samples_per_curve,
        rng=rng,
    )

    times: list[np.ndarray] = []
    values: list[np.ndarray] = []
    for curve, n_samples in enumerate(sample_counts):
        time = _sample_observation_times(
            n_samples=int(n_samples),
            observation_design=observation_design,
            rng=rng,
        )
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

    truth = SparseFunctionalTruth(
        mean=mean_function,
        eigenfunctions=(phi1, phi2),
        eigenvalues=eigenvalue_array.copy(),
        scores=scores,
        noise_sd=float(noise_sd),
        sample_counts=sample_counts.copy(),
        observation_design=observation_design,
    )
    return tuple(times), tuple(values), truth
