#!/usr/bin/env python3
"""Known-truth qualification for audited native sparse-FPCA bandwidth selection."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from eyetrajectoriespy._sparse_truth import simulate_sparse_functional_truth
from eyetrajectoriespy.fpca import functional_trapezoid_weights
from eyetrajectoriespy.sparse_bandwidth_selection import select_sparse_fpca_bandwidths
from eyetrajectoriespy.sparse_native import fit_sparse_fpca
from eyetrajectoriespy.types import IrregularTrajectorySet


def _dataset(
    *,
    n_curves: int,
    samples_per_curve: int | tuple[int, int],
    noise_sd: float,
    observation_design: str,
    random_state: int,
    grouped: bool,
):
    times, values, truth = simulate_sparse_functional_truth(
        n_curves=n_curves,
        samples_per_curve=samples_per_curve,
        noise_sd=noise_sd,
        observation_design=observation_design,
        random_state=random_state,
    )
    participant_ids = (
        [f"P{i // 2 + 1:03d}" for i in range(n_curves)]
        if grouped
        else [f"P{i + 1:03d}" for i in range(n_curves)]
    )
    observations = IrregularTrajectorySet(
        time=times,
        values=tuple(value[:, None] for value in values),
        curve_ids=tuple(f"curve_{i:03d}" for i in range(n_curves)),
        dimension_names=("x",),
        metadata=pd.DataFrame({"participant_id": participant_ids}),
        coordinate_system="normalized",
        time_unit="normalized",
        provenance={"source": "known_sparse_functional_truth"},
    )
    return observations, truth


def _truth_covariance(truth, grid: np.ndarray) -> np.ndarray:
    functions = np.vstack([function(grid) for function in truth.eigenfunctions])
    return (functions.T * truth.eigenvalues[None, :]) @ functions


def _recovery_metrics(fit, truth, grid: np.ndarray) -> dict[str, float]:
    true_mean = truth.mean(grid)
    true_covariance = _truth_covariance(truth, grid)
    mean_rmse = float(np.sqrt(np.mean((fit.mean - true_mean) ** 2)))
    covariance_rmse = float(np.sqrt(np.mean((fit.covariance - true_covariance) ** 2)))
    covariance_scale = float(np.sqrt(np.mean(true_covariance**2)))
    covariance_relative_rmse = covariance_rmse / covariance_scale

    weights = functional_trapezoid_weights(grid)
    true_functions = np.vstack([function(grid) for function in truth.eigenfunctions])
    similarities = np.abs(fit.eigenfunctions @ np.diag(weights) @ true_functions.T)
    score_correlations = [
        float(abs(np.corrcoef(fit.scores[:, component], truth.scores[:, component])[0, 1]))
        for component in range(2)
    ]
    return {
        "mean_rmse": mean_rmse,
        "covariance_relative_rmse": float(covariance_relative_rmse),
        "component_1_similarity": float(similarities[0, 0]),
        "component_2_similarity": float(similarities[1, 1]),
        "score_1_abs_correlation": score_correlations[0],
        "score_2_abs_correlation": score_correlations[1],
    }


def _candidate_loss(result, *, mean_bandwidth: float, covariance_bandwidth: float):
    mask = np.isclose(result.candidate_summary["mean_bandwidth"], mean_bandwidth) & np.isclose(
        result.candidate_summary["covariance_bandwidth"], covariance_bandwidth
    )
    rows = result.candidate_summary[mask]
    if rows.empty:
        return None
    eligible = rows[rows["eligible"] & np.isfinite(rows["mean_loss"])]
    if eligible.empty:
        return None
    return float(eligible["mean_loss"].min())


def _run_scenario(
    *,
    name: str,
    n_curves: int,
    samples_per_curve: int | tuple[int, int],
    noise_sd: float,
    observation_design: str,
    random_state: int,
    grouped: bool,
) -> dict[str, Any]:
    observations, truth = _dataset(
        n_curves=n_curves,
        samples_per_curve=samples_per_curve,
        noise_sd=noise_sd,
        observation_design=observation_design,
        random_state=random_state,
        grouped=grouped,
    )
    grid = np.linspace(0.0, 1.0, 21)
    mean_candidates = (0.06, 0.20, 0.50)
    covariance_candidates = (0.12, 0.32, 0.65)

    result = select_sparse_fpca_bandwidths(
        observations,
        dimension="x",
        evaluation_grid=grid,
        mean_bandwidths=mean_candidates,
        covariance_bandwidths=covariance_candidates,
        noise_variance_method="fixed",
        measurement_error_variance=truth.noise_sd**2,
        n_splits=3,
        resampling_unit="group" if grouped else "curve",
        group_column="participant_id" if grouped else None,
        random_state=19,
        psd_action="project",
        failure_action="retain",
    )
    if result.selected_bandwidths is None:
        raise AssertionError(f"{name}: selector returned no eligible candidate")
    if result.provenance["noise_bandwidth_tuned"] is not False:
        raise AssertionError(f"{name}: A2 must not tune the noise bandwidth")

    eligible = result.candidate_summary[
        result.candidate_summary["eligible"]
        & np.isfinite(result.candidate_summary["mean_loss"])
    ]
    if eligible.empty:
        raise AssertionError(f"{name}: no eligible finite candidate summary")
    selected_id = result.selected_bandwidths["candidate_id"]
    selected_row = eligible[eligible["candidate_id"] == selected_id]
    if len(selected_row) != 1:
        raise AssertionError(f"{name}: selected candidate missing from eligible summary")
    selected_loss = float(selected_row.iloc[0]["mean_loss"])
    minimum_loss = float(eligible["mean_loss"].min())
    if not np.isclose(selected_loss, minimum_loss, rtol=0.0, atol=1e-12):
        raise AssertionError(f"{name}: selected candidate is not the minimum-loss candidate")
    if int(selected_row.iloc[0]["n_valid_folds"]) != result.n_splits:
        raise AssertionError(f"{name}: selected candidate does not have all folds valid")
    if result.assignments["curve_id"].nunique() != observations.n_curves:
        raise AssertionError(f"{name}: fold assignments do not cover every curve")
    if len(result.assignments) != observations.n_curves:
        raise AssertionError(f"{name}: duplicate/missing assignment rows")
    if grouped and result.assignments.groupby("group")["fold"].nunique().max() != 1:
        raise AssertionError(f"{name}: repeated participant leaked across validation folds")

    fit = fit_sparse_fpca(
        observations,
        dimension="x",
        n_components=2,
        evaluation_grid=grid,
        mean_bandwidth=float(result.selected_bandwidths["mean_bandwidth"]),
        covariance_bandwidth=float(result.selected_bandwidths["covariance_bandwidth"]),
        noise_variance_method="fixed",
        measurement_error_variance=truth.noise_sd**2,
        psd_action="project",
    )
    recovery = _recovery_metrics(fit, truth, grid)
    if recovery["mean_rmse"] >= 0.35:
        raise AssertionError(f"{name}: selected mean recovery is catastrophically poor")
    if recovery["covariance_relative_rmse"] >= 0.90:
        raise AssertionError(f"{name}: selected covariance recovery is catastrophically poor")
    if recovery["component_1_similarity"] <= 0.60:
        raise AssertionError(f"{name}: first component recovery is too weak")
    if recovery["score_1_abs_correlation"] <= 0.50:
        raise AssertionError(f"{name}: first score recovery is too weak")

    under_loss = _candidate_loss(
        result,
        mean_bandwidth=mean_candidates[0],
        covariance_bandwidth=covariance_candidates[0],
    )
    over_loss = _candidate_loss(
        result,
        mean_bandwidth=mean_candidates[-1],
        covariance_bandwidth=covariance_candidates[-1],
    )
    for label, comparison in (("under", under_loss), ("over", over_loss)):
        if comparison is not None and selected_loss > comparison + 1e-12:
            raise AssertionError(
                f"{name}: selected loss exceeds eligible {label}-smooth extreme"
            )

    failed_folds = int(np.count_nonzero(result.fold_results["status_code"] != "ok"))
    valid_fold_noise = result.fold_results.loc[
        result.fold_results["status_code"] == "ok",
        "fitted_noise_variance",
    ].to_numpy(dtype=float)
    expected_noise = truth.noise_sd**2
    if not np.allclose(valid_fold_noise, expected_noise, rtol=0.0, atol=1e-14):
        raise AssertionError(f"{name}: fixed measurement-error variance changed across folds")

    return {
        "name": name,
        "n_curves": int(observations.n_curves),
        "samples_per_curve": (
            list(samples_per_curve)
            if isinstance(samples_per_curve, tuple)
            else int(samples_per_curve)
        ),
        "noise_sd": float(noise_sd),
        "observation_design": observation_design,
        "resampling_unit": result.resampling_unit,
        "noise_variance_method": "fixed",
        "noise_bandwidth_tuned": False,
        "candidate_count": int(len(result.candidates)),
        "failed_candidate_folds": failed_folds,
        "eligible_candidate_count": int(np.count_nonzero(result.candidate_summary["eligible"])),
        "selected_bandwidths": dict(result.selected_bandwidths),
        "selected_mean_loss": selected_loss,
        "minimum_eligible_mean_loss": minimum_loss,
        "under_smooth_extreme_loss": under_loss,
        "over_smooth_extreme_loss": over_loss,
        "selected_full_fit_noise_variance": float(fit.noise_variance),
        "recovery": recovery,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-curves", type=int, default=60)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.n_curves < 30 or args.n_curves % 2:
        raise ValueError("--n-curves must be an even integer >= 30")

    scenarios = [
        _run_scenario(
            name="sparse_uniform_low_noise",
            n_curves=args.n_curves,
            samples_per_curve=8,
            noise_sd=0.10,
            observation_design="uniform",
            random_state=1601,
            grouped=False,
        ),
        _run_scenario(
            name="variable_center_clustered_moderate_noise_grouped",
            n_curves=args.n_curves,
            samples_per_curve=(7, 11),
            noise_sd=0.16,
            observation_design="center_clustered",
            random_state=1602,
            grouped=True,
        ),
        _run_scenario(
            name="boundary_poor_high_noise",
            n_curves=args.n_curves,
            samples_per_curve=12,
            noise_sd=0.22,
            observation_design="boundary_poor",
            random_state=1603,
            grouped=False,
        ),
    ]

    payload = {
        "method": "audited_sparse_fpca_bandwidth_selection_known_truth_qualification",
        "criterion": "mean_curve_gaussian_nll",
        "qualified_scope": "mean_and_covariance_bandwidth_selection_only",
        "noise_bandwidth_tuned": False,
        "noise_bandwidth_scope_note": (
            "A2 does not tune diagonal-difference noise bandwidth. Earlier exploratory "
            "qualification showed that marginal predictive likelihood can recover total "
            "observation covariance while misallocating latent and measurement-noise "
            "variance; decomposition-specific noise-bandwidth selection therefore "
            "requires a separate criterion and qualification."
        ),
        "claim_scope": (
            "Qualification checks leakage-free held-out predictive selection and "
            "descriptive population recovery. It does not define or recover a unique "
            "true bandwidth."
        ),
        "scenario_count": len(scenarios),
        "scenarios": scenarios,
    }
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
