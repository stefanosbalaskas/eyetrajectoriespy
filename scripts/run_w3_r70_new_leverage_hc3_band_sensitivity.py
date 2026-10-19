"""R70 NEW independent-source leverage x HC3 studentization diagnostic.

Original W3 OLS/HC1 package estimator and Rademacher wild bootstrap remain
unchanged. HC3 and factorial components are *research-only* analytic oracles.
Store all four 999-draw maximum-statistic arrays for independent later audit.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

from eyetrajectoriespy import TrajectorySet
from eyetrajectoriespy.function_on_scalar import (
    bootstrap_function_on_scalar_coefficients,
    function_on_scalar_simultaneous_bands,
)
from eyetrajectoriespy.workflows import (
    FunctionOnScalarWorkflowConfig, run_function_on_scalar_workflow,
)
from scripts.run_w3_fixed_truth_interval_pilot import independent_hc1_oracle, wilson
from scripts.run_w3_known_truth_workflow_validation import TIME, DIMS, truth_coefficients

STUDY="W3_R70_NEW_FIXED_TRUTH_LEVERAGE_HC3_SIMULTANEOUS_DIAGNOSTIC"
SOURCE_SEED=202610197070
DRAW_SEED=202610197071
BLOCKS=32
DESIGNS=("curve","participant")
SUPPORT=("ordinary","extreme")
ADJUSTMENTS=("unadjusted","hc3_residual")
STUDENTIZATIONS=("hc1","hc3")
CELLS=tuple(f"{a}/{s}" for a in ADJUSTMENTS for s in STUDENTIZATIONS)
B=999
NOMINAL=.90
ORACLE_TOL=2e-10
SOURCE_CASES=BLOCKS*len(DESIGNS)*len(SUPPORT)
SHARDS=tuple((i,i+4) for i in range(0,BLOCKS,4))
CONDITIONAL_MULTIPLIER_ROWS=SOURCE_CASES*B
DERIVED_COEFFICIENT_REPLICATES=SOURCE_CASES*B*len(CELLS)
QUANTILE_METHOD="higher"
MAX_HAT_CUTOFF=1-1e-10


def seed_for(block:int,design:str,support:str)->int:
    if type(block) is not int or not 0<=block<BLOCKS or design not in DESIGNS or support not in SUPPORT:
        raise ValueError("R70 wild source identity outside frozen design")
    return DRAW_SEED+100003*block+10007*DESIGNS.index(design)+739*SUPPORT.index(support)


def simulate(block:int,design:str,support:str):
    if type(block) is not int or not 0<=block<BLOCKS or design not in DESIGNS or support not in SUPPORT:
        raise ValueError("R70 source outside prospective block×design×support grid")
    n,trials=(72,1) if design=="curve" else (36,3)
    # SAME primitive Gaussian source innovations and original conditions
    # are deliberately reused across the two leverage supports.
    rng=np.random.default_rng(SOURCE_SEED+10007*block+DESIGNS.index(design))
    condition=rng.uniform(-.95,.95,size=n)
    if support=="extreme":
        condition[0]=-4.
        condition[-1]=4.
    truth=truth_coefficients()
    mean=truth[0][None]+condition[:,None,None]*truth[1][None]
    participant_effect=np.zeros_like(mean)
    if design=="participant":
        participant_effect=(rng.normal(0,.065,(n,1,2))
                            *(1+.35*TIME[None,:,None]))
    noise=rng.normal(0,.04,(n,trials,len(TIME),len(DIMS)))
    observed=(mean+participant_effect)[:,None]+noise
    values=observed.reshape(n*trials,len(TIME),len(DIMS))
    ids=tuple(f"P{i:03d}-T{j:02d}" for i in range(n) for j in range(trials))
    metadata=pd.DataFrame({
        "participant_id":[f"P{i:03d}" for i in range(n) for _ in range(trials)],
        "trial_id":[j for _ in range(n) for j in range(trials)],
    })
    gaze=TrajectorySet(
        time=TIME.copy(),values=values,curve_ids=ids,
        dimension_names=DIMS,coordinate_system="normalized",time_unit="s",
        metadata=metadata,provenance={
            "simulation":True,"study":STUDY,"block":block,
            "design":design,"support":support,"independent_unit":design,
        })
    X=np.column_stack((np.ones(n),condition))
    frame=pd.DataFrame({"curve_id":ids,"condition":np.repeat(condition,trials)})
    return gaze,frame,truth,X,observed.mean(axis=1)


def numerical_reference(X:np.ndarray,Y:np.ndarray):
    n,p=X.shape
    if p!=2 or n not in (72,36):
        raise ValueError("R70 native independent-unit design not matched")
    inv=np.linalg.inv(X.T@X)
    projector=inv@X.T
    beta=np.einsum("pn,ntd->ptd",projector,Y,optimize=True)
    resid=Y-X@beta
    hat=np.einsum("np,pn->n",X,projector,optimize=True)
    if (np.min(hat)<=0 or np.max(hat)>=MAX_HAT_CUTOFF
        or not np.isfinite(hat).all()):
        raise ValueError("R70 HC3 leverage hat invalid")
    hc1sq=np.einsum("pn,ntd->ptd",projector**2,resid**2,optimize=True)*n/(n-p)
    adj=resid/(1.-hat)[:,None,None]
    hc3sq=np.einsum("pn,ntd->ptd",projector**2,adj**2,optimize=True)
    if np.any(hc1sq<=0) or np.any(hc3sq<=0):
        raise ValueError("R70 observed reference SE nonpositive")
    return {
        "beta":beta,"residual":resid,"adjusted_residual":adj,
        "se":{"hc1":np.sqrt(hc1sq),"hc3":np.sqrt(hc3sq)},
        "hat":hat,"projector":projector,
    }


def max_draw_statistics(ref:dict,weights:np.ndarray,adjustment:str,studentization:str):
    if adjustment not in ADJUSTMENTS or studentization not in STUDENTIZATIONS:
        raise ValueError("R70 unknown crossed residual/studentization cell")
    if weights.ndim!=2 or weights.shape[1]!=ref["projector"].shape[1] or weights.shape[0]!=B:
        raise ValueError("R70 original 999 whole-independent-unit multiplier matrix required")
    residual=(ref["residual"] if adjustment=="unadjusted" else
              ref["adjusted_residual"])
    delta=np.einsum(
        "pn,bn,ntd->bptd",ref["projector"],weights,residual,optimize=True)
    pivots=np.abs(delta/ref["se"][studentization][None])
    return np.max(pivots[:,1],axis=(1,2)),np.max(pivots,axis=(1,2,3)),delta


def evaluate(block:int,design:str,support:str)->dict:
    row={
        "study":STUDY,"block":block,"design":design,"support":support,
        "source_seed":SOURCE_SEED+10007*block+DESIGNS.index(design),
        "draw_seed":seed_for(block,design,support),
        "independent_units":72 if design=="curve" else 36,
        "observed_curves":72 if design=="curve" else 108,
        "completed":False,"exception":None,
        "maximum_original_HC1_coefficient_oracle_error":None,
        "maximum_original_HC1_SE_oracle_error":None,
        "maximum_original_wild_999_coefficient_oracle_error":None,
        "max_hat":None,"min_hat":None,"hc3_to_hc1_median_se_ratio":None,
        "pointwise_HC1_slope_cell_truth_fraction":None,
        "cells":{},
        "raw_999_draws_archived_for_independent_max_quantiles":True,
        "no_calibrated_90pct_band_claim":True,"release_authorized":False,
    }
    try:
        gaze,frame,truth,X,Y=simulate(block,design,support)
        config=FunctionOnScalarWorkflowConfig(
            predictors=("condition",),dimensions=DIMS,unit=design,
            participant_column="participant_id" if design=="participant" else None,
        )
        fit=run_function_on_scalar_workflow(gaze,frame,config=config).fit
        ref=numerical_reference(X,Y)
        original_beta,original_se=independent_hc1_oracle(X,Y)
        beta_err=float(np.max(np.abs(ref["beta"]-original_beta)))
        se_err=float(np.max(np.abs(ref["se"]["hc1"]-original_se)))
        fit_beta_err=float(np.max(np.abs(fit.coefficients-ref["beta"])))
        fit_se_err=float(np.max(np.abs(fit.standard_errors-ref["se"]["hc1"])))
        if (max(beta_err,se_err,fit_beta_err,fit_se_err)>ORACLE_TOL
            or fit.unit!=design or len(fit.unit_ids)!=len(X)):
            raise ValueError("R70 independent OLS/HC1 numerical oracle mismatch")
        seed=seed_for(block,design,support)
        weights=np.random.default_rng(seed).choice(
            np.array([-1.,1.]),size=(B,len(X)),replace=True)
        baseline=bootstrap_function_on_scalar_coefficients(
            fit,n_bootstrap=B,multiplier="rademacher",random_state=seed)
        if not np.array_equal(weights,baseline.multipliers):
            raise ValueError("R70 frozen package wild multipliers not identical")
        if baseline.bootstrap_coefficients.shape!=(B,)+truth.shape:
            raise ValueError("R70 original W3 bootstrap 999 curve shape mismatch")
        package_slope=function_on_scalar_simultaneous_bands(
            baseline,confidence_level=NOMINAL,simultaneous_scope="coefficient")
        package_family=function_on_scalar_simultaneous_bands(
            baseline,confidence_level=NOMINAL,simultaneous_scope="family")
        z=float(norm.ppf((1+NOMINAL)/2))
        row["maximum_original_HC1_coefficient_oracle_error"]=max(beta_err,fit_beta_err)
        row["maximum_original_HC1_SE_oracle_error"]=max(se_err,fit_se_err)
        row["max_hat"]=float(np.max(ref["hat"]))
        row["min_hat"]=float(np.min(ref["hat"]))
        row["hc3_to_hc1_median_se_ratio"]=float(np.median(ref["se"]["hc3"]/ref["se"]["hc1"]))
        row["pointwise_HC1_slope_cell_truth_fraction"]=float(np.mean(
            np.abs(ref["beta"][1]-truth[1])<=z*ref["se"]["hc1"][1]))
        for adjustment in ADJUSTMENTS:
            for studentization in STUDENTIZATIONS:
                label=f"{adjustment}/{studentization}"
                slope_draws,family_draws,delta=max_draw_statistics(
                    ref,weights,adjustment,studentization)
                slope_c=float(np.quantile(slope_draws,NOMINAL,method=QUANTILE_METHOD))
                family_c=float(np.quantile(family_draws,NOMINAL,method=QUANTILE_METHOD))
                se=ref["se"][studentization]
                observed_slope=float(np.max(np.abs(
                    (ref["beta"][1]-truth[1])/se[1])))
                observed_family=float(np.max(np.abs(
                    (ref["beta"]-truth)/se)))
                if adjustment=="unadjusted" and studentization=="hc1":
                    original_delta=baseline.bootstrap_coefficients-fit.coefficients[None]
                    wild_err=float(np.max(np.abs(delta-original_delta)))
                    row["maximum_original_wild_999_coefficient_oracle_error"]=wild_err
                    if (wild_err>ORACLE_TOL
                        or not np.isclose(slope_c,package_slope.critical_values[1],atol=ORACLE_TOL)
                        or not np.allclose(family_c,package_family.critical_values,atol=ORACLE_TOL)):
                        raise ValueError("R70 original W3 999 bootstrap package/reference mismatch")
                row["cells"][label]={
                    "adjustment":adjustment,"studentization":studentization,
                    "draw_count":B,"quantile_method":QUANTILE_METHOD,
                    "slope_wild_max_draws":slope_draws.tolist(),
                    "family_wild_max_draws":family_draws.tolist(),
                    "slope_critical":slope_c,"family_critical":family_c,
                    "observed_slope_truth_max_pivot":observed_slope,
                    "observed_family_truth_max_pivot":observed_family,
                    "slope_simultaneous_truth_included":bool(observed_slope<=slope_c),
                    "joint_family_truth_included":bool(observed_family<=family_c),
                    "slope_median_band_width":float(np.median(2*slope_c*se[1])),
                    "same_fitted_source_and_wild_multiplier_vectors":True,
                }
        row["completed"]=True
    except Exception as exc:
        row["exception"]={"type":type(exc).__name__,"message":str(exc)[:700]}
    return row


def summary(rows:list[dict])->dict:
    identities=[(x["block"],x["design"],x["support"]) for x in rows]
    expected={(b,d,s) for b in range(BLOCKS) for d in DESIGNS for s in SUPPORT}
    if len(identities)!=SOURCE_CASES or set(identities)!=expected or len(set(identities))!=SOURCE_CASES:
        raise ValueError("R70 duplicated or incomplete original independent source grid")
    data={}
    for design in DESIGNS:
        data[design]={}
        for support in SUPPORT:
            sub=[x for x in rows if x["design"]==design and x["support"]==support]
            ok=[x for x in sub if x["completed"]]
            for row in sub:
                if (row["study"]!=STUDY or row["source_seed"]!=SOURCE_SEED+10007*row["block"]+DESIGNS.index(design)
                    or row["draw_seed"]!=seed_for(row["block"],design,support)
                    or row["no_calibrated_90pct_band_claim"] is not True or
                    row["release_authorized"] is not False):
                    raise ValueError("R70 source or science-release provenance invalid")
                if row["completed"]:
                    if set(row["cells"])!=set(CELLS):
                        raise ValueError("R70 missing 2x2 original numerical cell")
                    if max(row["maximum_original_HC1_coefficient_oracle_error"],
                           row["maximum_original_HC1_SE_oracle_error"],
                           row["maximum_original_wild_999_coefficient_oracle_error"])>ORACLE_TOL:
                        raise ValueError("R70 prior baseline numerical oracle failed")
                    for name,cell in row["cells"].items():
                        if (cell["draw_count"]!=B or cell["quantile_method"]!=QUANTILE_METHOD
                            or cell["same_fitted_source_and_wild_multiplier_vectors"] is not True
                            or len(cell["slope_wild_max_draws"])!=B or
                            len(cell["family_wild_max_draws"])!=B):
                            raise ValueError("R70 missing original source wild draw maxima")
                elif row["exception"] is None:
                    raise ValueError("R70 source failure lacks preserved exception")
            cells={}
            for name in CELLS:
                k=sum(x["cells"][name]["slope_simultaneous_truth_included"] for x in ok)
                fam=sum(x["cells"][name]["joint_family_truth_included"] for x in ok)
                cells[name]={
                    "successful_source_inclusions":k,"family_source_inclusions":fam,
                    "independent_blocks_planned":BLOCKS,"source_cases_complete":len(ok),
                    "source_cases_failed":BLOCKS-len(ok),
                    "full_denominator_lower":k/BLOCKS,
                    "full_denominator_upper":(k+BLOCKS-len(ok))/BLOCKS,
                    "wilson95_complete_only":wilson(k,len(ok)),
                    "mean_slope_critical":float(np.mean([x["cells"][name]["slope_critical"] for x in ok])) if ok else None,
                }
            data[design][support]={
                "attempted":BLOCKS,"completed":len(ok),"refused":BLOCKS-len(ok),
                "maximum_hat_mean":float(np.mean([x["max_hat"] for x in ok])) if ok else None,
                "mean_hc3_to_hc1_SE_ratio":float(np.mean([x["hc3_to_hc1_median_se_ratio"] for x in ok])) if ok else None,
                "cells":cells,
            }
    comparisons={}
    for design in DESIGNS:
        for support in SUPPORT:
            paired=[x for x in rows if x["design"]==design and x["support"]==support and x["completed"]]
            diff=[int(x["cells"]["hc3_residual/hc3"]["slope_simultaneous_truth_included"])-
                  int(x["cells"]["unadjusted/hc1"]["slope_simultaneous_truth_included"]) for x in paired]
            count=len(paired); missing=BLOCKS-count
            comparisons[f"{design}/{support}/HC3_full_minus_HC1_original"]={
                "independent_primitive_blocks_complete":count,
                "source_refusals":missing,
                "HC3_only_included":sum(v==1 for v in diff),
                "HC1_only_included":sum(v==-1 for v in diff),
                "same_status":sum(v==0 for v in diff),
                "complete_source_change":sum(diff)/count if count else None,
                "full_denominator_change_lower":(sum(diff)-missing)/BLOCKS,
                "full_denominator_change_upper":(sum(diff)+missing)/BLOCKS,
                "not_statistical_method_superiority":True,
            }
    return {
        "study":STUDY,"source_seed":SOURCE_SEED,"draw_seed":DRAW_SEED,
        "independent_primitive_generating_blocks":BLOCKS,
        "paired_dataset_cases":SOURCE_CASES,
        "independent_curve_units":72,"independent_participant_units":36,
        "conditional_rademacher_multiplier_vectors":CONDITIONAL_MULTIPLIER_ROWS,
        "derived_crossed_bootstrap_coefficient_replicates":DERIVED_COEFFICIENT_REPLICATES,
        "original_wild_maxima_archived":True,
        "confidence_level":NOMINAL,"wild_draw_count_per_case":B,
        "original_W3_OLS_HC1_numerical_oracle":True,
        "SE_adjustments":list(STUDENTIZATIONS),
        "residual_adjustments":list(ADJUSTMENTS),
        "results":data,"matched_diagnostics":comparisons,
        "no_calibrated_90pct_pointwise_or_simultaneous_claim":True,
        "no_response_dependent_dropout_experiment":True,
        "release_authorized":False,
    }


def shard(out:Path,start:int,stop:int)->None:
    if (start,stop) not in SHARDS:
        raise ValueError("R70 original NEW primitive block shard not preregistered")
    out.mkdir(parents=True,exist_ok=True)
    rows=[evaluate(b,d,s) for b in range(start,stop) for d in DESIGNS for s in SUPPORT]
    raw=(json.dumps(rows,sort_keys=True,allow_nan=False,indent=2)+"\n").encode()
    (out/"cases.json").write_bytes(raw)
    (out/"manifest.json").write_text(json.dumps({
        "study":STUDY,"source_seed":SOURCE_SEED,"draw_seed":DRAW_SEED,
        "start":start,"stop":stop,"number_cases":len(rows),
        "source_checkout":os.environ.get("GITHUB_SHA","unverified-local"),
        "cases_sha256":sha256(raw).hexdigest()},indent=2,sort_keys=True)+"\n")


def aggregate(out:Path,parts:Path)->None:
    manifests=list(parts.glob("*/manifest.json"))
    if len(manifests)!=len(SHARDS):
        raise ValueError("R70 all eight original Gaussian source shards required")
    checkout=os.environ.get("GITHUB_SHA","unverified-local")
    records=[];seen=set()
    for f in manifests:
        m=json.loads(f.read_bytes())
        key=(m["start"],m["stop"])
        if (key not in SHARDS or key in seen or m["study"]!=STUDY
            or m["source_seed"]!=SOURCE_SEED or m["draw_seed"]!=DRAW_SEED
            or m["source_checkout"]!=checkout):
            raise ValueError("R70 original source manifest or checkout mismatch")
        seen.add(key)
        raw=(f.parent/"cases.json").read_bytes()
        if sha256(raw).hexdigest()!=m["cases_sha256"]:
            raise ValueError("R70 source shard SHA256 tampering")
        rows=json.loads(raw)
        expected={(b,d,s) for b in range(*key) for d in DESIGNS for s in SUPPORT}
        ids={(q["block"],q["design"],q["support"]) for q in rows}
        if len(rows)!=m["number_cases"] or len(ids)!=len(rows) or ids!=expected:
            raise ValueError("R70 original source shard grid missing/duplicated")
        records.extend(rows)
    records.sort(key=lambda x:(x["block"],DESIGNS.index(x["design"]),SUPPORT.index(x["support"])))
    report=summary(records)
    out.mkdir(parents=True,exist_ok=True)
    (out/"cases.json").write_text(json.dumps(records,sort_keys=True,allow_nan=False)+"\n")
    (out/"summary.json").write_text(json.dumps(report,sort_keys=True,allow_nan=False,indent=2)+"\n")
    (out/"source-commit.txt").write_text(checkout+"\n")
    (out/"SHA256SUMS").write_text("".join(
        sha256((out/name).read_bytes()).hexdigest()+"  "+name+"\n"
        for name in ("cases.json","summary.json","source-commit.txt")))
    print(json.dumps({
        "study":STUDY,"checkout":checkout,"source_cases":len(records),
        "source_failures":sum(not q["completed"] for q in records),
        "summary":report,
    },sort_keys=True))


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True,type=Path)
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
        raise SystemExit("R70 --start requires frozen --stop")
if __name__=="__main__":
    main()
