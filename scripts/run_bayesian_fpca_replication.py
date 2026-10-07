"""Generate replicated known-truth evidence for Bayesian FPCA B2/B3.

This post-1.1 research harness extends immutable B1 evidence with:
- Monte Carlo replication under predeclared seeds;
- separate low-N and near-tied scenarios;
- a localized non-harmonic truth family;
- one simulation-only informative observation mechanism;
- secondary audited native bandwidth selection where supported; and
- native fitted conditional score-covariance exports for B3.

It does not add or modify a package estimator or public API.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
import importlib.metadata
import json
from pathlib import Path
import time

import numpy as np
import pandas as pd

from eyetrajectoriespy import IrregularTrajectorySet, fit_sparse_fpca, fit_sparse_mfpca
from eyetrajectoriespy.sparse_bandwidth_selection import (
    select_sparse_fpca_bandwidths,
)
from eyetrajectoriespy.sparse_multivariate import fit_sparse_mfpca
from eyetrajectoriespy.sparse_multivariate_async import fit_sparse_mfpca_async
from eyetrajectoriespy.sparse_multivariate_bandwidth_selection import (
    select_sparse_mfpca_bandwidths,
)
from eyetrajectoriespy.sparse_multivariate_score_uncertainty import (
    sparse_mfpca_score_uncertainty,
)
from eyetrajectoriespy.sparse_score_uncertainty import (
    sparse_fpca_score_uncertainty,
)


GRID = np.linspace(0.02, 0.98, 41)
N_COMPONENTS = 2
NOISE_SD = 0.05
BAYESFPCA_COMMIT = "f05b0615632cffe5c63838858d9a956af6588a73"
DEFAULT_REPLICATES = 16
BASE_SEED = 2026120700
K_SENSITIVITY = (5, 6, 7, 8, 9)
FAIRNESS_REPLICATES = 4
FAIRNESS_SCENARIOS = frozenset(
    {
        "univariate_extreme_sparse",
        "univariate_low_n",
        "univariate_near_tied",
        "univariate_localized",
        "planar_paired",
    }
)


@dataclass(frozen=True)
class Scenario:
    name: str
    design: str
    truth_family: str
    n_curves: int
    samples_min: int
    samples_max: int
    eigenvalues: tuple[float, float]
    mean_bandwidth: float
    covariance_bandwidth: float
    observation_mechanism: str = "independent_irregular"


SCENARIOS = (
    Scenario(
        "univariate_moderate",
        "univariate",
        "harmonic",
        32,
        12,
        18,
        (1.00, 0.40),
        0.20,
        0.30,
    ),
    Scenario(
        "univariate_extreme_sparse",
        "univariate",
        "harmonic",
        32,
        6,
        9,
        (1.00, 0.40),
        0.28,
        0.38,
    ),
    Scenario(
        "univariate_low_n",
        "univariate",
        "harmonic",
        14,
        12,
        18,
        (1.00, 0.40),
        0.22,
        0.32,
    ),
    Scenario(
        "univariate_near_tied",
        "univariate",
        "harmonic",
        32,
        12,
        18,
        (1.00, 0.90),
        0.20,
        0.30,
    ),
    Scenario(
        "univariate_localized",
        "univariate",
        "localized",
        32,
        12,
        18,
        (1.00, 0.40),
        0.18,
        0.28,
    ),
    Scenario(
        "univariate_informative_time",
        "univariate",
        "harmonic",
        32,
        4,
        17,
        (1.00, 0.40),
        0.20,
        0.30,
        "latent_value_and_time_logistic_retention",
    ),
    Scenario(
        "planar_paired",
        "planar_paired",
        "harmonic",
        28,
        12,
        18,
        (1.10, 0.55),
        0.22,
        0.32,
    ),
    Scenario(
        "planar_async",
        "planar_async",
        "harmonic",
        28,
        8,
        12,
        (1.10, 0.55),
        0.25,
        0.36,
    ),
)


def _trap_weights(grid: np.ndarray) -> np.ndarray:
    grid = np.asarray(grid, dtype=float)
    weights = np.empty_like(grid)
    weights[0] = 0.5 * (grid[1] - grid[0])
    weights[-1] = 0.5 * (grid[-1] - grid[-2])
    weights[1:-1] = 0.5 * (grid[2:] - grid[:-2])
    return weights


_LOCALIZED_REFERENCE_GRID = np.linspace(float(GRID[0]), float(GRID[-1]), 4001)
_LOCALIZED_REFERENCE_WEIGHTS = _trap_weights(_LOCALIZED_REFERENCE_GRID)


def _localized_raw(time_values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    time_values = np.asarray(time_values, dtype=float)
    first = np.maximum(
        1.0 - np.abs(time_values - 0.30) / 0.18,
        0.0,
    )
    second = np.maximum(
        1.0 - np.abs(time_values - 0.72) / 0.16,
        0.0,
    )
    return first, second


def _localized_constants() -> tuple[float, float, float]:
    first, second = _localized_raw(_LOCALIZED_REFERENCE_GRID)
    norm_first = np.sqrt(np.sum(first**2 * _LOCALIZED_REFERENCE_WEIGHTS))
    phi_first = first / norm_first
    projection = np.sum(second * phi_first * _LOCALIZED_REFERENCE_WEIGHTS)
    residual = second - projection * phi_first
    norm_second = np.sqrt(np.sum(residual**2 * _LOCALIZED_REFERENCE_WEIGHTS))
    return float(norm_first), float(projection), float(norm_second)


_LOCALIZED_NORM_FIRST, _LOCALIZED_PROJECTION, _LOCALIZED_NORM_SECOND = (
    _localized_constants()
)


def _scalar_modes(time_values: np.ndarray, truth_family: str) -> np.ndarray:
    time_values = np.asarray(time_values, dtype=float)
    if truth_family == "harmonic":
        return np.column_stack(
            (
                np.sqrt(2.0) * np.sin(np.pi * time_values),
                np.sqrt(2.0) * np.sin(2.0 * np.pi * time_values),
            )
        )
    if truth_family == "localized":
        first, second = _localized_raw(time_values)
        phi_first = first / _LOCALIZED_NORM_FIRST
        phi_second = (
            second - _LOCALIZED_PROJECTION * phi_first
        ) / _LOCALIZED_NORM_SECOND
        return np.column_stack((phi_first, phi_second))
    raise ValueError(f"unknown truth family {truth_family!r}")


def _mean(time_values: np.ndarray, scenario: Scenario) -> np.ndarray:
    time_values = np.asarray(time_values, dtype=float)
    if scenario.design == "univariate":
        if scenario.truth_family == "localized":
            bump = np.exp(-0.5 * ((time_values - 0.55) / 0.18) ** 2)
            return (0.20 + 0.08 * time_values + 0.05 * bump)[:, None]
        return (
            0.20 + 0.10 * time_values + 0.04 * np.sin(np.pi * time_values)
        )[:, None]
    return np.column_stack(
        (
            0.50 + 0.05 * np.sin(np.pi * time_values),
            0.50 + 0.05 * np.cos(np.pi * time_values),
        )
    )


def _modes(time_values: np.ndarray, scenario: Scenario) -> np.ndarray:
    scalar = _scalar_modes(time_values, scenario.truth_family)
    if scenario.design == "univariate":
        return scalar[:, :, None].transpose(1, 0, 2)
    plus = np.array([1.0, 1.0], dtype=float) / np.sqrt(2.0)
    minus = np.array([1.0, -1.0], dtype=float) / np.sqrt(2.0)
    return np.stack(
        (
            scalar[:, 0, None] * plus[None, :],
            scalar[:, 1, None] * minus[None, :],
        ),
        axis=0,
    )


def _latent(
    time_values: np.ndarray,
    scores: np.ndarray,
    scenario: Scenario,
) -> np.ndarray:
    return _mean(time_values, scenario) + np.einsum(
        "k,ktd->td",
        scores,
        _modes(time_values, scenario),
        optimize=True,
    )


def _sample_times(
    rng: np.random.Generator,
    low: int,
    high: int,
) -> np.ndarray:
    count = int(rng.integers(low, high + 1))
    if count < 2:
        raise ValueError("sample count must be at least two")
    interior = rng.uniform(float(GRID[0]), float(GRID[-1]), size=count - 2)
    return np.sort(
        np.concatenate(([float(GRID[0])], interior, [float(GRID[-1])]))
    )


def _informative_times(
    rng: np.random.Generator,
    score: np.ndarray,
    scenario: Scenario,
) -> tuple[np.ndarray, np.ndarray]:
    candidates = np.linspace(float(GRID[0]), float(GRID[-1]), 17)
    latent = _latent(candidates, score, scenario)[:, 0]
    centered = latent - _mean(candidates, scenario)[:, 0]
    scale = float(np.std(centered))
    standardized = centered / scale if scale > 0 else centered
    logits = 1.15 - 1.60 * (candidates - 0.50) - 0.75 * standardized
    probability = 1.0 / (1.0 + np.exp(-logits))
    retained = rng.uniform(size=candidates.size) < probability
    retained[[0, -1]] = True
    if int(np.count_nonzero(retained)) < 4:
        interior = np.argsort(probability[1:-1])[-2:] + 1
        retained[interior] = True
    return candidates[retained], probability


def _make_dataset(
    scenario: Scenario,
    *,
    seed: int,
) -> tuple[IrregularTrajectorySet, dict[str, object]]:
    rng = np.random.default_rng(seed)
    dimensions = ("x",) if scenario.design == "univariate" else ("x", "y")
    eigenvalues = np.asarray(scenario.eigenvalues, dtype=float)
    scores = rng.normal(size=(scenario.n_curves, N_COMPONENTS)) * np.sqrt(
        eigenvalues
    )[None, :]
    curve_ids = tuple(
        f"curve_{index + 1:03d}" for index in range(scenario.n_curves)
    )

    times: list[np.ndarray] = []
    values: list[np.ndarray] = []
    observed_by_dimension: dict[
        str, list[tuple[str, np.ndarray, np.ndarray]]
    ] = {dimension: [] for dimension in dimensions}
    informative_probability: dict[str, list[float]] = {}

    for curve_index, curve_id in enumerate(curve_ids):
        if scenario.observation_mechanism != "independent_irregular":
            curve_time, probability = _informative_times(
                rng,
                scores[curve_index],
                scenario,
            )
            informative_probability[curve_id] = probability.tolist()
            latent = _latent(curve_time, scores[curve_index], scenario)
            observed = latent + rng.normal(scale=NOISE_SD, size=latent.shape)
            times.append(curve_time)
            values.append(observed)
            observed_by_dimension["x"].append(
                (curve_id, curve_time, observed[:, 0])
            )
            continue

        if scenario.design != "planar_async":
            curve_time = _sample_times(
                rng,
                scenario.samples_min,
                scenario.samples_max,
            )
            latent = _latent(curve_time, scores[curve_index], scenario)
            observed = latent + rng.normal(scale=NOISE_SD, size=latent.shape)
            times.append(curve_time)
            values.append(observed)
            for dim_index, dimension in enumerate(dimensions):
                observed_by_dimension[dimension].append(
                    (curve_id, curve_time, observed[:, dim_index])
                )
            continue

        x_time = _sample_times(
            rng,
            scenario.samples_min,
            scenario.samples_max,
        )
        y_time = _sample_times(
            rng,
            scenario.samples_min,
            scenario.samples_max,
        )
        x_latent = _latent(x_time, scores[curve_index], scenario)[:, 0]
        y_latent = _latent(y_time, scores[curve_index], scenario)[:, 1]
        x_value = x_latent + rng.normal(scale=NOISE_SD, size=x_time.size)
        y_value = y_latent + rng.normal(scale=NOISE_SD, size=y_time.size)
        union = np.union1d(x_time, y_time)
        matrix = np.full((union.size, 2), np.nan, dtype=float)
        matrix[np.searchsorted(union, x_time), 0] = x_value
        matrix[np.searchsorted(union, y_time), 1] = y_value
        times.append(union)
        values.append(matrix)
        observed_by_dimension["x"].append((curve_id, x_time, x_value))
        observed_by_dimension["y"].append((curve_id, y_time, y_value))

    dataset = IrregularTrajectorySet(
        time=tuple(times),
        values=tuple(values),
        curve_ids=curve_ids,
        dimension_names=dimensions,
        metadata=pd.DataFrame(
            {
                "participant_id": list(curve_ids),
                "scenario": scenario.name,
            }
        ),
        coordinate_system="normalized",
        time_unit="normalized",
        provenance={
            "programme": "post-1.1-bayesian-fpca-b2-b3",
            "scenario": scenario.name,
            "truth_family": scenario.truth_family,
            "observation_mechanism": scenario.observation_mechanism,
            "known_truth": True,
            "raw_interpolation": False,
        },
    )

    truth_modes = _modes(GRID, scenario)
    truth_mean = _mean(GRID, scenario)
    truth_latent = np.stack(
        [
            truth_mean
            + np.einsum(
                "k,kgd->gd",
                score,
                truth_modes,
                optimize=True,
            )
            for score in scores
        ],
        axis=0,
    )
    truth: dict[str, object] = {
        "schema_version": 1,
        "scenario": scenario.name,
        "design": scenario.design,
        "truth_family": scenario.truth_family,
        "observation_mechanism": scenario.observation_mechanism,
        "known_truth": True,
        "truth_grid": GRID.tolist(),
        "dimension_names": list(dimensions),
        "curve_ids": list(curve_ids),
        "eigenvalues": eigenvalues.tolist(),
        "eigenfunctions": truth_modes.tolist(),
        "scores": scores.tolist(),
        "mean": truth_mean.tolist(),
        "latent_on_truth_grid": truth_latent.tolist(),
        "noise_sd": NOISE_SD,
        "frozen_mean_bandwidth": scenario.mean_bandwidth,
        "frozen_covariance_bandwidth": scenario.covariance_bandwidth,
        "observation_counts": {
            dimension: [
                int(item[1].size)
                for item in observed_by_dimension[dimension]
            ]
            for dimension in dimensions
        },
        "informative_candidate_retention_probability": informative_probability,
        "contract": {
            "equivalence_claim": False,
            "architecture_winner_selected": False,
            "automatic_promotion_decision": False,
            "truth_tuning_performed": False,
            "post_hoc_favorable_search_performed": False,
            "raw_interpolation": False,
            "external_runtime_backend": False,
        },
    }
    return dataset, {"truth": truth, "observed": observed_by_dimension}


def _fit_native(
    scenario: Scenario,
    dataset: IrregularTrajectorySet,
    *,
    mean_bandwidth: float,
    covariance_bandwidth: float,
):
    common = dict(
        n_components=N_COMPONENTS,
        evaluation_grid=GRID,
        mean_bandwidth=float(mean_bandwidth),
        covariance_bandwidth=float(covariance_bandwidth),
        psd_action="project",
        score_failure_action="retain_nan",
    )
    start = time.perf_counter()
    if scenario.design == "univariate":
        fit = fit_sparse_fpca(
            dataset,
            dimension="x",
            noise_variance_method="fixed",
            measurement_error_variance=NOISE_SD**2,
            **common,
        )
    elif scenario.design == "planar_paired":
        fit = fit_sparse_mfpca(
            dataset,
            dimensions=("x", "y"),
            measurement_error="diagonal",
            measurement_error_variance=(NOISE_SD**2, NOISE_SD**2),
            **common,
        )
    else:
        fit = fit_sparse_mfpca_async(
            dataset,
            dimensions=("x", "y"),
            measurement_error="diagonal",
            measurement_error_variance=(NOISE_SD**2, NOISE_SD**2),
            **common,
        )
    return fit, float(time.perf_counter() - start)


def _selected_bandwidths(
    scenario: Scenario,
    dataset: IrregularTrajectorySet,
    *,
    seed: int,
    replicate: int,
) -> tuple[dict[str, float] | None, pd.DataFrame | None]:
    if (
        replicate > FAIRNESS_REPLICATES
        or scenario.name not in FAIRNESS_SCENARIOS
    ):
        return None, None

    multipliers = (0.75, 1.00, 1.25)
    mean_candidates = tuple(
        multiplier * scenario.mean_bandwidth for multiplier in multipliers
    )
    covariance_candidates = tuple(
        multiplier * scenario.covariance_bandwidth for multiplier in multipliers
    )
    if scenario.design == "univariate":
        result = select_sparse_fpca_bandwidths(
            dataset,
            dimension="x",
            evaluation_grid=GRID,
            mean_bandwidths=mean_candidates,
            covariance_bandwidths=covariance_candidates,
            noise_variance_method="fixed",
            measurement_error_variance=NOISE_SD**2,
            n_splits=3,
            random_state=seed + 700,
            failure_action="retain",
            psd_action="project",
        )
    elif scenario.design == "planar_paired":
        result = select_sparse_mfpca_bandwidths(
            dataset,
            dimensions=("x", "y"),
            evaluation_grid=GRID,
            mean_bandwidths=mean_candidates,
            covariance_bandwidths=covariance_candidates,
            measurement_error="diagonal",
            measurement_error_variance=(NOISE_SD**2, NOISE_SD**2),
            n_splits=3,
            random_state=seed + 700,
            failure_action="retain",
            psd_action="project",
        )
    else:
        return None, None

    if result.selected_bandwidths is None:
        return None, result.candidate_summary.copy()
    selected = {
        "mean_bandwidth": float(
            result.selected_bandwidths["mean_bandwidth"]
        ),
        "covariance_bandwidth": float(
            result.selected_bandwidths["covariance_bandwidth"]
        ),
    }
    return selected, result.candidate_summary.copy()


def _function_array(fit, design: str) -> np.ndarray:
    functions = np.asarray(fit.eigenfunctions, dtype=float)
    if design == "univariate":
        return functions[:, :, None]
    return functions


def _mean_array(fit, design: str) -> np.ndarray:
    mean = np.asarray(fit.mean, dtype=float)
    if design == "univariate":
        return mean[:, None]
    return mean


def _write_function_long(
    path: Path,
    grid: np.ndarray,
    dimensions: tuple[str, ...],
    functions: np.ndarray,
) -> None:
    rows = []
    for component in range(functions.shape[0]):
        for dim_index, dimension in enumerate(dimensions):
            for time_value, value in zip(
                grid,
                functions[component, :, dim_index],
                strict=True,
            ):
                rows.append(
                    {
                        "component": component + 1,
                        "dimension": dimension,
                        "time": float(time_value),
                        "value": float(value),
                    }
                )
    pd.DataFrame(rows).to_csv(path, index=False)


def _write_mean(
    path: Path,
    grid: np.ndarray,
    dimensions: tuple[str, ...],
    mean: np.ndarray,
) -> None:
    frame = pd.DataFrame({"time": grid})
    for dim_index, dimension in enumerate(dimensions):
        frame[dimension] = mean[:, dim_index]
    frame.to_csv(path, index=False)


def _write_scores(
    path: Path,
    curve_ids: tuple[str, ...],
    scores: np.ndarray,
) -> None:
    frame = pd.DataFrame(
        np.asarray(scores, dtype=float),
        columns=[f"PC{index + 1}" for index in range(scores.shape[1])],
    )
    frame.insert(0, "curve_id", list(curve_ids))
    frame.to_csv(path, index=False)


def _write_eigenvalues(path: Path, values: np.ndarray) -> None:
    pd.DataFrame(
        {
            "component": np.arange(1, values.size + 1),
            "eigenvalue": np.asarray(values, dtype=float),
        }
    ).to_csv(path, index=False)


def _write_covariance_long(
    path: Path,
    curve_ids: tuple[str, ...],
    covariance: np.ndarray,
) -> None:
    rows = []
    for curve_index, curve_id in enumerate(curve_ids):
        for first in range(covariance.shape[1]):
            for second in range(covariance.shape[2]):
                rows.append(
                    {
                        "curve_id": curve_id,
                        "component_i": first + 1,
                        "component_j": second + 1,
                        "covariance": float(
                            covariance[curve_index, first, second]
                        ),
                    }
                )
    pd.DataFrame(rows).to_csv(path, index=False)


def _write_fit(
    scenario_dir: Path,
    prefix: str,
    fit,
    *,
    design: str,
    dimensions: tuple[str, ...],
) -> None:
    _write_mean(
        scenario_dir / f"{prefix}_mean.csv",
        GRID,
        dimensions,
        _mean_array(fit, design),
    )
    _write_function_long(
        scenario_dir / f"{prefix}_eigenfunctions.csv",
        GRID,
        dimensions,
        _function_array(fit, design),
    )
    _write_scores(
        scenario_dir / f"{prefix}_scores.csv",
        tuple(fit.curve_ids),
        np.asarray(fit.scores, dtype=float),
    )
    _write_eigenvalues(
        scenario_dir / f"{prefix}_eigenvalues.csv",
        np.asarray(fit.eigenvalues, dtype=float),
    )


def _write_observations(
    scenario_dir: Path,
    observed: dict[str, list[tuple[str, np.ndarray, np.ndarray]]],
) -> None:
    for dimension, curves in observed.items():
        rows = []
        for curve_id, time_values, values in curves:
            rows.extend(
                {
                    "curve_id": curve_id,
                    "time": float(time_value),
                    "value": float(value),
                }
                for time_value, value in zip(
                    time_values,
                    values,
                    strict=True,
                )
            )
        pd.DataFrame(rows).to_csv(
            scenario_dir / f"observations_{dimension}.csv",
            index=False,
        )


def _native_uncertainty(
    scenario: Scenario,
    fit,
    dataset: IrregularTrajectorySet,
):
    if scenario.design == "univariate":
        return sparse_fpca_score_uncertainty(
            fit,
            dataset,
            failure_action="retain_nan",
        )
    if scenario.design == "planar_paired":
        return sparse_mfpca_score_uncertainty(
            fit,
            dataset,
            failure_action="retain_nan",
        )
    return None


def generate(output_dir: Path, *, replicates: int) -> dict[str, object]:
    if replicates < 3:
        raise ValueError("replicates must be >= 3")
    output_dir.mkdir(parents=True, exist_ok=True)
    scenario_root = output_dir / "replicates"
    scenario_root.mkdir(exist_ok=True)

    manifest_rows: list[dict[str, object]] = []
    replicate_summaries: list[dict[str, object]] = []

    for scenario_index, template in enumerate(SCENARIOS):
        for replicate in range(1, replicates + 1):
            seed = BASE_SEED + scenario_index * 100 + replicate
            scenario = replace(template)
            replicate_dir = (
                scenario_root
                / scenario.name
                / f"replicate_{replicate:03d}"
            )
            replicate_dir.mkdir(parents=True, exist_ok=True)

            dataset, payload = _make_dataset(scenario, seed=seed)
            frozen_fit, frozen_elapsed = _fit_native(
                scenario,
                dataset,
                mean_bandwidth=scenario.mean_bandwidth,
                covariance_bandwidth=scenario.covariance_bandwidth,
            )
            _write_observations(replicate_dir, payload["observed"])
            (replicate_dir / "truth.json").write_text(
                json.dumps(payload["truth"], indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            pd.DataFrame({"time": GRID}).to_csv(
                replicate_dir / "truth_grid.csv",
                index=False,
            )
            _write_fit(
                replicate_dir,
                "native_frozen",
                frozen_fit,
                design=scenario.design,
                dimensions=dataset.dimension_names,
            )

            uncertainty = _native_uncertainty(
                scenario,
                frozen_fit,
                dataset,
            )
            uncertainty_available = uncertainty is not None
            if uncertainty is not None:
                _write_covariance_long(
                    replicate_dir / "native_frozen_score_covariance.csv",
                    tuple(frozen_fit.curve_ids),
                    np.asarray(uncertainty.covariance, dtype=float),
                )
                uncertainty.diagnostics.to_csv(
                    replicate_dir
                    / "native_frozen_score_uncertainty_diagnostics.csv",
                    index=False,
                )

            selected, selection_summary = _selected_bandwidths(
                scenario,
                dataset,
                seed=seed,
                replicate=replicate,
            )
            selected_status = "not_supported"
            selected_elapsed = np.nan
            if selection_summary is not None:
                selection_summary.to_csv(
                    replicate_dir / "native_bandwidth_selection.csv",
                    index=False,
                )
                selected_status = (
                    "selected" if selected is not None else "no_eligible_candidate"
                )
            if selected is not None:
                selected_fit, selected_elapsed = _fit_native(
                    scenario,
                    dataset,
                    mean_bandwidth=selected["mean_bandwidth"],
                    covariance_bandwidth=selected["covariance_bandwidth"],
                )
                _write_fit(
                    replicate_dir,
                    "native_selected",
                    selected_fit,
                    design=scenario.design,
                    dimensions=dataset.dimension_names,
                )
                (
                    replicate_dir / "native_selected_bandwidths.json"
                ).write_text(
                    json.dumps(selected, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )

            manifest_rows.append(
                {
                    "scenario": scenario.name,
                    "replicate": replicate,
                    "seed": seed,
                    "design": scenario.design,
                    "truth_family": scenario.truth_family,
                    "observation_mechanism": scenario.observation_mechanism,
                    "n_curves": scenario.n_curves,
                    "n_dimensions": len(dataset.dimension_names),
                    "n_components": N_COMPONENTS,
                    "primary_spline_basis_size": 7,
                    "k_sensitivity": ";".join(map(str, K_SENSITIVITY)),
                    "fairness_sensitivity": (
                        scenario.name in FAIRNESS_SCENARIOS
                        and replicate <= FAIRNESS_REPLICATES
                    ),
                    "relative_path": (
                        f"replicates/{scenario.name}/replicate_{replicate:03d}"
                    ),
                }
            )
            replicate_summaries.append(
                {
                    "scenario": scenario.name,
                    "replicate": replicate,
                    "seed": seed,
                    "design": scenario.design,
                    "native_frozen_elapsed_seconds": frozen_elapsed,
                    "native_selected_elapsed_seconds": (
                        None
                        if not np.isfinite(selected_elapsed)
                        else float(selected_elapsed)
                    ),
                    "native_bandwidth_selection_status": selected_status,
                    "native_score_uncertainty_available": uncertainty_available,
                    "native_score_failure_rate": float(
                        np.mean(
                            ~np.all(
                                np.isfinite(
                                    np.asarray(frozen_fit.scores, dtype=float)
                                ),
                                axis=1,
                            )
                        )
                    ),
                }
            )

    pd.DataFrame(manifest_rows).to_csv(
        output_dir / "replication_manifest.csv",
        index=False,
    )
    manifest = {
        "schema_version": 1,
        "programme": "post-1.1-bayesian-fpca-b2-b3",
        "b1_evidence_immutable": True,
        "replicates_per_scenario": replicates,
        "predeclared_seed_base": BASE_SEED,
        "scenario_count": len(SCENARIOS),
        "eyetrajectoriespy_version": importlib.metadata.version(
            "eyetrajectoriespy"
        ),
        "external_comparator": "hruffieux/bayesFPCA",
        "external_comparator_version": "0.1.0",
        "external_comparator_commit": BAYESFPCA_COMMIT,
        "external_comparator_license": "GPL-3.0-or-later",
        "bayesfpca_k_sensitivity": list(K_SENSITIVITY),
        "bayesfpca_primary_k": 7,
        "native_secondary_tuning": {
            "method": "existing_audited_training_fold_predictive_likelihood",
            "mean_bandwidth_multipliers": [0.75, 1.00, 1.25],
            "covariance_bandwidth_multipliers": [0.75, 1.00, 1.25],
            "fairness_replicates": FAIRNESS_REPLICATES,
            "fairness_scenarios": sorted(FAIRNESS_SCENARIOS),
            "folds": 3,
            "truth_used_for_tuning": False,
            "available_for_async_planar": False,
        },
        "informative_observation_scope": (
            "simulation-only sensitivity; no MAR/MNAR classification or correction claim"
        ),
        "uncertainty_scope": (
            "native fitted conditional score covariance exported where supported; "
            "full population-estimation uncertainty is not claimed"
        ),
        "external_runtime_backend": False,
        "source_code_ported": False,
        "equivalence_claim": False,
        "architecture_winner_selected": False,
        "automatic_promotion_decision": False,
        "b4_decision_recorded": False,
        "replicates": replicate_summaries,
    }
    (output_dir / "replication_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--replicates",
        type=int,
        default=DEFAULT_REPLICATES,
    )
    args = parser.parse_args()
    payload = generate(args.output_dir, replicates=args.replicates)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
