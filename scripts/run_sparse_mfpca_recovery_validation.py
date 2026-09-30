"""Deterministic known-truth qualification for native sparse MFPCA.

This script separates small predeclared qualification guards from descriptive
grid/ridge sensitivity. It does not compare against an external implementation
and it never selects tuning parameters from the sensitivity tables.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

from eyetrajectoriespy import (
    FunctionalSimulationScenario,
    evaluate_sparse_mfpca_recovery,
    fit_sparse_mfpca,
    functional_recovery_assessment_frame,
    functional_trapezoid_weights,
    simulate_functional_scenario,
)


RHO_FAMILY = (-0.6, 0.0, 0.3, 0.6, 0.9)
QUALIFICATION_GRID_SIZE = 31
QUALIFICATION_GUARDS = {
    "score_failure_rate_max": 0.05,
    "minimum_subspace_principal_cosine_min": 0.70,
    "mean_ise_sampling_reference_ratio_max": 2.0,
    "joint_covariance_ise_max": 1.50,
    "reconstruction_ise_max": 0.80,
    "psd_relative_operator_correction_max": 0.50,
    "median_separated_score_correlation_min": 0.45,
    "tied_score_subspace_procrustes_rmse_max": 0.80,
}
GRID_SIZES = (31, 51, 81)
RIDGES = (0.0, 1e-8, 1e-6, 1e-4)


def _mean_planar(time: np.ndarray) -> np.ndarray:
    time = np.asarray(time, dtype=float)
    return np.column_stack(
        (
            0.50 + 0.04 * np.sin(np.pi * time),
            0.50 + 0.04 * np.cos(np.pi * time),
        )
    )


def _scalar_mode(frequency: int) -> Callable[[np.ndarray], np.ndarray]:
    def mode(time: np.ndarray) -> np.ndarray:
        time = np.asarray(time, dtype=float)
        return np.sqrt(2.0) * np.sin(frequency * np.pi * time)

    return mode


def _vector_mode(
    scalar: Callable[[np.ndarray], np.ndarray],
    loading: np.ndarray,
) -> Callable[[np.ndarray], np.ndarray]:
    loading_array = np.asarray(loading, dtype=float).copy()

    def mode(time: np.ndarray) -> np.ndarray:
        values = scalar(np.asarray(time, dtype=float))
        return values[:, None] * loading_array[None, :]

    return mode


def planar_rho_design(
    rho_xy: float,
) -> tuple[tuple[float, ...], tuple[Callable[[np.ndarray], np.ndarray], ...]]:
    """Return the fixed-marginal planar family for -1 < rho_xy < 1."""

    rho = float(rho_xy)
    if not np.isfinite(rho) or rho <= -1.0 or rho >= 1.0:
        raise ValueError("rho_xy must satisfy -1 < rho_xy < 1")

    plus = np.array([1.0, 1.0]) / np.sqrt(2.0)
    minus = np.array([1.0, -1.0]) / np.sqrt(2.0)
    temporal = ((_scalar_mode(1), 1.0), (_scalar_mode(2), 0.45))
    channel = ((plus, 1.0 + rho), (minus, 1.0 - rho))

    pairs: list[
        tuple[float, Callable[[np.ndarray], np.ndarray]]
    ] = []
    for scalar, temporal_value in temporal:
        for loading, channel_value in channel:
            pairs.append(
                (
                    float(temporal_value * channel_value),
                    _vector_mode(scalar, loading),
                )
            )
    pairs.sort(key=lambda item: item[0], reverse=True)
    return (
        tuple(item[0] for item in pairs),
        tuple(item[1] for item in pairs),
    )


def asymmetric_cross_covariance_design(
) -> tuple[tuple[float, ...], tuple[Callable[[np.ndarray], np.ndarray], ...]]:
    """Return a rank-two design with Cxy(s,t) != Cxy(t,s)."""

    u = _scalar_mode(1)
    v = _scalar_mode(2)

    def plus(time: np.ndarray) -> np.ndarray:
        return np.column_stack([u(time), v(time)]) / np.sqrt(2.0)

    def minus(time: np.ndarray) -> np.ndarray:
        return np.column_stack([u(time), -v(time)]) / np.sqrt(2.0)

    return (1.20, 0.45), (plus, minus)


def _scenario(
    *,
    name: str,
    grid_size: int,
    eigenvalues: tuple[float, ...],
    noise_covariance: np.ndarray,
    seed: int,
    n_participants: int = 36,
    samples_per_curve: tuple[int, int] = (22, 30),
    labels: dict[str, object] | None = None,
) -> FunctionalSimulationScenario:
    return FunctionalSimulationScenario(
        name=name,
        truth_grid=np.linspace(0.0, 1.0, int(grid_size)),
        eigenvalues=eigenvalues,
        n_participants=n_participants,
        dimension_names=("x", "y"),
        coordinate_system="normalized",
        time_unit="normalized",
        observation_design="irregular",
        samples_per_curve=samples_per_curve,
        irregular_time_design="uniform",
        measurement_noise_sd=0.0,
        measurement_noise_covariance=np.asarray(
            noise_covariance, dtype=float
        ),
        replicates=1,
        seed_start=int(seed),
        labels=dict(labels or {}),
    )


def _fit_truth(
    simulation,
    *,
    score_ridge: float = 0.0,
):
    truth = simulation.truth
    noise = np.asarray(
        truth.measurement_noise_covariance,
        dtype=float,
    )
    diagonal = np.allclose(
        noise,
        np.diag(np.diag(noise)),
        rtol=0.0,
        atol=1e-15,
    )
    kwargs = (
        {
            "measurement_error": "diagonal",
            "measurement_error_variance": tuple(
                float(value) for value in np.diag(noise)
            ),
        }
        if diagonal
        else {
            "measurement_error": "fixed_matrix",
            "measurement_error_covariance": noise.copy(),
        }
    )
    return fit_sparse_mfpca(
        simulation.observations,
        dimensions=("x", "y"),
        n_components=len(truth.eigenvalues),
        evaluation_grid=np.asarray(truth.truth_grid, dtype=float),
        mean_bandwidth=0.20,
        covariance_bandwidth=0.28,
        psd_action="project",
        score_ridge=float(score_ridge),
        score_failure_action="retain_nan",
        covariance_min_local_pairs=8,
        **kwargs,
    )


def _truth_cxy(truth) -> np.ndarray:
    functions = np.asarray(truth.eigenfunctions, dtype=float)
    return np.einsum(
        "k,ks,kt->st",
        np.asarray(truth.eigenvalues, dtype=float),
        functions[:, :, 0],
        functions[:, :, 1],
        optimize=True,
    )


def _weighted_surface_norm_sq(
    surface: np.ndarray,
    grid: np.ndarray,
) -> float:
    weights = functional_trapezoid_weights(grid)
    return float(
        np.sum(
            np.asarray(surface, dtype=float) ** 2
            * np.outer(weights, weights)
        )
    )


def _metric_values(frame: pd.DataFrame, metric: str) -> np.ndarray:
    values = frame.loc[frame["metric"] == metric, "value"].to_numpy(
        dtype=float
    )
    return values[np.isfinite(values)]


def _assessment_row(
    *,
    case: str,
    simulation,
    fitted,
    rho_xy: float | None,
    case_type: str,
) -> dict[str, object]:
    assessment = evaluate_sparse_mfpca_recovery(
        fitted,
        simulation.truth,
    )
    frame = functional_recovery_assessment_frame(assessment)
    subspace = _metric_values(
        frame.loc[frame["source"].isna()],
        "subspace_principal_cosine",
    )
    score_correlations = _metric_values(frame, "score_correlation")
    score_rmse = _metric_values(frame, "score_rmse")
    procrustes = _metric_values(
        frame,
        "score_subspace_procrustes_rmse",
    )
    failure = _metric_values(frame, "score_failure_rate")
    condition_median = _metric_values(
        frame, "score_condition_number_median"
    )
    condition_q95 = _metric_values(
        frame, "score_condition_number_q95"
    )
    condition_max = _metric_values(
        frame, "score_condition_number_max"
    )
    mean_ise = _metric_values(frame, "mean_ise")
    covariance_ise = _metric_values(frame, "covariance_ise")
    reconstruction = _metric_values(frame, "reconstruction_ise")
    psd = _metric_values(
        frame,
        "psd_relative_operator_correction",
    )
    cxy = frame.loc[
        (frame["metric"] == "covariance_block_ise")
        & (frame["source"] == "cxy"),
        "value",
    ].to_numpy(dtype=float)

    truth_cxy = _truth_cxy(simulation.truth)
    zero_cxy_ise = _weighted_surface_norm_sq(
        truth_cxy,
        np.asarray(simulation.truth.truth_grid, dtype=float),
    )
    n_curves = int(simulation.truth.scores.shape[0])
    mean_sampling_reference = float(
        np.sum(np.asarray(simulation.truth.eigenvalues, dtype=float))
        / n_curves
    )
    mean_sampling_ratio = (
        float(mean_ise[0]) / mean_sampling_reference
    )
    return {
        "case": case,
        "case_type": case_type,
        "rho_xy": rho_xy,
        "grid_size": int(len(simulation.truth.truth_grid)),
        "n_curves": n_curves,
        "n_components": int(fitted.n_components),
        "mean_ise": float(mean_ise[0]),
        "mean_latent_sampling_reference_ise": mean_sampling_reference,
        "mean_ise_sampling_reference_ratio": mean_sampling_ratio,
        "joint_covariance_ise": float(covariance_ise[0]),
        "cxy_ise": float(cxy[0]),
        "cxy_zero_baseline_ise": float(zero_cxy_ise),
        "minimum_subspace_principal_cosine": float(np.min(subspace)),
        "median_separated_score_correlation": (
            float(np.median(score_correlations))
            if score_correlations.size
            else np.nan
        ),
        "median_separated_score_rmse": (
            float(np.median(score_rmse))
            if score_rmse.size
            else np.nan
        ),
        "maximum_tied_score_subspace_procrustes_rmse": (
            float(np.max(procrustes))
            if procrustes.size
            else np.nan
        ),
        "reconstruction_ise": float(reconstruction[0]),
        "score_failure_rate": float(failure[0]),
        "score_condition_number_median": (
            float(condition_median[0])
            if condition_median.size
            else np.nan
        ),
        "score_condition_number_q95": (
            float(condition_q95[0])
            if condition_q95.size
            else np.nan
        ),
        "score_condition_number_max": (
            float(condition_max[0])
            if condition_max.size
            else np.nan
        ),
        "psd_relative_operator_correction": (
            float(psd[0]) if psd.size else np.nan
        ),
        "measurement_error_truth_supplied": bool(
            assessment.provenance[
                "measurement_error_truth_supplied"
            ]
        ),
        "tied_truth_component_groups": assessment.provenance[
            "tied_truth_component_groups"
        ],
    }


def _guard_row(row: dict[str, object]) -> list[str]:
    failures: list[str] = []
    finite_required = (
        "mean_ise",
        "mean_latent_sampling_reference_ise",
        "mean_ise_sampling_reference_ratio",
        "joint_covariance_ise",
        "cxy_ise",
        "minimum_subspace_principal_cosine",
        "reconstruction_ise",
        "score_failure_rate",
        "score_condition_number_median",
        "score_condition_number_q95",
        "score_condition_number_max",
        "psd_relative_operator_correction",
    )
    for key in finite_required:
        if not np.isfinite(float(row[key])):
            failures.append(f"{key}:nonfinite")

    if float(row["score_failure_rate"]) > QUALIFICATION_GUARDS[
        "score_failure_rate_max"
    ]:
        failures.append("score_failure_rate")
    if float(row["minimum_subspace_principal_cosine"]) < (
        QUALIFICATION_GUARDS[
            "minimum_subspace_principal_cosine_min"
        ]
    ):
        failures.append("minimum_subspace_principal_cosine")
    if float(row["mean_ise_sampling_reference_ratio"]) > (
        QUALIFICATION_GUARDS[
            "mean_ise_sampling_reference_ratio_max"
        ]
    ):
        failures.append("mean_ise_sampling_reference_ratio")
    if float(row["joint_covariance_ise"]) > QUALIFICATION_GUARDS[
        "joint_covariance_ise_max"
    ]:
        failures.append("joint_covariance_ise")
    if float(row["reconstruction_ise"]) > QUALIFICATION_GUARDS[
        "reconstruction_ise_max"
    ]:
        failures.append("reconstruction_ise")
    if float(row["psd_relative_operator_correction"]) > (
        QUALIFICATION_GUARDS[
            "psd_relative_operator_correction_max"
        ]
    ):
        failures.append("psd_relative_operator_correction")

    separated = float(row["median_separated_score_correlation"])
    tied = float(row["maximum_tied_score_subspace_procrustes_rmse"])
    if np.isfinite(separated):
        if separated < QUALIFICATION_GUARDS[
            "median_separated_score_correlation_min"
        ]:
            failures.append("median_separated_score_correlation")
    elif np.isfinite(tied):
        if tied > QUALIFICATION_GUARDS[
            "tied_score_subspace_procrustes_rmse_max"
        ]:
            failures.append("tied_score_subspace_procrustes_rmse")
    else:
        failures.append("score_identification_metric:missing")

    if not bool(row["measurement_error_truth_supplied"]):
        failures.append("measurement_error_truth_supplied")

    if row["case_type"] == "asymmetric_cxy":
        baseline = float(row["cxy_zero_baseline_ise"])
        if (
            baseline <= 0
            or float(row["cxy_ise"]) >= baseline
        ):
            failures.append("asymmetric_cxy_not_better_than_zero")

    return failures


def qualification_matrix() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    diagonal_noise = np.diag([0.0009, 0.0016])
    for index, rho in enumerate(RHO_FAMILY):
        eigenvalues, eigenfunctions = planar_rho_design(rho)
        scenario = _scenario(
            name=f"rho-{rho:+.1f}",
            grid_size=QUALIFICATION_GRID_SIZE,
            eigenvalues=eigenvalues,
            noise_covariance=diagonal_noise,
            seed=12000 + index,
            labels={
                "qualification": "native_sparse_mfpca",
                "rho_xy": rho,
                "marginal_covariance_contract": "fixed_across_rho",
            },
        )
        simulation = simulate_functional_scenario(
            scenario,
            mean=_mean_planar,
            eigenfunctions=eigenfunctions,
        )
        fitted = _fit_truth(simulation)
        rows.append(
            _assessment_row(
                case=scenario.name,
                simulation=simulation,
                fitted=fitted,
                rho_xy=rho,
                case_type="rho_family",
            )
        )

    asymmetric_values, asymmetric_functions = (
        asymmetric_cross_covariance_design()
    )
    asymmetric_scenario = _scenario(
        name="asymmetric-cxy",
        grid_size=QUALIFICATION_GRID_SIZE,
        eigenvalues=asymmetric_values,
        noise_covariance=diagonal_noise,
        seed=12100,
        labels={
            "qualification": "native_sparse_mfpca",
            "cross_covariance": "directional_asymmetric",
        },
    )
    asymmetric_simulation = simulate_functional_scenario(
        asymmetric_scenario,
        mean=_mean_planar,
        eigenfunctions=asymmetric_functions,
    )
    rows.append(
        _assessment_row(
            case=asymmetric_scenario.name,
            simulation=asymmetric_simulation,
            fitted=_fit_truth(asymmetric_simulation),
            rho_xy=None,
            case_type="asymmetric_cxy",
        )
    )

    correlated_noise = np.array(
        [
            [0.0009, 0.0003],
            [0.0003, 0.0016],
        ],
        dtype=float,
    )
    correlated_values, correlated_functions = planar_rho_design(0.6)
    correlated_scenario = _scenario(
        name="correlated-measurement-error",
        grid_size=QUALIFICATION_GRID_SIZE,
        eigenvalues=correlated_values,
        noise_covariance=correlated_noise,
        seed=12200,
        labels={
            "qualification": "native_sparse_mfpca",
            "measurement_error": "fixed_correlated_matrix",
        },
    )
    correlated_simulation = simulate_functional_scenario(
        correlated_scenario,
        mean=_mean_planar,
        eigenfunctions=correlated_functions,
    )
    rows.append(
        _assessment_row(
            case=correlated_scenario.name,
            simulation=correlated_simulation,
            fitted=_fit_truth(correlated_simulation),
            rho_xy=0.6,
            case_type="correlated_measurement_error",
        )
    )

    frame = pd.DataFrame(rows)
    guard_failures = [
        _guard_row(row)
        for row in frame.to_dict(orient="records")
    ]
    frame["guard_failures"] = [
        ";".join(values) for values in guard_failures
    ]
    frame["qualified"] = [not values for values in guard_failures]
    return frame


def grid_sensitivity() -> pd.DataFrame:
    """Descriptive grid refinement; no grid is selected from this table."""

    rows: list[dict[str, object]] = []
    eigenvalues, eigenfunctions = planar_rho_design(0.6)
    noise = np.diag([0.0009, 0.0016])
    for grid_size in GRID_SIZES:
        scenario = _scenario(
            name=f"grid-{grid_size}",
            grid_size=grid_size,
            eigenvalues=eigenvalues,
            noise_covariance=noise,
            seed=13000,
            n_participants=28,
            samples_per_curve=(20, 26),
            labels={
                "sensitivity": "evaluation_grid",
                "selection_performed": False,
            },
        )
        simulation = simulate_functional_scenario(
            scenario,
            mean=_mean_planar,
            eigenfunctions=eigenfunctions,
        )
        row = _assessment_row(
            case=scenario.name,
            simulation=simulation,
            fitted=_fit_truth(simulation),
            rho_xy=0.6,
            case_type="grid_sensitivity",
        )
        row["selection_performed"] = False
        rows.append(row)
    return pd.DataFrame(rows)


def ridge_sensitivity() -> pd.DataFrame:
    """Descriptive score-ridge sensitivity; no ridge is selected."""

    eigenvalues, eigenfunctions = planar_rho_design(0.6)
    scenario = _scenario(
        name="ridge-sensitivity",
        grid_size=QUALIFICATION_GRID_SIZE,
        eigenvalues=eigenvalues,
        noise_covariance=np.diag([0.0009, 0.0016]),
        seed=14000,
        n_participants=28,
        samples_per_curve=(20, 26),
        labels={
            "sensitivity": "score_ridge",
            "selection_performed": False,
        },
    )
    simulation = simulate_functional_scenario(
        scenario,
        mean=_mean_planar,
        eigenfunctions=eigenfunctions,
    )
    rows: list[dict[str, object]] = []
    for ridge in RIDGES:
        row = _assessment_row(
            case=f"ridge-{ridge:.0e}",
            simulation=simulation,
            fitted=_fit_truth(
                simulation,
                score_ridge=ridge,
            ),
            rho_xy=0.6,
            case_type="ridge_sensitivity",
        )
        row["score_ridge"] = float(ridge)
        row["selection_performed"] = False
        rows.append(row)
    return pd.DataFrame(rows)


def run_validation(
    *,
    mode: str = "all",
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if mode not in {"all", "qualification", "sensitivity"}:
        raise ValueError(
            "mode must be 'all', 'qualification', or 'sensitivity'"
        )
    qualification = (
        qualification_matrix()
        if mode in {"all", "qualification"}
        else pd.DataFrame()
    )
    grid = (
        grid_sensitivity()
        if mode in {"all", "sensitivity"}
        else pd.DataFrame()
    )
    ridge = (
        ridge_sensitivity()
        if mode in {"all", "sensitivity"}
        else pd.DataFrame()
    )
    return qualification, grid, ridge


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-json",
        default="sparse-mfpca-recovery-validation.json",
    )
    parser.add_argument(
        "--qualification-csv",
        default="sparse-mfpca-recovery-qualification.csv",
    )
    parser.add_argument(
        "--grid-csv",
        default="sparse-mfpca-grid-sensitivity.csv",
    )
    parser.add_argument(
        "--ridge-csv",
        default="sparse-mfpca-ridge-sensitivity.csv",
    )
    parser.add_argument(
        "--mode",
        choices=("all", "qualification", "sensitivity"),
        default="all",
    )
    args = parser.parse_args()

    qualification, grid, ridge = run_validation(mode=args.mode)
    Path(args.qualification_csv).parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    if len(qualification):
        qualification.to_csv(args.qualification_csv, index=False)
    if len(grid):
        grid.to_csv(args.grid_csv, index=False)
    if len(ridge):
        ridge.to_csv(args.ridge_csv, index=False)

    qualified = (
        bool(qualification["qualified"].all())
        if len(qualification)
        else None
    )
    payload = {
        "evidence_type": "simulation_recovery",
        "estimator": "fit_sparse_mfpca",
        "qualification_qualified": qualified,
        "qualification_guards": QUALIFICATION_GUARDS,
        "rho_family": list(RHO_FAMILY),
        "qualification": qualification.to_dict(orient="records"),
        "grid_sensitivity": grid.to_dict(orient="records"),
        "ridge_sensitivity": ridge.to_dict(orient="records"),
        "sensitivity_selection_performed": False,
        "external_comparator_included": False,
        "measurement_error_recovery_claim": False,
        "notes": [
            "Covariance recovery is evaluated block-wise in named x/y coordinates before joint aggregation.",
            "Exact tied truth eigenspaces omit component-specific eigenfunction/score recovery and use subspace geometry plus Procrustes score RMSE.",
            "Grid and ridge tables are descriptive sensitivity evidence and do not select tuning parameters.",
        ],
    }
    Path(args.output_json).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if len(qualification):
        print("QUALIFICATION_EVIDENCE")
        print(qualification.to_string(index=False))
    if len(grid):
        print("GRID_SENSITIVITY_EVIDENCE")
        print(grid.to_string(index=False))
    if len(ridge):
        print("RIDGE_SENSITIVITY_EVIDENCE")
        print(ridge.to_string(index=False))
    if len(qualification) and not qualified:
        failures = qualification.loc[
            ~qualification["qualified"],
            ["case", "guard_failures"],
        ]
        raise RuntimeError(
            "sparse MFPCA qualification guards failed: "
            + failures.to_dict(orient="records").__repr__()
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
