"""Deterministic stress validation for native sparse FPCA/PACE.

This is a recovery/failure-characterization workflow, not a comparative
benchmark and not an automatic tuning procedure.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from eyetrajectoriespy import IrregularTrajectorySet, fit_sparse_fpca
from eyetrajectoriespy._sparse_native import SparseNativeError
from eyetrajectoriespy._sparse_truth import simulate_sparse_functional_truth
from eyetrajectoriespy._sparse_validation import evaluate_sparse_truth_recovery


SCENARIOS = (
    {
        "name": "moderate_baseline",
        "n_curves": 36,
        "samples_per_curve": (6, 10),
        "noise_sd": 0.10,
        "eigenvalues": (1.0, 0.35),
        "observation_design": "uniform",
        "grid": (0.0, 1.0, 21),
        "mean_bandwidth": 0.24,
        "covariance_bandwidth": 0.32,
        "noise_method": "fixed",
        "required_successes": 3,
        "min_subspace_cosine": 0.70,
        "min_score_correlation": 0.45,
    },
    {
        "name": "very_sparse_2_4",
        "n_curves": 60,
        "samples_per_curve": (2, 4),
        "noise_sd": 0.10,
        "eigenvalues": (1.0, 0.35),
        "observation_design": "uniform",
        "grid": (0.0, 1.0, 19),
        "mean_bandwidth": 0.34,
        "covariance_bandwidth": 0.46,
        "noise_method": "fixed",
        "required_successes": 0,
    },
    {
        "name": "high_measurement_noise",
        "n_curves": 42,
        "samples_per_curve": (6, 10),
        "noise_sd": 0.30,
        "eigenvalues": (1.0, 0.35),
        "observation_design": "uniform",
        "grid": (0.0, 1.0, 21),
        "mean_bandwidth": 0.26,
        "covariance_bandwidth": 0.36,
        "noise_method": "fixed",
        "required_successes": 2,
        "min_subspace_cosine": 0.50,
    },
    {
        "name": "near_tied_eigenvalues",
        "n_curves": 48,
        "samples_per_curve": (7, 11),
        "noise_sd": 0.10,
        "eigenvalues": (1.0, 0.90),
        "observation_design": "uniform",
        "grid": (0.0, 1.0, 21),
        "mean_bandwidth": 0.24,
        "covariance_bandwidth": 0.34,
        "noise_method": "fixed",
        "required_successes": 2,
        "min_subspace_cosine": 0.65,
    },
    {
        "name": "center_clustered_times",
        "n_curves": 42,
        "samples_per_curve": (6, 10),
        "noise_sd": 0.10,
        "eigenvalues": (1.0, 0.35),
        "observation_design": "center_clustered",
        "grid": (0.0, 1.0, 21),
        "mean_bandwidth": 0.28,
        "covariance_bandwidth": 0.40,
        "noise_method": "fixed",
        "required_successes": 2,
        "min_subspace_cosine": 0.50,
    },
    {
        "name": "boundary_poor_interior_support",
        "n_curves": 42,
        "samples_per_curve": (8, 12),
        "noise_sd": 0.10,
        "eigenvalues": (1.0, 0.35),
        "observation_design": "boundary_poor",
        "grid": (0.10, 0.90, 21),
        "analysis_support_action": "restrict",
        "mean_bandwidth": 0.24,
        "covariance_bandwidth": 0.34,
        "noise_method": "fixed",
        "required_successes": 2,
        "min_subspace_cosine": 0.55,
    },
    {
        "name": "estimated_noise_interior_domain",
        "n_curves": 48,
        "samples_per_curve": (8, 12),
        "noise_sd": 0.15,
        "eigenvalues": (1.0, 0.35),
        "observation_design": "uniform",
        "grid": (0.0, 1.0, 21),
        "mean_bandwidth": 0.24,
        "covariance_bandwidth": 0.34,
        "noise_method": "diagonal_difference",
        "noise_bandwidth": 0.24,
        "noise_support": (0.20, 0.80),
        "required_successes": 1,
    },
    {
        "name": "deliberate_narrow_bandwidth_probe",
        "n_curves": 30,
        "samples_per_curve": (4, 7),
        "noise_sd": 0.10,
        "eigenvalues": (1.0, 0.35),
        "observation_design": "center_clustered",
        "grid": (0.0, 1.0, 21),
        "mean_bandwidth": 0.08,
        "covariance_bandwidth": 0.10,
        "noise_method": "fixed",
        "required_successes": 0,
    },
)


def _dataset(scenario, seed):
    times, values, truth = simulate_sparse_functional_truth(
        n_curves=scenario["n_curves"],
        samples_per_curve=scenario["samples_per_curve"],
        noise_sd=scenario["noise_sd"],
        eigenvalues=scenario["eigenvalues"],
        observation_design=scenario["observation_design"],
        random_state=seed,
    )
    trajectories = IrregularTrajectorySet(
        time=times,
        values=tuple(value[:, None] for value in values),
        curve_ids=tuple(f"P{i + 1:03d}|1" for i in range(len(times))),
        dimension_names=("x",),
        metadata=pd.DataFrame(
            {
                "participant_id": [
                    f"P{i + 1:03d}" for i in range(len(times))
                ]
            }
        ),
        coordinate_system="normalized",
        time_unit="s",
        provenance={
            "source": "private_sparse_stress_truth",
            "scenario": scenario["name"],
        },
    )
    return trajectories, truth


def _metric_payload(metrics):
    return {
        "mean_ise": metrics.mean_ise,
        "covariance_ise": metrics.covariance_ise,
        "eigenvalue_relative_error": (
            metrics.eigenvalue_relative_error.tolist()
        ),
        "component_absolute_similarity": (
            metrics.component_absolute_similarity.tolist()
        ),
        "subspace_principal_cosines": (
            metrics.subspace_principal_cosines.tolist()
        ),
        "score_correlation": metrics.score_correlation.tolist(),
        "score_rmse": metrics.score_rmse.tolist(),
        "score_failure_rate": metrics.score_failure_rate,
    }


def _run_replicate(scenario, seed):
    trajectories, truth = _dataset(scenario, seed)
    start, end, n_grid = scenario["grid"]
    grid = np.linspace(start, end, n_grid)

    kwargs = {
        "dimension": "x",
        "n_components": 2,
        "evaluation_grid": grid,
        "mean_bandwidth": scenario["mean_bandwidth"],
        "covariance_bandwidth": scenario["covariance_bandwidth"],
        "analysis_support_action": scenario.get(
            "analysis_support_action",
            "error",
        ),
        "psd_action": "project",
        "score_failure_action": "retain_nan",
    }
    if scenario["noise_method"] == "fixed":
        kwargs.update(
            {
                "noise_variance_method": "fixed",
                "measurement_error_variance": truth.noise_sd**2,
            }
        )
    else:
        kwargs.update(
            {
                "noise_variance_method": "diagonal_difference",
                "noise_bandwidth": scenario["noise_bandwidth"],
                "noise_support": scenario["noise_support"],
            }
        )

    pair_count = int(
        sum(len(time) * (len(time) - 1) for time in trajectories.time)
    )
    try:
        result = fit_sparse_fpca(trajectories, **kwargs)
    except SparseNativeError as exc:
        return {
            "seed": seed,
            "status": "failed_closed",
            "failure_code": exc.code,
            "failure_details": exc.details,
            "n_curves": trajectories.n_curves,
            "median_samples_per_curve": float(
                np.median(trajectories.sample_counts)
            ),
            "covariance_pair_count": pair_count,
            "grid_points": int(n_grid),
        }

    metrics = evaluate_sparse_truth_recovery(result, truth)
    return {
        "seed": seed,
        "status": "success",
        "failure_code": None,
        "n_curves": trajectories.n_curves,
        "median_samples_per_curve": float(
            np.median(trajectories.sample_counts)
        ),
        "covariance_pair_count": pair_count,
        "grid_points": int(n_grid),
        "metrics": _metric_payload(metrics),
    }


def _scenario_summary(scenario, replicates):
    successes = [row for row in replicates if row["status"] == "success"]
    failures = [row for row in replicates if row["status"] != "success"]
    failure_codes = {}
    for row in failures:
        code = row["failure_code"]
        failure_codes[code] = failure_codes.get(code, 0) + 1

    summary = {
        "name": scenario["name"],
        "n_replicates": len(replicates),
        "n_success": len(successes),
        "failure_rate": len(failures) / len(replicates),
        "failure_codes": failure_codes,
    }
    if successes:
        summary["median_mean_ise"] = float(
            np.median([row["metrics"]["mean_ise"] for row in successes])
        )
        summary["median_covariance_ise"] = float(
            np.median(
                [row["metrics"]["covariance_ise"] for row in successes]
            )
        )
        summary["minimum_subspace_cosine"] = float(
            min(
                min(row["metrics"]["subspace_principal_cosines"])
                for row in successes
            )
        )
        finite_score_correlations = [
            value
            for row in successes
            for value in row["metrics"]["score_correlation"]
            if np.isfinite(value)
        ]
        summary["minimum_score_correlation"] = (
            None
            if not finite_score_correlations
            else float(min(finite_score_correlations))
        )
        summary["maximum_score_failure_rate"] = float(
            max(
                row["metrics"]["score_failure_rate"]
                for row in successes
            )
        )
    return summary


def _check_predeclared_gates(scenario, summary):
    required = int(scenario.get("required_successes", 0))
    if summary["n_success"] < required:
        raise RuntimeError(
            f"{scenario['name']} produced {summary['n_success']} successful "
            f"fits; predeclared minimum is {required}"
        )

    minimum_cosine = scenario.get("min_subspace_cosine")
    if minimum_cosine is not None and summary["n_success"]:
        observed = summary["minimum_subspace_cosine"]
        if observed < minimum_cosine:
            raise RuntimeError(
                f"{scenario['name']} minimum subspace cosine {observed:.3f} "
                f"is below predeclared {minimum_cosine:.3f}"
            )

    minimum_score = scenario.get("min_score_correlation")
    if minimum_score is not None and summary["n_success"]:
        observed = summary["minimum_score_correlation"]
        if observed is None or observed < minimum_score:
            raise RuntimeError(
                f"{scenario['name']} minimum score correlation {observed} "
                f"is below predeclared {minimum_score:.3f}"
            )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--replicates", type=int, default=3)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("sparse-fpca-stress-validation.json"),
    )
    args = parser.parse_args()
    if args.replicates < 1:
        raise ValueError("replicates must be positive")

    scenario_payloads = []
    for scenario_index, scenario in enumerate(SCENARIOS):
        replicates = [
            _run_replicate(
                scenario,
                seed=202620
                + 100 * scenario_index
                + replicate,
            )
            for replicate in range(args.replicates)
        ]
        summary = _scenario_summary(scenario, replicates)
        _check_predeclared_gates(scenario, summary)
        scenario_payloads.append(
            {
                "specification": scenario,
                "summary": summary,
                "replicates": replicates,
            }
        )

    payload = {
        "schema_version": 1,
        "kind": "native sparse FPCA/PACE stress validation",
        "comparative_benchmark": False,
        "automatic_tuning": False,
        "replicates_per_scenario": args.replicates,
        "scenarios": scenario_payloads,
        "interpretation": (
            "Deterministic finite-sample recovery and fail-closed "
            "characterization under declared sparse regimes. Thresholds are "
            "qualification guards, not universal statistical guarantees."
        ),
    }
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
