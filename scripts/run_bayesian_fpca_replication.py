#!/usr/bin/env python3
"""B2 replicated recovery/fairness evidence for the post-1.1 Bayesian comparator.

This script generates repeated known-truth fixtures, runs the native fixed
baseline, runs the predeclared native bandwidth-selection sensitivity on a
subset, and exports neutral inputs for the external Bayesian comparator.

B2 is evidence only: no estimator/API/default/dependency is changed and no B4
decision is made.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import importlib.metadata
import importlib.util
import json
from pathlib import Path
import sys
import time

import numpy as np
import pandas as pd

from eyetrajectoriespy import (
    IrregularTrajectorySet,
    fit_sparse_fpca,
    fit_sparse_mfpca,
)
from eyetrajectoriespy.sparse_bandwidth_selection import (
    select_sparse_fpca_bandwidths,
)
from eyetrajectoriespy.sparse_multivariate_async import (
    fit_sparse_mfpca_async,
)
from eyetrajectoriespy.sparse_multivariate_bandwidth_selection import (
    select_sparse_mfpca_bandwidths,
)
from eyetrajectoriespy.sparse_multivariate_score_uncertainty import (
    sparse_mfpca_score_uncertainty,
)
from eyetrajectoriespy.sparse_score_uncertainty import (
    sparse_fpca_score_uncertainty,
)


N_COMPONENTS = 2
NOISE_SD = 0.05
BAYESFPCA_COMMIT = "f05b0615632cffe5c63838858d9a956af6588a73"
PRIMARY_REPLICATES = 16
FAIRNESS_REPLICATES = 4
K_CANDIDATES = (5, 6, 7, 8, 9)
BANDWIDTH_FACTORS = (0.75, 1.0, 1.25)


def _load_b1():
    path = Path(__file__).with_name("run_bayesian_fpca_comparator.py")
    spec = importlib.util.spec_from_file_location(
        "_b1_bayesian_fpca",
        path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load B1 comparator helpers")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


B1 = _load_b1()


@dataclass(frozen=True)
class ReplicationScenario:
    name: str
    design: str
    n_curves: int
    samples_min: int
    samples_max: int
    eigenvalues: tuple[float, float]
    mean_bandwidth: float
    covariance_bandwidth: float
    truth_family: str
    observation_mechanism: str
    seed_base: int


SCENARIOS = (
    ReplicationScenario(
        "univariate_moderate",
        "univariate",
        32,
        12,
        18,
        (1.00, 0.40),
        0.20,
        0.30,
        "harmonic",
        "iid_uniform",
        2026120100,
    ),
    ReplicationScenario(
        "univariate_extreme_sparse",
        "univariate",
        32,
        6,
        9,
        (1.00, 0.40),
        0.28,
        0.38,
        "harmonic",
        "iid_uniform",
        2026120200,
    ),
    ReplicationScenario(
        "univariate_low_n",
        "univariate",
        14,
        12,
        18,
        (1.00, 0.40),
        0.22,
        0.32,
        "harmonic",
        "iid_uniform",
        2026120300,
    ),
    ReplicationScenario(
        "univariate_near_tied",
        "univariate",
        32,
        12,
        18,
        (1.00, 0.90),
        0.20,
        0.30,
        "harmonic",
        "iid_uniform",
        2026120400,
    ),
    ReplicationScenario(
        "univariate_localized",
        "univariate",
        32,
        12,
        18,
        (1.00, 0.40),
        0.18,
        0.28,
        "localized_triangular",
        "iid_uniform",
        2026120500,
    ),
    ReplicationScenario(
        "univariate_informative_time",
        "univariate",
        32,
        2,
        31,
        (1.00, 0.40),
        0.20,
        0.30,
        "harmonic",
        "logistic_candidate_time",
        2026120600,
    ),
    ReplicationScenario(
        "planar_paired",
        "planar_paired",
        28,
        12,
        18,
        (1.10, 0.55),
        0.22,
        0.32,
        "harmonic",
        "iid_uniform",
        2026120700,
    ),
    ReplicationScenario(
        "planar_async",
        "planar_async",
        28,
        8,
        12,
        (1.10, 0.55),
        0.25,
        0.36,
        "harmonic",
        "iid_uniform",
        2026120800,
    ),
)

FAIRNESS_SCENARIOS = {
    "univariate_extreme_sparse",
    "univariate_low_n",
    "univariate_near_tied",
    "univariate_localized",
    "planar_paired",
}


def _localized_modes(time_values: np.ndarray) -> np.ndarray:
    time_values = np.asarray(time_values, dtype=float)
    half_width = 0.18
    norm = np.sqrt(2.0 * half_width / 3.0)
    first = (
        np.maximum(
            1.0 - np.abs(time_values - 0.30) / half_width,
            0.0,
        )
        / norm
    )
    second = (
        np.maximum(
            1.0 - np.abs(time_values - 0.70) / half_width,
            0.0,
        )
        / norm
    )
    return np.stack((first[:, None], second[:, None]), axis=0)


def _modes(
    time_values: np.ndarray,
    scenario: ReplicationScenario,
) -> np.ndarray:
    if scenario.truth_family == "localized_triangular":
        return _localized_modes(time_values)
    return B1._modes(time_values, scenario.design)


def _mean(
    time_values: np.ndarray,
    scenario: ReplicationScenario,
) -> np.ndarray:
    return B1._mean(time_values, scenario.design)


def _latent(
    time_values: np.ndarray,
    scores: np.ndarray,
    scenario: ReplicationScenario,
) -> np.ndarray:
    return _mean(time_values, scenario) + np.einsum(
        "k,ktd->td",
        scores,
        _modes(time_values, scenario),
        optimize=True,
    )


def _uniform_times(
    rng: np.random.Generator,
    low: int,
    high: int,
) -> np.ndarray:
    count = int(rng.integers(low, high + 1))
    if count < 2:
        raise ValueError("sample count must be at least two")
    interior = rng.uniform(0.02, 0.98, size=count - 2)
    return np.sort(np.concatenate(([0.02], interior, [0.98])))


def _informative_times(
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    candidate = np.linspace(0.02, 0.98, 31)
    probability = 1.0 / (
        1.0 + np.exp(-(1.4 - 2.5 * candidate))
    )
    retained = rng.random(candidate.size) < probability
    if np.count_nonzero(retained) < 2:
        raise RuntimeError(
            "informative-time replicate retained fewer than two samples"
        )
    return candidate[retained], probability[retained]


def _make_dataset(
    scenario: ReplicationScenario,
    seed: int,
) -> tuple[
    IrregularTrajectorySet,
    dict[str, object],
    dict[str, list[tuple[str, np.ndarray, np.ndarray]]],
    np.ndarray,
]:
    rng = np.random.default_rng(seed)
    dimensions = (
        ("x",)
        if scenario.design == "univariate"
        else ("x", "y")
    )
    eigenvalues = np.asarray(scenario.eigenvalues, dtype=float)
    scores = (
        rng.normal(
            size=(scenario.n_curves, N_COMPONENTS)
        )
        * np.sqrt(eigenvalues)[None, :]
    )
    curve_ids = tuple(
        f"curve_{index + 1:03d}"
        for index in range(scenario.n_curves)
    )

    times: list[np.ndarray] = []
    values: list[np.ndarray] = []
    observed: dict[
        str,
        list[tuple[str, np.ndarray, np.ndarray]],
    ] = {dimension: [] for dimension in dimensions}
    retained_probabilities: list[list[float]] = []

    for curve_index, curve_id in enumerate(curve_ids):
        if scenario.design == "planar_async":
            x_time = _uniform_times(
                rng,
                scenario.samples_min,
                scenario.samples_max,
            )
            y_time = _uniform_times(
                rng,
                scenario.samples_min,
                scenario.samples_max,
            )
            x_value = (
                _latent(
                    x_time,
                    scores[curve_index],
                    scenario,
                )[:, 0]
                + rng.normal(
                    scale=NOISE_SD,
                    size=x_time.size,
                )
            )
            y_value = (
                _latent(
                    y_time,
                    scores[curve_index],
                    scenario,
                )[:, 1]
                + rng.normal(
                    scale=NOISE_SD,
                    size=y_time.size,
                )
            )
            union = np.union1d(x_time, y_time)
            matrix = np.full(
                (union.size, 2),
                np.nan,
                dtype=float,
            )
            matrix[
                np.searchsorted(union, x_time),
                0,
            ] = x_value
            matrix[
                np.searchsorted(union, y_time),
                1,
            ] = y_value
            times.append(union)
            values.append(matrix)
            observed["x"].append(
                (curve_id, x_time, x_value)
            )
            observed["y"].append(
                (curve_id, y_time, y_value)
            )
            continue

        if (
            scenario.observation_mechanism
            == "logistic_candidate_time"
        ):
            curve_time, retained_probability = (
                _informative_times(rng)
            )
            retained_probabilities.append(
                retained_probability.tolist()
            )
        else:
            curve_time = _uniform_times(
                rng,
                scenario.samples_min,
                scenario.samples_max,
            )

        latent = _latent(
            curve_time,
            scores[curve_index],
            scenario,
        )
        observed_values = latent + rng.normal(
            scale=NOISE_SD,
            size=latent.shape,
        )
        times.append(curve_time)
        values.append(observed_values)
        for dimension_index, dimension in enumerate(
            dimensions
        ):
            observed[dimension].append(
                (
                    curve_id,
                    curve_time,
                    observed_values[
                        :,
                        dimension_index,
                    ],
                )
            )

    pooled = np.concatenate(
        [
            item[1]
            for curves in observed.values()
            for item in curves
        ]
    )
    grid = np.linspace(
        float(np.min(pooled)),
        float(np.max(pooled)),
        41,
    )

    dataset = IrregularTrajectorySet(
        time=tuple(times),
        values=tuple(values),
        curve_ids=curve_ids,
        dimension_names=dimensions,
        metadata=pd.DataFrame(
            {
                "participant_id": curve_ids,
                "scenario": scenario.name,
            }
        ),
        coordinate_system="normalized",
        time_unit="normalized",
        provenance={
            "programme": "post-1.1-bayesian-fpca-b2",
            "scenario": scenario.name,
            "replicate_seed": seed,
            "known_truth": True,
            "raw_interpolation": False,
        },
    )

    truth_modes = _modes(grid, scenario)
    truth_mean = _mean(grid, scenario)
    truth_latent = np.stack(
        [
            truth_mean
            + np.einsum(
                "k,kgd->gd",
                score,
                truth_modes,
                optimize=True,
            )
            for score in scores
        ],
        axis=0,
    )
    truth: dict[str, object] = {
        "schema_version": 1,
        "scenario": scenario.name,
        "seed": seed,
        "design": scenario.design,
        "truth_family": scenario.truth_family,
        "observation_mechanism": (
            scenario.observation_mechanism
        ),
        "truth_grid": grid.tolist(),
        "dimension_names": list(dimensions),
        "curve_ids": list(curve_ids),
        "eigenvalues": eigenvalues.tolist(),
        "eigenfunctions": truth_modes.tolist(),
        "scores": scores.tolist(),
        "mean": truth_mean.tolist(),
        "latent_on_truth_grid": (
            truth_latent.tolist()
        ),
        "noise_sd": NOISE_SD,
        "mean_bandwidth": (
            scenario.mean_bandwidth
        ),
        "covariance_bandwidth": (
            scenario.covariance_bandwidth
        ),
        "retention": (
            {
                "candidate_grid_size": 31,
                "logit_intercept": 1.4,
                "logit_slope": -2.5,
                "retained_probabilities": (
                    retained_probabilities
                ),
            }
            if scenario.observation_mechanism
            == "logistic_candidate_time"
            else None
        ),
        "contract": {
            "equivalence_claim": False,
            "architecture_winner_selected": False,
            "automatic_promotion_decision": False,
            "b4_decision": "deferred",
            "informative_observation_is_sensitivity_only": (
                scenario.observation_mechanism
                == "logistic_candidate_time"
            ),
            "raw_interpolation": False,
        },
    }
    return dataset, truth, observed, grid


def _fit_native(
    scenario: ReplicationScenario,
    dataset: IrregularTrajectorySet,
    grid: np.ndarray,
    *,
    mean_bw: float,
    covariance_bw: float,
):
    common = dict(
        n_components=N_COMPONENTS,
        evaluation_grid=grid,
        mean_bandwidth=mean_bw,
        covariance_bandwidth=covariance_bw,
        psd_action="project",
        score_failure_action="retain_nan",
    )
    if scenario.design == "univariate":
        return fit_sparse_fpca(
            dataset,
            dimension="x",
            noise_variance_method="fixed",
            measurement_error_variance=(
                NOISE_SD**2
            ),
            **common,
        )
    if scenario.design == "planar_paired":
        return fit_sparse_mfpca(
            dataset,
            dimensions=("x", "y"),
            measurement_error="diagonal",
            measurement_error_variance=(
                NOISE_SD**2,
                NOISE_SD**2,
            ),
            **common,
        )
    return fit_sparse_mfpca_async(
        dataset,
        dimensions=("x", "y"),
        measurement_error="diagonal",
        measurement_error_variance=(
            NOISE_SD**2,
            NOISE_SD**2,
        ),
        **common,
    )


def _write_score_covariance(
    path: Path,
    curve_ids: tuple[str, ...],
    covariance: np.ndarray,
) -> None:
    rows = []
    for curve_index, curve_id in enumerate(
        curve_ids
    ):
        for first in range(
            covariance.shape[1]
        ):
            for second in range(
                covariance.shape[2]
            ):
                rows.append(
                    {
                        "curve_id": curve_id,
                        "component_i": first + 1,
                        "component_j": second + 1,
                        "covariance": float(
                            covariance[
                                curve_index,
                                first,
                                second,
                            ]
                        ),
                    }
                )
    pd.DataFrame(rows).to_csv(
        path,
        index=False,
    )


def _write_fit(
    root: Path,
    prefix: str,
    fit,
    scenario: ReplicationScenario,
    dataset: IrregularTrajectorySet,
    grid: np.ndarray,
    elapsed: float,
) -> None:
    functions = B1._function_array(
        fit,
        scenario.design,
    )
    mean = B1._mean_array(
        fit,
        scenario.design,
    )
    B1._write_mean(
        root / f"{prefix}_mean.csv",
        grid,
        dataset.dimension_names,
        mean,
    )
    B1._write_function_long(
        root / f"{prefix}_eigenfunctions.csv",
        grid,
        dataset.dimension_names,
        functions,
    )
    scores = np.asarray(
        fit.scores,
        dtype=float,
    )
    B1._write_scores(
        root / f"{prefix}_scores.csv",
        dataset.curve_ids,
        scores,
    )
    pd.DataFrame(
        {
            "component": np.arange(
                1,
                N_COMPONENTS + 1,
            ),
            "eigenvalue": np.asarray(
                fit.eigenvalues,
                dtype=float,
            )[:N_COMPONENTS],
        }
    ).to_csv(
        root / f"{prefix}_eigenvalues.csv",
        index=False,
    )
    (
        root / f"{prefix}_status.json"
    ).write_text(
        json.dumps(
            {
                "status": "ok",
                "elapsed_seconds": elapsed,
                "score_failure_rate": float(
                    np.mean(
                        ~np.all(
                            np.isfinite(scores),
                            axis=1,
                        )
                    )
                ),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    # Retained raw inputs for B3 only. B2 does
    # not interpret these covariance values.
    if prefix == "native_fixed":
        if scenario.design == "univariate":
            uncertainty = (
                sparse_fpca_score_uncertainty(
                    fit,
                    dataset,
                    failure_action="retain_nan",
                )
            )
            _write_score_covariance(
                root
                / "native_fixed_score_covariance.csv",
                dataset.curve_ids,
                uncertainty.covariance,
            )
        elif scenario.design == "planar_paired":
            uncertainty = (
                sparse_mfpca_score_uncertainty(
                    fit,
                    dataset,
                    failure_action="retain_nan",
                )
            )
            _write_score_covariance(
                root
                / "native_fixed_score_covariance.csv",
                dataset.curve_ids,
                uncertainty.covariance,
            )


def _write_failure(
    root: Path,
    prefix: str,
    exc: Exception,
    elapsed: float,
) -> None:
    (
        root / f"{prefix}_status.json"
    ).write_text(
        json.dumps(
            {
                "status": "failed",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "elapsed_seconds": elapsed,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _candidate_grid(
    value: float,
) -> tuple[float, ...]:
    return tuple(
        float(value * factor)
        for factor in BANDWIDTH_FACTORS
    )


def _fit_selected(
    scenario: ReplicationScenario,
    dataset: IrregularTrajectorySet,
    grid: np.ndarray,
    seed: int,
    root: Path,
):
    if scenario.design == "univariate":
        selection = (
            select_sparse_fpca_bandwidths(
                dataset,
                dimension="x",
                evaluation_grid=grid,
                mean_bandwidths=_candidate_grid(
                    scenario.mean_bandwidth
                ),
                covariance_bandwidths=(
                    _candidate_grid(
                        scenario.covariance_bandwidth
                    )
                ),
                noise_variance_method="fixed",
                measurement_error_variance=(
                    NOISE_SD**2
                ),
                n_splits=3,
                resampling_unit="curve",
                shuffle=True,
                random_state=seed,
                failure_action="retain",
                psd_action="project",
            )
        )
    elif scenario.design == "planar_paired":
        selection = (
            select_sparse_mfpca_bandwidths(
                dataset,
                dimensions=("x", "y"),
                evaluation_grid=grid,
                mean_bandwidths=_candidate_grid(
                    scenario.mean_bandwidth
                ),
                covariance_bandwidths=(
                    _candidate_grid(
                        scenario.covariance_bandwidth
                    )
                ),
                measurement_error="diagonal",
                measurement_error_variance=(
                    NOISE_SD**2,
                    NOISE_SD**2,
                ),
                n_splits=3,
                resampling_unit="curve",
                shuffle=True,
                random_state=seed,
                failure_action="retain",
                psd_action="project",
            )
        )
    else:
        return None

    for name in (
        "assignments",
        "fold_results",
        "curve_losses",
        "candidate_summary",
        "candidates",
    ):
        getattr(selection, name).to_csv(
            root
            / f"native_selection_{name}.csv",
            index=False,
        )

    selected = selection.selected_bandwidths
    (
        root / "native_selection.json"
    ).write_text(
        json.dumps(
            {
                "status_code": (
                    selection.status_code
                ),
                "selected_bandwidths": selected,
            },
            indent=2,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )
    if selected is None:
        return None
    return _fit_native(
        scenario,
        dataset,
        grid,
        mean_bw=float(
            selected["mean_bandwidth"]
        ),
        covariance_bw=float(
            selected["covariance_bandwidth"]
        ),
    )


def generate(
    output_dir: Path,
    *,
    replicates: int,
    fairness_replicates: int,
) -> dict[str, object]:
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )
    rows = []

    for scenario in SCENARIOS:
        for replicate in range(replicates):
            seed = (
                scenario.seed_base
                + replicate
            )
            root = (
                output_dir
                / "scenarios"
                / scenario.name
                / f"replicate_{replicate:03d}"
            )
            root.mkdir(
                parents=True,
                exist_ok=True,
            )
            (
                dataset,
                truth,
                observed,
                grid,
            ) = _make_dataset(
                scenario,
                seed,
            )
            B1._write_observations(
                root,
                observed,
            )
            (
                root / "truth.json"
            ).write_text(
                json.dumps(
                    truth,
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            pd.DataFrame(
                {"time": grid}
            ).to_csv(
                root / "truth_grid.csv",
                index=False,
            )

            start = time.perf_counter()
            try:
                fixed_fit = _fit_native(
                    scenario,
                    dataset,
                    grid,
                    mean_bw=(
                        scenario.mean_bandwidth
                    ),
                    covariance_bw=(
                        scenario.covariance_bandwidth
                    ),
                )
                _write_fit(
                    root,
                    "native_fixed",
                    fixed_fit,
                    scenario,
                    dataset,
                    grid,
                    (
                        time.perf_counter()
                        - start
                    ),
                )
            except Exception as exc:
                _write_failure(
                    root,
                    "native_fixed",
                    exc,
                    (
                        time.perf_counter()
                        - start
                    ),
                )

            fairness = (
                replicate
                < fairness_replicates
                and scenario.name
                in FAIRNESS_SCENARIOS
            )
            if fairness:
                start = time.perf_counter()
                try:
                    selected_fit = (
                        _fit_selected(
                            scenario,
                            dataset,
                            grid,
                            seed,
                            root,
                        )
                    )
                    if selected_fit is None:
                        raise RuntimeError(
                            "no eligible native "
                            "bandwidth candidate"
                        )
                    _write_fit(
                        root,
                        "native_selected",
                        selected_fit,
                        scenario,
                        dataset,
                        grid,
                        (
                            time.perf_counter()
                            - start
                        ),
                    )
                except Exception as exc:
                    _write_failure(
                        root,
                        "native_selected",
                        exc,
                        (
                            time.perf_counter()
                            - start
                        ),
                    )

            rows.append(
                {
                    "scenario": scenario.name,
                    "replicate": replicate,
                    "seed": seed,
                    "design": scenario.design,
                    "truth_family": (
                        scenario.truth_family
                    ),
                    "observation_mechanism": (
                        scenario.observation_mechanism
                    ),
                    "n_curves": scenario.n_curves,
                    "n_components": (
                        N_COMPONENTS
                    ),
                    "spline_basis_size": 7,
                    "fairness": fairness,
                }
            )

    pd.DataFrame(rows).to_csv(
        output_dir / "manifest.csv",
        index=False,
    )
    payload = {
        "schema_version": 1,
        "programme": (
            "post-1.1-bayesian-fpca-b2-replication"
        ),
        "eyetrajectoriespy_version": (
            importlib.metadata.version(
                "eyetrajectoriespy"
            )
        ),
        "bayesfpca_commit": BAYESFPCA_COMMIT,
        "primary_replicates": replicates,
        "fairness_replicates": (
            fairness_replicates
        ),
        "k_candidates": list(K_CANDIDATES),
        "bandwidth_factors": list(
            BANDWIDTH_FACTORS
        ),
        "scenario_names": [
            scenario.name
            for scenario in SCENARIOS
        ],
        "b4_decision": "deferred",
        "qualification_thresholds_introduced": False,
        "architecture_winner_selected": False,
        "automatic_promotion_decision": False,
        "p_values_computed": False,
        "raw_interpolation": False,
        "uncertainty_outputs_retained_for_later_b3_only": True,
    }
    (
        output_dir / "manifest.json"
    ).write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--replicates",
        type=int,
        default=PRIMARY_REPLICATES,
    )
    parser.add_argument(
        "--fairness-replicates",
        type=int,
        default=FAIRNESS_REPLICATES,
    )
    args = parser.parse_args()

    if args.replicates != PRIMARY_REPLICATES:
        raise ValueError(
            "B2 primary design is frozen at "
            f"{PRIMARY_REPLICATES} replicates"
        )
    if (
        args.fairness_replicates
        != FAIRNESS_REPLICATES
    ):
        raise ValueError(
            "B2 fairness design is frozen at "
            f"{FAIRNESS_REPLICATES} replicates"
        )

    payload = generate(
        args.output_dir,
        replicates=args.replicates,
        fairness_replicates=(
            args.fairness_replicates
        ),
    )
    print(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
