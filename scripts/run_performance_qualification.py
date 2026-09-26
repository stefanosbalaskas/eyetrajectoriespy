"""Reproducible runtime/peak-memory qualification for expensive workflows.

This is not a comparative benchmark. It records one package/environment
performance envelope under an explicit synthetic workload and never asserts
that eyetrajectoriespy is faster than another implementation.
"""

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


PROFILE = {
    "ci-qualification": {
        "fpca_bootstrap": {
            "n_participants": 10,
            "n_trials": 3,
            "n_time": 41,
            "n_bootstrap": 20,
            "q": 3,
        },
        "mixed_full_refit_bootstrap": {
            "n_participants": 12,
            "n_trials": 3,
            "n_time": 6,
            "n_bootstrap": 20,
            "q": 2,
        },
        "nested_mixed_fit": {
            "n_participants": 8,
            "n_trials": 3,
            "n_time": 5,
            "q": 2,
        },
        "generalized_gee_bootstrap": {
            "n_participants": 8,
            "n_trials": 2,
            "n_time": 5,
            "n_bootstrap": 100,
            "q": 2,
        },
        "recurrence_rqa": {
            "n_participants": 1,
            "n_trials": 1,
            "n_time": 800,
            "q": None,
        },
        "nonlinear_sensitivity": {
            "n_participants": 1,
            "n_trials": 1,
            "n_time": 300,
            "q": None,
            "n_specifications": 16,
        },
    }
}


def _peak_rss_mib() -> float | None:
    try:
        import resource
    except ImportError:
        return None
    value = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    if sys.platform == "darwin":
        return value / (1024.0 * 1024.0)
    return value / 1024.0


def _linear_basis(time_values):
    import numpy as np

    time_values = np.asarray(time_values, dtype=float)
    scaled = (time_values - time_values[0]) / (
        time_values[-1] - time_values[0]
    )
    return np.column_stack((1.0 - scaled, scaled))


def _mixed_data(*, n_participants, n_trials, n_time, seed, include_trial_ids):
    import numpy as np
    import pandas as pd

    from eyetrajectoriespy import TrajectorySet

    rng = np.random.default_rng(seed)
    time_values = np.linspace(0.0, 1.0, n_time)
    basis = _linear_basis(time_values)
    condition_template = np.linspace(-0.5, 0.5, n_trials)
    condition = np.tile(condition_template, n_participants)
    participant_ids = np.repeat(
        [f"P{i:02d}" for i in range(n_participants)],
        n_trials,
    )
    random_coefficients = rng.multivariate_normal(
        np.zeros(2),
        np.array([[0.030, 0.004], [0.004, 0.020]]),
        size=n_participants,
    )
    intercept = 0.25 + 0.10 * time_values
    slope = 0.15 + 0.25 * time_values

    values = []
    trial_ids = []
    for participant_index in range(n_participants):
        participant_random = random_coefficients[participant_index] @ basis.T
        for trial_index in range(n_trials):
            curve_index = participant_index * n_trials + trial_index
            trial_random = (
                rng.normal(0.0, 0.025, size=n_time)
                if include_trial_ids
                else 0.0
            )
            response = (
                intercept
                + condition[curve_index] * slope
                + participant_random
                + trial_random
                + rng.normal(0.0, 0.035, size=n_time)
            )
            values.append(response[:, None])
            trial_ids.append(f"P{participant_index:02d}_T{trial_index:02d}")

    metadata = {"participant_id": participant_ids}
    if include_trial_ids:
        metadata["trial_id"] = trial_ids
    trajectories = TrajectorySet(
        time=time_values,
        values=np.asarray(values),
        curve_ids=tuple(f"M{i:03d}" for i in range(len(values))),
        dimension_names=("response",),
        metadata=pd.DataFrame(metadata),
        coordinate_system="arbitrary",
        time_unit="s",
    )
    design = pd.DataFrame(
        {
            "curve_id": trajectories.curve_ids,
            "condition": condition,
        }
    )
    return trajectories, design


def _case_fpca_bootstrap(scale):
    from eyetrajectoriespy import (
        bootstrap_fpca_stability,
        simulate_planar_trajectories,
    )

    trajectories = simulate_planar_trajectories(
        n_participants=scale["n_participants"],
        trials_per_participant=scale["n_trials"],
        n_time=scale["n_time"],
        random_state=560,
    )
    bootstrap_fpca_stability(
        trajectories,
        n_bootstrap=scale["n_bootstrap"],
        n_components=scale["q"],
        scaling="dimension_sd",
        resample_unit="participant",
        participant_column="participant_id",
        random_state=560,
    )


def _case_mixed_full_refit_bootstrap(scale):
    from eyetrajectoriespy import (
        bootstrap_functional_mixed_effects_full_refit,
        fit_functional_mixed_effects_regression,
    )

    trajectories, design = _mixed_data(
        n_participants=scale["n_participants"],
        n_trials=scale["n_trials"],
        n_time=scale["n_time"],
        seed=461,
        include_trial_ids=False,
    )
    fitted = fit_functional_mixed_effects_regression(
        trajectories,
        design,
        predictors=("condition",),
        participant_column="participant_id",
        dimension="response",
        fixed_basis_size=scale["q"],
        random_basis_size=scale["q"],
        spline_degree=1,
        reml=True,
        maxiter=1000,
    )
    bootstrap_functional_mixed_effects_full_refit(
        fitted,
        n_bootstrap=scale["n_bootstrap"],
        random_state=561,
    )


def _case_nested_mixed_fit(scale):
    from eyetrajectoriespy import fit_functional_mixed_effects_regression

    trajectories, design = _mixed_data(
        n_participants=scale["n_participants"],
        n_trials=scale["n_trials"],
        n_time=scale["n_time"],
        seed=562,
        include_trial_ids=True,
    )
    fit_functional_mixed_effects_regression(
        trajectories,
        design,
        predictors=("condition",),
        participant_column="participant_id",
        trial_column="trial_id",
        dimension="response",
        fixed_basis_size=scale["q"],
        random_basis_size=scale["q"],
        trial_random_effect="functional_intercept",
        trial_random_basis_size=scale["q"],
        residual_correlation="iid",
        spline_degree=1,
        reml=False,
        maxiter=300,
    )


def _case_generalized_gee_bootstrap(scale):
    import numpy as np
    import pandas as pd

    from eyetrajectoriespy import (
        TrajectorySet,
        bootstrap_generalized_function_on_scalar_coefficients,
        fit_generalized_function_on_scalar_regression,
    )

    rng = np.random.default_rng(563)
    n_participants = scale["n_participants"]
    n_trials = scale["n_trials"]
    time_values = np.linspace(0.0, 1.0, scale["n_time"])
    participants = np.repeat(
        [f"P{i:02d}" for i in range(n_participants)],
        n_trials,
    )
    condition = np.tile(np.linspace(0.0, 1.0, n_trials), n_participants)
    eta = (
        (0.10 + 0.15 * time_values)[None, :]
        + condition[:, None] * (0.30 - 0.10 * time_values)[None, :]
    )
    exposure = (
        0.8
        + 0.4 * time_values[None, :]
        + 0.1 * (np.arange(condition.size)[:, None] % 3)
    )
    counts = rng.poisson(exposure * np.exp(eta)).astype(float)
    trajectories = TrajectorySet(
        time=time_values,
        values=counts[:, :, None],
        curve_ids=tuple(f"G{i:03d}" for i in range(counts.shape[0])),
        dimension_names=("count",),
        metadata=pd.DataFrame({"participant_id": participants}),
        coordinate_system="arbitrary",
        time_unit="s",
    )
    design = pd.DataFrame(
        {
            "curve_id": trajectories.curve_ids,
            "condition": condition,
        }
    )
    fitted = fit_generalized_function_on_scalar_regression(
        trajectories,
        design,
        predictors=("condition",),
        participant_column="participant_id",
        dimension="count",
        family="poisson",
        exposure=exposure,
        exposure_units="seconds",
        basis_size=scale["q"],
        spline_degree=1,
    )
    bootstrap_generalized_function_on_scalar_coefficients(
        fitted,
        n_bootstrap=scale["n_bootstrap"],
        random_state=563,
    )


def _case_recurrence_rqa(scale):
    import numpy as np

    from eyetrajectoriespy import TrajectorySet, recurrence_matrix, rqa_metrics

    n_time = scale["n_time"]
    time_values = np.arange(n_time, dtype=float)
    values = (
        np.sin(np.linspace(0.0, 24.0 * np.pi, n_time))
        + 0.15 * np.sin(np.linspace(0.0, 70.0 * np.pi, n_time))
    )
    trajectories = TrajectorySet(
        time=time_values,
        values=values[None, :, None],
        curve_ids=("R0",),
        dimension_names=("x",),
        coordinate_system="arbitrary",
        time_unit="samples",
    )
    recurrence = recurrence_matrix(
        trajectories,
        curve=0,
        radius=0.12,
        theiler_window=2,
        dimensions=("x",),
    )
    rqa_metrics(
        recurrence,
        min_diagonal_length=2,
        min_vertical_length=2,
    )


def _case_nonlinear_sensitivity(scale):
    import numpy as np

    from eyetrajectoriespy import TrajectorySet, rqa_parameter_sensitivity

    n_time = scale["n_time"]
    time_values = np.arange(n_time, dtype=float)
    values = np.sin(np.linspace(0.0, 18.0 * np.pi, n_time))
    trajectories = TrajectorySet(
        time=time_values,
        values=values[None, :, None],
        curve_ids=("S0",),
        dimension_names=("x",),
        coordinate_system="arbitrary",
        time_unit="samples",
    )
    result = rqa_parameter_sensitivity(
        trajectories,
        curve=0,
        dimensions=("x",),
        embedding_dimensions=(2, 3),
        delays=(1, 2),
        theiler_windows=(1, 2),
        min_diagonal_lengths=(2,),
        min_vertical_lengths=(2,),
        radii=(0.20, 0.30),
    )
    if len(result.table) != scale["n_specifications"]:
        raise RuntimeError("unexpected sensitivity specification count")


CASES = {
    "fpca_bootstrap": _case_fpca_bootstrap,
    "mixed_full_refit_bootstrap": _case_mixed_full_refit_bootstrap,
    "nested_mixed_fit": _case_nested_mixed_fit,
    "generalized_gee_bootstrap": _case_generalized_gee_bootstrap,
    "recurrence_rqa": _case_recurrence_rqa,
    "nonlinear_sensitivity": _case_nonlinear_sensitivity,
}


def _run_child(case_name, profile_name):
    scale = PROFILE[profile_name][case_name]
    start = time.perf_counter()
    CASES[case_name](scale)
    elapsed = time.perf_counter() - start
    payload = {
        "case": case_name,
        "profile": profile_name,
        "runtime_seconds": elapsed,
        "peak_memory_mib": _peak_rss_mib(),
        "scale": scale,
    }
    print("BENCHMARK_RESULT=" + json.dumps(payload, sort_keys=True))


def _quantile(values, probability):
    ordered = sorted(float(value) for value in values)
    if len(ordered) == 1:
        return ordered[0]
    position = probability * (len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def _cpu_model():
    cpuinfo = Path("/proc/cpuinfo")
    if cpuinfo.exists():
        for line in cpuinfo.read_text(encoding="utf-8").splitlines():
            if line.lower().startswith("model name"):
                return line.split(":", 1)[1].strip()
    return platform.processor() or None


def _environment():
    packages = {}
    for package_name in (
        "eyetrajectoriespy",
        "numpy",
        "scipy",
        "pandas",
        "scikit-learn",
        "statsmodels",
    ):
        try:
            packages[package_name] = importlib.metadata.version(package_name)
        except importlib.metadata.PackageNotFoundError:
            packages[package_name] = None
    return {
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "cpu_model": _cpu_model(),
        "logical_cpu_count": os.cpu_count(),
        "packages": packages,
        "git_commit": os.environ.get("GITHUB_SHA"),
        "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        "github_runner_name": os.environ.get("RUNNER_NAME"),
        "github_runner_environment": os.environ.get("RUNNER_ENVIRONMENT"),
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


def _run_parent(profile_name, repeats, output_path):
    if repeats < 3:
        raise ValueError("qualification requires at least three repeated timings")
    results = []
    script_path = str(Path(__file__).resolve())
    for case_name in PROFILE[profile_name]:
        case_results = []
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
                [
                    sys.executable,
                    script_path,
                    "--profile",
                    profile_name,
                    "--child-case",
                    case_name,
                ],
                check=False,
                capture_output=True,
                text=True,
                env=env,
            )
            if completed.returncode != 0:
                raise RuntimeError(
                    f"benchmark child {case_name!r} failed with exit "
                    f"{completed.returncode}\nSTDOUT:\n{completed.stdout}\n"
                    f"STDERR:\n{completed.stderr}"
                )
            marker = [
                line
                for line in completed.stdout.splitlines()
                if line.startswith("BENCHMARK_RESULT=")
            ]
            if len(marker) != 1:
                raise RuntimeError(
                    f"benchmark child {case_name!r} did not emit one result"
                )
            case_results.append(
                json.loads(marker[0].split("=", 1)[1])
            )

        runtimes = [item["runtime_seconds"] for item in case_results]
        memories = [
            item["peak_memory_mib"]
            for item in case_results
            if item["peak_memory_mib"] is not None
        ]
        results.append(
            {
                "case": case_name,
                "scale": PROFILE[profile_name][case_name],
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
            }
        )

    payload = {
        "schema_version": 1,
        "benchmark_kind": "single-package performance envelope",
        "comparative_benchmark": False,
        "profile": profile_name,
        "environment": _environment(),
        "results": results,
        "interpretation": (
            "Observed runtime and process peak RSS on the recorded environment. "
            "No cross-package speed claim and no universal workstation claim."
        ),
    }
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, sort_keys=True))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--profile",
        choices=tuple(PROFILE),
        default="ci-qualification",
    )
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--output", type=Path, default=Path("performance-envelope.json"))
    parser.add_argument("--child-case", choices=tuple(CASES))
    args = parser.parse_args()

    if args.child_case is not None:
        _run_child(args.child_case, args.profile)
        return
    _run_parent(args.profile, args.repeats, args.output)


if __name__ == "__main__":
    main()
