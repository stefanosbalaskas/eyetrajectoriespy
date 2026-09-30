"""Non-comparative performance envelope for public sparse MFPCA/joint PACE."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time
from typing import Callable

import numpy as np


CASES = {
    "very_sparse_planar": {
        "n_curves": 80,
        "samples_per_curve": (6, 10),
        "grid_points": 21,
        "mean_bandwidth": 0.32,
        "covariance_bandwidth": 0.44,
    },
    "moderate_planar": {
        "n_curves": 60,
        "samples_per_curve": (12, 16),
        "grid_points": 31,
        "mean_bandwidth": 0.25,
        "covariance_bandwidth": 0.34,
    },
    "irregular_rich_planar": {
        "n_curves": 36,
        "samples_per_curve": (20, 28),
        "grid_points": 41,
        "mean_bandwidth": 0.20,
        "covariance_bandwidth": 0.28,
    },
}
RHO_XY = 0.6


def _peak_rss_mib() -> float | None:
    try:
        import resource
    except ImportError:
        return None
    value = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    if sys.platform == "darwin":
        return value / (1024.0 * 1024.0)
    return value / 1024.0


def _mean_planar(time_values: np.ndarray) -> np.ndarray:
    time_values = np.asarray(time_values, dtype=float)
    return np.column_stack(
        (
            0.50 + 0.04 * np.sin(np.pi * time_values),
            0.50 + 0.04 * np.cos(np.pi * time_values),
        )
    )


def _scalar_mode(frequency: int) -> Callable[[np.ndarray], np.ndarray]:
    def mode(time_values: np.ndarray) -> np.ndarray:
        time_values = np.asarray(time_values, dtype=float)
        return np.sqrt(2.0) * np.sin(frequency * np.pi * time_values)

    return mode


def _vector_mode(
    scalar: Callable[[np.ndarray], np.ndarray],
    loading: np.ndarray,
) -> Callable[[np.ndarray], np.ndarray]:
    loading_array = np.asarray(loading, dtype=float).copy()

    def mode(time_values: np.ndarray) -> np.ndarray:
        values = scalar(np.asarray(time_values, dtype=float))
        return values[:, None] * loading_array[None, :]

    return mode


def _design():
    plus = np.array([1.0, 1.0]) / np.sqrt(2.0)
    minus = np.array([1.0, -1.0]) / np.sqrt(2.0)
    temporal = ((_scalar_mode(1), 1.0), (_scalar_mode(2), 0.45))
    channel = (
        (plus, 1.0 + RHO_XY),
        (minus, 1.0 - RHO_XY),
    )
    pairs = []
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


def _run_case(name: str) -> None:
    from eyetrajectoriespy import (
        FunctionalSimulationScenario,
        fit_sparse_mfpca,
        simulate_functional_scenario,
    )

    spec = CASES[name]
    eigenvalues, eigenfunctions = _design()
    scenario = FunctionalSimulationScenario(
        name=f"performance-{name}",
        truth_grid=np.linspace(0.0, 1.0, spec["grid_points"]),
        eigenvalues=eigenvalues,
        n_participants=spec["n_curves"],
        dimension_names=("x", "y"),
        coordinate_system="normalized",
        time_unit="normalized",
        observation_design="irregular",
        samples_per_curve=spec["samples_per_curve"],
        irregular_time_design="uniform",
        measurement_noise_sd=(0.03, 0.03),
        replicates=1,
        seed_start=18100 + list(CASES).index(name),
    )
    simulation = simulate_functional_scenario(
        scenario,
        mean=_mean_planar,
        eigenfunctions=eigenfunctions,
    )
    trajectories = simulation.observations
    per_block_pairs = int(
        sum(
            len(time_values) * (len(time_values) - 1)
            for time_values in trajectories.time
        )
    )
    start = time.perf_counter()
    result = fit_sparse_mfpca(
        trajectories,
        dimensions=("x", "y"),
        n_components=4,
        evaluation_grid=np.linspace(
            0.0,
            1.0,
            spec["grid_points"],
        ),
        mean_bandwidth=spec["mean_bandwidth"],
        covariance_bandwidth=spec["covariance_bandwidth"],
        measurement_error="diagonal",
        measurement_error_variance=(0.0009, 0.0009),
        psd_action="project",
        score_failure_action="retain_nan",
        covariance_min_local_pairs=8,
    )
    elapsed = time.perf_counter() - start
    payload = {
        "case": name,
        "n_curves": trajectories.n_curves,
        "median_samples_per_curve": float(
            np.median(trajectories.sample_counts)
        ),
        "per_block_covariance_pair_count": per_block_pairs,
        "total_latent_pair_products": 3 * per_block_pairs,
        "grid_points": spec["grid_points"],
        "n_components": result.n_components,
        "runtime_seconds": elapsed,
        "peak_memory_mib": _peak_rss_mib(),
        "score_failure_rate": float(
            np.mean(
                result.score_diagnostics["status_code"].to_numpy()
                != "ok"
            )
        ),
        "psd_relative_operator_correction": float(
            result.covariance_diagnostics[
                "relative_operator_correction_frobenius_norm"
            ]
        ),
    }
    print(
        "SPARSE_MFPCA_PERFORMANCE_RESULT="
        + json.dumps(payload, sort_keys=True)
    )


def _quantile(values, probability):
    ordered = sorted(float(value) for value in values)
    if len(ordered) == 1:
        return ordered[0]
    position = probability * (len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def _cpu_model() -> str | None:
    cpuinfo = Path("/proc/cpuinfo")
    if cpuinfo.exists():
        for line in cpuinfo.read_text(encoding="utf-8").splitlines():
            if line.lower().startswith("model name"):
                return line.split(":", 1)[1].strip()
    return platform.processor() or None


def _environment() -> dict[str, object]:
    packages = {}
    for package_name in (
        "eyetrajectoriespy",
        "numpy",
        "scipy",
        "pandas",
        "scikit-learn",
    ):
        try:
            packages[package_name] = importlib.metadata.version(package_name)
        except importlib.metadata.PackageNotFoundError:
            packages[package_name] = None
    return {
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu_model": _cpu_model(),
        "logical_cpu_count": os.cpu_count(),
        "packages": packages,
        "source_commit": os.environ.get(
            "EYETRAJECTORIESPY_SOURCE_SHA",
            os.environ.get("GITHUB_SHA"),
        ),
        "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        "runner_name": os.environ.get("RUNNER_NAME"),
        "thread_limits": {
            key: os.environ.get(key)
            for key in (
                "OMP_NUM_THREADS",
                "OPENBLAS_NUM_THREADS",
                "MKL_NUM_THREADS",
                "NUMEXPR_NUM_THREADS",
            )
        },
    }


def _run_parent(repeats: int, output: Path) -> None:
    if repeats < 3:
        raise ValueError(
            "performance qualification requires at least three repeats"
        )
    script = str(Path(__file__).resolve())
    results = []
    for name in CASES:
        observations = []
        for _ in range(repeats):
            env = os.environ.copy()
            env.update(
                {
                    "PYTHONHASHSEED": "0",
                    "OMP_NUM_THREADS": "1",
                    "OPENBLAS_NUM_THREADS": "1",
                    "MKL_NUM_THREADS": "1",
                    "NUMEXPR_NUM_THREADS": "1",
                }
            )
            completed = subprocess.run(
                [sys.executable, script, "--child-case", name],
                capture_output=True,
                text=True,
                check=False,
                env=env,
            )
            if completed.returncode != 0:
                raise RuntimeError(
                    f"sparse MFPCA performance child {name!r} failed\n"
                    f"STDOUT:\n{completed.stdout}\n"
                    f"STDERR:\n{completed.stderr}"
                )
            markers = [
                line
                for line in completed.stdout.splitlines()
                if line.startswith(
                    "SPARSE_MFPCA_PERFORMANCE_RESULT="
                )
            ]
            if len(markers) != 1:
                raise RuntimeError(
                    f"sparse MFPCA performance child {name!r} emitted "
                    f"{len(markers)} result markers"
                )
            observations.append(
                json.loads(markers[0].split("=", 1)[1])
            )

        runtimes = [row["runtime_seconds"] for row in observations]
        memories = [
            row["peak_memory_mib"]
            for row in observations
            if row["peak_memory_mib"] is not None
        ]
        scale = {
            key: observations[0][key]
            for key in (
                "n_curves",
                "median_samples_per_curve",
                "per_block_covariance_pair_count",
                "total_latent_pair_products",
                "grid_points",
                "n_components",
            )
        }
        results.append(
            {
                "case": name,
                "scale": scale,
                "repeats": repeats,
                "runtime_seconds": {
                    "median": statistics.median(runtimes),
                    "q1": _quantile(runtimes, 0.25),
                    "q3": _quantile(runtimes, 0.75),
                    "minimum": min(runtimes),
                    "maximum": max(runtimes),
                    "all": runtimes,
                },
                "peak_memory_mib": (
                    None
                    if not memories
                    else {
                        "median": statistics.median(memories),
                        "maximum": max(memories),
                        "all": memories,
                    }
                ),
                "maximum_score_failure_rate": max(
                    row["score_failure_rate"] for row in observations
                ),
                "maximum_psd_relative_operator_correction": max(
                    row["psd_relative_operator_correction"]
                    for row in observations
                ),
            }
        )

    payload = {
        "schema_version": 1,
        "benchmark_kind": (
            "native sparse MFPCA/joint PACE single-package performance envelope"
        ),
        "comparative_benchmark": False,
        "speed_threshold_applied": False,
        "repeats": repeats,
        "environment": _environment(),
        "results": results,
        "interpretation": (
            "Runtime and process peak RSS are conditional on the declared "
            "planar sparse workloads and runner environment. No cross-package "
            "speed claim, universal workstation claim, or release speed "
            "threshold is made."
        ),
    }
    output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("sparse-mfpca-performance.json"),
    )
    parser.add_argument("--child-case", choices=tuple(CASES))
    args = parser.parse_args()
    if args.child_case is not None:
        _run_case(args.child_case)
        return 0
    _run_parent(args.repeats, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
