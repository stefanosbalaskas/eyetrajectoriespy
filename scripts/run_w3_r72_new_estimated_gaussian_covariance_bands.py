"""R72 research-only: data-estimated HC2 covariance Gaussian 90% slope bands.

32 NEW independent primitive Gaussian source blocks; 72 independent curves or
36 participants with 3 trials, paired ordinary/extreme predictor leverage.
Compare unchanged production W3 wild-HC1 to a PREDECLARED, independent-unit
residual HC2 covariance Gaussian plug-in max reference, and a KNOWN-law Gaussian
oracle. All bands are full observed time×dimension slope bands. No estimated
covariance procedure is qualified for a public API or 90% claim.
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
from eyetrajectoriespy.function_on_scalar import bootstrap_function_on_scalar_coefficients
from eyetrajectoriespy.workflows import FunctionOnScalarWorkflowConfig, run_function_on_scalar_workflow
from scripts.run_w3_fixed_truth_interval_pilot import independent_hc1_oracle, wilson
from scripts.run_w3_known_truth_workflow_validation import TIME, DIMS, truth_coefficients
from scripts import run_w3_r71_new_known_gaussian_band_oracle as r71

STUDY="W3_R72_NEW_DATA_ESTIMATED_HC2_GAUSSIAN_SIMULTANEOUS_SLOPE_BAND"
SOURCE_SEED=202610197272
GAUSSIAN_SEED=202610197273
WILD_SEED=202610197274
BLOCKS=32
DESIGNS=("curve","participant")
SUPPORT=("ordinary","extreme")
SHARDS=((0,8),(8,16),(16,24),(24,32))
SOURCE_CASES=BLOCKS*len(DESIGNS)*len(SUPPORT)
DRAW_B=999
QUANTILE="higher"
CONFIDENCE=.9
ORACLE_TOL=2e-10
MIN_VARIANCE=1e-14
METHODS=("original_wild_HC1","estimated_HC2_Gaussian","known_Gaussian_law")

def source_seed(block,design):
    if type(block) is not int or block<0 or block>=BLOCKS or design not in DESIGNS:
        raise ValueError("R72 original source block or independent-unit design not registered")
    return SOURCE_SEED+10007*block+DESIGNS.index(design)

def wild_seed(block,design,support):
    if support not in SUPPORT: raise ValueError("R72 wild support outside registered design")
    return WILD_SEED+100003*block+10007*DESIGNS.index(design)+739*SUPPORT.index(support)

def gaussian_seed(block,design,support):
    if support not in SUPPORT: raise ValueError("R72 Gaussian support outside registered design")
    return GAUSSIAN_SEED+100003*block+10007*DESIGNS.index(design)+739*SUPPORT.index(support)

def simulate(block,design,support):
    """Fresh independent data and paired innovations; no R71 source reuse."""
    if support not in SUPPORT: raise ValueError("R72 source leverage outside registered design")
    n,trials=(72,1) if design=="curve" else (36,3)
    rng=np.random.default_rng(source_seed(block,design))
    cond=rng.uniform(-.95,.95,size=n)
    if support=="extreme":
        cond[0]=-4.
        cond[-1]=4.
    truth=truth_coefficients()
    mean=truth[0][None]+cond[:,None,None]*truth[1][None]
    u=np.zeros_like(mean)
    if design=="participant":
        u=rng.normal(0,r71.SIGMA_PART,size=(n,1,len(DIMS)))*(1+.35*TIME[None,:,None])
    e=rng.normal(0,r71.SIGMA_E,size=(n,trials,len(TIME),len(DIMS)))
    observations=(mean+u)[:,None]+e
    ids=tuple(f"P{i:03d}-T{j:02d}" for i in range(n) for j in range(trials))
    metadata=pd.DataFrame({
        "participant_id":[f"P{i:03d}" for i in range(n) for _ in range(trials)],
        "trial_id":[j for _ in range(n) for j in range(trials)],
    })
    gaze=TrajectorySet(
        time=TIME.copy(),values=observations.reshape(n*trials,len(TIME),len(DIMS)),
        curve_ids=ids,dimension_names=DIMS,coordinate_system="normalized",
        time_unit="s",metadata=metadata,
        provenance={"simulation":True,"study":STUDY,"block":block,
                    "design":design,"support":support},
    )
    frame=pd.DataFrame({"curve_id":ids,"condition":np.repeat(cond,trials)})
    X=np.column_stack((np.ones(n),cond))
    return gaze,frame,truth,X,observations.mean(axis=1)

def hc2_gaussian_covariance_maxima(X,Y,beta,*,seed,draws=DRAW_B):
    """No true covariance input. HC2-adjusted *unit residual* covariance.

    C_hat = (1/n) sum_i [r_i/sqrt(1-h_ii)] outer [r_i/sqrt(1-h_ii)].
    For source-independent Gaussian units with a common covariance C,
    E[C_hat | X] = C (HC2 marginal residual correction).
    The covariance is finite-rank when grid dimension > n; deliberately
    retain PSD/no forced positive-definite inversion. Conditional Gaussian
    coefficient-error draws have slope variance scalar g_11*C_hat.
    """
    n=X.shape[0]
    if X.shape!=(n,2) or Y.shape!=(n,len(TIME),len(DIMS)) or beta.shape!=(2,len(TIME),len(DIMS)):
        raise ValueError("R72 HC2 covariance source shape invalid")
    inverse=np.linalg.inv(X.T@X)
    H=np.sum((X@inverse)*X,axis=1)
    if np.any(H>=1-1e-9) or np.any(H<0) or not np.isfinite(H).all():
        raise ValueError("R72 HC2 adjustment undefined at unit leverage boundary")
    residual=Y-np.einsum("np,ptd->ntd",X,beta,optimize=True)
    # Draws from factor*factor.T without imposing a spurious full-rank inverse.
    factor=residual.reshape(n,-1)/np.sqrt(1-H)[:,None]/np.sqrt(n)
    covariance_diag=np.sum(factor**2,axis=0)
    if np.any(covariance_diag<=MIN_VARIANCE) or not np.isfinite(covariance_diag).all():
        raise ValueError("R72 source estimated covariance diagonal nonpositive")
    se=np.sqrt(float(inverse[1,1])*covariance_diag).reshape(len(TIME),len(DIMS))
    rng=np.random.default_rng(seed)
    z=rng.standard_normal((draws,n))
    gaussian=z@factor
    maxima=np.max(np.abs(gaussian)/np.sqrt(covariance_diag)[None],axis=1)
    if maxima.shape!=(draws,) or not np.isfinite(maxima).all():
        raise ValueError("R72 estimated Gaussian reference invalid")
    critical=float(np.quantile(maxima,CONFIDENCE,method=QUANTILE))
    return {"critical":critical,"maxima":maxima,
            "estimated_se":se,"unit_hat":H,
            "covariance_trace":float(covariance_diag.sum()),
            "covariance_effective_rank_upper":min(n-2,len(TIME)*len(DIMS))}

def case(block,design,support):
    row={
        "study":STUDY,"block":block,"design":design,"support":support,
        "source_seed":source_seed(block,design),
        "wild_seed":wild_seed(block,design,support),
        "estimated_gaussian_seed":gaussian_seed(block,design,support),
        "completed":False,"exception":None,"refused":True,
        "source_units":72 if design=="curve" else 36,
        "observed_curves":72 if design=="curve" else 108,
        "coverage":{name:None for name in METHODS},
        "pivots":{name:None for name in METHODS},
        "criticals":{name:None for name in METHODS},
        "mean_estimated_HC2_over_true_SE":None,
        "mean_HC1_over_true_SE":None,
        "maximum_unit_hat":None,
        "HC2_covariance_trace":None,
        "HC2_covariance_effective_rank_upper":None,
        "package_HC1_OLS_max_error":None,
        "package_wild_max_reference_error":None,
        "estimated_HC2_Gaussian_999_maxima":None,
        "original_wild_999_maxima":None,
        # Raw artificial source unit means and design retained for future
        # independent reconstruction of the estimated covariance method.
        "original_artificial_X":None,
        "original_artificial_Y_unit_means":None,
        "original_function_truth_slope":None,
        "calibrated_90pct_simultaneous_band":False,
        "source_law_not_a_real_data_covariance_estimator":True,
        "release_authorized":False,
    }
    try:
        gaze,frame,truth,X,Y=simulate(block,design,support)
        fit=run_function_on_scalar_workflow(
            gaze,frame,
            config=FunctionOnScalarWorkflowConfig(
                predictors=("condition",),dimensions=DIMS,unit=design,
                participant_column="participant_id" if design=="participant" else None,
            ),
        ).fit
        beta,hc1=independent_hc1_oracle(X,Y)
        coeff_err=float(np.max(np.abs(fit.coefficients-beta)))
        se_err=float(np.max(np.abs(fit.standard_errors-hc1)))
        if max(coeff_err,se_err)>ORACLE_TOL or np.any(hc1[1]<=0):
            raise ValueError("R72 original W3 OLS/HC1 numerical oracle mismatch")
        wb=bootstrap_function_on_scalar_coefficients(
            fit,n_bootstrap=DRAW_B,multiplier="rademacher",
            random_state=wild_seed(block,design,support))
        raw_wild=np.max(np.abs(
            (wb.bootstrap_coefficients[:,1]-fit.coefficients[None,1])/
            hc1[None,1]),axis=(1,2))
        cwild=float(np.quantile(raw_wild,CONFIDENCE,method=QUANTILE))
        est=hc2_gaussian_covariance_maxima(
            X,Y,beta,seed=gaussian_seed(block,design,support))
        true_se=r71.true_slope_standard_errors(X,design)
        known=r71.known_law_reference(design)
        diff=beta[1]-truth[1]
        stderr={"original_wild_HC1":hc1[1],
                "estimated_HC2_Gaussian":est["estimated_se"],
                "known_Gaussian_law":true_se}
        criticals={"original_wild_HC1":cwild,
                   "estimated_HC2_Gaussian":est["critical"],
                   "known_Gaussian_law":known["critical"]}
        pivots={k:float(np.max(np.abs(diff/std))) for k,std in stderr.items()}
        coverage={k:bool(pivots[k]<=criticals[k]) for k in METHODS}
        row.update({
            "completed":True,"exception":None,"refused":False,
            "coverage":coverage,"pivots":pivots,"criticals":criticals,
            "mean_estimated_HC2_over_true_SE":float(
                np.mean(est["estimated_se"]/true_se)),
            "mean_HC1_over_true_SE":float(np.mean(hc1[1]/true_se)),
            "maximum_unit_hat":float(np.max(est["unit_hat"])),
            "HC2_covariance_trace":est["covariance_trace"],
            "HC2_covariance_effective_rank_upper":est["covariance_effective_rank_upper"],
            "package_HC1_OLS_max_error":max(coeff_err,se_err),
            "package_wild_max_reference_error":abs(
                cwild-float(np.quantile(raw_wild,CONFIDENCE,method=QUANTILE))),
            "estimated_HC2_Gaussian_999_maxima":est["maxima"].tolist(),
            "original_wild_999_maxima":raw_wild.tolist(),
            "original_artificial_X":X.tolist(),
            "original_artificial_Y_unit_means":Y.tolist(),
            "original_function_truth_slope":truth[1].tolist(),
        })
    except Exception as exc:
        row["exception"]={"type":type(exc).__name__,"message":str(exc)[:750]}
    return row

def summarize(rows):
    expected={(b,d,s) for b in range(BLOCKS) for d in DESIGNS for s in SUPPORT}
    ids=[(q["block"],q["design"],q["support"]) for q in rows]
    if len(ids)!=SOURCE_CASES or len(set(ids))!=SOURCE_CASES or set(ids)!=expected:
        raise ValueError("R72 missing/duplicate primitive generating source identities")
    detail={}
    matched={}
    for design in DESIGNS:
        detail[design]={}
        for support in SUPPORT:
            sub=[r for r in rows if r["design"]==design and r["support"]==support]
            for r in sub:
                if (r["study"]!=STUDY or r["source_seed"]!=source_seed(r["block"],design)
                    or r["wild_seed"]!=wild_seed(r["block"],design,support)
                    or r["estimated_gaussian_seed"]!=gaussian_seed(r["block"],design,support)
                    or r["calibrated_90pct_simultaneous_band"] is not False
                    or r["source_law_not_a_real_data_covariance_estimator"] is not True
                    or r["release_authorized"] is not False):
                    raise ValueError("R72 original source/seed/release contract changed")
                if r["completed"]:
                    if (r["refused"] or r["exception"] is not None
                        or any(type(r["coverage"][k]) is not bool for k in METHODS)
                        or any(not math.isfinite(float(r["pivots"][k])) for k in METHODS)
                        or any(not math.isfinite(float(r["criticals"][k])) for k in METHODS)
                        or any(r["coverage"][k]!=(r["pivots"][k]<=r["criticals"][k]) for k in METHODS)
                        or len(r["estimated_HC2_Gaussian_999_maxima"])!=DRAW_B
                        or len(r["original_wild_999_maxima"])!=DRAW_B
                        or r["package_HC1_OLS_max_error"]>ORACLE_TOL
                        or r["package_wild_max_reference_error"]>ORACLE_TOL):
                        raise ValueError("R72 false successful observation or incomplete numerical ledger")
                elif r["exception"] is None or not r["refused"]:
                    raise ValueError("R72 original refused source has no permanent refusal")
            success=[r for r in sub if r["completed"]]
            n=len(success)
            detail[design][support]={
                "independent_primitive_blocks":BLOCKS,
                "attempted_source_cases":BLOCKS,
                "completed":n,"refused":BLOCKS-n,
                "methods":{name:{
                    "truth_inclusions_complete":sum(x["coverage"][name] for x in success),
                    "Wilson95_complete":wilson(sum(x["coverage"][name] for x in success),n),
                    "full_denominator_lower":sum(x["coverage"][name] for x in success)/BLOCKS,
                    "full_denominator_upper":(sum(x["coverage"][name] for x in success)+BLOCKS-n)/BLOCKS,
                } for name in METHODS},
                "mean_HC1_over_known_SE":float(np.mean([x["mean_HC1_over_true_SE"] for x in success])) if n else None,
                "mean_HC2_over_known_SE":float(np.mean([x["mean_estimated_HC2_over_true_SE"] for x in success])) if n else None,
                "mean_estimated_Gaussian_critical":float(np.mean(
                    [x["criticals"]["estimated_HC2_Gaussian"] for x in success])) if n else None,
            }
            for a,b in (("estimated_HC2_Gaussian","original_wild_HC1"),
                        ("known_Gaussian_law","estimated_HC2_Gaussian")):
                vals=[int(x["coverage"][a])-int(x["coverage"][b]) for x in success]
                missing=BLOCKS-n
                matched[f"{design}/{support}/{a}_minus_{b}"]={
                    "completed_primitive_blocks":n,"refused_primitive_blocks":missing,
                    "first_only_truth_included":sum(v==1 for v in vals),
                    "second_only_truth_included":sum(v==-1 for v in vals),
                    "agreement":sum(v==0 for v in vals),
                    "mean_difference_complete":sum(vals)/n if n else None,
                    "full_denominator_lower":(sum(vals)-missing)/BLOCKS,
                    "full_denominator_upper":(sum(vals)+missing)/BLOCKS,
                }
    return {"study":STUDY,"new_independent_primitive_blocks":BLOCKS,
            "paired_design_and_support_cases":SOURCE_CASES,
            "source_seed":SOURCE_SEED,"estimated_Gaussian_seed":GAUSSIAN_SEED,
            "original_wild_seed":WILD_SEED,
            "Gaussian_reference_draws_per_original_case":DRAW_B,
            "original_wild_draws_per_original_case":DRAW_B,
            "method_labels":list(METHODS),"per_cell":detail,
            "paired_source_coverage_differences":matched,
            "known_law_reference_from_frozen_R71":True,
            "estimated_covariance_is_HC2_unit_residual":True,
            "no_independent_original_ledger_audit_yet":True,
            "no_90pct_simultaneous_qualification":True,
            "no_missingness_or_MNAR_examined":True,
            "release_authorized":False}

def shard(out,start,stop):
    if (start,stop) not in SHARDS:
        raise ValueError("R72 unregistered immutable 8-block original source shard")
    out.mkdir(parents=True,exist_ok=True)
    rows=[case(b,d,s) for b in range(start,stop) for d in DESIGNS for s in SUPPORT]
    raw=(json.dumps(rows,sort_keys=True,allow_nan=False,indent=2)+"\n").encode("utf-8")
    (out/"cases.json").write_bytes(raw)
    (out/"manifest.json").write_bytes((json.dumps({
        "study":STUDY,"start":start,"stop":stop,
        "source_seed":SOURCE_SEED,"Gaussian_seed":GAUSSIAN_SEED,
        "wild_seed":WILD_SEED,"checkout":os.environ.get("GITHUB_SHA","unverified-local"),
        "source_count":len(rows),"sha256_cases":sha256(raw).hexdigest()
    },sort_keys=True,indent=2)+"\n").encode("utf-8"))

def aggregate(out,parts):
    shards=list(parts.glob("*/manifest.json"))
    if len(shards)!=len(SHARDS):
        raise ValueError("R72 all four immutable source shards required")
    commit=os.environ.get("GITHUB_SHA","unverified-local")
    ids=set()
    rows=[]
    for path in shards:
        item=json.loads(path.read_bytes())
        shard_id=(item["start"],item["stop"])
        if (shard_id not in SHARDS or shard_id in ids
            or item["checkout"]!=commit or item["study"]!=STUDY
            or item["source_seed"]!=SOURCE_SEED
            or item["Gaussian_seed"]!=GAUSSIAN_SEED or item["wild_seed"]!=WILD_SEED):
            raise ValueError("R72 mixed-checkout/seed or duplicate original source shard")
        ids.add(shard_id)
        raw=(path.parent/"cases.json").read_bytes()
        if sha256(raw).hexdigest()!=item["sha256_cases"]:
            raise ValueError("R72 immutable original source SHA256 mismatch")
        records=json.loads(raw)
        exp={(b,d,s) for b in range(*shard_id) for d in DESIGNS for s in SUPPORT}
        if (len(records)!=item["source_count"] or len(records)!=len(exp)
            or {(q["block"],q["design"],q["support"]) for q in records}!=exp):
            raise ValueError("R72 original source shard case identities corrupted")
        rows.extend(records)
    rows.sort(key=lambda r:(r["block"],DESIGNS.index(r["design"]),SUPPORT.index(r["support"])))
    report=summarize(rows)
    out.mkdir(parents=True,exist_ok=True)
    (out/"cases.json").write_bytes((json.dumps(
        rows,sort_keys=True,allow_nan=False)+"\n").encode("utf-8"))
    (out/"summary.json").write_bytes((json.dumps(
        report,sort_keys=True,indent=2,allow_nan=False)+"\n").encode("utf-8"))
    (out/"source-commit.txt").write_bytes((commit+"\n").encode("utf-8"))
    (out/"SHA256SUMS").write_bytes("".join(
        sha256((out/name).read_bytes()).hexdigest()+"  "+name+"\n"
        for name in ("cases.json","summary.json","source-commit.txt")
    ).encode("utf-8"))
    print(json.dumps(report,sort_keys=True))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument("--start",type=int)
    g.add_argument("--merge-parts",type=Path)
    p.add_argument("--stop",type=int)
    a=p.parse_args()
    if a.merge_parts is not None: aggregate(a.out,a.merge_parts)
    elif a.stop is not None: shard(a.out,a.start,a.stop)
    else: raise SystemExit("R72 shard mode requires --stop")

if __name__=="__main__":
    main()
