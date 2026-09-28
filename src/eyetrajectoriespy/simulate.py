"""Deterministic synthetic trajectory generators for examples and tests."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from itertools import product
import json
import re
from types import MappingProxyType
from typing import Any, Literal

import numpy as np
import pandas as pd

from ._functional_simulation import (
    FunctionalSimulationResult,
    FunctionalSimulationTruth,
    simulate_functional_process_core,
)
from .types import IrregularTrajectorySet, TrajectorySet

def simulate_functional_process(
    *,
    mean: Callable[[np.ndarray], np.ndarray],
    eigenfunctions: Sequence[Callable[[np.ndarray], np.ndarray]],
    eigenvalues: Sequence[float],
    truth_grid: np.ndarray,
    n_participants: int,
    trials_per_participant: int = 1,
    dimension_names: Sequence[str] = ("value",),
    coordinate_system: str = "unknown",
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
    score_distribution: str = "normal",
    score_df: float = 5.0,
    orthonormal_tolerance: float = 1e-6,
    random_state: int | None = 42,
) -> FunctionalSimulationResult:
    """Simulate dense or irregular functional trajectories with exact truth.

    Mean and vector-valued functional modes are evaluated directly on each
    observation schedule. Irregular observations are never created by silently
    interpolating a dense raw trajectory.

    The returned FunctionalSimulationResult contains both the observed
    TrajectorySet or IrregularTrajectorySet and a complete
    FunctionalSimulationTruth record with realized scores, hierarchy, phase
    warps, measurement noise, missingness and pre-missing schedules.

    Curve-level scores may follow a variance-matched normal or Student-t
    distribution. Participant/trial score effects remain Gaussian and are
    retained separately in truth.
    """

    return simulate_functional_process_core(
        mean=mean,
        eigenfunctions=eigenfunctions,
        eigenvalues=eigenvalues,
        truth_grid=truth_grid,
        n_participants=n_participants,
        trials_per_participant=trials_per_participant,
        dimension_names=dimension_names,
        coordinate_system=coordinate_system,
        time_unit=time_unit,
        observation_design=observation_design,
        observation_times=observation_times,
        samples_per_curve=samples_per_curve,
        irregular_time_design=irregular_time_design,
        participant_eigenvalues=participant_eigenvalues,
        trial_eigenvalues=trial_eigenvalues,
        measurement_noise_sd=measurement_noise_sd,
        measurement_noise_covariance=measurement_noise_covariance,
        missingness=missingness,
        phase_variation=phase_variation,
        score_distribution=score_distribution,
        score_df=score_df,
        orthonormal_tolerance=orthonormal_tolerance,
        random_state=random_state,
    )

def simulate_planar_trajectories(
    *,
    n_participants: int = 20,
    trials_per_participant: int = 6,
    n_time: int = 121,
    duration: float = 2.0,
    random_state: int = 42,
) -> TrajectorySet:
    """Simulate repeated 2-D gaze paths with known participant/trial variation."""
    if n_participants < 2 or trials_per_participant < 1 or n_time < 5 or duration <= 0:
        raise ValueError("Use at least 2 participants, 1 trial each, 5 time points, and positive duration")
    rng = np.random.default_rng(random_state)
    time = np.linspace(0.0, duration, n_time)
    u = time / duration
    n = n_participants * trials_per_participant
    values = np.empty((n, n_time, 2), dtype=float)
    rows = []
    ids = []
    index = 0
    for participant in range(n_participants):
        p_shift = rng.normal(0.0, 0.025, size=2)
        p_phase = rng.normal(0.0, 0.035)
        p_amp = rng.normal(1.0, 0.07)
        for trial in range(trials_per_participant):
            condition = "evidence_prompt" if trial % 2 else "control"
            prompt = 1.0 if condition == "evidence_prompt" else 0.0
            phase = np.clip(u + p_phase + rng.normal(0, 0.018), 0, 1)
            evidence_gate = 1 / (1 + np.exp(-(phase - (0.38 - 0.04 * prompt)) / 0.055))
            decision_gate = 1 / (1 + np.exp(-(phase - 0.73) / 0.07))
            x = 0.50 + (0.26 + 0.05 * prompt) * p_amp * evidence_gate - 0.17 * decision_gate
            y = 0.50 - 0.17 * p_amp * evidence_gate + 0.27 * decision_gate
            x += p_shift[0] + 0.012 * np.sin(2 * np.pi * phase) + rng.normal(0, 0.008, n_time)
            y += p_shift[1] + 0.010 * np.cos(2 * np.pi * phase) + rng.normal(0, 0.008, n_time)
            values[index, :, 0] = np.clip(x, 0.0, 1.0)
            values[index, :, 1] = np.clip(y, 0.0, 1.0)
            ids.append(f"P{participant + 1:03d}|T{trial + 1:02d}")
            rows.append({
                "participant_id": f"P{participant + 1:03d}",
                "trial_id": trial + 1,
                "condition": condition,
                "latent_participant_amplitude": p_amp,
            })
            index += 1
    return TrajectorySet(
        time=time,
        values=values,
        curve_ids=tuple(ids),
        dimension_names=("x", "y"),
        metadata=pd.DataFrame(rows),
        coordinate_system="normalized",
        time_unit="s",
        provenance={"source": "simulate_planar_trajectories", "random_state": random_state, "synthetic": True},
    )


def simulate_aoi_probability_trajectories(
    *,
    n_curves: int = 80,
    n_time: int = 101,
    n_aoi: int = 4,
    duration: float = 2.0,
    random_state: int = 17,
) -> TrajectorySet:
    """Simulate smooth AOI probability functions that lie on the simplex."""
    if n_curves < 2 or n_time < 5 or n_aoi < 2 or duration <= 0:
        raise ValueError("Use at least 2 curves, 5 time points, 2 AOIs, and positive duration")
    rng = np.random.default_rng(random_state)
    time = np.linspace(0.0, duration, n_time)
    u = time / duration
    centers = np.linspace(0.12, 0.88, n_aoi)
    logits = np.empty((n_curves, n_time, n_aoi), dtype=float)
    for i in range(n_curves):
        shift = rng.normal(0, 0.035)
        participant_bias = rng.normal(0, 0.25, n_aoi)
        for k, center in enumerate(centers):
            logits[i, :, k] = -((u - center - shift) ** 2) / 0.025 + participant_bias[k]
        logits[i] += rng.normal(0, 0.08, size=(n_time, n_aoi))
    logits -= logits.max(axis=2, keepdims=True)
    exp = np.exp(logits)
    probs = exp / exp.sum(axis=2, keepdims=True)
    return TrajectorySet(
        time=time,
        values=probs,
        curve_ids=tuple(f"curve_{i + 1:03d}" for i in range(n_curves)),
        dimension_names=tuple(f"AOI_{i + 1}" for i in range(n_aoi)),
        metadata=pd.DataFrame({"curve_index": np.arange(n_curves)}),
        coordinate_system="probability_simplex",
        time_unit="s",
        provenance={"source": "simulate_aoi_probability_trajectories", "random_state": random_state, "synthetic": True},
    )


FunctionalEstimator = Callable[
    [TrajectorySet | IrregularTrajectorySet, "FunctionalSimulationScenario"],
    Any,
]
FunctionalRecoveryScorer = Callable[
    [Any, FunctionalSimulationTruth, "FunctionalSimulationScenario"],
    Mapping[str, float],
]


def _immutable_mapping(
    value: Mapping[str, Any] | None,
) -> Mapping[str, Any] | None:
    if value is None:
        return None
    return MappingProxyType(dict(value))


def _scenario_variances(
    values: Sequence[float] | None,
    *,
    n_components: int,
    name: str,
) -> tuple[float, ...] | None:
    if values is None:
        return None
    array = np.asarray(values, dtype=float)
    if array.shape != (n_components,):
        raise ValueError(
            f"{name} must contain one value per component"
        )
    if not np.all(np.isfinite(array)) or np.any(array < 0):
        raise ValueError(f"{name} must be finite and non-negative")
    return tuple(float(value) for value in array)


def _scenario_samples(
    value: int | tuple[int, int] | None,
) -> int | tuple[int, int] | None:
    if value is None:
        return None
    if isinstance(value, (int, np.integer)):
        if int(value) < 2:
            raise ValueError("samples_per_curve must be at least 2")
        return int(value)
    if len(value) != 2:
        raise ValueError(
            "samples_per_curve must be an int or (minimum, maximum)"
        )
    lower, upper = int(value[0]), int(value[1])
    if lower < 2 or upper < lower:
        raise ValueError(
            "samples_per_curve must satisfy 2 <= minimum <= maximum"
        )
    return (lower, upper)


@dataclass(frozen=True)
class FunctionalSimulationScenario:
    """Declared finite-sample design for native functional simulation."""

    name: str
    truth_grid: Sequence[float]
    eigenvalues: Sequence[float]
    n_participants: int
    trials_per_participant: int = 1
    dimension_names: Sequence[str] = ("value",)
    coordinate_system: str = "unknown"
    time_unit: str = "normalized"
    observation_design: str = "dense"
    samples_per_curve: int | tuple[int, int] | None = None
    irregular_time_design: str = "uniform"
    participant_eigenvalues: Sequence[float] | None = None
    trial_eigenvalues: Sequence[float] | None = None
    measurement_noise_sd: float | Sequence[float] | None = 0.0
    measurement_noise_covariance: np.ndarray | None = None
    missingness: Mapping[str, Any] | None = None
    phase_variation: Mapping[str, Any] | None = None
    score_distribution: str = "normal"
    score_df: float = 5.0
    orthonormal_tolerance: float = 1e-6
    replicates: int = 1
    seed_start: int = 42
    labels: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        name = str(self.name).strip()
        if not name:
            raise ValueError("scenario name must be non-empty")

        grid = np.asarray(self.truth_grid, dtype=float)
        if (
            grid.ndim != 1
            or grid.size < 3
            or not np.all(np.isfinite(grid))
            or not np.all(np.diff(grid) > 0)
        ):
            raise ValueError(
                "truth_grid must be finite and strictly increasing"
            )

        eigenvalues = np.asarray(self.eigenvalues, dtype=float)
        if eigenvalues.ndim != 1 or eigenvalues.size < 1:
            raise ValueError(
                "eigenvalues must be a non-empty one-dimensional sequence"
            )
        if not np.all(np.isfinite(eigenvalues)) or np.any(eigenvalues <= 0):
            raise ValueError("eigenvalues must be finite and positive")
        if np.any(np.diff(eigenvalues) > 0):
            raise ValueError(
                "eigenvalues must be supplied in descending order"
            )

        if int(self.n_participants) < 1:
            raise ValueError("n_participants must be positive")
        if int(self.trials_per_participant) < 1:
            raise ValueError("trials_per_participant must be positive")
        if int(self.replicates) < 1:
            raise ValueError("replicates must be positive")
        if not isinstance(self.seed_start, (int, np.integer)):
            raise TypeError("seed_start must be an integer")

        dimensions = tuple(str(value) for value in self.dimension_names)
        if not dimensions or any(not value for value in dimensions):
            raise ValueError(
                "dimension_names must contain non-empty values"
            )
        if len(set(dimensions)) != len(dimensions):
            raise ValueError("dimension_names must be unique")

        if self.observation_design not in {"dense", "irregular"}:
            raise ValueError(
                "observation_design must be 'dense' or 'irregular'"
            )
        samples = _scenario_samples(self.samples_per_curve)
        if self.observation_design == "dense" and samples is not None:
            raise ValueError(
                "samples_per_curve is only defined for irregular scenarios"
            )
        if self.observation_design == "irregular" and samples is None:
            raise ValueError(
                "irregular scenarios require samples_per_curve"
            )

        participant = _scenario_variances(
            self.participant_eigenvalues,
            n_components=eigenvalues.size,
            name="participant_eigenvalues",
        )
        trial = _scenario_variances(
            self.trial_eigenvalues,
            n_components=eigenvalues.size,
            name="trial_eigenvalues",
        )

        if self.score_distribution not in {"normal", "student_t"}:
            raise ValueError(
                "score_distribution must be 'normal' or 'student_t'"
            )
        score_df = float(self.score_df)
        if self.score_distribution == "student_t" and (
            not np.isfinite(score_df) or score_df <= 2
        ):
            raise ValueError(
                "score_df must exceed 2 for Student-t score simulation"
            )

        tolerance = float(self.orthonormal_tolerance)
        if not np.isfinite(tolerance) or tolerance <= 0:
            raise ValueError(
                "orthonormal_tolerance must be finite and positive"
            )

        object.__setattr__(self, "name", name)
        object.__setattr__(
            self,
            "truth_grid",
            tuple(float(value) for value in grid),
        )
        object.__setattr__(
            self,
            "eigenvalues",
            tuple(float(value) for value in eigenvalues),
        )
        object.__setattr__(
            self,
            "n_participants",
            int(self.n_participants),
        )
        object.__setattr__(
            self,
            "trials_per_participant",
            int(self.trials_per_participant),
        )
        object.__setattr__(self, "dimension_names", dimensions)
        object.__setattr__(self, "samples_per_curve", samples)
        object.__setattr__(
            self,
            "participant_eigenvalues",
            participant,
        )
        object.__setattr__(self, "trial_eigenvalues", trial)
        object.__setattr__(
            self,
            "missingness",
            _immutable_mapping(self.missingness),
        )
        object.__setattr__(
            self,
            "phase_variation",
            _immutable_mapping(self.phase_variation),
        )
        object.__setattr__(self, "score_df", score_df)
        object.__setattr__(
            self,
            "orthonormal_tolerance",
            tolerance,
        )
        object.__setattr__(self, "replicates", int(self.replicates))
        object.__setattr__(self, "seed_start", int(self.seed_start))
        object.__setattr__(
            self,
            "labels",
            MappingProxyType(dict(self.labels)),
        )

    @property
    def n_time(self) -> int:
        """Number of points on the canonical truth grid."""

        return len(self.truth_grid)

    def seeds(self) -> tuple[int, ...]:
        """Deterministic replicate seeds declared by the scenario."""

        return tuple(
            self.seed_start + replicate
            for replicate in range(self.replicates)
        )

    def simulation_kwargs(self, *, seed: int) -> dict[str, Any]:
        """Simulator keyword arguments for one replicate."""

        return {
            "eigenvalues": self.eigenvalues,
            "truth_grid": np.asarray(self.truth_grid, dtype=float),
            "n_participants": self.n_participants,
            "trials_per_participant": self.trials_per_participant,
            "dimension_names": self.dimension_names,
            "coordinate_system": self.coordinate_system,
            "time_unit": self.time_unit,
            "observation_design": self.observation_design,
            "samples_per_curve": self.samples_per_curve,
            "irregular_time_design": self.irregular_time_design,
            "participant_eigenvalues": self.participant_eigenvalues,
            "trial_eigenvalues": self.trial_eigenvalues,
            "measurement_noise_sd": self.measurement_noise_sd,
            "measurement_noise_covariance": self.measurement_noise_covariance,
            "missingness": (
                None
                if self.missingness is None
                else dict(self.missingness)
            ),
            "phase_variation": (
                None
                if self.phase_variation is None
                else dict(self.phase_variation)
            ),
            "score_distribution": self.score_distribution,
            "score_df": self.score_df,
            "orthonormal_tolerance": self.orthonormal_tolerance,
            "random_state": int(seed),
        }


@dataclass(frozen=True)
class FunctionalRecoveryRecord:
    """Recovery metrics for one declared scenario replicate."""

    scenario_name: str
    replicate: int
    seed: int
    metrics: Mapping[str, float]

    def __post_init__(self) -> None:
        if not self.metrics:
            raise ValueError("recovery metrics must be non-empty")
        clean = {}
        for key, value in self.metrics.items():
            name = str(key).strip()
            scalar = float(value)
            if not name or not np.isfinite(scalar):
                raise ValueError(
                    "recovery metrics require names and finite values"
                )
            clean[name] = scalar
        object.__setattr__(
            self,
            "metrics",
            MappingProxyType(clean),
        )


@dataclass(frozen=True)
class FunctionalRecoveryResult:
    """Collection of finite-sample recovery records."""

    records: tuple[FunctionalRecoveryRecord, ...]

    def __post_init__(self) -> None:
        if not self.records:
            raise ValueError(
                "recovery result must contain at least one record"
            )


def simulate_functional_scenario(
    scenario: FunctionalSimulationScenario,
    *,
    mean: Callable[[np.ndarray], np.ndarray],
    eigenfunctions: Sequence[Callable[[np.ndarray], np.ndarray]],
    replicate: int = 0,
) -> FunctionalSimulationResult:
    """Simulate one scenario replicate and stamp scenario provenance."""

    if not isinstance(scenario, FunctionalSimulationScenario):
        raise TypeError(
            "scenario must be a FunctionalSimulationScenario"
        )
    replicate = int(replicate)
    if replicate < 0 or replicate >= scenario.replicates:
        raise ValueError(
            "replicate is outside the declared scenario range"
        )
    seed = scenario.seeds()[replicate]
    result = simulate_functional_process(
        mean=mean,
        eigenfunctions=eigenfunctions,
        **scenario.simulation_kwargs(seed=seed),
    )
    provenance = dict(result.truth.provenance)
    provenance.update(
        {
            "scenario_name": scenario.name,
            "scenario_replicate": replicate,
            "scenario_seed": seed,
            "scenario_labels": dict(scenario.labels),
        }
    )
    return replace(
        result,
        truth=replace(
            result.truth,
            provenance=provenance,
        ),
    )


def run_functional_recovery_scenarios(
    scenarios: Sequence[FunctionalSimulationScenario],
    *,
    mean: Callable[[np.ndarray], np.ndarray],
    eigenfunctions: Sequence[Callable[[np.ndarray], np.ndarray]],
    estimator: FunctionalEstimator,
    recovery: FunctionalRecoveryScorer,
) -> FunctionalRecoveryResult:
    """Fit and score scenarios without passing truth to the estimator.

    The estimator receives observations and the declared scenario only.
    The recovery callback runs afterward and receives the fitted object
    plus exact truth. This function performs no automatic tuning and
    applies no package-chosen qualification threshold.
    """

    scenarios = tuple(scenarios)
    if not scenarios:
        raise ValueError("scenarios must be non-empty")
    if not callable(estimator) or not callable(recovery):
        raise TypeError(
            "estimator and recovery must be callable"
        )

    records = []
    for scenario in scenarios:
        if not isinstance(
            scenario,
            FunctionalSimulationScenario,
        ):
            raise TypeError(
                "every scenario must be a FunctionalSimulationScenario"
            )
        for replicate, seed in enumerate(scenario.seeds()):
            simulation = simulate_functional_scenario(
                scenario,
                mean=mean,
                eigenfunctions=eigenfunctions,
                replicate=replicate,
            )
            fitted = estimator(
                simulation.observations,
                scenario,
            )
            metrics = recovery(
                fitted,
                simulation.truth,
                scenario,
            )
            records.append(
                FunctionalRecoveryRecord(
                    scenario_name=scenario.name,
                    replicate=replicate,
                    seed=seed,
                    metrics=metrics,
                )
            )
    return FunctionalRecoveryResult(records=tuple(records))


def functional_recovery_frame(
    result: FunctionalRecoveryResult,
) -> pd.DataFrame:
    """Return one tidy row per scenario replicate and metric."""

    if not isinstance(result, FunctionalRecoveryResult):
        raise TypeError(
            "result must be a FunctionalRecoveryResult"
        )
    rows = []
    for record in result.records:
        for metric, value in record.metrics.items():
            rows.append(
                {
                    "scenario": record.scenario_name,
                    "replicate": record.replicate,
                    "seed": record.seed,
                    "metric": metric,
                    "value": value,
                }
            )
    return pd.DataFrame(rows)


def functional_simulation_scenario_frame(
    scenarios: Sequence[FunctionalSimulationScenario],
) -> pd.DataFrame:
    """Return an auditable one-row-per-scenario design table."""

    rows = []
    for scenario in scenarios:
        if not isinstance(
            scenario,
            FunctionalSimulationScenario,
        ):
            raise TypeError(
                "every scenario must be a FunctionalSimulationScenario"
            )
        samples = scenario.samples_per_curve
        if isinstance(samples, tuple):
            sample_min, sample_max = samples
        elif samples is None:
            sample_min = sample_max = scenario.n_time
        else:
            sample_min = sample_max = samples
        rows.append(
            {
                "scenario": scenario.name,
                "n_participants": scenario.n_participants,
                "trials_per_participant": (
                    scenario.trials_per_participant
                ),
                "n_curves": (
                    scenario.n_participants
                    * scenario.trials_per_participant
                ),
                "n_time_truth": scenario.n_time,
                "n_components": len(scenario.eigenvalues),
                "eigenvalues": json.dumps(
                    scenario.eigenvalues
                ),
                "observation_design": (
                    scenario.observation_design
                ),
                "samples_per_curve_min": sample_min,
                "samples_per_curve_max": sample_max,
                "irregular_time_design": (
                    scenario.irregular_time_design
                ),
                "missingness": (
                    None
                    if scenario.missingness is None
                    else json.dumps(
                        dict(scenario.missingness),
                        sort_keys=True,
                    )
                ),
                "phase_variation": (
                    None
                    if scenario.phase_variation is None
                    else json.dumps(
                        dict(scenario.phase_variation),
                        sort_keys=True,
                    )
                ),
                "score_distribution": (
                    scenario.score_distribution
                ),
                "replicates": scenario.replicates,
                "seed_start": scenario.seed_start,
                "labels": json.dumps(
                    dict(scenario.labels),
                    sort_keys=True,
                ),
            }
        )
    return pd.DataFrame(rows)


def _scenario_factor_slug(value: Any) -> str:
    if isinstance(value, Mapping):
        raw = str(value.get("kind", "mapping"))
    elif isinstance(value, np.ndarray):
        raw = f"array{value.size}"
    elif (
        isinstance(value, Sequence)
        and not isinstance(value, (str, bytes))
    ):
        raw = (
            f"seq{len(value)}"
            if len(value) > 4
            else "-".join(map(str, value))
        )
    else:
        raw = str(value)
    return (
        re.sub(
            r"[^A-Za-z0-9_.+-]+",
            "-",
            raw,
        ).strip("-")
        or "value"
    )


def expand_functional_simulation_scenarios(
    base: FunctionalSimulationScenario,
    factors: Mapping[str, Sequence[Any]],
    *,
    seed_policy: Literal["shared", "disjoint"] = "shared",
) -> tuple[FunctionalSimulationScenario, ...]:
    """Expand a Cartesian matrix with explicit seed handling.

    shared uses identical replicate seeds across scenarios for paired
    comparisons. disjoint assigns non-overlapping seed blocks.
    """

    if not isinstance(base, FunctionalSimulationScenario):
        raise TypeError(
            "base must be a FunctionalSimulationScenario"
        )
    if not factors:
        raise ValueError("factors must be non-empty")
    if seed_policy not in {"shared", "disjoint"}:
        raise ValueError(
            "seed_policy must be 'shared' or 'disjoint'"
        )

    allowed = set(
        FunctionalSimulationScenario.__dataclass_fields__
    ) - {"name"}
    factor_names = tuple(factors)
    levels = []
    for name in factor_names:
        if name not in allowed:
            raise ValueError(
                f"unknown scenario factor {name!r}"
            )
        if name == "seed_start":
            raise ValueError(
                "seed_start is controlled by seed_policy"
            )
        values = factors[name]
        if isinstance(values, (str, bytes)):
            raise TypeError(
                f"factor {name!r} must be a sequence of levels"
            )
        values = tuple(values)
        if not values:
            raise ValueError(
                f"factor {name!r} must contain at least one level"
            )
        levels.append(values)

    scenarios = []
    for index, combination in enumerate(product(*levels)):
        updates = dict(
            zip(
                factor_names,
                combination,
                strict=True,
            )
        )
        suffix = "__".join(
            f"{name}={_scenario_factor_slug(value)}"
            for name, value in updates.items()
        )
        seed_start = base.seed_start
        if seed_policy == "disjoint":
            seed_start += index * base.replicates
        scenarios.append(
            replace(
                base,
                name=f"{base.name}__{suffix}",
                seed_start=seed_start,
                **updates,
            )
        )
    return tuple(scenarios)
