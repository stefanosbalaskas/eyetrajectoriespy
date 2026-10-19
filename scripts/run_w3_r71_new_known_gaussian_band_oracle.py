"""R71 prospectively new Gaussian fixed-truth sources with a KNOWN-law reference.

Exact source conditional covariance is known by construction and never estimated
from data for the Gaussian reference. This is a research benchmark ONLY, not
an API or an empirically calibrated observed-data 90% band.
"""
from __future__ import annotations

import argparse
from functools import lru_cache
from hashlib import sha256
import json
import math
import os
from pathlib import Path

import numpy as np
import pandas as pd

from eyetrajectoriespy import TrajectorySet
from eyetrajectoriespy.function_on_scalar import (
    bootstrap_function_on_scalar_coefficients,
    function_on_scalar_simultaneous_bands,
)
from eyetrajectoriespy.workflows import FunctionOnScalarWorkflowConfig, run_function_on_scalar_workflow
from scripts.run_w3_fixed_truth_interval_pilot import independent_hc1_oracle, wilson
from scripts.run_w3_known_truth_workflow_validation import TIME, DIMS, truth_coefficients

STUDY="W3_R71_NEW_FIXED_TRUTH_KNOWN_GAUSSIAN_LAW_ORACLE_DIAGNOSTIC"
SOURCE_SEED=202610197171
ORACLE_SEED=202610197172
WILD_SEED=202610197173
BLOCKS=32
DESIGNS=("curve","participant")
SUPPORT=("ordinary","extreme")
SHARDS=((0,8),(8,16),(16,24),(24,32))
SOURCE_CASES=BLOCKS*len(DESIGNS)*len(SUPPORT)
WILD_B=999
ORACLE_K=32767
ORACLE_TOTAL=ORACLE_K*len(DESIGNS)
WILD_DRAW_POSITIONS=SOURCE_CASES*WILD_B
NOMINAL=.90
ORACLE_TOL=2e-10
SIGMA_E=.04
SIGMA_PART=.065
PARTICIPANT_TRIALS=3
QUANTILE="higher"


def wild_seed(block:int,design:str,support:str):
    if type(block) is not int or block<0 or block>=BLOCKS or design not in DESIGNS or support not in SUPPORT:
        raise ValueError("R71 wild draw source outside frozen design")
    return WILD_SEED+100003*block+10007*DESIGNS.index(design)+739*SUPPORT.index(support)


def simulate(block:int,design:str,support:str):
    if type(block) is not int or block<0 or block>=BLOCKS or design not in DESIGNS or support not in SUPPORT:
        raise ValueError("R71 Gaussian source outside frozen design")
    n,trials=(72,1) if design=="curve" else (36,PARTICIPANT_TRIALS)
    rng=np.random.default_rng(SOURCE_SEED+10007*block+DESIGNS.index(design))
    condition=rng.uniform(-.95,.95,size=n)
    if support=="extreme":
        condition[0]=-4.
        condition[-1]=4.
    truth=truth_coefficients()
    mean=truth[0][None]+condition[:,None,None]*truth[1][None]
    random_part=np.zeros_like(mean)
    if design=="participant":
        random_part=(rng.normal(0,SIGMA_PART,size=(n,1,len(DIMS)))
                     *(1+.35*TIME[None,:,None]))
    noise=rng.normal(0,SIGMA_E,size=(n,trials,len(TIME),len(DIMS)))
    observed=(mean+random_part)[:,None]+noise
    ids=tuple(f"P{i:03d}-T{j:02d}" for i in range(n) for j in range(trials))
    frame=pd.DataFrame({"curve_id":ids,"condition":np.repeat(condition,trials)})
    metadata=pd.DataFrame({
        "participant_id":[f"P{i:03d}" for i in range(n) for _ in range(trials)],
        "trial_id":[j for _ in range(n) for j in range(trials)],
    })
    gaze=TrajectorySet(
        time=TIME.copy(),values=observed.reshape(n*trials,len(TIME),len(DIMS)),
        curve_ids=ids,dimension_names=DIMS,
        coordinate_system="normalized",time_unit="s",metadata=metadata,
        provenance={"simulation":True,"study":STUDY,"block":block,
                    "design":design,"support":support},
    )
    X=np.column_stack((np.ones(n),condition))
    return gaze,frame,truth,X,observed.mean(axis=1)


def unit_covariance_variance(design:str):
    if design=="curve":
        return np.full((len(TIME),len(DIMS)),SIGMA_E**2)
    if design=="participant":
        v=SIGMA_PART**2*(1.+.35*TIME)**2+SIGMA_E**2/PARTICIPANT_TRIALS
        return np.repeat(v[:,None],len(DIMS),axis=1)
    raise ValueError("R71 original independent-unit design missing")


def true_slope_standard_errors(X:np.ndarray,design:str):
    if X.shape[1]!=2 or X.shape[0]!=(72 if design=="curve" else 36):
        raise ValueError("R71 exact 2-coefficient design unit size invalid")
    scalar=float(np.linalg.inv(X.T@X)[1,1])
    if not np.isfinite(scalar) or scalar<=0:
        raise ValueError("R71 invalid true OLS Gaussian variance scalar")
    return np.sqrt(scalar*unit_covariance_variance(design))


@lru_cache(maxsize=2)
def known_law_reference(design:str):
    """Simulate EXACT standardized Gaussian covariance law, not fitted HC1."""
    if design not in DESIGNS:
        raise ValueError("R71 unknown oracle law")
    rng=np.random.default_rng(ORACLE_SEED+DESIGNS.index(design))
    if design=="curve":
        standardized=rng.standard_normal((ORACLE_K,len(TIME),len(DIMS)))
    else:
        subject=rng.standard_normal((ORACLE_K,1,len(DIMS)))
        independent_trial_mean=rng.standard_normal((ORACLE_K,len(TIME),len(DIMS)))
        amplitude=1+.35*TIME[None,:,None]
        process=SIGMA_PART*amplitude*subject
        process+=(SIGMA_E/np.sqrt(PARTICIPANT_TRIALS))*independent_trial_mean
        standardized=process/np.sqrt(unit_covariance_variance(design))[None]
    maxes=np.max(np.abs(standardized),axis=(1,2))
    crit=float(np.quantile(maxes,NOMINAL,method=QUANTILE))
    if not np.isfinite(crit) or crit<=0:
        raise ValueError("R71 invalid Gaussian maximum-statistic reference")
    return {"design":design,"reference_seed":ORACLE_SEED+DESIGNS.index(design),
            "raw_standardized_maxima":maxes.tolist(),
            "reference_draws":ORACLE_K,"critical":crit,
            "true_unit_variance_grid":unit_covariance_variance(design).tolist()}


def case(block:int,design:str,support:str):
    n=72 if design=="curve" else 36
    row={
        "study":STUDY,"block":block,"design":design,"support":support,
        "source_seed":SOURCE_SEED+10007*block+DESIGNS.index(design),
        "wild_seed":wild_seed(block,design,support),
        "independent_units":n,"observed_curves":72 if design=="curve" else 108,
        "completed":False,"exception":None,
        "OLS_oracle_max_error":None,"HC1_oracle_max_error":None,
        "package_wild_max_reference_error":None,
        "observed_max_hat":None,
        "known_law_critical":None,"original_wild_critical":None,
        "known_law_slope_truth_included":None,
        "original_wild_HC1_slope_truth_included":None,
        "known_law_slope_max_pivot":None,
        "original_wild_HC1_slope_max_pivot":None,
        "min_HC1_over_known_SE":None,
        "mean_HC1_over_known_SE":None,
        "max_HC1_over_known_SE":None,
        "wild_critical_over_known_law_critical":None,
        "observed_slope_beta_error_grid":None,
        "observed_HC1_slope_SE_grid":None,
        "known_law_true_slope_SE_grid":None,
        "wild_999_raw_slope_maxima":None,
        "no_nominal_90pct_wild_band_qualification":True,
        "known_covariance_not_observed_data_estimator":True,
        "release_authorized":False,
    }
    try:
        gaze,frame,truth,X,Y=simulate(block,design,support)
        fit=run_function_on_scalar_workflow(
            gaze,frame,
            config=FunctionOnScalarWorkflowConfig(
                predictors=("condition",),dimensions=DIMS,unit=design,
                participant_column="participant_id" if design=="participant" else None)
        ).fit
        beta,hc1=independent_hc1_oracle(X,Y)
        if fit.unit!=design or len(fit.unit_ids)!=n:
            raise ValueError("R71 original package independent unit mismatch")
        berr=float(np.max(np.abs(fit.coefficients-beta)))
        serr=float(np.max(np.abs(fit.standard_errors-hc1)))
        if berr>ORACLE_TOL or serr>ORACLE_TOL or np.any(hc1<=0):
            raise ValueError("R71 original OLS/HC1 numerical oracle failed")
        orig_seed=wild_seed(block,design,support)
        boot=bootstrap_function_on_scalar_coefficients(
            fit,n_bootstrap=WILD_B,multiplier="rademacher",random_state=orig_seed)
        expected_weights=np.random.default_rng(orig_seed).choice(
            np.array([-1.,1.]),size=(WILD_B,n))
        if not np.array_equal(boot.multipliers,expected_weights):
            raise ValueError("R71 original wild multiplier RNG streams not identical")
        delta=boot.bootstrap_coefficients-fit.coefficients[None]
        refmax=np.max(np.abs(delta[:,1]/hc1[None,1]),axis=(1,2))
        source_package=function_on_scalar_simultaneous_bands(
            boot,confidence_level=NOMINAL,simultaneous_scope="coefficient")
        wildc=float(np.quantile(refmax,NOMINAL,method=QUANTILE))
        packc=float(source_package.critical_values[1])
        err=abs(wildc-packc)
        if err>ORACLE_TOL:
            raise ValueError("R71 original package W3 max-statistic quantile mismatch")
        ref=known_law_reference(design)
        sec=true_slope_standard_errors(X,design)
        source_error=beta[1]-truth[1]
        true_pivot=float(np.max(np.abs(source_error/sec)))
        estimated_pivot=float(np.max(np.abs(source_error/hc1[1])))
        ratio=hc1[1]/sec
        if not np.all(np.isfinite(ratio)) or np.any(ratio<=0):
            raise ValueError("R71 nonfinite HC1 to exact-known-SE ratio")
        hat=np.einsum("np,pn->n",X,np.linalg.inv(X.T@X)@X.T,optimize=True)
        row.update({
            "completed":True,
            "OLS_oracle_max_error":berr,"HC1_oracle_max_error":serr,
            "package_wild_max_reference_error":err,
            "observed_max_hat":float(max(hat)),
            "known_law_critical":ref["critical"],
            "original_wild_critical":wildc,
            "known_law_slope_truth_included":bool(true_pivot<=ref["critical"]),
            "original_wild_HC1_slope_truth_included":bool(estimated_pivot<=wildc),
            "known_law_slope_max_pivot":true_pivot,
            "original_wild_HC1_slope_max_pivot":estimated_pivot,
            "min_HC1_over_known_SE":float(np.min(ratio)),
            "mean_HC1_over_known_SE":float(np.mean(ratio)),
            "max_HC1_over_known_SE":float(np.max(ratio)),
            "wild_critical_over_known_law_critical":wildc/ref["critical"],
            "observed_slope_beta_error_grid":source_error.tolist(),
            "observed_HC1_slope_SE_grid":hc1[1].tolist(),
            "known_law_true_slope_SE_grid":sec.tolist(),
            "wild_999_raw_slope_maxima":refmax.tolist(),
        })
    except Exception as exc:
        row["exception"]={"type":type(exc).__name__,"message":str(exc)[:750]}
    return row


def summarize(rows:list[dict]):
    ids=[(x["block"],x["design"],x["support"]) for x in rows]
    expected={(b,d,s) for b in range(BLOCKS) for d in DESIGNS for s in SUPPORT}
    if len(ids)!=SOURCE_CASES or len(set(ids))!=SOURCE_CASES or set(ids)!=expected:
        raise ValueError("R71 missing/duplicate primitive generating source identities")
    info={}
    paired={}
    for design in DESIGNS:
        info[design]={}
        for support in SUPPORT:
            sub=[x for x in rows if x["design"]==design and x["support"]==support]
            ok=[x for x in sub if x["completed"]]
            for row in sub:
                if (row["study"]!=STUDY or row["source_seed"]!=SOURCE_SEED+10007*row["block"]+DESIGNS.index(design)
                    or row["wild_seed"]!=wild_seed(row["block"],design,support)
                    or row["no_nominal_90pct_wild_band_qualification"] is not True
                    or row["known_covariance_not_observed_data_estimator"] is not True
                    or row["release_authorized"] is not False):
                    raise ValueError("R71 original source provenance or qualification flag changed")
                if row["completed"]:
                    if (len(row["wild_999_raw_slope_maxima"])!=WILD_B
                        or row["OLS_oracle_max_error"]>ORACLE_TOL
                        or row["HC1_oracle_max_error"]>ORACLE_TOL
                        or row["package_wild_max_reference_error"]>ORACLE_TOL):
                        raise ValueError("R71 source 999 maxima or original OLS/HC1 numerical oracle invalid")
                elif row["exception"] is None:
                    raise ValueError("R71 refused source lacks original exception")
            kknown=sum(x["known_law_slope_truth_included"] for x in ok)
            kwild=sum(x["original_wild_HC1_slope_truth_included"] for x in ok)
            info[design][support]={
                "attempted_primitive_blocks":BLOCKS,"complete":len(ok),
                "failed":BLOCKS-len(ok),
                "known_law_true_inclusions":kknown,
                "original_wild_HC1_inclusions":kwild,
                "known_law_Wilson95_complete":wilson(kknown,len(ok)),
                "wild_HC1_Wilson95_complete":wilson(kwild,len(ok)),
                "known_law_full_denominator_lower":kknown/BLOCKS,
                "known_law_full_denominator_upper":(kknown+BLOCKS-len(ok))/BLOCKS,
                "wild_HC1_full_denominator_lower":kwild/BLOCKS,
                "wild_HC1_full_denominator_upper":(kwild+BLOCKS-len(ok))/BLOCKS,
                "mean_min_HC1_over_known_SE":float(np.mean([x["min_HC1_over_known_SE"] for x in ok])) if ok else None,
                "mean_average_HC1_over_known_SE":float(np.mean([x["mean_HC1_over_known_SE"] for x in ok])) if ok else None,
                "mean_wild_critical_over_known_law_critical":float(np.mean([x["wild_critical_over_known_law_critical"] for x in ok])) if ok else None,
            }
            differences=[int(x["known_law_slope_truth_included"])-int(x["original_wild_HC1_slope_truth_included"]) for x in ok]
            missing=BLOCKS-len(ok)
            paired[f"{design}/{support}/known_minus_original_wild"]={
                "complete_matched_primitive_blocks":len(ok),
                "refused_primitive_blocks":missing,
                "known_only_truth_included":sum(d==1 for d in differences),
                "wild_only_truth_included":sum(d==-1 for d in differences),
                "both_agree":sum(d==0 for d in differences),
                "mean_difference_complete":sum(differences)/len(ok) if ok else None,
                "full_denominator_lower":(sum(differences)-missing)/BLOCKS,
                "full_denominator_upper":(sum(differences)+missing)/BLOCKS,
                "not_test_of_method_superiority":True,
            }
    return {
        "study":STUDY,"source_seed":SOURCE_SEED,
        "oracle_seed":ORACLE_SEED,"wild_seed":WILD_SEED,
        "new_independent_primitive_generating_blocks":BLOCKS,
        "source_cases":SOURCE_CASES,
        "source_unit_designs":list(DESIGNS),
        "source_supports":list(SUPPORT),
        "original_Rademacher_wild_multiplier_draw_positions":WILD_DRAW_POSITIONS,
        "original_known_gaussian_reference_draws":ORACLE_TOTAL,
        "oracle_reference_draws_per_design":ORACLE_K,
        "exact_unit_gaussian_variances":True,
        "original_W3_OLS_HC1_oracle_tolerance":ORACLE_TOL,
        "per_design_and_support":info,
        "paired_truth_inclusion_diagnostics":paired,
        "no_calibrated_90pct_estimated_simultaneous_band_claim":True,
        "known_law_is_not_estimable_real_data_reference":True,
        "no_response_dependent_gaze_missingness":True,
        "release_authorized":False,
    }


def shard(out:Path,start:int,stop:int):
    if (start,stop) not in SHARDS:
        raise ValueError("R71 original eight-block source shard unregistered")
    out.mkdir(parents=True,exist_ok=True)
    rows=[case(b,d,s) for b in range(start,stop) for d in DESIGNS for s in SUPPORT]
    payload=(json.dumps(rows,allow_nan=False,sort_keys=True,indent=2)+"\n").encode()
    (out/"cases.json").write_bytes(payload)
    (out/"manifest.json").write_text(json.dumps({
        "study":STUDY,"start":start,"stop":stop,
        "source_seed":SOURCE_SEED,"oracle_seed":ORACLE_SEED,"wild_seed":WILD_SEED,
        "source_checkout":os.environ.get("GITHUB_SHA","unverified-local"),
        "original_source_cases":len(rows),
        "cases_sha256":sha256(payload).hexdigest(),
    },sort_keys=True,indent=2)+"\n")


def aggregate(out:Path,parts:Path):
    source_files=list(parts.glob("*/manifest.json"))
    if len(source_files)!=len(SHARDS):
        raise ValueError("R71 requires four immutable original-source shard manifests")
    orig_checkout=os.environ.get("GITHUB_SHA","unverified-local")
    seen=set()
    cases=[]
    for f in source_files:
        m=json.loads(f.read_bytes())
        ident=(m["start"],m["stop"])
        if (ident not in SHARDS or ident in seen or m["source_checkout"]!=orig_checkout
            or m["study"]!=STUDY or m["source_seed"]!=SOURCE_SEED
            or m["oracle_seed"]!=ORACLE_SEED or m["wild_seed"]!=WILD_SEED):
            raise ValueError("R71 source original checkout/seed/shard malformed")
        seen.add(ident)
        raw=(f.parent/"cases.json").read_bytes()
        if sha256(raw).hexdigest()!=m["cases_sha256"]:
            raise ValueError("R71 original primitive source archive SHA256 mismatch")
        rows=json.loads(raw)
        expected={(b,d,s) for b in range(*ident) for d in DESIGNS for s in SUPPORT}
        if (len(rows)!=m["original_source_cases"] or len(rows)!=len(expected)
            or {(q["block"],q["design"],q["support"]) for q in rows}!=expected):
            raise ValueError("R71 missing original source cases in shard")
        cases.extend(rows)
    cases.sort(key=lambda z:(z["block"],DESIGNS.index(z["design"]),SUPPORT.index(z["support"])))
    result=summarize(cases)
    refs={d:known_law_reference(d) for d in DESIGNS}
    for row in cases:
        if row["completed"] and not math.isclose(
            row["known_law_critical"],refs[row["design"]]["critical"],rel_tol=0,abs_tol=1e-12):
            raise ValueError("R71 original Gaussian maximum reference changed across shards")
    out.mkdir(parents=True,exist_ok=True)
    (out/"cases.json").write_text(json.dumps(cases,sort_keys=True,allow_nan=False)+"\n")
    (out/"summary.json").write_text(json.dumps(result,sort_keys=True,allow_nan=False,indent=2)+"\n")
    (out/"known_gaussian_reference.json").write_text(json.dumps(refs,sort_keys=True,allow_nan=False)+"\n")
    (out/"source-commit.txt").write_text(orig_checkout+"\n")
    names=("cases.json","summary.json","known_gaussian_reference.json","source-commit.txt")
    (out/"SHA256SUMS").write_text("".join(
        sha256((out/name).read_bytes()).hexdigest()+"  "+name+"\n" for name in names))
    print(json.dumps({"study":STUDY,"original_source_checkout":orig_checkout,
        "source_cases":len(cases),
        "failed":sum(not x["completed"] for x in cases),
        "oracle_critical":{d:refs[d]["critical"] for d in DESIGNS},
        "summary":result},sort_keys=True))


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument("--start",type=int)
    group.add_argument("--merge-parts",type=Path)
    p.add_argument("--stop",type=int)
    args=p.parse_args()
    if args.merge_parts is not None:
        aggregate(args.out,args.merge_parts)
    elif args.stop is not None:
        shard(args.out,args.start,args.stop)
    else:
        raise SystemExit("R71 --start requires --stop")
if __name__=="__main__":
    main()
