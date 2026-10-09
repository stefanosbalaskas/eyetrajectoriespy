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

from eyetrajectoriespy.bayesian import (fit_bayesian_planar_factor, predict_bayesian_planar_new_participant)
from eyetrajectoriespy.bayesian.sparse_factor_gibbs import _spline_basis
from eyetrajectoriespy.types import IrregularTrajectorySet
from eyetrajectoriespy.research.calibration_seed import (calibration_replicate_seed, calibration_manifest)


def _replicate(seed: int, rank: int, asynchronous: bool, draws: int, warmup: int, *, diagnostics: bool=False, scale_interweave_proposal_sd: float=0.0, collapsed_population_mean_update: bool=False) -> dict:
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
        loading_prior_sd=loading_prior_sd,
        scale_interweave_proposal_sd=scale_interweave_proposal_sd,
        collapsed_population_mean_update=collapsed_population_mean_update,
        n_chains=2,n_draws=draws,
        warmup=warmup,thin=1,random_state=seed+109)
    mid=len(grid)//2
    mu_draws=fit.population_mean_draws[:,:,mid,:].reshape(-1,2)
    cross_draws=fit.joint_population_covariance_draws[:,:,mid,len(grid)+mid].reshape(-1)
    qmu=np.quantile(mu_draws,[.05,.95],axis=0)
    qcross=np.quantile(cross_draws,[.05,.95])
    # A genuinely held-out participant is generated AFTER fitting; never
    # included in the learned population likelihood or fitted score tensor.
    indices_x=np.asarray([3,8,12,18])
    indices_y=np.asarray([5,9,14,20])
    new_score=rng.normal(size=rank)
    expected_x=(b[indices_x]@(mu[0]+load[0]@new_score))
    expected_y=(b[indices_y]@(mu[1]+load[1]@new_score))
    withheld=np.r_[
        expected_x+rng.normal(0,noise[0],len(indices_x)),
        expected_y+rng.normal(0,noise[1],len(indices_y)),
    ]
    prediction=predict_bayesian_planar_new_participant(
        fit,evaluation_indices_x=indices_x,evaluation_indices_y=indices_y,
        observation_noise_sd=tuple(noise),random_state=seed+210)
    summary=prediction.summary_frame()
    diag=fit.diagnostics_frame() if diagnostics else None
    max_rhat=float(diag.rhat_max.max()) if diag is not None else None
    min_bulk=float(diag.ess_bulk_min.min()) if diag is not None else None
    included=(summary.predictive_q05.to_numpy()<=withheld)&(
        withheld<=summary.predictive_q95.to_numpy())
    return {
        "scale_interweave_acceptance_rate":fit.evidence["scale_interweave_acceptance_rate"],
        "convergence_rhat_max":max_rhat,
        "convergence_ess_bulk_min":min_bulk,
        "x_mean_mid_q90_width":float(qmu[1,0]-qmu[0,0]),
        "y_mean_mid_q90_width":float(qmu[1,1]-qmu[0,1]),
        "xy_crosscov_mid_q90_width":float(qcross[1]-qcross[0]),
        "x_mean_mid_90_covered":bool(qmu[0,0]<=true_mean[mid,0]<=qmu[1,0]),
        "y_mean_mid_90_covered":bool(qmu[0,1]<=true_mean[mid,1]<=qmu[1,1]),
        "xy_crosscov_mid_90_covered":bool(
            qcross[0]<=true_cov[mid,len(grid)+mid]<=qcross[1]),
        "xy_crosscov_mid_absolute_error":float(
            abs(cross_draws.mean()-true_cov[mid,len(grid)+mid])),
        "population_joint_covariance_psd_draws":bool(all(
            np.linalg.eigvalsh(c).min()>-1e-8 for c in
            fit.joint_population_covariance_draws.reshape(-1,2*len(grid),2*len(grid)))),
        "new_participant_pointwise_90_included":int(included.sum()),
        "new_participant_evaluation_rows":int(len(included)),
        "new_participant_average_pointwise_inclusion":float(included.mean()),
        "new_participant_all_points_within_marginal_bands":bool(included.all()),
        "new_participant_evaluation_heldout":True,
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
    parser.add_argument("--master-seed",type=int,default=306700)
    parser.add_argument("--shard-id",type=int,default=0)
    parser.add_argument("--draws",type=int,default=35)
    parser.add_argument("--warmup",type=int,default=60)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    if args.replicates<2 or args.draws<20 or args.warmup<20:
        raise ValueError("at least 2 replicates, 20 retained draws and 20 warmup sweeps")
    records=[]
    for rank in (1,2):
        for asynchronous in (False,True):
            for iteration in range(args.replicates):
                seed=calibration_replicate_seed("B7",master_seed=args.master_seed,
                    shard_id=args.shard_id,
                    scenario=f"rank{rank}_async{int(asynchronous)}",replicate=iteration)
                record=dict(rank=rank,asynchronous=asynchronous,
                            shard_id=args.shard_id,
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
            "new_participant_all_pointwise_bands":_coverage(
                good,"new_participant_all_points_within_marginal_bands"),
            "new_participant_mean_pointwise_fraction":(
                float(good.new_participant_average_pointwise_inclusion.mean())
                if len(good) else None),
        })
    evidence={
        "programme":"B7_planar_shared_factor_learned_population_prior_truth",
        "actual_native_learned_Gibbs_refit_each_case":True,
        "paired_and_asynchronous_observations":True,
        "rank1_and_rank2":True,
        "population_joint_xy_covariance_learned":True,
        "full_rank_based_SBC_qualified":False,
        "heldout_new_participant_predictions_included":True,
        "heldout_truth_not_in_training":True,
        "posterior_population_and_shared_new_scores_propagated":True,
        "heldout_pointwise_fraction_not_binomial_independent_points":True,
        "all_pointwise_bands_not_a_simultaneous_credible_band":True,
        "predictive_calibration_qualified":False,
        "scientific_coverage_qualified":False,
        "individual_eigenfunctions_identified":False,
        "residual_serial_or_cross_channel_noise_learned":False,
        "publication_authorized":False,
        "attempts":len(frame),"failed":int((frame.status=="failed").sum()),
        "master_seed":args.master_seed,"shard_id":args.shard_id,
        "scenarios":scenarios,
    }
    args.out.mkdir(parents=True,exist_ok=True)
    cases=args.out/"cases.csv"
    source=args.out/"evidence.json"
    frame.to_csv(cases,index=False)
    (args.out/"manifest.json").write_text(json.dumps(calibration_manifest(
        "B7",master_seed=args.master_seed,shard_id=args.shard_id,
        records_per_scenario=args.replicates,case_files=("cases.csv",)),
        indent=2,sort_keys=True)+"\n")
    source.write_text(json.dumps(evidence,indent=2,sort_keys=True)+"\n")
    (args.out/"sha256.txt").write_text(
        sha256(cases.read_bytes()).hexdigest()+"  cases.csv\n"+
        sha256(source.read_bytes()).hexdigest()+"  evidence.json\n"+
        sha256((args.out/"manifest.json").read_bytes()).hexdigest()+"  manifest.json\n")
    print(json.dumps(evidence,sort_keys=True,indent=2))


if __name__=="__main__":
    main()
