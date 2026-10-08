"""F5 experimental whole-functional mean CUSUM across ordered curves.
Not within-curve saccade detection or the robust U-statistic of Wegner and Wendler.
Dependent weak-stationary null approximation requires a declared block length.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping, Any
import numpy as np
import pandas as pd
from eyetrajectoriespy.types import TrajectorySet

@dataclass(frozen=True)
class FunctionalChangepointResult:
    split_index: int
    statistic: float
    scan: pd.DataFrame
    null_statistics: np.ndarray
    p_value_experimental: float
    evidence: Mapping[str, Any]

def detect_ordered_functional_changepoint(
    trajectories: TrajectorySet, *, dependence: str,
    block_length: int | None = None, min_segment: int = 4,
    n_bootstrap: int = 499, random_state: int = 0,
) -> FunctionalChangepointResult:
    """Whole-function scan; conditional bootstrap calibration remains unqualified."""
    if not isinstance(trajectories, TrajectorySet):
        raise TypeError("common-grid TrajectorySet required")
    x = np.asarray(trajectories.values, float)
    n = len(x)
    if not np.isfinite(x).all():
        raise ValueError("missing values require declared preprocessing")
    if dependence not in ("independent", "weak_block"):
        raise ValueError("declare independent or weak_block dependence")
    if isinstance(n_bootstrap, bool) or n_bootstrap < 99:
        raise ValueError("at least 99 bootstrap draws required")
    if min_segment < 3 or n < 2 * min_segment:
        raise ValueError("not enough ordered curves")
    if dependence == "weak_block":
        if block_length is None or not isinstance(block_length, int) or not 2 <= block_length <= n // 2:
            raise ValueError("weak_block requires an explicit valid block_length")
    elif block_length is not None:
        raise ValueError("independent mode forbids block_length")
    split = np.arange(min_segment, n - min_segment + 1)
    def stat(curves):
        c = np.cumsum(curves, axis=0)
        a = c[split - 1] / split[:, None, None]
        b = (c[-1] - c[split - 1]) / (n - split)[:, None, None]
        norm_squared = np.trapz((a - b)**2, x=trajectories.time, axis=1).sum(axis=1)
        return np.sqrt(np.maximum(0, norm_squared) * split * (n - split) / n)
    scores = stat(x)
    observed = float(scores.max())
    residuals = x - x.mean(axis=0, keepdims=True)
    random = np.random.default_rng(random_state)
    null = np.empty(n_bootstrap, float)
    for i in range(n_bootstrap):
        if dependence == "independent":
            sample = residuals[random.permutation(n)]
        else:
            starts = random.integers(0, n, size=int(np.ceil(n / block_length)))
            indices = np.concatenate([(s + np.arange(block_length)) % n for s in starts])[:n]
            sample = residuals[indices]
        null[i] = stat(sample).max()
    return FunctionalChangepointResult(
        split_index=int(split[scores.argmax()]), statistic=observed,
        scan=pd.DataFrame({"split_index": split, "cusum_norm": scores}),
        null_statistics=null,
        p_value_experimental=float((1 + (null >= observed).sum()) / (n_bootstrap + 1)),
        evidence={"experimental": True, "dependence": dependence,
                  "block_length": block_length, "seed": random_state,
                  "ordered_functional_mean_change_not_within_recording_events": True,
                  "calibration_not_qualified": True,
                  "not_Wegner_Wendler_estimator": True},
    )
