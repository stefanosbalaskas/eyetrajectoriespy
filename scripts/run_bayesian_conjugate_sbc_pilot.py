"""B5 known-prior calibration for B6 known-basis and B8 fixed-noise Gaussian.

Every replication draws the true quantity from the implemented model prior,
then observations from that model likelihood, and independently fits the
corresponding conjugate implementation. Does NOT validate full Bayesian FPCA,
latent eigenfunction uncertainty, residual autocorrelation or mixed effects.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest
from eyetrajectoriespy.types import TrajectorySet, IrregularTrajectorySet
from eyetrajectoriespy.bayesian import (
    bayesian_calibration_study,
    fit_bayesian_sparse_score_baseline, fit_bayesian_function_on_scalar,
)
from eyetrajectoriespy.bayesian.function_on_scalar import _bspline_basis


def _conditional_score_case(seed: int, draws: int) -> tuple[float, np.ndarray]:
    rng = np.random.default_rng(seed)
    grid = np.linspace(0, 1, 41)
    mean = .4 + .03*np.sin(np.pi*grid)
    basis = np.array([np.sqrt(2)*np.sin(np.pi*grid)])
    latent_score = float(rng.normal(0, .3))
    times = np.sort(rng.uniform(.03, .97, 13))
    measured = (np.interp(times, grid, mean+latent_score*basis[0])
                + rng.normal(0, .05, len(times)))
    data = IrregularTrajectorySet(
        time=(times,), values=(measured[:,None],),
        curve_ids=("synthetic-unit",),dimension_names=("x",),
        coordinate_system="normalized",time_unit="normalized",
    )
    fit = fit_bayesian_sparse_score_baseline(
        data, dimension="x", evaluation_grid=grid,
        population_mean=mean, population_components=basis,
        score_prior_variances=np.array([.09]), noise_sd=.05,
        n_draws=draws, random_state=seed+1,
    )
    return latent_score, fit.posterior_score_draws[0,:,0]


def _regression_case(seed: int, draws: int) -> tuple[float, np.ndarray]:
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 1, 21)
    n_basis = 5
    basis = _bspline_basis(t, n_basis)
    x = np.column_stack((np.ones(20), np.r_[np.zeros(10),np.ones(10)]))
    prior_sd = .25
    theta = rng.normal(0, prior_sd, size=(2,n_basis))
    mean = x @ theta @ basis.T
    y = mean + rng.normal(0, .08, size=mean.shape)
    gaze = TrajectorySet(
        time=t, values=y[:,:,None], curve_ids=tuple(f"P{i}" for i in range(len(x))),
        dimension_names=("x",),time_unit="normalized",coordinate_system="normalized",
        metadata=pd.DataFrame({"participant_id":[f"P{i}" for i in range(len(x))]}),
    )
    design=pd.DataFrame({"curve_id":gaze.curve_ids,
                         "intercept":x[:,0],"condition":x[:,1]})
    fit=fit_bayesian_function_on_scalar(
        gaze,design=design,predictors=("intercept","condition"),
        noise_sd=.08,prior_sd=prior_sd,n_basis=n_basis,n_draws=draws,
        random_state=seed+1,
    )
    index = len(t)//2
    actual=float(theta[1]@basis[index])
    return actual, fit.posterior_coefficient_draws[:,1,index,0]


def run_case(fn, *, seed: int, n_replicates: int,
             n_draws: int) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    rng = np.random.default_rng(seed)
    rows,truths,posterior=[],[],[]
    for iteration in range(n_replicates):
        sample_seed=int(rng.integers(1,2**30))
        rec={"replicate":iteration,"seed":sample_seed,"status":"failed",
             "true_value":np.nan,"posterior_mean":np.nan,
             "included_in_90pct_interval":None,
             "exception":None}
        try:
            truth, draw = fn(sample_seed,n_draws)
            assert len(draw)==n_draws and np.isfinite(draw).all()
            lo,hi = np.quantile(draw,[.05,.95])
            rec.update(status="ok",true_value=truth,
                       posterior_mean=float(np.mean(draw)),
                       included_in_90pct_interval=bool(lo<=truth<=hi))
            truths.append(truth)
            posterior.append(draw)
        except Exception as error:
            rec["exception"]=f"{type(error).__name__}: {error}"[:300]
        rows.append(rec)
    records=pd.DataFrame(rows)
    hist=pd.DataFrame(columns=["bin","rank_start","rank_end","count"])
    evidence={
        "n_attempted":len(records),
        "n_success":len(posterior),
        "n_failed":len(records)-len(posterior),
        "draws_per_posterior":n_draws,
        "coverage_90_conditional_on_success":None,
        "coverage_90_exact_95_interval":None,
        "rank_uniformity_scientifically_qualified":False,
        "fit_failures_retained":True,
        "full_population_Bayesian_FPCA_qualified":False,
        "missingness_or_serial_noise_qualified":False,
        "prior_and_likelihood_generator_matches_conjugate_baseline":True,
        "experimental":True,
    }
    if len(posterior)>=5:
        hist, sbc=bayesian_calibration_study(
            np.array(truths),np.stack(posterior),bins=10,
            random_state=seed+999,
        )
        successes=records.loc[records.status=="ok"]
        k=int(successes.included_in_90pct_interval.astype(bool).sum())
        n=len(successes)
        interval=binomtest(k,n).proportion_ci(.95,method="exact")
        evidence["coverage_90_conditional_on_success"]=k/n
        evidence["coverage_90_exact_95_interval"]=[interval.low,interval.high]
        evidence["rank_summary"]=sbc
    return records,hist,evidence


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--replicates",type=int,default=30)
    p.add_argument("--posterior-draws",type=int,default=99)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    if args.replicates<5 or args.posterior_draws<20:
        raise ValueError("at least five independent replications and 20 posterior draws")
    args.out.mkdir(parents=True,exist_ok=True)
    all_evidence={}
    for label,fn,seed in (
        ("B6_known_population_sparse_score",_conditional_score_case,6524),
        ("B8_fixed_noise_Bspline_regression",_regression_case,7552),
    ):
        cases,ranks,evidence=run_case(
            fn,seed=seed,n_replicates=args.replicates,n_draws=args.posterior_draws
        )
        cases.to_csv(args.out/f"{label}_cases.csv",index=False)
        ranks.to_csv(args.out/f"{label}_sbc_ranks.csv",index=False)
        all_evidence[label]=evidence
    evidence_path=args.out/"qualification.json"
    evidence_path.write_text(json.dumps({
        "scenarios":all_evidence,
        "scientific_qualification":False,
        "release_authorized":False,
        "not_learnt_population_Bayesian_FPCA":True,
        "not_general_functional_posterior_calibration":True,
    },indent=2,sort_keys=True)+"\n")
    files=sorted(args.out.glob("*.csv"))+[evidence_path]
    (args.out/"sha256.txt").write_text("\n".join(
        f"{sha256(file.read_bytes()).hexdigest()}  {file.name}" for file in files
    )+"\n")
    print(evidence_path.read_text())
    print("B5 B6/B8 exact-model calibration PILOT; no scientific promotion")


if __name__=="__main__":
    main()
