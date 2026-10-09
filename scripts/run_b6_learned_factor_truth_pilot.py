"""Known-prior calibration pilot for genuinely LEARNED B6 Gaussian function factors.

Each replicate draws the population mean/loadings from the exact model priors,
unit scores from their Gaussian prior, and native irregular gaze observations
from the independent Gaussian likelihood. It refits the Gibbs sampler on
each replicate, retains failures, and summarizes 90% posterior intervals
for *rotation-invariant* population mean and covariance diagonal.

Small CI pilot is proof of executing calibration, NOT proof of nominal
coverage, chain mixing, or universal functional FPCA validity.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest

from eyetrajectoriespy.types import IrregularTrajectorySet
from eyetrajectoriespy.bayesian import fit_bayesian_sparse_fpca
from eyetrajectoriespy.bayesian.sparse_factor_gibbs import _spline_basis


def _one(seed: int, draws: int, warmup: int) -> tuple[dict, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    grid = np.linspace(0, 1, 27)
    q = 5
    n = 16
    mean_prior_sd = .45
    loading_prior_sd = .20
    noise_sd = .05
    true_mean = rng.normal(0, mean_prior_sd, q)
    true_loadings = rng.normal(0, loading_prior_sd, (q,1))
    scores = rng.normal(size=(n,1))
    times = []
    values = []
    for i in range(n):
        ti = np.sort(rng.uniform(.025, .975, 10 + (i%5)))
        B = _spline_basis(ti, grid[0], grid[-1], q)
        yi = B @ (true_mean + true_loadings @ scores[i])
        yi = yi + rng.normal(0, noise_sd, len(ti))
        times.append(ti)
        values.append(yi[:,None])
    gaze = IrregularTrajectorySet(
        time=tuple(times), values=tuple(values),
        curve_ids=tuple(f"person{i}" for i in range(n)),
        dimension_names=("x",), time_unit="normalized",
        coordinate_system="normalized",
        metadata=pd.DataFrame({"participant_id": [f"P{i}" for i in range(n)]}),
        provenance={"known_truth_prior_draw":True},
    )
    fit = fit_bayesian_sparse_fpca(
        gaze,dimension="x",evaluation_grid=grid,
        n_components=1,n_basis=q,noise_sd=noise_sd,
        mean_prior_sd=mean_prior_sd,loading_prior_sd=loading_prior_sd,
        n_chains=2,n_draws=draws,warmup=warmup,thin=1,
        random_state=seed+333,
    )
    center = len(grid)//2
    b = _spline_basis(grid, grid[0], grid[-1],q)[center]
    population_mean_truth = float(b@true_mean)
    pop_cov_truth = float((b@true_loadings)[0]**2)
    mean_posterior = fit.population_mean_draws[:,:,center].reshape(-1)
    covariance_posterior = fit.population_covariance_draws[:,:,center,center].reshape(-1)
    qmu = np.quantile(mean_posterior,[.05,.95])
    qcov = np.quantile(covariance_posterior,[.05,.95])
    return {
        "population_mean_truth":population_mean_truth,
        "population_covariance_diag_truth":pop_cov_truth,
        "population_mean_90_included":bool(qmu[0] <= population_mean_truth <= qmu[1]),
        "population_covariance_90_included":bool(qcov[0] <= pop_cov_truth <= qcov[1]),
        "population_mean_posterior_median":float(np.median(mean_posterior)),
        "covariance_diag_posterior_median":float(np.median(covariance_posterior)),
        "observed_curves":n,
        "posterior_chains":fit.n_chains,
        "posterior_draws_per_chain":fit.n_draws_per_chain,
    }, mean_posterior, covariance_posterior


def _status(successful: pd.DataFrame, key: str) -> dict:
    if successful.empty:
        return {"coverage":None,"coverage_exact_95_CI":None}
    n=len(successful)
    k=int(successful[key].astype(bool).sum())
    ci=binomtest(k,n).proportion_ci(confidence_level=.95,method="exact")
    return {"coverage":k/n,"count_included":k,
            "n_success":n,"coverage_exact_95_CI":[float(ci.low),float(ci.high)]}


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--replicates",type=int,default=8)
    ap.add_argument("--draws",type=int,default=35)
    ap.add_argument("--warmup",type=int,default=60)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    if args.replicates<5 or args.draws<20 or args.warmup<20:
        raise ValueError("at least 5 replicates, 20 draws and 20 warmup")
    rng=np.random.default_rng(493402)
    rows=[]
    for i in range(args.replicates):
        seed=int(rng.integers(100,2**30))
        row={"replicate":i,"seed":seed,"status":"failed","exception":None}
        try:
            info,_,_=_one(seed,args.draws,args.warmup)
            row.update(info)
            row["status"]="ok"
        except Exception as error:
            row["exception"]=f"{type(error).__name__}: {error}"[:300]
        rows.append(row)
    table=pd.DataFrame(rows)
    good=table.loc[table.status=="ok"]
    payload={
        "model":"B6_finite_basis_Gaussian_factor_Gibbs",
        "population_mean_and_covariance_LEARNED":True,
        "generating_truth_from_exact_prior":True,
        "generating_observations_from_declared_likelihood":True,
        "posterior_refit_per_replicate":True,
        "n_attempted":len(table),
        "n_successful":len(good),
        "n_failed":int((table.status!="ok").sum()),
        "mean_location_90":_status(good,"population_mean_90_included"),
        "population_covariance_90":_status(good,"population_covariance_90_included"),
        "posterior_mixing_and_rank_SBC_qualified":False,
        "posterior_coverage_scientifically_qualified":False,
        "component_sign_rotation_identified":False,
        "noise_prior_and_rank_sensitivity_qualified":False,
        "out_of_model_missingness_sensitivity_qualified":False,
        "release_authorized":False,
    }
    args.out.mkdir(parents=True,exist_ok=True)
    data=args.out/"cases.csv"
    table.to_csv(data,index=False)
    evidence=args.out/"evidence.json"
    evidence.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
    (args.out/"sha256.txt").write_text(
        sha256(data.read_bytes()).hexdigest()+"  cases.csv\n"+
        sha256(evidence.read_bytes()).hexdigest()+"  evidence.json\n"
    )
    print(json.dumps(payload,indent=2))


if __name__=="__main__":
    main()
