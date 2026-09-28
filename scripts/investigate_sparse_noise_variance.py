"""Diagnose diagonal-difference noise-variance recovery for sparse FPCA/PACE.

This is an investigation workflow, not an estimator modification and not an
automatic tuning procedure. It holds latent truth fixed where possible and
varies declared smoothing/support or data-regime factors one at a time.

The diagnostic decomposes
    estimated noise = smoothed raw diagonal - smoothed latent diagonal
against exact generating truth so that raw-diagonal and covariance-diagonal
bias can be separated.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from eyetrajectoriespy._sparse_native import (
    SparseNativeError,
    estimate_noise_variance_diagonal_difference,
    local_linear_covariance_surface,
    local_linear_smooth_1d,
    raw_offdiagonal_covariance_pairs,
    rotated_local_quadratic_covariance_diagonal,
)
from eyetrajectoriespy._sparse_truth import simulate_sparse_functional_truth
from eyetrajectoriespy.fpca import functional_trapezoid_weights


BASELINE = {
    "n_curves": 120,
    "samples_per_curve": (10, 14),
    "noise_sd": 0.10,
    "mean_bandwidth": 0.22,
    "covariance_bandwidth": 0.30,
    "noise_bandwidth": 0.24,
    "noise_support": (0.20, 0.80),
}

REGIMES = (
    {"name": "baseline"},
    {"name": "support_full", "noise_support": (0.00, 1.00)},
    {"name": "support_10_90", "noise_support": (0.10, 0.90)},
    {"name": "support_25_75", "noise_support": (0.25, 0.75)},
    {"name": "mean_bw_016", "mean_bandwidth": 0.16},
    {"name": "mean_bw_030", "mean_bandwidth": 0.30},
    {"name": "cov_bw_022", "covariance_bandwidth": 0.22},
    {"name": "cov_bw_038", "covariance_bandwidth": 0.38},
    {"name": "noise_bw_016", "noise_bandwidth": 0.16},
    {"name": "noise_bw_032", "noise_bandwidth": 0.32},
    {"name": "higher_n", "n_curves": 240},
    {"name": "more_samples", "samples_per_curve": (14, 18)},
    {"name": "lower_noise", "noise_sd": 0.05},
    {"name": "higher_noise", "noise_sd": 0.20},
    {
        "name": "favorable_combination",
        "n_curves": 240,
        "samples_per_curve": (14, 18),
        "noise_sd": 0.10,
        "mean_bandwidth": 0.18,
        "covariance_bandwidth": 0.24,
        "noise_bandwidth": 0.18,
        "noise_support": (0.20, 0.80),
    },
)


def _spec(regime):
    spec = dict(BASELINE)
    spec.update(regime)
    return spec


def _weighted_average(grid, values, support):
    mask = (grid >= support[0]) & (grid <= support[1])
    support_grid = grid[mask]
    weights = functional_trapezoid_weights(support_grid)
    return float(np.sum(weights * np.asarray(values, dtype=float)[mask]) / np.sum(weights))


def _truth_covariance_diagonal(truth, grid):
    diagonal = np.zeros_like(grid, dtype=float)
    for eigenvalue, eigenfunction in zip(truth.eigenvalues, truth.eigenfunctions, strict=True):
        values = np.asarray(eigenfunction(grid), dtype=float)
        diagonal += float(eigenvalue) * values**2
    return diagonal


def _replicate(spec, seed):
    times, values, truth = simulate_sparse_functional_truth(
        n_curves=spec["n_curves"],
        samples_per_curve=spec["samples_per_curve"],
        noise_sd=spec["noise_sd"],
        eigenvalues=(1.0, 0.35),
        observation_design="uniform",
        random_state=seed,
    )
    grid = np.linspace(0.0, 1.0, 41)
    pooled_time = np.concatenate(times)
    pooled_values = np.concatenate(values)

    mean_fit = local_linear_smooth_1d(
        pooled_time,
        pooled_values,
        grid,
        bandwidth=spec["mean_bandwidth"],
        min_local_points=3,
    )
    residuals = []
    for time, observed in zip(times, values, strict=True):
        mean_native = local_linear_smooth_1d(
            pooled_time,
            pooled_values,
            time,
            bandwidth=spec["mean_bandwidth"],
            min_local_points=3,
        ).values
        residuals.append(np.asarray(observed, dtype=float) - mean_native)

    pairs = raw_offdiagonal_covariance_pairs(times, tuple(residuals), include_mirror=True)
    covariance_fit = local_linear_covariance_surface(
        pairs,
        grid,
        bandwidth=spec["covariance_bandwidth"],
        min_local_pairs=6,
    )
    generic_noise = estimate_noise_variance_diagonal_difference(
        times,
        tuple(residuals),
        grid,
        covariance_fit.values,
        bandwidth=spec["noise_bandwidth"],
        noise_support=spec["noise_support"],
        min_local_points=3,
    )
    rotated_diagonal = rotated_local_quadratic_covariance_diagonal(
        pairs,
        grid,
        bandwidth=spec["covariance_bandwidth"],
        min_local_pairs=6,
    )
    noise = estimate_noise_variance_diagonal_difference(
        times,
        tuple(residuals),
        grid,
        covariance_fit.values,
        latent_diagonal=rotated_diagonal.values,
        bandwidth=spec["noise_bandwidth"],
        noise_support=spec["noise_support"],
        min_local_points=3,
    )

    truth_diagonal = _truth_covariance_diagonal(truth, grid)
    support = spec["noise_support"]
    true_noise = float(truth.noise_sd**2)
    raw_average = _weighted_average(grid, noise.raw_diagonal, support)
    covariance_average = _weighted_average(grid, noise.latent_diagonal, support)
    truth_covariance_average = _weighted_average(grid, truth_diagonal, support)
    expected_raw_average = truth_covariance_average + true_noise

    raw_bias = raw_average - expected_raw_average
    covariance_bias = covariance_average - truth_covariance_average
    estimate_error = float(noise.variance - true_noise)
    relative_error = abs(estimate_error) / true_noise if true_noise > 0 else np.nan
    estimate_to_truth_ratio = float(noise.variance / true_noise) if true_noise > 0 else np.nan
    oracle_noise_from_raw = raw_average - truth_covariance_average

    return {
        "seed": int(seed),
        "status": noise.status_code,
        "true_noise_variance": true_noise,
        "estimated_noise_variance": float(noise.variance),
        "generic_surface_noise_variance": float(generic_noise.variance),
        "generic_surface_relative_error": float(
            abs(generic_noise.variance - true_noise) / true_noise
        ),
        "estimate_to_truth_ratio": estimate_to_truth_ratio,
        "noise_variance_relative_error": float(relative_error),
        "raw_diagonal_support_average": raw_average,
        "estimated_latent_diagonal_support_average": covariance_average,
        "true_latent_diagonal_support_average": truth_covariance_average,
        "expected_raw_diagonal_support_average": expected_raw_average,
        "oracle_noise_from_raw_diagonal": oracle_noise_from_raw,
        "raw_diagonal_bias": raw_bias,
        "covariance_diagonal_bias": covariance_bias,
        "estimate_error": estimate_error,
        "bias_identity_residual": float(estimate_error - (raw_bias - covariance_bias)),
        "minimum_mean_support": int(np.min(mean_fit.support_counts)),
        "minimum_covariance_support": int(np.min(covariance_fit.support_counts)),
        "minimum_rotated_diagonal_support": int(
            np.min(rotated_diagonal.support_counts)
        ),
        "minimum_noise_support": int(
            np.min(
                local_linear_smooth_1d(
                    pooled_time,
                    np.concatenate([r**2 for r in residuals]),
                    grid,
                    bandwidth=spec["noise_bandwidth"],
                    min_local_points=3,
                ).support_counts
            )
        ),
        "covariance_pair_count": int(pairs.n_pairs),
    }


def _aggregate(name, spec, rows):
    evaluated = [
        row for row in rows
        if "estimated_noise_variance" in row
    ]
    positive = [row for row in evaluated if row["status"] == "ok"]
    if not evaluated:
        return {
            "regime": name,
            "n_replicates": len(rows),
            "n_evaluated": 0,
            "n_positive": 0,
            "positive_rate": 0.0,
            "true_noise_variance": float(spec["noise_sd"] ** 2),
        }

    def values(key):
        return np.asarray([row[key] for row in evaluated], dtype=float)

    return {
        "regime": name,
        "n_replicates": len(rows),
        "n_evaluated": len(evaluated),
        "n_positive": len(positive),
        "positive_rate": len(positive) / len(evaluated),
        "true_noise_variance": float(spec["noise_sd"] ** 2),
        "estimated_noise_median": float(np.median(values("estimated_noise_variance"))),
        "generic_surface_noise_median": float(
            np.median(values("generic_surface_noise_variance"))
        ),
        "generic_surface_relative_error_median": float(
            np.median(values("generic_surface_relative_error"))
        ),
        "estimated_noise_min": float(np.min(values("estimated_noise_variance"))),
        "estimated_noise_max": float(np.max(values("estimated_noise_variance"))),
        "relative_error_median": float(np.median(values("noise_variance_relative_error"))),
        "relative_error_max": float(np.max(values("noise_variance_relative_error"))),
        "estimate_to_truth_ratio_median": float(np.median(values("estimate_to_truth_ratio"))),
        "raw_diagonal_bias_median": float(np.median(values("raw_diagonal_bias"))),
        "covariance_diagonal_bias_median": float(np.median(values("covariance_diagonal_bias"))),
        "oracle_noise_from_raw_median": float(np.median(values("oracle_noise_from_raw_diagonal"))),
        "minimum_mean_support": int(np.min(values("minimum_mean_support"))),
        "minimum_covariance_support": int(np.min(values("minimum_covariance_support"))),
        "minimum_noise_support": int(np.min(values("minimum_noise_support"))),
        "minimum_rotated_diagonal_support": int(
            np.min(values("minimum_rotated_diagonal_support"))
        ),
        "mean_bandwidth": float(spec["mean_bandwidth"]),
        "covariance_bandwidth": float(spec["covariance_bandwidth"]),
        "noise_bandwidth": float(spec["noise_bandwidth"]),
        "noise_support": list(spec["noise_support"]),
        "n_curves": int(spec["n_curves"]),
        "samples_per_curve": list(spec["samples_per_curve"]),
        "noise_sd": float(spec["noise_sd"]),
    }


def _print_table(summaries):
    columns = (
        "regime",
        "n_positive",
        "positive_rate",
        "true_noise_variance",
        "estimated_noise_median",
        "generic_surface_noise_median",
        "generic_surface_relative_error_median",
        "relative_error_median",
        "relative_error_max",
        "estimate_to_truth_ratio_median",
        "raw_diagonal_bias_median",
        "covariance_diagonal_bias_median",
        "mean_bandwidth",
        "covariance_bandwidth",
        "noise_bandwidth",
        "noise_support",
        "n_curves",
        "samples_per_curve",
    )
    print("\nDIAGNOSTIC_SUMMARY_TABLE")
    print("\t".join(columns))
    for summary in summaries:
        print(
            "\t".join(
                json.dumps(summary.get(column), sort_keys=True)
                for column in columns
            )
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--replicates", type=int, default=5)
    parser.add_argument("--seed-start", type=int, default=2026900)
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("sparse-noise-variance-investigation.json"),
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("sparse-noise-variance-investigation.csv"),
    )
    args = parser.parse_args()
    if args.replicates < 1:
        raise ValueError("replicates must be positive")

    payloads = []
    summaries = []
    for regime in REGIMES:
        spec = _spec(regime)
        rows = []
        for replicate in range(args.replicates):
            seed = args.seed_start + replicate
            try:
                row = _replicate(spec, seed)
            except SparseNativeError as exc:
                row = {
                    "seed": int(seed),
                    "status": "failed_closed",
                    "failure_code": exc.code,
                    "failure_details": exc.details,
                }
            rows.append(row)
        summary = _aggregate(regime["name"], spec, rows)
        payloads.append(
            {
                "regime": regime["name"],
                "specification": spec,
                "summary": summary,
                "replicates": rows,
            }
        )
        summaries.append(summary)

    payload = {
        "schema_version": 1,
        "kind": "sparse diagonal-difference noise-variance investigation",
        "estimator_modified": False,
        "automatic_tuning": False,
        "baseline_seed_reuse_across_regimes": True,
        "replicates_per_regime": args.replicates,
        "candidate_latent_diagonal_method": (
            "45-degree rotated local linear along diagonal + "
            "local quadratic perpendicular to diagonal"
        ),
        "candidate_latent_diagonal_bandwidth_source": "covariance_bandwidth",
        "identity": (
            "noise estimation error = raw-diagonal smoothing bias "
            "- covariance-diagonal smoothing bias"
        ),
        "regimes": payloads,
    }
    args.output_json.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    fieldnames = sorted({key for summary in summaries for key in summary})
    with args.output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summaries)

    _print_table(summaries)


if __name__ == "__main__":
    main()
