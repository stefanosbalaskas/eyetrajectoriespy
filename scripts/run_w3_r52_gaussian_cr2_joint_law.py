"""R52 research: finite Gaussian CR2 studentization via exact joint covariance.

Under a *fixed* native design, fixed true Gaussian error covariance V, and
fixed CR2 working target Phi, the focal WLS coefficient error N=u'e and
adjusted participant residual scores S_i=h_i'e are jointly centered Gaussian
with deterministically computable covariance Omega. The CR2 pivot is
N / ||S||, and its reference law can be numerically sampled directly from
Omega, with NO bootstrap nuisance refit, no new synthetic observed responses,
and no assumption that N is independent of S.

For an oracle FIXED target Phi=V this is the Gaussian finite-design pivot
law up to explicit Monte Carlo quantile error (and the fixed-mean model).
For Phi estimated from the observed y and then FROZEN, the law is a
COUNTERFACTUAL frozen-working-target geometry diagnostic, NOT the sampling
law of the actual estimated-covariance CR2 statistic; conditioning on a
function of y changes the distribution. This study is research-only,
neither nuisance-estimation-aware CR2 nor nominal-90%-qualified inference.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np
from scipy.stats import binom, t as student_t

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts import run_w3_r17_fresh_feasibility as fresh
from scripts import run_w3_r48_independent_fitted_cr2 as r48
from scripts import run_w3_r49_nuisance_refit_bootstrap_t as r49
from scripts.w3_r22_scaled_cholesky_cr2 import (
    scaled_symmetric_adjustment,stable_cr2_blockwise_wls,
)

STUDY="W3_R52_FIXED_GAUSSIAN_CR2_JOINT_NUMERATOR_SCORE_REFERENCE"
MASTER_SEED=202610165252
MC_SEED=202610165253
BLOCKS=4
PARTICIPANTS=24
SUPPORT=("ordinary_dependent","extreme_dependent")
TARGETS=("known_generating_covariance","estimated_REML_frozen_working_covariance")
REFERENCES=("joint_Gaussian_exact_geometry_MC","independent_numerator_counterfactual_MC")
N_MC=16384
NOMINAL=.90
EXPECTED_SOURCE=BLOCKS*len(SUPPORT)
EXPECTED_TARGET=EXPECTED_SOURCE*len(TARGETS)
EXPECTED_CRITICAL=EXPECTED_TARGET*len(REFERENCES)


def _sym(a):
    return (np.asarray(a,float)+np.asarray(a,float).T)*.5


def source(block,support):
    if type(block) is not int or block not in range(BLOCKS) or support not in SUPPORT:
        raise ValueError("R52 unregistered primitive Gaussian source")
    return fresh.fresh_source(
        block,support,n=PARTICIPANTS,master_seed=MASTER_SEED,
        n_blocks=BLOCKS,max_n=PARTICIPANTS,
    )


def native_problem(block,support):
    s=source(block,support)
    X,y,w,g,t,tr,x,c,truth,raw=r48.native_data(s)
    true_cov=r48.r32.known_gaussian_blocks(
        g,t,tr,x,w,r49.SLOPE_FAMILY)
    return {"X":X,"y":y,"w":w,"group":g,"time":t,"trial":tr,
            "x":x,"contrast":c,"truth":truth,"raw_truth":raw,
            "true_covariance":true_cov}


def joint_geometry(X,weights,group,contrast,true_blocks,working_blocks):
    """Independent algebraic reconstruction of Gaussian CR2 pivot geometry.

    WLS beta contrast error is u'epsilon, u=Z (Z'Z)^-1 contrast.
    For each CR2 participant adjusted score g_i' residual_i:
        h_i = pad_i(g_i) - Z (Z'Z)^-1 Z_i' g_i
        g_i=A_i Z_i (Z'Z)^-1 contrast,
    where A_i D_i A_i' = working-Phi_i, as in original R22.
    Therefore Omega=Cov([u'eps,h_1'eps,...,h_G'eps]) is determined
    by original TRUE block covariance, without fitting any simulated y.
    """
    X=np.asarray(X,float);w=np.asarray(weights,float)
    group=np.asarray(group);c=np.asarray(contrast,float)
    if X.ndim!=2 or np.any(~np.isfinite(X)) or np.any(w<=0):
        raise ValueError("R52 invalid fixed Gaussian design")
    n,p=X.shape
    if w.shape!=(n,) or c.shape!=(p,) or group.shape!=(n,):
        raise ValueError("R52 WLS design dimensions inconsistent")
    groups=np.unique(group)
    m=len(groups)
    if len(true_blocks)!=m or len(working_blocks)!=m:
        raise ValueError("R52 Gaussian covariance group-block mismatch")
    Z=X*np.sqrt(w)[:,None]
    gram=Z.T@Z
    inv=np.linalg.solve(gram,np.eye(p))
    bc=inv@c
    u=Z@bc
    ix=[np.flatnonzero(group==v) for v in groups]
    for indices,V,Phi in zip(ix,true_blocks,working_blocks):
        if (np.asarray(V).shape!=(len(indices),len(indices))
                or np.asarray(Phi).shape!=(len(indices),len(indices))):
            raise ValueError("R52 native participant Gaussian covariance dimension mismatch")
        np.linalg.cholesky(_sym(V))
        np.linalg.cholesky(_sym(Phi))

    M=np.zeros((p,p),float)
    for indices,Phi in zip(ix,working_blocks):
        Zi=Z[indices]
        M+=Zi.T@Phi@Zi
    Hscores=[]
    adjustments=[]
    for indices,Phi in zip(ix,working_blocks):
        Zi=Z[indices]
        H=Zi@inv@Zi.T
        D=_sym(Phi-H@Phi-Phi@H+Zi@inv@M@inv@Zi.T)
        A,check=scaled_symmetric_adjustment(Phi,D)
        adjustments.append(check)
        gi=A@(Zi@bc)
        # Score_i = h_i' epsilon; h is in observed weighted native rows.
        h=np.zeros(n)
        h[indices]=gi
        h-=Z@(inv@(Zi.T@gi))
        Hscores.append(h)
    Hscores=np.stack(Hscores)
    Omega=np.zeros((m+1,m+1),float)
    # Original generating covariance, NEVER fitted target, determines the law.
    for indices,V in zip(ix,true_blocks):
        T=np.vstack([u[indices],Hscores[:,indices]])
        Omega+=T@V@T.T
    Omega=_sym(Omega)
    eigen,U=np.linalg.eigh(Omega)
    if not np.isfinite(eigen).all():
        raise ValueError("R52 nonfinite Gaussian joint covariance eigenvalues")
    scale=max(abs(eigen).max(),np.finfo(float).tiny)
    if eigen.min() < -1e-9*scale:
        raise ValueError("R52 non-PSD Gaussian joint covariance")
    clipped=np.maximum(eigen,0.)
    if clipped[-1]<=0 or np.trace(Omega[1:,1:])<=0 or Omega[0,0]<=0:
        raise ValueError("R52 degenerate focal Gaussian covariance")
    sigma=Omega[1:,1:]
    moments={
        "true_numerator_variance":float(Omega[0,0]),
        "expected_CR2_squared_SE":float(np.trace(sigma)),
        "variance_CR2_squared_SE":float(2*np.sum(sigma*sigma)),
        "score_effective_df_from_true_covariance":float(
            np.trace(sigma)**2/np.sum(sigma*sigma)),
        "max_absolute_numerator_score_correlation":float(np.max(
            np.abs(Omega[0,1:])/
            np.sqrt(Omega[0,0]*np.diag(sigma)))),
        "mean_squared_cross_covariance":float(np.mean(Omega[0,1:]**2)),
        "number_of_clusters":m,
        "minimum_joint_covariance_eigenvalue":float(eigen.min()),
        "max_adjustment_identity_error":float(max(
            item["relative_identity_error"] for item in adjustments)),
        "maximum_conditioned_adjustment_product":float(max(
            item["normalized_product_condition"] for item in adjustments)),
        "nuisance_target_treated_fixed":True,
        "true_covariance_used_for_reference_only":True,
    }
    return Omega,moments,{"u":u,"score_rows":Hscores}


def _mc_quantiles(Omega,*,seed,n=N_MC):
    """Gaussian pivot quantiles with independent- vs correlated-numerator arms.

    Both arms reuse one IID draw matrix; only numerator-score cross
    covariance is set to zero for the counterfactual independence arm.
    The order-statistic 95% confidence bounds quantify MC quantile error.
    """
    O=_sym(Omega)
    if O.shape[0]<3 or n<100 or O[0,0]<=0:
        raise ValueError("R52 invalid exact-law Gaussian Monte Carlo request")
    z=np.random.default_rng(seed).standard_normal((n,O.shape[0]))
    quantiles=[]
    for name,copy in (
        (REFERENCES[0],O),
        (REFERENCES[1],np.block([
            [O[:1,:1],np.zeros_like(O[:1,1:])],
            [np.zeros_like(O[1:,:1]),O[1:,1:]],
        ])),
    ):
        eig,Q=np.linalg.eigh(_sym(copy))
        scale=max(abs(eig).max(),np.finfo(float).tiny)
        if eig.min()<-1e-9*scale:
            raise ValueError("R52 non-PSD Gaussian pivot moment matrix")
        B=(Q*np.sqrt(np.maximum(eig,0.)))@Q.T
        draws=z@B
        denominator=np.linalg.norm(draws[:,1:],axis=1)
        if not np.isfinite(denominator).all() or np.any(denominator<=0):
            raise ValueError("R52 Gaussian score norm zero/nonfinite")
        pivots=np.abs(draws[:,0])/denominator
        if not np.isfinite(pivots).all():
            raise ValueError("R52 nonfinite studentized Gaussian exact-law pivots")
        ordered=np.sort(pivots)
        low=int(max(0,binom.ppf(.025,n,NOMINAL)-1))
        high=int(min(n-1,binom.ppf(.975,n,NOMINAL)))
        q=float(np.quantile(pivots,NOMINAL,method="linear"))
        quantiles.append({
            "reference":name,"status":"ok",
            "absolute_studentized_critical_q90":q,
            "iid_normal_draws":n,
            "MC_order_statistic_95pct_limits":[
                float(ordered[low]),float(ordered[high])],
            "numerator_score_dependence_preserved":name==REFERENCES[0],
            "oracle_generating_covariance_needed":True,
            "fitted_target_sampling_variability_included":False,
        })
    return quantiles


def refuse(target,reason):
    return {"target":target,"status":"refused",
            "reason":str(reason)[:350],
            "critical_records":[
                {"reference":ref,"status":"refused"}
                for ref in REFERENCES]}


def evaluate(block,support):
    row={
        "study":STUDY,"block":block,"support":support,
        "source_status":"failed","source_error":None,
        "source_new_independent_primitive_unit":True,
        "fitted_nuisance_status":"not_attempted",
        "fitted_nuisance_diagnostics":None,
        "targets":[],"release_authorized":False,
    }
    try:
        data=native_problem(block,support)
        row["source_status"]="ok"
        row["projected_true_focal_slope"]=float(data["truth"])
        row["projection_minus_raw_truth"]=float(
            data["truth"]-data["raw_truth"])
    except Exception as exc:
        row["source_error"]=repr(exc)[:350]
        row["targets"]=[refuse(t,row["source_error"]) for t in TARGETS]
        return row
    fit=r49.fit_nuisance(
        {k:v for k,v in data.items() if k!="true_covariance"})
    row["fitted_nuisance_status"]=fit["status"]
    row["fitted_nuisance_diagnostics"]={
        k:v for k,v in fit.items() if k!="working_blocks"}
    for j,target in enumerate(TARGETS):
        if j==1 and fit["status"]!="accepted":
            row["targets"].append(refuse(target,"strict physical REML nuisance refusal"))
            continue
        try:
            working=(data["true_covariance"] if j==0
                     else fit["working_blocks"])
            cov,m,lin=joint_geometry(
                data["X"],data["w"],data["group"],data["contrast"],
                data["true_covariance"],working)
            original=stable_cr2_blockwise_wls(
                data["X"],data["y"],data["w"],data["group"],
                data["contrast"],working)
            # Oracle target matches source covariance: independent
            # CR2 implementation's conditional moments must match exactly.
            if j==0:
                if not np.isclose(
                    original["conditional_expectation"],
                    m["expected_CR2_squared_SE"],rtol=3e-7,atol=3e-9):
                    raise ValueError("R52 oracle quadratic moment disagrees with R22")
                if not np.isclose(
                    original["satterthwaite_df"],
                    m["score_effective_df_from_true_covariance"],
                    rtol=3e-7,atol=3e-9):
                    raise ValueError("R52 oracle Satterthwaite df differs from Gaussian score spectrum")
            q=_mc_quantiles(
                cov,seed=MC_SEED+100003*block+711*SUPPORT.index(support)
                +29*j)
            reference_t=float(student_t.ppf(
                .95,original["satterthwaite_df"]))
            if not np.isfinite(reference_t):
                raise ValueError("R52 conditional t reference not finite")
            row["targets"].append({
                "target":target,"status":"accepted",
                "true_Gaussian_linear_numerator_and_quadratic_score":True,
                "source_oracle_not_empirically_available":True,
                "original_conditional_satterthwaite_df":float(
                    original["satterthwaite_df"]),
                "original_conditional_Satterthwaite_t_critical":reference_t,
                "original_focal_point":float(original["point"]),
                "original_cr2_se":float(original["cr2_se"]),
                "source_Gaussian_joint_covariance":m,
                "critical_records":q,
                "joint_q_over_conditional_t":float(
                    q[0]["absolute_studentized_critical_q90"]/reference_t),
                "joint_q_over_independent_numerator_q":float(
                    q[0]["absolute_studentized_critical_q90"]/
                    q[1]["absolute_studentized_critical_q90"]),
                "fitted_working_target_is_random_in_real_sampling":j==1,
                "fitted_target_sampling_variability_included":False,
                "reported_as_inferentially_valid":False,
            })
        except Exception as exc:
            row["targets"].append(refuse(target,repr(exc)))
    return row


def summarize(rows):
    ids=[(r["block"],r["support"]) for r in rows]
    expected={(b,s) for b in range(BLOCKS) for s in SUPPORT}
    if len(ids)!=len(set(ids)) or not set(ids).issubset(expected):
        raise ValueError("R52 duplicated/unregistered independent primitive block")
    if any(tuple(t["target"] for t in row["targets"])!=TARGETS or any(
        tuple(x["reference"] for x in t["critical_records"])!=REFERENCES
        for t in row["targets"]) for row in rows):
        raise ValueError("R52 missing original target/quantile/refusal slots")
    targets=[t for row in rows for t in row["targets"]]
    critical=[v for t in targets for v in t["critical_records"]]
    results={}
    for support in SUPPORT:
        source=[r for r in rows if r["support"]==support]
        result={}
        for target in TARGETS:
            completed=[t for row in source for t in row["targets"]
                       if t["target"]==target]
            ok=[t for t in completed if t["status"]=="accepted"]
            result[target]={
                "source_blocks_planned":BLOCKS,
                "recorded":len(completed),"accepted":len(ok),
                "refused":len(completed)-len(ok),
                "median_joint_exact_Gaussian_q_over_conditional_t":(
                    float(np.median([t["joint_q_over_conditional_t"] for t in ok]))
                    if ok else None),
                "median_joint_exact_q_over_independent_numerator":(
                    float(np.median([t["joint_q_over_independent_numerator_q"] for t in ok]))
                    if ok else None),
                "median_max_numerator_score_correlation":(
                    float(np.median([
                        t["source_Gaussian_joint_covariance"][
                            "max_absolute_numerator_score_correlation"]
                        for t in ok]))
                    if ok else None),
                "median_satterthwaite_df":(
                    float(np.median([
                        t["original_conditional_satterthwaite_df"] for t in ok]))
                    if ok else None),
                "all_exactness_claims_only_fixed_targets":True,
            }
        results[support]=result
    return {
        "study":STUDY,"new_source_seed":MASTER_SEED,
        "Gaussian_numerical_reference_seed":MC_SEED,
        "fresh_independent_primitive_blocks":BLOCKS,
        "paired_leverage_states_not_independent":True,
        "total_monte_carlo_reference_draws_per_target":N_MC,
        "planned_source_cases":EXPECTED_SOURCE,
        "recorded_source_cases":len(rows),
        "planned_covariance_targets":EXPECTED_TARGET,
        "recorded_covariance_targets":len(targets),
        "planned_critical_records":EXPECTED_CRITICAL,
        "recorded_critical_records":len(critical),
        "complete_failure_inclusive_evidence":(
            len(rows)==EXPECTED_SOURCE and
            len(targets)==EXPECTED_TARGET and
            len(critical)==EXPECTED_CRITICAL),
        "strata":results,
        "analytic_Gaussian_score_numerator_joint_covariance":True,
        "oracle_reference_requires_unavailable_true_covariance":True,
        "estimated_target_held_fixed_is_counterfactual_not_true_conditional_distribution":True,
        "nuisance_estimation_sampling_uncertainty_NOT_included":True,
        "no_90pct_pointwise_coverage_qualification":True,
        "no_90pct_whole_function_band":True,
        "no_random_slope_boundary_test_calibration":True,
        "no_MNAR_or_lost_participant_identification":True,
        "release_authorized":False,
    }


def _write(path,value):
    path.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+"\n")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    cases=[evaluate(b,s) for b in range(BLOCKS) for s in SUPPORT]
    report=summarize(cases)
    _write(args.out/"cases.json",cases)
    _write(args.out/"summary.json",report)
    (args.out/"source-commit.txt").write_text(
        os.environ.get("GITHUB_SHA","unverified-local")+"\n")
    filenames=("cases.json","summary.json","source-commit.txt")
    (args.out/"SHA256SUMS").write_text("".join(
        hashlib.sha256((args.out/f).read_bytes()).hexdigest()+"  "+f+"\n"
        for f in filenames))
    print("R52 Gaussian joint-law reference:",json.dumps(report,sort_keys=True))
    if not report["complete_failure_inclusive_evidence"]:
        raise SystemExit("R52 refused incomplete original Gaussian reference accounting")


if __name__=="__main__":
    main()
