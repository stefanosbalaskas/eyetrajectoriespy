"""F1 experimental sparse-planar two-sample analysis.

This is a newly implemented conditional permutation test of pooled MFPCA PACE
scores, NOT a reproduction or validated implementation of Koner & Luo (2024).
Exchangeable independent units and common nuisance/data-generating structure
are assumed. No population inference should be claimed before size/power study.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping, Sequence
import numpy as np
import pandas as pd
from eyetrajectoriespy.types import IrregularTrajectorySet
from eyetrajectoriespy.sparse_multivariate import fit_sparse_mfpca


@dataclass(frozen=True)
class SparseFunctionalGroupTest:
    fit: Any
    groups: tuple[str, str]
    group_sizes: tuple[int, int]
    score_mean_difference: np.ndarray
    mean_difference: np.ndarray
    statistic: float
    permutation_statistics: np.ndarray
    p_value: float
    n_independent_units: int
    evidence: Mapping[str, Any]



def _conditional_score_permutation(
    by_unit: np.ndarray,
    first_group: np.ndarray,
    *,
    n_permutations: int,
    random_state: int,
) -> tuple[float, np.ndarray, float]:
    """Conditional Monte Carlo randomization of independent-unit score vectors.

    Only valid if the unit-group allocations were exchangeable under the
    sharp null. This does not establish validity of learned sparse scores.
    """
    scores = np.asarray(by_unit, dtype=float)
    mask = np.asarray(first_group, dtype=bool)
    if scores.ndim != 2 or mask.shape != (len(scores),) or not np.isfinite(scores).all():
        raise ValueError("finite two-dimensional independent-unit scores required")
    if min(int(mask.sum()), int((~mask).sum())) < 4:
        raise ValueError("at least four independent units per group required")
    if not isinstance(n_permutations, int) or n_permutations < 99:
        raise ValueError("at least 99 permutations required")
    pooled = np.atleast_2d(np.cov(scores, rowvar=False))
    inv = np.linalg.pinv(pooled, rcond=1e-10)

    def statistic(m: np.ndarray) -> float:
        difference = scores[m].mean(axis=0) - scores[~m].mean(axis=0)
        return float(difference @ inv @ difference)

    observed = statistic(mask)
    rng = np.random.default_rng(random_state)
    null = np.empty(n_permutations, dtype=float)
    for iteration in range(n_permutations):
        selected = rng.permutation(len(scores))[:int(mask.sum())]
        draw = np.zeros(len(scores), dtype=bool)
        draw[selected] = True
        null[iteration] = statistic(draw)
    p_value = float((1 + np.count_nonzero(null >= observed - 1e-12)) / (1 + len(null)))
    return observed, null, p_value


def test_sparse_functional_groups(
    trajectories: IrregularTrajectorySet,
    groups: Sequence[str],
    *,
    fit_kwargs: Mapping[str, Any],
    unit_ids: Sequence[str] | None = None,
    n_permutations: int = 999,
    random_state: int = 0,
) -> SparseFunctionalGroupTest:
    """Compare paired sparse planar curves through joint PACE score permutation.

    Groups are permuted at the independent-unit level; repeated curves from
    one participant must provide unit_ids, all assigned to a single group.
    The pooled FPCA fit is estimated without group labels, which allows
    conditional re-labelling under a strict exchangeable-unit null. This does
    NOT implement nuisance-adjusted Koner--Luo covariance-based inference.
    """
    if not isinstance(trajectories, IrregularTrajectorySet):
        raise TypeError("F1 needs genuinely irregular trajectories")
    n = trajectories.n_curves
    labels = np.asarray(groups, dtype=str)
    if labels.ndim != 1 or labels.size != n:
        raise ValueError("groups must contain one label for each curve")
    names = tuple(sorted(set(labels)))
    if len(names) != 2 or any(not name.strip() for name in names):
        raise ValueError("exactly two nonempty groups required")
    if isinstance(n_permutations, bool) or int(n_permutations) < 99:
        raise ValueError("at least 99 permutations required")
    if unit_ids is None:
        if "participant_id" in trajectories.metadata.columns:
            observed = trajectories.metadata["participant_id"].astype(str).to_numpy()
            if len(set(observed)) != n:
                raise ValueError("repeated participants require explicit unit_ids")
        ids = np.asarray(trajectories.curve_ids, dtype=str)
    else:
        ids = np.asarray(unit_ids, dtype=str)
        if ids.ndim != 1 or ids.size != n or any(not x.strip() for x in ids):
            raise ValueError("unit_ids must identify every independent unit")
    if "participant_id" in trajectories.metadata.columns:
        participant_ids = trajectories.metadata["participant_id"].astype(str).to_numpy()
        for participant in set(participant_ids):
            assigned_units = set(ids[participant_ids == participant])
            if len(assigned_units) != 1:
                raise ValueError(
                    "all repeated curves from each participant must share one independent unit_id"
                )
    if any(not unit.strip() for unit in ids):
        raise ValueError("independent unit identifiers cannot be blank")
    unit_names = list(dict.fromkeys(ids))
    unit_scores_index = [np.flatnonzero(ids == name) for name in unit_names]
    unit_groups = []
    for indices in unit_scores_index:
        found = set(labels[indices])
        if len(found) != 1:
            raise ValueError("one independent unit cannot cross groups in this between-unit test")
        unit_groups.append(next(iter(found)))
    unit_groups = np.asarray(unit_groups)
    if min(int((unit_groups == g).sum()) for g in names) < 4:
        raise ValueError("at least four independent units in each group")
    if "dimensions" in fit_kwargs and len(fit_kwargs["dimensions"]) != 2:
        raise ValueError("joint two-dimensional fit required")
    fit = fit_sparse_mfpca(trajectories, **dict(fit_kwargs))
    scores = np.asarray(fit.scores, dtype=float)
    if scores.ndim != 2 or scores.shape[0] != n or not np.isfinite(scores).all():
        raise ValueError("unusable or nonfinite PACE scores; do not silently discard failed fits")
    by_unit = np.asarray([scores[indices].mean(axis=0) for indices in unit_scores_index])
    group_mask = unit_groups == names[0]
    group_counts = (int(group_mask.sum()), int((~group_mask).sum()))
    delta = by_unit[group_mask].mean(axis=0) - by_unit[~group_mask].mean(axis=0)
    observed, null, p = _conditional_score_permutation(
        by_unit, group_mask,
        n_permutations=int(n_permutations), random_state=random_state,
    )
    eig = np.asarray(fit.eigenfunctions, dtype=float)
    if eig.ndim != 3 or eig.shape[0] != delta.size:
        raise RuntimeError("unexpected component representation; fail closed")
    contrast = np.tensordot(delta, eig, axes=(0, 0))
    return SparseFunctionalGroupTest(
        fit=fit, groups=names, group_sizes=group_counts,
        score_mean_difference=delta, mean_difference=contrast,
        statistic=observed, permutation_statistics=null,
        p_value=p, n_independent_units=len(unit_names),
        evidence={"experimental": True,
                  "method": "pooled_PACE_conditional_unit_permutation",
                  "not_Koner_Luo_2024_replication": True,
                  "exchangeability_assumption": "independent_units_same_null_distribution",
                  "serial_dependency_modelled": False,
                  "heteroscedastic_validity_qualified": False,
                  "n_permutations": len(null), "seed": random_state,
                  "group_effect_is_observational_not_causal": True},
    )


def functional_group_contrast_frame(result: SparseFunctionalGroupTest) -> pd.DataFrame:
    """Coordinate contrast reconstructed from pooled joint score mean difference."""
    values = np.asarray(result.mean_difference)
    return pd.DataFrame({
        "time": np.repeat(np.asarray(result.fit.evaluation_grid), values.shape[1]),
        "dimension": np.tile(list(result.fit.dimensions), values.shape[0]),
        "mean_score_reconstruction_contrast": values.reshape(-1),
        "group_a": result.groups[0],
        "group_b": result.groups[1],
    })


def plot_functional_group_contrast(result: SparseFunctionalGroupTest, ax=None):
    """Descriptive contrast plot without unqualified confidence bands."""
    import matplotlib.pyplot as plt
    if ax is None:
        _, ax = plt.subplots()
    for j, name in enumerate(result.fit.dimensions):
        ax.plot(result.fit.evaluation_grid, result.mean_difference[:, j], label=name)
    ax.axhline(0, color="0.5", linestyle="--")
    ax.set(xlabel="Time", ylabel="Pooled score-reconstruction group contrast",
           title="Experimental sparse group comparison (descriptive)")
    ax.legend()
    return ax
