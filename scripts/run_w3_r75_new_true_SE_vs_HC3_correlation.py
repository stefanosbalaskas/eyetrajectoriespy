"""R75 NEW independent-source true-vs-HC3 marginal SE × correlation reference.

The true Gaussian law is a *simulation diagnostic*, NEVER an observed-data
covariance estimator. All source failures and 999 raw reference maxima retained.
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
    FunctionOnScalarWorkflowConfig,run_function_on_scalar_workflow,
)
from scripts.run_w3_fixed_truth_interval_pilot import independent_hc1_oracle,wilson
from scripts.run_w3_known_truth_workflow_validation import TIME,DIMS,truth_coefficients
from scripts import run_w3_r71_new_known_gaussian_band_oracle as r71
from scripts import run_w3_r74_new_weighted_slope_hc2_hc3 as r74

STUDY="W3_R75_NEW_SOURCE_TRUE_SE_VS_HC3_CORRELATION_GAUSSIAN_FACTORIAL"
SOURCE_SEED=202610207575
GAUSSIAN_SEED=202610207576
WILD_SEED=202610207577
BLOCKS=32
CONFIGS=("curve_standard","participant_standard")
SUPPORT=("ordinary","extreme")
VARIANCES=("constant","predictor_heteroskedastic")
SHARDS=((0,8),(8,16),(16,24),(24,32))
B=999
CONF=.90
TOL=2e-10
SOURCE_CASES=BLOCKS*len(CONFIGS)*len(SUPPORT)*len(VARIANCES)
CELLS=(
    "true_SE/true_corr","HC3_SE/true_corr",
    "true_SE/HC3_corr","HC3_SE/HC3_corr",
)
MAX_ARRAYS=("wild_HC1","true_corr","HC3_corr")


def config_info(config):
    if config=="curve_standard":
        return 72,1,"curve"
    if config=="participant_standard":
        return 36,3,"participant"
    raise ValueError("R75 native-unit source design unregistered")


def check_identity(block,config,support,variance):
    if (type(block) is not int or not 0<=block<BLOCKS or config not in CONFIGS
        or support not in SUPPORT or variance not in VARIANCES):
        raise ValueError("R75 frozen NEW original source identity invalid")


def seed(block,config,support,variance,domain):
    check_identity(block,config,support,variance)
    ci=CONFIGS.index(config)
    if domain=="source":
        return SOURCE_SEED+100003*block+10007*ci
    base=GAUSSIAN_SEED if domain=="gaussian" else WILD_SEED if domain=="wild" else None
    if base is None:
        raise ValueError("R75 unknown source reference RNG domain")
    return base+1000003*block+10007*ci+739*SUPPORT.index(support)+37*VARIANCES.index(variance)


def simulate(block,config,support,variance):
    n,trials,design=config_info(config)
    rng=np.random.default_rng(seed(block,config,support,variance,"source"))
    x=rng.uniform(-.95,.95,size=n)
    if support=="extreme":
        x[0],x[-1]=-4.,4.
    unit_sd=(np.ones(n) if variance=="constant" else 1.+.75*np.abs(x))
    truth=truth_coefficients()
    mean=truth[0][None]+x[:,None,None]*truth[1][None]
    participant=np.zeros((n,len(TIME),len(DIMS)))
    if design=="participant":
        participant=(rng.normal(0,.065,size=(n,1,len(DIMS)))
                     *(1.+.35*TIME[None,:,None]))
    noise=rng.normal(0,.04,size=(n,trials,len(TIME),len(DIMS)))
    Y=mean[:,None]+unit_sd[:,None,None,None]*(participant[:,None]+noise)
    ids=tuple(f"P{i:03d}-T{j:02d}" for i in range(n) for j in range(trials))
    metadata=pd.DataFrame({
        "participant_id":[f"P{i:03d}" for i in range(n) for _ in range(trials)],
        "trial_id":[j for _ in range(n) for j in range(trials)],
    })
    gaze=TrajectorySet(
        time=TIME.copy(),values=Y.reshape(n*trials,len(TIME),len(DIMS)),
        curve_ids=ids,dimension_names=DIMS,coordinate_system="normalized",
        time_unit="s",metadata=metadata,
        provenance={"simulation":True,"study":STUDY,"block":block,
                    "config":config,"support":support,"variance":variance},
    )
    predictors=pd.DataFrame({"curve_id":ids,"condition":np.repeat(x,trials)})
    X=np.column_stack((np.ones(n),x))
    return gaze,predictors,truth,X,Y.mean(axis=1),unit_sd


def exact_heterogeneous_slope_se(X,unit_sd,design):
    a=(np.linalg.inv(X.T@X)@X.T)[1]
    scalar=float(np.sum((a*unit_sd)**2))
    if scalar<=0 or not math.isfinite(scalar):
        raise ValueError("R75 exact source law invalid slope precision")
    return np.sqrt(scalar*r71.unit_covariance_variance(design))


def estimated_HC3_slope_factor(X,Y,beta):
    n=len(X)
    proj=np.linalg.inv(X.T@X)@X.T
    hat=np.einsum("np,pn->n",X,proj)
    if np.min(hat)<=0 or np.max(hat)>=1-1e-9:
        raise ValueError("R75 fitted HC3 factor leverage outside boundary")
    residual=Y-np.einsum("np,ptd->ntd",X,beta,optimize=True)
    a=proj[1]
    factor=(a/(1-hat))[:,None]*residual.reshape(n,-1)
    diag=np.einsum("nk,nk->k",factor,factor)
    if not np.isfinite(diag).all() or np.any(diag<=1e-14):
        raise ValueError("R75 weighted HC3 covariance nonpositive diagonal")
    return factor,np.sqrt(diag).reshape(len(TIME),len(DIMS)),hat


def true_correlation_maxima(design,rng,draws=B):
    # Exact DGP standardized correlation, independent of X and unit scales.
    if design=="curve":
        standardized=rng.standard_normal((draws,len(TIME),len(DIMS)))
    elif design=="participant":
        latent=rng.standard_normal((draws,1,len(DIMS)))
        trials=rng.standard_normal((draws,len(TIME),len(DIMS)))
        variance=r71.unit_covariance_variance(design)
        standardized=(
            .065*(1+.35*TIME[None,:,None])*latent
            +.04/math.sqrt(3)*trials)/np.sqrt(variance)[None]
    else:
        raise ValueError("R75 covariance source design unregistered")
    return np.max(np.abs(standardized),axis=(1,2))


def estimated_correlation_maxima(factor,estimated_se,rng,draws=B):
    z=rng.standard_normal((draws,len(factor)))
    m=(z@factor).reshape(draws,len(TIME),len(DIMS))
    return np.max(np.abs(m/estimated_se[None]),axis=(1,2))


def evaluate(block,config,support,variance):
    check_identity(block,config,support,variance)
    n,trials,design=config_info(config)
    record={
        "study":STUDY,"block":block,"config":config,"design":design,
        "support":support,"variance":variance,
        "source_seed":seed(block,config,support,variance,"source"),
        "gaussian_seed":seed(block,config,support,variance,"gaussian"),
        "wild_seed":seed(block,config,support,variance,"wild"),
        "native_units":n,"observed_curves":n*trials,
        "completed":False,"refused":True,"exception":None,
        "observed_X":None,"observed_Y_native_unit_mean":None,
        "truth_slope":None,"unit_sd":None,
        "OLS_HC1_package_oracle_error":None,
        "W3_wild_package_critical_error":None,
        "known_SE_grid":None,"estimated_HC3_SE_grid":None,
        "source_slope_beta_error":None,
        "HC3_SE_to_true_SE_mean":None,
        "max_unit_hat":None,
        "raw_reference_maxima":{k:None for k in MAX_ARRAYS},
        "reference_criticals":{k:None for k in MAX_ARRAYS},
        "cell_observed_pivots":{k:None for k in CELLS},
        "cell_truth_included":{k:None for k in CELLS},
        "wild_HC1_truth_included":None,
        "wild_HC1_truth_pivot":None,
        "not_90pct_calibrated":True,"release_authorized":False,
        "no_MNAR_missingness":True,
    }
    try:
        gaze,frame,truth,X,Y,unit_sd=simulate(block,config,support,variance)
        fit=run_function_on_scalar_workflow(
            gaze,frame,config=FunctionOnScalarWorkflowConfig(
                predictors=("condition",),dimensions=DIMS,unit=design,
                participant_column="participant_id" if design=="participant" else None,
            ),
        ).fit
        beta,hc1=independent_hc1_oracle(X,Y)
        errors=[
            float(np.max(np.abs(fit.coefficients-beta))),
            float(np.max(np.abs(fit.standard_errors-hc1))),
        ]
        if (max(errors)>TOL or fit.unit!=design or len(fit.unit_ids)!=n):
            raise ValueError("R75 original W3 OLS/HC1 numeric oracle mismatch")
        original=bootstrap_function_on_scalar_coefficients(
            fit,n_bootstrap=B,multiplier="rademacher",
            random_state=seed(block,config,support,variance,"wild"),
        )
        raw_wild=np.max(np.abs(
            (original.bootstrap_coefficients[:,1]-fit.coefficients[None,1])
            /hc1[None,1]),axis=(1,2))
        wild_c=float(np.quantile(raw_wild,CONF,method="higher"))
        package=function_on_scalar_simultaneous_bands(
            original,confidence_level=CONF,simultaneous_scope="coefficient")
        wild_err=abs(float(package.critical_values[1])-wild_c)
        if wild_err>TOL:
            raise ValueError("R75 original W3 wild 999 max reference mismatch")
        factor,hc3se,hat=estimated_HC3_slope_factor(X,Y,beta)
        true_se=exact_heterogeneous_slope_se(X,unit_sd,design)
        rng=np.random.default_rng(seed(block,config,support,variance,"gaussian"))
        tmax=true_correlation_maxima(design,rng)
        emax=estimated_correlation_maxima(factor,hc3se,rng)
        raw={"wild_HC1":raw_wild,"true_corr":tmax,"HC3_corr":emax}
        crit={name:float(np.quantile(values,CONF,method="higher"))
              for name,values in raw.items()}
        diff=beta[1]-truth[1]
        ptrue=float(np.max(np.abs(diff/true_se)))
        phc3=float(np.max(np.abs(diff/hc3se)))
        pwild=float(np.max(np.abs(diff/hc1[1])))
        pivots={
            "true_SE/true_corr":ptrue,
            "HC3_SE/true_corr":phc3,
            "true_SE/HC3_corr":ptrue,
            "HC3_SE/HC3_corr":phc3,
        }
        covers={name:bool(pivots[name]<=crit[name.split("/")[1]])
                for name in CELLS}
        record.update({
            "completed":True,"refused":False,
            "observed_X":X.tolist(),"observed_Y_native_unit_mean":Y.tolist(),
            "truth_slope":truth[1].tolist(),"unit_sd":unit_sd.tolist(),
            "OLS_HC1_package_oracle_error":max(errors),
            "W3_wild_package_critical_error":wild_err,
            "known_SE_grid":true_se.tolist(),
            "estimated_HC3_SE_grid":hc3se.tolist(),
            "source_slope_beta_error":diff.tolist(),
            "HC3_SE_to_true_SE_mean":float(np.mean(hc3se/true_se)),
            "max_unit_hat":float(np.max(hat)),
            "raw_reference_maxima":{k:v.tolist() for k,v in raw.items()},
            "reference_criticals":crit,
            "cell_observed_pivots":pivots,"cell_truth_included":covers,
            "wild_HC1_truth_included":bool(pwild<=wild_c),
            "wild_HC1_truth_pivot":pwild,
        })
    except Exception as exc:
        record["exception"]={"type":type(exc).__name__,"message":str(exc)[:850]}
    return record


def summarize(rows):
    ids=[(x["block"],x["config"],x["support"],x["variance"]) for x in rows]
    required={(b,c,s,v) for b in range(BLOCKS) for c in CONFIGS
              for s in SUPPORT for v in VARIANCES}
    if len(ids)!=SOURCE_CASES or set(ids)!=required or len(set(ids))!=SOURCE_CASES:
        raise ValueError("R75 full original primitive source grid incomplete or duplicated")
    results={}
    pairs={}
    for config in CONFIGS:
        results[config]={}
        for support in SUPPORT:
            results[config][support]={}
            for variance in VARIANCES:
                sub=[x for x in rows if x["config"]==config and
                     x["support"]==support and x["variance"]==variance]
                ok=[x for x in sub if x["completed"]]
                for x in sub:
                    block=x["block"]
                    if (x["study"]!=STUDY or
                        x["source_seed"]!=seed(block,config,support,variance,"source") or
                        x["gaussian_seed"]!=seed(block,config,support,variance,"gaussian") or
                        x["wild_seed"]!=seed(block,config,support,variance,"wild") or
                        x["not_90pct_calibrated"] is not True or
                        x["release_authorized"] is not False or
                        x["no_MNAR_missingness"] is not True):
                        raise ValueError("R75 original source provenance or withheld calibration flag invalid")
                    if x["completed"]:
                        if (x["refused"] or x["exception"] is not None or
                            set(x["cell_truth_included"])!=set(CELLS) or
                            set(x["raw_reference_maxima"])!=set(MAX_ARRAYS) or
                            any(len(x["raw_reference_maxima"][m])!=B for m in MAX_ARRAYS)
                            or max(x["OLS_HC1_package_oracle_error"],
                                   x["W3_wild_package_critical_error"])>TOL
                            or any(type(x["cell_truth_included"][m]) is not bool for m in CELLS)
                            or type(x["wild_HC1_truth_included"]) is not bool):
                            raise ValueError("R75 full accepted Gaussian reference source evidence missing")
                    elif not x["refused"] or x["exception"] is None:
                        raise ValueError("R75 refused primitive source omitted")
                complete=len(ok);fail=BLOCKS-complete
                measurements={}
                for name in CELLS:
                    n=sum(x["cell_truth_included"][name] for x in ok)
                    measurements[name]={
                        "attempted_primitive_source_blocks":BLOCKS,
                        "complete":complete,"refused":fail,
                        "truth_inclusion":n,
                        "Wilson95_complete":wilson(n,complete),
                        "failure_inclusive_lower":n/BLOCKS,
                        "failure_inclusive_upper":(n+fail)/BLOCKS,
                    }
                k=sum(x["wild_HC1_truth_included"] for x in ok)
                measurements["wild_HC1"]={
                    "attempted_primitive_source_blocks":BLOCKS,
                    "complete":complete,"refused":fail,
                    "truth_inclusion":k,
                    "Wilson95_complete":wilson(k,complete),
                    "failure_inclusive_lower":k/BLOCKS,
                    "failure_inclusive_upper":(k+fail)/BLOCKS,
                }
                results[config][support][variance]={
                    "attempted":BLOCKS,"complete":complete,"refused":fail,
                    "coverage":measurements,
                    "mean_HC3_SE_over_true_SE":float(np.mean([
                        x["HC3_SE_to_true_SE_mean"] for x in ok])) if ok else None,
                    "mean_true_max_critical":float(np.mean([
                        x["reference_criticals"]["true_corr"] for x in ok])) if ok else None,
                    "mean_HC3_max_critical":float(np.mean([
                        x["reference_criticals"]["HC3_corr"] for x in ok])) if ok else None,
                }
                for first,second in [
                    ("true_SE/HC3_corr","true_SE/true_corr"),
                    ("HC3_SE/true_corr","true_SE/true_corr"),
                    ("HC3_SE/HC3_corr","true_SE/true_corr"),
                ]:
                    diffs=[int(x["cell_truth_included"][first])-
                           int(x["cell_truth_included"][second]) for x in ok]
                    key=f"{config}/{support}/{variance}/{first}_minus_{second}"
                    pairs[key]={
                        "completed_primitive_blocks":complete,
                        "refused_primitive_blocks":fail,
                        "first_only_truth_included":sum(v==1 for v in diffs),
                        "second_only_truth_included":sum(v==-1 for v in diffs),
                        "both_agree":sum(v==0 for v in diffs),
                        "complete_change":sum(diffs)/complete if complete else None,
                        "failure_inclusive_lower":(sum(diffs)-fail)/BLOCKS,
                        "failure_inclusive_upper":(sum(diffs)+fail)/BLOCKS,
                        "not_a_calibrated_method_superiority_comparison":True,
                    }
    return {
        "study":STUDY,"source_seed":SOURCE_SEED,
        "gaussian_seed":GAUSSIAN_SEED,"wild_seed":WILD_SEED,
        "new_independent_primitive_blocks":BLOCKS,
        "source_cases":SOURCE_CASES,
        "configs":list(CONFIGS),"supports":list(SUPPORT),
        "variances":list(VARIANCES),"factorial_cells":list(CELLS),
        "original_wild_999_multiplier_positions":SOURCE_CASES*B,
        "known_Gaussian_maxima":SOURCE_CASES*B,
        "HC3_Gaussian_maxima":SOURCE_CASES*B,
        "reference_draws_not_independent_source_replications":True,
        "true_Gaussian_covariance_used_for_diagnostic_cells_only":True,
        "results":results,"paired":pairs,
        "no_90pct_simultaneous_band_calibration":True,
        "no_MNAR_or_dropout_study":True,
        "release_authorized":False,
    }


def shard(out,start,stop):
    if (start,stop) not in SHARDS:
        raise ValueError("R75 original new-source 8-block shard unregistered")
    out.mkdir(parents=True,exist_ok=True)
    cases=[evaluate(b,c,s,v) for b in range(start,stop)
           for c in CONFIGS for s in SUPPORT for v in VARIANCES]
    raw=(json.dumps(cases,indent=2,sort_keys=True,allow_nan=False)+"\n").encode()
    (out/"cases.json").write_bytes(raw)
    (out/"manifest.json").write_text(json.dumps({
        "study":STUDY,"start":start,"stop":stop,
        "source_seed":SOURCE_SEED,"gaussian_seed":GAUSSIAN_SEED,
        "wild_seed":WILD_SEED,"number_cases":len(cases),
        "source_checkout":os.environ.get("GITHUB_SHA","unverified-local"),
        "cases_sha256":sha256(raw).hexdigest(),
    },sort_keys=True,indent=2)+"\n")


def aggregate(out,parts):
    files=list(parts.glob("*/manifest.json"))
    if len(files)!=len(SHARDS):
        raise ValueError("R75 original full four new-source shard aggregate required")
    checkout=os.environ.get("GITHUB_SHA","unverified-local")
    visited=set();cases=[]
    for file in files:
        manifest=json.loads(file.read_bytes())
        key=(manifest["start"],manifest["stop"])
        if (key not in SHARDS or key in visited or manifest["study"]!=STUDY or
            manifest["source_seed"]!=SOURCE_SEED or
            manifest["gaussian_seed"]!=GAUSSIAN_SEED or
            manifest["wild_seed"]!=WILD_SEED or
            manifest["source_checkout"]!=checkout):
            raise ValueError("R75 source provenance/checkout manifest mismatch")
        visited.add(key)
        raw=(file.parent/"cases.json").read_bytes()
        if sha256(raw).hexdigest()!=manifest["cases_sha256"]:
            raise ValueError("R75 original source SHA256 shard tamper")
        part=json.loads(raw)
        required={(b,c,s,v) for b in range(*key)
                  for c in CONFIGS for s in SUPPORT for v in VARIANCES}
        found={(x["block"],x["config"],x["support"],x["variance"]) for x in part}
        if (len(part)!=len(required) or len(part)!=manifest["number_cases"] or found!=required):
            raise ValueError("R75 original shard identity incomplete")
        cases.extend(part)
    cases.sort(key=lambda x:(x["block"],CONFIGS.index(x["config"]),
                             SUPPORT.index(x["support"]),VARIANCES.index(x["variance"])))
    report=summarize(cases)
    out.mkdir(parents=True,exist_ok=True)
    (out/"cases.json").write_text(json.dumps(cases,sort_keys=True,allow_nan=False)+"\n")
    (out/"summary.json").write_text(json.dumps(report,sort_keys=True,indent=2,allow_nan=False)+"\n")
    (out/"source-commit.txt").write_text(checkout+"\n")
    members=("cases.json","summary.json","source-commit.txt")
    (out/"SHA256SUMS").write_text("".join(
        sha256((out/n).read_bytes()).hexdigest()+"  "+n+"\n" for n in members))
    print(json.dumps({
        "study":STUDY,"source_checkout":checkout,
        "original_sources":len(cases),
        "refusals":sum(not x["completed"] for x in cases),
        "summary":report,
    },sort_keys=True))


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
        raise SystemExit("R75 original source shard requires --start and --stop")

if __name__=="__main__":
    main()
