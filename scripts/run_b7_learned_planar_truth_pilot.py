"""B7 prior/likelihood population posterior pilot; never scientific qualification.

Known rank-1/2 x/y means and loadings are drawn from declared Gaussian priors,
each participant has ONE shared latent score vector, and each observed channel
at its native (potentially disjoint) timestamps follows the declared likelihood.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest

from eyetrajectoriespy.bayesian import fit_bayesian_planar_factor
from eyetrajectoriespy.bayesian.sparse_factor_gibbs import _spline_basis
from eyetrajectoriespy.types import IrregularTrajectorySet


def _replicate(seed: int, rank: int, asynchronous: bool, draws: int, warmup: int) -> dict:
    rng=np.random.default_rng(seed)
    grid=np.linspace(0,1,23)
    n,q=18,5
    mean_prior_sd, loading_prior_sd=.45,.20
    noise=np.array([.04,.06])
    mu=rng.normal(0,mean_prior_sd,(2,q))
    load=rng.normal(0,loading_prior_sd,(2,q,rank))
    times, values=[], []
    for i in range(n):
        tx=np.sort(rng.uniform(.01,.99,size=12+i%3))
        ty=np.sort(rng.uniform(.01,.99,size=11+i%4)) if asynchronous else tx.copy()
        z=rng.normal(size=rank)
        xx=_spline_basis(tx,0,1,q)@(mu[0]+load[0]@z)
        yy=_spline_basis(ty,0,1,q)@(mu[1]+load[1]@z)
        xx += rng.normal(0,noise[0],len(tx))
        yy += rng.normal(0,noise[1],len(ty))
        if asynchronous:
            joint=np.sort(np.r_[tx,ty])
            data=np.full((len(joint),2),np.nan)
            data[np.searchsorted(joint,tx),0]=xx
            data[np.searchsorted(joint,ty),1]=yy
        else:
            joint=tx
            data=np.column_stack((xx,yy))
        times.append(joint)
        values.append(data)
    gaze=IrregularTrajectorySet(
        time=tuple(times),values=tuple(values),
        curve_ids=tuple(f"u{i}" for i in range(n)),
        dimension_names=("x","y"),coordinate_system="normalized",time_unit="s",
        metadata=pd.DataFrame({"participant_id":[f"P{i}" for i in range(n)]}),
        provenance={"synthetic_prior_likelihood_known_truth":True},
    )
    b=_spline_basis(grid,0,1,q)
    true_mean=np.column_stack((b@mu[0],b@mu[1]))
    true_projected=np.concatenate((b@load[0],b@load[1]),axis=0)
    true_cov=true_projected@true_projected.T
    fit=fit_bayesian_planar_factor(
        gaze,evaluation_grid=grid,observation_noise_sd=tuple(noise),
        n_components=rank,n_basis=q,mean_prior_sd=mean_prior_sd,
        loading_prior_sd=loading_prior_sd,n_chains=2,n_draws=draws,
        warmup=warmup,thin=1,random_state=seed+109)
    mid=len(grid)//2
    mu_draws=fit.population_mean_draws[:,:,mid,:].reshape(-1,2)
    cross_draws=fit.joint_population_covariance_draws[:,:,mid,len(grid)+mid].reshape(-1)
    qmu=np.quantile(mu_draws,[.05,.95],axis=0)
    qcross=np.quantile(cross_draws,[.05,.95])
    return {
        "x_mean_mid_90_covered":bool(qmu[0,0]<=true_mean[mid,0]<=qmu[1,0]),
        "y_mean_mid_90_covered":bool(qmu[0,1]<=true_mean[mid,1]<=qmu[1,1]),
        "xy_crosscov_mid_90_covered":bool(
            qcross[0]<=true_cov[mid,len(grid)+mid]<=qcross[1]),
        "xy_crosscov_mid_absolute_error":float(
            abs(cross_draws.mean()-true_cov[mid,len(grid)+mid])),
        "population_joint_covariance_psd_draws":bool(all(
            np.linalg.eigvalsh(c).min()>-1e-8 for c in
            fit.joint_population_covariance_draws.reshape(-1,2*len(grid),2*len(grid)))),
        "source_asynchronous":bool(asynchronous),
        "observations_resampled":bool(fit.evidence["native_observation_times_interpolated"]),
    }


def _coverage(df: pd.DataFrame, name: str) -> dict:
    if df.empty:
        return {"completed":0,"coverage":None,"exact_95_mc_interval":None}
    k=int(df[name].sum())
    n=len(df)
    ci=binomtest(k,n).proportion_ci(.95,method="exact")
    return {"completed":n,"included":k,"coverage":k/n,
            "exact_95_mc_interval":[float(ci.low),float(ci.high)]}


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--replicates",type=int,default=4)
    parser.add_argument("--draws",type=int,default=35)
    parser.add_argument("--warmup",type=int,default=60)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    if args.replicates<2 or args.draws<20 or args.warmup<20:
        raise ValueError("at least 2 replicates, 20 retained draws and 20 warmup sweeps")
    rng=np.random.default_rng(306700)
    records=[]
    for rank in (1,2):
        for asynchronous in (False,True):
            for iteration in range(args.replicates):
                seed=int(rng.integers(1000,2**30))
                record=dict(rank=rank,asynchronous=asynchronous,
                            replicate=iteration,seed=seed,status="failed",
                            exception_type=None,exception=None)
                try:
                    record.update(_replicate(seed,rank,asynchronous,args.draws,args.warmup))
                    record["status"]="ok"
                except Exception as e:
                    record["exception_type"]=type(e).__name__
                    record["exception"]=str(e)[:500]
                records.append(record)
    frame=pd.DataFrame(records)
    scenarios=[]
    for (rank,asynchronous),one in frame.groupby(["rank","asynchronous"]):
        good=one.loc[one.status=="ok"]
        scenarios.append({
            "rank":int(rank),"asynchronous":bool(asynchronous),
            "attempted":len(one),"failed":len(one)-len(good),
            "x_mean_90":_coverage(good,"x_mean_mid_90_covered"),
            "y_mean_90":_coverage(good,"y_mean_mid_90_covered"),
            "xy_crosscovariance_90":_coverage(good,"xy_crosscov_mid_90_covered"),
        })
    evidence={
        "programme":"B7_planar_shared_factor_learned_population_prior_truth",
        "actual_native_learned_Gibbs_refit_each_case":True,
        "paired_and_asynchronous_observations":True,
        "rank1_and_rank2":True,
        "population_joint_xy_covariance_learned":True,
        "full_rank_based_SBC_qualified":False,
        "scientific_coverage_qualified":False,
        "individual_eigenfunctions_identified":False,
        "residual_serial_or_cross_channel_noise_learned":False,
        "publication_authorized":False,
        "attempts":len(frame),"failed":int((frame.status=="failed").sum()),
        "scenarios":scenarios,
    }
    args.out.mkdir(parents=True,exist_ok=True)
    cases=args.out/"cases.csv"
    source=args.out/"evidence.json"
    frame.to_csv(cases,index=False)
    source.write_text(json.dumps(evidence,indent=2,sort_keys=True)+"\n")
    (args.out/"sha256.txt").write_text(
        sha256(cases.read_bytes()).hexdigest()+"  cases.csv\n"+
        sha256(source.read_bytes()).hexdigest()+"  evidence.json\n")
    print(json.dumps(evidence,sort_keys=True,indent=2))


if __name__=="__main__":
    main()
