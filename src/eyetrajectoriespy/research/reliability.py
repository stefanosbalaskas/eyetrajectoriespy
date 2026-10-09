"""Experimental balanced repeated-trial functional variance decomposition.

Moment estimators assume independent participants, common registered time grid,
exchangeable trials within participant, no session/condition confounding.
They are not generic functional ICCs or evidence of measurement validity.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping, Any
import numpy as np
import pandas as pd
from eyetrajectoriespy.types import TrajectorySet
from eyetrajectoriespy.fpca import functional_trapezoid_weights

@dataclass(frozen=True)
class FunctionalReliabilityResult:
    time: np.ndarray
    dimension_names: tuple[str, ...]
    pointwise_single_trial_reliability: np.ndarray
    pointwise_mean_trial_reliability: np.ndarray
    integrated_single_trial_reliability: np.ndarray
    integrated_mean_trial_reliability: np.ndarray
    between_variance: np.ndarray
    within_variance: np.ndarray
    n_participants: int
    trials_per_participant: int
    evidence: Mapping[str, Any]


def fit_functional_reliability(
    trajectories: TrajectorySet,
    *,
    participant_column: str = "participant_id",
    condition_column: str | None = None,
) -> FunctionalReliabilityResult:
    """Moment-based balanced random-intercept reliability for registered curves.

    At each time/dimension: sigma_b^2=max(0,(MSB-MSW)/m);
    sigma_w^2=MSW. Reliability of the mean of m trials:
    sigma_b^2/(sigma_b^2+sigma_w^2/m). The truncation is disclosed.
    """
    if not isinstance(trajectories, TrajectorySet):
        raise TypeError("common-grid TrajectorySet required")
    if not np.isfinite(trajectories.values).all():
        raise ValueError("finite registered trajectories required; no hidden imputation")
    meta = trajectories.metadata.reset_index(drop=True)
    if participant_column not in meta or meta[participant_column].isna().any():
        raise ValueError("participant metadata must identify each independent participant")
    if condition_column is not None:
        if condition_column not in meta:
            raise ValueError("condition column not found")
        if meta[condition_column].nunique(dropna=False) != 1:
            raise ValueError("multi-condition trials require separate condition-stratified reliability")
    ids = meta[participant_column].astype(str).to_numpy()
    names = list(dict.fromkeys(ids))
    if len(names) < 3:
        raise ValueError("at least three independent participants required")
    sets = [np.flatnonzero(ids == name) for name in names]
    counts = [len(i) for i in sets]
    if min(counts) < 2 or len(set(counts)) != 1:
        raise ValueError("balanced design with >=2 trials per participant required")
    m = counts[0]
    arr = np.stack([trajectories.values[i] for i in sets])
    centers = arr.mean(axis=1)
    grand = centers.mean(axis=0)
    ms_between = m * np.sum((centers - grand)**2, axis=0) / (len(names) - 1)
    ms_within = np.sum((arr - centers[:, None])**2, axis=(0, 1)) / (
        len(names) * (m - 1)
    )
    between_untruncated = (ms_between - ms_within) / m
    between = np.maximum(0.0, between_untruncated)
    within = np.maximum(0.0, ms_within)
    def ratio(b: np.ndarray, w: np.ndarray, factor: float) -> np.ndarray:
        den = b + w/factor
        return np.divide(
            b, den, out=np.full_like(b, np.nan), where=den > 1e-14
        )
    single = ratio(between, within, 1)
    average = ratio(between, within, m)
    wq = functional_trapezoid_weights(trajectories.time)
    ib = np.einsum("t,td->d", wq, between)
    iw = np.einsum("t,td->d", wq, within)
    result = FunctionalReliabilityResult(
        time=trajectories.time.copy(),
        dimension_names=trajectories.dimension_names,
        pointwise_single_trial_reliability=single,
        pointwise_mean_trial_reliability=average,
        integrated_single_trial_reliability=ratio(ib, iw, 1),
        integrated_mean_trial_reliability=ratio(ib, iw, m),
        between_variance=between, within_variance=within,
        n_participants=len(names), trials_per_participant=m,
        evidence={
            "experimental": True,
            "method": "balanced_random_intercept_moment_variance_components",
            "negative_between_component_truncated_to_zero": bool(
                (between_untruncated < 0).any()
            ),
            "zero_total_variance_returns_nan": True,
            "trial_exchangeability_assumed": True,
            "conditions_and_sessions_not_jointly_modelled": True,
            "registration_assumed": True,
            "bootstrap_inference_qualified": False,
        },
    )
    return result


def functional_reliability_frame(result: FunctionalReliabilityResult) -> pd.DataFrame:
    """Tidy pointwise reliability with a separate integrated summary."""
    rows = []
    for j, dimension in enumerate(result.dimension_names):
        for t, single, mean in zip(
            result.time,
            result.pointwise_single_trial_reliability[:, j],
            result.pointwise_mean_trial_reliability[:, j],
        ):
            rows.append({"time": float(t), "dimension": dimension,
                "single_trial_ratio": float(single),
                "mean_trial_ratio": float(mean)})
    return pd.DataFrame(rows)
