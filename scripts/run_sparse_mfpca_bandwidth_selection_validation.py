#!/usr/bin/env python3
"""Known-truth qualification for audited sparse planar MFPCA bandwidth selection.

This runner qualifies the selection contract, not recovery of a unique "true"
bandwidth. It exercises training-fold population refits, full joint held-out
Gaussian likelihood, failed-candidate retention, deterministic evidence,
curve/group resampling, fixed diagonal/correlated measurement error, and an
explicit downstream fit using the selected bandwidths.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

from eyetrajectoriespy import (
    FunctionalSimulationScenario,
    simulate_functional_scenario,
)
from eyetrajectoriespy.sparse_multivariate import fit_sparse_mfpca
from eyetrajectoriespy.sparse_multivariate_bandwidth_selection import (
    select_sparse_mfpca_bandwidths,
)


MEAN_CANDIDATES = (1e-6, 0.18, 0.50)
COVARIANCE_CANDIDATES = (0.25, 0.60)
N_SPLITS = 3


def _mean(time: np.ndarray) -> np.ndarray:
    time = np.asarray(time, dtype=float)
    return np.column_stack(
        [
            0.45 + 0.04 * np.sin(np.pi * time),
            0.55 + 0.03 * np.cos(np.pi * time),
        ]
    )


def _u(time: np.ndarray) -> np.ndarray:
    time = np.asarray(time, dtype=float)
    return np.sqrt(2.0) * np.sin(np.pi * time)


def _v(time: np.ndarray) -> np.ndarray:
    time = np.asarray(time, dtype=float)
    return np.sqrt(2.0) * np.sin(2.0 * np.pi * time)


def _plus_mode(time: np.ndarray) -> np.ndarray:
    values = _u(time) / np.sqrt(2.0)
    return np.column_stack([values, values])


def _minus_mode(time: np.ndarray) -> np.ndarray:
    values = _v(time) / np.sqrt(2.0)
    return np.column_stack([values, -values])


EIGENFUNCTIONS: tuple[Callable[[np.ndarray], np.ndarray], ...] = (
    _plus_mode,
    _minus_mode,
)


def _scenario(
    *,
    name: str,
    n_participants: int,
    trials_per_participant: int,
    noise_covariance: np.ndarray,
    seed: int,
    repeated_structure: bool,
) -> FunctionalSimulationScenario:
    return FunctionalSimulationScenario(
        name=name,
        truth_grid=np.linspace(0.0, 1.0, 81),
        eigenvalues=(0.80, 0.30),
        n_participants=n_participants,
        trials_per_participant=trials_per_participant,
        dimension_names=("x", "y"),
        coordinate_system="normalized",
        time_unit="normalized",
        observation_design="irregular",
        samples_per_curve=(10, 14),
        irregular_time_design="uniform",
        participant_eigenvalues=(0.18, 0.07) if repeated_structure else None,
        trial_eigenvalues=(0.07, 0.03) if repeated_structure else None,
        measurement_noise_sd=0.0,
        measurement_noise_covariance=np.asarray(noise_covariance, dtype=float),
        replicates=1,
        seed_start=seed,
        labels={
            "qualification": "audited_sparse_mfpca_bandwidth_selection",
            "bandwidth_truth_target": "not_defined",
        },
    )


def _measurement_error_kwargs(noise_covariance: np.ndarray) -> dict[str, object]:
    covariance = np.asarray(noise_covariance, dtype=float)
    if np.allclose(
        covariance,
        np.diag(np.diag(covariance)),
        rtol=0.0,
        atol=1e-15,
    ):
        return {
            "measurement_error": "diagonal",
            "measurement_error_variance": tuple(
                float(value) for value in np.diag(covariance)
            ),
        }
    return {
        "measurement_error": "fixed_matrix",
        "measurement_error_covariance": covariance.copy(),
    }


def _candidate_row(
    result,
    *,
    mean_bandwidth: float,
    covariance_bandwidth: float,
) -> pd.Series | None:
    summary = result.candidate_summary
    rows = summary[
        np.isclose(summary["mean_bandwidth"], mean_bandwidth)
        & np.isclose(summary["covariance_bandwidth"], covariance_bandwidth)
    ]
    if rows.empty:
        return None
    return rows.iloc[0]


def _selected_row(result) -> pd.Series:
    if result.selected_bandwidths is None:
        raise AssertionError("selector returned no eligible candidate")
    candidate_id = str(result.selected_bandwidths["candidate_id"])
    rows = result.candidate_summary[
        result.candidate_summary["candidate_id"] == candidate_id
    ]
    if len(rows) != 1:
        raise AssertionError("selected candidate missing from summary")
    return rows.iloc[0]


def _assert_deterministic(first, second, *, name: str) -> None:
    pd.testing.assert_frame_equal(first.assignments, second.assignments)
    pd.testing.assert_frame_equal(first.candidates, second.candidates)
    pd.testing.assert_frame_equal(first.fold_results, second.fold_results)
    pd.testing.assert_frame_equal(first.curve_losses, second.curve_losses)
    pd.testing.assert_frame_equal(
        first.candidate_summary,
        second.candidate_summary,
    )
    if first.selected_bandwidths != second.selected_bandwidths:
        raise AssertionError(f"{name}: selected bandwidths are not deterministic")


def _run_case(
    *,
    name: str,
    n_participants: int,
    trials_per_participant: int,
    noise_covariance: np.ndarray,
    seed: int,
    resampling_unit: str,
    group_column: str | None,
) -> dict[str, Any]:
    repeated = trials_per_participant > 1
    scenario = _scenario(
        name=name,
        n_participants=n_participants,
        trials_per_participant=trials_per_participant,
        noise_covariance=noise_covariance,
        seed=seed,
        repeated_structure=repeated,
    )
    simulation = simulate_functional_scenario(
        scenario,
        mean=_mean,
        eigenfunctions=EIGENFUNCTIONS,
    )
    observations = simulation.observations
    grid = np.linspace(0.12, 0.88, 13)
    error_kwargs = _measurement_error_kwargs(noise_covariance)
    selector_kwargs: dict[str, Any] = {
        "dimensions": ("x", "y"),
        "evaluation_grid": grid,
        "mean_bandwidths": MEAN_CANDIDATES,
        "covariance_bandwidths": COVARIANCE_CANDIDATES,
        "analysis_support_action": "restrict",
        "n_splits": N_SPLITS,
        "resampling_unit": resampling_unit,
        "group_column": group_column,
        "shuffle": True,
        "random_state": 1705,
        "failure_action": "retain",
        "psd_action": "project",
        **error_kwargs,
    }
    result = select_sparse_mfpca_bandwidths(
        observations,
        **selector_kwargs,
    )
    replay = select_sparse_mfpca_bandwidths(
        observations,
        **selector_kwargs,
    )
    _assert_deterministic(result, replay, name=name)

    if result.status_code != "ok":
        raise AssertionError(f"{name}: selector status is {result.status_code!r}")
    selected_row = _selected_row(result)
    if not bool(selected_row["eligible"]):
        raise AssertionError(f"{name}: selected candidate is not eligible")
    if int(selected_row["n_valid_folds"]) != N_SPLITS:
        raise AssertionError(f"{name}: selected candidate lacks all valid folds")

    eligible = result.candidate_summary[
        result.candidate_summary["eligible"]
        & np.isfinite(result.candidate_summary["mean_loss"])
    ]
    if eligible.empty:
        raise AssertionError(f"{name}: no finite eligible candidates")
    selected_loss = float(selected_row["mean_loss"])
    minimum_loss = float(eligible["mean_loss"].min())
    if not np.isclose(selected_loss, minimum_loss, rtol=0.0, atol=1e-12):
        raise AssertionError(f"{name}: selected candidate is not exact argmin")

    pathological = result.candidate_summary[
        np.isclose(result.candidate_summary["mean_bandwidth"], MEAN_CANDIDATES[0])
    ]
    if pathological.empty:
        raise AssertionError(f"{name}: pathological candidates are missing")
    pathological_failed_folds = int(pathological["n_failed_folds"].sum())
    if pathological_failed_folds < 1:
        raise AssertionError(
            f"{name}: pathological undersmoothing edge did not retain any failures"
        )

    oversmooth = _candidate_row(
        result,
        mean_bandwidth=MEAN_CANDIDATES[-1],
        covariance_bandwidth=COVARIANCE_CANDIDATES[-1],
    )
    if oversmooth is None:
        raise AssertionError(f"{name}: oversmoothing edge missing from summary")
    oversmooth_status = "eligible" if bool(oversmooth["eligible"]) else "failed"
    oversmooth_loss = (
        float(oversmooth["mean_loss"])
        if bool(oversmooth["eligible"]) and np.isfinite(oversmooth["mean_loss"])
        else None
    )
    if oversmooth_loss is not None and selected_loss > oversmooth_loss + 1e-12:
        raise AssertionError(
            f"{name}: selected loss exceeds eligible oversmoothing edge"
        )

    if resampling_unit == "group":
        if group_column is None:
            raise AssertionError(f"{name}: group resampling missing group column")
        if result.assignments.groupby("group")["fold"].nunique().max() != 1:
            raise AssertionError(f"{name}: participant leakage across folds")
        expected_groups = observations.metadata[group_column].astype(str).nunique()
        if result.assignments["group"].nunique() != expected_groups:
            raise AssertionError(f"{name}: group assignments do not cover participants")

    provenance = result.provenance
    required_false = (
        "joint_pace_scoring_performed",
        "validation_observations_used_for_population_fitting",
        "validation_observations_used_for_score_fitting",
        "rank_k_covariance_used_for_validation",
        "score_ridge_included_in_validation_covariance",
        "measurement_error_tuned",
        "automatic_fit_bandwidth_selection_performed",
        "rank_tuned",
        "score_ridge_tuned",
        "evaluation_grid_tuned",
        "psd_policy_tuned",
        "support_policy_tuned",
    )
    for key in required_false:
        if provenance[key] is not False:
            raise AssertionError(f"{name}: provenance flag {key!r} is not false")
    if provenance["population_refit_inside_fold"] is not True:
        raise AssertionError(f"{name}: training-fold refit flag is false")
    if provenance["full_fitted_joint_covariance_used_for_validation"] is not True:
        raise AssertionError(f"{name}: full joint covariance flag is false")
    if provenance["selected_values_must_be_passed_explicitly_to_fit_sparse_mfpca"] is not True:
        raise AssertionError(f"{name}: explicit downstream-fit flag is false")

    selected = result.selected_bandwidths
    assert selected is not None
    fitted = fit_sparse_mfpca(
        observations,
        dimensions=("x", "y"),
        n_components=1,
        evaluation_grid=grid,
        mean_bandwidth=float(selected["mean_bandwidth"]),
        covariance_bandwidth=float(selected["covariance_bandwidth"]),
        analysis_support_action="restrict",
        psd_action="project",
        score_failure_action="retain_nan",
        **error_kwargs,
    )
    sparse_fit = fitted.provenance["sparse_mfpca"]
    if sparse_fit["automatic_bandwidth_selection_performed"] is not False:
        raise AssertionError(f"{name}: downstream fitter became automatic")
    if not np.isclose(
        float(sparse_fit["mean_bandwidth"]),
        float(selected["mean_bandwidth"]),
    ):
        raise AssertionError(f"{name}: selected mean bandwidth not passed exactly")
    if not np.isclose(
        float(sparse_fit["covariance_bandwidth"]),
        float(selected["covariance_bandwidth"]),
    ):
        raise AssertionError(
            f"{name}: selected covariance bandwidth not passed exactly"
        )

    failed_folds = int(
        np.count_nonzero(result.fold_results["status_code"].to_numpy() != "ok")
    )
    return {
        "name": name,
        "n_participants": int(n_participants),
        "trials_per_participant": int(trials_per_participant),
        "n_curves": int(observations.n_curves),
        "resampling_unit": result.resampling_unit,
        "group_column": result.group_column,
        "measurement_error_mode": provenance["measurement_error_mode"],
        "measurement_error_covariance": np.asarray(
            provenance["measurement_error_covariance"], dtype=float
        ).tolist(),
        "candidate_count": int(len(result.candidates)),
        "eligible_candidate_count": int(np.count_nonzero(result.candidate_summary["eligible"])),
        "failed_candidate_folds": failed_folds,
        "pathological_failed_folds": pathological_failed_folds,
        "selected_bandwidths": dict(selected),
        "selected_mean_loss": selected_loss,
        "minimum_eligible_mean_loss": minimum_loss,
        "oversmoothing_edge_status": oversmooth_status,
        "oversmoothing_edge_loss": oversmooth_loss,
        "deterministic_replay_passed": True,
        "group_leakage_prevented": bool(
            provenance["group_leakage_prevented"]
        ),
        "full_fitted_joint_covariance_used_for_validation": True,
        "joint_pace_scoring_performed": False,
        "rank_k_covariance_used_for_validation": False,
        "measurement_error_tuned": False,
        "downstream_fit_automatic_bandwidth_selection_performed": bool(
            sparse_fit["automatic_bandwidth_selection_performed"]
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-participants", type=int, default=24)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.n_participants < 18 or args.n_participants % N_SPLITS:
        raise ValueError(
            "--n-participants must be >= 18 and divisible by the number of folds"
        )

    diagonal = np.asarray(
        [[0.0025, 0.0], [0.0, 0.0036]],
        dtype=float,
    )
    correlated = np.asarray(
        [[0.0025, 0.0012], [0.0012, 0.0036]],
        dtype=float,
    )
    scenarios = [
        _run_case(
            name="diagonal_curve_cv",
            n_participants=args.n_participants,
            trials_per_participant=1,
            noise_covariance=diagonal,
            seed=20261710,
            resampling_unit="curve",
            group_column=None,
        ),
        _run_case(
            name="correlated_repeated_trial_group_cv",
            n_participants=args.n_participants,
            trials_per_participant=2,
            noise_covariance=correlated,
            seed=20261711,
            resampling_unit="group",
            group_column="participant_id",
        ),
    ]

    payload = {
        "method": "audited_sparse_mfpca_bandwidth_selection_known_truth_qualification",
        "criterion": "mean_curve_planar_gaussian_nll",
        "qualified_scope": "mean_and_joint_latent_covariance_bandwidth_selection_only",
        "measurement_error_tuned": False,
        "joint_pace_scoring_performed": False,
        "rank_k_covariance_used_for_validation": False,
        "unique_true_bandwidth_recovery_claimed": False,
        "claim_scope": (
            "Qualification checks leakage-free training-fold population refits, "
            "full-joint held-out predictive selection, retained candidate failures, "
            "deterministic evidence, and explicit downstream use. It does not define "
            "or recover a unique population-optimal smoothing bandwidth."
        ),
        "candidate_grid": {
            "mean_bandwidths": list(MEAN_CANDIDATES),
            "covariance_bandwidths": list(COVARIANCE_CANDIDATES),
        },
        "scenario_count": len(scenarios),
        "scenarios": scenarios,
        "validation_passed": True,
    }
    args.output.write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
