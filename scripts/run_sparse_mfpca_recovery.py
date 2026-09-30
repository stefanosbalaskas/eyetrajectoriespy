"""Threshold-free known-truth recovery audit for native sparse MFPCA."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from eyetrajectoriespy import IrregularTrajectorySet, fit_sparse_mfpca
from eyetrajectoriespy._sparse_multivariate import (
    block_quadrature_weights,
    covariance_blocks_to_matrix,
)
from eyetrajectoriespy._sparse_multivariate_truth import (
    simulate_sparse_multivariate_truth,
)


SIGNAL_RELATIVE_EIGENVALUE_FLOOR = 0.05


def _principal_cosines_functional(estimated, truth, grid):
    estimated = np.asarray(estimated, dtype=float)
    truth = np.asarray(truth, dtype=float)
    n_components, n_grid, n_dimensions = estimated.shape
    if truth.shape != estimated.shape:
        raise ValueError("truth and estimated eigenfunctions must align")

    weights = block_quadrature_weights(
        grid,
        n_dimensions=n_dimensions,
    )
    estimated_flat = (
        estimated.transpose(0, 2, 1)
        .reshape(n_components, n_dimensions * n_grid)
    )
    truth_flat = (
        truth.transpose(0, 2, 1)
        .reshape(n_components, n_dimensions * n_grid)
    )
    cross = (
        estimated_flat * weights[None, :]
    ) @ truth_flat.T
    return np.linalg.svd(cross, compute_uv=False)


def _principal_cosines_scores(estimated, truth):
    estimated = np.asarray(estimated, dtype=float)
    truth = np.asarray(truth, dtype=float)
    if estimated.shape != truth.shape:
        raise ValueError("truth and estimated scores must align")
    estimated = estimated - np.mean(estimated, axis=0, keepdims=True)
    truth = truth - np.mean(truth, axis=0, keepdims=True)
    q_estimated, _ = np.linalg.qr(estimated)
    q_truth, _ = np.linalg.qr(truth)
    return np.linalg.svd(q_estimated.T @ q_truth, compute_uv=False)


def _weighted_operator(blocks, grid):
    matrix = covariance_blocks_to_matrix(blocks)
    weights = block_quadrature_weights(
        grid,
        n_dimensions=blocks.shape[0],
    )
    root = np.sqrt(weights)
    return root[:, None] * matrix * root[None, :]


def _recovery_row(rho, seed):
    times, values, truth = simulate_sparse_multivariate_truth(
        n_curves=72,
        samples_per_curve=(9, 14),
        noise_sd=(0.06, 0.07),
        temporal_eigenvalues=(1.0, 0.35),
        channel_correlation=rho,
        observation_design="uniform",
        random_state=seed,
    )
    trajectories = IrregularTrajectorySet(
        time=times,
        values=values,
        curve_ids=tuple(f"curve-{i:03d}" for i in range(len(times))),
        dimension_names=("x", "y"),
        coordinate_system="normalized",
        time_unit="normalized",
        provenance={
            "validation_fixture": "sparse_multivariate_known_truth",
            "rho_xy": rho,
            "random_state": seed,
        },
    )
    grid = np.linspace(0.0, 1.0, 17)
    fit = fit_sparse_mfpca(
        trajectories,
        n_components=4,
        evaluation_grid=grid,
        mean_bandwidth=0.24,
        covariance_bandwidth=0.34,
        cross_covariance_bandwidth=0.34,
        noise_variance_method="fixed",
        measurement_error_variances={
            "x": float(truth.noise_sd[0] ** 2),
            "y": float(truth.noise_sd[1] ** 2),
        },
        psd_action="project",
        score_ridge=1e-8,
        covariance_min_local_pairs=8,
        cross_covariance_min_local_pairs=8,
    )

    true_mean = truth.mean(grid)
    true_blocks = truth.covariance_blocks(grid)
    true_functions = truth.joint_eigenfunctions(grid)

    functional_cosines = _principal_cosines_functional(
        fit.eigenfunctions,
        true_functions,
        grid,
    )
    score_cosines = _principal_cosines_scores(
        fit.scores,
        truth.joint_scores,
    )

    signal_mask = (
        truth.joint_eigenvalues
        >= SIGNAL_RELATIVE_EIGENVALUE_FLOOR
        * float(truth.joint_eigenvalues[0])
    )
    n_signal_components = int(np.count_nonzero(signal_mask))
    signal_functional_cosines = _principal_cosines_functional(
        fit.eigenfunctions[:n_signal_components],
        true_functions[:n_signal_components],
        grid,
    )
    signal_score_cosines = _principal_cosines_scores(
        fit.scores[:, :n_signal_components],
        truth.joint_scores[:, :n_signal_components],
    )

    fitted_operator = _weighted_operator(fit.covariance, grid)
    true_operator = _weighted_operator(true_blocks, grid)
    full_covariance_relative_error = float(
        np.linalg.norm(fitted_operator - true_operator, ord="fro")
        / np.linalg.norm(true_operator, ord="fro")
    )

    marginal_errors = []
    for dimension in range(2):
        fitted = fit.covariance[dimension, :, dimension, :]
        expected = true_blocks[dimension, :, dimension, :]
        marginal_errors.append(
            float(
                np.linalg.norm(fitted - expected, ord="fro")
                / np.linalg.norm(expected, ord="fro")
            )
        )

    cross_error_scaled_to_marginal = float(
        np.linalg.norm(
            fit.covariance[0, :, 1, :] - true_blocks[0, :, 1, :],
            ord="fro",
        )
        / np.linalg.norm(true_blocks[0, :, 0, :], ord="fro")
    )

    cross_operator = np.zeros_like(true_blocks)
    cross_operator[0, :, 1, :] = true_blocks[0, :, 1, :]
    cross_operator[1, :, 0, :] = true_blocks[1, :, 0, :]
    cross_energy_fraction = float(
        np.linalg.norm(_weighted_operator(cross_operator, grid), ord="fro") ** 2
        / np.linalg.norm(true_operator, ord="fro") ** 2
    )

    diagnostics = fit.score_diagnostics
    failure_rate = float(np.mean(diagnostics["status_code"] != "ok"))

    row = {
        "rho_xy": float(rho),
        "seed": int(seed),
        "n_curves": int(trajectories.n_curves),
        "mean_samples_per_curve": float(np.mean(trajectories.sample_counts)),
        "truth_cross_operator_energy_fraction": cross_energy_fraction,
        "mean_rmse": float(np.sqrt(np.mean((fit.mean - true_mean) ** 2))),
        "marginal_covariance_relative_error_mean": float(
            np.mean(marginal_errors)
        ),
        "cross_covariance_error_scaled_to_marginal": (
            cross_error_scaled_to_marginal
        ),
        "full_block_covariance_relative_error": full_covariance_relative_error,
        "requested_component_count": int(len(truth.joint_eigenvalues)),
        "signal_relative_eigenvalue_floor": (
            SIGNAL_RELATIVE_EIGENVALUE_FLOOR
        ),
        "signal_component_count": n_signal_components,
        "functional_subspace_min_principal_cosine": float(
            np.min(functional_cosines)
        ),
        "functional_subspace_principal_cosines": [
            float(value) for value in functional_cosines
        ],
        "signal_functional_subspace_min_principal_cosine": float(
            np.min(signal_functional_cosines)
        ),
        "signal_functional_subspace_principal_cosines": [
            float(value) for value in signal_functional_cosines
        ],
        "score_subspace_min_principal_cosine": float(np.min(score_cosines)),
        "score_subspace_principal_cosines": [
            float(value) for value in score_cosines
        ],
        "signal_score_subspace_min_principal_cosine": float(
            np.min(signal_score_cosines)
        ),
        "signal_score_subspace_principal_cosines": [
            float(value) for value in signal_score_cosines
        ],
        "score_failure_rate": failure_rate,
        "estimated_eigenvalues": [
            float(value) for value in fit.eigenvalues
        ],
        "truth_eigenvalues": [
            float(value) for value in truth.joint_eigenvalues
        ],
        "block_psd_relative_operator_correction": float(
            fit.covariance_diagnostics[
                "relative_operator_correction_frobenius_norm"
            ]
        ),
    }
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        default="sparse-mfpca-recovery",
    )
    args = parser.parse_args()

    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)

    rows = [
        _recovery_row(rho, 202612 + index * 101)
        for index, rho in enumerate((0.0, 0.3, 0.6, 0.9))
    ]

    flat_rows = []
    for row in rows:
        flat = {
            key: value
            for key, value in row.items()
            if not isinstance(value, list)
        }
        flat_rows.append(flat)
    pd.DataFrame(flat_rows).to_csv(
        output / "sparse_mfpca_recovery.csv",
        index=False,
    )

    payload = {
        "audit": "native sparse multivariate FPCA threshold-free recovery",
        "qualification_gate": False,
        "estimator": "fit_sparse_mfpca",
        "pilot_role": (
            "descriptive development evidence used to freeze the subsequent "
            "independent qualification contract"
        ),
        "signal_subspace_contract": {
            "relative_eigenvalue_floor": SIGNAL_RELATIVE_EIGENVALUE_FLOOR,
            "definition": (
                "truth eigenvalue >= relative_eigenvalue_floor times the "
                "leading truth eigenvalue"
            ),
            "weak_tail_reporting": "retained separately; never deleted",
        },
        "measurement_error_contract": "fixed_marginal_independent_cross_channel",
        "psd_action": "project",
        "scenarios": rows,
        "interpretation": (
            "descriptive known-truth recovery evidence; thresholds are not "
            "introduced in this first evidence pass"
        ),
    }
    (output / "sparse_mfpca_recovery.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
