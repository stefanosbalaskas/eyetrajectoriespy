"""R69 new-source W3 band coverage sensitivity to multiplier and 199/999 budget.

Prospective engineering/scientific research ONLY; no nominal 90% band
qualification, source replacement, production inference or release.
"""
from __future__ import annotations

import argparse
from collections import Counter
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
from scripts.run_w3_known_truth_workflow_validation import (
    TIME, DIMS, truth_coefficients,
)
from scripts.run_w3_fixed_truth_interval_pilot import independent_hc1_oracle, wilson

STUDY="W3_R69_NEW_INDEPENDENT_FIXED_TRUTH_BAND_MULTIPLIER_BUDGET_DIAGNOSTIC"
SEED=202610196969
BLOCKS=16
SHARDS=((0,4),(4,8),(8,12),(12,16))
DESIGNS=("curve","participant")
MULTIPLIERS=("rademacher","normal")
BUDGETS=(199,999)
NOMINAL=.90
ORACLE_TOL=2e-10
DATASETS=BLOCKS*len(DESIGNS)
CONDITIONAL_DRAW_STREAMS=DATASETS*len(MULTIPLIERS)*max(BUDGETS)


def simulate(block:int,design:str):
    if type(block) is not int or not 0<=block<BLOCKS or design not in DESIGNS:
        raise ValueError("R69 independent block/design not in preregistered grid")
    n,trials=(72,1) if design=="curve" else (36,3)
    rng=np.random.default_rng(SEED+10007*block+(0 if design=="curve" else 1))
    cond=rng.uniform(-.95,.95,size=n)
    truth=truth_coefficients()
    mean=truth[0][None]+cond[:,None,None]*truth[1][None]
    participant=np.zeros_like(mean)
    if design=="participant":
        participant=rng.normal(0,.065,(n,1,2))*(1+.35*TIME[None,:,None])
    noise=rng.normal(0,.04,(n,trials,len(TIME),2))
    observed=(mean+participant)[:,None]+noise
    values=observed.reshape(n*trials,len(TIME),2)
    ids=tuple(f"P{i:03d}-T{j:02d}" for i in range(n) for j in range(trials))
    meta=pd.DataFrame({
        "participant_id":[f"P{i:03d}" for i in range(n) for _ in range(trials)],
        "trial_id":[j for _ in range(n) for j in range(trials)],
    })
    gaze=TrajectorySet(
        time=TIME.copy(),values=values,curve_ids=ids,
        dimension_names=DIMS,coordinate_system="normalized",time_unit="s",
        metadata=meta,provenance={"simulation":True,"study":STUDY,"block":block,
                                  "independent_unit":design},
    )
    frame=pd.DataFrame({"curve_id":ids,"condition":np.repeat(cond,trials)})
    oracle_y=observed.mean(axis=1)
    X=np.column_stack((np.ones(n),cond))
    return gaze,frame,truth,X,oracle_y


def draw_seed(block:int,design:str,multiplier:str)->int:
    if type(block) is not int or not 0<=block<BLOCKS or design not in DESIGNS or multiplier not in MULTIPLIERS:
        raise ValueError("R69 bootstrap seed outside frozen sources")
    return SEED+1000003*block+10007*DESIGNS.index(design)+557*MULTIPLIERS.index(multiplier)+41


def _critical(boot_coeff:np.ndarray,center:np.ndarray,se:np.ndarray,budget:int):
    if budget not in BUDGETS or boot_coeff.shape[0]<budget:
        raise ValueError("R69 original nested wild draw prefix not available")
    dev=(boot_coeff[:budget]-center[None])/se[None]
    slopes=np.max(np.abs(dev[:,1]),axis=(1,2))
    family=np.max(np.abs(dev),axis=(1,2,3))
    return (
        float(np.quantile(slopes,NOMINAL,method="higher")),
        float(np.quantile(family,NOMINAL,method="higher")),
    )


def evaluate(block:int,design:str)->dict:
    n=72 if design=="curve" else 36
    row={
        "study":STUDY,"block":block,"design":design,
        "source_seed":SEED+10007*block+DESIGNS.index(design),
        "independent_units":n,"total_observed_curves":72 if design=="curve" else 108,
        "completed":False,"exception":None,
        "max_beta_oracle_error":None,"max_HC1_oracle_error":None,
        "mean_slope_pointwise_truth_inclusion":None,
        "conditions":{},
        "new_primitive_source_blocks":BLOCKS,
        "bootstrap_draws_are_not_independent_source_units":True,
        "simultaneous_90pct_coverage_qualified":False,
        "release_authorized":False,
    }
    try:
        gaze,frame,truth,X,oracle_y=simulate(block,design)
        config=FunctionOnScalarWorkflowConfig(
            predictors=("condition",),dimensions=DIMS,unit=design,
            participant_column="participant_id" if design=="participant" else None,
        )
        fit=run_function_on_scalar_workflow(gaze,frame,config=config).fit
        beta,se=independent_hc1_oracle(X,oracle_y)
        if fit.coefficients.shape!=truth.shape or fit.standard_errors.shape!=truth.shape:
            raise ValueError("R69 original fitted result shape mismatch")
        if fit.unit!=design or len(fit.unit_ids)!=n:
            raise ValueError("R69 original independent unit misidentified")
        if not np.isfinite(se).all() or np.any(se<=0):
            raise ValueError("R69 original HC1 pointwise SE nonpositive")
        beta_diff=float(np.max(np.abs(beta-fit.coefficients)))
        se_diff=float(np.max(np.abs(se-fit.standard_errors)))
        if max(beta_diff,se_diff)>ORACLE_TOL:
            raise ValueError("R69 independent coefficient/HC1 numerical oracle disagreement")
        row["max_beta_oracle_error"]=beta_diff
        row["max_HC1_oracle_error"]=se_diff
        z=float(norm.ppf((1+NOMINAL)/2))
        row["mean_slope_pointwise_truth_inclusion"]=float(np.mean(
            np.abs(beta[1]-truth[1])<=z*se[1]))
        for multiplier in MULTIPLIERS:
            seed=draw_seed(block,design,multiplier)
            boot=bootstrap_function_on_scalar_coefficients(
                fit,n_bootstrap=BUDGETS[-1],
                multiplier=multiplier,random_state=seed)
            if boot.multipliers.shape!=(BUDGETS[-1],n):
                raise ValueError("R69 wild weights resampled trial rather than independent unit")
            if boot.bootstrap_coefficients.shape!=(BUDGETS[-1],)+truth.shape:
                raise ValueError("R69 stored wild-coefficient bootstrap shape mismatch")
            slope_band=function_on_scalar_simultaneous_bands(
                boot,confidence_level=NOMINAL,simultaneous_scope="coefficient")
            family_band=function_on_scalar_simultaneous_bands(
                boot,confidence_level=NOMINAL,simultaneous_scope="family")
            for b in BUDGETS:
                slope,family=_critical(boot.bootstrap_coefficients,beta,se,b)
                if b==BUDGETS[-1]:
                    if (not np.isclose(slope,slope_band.critical_values[1],atol=ORACLE_TOL)
                        or not np.allclose(family,family_band.critical_values,atol=ORACLE_TOL)):
                        raise ValueError("R69 maximum-statistic package/oracle disagreement")
                row["conditions"][f"{multiplier}/{b}"]={
                    "multiplier":multiplier,"draws":b,"seed":seed,
                    "source_units":n,"truth_slope_simultaneous_all_grid":bool(np.all(
                        np.abs(beta[1]-truth[1])<=slope*se[1])),
                    "truth_joint_family_simultaneous_all_grid":bool(np.all(
                        np.abs(beta-truth)<=family*se)),
                    "critical_slope":slope,"critical_family":family,
                    "slope_median_band_width":float(np.median(2*slope*se[1])),
                    "family_median_band_width":float(np.median(2*family*se)),
                    "bootstrap_prefix_of_same_999draw_stream":True,
                }
        if set(row["conditions"])!={f"{m}/{b}" for m in MULTIPLIERS for b in BUDGETS}:
            raise ValueError("R69 missing one original paired diagnostic condition")
        row["completed"]=True
    except Exception as exc:
        row["exception"]={"type":type(exc).__name__,"message":str(exc)[:700]}
    return row


def _paired(summary_rows:list[dict],design:str,key_left:str,key_right:str):
    complete=[r for r in summary_rows if r["design"]==design and r["completed"]]
    counted=len(complete)
    missing=BLOCKS-counted
    changes=[int(r["conditions"][key_right]["truth_slope_simultaneous_all_grid"])-
             int(r["conditions"][key_left]["truth_slope_simultaneous_all_grid"])
             for r in complete]
    critical=[r["conditions"][key_right]["critical_slope"]-
              r["conditions"][key_left]["critical_slope"] for r in complete]
    return {
        "matched_complete_primitive_generating_blocks":counted,
        "missing_or_failed_primitive_blocks":missing,
        "later_only_truth_included":sum(v==1 for v in changes),
        "earlier_only_truth_included":sum(v==-1 for v in changes),
        "both_agree":sum(v==0 for v in changes),
        "mean_paired_critical_change_complete":float(np.mean(critical)) if critical else None,
        "observed_truth_inclusion_change_complete":sum(changes)/counted if counted else None,
        "failure_inclusive_lower":(sum(changes)-missing)/BLOCKS,
        "failure_inclusive_upper":(sum(changes)+missing)/BLOCKS,
        "exploratory_not_confirmatory_superiority":True,
    }


def summarize(rows:list[dict])->dict:
    ids=[(r["block"],r["design"]) for r in rows]
    req={(b,d) for b in range(BLOCKS) for d in DESIGNS}
    if len(ids)!=DATASETS or len(set(ids))!=DATASETS or set(ids)!=req:
        raise ValueError("R69 exact 16-source-block x two design grid required")
    info={}
    paired={}
    for design in DESIGNS:
        sub=[r for r in rows if r["design"]==design]
        ok=[r for r in sub if r["completed"]]
        for r in sub:
            if (r["study"]!=STUDY or r["source_seed"]!=SEED+10007*r["block"]+DESIGNS.index(design)
                or r["independent_units"]!=(72 if design=="curve" else 36)
                or r["simultaneous_90pct_coverage_qualified"] is not False
                or r["release_authorized"] is not False):
                raise ValueError("R69 original source/provenance/release flags altered")
            if r["completed"]:
                if set(r["conditions"])!={f"{m}/{b}" for m in MULTIPLIERS for b in BUDGETS}:
                    raise ValueError("R69 complete source lacks paired wild budget condition")
                if (r["max_beta_oracle_error"]>ORACLE_TOL or
                    r["max_HC1_oracle_error"]>ORACLE_TOL):
                    raise ValueError("R69 independent original HC1 numerical oracle failed")
                for mult in MULTIPLIERS:
                    for b in BUDGETS:
                        cell=r["conditions"][f"{mult}/{b}"]
                        if (cell["draws"]!=b or cell["multiplier"]!=mult
                            or cell["seed"]!=draw_seed(r["block"],design,mult)
                            or cell["source_units"]!=r["independent_units"]
                            or cell["bootstrap_prefix_of_same_999draw_stream"] is not True):
                            raise ValueError("R69 original paired wild RNG/draw-unit provenance changed")
        cells={}
        for mult in MULTIPLIERS:
            for budget in BUDGETS:
                key=f"{mult}/{budget}"
                included=sum(r["conditions"][key]["truth_slope_simultaneous_all_grid"] for r in ok)
                family=sum(r["conditions"][key]["truth_joint_family_simultaneous_all_grid"] for r in ok)
                cells[key]={
                    "independent_generating_blocks_attempted":BLOCKS,
                    "independent_generating_blocks_completed":len(ok),
                    "slope_simultaneous_truth_inclusions":included,
                    "joint_family_truth_inclusions":family,
                    "slope_complete_case_rate":included/len(ok) if ok else None,
                    "slope_full_denominator_lower":included/BLOCKS,
                    "slope_full_denominator_upper":(included+BLOCKS-len(ok))/BLOCKS,
                    "slope_Wilson95_completed_only":wilson(included,len(ok)),
                    "average_slope_wild_critical":float(np.mean([
                        r["conditions"][key]["critical_slope"] for r in ok])) if ok else None,
                    "not_90pct_coverage_calibrated":True,
                }
        info[design]={
            "attempted":BLOCKS,"complete":len(ok),"failed":BLOCKS-len(ok),
            "mean_pointwise_slope_cell_truth_fraction":float(np.mean([
                r["mean_slope_pointwise_truth_inclusion"] for r in ok])) if ok else None,
            "conditions":cells,
        }
        for mult in MULTIPLIERS:
            paired[f"{design}/{mult}/199_to_999"]=_paired(rows,design,f"{mult}/199",f"{mult}/999")
        for budget in BUDGETS:
            paired[f"{design}/{budget}/rademacher_to_normal"]=_paired(
                rows,design,f"rademacher/{budget}",f"normal/{budget}")
    return {
        "study":STUDY,"source_seed":SEED,
        "independent_primitive_generating_blocks":BLOCKS,
        "datasets_paired_within_primitive_block":2,
        "total_source_dataset_records":DATASETS,
        "same_fitted_data_across_four_multiplier_budget_cells":True,
        "original_full_bootstrap_draws_generated_not_prefixes":CONDITIONAL_DRAW_STREAMS,
        "Rademacher_and_normal_multipliers":list(MULTIPLIERS),
        "original_199_prefix_nested_inside_999draw_stream":True,
        "nominal_confidence_target":NOMINAL,
        "original_fixed_truth_HC1_oracle_tolerance":ORACLE_TOL,
        "per_design":info,"paired_diagnostics":paired,
        "planned_source_records_complete":len(ids)==DATASETS,
        "no_calibrated_90pct_simultaneous_coverage_claim":True,
        "no_realistic_MNAR_identification":True,
        "release_authorized":False,
    }


def shard(out:Path,start:int,stop:int)->None:
    if (start,stop) not in SHARDS:
        raise ValueError("R69 shard not preregistered")
    out.mkdir(parents=True,exist_ok=True)
    rows=[evaluate(b,d) for b in range(start,stop) for d in DESIGNS]
    payload=(json.dumps(rows,indent=2,sort_keys=True,allow_nan=False)+"\n").encode()
    (out/"cases.json").write_bytes(payload)
    manifest={
        "study":STUDY,"start":start,"stop":stop,"source_seed":SEED,
        "cases":len(rows),"checkout":os.environ.get("GITHUB_SHA","unverified-local"),
        "sha256_cases":sha256(payload).hexdigest(),
    }
    (out/"manifest.json").write_text(json.dumps(manifest,sort_keys=True,indent=2)+"\n")


def aggregate(out:Path,parts:Path)->None:
    files=list(parts.glob("*/manifest.json"))
    if len(files)!=len(SHARDS):
        raise ValueError("R69 four original immutable new-source shard manifests required")
    checkout=os.environ.get("GITHUB_SHA","unverified-local")
    seen=set();all_rows=[]
    for f in files:
        data=json.loads(f.read_bytes())
        pair=(data["start"],data["stop"])
        if (pair not in SHARDS or pair in seen or data["study"]!=STUDY or
            data["source_seed"]!=SEED or data["checkout"]!=checkout):
            raise ValueError("R69 source fragment/seed/original checkout invalid")
        seen.add(pair)
        sourcefile=f.parent/"cases.json"
        raw=sourcefile.read_bytes()
        if sha256(raw).hexdigest()!=data["sha256_cases"]:
            raise ValueError("R69 original source-case SHA256 tamper detected")
        sub=json.loads(raw)
        if len(sub)!=data["cases"] or len(sub)!=(pair[1]-pair[0])*len(DESIGNS):
            raise ValueError("R69 incomplete original source shard")
        if {(x["block"],x["design"]) for x in sub}!={(b,d) for b in range(*pair) for d in DESIGNS}:
            raise ValueError("R69 duplicate or unregistered source in shard")
        all_rows.extend(sub)
    all_rows.sort(key=lambda x:(x["block"],DESIGNS.index(x["design"])))
    result=summarize(all_rows)
    out.mkdir(parents=True,exist_ok=True)
    (out/"cases.json").write_text(json.dumps(all_rows,sort_keys=True,indent=2,allow_nan=False)+"\n")
    (out/"summary.json").write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n")
    (out/"source-commit.txt").write_text(checkout+"\n")
    (out/"SHA256SUMS").write_text("".join(
        sha256((out/n).read_bytes()).hexdigest()+"  "+n+"\n"
        for n in ("cases.json","summary.json","source-commit.txt")))
    print(json.dumps(result,sort_keys=True))


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True,type=Path)
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument("--start",type=int)
    group.add_argument("--merge-parts",type=Path)
    p.add_argument("--stop",type=int)
    a=p.parse_args()
    if a.merge_parts is not None:
        aggregate(a.out,a.merge_parts)
    elif a.stop is not None:
        shard(a.out,a.start,a.stop)
    else:
        raise SystemExit("R69 source shard requires both start and stop")
if __name__=="__main__":
    main()
