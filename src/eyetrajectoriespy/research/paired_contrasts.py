"""Exploratory participant-paired whole-functional contrast.

All inference uses participant-level sign flips, not independent-curve labels.
A symmetric null distribution of subject differences is required. This code
does not estimate carryover/order/time drift, cluster dependence or causality.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping, Any, Sequence
import numpy as np
import pandas as pd
from eyetrajectoriespy.types import TrajectorySet
from eyetrajectoriespy.fpca import functional_trapezoid_weights

@dataclass(frozen=True)
class PairedFunctionalContrast:
    groups: tuple[str, str]
    time: np.ndarray
    dimensions: tuple[str, ...]
    mean_paired_difference: np.ndarray
    statistic: float
    null_statistics: np.ndarray
    p_value_experimental: float
    n_participants: int
    evidence: Mapping[str, Any]


def compare_repeated_functional_groups(
    trajectories: TrajectorySet,
    *,
    participants: Sequence[str],
    conditions: Sequence[str],
    sign_symmetry_assumed: bool,
    n_permutations: int = 999,
    random_state: int = 0,
    order_or_period: Sequence[str] | None = None,
) -> PairedFunctionalContrast:
    """Two-condition paired whole-curve random sign-flip test.

    Replicates are averaged within each participant-condition. Equal replicates
    per participant-condition are required; no missing observations permitted.
    If order/period effects exist, use an explicit crossover model instead.
    """
    if not isinstance(trajectories, TrajectorySet):
        raise TypeError("paired contrast requires common-grid TrajectorySet")
    x = np.asarray(trajectories.values, dtype=float)
    if not np.isfinite(x).all():
        raise ValueError("paired contrasts cannot silently impute missing samples")
    if sign_symmetry_assumed is not True:
        raise ValueError("explicit sign_symmetry_assumed=True required for experimental inference")
    if order_or_period is not None:
        raise ValueError("period/order effects are not modelled; fit a crossover model")
    if isinstance(n_permutations, bool) or not isinstance(n_permutations, int) or n_permutations < 99:
        raise ValueError("n_permutations must be an integer >=99")
    p = np.asarray(participants, dtype=str)
    c = np.asarray(conditions, dtype=str)
    if p.shape != (len(x),) or c.shape != (len(x),):
        raise ValueError("participant and condition vectors must match n_curves")
    if not all(name.strip() for name in p) or not all(name.strip() for name in c):
        raise ValueError("empty participant or condition names")
    groups = tuple(sorted(set(c)))
    if len(groups) != 2:
        raise ValueError("exactly two conditions required")
    subjects = list(dict.fromkeys(p))
    if len(subjects) < 8:
        raise ValueError("at least eight independent participants required")
    diffs = []
    replicate_counts = []
    for pid in subjects:
        means = []
        counts = []
        for cond in groups:
            section = x[(p == pid) & (c == cond)]
            if len(section) == 0:
                raise ValueError("each participant must have observations in both conditions")
            means.append(section.mean(axis=0))
            counts.append(len(section))
        if counts[0] != counts[1]:
            raise ValueError("unequal condition replicate counts per participant")
        replicate_counts.extend(counts)
        diffs.append(means[0] - means[1])
    differences = np.stack(diffs, axis=0)
    weights = functional_trapezoid_weights(trajectories.time)
    def statistic(d):
        delta = d.mean(axis=0)
        return float(np.sqrt(np.sum(delta**2 * weights[:, None])))
    observed = statistic(differences)
    rng = np.random.default_rng(random_state)
    null = np.empty(n_permutations)
    for i in range(n_permutations):
        signs = rng.choice((-1.0, 1.0), size=len(subjects))
        null[i] = statistic(differences * signs[:, None, None])
    pvalue = float((1 + np.count_nonzero(null >= observed - 1e-12)) / (n_permutations + 1))
    return PairedFunctionalContrast(
        groups=groups, time=trajectories.time.copy(),
        dimensions=trajectories.dimension_names,
        mean_paired_difference=differences.mean(axis=0),
        statistic=observed, null_statistics=null,
        p_value_experimental=pvalue, n_participants=len(subjects),
        evidence={
            "experimental": True,
            "method": "balanced_participant_mean_difference_sign_flip_L2",
            "symmetric_subject_difference_null_required": True,
            "no_order_carryover_or_period_adjustment": True,
            "within_participant_trials_aggregated": True,
            "balanced_replicates_per_condition_participant": True,
            "replicate_counts": tuple(replicate_counts),
            "not_qualified_population_inference": True,
            "n_permutations": n_permutations,
            "seed": random_state,
        }
    )


def repeated_functional_contrast_frame(result: PairedFunctionalContrast) -> pd.DataFrame:
    return pd.DataFrame({
        "time": np.repeat(result.time, len(result.dimensions)),
        "dimension": np.tile(list(result.dimensions), len(result.time)),
        "mean_paired_difference": result.mean_paired_difference.reshape(-1),
        "condition_a": result.groups[0], "condition_b": result.groups[1],
    })
