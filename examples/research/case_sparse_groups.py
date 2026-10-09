"""Runnable synthetic D1 example: native sparse F1 study-planning pilot.

This is NOT a validated power or sample-size result. Requires source 1.2 dev.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from eyetrajectoriespy.research import simulate_functional_study_power


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--replicates", type=int, default=2)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    result = simulate_functional_study_power(
        units_per_group=8, n_replicates=args.replicates,
        samples_per_trial=19, trials_per_participant=1,
        effect_amplitude=.08, n_permutations=99,
        random_state=20261,
    )
    result.cases.to_csv(args.out/"cases.csv", index=False)
    result.summary.to_csv(args.out/"summary.csv", index=False)
    (args.out/"provenance.json").write_text(
        json.dumps(dict(result.plan), indent=2, default=str)+"\n"
    )
    fig, ax = plt.subplots(figsize=(5.4, 2.9))
    frame = result.summary
    ax.bar(frame.scenario.tolist(),
           frame.fraction_reject_005_given_fit.fillna(0).to_numpy())
    ax.set(ylim=(0, 1), ylabel="Conditional rejection fraction",
           title="Sparse F1 native refit pilot — not calibrated power")
    fig.tight_layout()
    fig.savefig(args.out/"synthetic-pilot.svg", metadata={"Date": None})
    plt.close(fig)
    assert result.recommended_sample_size is None
    assert not result.scientifically_qualified
    print("PASS: synthetic F1 cases, summary and figure; inference unqualified")


if __name__ == "__main__":
    main()
