"""Sparse irregular FPCA with FDApy PACE score recovery."""

import numpy as np
import pandas as pd

from eyetrajectoriespy import (
    IrregularTrajectorySet,
    fit_sparse_fpca_fdapy,
    sparse_dimension_summary,
    sparse_fpca_reporting_text,
    sparse_fpca_score_frame,
)


def synthetic_sparse_curves(
    *,
    n_curves: int = 18,
    random_state: int = 2026,
) -> IrregularTrajectorySet:
    rng = np.random.default_rng(random_state)
    dense_time = np.linspace(0.0, 1.0, 41)
    times = []
    values = []
    ids = []
    participants = []

    for i in range(n_curves):
        keep = np.sort(rng.choice(len(dense_time), size=12, replace=False))
        time = dense_time[keep]
        amplitude = rng.normal(scale=0.25)
        trajectory = (
            np.sin(2 * np.pi * time)
            + amplitude * np.cos(np.pi * time)
            + rng.normal(scale=0.05, size=len(time))
        )
        times.append(time)
        values.append(trajectory[:, None])
        ids.append(f"P{i + 1:02d}|1")
        participants.append(f"P{i + 1:02d}")

    return IrregularTrajectorySet(
        time=tuple(times),
        values=tuple(values),
        curve_ids=tuple(ids),
        dimension_names=("x",),
        metadata=pd.DataFrame({"participant_id": participants}),
        coordinate_system="normalized",
        time_unit="s",
        provenance={"source": "synthetic_sparse_pace_example"},
    )


def main() -> None:
    gaze = synthetic_sparse_curves()

    print(sparse_dimension_summary(gaze, dimension="x").head().to_string(index=False))

    result = fit_sparse_fpca_fdapy(
        gaze,
        dimension="x",
        n_components=3,
        fit_smoothing="PS",
        score_smoothing="LP",
        tol=1e-4,
        normalize=False,
        evaluation_grid=np.linspace(0.0, 1.0, 101),
    )

    print()
    print(sparse_fpca_score_frame(result).head().to_string(index=False))
    print()
    print(sparse_fpca_reporting_text(result))


if __name__ == "__main__":
    main()
