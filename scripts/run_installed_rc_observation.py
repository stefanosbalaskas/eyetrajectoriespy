"""External-consumer observation harness for a production-installed release candidate.

This script is intentionally executed outside the repository working tree against
an exact production-PyPI installation. It uses only public eyetrajectoriespy APIs
for scientific work. Repository scripts may orchestrate the run, but the fitted
package imported here must resolve to the installed distribution rather than the
source checkout.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import sys
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import eyetrajectoriespy as et


def _mean(time):
    time = np.asarray(time, dtype=float)
    return 0.25 + 0.30 * time


def _phi1(time):
    time = np.asarray(time, dtype=float)
    return np.sqrt(2.0) * np.sin(np.pi * time)


def _phi2(time):
    time = np.asarray(time, dtype=float)
    return np.sqrt(2.0) * np.sin(2.0 * np.pi * time)


def _constant_mode(time):
    time = np.asarray(time, dtype=float)
    span = float(time[-1] - time[0])
    if span <= 0:
        raise ValueError("time support must be strictly increasing")
    return np.ones_like(time) / np.sqrt(span)


def _linear_mode(time):
    time = np.asarray(time, dtype=float)
    midpoint = 0.5 * float(time[0] + time[-1])
    centered = time - midpoint
    integral = float(
        np.sum(
            0.5
            * (centered[:-1] ** 2 + centered[1:] ** 2)
            * np.diff(time)
        )
    )
    if integral <= 0:
        raise ValueError("linear mode has non-positive trapezoid norm")
    return centered / np.sqrt(integral)


def _frame_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    clean = frame.replace({np.nan: None})
    records = clean.to_dict(orient="records")
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


def _curve_values_equal(first, second) -> bool:
    if isinstance(first.values, tuple):
        if not isinstance(second.values, tuple):
            return False
        if len(first.values) != len(second.values):
            return False
        return all(
            np.array_equal(a, b, equal_nan=True)
            for a, b in zip(first.values, second.values, strict=True)
        )
    return bool(
        np.array_equal(
            np.asarray(first.values),
            np.asarray(second.values),
            equal_nan=True,
        )
    )


def _determinism_observation() -> dict[str, Any]:
    scenario = et.FunctionalSimulationScenario(
        name="installed-rc-determinism",
        truth_grid=np.linspace(0.0, 1.0, 41),
        eigenvalues=(1.0, 0.30),
        n_participants=12,
        trials_per_participant=2,
        observation_design="irregular",
        samples_per_curve=(8, 12),
        irregular_time_design="center_clustered",
        participant_eigenvalues=(0.10, 0.03),
        trial_eigenvalues=(0.05, 0.02),
        measurement_noise_sd=0.05,
        missingness={"kind": "mcar", "probability": 0.08},
        phase_variation={"kind": "power", "sd": 0.08},
        replicates=2,
        seed_start=91100,
    )
    first = et.simulate_functional_scenario(
        scenario,
        mean=_mean,
        eigenfunctions=(_phi1, _phi2),
        replicate=0,
    )
    replay = et.simulate_functional_scenario(
        scenario,
        mean=_mean,
        eigenfunctions=(_phi1, _phi2),
        replicate=0,
    )
    second_seed = et.simulate_functional_scenario(
        scenario,
        mean=_mean,
        eigenfunctions=(_phi1, _phi2),
        replicate=1,
    )

    same_observations = _curve_values_equal(
        first.observations,
        replay.observations,
    )
    same_scores = bool(np.array_equal(first.truth.scores, replay.truth.scores))
    same_missingness = all(
        np.array_equal(a, b)
        for a, b in zip(
            first.truth.missingness_mask,
            replay.truth.missingness_mask,
            strict=True,
        )
    )
    different_seed_changes_scores = not np.array_equal(
        first.truth.scores,
        second_seed.truth.scores,
    )
    if not (
        same_observations
        and same_scores
        and same_missingness
        and different_seed_changes_scores
    ):
        raise RuntimeError(
            "seeded FunctionalSimulationScenario replay was not deterministic "
            "or a distinct declared replicate did not change realized scores"
        )

    return {
        "scenario": scenario.name,
        "seeds": list(scenario.seeds()),
        "same_seed_observations_identical": same_observations,
        "same_seed_scores_identical": same_scores,
        "same_seed_missingness_identical": same_missingness,
        "different_seed_changes_realized_scores": (
            different_seed_changes_scores
        ),
        "observation_design": scenario.observation_design,
        "missingness_kind": dict(scenario.missingness)["kind"],
        "phase_variation_kind": dict(scenario.phase_variation)["kind"],
    }


def _dense_recovery_and_portability(
    output_dir: Path,
) -> tuple[dict[str, Any], Any]:
    scenario = et.FunctionalSimulationScenario(
        name="installed-rc-dense-recovery",
        truth_grid=np.linspace(0.0, 1.0, 61),
        eigenvalues=(1.0, 0.35),
        n_participants=100,
        measurement_noise_sd=0.05,
        replicates=1,
        seed_start=91200,
    )
    simulation = et.simulate_functional_scenario(
        scenario,
        mean=_mean,
        eigenfunctions=(_phi1, _phi2),
    )
    fit = et.fit_fpca(
        simulation.observations,
        n_components=2,
        scaling="none",
    )
    assessment = et.evaluate_fpca_recovery(fit, simulation.truth)
    recovery_frame = et.functional_recovery_assessment_frame(assessment)
    if recovery_frame.empty or not np.all(
        np.isfinite(recovery_frame["value"].to_numpy(dtype=float))
    ):
        raise RuntimeError("dense installed-package recovery is empty/non-finite")

    portable_dir = output_dir / "portable-fpca"
    et.export_portable_result(fit, portable_dir)
    snapshot = et.load_portable_result(portable_dir)
    if not snapshot.package_version_match:
        raise RuntimeError("portable snapshot package version did not match")
    np.testing.assert_array_equal(snapshot.payload["mean"], fit.mean)
    np.testing.assert_array_equal(
        snapshot.payload["components"],
        fit.components,
    )
    np.testing.assert_array_equal(snapshot.payload["scores"], fit.scores)

    simulation_report = et.functional_simulation_reporting_text(simulation)
    recovery_report = et.functional_recovery_reporting_text(assessment)
    (output_dir / "simulation-report.txt").write_text(
        simulation_report + "\n",
        encoding="utf-8",
    )
    (output_dir / "dense-recovery-report.txt").write_text(
        recovery_report + "\n",
        encoding="utf-8",
    )

    ax = et.plot_functional_simulation_curve(
        simulation,
        curve=0,
        dimension=0,
        show_pre_missing=True,
    )
    figure_path = output_dir / "installed-simulation-curve.png"
    ax.figure.savefig(figure_path, dpi=140, bbox_inches="tight")
    plt.close(ax.figure)

    return (
        {
            "scenario": scenario.name,
            "recovery": _frame_records(recovery_frame),
            "portable_result": {
                "result_type": snapshot.result_type,
                "package_version_match": snapshot.package_version_match,
                "nonportable_fields": list(snapshot.nonportable_fields),
                "manifest": str(portable_dir / "manifest.json"),
                "arrays": str(portable_dir / "arrays.npz"),
            },
            "reporting": {
                "simulation_report_nonempty": bool(simulation_report.strip()),
                "recovery_report_nonempty": bool(recovery_report.strip()),
            },
            "plot": {
                "path": str(figure_path),
                "exists": figure_path.is_file(),
                "bytes": figure_path.stat().st_size,
            },
        },
        fit,
    )


def _registration_recovery() -> dict[str, Any]:
    scenario = et.FunctionalSimulationScenario(
        name="installed-rc-registration",
        truth_grid=np.linspace(0.0, 1.0, 61),
        eigenvalues=(0.60, 0.20),
        n_participants=20,
        measurement_noise_sd=0.01,
        phase_variation={"kind": "power", "sd": 0.12},
        replicates=1,
        seed_start=91300,
    )
    simulation = et.simulate_functional_scenario(
        scenario,
        mean=_mean,
        eigenfunctions=(_phi1, _phi2),
    )
    grid = np.asarray(simulation.truth.truth_grid, dtype=float)
    generated = np.asarray(
        simulation.truth.phase_warps_on_truth_grid,
        dtype=float,
    )
    reference = np.array([0.5], dtype=float)
    observed = np.asarray(
        [
            [np.interp(reference[0], warp, grid)]
            for warp in generated
        ],
        dtype=float,
    )
    registered = et.register_to_landmarks(
        simulation.observations,
        observed_landmarks=observed,
        reference_landmarks=reference,
    )
    assessment = et.evaluate_registration_recovery(
        registered,
        simulation.truth,
    )
    frame = et.functional_recovery_assessment_frame(assessment)
    values = frame["value"].to_numpy(dtype=float)
    if frame.empty or not np.all(np.isfinite(values)):
        raise RuntimeError("registration recovery is empty/non-finite")

    return {
        "scenario": scenario.name,
        "landmark_reference": reference.tolist(),
        "metrics": _frame_records(frame),
        "max_recorded_metric": float(np.max(values)),
        "truth_target": assessment.provenance.get("truth_target"),
    }


def _mixed_effects_recovery() -> dict[str, Any]:
    # Match the declared two-function degree-1 random-effect basis with
    # full-rank participant truth. A rank-one truth process would place the
    # unstructured two-dimensional covariance on its boundary and is not a
    # suitable convergence qualification workload.
    scenario = et.FunctionalSimulationScenario(
        name="installed-rc-mixed-effects",
        truth_grid=np.linspace(0.0, 1.0, 13),
        eigenvalues=(1e-5, 1e-5),
        n_participants=30,
        trials_per_participant=3,
        participant_eigenvalues=(0.12, 0.06),
        measurement_noise_sd=0.04,
        replicates=1,
        seed_start=91400,
    )
    simulation = et.simulate_functional_scenario(
        scenario,
        mean=_mean,
        eigenfunctions=(_constant_mode, _linear_mode),
    )
    metadata = simulation.observations.metadata.reset_index(drop=True)
    trial_centered = (
        metadata["trial_id"].to_numpy(dtype=float)
        - float(metadata["trial_id"].mean())
    )
    design = pd.DataFrame(
        {
            "curve_id": simulation.observations.curve_ids,
            "trial_centered": trial_centered,
        }
    )
    fitted = et.fit_functional_mixed_effects_regression(
        simulation.observations,
        design,
        predictors=("trial_centered",),
        participant_column="participant_id",
        dimension="value",
        fixed_basis_size=2,
        random_basis_size=2,
        spline_degree=1,
        reml=True,
        method="lbfgs",
        maxiter=500,
    )
    assessment = et.evaluate_functional_mixed_effects_recovery(
        fitted,
        simulation.truth,
    )
    frame = et.functional_recovery_assessment_frame(assessment)
    if frame.empty or not np.all(
        np.isfinite(frame["value"].to_numpy(dtype=float))
    ):
        raise RuntimeError("mixed-effects recovery is empty/non-finite")

    return {
        "scenario": scenario.name,
        "converged": bool(fitted.converged),
        "boundary_fit": bool(fitted.boundary_fit),
        "n_participants": int(fitted.n_participants),
        "n_curves": int(fitted.n_curves),
        "metrics": _frame_records(frame),
        "basis_covariance_compared_directly_to_kl_eigenvalues": (
            assessment.provenance.get(
                "basis_covariance_compared_directly_to_kl_eigenvalues"
            )
        ),
    }


def _runner_context() -> dict[str, Any]:
    return {
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "executable": sys.executable,
        },
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "platform": platform.platform(),
        },
        "github_runner": {
            key: os.environ.get(key)
            for key in (
                "RUNNER_OS",
                "RUNNER_ARCH",
                "RUNNER_NAME",
                "RUNNER_ENVIRONMENT",
                "ImageOS",
                "ImageVersion",
            )
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-version", required=True)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("installed-rc-observation"),
    )
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=False)

    installation = _assert_installed_distribution(args.expected_version)
    determinism = _determinism_observation()
    dense, _ = _dense_recovery_and_portability(args.output_dir)
    registration = _registration_recovery()
    mixed_effects = _mixed_effects_recovery()
    environment = et.capture_environment()
    runner = _runner_context()

    payload = {
        "schema_version": 1,
        "kind": "production-installed release-candidate observation",
        "expected_version": args.expected_version,
        "scientific_thresholds_added": False,
        "source_checkout_imported": False,
        "truth_available_to_estimators": False,
        "installation": installation,
        "determinism": determinism,
        "dense_fpca_recovery_and_portability": dense,
        "registration_recovery": registration,
        "mixed_effects_recovery": mixed_effects,
        "environment": environment,
        "runner": runner,
        "interpretation": (
            "External-consumer observation of the exact production-installed "
            "release candidate. Existing qualification/stress thresholds remain "
            "owned by their dedicated runners; this harness adds no new "
            "scientific pass/fail cutoffs."
        ),
    }
    output = args.output_dir / "installed-rc-observation.json"
    output.write_text(
        json.dumps(_jsonable(payload), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(_jsonable(payload), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
