"""Minimal installed-package smoke test used by release workflows."""

from __future__ import annotations

import argparse

import numpy as np

import eyetrajectoriespy as et


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-version", required=True)
    args = parser.parse_args()

    if et.__version__ != args.expected_version:
        raise RuntimeError(
            f"installed version mismatch: {et.__version__} != "
            f"{args.expected_version}"
        )

    time = np.linspace(0.0, 1.0, 9)
    values = np.stack(
        (
            np.sin(np.pi * time),
            1.1 * np.sin(np.pi * time),
            0.9 * np.sin(np.pi * time),
            -np.sin(np.pi * time),
        ),
        axis=0,
    )
    trajectories = et.TrajectorySet(
        time=time,
        values=values[:, :, None],
        curve_ids=("a", "b", "c", "d"),
        dimension_names=("signal",),
        coordinate_system="unknown",
        time_unit="s",
    )
    fit = et.fit_fpca(
        trajectories,
        n_components=1,
        scaling="none",
    )
    if fit.components.shape != (1, time.size, 1):
        raise RuntimeError("installed-package FPCA smoke result has wrong shape")
    if not np.isfinite(fit.explained_variance[0]):
        raise RuntimeError("installed-package FPCA smoke result is non-finite")
    print(f"eyetrajectoriespy {et.__version__} release smoke test passed")


if __name__ == "__main__":
    main()
