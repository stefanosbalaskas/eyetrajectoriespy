"""Private known-truth generator for sparse multivariate FPCA validation."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from ._sparse_truth import _resolve_sample_counts, _sample_observation_times


@dataclass(frozen=True)
class SparseMultivariateTruth:
    """Known planar latent structure for sparse-MFPCA recovery tests."""

    mean: Callable[[np.ndarray], np.ndarray]
    temporal_modes: tuple[Callable[[np.ndarray], np.ndarray], ...]
    temporal_eigenvalues: np.ndarray
    channel_correlation: float
    channel_coefficients: np.ndarray
    joint_eigenvalues: np.ndarray
    joint_scores: np.ndarray
    joint_mode_specification: tuple[tuple[int, int], ...]
    noise_sd: np.ndarray
    sample_counts: np.ndarray
    observation_design: str

    def joint_eigenfunctions(self, grid: np.ndarray) -> np.ndarray:
        """Evaluate ordered joint eigenfunctions on a common grid."""

        time = np.asarray(grid, dtype=float)
        result = np.empty(
            (len(self.joint_mode_specification), time.size, 2),
            dtype=float,
        )
        root_two = np.sqrt(2.0)
        for component, (mode_index, sign) in enumerate(
            self.joint_mode_specification
        ):
            temporal = self.temporal_modes[mode_index](time)
            result[component, :, 0] = temporal / root_two
            result[component, :, 1] = sign * temporal / root_two
        return result

    def covariance_blocks(self, grid: np.ndarray) -> np.ndarray:
        """Evaluate the true (2, M, 2, M) latent covariance blocks."""

        time = np.asarray(grid, dtype=float)
        marginal = np.zeros((time.size, time.size), dtype=float)
        for eigenvalue, mode in zip(
            self.temporal_eigenvalues,
            self.temporal_modes,
            strict=True,
        ):
            values = mode(time)
            marginal += float(eigenvalue) * np.outer(values, values)

        blocks = np.empty((2, time.size, 2, time.size), dtype=float)
        blocks[0, :, 0, :] = marginal
        blocks[1, :, 1, :] = marginal
        blocks[0, :, 1, :] = self.channel_correlation * marginal
        blocks[1, :, 0, :] = (
            self.channel_correlation * marginal.T
        )
        return blocks


def simulate_sparse_multivariate_truth(
    *,
    n_curves: int = 64,
    samples_per_curve: int | tuple[int, int] = (9, 14),
    noise_sd: tuple[float, float] = (0.06, 0.07),
    temporal_eigenvalues: tuple[float, float] = (1.0, 0.35),
    channel_correlation: float = 0.6,
    observation_design: str = "uniform",
    random_state: int = 202612,
) -> tuple[
    tuple[np.ndarray, ...],
    tuple[np.ndarray, ...],
    SparseMultivariateTruth,
]:
    """Generate sparse planar trajectories with controlled cross covariance.

    Marginal x/y covariance is fixed as channel_correlation changes. Only the
    cross-channel covariance block changes. The latent joint eigensystem is
    available analytically through plus/minus channel combinations.
    """

    if n_curves < 3:
        raise ValueError("n_curves must be at least 3")
    rho = float(channel_correlation)
    if not np.isfinite(rho) or abs(rho) >= 1:
        raise ValueError(
            "channel_correlation must be finite and strictly between -1 and 1"
        )
    noise = np.asarray(noise_sd, dtype=float)
    if (
        noise.shape != (2,)
        or not np.all(np.isfinite(noise))
        or np.any(noise < 0)
    ):
        raise ValueError(
            "noise_sd must contain two finite non-negative values"
        )
    temporal = np.asarray(temporal_eigenvalues, dtype=float)
    if (
        temporal.shape != (2,)
        or not np.all(np.isfinite(temporal))
        or np.any(temporal <= 0)
    ):
        raise ValueError(
            "temporal_eigenvalues must contain two finite positive values"
        )
    if temporal[0] < temporal[1]:
        raise ValueError(
            "temporal_eigenvalues must be supplied in descending order"
        )

    rng = np.random.default_rng(random_state)

    def mean_function(t: np.ndarray) -> np.ndarray:
        time = np.asarray(t, dtype=float)
        return np.column_stack(
            [
                0.20 + 0.25 * time,
                -0.15 + 0.10 * time,
            ]
        )

    def phi1(t: np.ndarray) -> np.ndarray:
        time = np.asarray(t, dtype=float)
        return np.sqrt(2.0) * np.sin(np.pi * time)

    def phi2(t: np.ndarray) -> np.ndarray:
        time = np.asarray(t, dtype=float)
        return np.sqrt(2.0) * np.sin(2.0 * np.pi * time)

    modes = (phi1, phi2)
    correlation = np.array([[1.0, rho], [rho, 1.0]], dtype=float)
    channel_coefficients = np.empty((n_curves, 2, 2), dtype=float)
    for mode_index, eigenvalue in enumerate(temporal):
        channel_coefficients[:, mode_index, :] = rng.multivariate_normal(
            mean=np.zeros(2),
            cov=float(eigenvalue) * correlation,
            size=n_curves,
        )

    candidates: list[tuple[float, int, int, np.ndarray]] = []
    root_two = np.sqrt(2.0)
    for mode_index, eigenvalue in enumerate(temporal):
        plus_score = (
            channel_coefficients[:, mode_index, 0]
            + channel_coefficients[:, mode_index, 1]
        ) / root_two
        minus_score = (
            channel_coefficients[:, mode_index, 0]
            - channel_coefficients[:, mode_index, 1]
        ) / root_two
        candidates.append(
            (
                float(eigenvalue * (1.0 + rho)),
                mode_index,
                1,
                plus_score,
            )
        )
        candidates.append(
            (
                float(eigenvalue * (1.0 - rho)),
                mode_index,
                -1,
                minus_score,
            )
        )
    candidates.sort(key=lambda item: item[0], reverse=True)

    joint_eigenvalues = np.asarray(
        [candidate[0] for candidate in candidates],
        dtype=float,
    )
    joint_mode_specification = tuple(
        (candidate[1], candidate[2]) for candidate in candidates
    )
    joint_scores = np.column_stack(
        [candidate[3] for candidate in candidates]
    )

    sample_counts = _resolve_sample_counts(
        n_curves=n_curves,
        samples_per_curve=samples_per_curve,
        rng=rng,
    )

    times: list[np.ndarray] = []
    values: list[np.ndarray] = []
    for curve_index, n_samples in enumerate(sample_counts):
        time = _sample_observation_times(
            n_samples=int(n_samples),
            observation_design=observation_design,
            rng=rng,
        )
        latent = mean_function(time)
        for mode_index, mode in enumerate(modes):
            latent = latent + (
                mode(time)[:, None]
                * channel_coefficients[curve_index, mode_index, :][
                    None, :
                ]
            )
        observed = latent + rng.normal(
            scale=noise[None, :],
            size=latent.shape,
        )
        times.append(time)
        values.append(observed)

    truth = SparseMultivariateTruth(
        mean=mean_function,
        temporal_modes=modes,
        temporal_eigenvalues=temporal.copy(),
        channel_correlation=rho,
        channel_coefficients=channel_coefficients.copy(),
        joint_eigenvalues=joint_eigenvalues,
        joint_scores=joint_scores,
        joint_mode_specification=joint_mode_specification,
        noise_sd=noise.copy(),
        sample_counts=sample_counts.copy(),
        observation_design=observation_design,
    )
    return tuple(times), tuple(values), truth
