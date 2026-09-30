"""Runtime/peak-memory characterization for native sparse multivariate FPCA.

This is not a comparative benchmark. It records the resource envelope of
fit_sparse_mfpca under declared synthetic workloads and does not assert a
universal workstation speed or cross-package advantage.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time

import numpy as np

CASES = {
    "very_sparse_planar": {
        "n_curves": 60,
        "samples_per_curve": (6, 8),
        "grid_points": 13,
        "mean_bandwidth": 0.30,
        "covariance_bandwidth": 0.42,
    },
    "moderate_sparse_planar": {
        "n_curves": 50,
        "samples_per_curve": (10, 14),
        "grid_points": 17,
        "mean_bandwidth": 0.24,
        "covariance_bandwidth": 0.34,
    },
    "irregular_rich_planar": {
        "n_curves": 30,
        "samples_per_curve": (18, 22),
        "grid_points": 25,
        "mean_bandwidth": 0.20,
        "covariance_bandwidth": 0.28,
    },
}


def _peak_rss_mib():
    try:
        import resource
    except ImportError:
        return None
    value = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    if sys.platform == "darwin":
        return value / (1024.0 * 1024.0)
    return value / 1024.0


def _run_case(name):
    from eyetrajectoriespy import IrregularTrajectorySet, fit_sparse_mfpca
    from eyetrajectoriespy._sparse_multivariate_truth import (
        simulate_sparse_multivariate_truth,
    )

    spec = CASES[name]
    times, values, truth = simulate_sparse_multivariate_truth(
        n_curves=spec["n_curves"],
        samples_per_curve=spec["samples_per_curve"],
        noise_sd=(0.06, 0.07),
        temporal_eigenvalues=(1.0, 0.35),
        channel_correlation=0.6,
        observation_design="uniform",
        random_state=202800 + list(CASES).index(name),
    )
    trajectories = IrregularTrajectorySet(
        time=times,
        values=values,
        curve_ids=tuple(f"P{i:03d}" for i in range(len(times))),
        dimension_names=("x", "y"),
        coordinate_system="normalized",
        time_unit="normalized",
        provenance={"performance_case": name},
    )
    marginal_pair_count = int(
        2 * sum(len(t) * (len(t) - 1) for t in trajectories.time)
    )
    cross_pair_count = int(
        sum(len(t) * len(t) for t in trajectories.time)
    )

    start = time.perf_counter()
    result = fit_sparse_mfpca(
        trajectories,
        n_components=4,
        evaluation_grid=np.linspace(
            0.0,
            1.0,
            spec["grid_points"],
        ),
        mean_bandwidth=spec["mean_bandwidth"],
        covariance_bandwidth=spec["covariance_bandwidth"],
        cross_covariance_bandwidth=spec["covariance_bandwidth"],
        noise_variance_method="fixed",
        measurement_error_variances={
            "x": float(truth.noise_sd[0] ** 2),
            "y": float(truth.noise_sd[1] ** 2),
        },
        psd_action="project",
        score_ridge=1e-8,
        score_failure_action="retain_nan",
        covariance_min_local_pairs=6,
        cross_covariance_min_local_pairs=6,
    )
    elapsed = time.perf_counter() - start

    payload = {
        "case": name,
        "n_curves": trajectories.n_curves,
        "median_samples_per_curve": float(
            np.median(trajectories.sample_counts)
        ),
        "marginal_offdiagonal_pair_count": marginal_pair_count,
        "cross_covariance_pair_count": cross_pair_count,
        "grid_points": spec["grid_points"],
        "block_operator_size": 2 * spec["grid_points"],
        "runtime_seconds": elapsed,
        "peak_memory_mib": _peak_rss_mib(),
        "score_failure_rate": float(
            np.mean(
                result.score_diagnostics["status_code"].to_numpy()
                != "ok"
            )
        ),
        "relative_psd_operator_correction": float(
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
    return (
        ordered[lower] * (1.0 - fraction)
        + ordered[upper] * fraction
    )


def _run_parent(repeats, output):
    if repeats < 3:
        raise ValueError("resource characterization requires at least 3 repeats")
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
                if line.startswith("SPARSE_MFPCA_PERFORMANCE_RESULT=")
            ]
            if len(markers) != 1:
                raise RuntimeError(
                    f"performance child {name!r} emitted "
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
        results.append(
            {
                "case": name,
                "scale": {
                    key: observations[0][key]
                    for key in (
                        "n_curves",
                        "median_samples_per_curve",
                        "marginal_offdiagonal_pair_count",
                        "cross_covariance_pair_count",
                        "grid_points",
                        "block_operator_size",
                    )
                },
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
                "score_failure_rate": max(
                    row["score_failure_rate"] for row in observations
                ),
                "relative_psd_operator_correction_max": max(
                    row["relative_psd_operator_correction"]
                    for row in observations
                ),
            }
        )

    payload = {
        "schema_version": 1,
        "kind": "native sparse multivariate FPCA performance characterization",
        "comparative_benchmark": False,
        "thread_limits": {
            key: "1"
            for key in (
                "OMP_NUM_THREADS",
                "OPENBLAS_NUM_THREADS",
                "MKL_NUM_THREADS",
                "NUMEXPR_NUM_THREADS",
            )
        },
        "results": results,
        "all_score_systems_completed": all(
            row["score_failure_rate"] == 0.0 for row in results
        ),
        "interpretation": (
            "Runtime and process peak RSS are conditional on the declared "
            "planar sparse workloads and runner environment. No cross-package "
            "or universal workstation speed claim is made."
        ),
    }
    output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    if not payload["all_score_systems_completed"]:
        raise SystemExit("resource characterization encountered score failures")


def main():
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
        return
    _run_parent(args.repeats, args.output)


if __name__ == "__main__":
    main()
