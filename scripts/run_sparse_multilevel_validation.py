#!/usr/bin/env python
"""Known-truth qualification for native sparse multilevel FPCA.

The workflow targets hierarchical covariance/eigenspace and conditional BLUP
score recovery under declared exchangeable repeated-trial designs. It does not
claim universal recovery or propagate population-estimation uncertainty into
conditional score uncertainty.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from eyetrajectoriespy._sparse_native import SparseNativeError
from eyetrajectoriespy.fpca import functional_trapezoid_weights
from eyetrajectoriespy.sparse_multilevel import fit_sparse_multilevel_fpca
from eyetrajectoriespy.types import IrregularTrajectorySet


@dataclass(frozen=True)
class HierarchicalTruth:
    participant_scores: dict[str, float]
    trial_scores: dict[str, float]
    trial_counts: dict[str, int]
    noise_sd: float


def _mean(time):
    time = np.asarray(time, dtype=float)
    return 0.20 + 0.10 * time


def _between_mode(time):
    time = np.asarray(time, dtype=float)
    return np.sqrt(2.0) * np.sin(np.pi * time)


def _within_mode(time):
    time = np.asarray(time, dtype=float)
    return np.sqrt(2.0) * np.sin(2.0 * np.pi * time)


def _trial_count(participant, n_participants, design):
    if design == "balanced":
        return 3
    # Deliberately unequal: roughly one sixth single-trial, then a mixture of
    # two and three trials. Single-trial participants remain valid scoring
    # units but do not identify the between covariance.
    if participant < max(1, n_participants // 6):
        return 1
    return 2 if participant % 2 == 0 else 3


def _simulate(*, n_participants, sample_range, noise_sd, design, seed):
    rng = np.random.default_rng(seed)
    times = []
    values = []
    curve_ids = []
    participant_ids = []
    participant_truth = {}
    trial_truth = {}
    trial_counts = {}

    for participant_index in range(n_participants):
        participant_id = f"p{participant_index:03d}"
        participant_score = float(rng.normal(0.0, 1.0))
        participant_truth[participant_id] = participant_score
        count = _trial_count(participant_index, n_participants, design)
        trial_counts[participant_id] = count
        for trial_index in range(count):
            curve_id = f"{participant_id}_t{trial_index:02d}"
            trial_score = float(rng.normal(0.0, np.sqrt(0.45)))
            trial_truth[curve_id] = trial_score
            n_samples = int(rng.integers(sample_range[0], sample_range[1] + 1))
            time = np.sort(rng.uniform(0.0, 1.0, size=n_samples))
            observed = (
                _mean(time)
                + participant_score * _between_mode(time)
                + trial_score * _within_mode(time)
                + rng.normal(0.0, noise_sd, size=n_samples)
            )
            times.append(time)
            values.append(observed[:, None])
            curve_ids.append(curve_id)
            participant_ids.append(participant_id)

    trajectories = IrregularTrajectorySet(
        time=tuple(times),
        values=tuple(values),
        curve_ids=tuple(curve_ids),
        dimension_names=("x",),
        metadata=pd.DataFrame({"participant_id": participant_ids}),
        coordinate_system="normalized",
        time_unit="normalized",
        provenance={
            "simulation": "known_truth_sparse_multilevel",
            "design": design,
            "seed": seed,
        },
    )
    truth = HierarchicalTruth(
        participant_scores=participant_truth,
        trial_scores=trial_truth,
        trial_counts=trial_counts,
        noise_sd=float(noise_sd),
    )
    return trajectories, truth


def _weighted_similarity(estimated, truth, grid):
    weights = functional_trapezoid_weights(grid)
    estimated = np.asarray(estimated, dtype=float)
    truth = np.asarray(truth, dtype=float)
    numerator = float(np.sum(weights * estimated * truth))
    denominator = float(
        np.sqrt(np.sum(weights * estimated**2) * np.sum(weights * truth**2))
    )
    return abs(numerator / denominator)


def _relative_rmse(estimated, truth):
    estimated = np.asarray(estimated, dtype=float)
    truth = np.asarray(truth, dtype=float)
    return float(
        np.sqrt(np.mean((estimated - truth) ** 2))
        / max(np.sqrt(np.mean(truth**2)), np.finfo(float).eps)
    )


def _absolute_correlation(estimated, truth):
    estimated = np.asarray(estimated, dtype=float)
    truth = np.asarray(truth, dtype=float)
    if estimated.size < 3 or np.std(estimated) == 0 or np.std(truth) == 0:
        return float("nan")
    return abs(float(np.corrcoef(estimated, truth)[0, 1]))


def _fit_scenario(name, *, n_participants, sample_range, noise_sd, design, seed):
    trajectories, truth = _simulate(
        n_participants=n_participants,
        sample_range=sample_range,
        noise_sd=noise_sd,
        design=design,
        seed=seed,
    )
    grid = np.linspace(0.08, 0.92, 29)
    result = fit_sparse_multilevel_fpca(
        trajectories,
        dimension="x",
        participant_column="participant_id",
        participant_components=1,
        trial_components=1,
        evaluation_grid=grid,
        mean_bandwidth=0.28,
        total_covariance_bandwidth=0.34,
        between_covariance_bandwidth=0.38,
        analysis_support_action="restrict",
        weighting="observation",
        noise_variance_method="fixed",
        measurement_error_variance=noise_sd**2,
        psd_action="project",
        score_ridge=1e-8,
        score_failure_action="error",
    )

    between_truth_mode = _between_mode(grid)
    within_truth_mode = _within_mode(grid)
    between_truth_covariance = np.outer(between_truth_mode, between_truth_mode)
    within_truth_covariance = 0.45 * np.outer(within_truth_mode, within_truth_mode)

    participant_frame = result.participant_scores.set_index("participant_id")
    participant_true = np.asarray(
        [truth.participant_scores[participant] for participant in participant_frame.index],
        dtype=float,
    )
    participant_estimated = participant_frame["participant_FPC1"].to_numpy(dtype=float)

    trial_frame = result.trial_scores.set_index("curve_id")
    trial_true = np.asarray(
        [truth.trial_scores[curve_id] for curve_id in trial_frame.index],
        dtype=float,
    )
    trial_estimated = trial_frame["trial_FPC1"].to_numpy(dtype=float)

    between_similarity = _weighted_similarity(
        result.participant_eigenfunctions[0],
        between_truth_mode,
        grid,
    )
    within_similarity = _weighted_similarity(
        result.trial_eigenfunctions[0],
        within_truth_mode,
        grid,
    )
    record = {
        "scenario": name,
        "design": design,
        "n_participants": n_participants,
        "n_trials": len(result.curve_ids),
        "samples_per_curve_range": list(sample_range),
        "noise_sd": noise_sd,
        "single_trial_participants": list(
            result.support_diagnostics["single_trial_participants"]
        ),
        "n_repeated_participants": int(
            result.support_diagnostics["n_repeated_participants"]
        ),
        "between_covariance_relative_rmse": _relative_rmse(
            result.between_covariance,
            between_truth_covariance,
        ),
        "within_covariance_relative_rmse": _relative_rmse(
            result.within_covariance,
            within_truth_covariance,
        ),
        "between_eigenfunction_similarity": between_similarity,
        "within_eigenfunction_similarity": within_similarity,
        "participant_score_absolute_correlation": _absolute_correlation(
            participant_estimated,
            participant_true,
        ),
        "trial_score_absolute_correlation": _absolute_correlation(
            trial_estimated,
            trial_true,
        ),
        "failed_participant_score_systems": int(
            np.count_nonzero(result.score_diagnostics["status_code"] != "ok")
        ),
        "between_psd_action": result.covariance_diagnostics["between"][
            "applied_action"
        ],
        "within_psd_action": result.covariance_diagnostics["within"][
            "applied_action"
        ],
        "between_relative_operator_correction": float(
            result.covariance_diagnostics["between"][
                "relative_operator_correction_frobenius_norm"
            ]
        ),
        "within_relative_operator_correction": float(
            result.covariance_diagnostics["within"][
                "relative_operator_correction_frobenius_norm"
            ]
        ),
        "rank_k_covariance_used_for_scoring": bool(
            result.provenance["sparse_multilevel_fpca"][
                "rank_k_covariance_used_for_scoring"
            ]
        ),
        "raw_sparse_trajectory_interpolation_performed": bool(
            result.provenance["sparse_multilevel_fpca"][
                "raw_sparse_trajectory_interpolation_performed"
            ]
        ),
        "weighting": result.provenance["sparse_multilevel_fpca"]["weighting"],
        "trial_fixed_effects_estimated": bool(
            result.provenance["sparse_multilevel_fpca"][
                "trial_fixed_effects_estimated"
            ]
        ),
    }
    return record


def _expected_identifiability_failure():
    trajectories, _ = _simulate(
        n_participants=6,
        sample_range=(8, 10),
        noise_sd=0.10,
        design="balanced",
        seed=2026174,
    )
    # Retain two repeated participants and one trial from four others.
    participant_ids = trajectories.metadata["participant_id"].astype(str).to_numpy()
    seen = {}
    keep = []
    for index, participant in enumerate(participant_ids):
        count = seen.get(participant, 0)
        seen[participant] = count + 1
        keep.append(participant in {"p000", "p001"} or count == 0)
    indices = np.flatnonzero(np.asarray(keep, dtype=bool))
    reduced = IrregularTrajectorySet(
        time=tuple(trajectories.time[index] for index in indices),
        values=tuple(trajectories.values[index] for index in indices),
        curve_ids=tuple(trajectories.curve_ids[index] for index in indices),
        dimension_names=trajectories.dimension_names,
        metadata=trajectories.metadata.iloc[indices].reset_index(drop=True),
        coordinate_system=trajectories.coordinate_system,
        time_unit=trajectories.time_unit,
        provenance={"simulation": "expected_identifiability_failure"},
    )
    try:
        fit_sparse_multilevel_fpca(
            reduced,
            dimension="x",
            participant_column="participant_id",
            participant_components=1,
            trial_components=1,
            evaluation_grid=np.linspace(0.08, 0.92, 21),
            mean_bandwidth=0.30,
            total_covariance_bandwidth=0.38,
            between_covariance_bandwidth=0.42,
            analysis_support_action="restrict",
            noise_variance_method="fixed",
            measurement_error_variance=0.01,
            psd_action="project",
        )
    except SparseNativeError as error:
        return {
            "expected_failure_observed": True,
            "failure_code": error.code,
            "n_curves": int(reduced.n_curves),
        }
    return {
        "expected_failure_observed": False,
        "failure_code": None,
        "n_curves": int(reduced.n_curves),
    }


def _validate(records, failure_record):
    failures = []
    for record in records:
        label = record["scenario"]
        if record["failed_participant_score_systems"] != 0:
            failures.append(f"{label}: participant BLUP systems failed")
        if record["rank_k_covariance_used_for_scoring"]:
            failures.append(f"{label}: rank-K score covariance was used")
        if record["raw_sparse_trajectory_interpolation_performed"]:
            failures.append(f"{label}: raw sparse interpolation was performed")
        if record["weighting"] != "observation":
            failures.append(f"{label}: unexpected weighting contract")
        if record["trial_fixed_effects_estimated"]:
            failures.append(f"{label}: fixed trial effects unexpectedly estimated")
        if record["between_eigenfunction_similarity"] < 0.70:
            failures.append(
                f"{label}: between mode similarity={record['between_eigenfunction_similarity']:.3f}"
            )
        if record["within_eigenfunction_similarity"] < 0.65:
            failures.append(
                f"{label}: within mode similarity={record['within_eigenfunction_similarity']:.3f}"
            )
        if record["participant_score_absolute_correlation"] < 0.65:
            failures.append(
                f"{label}: participant score corr={record['participant_score_absolute_correlation']:.3f}"
            )
        if record["trial_score_absolute_correlation"] < 0.55:
            failures.append(
                f"{label}: trial score corr={record['trial_score_absolute_correlation']:.3f}"
            )
        if record["between_covariance_relative_rmse"] > 1.10:
            failures.append(
                f"{label}: between covariance relRMSE={record['between_covariance_relative_rmse']:.3f}"
            )
        if record["within_covariance_relative_rmse"] > 1.20:
            failures.append(
                f"{label}: within covariance relRMSE={record['within_covariance_relative_rmse']:.3f}"
            )
    unequal = next(record for record in records if record["design"] == "unequal")
    if not unequal["single_trial_participants"]:
        failures.append("unequal design did not retain single-trial participants")
    if not failure_record["expected_failure_observed"]:
        failures.append("non-identifiable hierarchy did not fail explicitly")
    elif failure_record["failure_code"] != "insufficient_repeated_participants":
        failures.append(
            "non-identifiable hierarchy failed with unexpected code "
            f"{failure_record['failure_code']}"
        )
    return failures


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    scenarios = [
        _fit_scenario(
            "balanced_dense_low_noise",
            n_participants=48,
            sample_range=(11, 15),
            noise_sd=0.08,
            design="balanced",
            seed=20261740,
        ),
        _fit_scenario(
            "unequal_sparse_higher_noise",
            n_participants=54,
            sample_range=(7, 10),
            noise_sd=0.16,
            design="unequal",
            seed=20261741,
        ),
    ]
    replay = _fit_scenario(
        "balanced_dense_low_noise",
        n_participants=48,
        sample_range=(11, 15),
        noise_sd=0.08,
        design="balanced",
        seed=20261740,
    )
    replay_passed = replay == scenarios[0]
    failure_record = _expected_identifiability_failure()
    failures = _validate(scenarios, failure_record)
    if not replay_passed:
        failures.append("deterministic replay did not reproduce scenario summary exactly")

    payload = {
        "validation_target": "native_sparse_multilevel_fpca",
        "hierarchical_model": "Y_ij(t)=mu(t)+U_i(t)+V_ij(t)+epsilon_ij(t)",
        "known_truth_between_eigenvalue": 1.0,
        "known_truth_within_eigenvalue": 0.45,
        "exchangeable_trials_assumed": True,
        "trial_fixed_effects_estimated": False,
        "weighting": "observation",
        "population_estimation_uncertainty_propagated": False,
        "raw_sparse_trajectory_interpolation_performed": False,
        "scenarios": scenarios,
        "expected_identifiability_failure": failure_record,
        "deterministic_replay_passed": replay_passed,
        "validation_failures": failures,
        "validation_passed": not failures,
        "interpretation": (
            "Known-truth deterministic qualification for the declared sparse hierarchical designs; "
            "not a universal recovery or uncertainty guarantee."
        ),
    }
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if failures:
        raise SystemExit("; ".join(failures))


if __name__ == "__main__":
    main()
