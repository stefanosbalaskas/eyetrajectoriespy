"""F4: seeded AOI simplex-geometry heldout reconstruction feasibility pilot.

Compares two simple estimators ONLY: existing ALR-FPCA and raw-space
FPCA + posthoc projection. It does not implement Kwan et al.'s constrained
principal component method and cannot qualify a new estimator.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
from pathlib import Path
import numpy as np
import pandas as pd
from eyetrajectoriespy.types import TrajectorySet
from eyetrajectoriespy.research import compare_aoi_functional_geometries_holdout


def _sample(seed: int, *, zero_pattern: bool) -> TrajectorySet:
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 1, 21)
    n = 45
    participant = rng.normal(0, .65, size=(n, 3))
    curve = np.empty((n, len(t), 3))
    for i in range(n):
        phase = float(rng.normal(0, .05))
        z = np.column_stack((
            .25 + participant[i, 0] + 1.25 * np.sin(np.pi * t + phase),
            -.1 + participant[i, 1] + .85 * np.cos(np.pi * t),
            participant[i, 2] + .65 * np.sin(2*np.pi*t),
        ))
        z += rng.normal(0, .08, z.shape)
        e = np.exp(z - z.max(axis=1, keepdims=True))
        curve[i] = e / e.sum(axis=1, keepdims=True)
    if zero_pattern:
        for i in range(n):
            channel = i % 3
            interval = (slice(3, 8) if i % 2 else slice(12, 18))
            curve[i, interval, channel] = 0
            curve[i, interval] /= curve[i, interval].sum(axis=-1, keepdims=True)
    return TrajectorySet(
        time=t, values=curve,
        curve_ids=tuple(f"unit{i:03d}" for i in range(n)),
        dimension_names=("headword", "definition", "context"),
        metadata=pd.DataFrame({"participant_id": [f"P{i:03d}" for i in range(n)]}),
        coordinate_system="probability_simplex",
        time_unit="normalized",
        provenance={"source": "synthetic", "known_truth": True,
                    "structural_zeros": zero_pattern},
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replicates", type=int, default=6)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.replicates < 2:
        raise ValueError("minimum 2 seeds required")
    outputs = []
    for zero_pattern in (False, True):
        for replicate in range(args.replicates):
            seed = 4170 + replicate + 100 * int(zero_pattern)
            data = _sample(seed, zero_pattern=zero_pattern)
            train, test = data.subset(range(30)), data.subset(range(30, 45))
            for ref in range(3):
                for epsilon in (1e-6, 1e-4):
                    # No train-test participant overlap and no estimator selection.
                    result = compare_aoi_functional_geometries_holdout(
                        train, test, n_components=2,
                        reference_dimension=ref, epsilon=epsilon,
                    )
                    for _, row in result.summary.iterrows():
                        outputs.append({
                            "replicate": replicate,
                            "source_seed": seed,
                            "zero_pattern": zero_pattern,
                            "reference_dimension": ref,
                            "epsilon": epsilon,
                            "geometry": str(row.geometry),
                            "heldout_reconstruction_mse": float(
                                row.holdout_reconstruction_mse
                            ),
                            "n_train": result.n_train,
                            "n_test": result.n_test,
                            "leakage_guard_passed": result.leakage_guard_passed,
                        })
    args.out.mkdir(parents=True, exist_ok=True)
    table = pd.DataFrame(outputs)
    if not np.isfinite(table["heldout_reconstruction_mse"]).all():
        raise RuntimeError("nonfinite holdout reconstruction risk")
    path = args.out / "holdout-cases.csv"
    table.to_csv(path, index=False, float_format="%.12g")
    summary = {
        "qualification_level": "experimental_holdout_feasibility_not_constrained_fpca",
        "n_seed_replicates": args.replicates,
        "zero_patterns": [False, True],
        "reference_aois": 3,
        "epsilons": [1e-6, 1e-4],
        "geometry_comparisons": [
            "existing_ALR_FPCA", "raw_FPCA_then_simplex_projection"
        ],
        "heldout_curve_projection_not_prediction": True,
        "all_training_test_participants_disjoint": True,
        "n_rows": len(table),
        "n_train_per_case": 30,
        "n_test_per_case": 15,
        "new_constrained_estimator_scientifically_qualified": False,
        "published_Kwan_estimator_implemented": False,
        "release_authorized": False,
        "group_summary": table.groupby(["zero_pattern", "geometry"])[
            "heldout_reconstruction_mse"
        ].agg(["count", "mean", "std"]).reset_index().to_dict("records"),
    }
    summary_path = args.out / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    (args.out / "sha256.txt").write_text(
        sha256(path.read_bytes()).hexdigest() + "  holdout-cases.csv\n"
        + sha256(summary_path.read_bytes()).hexdigest() + "  summary.json\n"
    )
    print(json.dumps({
        "rows": len(table),
        "seeds": args.replicates,
        "feasibility_only": True,
    }))


if __name__ == "__main__":
    main()
