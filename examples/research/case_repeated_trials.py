"""Runnable synthetic D4 balanced repeatability and paired-contrast example."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from eyetrajectoriespy.types import TrajectorySet
from eyetrajectoriespy.research import (
    fit_functional_reliability, functional_reliability_frame,
    compare_repeated_functional_groups, repeated_functional_contrast_frame,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    rng = np.random.default_rng(2205)
    t = np.linspace(0, 1, 41)
    values, people, condition, trials = [], [], [], []
    for subject in range(12):
        latent = rng.normal(scale=.11, size=2)
        for cond in ("A", "B"):
            for trial in range(3):
                values.append(
                    np.column_stack((
                        .45 + latent[0]*np.sin(np.pi*t)
                          + (.14*np.sin(np.pi*t) if cond == "B" else 0),
                        .52 + latent[1]*np.cos(np.pi*t),
                    )) + rng.normal(scale=.018, size=(len(t), 2))
                )
                people.append(f"participant_{subject:02d}")
                condition.append(cond)
                trials.append(f"{subject}_{cond}_{trial}")
    gaze = TrajectorySet(
        time=t, values=np.stack(values),
        curve_ids=tuple(trials), dimension_names=("x","y"),
        coordinate_system="normalized", time_unit="s",
        metadata=pd.DataFrame({"participant_id":people,"condition":condition}),
    )
    a_indices = np.flatnonzero(gaze.metadata.condition == "A")
    reliable = fit_functional_reliability(
        gaze.subset(a_indices), condition_column="condition",
    )
    paired = compare_repeated_functional_groups(
        gaze, participants=people, conditions=condition,
        sign_symmetry_assumed=True, n_permutations=199, random_state=2205,
    )
    args.out.mkdir(parents=True, exist_ok=True)
    functional_reliability_frame(reliable).to_csv(args.out/"reliability.csv", index=False)
    repeated_functional_contrast_frame(paired).to_csv(
        args.out/"paired-contrast.csv", index=False
    )
    evidence = {
        "synthetic": True, "participants": paired.n_participants,
        "n_repeated_curves": gaze.n_curves,
        "reliability_balanced": reliable.trials_per_participant == 3,
        "contrast_p_value_experimental": paired.p_value_experimental,
        "calibrated_inference": False,
        "order_or_carryover_modelled": False,
    }
    (args.out/"provenance.json").write_text(json.dumps(evidence,indent=2)+"\n")
    fig, ax = plt.subplots(figsize=(5.4, 2.9))
    for j,name in enumerate(reliable.dimension_names):
        ax.plot(reliable.time,
                reliable.pointwise_mean_trial_reliability[:, j],
                label=name)
    ax.set(ylim=(0,1.01), xlabel="Trial phase",
           ylabel="Moment-based reliability of 3-trial mean",
           title="Synthetic participant/trial repeatability — descriptive")
    ax.legend()
    fig.tight_layout()
    fig.savefig(args.out/"synthetic-reliability.svg",metadata={"Date": None})
    plt.close(fig)
    print("PASS: synthetic reliability/paired functional experiment; no inference qualified")


if __name__ == "__main__":
    main()
