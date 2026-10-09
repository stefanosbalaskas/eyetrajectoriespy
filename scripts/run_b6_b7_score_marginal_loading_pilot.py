"""Paired actual native Gibbs B6/B7 likelihood-preserving ESS-mixing study.

Research-only pilot. Existing collapsed mean + conjugate load vs exact
score-marginal loading ESS on NEW prior-generated participant-level data.
Diagnostic targets are rank-invariant population mean and covariance.
Source cases and failures are retained without threshold optimization.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

from eyetrajectoriespy.bayesian.sparse_factor_gibbs import fit_bayesian_sparse_fpca
from eyetrajectoriespy.bayesian.planar_factor_gibbs import fit_bayesian_planar_factor
from eyetrajectoriespy.bayesian._posterior_diagnostics import _identified_chain_diagnostics
from eyetrajectoriespy.research.calibration_seed import calibration_replicate_seed
from scripts.run_b6_population_calibration_grid import _known_truth,GRID as B6_GRID,MEAN_PRIOR_SD,N_BASIS
from scripts.run_b6_b7_independent_pymc_nuts import _planar_data

DESIGNS=("B6_rank1","B7_rank1_paired","B7_rank1_asynchronous")
METHODS=("original_collapsed_mean","score_marginal_loading_ess")


def run_study(*,replicates:int=6,draws:int=250,warmup:int=350,
    master_seed:int=20261206,scenario_subset:tuple[str,...]=DESIGNS):
    if (replicates<2 or draws<50 or warmup<50 or
        not scenario_subset or not set(scenario_subset).issubset(DESIGNS)):
        raise ValueError("require a valid fully declared native Bayesian study")
    cases=[]
    for design in scenario_subset:
        for rep in range(replicates):
            seed=calibration_replicate_seed(
                "B6_B7_SCORE_MARGINAL_LOADING_ESS_PILOT_V1",
                master_seed=master_seed,shard_id=0,scenario=design,replicate=rep)
            if design=="B6_rank1":
                gaze,truth_mean,truth_cov,_,_=_known_truth(seed,"matched_rank1")
                grid=B6_GRID
                truth_mu=float(truth_mean[len(grid)//2])
                truth_c=float(truth_cov[len(grid)//2,len(grid)//2])
            else:
                gaze,grid,noise,truth_mean,truth_cov=_planar_data(
                    seed,design.endswith("asynchronous"))
                mid=len(grid)//2
                truth_mu=float(truth_mean[mid,0])
                truth_c=float(truth_cov[mid,len(grid)+mid])
            for mode in METHODS:
                row={
                    "design":design,"replicate":rep,"seed":seed,
                    "method":mode,"status":"failed","error_type":None,
                    "error":None,"draws_per_chain":draws,
                    "warmup":warmup,"chains":2,
                    "fit_ess_evaluations":None,
                    "population_mean_rank_rhat":None,
                    "population_mean_bulk_ess":None,
                    "covariance_rank_rhat":None,
                    "covariance_bulk_ess":None,
                    "covariance_tail_ess":None,
                    "covariance_mcse_bulk_approx":None,
                    "covariance_posterior_mean":None,
                    "covariance_posterior_q05":None,
                    "covariance_posterior_q95":None,
                    "known_covariance_truth":truth_c,
                    "covariance_90_contains_truth":None,
                    "known_mean_truth":truth_mu,
                    "scientific_inference_qualified":False,
                    "publication_authorized":False,
                }
                try:
                    opts=dict(
                        n_chains=2,n_draws=draws,warmup=warmup,thin=1,
                        random_state=seed+1231,
                        collapsed_population_mean_update=True,
                        score_marginal_loading_ess=mode=="score_marginal_loading_ess",
                        n_components=1,
                    )
                    if design=="B6_rank1":
                        fit=fit_bayesian_sparse_fpca(
                            gaze,dimension="x",evaluation_grid=grid,
                            n_basis=N_BASIS,noise_sd=.05,
                            mean_prior_sd=MEAN_PRIOR_SD,loading_prior_sd=.2,
                            **opts)
                        vals_mu=fit.population_mean_draws[:,:,len(grid)//2]
                        vals_c=fit.population_covariance_draws[:,:,len(grid)//2,len(grid)//2]
                    else:
                        fit=fit_bayesian_planar_factor(
                            gaze,dimensions=("x","y"),evaluation_grid=grid,
                            observation_noise_sd=noise,n_basis=5,
                            mean_prior_sd=.45,loading_prior_sd=.2,**opts)
                        mid=len(grid)//2
                        vals_mu=fit.population_mean_draws[:,:,mid,0]
                        vals_c=fit.joint_population_covariance_draws[:,:,mid,len(grid)+mid]
                    m=_identified_chain_diagnostics(vals_mu)
                    c=_identified_chain_diagnostics(vals_c)
                    q=np.quantile(vals_c,[.05,.95])
                    row.update(
                        status="ok",error_type=None,error=None,
                        fit_ess_evaluations=int(fit.evidence[
                            "score_marginal_loading_ess_likelihood_evaluations"]),
                        population_mean_rank_rhat=m["rank_rhat"],
                        population_mean_bulk_ess=m["bulk_ess"],
                        covariance_rank_rhat=c["rank_rhat"],
                        covariance_bulk_ess=c["bulk_ess"],
                        covariance_tail_ess=c["tail_ess"],
                        covariance_mcse_bulk_approx=c["mcse_mean_bulk_ess_approx"],
                        covariance_posterior_mean=float(np.mean(vals_c)),
                        covariance_posterior_q05=float(q[0]),
                        covariance_posterior_q95=float(q[1]),
                        covariance_90_contains_truth=bool(q[0]<=truth_c<=q[1]),
                    )
                except Exception as ex:
                    row["error_type"]=type(ex).__name__
                    row["error"]=str(ex)[:650]
                cases.append(row)
    frame=pd.DataFrame(cases)
    summaries=[]
    for (design,mode),group in frame.groupby(["design","method"]):
        valid=group.loc[group.status=="ok"]
        summaries.append({
            "design":design,"method":mode,"attempts":len(group),
            "successful_fits":len(valid),
            "failed_fits":len(group)-len(valid),
            "median_rank_rhat_covariance":(
                float(valid.covariance_rank_rhat.median()) if len(valid) else None),
            "median_bulk_ess_covariance":(
                float(valid.covariance_bulk_ess.median()) if len(valid) else None),
            "count_predeclared_identified_mix_screen_pass":int((
                (valid.covariance_rank_rhat<=1.01)&
                (valid.covariance_bulk_ess>=400)).sum()),
            "90_interval_covariance_truth_included":int(
                valid.covariance_90_contains_truth.astype(bool).sum()),
            "population_inferential_coverage_qualified":False,
        })
    evidence={
        "programme":"B6_B7_joint_score_marginal_loading_exact_elliptical_slice",
        "methodological_transition":"L_given_mu_Y_with_all_z_marginalized_then_mu_marginal_then_z_conditional",
        "original_method_default_unchanged":True,
        "likelihood_and_gaussian_prior_unaltered":True,
        "new_seed_namespace":"B6_B7_SCORE_MARGINAL_LOADING_ESS_PILOT_V1",
        "master_seed":master_seed,
        "designs":list(scenario_subset),
        "replicates_per_design":replicates,
        "methods":list(METHODS),
        "attempts":len(frame),
        "failed_attempts":int(frame.status.eq("failed").sum()),
        "raw_truth_and_all_failing_fit_attempts_retained":True,
        "prespecified_rank_rhat_screen":1.01,
        "prespecified_bulk_ess_screen":400,
        "any_sbc_or_nominal_coverage_claim":False,
        "native_sampler_scientifically_qualified":False,
        "release_authorized":False,
        "summary":summaries,
    }
    return frame,evidence


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--replicates",type=int,default=6)
    ap.add_argument("--draws",type=int,default=250)
    ap.add_argument("--warmup",type=int,default=350)
    ap.add_argument("--seed",type=int,default=20261206)
    ap.add_argument("--design",choices=DESIGNS,action="append")
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    frames,ev=run_study(
        replicates=args.replicates,draws=args.draws,warmup=args.warmup,
        master_seed=args.seed,
        scenario_subset=tuple(args.design) if args.design else DESIGNS)
    args.out.mkdir(parents=True,exist_ok=True)
    a=args.out/"cases.csv";b=args.out/"evidence.json"
    frames.to_csv(a,index=False)
    b.write_text(json.dumps(ev,indent=2,sort_keys=True)+"\n")
    (args.out/"SHA256SUMS").write_text(
        sha256(a.read_bytes()).hexdigest()+"  cases.csv\n"+
        sha256(b.read_bytes()).hexdigest()+"  evidence.json\n")
    print(json.dumps({"attempts":len(frames),"failures":ev["failed_attempts"],
        "science_qualified":False,"summary":ev["summary"]},sort_keys=True))

if __name__=="__main__":
    main()
