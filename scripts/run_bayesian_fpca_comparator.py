"""Generate frozen native/known-truth fixtures for Bayesian FPCA sensitivity.

This is an external-comparator evidence harness for post-1.1 development.
It does not implement a Bayesian estimator and does not import bayesFPCA.
All source data are generated independently by eyetrajectoriespy/Python and
exported as neutral CSV/JSON files for a separately installed R comparator.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import importlib.metadata
import json
from pathlib import Path
import time

import numpy as np
import pandas as pd

from eyetrajectoriespy import IrregularTrajectorySet, fit_sparse_fpca, fit_sparse_mfpca
from eyetrajectoriespy.sparse_multivariate_async import fit_sparse_mfpca_async


GRID = np.linspace(0.0, 1.0, 41)
N_COMPONENTS = 2
NOISE_SD = 0.05
BAYESFPCA_COMMIT = "f05b0615632cffe5c63838858d9a956af6588a73"


@dataclass(frozen=True)
class Scenario:
    name: str
    design: str
    n_curves: int
    samples_min: int
    samples_max: int
    eigenvalues: tuple[float, float]
    seed: int
    mean_bandwidth: float
    covariance_bandwidth: float


SCENARIOS = (
    Scenario(
        "univariate_moderate",
        "univariate",
        32,
        12,
        18,
        (1.00, 0.40),
        2026110101,
        0.20,
        0.30,
    ),
    Scenario(
        "univariate_extreme_sparse",
        "univariate",
        32,
        6,
        9,
        (1.00, 0.40),
        2026110102,
        0.28,
        0.38,
    ),
    Scenario(
        "univariate_low_n_near_tied",
        "univariate",
        14,
        10,
        14,
        (1.00, 0.90),
        2026110103,
        0.25,
        0.34,
    ),
    Scenario(
        "planar_paired",
        "planar_paired",
        28,
        12,
        18,
        (1.10, 0.55),
        2026110104,
        0.22,
        0.32,
    ),
    Scenario(
        "planar_async",
        "planar_async",
        28,
        8,
        12,
        (1.10, 0.55),
        2026110105,
        0.25,
        0.36,
    ),
)


def _scalar_modes(time_values: np.ndarray) -> np.ndarray:
    time_values = np.asarray(time_values, dtype=float)
    return np.column_stack(
        (
            np.sqrt(2.0) * np.sin(np.pi * time_values),
            np.sqrt(2.0) * np.sin(2.0 * np.pi * time_values),
        )
    )


def _mean(time_values: np.ndarray, design: str) -> np.ndarray:
    time_values = np.asarray(time_values, dtype=float)
    if design == "univariate":
        return (0.20 + 0.10 * time_values + 0.04 * np.sin(np.pi * time_values))[:, None]
    return np.column_stack(
        (
            0.50 + 0.05 * np.sin(np.pi * time_values),
            0.50 + 0.05 * np.cos(np.pi * time_values),
        )
    )


def _modes(time_values: np.ndarray, design: str) -> np.ndarray:
    scalar = _scalar_modes(time_values)
    if design == "univariate":
        return scalar[:, :, None].transpose(1, 0, 2)
    plus = np.array([1.0, 1.0], dtype=float) / np.sqrt(2.0)
    minus = np.array([1.0, -1.0], dtype=float) / np.sqrt(2.0)
    return np.stack(
        (
            scalar[:, 0, None] * plus[None, :],
            scalar[:, 1, None] * minus[None, :],
        ),
        axis=0,
    )


def _latent(
    time_values: np.ndarray,
    scores: np.ndarray,
    design: str,
) -> np.ndarray:
    return _mean(time_values, design) + np.einsum(
        "k,ktd->td",
        scores,
        _modes(time_values, design),
        optimize=True,
    )


def _sample_times(
    rng: np.random.Generator,
    low: int,
    high: int,
) -> np.ndarray:
    count = int(rng.integers(low, high + 1))
    return np.sort(rng.uniform(0.02, 0.98, size=count))


def _make_dataset(scenario: Scenario) -> tuple[IrregularTrajectorySet, dict[str, object]]:
    rng = np.random.default_rng(scenario.seed)
    dimensions = ("x",) if scenario.design == "univariate" else ("x", "y")
    eigenvalues = np.asarray(scenario.eigenvalues, dtype=float)
    scores = rng.normal(size=(scenario.n_curves, N_COMPONENTS)) * np.sqrt(
        eigenvalues
    )[None, :]
    curve_ids = tuple(f"curve_{index + 1:03d}" for index in range(scenario.n_curves))

    times: list[np.ndarray] = []
    values: list[np.ndarray] = []
    observed_by_dimension: dict[str, list[tuple[str, np.ndarray, np.ndarray]]] = {
        dimension: [] for dimension in dimensions
    }

    for curve_index, curve_id in enumerate(curve_ids):
        if scenario.design != "planar_async":
            curve_time = _sample_times(
                rng,
                scenario.samples_min,
                scenario.samples_max,
            )
            latent = _latent(curve_time, scores[curve_index], scenario.design)
            observed = latent + rng.normal(scale=NOISE_SD, size=latent.shape)
            times.append(curve_time)
            values.append(observed)
            for dim_index, dimension in enumerate(dimensions):
                observed_by_dimension[dimension].append(
                    (curve_id, curve_time, observed[:, dim_index])
                )
            continue

        x_time = _sample_times(rng, scenario.samples_min, scenario.samples_max)
        y_time = _sample_times(rng, scenario.samples_min, scenario.samples_max)
        x_latent = _latent(x_time, scores[curve_index], scenario.design)[:, 0]
        y_latent = _latent(y_time, scores[curve_index], scenario.design)[:, 1]
        x_value = x_latent + rng.normal(scale=NOISE_SD, size=x_time.size)
        y_value = y_latent + rng.normal(scale=NOISE_SD, size=y_time.size)
        union = np.union1d(x_time, y_time)
        matrix = np.full((union.size, 2), np.nan, dtype=float)
        matrix[np.searchsorted(union, x_time), 0] = x_value
        matrix[np.searchsorted(union, y_time), 1] = y_value
        times.append(union)
        values.append(matrix)
        observed_by_dimension["x"].append((curve_id, x_time, x_value))
        observed_by_dimension["y"].append((curve_id, y_time, y_value))

    dataset = IrregularTrajectorySet(
        time=tuple(times),
        values=tuple(values),
        curve_ids=curve_ids,
        dimension_names=dimensions,
        metadata=pd.DataFrame(
            {
                "participant_id": list(curve_ids),
                "scenario": scenario.name,
            }
        ),
        coordinate_system="normalized",
        time_unit="normalized",
        provenance={
            "programme": "post-1.1-bayesian-fpca-comparator",
            "scenario": scenario.name,
            "known_truth": True,
            "raw_interpolation": False,
        },
    )
    truth_modes = _modes(GRID, scenario.design)
    truth_mean = _mean(GRID, scenario.design)
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
        "design": scenario.design,
        "known_truth": True,
        "truth_grid": GRID.tolist(),
        "dimension_names": list(dimensions),
        "curve_ids": list(curve_ids),
        "eigenvalues": eigenvalues.tolist(),
        "eigenfunctions": truth_modes.tolist(),
        "scores": scores.tolist(),
        "mean": truth_mean.tolist(),
        "latent_on_truth_grid": truth_latent.tolist(),
        "noise_sd": NOISE_SD,
        "mean_bandwidth": scenario.mean_bandwidth,
        "covariance_bandwidth": scenario.covariance_bandwidth,
        "observation_counts": {
            dimension: [
                int(item[1].size) for item in observed_by_dimension[dimension]
            ]
            for dimension in dimensions
        },
        "contract": {
            "equivalence_claim": False,
            "architecture_winner_selected": False,
            "automatic_promotion_decision": False,
            "raw_interpolation": False,
            "external_runtime_backend": False,
        },
    }
    return dataset, {"truth": truth, "observed": observed_by_dimension}


def _fit_native(scenario: Scenario, dataset: IrregularTrajectorySet):
    common = dict(
        n_components=N_COMPONENTS,
        evaluation_grid=GRID,
        mean_bandwidth=scenario.mean_bandwidth,
        covariance_bandwidth=scenario.covariance_bandwidth,
        psd_action="project",
        score_failure_action="retain_nan",
    )
    start = time.perf_counter()
    if scenario.design == "univariate":
        fit = fit_sparse_fpca(
            dataset,
            dimension="x",
            noise_variance_method="fixed",
            measurement_error_variance=NOISE_SD**2,
            **common,
        )
    elif scenario.design == "planar_paired":
        fit = fit_sparse_mfpca(
            dataset,
            dimensions=("x", "y"),
            measurement_error="diagonal",
            measurement_error_variance=(NOISE_SD**2, NOISE_SD**2),
            **common,
        )
    else:
        fit = fit_sparse_mfpca_async(
            dataset,
            dimensions=("x", "y"),
            measurement_error="diagonal",
            measurement_error_variance=(NOISE_SD**2, NOISE_SD**2),
            **common,
        )
    elapsed = time.perf_counter() - start
    return fit, elapsed


def _function_array(fit, design: str) -> np.ndarray:
    functions = np.asarray(fit.eigenfunctions, dtype=float)
    if design == "univariate":
        return functions[:, :, None]
    return functions


def _mean_array(fit, design: str) -> np.ndarray:
    mean = np.asarray(fit.mean, dtype=float)
    if design == "univariate":
        return mean[:, None]
    return mean


def _write_function_long(
    path: Path,
    grid: np.ndarray,
    dimensions: tuple[str, ...],
    functions: np.ndarray,
) -> None:
    rows = []
    for component in range(functions.shape[0]):
        for dim_index, dimension in enumerate(dimensions):
            for time_value, value in zip(
                grid,
                functions[component, :, dim_index],
                strict=True,
            ):
                rows.append(
                    {
                        "component": component + 1,
                        "dimension": dimension,
                        "time": float(time_value),
                        "value": float(value),
                    }
                )
    pd.DataFrame(rows).to_csv(path, index=False)


def _write_mean(
    path: Path,
    grid: np.ndarray,
    dimensions: tuple[str, ...],
    mean: np.ndarray,
) -> None:
    frame = pd.DataFrame({"time": grid})
    for dim_index, dimension in enumerate(dimensions):
        frame[dimension] = mean[:, dim_index]
    frame.to_csv(path, index=False)


def _write_scores(
    path: Path,
    curve_ids: tuple[str, ...],
    scores: np.ndarray,
) -> None:
    frame = pd.DataFrame(
        np.asarray(scores, dtype=float),
        columns=[f"PC{index + 1}" for index in range(scores.shape[1])],
    )
    frame.insert(0, "curve_id", list(curve_ids))
    frame.to_csv(path, index=False)


def _write_observations(
    scenario_dir: Path,
    observed: dict[str, list[tuple[str, np.ndarray, np.ndarray]]],
) -> None:
    for dimension, curves in observed.items():
        rows = []
        for curve_id, time_values, values in curves:
            rows.extend(
                {
                    "curve_id": curve_id,
                    "time": float(time_value),
                    "value": float(value),
                }
                for time_value, value in zip(time_values, values, strict=True)
            )
        pd.DataFrame(rows).to_csv(
            scenario_dir / f"observations_{dimension}.csv",
            index=False,
        )


def generate(output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    scenario_root = output_dir / "scenarios"
    scenario_root.mkdir(exist_ok=True)
    manifest_rows = []
    summaries = []

    for scenario in SCENARIOS:
        scenario_dir = scenario_root / scenario.name
        scenario_dir.mkdir(exist_ok=True)
        dataset, payload = _make_dataset(scenario)
        fit, elapsed = _fit_native(scenario, dataset)
        dimensions = dataset.dimension_names
        functions = _function_array(fit, scenario.design)
        mean = _mean_array(fit, scenario.design)
        scores = np.asarray(fit.scores, dtype=float)
        eigenvalues = np.asarray(fit.eigenvalues, dtype=float)

        _write_observations(scenario_dir, payload["observed"])
        (scenario_dir / "truth.json").write_text(
            json.dumps(payload["truth"], indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        pd.DataFrame({"time": GRID}).to_csv(
            scenario_dir / "truth_grid.csv",
            index=False,
        )
        _write_mean(scenario_dir / "native_mean.csv", GRID, dimensions, mean)
        _write_function_long(
            scenario_dir / "native_eigenfunctions.csv",
            GRID,
            dimensions,
            functions,
        )
        _write_scores(scenario_dir / "native_scores.csv", dataset.curve_ids, scores)
        pd.DataFrame(
            {
                "component": np.arange(1, eigenvalues.size + 1),
                "eigenvalue": eigenvalues,
            }
        ).to_csv(scenario_dir / "native_eigenvalues.csv", index=False)
        diagnostics = getattr(fit, "score_diagnostics", pd.DataFrame())
        if isinstance(diagnostics, pd.DataFrame) and not diagnostics.empty:
            diagnostics.to_csv(
                scenario_dir / "native_score_diagnostics.csv",
                index=False,
            )

        manifest_rows.append(
            {
                "scenario": scenario.name,
                "design": scenario.design,
                "n_curves": scenario.n_curves,
                "n_dimensions": len(dimensions),
                "n_components": N_COMPONENTS,
                "spline_basis_size": 7,
            }
        )
        summaries.append(
            {
                "scenario": scenario.name,
                "design": scenario.design,
                "native_elapsed_seconds": elapsed,
                "native_score_failure_rate": float(
                    np.mean(~np.all(np.isfinite(scores), axis=1))
                ),
                "n_curves": scenario.n_curves,
            }
        )

    pd.DataFrame(manifest_rows).to_csv(output_dir / "manifest.csv", index=False)
    manifest = {
        "schema_version": 1,
        "programme": "post-1.1-bayesian-fpca-comparator-b1",
        "eyetrajectoriespy_version": importlib.metadata.version("eyetrajectoriespy"),
        "external_comparator": "hruffieux/bayesFPCA",
        "external_comparator_version": "0.1.0",
        "external_comparator_commit": BAYESFPCA_COMMIT,
        "external_comparator_license": "GPL-3.0-or-later",
        "external_runtime_backend": False,
        "source_code_ported": False,
        "equivalence_claim": False,
        "architecture_winner_selected": False,
        "automatic_promotion_decision": False,
        "scenarios": summaries,
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    manifest = generate(args.output_dir)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
