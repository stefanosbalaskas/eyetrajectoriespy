"""B8 experimental conjugate participant-intercept Bayesian functional mixed model.

Model: Y_ij(t)=X_ij beta(t)+u_i(t)+epsilon_ij(t).
All fixed coefficient, participant random functional effects and residuals are
Gaussian. Hyperparameters for observation noise and functional random-effects
prior are explicitly FIXED, not learned. Within-curve residual errors are
independent; no cross-channel covariance, random slopes, or nested trial effects.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd
from scipy.linalg import cho_factor, cho_solve
from eyetrajectoriespy.types import TrajectorySet
from .evidence import BayesianFunctionalDraws
from .function_on_scalar import _bspline_basis


@dataclass(frozen=True)
class BayesianFunctionalMixedEffectsFit:
    fixed_predictor_names: tuple[str, ...]
    participant_ids: tuple[str, ...]
    time: np.ndarray
    dimension_names: tuple[str, ...]
    fixed_effect_draws: np.ndarray
    participant_random_intercept_draws: np.ndarray
    posterior_mean_fixed_effects: np.ndarray
    fitted_mean: np.ndarray
    noise_sd: float
    fixed_prior_sd: float
    participant_prior_sd: float
    evidence: Mapping[str, Any]

    def fixed_effect_posterior(self, predictor: str) -> BayesianFunctionalDraws:
        if predictor not in self.fixed_predictor_names:
            raise KeyError(predictor)
        j=self.fixed_predictor_names.index(predictor)
        return BayesianFunctionalDraws(
            values=self.fixed_effect_draws[:,j][None,:,:,:],
            time=self.time, dimension_names=self.dimension_names,
            provenance=dict(self.evidence, predictor=predictor),
        )

    def participant_posterior(self, participant_id: str) -> BayesianFunctionalDraws:
        if participant_id not in self.participant_ids:
            raise KeyError(participant_id)
        i=self.participant_ids.index(participant_id)
        return BayesianFunctionalDraws(
            values=self.participant_random_intercept_draws[:,i][None,:,:,:],
            time=self.time, dimension_names=self.dimension_names,
            provenance=dict(self.evidence, participant_id=participant_id),
        )


def fit_bayesian_functional_mixed_effects(
    trajectories: TrajectorySet, *,
    design: pd.DataFrame,
    predictors: Sequence[str],
    participant_column: str = "participant_id",
    noise_sd: float,
    fixed_prior_sd: float = 1.0,
    participant_prior_sd: float = .35,
    n_basis: int = 5,
    n_draws: int = 200,
    random_state: int = 0,
) -> BayesianFunctionalMixedEffectsFit:
    """Conjugate functional random-intercept model, conditional on fixed SDs.

    Every participant must appear on >=2 observed trials. The deterministic
    spline grid is common to all curves; participant-specific functional
    intercepts are partially pooled through a zero-mean Normal prior.
    """
    if not isinstance(trajectories, TrajectorySet):
        raise TypeError("common-grid TrajectorySet required")
    if not isinstance(design, pd.DataFrame) or "curve_id" not in design:
        raise ValueError("design requires curve_id and fixed predictors")
    if design.curve_id.astype(str).tolist() != list(trajectories.curve_ids):
        raise ValueError("design curve_id must match exact curve order")
    predictors=tuple(predictors)
    if not predictors or len(predictors)!=len(set(predictors)) or any(
        not isinstance(p,str) or not p or p not in design for p in predictors
    ):
        raise ValueError("unique valid predictor columns required")
    if len(predictors)>8:
        raise ValueError("at most eight fixed predictors in research model")
    md=trajectories.metadata.reset_index(drop=True)
    if participant_column not in md or md[participant_column].isna().any():
        raise ValueError("metadata must supply nonmissing participant IDs")
    ids=md[participant_column].astype(str).tolist()
    if not all(i.strip() for i in ids):
        raise ValueError("participant identifiers cannot be empty")
    people=tuple(dict.fromkeys(ids))
    if len(people)<4:
        raise ValueError("at least four independent participants required")
    counts=pd.Series(ids).value_counts()
    if (counts<2).any():
        raise ValueError(">=2 repeated trials per participant required")
    x=design.loc[:,predictors].to_numpy(dtype=float)
    if not np.isfinite(x).all() or np.linalg.matrix_rank(x)!=len(predictors):
        raise ValueError("finite full-rank fixed-effect design required")
    y=np.asarray(trajectories.values,dtype=float)
    if not np.isfinite(y).all():
        raise ValueError("finite observed trajectories required, no silent imputation")
    if isinstance(n_basis,bool) or not isinstance(n_basis,int) or n_basis<4 or n_basis>len(trajectories.time):
        raise ValueError("n_basis must lie between 4 and number of time samples")
    if isinstance(n_draws,bool) or not isinstance(n_draws,int) or n_draws<20:
        raise ValueError("n_draws must be >=20")
    for value,name in ((noise_sd,"noise_sd"),(fixed_prior_sd,"fixed_prior_sd"),
                       (participant_prior_sd,"participant_prior_sd")):
        if not np.isfinite(value) or value<=0:
            raise ValueError(f"{name} must be a positive finite declared SD")
    basis=_bspline_basis(trajectories.time,n_basis)
    n=y.shape[0]
    t=y.shape[1]
    p=len(predictors)
    u=len(people)
    z=np.zeros((n,u),dtype=float)
    index={name:i for i,name in enumerate(people)}
    z[np.arange(n),[index[name] for name in ids]]=1.0
    fixed_design=np.einsum("ip,tq->itpq",x,basis).reshape(n*t,p*n_basis)
    random_design=np.einsum("iu,tq->ituq",z,basis).reshape(n*t,u*n_basis)
    joint=np.column_stack((fixed_design,random_design))
    var=np.r_[
        np.full(p*n_basis,float(fixed_prior_sd)**2),
        np.full(u*n_basis,float(participant_prior_sd)**2),
    ]
    precision=(joint.T@joint)/(noise_sd**2)+np.diag(1.0/var)
    factor=cho_factor(precision,lower=True,check_finite=True)
    covariance=cho_solve(factor,np.eye(len(var)))
    means=cho_solve(factor,joint.T@y.reshape(n*t,-1)/(noise_sd**2))
    rng=np.random.default_rng(random_state)
    all_draws=np.stack([
        rng.multivariate_normal(means[:,j],covariance,size=n_draws)
        for j in range(trajectories.n_dimensions)
    ],axis=-1)
    fixed=all_draws[:,:p*n_basis].reshape(n_draws,p,n_basis,-1)
    subject=all_draws[:,p*n_basis:].reshape(n_draws,u,n_basis,-1)
    fixed_curves=np.einsum("spqd,tq->sptd",fixed,basis)
    subject_curves=np.einsum("suqd,tq->sutd",subject,basis)
    beta_hat=np.einsum("pqd,tq->ptd",means[:p*n_basis].reshape(p,n_basis,-1),basis)
    fitted=(joint@means).reshape(y.shape)
    return BayesianFunctionalMixedEffectsFit(
        fixed_predictor_names=predictors,participant_ids=people,
        time=trajectories.time.copy(),dimension_names=trajectories.dimension_names,
        fixed_effect_draws=fixed_curves,
        participant_random_intercept_draws=subject_curves,
        posterior_mean_fixed_effects=beta_hat,fitted_mean=fitted,
        noise_sd=float(noise_sd),fixed_prior_sd=float(fixed_prior_sd),
        participant_prior_sd=float(participant_prior_sd),
        evidence={
            "experimental":True,
            "model":"conjugate_participant_random_functional_intercept_Bspline",
            "participant_random_intercepts_modelled":True,
            "random_slopes_or_trial_random_effects_modelled":False,
            "conditional_on_declared_fixed_prior_and_noise_sds":True,
            "population_variance_hyperparameters_estimated":False,
            "within_curve_serial_noise_modelled":False,
            "cross_channel_residual_covariance_modelled":False,
            "posterior_parameter_uncertainty_included":True,
            "posterior_coverage_scientifically_calibrated":False,
            "n_independent_participants":u,
            "n_repeated_curves":n,
            "n_draws":n_draws,"seed":random_state,
        },
    )
