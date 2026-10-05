"""Deterministic known-truth qualification for sparse partial prediction.

The evidence separates oracle-population conditional Gaussian calibration from
participant-aware split-conformal finite-grid coverage. No continuous-domain or
latent-function conformal coverage claim is evaluated here.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from eyetrajectoriespy.sparse_partial_conformal import (
    calibrate_sparse_fpca_partial_prediction_conformal,
    sparse_fpca_conformal_prediction_band,
)
from eyetrajectoriespy.sparse_partial_prediction import (
    sparse_fpca_partial_trajectory_prediction,
)
from eyetrajectoriespy.types import IrregularTrajectorySet, SparseFPCAResult


GRID = np.linspace(0.0, 1.0, 101)
TARGET_GRID = np.asarray([0.75, 0.85, 0.95])
HISTORY_TIMES = np.asarray(
    [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60]
)
EIGENVALUES = np.asarray([0.55, 0.25, 0.10])
ALPHA = 0.10


def _mean(time: np.ndarray) -> np.ndarray:
    time = np.asarray(time, dtype=float)
    return 0.15 + 0.08 * np.sin(np.pi * time)


def _basis(time: np.ndarray) -> np.ndarray:
    time = np.asarray(time, dtype=float)
    return np.vstack(
        [
            np.sqrt(2.0) * np.sin(np.pi * time),
            np.sqrt(2.0) * np.sin(2.0 * np.pi * time),
            np.sqrt(2.0) * np.cos(np.pi * time),
        ]
    )


def _covariance(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    left_basis = _basis(left)
    right_basis = _basis(right)
    return (left_basis.T * EIGENVALUES[None, :]) @ right_basis


def _oracle_fit(
    *,
    noise_sd: float,
    training_participants: tuple[str, ...] = ("train-p1", "train-p2", "train-p3"),
) -> SparseFPCAResult:
    covariance = _covariance(GRID, GRID)
    eigenfunctions = _basis(GRID)
    curve_ids = tuple(f"train-{index + 1}" for index in range(len(training_participants)))
    return SparseFPCAResult(
        scores=np.zeros((len(curve_ids), EIGENVALUES.size), dtype=float),
        eigenvalues=EIGENVALUES.copy(),
        dimension="x",
        curve_ids=curve_ids,
        metadata=pd.DataFrame({"participant_id": list(training_participants)}),
        coordinate_system="normalized",
        time_unit="normalized",
        n_components=int(EIGENVALUES.size),
        fit_method="native_covariance",
        fit_smoothing="oracle_population",
        score_method="PACE",
        score_smoothing=None,
        tolerance=1e-10,
        normalize=False,
        provenance={
            "sparse_fpca": {
                "backend": "native",
                "score_ridge": 0.0,
                "score_condition_limit": 1e12,
                "min_score_samples": 2,
            },
            "qualification": {"population_objects": "oracle_known_truth"},
        },
        evaluation_grid=GRID.copy(),
        mean=_mean(GRID),
        covariance=covariance,
        eigenfunctions=eigenfunctions,
        noise_variance=float(noise_sd**2),
        quadrature_weights=np.ones(GRID.size),
        score_diagnostics=pd.DataFrame(),
        covariance_diagnostics={},
        mean_support_counts=np.ones(GRID.size, dtype=int),
        covariance_support_counts=np.ones((GRID.size, GRID.size), dtype=int),
    )


def _curve_values(
    rng: np.random.Generator,
    *,
    score: np.ndarray,
    noise_sd: float,
    times: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    latent = _mean(times) + _basis(times).T @ (np.sqrt(EIGENVALUES) * score)
    observed = latent + rng.normal(scale=noise_sd, size=times.size)
    return latent, observed


def _single_curve(
    *,
    curve_id: str,
    times: np.ndarray,
    observed: np.ndarray,
    participant_id: str | None = None,
) -> IrregularTrajectorySet:
    metadata = (
        pd.DataFrame({"participant_id": [participant_id]})
        if participant_id is not None
        else pd.DataFrame()
    )
    return IrregularTrajectorySet(
        time=(np.asarray(times, dtype=float),),
        values=(np.asarray(observed, dtype=float)[:, None],),
        curve_ids=(curve_id,),
        dimension_names=("x",),
        metadata=metadata,
        coordinate_system="normalized",
        time_unit="normalized",
    )


def _oracle_conditional_scenario(
    *,
    seed: int,
    noise_sd: float,
    cutoff: float,
    n_curves: int = 400,
) -> dict[str, float | int]:
    rng = np.random.default_rng(seed)
    fit = _oracle_fit(noise_sd=noise_sd)
    all_times = np.concatenate([HISTORY_TIMES, TARGET_GRID])
    latent_errors: list[np.ndarray] = []
    observed_errors: list[np.ndarray] = []
    latent_variances: list[np.ndarray] = []
    observed_variances: list[np.ndarray] = []
    latent_cover: list[np.ndarray] = []
    observed_cover: list[np.ndarray] = []

    for index in range(n_curves):
        score = rng.normal(size=EIGENVALUES.size)
        latent, observed = _curve_values(
            rng,
            score=score,
            noise_sd=noise_sd,
            times=all_times,
        )
        curve = _single_curve(
            curve_id=f"oracle-{seed}-{index}",
            times=all_times,
            observed=observed,
        )
        prediction = sparse_fpca_partial_trajectory_prediction(
            fit,
            curve,
            history_cutoff=cutoff,
            prediction_grid=TARGET_GRID,
        )
        future_latent = latent[-TARGET_GRID.size :]
        future_observed = observed[-TARGET_GRID.size :]
        latent_error = future_latent - prediction.conditional_mean
        observed_error = future_observed - prediction.conditional_mean
        latent_errors.append(latent_error)
        observed_errors.append(observed_error)
        latent_variances.append(np.diag(prediction.latent_covariance))
        observed_variances.append(np.diag(prediction.observed_predictive_covariance))
        latent_cover.append(
            np.abs(latent_error) <= 1.959963984540054 * prediction.latent_standard_errors
        )
        observed_cover.append(
            np.abs(observed_error)
            <= 1.959963984540054 * prediction.observed_predictive_standard_errors
        )

    latent_error_array = np.concatenate(latent_errors)
    observed_error_array = np.concatenate(observed_errors)
    latent_variance_array = np.concatenate(latent_variances)
    observed_variance_array = np.concatenate(observed_variances)
    latent_z = latent_error_array / np.sqrt(latent_variance_array)
    observed_z = observed_error_array / np.sqrt(observed_variance_array)
    return {
        "seed": int(seed),
        "noise_sd": float(noise_sd),
        "history_cutoff": float(cutoff),
        "n_curves": int(n_curves),
        "n_history": int(np.count_nonzero(HISTORY_TIMES <= cutoff)),
        "latent_rmse": float(np.sqrt(np.mean(latent_error_array**2))),
        "observed_rmse": float(np.sqrt(np.mean(observed_error_array**2))),
        "mean_latent_conditional_variance": float(np.mean(latent_variance_array)),
        "mean_observed_predictive_variance": float(np.mean(observed_variance_array)),
        "latent_standardized_error_mean": float(np.mean(latent_z)),
        "latent_standardized_error_sd": float(np.std(latent_z, ddof=1)),
        "observed_standardized_error_mean": float(np.mean(observed_z)),
        "observed_standardized_error_sd": float(np.std(observed_z, ddof=1)),
        "latent_pointwise_95_coverage": float(np.mean(np.concatenate(latent_cover))),
        "observed_pointwise_95_coverage": float(np.mean(np.concatenate(observed_cover))),
    }


def _grouped_curves(
    *,
    rng: np.random.Generator,
    participant_prefix: str,
    n_participants: int,
    trials_per_participant: int,
    noise_sd: float,
    within_participant_rho: float,
) -> tuple[IrregularTrajectorySet, dict[str, np.ndarray]]:
    all_times = np.concatenate([HISTORY_TIMES, TARGET_GRID])
    times: list[np.ndarray] = []
    values: list[np.ndarray] = []
    curve_ids: list[str] = []
    participants: list[str] = []
    truth: dict[str, np.ndarray] = {}
    rho = float(within_participant_rho)
    for participant_index in range(n_participants):
        participant = f"{participant_prefix}{participant_index + 1}"
        shared = rng.normal(size=EIGENVALUES.size)
        for trial in range(trials_per_participant):
            independent = rng.normal(size=EIGENVALUES.size)
            score = np.sqrt(rho) * shared + np.sqrt(1.0 - rho) * independent
            latent, observed = _curve_values(
                rng,
                score=score,
                noise_sd=noise_sd,
                times=all_times,
            )
            curve_id = f"{participant}-t{trial + 1}"
            times.append(all_times.copy())
            values.append(observed[:, None])
            curve_ids.append(curve_id)
            participants.append(participant)
            truth[curve_id] = np.column_stack([latent, observed])
    return (
        IrregularTrajectorySet(
            time=tuple(times),
            values=tuple(values),
            curve_ids=tuple(curve_ids),
            dimension_names=("x",),
            metadata=pd.DataFrame({"participant_id": participants}),
            coordinate_system="normalized",
            time_unit="normalized",
        ),
        truth,
    )


def _grouped_conformal_scenario(seed: int) -> dict[str, object]:
    rng = np.random.default_rng(seed)
    noise_sd = 0.12
    cutoff = 0.60
    training_participants = tuple(f"train-p{i + 1}" for i in range(30))
    fit = _oracle_fit(
        noise_sd=noise_sd,
        training_participants=training_participants,
    )
    calibration, _ = _grouped_curves(
        rng=rng,
        participant_prefix="cal-p",
        n_participants=60,
        trials_per_participant=2,
        noise_sd=noise_sd,
        within_participant_rho=0.55,
    )
    calibrated = calibrate_sparse_fpca_partial_prediction_conformal(
        fit,
        calibration,
        history_cutoff=cutoff,
        prediction_grid=TARGET_GRID,
        alpha=ALPHA,
        group_column="participant_id",
    )

    targets, truth = _grouped_curves(
        rng=rng,
        participant_prefix="test-p",
        n_participants=180,
        trials_per_participant=2,
        noise_sd=noise_sd,
        within_participant_rho=0.55,
    )
    participant_success: dict[str, bool] = {
        participant: True
        for participant in targets.metadata["participant_id"].astype(str).unique()
    }
    curve_success: list[bool] = []
    for index, curve_id in enumerate(targets.curve_ids):
        curve = targets.subset([index])
        band = sparse_fpca_conformal_prediction_band(calibrated, curve)
        observed_future = truth[str(curve_id)][-TARGET_GRID.size :, 1]
        covered = bool(
            np.all(observed_future >= band.lower)
            and np.all(observed_future <= band.upper)
        )
        curve_success.append(covered)
        participant = str(targets.metadata.iloc[index]["participant_id"])
        participant_success[participant] = participant_success[participant] and covered

    # Deliberate missing-grid failure: replace 0.85 by 0.86 in one calibration curve.
    bad_times = list(calibration.time)
    bad_times[0] = bad_times[0].copy()
    bad_times[0][np.flatnonzero(bad_times[0] == 0.85)[0]] = 0.86
    order = np.argsort(bad_times[0])
    bad_times[0] = bad_times[0][order]
    bad_values = list(calibration.values)
    bad_values[0] = bad_values[0][order].copy()
    bad_calibration = IrregularTrajectorySet(
        time=tuple(bad_times),
        values=tuple(bad_values),
        curve_ids=calibration.curve_ids,
        dimension_names=calibration.dimension_names,
        metadata=calibration.metadata.reset_index(drop=True),
        coordinate_system=calibration.coordinate_system,
        time_unit=calibration.time_unit,
    )
    missing_grid_failure = None
    try:
        calibrate_sparse_fpca_partial_prediction_conformal(
            fit,
            bad_calibration,
            history_cutoff=cutoff,
            prediction_grid=TARGET_GRID,
            alpha=ALPHA,
            group_column="participant_id",
        )
    except Exception as exc:  # evidence captures exact guarded failure code
        missing_grid_failure = getattr(exc, "code", type(exc).__name__)

    leakage_failure = None
    overlapping = calibration.subset(list(range(calibration.n_curves)))
    overlap_ids = list(overlapping.curve_ids)
    overlap_ids[0] = fit.curve_ids[0]
    overlapping = IrregularTrajectorySet(
        time=overlapping.time,
        values=overlapping.values,
        curve_ids=tuple(overlap_ids),
        dimension_names=overlapping.dimension_names,
        metadata=overlapping.metadata.reset_index(drop=True),
        coordinate_system=overlapping.coordinate_system,
        time_unit=overlapping.time_unit,
    )
    try:
        calibrate_sparse_fpca_partial_prediction_conformal(
            fit,
            overlapping,
            history_cutoff=cutoff,
            prediction_grid=TARGET_GRID,
            alpha=ALPHA,
            group_column="participant_id",
        )
    except Exception as exc:
        leakage_failure = type(exc).__name__

    return {
        "seed": int(seed),
        "alpha": ALPHA,
        "n_calibration_participants": int(calibrated.n_calibration_units),
        "n_calibration_curves": int(calibrated.n_calibration_curves),
        "critical_value": float(calibrated.critical_value),
        "n_target_participants": int(len(participant_success)),
        "n_target_curves": int(len(curve_success)),
        "participant_level_simultaneous_coverage": float(
            np.mean(list(participant_success.values()))
        ),
        "curve_level_simultaneous_coverage": float(np.mean(curve_success)),
        "group_aggregation": calibrated.provenance["group_aggregation"],
        "continuous_domain_coverage_claimed": False,
        "latent_function_coverage_claimed": False,
        "raw_future_response_interpolation_performed": False,
        "missing_grid_failure": missing_grid_failure,
        "leakage_failure": leakage_failure,
    }


def run_validation() -> dict[str, object]:
    scenarios = [
        _oracle_conditional_scenario(seed=8101, noise_sd=0.05, cutoff=0.30),
        _oracle_conditional_scenario(seed=8101, noise_sd=0.05, cutoff=0.60),
        _oracle_conditional_scenario(seed=9101, noise_sd=0.20, cutoff=0.30),
        _oracle_conditional_scenario(seed=9101, noise_sd=0.20, cutoff=0.60),
    ]
    conformal = _grouped_conformal_scenario(seed=12031)
    conformal_replay = _grouped_conformal_scenario(seed=12031)

    by_noise = {}
    for noise_sd in (0.05, 0.20):
        subset = [row for row in scenarios if row["noise_sd"] == noise_sd]
        subset.sort(key=lambda row: row["history_cutoff"])
        by_noise[str(noise_sd)] = {
            "short_history_variance": subset[0]["mean_latent_conditional_variance"],
            "long_history_variance": subset[1]["mean_latent_conditional_variance"],
            "long_history_reduces_variance": bool(
                subset[1]["mean_latent_conditional_variance"]
                < subset[0]["mean_latent_conditional_variance"]
            ),
        }

    replay_passed = conformal == conformal_replay
    guards = {
        "all_conditional_standardized_sd_between_0_88_and_1_12": all(
            0.88 <= row["latent_standardized_error_sd"] <= 1.12
            and 0.88 <= row["observed_standardized_error_sd"] <= 1.12
            for row in scenarios
        ),
        "all_pointwise_95_coverage_between_0_92_and_0_98": all(
            0.92 <= row["latent_pointwise_95_coverage"] <= 0.98
            and 0.92 <= row["observed_pointwise_95_coverage"] <= 0.98
            for row in scenarios
        ),
        "longer_history_reduces_conditional_variance": all(
            entry["long_history_reduces_variance"] for entry in by_noise.values()
        ),
        "participant_conformal_coverage_at_least_0_84": (
            conformal["participant_level_simultaneous_coverage"] >= 0.84
        ),
        "participant_conformal_coverage_not_degenerate": (
            conformal["participant_level_simultaneous_coverage"] <= 0.99
        ),
        "missing_grid_fails_without_interpolation": (
            conformal["missing_grid_failure"]
            == "calibration_future_grid_observation_missing"
        ),
        "training_calibration_leakage_fails": (
            conformal["leakage_failure"] == "ValueError"
        ),
        "deterministic_replay": replay_passed,
    }
    passed = all(bool(value) for value in guards.values())
    return {
        "validation_passed": passed,
        "conditional_oracle_scenarios": scenarios,
        "history_information_ordering": by_noise,
        "grouped_split_conformal": conformal,
        "guards": guards,
        "deterministic_replay_passed": replay_passed,
        "prediction_target": "future_observed_measurements_on_declared_finite_grid_for_conformal_layer",
        "conditional_moments_target": "latent_future_trajectory_conditional_on_oracle_population",
        "continuous_domain_conformal_coverage_claimed": False,
        "latent_function_conformal_coverage_claimed": False,
        "raw_history_interpolation_performed": False,
        "raw_future_response_interpolation_performed": False,
        "population_estimation_uncertainty_propagated": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    evidence = run_validation()
    args.output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    if not evidence["validation_passed"]:
        raise SystemExit("sparse partial-prediction qualification failed")


if __name__ == "__main__":
    main()
