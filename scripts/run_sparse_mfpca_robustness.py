"""Robustness evidence for native sparse multivariate FPCA.

Two independent checks are run:
1. evaluation-grid and declared-bandwidth sensitivity on known truth;
2. reuse of the pre-0.12 MCAR/signal-dependent observation-loss laboratory.

The observation-loss section is stress evidence rather than an estimator
correctness gate because informative missingness changes the data-generating
process seen by the estimator.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from eyetrajectoriespy import (
    IrregularTrajectorySet,
    fit_sparse_mfpca,
    functional_trapezoid_weights,
    simulate_functional_scenario,
)
from eyetrajectoriespy._sparse_multivariate_truth import (
    simulate_sparse_multivariate_truth,
)
from run_pre012_recovery_audit import (
    LOSS_MECHANISMS,
    _apply_loss,
    _mean_planar,
    _planar_scenario,
)


SIGNAL_RELATIVE_EIGENVALUE_FLOOR = 0.05


def _functional_cosines(estimated, truth, weights):
    estimated = np.asarray(estimated, dtype=float)
    truth = np.asarray(truth, dtype=float)
    if estimated.shape != truth.shape:
        raise ValueError("estimated and truth eigenfunctions must align")
    cross = np.einsum(
        "ktd,t,ltd->kl",
        estimated,
        weights,
        truth,
    )
    return np.linalg.svd(cross, compute_uv=False)


def _score_cosines(estimated, truth):
    estimated = np.asarray(estimated, dtype=float)
    truth = np.asarray(truth, dtype=float)
    if estimated.shape != truth.shape:
        raise ValueError("estimated and truth scores must align")
    valid = np.all(np.isfinite(estimated), axis=1)
    if np.count_nonzero(valid) <= estimated.shape[1]:
        return np.full(estimated.shape[1], np.nan)
    left = estimated[valid] - np.mean(
        estimated[valid], axis=0, keepdims=True
    )
    right = truth[valid] - np.mean(
        truth[valid], axis=0, keepdims=True
    )
    q_left, _ = np.linalg.qr(left)
    q_right, _ = np.linalg.qr(right)
    return np.linalg.svd(q_left.T @ q_right, compute_uv=False)


def _signal_count(eigenvalues):
    values = np.asarray(eigenvalues, dtype=float)
    return int(
        np.count_nonzero(
            values
            >= SIGNAL_RELATIVE_EIGENVALUE_FLOOR * float(values[0])
        )
    )


def _fit_metrics(
    observations,
    *,
    grid,
    truth_functions,
    truth_scores,
    truth_eigenvalues,
    noise_variances,
    mean_bandwidth,
    covariance_bandwidth,
):
    n_components = len(truth_eigenvalues)
    result = fit_sparse_mfpca(
        observations,
        n_components=n_components,
        evaluation_grid=grid,
        mean_bandwidth=mean_bandwidth,
        covariance_bandwidth=covariance_bandwidth,
        cross_covariance_bandwidth=covariance_bandwidth,
        noise_variance_method="fixed",
        measurement_error_variances={
            "x": float(noise_variances[0]),
            "y": float(noise_variances[1]),
        },
        psd_action="project",
        score_ridge=1e-8,
        score_failure_action="retain_nan",
        covariance_min_local_pairs=8,
        cross_covariance_min_local_pairs=8,
    )

    signal_count = _signal_count(truth_eigenvalues)
    weights = functional_trapezoid_weights(grid)
    function_cosines = _functional_cosines(
        result.eigenfunctions[:signal_count],
        truth_functions[:signal_count],
        weights,
    )
    score_cosines = _score_cosines(
        result.scores[:, :signal_count],
        truth_scores[:, :signal_count],
    )
    failure_rate = float(
        np.mean(
            result.score_diagnostics["status_code"].to_numpy() != "ok"
        )
    )
    return result, {
        "signal_component_count": signal_count,
        "signal_functional_subspace_min_principal_cosine": float(
            np.nanmin(function_cosines)
        ),
        "signal_score_subspace_min_principal_cosine": float(
            np.nanmin(score_cosines)
        ),
        "score_failure_rate": failure_rate,
        "block_psd_relative_operator_correction": float(
            result.covariance_diagnostics[
                "relative_operator_correction_frobenius_norm"
            ]
        ),
    }


def _grid_bandwidth_sensitivity():
    times, values, truth = simulate_sparse_multivariate_truth(
        n_curves=72,
        samples_per_curve=(9, 14),
        noise_sd=(0.06, 0.07),
        temporal_eigenvalues=(1.0, 0.35),
        channel_correlation=0.6,
        observation_design="uniform",
        random_state=420001,
    )
    observations = IrregularTrajectorySet(
        time=times,
        values=values,
        curve_ids=tuple(f"curve-{i:03d}" for i in range(len(times))),
        dimension_names=("x", "y"),
        coordinate_system="normalized",
        time_unit="normalized",
        provenance={"validation": "sparse_mfpca_grid_bandwidth_sensitivity"},
    )
    configurations = (
        ("base", 17, 0.24, 0.34),
        ("grid_coarse", 13, 0.24, 0.34),
        ("grid_fine", 21, 0.24, 0.34),
        ("bandwidth_low", 17, 0.20, 0.30),
        ("bandwidth_high", 17, 0.28, 0.38),
    )

    rows = []
    for name, grid_points, mean_bandwidth, covariance_bandwidth in configurations:
        grid = np.linspace(0.0, 1.0, grid_points)
        truth_functions = truth.joint_eigenfunctions(grid)
        result, metrics = _fit_metrics(
            observations,
            grid=grid,
            truth_functions=truth_functions,
            truth_scores=truth.joint_scores,
            truth_eigenvalues=truth.joint_eigenvalues,
            noise_variances=truth.noise_sd**2,
            mean_bandwidth=mean_bandwidth,
            covariance_bandwidth=covariance_bandwidth,
        )
        row = {
            "configuration": name,
            "grid_points": grid_points,
            "mean_bandwidth": mean_bandwidth,
            "covariance_bandwidth": covariance_bandwidth,
            **metrics,
            "estimated_eigenvalues": [
                float(value) for value in result.eigenvalues
            ],
        }
        row["sensitivity_pass"] = bool(
            row["signal_functional_subspace_min_principal_cosine"] >= 0.93
            and row["signal_score_subspace_min_principal_cosine"] >= 0.93
            and row["score_failure_rate"] == 0.0
            and row["block_psd_relative_operator_correction"] <= 0.10
        )
        rows.append(row)
    return rows


def _pre012_truth_functions(truth, grid):
    truth_grid = np.asarray(truth.truth_grid, dtype=float)
    functions = np.asarray(truth.eigenfunctions, dtype=float)
    indices = np.searchsorted(truth_grid, grid)
    if (
        np.any(indices >= truth_grid.size)
        or not np.allclose(truth_grid[indices], grid)
    ):
        raise ValueError("stress grid must be a subset of truth.truth_grid")
    return functions[:, indices, :]


def _observation_loss_stress():
    scenario, design = _planar_scenario(
        0.6,
        name="sparse_mfpca_signal_loss",
        seed_start=430000,
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
        truth = simulation.truth
        noise = np.diag(
            np.asarray(truth.measurement_noise_covariance, dtype=float)
        )
        for mechanism_index, mechanism in enumerate(LOSS_MECHANISMS):
            observations, loss = _apply_loss(
                simulation,
                mechanism,
                seed=(
                    scenario.seeds()[replicate]
                    + 10000 * (mechanism_index + 1)
                ),
            )
            pooled_start = min(float(t[0]) for t in observations.time)
            pooled_end = max(float(t[-1]) for t in observations.time)
            truth_grid = np.asarray(truth.truth_grid, dtype=float)
            mask = (
                (truth_grid >= pooled_start)
                & (truth_grid <= pooled_end)
            )
            grid = truth_grid[mask]
            if grid.size < 13:
                raise RuntimeError(
                    "observation loss left insufficient pooled truth-grid support"
                )
            truth_functions = _pre012_truth_functions(truth, grid)
            result, metrics = _fit_metrics(
                observations,
                grid=grid,
                truth_functions=truth_functions,
                truth_scores=np.asarray(truth.scores, dtype=float),
                truth_eigenvalues=np.asarray(
                    truth.eigenvalues, dtype=float
                ),
                noise_variances=noise,
                mean_bandwidth=0.20,
                covariance_bandwidth=0.28,
            )
            rows.append(
                {
                    "mechanism": mechanism,
                    "replicate": replicate,
                    **loss,
                    "grid_points": int(grid.size),
                    **metrics,
                    "estimated_eigenvalues": [
                        float(value) for value in result.eigenvalues
                    ],
                }
            )

    by_replicate = {}
    for row in rows:
        by_replicate.setdefault(row["replicate"], {})[
            row["mechanism"]
        ] = row
    for row in rows:
        baseline = by_replicate[row["replicate"]]["mcar"]
        row["delta_functional_cosine_vs_mcar"] = (
            row["signal_functional_subspace_min_principal_cosine"]
            - baseline["signal_functional_subspace_min_principal_cosine"]
        )
        row["delta_score_cosine_vs_mcar"] = (
            row["signal_score_subspace_min_principal_cosine"]
            - baseline["signal_score_subspace_min_principal_cosine"]
        )
        row["stress_completed"] = bool(
            np.isfinite(
                row["signal_functional_subspace_min_principal_cosine"]
            )
            and np.isfinite(
                row["signal_score_subspace_min_principal_cosine"]
            )
        )
    return rows


def _flatten(rows):
    return [
        {
            key: value
            for key, value in row.items()
            if not isinstance(value, list)
        }
        for row in rows
    ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        default="sparse-mfpca-robustness",
    )
    args = parser.parse_args()
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)

    sensitivity = _grid_bandwidth_sensitivity()
    stress = _observation_loss_stress()

    pd.DataFrame(_flatten(sensitivity)).to_csv(
        output / "grid_bandwidth_sensitivity.csv",
        index=False,
    )
    pd.DataFrame(_flatten(stress)).to_csv(
        output / "observation_loss_stress.csv",
        index=False,
    )

    payload = {
        "schema_version": 1,
        "audit": "native sparse MFPCA robustness",
        "signal_relative_eigenvalue_floor": (
            SIGNAL_RELATIVE_EIGENVALUE_FLOOR
        ),
        "grid_bandwidth_sensitivity": {
            "qualification_gate": True,
            "criteria": {
                "signal_functional_subspace_min_principal_cosine": 0.93,
                "signal_score_subspace_min_principal_cosine": 0.93,
                "score_failure_rate": 0.0,
                "block_psd_relative_operator_correction": 0.10,
            },
            "rows": sensitivity,
            "qualification_pass": all(
                row["sensitivity_pass"] for row in sensitivity
            ),
        },
        "observation_loss_stress": {
            "qualification_gate": False,
            "mechanisms": list(LOSS_MECHANISMS),
            "rows": stress,
            "all_stress_runs_completed": all(
                row["stress_completed"] for row in stress
            ),
            "interpretation": (
                "MCAR and informative observation loss alter the observation "
                "process itself. These rows are descriptive stress evidence; "
                "they are not silently reclassified as estimator defects."
            ),
        },
    }
    (output / "sparse_mfpca_robustness.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, sort_keys=True))

    if not payload["grid_bandwidth_sensitivity"]["qualification_pass"]:
        raise SystemExit("grid/bandwidth sensitivity qualification failed")
    if not payload["observation_loss_stress"]["all_stress_runs_completed"]:
        raise SystemExit("one or more observation-loss stress runs failed")


if __name__ == "__main__":
    main()
