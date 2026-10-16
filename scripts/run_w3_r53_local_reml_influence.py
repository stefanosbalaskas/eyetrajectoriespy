"""W3 R53: local observed-Gaussian REML nuisance influence on CR2 pivot.

Research only. At an INTERIOR, numerically accepted local four-component
Gaussian REML solution theta_hat(y), derive:
    score_k = .5(tr(P K_k)-y'P K_k P y)
    H_kl = -.5 tr(P K_l P K_k)
           + (K_l P y)' P (K_k P y)
    ∂theta_hat/∂y = H^{-1} [P K_k P y]_(k rows)
for frozen weighted native design Z, Gaussian variance kernels K, and REML
residual projection P=V^{-1}-V^{-1}Z(Z'V^{-1}Z)^{-1}Z'V^{-1}.
All y in these expressions are weighted, y_w = sqrt(w)*y.

With CR2 squared contrast SE q=sum_i(h_i(theta)'y_w)^2:
  ∂_y q |theta = 2 sum_i(h_i'y_w) h_i;
  total ∇_y q = partial_y q + (partial_theta q) @ ∂theta/∂y.
The CR2 theta-partial is independently finite-differenced using original
R22 scaled-Cholesky at fixed observed y. Point numerator derivative is the
exact WLS contrast linear form. Therefore the first-order local derivative
of T=(point - source_truth)/sqrt(q) can be predicted at this OBSERVED y.

Validate observed theta, squared CR2 SE, and studentized point perturbations
against actual TWO-START REML re-fits on symmetric pseudo-y perturbations.
All refusals, active-box/bad-Hessian cases and mismatches are scientific
outcomes, not eligible to be relabeled as estimator qualification.

This is an implicit local derivative of an INTERIOR REML stationary point,
NOT the joint finite-sample sampling distribution, not nuisance-adjusted CR2
coverage, not a global optimum proof, and NOT an empirical supported API.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np
from scipy.linalg import block_diag, cho_factor, cho_solve

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts import run_w3_r17_fresh_feasibility as fresh
from scripts import run_w3_r48_independent_fitted_cr2 as r48
from scripts import run_w3_r49_nuisance_refit_bootstrap_t as r49
from scripts import run_w3_r52_gaussian_cr2_joint_law as r52
from scripts.w3_r20_estimated_working_target import COMPONENTS
from scripts.w3_r25_gaussian_reml_components import prepare_reml_design

STUDY="W3_R53_INTERIOR_REML_LOCAL_NUISANCE_CR2_PIVOT_INFLUENCE"
SOURCE_SEED=202610175353
DIRECTION_SEED=202610175354
BLOCKS=4
PARTICIPANTS=24
SUPPORT=("ordinary_dependent","extreme_dependent")
DIRECTIONS=3
N_SOURCE=BLOCKS*len(SUPPORT)
N_DIRECTION=N_SOURCE*DIRECTIONS
N_PERTURBED_FITS=N_DIRECTION*2
N_TOTAL_FITS=N_SOURCE+N_PERTURBED_FITS
N_SOLVER_STARTS=N_TOTAL_FITS*len(r49.START_RATIOS)
KKT_LIMIT=.001
EIGEN_CONDITION_LIMIT=1e9
INTERIOR_BOX_MULTIPLIER=20.
PARTIAL_THETA_RELATIVE_STEP=2e-4
RESPONSE_STEP_FRACTION=.003
MAX_HESSIAN_SCORE_FD_REL_ERROR=.03
MAX_PARTIAL_CR2_FD_SPREAD=.1


def source(block,support):
    if type(block) is not int or block not in range(BLOCKS) or support not in SUPPORT:
        raise ValueError("R53 outside preregistered independent Gaussian primitives")
    return fresh.fresh_source(
        block,support,n=PARTICIPANTS,
        master_seed=SOURCE_SEED,n_blocks=BLOCKS,max_n=PARTICIPANTS,
    )


def problem(block,support):
    s=source(block,support)
    X,y,w,g,t,tr,x,c,truth,raw=r48.native_data(s)
    return {
        "X":X,"y":y,"w":w,"group":g,"time":t,"trial":tr,"x":x,
        "contrast":c,"truth":float(truth),"raw_truth":float(raw),
    }


def _sym(x):
    x=np.asarray(x,float)
    return .5*(x+x.T)


def weighted_matrices(data,theta):
    """Actual observable-only REML kernels and fixed weighted design."""
    X,y,w,g,t,tr,x=(data[k] for k in
        ("X","y","w","group","time","trial","x"))
    prep=prepare_reml_design(X,y,w,g,t,tr,x,slope=r49.SLOPE_FAMILY)
    Z=X*np.sqrt(w)[:,None]
    yw=y*np.sqrt(w)
    K=[block_diag(*[item[2][k] for item in prep])
       for k in range(len(COMPONENTS))]
    V=_sym(sum(float(theta[k])*K[k] for k in range(len(K))))
    if not np.isfinite(V).all():
        raise ValueError("R53 Gaussian covariance not finite")
    fac=cho_factor(V,lower=True,check_finite=False)
    invV=cho_solve(fac,np.eye(len(yw)),check_finite=False)
    W=invV@Z
    G=Z.T@W
    C=np.linalg.solve(G,np.eye(G.shape[0]))
    P=_sym(invV-W@C@W.T)
    if np.linalg.norm(P@Z)>1e-5*max(1,np.linalg.norm(Z)):
        raise ValueError("R53 restricted projection violates P Z=0")
    return {
        "Z":Z,"yw":yw,"K":K,"V":V,"P":P,
        "groups":np.unique(g),
    }


def score_hessian(data,theta):
    """Independent direct matrix REML score/Hessian derivation in PHYSICAL theta.

    Score is derivative of negative restricted loglik. This does not use
    optimizer gradients and can be tested against original analytical score.
    """
    m=weighted_matrices(data,theta)
    P=m["P"];K=m["K"];py=P@m["yw"]
    PK=[P@k for k in K]
    KP_y=[k@py for k in K]
    score=np.array([
        .5*(np.trace(PK[k])-py@K[k]@py)
        for k in range(len(K))
    ])
    Hessian=np.zeros((len(K),len(K)))
    for k in range(len(K)):
        for j in range(len(K)):
            Hessian[k,j]=(
                -.5*np.trace(PK[j]@PK[k])
                +KP_y[j]@P@KP_y[k]
            )
    Hessian=_sym(Hessian)
    By=np.stack([P@v for v in KP_y])
    return m,score,Hessian,By


def covariance_blocks(data,theta):
    m=prepare_reml_design(
        data["X"],data["y"],data["w"],data["group"],data["time"],
        data["trial"],data["x"],slope=r49.SLOPE_FAMILY)
    blocks=[]
    for _,_,K in m:
        V=_sym(sum(float(theta[k])*K[k] for k in range(len(K))))
        np.linalg.cholesky(V)
        blocks.append(V)
    return blocks


def cr2(data,theta):
    return r49.cr2_on(data,covariance_blocks(data,theta))


def gradient_of_CR2_variance(data,theta,original_q):
    """Finite differences only for partial_theta(q) at FIXED y.

    Does not alter Gaussian likelihood or nuisance estimator.
    """
    partial=[]
    records=[]
    for j,v in enumerate(theta):
        step=PARTIAL_THETA_RELATIVE_STEP*float(v)
        if v-step<=0:
            raise ValueError("R53 theta derivative approaches zero variance")
        v1=np.array(theta,float);v2=np.array(theta,float)
        v1[j]+=step;v2[j]-=step
        q1=cr2(data,v1)["cr2_se"]**2
        q2=cr2(data,v2)["cr2_se"]**2
        grad=float((q1-q2)/(2*step))
        if not np.isfinite(grad):
            raise ValueError("R53 nonfinite partial CR2 q/partial theta")
        partial.append(grad)
        records.append({
            "component":COMPONENTS[j],
            "physical_theta":float(v),
            "central_difference_step":float(step),
            "q_at_plus":float(q1),
            "q_at_minus":float(q2),
            "dq_dtheta":grad,
            "original_squared_CR2_SE":float(original_q),
        })
    return np.asarray(partial,float),records


def local_influence(data,fit):
    if fit["status"]!="accepted":
        return {"status":"refused","reason":"original_REML_numerical_refusal"}
    theta=np.array([fit["components"][k] for k in COMPONENTS],float)
    ratios=theta/fit["reference_variance"]
    if np.any(ratios<r49.BOUND_LOW*INTERIOR_BOX_MULTIPLIER) or np.any(
        ratios>r49.BOUND_HIGH/INTERIOR_BOX_MULTIPLIER
    ):
        return {"status":"refused","reason":"noninterior_variance_component",
                "ratios":ratios.tolist()}
    try:
        m,score,H,By=score_hessian(data,theta)
        eig=np.linalg.eigvalsh(H)
        if eig.min()<=0 or eig.max()/eig.min()>EIGEN_CONDITION_LIMIT:
            return {
                "status":"refused","reason":"nonpositive_or_illconditioned_REML_observed_Hessian",
                "hessian_eigenvalues":[float(v) for v in eig],
            }
        if fit["physical_projected_KKT"]>KKT_LIMIT:
            return {"status":"refused","reason":"physical_REML_KKT_failed"}
        jac_theta=np.linalg.solve(H,By)
        original=cr2(data,theta)
        q=float(original["cr2_se"]**2)
        # h_i(y,theta) from the SAME original R22 adjustment, source
        # Gaussian oracle NOT needed to derive h_i at a working theta.
        _,_,linear=r52.joint_geometry(
            data["X"],data["w"],data["group"],data["contrast"],
            covariance_blocks(data,theta),covariance_blocks(data,theta))
        h=linear["score_rows"]
        yw=m["yw"]
        q_direct=float(np.linalg.norm(h@yw)**2)
        if not np.isclose(q,q_direct,atol=1e-9,rtol=3e-7):
            raise ValueError("R53 original CR2 q != linear score quadratic")
        partial_y=2*h.T@(h@yw)
        partial_theta,steps=gradient_of_CR2_variance(data,theta,q)
        total_y=partial_y+partial_theta@jac_theta
        Z=m["Z"]
        bc=np.linalg.solve(Z.T@Z,data["contrast"])
        numerator_gradient=Z@bc
        numerator=float(original["point"]-data["truth"])
        studentized_grad=(
            numerator_gradient/np.sqrt(q)
            -numerator*total_y/(2*q**1.5))
        # Hessian from score derivatives, distinct from Gaussian expected
        # information. Can be indefinite in finite samples: refuse rather
        # than silently inverting or regularizing.
        return {
            "status":"ok",
            "theta":[float(v) for v in theta],
            "ratios":[float(v) for v in ratios],
            "raw_negative_REML_score":[float(v) for v in score],
            "maximum_absolute_score":float(np.max(abs(score))),
            "observed_hessian_eigenvalues":[float(v) for v in eig],
            "hessian_condition":float(eig.max()/eig.min()),
            "jacobian_theta_wrt_weighted_y":jac_theta,
            "CR2_q":q,
            "CR2_focal_point":float(original["point"]),
            "CR2_numerator":numerator,
            "CR2_pivot":float(numerator/np.sqrt(q)),
            "CR2_partial_y_gradient":partial_y,
            "CR2_total_y_gradient":total_y,
            "CR2_partial_theta_gradient":partial_theta,
            "theta_derivative_component_checks":steps,
            "studentized_total_y_gradient":studentized_grad,
            "local_influence_not_full_sampling_law":True,
        }
    except Exception as exc:
        return {"status":"refused","reason":"algebra_or_numerical_exception",
                "exception":repr(exc)[:350]}


def perturb_record(label):
    return {
        "label":label,"status":"not_attempted","reason":None,
        "direction_seed":None,"weighted_y_perturbation_step":None,
        "numerical_plus":None,"numerical_minus":None,
        "theta_implicit_direction":None,
        "theta_refit_centered_direction":None,
        "theta_direction_relative_difference":None,
        "CR2_q_implicit_direction":None,
        "CR2_q_refit_centered_direction":None,
        "pivot_implicit_direction":None,
        "pivot_refit_centered_direction":None,
        "pivot_absolute_derivative_error":None,
    }


def evaluate(block,support):
    row={
        "study":STUDY,"block":block,"support":support,
        "original_status":"source_failed","original_error":None,
        "original_nuisance":None,
        "influence_status":"not_attempted","influence":None,
        "perturbations":[],"release_authorized":False,
    }
    data=None
    try:
        data=problem(block,support)
        row["original_status"]="ok"
        row["projected_truth"]=float(data["truth"])
    except Exception as exc:
        row["original_error"]=repr(exc)[:350]
    fit=None
    if data is not None:
        fit=r49.fit_nuisance(data)
        row["original_nuisance"]={k:v for k,v in fit.items()
                                  if k!="working_blocks"}
    else:
        row["original_nuisance"]={
            "status":"not_attempted",
            "numerical_starts":[{"label":name,"status":"not_attempted"}
                                for name,_ in r49.START_RATIOS],
        }
    influence=local_influence(data,fit) if fit is not None else {
        "status":"refused","reason":"original_source_unavailable"}
    row["influence_status"]=influence["status"]
    # Never serialize full huge analytic derivative Jacobian. Project to
    # frozen Gaussian random response directions and retain summaries.
    row["influence"]={
        k:v for k,v in influence.items() if k not in (
            "jacobian_theta_wrt_weighted_y",
            "CR2_partial_y_gradient","CR2_total_y_gradient",
            "studentized_total_y_gradient",
        )
    }
    for direction in range(DIRECTIONS):
        item=perturb_record(direction)
        if influence["status"]=="ok":
            try:
                seed=DIRECTION_SEED+100003*block+711*SUPPORT.index(support)+direction
                rng=np.random.default_rng(seed)
                d=rng.standard_normal(size=len(data["y"]))
                d=d/(np.linalg.norm(d)/np.sqrt(len(d)))
                W=np.sqrt(data["w"])
                base=np.mean((W*data["y"])**2)**.5
                h=RESPONSE_STEP_FRACTION*max(base,.01)
                item["direction_seed"]=seed
                item["weighted_y_perturbation_step"]=float(h)
                plus={**data,"y":data["y"]+h*d/W}
                minus={**data,"y":data["y"]-h*d/W}
                a=r49.fit_nuisance(plus)
                b=r49.fit_nuisance(minus)
                item["numerical_plus"]={
                    k:v for k,v in a.items() if k!="working_blocks"}
                item["numerical_minus"]={
                    k:v for k,v in b.items() if k!="working_blocks"}
                if a["status"]!="accepted" or b["status"]!="accepted":
                    raise ValueError("R53 direct perturbation REML refit refused")
                ap=np.array([a["components"][c] for c in COMPONENTS])
                bp=np.array([b["components"][c] for c in COMPONENTS])
                theta_emp=(ap-bp)/(2*h)
                theta_predict=influence[
                    "jacobian_theta_wrt_weighted_y"]@d
                qa=float(r49.cr2_on(plus,a["working_blocks"])["cr2_se"]**2)
                qb=float(r49.cr2_on(minus,b["working_blocks"])["cr2_se"]**2)
                pa=float(r49.cr2_on(plus,a["working_blocks"])["point"])
                pb=float(r49.cr2_on(minus,b["working_blocks"])["point"])
                t_a=(pa-data["truth"])/np.sqrt(qa)
                t_b=(pb-data["truth"])/np.sqrt(qb)
                q_emp=(qa-qb)/(2*h)
                t_emp=(t_a-t_b)/(2*h)
                q_pred=float(influence["CR2_total_y_gradient"]@d)
                t_pred=float(influence["studentized_total_y_gradient"]@d)
                theta_rel=float(
                    np.linalg.norm(theta_emp-theta_predict)/
                    max(np.linalg.norm(theta_emp),np.linalg.norm(theta_predict),1e-9))
                item.update({
                    "status":"ok",
                    "theta_implicit_direction":theta_predict.tolist(),
                    "theta_refit_centered_direction":theta_emp.tolist(),
                    "theta_direction_relative_difference":theta_rel,
                    "CR2_q_implicit_direction":q_pred,
                    "CR2_q_refit_centered_direction":float(q_emp),
                    "pivot_implicit_direction":t_pred,
                    "pivot_refit_centered_direction":float(t_emp),
                    "pivot_absolute_derivative_error":float(abs(t_pred-t_emp)),
                })
            except Exception as exc:
                item["status"]="refused"
                item["reason"]=repr(exc)[:350]
        row["perturbations"].append(item)
    return row


def summary(rows):
    universe={(b,s) for b in range(BLOCKS) for s in SUPPORT}
    keys=[(r["block"],r["support"]) for r in rows]
    if len(keys)!=len(set(keys)) or not set(keys).issubset(universe):
        raise ValueError("R53 duplicate or unregistered primitive case")
    if any(len(r["perturbations"])!=DIRECTIONS or
           tuple(v["label"] for v in r["perturbations"])!=tuple(range(DIRECTIONS))
           or len(r["original_nuisance"]["numerical_starts"])!=2
           or any(v["numerical_plus"] is not None and
                  len(v["numerical_plus"]["numerical_starts"])!=2
                  for v in r["perturbations"])
           or any(v["numerical_minus"] is not None and
                  len(v["numerical_minus"]["numerical_starts"])!=2
                  for v in r["perturbations"])
           for r in rows):
        raise ValueError("R53 incomplete perturbation/numerical start slots")
    perturb=[v for r in rows for v in r["perturbations"]]
    completed=sum(
        1 for r in rows for x in r["perturbations"]
        for name in ("numerical_plus","numerical_minus")
        if x[name] is not None)
    declared=sum(
        2 for r in rows if r["original_nuisance"] is not None
    )+sum(2 for r in rows for x in r["perturbations"]
          for name in ("numerical_plus","numerical_minus")
          if x[name] is not None)
    stats={}
    for support in SUPPORT:
        rr=[r for r in rows if r["support"]==support]
        p=[v for r in rr for v in r["perturbations"]]
        good=[v for v in p if v["status"]=="ok"]
        stats[support]={
            "independent_primitive_blocks":BLOCKS,
            "source_cases_recorded":len(rr),
            "observed_nuisance_accepted":sum(
                r["original_nuisance"]["status"]=="accepted" for r in rr),
            "local_influence_accepted":sum(
                r["influence_status"]=="ok" for r in rr),
            "local_influence_refused":sum(
                r["influence_status"]=="refused" for r in rr),
            "perturbation_successes":len(good),
            "perturbation_refusals":sum(v["status"]=="refused" for v in p),
            "perturbation_not_attempted":sum(
                v["status"]=="not_attempted" for v in p),
            "median_theta_relative_derivative_discrepancy":(
                float(np.median([v["theta_direction_relative_difference"]
                                 for v in good])) if good else None),
            "median_studentized_absolute_derivative_discrepancy":(
                float(np.median([v["pivot_absolute_derivative_error"]
                                 for v in good])) if good else None),
        }
    return {
        "study":STUDY,"new_independent_source_seed":SOURCE_SEED,
        "independent_response_direction_seed":DIRECTION_SEED,
        "new_independent_primitive_blocks":BLOCKS,
        "paired_leverage_support_not_independent_sources":True,
        "n_participants_per_primitive":PARTICIPANTS,
        "declared_perturb_directions_per_case":DIRECTIONS,
        "planned_original_source_cases":N_SOURCE,
        "recorded_original_source_cases":len(rows),
        "planned_response_perturbation_records":N_DIRECTION,
        "recorded_response_perturbation_records":len(perturb),
        "planned_plus_minus_refit_attempt_slots":N_PERTURBED_FITS,
        "recorded_plus_minus_fit_attempts":completed,
        "planned_total_REML_fit_attempt_slots":N_TOTAL_FITS,
        "planned_two_start_optimizer_outcome_slots":N_SOLVER_STARTS,
        "recorded_executed_two_start_optimizer_outcomes":declared,
        "complete_structural_source_and_perturbation_denominator":(
            len(rows)==N_SOURCE and len(perturb)==N_DIRECTION),
        "analytic_local_REML_Hessian_score_and_response_Jacobian":True,
        "physical_box_or_bad_Hessian_refused_not_regularized":True,
        "no_global_REML_optimum_proof":True,
        "local_influence_not_complete_sampling_distribution":True,
        "no_90pct_pointwise_coverage_qualification":True,
        "no_simultaneous_90pct_whole_function_bands":True,
        "no_random_slope_boundary_null_qualification":True,
        "no_MNAR_or_whole_participant_selection_identification":True,
        "release_authorized":False,
        "strata":stats,
    }


def _json_plain(value):
    """Convert numeric numpy array/scalar evidence to JSON without data loss.

    This is serialization ONLY; it does not change the original Gaussian
    source, fitted REML solution, derivative, CR2 pivot or refusal policy.
    allow_nan=False remains mandatory to refuse invalid numerical output.
    """
    if isinstance(value,np.ndarray):
        return [_json_plain(x) for x in value.tolist()]
    if isinstance(value,np.generic):
        return _json_plain(value.item())
    if isinstance(value,dict):
        return {k:_json_plain(v) for k,v in value.items()}
    if isinstance(value,(tuple,list)):
        return [_json_plain(x) for x in value]
    return value


def _write(path,x):
    path.write_text(json.dumps(
        _json_plain(x),sort_keys=True,indent=2,allow_nan=False)+"\n")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    cases=[evaluate(b,s) for b in range(BLOCKS) for s in SUPPORT]
    report=summary(cases)
    _write(args.out/"cases.json",cases)
    _write(args.out/"summary.json",report)
    (args.out/"source-commit.txt").write_text(
        os.environ.get("GITHUB_SHA","unverified-local")+"\n")
    files=("cases.json","summary.json","source-commit.txt")
    (args.out/"SHA256SUMS").write_text("".join(
        hashlib.sha256((args.out/f).read_bytes()).hexdigest()+"  "+f+"\n"
        for f in files))
    print("R53 local Gaussian nuisance influence:",json.dumps(report,sort_keys=True))
    if not report["complete_structural_source_and_perturbation_denominator"]:
        raise SystemExit("R53 source/perturbation records missing")


if __name__=="__main__":
    main()
