"""B7 experimental learned-population shared latent planar factor Gibbs model.

For channel d in {x,y}, Y_{idj} = B(t_{idj}) (mu_d + L_d z_i) + e_{idj}.
Participant scores z_i ~ N(0,I); mu_d and all L_d columns have independent
zero-mean Gaussian priors. Each channel has declared fixed Gaussian noise SD.
Mean, loading matrices, shared scores, and posterior *joint* planar covariance
are learned from native irregular timestamps, with channel-specific NaNs.

This is a finite-basis Gaussian functional FACTOR model, not a calibrated
Bayesian planar MFPCA eigensystem. Component sign/rotation are unidentified.
The covariance has CHANNEL-MAJOR ordering: (x-grid, y-grid).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np
import pandas as pd
from scipy.integrate import trapezoid

from eyetrajectoriespy.types import IrregularTrajectorySet
from ._score_marginal_loading import _elliptical_slice_score_marginal_loading
from .sparse_factor_gibbs import (_draw_gaussian_precision, _spline_basis,
                                  _metropolis_scale_interweave)


@dataclass(frozen=True)
class BayesianPlanarFactorFit:
    evaluation_grid: np.ndarray
    dimensions: tuple[str, str]
    population_mean_draws: np.ndarray
    joint_population_covariance_draws: np.ndarray
    loading_function_draws: np.ndarray
    shared_score_draws: np.ndarray
    reconstructed_latent_draws: np.ndarray
    evidence: Mapping[str, Any]

    @property
    def n_chains(self) -> int:
        return self.population_mean_draws.shape[0]

    @property
    def n_draws_per_chain(self) -> int:
        return self.population_mean_draws.shape[1]

    def posterior_population_frame(self) -> pd.DataFrame:
        """Rotation-invariant population mean, variance and xy covariance."""
        g = len(self.evaluation_grid)
        pop = self.population_mean_draws.reshape(-1, g, 2)
        cov = self.joint_population_covariance_draws.reshape(-1, 2*g, 2*g)
        xx = np.diagonal(cov[:, :g, :g], axis1=1, axis2=2)
        yy = np.diagonal(cov[:, g:, g:], axis1=1, axis2=2)
        xy = np.diagonal(cov[:, :g, g:], axis1=1, axis2=2)
        summary = {"time":self.evaluation_grid.copy()}
        for label, values in (
            ("x_mean",pop[:,:,0]), ("y_mean",pop[:,:,1]),
            ("x_variance",xx), ("y_variance",yy), ("xy_covariance",xy),
        ):
            summary[f"{label}_posterior_mean"] = values.mean(axis=0)
            summary[f"{label}_q05"] = np.quantile(values,.05,axis=0)
            summary[f"{label}_q95"] = np.quantile(values,.95,axis=0)
        summary["scientific_coverage_qualified"] = False
        return pd.DataFrame(summary)

    def diagnostics_frame(self) -> pd.DataFrame:
        """Optional ArviZ diagnostics of identifiable integrated quantities."""
        try:
            import arviz as az
        except ImportError as exc:
            raise ImportError("Install optional eyetrajectoriespy[bayesian]") from exc
        from .evidence import bayesian_diagnostics_frame
        g = len(self.evaluation_grid)
        t = self.evaluation_grid
        integrated_mean = trapezoid(self.population_mean_draws, x=t, axis=2)
        xy_cross = self.joint_population_covariance_draws[:, :, :g, g:]
        integrated_cross = trapezoid(
            np.diagonal(xy_cross, axis1=-2, axis2=-1), x=t, axis=-1)
        idata = az.from_dict(posterior={
            "integrated_x_mean": integrated_mean[:,: ,0],
            "integrated_y_mean": integrated_mean[:,: ,1],
            "integrated_xy_crosscovariance": integrated_cross,
        })
        return bayesian_diagnostics_frame(idata)



def _collapsed_planar_mean_precision_rhs(
    gram: np.ndarray, cross: np.ndarray, load: np.ndarray,
    observation_noise_sd: tuple[float,float] | np.ndarray,
    mean_prior_sd: float,
) -> tuple[np.ndarray,np.ndarray]:
    """Exact p(mu_x,mu_y | L_x,L_y,Y), integrating shared latent scores.

    Unlike independent channel updates, the marginalized shared scores
    induce nonzero cross-channel blocks. Uses Woodbury per participant
    and preserves x-grid/y-grid order and asynchronous original times.
    """
    _,n,q,_=gram.shape
    k=load.shape[-1]
    w=1./np.asarray(observation_noise_sd,dtype=float)**2
    precision=np.eye(2*q)/mean_prior_sd**2
    rhs=np.zeros(2*q)
    for i in range(n):
        score_precision=np.eye(k)
        H=np.empty((2*q,k))
        v=np.zeros(k)
        for d in range(2):
            g=gram[d,i]
            ld=load[d]
            score_precision += w[d]*ld.T@g@ld
            H[d*q:(d+1)*q,:]=w[d]*g@ld
            precision[d*q:(d+1)*q,d*q:(d+1)*q]+=w[d]*g
            rhs[d*q:(d+1)*q]+=w[d]*cross[d,i]
            v+=w[d]*ld.T@cross[d,i]
        precision -= H@np.linalg.solve(score_precision,H.T)
        rhs -= H@np.linalg.solve(score_precision,v)
    precision=(precision+precision.T)/2
    return precision,rhs



def fit_bayesian_planar_factor(
    trajectories: IrregularTrajectorySet,
    *,
    dimensions: tuple[str, str] = ("x","y"),
    evaluation_grid: np.ndarray,
    observation_noise_sd: tuple[float,float],
    n_components: int = 1,
    n_basis: int = 5,
    mean_prior_sd: float = 1.,
    loading_prior_sd: float = .3,
    scale_interweave_proposal_sd: float = 0.0,
    collapsed_population_mean_update: bool = False,
    score_marginal_loading_ess: bool = False,
    n_chains: int = 2,
    n_draws: int = 60,
    warmup: int = 90,
    thin: int = 2,
    random_state: int = 2026,
) -> BayesianPlanarFactorFit:
    """Fit learned x/y mean and cross-covariance from paired/asynchronous gaze.

    Independently identified participant curves are required. Each channel
    contributes observed rows at exactly its own recorded times; NaN denotes
    an unobserved channel (not zero). Any repetition of participant_id or
    missing/noisy clock alignment must be handled in a separate design.
    """
    if not isinstance(trajectories, IrregularTrajectorySet):
        raise TypeError("IrregularTrajectorySet required")
    if (len(dimensions) != 2 or len(set(dimensions)) != 2 or
        any(d not in trajectories.dimension_names for d in dimensions)):
        raise ValueError("two distinct present dimensions are required")
    for value, name, minimum in (
        (n_components,"n_components",1), (n_basis,"n_basis",4),
        (n_chains,"n_chains",2), (n_draws,"n_draws",20),
        (warmup,"warmup",20), (thin,"thin",1),
    ):
        if isinstance(value,bool) or not isinstance(value,int) or value < minimum:
            raise ValueError(f"{name} must be integer >= {minimum}")
    if n_basis > 12 or n_components > min(n_basis,trajectories.n_curves-1):
        raise ValueError("invalid finite dictionary/factor rank")
    if trajectories.n_curves < max(8, 2*n_components+2):
        raise ValueError("at least eight independent participants needed")
    if "participant_id" not in trajectories.metadata:
        raise ValueError("explicit participant_id metadata is required")
    ids = trajectories.metadata["participant_id"]
    if (ids.isna().any() or (ids.astype(str).str.strip()=="").any() or
        ids.astype(str).duplicated().any()):
        raise ValueError("participant_id must be complete and unique; repeated units unsupported")
    noise = np.asarray(observation_noise_sd,dtype=float)
    if noise.shape!=(2,) or not np.isfinite(noise).all() or (noise<=0).any():
        raise ValueError("observation_noise_sd must have two positive finite entries")
    for sd,name in ((mean_prior_sd,"mean_prior_sd"),
                    (loading_prior_sd,"loading_prior_sd")):
        if not np.isfinite(sd) or sd<=0:
            raise ValueError(f"{name} must be finite and positive")
    if (not np.isscalar(scale_interweave_proposal_sd)
        or isinstance(scale_interweave_proposal_sd,bool)
        or not np.isfinite(scale_interweave_proposal_sd)
        or not 0. <= scale_interweave_proposal_sd <= 1.):
        raise ValueError("scale_interweave_proposal_sd must be finite in [0,1]")
    if not isinstance(collapsed_population_mean_update,bool):
        raise ValueError("collapsed_population_mean_update must be bool")
    if not isinstance(score_marginal_loading_ess,bool):
        raise ValueError("score_marginal_loading_ess must be bool")
    grid = np.asarray(evaluation_grid,dtype=float)
    if (grid.ndim!=1 or len(grid)<max(5,n_basis) or
        not np.isfinite(grid).all() or not np.all(np.diff(grid)>0)):
        raise ValueError("evaluation_grid must be finite, increasing and sufficiently long")
    n=trajectories.n_curves
    q,k,g=n_basis,n_components,len(grid)
    cols = tuple(trajectories.dimension_names.index(d) for d in dimensions)
    gram = np.zeros((2,n,q,q))
    cross = np.zeros((2,n,q))
    counts = np.zeros((n,2),dtype=int)
    asynchronous=False
    for i,(times, values) in enumerate(zip(trajectories.time,trajectories.values,strict=True)):
        t=np.asarray(times,dtype=float)
        observation=np.asarray(values[:,cols],dtype=float)
        if np.isinf(observation).any():
            raise ValueError("Inf invalid; use NaN for unobserved channel")
        observed_times=[]
        for d in range(2):
            mask=np.isfinite(observation[:,d])
            count=int(mask.sum())
            if count<4:
                raise ValueError("at least four finite observations per curve and channel")
            td=t[mask]
            if td[0]<grid[0] or td[-1]>grid[-1]:
                raise ValueError("observed timestamps lie outside evaluation_grid")
            bd=_spline_basis(td,grid[0],grid[-1],q)
            gram[d,i]=bd.T@bd
            cross[d,i]=bd.T@observation[mask,d]
            counts[i,d]=count
            observed_times.append(tuple(td))
        asynchronous |= observed_times[0]!=observed_times[1]
    b_grid=_spline_basis(grid,grid[0],grid[-1],q)
    inv_var=1/noise**2
    sum_gram=gram.sum(axis=1)
    sum_cross=cross.sum(axis=1)
    mean_precision=np.asarray([
        inv_var[d]*sum_gram[d]+np.eye(q)/(mean_prior_sd**2)
        for d in range(2)])
    saved_mu=np.empty((n_chains,n_draws,g,2))
    saved_cov=np.empty((n_chains,n_draws,2*g,2*g))
    saved_load=np.empty((n_chains,n_draws,k,g,2))
    saved_z=np.empty((n_chains,n_draws,n,k))
    saved_latent=np.empty((n_chains,n_draws,n,g,2))
    total=warmup+thin*n_draws
    interweave_accepted=0
    interweave_attempted=0
    ess_likelihood_evaluations=0
    sequence=np.random.SeedSequence(random_state)
    for chain,chain_seed in enumerate(sequence.spawn(n_chains)):
        rng=np.random.default_rng(chain_seed)
        # Each channel first has a ridge-regularized population mean.
        mu=np.asarray([
            np.linalg.solve(mean_precision[d],inv_var[d]*sum_cross[d])
            for d in range(2)])
        load=rng.normal(scale=loading_prior_sd,size=(2,q,k))
        scores=rng.normal(size=(n,k))
        retained=0
        for sweep in range(total):
            for d in range(2):
                rhs=sum_cross[d].copy()
                for i in range(n):
                    rhs -= gram[d,i]@load[d]@scores[i]
                if not collapsed_population_mean_update:
                    mu[d]=_draw_gaussian_precision(
                        mean_precision[d],rhs*inv_var[d],rng)
                if not score_marginal_loading_ess:
                    precision=np.eye(q*k)/(loading_prior_sd**2)
                    targets=np.zeros((q,k))
                    for i in range(n):
                        precision += inv_var[d]*np.kron(
                            gram[d,i],np.outer(scores[i],scores[i]))
                        targets += np.outer(cross[d,i]-gram[d,i]@mu[d],scores[i])
                    load[d]=_draw_gaussian_precision(
                        precision,(targets*inv_var[d]).reshape(-1),rng
                    ).reshape(q,k)
            if score_marginal_loading_ess:
                # Exact joint loading block given mu and observed Y,
                # integrating shared z; subsequent score draw is conditional.
                load,ess_evals=_elliptical_slice_score_marginal_loading(
                    load,gram,cross,mu,noise,loading_prior_sd,rng)
                ess_likelihood_evaluations+=ess_evals

            if collapsed_population_mean_update:
                # Given newly updated channel loadings, draw the joint
                # x/y mean *after integrating shared z*, then sample
                # shared z conditional on the new mean and loadings.
                mean_p,mean_rhs=_collapsed_planar_mean_precision_rhs(
                    gram,cross,load,noise,mean_prior_sd)
                mu=_draw_gaussian_precision(mean_p,mean_rhs,rng).reshape(2,q)

            for i in range(n):
                precision=np.eye(k)
                targets=np.zeros(k)
                for d in range(2):
                    precision += inv_var[d]*load[d].T@gram[d,i]@load[d]
                    targets += inv_var[d]*load[d].T@(cross[d,i]-gram[d,i]@mu[d])
                scores[i]=_draw_gaussian_precision(precision,targets,rng)
            if scale_interweave_proposal_sd>0:
                interweave_accepted += _metropolis_scale_interweave(
                    load,scores,rng,scale_interweave_proposal_sd,
                    loading_prior_sd)
                interweave_attempted += k
            if sweep>=warmup and (sweep-warmup)%thin==0:
                if retained>=n_draws:
                    raise RuntimeError("invalid retention schedule")
                projected=np.stack((b_grid@load[0],b_grid@load[1]))
                # Channel-major (2*G,K), NOT a time-major flattened covariance.
                joint_load=projected.reshape(2*g,k)
                mean=np.stack((b_grid@mu[0],b_grid@mu[1]),axis=1)
                saved_mu[chain,retained]=mean
                saved_cov[chain,retained]=joint_load@joint_load.T
                saved_load[chain,retained]=np.transpose(projected,(2,1,0))
                saved_z[chain,retained]=scores
                saved_latent[chain,retained]=(
                    mean[None,:,:]+np.einsum("nk,kgd->ngd",
                                             scores,saved_load[chain,retained]))
                retained+=1
        if retained!=n_draws:
            raise RuntimeError("incomplete Gibbs sampling")
    for val in (grid,saved_mu,saved_cov,saved_load,saved_z,saved_latent):
        val.setflags(write=False)
    return BayesianPlanarFactorFit(
        evaluation_grid=grid,dimensions=dimensions,
        population_mean_draws=saved_mu,
        joint_population_covariance_draws=saved_cov,
        loading_function_draws=saved_load,
        shared_score_draws=saved_z,
        reconstructed_latent_draws=saved_latent,
        evidence={
            "experimental":True,
            "model":"learned_shared_Gaussian_planar_functional_factor_Gibbs",
            "population_mean_and_joint_covariance_learned":True,
            "latent_scores_shared_across_channels":True,
            "asynchronous_coordinate_observations":asynchronous,
            "native_observation_times_interpolated":False,
            "joint_covariance_flattening_order":"channel_major_xgrid_then_ygrid",
            "observation_noise_model":"fixed_diagonal_channel_specific",
            "n_components":k,"n_basis":q,"n_participants":n,
            "minimum_observations_per_coordinate":int(counts.min()),
            "rank_and_hyperparameter_learning":False,
            "eigenfunction_rotation_sign_identified":False,
            "hierarchical_participant_trial_modelled":False,
            "posterior_population_coverage_scientifically_qualified":False,
            "collapsed_population_mean_experimental_opt_in":collapsed_population_mean_update,
            "collapsed_population_mean_integrates_shared_scores":collapsed_population_mean_update,
            "collapsed_mean_inferential_qualification":False,
            "score_marginal_loading_ess_experimental_opt_in":score_marginal_loading_ess,
            "score_marginal_loading_ess_likelihood_evaluations":ess_likelihood_evaluations,
            "score_marginal_loading_ess_scientifically_qualified":False,
            "scale_interweave_experimental_opt_in":scale_interweave_proposal_sd>0,
            "scale_interweave_proposal_sd":float(scale_interweave_proposal_sd),
            "scale_interweave_accepted":interweave_accepted,
            "scale_interweave_attempted":interweave_attempted,
            "scale_interweave_acceptance_rate":(
                interweave_accepted/interweave_attempted
                if interweave_attempted else None),
            "scale_interweave_inferential_qualification":False,
            "posterior_mixing_scientifically_qualified":False,
            "learned_orthonormal_eigenfunction_posterior":False,
            "native_full_Bayesian_planar_MFPCA_scientifically_qualified":False,
            "release_authorized":False,
            "seed":random_state,"n_chains":n_chains,"draws_per_chain":n_draws,
        },
    )
