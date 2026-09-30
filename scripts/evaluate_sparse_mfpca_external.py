"""Evaluate native sparse MFPCA on the frozen pre-0.12 external fixture."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
from pathlib import Path

import numpy as np
import pandas as pd

from eyetrajectoriespy import IrregularTrajectorySet, fit_sparse_mfpca
from evaluate_pre012_mgsfpca import (
    _column_subspace_cosines,
    _functional_subspace_cosines,
)
from eyetrajectoriespy import functional_trapezoid_weights


SIGNAL_RELATIVE_EIGENVALUE_FLOOR = 0.05


def _load_fixture(output_dir: Path) -> tuple[IrregularTrajectorySet, dict]:
    truth = json.loads(
        (output_dir / "external_fixture_truth.json").read_text(
            encoding="utf-8"
        )
    )
    x = pd.read_csv(output_dir / "external_fixture_x.csv")
    y = pd.read_csv(output_dir / "external_fixture_y.csv")
    required = ["ID", "time", "value"]
    if list(x.columns) != required or list(y.columns) != required:
        raise ValueError("frozen fixture columns must be ID, time, value")

    curve_ids = tuple(map(str, truth["curve_ids"]))
    times = []
    values = []
    for curve_id in curve_ids:
        x_curve = x.loc[x["ID"].astype(str) == curve_id]
        y_curve = y.loc[y["ID"].astype(str) == curve_id]
        if len(x_curve) == 0 or len(y_curve) == 0:
            raise ValueError(f"missing fixture rows for {curve_id!r}")

        x_time = pd.to_numeric(
            x_curve["time"], errors="raise"
        ).to_numpy(dtype=float)
        y_time = pd.to_numeric(
            y_curve["time"], errors="raise"
        ).to_numpy(dtype=float)
        x_value = pd.to_numeric(
            x_curve["value"], errors="raise"
        ).to_numpy(dtype=float)
        y_value = pd.to_numeric(
            y_curve["value"], errors="raise"
        ).to_numpy(dtype=float)
        if not np.array_equal(x_time, y_time):
            raise ValueError(
                "frozen x/y fixture must share native times within curve"
            )
        order = np.argsort(x_time)
        times.append(x_time[order])
        values.append(
            np.column_stack([x_value[order], y_value[order]])
        )

    trajectories = IrregularTrajectorySet(
        time=tuple(times),
        values=tuple(values),
        curve_ids=curve_ids,
        dimension_names=("x", "y"),
        coordinate_system="normalized",
        time_unit="normalized",
        provenance={
            "fixture": "pre012_external_fixture",
            "rho_xy": truth["rho_xy"],
        },
    )
    return trajectories, truth


def evaluate(output_dir: Path) -> dict[str, object]:
    trajectories, truth = _load_fixture(output_dir)
    grid = np.asarray(truth["truth_grid"], dtype=float)
    truth_functions = np.asarray(truth["eigenfunctions"], dtype=float)
    truth_scores = np.asarray(truth["scores"], dtype=float)
    truth_eigenvalues = np.asarray(truth["eigenvalues"], dtype=float)
    n_components = int(truth_eigenvalues.size)

    fit = fit_sparse_mfpca(
        trajectories,
        n_components=n_components,
        evaluation_grid=grid,
        mean_bandwidth=0.20,
        covariance_bandwidth=0.28,
        cross_covariance_bandwidth=0.28,
        noise_variance_method="fixed",
        measurement_error_variances={
            "x": 0.03**2,
            "y": 0.03**2,
        },
        cross_channel_measurement_error="independent",
        psd_action="project",
        score_ridge=1e-8,
        score_failure_action="retain_nan",
        covariance_min_local_pairs=8,
        cross_covariance_min_local_pairs=8,
    )

    weights = functional_trapezoid_weights(grid)
    functional_cosines = _functional_subspace_cosines(
        fit.eigenfunctions,
        truth_functions,
        weights,
    )
    score_cosines = _column_subspace_cosines(
        fit.scores,
        truth_scores[:, :n_components],
    )

    signal_count = int(
        np.count_nonzero(
            truth_eigenvalues
            >= SIGNAL_RELATIVE_EIGENVALUE_FLOOR
            * float(truth_eigenvalues[0])
        )
    )
    signal_functional_cosines = _functional_subspace_cosines(
        fit.eigenfunctions[:signal_count],
        truth_functions[:signal_count],
        weights,
    )
    signal_score_cosines = _column_subspace_cosines(
        fit.scores[:, :signal_count],
        truth_scores[:, :signal_count],
    )

    diagnostics = fit.score_diagnostics
    score_failure_rate = float(
        np.mean(diagnostics["status_code"].to_numpy() != "ok")
    )

    payload = {
        "schema_version": 1,
        "audit": "native sparse MFPCA frozen-fixture sensitivity",
        "estimator": "eyetrajectoriespy::fit_sparse_mfpca",
        "eyetrajectoriespy_version": importlib.metadata.version(
            "eyetrajectoriespy"
        ),
        "equivalence_claim": False,
        "fixture_rho_xy": float(truth["rho_xy"]),
        "n_curves": trajectories.n_curves,
        "n_components": n_components,
        "signal_relative_eigenvalue_floor": (
            SIGNAL_RELATIVE_EIGENVALUE_FLOOR
        ),
        "signal_component_count": signal_count,
        "functional_subspace_principal_cosines": [
            float(value) for value in functional_cosines
        ],
        "functional_subspace_min_principal_cosine": float(
            np.min(functional_cosines)
        ),
        "signal_functional_subspace_principal_cosines": [
            float(value) for value in signal_functional_cosines
        ],
        "signal_functional_subspace_min_principal_cosine": float(
            np.min(signal_functional_cosines)
        ),
        "score_subspace_principal_cosines": [
            float(value) for value in score_cosines
        ],
        "score_subspace_min_principal_cosine": float(
            np.min(score_cosines)
        ),
        "signal_score_subspace_principal_cosines": [
            float(value) for value in signal_score_cosines
        ],
        "signal_score_subspace_min_principal_cosine": float(
            np.min(signal_score_cosines)
        ),
        "score_failure_rate": score_failure_rate,
        "estimated_eigenvalues": [
            float(value) for value in fit.eigenvalues
        ],
        "truth_eigenvalues": [
            float(value) for value in truth_eigenvalues
        ],
        "block_psd_relative_operator_correction": float(
            fit.covariance_diagnostics[
                "relative_operator_correction_frobenius_norm"
            ]
        ),
        "settings": {
            "mean_bandwidth": 0.20,
            "covariance_bandwidth": 0.28,
            "cross_covariance_bandwidth": 0.28,
            "measurement_error_variance_x": 0.03**2,
            "measurement_error_variance_y": 0.03**2,
            "psd_action": "project",
            "score_ridge": 1e-8,
        },
        "interpretation": (
            "Frozen-fixture sensitivity evidence for the new native estimator. "
            "The fixture predates the estimator implementation. This is not an "
            "exact-equivalence claim against mGSFPCA because the methods use "
            "different smoothing, bases, likelihoods and score contracts."
        ),
    }
    (output_dir / "eyetrajectoriespy_sparse_mfpca_sensitivity.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    evaluate(args.output_dir)


if __name__ == "__main__":
    main()
