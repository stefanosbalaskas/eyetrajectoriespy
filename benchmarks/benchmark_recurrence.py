"""Benchmark sparse recurrence construction without asserting performance targets."""

from __future__ import annotations

import argparse
from time import perf_counter

import numpy as np

from eyetrajectoriespy import TrajectorySet, recurrence_matrix


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, nargs="+", default=[5000, 18000])
    parser.add_argument("--dimensions", type=int, default=2)
    policy = parser.add_mutually_exclusive_group(required=True)
    policy.add_argument("--radius", type=float)
    policy.add_argument("--target-rr", type=float)
    parser.add_argument("--theiler", type=int, default=0)
    parser.add_argument("--seed", type=int, default=20260923)
    return parser.parse_args()


def _csr_bytes(matrix) -> int:
    return int(matrix.data.nbytes + matrix.indices.nbytes + matrix.indptr.nbytes)


def main() -> None:
    args = _parse_args()
    if args.dimensions < 1:
        raise ValueError("--dimensions must be positive")
    if any(n < 2 for n in args.n):
        raise ValueError("every --n value must be at least 2")

    rng = np.random.default_rng(args.seed)
    names = tuple(f"state_{j}" for j in range(args.dimensions))

    print(
        "n,dimensions,policy,value,theiler,achieved_rr,elapsed_seconds,"
        "nnz,csr_bytes"
    )
    for n in args.n:
        values = rng.random((1, n, args.dimensions))
        trajectories = TrajectorySet(
            time=np.arange(n, dtype=float),
            values=values,
            curve_ids=(f"synthetic_{n}",),
            dimension_names=names,
            time_unit="samples",
            coordinate_system="arbitrary",
            provenance={
                "benchmark_seed": args.seed,
                "benchmark_distribution": "iid_uniform_0_1",
            },
        )
        kwargs = (
            {"radius": args.radius}
            if args.radius is not None
            else {"target_recurrence_rate": args.target_rr}
        )
        start = perf_counter()
        result = recurrence_matrix(
            trajectories,
            curve=0,
            dimensions=names,
            theiler_window=args.theiler,
            **kwargs,
        )
        elapsed = perf_counter() - start
        policy_name = "radius" if args.radius is not None else "target_rr"
        policy_value = args.radius if args.radius is not None else args.target_rr
        print(
            f"{n},{args.dimensions},{policy_name},{policy_value},"
            f"{args.theiler},{result.achieved_recurrence_rate:.12g},"
            f"{elapsed:.6f},{result.matrix.nnz},{_csr_bytes(result.matrix)}"
        )


if __name__ == "__main__":
    main()
