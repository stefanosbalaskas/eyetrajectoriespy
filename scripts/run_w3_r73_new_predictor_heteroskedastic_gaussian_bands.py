"""R73 research-only NEW predictor-heteroskedastic Gaussian HC2 stress test.

Prospectively frozen, no public inference API. Analytic heterogeneous Gaussian
slope variance used for benchmark ONLY, never inside original wild/HC2 fit.
"""
from __future__ import annotations

import argparse
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
from scripts import run_w3_r71_new_known_gaussian_band_oracle as r71
from scripts import run_w3_r72_new_estimated_gaussian_covariance_bands as r72

STUDY="W3_R73_PREDICTOR_HETEROSKEDASTIC_GAUSSIAN_HC2_STRESS"
SOURCE_SEED=202610197373
WILD_SEED=202610197374
ESTIMATED_SEED=202610197375
BLOCKS=32
DESIGNS=("curve","participant")
SUPPORT=("ordinary","extreme")
VARIANCE=("constant","predictor_heteroskedastic")
SHARDS=((0,8),(8,16),(16,24),(24,32))
METHODS=("original_wild_HC1","estimated_HC2_Gaussian","known_heteroskedastic_Gaussian")
SOURCE_CASES=BLOCKS*len(DESIGNS)*len(SUPPORT)*len(VARIANCE)
DRAW_B=999
CONFIDENCE=.90
TOL=2e-10
SCALE_RATE=.75
RNG_DOMAINS={"source":SOURCE_SEED,"wild":WILD_SEED,"estimated":ESTIMATED_SEED}


def _ident(block:int,design:str,support:str,variance:str):
    if (type(block) is not int or not 0<=block<BLOCKS
        or design not in DESIGNS or support not in SUPPORT or variance not in VARIANCE):
        raise ValueError("R73 source identity outside frozen prospective design")


def seed_for(block:int,design:str,support:str,variance:str,domain:str):
    _ident(block,design,support,variance)
    if domain not in RNG_DOMAINS:
        raise ValueError("R73 Gaussian/wild RNG domain invalid")
    if domain=="source":
        return SOURCE_SEED+10007*block+DESIGNS.index(design)
    return (RNG_DOMAINS[domain]+100003*block+10007*DESIGNS.index(design)
            +739*SUPPORT.index(support)+37*VARIANCE.index(variance))


def simulate(block:int,design:str,support:str,variance:str):
    _ident(block,design,support,variance)
    n,trials=(72,1) if design=="curve" else (36,3)
    rng=np.random.default_rng(seed_for(block,design,support,variance,"source"))
    condition=rng.uniform(-.95,.95,size=n)
    if support=="extreme":
        condition[0]=-4.
        condition[-1]=4.
    scale=np.ones(n) if variance=="constant" else 1.+SCALE_RATE*np.abs(condition)
    truth=truth_coefficients()
    mean=truth[0][None]+condition[:,None,None]*truth[1][None]
    part=np.zeros((n,len(TIME),len(DIMS)))
    if design=="participant":
        part=(rng.normal(0,r71.SIGMA_PART,size=(n,1,len(DIMS)))
              *(1.+.35*TIME[None,:,None]))
    trials_noise=rng.normal(0,r71.SIGMA_E,size=(n,trials,len(TIME),len(DIMS)))
    observed=mean[:,None]+scale[:,None,None,None]*(part[:,None]+trials_noise)
    ids=tuple(f"P{i:03d}-T{j:02d}" for i in range(n) for j in range(trials))
    metadata=pd.DataFrame({
        "participant_id":[f"P{i:03d}" for i in range(n) for _ in range(trials)],
        "trial_id":[j for _ in range(n) for j in range(trials)],
    })
    gaze=TrajectorySet(
        time=TIME.copy(),values=observed.reshape(n*trials,len(TIME),len(DIMS)),
        curve_ids=ids,dimension_names=DIMS,coordinate_system="normalized",
        time_unit="s",metadata=metadata,
        provenance={"simulation":True,"study":STUDY,"block":block,
                    "design":design,"support":support,"variance":variance},
    )
    frame=pd.DataFrame({"curve_id":ids,"condition":np.repeat(condition,trials)})
    X=np.column_stack((np.ones(n),condition))
    return gaze,frame,truth,X,observed.mean(axis=1),scale


def exact_heteroskedastic_slope_se(X:np.ndarray,scale:np.ndarray,design:str):
    n=72 if design=="curve" else 36
    if X.shape!=(n,2) or scale.shape!=(n,) or np.any(scale<=0):
        raise ValueError("R73 exact heterogeneous conditional Gaussian law design mismatch")
    projector=np.linalg.inv(X.T@X)@X.T
    slope_weights=projector[1]
    scalar=float(np.sum((slope_weights*scale)**2))
    if scalar<=0 or not math.isfinite(scalar):
        raise ValueError("R73 degenerate Gaussian oracle slope variance")
    return np.sqrt(scalar*r71.unit_covariance_variance(design))


def evaluate(block:int,design:str,support:str,variance:str)->dict:
    _ident(block,design,support,variance)
    n=72 if design=="curve" else 36
    row={
        "study":STUDY,"block":block,"design":design,"support":support,
        "variance":variance,
        "source_seed":seed_for(block,design,support,variance,"source"),
        "wild_seed":seed_for(block,design,support,variance,"wild"),
        "estimated_seed":seed_for(block,design,support,variance,"estimated"),
        "source_units":n,"observed_curves":n if design=="curve" else n*3,
        "completed":False,"refused":True,"exception":None,
        "coverage":{m:None for m in METHODS},
        "pivots":{m:None for m in METHODS},
        "criticals":{m:None for m in METHODS},
        "package_OLS_HC1_oracle_error":None,
        "package_wild_critical_oracle_error":None,
        "mean_HC2_to_heteroskedastic_true_SE":None,
        "mean_HC1_to_heteroskedastic_true_SE":None,
        "max_unit_leverage":None,
        "unit_scale_min":None,"unit_scale_max":None,
        "full_X":None,"full_Y_native_unit_mean":None,
        "full_slope_truth":None,"unit_scales":None,
        "estimated_HC2_slope_SE_grid":None,"original_HC1_slope_SE_grid":None,
        "heteroskedastic_true_slope_SE_grid":None,
        "original_wild_999_maxima":None,"estimated_HC2_999_maxima":None,
        "not_calibrated_90pct_simultaneous_bands":True,
        "release_authorized":False,
    }
    try:
        gaze,frame,truth,X,Y,scale=simulate(block,design,support,variance)
        fit=run_function_on_scalar_workflow(
            gaze,frame,config=FunctionOnScalarWorkflowConfig(
                predictors=("condition",),dimensions=DIMS,unit=design,
                participant_column="participant_id" if design=="participant" else None)
        ).fit
        beta,hc1=independent_hc1_oracle(X,Y)
        berr=float(np.max(np.abs(beta-fit.coefficients)))
        serr=float(np.max(np.abs(hc1-fit.standard_errors)))
        if (fit.unit!=design or len(fit.unit_ids)!=n
            or max(berr,serr)>TOL or np.any(hc1[1]<=0)):
            raise ValueError("R73 original W3 package OLS/HC1 source contract failed")
        wild=bootstrap_function_on_scalar_coefficients(
            fit,n_bootstrap=DRAW_B,multiplier="rademacher",
            random_state=seed_for(block,design,support,variance,"wild"))
        wmax=np.max(np.abs(
            (wild.bootstrap_coefficients[:,1]-fit.coefficients[None,1])
            /hc1[None,1]),axis=(1,2))
        wcrit=float(np.quantile(wmax,CONFIDENCE,method="higher"))
        package=function_on_scalar_simultaneous_bands(
            wild,confidence_level=CONFIDENCE,simultaneous_scope="coefficient")
        werr=abs(float(package.critical_values[1])-wcrit)
        if werr>TOL:
            raise ValueError("R73 original 999 unit-wild maxima reference mismatch")
        est=r72.hc2_gaussian_covariance_maxima(
            X,Y,beta,seed=seed_for(block,design,support,variance,"estimated"),draws=DRAW_B)
        knownse=exact_heteroskedastic_slope_se(X,scale,design)
        knowncrit=float(r71.known_law_reference(design)["critical"])
        diff=beta[1]-truth[1]
        se={
            "original_wild_HC1":hc1[1],
            "estimated_HC2_Gaussian":est["estimated_se"],
            "known_heteroskedastic_Gaussian":knownse,
        }
        criticals={
            "original_wild_HC1":wcrit,
            "estimated_HC2_Gaussian":float(est["critical"]),
            "known_heteroskedastic_Gaussian":knowncrit,
        }
        pivots={m:float(np.max(np.abs(diff/se[m]))) for m in METHODS}
        inclusions={m:bool(pivots[m]<=criticals[m]) for m in METHODS}
        row.update({
            "completed":True,"refused":False,
            "coverage":inclusions,"pivots":pivots,"criticals":criticals,
            "package_OLS_HC1_oracle_error":max(berr,serr),
            "package_wild_critical_oracle_error":werr,
            "mean_HC2_to_heteroskedastic_true_SE":float(
                np.mean(est["estimated_se"]/knownse)),
            "mean_HC1_to_heteroskedastic_true_SE":float(np.mean(hc1[1]/knownse)),
            "max_unit_leverage":float(np.max(est["unit_hat"])),
            "unit_scale_min":float(np.min(scale)),
            "unit_scale_max":float(np.max(scale)),
            "full_X":X.tolist(),"full_Y_native_unit_mean":Y.tolist(),
            "full_slope_truth":truth[1].tolist(),"unit_scales":scale.tolist(),
            "estimated_HC2_slope_SE_grid":est["estimated_se"].tolist(),
            "original_HC1_slope_SE_grid":hc1[1].tolist(),
            "heteroskedastic_true_slope_SE_grid":knownse.tolist(),
            "original_wild_999_maxima":wmax.tolist(),
            "estimated_HC2_999_maxima":est["maxima"].tolist(),
        })
    except Exception as exc:
        row["exception"]={"type":type(exc).__name__,"message":str(exc)[:750]}
    return row


def summarize(rows:list[dict])->dict:
    identities=[(x["block"],x["design"],x["support"],x["variance"]) for x in rows]
    expected={(b,d,s,v) for b in range(BLOCKS) for d in DESIGNS
              for s in SUPPORT for v in VARIANCE}
    if len(identities)!=SOURCE_CASES or len(set(identities))!=SOURCE_CASES or set(identities)!=expected:
        raise ValueError("R73 missing/duplicate original independent generating source identities")
    data={};paired={}
    for design in DESIGNS:
        data[design]={}
        for support in SUPPORT:
            data[design][support]={}
            for variance in VARIANCE:
                sub=[x for x in rows if x["design"]==design and x["support"]==support and x["variance"]==variance]
                ok=[x for x in sub if x["completed"]]
                for x in sub:
                    if (x["study"]!=STUDY or x["source_seed"]!=seed_for(x["block"],design,support,variance,"source")
                        or x["wild_seed"]!=seed_for(x["block"],design,support,variance,"wild")
                        or x["estimated_seed"]!=seed_for(x["block"],design,support,variance,"estimated")
                        or x["not_calibrated_90pct_simultaneous_bands"] is not True
                        or x["release_authorized"] is not False):
                        raise ValueError("R73 original source provenance or release flag corrupted")
                    if x["completed"]:
                        if (x["refused"] or x["exception"] is not None
                            or any(type(x["coverage"][m]) is not bool for m in METHODS)
                            or any(x["coverage"][m]!=(x["pivots"][m]<=x["criticals"][m]) for m in METHODS)
                            or x["package_OLS_HC1_oracle_error"]>TOL
                            or x["package_wild_critical_oracle_error"]>TOL
                            or len(x["original_wild_999_maxima"])!=DRAW_B
                            or len(x["estimated_HC2_999_maxima"])!=DRAW_B):
                            raise ValueError("R73 fake completed source, numerical error or wild maximum missing")
                    elif not x["refused"] or x["exception"] is None:
                        raise ValueError("R73 failed source not preserved")
                methods={}
                for m in METHODS:
                    k=sum(x["coverage"][m] for x in ok)
                    methods[m]={
                        "attempted_independent_generating_blocks":BLOCKS,
                        "complete_sources":len(ok),"refused_sources":BLOCKS-len(ok),
                        "truth_inclusions":k,
                        "observed_complete_rate":k/len(ok) if ok else None,
                        "full_denominator_lower":k/BLOCKS,
                        "full_denominator_upper":(k+BLOCKS-len(ok))/BLOCKS,
                        "Wilson95_complete":wilson(k,len(ok)),
                    }
                data[design][support][variance]={
                    "attempted":BLOCKS,"complete":len(ok),"failed":BLOCKS-len(ok),
                    "methods":methods,
                    "mean_HC2_over_true_SE":float(np.mean([
                        x["mean_HC2_to_heteroskedastic_true_SE"] for x in ok])) if ok else None,
                    "mean_HC1_over_true_SE":float(np.mean([
                        x["mean_HC1_to_heteroskedastic_true_SE"] for x in ok])) if ok else None,
                    "mean_max_hat":float(np.mean([x["max_unit_leverage"] for x in ok])) if ok else None,
                }
                for first,second in (
                    ("estimated_HC2_Gaussian","original_wild_HC1"),
                    ("known_heteroskedastic_Gaussian","estimated_HC2_Gaussian"),
                ):
                    changes=[int(x["coverage"][first])-int(x["coverage"][second]) for x in ok]
                    missing=BLOCKS-len(ok)
                    paired[f"{design}/{support}/{variance}/{first}_minus_{second}"]={
                        "completed_primitive_blocks":len(ok),"refused_primitive_blocks":missing,
                        "first_only_truth_included":sum(x==1 for x in changes),
                        "second_only_truth_included":sum(x==-1 for x in changes),
                        "both_agree":sum(x==0 for x in changes),
                        "mean_change_completed":sum(changes)/len(ok) if ok else None,
                        "full_denominator_lower":(sum(changes)-missing)/BLOCKS,
                        "full_denominator_upper":(sum(changes)+missing)/BLOCKS,
                        "not_a_calibrated_method_superiority_test":True,
                    }
    return {
        "study":STUDY,"new_primitive_independent_generating_blocks":BLOCKS,
        "source_cases":SOURCE_CASES,"source_seed":SOURCE_SEED,
        "wild_seed":WILD_SEED,"estimated_Gaussian_seed":ESTIMATED_SEED,
        "heteroskedastic_scale_rate":SCALE_RATE,
        "designs":list(DESIGNS),"supports":list(SUPPORT),
        "variance_regimes":list(VARIANCE),"methods":list(METHODS),
        "original_source_wild_multiplier_draw_positions":SOURCE_CASES*DRAW_B,
        "source_estimated_Gaussian_draw_positions":SOURCE_CASES*DRAW_B,
        "true_covariance_in_HC2_estimator":False,
        "known_law_critical_reused_by_design_only":True,
        "per_cell":data,"paired":paired,
        "no_nominal_90pct_coverage_claim":True,
        "no_missingness_or_MNAR_experiment":True,
        "release_authorized":False,
    }


def shard(out:Path,start:int,stop:int):
    if (start,stop) not in SHARDS:
        raise ValueError("R73 8-primitive-block shard not preregistered")
    out.mkdir(parents=True,exist_ok=True)
    rows=[evaluate(b,d,s,v) for b in range(start,stop)
          for d in DESIGNS for s in SUPPORT for v in VARIANCE]
    raw=(json.dumps(rows,sort_keys=True,indent=2,allow_nan=False)+"\n").encode()
    (out/"cases.json").write_bytes(raw)
    (out/"manifest.json").write_text(json.dumps({
        "study":STUDY,"start":start,"stop":stop,
        "source_seed":SOURCE_SEED,"wild_seed":WILD_SEED,"estimated_seed":ESTIMATED_SEED,
        "checkout":os.environ.get("GITHUB_SHA","unverified-local"),
        "source_cases":len(rows),"cases_sha256":sha256(raw).hexdigest(),
    },indent=2,sort_keys=True)+"\n")


def aggregate(out:Path,parts:Path):
    all_files=list(parts.glob("*/manifest.json"))
    if len(all_files)!=len(SHARDS):
        raise ValueError("R73 all four original SHA256 shards required")
    checkout=os.environ.get("GITHUB_SHA","unverified-local")
    seen=set();records=[]
    for manifest in all_files:
        item=json.loads(manifest.read_bytes())
        key=(item["start"],item["stop"])
        if (key not in SHARDS or key in seen or item["study"]!=STUDY
            or item["source_seed"]!=SOURCE_SEED or item["wild_seed"]!=WILD_SEED
            or item["estimated_seed"]!=ESTIMATED_SEED or item["checkout"]!=checkout):
            raise ValueError("R73 original shard source checkout/seed mismatch")
        seen.add(key)
        raw=(manifest.parent/"cases.json").read_bytes()
        if sha256(raw).hexdigest()!=item["cases_sha256"]:
            raise ValueError("R73 original Gaussian source SHA256 mismatch")
        sub=json.loads(raw)
        expected={(b,d,s,v) for b in range(*key) for d in DESIGNS
                  for s in SUPPORT for v in VARIANCE}
        if (len(sub)!=item["source_cases"] or len(sub)!=len(expected)
            or {(x["block"],x["design"],x["support"],x["variance"]) for x in sub}!=expected):
            raise ValueError("R73 duplicate/incomplete original shard source")
        records.extend(sub)
    records.sort(key=lambda x:(x["block"],DESIGNS.index(x["design"]),
                               SUPPORT.index(x["support"]),VARIANCE.index(x["variance"])))
    result=summarize(records)
    out.mkdir(parents=True,exist_ok=True)
    (out/"cases.json").write_text(json.dumps(records,sort_keys=True,allow_nan=False)+"\n")
    (out/"summary.json").write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n")
    (out/"source-commit.txt").write_text(checkout+"\n")
    names=("cases.json","summary.json","source-commit.txt")
    (out/"SHA256SUMS").write_text("".join(
        sha256((out/name).read_bytes()).hexdigest()+"  "+name+"\n" for name in names))
    print(json.dumps({
        "study":STUDY,"source_checkout":checkout,
        "original_sources":len(records),
        "failures":sum(not x["completed"] for x in records),
        "summary":result,
    },sort_keys=True))


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    grp=p.add_mutually_exclusive_group(required=True)
    grp.add_argument("--start",type=int)
    grp.add_argument("--merge-parts",type=Path)
    p.add_argument("--stop",type=int)
    a=p.parse_args()
    if a.merge_parts is not None:
        aggregate(a.out,a.merge_parts)
    elif a.stop is not None:
        shard(a.out,a.start,a.stop)
    else:
        raise SystemExit("R73 shard requires --start and --stop")
if __name__=="__main__":
    main()
