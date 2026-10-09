"""F1 study-design calibration *pilot* across sparse/imbalance/variance/trial regimes.

All simulations invoke the actual unqualified native F1 estimator; outputs
include missing fits and conditional rejection rates. Small CI defaults cannot
qualify null type-I error and must never auto-authorize release.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import pandas as pd
from eyetrajectoriespy.research import simulate_functional_study_power

DESIGNS = {
    "balanced_same_covariance": {"units_per_group": 8, "other_group_size": 8,
                                  "group_noise_multiplier": 1., "samples_per_trial": 19,
                                  "trials_per_participant": 1},
    "unequal_allocation": {"units_per_group": 8, "other_group_size": 16,
                            "group_noise_multiplier": 1., "samples_per_trial": 19,
                            "trials_per_participant": 1},
    "heteroscedastic_null": {"units_per_group": 8, "other_group_size": 8,
                              "group_noise_multiplier": 2., "samples_per_trial": 19,
                              "trials_per_participant": 1},
    "very_sparse_sampling": {"units_per_group": 8, "other_group_size": 8,
                              "group_noise_multiplier": 1., "samples_per_trial": 9,
                              "trials_per_participant": 1},
    "repeated_participant_curves": {"units_per_group": 8, "other_group_size": 8,
                                    "group_noise_multiplier": 1., "samples_per_trial": 19,
                                    "trials_per_participant": 2},
}

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--replicates", type=int, default=4)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    if args.replicates < 2:
        raise ValueError("at least 2 full-model refits per null/effect scenario")
    summaries, cases = [], []
    for j, (name, design) in enumerate(DESIGNS.items()):
        result = simulate_functional_study_power(
            n_replicates=args.replicates, effect_amplitude=.12,
            noise_sd=.015, n_permutations=99, random_state=10210+j*773,
            **design,
        )
        one = result.summary.copy()
        one["design"] = name
        summaries.append(one)
        trial = result.cases.copy()
        trial["design"] = name
        cases.append(trial)
    args.out.mkdir(parents=True, exist_ok=True)
    summary = pd.concat(summaries, ignore_index=True)
    raw = pd.concat(cases, ignore_index=True)
    summary.to_csv(args.out/"design-summary.csv", index=False)
    raw.to_csv(args.out/"design-cases.csv", index=False)
    evidence = {
        "method": "F1_native_sparse_PACE_permutation_experimental",
        "replicates_per_design_scenario": args.replicates,
        "n_designs": len(DESIGNS),
        "n_total_fit_attempts": len(raw),
        "n_failed_fit_attempts": int((raw.status == "failed").sum()),
        "includes_group_heteroscedasticity": True,
        "includes_unequal_group_sizes": True,
        "includes_repeated_participants": True,
        "type_one_error_or_power_qualified": False,
        "scientific_recommendation_generated": False,
        "release_authorized": False,
    }
    (args.out/"evidence.json").write_text(json.dumps(evidence, sort_keys=True, indent=2)+"\n")
    hashes = []
    for p in sorted(args.out.iterdir()):
        hashes.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}")
    (args.out/"sha256.txt").write_text("\n".join(hashes)+"\n")
    print(json.dumps(evidence, sort_keys=True))
    print(summary.to_string(index=False))

if __name__ == "__main__":
    main()
