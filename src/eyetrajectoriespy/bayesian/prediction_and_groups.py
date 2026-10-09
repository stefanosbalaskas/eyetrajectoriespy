"""B9 conditional functional probabilities and partial-trajectory completion.

These are deliberately narrowly scoped research adapters. They do NOT
establish a Bayesian clinical/behavioral hypothesis test or full Bayesian
partial-trajectory prediction with re-estimated population parameters.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping
import numpy as np
from eyetrajectoriespy.types import IrregularTrajectorySet
from .evidence import BayesianFunctionalDraws, BayesianCredibleBand, bayesian_credible_band
from .sparse_score_baseline import fit_bayesian_sparse_score_baseline


@dataclass(frozen=True)
class BayesianFunctionalGroupComparison:
    posterior_difference: BayesianFunctionalDraws
    credible_band: BayesianCredibleBand
    probability_above_margin_everywhere: float
    margin: float
    evidence: Mapping[str, Any]


def compare_bayesian_functional_groups(
    group_a: BayesianFunctionalDraws,
    group_b: BayesianFunctionalDraws, *,
    joint_posterior_draw_pairing_verified: bool,
    margin: float = 0.0,
    coverage: float = .95,
    simultaneous: bool = True,
) -> BayesianFunctionalGroupComparison:
    """Difference of correctly paired *joint-model* group posterior draws.

    Prohibits accidental subtraction of separately fitted posteriors with
    unmatched draws. For independent fits, explicitly construct valid joint
    draws as a separate, audited step before calling this function.
    """
    if not isinstance(group_a, BayesianFunctionalDraws) or not isinstance(group_b, BayesianFunctionalDraws):
        raise TypeError("group curves must be BayesianFunctionalDraws")
    if joint_posterior_draw_pairing_verified is not True:
        raise ValueError("joint_posterior_draw_pairing_verified=True is required")
    if group_a.values.shape != group_b.values.shape or group_a.dimension_names != group_b.dimension_names or not np.array_equal(group_a.time,group_b.time):
        raise ValueError("joint posterior groups must match in chains, draws, time, and dimensions")
    if not np.isfinite(margin):
        raise ValueError("declared meaningful margin must be finite")
    difference=BayesianFunctionalDraws(
        group_a.values-group_b.values,
        time=group_a.time,dimension_names=group_a.dimension_names,
        provenance={
            "joint_draws_explicitly_certified_by_analyst":True,
            "group_difference_not_independent_fit_pairing":True,
            "experimental":True,
        },
    )
    band=bayesian_credible_band(
        difference,coverage=coverage,simultaneous=simultaneous,
    )
    probability=float(np.mean((difference.values>margin).all(axis=(2,3))))
    return BayesianFunctionalGroupComparison(
        posterior_difference=difference,credible_band=band,
        probability_above_margin_everywhere=probability,margin=float(margin),
        evidence={
            "experimental":True,
            "posterior_probability_is_not_a_p_value":True,
            "joint_model_provenance_independently_verified":False,
            "gridwise_condition_not_continuum":True,
            "posterior_calibration_qualified":False,
        },
    )


@dataclass(frozen=True)
class BayesianPartialTrajectoryPrediction:
    posterior_latent_draws: np.ndarray
    evaluation_grid: np.ndarray
    future_mask: np.ndarray
    n_used_observations_per_curve: tuple[int, ...]
    evidence: Mapping[str, Any]


def predict_bayesian_trajectory(
    trajectories: IrregularTrajectorySet, *,
    dimension: str,
    observation_cutoff: float,
    evaluation_grid: np.ndarray,
    population_mean: np.ndarray,
    population_components: np.ndarray,
    score_prior_variances: np.ndarray,
    noise_sd: float,
    n_draws: int = 200,
    random_state: int = 0,
) -> BayesianPartialTrajectoryPrediction:
    """Known-basis partial completion using observations at/before cutoff ONLY.

    This calls the *fixed-population B6 score benchmark*, never refits a
    population eigensystem. Heldout later gaze samples cannot inform its
    posterior, even if supplied in the original trajectory.
    """
    if not isinstance(trajectories, IrregularTrajectorySet):
        raise TypeError("native irregular trajectories required")
    grid=np.asarray(evaluation_grid,dtype=float)
    if grid.ndim != 1 or not np.isfinite(grid).all() or len(grid) < 3 or not grid[0] < observation_cutoff < grid[-1]:
        raise ValueError("cutoff must be strictly inside finite evaluation grid")
    times, values, counts=[],[],[]
    if dimension not in trajectories.dimension_names:
        raise ValueError("specified dimension absent")
    dim=trajectories.dimension_names.index(dimension)
    for t,v in zip(trajectories.time,trajectories.values,strict=True):
        retained=(np.asarray(t)<=observation_cutoff)
        valid=retained & np.isfinite(v[:,dim])
        if valid.sum()<2:
            raise ValueError("at least two valid observed samples at or before cutoff required")
        times.append(np.asarray(t)[valid])
        values.append(np.asarray(v)[valid])
        counts.append(int(valid.sum()))
    partial=IrregularTrajectorySet(
        time=tuple(times),values=tuple(values),
        curve_ids=trajectories.curve_ids,
        dimension_names=trajectories.dimension_names,
        metadata=trajectories.metadata,
        coordinate_system=trajectories.coordinate_system,
        time_unit=trajectories.time_unit,
        provenance={"input_truncated_to_cutoff":float(observation_cutoff)},
    )
    result=fit_bayesian_sparse_score_baseline(
        partial,dimension=dimension,evaluation_grid=grid,
        population_mean=population_mean,population_components=population_components,
        score_prior_variances=score_prior_variances,noise_sd=noise_sd,
        n_draws=n_draws,random_state=random_state,
    )
    return BayesianPartialTrajectoryPrediction(
        posterior_latent_draws=result.conditional_latent_trajectory_draws,
        evaluation_grid=grid.copy(),future_mask=grid>observation_cutoff,
        n_used_observations_per_curve=tuple(counts),
        evidence={
            "experimental":True,"known_population_basis":True,
            "population_parameter_uncertainty_included":False,
            "future_observations_leakage_guard":True,
            "cutoff":float(observation_cutoff),
            "predictive_coverage_qualified":False,
            "not_full_Bayesian_FPCA_forecasting":True,
        },
    )
