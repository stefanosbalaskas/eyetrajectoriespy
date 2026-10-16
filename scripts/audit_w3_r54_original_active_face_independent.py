"""Independent read-only R54 evidence audit comparing IMMUTABLE R53/R54 archives.

This tool does not import R53 or R54 simulators, estimators or summaries.
Checks raw SHA256 files, matched primitive source identities, numerical REML
KKT two-start selection, fixed bound signatures, original direction
denominators and component/pivot derivative arithmetic. Does not certify
a global REML optimum, true theta=0 null, sampling law, coverage or release.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import numpy as np

COMPONENTS=("participant_intercept","participant_slope","trial","sensor")
SUPPORT=("ordinary_dependent","extreme_dependent")
LOW=math.exp(-13.8)
HIGH=math.exp(7.)
KKT_TOL=.001
NLL_TOL=.001
MARGIN=.001
SOURCE_IDS={(b,s) for b in range(4) for s in SUPPORT}
R53_CHECKOUT="11689d8562b061ebd5ac98103f5be26fd94b228f"
R54_CHECKOUT="d8c933164fd2ef7f0092a94dccc76db69ea6fc44"
R53_CASE_HASH="4bcc5be49d90365b25898fa044e23c9704ea2be6de6a68d591fc4ee5b147ba7d"
R54_CASE_HASH="40dd9e448ada9c2a4bf07511eb6db8d104a32dcacae5aa8055e2470868afe13e"


def close(actual,expected,label,rtol=1e-8,atol=1e-9):
    if not (math.isfinite(float(actual)) and math.isfinite(float(expected))
            and math.isclose(float(actual),float(expected),
                             rel_tol=rtol,abs_tol=atol)):
        raise ValueError("R54 independent mismatch "+label)


def verify_SHA256(folder,original_expected,checkout):
    folder=Path(folder)
    lines=(folder/"SHA256SUMS").read_text().splitlines()
    required={"cases.json","summary.json","source-commit.txt"}
    if len(lines)!=3:
        raise ValueError("R54 audit incomplete original SHA256 manifest")
    out={}
    for line in lines:
        declared,sep,name=line.partition("  ")
        if (not sep or name not in required or name in out
                or len(declared)!=64):
            raise ValueError("R54 audit invalid SHA256 member identity")
        actual=hashlib.sha256((folder/name).read_bytes()).hexdigest()
        if actual!=declared:
            raise ValueError("R54 audit original SHA256 mismatch: "+name)
        out[name]=actual
    if set(out)!=required or out["cases.json"]!=original_expected:
        raise ValueError("R54 audit wrong original Gaussian source case hash")
    if (folder/"source-commit.txt").read_text().strip()!=checkout:
        raise ValueError("R54 audit original GitHub PR merge checkout mismatch")
    return out


def validate_fit(fit,label):
    status=fit["status"]
    starts=fit["numerical_starts"]
    if len(starts)!=2 or tuple(s.get("label") for s in starts)!=(
        "interior","spread"):
        raise ValueError("R54 original two-start identities missing: "+label)
    if status!="accepted":
        raise ValueError("R54 audited original fit was refused: "+label)
    scored=[]
    valid=[]
    for start in starts:
        nll=start.get("negative_loglik")
        if nll is not None:
            if not math.isfinite(float(nll)):
                raise ValueError("R54 nonfinite original NLL: "+label)
            scored.append(start)
    if not scored:
        raise ValueError("R54 no original likelihood candidate: "+label)
    minimum=min(float(s["negative_loglik"]) for s in scored)
    for start in scored:
        kkt=start.get("physical_projected_KKT")
        if start["status"]=="ok":
            if not start.get("optimizer_success"):
                raise ValueError("R54 accepted optimizer success flag false: "+label)
            ratios=start.get("ratios")
            if len(ratios)!=4 or any(
                not math.isfinite(float(x)) or x<=0 for x in ratios
            ):
                raise ValueError("R54 invalid positive physical variance ratios")
            recon=float(start["objective_reconstruction_error"])
            if not math.isfinite(recon) or recon>1e-6+1e-10:
                raise ValueError("R54 original objective reconstruction gate")
            if kkt is not None and math.isfinite(float(kkt)) and float(kkt)<=KKT_TOL+1e-10 and (
                float(start["negative_loglik"])-minimum<=NLL_TOL+1e-10
            ):
                valid.append(start)
    if not valid:
        raise ValueError("R54 false numerical fit acceptance: "+label)
    if float(fit["physical_projected_KKT"])>KKT_TOL+1e-10:
        raise ValueError("R54 selected fit KKT failed: "+label)
    if float(fit["selected_NLL"])-minimum>NLL_TOL+1e-10:
        raise ValueError("R54 selected fit NLL failed: "+label)
    if not any(
        math.isclose(float(s["negative_loglik"]),
                     float(fit["selected_NLL"]),rel_tol=1e-8,abs_tol=1e-8)
        and math.isclose(float(s["physical_projected_KKT"]),
                         float(fit["physical_projected_KKT"]),
                         rel_tol=1e-5,abs_tol=1e-8)
        for s in valid
    ):
        raise ValueError("R54 selected fit not on recorded accepted start")
    return fit["selected_start"]


def signature(fit):
    ref=float(fit["reference_variance"])
    ratio=[float(fit["components"][k])/ref for k in COMPONENTS]
    low=[i for i,v in enumerate(ratio)
         if abs(v-LOW)<=1e-5*LOW]
    upper=[i for i,v in enumerate(ratio)
           if abs(v-HIGH)<=1e-5*HIGH]
    return [low,upper]


def audit(original_R53,original_R54):
    sha53=verify_SHA256(original_R53,R53_CASE_HASH,R53_CHECKOUT)
    sha54=verify_SHA256(original_R54,R54_CASE_HASH,R54_CHECKOUT)
    r53=json.loads((Path(original_R53)/"cases.json").read_text())
    r54=json.loads((Path(original_R54)/"cases.json").read_text())
    published=json.loads((Path(original_R54)/"summary.json").read_text())
    for values in (r53,r54):
        ids=[(r["block"],r["support"]) for r in values]
        if len(ids)!=8 or set(ids)!=SOURCE_IDS:
            raise ValueError("R54 unmatched or duplicated R53 original source cases")
    prev={(r["block"],r["support"]):r for r in r53}
    expected_ids=sorted(SOURCE_IDS)
    if (published["planned_direction_records"]!=16
            or published["recorded_direction_records"]!=16
            or published["recorded_attempted_plus_minus_refits"]!=32
            or published["recorded_attempted_optimizer_starts"]!=80
            or not published["full_source_and_direction_denominator_preserved"]
            or published["new_direction_seed"]!=202610175454
            or published["reused_original_R53_primitive_source_seed"]!=202610175353
            or published["release_authorized"]):
        raise ValueError("R54 audit planned or reported denominator mismatch")

    matched=0
    active_cases=[]
    changed_selection=[]
    rows=[]
    for row in r54:
        name=f"{row['block']}:{row['support']}"
        past=prev[(row["block"],row["support"])]
        current=row["original_fit"]
        old=past["original_nuisance"]
        if not row["reuses_original_R53_source"]:
            raise ValueError("R54 source replay explicitly disclaimed")
        validate_fit(current,name+"/original")
        for component in COMPONENTS:
            close(current["components"][component],old["components"][component],
                  name+"/replayed-component/"+component,rtol=1e-6,atol=2e-10)
        close(current["reference_variance"],old["reference_variance"],
              name+"/replayed-reference",rtol=1e-10,atol=1e-12)
        close(row["projected_true_focal"],past["projected_truth"],
              name+"/source-focal-truth",rtol=1e-12)
        matched+=1
        if current["selected_start"]!=old["selected_start"]:
            changed_selection.append(name)
        face=row["active_face"]
        if face["status"]!="ok" or signature(current)!=[
            face["active_low"],face["active_high"]
        ]:
            raise ValueError("R54 invalid local active-face source: "+name)
        low,upper=signature(current)
        if low:
            active_cases.append(name)
        if (past["influence_status"]=="refused")!=(low==[1]):
            raise ValueError("R54 replay improperly reclassified R53 interior refusal")
        for k in low:
            if float(face["signed_KKT"][COMPONENTS[k]])<=MARGIN:
                raise ValueError("R54 failed strict lower active KKT gradient")
        for k in upper:
            if float(face["signed_KKT"][COMPONENTS[k]])>=-MARGIN:
                raise ValueError("R54 failed strict upper active KKT gradient")
        eig=np.array(face["free_Hessian_eigenvalues"],float)
        if eig.min()<=0 or eig.max()/eig.min()>1e9:
            raise ValueError("R54 missing reduced free-Hessian SPD/condition")
        if len(row["directions"])!=2 or [d["index"] for d in row["directions"]] != [0,1]:
            raise ValueError("R54 missing original direction records")
        for direction in row["directions"]:
            lab=name+"/direction"+str(direction["index"])
            if direction["status"]!="ok":
                raise ValueError("R54 refused matched-source direction: "+lab)
            plus=direction["plus_fit"];minus=direction["minus_fit"]
            validate_fit(plus,lab+"/plus")
            validate_fit(minus,lab+"/minus")
            if direction["plus_signature"]!=[low,upper] or direction["minus_signature"]!=[low,upper]:
                raise ValueError("R54 original active face changed: "+lab)
            predicted=np.array(direction["predicted_nuisance_derivative"],float)
            recorded=np.array(direction["observed_nuisance_derivative"],float)
            h=float(direction["weighted_step"])
            if h<=0:
                raise ValueError("R54 invalid perturbation step")
            actual=np.array([
                (plus["components"][k]-minus["components"][k])/(2*h)
                for k in COMPONENTS],float)
            np.testing.assert_allclose(actual,recorded,rtol=1e-8,atol=1e-8,
                                       err_msg="R54 false nuisance derivative: "+lab)
            err=float(np.linalg.norm(actual-predicted)/
                      max(np.linalg.norm(actual),np.linalg.norm(predicted),1e-9))
            close(err,direction["relative_nuisance_derivative_error"],
                  lab+"/relative-score",rtol=1e-9,atol=1e-9)
            abs_pivot=abs(direction["predicted_pivot_derivative"]-
                          direction["observed_pivot_derivative"])
            close(abs_pivot,direction["absolute_pivot_derivative_error"],
                  lab+"/pivot",rtol=1e-8,atol=1e-10)
            for k in low:
                moving=LOW*(plus["reference_variance"]-
                            minus["reference_variance"])/(2*h)
                close(actual[k],moving,lab+"/observed-moving-bound",
                      rtol=1e-5,atol=1e-9)
                close(predicted[k],moving,lab+"/predicted-moving-bound",
                      rtol=1e-3,atol=2e-7)
            rows.append({
                "block":row["block"],"support":row["support"],
                "direction":direction["index"],
                "relative_component_derivative_error":err,
                "absolute_CR2_pivot_derivative_error":abs_pivot,
                "original_low_active":low,
            })
    if matched!=8 or len(active_cases)!=4 or len(rows)!=16:
        raise ValueError("R54 incomplete replayed original/refit evidence")
    strata={}
    for support in SUPPORT:
        values=[x for x in rows if x["support"]==support]
        alpha=float(np.median([x["relative_component_derivative_error"] for x in values]))
        beta=float(np.median([x["absolute_CR2_pivot_derivative_error"] for x in values]))
        reported=published["strata"][support]
        close(alpha,reported["median_nuisance_relative_derivative_error"],
              support+"/reported-component-median",rtol=1e-12)
        close(beta,reported["median_pivot_absolute_derivative_error"],
              support+"/reported-pivot-median",rtol=1e-12)
        strata[support]={
            "directions":len(values),
            "active_slope_original_sources":sum(
                1 for key in active_cases if key.endswith(support)),
            "median_relative_nuisance_derivative_error":alpha,
            "median_absolute_pivot_derivative_error":beta,
        }
    return {
        "independent_immutable_artifact_audit_passed":True,
        "original_R53_SHA256":sha53,
        "original_R54_SHA256":sha54,
        "original_R53_replayed_source_cases":matched,
        "selected_near_equivalent_solver_start_changes":changed_selection,
        "original_positive_lower_active_slope_source_cases":active_cases,
        "verified_stable_face_weighted_response_directions":len(rows),
        "verified_plus_minus_full_REML_refit_records":2*len(rows),
        "verified_original_and_refit_optimizer_start_slots":80,
        "all_moving_positive_lower_bounds_verified_against_original_reference":True,
        "strata":strata,
        "no_new_independent_source_coverage":True,
        "no_true_zero_variance_boundary_inference":True,
        "no_pointwise_or_simultaneous_90pct_calibration":True,
        "release_authorized":False,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--r53",type=Path,required=True)
    p.add_argument("--r54",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(
        audit(args.r53,args.r54),indent=2,sort_keys=True)+"\n")
    print(args.out.read_text())


if __name__=="__main__":
    main()
