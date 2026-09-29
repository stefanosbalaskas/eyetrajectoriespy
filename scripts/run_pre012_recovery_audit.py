"""Decision-oriented pre-0.12 recovery audit.

This runner does not implement the planned 0.12 estimator. It uses the
published 0.11 simulation/recovery infrastructure to answer four narrower
questions before sparse multivariate planar FPCA development begins:

1. sensitivity of native sparse FPCA/PACE to signal-dependent observation loss;
2. information omitted when x/y are fitted separately while cross-channel
   covariance changes under fixed marginal covariance;
3. the explicit current boundary for sparse/unequal repeated-trial hierarchy;
4. reproducible external-comparator fixtures for mGSFPCA and related R methods.

The audit is descriptive. It does not silently reinterpret informative
missingness as an estimator defect and does not invent qualification thresholds.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import importlib.metadata
import json
import math
from pathlib import Path
import platform
from typing import Callable

import numpy as np
import pandas as pd

from eyetrajectoriespy import (
    FunctionalSimulationScenario,
    IrregularTrajectorySet,
    fit_functional_mixed_effects_regression,
    fit_sparse_fpca,
    functional_trapezoid_weights,
    simulate_functional_scenario,
)


RHO_LEVELS = (0.0, 0.3, 0.6, 0.9)
LOSS_MECHANISMS = (
    "mcar",
    "signal_dependent_x_loss",
    "signal_dependent_y_loss",
    "eccentricity_dependent_loss",
    "velocity_dependent_loss",
    "phase_dependent_loss",
)
TARGET_LOSS = 0.20
LOSS_STRENGTH = 1.5
GRID = np.linspace(0.0, 1.0, 51)


@dataclass(frozen=True)
class _PlanarDesign:
    rho_xy: float
    eigenvalues: tuple[float, ...]
    eigenfunctions: tuple[Callable[[np.ndarray], np.ndarray], ...]


def _mean_planar(time: np.ndarray) -> np.ndarray:
    time = np.asarray(time, dtype=float)
    return np.column_stack(
        (
            0.50 + 0.04 * np.sin(np.pi * time),
            0.50 + 0.04 * np.cos(np.pi * time),
        )
    )


def _scalar_mode(frequency: int) -> Callable[[np.ndarray], np.ndarray]:
    def mode(time: np.ndarray) -> np.ndarray:
        time = np.asarray(time, dtype=float)
        return np.sqrt(2.0) * np.sin(frequency * np.pi * time)

    return mode


def _vector_mode(
    scalar: Callable[[np.ndarray], np.ndarray],
    loading: np.ndarray,
) -> Callable[[np.ndarray], np.ndarray]:
    loading = np.asarray(loading, dtype=float).copy()

    def mode(time: np.ndarray) -> np.ndarray:
        values = scalar(np.asarray(time, dtype=float))
        return values[:, None] * loading[None, :]

    return mode


def _planar_design(rho_xy: float) -> _PlanarDesign:
    rho = float(rho_xy)
    if not np.isfinite(rho) or rho < 0.0 or rho >= 1.0:
        raise ValueError("rho_xy must satisfy 0 <= rho_xy < 1")

    plus = np.array([1.0, 1.0]) / np.sqrt(2.0)
    minus = np.array([1.0, -1.0]) / np.sqrt(2.0)
    temporal = ((_scalar_mode(1), 1.0), (_scalar_mode(2), 0.45))
    channel = ((plus, 1.0 + rho), (minus, 1.0 - rho))

    pairs = []
    for scalar, temporal_value in temporal:
        for loading, channel_value in channel:
            pairs.append(
                (
                    temporal_value * channel_value,
                    _vector_mode(scalar, loading),
                )
            )
    pairs.sort(key=lambda item: item[0], reverse=True)
    return _PlanarDesign(
        rho_xy=rho,
        eigenvalues=tuple(float(item[0]) for item in pairs),
        eigenfunctions=tuple(item[1] for item in pairs),
    )


def _planar_scenario(
    rho_xy: float,
    *,
    name: str,
    seed_start: int,
    replicates: int,
    n_participants: int = 24,
    samples_per_curve: tuple[int, int] = (24, 34),
) -> tuple[FunctionalSimulationScenario, _PlanarDesign]:
    design = _planar_design(rho_xy)
    scenario = FunctionalSimulationScenario(
        name=name,
        truth_grid=GRID,
        eigenvalues=design.eigenvalues,
        n_participants=n_participants,
        trials_per_participant=1,
        dimension_names=("x", "y"),
        coordinate_system="normalized",
        time_unit="normalized",
        observation_design="irregular",
        samples_per_curve=samples_per_curve,
        irregular_time_design="uniform",
        measurement_noise_sd=(0.03, 0.03),
        replicates=replicates,
        seed_start=seed_start,
        labels={
            "audit": "pre-0.12",
            "rho_xy": rho_xy,
            "marginal_covariance_contract": "fixed_across_rho",
        },
    )
    return scenario, design


def _truth_covariance(truth, first: int, second: int) -> np.ndarray:
    modes_first = np.asarray(truth.eigenfunctions[:, :, first], dtype=float)
    modes_second = np.asarray(truth.eigenfunctions[:, :, second], dtype=float)
    return np.einsum(
        "k,ks,kt->st",
        np.asarray(truth.eigenvalues, dtype=float),
        modes_first,
        modes_second,
        optimize=True,
    )


def _weighted_eigensystem(
    covariance: np.ndarray,
    grid: np.ndarray,
    n_components: int,
) -> tuple[np.ndarray, np.ndarray]:
    weights = functional_trapezoid_weights(grid)
    sqrt_weights = np.sqrt(weights)
    operator = (
        sqrt_weights[:, None]
        * np.asarray(covariance, dtype=float)
        * sqrt_weights[None, :]
    )
    operator = 0.5 * (operator + operator.T)
    values, vectors = np.linalg.eigh(operator)
    order = np.argsort(values)[::-1]
    values = values[order][:n_components]
    vectors = vectors[:, order][:, :n_components]
    functions = (vectors / sqrt_weights[:, None]).T
    for index in range(functions.shape[0]):
        norm = math.sqrt(float(np.sum(functions[index] ** 2 * weights)))
        functions[index] /= norm
    return values, functions


def _subspace_min_cosine(
    estimated: np.ndarray,
    truth: np.ndarray,
    weights: np.ndarray,
) -> float:
    estimated = np.asarray(estimated, dtype=float)
    truth = np.asarray(truth, dtype=float)
    cross = (estimated * weights[None, :]) @ truth.T
    singular = np.linalg.svd(cross, compute_uv=False)
    singular = np.clip(singular, 0.0, 1.0)
    return float(np.min(singular))


def _fit_sparse_dimension(observations, truth, dimension: str):
    index = truth.dimension_names.index(dimension)
    return fit_sparse_fpca(
        observations,
        dimension=dimension,
        n_components=2,
        evaluation_grid=np.asarray(truth.truth_grid, dtype=float),
        mean_bandwidth=0.20,
        covariance_bandwidth=0.28,
        noise_variance_method="fixed",
        measurement_error_variance=float(
            truth.measurement_noise_covariance[index, index]
        ),
        psd_action="project",
        score_failure_action="retain_nan",
    )


def _marginal_metrics(fitted, truth, dimension: str) -> dict[str, float]:
    index = truth.dimension_names.index(dimension)
    grid = np.asarray(truth.truth_grid, dtype=float)
    weights = functional_trapezoid_weights(grid)
    covariance_weights = np.outer(weights, weights)
    true_mean = np.asarray(truth.mean[:, index], dtype=float)
    true_covariance = _truth_covariance(truth, index, index)
    _, true_functions = _weighted_eigensystem(true_covariance, grid, 2)

    fitted_mean = np.asarray(fitted.mean, dtype=float)
    fitted_covariance = np.asarray(fitted.covariance, dtype=float)
    fitted_functions = np.asarray(fitted.eigenfunctions, dtype=float)
    reconstruction = (
        fitted_mean[None, :]
        + np.asarray(fitted.scores, dtype=float) @ fitted_functions
    )
    latent = np.asarray(truth.latent_on_truth_grid[:, :, index], dtype=float)
    curve_ise = np.sum(
        (reconstruction - latent) ** 2 * weights[None, :],
        axis=1,
    )
    finite_curve = np.isfinite(curve_ise)

    diagnostics = fitted.score_diagnostics
    if len(diagnostics) and "status_code" in diagnostics.columns:
        failure_rate = float(
            np.mean(diagnostics["status_code"].to_numpy() != "ok")
        )
    else:
        failure_rate = float(
            np.mean(~np.all(np.isfinite(fitted.scores), axis=1))
        )

    return {
        "mean_ise": float(
            np.sum((fitted_mean - true_mean) ** 2 * weights)
        ),
        "covariance_ise": float(
            np.sum(
                (fitted_covariance - true_covariance) ** 2
                * covariance_weights
            )
        ),
        "subspace_min_principal_cosine": _subspace_min_cosine(
            fitted_functions,
            true_functions,
            weights,
        ),
        "reconstruction_ise": (
            float(np.mean(curve_ise[finite_curve]))
            if np.any(finite_curve)
            else float("nan")
        ),
        "score_failure_rate": failure_rate,
    }


def _standardize(values: tuple[np.ndarray, ...]) -> tuple[np.ndarray, ...]:
    pooled = np.concatenate(values)
    mean = float(np.mean(pooled))
    sd = float(np.std(pooled))
    if not np.isfinite(sd) or sd <= 1e-12:
        return tuple(np.zeros_like(value, dtype=float) for value in values)
    return tuple((np.asarray(value, dtype=float) - mean) / sd for value in values)


def _loss_predictors(truth, mechanism: str) -> tuple[np.ndarray, ...] | None:
    if mechanism == "mcar":
        return None

    predictors = []
    for time, warped, latent in zip(
        truth.pre_missing_observation_times,
        truth.warped_pre_missing_observation_times,
        truth.latent_at_pre_missing_times,
        strict=True,
    ):
        time = np.asarray(time, dtype=float)
        warped = np.asarray(warped, dtype=float)
        latent = np.asarray(latent, dtype=float)
        if mechanism == "signal_dependent_x_loss":
            raw = latent[:, 0]
        elif mechanism == "signal_dependent_y_loss":
            raw = latent[:, 1]
        elif mechanism == "eccentricity_dependent_loss":
            raw = np.sqrt(
                (latent[:, 0] - 0.5) ** 2
                + (latent[:, 1] - 0.5) ** 2
            )
        elif mechanism == "velocity_dependent_loss":
            dx = np.gradient(latent[:, 0], time)
            dy = np.gradient(latent[:, 1], time)
            raw = np.sqrt(dx**2 + dy**2)
        elif mechanism == "phase_dependent_loss":
            domain = float(time[-1] - time[0])
            raw = (warped - time[0]) / domain
        else:
            raise ValueError(f"unknown loss mechanism {mechanism!r}")
        predictors.append(np.asarray(raw, dtype=float))
    return _standardize(tuple(predictors))


def _calibrated_intercept(
    predictors: tuple[np.ndarray, ...],
    *,
    target: float,
    strength: float,
) -> float:
    pooled = np.concatenate(predictors)
    lo, hi = -20.0, 20.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        linear = np.clip(mid + strength * pooled, -40.0, 40.0)
        probability = 1.0 / (1.0 + np.exp(-linear))
        if float(np.mean(probability)) < target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def _apply_loss(simulation, mechanism: str, *, seed: int):
    truth = simulation.truth
    rng = np.random.default_rng(seed)
    predictors = _loss_predictors(truth, mechanism)

    if predictors is None:
        probabilities = tuple(
            np.full(len(time), TARGET_LOSS, dtype=float)
            for time in truth.pre_missing_observation_times
        )
    else:
        intercept = _calibrated_intercept(
            predictors,
            target=TARGET_LOSS,
            strength=LOSS_STRENGTH,
        )
        probabilities = tuple(
            1.0
            / (
                1.0
                + np.exp(
                    -np.clip(
                        intercept + LOSS_STRENGTH * value,
                        -40.0,
                        40.0,
                    )
                )
            )
            for value in predictors
        )

    masks = tuple(
        rng.random(len(probability)) < probability
        for probability in probabilities
    )
    retained = tuple(~mask for mask in masks)
    minimum = min(int(np.count_nonzero(keep)) for keep in retained)
    if minimum < 4:
        raise RuntimeError(
            "signal-dependent loss left fewer than four samples on a curve"
        )

    observations = IrregularTrajectorySet(
        time=tuple(
            np.asarray(time, dtype=float)[keep]
            for time, keep in zip(
                truth.pre_missing_observation_times,
                retained,
                strict=True,
            )
        ),
        values=tuple(
            np.asarray(values, dtype=float)[keep]
            for values, keep in zip(
                truth.observed_pre_missing,
                retained,
                strict=True,
            )
        ),
        curve_ids=simulation.observations.curve_ids,
        dimension_names=truth.dimension_names,
        metadata=truth.metadata,
        coordinate_system=truth.coordinate_system,
        time_unit=truth.time_unit,
        provenance={
            **dict(simulation.observations.provenance),
            "pre012_observation_process": mechanism,
            "pre012_target_loss": TARGET_LOSS,
            "pre012_strength": LOSS_STRENGTH,
            "pre012_mask_seed": seed,
        },
    )
    total = sum(len(mask) for mask in masks)
    missing = sum(int(np.count_nonzero(mask)) for mask in masks)
    return observations, {
        "target_loss_fraction": TARGET_LOSS,
        "actual_loss_fraction": missing / total,
        "minimum_retained_samples": minimum,
        "mean_retained_samples": float(
            np.mean([np.count_nonzero(keep) for keep in retained])
        ),
    }


def _signal_dependent_audit() -> pd.DataFrame:
    scenario, design = _planar_scenario(
        0.6,
        name="pre012_signal_loss",
        seed_start=8100,
        replicates=3,
    )
    rows = []
    for replicate in range(scenario.replicates):
        simulation = simulate_functional_scenario(
            scenario,
            mean=_mean_planar,
            eigenfunctions=design.eigenfunctions,
            replicate=replicate,
        )
        for mechanism_index, mechanism in enumerate(LOSS_MECHANISMS):
            try:
                observations, design_metrics = _apply_loss(
                    simulation,
                    mechanism,
                    seed=scenario.seeds()[replicate]
                    + 10000 * (mechanism_index + 1),
                )
            except Exception as exc:
                rows.append(
                    {
                        "mechanism": mechanism,
                        "replicate": replicate,
                        "dimension": "both",
                        "status": "observation_process_failed",
                        "error_type": type(exc).__name__,
                        "error_message": str(exc),
                    }
                )
                continue

            for dimension in ("x", "y"):
                row = {
                    "mechanism": mechanism,
                    "replicate": replicate,
                    "dimension": dimension,
                    "status": "ok",
                    **design_metrics,
                }
                try:
                    fitted = _fit_sparse_dimension(
                        observations,
                        simulation.truth,
                        dimension,
                    )
                    row.update(
                        _marginal_metrics(
                            fitted,
                            simulation.truth,
                            dimension,
                        )
                    )
                except Exception as exc:
                    row.update(
                        {
                            "status": "fit_failed",
                            "error_type": type(exc).__name__,
                            "error_message": str(exc),
                        }
                    )
                rows.append(row)
    return pd.DataFrame(rows)


def _joint_truth_metrics(truth) -> dict[str, float]:
    grid = np.asarray(truth.truth_grid, dtype=float)
    weights = functional_trapezoid_weights(grid)
    pair_weights = np.outer(weights, weights)
    cxx = _truth_covariance(truth, 0, 0)
    cyy = _truth_covariance(truth, 1, 1)
    cxy = _truth_covariance(truth, 0, 1)
    marginal = float(
        np.sum(cxx**2 * pair_weights)
        + np.sum(cyy**2 * pair_weights)
    )
    cross = float(2.0 * np.sum(cxy**2 * pair_weights))
    total = marginal + cross
    diagonal_correlation = np.diag(cxy) / np.sqrt(
        np.maximum(np.diag(cxx) * np.diag(cyy), 1e-15)
    )
    return {
        "truth_cross_block_energy": cross,
        "truth_total_block_energy": total,
        "truth_cross_block_energy_fraction": cross / total,
        "truth_mean_absolute_same_time_correlation": float(
            np.sum(np.abs(diagonal_correlation) * weights)
            / np.sum(weights)
        ),
    }


def _cross_channel_audit() -> pd.DataFrame:
    rows = []
    for rho_index, rho in enumerate(RHO_LEVELS):
        scenario, design = _planar_scenario(
            rho,
            name=f"pre012_rho_{rho:.1f}",
            seed_start=8400,
            replicates=3,
        )
        for replicate in range(scenario.replicates):
            simulation = simulate_functional_scenario(
                scenario,
                mean=_mean_planar,
                eigenfunctions=design.eigenfunctions,
                replicate=replicate,
            )
            truth_metrics = _joint_truth_metrics(simulation.truth)
            rows.append(
                {
                    "rho_xy": rho,
                    "replicate": replicate,
                    "dimension": "joint_truth",
                    "status": "ok",
                    **truth_metrics,
                }
            )
            for dimension in ("x", "y"):
                row = {
                    "rho_xy": rho,
                    "replicate": replicate,
                    "dimension": dimension,
                    "status": "ok",
                    **truth_metrics,
                }
                try:
                    fitted = _fit_sparse_dimension(
                        simulation.observations,
                        simulation.truth,
                        dimension,
                    )
                    row.update(
                        _marginal_metrics(
                            fitted,
                            simulation.truth,
                            dimension,
                        )
                    )
                except Exception as exc:
                    row.update(
                        {
                            "status": "fit_failed",
                            "error_type": type(exc).__name__,
                            "error_message": str(exc),
                        }
                    )
                rows.append(row)
    return pd.DataFrame(rows)


def _mean_univariate(time: np.ndarray) -> np.ndarray:
    time = np.asarray(time, dtype=float)
    return 0.25 + 0.15 * time


def _hierarchy_scenario(
    *,
    name: str,
    samples_per_curve: tuple[int, int],
    seed: int,
) -> FunctionalSimulationScenario:
    return FunctionalSimulationScenario(
        name=name,
        truth_grid=GRID,
        eigenvalues=(0.55, 0.22),
        n_participants=10,
        trials_per_participant=3,
        dimension_names=("value",),
        coordinate_system="unknown",
        time_unit="normalized",
        observation_design="irregular",
        samples_per_curve=samples_per_curve,
        irregular_time_design="uniform",
        participant_eigenvalues=(0.30, 0.12),
        trial_eigenvalues=(0.18, 0.07),
        measurement_noise_sd=0.04,
        replicates=1,
        seed_start=seed,
        labels={"audit": "pre-0.12", "question": "sparse_hierarchy"},
    )


def _sparse_hierarchy_audit() -> pd.DataFrame:
    levels = (
        ("very_sparse_unequal", (8, 12), 8800),
        ("moderately_sparse_unequal", (14, 20), 8801),
        ("less_sparse_unequal", (24, 32), 8802),
    )
    rows = []
    eigenfunctions = (_scalar_mode(1), _scalar_mode(2))
    for name, samples, seed in levels:
        scenario = _hierarchy_scenario(
            name=name,
            samples_per_curve=samples,
            seed=seed,
        )
        simulation = simulate_functional_scenario(
            scenario,
            mean=_mean_univariate,
            eigenfunctions=eigenfunctions,
        )
        counts = simulation.observations.sample_counts
        design = pd.DataFrame(
            {"curve_id": simulation.observations.curve_ids}
        )
        row = {
            "scenario": name,
            "samples_per_curve_min_declared": samples[0],
            "samples_per_curve_max_declared": samples[1],
            "observed_samples_min": int(np.min(counts)),
            "observed_samples_mean": float(np.mean(counts)),
            "observed_samples_max": int(np.max(counts)),
            "native_irregular_input_supported": False,
            "status": "boundary_confirmed",
        }
        try:
            fit_functional_mixed_effects_regression(
                simulation.observations,
                design,
                predictors=(),
                participant_column="participant_id",
                trial_column="trial_id",
                trial_random_effect="functional_intercept",
                dimension="value",
                fixed_basis_size=3,
                random_basis_size=2,
                trial_random_basis_size=2,
                spline_degree=1,
                maxiter=100,
            )
        except Exception as exc:
            row["error_type"] = type(exc).__name__
            row["error_message"] = str(exc)
        else:
            row["native_irregular_input_supported"] = True
            row["status"] = "unexpected_direct_fit"
        rows.append(row)
    return pd.DataFrame(rows)


def _external_fixture(output_dir: Path) -> dict[str, object]:
    scenario, design = _planar_scenario(
        0.6,
        name="pre012_external_fixture",
        seed_start=9100,
        replicates=1,
        n_participants=30,
        samples_per_curve=(20, 32),
    )
    simulation = simulate_functional_scenario(
        scenario,
        mean=_mean_planar,
        eigenfunctions=design.eigenfunctions,
    )
    for dimension_index, dimension in enumerate(("x", "y")):
        rows = []
        for curve_id, time, values in zip(
            simulation.observations.curve_ids,
            simulation.observations.time,
            simulation.observations.values,
            strict=True,
        ):
            for time_value, value in zip(
                time,
                values[:, dimension_index],
                strict=True,
            ):
                rows.append(
                    {
                        "ID": curve_id,
                        "time": float(time_value),
                        "value": float(value),
                    }
                )
        pd.DataFrame(rows).to_csv(
            output_dir / f"external_fixture_{dimension}.csv",
            index=False,
        )

    truth_metrics = _joint_truth_metrics(simulation.truth)
    truth_payload = {
        "rho_xy": 0.6,
        "truth_grid": np.asarray(
            simulation.truth.truth_grid, dtype=float
        ).tolist(),
        "eigenvalues": np.asarray(
            simulation.truth.eigenvalues, dtype=float
        ).tolist(),
        "eigenfunctions": np.asarray(
            simulation.truth.eigenfunctions, dtype=float
        ).tolist(),
        "mean": np.asarray(simulation.truth.mean, dtype=float).tolist(),
        "joint_truth_metrics": truth_metrics,
        "fixture_contract": {
            "columns": ["ID", "time", "value"],
            "variables": ["x", "y"],
            "selection_policy": (
                "external comparators must use explicit rank/basis settings; "
                "automatic model selection must not be treated as equivalent"
            ),
        },
    }
    (output_dir / "external_fixture_truth.json").write_text(
        json.dumps(truth_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return truth_payload


def _environment() -> dict[str, object]:
    packages = {}
    for name in (
        "eyetrajectoriespy",
        "numpy",
        "pandas",
        "scipy",
        "scikit-learn",
        "statsmodels",
    ):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "packages": packages,
    }


def _frame_records(frame: pd.DataFrame) -> list[dict[str, object]]:
    clean = frame.replace({np.nan: None})
    records = clean.to_dict(orient="records")
    for row in records:
        for key, value in tuple(row.items()):
            if isinstance(value, np.generic):
                row[key] = value.item()
    return records


def run_audit(output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)

    signal = _signal_dependent_audit()
    cross = _cross_channel_audit()
    hierarchy = _sparse_hierarchy_audit()
    external_truth = _external_fixture(output_dir)

    signal.to_csv(output_dir / "signal_dependent_missingness.csv", index=False)
    cross.to_csv(output_dir / "cross_channel_truth.csv", index=False)
    hierarchy.to_csv(output_dir / "sparse_hierarchy_boundary.csv", index=False)

    cross_truth = (
        cross.loc[cross["dimension"] == "joint_truth"]
        .groupby("rho_xy", as_index=False)[
            [
                "truth_cross_block_energy_fraction",
                "truth_mean_absolute_same_time_correlation",
            ]
        ]
        .mean()
    )
    signal_summary = (
        signal.loc[signal["status"] == "ok"]
        .groupby(["mechanism", "dimension"], as_index=False)
        .agg(
            actual_loss_fraction=("actual_loss_fraction", "mean"),
            mean_ise=("mean_ise", "mean"),
            covariance_ise=("covariance_ise", "mean"),
            subspace_min_principal_cosine=(
                "subspace_min_principal_cosine",
                "mean",
            ),
            reconstruction_ise=("reconstruction_ise", "mean"),
            score_failure_rate=("score_failure_rate", "mean"),
        )
    )

    payload = {
        "schema_version": 1,
        "audit": "pre-0.12 decision-oriented recovery audit",
        "package_version": importlib.metadata.version("eyetrajectoriespy"),
        "environment": _environment(),
        "questions": {
            "signal_dependent_missingness": {
                "status": "executed",
                "interpretation": (
                    "descriptive sensitivity evidence; informative loss is not "
                    "silently classified as an estimator defect"
                ),
                "mechanisms": list(LOSS_MECHANISMS),
                "target_loss_fraction": TARGET_LOSS,
                "summary": _frame_records(signal_summary),
            },
            "joint_vs_separate_xy": {
                "status": "executed",
                "interpretation": (
                    "marginal covariance is held fixed while the truth cross-"
                    "covariance block changes; separate sparse fits contain no "
                    "first-class cross-channel covariance operator"
                ),
                "rho_levels": list(RHO_LEVELS),
                "truth_summary": _frame_records(cross_truth),
            },
            "sparse_repeated_trial_hierarchy": {
                "status": "executed",
                "interpretation": (
                    "current functional mixed-effects regression requires "
                    "complete common-grid TrajectorySet input; this audit does "
                    "not interpolate sparse trials to manufacture compatibility"
                ),
                "results": _frame_records(hierarchy),
            },
            "external_comparison": {
                "status": "fixture_prepared",
                "primary_comparator": "mGSFPCA::spMultFPCA",
                "secondary_comparators": ["MFPCA", "bayesFPCA"],
                "runtime_dependency": False,
                "truth_metrics": external_truth["joint_truth_metrics"],
            },
        },
        "decision_contract": {
            "block_0.12_only_for": (
                "a result-changing/public-API defect inside an already supported "
                "0.11 contract"
            ),
            "does_not_count_as_0.11_defect": [
                "sensitivity under explicitly informative observation loss",
                "absence of a joint cross-channel covariance object from separate univariate fits",
                "fail-closed rejection of irregular input by the dense functional mixed-effects API",
            ],
            "next_method_if_no_supported-contract_defect": (
                "native sparse multivariate functional analysis for planar gaze"
            ),
        },
    }
    (output_dir / "pre012_audit_summary.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("pre012-audit"),
    )
    parser.add_argument(
        "--external-fixture-only",
        action="store_true",
        help=(
            "Generate only the frozen cross-language comparator fixture, "
            "without rerunning the full audit."
        ),
    )
    args = parser.parse_args()
    if args.external_fixture_only:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        truth = _external_fixture(args.output_dir)
        payload = {
            "schema_version": 1,
            "audit": "pre-0.12 external comparator fixture",
            "package_version": importlib.metadata.version("eyetrajectoriespy"),
            "environment": _environment(),
            "external_comparison": {
                "status": "fixture_prepared",
                "primary_comparator": "mGSFPCA::spMultFPCA",
                "truth_metrics": truth["joint_truth_metrics"],
            },
        }
        (args.output_dir / "external_fixture_summary.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    else:
        payload = run_audit(args.output_dir)
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
