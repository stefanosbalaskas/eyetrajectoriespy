"""Independent PyMC/NUTS marginal-likelihood posterior reference for B6/B7.

Reference mathematical model, *not* a wrap around native Gibbs conditionals.
Native Gibbs and PyMC/NUTS receive exactly the same native irregular data,
noise, rank, dictionary and priors. Participant scores are analytically
integrated only in the independent NUTS likelihood. No sampler qualification,
rank SBC, cross-system equivalence or production release is asserted.
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

from eyetrajectoriespy.bayesian.sparse_factor_gibbs import (
    _spline_basis,fit_bayesian_sparse_fpca)
from eyetrajectoriespy.bayesian.planar_factor_gibbs import fit_bayesian_planar_factor
from eyetrajectoriespy.types import IrregularTrajectorySet
from scripts.run_b6_population_calibration_grid import (
    _known_truth as generate_B6_truth,GRID as B6_GRID,
    MEAN_PRIOR_SD,N_BASIS,
)
from eyetrajectoriespy.research.calibration_seed import calibration_replicate_seed


def _planar_data(seed:int,async_channels:bool):
    rng=np.random.default_rng(seed)
    grid=np.linspace(0,1,23)
    n,q,k=18,5,1
    mean_sd,load_sd=.45,.20
    noise=(.04,.06)
    mu=rng.normal(0,mean_sd,(2,q))
    load=rng.normal(0,load_sd,(2,q,k))
    times=[];values=[]
    for i in range(n):
        tx=np.sort(rng.uniform(.01,.99,12+i%3))
        ty=np.sort(rng.uniform(.01,.99,11+i%4)) if async_channels else tx.copy()
        z=rng.normal(size=k)
        x=_spline_basis(tx,0,1,q)@(mu[0]+load[0]@z)+rng.normal(0,noise[0],len(tx))
        y=_spline_basis(ty,0,1,q)@(mu[1]+load[1]@z)+rng.normal(0,noise[1],len(ty))
        if async_channels:
            t=np.sort(np.r_[tx,ty])
            v=np.full((len(t),2),np.nan)
            v[np.searchsorted(t,tx),0]=x
            v[np.searchsorted(t,ty),1]=y
        else:
            t=tx;v=np.column_stack((x,y))
        times.append(t);values.append(v)
    gaze=IrregularTrajectorySet(
        time=tuple(times),values=tuple(values),
        curve_ids=tuple(f"P{i}" for i in range(n)),
        dimension_names=("x","y"),coordinate_system="normalized",time_unit="s",
        metadata=pd.DataFrame({"participant_id":[f"P{i}" for i in range(n)]}),
        provenance={"synthetic_exact_prior_likelihood":True})
    basis=_spline_basis(grid,0,1,q)
    projected=np.concatenate((basis@load[0],basis@load[1]),axis=0)
    return gaze,grid,tuple(noise),basis@mu.T,projected@projected.T


def _summarize_posterior(a:np.ndarray,b:np.ndarray,truth:float, label:str)->dict:
    """Compare fully independent flattened posterior distributions."""
    left=np.asarray(a).reshape(-1)
    right=np.asarray(b).reshape(-1)
    if not np.isfinite(left).all() or not np.isfinite(right).all():
        raise ValueError("invalid reference posterior samples")
    q1=np.quantile(left,[.05,.95]);q2=np.quantile(right,[.05,.95])
    return {
        "quantity":label,"known_prior_truth":float(truth),
        "native_mean":float(left.mean()),"reference_mean":float(right.mean()),
        "native_sd":float(left.std(ddof=1)),"reference_sd":float(right.std(ddof=1)),
        "mean_difference_in_reference_sd":float((left.mean()-right.mean())/
                                              max(right.std(ddof=1),1.e-12)),
        "native_q05_q95":[float(x) for x in q1],
        "reference_q05_q95":[float(x) for x in q2],
        "native_90_covers_truth":bool(q1[0]<=truth<=q1[1]),
        "reference_90_covers_truth":bool(q2[0]<=truth<=q2[1]),
        "intervals_overlap":bool(q1[0]<=q2[1] and q2[0]<=q1[1]),
        "scientifically_qualified":False,
    }


def _identified_chain_diagnostics(draws:np.ndarray)->dict:
    """Rank Rhat, bulk/tail ESS and MCSE of an invariant scalar functional.

    This is the only correct level for evaluating rank-1 covariance
    functionals when loading signs are not identified. Raw loading
    Rhat remains separately available and is never silently ignored.
    """
    import arviz as az
    a=np.asarray(draws,dtype=float)
    if a.ndim!=2 or a.shape[0]<2 or a.shape[1]<20 or not np.isfinite(a).all():
        raise ValueError("need >=2 finite chains with >=20 draws for diagnostics")
    fields={
        "rank_rhat":float(np.asarray(az.rhat(a,method="rank"))),
        "bulk_ess":float(np.asarray(az.ess(a,method="bulk"))),
        "tail_ess":float(np.asarray(az.ess(a,method="tail"))),
        "mcse_mean":float(np.asarray(az.mcse(a,method="mean"))),
    }
    if not all(np.isfinite(v) and v>=0 for v in fields.values()):
        raise ValueError("invalid identifiable population diagnostic")
    return fields


def _pymc_marginal(gaze:IrregularTrajectorySet,*,dimensions:tuple[str,...],
                   noise_sd:tuple[float,...],q:int,k:int,
                   mean_sd:float,load_sd:float,
                   draws:int,warmup:int,random_state:int):
    """PyMC posterior using independently derived observation marginal density.

    Integration over z_i is done via the determinant lemma and a small
    k x k precision matrix. This target has only mu and L; NUTS does
    not share native Gibbs conditional code, random streams or z states.
    """
    try:
        import pymc as pm
        import pytensor.tensor as pt
    except ImportError as exc:
        raise ImportError("requires optional [bayesian-pymc] install") from exc
    if k!=1:
        raise ValueError("independent reference currently supports rank 1 only")
    d=len(dimensions)
    col=[gaze.dimension_names.index(c) for c in dimensions]
    G=np.empty((gaze.n_curves,d,q,q),float)
    C=np.empty((gaze.n_curves,d,q),float)
    Ysq=np.empty((gaze.n_curves,d),float)
    Nobs=np.empty((gaze.n_curves,d),int)
    for i,(t,v) in enumerate(zip(gaze.time,gaze.values,strict=True)):
        for axis in range(d):
            y=np.asarray(v[:,col[axis]],float)
            mask=np.isfinite(y)
            B=_spline_basis(np.asarray(t)[mask],0.,1.,q)
            yy=y[mask]
            G[i,axis]=B.T@B
            C[i,axis]=B.T@yy
            Ysq[i,axis]=float(yy@yy)
            Nobs[i,axis]=len(yy)

    # Fully vectorized rank-one determinant-lemma Gaussian log likelihood.
    # The design uses a single symbolic graph with bounded operation count
    # regardless of the number of participants. No unrolled 18-term Add
    # chain, preventing the observed PyTensor Scratchpad.ufunc fusion error.
    #
    # NUTS only sees (mu, L). Scores z_i are integrated in p(Y_i|mu,L):
    # Q_i = 1 + sum_d inv_sigma_d² L_d.T G_di L_d
    # v_i = sum_d inv_sigma_d² L_d.T(c_di-G_di mu_d)
    # residual quadratic - v_i²/Q_i + log(Q_i) + log|sigma²I|.
    inv=np.asarray([1./z**2 for z in noise_sd],float)
    noise_logdet=np.sum(
        Nobs*np.log(np.square(np.asarray(noise_sd,float)))[None,:],
        axis=1,
    )
    with pm.Model() as model:
        mean=pm.Normal("mean",mu=0,sigma=mean_sd,shape=(d,q))
        load=pm.Normal("load",mu=0,sigma=load_sd,shape=(d,q,k))
        L=load[:,:,0]
        Gt=pt.as_tensor_variable(G)
        Ct=pt.as_tensor_variable(C)
        ysq_t=pt.as_tensor_variable(Ysq)
        inv_t=pt.as_tensor_variable(inv)
        log_noise=pt.as_tensor_variable(noise_logdet)

        Gmu=pt.sum(Gt*mean[None,:,None,:],axis=3)
        GL=pt.sum(Gt*L[None,:,None,:],axis=3)
        residual=ysq_t-2*pt.sum(Ct*mean[None,:,:],axis=2)
        residual=residual+pt.sum(mean[None,:,:]*Gmu,axis=2)
        weighted=pt.sum(inv_t[None,:]*residual,axis=1)
        Q=1+pt.sum(inv_t[None,:]*pt.sum(L[None,:,:]*GL,axis=2),axis=1)
        v=pt.sum(inv_t[None,:]*pt.sum(
            L[None,:,:]*(Ct-Gmu),axis=2),axis=1)
        marginal_ll=-.5*pt.sum(weighted-v*v/Q+pt.log(Q)+log_noise)
        pm.Potential("known_noise_marginal_loglik",marginal_ll)
        inference=pm.sample(
            draws=draws,tune=warmup,chains=2,cores=2,random_seed=random_state,
            target_accept=.94,progressbar=False,compute_convergence_checks=True,
            return_inferencedata=True)

    return inference


def execute(*,replicates:int=2,nuts_draws:int=350,
            nuts_warmup:int=650,gibbs_draws:int=450,
            gibbs_warmup:int=850,master_seed:int=20261127):
    if replicates<1 or min(nuts_draws,nuts_warmup,gibbs_draws,gibbs_warmup)<50:
        raise ValueError("require >=1 dataset and >=50 warmup/draws")
    import arviz as az
    rows=[]
    for design in ("B6_rank1","B7_rank1_paired","B7_rank1_asynchronous"):
        for replicate in range(replicates):
            seed=calibration_replicate_seed(
                "B6_B7_INDEPENDENT_PYMC_NUTS_REFERENCE",
                master_seed=master_seed,shard_id=0,
                scenario=design,replicate=replicate)
            row={"design":design,"replicate":replicate,"seed":seed,
                 "status":"failed","error_type":None,"error":None}
            try:
                if design=="B6_rank1":
                    gaze,truth_mean,truth_cov,_,_=generate_B6_truth(seed,"matched_rank1")
                    grid=B6_GRID
                    dimensions=("x",)
                    noise=(.05,)
                    native=fit_bayesian_sparse_fpca(
                        gaze,dimension="x",evaluation_grid=grid,
                        n_basis=N_BASIS,n_components=1,
                        noise_sd=noise[0],
                        mean_prior_sd=MEAN_PRIOR_SD,loading_prior_sd=.2,
                        collapsed_population_mean_update=True,
                        n_chains=2,n_draws=gibbs_draws,warmup=gibbs_warmup,
                        thin=1,random_state=seed+937)
                    center_mu=native.population_mean_draws[:,:,len(grid)//2]
                    center_cov=native.population_covariance_draws[:,:,
                                          len(grid)//2,len(grid)//2]
                    truth_mu=float(truth_mean[len(grid)//2])
                    truth_cv=float(truth_cov[len(grid)//2,len(grid)//2])
                    priormu=MEAN_PRIOR_SD
                else:
                    async_ch=design.endswith("asynchronous")
                    gaze,grid,noise,truth_mean,truth_cov=_planar_data(seed,async_ch)
                    dimensions=("x","y")
                    native=fit_bayesian_planar_factor(
                        gaze,dimensions=dimensions,evaluation_grid=grid,
                        observation_noise_sd=noise,n_basis=5,n_components=1,
                        mean_prior_sd=.45,loading_prior_sd=.2,
                        collapsed_population_mean_update=True,
                        n_chains=2,n_draws=gibbs_draws,warmup=gibbs_warmup,
                        thin=1,random_state=seed+109)
                    mid=len(grid)//2
                    center_mu=native.population_mean_draws[:,:,mid,0]
                    center_cov=native.joint_population_covariance_draws[
                        :,:,mid,len(grid)+mid]
                    truth_mu=float(truth_mean[mid,0])
                    truth_cv=float(truth_cov[mid,len(grid)+mid])
                    priormu=.45
                idata=_pymc_marginal(
                    gaze,dimensions=dimensions,noise_sd=noise,q=5,k=1,
                    mean_sd=priormu,load_sd=.2,draws=nuts_draws,
                    warmup=nuts_warmup,random_state=seed+201)
                m=np.asarray(idata.posterior["mean"])
                L=np.asarray(idata.posterior["load"])
                basis=_spline_basis(grid,0,1,5)
                at=basis[len(grid)//2]
                marginal_mu=np.einsum("q,cdq->cd",at,m[:,:,0,:])
                if len(dimensions)==1:
                    projected=np.einsum("q,cdq->cd",at,L[:,:,0,:,0])
                    marginal_cv=projected**2
                else:
                    x=np.einsum("q,cdq->cd",at,L[:,:,0,:,0])
                    y=np.einsum("q,cdq->cd",at,L[:,:,1,:,0])
                    marginal_cv=x*y
                summary=[
                    _summarize_posterior(center_mu,marginal_mu,truth_mu,"x_mid_population_mean"),
                    _summarize_posterior(center_cov,marginal_cv,truth_cv,
                         "x_mid_covariance" if len(dimensions)==1 else "mid_xy_crosscovariance")
                ]
                # Diagnostic chain arrays are specifically the *identifiable*
                # mean and covariance functionals, not sign-switching L.
                invariant_diagnostics={}
                for name,native_values,reference_values in (
                    ("x_mid_population_mean",center_mu,marginal_mu),
                    ("x_mid_covariance" if len(dimensions)==1
                     else "mid_xy_crosscovariance",center_cov,marginal_cv),
                ):
                    native_diag=_identified_chain_diagnostics(native_values)
                    reference_diag=_identified_chain_diagnostics(reference_values)
                    mean_difference=float(np.mean(native_values)-np.mean(reference_values))
                    combined_mcse=float(np.hypot(
                        native_diag["mcse_mean"],reference_diag["mcse_mean"]))
                    invariant_diagnostics[name]={
                        "native":native_diag,"independent_nuts":reference_diag,
                        "native_minus_reference_mean":mean_difference,
                        "mean_discrepancy_to_combined_mcse":(
                            mean_difference/combined_mcse
                            if combined_mcse>0 else None),
                        "both_chain_mixing_diagnostics_acceptable":(
                            native_diag["rank_rhat"]<=1.01 and
                            reference_diag["rank_rhat"]<=1.01 and
                            native_diag["bulk_ess"]>=400 and
                            reference_diag["bulk_ess"]>=400),
                        "scientific_qualified":False,
                    }
                mu_diag=az.rhat(idata,var_names=["mean"])
                L_diag=az.rhat(idata,var_names=["load"])
                native_frame=native.diagnostics_frame()
                row.update(
                    status="ok",
                    conditional_nuts_marginal_population_comparison=summary,
                    rotation_invariant_population_chain_diagnostics=invariant_diagnostics,
                    rank1_loading_sign_nonidentifiability_preserved=True,
                    native_rhat_max=float(native_frame.rhat_max.max()),
                    native_bulk_ess_min=float(native_frame.ess_bulk_min.min()),
                    nuts_max_parameter_rhat=float(max(
                        np.asarray(mu_diag["mean"]).max(),
                        np.asarray(L_diag["load"]).max())),
                    nuts_mean_ess_min=float(np.asarray(
                        az.ess(idata,var_names=["mean"])["mean"]).min()),
                    nuts_divergences=int(np.asarray(
                        idata.sample_stats["diverging"]).sum()),
                    nuts_draws_per_chain=nuts_draws,
                    nuts_warmup=nuts_warmup,
                    gibbs_draws_per_chain=gibbs_draws,
                    gibbs_warmup=gibbs_warmup,
                    independent_reference_validity_qualified=False,
                    posterior_coverage_qualified=False)
            except Exception as exc:
                row["error_type"]=type(exc).__name__
                row["error"]=str(exc)[:700]
            rows.append(row)
    frame=pd.DataFrame(rows)
    evidence={
        "programme":"Independent_PyMC_NUTS_score_marginalized_posterior_reference",
        "model":"fixed_dictionary_Gaussian_rank1_mean_loading_known_noise",
        "independent_NUTS_backend":"PyMC_automatic_differentiation",
        "independently_implemented_marginal_loglik_using_determinant_lemma":True,
        "comparison_native_sampler":"exact_partially_collapsed_B6_B7_Gibbs",
        "identical_prior_generated_native_irregular_data_per_pair":True,
        "source_master_seed":master_seed,
        "independent_datasets_per_scenario":replicates,
        "attempts":len(frame),
        "failed_attempts":int(frame.status.eq("failed").sum()),
        "no_automatic_qualifications":True,
        "native_inference_qualified":False,
        "NUTS_reference_convergence_qualified":False,
        "rank_SBC_completed":False,
        "posterior_coverage_qualified":False,
        "publication_authorized":False,
        "release_authorized":False,
        "case_results":rows,
    }
    return frame,evidence


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--replicates",type=int,default=2)
    ap.add_argument("--nuts-draws",type=int,default=350)
    ap.add_argument("--nuts-warmup",type=int,default=650)
    ap.add_argument("--gibbs-draws",type=int,default=450)
    ap.add_argument("--gibbs-warmup",type=int,default=850)
    ap.add_argument("--master-seed",type=int,default=20261127)
    ap.add_argument("--out",required=True,type=Path)
    a=ap.parse_args()
    frame,ev=execute(replicates=a.replicates,
         nuts_draws=a.nuts_draws,nuts_warmup=a.nuts_warmup,
         gibbs_draws=a.gibbs_draws,gibbs_warmup=a.gibbs_warmup,
         master_seed=a.master_seed)
    a.out.mkdir(parents=True,exist_ok=True)
    p=a.out/"cases.json";e=a.out/"evidence.json"
    p.write_text(json.dumps(ev["case_results"],indent=2,sort_keys=True)+"\n")
    e.write_text(json.dumps(ev,indent=2,sort_keys=True)+"\n")
    (a.out/"sha256.txt").write_text(
        sha256(p.read_bytes()).hexdigest()+"  cases.json\n"+
        sha256(e.read_bytes()).hexdigest()+"  evidence.json\n")
    print(json.dumps({"attempts":len(frame),"failed":ev["failed_attempts"],
                      "scientifically_qualified":False,
                      "results":ev["case_results"]},sort_keys=True))


if __name__=="__main__":
    main()
