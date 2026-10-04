#!/usr/bin/env python
"""Known-population validation for conditional sparse PACE score uncertainty.

This script deliberately supplies the true Gaussian population objects to PACE.
It therefore validates the conditional score-uncertainty contract itself rather
than claiming coverage after mean/covariance/eigensystem estimation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from eyetrajectoriespy._sparse_native import pace_scores
from eyetrajectoriespy._sparse_truth import simulate_sparse_functional_truth
from eyetrajectoriespy.fpca import functional_trapezoid_weights
from eyetrajectoriespy.sparse_score_uncertainty import (
    sparse_fpca_score_uncertainty,
)
from eyetrajectoriespy.types import IrregularTrajectorySet, SparseFPCAResult


SCENARIOS = (
    ("sparse_low_noise", (4, 6), 0.05),
    ("dense_low_noise", (12, 16), 0.05),
    ("sparse_high_noise", (4, 6), 0.25),
    ("dense_high_noise", (12, 16), 0.25),
)


def _oracle_fit(times, observed, truth, curve_ids, *, grid):
    mean = truth.mean(grid)
    functions = np.vstack([function(grid) for function in truth.eigenfunctions])
    covariance = np.zeros((grid.size, grid.size), dtype=float)
    for eigenvalue, function in zip(
        truth.eigenvalues,
        functions,
        strict=True,
    ):
        covariance += float(eigenvalue) * np.outer(function, function)

    scored = pace_scores(
        curve_ids,
        times,
        observed,
        evaluation_grid=grid,
        fitted_mean=mean,
        fitted_covariance=covariance,
        eigenvalues=truth.eigenvalues,
        eigenfunctions=functions,
        noise_variance=truth.noise_sd**2,
        n_components=2,
        score_ridge=0.0,
        condition_limit=1e12,
        min_score_samples=2,
        failure_action="error",
    )
    return SparseFPCAResult(
        scores=scored.scores,
        eigenvalues=truth.eigenvalues.copy(),
        dimension="x",
        curve_ids=curve_ids,
        metadata=pd.DataFrame(index=range(len(curve_ids))),
        coordinate_system="normalized",
        time_unit="normalized",
        n_components=2,
        fit_method="native_covariance",
        fit_smoothing="oracle_population",
        score_method="PACE",
        score_smoothing=None,
        tolerance=1e-12,
        normalize=False,
        provenance={
            "sparse_fpca": {
                "backend": "native",
                "score_ridge": 0.0,
                "score_condition_limit": 1e12,
                "min_score_samples": 2,
                "score_failure_action": "error",
                "sample_counts": truth.sample_counts.tolist(),
                "analysis_support_action": "error",
                "population_source": "known_simulation_truth",
            }
        },
        evaluation_grid=grid.copy(),
        mean=mean.copy(),
        covariance=covariance.copy(),
        eigenfunctions=functions.copy(),
        noise_variance=float(truth.noise_sd**2),
        quadrature_weights=functional_trapezoid_weights(grid),
        score_diagnostics=scored.diagnostics.copy(),
        covariance_diagnostics={},
        mean_support_counts=np.full(grid.size, len(curve_ids), dtype=int),
        covariance_support_counts=np.full(
            (grid.size, grid.size), len(curve_ids), dtype=int
        ),
    )


def _run_scenario(name, sample_counts, noise_sd, *, n_curves, seed):
    times, observed, truth = simulate_sparse_functional_truth(
        n_curves=n_curves,
        samples_per_curve=sample_counts,
        noise_sd=noise_sd,
        eigenvalues=(1.0, 0.35),
        observation_design="uniform",
        random_state=seed,
    )
    curve_ids = tuple(f"curve_{index:04d}" for index in range(n_curves))
    trajectories = IrregularTrajectorySet(
        time=times,
        values=tuple(value[:, None] for value in observed),
        curve_ids=curve_ids,
        dimension_names=("x",),
        coordinate_system="normalized",
        time_unit="normalized",
        provenance={"simulation": name},
    )
    grid = np.linspace(0.0, 1.0, 401)
    fit = _oracle_fit(times, observed, truth, curve_ids, grid=grid)
    uncertainty = sparse_fpca_score_uncertainty(fit, trajectories)

    error = fit.scores - truth.scores
    variance = np.diagonal(uncertainty.covariance, axis1=1, axis2=2)
    se = uncertainty.standard_errors
    standardized = error / se

    component_records = []
    for component in range(2):
        component_error = error[:, component]
        component_variance = variance[:, component]
        component_standardized = standardized[:, component]
        component_records.append(
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
                "mean_standard_error": float(np.mean(se[:, component])),
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
                    np.mean(np.abs(component_standardized) <= 1.959963984540054)
                ),
            }
        )

    diagnostics = uncertainty.diagnostics
    return {
        "scenario": name,
        "n_curves": n_curves,
        "samples_per_curve": list(sample_counts),
        "noise_sd": noise_sd,
        "failed_system_proportion": float(
            np.mean(diagnostics["status_code"] != "ok")
        ),
        "mean_total_conditional_variance": float(np.mean(np.sum(variance, axis=1))),
        "components": component_records,
    }


def _validate(records):
    failures = []
    by_name = {record["scenario"]: record for record in records}

    for record in records:
        if record["failed_system_proportion"] != 0.0:
            failures.append(
                f"{record['scenario']}: conditional systems unexpectedly failed"
            )
        for component in record["components"]:
            label = f"{record['scenario']}:pc{component['component']}"
            ratio = component["mse_to_variance_ratio"]
            if not 0.70 <= ratio <= 1.30:
                failures.append(f"{label}: mse/variance ratio={ratio:.3f}")
            if not 0.60 <= component["coverage_68"] <= 0.76:
                failures.append(
                    f"{label}: 68% conditional coverage={component['coverage_68']:.3f}"
                )
            if not 0.91 <= component["coverage_95"] <= 0.98:
                failures.append(
                    f"{label}: 95% conditional coverage={component['coverage_95']:.3f}"
                )
            if abs(component["standardized_error_mean"]) > 0.15:
                failures.append(
                    f"{label}: standardized mean={component['standardized_error_mean']:.3f}"
                )
            if not 0.80 <= component["standardized_error_sd"] <= 1.20:
                failures.append(
                    f"{label}: standardized sd={component['standardized_error_sd']:.3f}"
                )

    if not (
        by_name["sparse_high_noise"]["mean_total_conditional_variance"]
        > by_name["sparse_low_noise"]["mean_total_conditional_variance"]
    ):
        failures.append("higher noise did not increase uncertainty for sparse curves")
    if not (
        by_name["dense_high_noise"]["mean_total_conditional_variance"]
        > by_name["dense_low_noise"]["mean_total_conditional_variance"]
    ):
        failures.append("higher noise did not increase uncertainty for dense curves")
    if not (
        by_name["sparse_low_noise"]["mean_total_conditional_variance"]
        > by_name["dense_low_noise"]["mean_total_conditional_variance"]
    ):
        failures.append("denser low-noise observation did not reduce uncertainty")
    if not (
        by_name["sparse_high_noise"]["mean_total_conditional_variance"]
        > by_name["dense_high_noise"]["mean_total_conditional_variance"]
    ):
        failures.append("denser high-noise observation did not reduce uncertainty")
    return failures


def main():
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
            noise_sd,
            n_curves=args.n_curves,
            seed=20261005 + index * 1000,
        )
        for index, (name, sample_counts, noise_sd) in enumerate(SCENARIOS)
    ]
    failures = _validate(records)
    payload = {
        "validation_target": "conditional_sparse_pace_score_uncertainty",
        "population_objects": "known_truth_oracle",
        "population_estimation_uncertainty_included": False,
        "coverage_interpretation": (
            "conditional on known population objects; not full sparse-FPCA coverage"
        ),
        "n_curves_per_scenario": args.n_curves,
        "scenarios": records,
        "validation_failures": failures,
        "validation_passed": not failures,
    }
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if failures:
        raise SystemExit("; ".join(failures))


if __name__ == "__main__":
    main()
