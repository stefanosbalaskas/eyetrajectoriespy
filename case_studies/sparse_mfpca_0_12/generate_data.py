"""Generate the frozen redistributable sparse-planar gaze surrogate.

This generator is part of the canonical post-0.12 reproducibility case study.
It creates synthetic normalized x/y gaze samples; it is not empirical human
participant data.  The output is frozen by SHA-256 in ``expected.json``.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd


EXPECTED_SHA256 = "9f1305c91c03aa188ad5535c901eb8140ae4553e92a63eb10569ccbcbaf30bf7"


def build_surrogate() -> pd.DataFrame:
    rng = np.random.default_rng(12012026)
    rows: list[dict[str, object]] = []
    for participant_index in range(36):
        participant = f"P{participant_index + 1:02d}"
        n_observations = int(rng.integers(9, 15))
        interior = np.sort(rng.uniform(0.04, 1.96, n_observations - 2))
        time = np.r_[0.0, interior, 2.0]
        z1, z2 = rng.normal(size=2)
        x = (
            0.46
            + 0.035 * time
            + 0.115 * z1 * np.sin(np.pi * time / 2.0)
            + 0.050 * z2 * np.sin(np.pi * time)
        )
        y = (
            0.53
            - 0.030 * time
            + 0.085 * z1 * np.cos(np.pi * time / 2.0)
            - 0.070 * z2 * np.sin(np.pi * time)
        )
        xy = np.column_stack((x, y)) + rng.normal(
            0.0, 0.025, size=(time.size, 2)
        )
        xy = np.clip(xy, 0.02, 0.98)
        for t, (x_value, y_value) in zip(time, xy, strict=True):
            rows.append(
                {
                    "participant_id": participant,
                    "trial_id": 1,
                    "condition": "free-view",
                    "time_s": float(t),
                    "x": float(x_value),
                    "y": float(y_value),
                }
            )
    return pd.DataFrame(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent / "data" / "input_long.csv",
    )
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    build_surrogate().to_csv(args.output, index=False)
    actual = sha256(args.output)
    if actual != EXPECTED_SHA256:
        raise RuntimeError(
            "frozen surrogate checksum changed: "
            f"expected={EXPECTED_SHA256}, actual={actual}"
        )
    print(f"generated {args.output} sha256={actual}")


if __name__ == "__main__":
    main()
