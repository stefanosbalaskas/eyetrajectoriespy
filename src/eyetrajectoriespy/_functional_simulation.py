"""Private deterministic functional-simulation core for the 0.11 research branch."""

from __future__ import annotations

from collections.abc import Callable, Sequence
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
    latent_on_truth_grid: np.ndarray
    observation_times: tuple[np.ndarray, ...]
    latent_at_observation_times: tuple[np.ndarray, ...]
    measurement_noise: tuple[np.ndarray, ...]
    observed_pre_missing: tuple[np.ndarray, ...]
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


def _resolve_noise_sd(
    measurement_noise_sd: float | Sequence[float],
    *,
    n_dimensions: int,
) -> np.ndarray:
    values = np.asarray(measurement_noise_sd, dtype=float)
    if values.ndim == 0:
        values = np.full(n_dimensions, float(values), dtype=float)
    if values.shape != (n_dimensions,):
        raise ValueError(
            "measurement_noise_sd must be a scalar or one value per dimension"
        )
    if not np.all(np.isfinite(values)) or np.any(values < 0):
        raise ValueError(
            "measurement_noise_sd values must be finite and non-negative"
        )
    return values


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
) -> tuple[tuple[str, ...], pd.DataFrame]:
    ids: list[str] = []
    rows: list[dict[str, Any]] = []
    for participant in range(n_participants):
        participant_id = f"P{participant + 1:03d}"
        for trial in range(trials_per_participant):
            trial_id = trial + 1
            ids.append(f"{participant_id}|T{trial_id:02d}")
            rows.append(
                {
                    "participant_id": participant_id,
                    "trial_id": trial_id,
                }
            )
    return tuple(ids), pd.DataFrame(rows)


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
    measurement_noise_sd: float | Sequence[float] = 0.0,
    orthonormal_tolerance: float = 1e-6,
    random_state: int | None = 42,
) -> FunctionalSimulationCoreResult:
    """Generate deterministic KL-process observations plus complete truth.

    This function is private while the 0.11 simulation contract is being
    qualified. Raw observations are generated directly on their declared
    schedules. Irregular observations are not constructed by interpolating
    simulated dense trajectories.
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
    noise_sd = _resolve_noise_sd(
        measurement_noise_sd,
        n_dimensions=n_dimensions,
    )

    n_curves = n_participants * trials_per_participant
    curve_ids, metadata = _curve_metadata(
        n_participants=n_participants,
        trials_per_participant=trials_per_participant,
    )
    rng = np.random.default_rng(random_state)
    scores = (
        rng.normal(size=(n_curves, eigenvalue_array.size))
        * np.sqrt(eigenvalue_array)[None, :]
    )
    latent_grid = (
        mean_grid[None, :, :]
        + np.einsum(
            "ik,ktd->itd",
            scores,
            mode_grid,
            optimize=True,
        )
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
                domain=(float(grid[0]), float(grid[-1])),
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
                    domain=(float(grid[0]), float(grid[-1])),
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

    latent_observed: list[np.ndarray] = []
    noise_realizations: list[np.ndarray] = []
    observed_values: list[np.ndarray] = []
    for curve, time in enumerate(schedules):
        mean_at_time = _evaluate_function(
            mean,
            time,
            n_dimensions=n_dimensions,
            name="mean",
        )
        modes_at_time = np.stack(
            [
                _evaluate_function(
                    function,
                    time,
                    n_dimensions=n_dimensions,
                    name=f"eigenfunctions[{component}]",
                )
                for component, function in enumerate(eigenfunctions)
            ],
            axis=0,
        )
        latent = (
            mean_at_time
            + np.einsum(
                "k,ktd->td",
                scores[curve],
                modes_at_time,
                optimize=True,
            )
        )
        noise = rng.normal(
            loc=0.0,
            scale=noise_sd,
            size=latent.shape,
        )
        latent_observed.append(latent)
        noise_realizations.append(noise)
        observed_values.append(latent + noise)

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
        "n_components": int(eigenvalue_array.size),
        "truth_grid": grid.tolist(),
        "raw_dense_to_irregular_interpolation_performed": False,
    }

    if observation_design == "dense":
        dense_values = np.stack(observed_values, axis=0)
        observations: TrajectorySet | IrregularTrajectorySet = TrajectorySet(
            time=grid.copy(),
            values=dense_values,
            curve_ids=curve_ids,
            dimension_names=names,
            metadata=metadata.copy(),
            coordinate_system=coordinate_system,
            time_unit=time_unit,
            provenance=provenance,
        )
    else:
        observations = IrregularTrajectorySet(
            time=tuple(time.copy() for time in schedules),
            values=tuple(value.copy() for value in observed_values),
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
        latent_on_truth_grid=latent_grid.copy(),
        observation_times=tuple(time.copy() for time in schedules),
        latent_at_observation_times=tuple(
            value.copy() for value in latent_observed
        ),
        measurement_noise=tuple(
            value.copy() for value in noise_realizations
        ),
        observed_pre_missing=tuple(
            value.copy() for value in observed_values
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
