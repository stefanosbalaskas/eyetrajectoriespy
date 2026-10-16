"""R54: constrained REML active-face influence, reusing R53 Gaussian sources.

Scientific diagnostic only. R53 found that 4/8 accepted REML nuisance fits
hit the *positive ratio* lower box bound for participant slope. R54 retains
those original source identities: it does NOT treat them as new independent
Gaussian replications or silently relax the R53 smooth-interior rule.

The r49 objective uses absolute physical covariance theta=reference(y)*ratio,
with each ratio constrained [LOW,HIGH]. Thus active physical theta_a(y) =
bound_ratio_a * reference(y); active physical theta cannot be held constant
during response perturbations.

At a strictly complementary active face, stationarity for the free
components gives
 H_ff dtheta_f = B_f dy - H_fa dtheta_a
 dtheta_a = bound_ratio_a * d(reference)/dy .
For original WLS raw residual r=diag(1/sqrt(w)) (I-H_Z) y_w,
 d(reference)/dy_w = 2/n * (I-H_Z) diag(1/w) (I-H_Z) y_w,
since reference=mean(r**2), away from its separate 1e-8 floor.
That constrained Jacobian enters the SAME R22 CR2 quadratic score and focal
studentized response derivative as R53.

The reduced Hessian must be SPD/well conditioned, free ratios far from box,
and signed active KKT gradients must exceed an a priori strict margin.
Every original and +/- fit and every active-set switch is retained. A
successful local derivative is not a coverage or variance-boundary-null test.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts import run_w3_r49_nuisance_refit_bootstrap_t as r49
from scripts import run_w3_r53_local_reml_influence as r53
from scripts import run_w3_r52_gaussian_cr2_joint_law as r52
from scripts.w3_r20_estimated_working_target import COMPONENTS

STUDY="W3_R54_R53_SOURCE_REPLAY_ACTIVE_FACE_REML_RESPONSE_INFLUENCE"
SOURCE_SEED=r53.SOURCE_SEED  # INTENTIONALLY same primitive blocks; no new-source claim
DIRECTION_SEED=202610175454
BLOCKS=r53.BLOCKS
PARTICIPANTS=r53.PARTICIPANTS
SUPPORT=r53.SUPPORT
DIRECTIONS=2
RESPONSE_STEP_FRACTION=.0005
REFERENCE_FLOOR=1e-8
ACTIVE_RATIO_RTOL=1e-5
STRICT_DIMENSIONLESS_KKT_MARGIN=.001
FREE_INTERIOR_BOX_MULTIPLIER=20.
FREE_HESSIAN_CONDITION_LIMIT=1e9
N_SOURCE=BLOCKS*len(SUPPORT)
N_DIRECTION=N_SOURCE*DIRECTIONS
N_REFIT_SLOTS=2*N_DIRECTION
N_REML_FIT_SLOTS=N_SOURCE+N_REFIT_SLOTS
N_START_SLOTS=2*N_REML_FIT_SLOTS


def original_data(block,support):
    return r53.problem(block,support)


def reference_and_gradient(data):
    """EXACT differential of R49's *unweighted-residual RMS²* reference.

    The derivative is expressed with respect to the weighted response y_w.
    No source Gaussian oracle or generating variance is used.
    """
    X,y,w=(np.asarray(data[z],float) for z in ("X","y","w"))
    Z=X*np.sqrt(w)[:,None]
    yw=y*np.sqrt(w)
    beta=np.linalg.lstsq(Z,yw,rcond=None)[0]
    weighted_residual=yw-Z@beta
    residual=weighted_residual/np.sqrt(w)
    raw_ref=float(np.mean(residual*residual))
    reference=max(raw_ref,REFERENCE_FLOOR)
    H=Z@np.linalg.solve(Z.T@Z,Z.T)
    residual_projector=np.eye(len(y))-H
    grad=(2/len(y))*residual_projector@(weighted_residual/w)
    if raw_ref<REFERENCE_FLOOR:
        grad=np.zeros_like(grad)
    if not np.isfinite(grad).all():
        raise ValueError("R54 nonfinite moving-bound reference derivative")
    return reference,grad,float(raw_ref)


def active_signature(fit):
    if fit.get("status")!="accepted":
        return None
    ref=float(fit["reference_variance"])
    ratios=np.array([fit["components"][k]/ref for k in COMPONENTS])
    active_low=tuple(int(i) for i,x in enumerate(ratios)
                     if abs(x-r49.BOUND_LOW)<=ACTIVE_RATIO_RTOL*r49.BOUND_LOW)
    active_high=tuple(int(i) for i,x in enumerate(ratios)
                      if abs(x-r49.BOUND_HIGH)<=ACTIVE_RATIO_RTOL*r49.BOUND_HIGH)
    if set(active_low)&set(active_high):
        raise ValueError("R54 same component on lower and upper face")
    return active_low,active_high


def local_active_face(data,fit):
    """Reduced Gaussian REML implicit derivative on one fixed active face."""
    if fit.get("status")!="accepted":
        return {"status":"refused","reason":"original_nuisance_numerical_refusal"}
    try:
        ref,dref,raw=reference_and_gradient(data)
        if not np.isclose(ref,fit["reference_variance"],atol=1e-11,rtol=1e-7):
            raise ValueError("reference variance does not match original R49 fit")
        if raw<=1.1*REFERENCE_FLOOR:
            return {"status":"refused","reason":"reference_scale_floor_nondifferentiable"}
        theta=np.array([fit["components"][k] for k in COMPONENTS],float)
        ratios=theta/ref
        low,high=active_signature(fit)
        active=tuple(sorted(low+high))
        free=tuple(i for i in range(len(theta)) if i not in active)
        if not free:
            return {"status":"refused","reason":"no_free_covariance_components"}
        if any(ratios[i]<=FREE_INTERIOR_BOX_MULTIPLIER*r49.BOUND_LOW
               or ratios[i]>=r49.BOUND_HIGH/FREE_INTERIOR_BOX_MULTIPLIER
               for i in free):
            return {"status":"refused","reason":"free_variance_component_near_box"}
        m,s,H,B=r53.score_hessian(data,theta)
        gradient_ratio=s*ref
        signed={
            COMPONENTS[i]:float(gradient_ratio[i]) for i in active
        }
        if any(gradient_ratio[i] < STRICT_DIMENSIONLESS_KKT_MARGIN for i in low):
            return {"status":"refused","reason":"lower_active_KKT_not_strict",
                    "active_low":low,"active_high":high,"signed_KKT":signed}
        if any(gradient_ratio[i] > -STRICT_DIMENSIONLESS_KKT_MARGIN for i in high):
            return {"status":"refused","reason":"upper_active_KKT_not_strict",
                    "active_low":low,"active_high":high,"signed_KKT":signed}
        Hff=H[np.ix_(free,free)]
        eig=np.linalg.eigvalsh(Hff)
        if eig.min()<=0 or eig.max()/eig.min()>FREE_HESSIAN_CONDITION_LIMIT:
            return {"status":"refused","reason":"reduced_free_Hessian_not_SPD",
                    "active_low":low,"active_high":high,
                    "free_hessian_eigenvalues":eig.tolist()}
        J=np.zeros((len(theta),len(data["y"])))
        for i in low:
            J[i]=r49.BOUND_LOW*dref
        for i in high:
            J[i]=r49.BOUND_HIGH*dref
        adjustment=B[list(free)].copy()
        if active:
            adjustment-=H[np.ix_(free,active)]@J[list(active)]
        J[list(free)]=np.linalg.solve(Hff,adjustment)

        base=r53.cr2(data,theta)
        q=float(base["cr2_se"]**2)
        blocks=r53.covariance_blocks(data,theta)
        _,_,lin=r52.joint_geometry(
            data["X"],data["w"],data["group"],data["contrast"],
            blocks,blocks)
        h=lin["score_rows"]
        yw=m["yw"]
        if not np.isclose(np.sum((h@yw)**2),q,rtol=3e-7,atol=1e-9):
            raise ValueError("R54 CR2 original quadratic score mismatch")
        dq_fixed=2*h.T@(h@yw)
        dq_theta,steps=r53.gradient_of_CR2_variance(data,theta,q)
        dq_total=dq_fixed+dq_theta@J
        u=m["Z"]@np.linalg.solve(m["Z"].T@m["Z"],data["contrast"])
        focal=float(base["point"]-data["truth"])
        derivative_pivot=u/np.sqrt(q)-focal*dq_total/(2*q**1.5)
        if not np.isfinite(J).all() or not np.isfinite(derivative_pivot).all():
            raise ValueError("R54 nonfinite active-face derivative")
        return {
            "status":"ok","reason":None,
            "active_low":low,"active_high":high,"free_components":free,
            "ratios":ratios.tolist(),"signed_KKT":signed,
            "reference_variance":ref,"reference_raw":raw,
            "reference_response_gradient":dref,
            "theta":theta,"theta_response_jacobian":J,
            "free_Hessian_eigenvalues":eig.tolist(),
            "reduced_Hessian_condition":float(eig.max()/eig.min()),
            "original_q":q,
            "original_studentized_pivot":float(focal/np.sqrt(q)),
            "CR2_q_total_response_gradient":dq_total,
            "CR2_pivot_total_response_gradient":derivative_pivot,
            "CR2_partial_theta_steps":steps,
            "moving_active_bound_explicit":True,
            "strict_active_set_required":True,
            "smooth_fixed_face_only_not_global":True,
        }
    except Exception as exc:
        return {"status":"refused","reason":"algebra_numerical_exception",
                "error":repr(exc)[:320]}


def direction_record(index):
    return {
        "index":index,"status":"not_attempted","reason":None,
        "seed":None,"weighted_step":None,
        "plus_fit":None,"minus_fit":None,
        "plus_signature":None,"minus_signature":None,
        "predicted_nuisance_derivative":None,
        "observed_nuisance_derivative":None,
        "relative_nuisance_derivative_error":None,
        "predicted_pivot_derivative":None,
        "observed_pivot_derivative":None,
        "absolute_pivot_derivative_error":None,
    }


def evaluate(block,support):
    case={
        "study":STUDY,"block":block,"support":support,
        "reuses_original_R53_source":True,
        "source_status":"failed","source_error":None,
        "original_fit":None,
        "active_face":None,"directions":[],
        "release_authorized":False,
    }
    data=None
    try:
        data=original_data(block,support)
        case["source_status"]="ok"
        case["projected_true_focal"]=data["truth"]
    except Exception as exc:
        case["source_error"]=repr(exc)[:330]
    if data is not None:
        fit=r49.fit_nuisance(data)
        case["original_fit"]={k:v for k,v in fit.items() if k!="working_blocks"}
        local=local_active_face(data,fit)
    else:
        case["original_fit"]={
            "status":"not_attempted",
            "numerical_starts":[{"label":s,"status":"not_attempted"}
                                for s,_ in r49.START_RATIOS],
        }
        local={"status":"refused","reason":"source_generation_failure"}
    case["active_face"]={
        k:r53._json_plain(v) for k,v in local.items()
        if k not in (
            "reference_response_gradient","theta_response_jacobian",
            "CR2_q_total_response_gradient",
            "CR2_pivot_total_response_gradient",
        )
    }
    for direction in range(DIRECTIONS):
        drec=direction_record(direction)
        if local["status"]=="ok":
            try:
                seed=(DIRECTION_SEED+100003*block
                      +711*SUPPORT.index(support)+direction)
                rng=np.random.default_rng(seed)
                v=rng.standard_normal(len(data["y"]))
                v/=np.linalg.norm(v)/np.sqrt(len(v))
                rootw=np.sqrt(data["w"])
                step=RESPONSE_STEP_FRACTION*max(
                    np.sqrt(np.mean((data["y"]*rootw)**2)),.01)
                plus={**data,"y":data["y"]+step*v/rootw}
                minus={**data,"y":data["y"]-step*v/rootw}
                aa=r49.fit_nuisance(plus)
                bb=r49.fit_nuisance(minus)
                drec["seed"]=seed
                drec["weighted_step"]=float(step)
                drec["plus_fit"]={k:x for k,x in aa.items() if k!="working_blocks"}
                drec["minus_fit"]={k:x for k,x in bb.items() if k!="working_blocks"}
                if aa["status"]!="accepted" or bb["status"]!="accepted":
                    drec["status"]="refused"
                    drec["reason"]="one_or_both_perturbed_REML_fit_refused"
                else:
                    original_signature=active_signature(fit)
                    drec["plus_signature"]=active_signature(aa)
                    drec["minus_signature"]=active_signature(bb)
                    if (drec["plus_signature"]!=original_signature
                            or drec["minus_signature"]!=original_signature):
                        drec["status"]="refused"
                        drec["reason"]="active_face_changed_under_weighted_response_perturbation"
                    else:
                        ta=np.array([aa["components"][k] for k in COMPONENTS])
                        tb=np.array([bb["components"][k] for k in COMPONENTS])
                        empirical=(ta-tb)/(2*step)
                        predicted=local["theta_response_jacobian"]@v
                        qaa=r49.cr2_on(plus,aa["working_blocks"])
                        qbb=r49.cr2_on(minus,bb["working_blocks"])
                        p_plus=(qaa["point"]-data["truth"])/qaa["cr2_se"]
                        p_minus=(qbb["point"]-data["truth"])/qbb["cr2_se"]
                        observed=(p_plus-p_minus)/(2*step)
                        calculated=float(local["CR2_pivot_total_response_gradient"]@v)
                        drec.update({
                            "status":"ok",
                            "predicted_nuisance_derivative":predicted.tolist(),
                            "observed_nuisance_derivative":empirical.tolist(),
                            "relative_nuisance_derivative_error":float(
                                np.linalg.norm(empirical-predicted)/
                                max(np.linalg.norm(empirical),
                                    np.linalg.norm(predicted),1e-9)),
                            "predicted_pivot_derivative":calculated,
                            "observed_pivot_derivative":float(observed),
                            "absolute_pivot_derivative_error":float(
                                abs(observed-calculated)),
                        })
            except Exception as exc:
                drec["status"]="refused"
                drec["reason"]=repr(exc)[:320]
        case["directions"].append(drec)
    return case


def summary(cases):
    pairs=[(c["block"],c["support"]) for c in cases]
    universe={(b,s) for b in range(BLOCKS) for s in SUPPORT}
    if len(pairs)!=len(set(pairs)) or not set(pairs).issubset(universe):
        raise ValueError("R54 unexpected/duplicate source replay identifier")
    for c in cases:
        if (len(c["directions"])!=DIRECTIONS
                or [x["index"] for x in c["directions"]]!=list(range(DIRECTIONS))
                or len(c["original_fit"]["numerical_starts"])!=2):
            raise ValueError("R54 missing original source/refit denominator")
        for d in c["directions"]:
            for f in (d["plus_fit"],d["minus_fit"]):
                if f is not None and len(f["numerical_starts"])!=2:
                    raise ValueError("R54 incomplete perturbed optimizer start outcomes")
    all_d=[d for c in cases for d in c["directions"]]
    actual_refits=sum(
        d[f] is not None for d in all_d for f in ("plus_fit","minus_fit"))
    actual_starts=sum(2 for _ in cases)+2*actual_refits
    by_support={}
    for s in SUPPORT:
        source=[c for c in cases if c["support"]==s]
        stages=[d for c in source for d in c["directions"]]
        ok=[d for d in stages if d["status"]=="ok"]
        by_support[s]={
            "original_sources_recorded":len(source),
            "accepted_original_REML_fits":sum(
                c["original_fit"]["status"]=="accepted" for c in source),
            "accepted_local_active_face_derivatives":sum(
                c["active_face"]["status"]=="ok" for c in source),
            "refused_local_derivatives":sum(
                c["active_face"]["status"]!="ok" for c in source),
            "original_active_lower_slope":sum(
                1 in c["active_face"].get("active_low",()) for c in source),
            "directions_accepted":len(ok),
            "directions_refused":sum(d["status"]=="refused" for d in stages),
            "directions_not_attempted":sum(
                d["status"]=="not_attempted" for d in stages),
            "median_nuisance_relative_derivative_error":(
                float(np.median([d["relative_nuisance_derivative_error"]
                                 for d in ok])) if ok else None),
            "median_pivot_absolute_derivative_error":(
                float(np.median([d["absolute_pivot_derivative_error"]
                                 for d in ok])) if ok else None),
        }
    return {
        "study":STUDY,
        "reused_original_R53_primitive_source_seed":SOURCE_SEED,
        "new_direction_seed":DIRECTION_SEED,
        "independent_primitive_blocks_NOT_new_source":BLOCKS,
        "paired_support_conditions_not_independent":True,
        "planned_replayed_source_cases":N_SOURCE,
        "recorded_source_cases":len(cases),
        "planned_direction_records":N_DIRECTION,
        "recorded_direction_records":len(all_d),
        "planned_plus_minus_refit_slots":N_REFIT_SLOTS,
        "recorded_attempted_plus_minus_refits":actual_refits,
        "planned_original_and_perturbed_REML_fit_slots":N_REML_FIT_SLOTS,
        "planned_optimizer_start_slots":N_START_SLOTS,
        "recorded_attempted_optimizer_starts":actual_starts,
        "full_source_and_direction_denominator_preserved":(
            len(cases)==N_SOURCE and len(all_d)==N_DIRECTION),
        "active_ratio_bound_moves_with_observed_response_reference":True,
        "active_sign_and_free_Hessian_refusals_not_overridden":True,
        "active_set_switch_is_refusal_not_success":True,
        "local_face_differential_not_global_or_full_sampling_law":True,
        "no_nominal_90pct_pointwise_coverage":True,
        "no_90pct_simultaneous_function_bands":True,
        "no_variance_boundary_null_TypeI_or_power_qualification":True,
        "no_MNAR_or_whole_participant_selection_identification":True,
        "release_authorized":False,
        "strata":by_support,
    }


def _write(path,obj):
    path.write_text(json.dumps(
        r53._json_plain(obj),sort_keys=True,indent=2,allow_nan=False)+"\n")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    records=[evaluate(b,s) for b in range(BLOCKS) for s in SUPPORT]
    report=summary(records)
    _write(args.out/"cases.json",records)
    _write(args.out/"summary.json",report)
    (args.out/"source-commit.txt").write_text(
        os.environ.get("GITHUB_SHA","unverified-local")+"\n")
    names=("cases.json","summary.json","source-commit.txt")
    (args.out/"SHA256SUMS").write_text("".join(
        hashlib.sha256((args.out/k).read_bytes()).hexdigest()+"  "+k+"\n"
        for k in names))
    print("R54 constrained Gaussian influence audit:",json.dumps(
        report,sort_keys=True))
    if not report["full_source_and_direction_denominator_preserved"]:
        raise SystemExit("R54 refused incomplete original source/direction ledger")


if __name__=="__main__":
    main()
