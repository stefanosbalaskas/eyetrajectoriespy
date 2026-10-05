"""Deterministic known-truth qualification for asynchronous sparse planar MFPCA."""

from __future__ import annotations

import argparse
import json
from itertools import permutations
from pathlib import Path

import numpy as np
import pandas as pd

from eyetrajectoriespy import functional_trapezoid_weights
from eyetrajectoriespy._sparse_native import SparseNativeError
from eyetrajectoriespy.sparse_multivariate import fit_sparse_mfpca
from eyetrajectoriespy.sparse_multivariate_async import fit_sparse_mfpca_async
from eyetrajectoriespy.types import IrregularTrajectorySet


GRID = np.linspace(0.0, 1.0, 31)
EIGENVALUES = np.array([1.0, 0.45], dtype=float)
GUARDS = {
    "paired": {
        "cxx_relrmse_max": 0.65,
        "cxy_relrmse_max": 0.75,
        "cyy_relrmse_max": 0.65,
        "minimum_subspace_principal_cosine_min": 0.80,
        "median_matched_score_correlation_min": 0.75,
        "score_failure_rate_max": 0.0,
        "psd_relative_operator_correction_max": 0.50,
    },
    "staggered": {
        "cxx_relrmse_max": 0.80,
        "cxy_relrmse_max": 0.95,
        "cyy_relrmse_max": 0.80,
        "minimum_subspace_principal_cosine_min": 0.70,
        "median_matched_score_correlation_min": 0.60,
        "score_failure_rate_max": 0.0,
        "psd_relative_operator_correction_max": 0.50,
    },
    "mixed": {
        "cxx_relrmse_max": 0.75,
        "cxy_relrmse_max": 0.85,
        "cyy_relrmse_max": 0.75,
        "minimum_subspace_principal_cosine_min": 0.75,
        "median_matched_score_correlation_min": 0.70,
        "score_failure_rate_max": 0.0,
        "psd_relative_operator_correction_max": 0.50,
    },
}
PAIRED_REDUCTION_TOLERANCE = 1e-8


def _mean(time: np.ndarray) -> np.ndarray:
    time = np.asarray(time, dtype=float)
    return np.column_stack(
        [
            0.45 + 0.06 * np.sin(np.pi * time),
            0.55 + 0.05 * np.cos(np.pi * time),
        ]
    )


def _eigenfunctions(time: np.ndarray) -> np.ndarray:
    time = np.asarray(time, dtype=float)
    temporal_1 = np.sqrt(2.0) * np.sin(np.pi * time)
    temporal_2 = np.sqrt(2.0) * np.sin(2.0 * np.pi * time)
    loading_1 = np.array([0.8, 0.6], dtype=float)
    loading_2 = np.array([0.6, -0.8], dtype=float)
    return np.stack(
        [
            temporal_1[:, None] * loading_1[None, :],
            temporal_2[:, None] * loading_2[None, :],
        ],
        axis=0,
    )


def _latent(time: np.ndarray, score: np.ndarray) -> np.ndarray:
    functions = _eigenfunctions(time)
    return _mean(time) + np.einsum("k,ktd->td", score, functions, optimize=True)


def _truth_covariances(grid: np.ndarray) -> dict[str, np.ndarray]:
    functions = _eigenfunctions(grid)
    return {
        "cxx": np.einsum(
            "k,ks,kt->st",
            EIGENVALUES,
            functions[:, :, 0],
            functions[:, :, 0],
            optimize=True,
        ),
        "cxy": np.einsum(
            "k,ks,kt->st",
            EIGENVALUES,
            functions[:, :, 0],
            functions[:, :, 1],
            optimize=True,
        ),
        "cyy": np.einsum(
            "k,ks,kt->st",
            EIGENVALUES,
            functions[:, :, 1],
            functions[:, :, 1],
            optimize=True,
        ),
    }


def _sample_times(rng: np.random.Generator, count: int) -> np.ndarray:
    interior = np.sort(rng.uniform(0.015, 0.985, size=count - 2))
    return np.concatenate([[0.0], interior, [1.0]])


def _observation_grids(
    rng: np.random.Generator,
    design: str,
) -> tuple[np.ndarray, np.ndarray]:
    if design == "paired":
        time = _sample_times(rng, int(rng.integers(16, 20)))
        return time, time.copy()
    if design == "staggered":
        return (
            _sample_times(rng, int(rng.integers(10, 14))),
            _sample_times(rng, int(rng.integers(10, 14))),
        )
    if design == "mixed":
        shared = _sample_times(rng, int(rng.integers(5, 8)))
        x_only = np.sort(rng.uniform(0.02, 0.98, size=int(rng.integers(5, 8))))
        y_only = np.sort(rng.uniform(0.02, 0.98, size=int(rng.integers(5, 8))))
        return (
            np.unique(np.concatenate([shared, x_only])),
            np.unique(np.concatenate([shared, y_only])),
        )
    raise ValueError(f"Unknown design {design!r}")


def _simulate(
    *,
    design: str,
    seed: int,
    n_curves: int,
    measurement_error_covariance: np.ndarray,
) -> tuple[IrregularTrajectorySet, np.ndarray, dict[str, int]]:
    rng = np.random.default_rng(seed)
    error = np.asarray(measurement_error_covariance, dtype=float)
    score_sd = np.sqrt(EIGENVALUES)
    scores = rng.normal(size=(n_curves, 2)) * score_sd[None, :]

    times: list[np.ndarray] = []
    values: list[np.ndarray] = []
    simultaneous_total = 0
    x_only_total = 0
    y_only_total = 0

    for index in range(n_curves):
        tx, ty = _observation_grids(rng, design)
        union = np.unique(np.concatenate([tx, ty]))
        observed = np.full((union.size, 2), np.nan, dtype=float)
        latent = _latent(union, scores[index])
        x_lookup = {float(value) for value in tx}
        y_lookup = {float(value) for value in ty}

        for row, time_value in enumerate(union):
            has_x = float(time_value) in x_lookup
            has_y = float(time_value) in y_lookup
            if has_x and has_y:
                noise = rng.multivariate_normal(np.zeros(2), error)
                observed[row] = latent[row] + noise
                simultaneous_total += 1
            elif has_x:
                observed[row, 0] = latent[row, 0] + rng.normal(
                    scale=float(np.sqrt(error[0, 0]))
                )
                x_only_total += 1
            elif has_y:
                observed[row, 1] = latent[row, 1] + rng.normal(
                    scale=float(np.sqrt(error[1, 1]))
                )
                y_only_total += 1
            else:
                raise RuntimeError("union construction invariant failed")

        times.append(union)
        values.append(observed)

    trajectories = IrregularTrajectorySet(
        time=tuple(times),
        values=tuple(values),
        curve_ids=tuple(f"{design}_{index:03d}" for index in range(n_curves)),
        dimension_names=("x", "y"),
        metadata=pd.DataFrame(
            {
                "participant": [f"P{index // 2:03d}" for index in range(n_curves)],
                "design": [design] * n_curves,
            }
        ),
        coordinate_system="normalized",
        time_unit="normalized",
        provenance={"source": "known_truth_async_sparse_mfpca", "design": design},
    )
    counts = {
        "simultaneous_observations": int(simultaneous_total),
        "x_only_observations": int(x_only_total),
        "y_only_observations": int(y_only_total),
    }
    return trajectories, scores, counts


def _fit_async(
    trajectories: IrregularTrajectorySet,
    error: np.ndarray,
):
    return fit_sparse_mfpca_async(
        trajectories,
        dimensions=("x", "y"),
        n_components=2,
        evaluation_grid=GRID,
        mean_bandwidth=0.20,
        covariance_bandwidth=0.28,
        measurement_error="fixed_matrix",
        measurement_error_covariance=error,
        same_time_tolerance=1e-12,
        psd_action="project",
        score_failure_action="retain_nan",
        covariance_min_local_pairs=8,
    )


def _fit_sync(
    trajectories: IrregularTrajectorySet,
    error: np.ndarray,
):
    return fit_sparse_mfpca(
        trajectories,
        dimensions=("x", "y"),
        n_components=2,
        evaluation_grid=GRID,
        mean_bandwidth=0.20,
        covariance_bandwidth=0.28,
        measurement_error="fixed_matrix",
        measurement_error_covariance=error,
        psd_action="project",
        score_failure_action="retain_nan",
        covariance_min_local_pairs=8,
    )


def _weighted_relrmse(
    estimated: np.ndarray,
    truth: np.ndarray,
    grid: np.ndarray,
) -> float:
    weights = functional_trapezoid_weights(grid)
    surface_weights = np.outer(weights, weights)
    numerator = float(np.sum(surface_weights * (estimated - truth) ** 2))
    denominator = float(np.sum(surface_weights * truth**2))
    return float(np.sqrt(numerator / denominator))


def _minimum_subspace_cosine(estimated: np.ndarray, grid: np.ndarray) -> float:
    truth = _eigenfunctions(grid)
    truth_flat = np.concatenate([truth[:, :, 0], truth[:, :, 1]], axis=1)
    estimated_flat = np.concatenate(
        [estimated[:, :, 0], estimated[:, :, 1]], axis=1
    )
    weights = functional_trapezoid_weights(grid)
    joint_sqrt_weights = np.sqrt(np.concatenate([weights, weights]))
    truth_weighted = truth_flat * joint_sqrt_weights[None, :]
    estimated_weighted = estimated_flat * joint_sqrt_weights[None, :]
    q_truth, _ = np.linalg.qr(truth_weighted.T)
    q_estimated, _ = np.linalg.qr(estimated_weighted.T)
    singular = np.linalg.svd(q_truth.T @ q_estimated, compute_uv=False)
    return float(np.min(singular))


def _matched_score_correlations(
    estimated: np.ndarray,
    truth: np.ndarray,
) -> tuple[list[float], tuple[int, ...]]:
    k = truth.shape[1]
    correlation = np.empty((k, k), dtype=float)
    for left in range(k):
        for right in range(k):
            correlation[left, right] = abs(
                float(np.corrcoef(truth[:, left], estimated[:, right])[0, 1])
            )
    best_perm: tuple[int, ...] | None = None
    best_value = -np.inf
    for perm in permutations(range(k)):
        value = float(sum(correlation[row, perm[row]] for row in range(k)))
        if value > best_value:
            best_value = value
            best_perm = tuple(int(item) for item in perm)
    assert best_perm is not None
    matched = [float(correlation[row, best_perm[row]]) for row in range(k)]
    return matched, best_perm


def _assess(
    design: str,
    trajectories: IrregularTrajectorySet,
    truth_scores: np.ndarray,
    observation_counts: dict[str, int],
    error: np.ndarray,
) -> tuple[dict[str, object], object]:
    result = _fit_async(trajectories, error)
    truth_covariance = _truth_covariances(GRID)
    score_ok = result.score_diagnostics["status_code"].astype(str).to_numpy() == "ok"
    matched, assignment = _matched_score_correlations(
        result.scores[score_ok],
        truth_scores[score_ok],
    )
    row: dict[str, object] = {
        "design": design,
        "n_curves": int(result.n_curves),
        **observation_counts,
        "cxx_relrmse": _weighted_relrmse(
            result.covariance_cxx, truth_covariance["cxx"], GRID
        ),
        "cxy_relrmse": _weighted_relrmse(
            result.covariance_cxy, truth_covariance["cxy"], GRID
        ),
        "cyy_relrmse": _weighted_relrmse(
            result.covariance_cyy, truth_covariance["cyy"], GRID
        ),
        "minimum_subspace_principal_cosine": _minimum_subspace_cosine(
            result.eigenfunctions, GRID
        ),
        "matched_score_correlations": matched,
        "median_matched_score_correlation": float(np.median(matched)),
        "score_assignment": list(assignment),
        "score_failure_rate": float(1.0 - np.mean(score_ok)),
        "psd_relative_operator_correction": float(
            result.covariance_diagnostics[
                "relative_operator_correction_frobenius_norm"
            ]
        ),
        "latent_cross_same_time_pairs_excluded": int(
            result.support_diagnostics["cross_same_time_pair_count_excluded"]
        ),
        "score_measurement_error_cross_links": int(
            result.score_diagnostics["measurement_error_cross_links"].sum()
        ),
        "raw_sparse_trajectory_interpolation_performed": bool(
            result.provenance["sparse_mfpca_async"][
                "raw_sparse_trajectory_interpolation_performed"
            ]
        ),
        "nearest_neighbour_synchronization_performed": bool(
            result.provenance["sparse_mfpca_async"][
                "nearest_neighbour_synchronization_performed"
            ]
        ),
        "time_binning_performed": bool(
            result.provenance["sparse_mfpca_async"]["time_binning_performed"]
        ),
        "rank_k_covariance_used_for_scoring": bool(
            result.provenance["sparse_mfpca_async"][
                "rank_k_covariance_used_for_scoring"
            ]
        ),
    }
    return row, result


def _guard_passed(row: dict[str, object], guards: dict[str, float]) -> bool:
    return bool(
        float(row["cxx_relrmse"]) <= guards["cxx_relrmse_max"]
        and float(row["cxy_relrmse"]) <= guards["cxy_relrmse_max"]
        and float(row["cyy_relrmse"]) <= guards["cyy_relrmse_max"]
        and float(row["minimum_subspace_principal_cosine"])
        >= guards["minimum_subspace_principal_cosine_min"]
        and float(row["median_matched_score_correlation"])
        >= guards["median_matched_score_correlation_min"]
        and float(row["score_failure_rate"]) <= guards["score_failure_rate_max"]
        and float(row["psd_relative_operator_correction"])
        <= guards["psd_relative_operator_correction_max"]
    )


def _paired_reduction(
    trajectories: IrregularTrajectorySet,
    error: np.ndarray,
    asynchronous,
) -> dict[str, float | bool]:
    synchronous = _fit_sync(trajectories, error)
    differences = {
        "mean_max_abs_difference": float(
            np.max(np.abs(asynchronous.mean - synchronous.mean))
        ),
        "cxx_max_abs_difference": float(
            np.max(np.abs(asynchronous.covariance_cxx - synchronous.covariance_cxx))
        ),
        "cxy_max_abs_difference": float(
            np.max(np.abs(asynchronous.covariance_cxy - synchronous.covariance_cxy))
        ),
        "cyy_max_abs_difference": float(
            np.max(np.abs(asynchronous.covariance_cyy - synchronous.covariance_cyy))
        ),
        "eigenvalue_max_abs_difference": float(
            np.max(np.abs(asynchronous.eigenvalues - synchronous.eigenvalues))
        ),
        "score_max_abs_difference": float(
            np.max(np.abs(asynchronous.scores - synchronous.scores))
        ),
    }
    passed = all(
        float(value) <= PAIRED_REDUCTION_TOLERANCE for value in differences.values()
    )
    return {
        **differences,
        "tolerance": float(PAIRED_REDUCTION_TOLERANCE),
        "passed": bool(passed),
    }


def _expected_failure(trajectories: IrregularTrajectorySet, error: np.ndarray) -> dict[str, object]:
    try:
        fit_sparse_mfpca_async(
            trajectories,
            n_components=1,
            evaluation_grid=GRID,
            mean_bandwidth=0.20,
            covariance_bandwidth=0.28,
            measurement_error="fixed_matrix",
            measurement_error_covariance=error,
            same_time_tolerance=2.0,
            psd_action="project",
            score_failure_action="retain_nan",
            covariance_min_local_pairs=8,
        )
    except SparseNativeError as exc:
        return {"failure_code": exc.code, "message": str(exc)}
    raise AssertionError("deliberately under-supported cross-channel fit unexpectedly succeeded")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    scenarios = {
        "paired": {
            "seed": 24601,
            "n_curves": 56,
            "error": np.array([[0.0064, 0.0015], [0.0015, 0.0081]]),
        },
        "staggered": {
            "seed": 24602,
            "n_curves": 64,
            "error": np.array([[0.0100, 0.0], [0.0, 0.0121]]),
        },
        "mixed": {
            "seed": 24603,
            "n_curves": 60,
            "error": np.array([[0.0081, 0.0018], [0.0018, 0.0100]]),
        },
    }

    rows: list[dict[str, object]] = []
    results: dict[str, object] = {}
    trajectories_by_design: dict[str, IrregularTrajectorySet] = {}
    errors: dict[str, np.ndarray] = {}
    for design, spec in scenarios.items():
        trajectories, truth_scores, counts = _simulate(
            design=design,
            seed=int(spec["seed"]),
            n_curves=int(spec["n_curves"]),
            measurement_error_covariance=np.asarray(spec["error"], dtype=float),
        )
        row, result = _assess(
            design,
            trajectories,
            truth_scores,
            counts,
            np.asarray(spec["error"], dtype=float),
        )
        row["guards"] = GUARDS[design]
        row["passed"] = _guard_passed(row, GUARDS[design])
        rows.append(row)
        results[design] = result
        trajectories_by_design[design] = trajectories
        errors[design] = np.asarray(spec["error"], dtype=float)

    paired_reduction = _paired_reduction(
        trajectories_by_design["paired"],
        errors["paired"],
        results["paired"],
    )

    replay = _fit_async(trajectories_by_design["staggered"], errors["staggered"])
    reference = results["staggered"]
    deterministic_replay_passed = bool(
        np.array_equal(replay.eigenvalues, reference.eigenvalues)
        and np.array_equal(replay.eigenfunctions, reference.eigenfunctions)
        and np.array_equal(replay.scores, reference.scores)
        and np.array_equal(replay.covariance_cxy, reference.covariance_cxy)
    )

    expected_failure = _expected_failure(
        trajectories_by_design["mixed"], errors["mixed"]
    )
    cross_semantics_passed = all(
        int(row["latent_cross_same_time_pairs_excluded"])
        == int(row["simultaneous_observations"])
        and int(row["score_measurement_error_cross_links"])
        == int(row["simultaneous_observations"])
        for row in rows
    )
    no_hidden_synchronization = all(
        row["raw_sparse_trajectory_interpolation_performed"] is False
        and row["nearest_neighbour_synchronization_performed"] is False
        and row["time_binning_performed"] is False
        and row["rank_k_covariance_used_for_scoring"] is False
        for row in rows
    )

    validation_passed = bool(
        all(bool(row["passed"]) for row in rows)
        and bool(paired_reduction["passed"])
        and deterministic_replay_passed
        and cross_semantics_passed
        and no_hidden_synchronization
        and expected_failure["failure_code"]
        == "insufficient_async_cross_covariance_pairs"
    )

    evidence = {
        "validation_passed": validation_passed,
        "method": "native_asynchronous_sparse_planar_mfpca_joint_pace",
        "scenarios": rows,
        "paired_reduction": paired_reduction,
        "deterministic_replay_passed": deterministic_replay_passed,
        "cross_semantics_passed": cross_semantics_passed,
        "no_hidden_synchronization": no_hidden_synchronization,
        "expected_cross_support_failure": expected_failure,
        "population_estimation_uncertainty_propagated": False,
        "automatic_bandwidth_selection_performed": False,
        "asynchronous_score_uncertainty_estimated": False,
        "multilevel_multivariate_model_fitted": False,
    }
    args.output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    if not validation_passed:
        raise SystemExit("asynchronous sparse MFPCA qualification failed")


if __name__ == "__main__":
    main()
