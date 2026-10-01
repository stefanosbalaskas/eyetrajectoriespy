"""Observe the public sparse-MFPCA chain from an exact installed RC artifact.

This script is intentionally executed outside the repository working tree against
an exact production-PyPI installation. It does not re-qualify sparse MFPCA or add
recovery thresholds. It asks a narrower release-candidate question: does the
installed wheel expose and execute the 0.12 public sparse-MFPCA/joint-PACE chain
with the already-qualified deterministic rho=0.6 fixture?
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

import eyetrajectoriespy as et


RHO_XY = 0.6
GRID_SIZE = 31
N_PARTICIPANTS = 36
SAMPLES_PER_CURVE = (22, 30)
SEED = 12003
NOISE_COVARIANCE = np.diag([0.0009, 0.0016])


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


def _planar_rho_design(
    rho_xy: float,
) -> tuple[tuple[float, ...], tuple[Callable[[np.ndarray], np.ndarray], ...]]:
    rho = float(rho_xy)
    if not np.isfinite(rho) or rho <= -1.0 or rho >= 1.0:
        raise ValueError("rho_xy must satisfy -1 < rho_xy < 1")

    plus = np.array([1.0, 1.0]) / np.sqrt(2.0)
    minus = np.array([1.0, -1.0]) / np.sqrt(2.0)
    temporal = ((_scalar_mode(1), 1.0), (_scalar_mode(2), 0.45))
    channel = ((plus, 1.0 + rho), (minus, 1.0 - rho))

    pairs: list[tuple[float, Callable[[np.ndarray], np.ndarray]]] = []
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


def _assert_installed_distribution(expected_version: str) -> dict[str, Any]:
    distribution = importlib.metadata.distribution("eyetrajectoriespy")
    distribution_version = distribution.version
    module_path = Path(et.__file__).resolve()
    distribution_root = Path(distribution.locate_file("")).resolve()
    workspace_raw = os.environ.get("GITHUB_WORKSPACE")
    workspace = None if not workspace_raw else Path(workspace_raw).resolve()

    if et.__version__ != expected_version:
        raise RuntimeError(
            f"package version mismatch: {et.__version__} != {expected_version}"
        )
    if distribution_version != expected_version:
        raise RuntimeError(
            "distribution metadata version mismatch: "
            f"{distribution_version} != {expected_version}"
        )
    if not module_path.is_relative_to(distribution_root):
        raise RuntimeError(
            "eyetrajectoriespy import does not resolve inside the installed "
            "distribution root"
        )
    if workspace is not None and module_path.is_relative_to(workspace):
        raise RuntimeError(
            "eyetrajectoriespy resolved from the repository checkout rather "
            "than the production-installed distribution"
        )

    return {
        "package_version": et.__version__,
        "distribution_version": distribution_version,
        "module_path": str(module_path),
        "distribution_root": str(distribution_root),
        "github_workspace": None if workspace is None else str(workspace),
        "source_checkout_imported": False,
    }


def _frame_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    records = frame.replace({np.nan: None}).to_dict(orient="records")
    for row in records:
        for key, value in tuple(row.items()):
            if isinstance(value, np.generic):
                row[key] = value.item()
    return records


def _jsonable(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def _run_observation(output_dir: Path) -> dict[str, Any]:
    eigenvalues, eigenfunctions = _planar_rho_design(RHO_XY)
    scenario = et.FunctionalSimulationScenario(
        name="installed-rc-sparse-mfpca-rho-0.6",
        truth_grid=np.linspace(0.0, 1.0, GRID_SIZE),
        eigenvalues=eigenvalues,
        n_participants=N_PARTICIPANTS,
        dimension_names=("x", "y"),
        coordinate_system="normalized",
        time_unit="normalized",
        observation_design="irregular",
        samples_per_curve=SAMPLES_PER_CURVE,
        irregular_time_design="uniform",
        measurement_noise_sd=0.0,
        measurement_noise_covariance=NOISE_COVARIANCE.copy(),
        replicates=1,
        seed_start=SEED,
        labels={
            "qualification": "installed_sparse_mfpca_observation",
            "rho_xy": RHO_XY,
            "source_contract": "0.12-qualified-rho-family",
        },
    )
    simulation = et.simulate_functional_scenario(
        scenario,
        mean=_mean_planar,
        eigenfunctions=eigenfunctions,
    )
    truth = simulation.truth
    result = et.fit_sparse_mfpca(
        simulation.observations,
        dimensions=("x", "y"),
        n_components=len(truth.eigenvalues),
        evaluation_grid=np.asarray(truth.truth_grid, dtype=float),
        mean_bandwidth=0.20,
        covariance_bandwidth=0.28,
        measurement_error="diagonal",
        measurement_error_variance=tuple(
            float(value)
            for value in np.diag(truth.measurement_noise_covariance)
        ),
        psd_action="project",
        score_ridge=0.0,
        score_failure_action="retain_nan",
        covariance_min_local_pairs=8,
    )

    expected_components = len(eigenvalues)
    expected_shapes = {
        "mean": (GRID_SIZE, 2),
        "eigenvalues": (expected_components,),
        "eigenfunctions": (expected_components, GRID_SIZE, 2),
        "scores": (N_PARTICIPANTS, expected_components),
        "cxy": (GRID_SIZE, GRID_SIZE),
    }
    observed_shapes = {
        "mean": result.mean.shape,
        "eigenvalues": result.eigenvalues.shape,
        "eigenfunctions": result.eigenfunctions.shape,
        "scores": result.scores.shape,
        "cxy": result.covariance_cxy.shape,
    }
    if observed_shapes != expected_shapes:
        raise RuntimeError(
            f"unexpected sparse-MFPCA public shapes: {observed_shapes}"
        )
    if not np.all(np.isfinite(result.eigenvalues)):
        raise RuntimeError("installed sparse-MFPCA eigenvalues are non-finite")
    if not np.all(np.isfinite(result.eigenfunctions)):
        raise RuntimeError("installed sparse-MFPCA eigenfunctions are non-finite")
    if not np.all(np.isfinite(result.scores)):
        raise RuntimeError("installed sparse-MFPCA joint scores are non-finite")

    status = result.score_diagnostics["status_code"].astype(str)
    if not bool((status == "ok").all()):
        failures = result.score_diagnostics.loc[
            status != "ok", ["curve_id", "status_code"]
        ]
        raise RuntimeError(
            "installed sparse-MFPCA joint PACE scoring had failures: "
            f"{failures.to_dict(orient='records')}"
        )

    provenance = result.provenance["sparse_mfpca"]
    expected_provenance = {
        "backend": "native",
        "fit_method": "direct_sparse_block_covariance",
        "score_method": "joint_PACE",
        "cross_channel_covariance_modeled": True,
        "yx_estimated_independently": False,
        "cross_covariance_self_symmetrized": False,
        "score_covariance_source": (
            "full_fitted_joint_covariance_plus_measurement_error"
        ),
        "rank_k_covariance_used_for_scoring": False,
        "raw_sparse_trajectory_interpolation_performed": False,
        "population_function_evaluation_at_native_times": True,
        "automatic_bandwidth_selection_performed": False,
    }
    for key, expected in expected_provenance.items():
        if provenance.get(key) != expected:
            raise RuntimeError(
                f"unexpected sparse-MFPCA provenance for {key}: "
                f"{provenance.get(key)!r} != {expected!r}"
            )
    np.testing.assert_allclose(
        result.smoothed_cyx,
        result.smoothed_cxy.T,
    )
    np.testing.assert_allclose(
        result.covariance_cyx,
        result.covariance_cxy.T,
    )

    assessment = et.evaluate_sparse_mfpca_recovery(result, truth)
    recovery_frame = et.functional_recovery_assessment_frame(assessment)
    if recovery_frame.empty:
        raise RuntimeError("installed sparse-MFPCA recovery frame is empty")
    numeric_values = recovery_frame["value"].to_numpy(dtype=float)
    if not np.all(np.isfinite(numeric_values)):
        raise RuntimeError("installed sparse-MFPCA recovery contains non-finite values")
    recovery_path = output_dir / "sparse-mfpca-recovery.csv"
    recovery_frame.to_csv(recovery_path, index=False)

    score_frame = et.sparse_mfpca_score_frame(result)
    if len(score_frame) != N_PARTICIPANTS:
        raise RuntimeError("sparse_mfpca_score_frame changed the curve denominator")
    expected_score_columns = {
        f"SMFPC{index + 1}" for index in range(expected_components)
    }
    if not expected_score_columns.issubset(score_frame.columns):
        raise RuntimeError("sparse_mfpca_score_frame is missing joint score columns")
    score_path = output_dir / "sparse-mfpca-scores.csv"
    score_frame.to_csv(score_path, index=False)

    reporting = et.sparse_mfpca_reporting_text(result)
    for phrase in (
        "Cxy was fitted directionally",
        "full fitted joint covariance",
        "never a rank-K covariance reconstruction",
    ):
        if phrase not in reporting:
            raise RuntimeError(
                f"sparse_mfpca_reporting_text is missing contract phrase: {phrase}"
            )
    report_path = output_dir / "sparse-mfpca-report.txt"
    report_path.write_text(reporting + "\n", encoding="utf-8")

    portable_dir = output_dir / "portable-sparse-mfpca"
    et.export_portable_result(
        result,
        portable_dir,
        include_environment=False,
    )
    snapshot = et.load_portable_result(portable_dir)
    if not snapshot.package_version_match:
        raise RuntimeError("portable sparse-MFPCA package version did not match")
    if snapshot.nonportable_fields != ():
        raise RuntimeError(
            "portable sparse-MFPCA snapshot has nonportable fields: "
            f"{snapshot.nonportable_fields}"
        )
    np.testing.assert_array_equal(snapshot.payload["mean"], result.mean)
    np.testing.assert_array_equal(
        snapshot.payload["eigenvalues"], result.eigenvalues
    )
    np.testing.assert_array_equal(
        snapshot.payload["eigenfunctions"], result.eigenfunctions
    )
    np.testing.assert_array_equal(snapshot.payload["scores"], result.scores)

    return {
        "scenario": scenario.name,
        "rho_xy": RHO_XY,
        "seed": SEED,
        "scientific_thresholds_added": False,
        "recovery_thresholds_applied": False,
        "automatic_tuning_performed": False,
        "truth_available_to_estimator": False,
        "expected_shapes": {
            key: list(value) for key, value in expected_shapes.items()
        },
        "observed_shapes": {
            key: list(value) for key, value in observed_shapes.items()
        },
        "joint_score_status_counts": {
            str(key): int(value)
            for key, value in status.value_counts(dropna=False).items()
        },
        "finite_eigenvalues": True,
        "finite_eigenfunctions": True,
        "finite_joint_scores": True,
        "directional_cxy_contract": {
            "cross_channel_covariance_modeled": provenance[
                "cross_channel_covariance_modeled"
            ],
            "yx_estimated_independently": provenance[
                "yx_estimated_independently"
            ],
            "cross_covariance_self_symmetrized": provenance[
                "cross_covariance_self_symmetrized"
            ],
            "cyx_is_cxy_transpose": True,
        },
        "joint_pace_contract": {
            "score_method": provenance["score_method"],
            "score_covariance_source": provenance[
                "score_covariance_source"
            ],
            "rank_k_covariance_used_for_scoring": provenance[
                "rank_k_covariance_used_for_scoring"
            ],
        },
        "recovery": {
            "rows": int(len(recovery_frame)),
            "all_values_finite": True,
            "records": _frame_records(recovery_frame),
            "csv": str(recovery_path),
        },
        "score_frame": {
            "rows": int(len(score_frame)),
            "columns": list(score_frame.columns),
            "csv": str(score_path),
        },
        "reporting": {
            "nonempty": bool(reporting.strip()),
            "path": str(report_path),
        },
        "portable_result": {
            "result_type": snapshot.result_type,
            "package_version_match": snapshot.package_version_match,
            "nonportable_fields": list(snapshot.nonportable_fields),
            "manifest": str(portable_dir / "manifest.json"),
            "arrays": str(portable_dir / "arrays.npz"),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-version", required=True)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("installed-sparse-mfpca-observation"),
    )
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=False)
    installation = _assert_installed_distribution(args.expected_version)
    observation = _run_observation(args.output_dir)
    payload = {
        "schema_version": 1,
        "kind": "production-installed sparse-MFPCA observation",
        "expected_version": args.expected_version,
        "scientific_thresholds_added": False,
        "source_checkout_imported": False,
        "installation": installation,
        "sparse_mfpca": observation,
        "interpretation": (
            "Observation-only installed-artifact evidence for the already-"
            "qualified 0.12 sparse-MFPCA/joint-PACE public chain. No recovery "
            "thresholds, parameter selection, or automatic tuning are added."
        ),
    }
    output = args.output_dir / "installed-sparse-mfpca-observation.json"
    output.write_text(
        json.dumps(_jsonable(payload), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(_jsonable(payload), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
