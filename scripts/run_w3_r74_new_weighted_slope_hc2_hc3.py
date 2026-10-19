"""R74 frozen NEW-source weighted-slope HC2/HC3 Gaussian band study.

All methods are research-only. Source truth/covariance never reaches an
estimated-data method. Complete failures retain the original source identity.
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
from eyetrajectoriespy.workflows import (
    FunctionOnScalarWorkflowConfig, run_function_on_scalar_workflow,
)
from scripts.run_w3_fixed_truth_interval_pilot import independent_hc1_oracle, wilson
from scripts.run_w3_known_truth_workflow_validation import TIME, DIMS, truth_coefficients
from scripts import run_w3_r71_new_known_gaussian_band_oracle as r71
from scripts import run_w3_r72_new_estimated_gaussian_covariance_bands as r72

STUDY="W3_R74_NEW_WEIGHTED_SLOPE_HC2_HC3_HETEROSKEDASTIC_GAUSSIAN_BANDS"
SOURCE_SEED=202610197474
GAUSSIAN_SEED=202610197475
WILD_SEED=202610197476
BLOCKS=32
CONFIGS=("curve_small","curve_standard","participant_small","participant_standard")
SUPPORT=("ordinary","extreme")
VARIANCE=("constant","predictor_heteroskedastic")
SHARDS=tuple((lo,lo+4) for lo in range(0,BLOCKS,4))
B=999
CONF=.90
TOL=2e-10
SCALE_RATE=.75
SOURCE_CASES=BLOCKS*len(CONFIGS)*len(SUPPORT)*len(VARIANCE)
METHODS=("original_wild_HC1","pooled_HC2_Gaussian",
         "weighted_slope_HC2_Gaussian","weighted_slope_HC3_Gaussian",
         "known_heteroskedastic_Gaussian")
ESTIMATED=("pooled_HC2_Gaussian","weighted_slope_HC2_Gaussian",
           "weighted_slope_HC3_Gaussian")


def config_info(config):
    if config not in CONFIGS:
        raise ValueError("R74 native independent-unit configuration unregistered")
    participant=config.startswith("participant")
    n=24 if config=="participant_small" else 36 if config in ("participant_standard","curve_small") else 72
    return n,(3 if participant else 1),("participant" if participant else "curve")


def _check(block,config,support,variance):
    if (type(block) is not int or not 0<=block<BLOCKS
        or config not in CONFIGS or support not in SUPPORT or variance not in VARIANCE):
        raise ValueError("R74 original source identity outside prospective design")


def seed(block,config,support,variance,domain):
    _check(block,config,support,variance)
    ci=CONFIGS.index(config)
    if domain=="source":
        return SOURCE_SEED+100003*block+10007*ci
    base=GAUSSIAN_SEED if domain=="gaussian" else WILD_SEED if domain=="wild" else None
    if base is None:
        raise ValueError("R74 RNG stream domain unknown")
    return base+1000003*block+10007*ci+739*SUPPORT.index(support)+37*VARIANCE.index(variance)


def simulate(block,config,support,variance):
    n,trials,design=config_info(config)
    rng=np.random.default_rng(seed(block,config,support,variance,"source"))
    x=rng.uniform(-.95,.95,size=n)
    if support=="extreme":
        x[0],x[-1]=-4.,4.
    scale=(np.ones(n) if variance=="constant" else 1.+SCALE_RATE*np.abs(x))
    truth=truth_coefficients()
    mean=truth[0][None]+x[:,None,None]*truth[1][None]
    participant_effect=np.zeros((n,len(TIME),len(DIMS)))
    if design=="participant":
        participant_effect=(rng.normal(0,r71.SIGMA_PART,size=(n,1,len(DIMS)))
                            *(1.+.35*TIME[None,:,None]))
    trial_noise=rng.normal(0,r71.SIGMA_E,size=(n,trials,len(TIME),len(DIMS)))
    observations=mean[:,None]+scale[:,None,None,None]*(
        participant_effect[:,None]+trial_noise)
    ids=tuple(f"P{i:03d}-T{j:02d}" for i in range(n) for j in range(trials))
    metadata=pd.DataFrame({
        "participant_id":[f"P{i:03d}" for i in range(n) for _ in range(trials)],
        "trial_id":[j for _ in range(n) for j in range(trials)],
    })
    gaze=TrajectorySet(
        time=TIME.copy(),values=observations.reshape(n*trials,len(TIME),len(DIMS)),
        curve_ids=ids,dimension_names=DIMS,
        coordinate_system="normalized",time_unit="s",metadata=metadata,
        provenance={"simulation":True,"study":STUDY,"block":block,
                    "config":config,"support":support,"variance":variance},
    )
    predictors=pd.DataFrame({"curve_id":ids,"condition":np.repeat(x,trials)})
    X=np.column_stack((np.ones(n),x))
    return gaze,predictors,truth,X,observations.mean(axis=1),scale


def true_slope_se(X,scale,design):
    """Exact conditional heterogeneous Gaussian slope SE for source benchmark ONLY."""
    proj=np.linalg.inv(X.T@X)@X.T
    scalar=float(np.sum((proj[1]*scale)**2))
    if not math.isfinite(scalar) or scalar<=0:
        raise ValueError("R74 invalid generating-law slope oracle")
    return np.sqrt(scalar*r71.unit_covariance_variance(design))


def slope_gaussian_candidates(X,Y,beta,*,normal_seed,draws=B):
    """Prespecified weighted HC2/HC3 with exactly source-matched Gaussian z.

    Factor[i,k]=a_i r_ik/(1-h_i)^q for q=.5 (HC2) or 1 (HC3).
    Covariance is F.T @ F, NOT a g11-scaled pooled unit covariance.
    """
    n=len(X)
    if X.shape!=(n,2) or Y.shape!=(n,len(TIME),len(DIMS)) or beta.shape!=(2,len(TIME),len(DIMS)):
        raise ValueError("R74 estimated covariance original source dimensions invalid")
    inverse=np.linalg.inv(X.T@X)
    projection=inverse@X.T
    leverage=np.einsum("np,pn->n",X,projection)
    if not np.isfinite(leverage).all() or np.min(leverage)<=0 or np.max(leverage)>=1-1e-9:
        raise ValueError("R74 original unit hat leverage invalid")
    residual=(Y-np.einsum("np,ptd->ntd",X,beta,optimize=True)).reshape(n,-1)
    a=projection[1]
    # Original pooled HC2 candidate from R72 is reconstructed from same
    # data and same Gaussian generator, not from source true covariance.
    z=np.random.default_rng(normal_seed).standard_normal((draws,n))
    factors={
        "pooled_HC2_Gaussian":residual/np.sqrt(1-leverage)[:,None]/np.sqrt(n)
                               *math.sqrt(float(inverse[1,1])),
        "weighted_slope_HC2_Gaussian":(a/np.sqrt(1-leverage))[:,None]*residual,
        "weighted_slope_HC3_Gaussian":(a/(1-leverage))[:,None]*residual,
    }
    result={}
    for name,factor in factors.items():
        diag=np.sum(factor**2,axis=0)
        if not np.isfinite(diag).all() or np.any(diag<=1e-14):
            raise ValueError("R74 Gaussian covariance diagonal nonpositive "+name)
        normal=z@factor
        maxima=np.max(np.abs(normal)/np.sqrt(diag)[None],axis=1)
        if maxima.shape!=(draws,) or not np.isfinite(maxima).all():
            raise ValueError("R74 Gaussian maximum reference invalid "+name)
        result[name]={
            "maxima":maxima,
            "se":np.sqrt(diag).reshape(len(TIME),len(DIMS)),
            "critical":float(np.quantile(maxima,CONF,method="higher")),
            "trace":float(diag.sum()),
        }
    # Check exact unchanged R72 reference, including same Gaussian z stream.
    r72_reference=r72.hc2_gaussian_covariance_maxima(
        X,Y,beta,seed=normal_seed,draws=draws)
    if (np.max(np.abs(r72_reference["maxima"]-result["pooled_HC2_Gaussian"]["maxima"]))>TOL
        or np.max(np.abs(r72_reference["estimated_se"]-
                          result["pooled_HC2_Gaussian"]["se"]))>TOL):
        raise ValueError("R74 original pooled HC2 numerical implementation changed")
    return result,leverage


def evaluate(block,config,support,variance):
    _check(block,config,support,variance)
    n,trials,design=config_info(config)
    row={
        "study":STUDY,"block":block,"config":config,"design":design,
        "support":support,"variance":variance,
        "source_seed":seed(block,config,support,variance,"source"),
        "gaussian_seed":seed(block,config,support,variance,"gaussian"),
        "wild_seed":seed(block,config,support,variance,"wild"),
        "native_units":n,"trials_per_unit":trials,"observed_curves":n*trials,
        "completed":False,"refused":True,"exception":None,
        "method_truth_included":{m:None for m in METHODS},
        "method_truth_pivots":{m:None for m in METHODS},
        "method_criticals":{m:None for m in METHODS},
        "method_SE_grids":{m:None for m in METHODS},
        "method_999_raw_maxima":{m:None for m in METHODS if m!="known_heteroskedastic_Gaussian"},
        "max_unit_hat":None,"unit_scale_min":None,"unit_scale_max":None,
        "mean_weighted_HC2_to_true_SE":None,
        "mean_weighted_HC3_to_true_SE":None,
        "mean_pooled_HC2_to_true_SE":None,
        "package_OLS_HC1_max_error":None,
        "package_wild_999_max_critical_error":None,
        "original_X":None,"original_Y_native_unit_mean":None,
        "original_slope_truth":None,"original_unit_scales":None,
        "no_calibrated_90pct_simultaneous_method":True,
        "no_source_missingness_or_MNAR":True,
        "release_authorized":False,
    }
    try:
        gaze,frame,truth,X,Y,scale=simulate(block,config,support,variance)
        fit=run_function_on_scalar_workflow(
            gaze,frame,config=FunctionOnScalarWorkflowConfig(
                predictors=("condition",),dimensions=DIMS,unit=design,
                participant_column="participant_id" if design=="participant" else None)
        ).fit
        beta,hc1=independent_hc1_oracle(X,Y)
        err_beta=float(np.max(np.abs(fit.coefficients-beta)))
        err_se=float(np.max(np.abs(fit.standard_errors-hc1)))
        if (fit.unit!=design or len(fit.unit_ids)!=n
            or max(err_beta,err_se)>TOL or np.any(hc1[1]<=0)):
            raise ValueError("R74 unchanged original W3 HC1 numerical oracle failed")
        original=bootstrap_function_on_scalar_coefficients(
            fit,n_bootstrap=B,multiplier="rademacher",
            random_state=seed(block,config,support,variance,"wild"))
        wild_delta=original.bootstrap_coefficients[:,1]-fit.coefficients[None,1]
        wild_max=np.max(np.abs(wild_delta/hc1[None,1]),axis=(1,2))
        wild_critical=float(np.quantile(wild_max,CONF,method="higher"))
        package=function_on_scalar_simultaneous_bands(
            original,confidence_level=CONF,simultaneous_scope="coefficient")
        wild_err=abs(float(package.critical_values[1])-wild_critical)
        if wild_err>TOL:
            raise ValueError("R74 unchanged W3 999-wild max reference mismatch")
        candidates,leverage=slope_gaussian_candidates(
            X,Y,beta,normal_seed=seed(block,config,support,variance,"gaussian"))
        true_se=true_slope_se(X,scale,design)
        truth_crit=float(r71.known_law_reference(design)["critical"])
        source_error=beta[1]-truth[1]
        se={
            "original_wild_HC1":hc1[1],
            **{m:candidates[m]["se"] for m in ESTIMATED},
            "known_heteroskedastic_Gaussian":true_se,
        }
        critical={
            "original_wild_HC1":wild_critical,
            **{m:candidates[m]["critical"] for m in ESTIMATED},
            "known_heteroskedastic_Gaussian":truth_crit,
        }
        pivots={m:float(np.max(np.abs(source_error/se[m]))) for m in METHODS}
        covered={m:bool(pivots[m]<=critical[m]) for m in METHODS}
        row.update({
            "completed":True,"refused":False,
            "method_truth_included":covered,
            "method_truth_pivots":pivots,
            "method_criticals":critical,
            "method_SE_grids":{m:se[m].tolist() for m in METHODS},
            "method_999_raw_maxima":{
                "original_wild_HC1":wild_max.tolist(),
                **{m:candidates[m]["maxima"].tolist() for m in ESTIMATED},
            },
            "max_unit_hat":float(np.max(leverage)),
            "unit_scale_min":float(np.min(scale)),
            "unit_scale_max":float(np.max(scale)),
            "mean_weighted_HC2_to_true_SE":float(
                np.mean(se["weighted_slope_HC2_Gaussian"]/true_se)),
            "mean_weighted_HC3_to_true_SE":float(
                np.mean(se["weighted_slope_HC3_Gaussian"]/true_se)),
            "mean_pooled_HC2_to_true_SE":float(
                np.mean(se["pooled_HC2_Gaussian"]/true_se)),
            "package_OLS_HC1_max_error":max(err_beta,err_se),
            "package_wild_999_max_critical_error":wild_err,
            "original_X":X.tolist(),
            "original_Y_native_unit_mean":Y.tolist(),
            "original_slope_truth":truth[1].tolist(),
            "original_unit_scales":scale.tolist(),
        })
    except Exception as exc:
        row["exception"]={"type":type(exc).__name__,"message":str(exc)[:850]}
    return row


def summarize(rows):
    expected={(b,c,s,v) for b in range(BLOCKS) for c in CONFIGS
              for s in SUPPORT for v in VARIANCE}
    ids=[(x["block"],x["config"],x["support"],x["variance"]) for x in rows]
    if len(ids)!=SOURCE_CASES or len(set(ids))!=SOURCE_CASES or set(ids)!=expected:
        raise ValueError("R74 original full primitive source grid missing or duplicated")
    cells={};pairs={}
    for config in CONFIGS:
        cells[config]={}
        for support in SUPPORT:
            cells[config][support]={}
            for variance in VARIANCE:
                cases=[x for x in rows if x["config"]==config and x["support"]==support
                       and x["variance"]==variance]
                for x in cases:
                    b=x["block"]
                    if (x["study"]!=STUDY or x["source_seed"]!=seed(b,config,support,variance,"source")
                        or x["gaussian_seed"]!=seed(b,config,support,variance,"gaussian")
                        or x["wild_seed"]!=seed(b,config,support,variance,"wild")
                        or x["no_calibrated_90pct_simultaneous_method"] is not True
                        or x["no_source_missingness_or_MNAR"] is not True
                        or x["release_authorized"] is not False):
                        raise ValueError("R74 original source or release qualification corrupted")
                    if x["completed"]:
                        if (x["refused"] or x["exception"] is not None
                            or set(x["method_truth_included"])!=set(METHODS)
                            or set(x["method_999_raw_maxima"])!=set(METHODS)-{"known_heteroskedastic_Gaussian"}
                            or any(type(x["method_truth_included"][m]) is not bool for m in METHODS)
                            or any(x["method_truth_included"][m]!=
                                   (x["method_truth_pivots"][m]<=x["method_criticals"][m]) for m in METHODS)
                            or any(len(x["method_999_raw_maxima"][m])!=B for m in x["method_999_raw_maxima"])
                            or x["package_OLS_HC1_max_error"]>TOL
                            or x["package_wild_999_max_critical_error"]>TOL):
                            raise ValueError("R74 incomplete accepted source numerical evidence")
                    elif not x["refused"] or x["exception"] is None:
                        raise ValueError("R74 refused original source cannot be omitted")
                accepted=[x for x in cases if x["completed"]];missing=BLOCKS-len(accepted)
                methods={}
                for m in METHODS:
                    k=sum(x["method_truth_included"][m] for x in accepted)
                    methods[m]={
                        "attempted_independent_blocks":BLOCKS,
                        "complete_sources":len(accepted),"failed_sources":missing,
                        "truth_included":k,
                        "complete_rate":k/len(accepted) if accepted else None,
                        "fixed_denominator_lower":k/BLOCKS,
                        "fixed_denominator_upper":(k+missing)/BLOCKS,
                        "Wilson95_complete":wilson(k,len(accepted)),
                    }
                cells[config][support][variance]={
                    "attempted":BLOCKS,"complete":len(accepted),"refused":missing,
                    "methods":methods,
                    "mean_weighted_HC2_to_true_SE":float(np.mean([
                        x["mean_weighted_HC2_to_true_SE"] for x in accepted])) if accepted else None,
                    "mean_weighted_HC3_to_true_SE":float(np.mean([
                        x["mean_weighted_HC3_to_true_SE"] for x in accepted])) if accepted else None,
                    "mean_pooled_HC2_to_true_SE":float(np.mean([
                        x["mean_pooled_HC2_to_true_SE"] for x in accepted])) if accepted else None,
                }
                for first,second in [
                    ("weighted_slope_HC2_Gaussian","pooled_HC2_Gaussian"),
                    ("weighted_slope_HC3_Gaussian","weighted_slope_HC2_Gaussian"),
                    ("known_heteroskedastic_Gaussian","weighted_slope_HC2_Gaussian"),
                ]:
                    diffs=[int(x["method_truth_included"][first])-
                           int(x["method_truth_included"][second]) for x in accepted]
                    pairs[f"{config}/{support}/{variance}/{first}_minus_{second}"]={
                        "completed_primitive_blocks":len(accepted),"refused_primitive_blocks":missing,
                        "first_only_included":sum(d==1 for d in diffs),
                        "second_only_included":sum(d==-1 for d in diffs),
                        "both_agree":sum(d==0 for d in diffs),
                        "complete_source_change":sum(diffs)/len(accepted) if accepted else None,
                        "fixed_denominator_change_lower":(sum(diffs)-missing)/BLOCKS,
                        "fixed_denominator_change_upper":(sum(diffs)+missing)/BLOCKS,
                        "not_calibrated_method_superiority":True,
                    }
    return {
        "study":STUDY,"source_seed":SOURCE_SEED,
        "gaussian_seed":GAUSSIAN_SEED,"wild_seed":WILD_SEED,
        "new_independent_primitive_blocks":BLOCKS,
        "source_cases":SOURCE_CASES,"configs":list(CONFIGS),
        "supports":list(SUPPORT),"variances":list(VARIANCE),"methods":list(METHODS),
        "original_wild_multiplier_positions":SOURCE_CASES*B,
        "original_gaussian_multiplier_positions":SOURCE_CASES*B,
        "derived_gaussian_maxima_across_three_covariances":SOURCE_CASES*B*len(ESTIMATED),
        "original_full_grid_dimensionality":len(TIME)*len(DIMS),
        "source_cases_are_paired_not_independent_method_replicates":True,
        "known_source_covariance_never_used_in_estimators":True,
        "per_cell":cells,"paired":pairs,
        "no_90pct_simultaneous_band_calibration":True,
        "no_missingness_or_MNAR_evaluated":True,"release_authorized":False,
    }


def shard(out,start,stop):
    if (start,stop) not in SHARDS:
        raise ValueError("R74 original prospective 4-block shard not preregistered")
    out.mkdir(parents=True,exist_ok=True)
    rows=[evaluate(b,c,s,v) for b in range(start,stop) for c in CONFIGS
          for s in SUPPORT for v in VARIANCE]
    raw=(json.dumps(rows,indent=2,sort_keys=True,allow_nan=False)+"\n").encode()
    (out/"cases.json").write_bytes(raw)
    (out/"manifest.json").write_text(json.dumps({
        "study":STUDY,"start":start,"stop":stop,
        "source_seed":SOURCE_SEED,"gaussian_seed":GAUSSIAN_SEED,
        "wild_seed":WILD_SEED,"source_count":len(rows),
        "original_checkout":os.environ.get("GITHUB_SHA","unverified-local"),
        "sha256_cases":sha256(raw).hexdigest(),
    },sort_keys=True,indent=2)+"\n")


def aggregate(out,parts):
    manifests=list(parts.glob("*/manifest.json"))
    if len(manifests)!=len(SHARDS):
        raise ValueError("R74 all eight immutable original shards mandatory")
    checkout=os.environ.get("GITHUB_SHA","unverified-local")
    seen=set();rows=[]
    for file in manifests:
        m=json.loads(file.read_bytes())
        key=(m["start"],m["stop"])
        if (key not in SHARDS or key in seen or m["study"]!=STUDY
            or m["source_seed"]!=SOURCE_SEED or m["gaussian_seed"]!=GAUSSIAN_SEED
            or m["wild_seed"]!=WILD_SEED or m["original_checkout"]!=checkout):
            raise ValueError("R74 original mixed checkout/source seed/shard")
        seen.add(key)
        raw=(file.parent/"cases.json").read_bytes()
        if sha256(raw).hexdigest()!=m["sha256_cases"]:
            raise ValueError("R74 original immutable source shard SHA256 mismatch")
        part=json.loads(raw)
        expected={(b,c,s,v) for b in range(*key) for c in CONFIGS
                  for s in SUPPORT for v in VARIANCE}
        if (len(part)!=m["source_count"] or len(part)!=len(expected)
            or {(z["block"],z["config"],z["support"],z["variance"]) for z in part}!=expected):
            raise ValueError("R74 original source shard incomplete or duplicated")
        rows.extend(part)
    rows.sort(key=lambda x:(x["block"],CONFIGS.index(x["config"]),
                            SUPPORT.index(x["support"]),VARIANCE.index(x["variance"])))
    report=summarize(rows)
    out.mkdir(parents=True,exist_ok=True)
    (out/"cases.json").write_text(json.dumps(rows,sort_keys=True,allow_nan=False)+"\n")
    (out/"summary.json").write_text(json.dumps(report,sort_keys=True,allow_nan=False,indent=2)+"\n")
    (out/"source-commit.txt").write_text(checkout+"\n")
    names=("cases.json","summary.json","source-commit.txt")
    (out/"SHA256SUMS").write_text("".join(
        sha256((out/name).read_bytes()).hexdigest()+"  "+name+"\n" for name in names))
    print(json.dumps({
        "study":STUDY,"original_source_checkout":checkout,
        "source_cases":len(rows),"source_failures":sum(not x["completed"] for x in rows),
        "source_summary":report,
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
        raise SystemExit("R74 --start also requires --stop")
if __name__=="__main__":
    main()
