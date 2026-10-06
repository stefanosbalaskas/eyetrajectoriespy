"""Run 1.1 R3 end-to-end product analyses.

The harness uses deterministic realistic synthetic eye-tracking fixtures rather
than known-truth qualification simulators. Its purpose is product integration:
can a scientist move from supported inputs through the completed 1.1 sparse/
irregular APIs to tidy diagnostics and manuscript-ready reporting without
repository-private helpers?

All specialist 1.1 APIs are imported from their supported module-scoped
surfaces. Stable 1.0 APIs remain imported from the package root.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import eyetrajectoriespy as et
from eyetrajectoriespy import (
    IrregularTrajectorySet,
    capture_environment,
    fit_sparse_fpca,
    fit_sparse_mfpca,
    from_irregular_long_dataframe_native,
    sparse_fpca_score_frame,
    sparse_mfpca_reporting_text,
    sparse_mfpca_score_frame,
)
from eyetrajectoriespy.observation_process import (
    diagnose_observation_process,
    observation_process_data,
    observation_process_frame,
    observation_process_reporting_text,
)
from eyetrajectoriespy.sparse_bandwidth_selection import (
    select_sparse_fpca_bandwidths,
    sparse_fpca_bandwidth_selection_reporting_text,
)
from eyetrajectoriespy.sparse_multilevel import (
    fit_sparse_multilevel_fpca,
    sparse_multilevel_fpca_reporting_text,
)
from eyetrajectoriespy.sparse_multivariate_async import (
    fit_sparse_mfpca_async,
    sparse_mfpca_async_reporting_text,
    sparse_mfpca_async_score_frame,
)
from eyetrajectoriespy.sparse_multivariate_bandwidth_selection import (
    select_sparse_mfpca_bandwidths,
    sparse_mfpca_bandwidth_selection_reporting_text,
)
from eyetrajectoriespy.sparse_multivariate_score_uncertainty import (
    sparse_mfpca_score_uncertainty,
    sparse_mfpca_score_uncertainty_frame,
    sparse_mfpca_score_uncertainty_reporting_text,
)
from eyetrajectoriespy.sparse_partial_conformal import (
    calibrate_sparse_fpca_partial_prediction_conformal,
    sparse_fpca_conformal_band_frame,
    sparse_fpca_conformal_band_reporting_text,
    sparse_fpca_conformal_prediction_band,
)
from eyetrajectoriespy.sparse_partial_prediction import (
    sparse_fpca_partial_prediction_frame,
    sparse_fpca_partial_prediction_reporting_text,
    sparse_fpca_partial_trajectory_prediction,
)
from eyetrajectoriespy.sparse_score_uncertainty import (
    sparse_fpca_score_uncertainty,
    sparse_fpca_score_uncertainty_frame,
)
from eyetrajectoriespy.sparse_score_uncertainty_reporting import (
    sparse_fpca_score_uncertainty_reporting_text,
)


SCHEMA_VERSION = 1
SYNTHETIC_LABEL = "deterministic realistic synthetic gaze; not empirical human data"
NOISE_SD = 0.02
NOISE_VAR = NOISE_SD**2


def _json_default(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, set):
        return sorted(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=_json_default) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _save_frame(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _max_rss_kb() -> int | None:
    try:
        import resource
    except ImportError:
        return None
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def _timed(callable_obj):
    started = time.perf_counter()
    value = callable_obj()
    return value, float(time.perf_counter() - started)


def _subset_participants(
    trajectories: IrregularTrajectorySet,
    participants: set[str],
) -> IrregularTrajectorySet:
    labels = trajectories.metadata["participant_id"].astype(str).to_numpy()
    indices = np.flatnonzero(np.isin(labels, sorted(participants)))
    return trajectories.subset(indices)


def _univariate_candidate_fixture() -> pd.DataFrame:
    rng = np.random.default_rng(2026100601)
    candidate_times = np.round(np.linspace(0.0, 2.0, 21), 10)
    future_anchors = {1.6, 1.8, 2.0}
    rows: list[dict[str, Any]] = []

    for participant_index in range(1, 32):
        participant = f"U{participant_index:02d}"
        participant_offset = rng.normal(0.0, 0.025)
        participant_mode = rng.normal(0.0, 1.0)
        participant_mode2 = rng.normal(0.0, 1.0)

        for trial_id, condition in ((1, "baseline"), (2, "visual-search")):
            search = float(condition == "visual-search")
            trial_shift = rng.normal(0.0, 0.012)
            latent_x = (
                0.48
                + participant_offset
                + trial_shift
                + 0.040 * candidate_times
                + 0.105 * participant_mode * np.sin(np.pi * candidate_times / 2.0)
                + 0.055 * participant_mode2 * np.sin(np.pi * candidate_times)
                + search * 0.035 * np.cos(1.5 * np.pi * candidate_times)
            )
            latent_y = (
                0.52
                - 0.020 * candidate_times
                + 0.060 * participant_mode * np.cos(np.pi * candidate_times / 2.0)
                - 0.040 * participant_mode2 * np.sin(np.pi * candidate_times)
                + search * 0.025 * np.sin(1.5 * np.pi * candidate_times)
            )
            x_obs = np.clip(
                latent_x + rng.normal(0.0, NOISE_SD, size=candidate_times.size),
                0.02,
                0.98,
            )
            y_obs = np.clip(
                latent_y + rng.normal(0.0, NOISE_SD, size=candidate_times.size),
                0.02,
                0.98,
            )

            middle = ((candidate_times >= 0.7) & (candidate_times <= 1.3)).astype(float)
            late = (candidate_times >= 1.4).astype(float)
            logits = 2.25 - 0.75 * middle - 0.35 * search + 0.18 * late
            probability = 1.0 / (1.0 + np.exp(-logits))
            retained = rng.random(candidate_times.size) < probability
            retained[0] = True
            retained[-1] = True
            if participant_index >= 21:
                for idx, t in enumerate(candidate_times):
                    if float(t) in future_anchors:
                        retained[idx] = True
            if retained.sum() < 10:
                missing = np.flatnonzero(~retained)
                retained[missing[: 10 - int(retained.sum())]] = True

            for idx, t in enumerate(candidate_times):
                task_phase = "orient" if t < 0.7 else ("inspect" if t <= 1.3 else "decision")
                rows.append(
                    {
                        "participant_id": participant,
                        "trial_id": int(trial_id),
                        "curve_id": f"{participant}|{trial_id}",
                        "condition": condition,
                        "task_phase": task_phase,
                        "time_s": float(t),
                        "retained": int(retained[idx]),
                        "x": float(x_obs[idx]) if retained[idx] else np.nan,
                        "y": float(y_obs[idx]) if retained[idx] else np.nan,
                    }
                )

    return pd.DataFrame(rows)


def _univariate_irregular(candidate: pd.DataFrame) -> IrregularTrajectorySet:
    retained = candidate.loc[
        candidate["retained"].eq(1),
        ["participant_id", "trial_id", "condition", "time_s", "x"],
    ].copy()
    return from_irregular_long_dataframe_native(
        retained,
        curve_columns=("participant_id", "trial_id"),
        time_column="time_s",
        value_columns=("x",),
        metadata_columns=("condition",),
        coordinate_system="normalized_screen",
        time_unit="s",
        provenance={
            "r3_fixture": "univariate_candidate_retention",
            "synthetic": True,
            "known_truth_qualification_simulator": False,
        },
    )


def run_univariate(output: Path) -> dict[str, Any]:
    route = output / "univariate-sparse"
    route.mkdir(parents=True, exist_ok=True)
    candidate = _univariate_candidate_fixture()
    candidate_path = route / "candidate_samples.csv"
    _save_frame(candidate, candidate_path)

    process = observation_process_data(
        candidate,
        curve_column="curve_id",
        time_column="time_s",
        observed_column="retained",
        group_column="participant_id",
        candidate_predictors=("condition", "task_phase"),
        predictor_sources={"condition": "design", "task_phase": "design"},
        coordinate_columns=("x", "y"),
        time_unit="s",
        coordinate_system="normalized_screen",
        provenance={"r3": True, "synthetic": True},
    )
    diagnostic, observation_seconds = _timed(
        lambda: diagnose_observation_process(
            process,
            predictors=("condition", "task_phase"),
            history_predictors=(
                "previous_observed_x",
                "previous_observed_speed",
                "time_since_last_observed",
            ),
            risk_set="all_candidates",
            time_basis="linear",
            time_bins=4,
            association_bins=4,
        )
    )
    for table in (
        "global",
        "curves",
        "groups",
        "time",
        "support",
        "associations",
        "profiles",
        "failures",
    ):
        _save_frame(
            observation_process_frame(diagnostic, table=table),
            route / f"observation-{table}.csv",
        )
    _write_text(
        route / "observation-reporting.txt",
        observation_process_reporting_text(diagnostic),
    )

    irregular = _univariate_irregular(candidate)
    all_participants = irregular.metadata["participant_id"].astype(str).to_numpy()
    proper_ids = {f"U{i:02d}" for i in range(1, 21)}
    calibration_ids = {f"U{i:02d}" for i in range(21, 31)}
    target_id = "U31"
    proper = _subset_participants(irregular, proper_ids)
    calibration = _subset_participants(irregular, calibration_ids)
    target_indices = np.flatnonzero(
        (all_participants == target_id)
        & (irregular.metadata["trial_id"].astype(int).to_numpy() == 1)
    )
    target = irregular.subset(target_indices[:1])

    evaluation_grid = np.linspace(0.0, 2.0, 41)
    selection, selection_seconds = _timed(
        lambda: select_sparse_fpca_bandwidths(
            proper,
            dimension="x",
            evaluation_grid=evaluation_grid,
            mean_bandwidths=(0.28, 0.36),
            covariance_bandwidths=(0.42, 0.54),
            noise_variance_method="fixed",
            measurement_error_variance=NOISE_VAR,
            n_splits=4,
            resampling_unit="group",
            group_column="participant_id",
            random_state=2026,
            psd_action="project",
            failure_action="retain",
        )
    )
    _save_frame(selection.assignments, route / "bandwidth-assignments.csv")
    _save_frame(selection.candidates, route / "bandwidth-declared-candidates.csv")
    _save_frame(selection.candidate_summary, route / "bandwidth-candidates.csv")
    _save_frame(selection.fold_results, route / "bandwidth-folds.csv")
    _save_frame(selection.curve_losses, route / "bandwidth-heldout-curves.csv")
    _write_text(
        route / "bandwidth-reporting.txt",
        sparse_fpca_bandwidth_selection_reporting_text(selection),
    )
    chosen = selection.selected_bandwidths
    if chosen is None:
        raise RuntimeError("univariate R3 bandwidth selector returned no eligible candidate")

    fit, fit_seconds = _timed(
        lambda: fit_sparse_fpca(
            proper,
            dimension="x",
            n_components=2,
            evaluation_grid=evaluation_grid,
            mean_bandwidth=float(chosen["mean_bandwidth"]),
            covariance_bandwidth=float(chosen["covariance_bandwidth"]),
            noise_variance_method="fixed",
            measurement_error_variance=NOISE_VAR,
            psd_action="project",
            score_failure_action="retain_nan",
        )
    )
    _save_frame(sparse_fpca_score_frame(fit), route / "pace-scores.csv")

    uncertainty, uncertainty_seconds = _timed(
        lambda: sparse_fpca_score_uncertainty(
            fit,
            proper,
            failure_action="retain_nan",
        )
    )
    _save_frame(
        sparse_fpca_score_uncertainty_frame(uncertainty),
        route / "pace-score-uncertainty.csv",
    )
    _write_text(
        route / "pace-score-uncertainty-reporting.txt",
        sparse_fpca_score_uncertainty_reporting_text(uncertainty),
    )

    prediction_grid = np.array([1.6, 1.8, 2.0])
    prediction, prediction_seconds = _timed(
        lambda: sparse_fpca_partial_trajectory_prediction(
            fit,
            target,
            history_cutoff=1.2,
            prediction_grid=prediction_grid,
        )
    )
    _save_frame(
        sparse_fpca_partial_prediction_frame(prediction),
        route / "partial-prediction.csv",
    )
    _write_text(
        route / "partial-prediction-reporting.txt",
        sparse_fpca_partial_prediction_reporting_text(prediction),
    )

    conformal, conformal_seconds = _timed(
        lambda: calibrate_sparse_fpca_partial_prediction_conformal(
            fit,
            calibration,
            history_cutoff=1.2,
            prediction_grid=prediction_grid,
            alpha=0.10,
            group_column="participant_id",
        )
    )
    band = sparse_fpca_conformal_prediction_band(conformal, target)
    _save_frame(sparse_fpca_conformal_band_frame(band), route / "conformal-band.csv")
    _save_frame(conformal.curve_scores, route / "conformal-curve-scores.csv")
    _write_text(
        route / "conformal-band-reporting.txt",
        sparse_fpca_conformal_band_reporting_text(band),
    )

    fit_status = fit.score_diagnostics["status_code"].astype(str)
    uncertainty_status = uncertainty.diagnostics["status_code"].astype(str)
    global_row = observation_process_frame(diagnostic, table="global").iloc[0]
    friction = [
        {
            "severity": "low",
            "release_blocking": False,
            "surface": "bandwidth selection -> fit",
            "observation": "The selector intentionally does not fit automatically; selected numeric bandwidths must be transferred explicitly to fit_sparse_fpca().",
        },
        {
            "severity": "low",
            "release_blocking": False,
            "surface": "conformal calibration",
            "observation": "Calibration requires actual retained observations at every declared future-grid timestamp; the fixture declares three acquisition anchors rather than interpolating responses.",
        },
        {
            "severity": "low",
            "release_blocking": False,
            "surface": "score uncertainty reporting",
            "observation": "The uncertainty estimator/frame and reporting helper live in companion supported modules, adding one discoverability step but no repository-private knowledge.",
        },
    ]
    evidence = {
        "route": "univariate_sparse_irregular_end_to_end",
        "input_kind": SYNTHETIC_LABEL,
        "empirical_human_data": False,
        "public_supported_api_only": True,
        "known_truth_qualification_simulator_used": False,
        "candidate_rows": int(len(candidate)),
        "candidate_missing_fraction": float(global_row["missing_fraction"]),
        "candidate_curve_count": int(global_row["curve_count"]),
        "participant_count": int(candidate["participant_id"].nunique()),
        "proper_training_participants": len(proper_ids),
        "proper_training_curves": int(proper.n_curves),
        "calibration_participants": len(calibration_ids),
        "calibration_curves": int(calibration.n_curves),
        "target_curve_id": str(target.curve_ids[0]),
        "selected_bandwidths": dict(chosen),
        "bandwidth_eligible_candidates": int(selection.candidate_summary["eligible"].sum()),
        "pace_score_failures": int((fit_status != "ok").sum()),
        "conditional_uncertainty_failures": int((uncertainty_status != "ok").sum()),
        "partial_prediction_history_count": int(prediction.n_history),
        "future_grid": prediction_grid.tolist(),
        "conformal_alpha": float(conformal.alpha),
        "conformal_calibration_units": int(len(conformal.calibration_unit_ids)),
        "conformal_critical_value": float(conformal.critical_value),
        "raw_interpolation_performed": False,
        "runtime_seconds": {
            "observation_process": observation_seconds,
            "bandwidth_selection": selection_seconds,
            "fit_sparse_fpca": fit_seconds,
            "score_uncertainty": uncertainty_seconds,
            "partial_prediction": prediction_seconds,
            "conformal_calibration": conformal_seconds,
        },
        "input_sha256": _sha256(candidate_path),
        "friction": friction,
    }
    _write_json(route / "evidence.json", evidence)
    return evidence


def _planar_paired_fixture() -> pd.DataFrame:
    rng = np.random.default_rng(2026100602)
    rows: list[dict[str, Any]] = []
    for participant_index in range(1, 29):
        participant = f"P{participant_index:02d}"
        n_samples = int(rng.integers(12, 17))
        interior = np.sort(rng.uniform(0.04, 1.96, n_samples - 2))
        time_s = np.r_[0.0, interior, 2.0]
        z1, z2, z3 = rng.normal(size=3)
        x = (
            0.47
            + 0.025 * time_s
            + 0.10 * z1 * np.sin(np.pi * time_s / 2.0)
            + 0.055 * z2 * np.sin(np.pi * time_s)
            + 0.025 * z3 * np.cos(1.5 * np.pi * time_s)
        )
        y = (
            0.53
            - 0.020 * time_s
            + 0.085 * z1 * np.cos(np.pi * time_s / 2.0)
            - 0.060 * z2 * np.sin(np.pi * time_s)
            + 0.030 * z3 * np.sin(1.5 * np.pi * time_s)
        )
        observed = np.column_stack((x, y)) + rng.normal(
            0.0, NOISE_SD, size=(time_s.size, 2)
        )
        observed = np.clip(observed, 0.02, 0.98)
        for t, (x_value, y_value) in zip(time_s, observed, strict=True):
            rows.append(
                {
                    "participant_id": participant,
                    "trial_id": 1,
                    "condition": "free-view",
                    "time_s": float(t),
                    "x": float(x_value),
                    "y": float(y_value),
                }
            )
    return pd.DataFrame(rows)


def _planar_async_fixture() -> pd.DataFrame:
    rng = np.random.default_rng(2026100603)
    rows: list[dict[str, Any]] = []
    for participant_index in range(1, 29):
        participant = f"A{participant_index:02d}"
        z1, z2, z3 = rng.normal(size=3)
        nx = int(rng.integers(10, 14))
        ny = int(rng.integers(10, 14))
        x_time = np.round(
            np.r_[0.0, np.sort(rng.uniform(0.03, 1.97, nx - 2)), 2.0], 8
        )
        y_time = np.round(
            np.r_[0.0, np.sort(rng.uniform(0.03, 1.97, ny - 2)), 2.0], 8
        )
        union = np.unique(np.r_[x_time, y_time])

        def latent_x(t):
            return (
                0.47
                + 0.025 * t
                + 0.10 * z1 * np.sin(np.pi * t / 2.0)
                + 0.055 * z2 * np.sin(np.pi * t)
                + 0.025 * z3 * np.cos(1.5 * np.pi * t)
            )

        def latent_y(t):
            return (
                0.53
                - 0.020 * t
                + 0.085 * z1 * np.cos(np.pi * t / 2.0)
                - 0.060 * z2 * np.sin(np.pi * t)
                + 0.030 * z3 * np.sin(1.5 * np.pi * t)
            )

        x_lookup = {
            float(t): float(
                np.clip(latent_x(t) + rng.normal(0.0, NOISE_SD), 0.02, 0.98)
            )
            for t in x_time
        }
        y_lookup = {
            float(t): float(
                np.clip(latent_y(t) + rng.normal(0.0, NOISE_SD), 0.02, 0.98)
            )
            for t in y_time
        }
        for t in union:
            rows.append(
                {
                    "participant_id": participant,
                    "trial_id": 1,
                    "condition": "free-view",
                    "time_s": float(t),
                    "x": x_lookup.get(float(t), np.nan),
                    "y": y_lookup.get(float(t), np.nan),
                }
            )
    return pd.DataFrame(rows)


def run_planar(output: Path) -> dict[str, Any]:
    route = output / "planar-sparse"
    route.mkdir(parents=True, exist_ok=True)
    paired_frame = _planar_paired_fixture()
    paired_path = route / "paired-input.csv"
    _save_frame(paired_frame, paired_path)
    paired = from_irregular_long_dataframe_native(
        paired_frame,
        curve_columns=("participant_id", "trial_id"),
        time_column="time_s",
        value_columns=("x", "y"),
        metadata_columns=("condition",),
        coordinate_system="normalized_screen",
        time_unit="s",
        provenance={
            "r3_fixture": "paired_planar_sparse",
            "synthetic": True,
            "raw_interpolation": False,
        },
    )

    evaluation_grid = np.linspace(0.0, 2.0, 41)
    selection, selection_seconds = _timed(
        lambda: select_sparse_mfpca_bandwidths(
            paired,
            dimensions=("x", "y"),
            evaluation_grid=evaluation_grid,
            mean_bandwidths=(0.28, 0.36),
            covariance_bandwidths=(0.44, 0.56),
            measurement_error="diagonal",
            measurement_error_variance=(NOISE_VAR, NOISE_VAR),
            n_splits=4,
            resampling_unit="curve",
            random_state=2026,
            psd_action="project",
            failure_action="retain",
        )
    )
    _save_frame(selection.assignments, route / "bandwidth-assignments.csv")
    _save_frame(selection.candidates, route / "bandwidth-declared-candidates.csv")
    _save_frame(selection.candidate_summary, route / "bandwidth-candidates.csv")
    _save_frame(selection.fold_results, route / "bandwidth-folds.csv")
    _save_frame(selection.curve_losses, route / "bandwidth-heldout-curves.csv")
    _write_text(
        route / "bandwidth-reporting.txt",
        sparse_mfpca_bandwidth_selection_reporting_text(selection),
    )
    chosen = selection.selected_bandwidths
    if chosen is None:
        raise RuntimeError("planar R3 bandwidth selector returned no eligible candidate")

    fit, fit_seconds = _timed(
        lambda: fit_sparse_mfpca(
            paired,
            dimensions=("x", "y"),
            n_components=2,
            evaluation_grid=evaluation_grid,
            mean_bandwidth=float(chosen["mean_bandwidth"]),
            covariance_bandwidth=float(chosen["covariance_bandwidth"]),
            measurement_error="diagonal",
            measurement_error_variance=(NOISE_VAR, NOISE_VAR),
            psd_action="project",
            score_failure_action="retain_nan",
        )
    )
    _save_frame(sparse_mfpca_score_frame(fit), route / "joint-pace-scores.csv")
    _write_text(route / "joint-pace-reporting.txt", sparse_mfpca_reporting_text(fit))

    uncertainty, uncertainty_seconds = _timed(
        lambda: sparse_mfpca_score_uncertainty(
            fit,
            paired,
            failure_action="retain_nan",
        )
    )
    _save_frame(
        sparse_mfpca_score_uncertainty_frame(uncertainty),
        route / "joint-pace-score-uncertainty.csv",
    )
    _write_text(
        route / "joint-pace-score-uncertainty-reporting.txt",
        sparse_mfpca_score_uncertainty_reporting_text(uncertainty),
    )

    async_frame = _planar_async_fixture()
    async_path = route / "async-input.csv"
    _save_frame(async_frame, async_path)
    asynchronous = from_irregular_long_dataframe_native(
        async_frame,
        curve_columns=("participant_id", "trial_id"),
        time_column="time_s",
        value_columns=("x", "y"),
        metadata_columns=("condition",),
        coordinate_system="normalized_screen",
        time_unit="s",
        provenance={
            "r3_fixture": "asynchronous_planar_sparse",
            "synthetic": True,
            "representation": "exact_union_of_native_coordinate_timestamps",
            "raw_interpolation": False,
            "nearest_neighbour_synchronization": False,
        },
    )
    async_fit, async_seconds = _timed(
        lambda: fit_sparse_mfpca_async(
            asynchronous,
            dimensions=("x", "y"),
            n_components=2,
            evaluation_grid=evaluation_grid,
            mean_bandwidth=0.34,
            covariance_bandwidth=0.52,
            measurement_error="diagonal",
            measurement_error_variance=(NOISE_VAR, NOISE_VAR),
            psd_action="project",
            score_failure_action="retain_nan",
        )
    )
    _save_frame(
        sparse_mfpca_async_score_frame(async_fit),
        route / "async-joint-pace-scores.csv",
    )
    _write_text(route / "async-reporting.txt", sparse_mfpca_async_reporting_text(async_fit))

    paired_status = fit.score_diagnostics["status_code"].astype(str)
    uncertainty_status = uncertainty.diagnostics["status_code"].astype(str)
    async_status = async_fit.score_diagnostics["status_code"].astype(str)
    x_only = int((async_frame["x"].notna() & async_frame["y"].isna()).sum())
    y_only = int((async_frame["x"].isna() & async_frame["y"].notna()).sum())
    simultaneous = int((async_frame["x"].notna() & async_frame["y"].notna()).sum())
    friction = [
        {
            "severity": "low",
            "release_blocking": False,
            "surface": "paired bandwidth selection -> paired fit",
            "observation": "The paired selector and fitter remain separate by design, so selected values are transferred explicitly.",
        },
        {
            "severity": "moderate",
            "release_blocking": False,
            "surface": "asynchronous bandwidth choice",
            "observation": "There is no qualified asynchronous bandwidth selector; R3 uses declared manual bandwidths and does not reuse paired CV as if it validated the asynchronous observation contract.",
        },
        {
            "severity": "low",
            "release_blocking": False,
            "surface": "paired versus asynchronous route choice",
            "observation": "Scientists must choose the observation contract explicitly; this is scientifically appropriate but requires reading the representation guidance before fitting.",
        },
    ]
    evidence = {
        "route": "paired_and_asynchronous_sparse_planar_end_to_end",
        "input_kind": SYNTHETIC_LABEL,
        "empirical_human_data": False,
        "public_supported_api_only": True,
        "known_truth_qualification_simulator_used": False,
        "paired_curves": int(paired.n_curves),
        "paired_selected_bandwidths": dict(chosen),
        "paired_eligible_candidates": int(selection.candidate_summary["eligible"].sum()),
        "paired_score_failures": int((paired_status != "ok").sum()),
        "paired_uncertainty_failures": int((uncertainty_status != "ok").sum()),
        "asynchronous_curves": int(asynchronous.n_curves),
        "asynchronous_x_only_rows": x_only,
        "asynchronous_y_only_rows": y_only,
        "asynchronous_simultaneous_rows": simultaneous,
        "asynchronous_score_failures": int((async_status != "ok").sum()),
        "raw_interpolation_performed": False,
        "nearest_neighbour_synchronization_performed": False,
        "time_binning_performed": False,
        "runtime_seconds": {
            "paired_bandwidth_selection": selection_seconds,
            "paired_fit": fit_seconds,
            "paired_score_uncertainty": uncertainty_seconds,
            "asynchronous_fit": async_seconds,
        },
        "input_sha256": {
            "paired": _sha256(paired_path),
            "asynchronous": _sha256(async_path),
        },
        "friction": friction,
    }
    _write_json(route / "evidence.json", evidence)
    return evidence


def _multilevel_fixture() -> pd.DataFrame:
    rng = np.random.default_rng(2026100604)
    rows: list[dict[str, Any]] = []
    for participant_index in range(1, 17):
        participant = f"M{participant_index:02d}"
        n_trials = 3 if participant_index <= 6 else (2 if participant_index <= 12 else 1)
        u1, u2 = rng.normal(size=2)
        for trial_id in range(1, n_trials + 1):
            n_samples = int(rng.integers(11, 16))
            interior = np.sort(rng.uniform(0.03, 1.97, n_samples - 2))
            time_s = np.r_[0.0, interior, 2.0]
            v1, v2 = rng.normal(size=2)
            mean = 0.50 + 0.025 * time_s
            participant_signal = (
                0.085 * u1 * np.sin(np.pi * time_s / 2.0)
                + 0.060 * u2 * np.cos(np.pi * time_s / 2.0)
            )
            trial_signal = (
                0.050 * v1 * np.sin(np.pi * time_s)
                + 0.035 * v2 * np.cos(np.pi * time_s)
            )
            x = np.clip(
                mean
                + participant_signal
                + trial_signal
                + rng.normal(0.0, NOISE_SD, size=time_s.size),
                0.02,
                0.98,
            )
            for t, value in zip(time_s, x, strict=True):
                rows.append(
                    {
                        "participant_id": participant,
                        "trial_id": int(trial_id),
                        "session": "single-session",
                        "time_s": float(t),
                        "x": float(value),
                    }
                )
    return pd.DataFrame(rows)


def run_multilevel(output: Path) -> dict[str, Any]:
    route = output / "repeated-trial-sparse"
    route.mkdir(parents=True, exist_ok=True)
    frame = _multilevel_fixture()
    input_path = route / "input-long.csv"
    _save_frame(frame, input_path)
    trajectories = from_irregular_long_dataframe_native(
        frame,
        curve_columns=("participant_id", "trial_id"),
        time_column="time_s",
        value_columns=("x",),
        metadata_columns=("session",),
        coordinate_system="normalized_screen",
        time_unit="s",
        provenance={
            "r3_fixture": "unequal_sparse_repeated_trials",
            "synthetic": True,
            "fixed_effects_present": False,
        },
    )

    fit, fit_seconds = _timed(
        lambda: fit_sparse_multilevel_fpca(
            trajectories,
            dimension="x",
            participant_column="participant_id",
            participant_components=2,
            trial_components=2,
            evaluation_grid=np.linspace(0.05, 1.95, 31),
            mean_bandwidth=0.32,
            total_covariance_bandwidth=0.44,
            between_covariance_bandwidth=0.50,
            analysis_support_action="restrict",
            weighting="observation",
            noise_variance_method="fixed",
            measurement_error_variance=NOISE_VAR,
            psd_action="project",
            score_failure_action="retain_nan",
        )
    )
    _save_frame(fit.participant_scores, route / "participant-scores.csv")
    _save_frame(fit.trial_scores, route / "trial-scores.csv")
    _save_frame(fit.score_diagnostics, route / "blup-diagnostics.csv")
    _write_text(route / "reporting.txt", sparse_multilevel_fpca_reporting_text(fit))
    _write_json(route / "covariance-diagnostics.json", fit.covariance_diagnostics)
    _write_json(route / "support-diagnostics.json", fit.support_diagnostics)

    trial_counts = (
        trajectories.metadata.groupby("participant_id", sort=True)["trial_id"]
        .nunique()
        .astype(int)
    )
    score_status = fit.score_diagnostics["status_code"].astype(str)
    friction = [
        {
            "severity": "moderate",
            "release_blocking": False,
            "surface": "multilevel bandwidth choice",
            "observation": "The sparse multilevel route has no dedicated qualified bandwidth selector; mean/total/between bandwidths remain explicit analyst inputs.",
        },
        {
            "severity": "low",
            "release_blocking": False,
            "surface": "diagnostic export",
            "observation": "Participant/trial score tables are tidy, but covariance/support diagnostics are mappings rather than a single convenience frame; R3 exports them directly to JSON.",
        },
        {
            "severity": "low",
            "release_blocking": False,
            "surface": "fixed functional effects boundary",
            "observation": "The fitter correctly does not absorb task/visit fixed effects. R3 uses a one-session no-fixed-effect fixture; applied users must stratify or remove such effects upstream.",
        },
    ]
    evidence = {
        "route": "sparse_repeated_trial_multilevel_fpca_end_to_end",
        "input_kind": SYNTHETIC_LABEL,
        "empirical_human_data": False,
        "public_supported_api_only": True,
        "known_truth_qualification_simulator_used": False,
        "participant_count": int(trial_counts.size),
        "trial_count": int(trajectories.n_curves),
        "repeated_participants": int((trial_counts >= 2).sum()),
        "single_trial_participants": int((trial_counts == 1).sum()),
        "trial_count_min": int(trial_counts.min()),
        "trial_count_max": int(trial_counts.max()),
        "participant_score_rows": int(len(fit.participant_scores)),
        "trial_score_rows": int(len(fit.trial_scores)),
        "blup_failures": int((score_status != "ok").sum()),
        "between_psd_action": fit.covariance_diagnostics["between"]["applied_action"],
        "within_psd_action": fit.covariance_diagnostics["within"]["applied_action"],
        "raw_interpolation_performed": False,
        "runtime_seconds": {"fit_sparse_multilevel_fpca": fit_seconds},
        "input_sha256": _sha256(input_path),
        "friction": friction,
    }
    _write_json(route / "evidence.json", evidence)
    return evidence


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("build/one-dot-one-product-analyses"),
    )
    parser.add_argument(
        "--source-commit",
        default=os.environ.get("SOURCE_COMMIT") or os.environ.get("GITHUB_SHA") or "unknown",
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    started = time.perf_counter()
    univariate = run_univariate(args.output_dir)
    planar = run_planar(args.output_dir)
    multilevel = run_multilevel(args.output_dir)
    elapsed = float(time.perf_counter() - started)

    friction = (
        [{"route": "univariate", **entry} for entry in univariate["friction"]]
        + [{"route": "planar", **entry} for entry in planar["friction"]]
        + [{"route": "multilevel", **entry} for entry in multilevel["friction"]]
    )
    _save_frame(pd.DataFrame(friction), args.output_dir / "product-friction-ledger.csv")
    _write_json(args.output_dir / "environment.json", capture_environment())
    summary = {
        "schema_version": SCHEMA_VERSION,
        "programme": "1.1-r3-canonical-end-to-end-product-analyses",
        "source_commit": str(args.source_commit),
        "package_version": str(et.__version__),
        "input_kind": SYNTHETIC_LABEL,
        "empirical_human_data": False,
        "known_truth_qualification_simulator_used": False,
        "public_supported_api_only": True,
        "routes": {
            "univariate": univariate,
            "planar": planar,
            "multilevel": multilevel,
        },
        "product_friction": friction,
        "release_blocking_friction_count": int(
            sum(bool(item["release_blocking"]) for item in friction)
        ),
        "wall_clock_seconds": elapsed,
        "max_rss_kb_linux_runner": _max_rss_kb(),
        "memory_scope": "process max RSS on Linux when available; not a method benchmark and not compared to package qualification thresholds",
    }
    _write_json(args.output_dir / "summary.json", summary)

    print(
        json.dumps(
            {
                "r3": "ok",
                "source_commit": summary["source_commit"],
                "package_version": summary["package_version"],
                "routes": {
                    "univariate": {
                        "missing_fraction": univariate["candidate_missing_fraction"],
                        "selected_bandwidths": univariate["selected_bandwidths"],
                        "score_failures": univariate["pace_score_failures"],
                        "uncertainty_failures": univariate["conditional_uncertainty_failures"],
                        "conformal_units": univariate["conformal_calibration_units"],
                    },
                    "planar": {
                        "selected_bandwidths": planar["paired_selected_bandwidths"],
                        "paired_score_failures": planar["paired_score_failures"],
                        "async_score_failures": planar["asynchronous_score_failures"],
                        "async_x_only_rows": planar["asynchronous_x_only_rows"],
                        "async_y_only_rows": planar["asynchronous_y_only_rows"],
                    },
                    "multilevel": {
                        "participants": multilevel["participant_count"],
                        "trials": multilevel["trial_count"],
                        "single_trial_participants": multilevel["single_trial_participants"],
                        "blup_failures": multilevel["blup_failures"],
                    },
                },
                "release_blocking_friction_count": summary["release_blocking_friction_count"],
                "wall_clock_seconds": summary["wall_clock_seconds"],
                "max_rss_kb_linux_runner": summary["max_rss_kb_linux_runner"],
            },
            sort_keys=True,
            default=_json_default,
        )
    )


if __name__ == "__main__":
    main()
