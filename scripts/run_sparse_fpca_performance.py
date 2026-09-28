"""Sparse-FPCA runtime/peak-memory characterization for the 0.10 branch."""

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
import pandas as pd


CASES = {
    "very_sparse": {
        "n_curves": 80,
        "samples_per_curve": 4,
        "grid_points": 21,
        "mean_bandwidth": 0.32,
        "covariance_bandwidth": 0.44,
    },
    "moderate_sparse": {
        "n_curves": 60,
        "samples_per_curve": 8,
        "grid_points": 31,
        "mean_bandwidth": 0.25,
        "covariance_bandwidth": 0.34,
    },
    "irregular_rich": {
        "n_curves": 36,
        "samples_per_curve": 16,
        "grid_points": 41,
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
    from eyetrajectoriespy import IrregularTrajectorySet, fit_sparse_fpca
    from eyetrajectoriespy._sparse_truth import simulate_sparse_functional_truth

    spec = CASES[name]
    times, values, truth = simulate_sparse_functional_truth(
        n_curves=spec["n_curves"],
        samples_per_curve=spec["samples_per_curve"],
        noise_sd=0.10,
        random_state=202700 + list(CASES).index(name),
    )
    trajectories = IrregularTrajectorySet(
        time=times,
        values=tuple(value[:, None] for value in values),
        curve_ids=tuple(f"P{i:03d}" for i in range(len(times))),
        dimension_names=("x",),
        metadata=pd.DataFrame(
            {"participant_id": [f"P{i:03d}" for i in range(len(times))]}
        ),
        coordinate_system="normalized",
        time_unit="s",
    )
    pair_count = int(
        sum(len(time) * (len(time) - 1) for time in trajectories.time)
    )
    start = time.perf_counter()
    result = fit_sparse_fpca(
        trajectories,
        dimension="x",
        n_components=2,
        evaluation_grid=np.linspace(
            0.0,
            1.0,
            spec["grid_points"],
        ),
        mean_bandwidth=spec["mean_bandwidth"],
        covariance_bandwidth=spec["covariance_bandwidth"],
        noise_variance_method="fixed",
        measurement_error_variance=truth.noise_sd**2,
        psd_action="project",
        score_failure_action="retain_nan",
    )
    elapsed = time.perf_counter() - start
    payload = {
        "case": name,
        "n_curves": trajectories.n_curves,
        "median_samples_per_curve": float(
            np.median(trajectories.sample_counts)
        ),
        "covariance_pair_count": pair_count,
        "grid_points": spec["grid_points"],
        "runtime_seconds": elapsed,
        "peak_memory_mib": _peak_rss_mib(),
        "score_failure_rate": float(
            np.mean(
                result.score_diagnostics["status_code"].to_numpy()
                != "ok"
            )
        ),
    }
    print("SPARSE_PERFORMANCE_RESULT=" + json.dumps(payload, sort_keys=True))


def _quantile(values, probability):
    ordered = sorted(float(value) for value in values)
    if len(ordered) == 1:
        return ordered[0]
    position = probability * (len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def _run_parent(repeats, output):
    if repeats < 3:
        raise ValueError("qualification requires at least three repeats")
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
                    f"sparse performance child {name!r} failed\n"
                    f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
                )
            markers = [
                line
                for line in completed.stdout.splitlines()
                if line.startswith("SPARSE_PERFORMANCE_RESULT=")
            ]
            if len(markers) != 1:
                raise RuntimeError(
                    f"sparse performance child {name!r} emitted "
                    f"{len(markers)} result markers"
                )
            observations.append(json.loads(markers[0].split("=", 1)[1]))

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
                "covariance_pair_count",
                "grid_points",
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
                "score_failure_rate": max(
                    row["score_failure_rate"] for row in observations
                ),
            }
        )

    payload = {
        "schema_version": 1,
        "kind": "native sparse FPCA/PACE performance characterization",
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
        "interpretation": (
            "Runtime and process peak RSS are conditional on the declared "
            "(n, median N_i, P, G) workloads and runner environment. No "
            "cross-package or universal workstation speed claim is made."
        ),
    }
    output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, sort_keys=True))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("sparse-fpca-performance.json"),
    )
    parser.add_argument("--child-case", choices=tuple(CASES))
    args = parser.parse_args()
    if args.child_case is not None:
        _run_case(args.child_case)
        return
    _run_parent(args.repeats, args.output)


if __name__ == "__main__":
    main()
