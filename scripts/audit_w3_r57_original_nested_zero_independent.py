"""Independent read-only ORIGINAL W3 R57 nested Gaussian REML evidence audit.

NO import of R57 scientific source/optimizer, R35/R37 likelihood or R49
estimator. Audit the ORIGINAL immutable Actions case, summary, source SHA.
Independently reconstruct original physical projected KKT for every retained
numerical optimizer start, exact-null membership, selected best-NLL contract,
raw nested deviance, 32-case paired primitive counts, and reported medians.
This verifies archived numerical EVIDENCE, NOT exact raw Gaussian trajectory
source generation (raw y is absent), a global optimum, a p-value, Type-I
calibration or public inference software.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

SOURCE_CHECKOUT="d120e5f48978dc7a86e6e400ac402dc42d2a3a59"
CASE_SHA="4b0acd21512579513ca904d61d0f74912855807f6ac46e4961af706e30ebc726"
SUMMARY_SHA="0ef577b86ded44343f18e2c345afbbea47e260883a510fd8393490bdfac7ea4b"
SEED=202610175757
SUPPORT=("ordinary_dependent","extreme_dependent")
STATES=("true_zero","true_positive")
EXPECTED={(b,s,v) for b in range(8) for s in SUPPORT for v in STATES}
LOW=float(np.exp(-13.8))
HIGH=float(np.exp(7.))
MAX_SLOPE=100.
KKT_TOL=.001
NLL_TOL=.001
RECON_TOL=1e-6
NESTING_TOL=1e-5


def close(x,y,where,rel=1e-9,absolute=1e-10):
    if not (
        math.isfinite(float(x)) and math.isfinite(float(y))
        and math.isclose(float(x),float(y),rel_tol=rel,abs_tol=absolute)
    ):
        raise ValueError("R57 independent original evidence mismatch: "+where)


def verify_source(folder):
    f=Path(folder)
    names={"cases.json","summary.json","source-commit.txt"}
    rows=(f/"SHA256SUMS").read_text().splitlines()
    if len(rows)!=3:
        raise ValueError("R57 original SHA256 manifest incomplete")
    out={}
    for line in rows:
        h,sep,name=line.partition("  ")
        if not sep or name not in names or name in out or len(h)!=64:
            raise ValueError("R57 invalid original source manifest member")
        actual=hashlib.sha256((f/name).read_bytes()).hexdigest()
        if actual!=h:
            raise ValueError("R57 immutable original source SHA256 mismatch "+name)
        out[name]=actual
    if set(out)!=names or out["cases.json"]!=CASE_SHA or out["summary.json"]!=SUMMARY_SHA:
        raise ValueError("R57 unexpected original numerical source or summary identity")
    if (f/"source-commit.txt").read_text().strip()!=SOURCE_CHECKOUT:
        raise ValueError("R57 source checkout not original Actions PR merge")
    return out


def projected_physical(gradient,ratios,model):
    g=np.asarray(gradient,float)
    x=np.asarray(ratios,float)
    if model=="exact_zero":
        bounds=[(LOW,HIGH)]*3
    elif model=="nonnegative":
        bounds=[(LOW,HIGH)]*3+[(0.,MAX_SLOPE)]
    else:
        raise ValueError("R57 original unknown nested model")
    if g.shape!=(len(bounds),) or x.shape!=g.shape:
        raise ValueError("R57 source physical score shape incorrect")
    if not np.isfinite(g).all() or not np.isfinite(x).all():
        raise ValueError("R57 invalid nonfinite Gaussian score or ratio")
    p=g.copy()
    for i,(a,b) in enumerate(bounds):
        if x[i]<a-1e-9 or x[i]>b+1e-9:
            raise ValueError("R57 original fitted variance violates model bounds")
        if x[i]<=a+1e-9:
            p[i]=min(g[i],0.)
        elif x[i]>=b-1e-9:
            p[i]=max(g[i],0.)
    return float(np.max(np.abs(p)))


def audit_model(fit,model,case_id):
    starts=("null_compact","null_spread") if model=="exact_zero" else (
        "alt_at_exact_zero","alt_tiny_positive","alt_positive","alt_wide")
    if fit["model"]!=model or [v["label"] for v in fit["original_starts"]]!=list(starts):
        raise ValueError("R57 original model start labels or order incorrect "+case_id)
    if fit["status"]!="accepted":
        raise ValueError("R57 original model was refused "+case_id)
    evaluated=[]
    valid=[]
    for stage in fit["original_starts"]:
        nll=stage["negative_loglik"]
        if nll is None:
            continue
        if not math.isfinite(float(nll)):
            raise ValueError("R57 original nonfinite observed Gaussian NLL")
        evaluated.append(stage)
        close(stage["negative_loglik"],stage["reconstructed_loglik"],
              case_id+"/Gaussian objective reconstruction",
              rel=1e-9,absolute=RECON_TOL+1e-10)
        kkt=projected_physical(
            stage["physical_score"],stage["ratios"],model)
        close(kkt,stage["physical_projected_KKT"],
              case_id+"/all-start physical projected KKT",
              rel=5e-7,absolute=2e-7)
        if (stage["optimizer_success"] and
            stage["objective_reconstruction_error"]<=RECON_TOL and
            kkt<=KKT_TOL):
            valid.append(stage)
    if not evaluated:
        raise ValueError("R57 original all Gaussian likelihood candidates failed")
    best=min(v["negative_loglik"] for v in evaluated)
    close(best,fit["best_observed_multistart_NLL"],
          case_id+"/original best observed NLL",absolute=1e-7)
    eligible=[stage for stage in valid if
              stage["negative_loglik"]-best<=NLL_TOL+1e-8]
    selected=[s for s in eligible if s["label"]==fit["selected_start"]]
    if not selected:
        raise ValueError("R57 false acceptance of a source start "+case_id)
    choose=selected[0]
    close(choose["negative_loglik"],fit["selected_NLL"],
          case_id+"/selected candidate NLL",absolute=1e-7)
    close(choose["physical_projected_KKT"],fit["selected_physical_KKT"],
          case_id+"/selected physical KKT",absolute=1e-8)
    close(fit["selected_NLL"],min(s["negative_loglik"] for s in eligible),
          case_id+"/chosen original best accepted NLL",absolute=1e-7)
    if model=="exact_zero":
        if fit["selected_slope_ratio"]!=0.:
            raise ValueError("R57 claimed exact null has nonzero fitted slope")
        if fit["null_includes_exact_zero_variance"] is not True:
            raise ValueError("R57 original exact-zero model renamed")
    else:
        if fit["alternative_includes_structural_zero"] is not True:
            raise ValueError("R57 alternative excluded its nested null")
        close(choose["ratios"][3],fit["selected_slope_ratio"],
              case_id+"/selected physical slope ratio")
        if fit["selected_slope_ratio"]<0:
            raise ValueError("R57 alternative illegally negative random slope")
    np.testing.assert_allclose(
        choose["ratios"][:3],fit["selected_free_component_variance_ratios"],
        rtol=1e-9,atol=1e-10,
        err_msg="R57 original fitted three free nuisance ratios mismatch")
    return {"selected_NLL":float(fit["selected_NLL"]),
            "selected_slope_ratio":float(fit["selected_slope_ratio"]),
            "selected_KKT":float(fit["selected_physical_KKT"]),
            "starts":len(starts)}


def audit(folder):
    digests=verify_source(folder)
    original=json.loads((Path(folder)/"cases.json").read_text())
    summary=json.loads((Path(folder)/"summary.json").read_text())
    ids=[(r["block"],r["support"],r["generating_state"]) for r in original]
    if len(ids)!=32 or set(ids)!=EXPECTED or len(set(ids))!=32:
        raise ValueError("R57 original independent Gaussian block/source identities lost")
    if (summary["master_new_independent_source_seed"]!=SEED
        or summary["new_independent_Gaussian_primitive_blocks"]!=8
        or summary["planned_source_state_cases"]!=32
        or summary["recorded_source_state_cases"]!=32
        or summary["planned_nested_Gaussian_likelihood_fits"]!=64
        or summary["recorded_nested_Gaussian_likelihood_fit_slots"]!=64
        or summary["planned_numerical_optimizer_start_slots"]!=192
        or summary["recorded_numerical_optimizer_start_slots"]!=192
        or not summary["complete_failure_inclusive_source_and_start_ledger"]
        or not summary["genuine_nested_H0_theta_slope_equals_zero"]
        or not summary["genuine_nested_H1_theta_slope_nonnegative_including_zero"]
        or summary["release_authorized"]):
        raise ValueError("R57 original denominator or supported inference misreported")
    paired={}
    report=[]
    discrepancies=[]
    for c in original:
        key=f"{c['block']}/{c['support']}/{c['generating_state']}"
        if (c["source_status"]!="ok" or
            c["paired_across_support_and_true_slope_states"] is not True or
            c["new_independent_source_primitive_block"] is not True or
            c["source_info"]["same_native_design_mean_and_non_slope_innovations"] is not True):
            raise ValueError("R57 original paired generating source incomplete")
        variance=0. if c["generating_state"]=="true_zero" else .002025
        close(variance,c["generating_slope_variance"],
              key+"/source generating Gaussian slope variance",absolute=1e-10)
        prior=paired.setdefault((c["block"],c["support"]),[])
        prior.append(c)
        null=audit_model(c["null_fit"],"exact_zero",key+"/null")
        alt=audit_model(c["alternative_fit"],"nonnegative",key+"/alternative")
        comparison=c["nested_comparison"]
        if comparison["status"]!="ok":
            raise ValueError("R57 original nested source numerically refused: "+key)
        if (comparison["p_value"] is not None or
            comparison["hypothesis_rejection"] is not None or
            not comparison["reference_probability_not_specified"]):
            raise ValueError("R57 uncalibrated likelihood gap reported as valid test")
        raw=float(2*(null["selected_NLL"]-alt["selected_NLL"]))
        close(raw,comparison["raw_twice_null_minus_alternative_NLL"],
              key+"/raw signed nested deviance",rel=1e-7,absolute=1e-7)
        if raw< -NESTING_TOL:
            raise ValueError("R57 invalid negative nested deviance beyond tolerance")
        dev=float(max(0.,raw))
        close(dev,comparison["nonnegative_twice_profile_NLL_gap"],
              key+"/numeric deviance after tolerance",rel=1e-9,absolute=1e-10)
        selected_zero=bool(alt["selected_slope_ratio"]<=1e-10)
        if selected_zero!=comparison["alternative_estimated_slope_at_structural_zero"]:
            raise ValueError("R57 false fitted structural-zero classification")
        discrepancies.append(raw)
        report.append({
            "block":c["block"],"support":c["support"],
            "state":c["generating_state"],
            "accepted_nested_deviance":dev,
            "raw_signed_deviance":raw,
            "alternative_selected_exact_zero":selected_zero,
            "source_key":key,
        })
    if len(paired)!=16 or any(
        len(vals)!=2 or {v["generating_state"] for v in vals}
        !=set(("true_zero","true_positive")) or
        vals[0]["source_info"]!=vals[1]["source_info"]
        for vals in paired.values()):
        raise ValueError("R57 original within-primitive source-state pairing invalid")
    strata={}
    for s in ("ordinary_dependent","extreme_dependent"):
        for state in ("true_zero","true_positive"):
            group=[r for r in report if r["support"]==s and r["state"]==state]
            saved=summary["strata"][s+"/"+state]
            if (len(group)!=8 or saved["recorded_source_variants"]!=8 or
                saved["null_two_start_accepted"]!=8 or
                saved["nonnegative_four_start_accepted"]!=8 or
                saved["strictly_numerically_accepted_nested_gaps"]!=8 or
                saved["nested_deviance_numerical_refusals"]!=0):
                raise ValueError("R57 original strict nested numerical cell incomplete")
            exact=sum(v["alternative_selected_exact_zero"] for v in group)
            median=float(np.median([v["accepted_nested_deviance"] for v in group]))
            if exact!=saved["alternative_selected_exact_zero_variance"]:
                raise ValueError("R57 original reported H1 zero variance count false")
            close(median,saved["median_exploratory_nonnegative_deviance"],
                  s+"/"+state+"/original nested cell median",rel=1e-11)
            strata[s+"/"+state]={
                "new_independent_primitive_blocks":8,
                "numerically_accepted_nested_cases":len(group),
                "H1_selected_exact_zero_variance":exact,
                "median_descriptive_nonnegative_nested_deviance":median,
            }
    return {
        "independent_read_only_original_R57_numeric_evidence_audit_passed":True,
        "verified_original_source_SHA256":digests,
        "original_R57_PR_merge_checkout":SOURCE_CHECKOUT,
        "eight_new_independent_primitive_Gaussian_blocks":8,
        "paired_slope_and_support_conditions_are_not_independent":True,
        "matched_primitive_leverage_state_cases":len(report),
        "original_two_model_candidate_slots_verified":2*len(report),
        "original_nested_optimizer_starts_verified":6*len(report),
        "original_signed_nested_deviance_min":float(min(discrepancies)),
        "original_selected_max_physical_KKT":float(max(
            v["selected_physical_KKT"] for c in original
            for v in (c["null_fit"],c["alternative_fit"]))),
        "null_reference_law_not_derived":True,
        "no_p_values_TypeI_power_or_CI_qualification":True,
        "raw_native_Y_not_in_original_case_JSON":True,
        "exact_slope_innovation_subtraction_tested_by_R57_source_contract_not_this_read_only_audit":True,
        "strata":strata,
        "release_authorized":False,
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--original",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(
        audit(args.original),sort_keys=True,indent=2)+"\n")
    print(args.out.read_text())


if __name__=="__main__":
    main()
