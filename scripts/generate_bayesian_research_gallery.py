"""Create five fitted/simulated Bayesian research SVGs from actual B5/B6/B8 objects.

All generated data are synthetic. This gallery never claims population
posterior calibration of native sparse Bayesian FPCA or hierarchical models.
"""
from __future__ import annotations
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from eyetrajectoriespy.types import TrajectorySet, IrregularTrajectorySet
from eyetrajectoriespy.bayesian import (
    bayesian_credible_band, bayesian_calibration_study,
    bayesian_posterior_predictive_check,
    fit_bayesian_function_on_scalar, fit_bayesian_sparse_score_baseline,
)
from eyetrajectoriespy.bayesian.function_on_scalar import _bspline_basis

OUTPUT = Path("docs/assets/research")
FILES = (
    "b5-credible-bands.svg",
    "b8-prior-versus-posterior.svg",
    "b6-fixed-population-sparse-scores.svg",
    "b5-posterior-predictive-check.svg",
    "b5-exact-normal-sbc-ranks.svg",
)


def _save(fig, name: str) -> None:
    fig.suptitle("Known-truth synthetic illustration — no scientific qualification", fontsize=9, y=1.04)
    fig.tight_layout()
    fig.savefig(OUTPUT/name, format="svg",
                bbox_inches="tight", metadata={"Date": None, "Creator": "eyetrajectoriespy B5 Bayesian research"})
    plt.close(fig)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    plt.rcParams["svg.hashsalt"] = "bayesian-research-v1"
    plt.rcParams["font.family"] = "DejaVu Sans"
    rng = np.random.default_rng(24061)
    t = np.linspace(0, 1, 31)
    n = 34
    cond = np.r_[np.zeros(n//2), np.ones(n//2)]
    beta_truth = .28*np.sin(np.pi*t)
    y = .4 + cond[:,None]*beta_truth[None,:] + rng.normal(0,.04,(n,len(t)))
    trajectories = TrajectorySet(
        time=t, values=y[:,:,None],
        curve_ids=tuple(f"syn-{i}" for i in range(n)),
        dimension_names=("x",),
        metadata=pd.DataFrame({"participant_id":[f"P{i}" for i in range(n)]}),
        time_unit="normalized", coordinate_system="normalized",
        provenance={"synthetic_truth":True},
    )
    design=pd.DataFrame({"curve_id":trajectories.curve_ids,
                         "intercept":np.ones(n),"condition":cond})
    fit = fit_bayesian_function_on_scalar(
        trajectories, design=design,
        predictors=("intercept","condition"),
        noise_sd=.04, prior_sd=1., n_basis=6,
        n_draws=240, random_state=143,
    )
    effect=fit.coefficient_posterior("condition")
    point=bayesian_credible_band(effect,coverage=.9)
    simultaneous=bayesian_credible_band(effect,coverage=.9,simultaneous=True)

    fig,ax=plt.subplots(figsize=(6.2,3.1))
    ax.fill_between(t,simultaneous.lower[:,0],simultaneous.upper[:,0],
                    alpha=.15,label="Posterior gridwise 90% band")
    ax.fill_between(t,point.lower[:,0],point.upper[:,0],
                    alpha=.25,label="Posterior pointwise 90% intervals")
    ax.plot(t,beta_truth,"k--",label="Known effect truth")
    ax.plot(t,fit.posterior_mean_coefficients[1,:,0],label="Posterior mean")
    ax.set(xlabel="Trial phase",ylabel="Condition beta(t)",
           title="B8 fixed-noise Gaussian spline posterior")
    ax.legend(fontsize=7)
    _save(fig,FILES[0])

    # Draws from the *actual declared Gaussian spline prior*, no fake priors.
    basis=_bspline_basis(t,6)
    prior=rng.normal(0,1.,size=(240,6)) @ basis.T
    post=effect.values.reshape(240,len(t),1)[:,:,0]
    fig,ax=plt.subplots(figsize=(6.2,3.1))
    ax.fill_between(t,*np.quantile(prior,[.05,.95],axis=0),alpha=.2,label="Declared prior 90%")
    ax.fill_between(t,*np.quantile(post,[.05,.95],axis=0),alpha=.35,label="Posterior 90% pointwise")
    ax.plot(t,beta_truth,"k--",label="Synthetic beta truth")
    ax.set(xlabel="Trial phase",ylabel="Coefficient",title="B8 prior-to-posterior contraction")
    ax.legend(fontsize=7)
    _save(fig,FILES[1])

    # Conditional score posterior with fixed truth basis: NOT native learned FPCA.
    grid=np.linspace(0,1,61)
    mean=.46+.08*np.sin(np.pi*grid)
    eigen=np.array([np.sqrt(2)*np.sin(np.pi*grid)])
    irregular_time=(np.array([.02,.11,.24,.35,.48,.62,.75,.88,.98]),)
    latent=mean+.21*eigen[0]
    raw=np.interp(irregular_time[0],grid,latent)+rng.normal(0,.025,len(irregular_time[0]))
    irregular=IrregularTrajectorySet(
        time=irregular_time,values=(raw[:,None],),
        curve_ids=("known-truth-1",),dimension_names=("x",),
        coordinate_system="normalized",time_unit="normalized",
    )
    b6=fit_bayesian_sparse_score_baseline(
        irregular,dimension="x",evaluation_grid=grid,population_mean=mean,
        population_components=eigen,score_prior_variances=np.array([.09]),
        noise_sd=.025,n_draws=240,random_state=18,
    )
    trajectories_pred=b6.conditional_latent_trajectory_draws[0]
    fig,ax=plt.subplots(figsize=(6.2,3.1))
    ax.fill_between(grid,*np.quantile(trajectories_pred,[.05,.95],axis=0),
                    alpha=.3,label="Conditional posterior 90% interval")
    ax.plot(grid,latent,"k--",label="Known latent function")
    ax.scatter(irregular_time[0],raw,s=22,label="Native sparse observations")
    ax.set(xlabel="Trial phase",ylabel="x",title="B6 fixed-population benchmark (not fitted FPCA)")
    ax.legend(fontsize=7)
    _save(fig,FILES[2])

    replicated=fit.fitted_mean[None]+rng.normal(
        0,.04,size=(240,*fit.fitted_mean.shape)
    )
    check=bayesian_posterior_predictive_check(
        replicated,trajectories.values,statistic="pointwise_sd"
    )
    fig,ax=plt.subplots(figsize=(5.6,2.9))
    index=np.arange(len(check))
    ax.bar(index,check.predictive_median,width=.6,label="Replicated marginal SD")
    ax.scatter(index,check.observed_statistic,label="Observed marginal SD",color="black")
    ax.set(xticks=index,xticklabels=("x",),ylabel="SD",
           title="Posterior predictive summary — model misspecification visible")
    ax.legend(fontsize=7)
    _save(fig,FILES[3])

    # GENUINE known-prior/likelihood conjugate Normal SBC mechanism.
    truths=rng.normal(0,1,size=80)
    ysim=truths+rng.normal(0,.5,size=80)
    var=1/(1+1/.5**2)
    postmean=var*(ysim/.5**2)
    posterior=rng.normal(postmean[:,None],np.sqrt(var),size=(80,99))
    ranks,information=bayesian_calibration_study(truths,posterior,bins=10,random_state=19)
    fig,ax=plt.subplots(figsize=(5.8,2.9))
    ax.bar(ranks.bin,ranks["count"],label="Normal–Normal rank histogram")
    ax.axhline(len(truths)/len(ranks),ls="--",color="black",label="Expected count")
    ax.set(xlabel="SBC rank bin",ylabel="Frequency",
           title="B5 known-prior Gaussian SBC demonstration (not FPCA calibration)")
    ax.legend(fontsize=7)
    _save(fig,FILES[4])

    assert not information["sbc_uniformity_qualified"]
    for name in FILES:
        assert (OUTPUT/name).is_file() and (OUTPUT/name).stat().st_size > 1000
    print(f"PASS {len(FILES)} fitted/simulated Bayesian research SVGs, inference unqualified")


if __name__=="__main__":
    main()
