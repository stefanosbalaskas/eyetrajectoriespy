"""Private deterministic functional-simulation core for the 0.11 research branch."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from .fpca import functional_trapezoid_weights
from .types import IrregularTrajectorySet, TrajectorySet


FunctionalCallable = Callable[[np.ndarray], np.ndarray]


@dataclass(frozen=True)
class FunctionalSimulationTruth:
    """Complete latent truth retained by the private simulation core."""

    truth_grid: np.ndarray
    mean: np.ndarray
    eigenfunctions: np.ndarray
    eigenvalues: np.ndarray
    scores: np.ndarray
    curve_scores: np.ndarray
    participant_scores: np.ndarray
    trial_scores: np.ndarray
    participant_eigenvalues: np.ndarray
    trial_eigenvalues: np.ndarray
    latent_on_truth_grid: np.ndarray
    phase_warps_on_truth_grid: np.ndarray
    pre_missing_observation_times: tuple[np.ndarray, ...]
    warped_pre_missing_observation_times: tuple[np.ndarray, ...]
    observation_times: tuple[np.ndarray, ...]
    warped_observation_times: tuple[np.ndarray, ...]
    latent_at_pre_missing_times: tuple[np.ndarray, ...]
    latent_at_observation_times: tuple[np.ndarray, ...]
    measurement_noise: tuple[np.ndarray, ...]
    measurement_noise_covariance: np.ndarray
    observed_pre_missing: tuple[np.ndarray, ...]
    missingness_mask: tuple[np.ndarray, ...]
    metadata: pd.DataFrame
    dimension_names: tuple[str, ...]
    coordinate_system: str
    time_unit: str
    observation_design: str
    random_state: int | None
    provenance: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FunctionalSimulationCoreResult:
    """Private simulation result containing observations and exact truth."""

    observations: TrajectorySet | IrregularTrajectorySet
    truth: FunctionalSimulationTruth


def _validate_truth_grid(truth_grid: np.ndarray) -> np.ndarray:
    grid = np.asarray(truth_grid, dtype=float)
    if (
        grid.ndim != 1
        or grid.size < 3
        or not np.all(np.isfinite(grid))
        or not np.all(np.diff(grid) > 0)
    ):
        raise ValueError(
            "truth_grid must be a finite, strictly increasing "
            "one-dimensional array with at least three points"
        )
    return grid


def _coerce_function_values(
    values: np.ndarray,
    *,
    n_time: int,
    n_dimensions: int,
    name: str,
) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if n_dimensions == 1 and array.shape == (n_time,):
        array = array[:, None]
    if array.shape != (n_time, n_dimensions):
        raise ValueError(
            f"{name} must return shape ({n_time}, {n_dimensions}); "
            f"got {array.shape}"
        )
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must return only finite values")
    return array


def _evaluate_function(
    function: FunctionalCallable,
    time: np.ndarray,
    *,
    n_dimensions: int,
    name: str,
) -> np.ndarray:
    if not callable(function):
        raise TypeError(f"{name} must be callable")
    values = function(np.asarray(time, dtype=float))
    return _coerce_function_values(
        values,
        n_time=len(time),
        n_dimensions=n_dimensions,
        name=name,
    )


def _validate_modes(
    *,
    truth_grid: np.ndarray,
    eigenfunctions: Sequence[FunctionalCallable],
    eigenvalues: Sequence[float],
    n_dimensions: int,
    orthonormal_tolerance: float,
) -> tuple[np.ndarray, np.ndarray]:
    values = np.asarray(eigenvalues, dtype=float)
    if values.ndim != 1 or values.size < 1:
        raise ValueError("eigenvalues must be a non-empty one-dimensional array")
    if not np.all(np.isfinite(values)) or np.any(values <= 0):
        raise ValueError("eigenvalues must be finite and strictly positive")
    if np.any(np.diff(values) > 0):
        raise ValueError("eigenvalues must be supplied in descending order")
    if len(eigenfunctions) != values.size:
        raise ValueError(
            "eigenfunctions and eigenvalues must contain the same "
            "number of components"
        )
    tolerance = float(orthonormal_tolerance)
    if not np.isfinite(tolerance) or tolerance <= 0:
        raise ValueError(
            "orthonormal_tolerance must be finite and strictly positive"
        )

    modes = np.stack(
        [
            _evaluate_function(
                function,
                truth_grid,
                n_dimensions=n_dimensions,
                name=f"eigenfunctions[{index}]",
            )
            for index, function in enumerate(eigenfunctions)
        ],
        axis=0,
    )
    weights = functional_trapezoid_weights(truth_grid)
    gram = np.einsum(
        "ktd,ltd,t->kl",
        modes,
        modes,
        weights,
        optimize=True,
    )
    if not np.allclose(
        gram,
        np.eye(values.size),
        rtol=0.0,
        atol=tolerance,
    ):
        raise ValueError(
            "eigenfunctions must be mutually orthonormal on truth_grid "
            "under the trapezoidal functional inner product; the simulator "
            "does not silently normalize or orthogonalize supplied modes"
        )
    return modes, values


def _resolve_hierarchy_variances(
    values: Sequence[float] | None,
    *,
    n_components: int,
    name: str,
) -> np.ndarray:
    if values is None:
        return np.zeros(n_components, dtype=float)
    array = np.asarray(values, dtype=float)
    if array.shape != (n_components,):
        raise ValueError(
            f"{name} must contain exactly one value per functional component"
        )
    if not np.all(np.isfinite(array)) or np.any(array < 0):
        raise ValueError(f"{name} must contain finite non-negative values")
    return array


def _resolve_noise_covariance(
    measurement_noise_sd: float | Sequence[float] | None,
    measurement_noise_covariance: np.ndarray | None,
    *,
    n_dimensions: int,
) -> tuple[np.ndarray, np.ndarray]:
    if measurement_noise_sd is None:
        noise_sd = np.zeros(n_dimensions, dtype=float)
    else:
        noise_sd = np.asarray(measurement_noise_sd, dtype=float)
        if noise_sd.ndim == 0:
            noise_sd = np.full(
                n_dimensions,
                float(noise_sd),
                dtype=float,
            )
        if noise_sd.shape != (n_dimensions,):
            raise ValueError(
                "measurement_noise_sd must be a scalar or one value "
                "per dimension"
            )
        if not np.all(np.isfinite(noise_sd)) or np.any(noise_sd < 0):
            raise ValueError(
                "measurement_noise_sd values must be finite and non-negative"
            )

    if measurement_noise_covariance is None:
        covariance = np.diag(noise_sd**2)
        return noise_sd, covariance

    covariance = np.asarray(
        measurement_noise_covariance,
        dtype=float,
    )
    if covariance.shape != (n_dimensions, n_dimensions):
        raise ValueError(
            "measurement_noise_covariance must have shape "
            f"({n_dimensions}, {n_dimensions})"
        )
    if not np.all(np.isfinite(covariance)):
        raise ValueError(
            "measurement_noise_covariance must contain only finite values"
        )
    if not np.allclose(covariance, covariance.T, rtol=0.0, atol=1e-12):
        raise ValueError(
            "measurement_noise_covariance must be symmetric"
        )
    eigenvalues = np.linalg.eigvalsh(covariance)
    if np.min(eigenvalues) < -1e-12:
        raise ValueError(
            "measurement_noise_covariance must be positive semidefinite"
        )
    if np.any(noise_sd > 0):
        raise ValueError(
            "measurement_noise_sd and measurement_noise_covariance "
            "cannot both specify non-zero measurement noise"
        )
    noise_sd = np.sqrt(np.maximum(np.diag(covariance), 0.0))
    return noise_sd, covariance


def _resolve_sample_counts(
    samples_per_curve: int | tuple[int, int],
    *,
    n_curves: int,
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


def _sample_irregular_times(
    *,
    domain: tuple[float, float],
    n_samples: int,
    design: str,
    rng: np.random.Generator,
) -> np.ndarray:
    start, end = domain
    if n_samples == 2:
        return np.array([start, end], dtype=float)

    n_interior = n_samples - 2
    if design == "uniform":
        unit = rng.uniform(0.01, 0.99, size=n_interior)
    elif design == "center_clustered":
        unit = 0.01 + 0.98 * rng.beta(4.0, 4.0, size=n_interior)
    elif design == "boundary_poor":
        unit = rng.uniform(0.15, 0.85, size=n_interior)
    else:
        raise ValueError(
            "irregular_time_design must be 'uniform', 'center_clustered', "
            "or 'boundary_poor'"
        )
    interior = start + (end - start) * unit
    return np.concatenate(
        [[start], np.sort(interior), [end]]
    ).astype(float)


def _validate_explicit_observation_times(
    observation_times: Sequence[np.ndarray],
    *,
    n_curves: int,
    domain: tuple[float, float],
) -> tuple[np.ndarray, ...]:
    if len(observation_times) != n_curves:
        raise ValueError(
            "observation_times must contain exactly one time array per curve"
        )
    start, end = domain
    validated: list[np.ndarray] = []
    for index, time in enumerate(observation_times):
        array = np.asarray(time, dtype=float)
        if (
            array.ndim != 1
            or array.size < 2
            or not np.all(np.isfinite(array))
            or not np.all(np.diff(array) > 0)
        ):
            raise ValueError(
                f"observation_times[{index}] must be finite, strictly "
                "increasing, and contain at least two samples"
            )
        if array[0] < start or array[-1] > end:
            raise ValueError(
                f"observation_times[{index}] lies outside truth_grid support"
            )
        validated.append(array.copy())
    return tuple(validated)


def _curve_metadata(
    *,
    n_participants: int,
    trials_per_participant: int,
) -> tuple[tuple[str, ...], pd.DataFrame, np.ndarray]:
    ids: list[str] = []
    rows: list[dict[str, Any]] = []
    participant_index: list[int] = []
    for participant in range(n_participants):
        participant_id = f"P{participant + 1:03d}"
        for trial in range(trials_per_participant):
            trial_id = trial + 1
            ids.append(f"{participant_id}|T{trial_id:02d}")
            participant_index.append(participant)
            rows.append(
                {
                    "participant_id": participant_id,
                    "trial_id": trial_id,
                }
            )
    return (
        tuple(ids),
        pd.DataFrame(rows),
        np.asarray(participant_index, dtype=int),
    )


def _resolve_phase_variation(
    phase_variation: Mapping[str, Any] | None,
    *,
    n_curves: int,
    rng: np.random.Generator,
) -> tuple[str, np.ndarray]:
    if phase_variation is None:
        return "none", np.ones(n_curves, dtype=float)
    if not isinstance(phase_variation, Mapping):
        raise TypeError("phase_variation must be a mapping or None")
    kind = str(phase_variation.get("kind", ""))
    if kind != "power":
        raise ValueError(
            "phase_variation currently supports only kind='power'"
        )
    sd = float(phase_variation.get("sd", np.nan))
    if not np.isfinite(sd) or sd < 0:
        raise ValueError(
            "phase_variation['sd'] must be finite and non-negative"
        )
    exponents = np.exp(rng.normal(0.0, sd, size=n_curves))
    return kind, exponents


def _apply_power_warp(
    time: np.ndarray,
    *,
    domain: tuple[float, float],
    exponent: float,
) -> np.ndarray:
    start, end = domain
    unit = (np.asarray(time, dtype=float) - start) / (end - start)
    warped = start + (end - start) * np.power(unit, exponent)
    warped[0] = start if np.isclose(time[0], start) else warped[0]
    warped[-1] = end if np.isclose(time[-1], end) else warped[-1]
    return warped


def _missingness_mask(
    n_samples: int,
    missingness: Mapping[str, Any] | None,
    *,
    rng: np.random.Generator,
) -> tuple[str, np.ndarray]:
    if missingness is None:
        return "none", np.zeros(n_samples, dtype=bool)
    if not isinstance(missingness, Mapping):
        raise TypeError("missingness must be a mapping or None")
    kind = str(missingness.get("kind", ""))
    if kind == "mcar":
        probability = float(missingness.get("probability", np.nan))
        if (
            not np.isfinite(probability)
            or probability < 0
            or probability >= 1
        ):
            raise ValueError(
                "missingness['probability'] must be in [0, 1)"
            )
        return kind, rng.random(n_samples) < probability
    if kind == "block":
        fraction = float(missingness.get("fraction", np.nan))
        if (
            not np.isfinite(fraction)
            or fraction < 0
            or fraction >= 1
        ):
            raise ValueError(
                "missingness['fraction'] must be in [0, 1)"
            )
        mask = np.zeros(n_samples, dtype=bool)
        block_size = int(np.floor(fraction * n_samples))
        if fraction > 0 and block_size == 0:
            block_size = 1
        if block_size:
            start = int(rng.integers(0, n_samples - block_size + 1))
            mask[start : start + block_size] = True
        return kind, mask
    raise ValueError(
        "missingness currently supports kind='mcar' or kind='block'"
    )


def _evaluate_latent(
    *,
    mean: FunctionalCallable,
    eigenfunctions: Sequence[FunctionalCallable],
    scores: np.ndarray,
    warped_time: np.ndarray,
    n_dimensions: int,
) -> np.ndarray:
    mean_at_time = _evaluate_function(
        mean,
        warped_time,
        n_dimensions=n_dimensions,
        name="mean",
    )
    modes_at_time = np.stack(
        [
            _evaluate_function(
                function,
                warped_time,
                n_dimensions=n_dimensions,
                name=f"eigenfunctions[{component}]",
            )
            for component, function in enumerate(eigenfunctions)
        ],
        axis=0,
    )
    return (
        mean_at_time
        + np.einsum(
            "k,ktd->td",
            scores,
            modes_at_time,
            optimize=True,
        )
    )


def simulate_functional_process_core(
    *,
    mean: FunctionalCallable,
    eigenfunctions: Sequence[FunctionalCallable],
    eigenvalues: Sequence[float],
    truth_grid: np.ndarray,
    n_participants: int,
    trials_per_participant: int = 1,
    dimension_names: Sequence[str] = ("value",),
    coordinate_system: str = "arbitrary",
    time_unit: str = "normalized",
    observation_design: str = "dense",
    observation_times: Sequence[np.ndarray] | None = None,
    samples_per_curve: int | tuple[int, int] | None = None,
    irregular_time_design: str = "uniform",
    participant_eigenvalues: Sequence[float] | None = None,
    trial_eigenvalues: Sequence[float] | None = None,
    measurement_noise_sd: float | Sequence[float] | None = 0.0,
    measurement_noise_covariance: np.ndarray | None = None,
    missingness: Mapping[str, Any] | None = None,
    phase_variation: Mapping[str, Any] | None = None,
    orthonormal_tolerance: float = 1e-6,
    random_state: int | None = 42,
) -> FunctionalSimulationCoreResult:
    """Generate deterministic functional observations plus accountable truth.

    This function remains private while the 0.11 simulation contract is being
    qualified. Irregular observations are generated directly on their declared
    schedules. Missingness, hierarchy, measurement noise, and phase variation
    are retained as separate truth components rather than folded into one
    opaque synthetic trajectory.
    """

    if (
        isinstance(n_participants, bool)
        or not isinstance(n_participants, int)
        or n_participants < 1
    ):
        raise ValueError("n_participants must be a positive integer")
    if (
        isinstance(trials_per_participant, bool)
        or not isinstance(trials_per_participant, int)
        or trials_per_participant < 1
    ):
        raise ValueError(
            "trials_per_participant must be a positive integer"
        )

    names = tuple(str(name) for name in dimension_names)
    if not names or len(set(names)) != len(names):
        raise ValueError("dimension_names must be non-empty and unique")
    n_dimensions = len(names)

    grid = _validate_truth_grid(truth_grid)
    domain = (float(grid[0]), float(grid[-1]))
    mean_grid = _evaluate_function(
        mean,
        grid,
        n_dimensions=n_dimensions,
        name="mean",
    )
    mode_grid, eigenvalue_array = _validate_modes(
        truth_grid=grid,
        eigenfunctions=eigenfunctions,
        eigenvalues=eigenvalues,
        n_dimensions=n_dimensions,
        orthonormal_tolerance=orthonormal_tolerance,
    )
    participant_variances = _resolve_hierarchy_variances(
        participant_eigenvalues,
        n_components=eigenvalue_array.size,
        name="participant_eigenvalues",
    )
    trial_variances = _resolve_hierarchy_variances(
        trial_eigenvalues,
        n_components=eigenvalue_array.size,
        name="trial_eigenvalues",
    )
    noise_sd, noise_covariance = _resolve_noise_covariance(
        measurement_noise_sd,
        measurement_noise_covariance,
        n_dimensions=n_dimensions,
    )

    n_curves = n_participants * trials_per_participant
    curve_ids, metadata, participant_index = _curve_metadata(
        n_participants=n_participants,
        trials_per_participant=trials_per_participant,
    )
    rng = np.random.default_rng(random_state)

    curve_scores = (
        rng.normal(size=(n_curves, eigenvalue_array.size))
        * np.sqrt(eigenvalue_array)[None, :]
    )
    participant_scores = (
        rng.normal(size=(n_participants, eigenvalue_array.size))
        * np.sqrt(participant_variances)[None, :]
    )
    trial_scores = (
        rng.normal(size=(n_curves, eigenvalue_array.size))
        * np.sqrt(trial_variances)[None, :]
    )
    scores = (
        curve_scores
        + participant_scores[participant_index]
        + trial_scores
    )

    if observation_design == "dense":
        if observation_times is not None or samples_per_curve is not None:
            raise ValueError(
                "dense observation_design uses truth_grid directly; "
                "observation_times and samples_per_curve must be None"
            )
        schedules = tuple(grid.copy() for _ in range(n_curves))
    elif observation_design == "irregular":
        if observation_times is not None and samples_per_curve is not None:
            raise ValueError(
                "for irregular simulation, specify observation_times or "
                "samples_per_curve, not both"
            )
        if observation_times is not None:
            schedules = _validate_explicit_observation_times(
                observation_times,
                n_curves=n_curves,
                domain=domain,
            )
        else:
            if samples_per_curve is None:
                raise ValueError(
                    "irregular observation_design requires observation_times "
                    "or samples_per_curve"
                )
            counts = _resolve_sample_counts(
                samples_per_curve,
                n_curves=n_curves,
                rng=rng,
            )
            schedules = tuple(
                _sample_irregular_times(
                    domain=domain,
                    n_samples=int(count),
                    design=irregular_time_design,
                    rng=rng,
                )
                for count in counts
            )
    else:
        raise ValueError(
            "observation_design must be 'dense' or 'irregular'"
        )

    phase_kind, phase_exponents = _resolve_phase_variation(
        phase_variation,
        n_curves=n_curves,
        rng=rng,
    )
    phase_warps_grid = np.stack(
        [
            _apply_power_warp(
                grid,
                domain=domain,
                exponent=float(exponent),
            )
            for exponent in phase_exponents
        ],
        axis=0,
    )

    latent_grid = np.stack(
        [
            _evaluate_latent(
                mean=mean,
                eigenfunctions=eigenfunctions,
                scores=scores[curve],
                warped_time=phase_warps_grid[curve],
                n_dimensions=n_dimensions,
            )
            for curve in range(n_curves)
        ],
        axis=0,
    )

    warped_pre_missing: list[np.ndarray] = []
    latent_pre_missing: list[np.ndarray] = []
    noise_realizations: list[np.ndarray] = []
    observed_pre_missing: list[np.ndarray] = []
    missing_masks: list[np.ndarray] = []
    final_times: list[np.ndarray] = []
    final_warped_times: list[np.ndarray] = []
    final_latent: list[np.ndarray] = []
    final_values: list[np.ndarray] = []

    missingness_kind = "none"
    for curve, time in enumerate(schedules):
        warped_time = _apply_power_warp(
            time,
            domain=domain,
            exponent=float(phase_exponents[curve]),
        )
        latent = _evaluate_latent(
            mean=mean,
            eigenfunctions=eigenfunctions,
            scores=scores[curve],
            warped_time=warped_time,
            n_dimensions=n_dimensions,
        )
        if np.allclose(noise_covariance, 0.0):
            noise = np.zeros_like(latent)
        else:
            noise = rng.multivariate_normal(
                mean=np.zeros(n_dimensions, dtype=float),
                cov=noise_covariance,
                size=len(time),
                check_valid="raise",
            )
            if n_dimensions == 1:
                noise = np.asarray(noise, dtype=float).reshape(-1, 1)
        observed = latent + noise
        current_kind, mask = _missingness_mask(
            len(time),
            missingness,
            rng=rng,
        )
        missingness_kind = current_kind

        warped_pre_missing.append(warped_time)
        latent_pre_missing.append(latent)
        noise_realizations.append(noise)
        observed_pre_missing.append(observed)
        missing_masks.append(mask)

        if observation_design == "dense":
            output = observed.copy()
            output[mask, :] = np.nan
            final_times.append(time.copy())
            final_warped_times.append(warped_time.copy())
            final_latent.append(latent.copy())
            final_values.append(output)
        else:
            keep = ~mask
            if np.count_nonzero(keep) < 2:
                raise ValueError(
                    "missingness left fewer than two irregular observations "
                    f"for curve {curve}; the simulator does not silently "
                    "resample or override the declared missingness mechanism"
                )
            final_times.append(time[keep].copy())
            final_warped_times.append(warped_time[keep].copy())
            final_latent.append(latent[keep].copy())
            final_values.append(observed[keep].copy())

    provenance = {
        "source": "simulate_functional_process_core",
        "synthetic": True,
        "private_0_11_simulation_core": True,
        "random_state": random_state,
        "observation_design": observation_design,
        "irregular_time_design": (
            irregular_time_design
            if observation_design == "irregular"
            and observation_times is None
            else None
        ),
        "measurement_noise_sd": noise_sd.tolist(),
        "measurement_noise_covariance": noise_covariance.tolist(),
        "participant_eigenvalues": participant_variances.tolist(),
        "trial_eigenvalues": trial_variances.tolist(),
        "phase_variation_kind": phase_kind,
        "phase_exponents": phase_exponents.tolist(),
        "missingness_kind": missingness_kind,
        "missingness_specification": (
            None if missingness is None else dict(missingness)
        ),
        "n_components": int(eigenvalue_array.size),
        "truth_grid": grid.tolist(),
        "raw_dense_to_irregular_interpolation_performed": False,
    }

    if observation_design == "dense":
        observations: TrajectorySet | IrregularTrajectorySet = TrajectorySet(
            time=grid.copy(),
            values=np.stack(final_values, axis=0),
            curve_ids=curve_ids,
            dimension_names=names,
            metadata=metadata.copy(),
            coordinate_system=coordinate_system,
            time_unit=time_unit,
            provenance=provenance,
        )
    else:
        observations = IrregularTrajectorySet(
            time=tuple(time.copy() for time in final_times),
            values=tuple(value.copy() for value in final_values),
            curve_ids=curve_ids,
            dimension_names=names,
            metadata=metadata.copy(),
            coordinate_system=coordinate_system,
            time_unit=time_unit,
            provenance=provenance,
        )

    truth = FunctionalSimulationTruth(
        truth_grid=grid.copy(),
        mean=mean_grid.copy(),
        eigenfunctions=mode_grid.copy(),
        eigenvalues=eigenvalue_array.copy(),
        scores=scores.copy(),
        curve_scores=curve_scores.copy(),
        participant_scores=participant_scores.copy(),
        trial_scores=trial_scores.copy(),
        participant_eigenvalues=participant_variances.copy(),
        trial_eigenvalues=trial_variances.copy(),
        latent_on_truth_grid=latent_grid.copy(),
        phase_warps_on_truth_grid=phase_warps_grid.copy(),
        pre_missing_observation_times=tuple(
            time.copy() for time in schedules
        ),
        warped_pre_missing_observation_times=tuple(
            time.copy() for time in warped_pre_missing
        ),
        observation_times=tuple(
            time.copy() for time in final_times
        ),
        warped_observation_times=tuple(
            time.copy() for time in final_warped_times
        ),
        latent_at_pre_missing_times=tuple(
            value.copy() for value in latent_pre_missing
        ),
        latent_at_observation_times=tuple(
            value.copy() for value in final_latent
        ),
        measurement_noise=tuple(
            value.copy() for value in noise_realizations
        ),
        measurement_noise_covariance=noise_covariance.copy(),
        observed_pre_missing=tuple(
            value.copy() for value in observed_pre_missing
        ),
        missingness_mask=tuple(
            mask.copy() for mask in missing_masks
        ),
        metadata=metadata.copy(),
        dimension_names=names,
        coordinate_system=coordinate_system,
        time_unit=time_unit,
        observation_design=observation_design,
        random_state=random_state,
        provenance=provenance.copy(),
    )
    return FunctionalSimulationCoreResult(
        observations=observations,
        truth=truth,
    )
