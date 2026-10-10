"""B6/B7 research-only long-chain identified population covariance geometry audit.

Independent prior-generated rank-one data, longer four-chain native Gibbs
versus longer *separate* PyMC/NUTS. Source failures retained; no scientific
coverage or population-uncertainty qualification is inferred from Rhat alone.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import arviz as az
import numpy as np

from eyetrajectoriespy.bayesian.sparse_factor_gibbs import (
    _spline_basis, fit_bayesian_sparse_fpca,
)
from eyetrajectoriespy.bayesian.planar_factor_gibbs import fit_bayesian_planar_factor
from eyetrajectoriespy.research.calibration_seed import calibration_replicate_seed
from scripts.run_b6_population_calibration_grid import (
    _known_truth, GRID as B6_GRID, MEAN_PRIOR_SD, N_BASIS,
)
from scripts.run_b6_b7_independent_pymc_nuts import _planar_data, _pymc_marginal

DESIGNS=("B6_rank1","B7_rank1_paired","B7_rank1_asynchronous")
METHODS=("original_collapsed_mean","joint_loading_score_marginal_ESS",
         "independent_score_integrated_PyMC_NUTS")


def identified_mcse_geometry(a: np.ndarray)->dict:
    """Independent *spectral* ArviZ mean MCSE, rank Rhat, ESS and chain drift.

    Analysis is only valid on the IDENTIFIED functional scalar (population
    covariance or population mean), not on sign-ambiguous raw loadings.
    Half-chain difference is descriptive; it is NOT a formal convergence test.
    """
    x=np.asarray(a,dtype=float)
    if (x.ndim!=2 or x.shape[0]<2 or x.shape[1]<100
        or not np.isfinite(x).all()):
        raise ValueError("need >=2 full finite chains, >=100 draws each")
    def scalar(obj, label):
        v=np.asarray(obj,dtype=float)
        if v.size!=1 or not np.isfinite(v).all():
            raise ValueError(f"invalid scalar {label} for identified chain")
        return float(v.item())
    med=x.shape[1]//2
    rhat=scalar(az.rhat(x,method="rank"),"rank Rhat")
    ess=scalar(az.ess(x,method="bulk"),"bulk ESS")
    tail=scalar(az.ess(x,method="tail"),"tail ESS")
    essmean=scalar(az.ess(x,method="mean"),"mean ESS")
    # Genuine autocorrelation-aware ArviZ spectral mean MCSE.
    mcse=scalar(az.mcse(x,method="mean"),"spectral mean MCSE")
    scale=float(np.std(x.reshape(-1),ddof=1))
    chain_means=x.mean(axis=1)
    result={
       "chains":int(x.shape[0]),"draws_per_chain":int(x.shape[1]),
       "rank_rhat":rhat,"bulk_ess":ess,"tail_ess":tail,
       "mean_ess":essmean,"mcse_mean_spectral":mcse,
       "posterior_mean":float(x.mean()),"posterior_sd":scale,
       "posterior_q05":float(np.quantile(x,.05)),
       "posterior_q95":float(np.quantile(x,.95)),
       "chain_means":[float(z) for z in chain_means],
       "chain_mean_range_in_posterior_sds":(
           float(np.ptp(chain_means)/scale) if scale>0 else None),
       "first_half_mean":float(x[:,:med].mean()),
       "second_half_mean":float(x[:,med:].mean()),
       "half_chain_shift_in_posterior_sds":(
           float((x[:,med:].mean()-x[:,:med].mean())/scale)
           if scale>0 else None),
       "passes_exploratory_identified_screen":bool(rhat<=1.01 and ess>=400),
       "scientifically_qualified":False,
    }
    return result


def run_design(*,design:str,native_draws:int=800,native_warmup:int=1000,
               nuts_draws:int=800,nuts_warmup:int=1200,
               master_seed:int=20261212)->tuple[list[dict],dict]:
    if design not in DESIGNS:
        raise ValueError("unknown research study design")
    if min(native_draws,native_warmup,nuts_draws,nuts_warmup)<100:
        raise ValueError("too few warmup/draws for a preregistered long-chain audit")
    seed=calibration_replicate_seed(
       "B6_B7_LONGCHAIN_IDENTIFIED_GEOMETRY_V1",
       master_seed=master_seed,shard_id=0,scenario=design,replicate=0)
    if design=="B6_rank1":
        gaze,truth_mean,truth_cov,_,_=_known_truth(seed,"matched_rank1")
        grid=B6_GRID
        noise=(.05,)
        dimensions=("x",)
        truth_mu=float(truth_mean[len(grid)//2])
        truth_covariance=float(truth_cov[len(grid)//2,len(grid)//2])
        prior_sd=MEAN_PRIOR_SD
    else:
        gaze,grid,noise,truth_mean,truth_cov=_planar_data(
             seed,design.endswith("asynchronous"))
        dimensions=("x","y")
        mid=len(grid)//2
        truth_mu=float(truth_mean[mid,0])
        truth_covariance=float(truth_cov[mid,len(grid)+mid])
        prior_sd=.45
    mid=len(grid)//2
    rows=[]
    for method in METHODS:
        row=dict(
          design=design,method=method,generation_seed=seed,
          status="failed",error_type=None,error=None,
          fitted_chains=None,posterior_draws_per_chain=None,
          identified_mean=None,identified_covariance=None,
          reference_divergences=None,
          model_matched_known_priors=True,
          rank=1,
          source_actual_posterior_fit_completed=False,
          population_covariance_scientifically_qualified=False,
          SBC_or_nominal_coverage_qualified=False,
          release_authorized=False,
        )
        try:
            if method=="independent_score_integrated_PyMC_NUTS":
                idata=_pymc_marginal(
                    gaze,dimensions=dimensions,noise_sd=noise,q=5,k=1,
                    mean_sd=prior_sd,load_sd=.2,draws=nuts_draws,
                    warmup=nuts_warmup,random_state=seed+201)
                mean=np.asarray(idata.posterior["mean"])
                loading=np.asarray(idata.posterior["load"])
                at=_spline_basis(grid,0.,1.,5)[mid]
                mean_func=np.einsum("q,cdq->cd",at,mean[:,:,0,:])
                lx=np.einsum("q,cdq->cd",at,loading[:,:,0,:,0])
                if len(dimensions)==1:
                    cov_func=lx*lx
                else:
                    ly=np.einsum("q,cdq->cd",at,loading[:,:,1,:,0])
                    cov_func=lx*ly
                divergence=np.asarray(idata.sample_stats["diverging"],dtype=int)
                row["reference_divergences"]=int(divergence.sum())
            else:
                options=dict(
                    n_chains=4,n_draws=native_draws,warmup=native_warmup,
                    thin=1,n_components=1,random_state=seed+1231,
                    collapsed_population_mean_update=True,
                    score_marginal_loading_ess=(
                         method=="joint_loading_score_marginal_ESS"),
                )
                if design=="B6_rank1":
                    fit=fit_bayesian_sparse_fpca(
                        gaze,dimension="x",evaluation_grid=grid,
                        n_basis=N_BASIS,noise_sd=noise[0],
                        mean_prior_sd=prior_sd,loading_prior_sd=.2,**options)
                    mean_func=fit.population_mean_draws[:,:,mid]
                    cov_func=fit.population_covariance_draws[:,:,mid,mid]
                else:
                    fit=fit_bayesian_planar_factor(
                        gaze,dimensions=dimensions,evaluation_grid=grid,
                        observation_noise_sd=noise,n_basis=5,
                        mean_prior_sd=prior_sd,loading_prior_sd=.2,**options)
                    mean_func=fit.population_mean_draws[:,:,mid,0]
                    cov_func=fit.joint_population_covariance_draws[
                         :,:,mid,len(grid)+mid]
            mg=identified_mcse_geometry(mean_func)
            cg=identified_mcse_geometry(cov_func)
            q05,q95=cg["posterior_q05"],cg["posterior_q95"]
            cg["contains_single_generated_truth_90pct"]=bool(
                 q05<=truth_covariance<=q95)
            row.update(
              status="ok",error_type=None,error=None,
              source_actual_posterior_fit_completed=True,
              fitted_chains=mg["chains"],
              posterior_draws_per_chain=mg["draws_per_chain"],
              identified_mean=mg,identified_covariance=cg,
            )
        except Exception as exc:
            row["error_type"]=type(exc).__name__
            row["error"]=str(exc)[:600]
        rows.append(row)
    results={
        "programme":"B6_B7_LONGCHAIN_IDENTIFIED_COVARIANCE_GEOMETRY_V1",
        "design":design,
        "data_generation_seed":seed,
        "n_independent_truth_datasets":1,
        "full_posterior_fit_attempts":len(rows),
        "failed_attempts":sum(x["status"]=="failed" for x in rows),
        "original_data_geometry_untouched":True,
        "independent_likelihood_backend":"PyMC NUTS score-integrated",
        "native_original_default_preserved":True,
        "parameterization_rank":1,
        "predeclared_rank_rhat_cutoff":1.01,
        "predeclared_bulk_ess_cutoff":400,
        "mcse_method":"ArviZ spectral autocorrelation-aware mean MCSE",
        "half_chain_drift_only_descriptive":True,
        "source_inference_qualified":False,
        "rank2_covered":False,
        "SBC_completed":False,
        "coverage_qualified":False,
        "release_authorized":False,
    }
    return rows,results


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--design",choices=DESIGNS,required=True)
    parser.add_argument("--native-draws",type=int,default=800)
    parser.add_argument("--native-warmup",type=int,default=1000)
    parser.add_argument("--nuts-draws",type=int,default=800)
    parser.add_argument("--nuts-warmup",type=int,default=1200)
    parser.add_argument("--seed",type=int,default=20261212)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    rows,evidence=run_design(
       design=args.design,native_draws=args.native_draws,
       native_warmup=args.native_warmup,nuts_draws=args.nuts_draws,
       nuts_warmup=args.nuts_warmup,master_seed=args.seed)
    args.out.mkdir(parents=True,exist_ok=True)
    path=args.out/"cases.json"
    ledger=args.out/"evidence.json"
    path.write_text(json.dumps(rows,sort_keys=True,indent=2)+"\n")
    ledger.write_text(json.dumps(evidence,sort_keys=True,indent=2)+"\n")
    (args.out/"SHA256SUMS").write_text(
       sha256(path.read_bytes()).hexdigest()+"  cases.json\n"
       +sha256(ledger.read_bytes()).hexdigest()+"  evidence.json\n")
    print("B6/B7 LONGCHAIN GEOMETRY:",json.dumps({
       "design":args.design,"attempts":len(rows),
       "errors":evidence["failed_attempts"],
       "covariance_screen":{x["method"]:(
         x["identified_covariance"]["passes_exploratory_identified_screen"]
         if x["status"]=="ok" else None) for x in rows},
       "science_qualified":False,
    },sort_keys=True))


if __name__=="__main__":
    main()
