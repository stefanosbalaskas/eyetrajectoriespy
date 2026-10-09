"""F1 native sparse-MFPCA/PACE whole-pipeline simulation pilot.

Unlike score-kernel checks, this runner *refits native sparse MFPCA per draw*.
Pilot defaults are intentionally too small to qualify population-level size or
power. Every fit failure is retained; no failing replicate is silently dropped.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
from pathlib import Path
import time
import numpy as np
import pandas as pd
from eyetrajectoriespy.types import IrregularTrajectorySet
from eyetrajectoriespy.research import test_sparse_functional_groups

SCENARIOS = {
    "balanced_null": {"n0": 12, "n1": 12, "effect": 0.0},
    "imbalanced_null": {"n0": 8, "n1": 16, "effect": 0.0},
    "balanced_joint_effect": {"n0": 12, "n1": 12, "effect": 0.12},
}

def _fixture(seed: int, *, n0: int, n1: int, effect: float) -> IrregularTrajectorySet:
    rng = np.random.default_rng(seed)
    times, values, names, labels = [], [], [], []
    for i in range(n0 + n1):
        t = np.r_[0.0, np.sort(rng.uniform(.03, .97, size=17)), 1.0]
        factors = rng.normal(size=2)
        group = i >= n0
        x = .45 + .075 * factors[0] * np.sin(np.pi * t)
        x += .035 * factors[1] * np.cos(2 * np.pi * t)
        y = .48 + .07 * factors[0] * np.cos(np.pi * t)
        y += .025 * factors[1] * np.sin(np.pi * t)
        if group:
            x += effect * np.sin(np.pi * t)
            y -= .65 * effect * np.cos(np.pi * t)
        observed = np.column_stack((x, y))
        observed += rng.normal(0, .012, size=observed.shape)
        times.append(t)
        values.append(observed)
        names.append(f"unit{i:03d}")
        labels.append("condition" if group else "control")
    return IrregularTrajectorySet(
        time=tuple(times), values=tuple(values), curve_ids=tuple(names),
        dimension_names=("x", "y"), coordinate_system="normalized",
        time_unit="s",
        metadata=pd.DataFrame({"participant_id": names, "group": labels}),
        provenance={"synthetic_known_truth": True, "group_difference": effect},
    )

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replicates", type=int, default=4)
    parser.add_argument("--permutations", type=int, default=99)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.replicates < 2 or args.permutations < 99:
        raise ValueError("replicates >=2 and permutations >=99 required")
    rng = np.random.default_rng(17008)
    results = []
    for label, params in SCENARIOS.items():
        for repetition in range(args.replicates):
            seed = int(rng.integers(1, 2**31))
            data = _fixture(seed, **params)
            groups = ["control"] * params["n0"] + ["condition"] * params["n1"]
            started = time.perf_counter()
            record = {
                "scenario": label, "iteration": repetition, "seed": seed,
                "n_independent_units": params["n0"] + params["n1"],
                "n0": params["n0"], "n1": params["n1"],
                "effect": params["effect"],
                "n_permutations": args.permutations,
            }
            try:
                fit = test_sparse_functional_groups(
                    data, groups,
                    fit_kwargs={
                        "n_components": 2,
                        "evaluation_grid": np.linspace(0, 1, 21),
                        "mean_bandwidth": 0.30,
                        "covariance_bandwidth": 0.45,
                        "measurement_error": "diagonal",
                        "measurement_error_variance": (.000144, .000144),
                        "psd_action": "project",
                        "score_failure_action": "retain_nan",
                    },
                    n_permutations=args.permutations,
                    random_state=seed + 1,
                )
                record["status"] = "ok"
                record["p_value"] = fit.p_value
                record["statistic"] = fit.statistic
                record["actual_n_scored"] = fit.fit.scores.shape[0]
            except Exception as err:
                record["status"] = "failed"
                record["exception_type"] = type(err).__name__
                record["reason"] = str(err)[:600]
            record["duration_seconds"] = round(time.perf_counter() - started, 5)
            results.append(record)
    args.output.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(results).to_csv(args.output / "full-pipeline-cases.csv", index=False)
    summary = []
    for name in SCENARIOS:
        selected = [record for record in results if record["scenario"] == name]
        successful = [record for record in selected if record["status"] == "ok"]
        summary.append({
            "scenario": name, "requested_replicates": len(selected),
            "successful_replicates": len(successful),
            "failed_replicates": len(selected) - len(successful),
            "conditional_rejection_rate_among_successes": (
                float(np.mean([r["p_value"] <= .05 for r in successful]))
                if successful else None
            ),
            "conditional_rejection_monte_carlo_se": (
                float(np.sqrt(r * (1-r) / len(successful)))
                if successful and (r := float(np.mean(
                    [entry["p_value"] <= .05 for entry in successful]
                ))) >= 0 else None
            ),
            "type_i_and_power_population_inference_warranted": False,
            "scientific_size_or_power_qualified": False,
        })
    evidence = {
        "qualification_level": "whole_native_sparse_pipeline_pilot_not_population_qualification",
        "full_sparse_refit_per_replicate": True,
        "all_failed_fits_retained": True,
        "missing_fit_rejections_count_as_valid_tests": False,
        "source": "seeded_known_truth_synthetic",
        "scenarios": summary,
        "production_release_authorized": False,
    }
    record_path = args.output / "summary.json"
    record_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    (args.output / "sha256.txt").write_text(
        sha256(record_path.read_bytes()).hexdigest() + "  summary.json\n"
    )
    print(json.dumps(summary, indent=2))
    print("F1 sparse native pilot completed; NOT a size/power qualification")

if __name__ == "__main__":
    main()
