"""Reproducible F1 permutation-kernel and F5 CUSUM simulation pilots.

No claim that isolated score-kernel calibration validates the sparse MFPCA
estimator or that conditional weak-block resampling is size-qualified.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import pandas as pd
from eyetrajectoriespy.types import TrajectorySet
from eyetrajectoriespy.research.sparse_group_inference import (
    _conditional_score_permutation,
)
from eyetrajectoriespy.research import detect_ordered_functional_changepoint



def _mc_binomial(p_values: list[float], alpha: float = .05) -> dict[str, float | int]:
    """Wilson Monte Carlo interval describes simulation uncertainty, NOT method validity."""
    n = len(p_values)
    if n < 1:
        raise ValueError("at least one completed replicate is required")
    k = int(np.count_nonzero(np.asarray(p_values, dtype=float) <= alpha))
    rate = k / n
    z = 1.959963984540054
    denominator = 1 + z*z/n
    center = (rate + z*z/(2*n)) / denominator
    radius = z / denominator * np.sqrt(rate*(1-rate)/n + z*z/(4*n*n))
    return {
        "n": n, "rejections": k, "rate": rate,
        "monte_carlo_standard_error": float(np.sqrt(rate*(1-rate)/n)),
        "wilson_95_low": float(max(0, center-radius)),
        "wilson_95_high": float(min(1, center+radius)),
    }

def score_pilot(
    *,
    seed: int,
    n_replicates: int,
    permutations: int,
    shift: float,
) -> dict[str, object]:
    rng = np.random.default_rng(seed)
    rates = {"null": [], "alternative": []}
    for case in rates:
        for _ in range(n_replicates):
            # Independent standard normal scores represent a *kernel*
            # verification, not sparse gaze observations or PACE fit outputs.
            scores = rng.multivariate_normal(
                [0.0, 0.0],
                [[1.0, 0.45], [0.45, 1.0]],
                size=24,
            )
            labels = np.r_[np.ones(12, dtype=bool), np.zeros(12, dtype=bool)]
            if case == "alternative":
                scores[labels, 0] += shift
                scores[labels, 1] -= shift * 0.35
            _, _, p = _conditional_score_permutation(
                scores, labels,
                n_permutations=permutations,
                random_state=int(rng.integers(0, 2**31 - 1)),
            )
            rates[case].append(p)
    return {
        "programme": "F1-conditional-score-permutation-kernel-only",
        "n_replicates_per_scenario": n_replicates,
        "independent_units": 24,
        "groups": [12, 12],
        "score_covariance": [[1.0, 0.45], [0.45, 1.0]],
        "effect_shift": shift,
        "n_permutations": permutations,
        "seed": seed,
        "null_rejection_rate_at_005": float(np.mean(np.asarray(rates["null"]) <= .05)),
        "alternative_rejection_rate_at_005": float(
            np.mean(np.asarray(rates["alternative"]) <= .05)
        ),
        "null_monte_carlo_uncertainty": _mc_binomial(rates["null"]),
        "alternative_monte_carlo_uncertainty": _mc_binomial(rates["alternative"]),
        "null_p_values": rates["null"],
        "alternative_p_values": rates["alternative"],
        "full_sparse_mfpca_fit_per_replicate": False,
        "not_koner_luo_qualification": True,
        "type_one_and_power_qualification_completed": False,
    }


def change_pilot(
    *,
    seed: int,
    n_replicates: int,
    draws: int,
    effect: float,
    dependence: str,
) -> dict[str, object]:
    rng = np.random.default_rng(seed)
    time = np.linspace(0.0, 1.0, 17)
    rates = {"null": [], "alternative": []}
    for case in rates:
        for _ in range(n_replicates):
            values = rng.normal(0, 0.07, (30, len(time), 2))
            if dependence == "weak_block":
                # Explicit AR(1) curve-level dependence under stationary null.
                # Variance is not standardized to independent regime because
                # this pilot is a separate sensitivity, not power equivalence.
                for index in range(1, 30):
                    values[index] += 0.6 * values[index - 1]
            if case == "alternative":
                values[15:, :, 0] += effect * np.sin(np.pi * time)[None, :]
            gaze = TrajectorySet(
                time=time, values=values,
                curve_ids=tuple(f"trial{i:02d}" for i in range(30)),
                dimension_names=("x", "y"),
                coordinate_system="normalized",
                time_unit="s",
                provenance={"synthetic": True},
            )
            result = detect_ordered_functional_changepoint(
                gaze, dependence=dependence,
                block_length=4 if dependence == "weak_block" else None,
                min_segment=5, n_bootstrap=draws,
                random_state=int(rng.integers(0, 2**31 - 1)),
            )
            rates[case].append({
                "p": result.p_value_experimental,
                "change_location": result.split_index,
            })
    return {
        "programme": "F5-experimental-mean-CUSUM-pilot",
        "dependence": dependence,
        "n_replicates_per_scenario": n_replicates,
        "curves_per_series": 30,
        "grid_samples": len(time),
        "effect_shift": effect,
        "n_bootstrap": draws,
        "seed": seed,
        "null_rejection_rate_at_005": float(np.mean(
            [x["p"] <= .05 for x in rates["null"]]
        )),
        "alternative_rejection_rate_at_005": float(np.mean(
            [x["p"] <= .05 for x in rates["alternative"]]
        )),
        "alternative_median_estimated_split": float(np.median(
            [x["change_location"] for x in rates["alternative"]]
        )),
        "null_monte_carlo_uncertainty": _mc_binomial([x["p"] for x in rates["null"]]),
        "alternative_monte_carlo_uncertainty": _mc_binomial([x["p"] for x in rates["alternative"]]),
        "scenario_records": rates,
        "serial_dependence_inference_qualified": False,
        "not_wendler_robust_test": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--replicates", type=int, default=100)
    parser.add_argument("--permutations", type=int, default=199)
    parser.add_argument("--f5-bootstrap", type=int, default=99)
    args = parser.parse_args()
    if args.replicates < 20 or args.permutations < 99 or args.f5_bootstrap < 99:
        raise ValueError("pilot needs >=20 replications and >=99 resamples")
    args.out.mkdir(parents=True, exist_ok=True)
    result = {
        "schema": 1,
        "qualification_level": "reproducible_pilot_not_population_qualification",
        "score_kernel": score_pilot(
            seed=616, n_replicates=args.replicates,
            permutations=args.permutations, shift=1.0,
        ),
        "ordered_change_independent": change_pilot(
            seed=617, n_replicates=args.replicates,
            draws=args.f5_bootstrap, effect=0.21,
            dependence="independent",
        ),
        "ordered_change_AR1": change_pilot(
            seed=618, n_replicates=args.replicates,
            draws=args.f5_bootstrap, effect=0.21,
            dependence="weak_block",
        ),
        "full_scientific_qualification_passed": False,
        "production_promotion_authorized": False,
    }
    output = args.out / "pilot.json"
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    digest = sha256(output.read_bytes()).hexdigest()
    (args.out / "sha256.txt").write_text(f"{digest}  pilot.json\n")
    rows = []
    for name in ("score_kernel", "ordered_change_independent", "ordered_change_AR1"):
        evidence = result[name]
        rows.append({
            "scenario": name,
            "n_replicates": args.replicates,
            "null_rejection_005": evidence["null_rejection_rate_at_005"],
            "alternative_rejection_005": evidence["alternative_rejection_rate_at_005"],
            "null_monte_carlo_se": evidence["null_monte_carlo_uncertainty"]["monte_carlo_standard_error"],
            "null_wilson_95_low": evidence["null_monte_carlo_uncertainty"]["wilson_95_low"],
            "null_wilson_95_high": evidence["null_monte_carlo_uncertainty"]["wilson_95_high"],
            "full_qualification": False,
        })
    pd.DataFrame(rows).to_csv(args.out / "pilot-summary.csv", index=False)
    print(json.dumps(rows, sort_keys=True))
    print("F1/F5 research pilots completed; inference NOT qualified")


if __name__ == "__main__":
    main()
