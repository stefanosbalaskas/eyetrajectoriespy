"""Observation-process stress for the public native sparse MFPCA estimator.

This is descriptive sensitivity evidence. It reuses the frozen pre-0.12
row-loss mechanisms, preserves paired x/y timestamps, and fits the public
0.12 sparse MFPCA estimator to each stressed dataset. No stress metric is used
to tune bandwidths, ridge, grid size, or component count.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

from eyetrajectoriespy import (
    evaluate_sparse_mfpca_recovery,
    fit_sparse_mfpca,
    functional_recovery_assessment_frame,
    simulate_functional_scenario,
)


ROOT = Path(__file__).resolve().parents[1]
PRE012_SCRIPT = ROOT / "scripts" / "run_pre012_recovery_audit.py"
MECHANISMS = (
    "none",
    "mcar",
    "signal_dependent_x_loss",
    "signal_dependent_y_loss",
    "eccentricity_dependent_loss",
    "velocity_dependent_loss",
    "phase_dependent_loss",
)
RHO_XY = 0.6
REPLICATES = 3


def _load_pre012():
    spec = importlib.util.spec_from_file_location(
        "run_pre012_recovery_audit_for_mfpca_stress",
        PRE012_SCRIPT,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load pre-0.12 observation-process helper")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _metric(frame: pd.DataFrame, name: str) -> np.ndarray:
    values = pd.to_numeric(
        frame.loc[frame["metric"] == name, "value"],
        errors="coerce",
    ).to_numpy(dtype=float)
    return values[np.isfinite(values)]


def _fit_and_assess(observations, truth):
    result = fit_sparse_mfpca(
        observations,
        dimensions=("x", "y"),
        n_components=len(truth.eigenvalues),
        evaluation_grid=np.asarray(truth.truth_grid, dtype=float),
        mean_bandwidth=0.20,
        covariance_bandwidth=0.28,
        measurement_error="diagonal",
        measurement_error_variance=(
            float(truth.measurement_noise_covariance[0, 0]),
            float(truth.measurement_noise_covariance[1, 1]),
        ),
        psd_action="project",
        score_failure_action="retain_nan",
        covariance_min_local_pairs=8,
    )
    assessment = evaluate_sparse_mfpca_recovery(result, truth)
    frame = functional_recovery_assessment_frame(assessment)

    subspace = _metric(
        frame.loc[frame["source"].isna()],
        "subspace_principal_cosine",
    )
    score_corr = _metric(frame, "score_correlation")
    mean_ise = _metric(frame, "mean_ise")
    covariance_ise = _metric(frame, "covariance_ise")
    reconstruction = _metric(frame, "reconstruction_ise")
    failure = _metric(frame, "score_failure_rate")
    q95 = _metric(frame, "score_condition_number_q95")
    psd = _metric(frame, "psd_relative_operator_correction")
    cxy = frame.loc[
        (frame["metric"] == "covariance_block_ise")
        & (frame["source"] == "cxy"),
        "value",
    ].to_numpy(dtype=float)

    return {
        "mean_ise": float(mean_ise[0]),
        "joint_covariance_ise": float(covariance_ise[0]),
        "cxy_ise": float(cxy[0]),
        "minimum_subspace_principal_cosine": float(np.min(subspace)),
        "median_score_correlation": float(np.median(score_corr)),
        "reconstruction_ise": float(reconstruction[0]),
        "score_failure_rate": float(failure[0]),
        "score_condition_number_q95": float(q95[0]),
        "psd_relative_operator_correction": float(psd[0]),
    }


def run_stress() -> pd.DataFrame:
    pre012 = _load_pre012()
    scenario, design = pre012._planar_scenario(
        RHO_XY,
        name="sparse_mfpca_observation_stress",
        seed_start=17100,
        replicates=REPLICATES,
        n_participants=36,
        samples_per_curve=(22, 30),
    )
    rows: list[dict[str, object]] = []

    for replicate in range(REPLICATES):
        simulation = simulate_functional_scenario(
            scenario,
            mean=pre012._mean_planar,
            eigenfunctions=design.eigenfunctions,
            replicate=replicate,
        )
        for mechanism_index, mechanism in enumerate(MECHANISMS):
            row: dict[str, object] = {
                "replicate": replicate,
                "mechanism": mechanism,
                "rho_xy": RHO_XY,
                "target_loss_fraction": (
                    0.0 if mechanism == "none" else pre012.TARGET_LOSS
                ),
                "status": "ok",
                "threshold_gate_applied": False,
                "parameter_selection_performed": False,
            }
            if mechanism == "none":
                observations = simulation.observations
                loss_metrics = {
                    "actual_loss_fraction": 0.0,
                    "minimum_retained_samples": int(
                        np.min(observations.sample_counts)
                    ),
                    "mean_retained_samples": float(
                        np.mean(observations.sample_counts)
                    ),
                }
            else:
                try:
                    observations, loss_metrics = pre012._apply_loss(
                        simulation,
                        mechanism,
                        seed=scenario.seeds()[replicate]
                        + 10000 * (mechanism_index + 1),
                    )
                except Exception as exc:
                    row.update(
                        {
                            "status": "observation_process_failed",
                            "error_type": type(exc).__name__,
                            "error_message": str(exc),
                        }
                    )
                    rows.append(row)
                    continue

            row.update(loss_metrics)
            try:
                row.update(
                    _fit_and_assess(
                        observations,
                        simulation.truth,
                    )
                )
            except Exception as exc:
                row.update(
                    {
                        "status": "fit_or_assessment_failed",
                        "error_type": type(exc).__name__,
                        "error_message": str(exc),
                    }
                )
            rows.append(row)

    return pd.DataFrame(rows)


def _summary(frame: pd.DataFrame) -> pd.DataFrame:
    ok = frame.loc[frame["status"] == "ok"].copy()
    if ok.empty:
        return pd.DataFrame()
    columns = [
        "actual_loss_fraction",
        "mean_ise",
        "joint_covariance_ise",
        "cxy_ise",
        "minimum_subspace_principal_cosine",
        "median_score_correlation",
        "reconstruction_ise",
        "score_failure_rate",
        "score_condition_number_q95",
        "psd_relative_operator_correction",
    ]
    return (
        ok.groupby("mechanism", as_index=False)[columns]
        .mean()
        .sort_values("mechanism")
        .reset_index(drop=True)
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("sparse-mfpca-observation-stress"),
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    frame = run_stress()
    summary = _summary(frame)
    frame.to_csv(args.output_dir / "observation_stress.csv", index=False)
    summary.to_csv(
        args.output_dir / "observation_stress_summary.csv",
        index=False,
    )
    payload = {
        "schema_version": 1,
        "evidence_type": "observation_process_stress",
        "estimator": "fit_sparse_mfpca",
        "rho_xy": RHO_XY,
        "replicates": REPLICATES,
        "mechanisms": list(MECHANISMS),
        "threshold_gate_applied": False,
        "parameter_selection_performed": False,
        "supported_contract": (
            "paired x/y coordinates retained on the same native timestamps"
        ),
        "rows": frame.replace({np.nan: None}).to_dict(orient="records"),
        "summary": summary.replace({np.nan: None}).to_dict(orient="records"),
        "interpretation": (
            "Descriptive sensitivity to seeded row-level observation loss. "
            "Signal-dependent loss can change finite-sample recovery and is "
            "not silently reclassified as an estimator defect. No stress "
            "metric selects tuning parameters or changes public defaults."
        ),
    }
    (args.output_dir / "observation_stress.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("SPARSE_MFPCA_OBSERVATION_STRESS")
    print(summary.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
