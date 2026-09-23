"""Benchmark recurrence-radius profiles without asserting performance targets."""

from __future__ import annotations

import argparse
from time import perf_counter

import numpy as np

from eyetrajectoriespy import TrajectorySet, recurrence_radius_profile


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, nargs="+", default=[5000, 18000])
    parser.add_argument("--dimensions", type=int, default=2)
    parser.add_argument(
        "--radii",
        type=float,
        nargs="+",
        default=[0.01, 0.02, 0.05, 0.10],
    )
    parser.add_argument("--theiler", type=int, default=0)
    parser.add_argument("--seed", type=int, default=20260923)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if args.dimensions < 1:
        raise ValueError("--dimensions must be positive")
    if any(n < 2 for n in args.n):
        raise ValueError("every --n value must be at least 2")
    if len(args.radii) < 2:
        raise ValueError("--radii requires at least two values")

    rng = np.random.default_rng(args.seed)
    names = tuple(f"state_{j}" for j in range(args.dimensions))

    print(
        "n,dimensions,n_radii,max_radius,theiler,max_rr,"
        "elapsed_seconds,table_bytes"
    )
    for n in args.n:
        trajectories = TrajectorySet(
            time=np.arange(n, dtype=float),
            values=rng.random((1, n, args.dimensions)),
            curve_ids=(f"synthetic_{n}",),
            dimension_names=names,
            time_unit="samples",
            coordinate_system="arbitrary",
            provenance={
                "benchmark_seed": args.seed,
                "benchmark_distribution": "iid_uniform_0_1",
            },
        )
        start = perf_counter()
        result = recurrence_radius_profile(
            trajectories,
            curve=0,
            radii=args.radii,
            dimensions=names,
            theiler_window=args.theiler,
        )
        elapsed = perf_counter() - start
        table_bytes = int(
            result.table.memory_usage(index=True, deep=True).sum()
        )
        print(
            f"{n},{args.dimensions},{result.n_radii},"
            f"{result.table['radius'].iloc[-1]},"
            f"{args.theiler},"
            f"{result.table['recurrence_rate'].iloc[-1]:.12g},"
            f"{elapsed:.6f},{table_bytes}"
        )


if __name__ == "__main__":
    main()
