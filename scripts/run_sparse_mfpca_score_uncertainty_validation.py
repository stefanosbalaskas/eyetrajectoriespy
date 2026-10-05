#!/usr/bin/env python
"""Known-population validation for sparse joint-PACE score uncertainty.

The runner supplies the true bivariate Gaussian population mean, covariance
operator, eigensystem, and measurement-error covariance to the native joint
PACE scorer. It therefore validates the conditional score-uncertainty formula
itself rather than claiming coverage after sparse population estimation,
bandwidth selection, PSD repair, or measurement-error estimation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

from eyetrajectoriespy import (
    FunctionalSimulationScenario,
    functional_trapezoid_weights,
    simulate_functional_scenario,
)
from eyetrajectoriespy._sparse_multivariate import (
    PlanarCovarianceBlocks,
    joint_pace_scores,
)
from eyetrajectoriespy.sparse_multivariate_score_uncertainty import (
    sparse_mfpca_score_uncertainty,
)
from eyetrajectoriespy.types import SparseMFPCAResult


SCENARIOS = (
    (
        "diagonal_sparse",
        (5, 7),
        np.asarray([[0.0025, 0.0], [0.0, 0.0049]], dtype=float),
    ),
    (
        "diagonal_dense",
        (14, 18),
        np.asarray([[0.0025, 0.0], [0.0, 0.0049]], dtype=float),
    ),
    (
        "correlated_sparse",
        (5, 7),
        np.asarray([[0.0025, 0.0012], [0.0012, 0.0049]], dtype=float),
    ),
    (
        "correlated_dense",
        (14, 18),
        np.asarray([[0.0025, 0.0012], [0.0012, 0.0049]], dtype=float),
    ),
)


def _mean(time: np.ndarray) -> np.ndarray:
    time = np.asarray(time, dtype=float)
    return np.column_stack(
        [
            0.45 + 0.04 * np.sin(np.pi * time),
            0.55 + 0.03 * np.cos(np.pi * time),
        ]
    )


def _u(time: np.ndarray) -> np.ndarray:
    time = np.asarray(time, dtype=float)
    return np.sqrt(2.0) * np.sin(np.pi * time)


def _v(time: np.ndarray) -> np.ndarray:
    time = np.asarray(time, dtype=float)
    return np.sqrt(2.0) * np.sin(2.0 * np.pi * time)


def _plus_mode(time: np.ndarray) -> np.ndarray:
    values = _u(time) / np.sqrt(2.0)
    return np.column_stack([values, values])


def _minus_mode(time: np.ndarray) -> np.ndarray:
    values = _v(time) / np.sqrt(2.0)
    return np.column_stack([values, -values])


EIGENVALUES = np.asarray([1.0, 0.40], dtype=float)
EIGENFUNCTIONS: tuple[Callable[[np.ndarray], np.ndarray], ...] = (
    _plus_mode,
    _minus_mode,
)


def _scenario(
    *,
    name: str,
    sample_counts: tuple[int, int],
    noise_covariance: np.ndarray,
    n_curves: int,
    seed: int,
) -> FunctionalSimulationScenario:
    return FunctionalSimulationScenario(
        name=name,
        truth_grid=np.linspace(0.0, 1.0, 81),
        eigenvalues=tuple(float(value) for value in EIGENVALUES),
        n_participants=int(n_curves),
        dimension_names=("x", "y"),
        coordinate_system="normalized",
        time_unit="normalized",
        observation_design="irregular",
        samples_per_curve=sample_counts,
        irregular_time_design="uniform",
        measurement_noise_sd=0.0,
        measurement_noise_covariance=np.asarray(
            noise_covariance,
            dtype=float,
        ),
        replicates=1,
        seed_start=int(seed),
        labels={
            "qualification": "conditional_sparse_joint_pace_score_uncertainty",
            "population_source": "known_simulation_truth",
        },
    )


def _truth_blocks(functions: np.ndarray) -> PlanarCovarianceBlocks:
    x = functions[:, :, 0]
    y = functions[:, :, 1]
    cxx = np.einsum("k,ks,kt->st", EIGENVALUES, x, x, optimize=True)
    cxy = np.einsum("k,ks,kt->st", EIGENVALUES, x, y, optimize=True)
    cyy = np.einsum("k,ks,kt->st", EIGENVALUES, y, y, optimize=True)
    return PlanarCovarianceBlocks(
        cxx=cxx,
        cxy=cxy,
        cyx=cxy.T,
        cyy=cyy,
    )


def _oracle_fit(simulation, *, noise_covariance: np.ndarray) -> SparseMFPCAResult:
    observations = simulation.observations
    pooled_start = min(float(time[0]) for time in observations.time)
    pooled_end = max(float(time[-1]) for time in observations.time)
    grid = np.linspace(pooled_start, pooled_end, 301)
    functions_public = np.stack(
        [function(grid) for function in EIGENFUNCTIONS],
        axis=0,
    )
    functions_private = np.transpose(functions_public, (0, 2, 1))
    mean_public = _mean(grid)
    blocks = _truth_blocks(functions_public)
    x_index = observations.dimension_names.index("x")
    y_index = observations.dimension_names.index("y")
    planar_values = tuple(
        np.asarray(values[:, [x_index, y_index]], dtype=float)
        for values in observations.values
    )
    scored = joint_pace_scores(
        observations.curve_ids,
        observations.time,
        planar_values,
        evaluation_grid=grid,
        fitted_mean=mean_public.T,
        covariance_blocks=blocks,
        eigenvalues=EIGENVALUES,
        eigenfunctions=functions_private,
        measurement_error_covariance=np.asarray(
            noise_covariance,
            dtype=float,
        ),
        n_components=2,
        score_ridge=0.0,
        condition_limit=1e12,
        min_score_time_points=2,
        failure_action="error",
    )
    sample_counts = tuple(int(time.size) for time in observations.time)
    error_mode = (
        "diagonal"
        if np.allclose(
            noise_covariance,
            np.diag(np.diag(noise_covariance)),
            rtol=0.0,
            atol=1e-15,
        )
        else "fixed_matrix"
    )
    covariance_support = {
        "cxx": np.full((grid.size, grid.size), len(sample_counts), dtype=int),
        "cxy": np.full((grid.size, grid.size), len(sample_counts), dtype=int),
        "cyy": np.full((grid.size, grid.size), len(sample_counts), dtype=int),
    }
    return SparseMFPCAResult(
        scores=scored.scores.copy(),
        eigenvalues=EIGENVALUES.copy(),
        eigenfunctions=functions_public.copy(),
        mean=mean_public.copy(),
        evaluation_grid=grid.copy(),
        dimensions=("x", "y"),
        curve_ids=tuple(observations.curve_ids),
        metadata=observations.metadata.reset_index(drop=True).copy(),
        coordinate_system=observations.coordinate_system,
        time_unit=observations.time_unit,
        n_components=2,
        quadrature_weights=functional_trapezoid_weights(grid),
        smoothed_cxx=blocks.cxx.copy(),
        smoothed_cxy=blocks.cxy.copy(),
        smoothed_cyx=blocks.cyx.copy(),
        smoothed_cyy=blocks.cyy.copy(),
        covariance_cxx=blocks.cxx.copy(),
        covariance_cxy=blocks.cxy.copy(),
        covariance_cyx=blocks.cyx.copy(),
        covariance_cyy=blocks.cyy.copy(),
        measurement_error_covariance=np.asarray(
            noise_covariance,
            dtype=float,
        ).copy(),
        score_diagnostics=scored.diagnostics.copy(),
        mean_support_counts=np.full((grid.size, 2), len(sample_counts), dtype=int),
        covariance_support_counts=covariance_support,
        covariance_pair_counts={"cxx": 0, "cxy": 0, "cyy": 0},
        covariance_diagnostics={
            "applied_action": "oracle_population",
            "relative_operator_correction_frobenius_norm": 0.0,
        },
        fit_method="direct_sparse_block_covariance",
        score_method="joint_PACE",
        provenance={
            "sparse_mfpca": {
                "backend": "native",
                "fit_method": "direct_sparse_block_covariance",
                "score_method": "joint_PACE",
                "dimensions": ["x", "y"],
                "n_components": 2,
                "analysis_support": [pooled_start, pooled_end],
                "analysis_support_action": "error",
                "analysis_sample_counts": list(sample_counts),
                "operator_storage_order": "channel_major",
                "score_observation_order": "time_major_interleaved_xy",
                "ordering_permutation_applied": True,
                "score_covariance_source": (
                    "full_fitted_joint_covariance_plus_measurement_error"
                ),
                "rank_k_covariance_used_for_scoring": False,
                "measurement_error_mode": error_mode,
                "measurement_error_covariance": np.asarray(
                    noise_covariance,
                    dtype=float,
                ).copy(),
                "score_ridge": 0.0,
                "score_condition_limit": 1e12,
                "min_score_time_points": 2,
                "score_failure_action": "error",
                "raw_sparse_trajectory_interpolation_performed": False,
                "population_function_evaluation_at_native_times": True,
                "automatic_bandwidth_selection_performed": False,
                "population_source": "known_simulation_truth",
            }
        },
    )


def _deterministic_replay(
    scenario: FunctionalSimulationScenario,
) -> bool:
    first = simulate_functional_scenario(
        scenario,
        mean=_mean,
        eigenfunctions=EIGENFUNCTIONS,
    )
    second = simulate_functional_scenario(
        scenario,
        mean=_mean,
        eigenfunctions=EIGENFUNCTIONS,
    )
    if not np.array_equal(first.truth.scores, second.truth.scores):
        return False
    if len(first.observations.time) != len(second.observations.time):
        return False
    for left, right in zip(
        first.observations.time,
        second.observations.time,
        strict=True,
    ):
        if not np.array_equal(left, right):
            return False
    for left, right in zip(
        first.observations.values,
        second.observations.values,
        strict=True,
    ):
        if not np.array_equal(left, right):
            return False
    return True


def _run_scenario(
    name: str,
    sample_counts: tuple[int, int],
    noise_covariance: np.ndarray,
    *,
    n_curves: int,
    seed: int,
) -> dict[str, object]:
    scenario = _scenario(
        name=name,
        sample_counts=sample_counts,
        noise_covariance=noise_covariance,
        n_curves=n_curves,
        seed=seed,
    )
    simulation = simulate_functional_scenario(
        scenario,
        mean=_mean,
        eigenfunctions=EIGENFUNCTIONS,
    )
    fit = _oracle_fit(simulation, noise_covariance=noise_covariance)
    uncertainty = sparse_mfpca_score_uncertainty(
        fit,
        simulation.observations,
    )

    truth_scores = np.asarray(simulation.truth.scores[:, :2], dtype=float)
    error = np.asarray(fit.scores, dtype=float) - truth_scores
    variance = np.diagonal(uncertainty.covariance, axis1=1, axis2=2)
    standardized = error / uncertainty.standard_errors
    posterior_minimum_eigenvalues = np.linalg.eigvalsh(
        uncertainty.covariance
    )[:, 0]
    symmetry_errors = np.max(
        np.abs(
            uncertainty.covariance
            - np.transpose(uncertainty.covariance, (0, 2, 1))
        ),
        axis=(1, 2),
    )

    components: list[dict[str, object]] = []
    for component in range(2):
        component_error = error[:, component]
        component_variance = variance[:, component]
        component_standardized = standardized[:, component]
        components.append(
            {
                "component": component + 1,
                "mse": float(np.mean(component_error**2)),
                "mean_conditional_variance": float(
                    np.mean(component_variance)
                ),
                "mse_to_variance_ratio": float(
                    np.mean(component_error**2)
                    / np.mean(component_variance)
                ),
                "standardized_error_mean": float(
                    np.mean(component_standardized)
                ),
                "standardized_error_sd": float(
                    np.std(component_standardized, ddof=1)
                ),
                "coverage_68": float(
                    np.mean(np.abs(component_standardized) <= 1.0)
                ),
                "coverage_95": float(
                    np.mean(
                        np.abs(component_standardized)
                        <= 1.959963984540054
                    )
                ),
            }
        )

    diagnostics = uncertainty.diagnostics
    return {
        "scenario": name,
        "n_curves": int(n_curves),
        "samples_per_curve": list(sample_counts),
        "measurement_error_covariance": np.asarray(
            noise_covariance,
            dtype=float,
        ).tolist(),
        "measurement_error_mode": fit.provenance["sparse_mfpca"][
            "measurement_error_mode"
        ],
        "failed_system_proportion": float(
            np.mean(diagnostics["status_code"] != "ok")
        ),
        "mean_total_conditional_variance": float(
            np.mean(np.sum(variance, axis=1))
        ),
        "minimum_posterior_eigenvalue": float(
            np.min(posterior_minimum_eigenvalues)
        ),
        "maximum_symmetry_error": float(np.max(symmetry_errors)),
        "mean_absolute_posterior_cross_covariance": float(
            np.mean(np.abs(uncertainty.covariance[:, 0, 1]))
        ),
        "rank_k_covariance_used_for_uncertainty": bool(
            uncertainty.provenance["rank_k_covariance_used_for_uncertainty"]
        ),
        "population_estimation_uncertainty_included": bool(
            uncertainty.provenance["population_estimation_uncertainty_included"]
        ),
        "bandwidth_uncertainty_included": bool(
            uncertainty.provenance["bandwidth_uncertainty_included"]
        ),
        "deterministic_replay_passed": _deterministic_replay(scenario),
        "components": components,
    }


def _validate(records: list[dict[str, object]]) -> list[str]:
    failures: list[str] = []
    by_name = {str(record["scenario"]): record for record in records}

    for record in records:
        scenario = str(record["scenario"])
        if float(record["failed_system_proportion"]) != 0.0:
            failures.append(f"{scenario}: conditional systems unexpectedly failed")
        if float(record["minimum_posterior_eigenvalue"]) < -1e-10:
            failures.append(
                f"{scenario}: posterior covariance not PSD within tolerance"
            )
        if float(record["maximum_symmetry_error"]) > 1e-12:
            failures.append(
                f"{scenario}: posterior covariance symmetry error too large"
            )
        if bool(record["rank_k_covariance_used_for_uncertainty"]):
            failures.append(f"{scenario}: rank-K covariance used for uncertainty")
        if bool(record["population_estimation_uncertainty_included"]):
            failures.append(
                f"{scenario}: population-estimation uncertainty mislabelled included"
            )
        if bool(record["bandwidth_uncertainty_included"]):
            failures.append(f"{scenario}: bandwidth uncertainty mislabelled included")
        if not bool(record["deterministic_replay_passed"]):
            failures.append(f"{scenario}: deterministic replay failed")

        components = record["components"]
        assert isinstance(components, list)
        for component in components:
            assert isinstance(component, dict)
            label = f"{scenario}:pc{component['component']}"
            ratio = float(component["mse_to_variance_ratio"])
            if not 0.70 <= ratio <= 1.30:
                failures.append(f"{label}: mse/variance ratio={ratio:.3f}")
            coverage_68 = float(component["coverage_68"])
            if not 0.59 <= coverage_68 <= 0.77:
                failures.append(
                    f"{label}: 68% conditional coverage={coverage_68:.3f}"
                )
            coverage_95 = float(component["coverage_95"])
            if not 0.90 <= coverage_95 <= 0.99:
                failures.append(
                    f"{label}: 95% conditional coverage={coverage_95:.3f}"
                )
            standardized_mean = float(component["standardized_error_mean"])
            if abs(standardized_mean) > 0.16:
                failures.append(
                    f"{label}: standardized mean={standardized_mean:.3f}"
                )
            standardized_sd = float(component["standardized_error_sd"])
            if not 0.78 <= standardized_sd <= 1.22:
                failures.append(
                    f"{label}: standardized sd={standardized_sd:.3f}"
                )

    for mode in ("diagonal", "correlated"):
        sparse = by_name[f"{mode}_sparse"]
        dense = by_name[f"{mode}_dense"]
        if not (
            float(sparse["mean_total_conditional_variance"])
            > float(dense["mean_total_conditional_variance"])
        ):
            failures.append(
                f"{mode}: denser native observation did not reduce uncertainty"
            )

    if by_name["diagonal_sparse"]["measurement_error_mode"] != "diagonal":
        failures.append("diagonal scenario did not retain diagonal error mode")
    if by_name["correlated_sparse"]["measurement_error_mode"] != "fixed_matrix":
        failures.append("correlated scenario did not retain fixed-matrix error mode")
    return failures


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-curves", type=int, default=500)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.n_curves < 100:
        raise ValueError("--n-curves must be at least 100 for calibration validation")

    records = [
        _run_scenario(
            name,
            sample_counts,
            noise_covariance,
            n_curves=args.n_curves,
            seed=20261005 + index * 1000,
        )
        for index, (name, sample_counts, noise_covariance) in enumerate(
            SCENARIOS
        )
    ]
    failures = _validate(records)
    payload = {
        "validation_target": "conditional_sparse_joint_pace_score_uncertainty",
        "population_objects": "known_truth_oracle",
        "population_estimation_uncertainty_included": False,
        "bandwidth_uncertainty_included": False,
        "measurement_error_estimation_uncertainty_included": False,
        "coverage_interpretation": (
            "conditional on known joint population objects and declared "
            "measurement-error covariance; not full sparse-MFPCA coverage"
        ),
        "n_curves_per_scenario": int(args.n_curves),
        "scenarios": records,
        "validation_failures": failures,
        "validation_passed": not failures,
    }
    args.output.write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    if failures:
        raise SystemExit("; ".join(failures))


if __name__ == "__main__":
    main()
