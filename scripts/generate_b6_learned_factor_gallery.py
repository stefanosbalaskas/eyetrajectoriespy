"""Deterministic learned Bayesian population curve/covariance research gallery.

The data are from a known finite-B-spline Gaussian factor process. The
posterior is fitted with B6 *native Gibbs* and learns both mean and covariance
under fixed noise/rank/prior scales. Displayed bands are posterior pointwise
intervals, NOT qualified empirical coverage nor identified FPCA eigenfunctions.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from eyetrajectoriespy.types import IrregularTrajectorySet
from eyetrajectoriespy.bayesian import fit_bayesian_sparse_fpca
from eyetrajectoriespy.bayesian.sparse_factor_gibbs import _spline_basis


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,default=Path("docs/assets/research"))
    args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    plt.rcParams["svg.hashsalt"]="eyetrajectoriespy-b6-learned-factor"
    plt.rcParams["font.family"]="DejaVu Sans"
    rng=np.random.default_rng(241006)
    grid=np.linspace(0,1,49)
    mean_coeff=np.array([.31,.53,.42,.22,.29])
    loading_coeff=np.array([.07,.14,-.04,.23,.12])
    truth_basis=_spline_basis(grid,0,1,5)
    true_mean=truth_basis@mean_coeff
    true_cov_diag=np.square(truth_basis@loading_coeff)
    times,values,curve_ids=[],[],[]
    for i in range(26):
        t=np.sort(rng.uniform(.02,.98,9+(i%7)))
        latent=float(rng.normal())
        y=_spline_basis(t,0,1,5)@(mean_coeff+latent*loading_coeff)
        y+=rng.normal(0,.04,len(t))
        times.append(t)
        values.append(y[:,None])
        curve_ids.append(f"synthetic_P{i:02d}")
    gaze=IrregularTrajectorySet(
        time=tuple(times),values=tuple(values),
        curve_ids=tuple(curve_ids),dimension_names=("x",),
        coordinate_system="normalized",time_unit="normalized",
        metadata=pd.DataFrame({"participant_id":curve_ids}),
        provenance={"synthetic_known_factor_truth":True},
    )
    fit=fit_bayesian_sparse_fpca(
        gaze,dimension="x",evaluation_grid=grid,noise_sd=.04,
        n_components=1,n_basis=5,mean_prior_sd=.8,
        loading_prior_sd=.3,n_chains=2,
        n_draws=80,warmup=100,thin=1,random_state=4106,
    )
    summaries=fit.posterior_population_frame()
    assert fit.evidence["population_mean_learned"]
    assert fit.evidence["population_covariance_learned"]
    assert not fit.evidence["posterior_inference_scientifically_qualified"]
    fig,axes=plt.subplots(1,2,figsize=(9,3.2))
    axes[0].plot(grid,true_mean,ls="--",color="black",label="Known truth")
    axes[0].plot(grid,summaries.mean_posterior_mean,
                 label="Fitted Gibbs posterior mean",lw=2)
    axes[0].fill_between(grid,summaries.mean_posterior_q05,
                         summaries.mean_posterior_q95,alpha=.3,
                         label="Pointwise posterior 90% interval")
    axes[0].set(xlabel="Trial phase",ylabel="x coordinate",
                title="Population mean function")
    axes[0].legend(fontsize=7)
    axes[1].plot(grid,true_cov_diag,ls="--",color="black",
                 label="Known latent variance")
    axes[1].plot(grid,summaries.latent_covariance_diagonal_mean,
                 lw=2,label="Posterior latent variance")
    axes[1].fill_between(grid,summaries.latent_covariance_diagonal_q05,
                         summaries.latent_covariance_diagonal_q95,
                         alpha=.3,label="Pointwise posterior 90% interval")
    axes[1].set(xlabel="Trial phase",ylabel="Latent variance",
                title="Learned covariance diagonal")
    axes[1].legend(fontsize=7)
    fig.suptitle(
        "Known synthetic truth and learned B6 finite-basis posterior — unqualified",
        fontsize=10,
    )
    fig.tight_layout()
    path=args.out/"b6-learned-population-mean-covariance.svg"
    fig.savefig(path,format="svg",
                metadata={"Date":None,"Creator":"eyetrajectoriespy B6 Gibbs research"})
    plt.close(fig)
    summaries["true_population_mean"]=true_mean
    summaries["true_population_covariance_diagonal"]=true_cov_diag
    summaries.to_csv(args.out/"b6-learned-population-known-truth.csv",index=False)
    assert path.stat().st_size>2000
    print("PASS: learned posterior mean+covariance from native Gibbs; no scientific coverage claim")


if __name__=="__main__":
    main()
