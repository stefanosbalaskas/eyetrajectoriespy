"""R75 research-only NEW-source Gaussian 2x2 marginal-SE x correlation audit.

Crosses source-known vs weighted-HC3 estimated marginal slope SE and
source-known vs weighted-HC3 estimated standardized Gaussian maximum reference.
The source-known components are *simulation-only*, never a public inference API.
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
from eyetrajectoriespy.workflows import (
    FunctionOnScalarWorkflowConfig,run_function_on_scalar_workflow,
)
from scripts.run_w3_fixed_truth_interval_pilot import independent_hc1_oracle,wilson
from scripts.run_w3_known_truth_workflow_validation import TIME,DIMS,truth_coefficients
from scripts import run_w3_r71_new_known_gaussian_band_oracle as r71

STUDY="W3_R75_FRESH_GAUSSIAN_MARGINAL_SE_CORRELATION_CROSS"
SOURCE_SEED=202610207575
GAUSSIAN_SEED=202610207576
BLOCKS=32
DESIGNS=("curve_standard","participant_standard")
SUPPORT=("ordinary","extreme")
VARIANCE=("constant","predictor_heteroskedastic")
SHARDS=((0,8),(8,16),(16,24),(24,32))
CELLS=("estimated_SE_estimated_correlation","known_SE_estimated_correlation",
       "estimated_SE_known_correlation","known_SE_known_correlation")
N_CASES=BLOCKS*len(DESIGNS)*len(SUPPORT)*len(VARIANCE)
B=999
CONF=.90
TOL=2e-10


def _check(block,design,support,variance):
    if (type(block) is not int or not 0<=block<BLOCKS or design not in DESIGNS
        or support not in SUPPORT or variance not in VARIANCE):
        raise ValueError("R75 original source identity outside prospective plan")


def random_seed(block,design,support,variance,stream):
    _check(block,design,support,variance)
    i=DESIGNS.index(design)
    if stream=="source":return SOURCE_SEED+100003*block+10007*i
    if stream=="gaussian":
        return GAUSSIAN_SEED+1000003*block+10007*i+739*SUPPORT.index(support)+37*VARIANCE.index(variance)
    raise ValueError("R75 unknown independent RNG stream")


def simulate(block,design,support,variance):
    _check(block,design,support,variance)
    participant=design=="participant_standard"
    n,trials=(36,3) if participant else (72,1)
    unit="participant" if participant else "curve"
    rng=np.random.default_rng(random_seed(block,design,support,variance,"source"))
    predictor=rng.uniform(-.95,.95,size=n)
    if support=="extreme":
        predictor[0],predictor[-1]=-4.,4.
    scales=np.ones(n) if variance=="constant" else 1+.75*np.abs(predictor)
    true=truth_coefficients()
    mean=true[0][None]+predictor[:,None,None]*true[1][None]
    random_part=np.zeros((n,len(TIME),len(DIMS)))
    if participant:
        random_part=rng.normal(0,.065,size=(n,1,len(DIMS)))*(1+.35*TIME[None,:,None])
    noise=rng.normal(0,.04,size=(n,trials,len(TIME),len(DIMS)))
    observations=mean[:,None]+scales[:,None,None,None]*(random_part[:,None]+noise)
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
                    "design":design,"support":support,"variance":variance},
    )
    frame=pd.DataFrame({"curve_id":ids,"condition":np.repeat(predictor,trials)})
    X=np.column_stack((np.ones(n),predictor))
    return gaze,frame,true,X,observations.mean(axis=1),scales


def true_slope_se(X,scales,unit):
    inverse=np.linalg.inv(X.T@X)
    a=(inverse@X.T)[1]
    factor=float(np.sum((a*scales)**2))
    if not math.isfinite(factor) or factor<=0:
        raise ValueError("R75 source known slope variance invalid")
    return np.sqrt(factor*r71.unit_covariance_variance(unit))


def estimated_HC3_correlation(X,Y,beta,gaussian_seed):
    n=len(X)
    inverse=np.linalg.inv(X.T@X)
    projector=inverse@X.T
    h=np.sum(X*projector.T,axis=1)
    if np.min(h)<=0 or np.max(h)>=1-1e-9 or not np.isfinite(h).all():
        raise ValueError("R75 observed leverage near HC3 singularity")
    a=projector[1]
    r=(Y-np.einsum("np,ptd->ntd",X,beta,optimize=True)).reshape(n,-1)
    factors=r*(a/(1-h))[:,None]
    d=np.sum(factors**2,axis=0)
    if np.any(d<=1e-14) or not np.isfinite(d).all():
        raise ValueError("R75 estimated HC3 slope covariance diagonal invalid")
    Z=np.random.default_rng(gaussian_seed).standard_normal((B,n))
    ref=np.max(np.abs(Z@factors)/np.sqrt(d)[None],axis=1)
    crit=float(np.quantile(ref,CONF,method="higher"))
    energy=np.sum(factors*factors,axis=1)
    concentration=float(energy.sum()**2/np.sum(energy**2))
    # Descriptive energy participation ratio, NOT independently calibrated ESS
    return {"se":np.sqrt(d).reshape(len(TIME),len(DIMS)),
            "maxima":ref,"critical":crit,
            "hat":h,"energy_participation":concentration,
            "energy_weights":energy}


def evaluate(block,design,support,variance):
    _check(block,design,support,variance)
    n,trials,unit=(36,3,"participant") if design=="participant_standard" else (72,1,"curve")
    row={
        "study":STUDY,"block":block,"design":design,"support":support,
        "variance":variance,
        "source_seed":random_seed(block,design,support,variance,"source"),
        "gaussian_seed":random_seed(block,design,support,variance,"gaussian"),
        "independent_units":n,"trials_per_unit":trials,
        "observed_curves":n*trials,
        "completed":False,"refused":True,"exception":None,
        "coverage":{m:None for m in CELLS},
        "truth_pivot_known_SE":None,"truth_pivot_estimated_SE":None,
        "estimated_gaussian_critical":None,"known_gaussian_critical":None,
        "original_gaussian_999_maxima":None,
        "estimated_HC3_slope_SE_grid":None,"true_slope_SE_grid":None,
        "full_original_X":None,"full_original_Y_native_mean":None,
        "source_slope_truth_grid":None,"source_unit_scales":None,
        "source_observed_slope_error_grid":None,
        "max_unit_hat":None,"estimated_factor_energy_participation":None,
        "estimated_factor_energy_weights":None,
        "min_HC3_to_known_SE":None,"mean_HC3_to_known_SE":None,
        "max_HC3_to_known_SE":None,
        "estimated_critical_to_known_critical":None,
        "W3_original_OLS_HC1_oracle_error":None,
        "not_a_qualified_90pct_data_estimated_band":True,
        "real_data_known_covariance_unavailable":True,
        "no_missingness_or_MNAR":True,
        "release_authorized":False,
    }
    try:
        gaze,frame,truth,X,Y,scales=simulate(block,design,support,variance)
        fit=run_function_on_scalar_workflow(
            gaze,frame,config=FunctionOnScalarWorkflowConfig(
                predictors=("condition",),dimensions=DIMS,unit=unit,
                participant_column="participant_id" if unit=="participant" else None)
        ).fit
        beta,hc1=independent_hc1_oracle(X,Y)
        err=max(float(np.max(np.abs(fit.coefficients-beta))),
                float(np.max(np.abs(fit.standard_errors-hc1))))
        if err>TOL or fit.unit!=unit or len(fit.unit_ids)!=n:
            raise ValueError("R75 unchanged W3 OLS/HC1 source numerical contract violated")
        hc3=estimated_HC3_correlation(
            X,Y,beta,gaussian_seed=random_seed(block,design,support,variance,"gaussian"))
        known_se=true_slope_se(X,scales,unit)
        known_crit=float(r71.known_law_reference(unit)["critical"])
        slope_error=beta[1]-truth[1]
        piv_est=float(np.max(np.abs(slope_error/hc3["se"])))
        piv_known=float(np.max(np.abs(slope_error/known_se)))
        criticals={"estimated":hc3["critical"],"known":known_crit}
        covered={
            "estimated_SE_estimated_correlation":piv_est<=criticals["estimated"],
            "known_SE_estimated_correlation":piv_known<=criticals["estimated"],
            "estimated_SE_known_correlation":piv_est<=criticals["known"],
            "known_SE_known_correlation":piv_known<=criticals["known"],
        }
        ratio=hc3["se"]/known_se
        row.update({
            "completed":True,"refused":False,
            "coverage":{k:bool(v) for k,v in covered.items()},
            "truth_pivot_known_SE":piv_known,"truth_pivot_estimated_SE":piv_est,
            "estimated_gaussian_critical":criticals["estimated"],
            "known_gaussian_critical":criticals["known"],
            "original_gaussian_999_maxima":hc3["maxima"].tolist(),
            "estimated_HC3_slope_SE_grid":hc3["se"].tolist(),
            "true_slope_SE_grid":known_se.tolist(),
            "full_original_X":X.tolist(),
            "full_original_Y_native_mean":Y.tolist(),
            "source_slope_truth_grid":truth[1].tolist(),
            "source_unit_scales":scales.tolist(),
            "source_observed_slope_error_grid":slope_error.tolist(),
            "max_unit_hat":float(np.max(hc3["hat"])),
            "estimated_factor_energy_participation":hc3["energy_participation"],
            "estimated_factor_energy_weights":hc3["energy_weights"].tolist(),
            "min_HC3_to_known_SE":float(np.min(ratio)),
            "mean_HC3_to_known_SE":float(np.mean(ratio)),
            "max_HC3_to_known_SE":float(np.max(ratio)),
            "estimated_critical_to_known_critical":criticals["estimated"]/criticals["known"],
            "W3_original_OLS_HC1_oracle_error":err,
        })
    except Exception as e:
        row["exception"]={"type":type(e).__name__,"message":str(e)[:700]}
    return row


def summarize(rows):
    expected={(b,d,s,v) for b in range(BLOCKS) for d in DESIGNS
              for s in SUPPORT for v in VARIANCE}
    keys=[(x["block"],x["design"],x["support"],x["variance"]) for x in rows]
    if len(keys)!=N_CASES or len(set(keys))!=N_CASES or set(keys)!=expected:
        raise ValueError("R75 source grid omitted/duplicated primitive independent blocks")
    cells={};pairs={}
    for design in DESIGNS:
        cells[design]={}
        for support in SUPPORT:
            cells[design][support]={}
            for variance in VARIANCE:
                records=[x for x in rows if x["design"]==design and
                         x["support"]==support and x["variance"]==variance]
                for x in records:
                    if (x["study"]!=STUDY
                        or x["source_seed"]!=random_seed(x["block"],design,support,variance,"source")
                        or x["gaussian_seed"]!=random_seed(x["block"],design,support,variance,"gaussian")
                        or x["not_a_qualified_90pct_data_estimated_band"] is not True
                        or x["real_data_known_covariance_unavailable"] is not True
                        or x["no_missingness_or_MNAR"] is not True or x["release_authorized"] is not False):
                        raise ValueError("R75 source provenance/inference release invariant invalid")
                    if x["completed"]:
                        if (x["refused"] or x["exception"] is not None
                            or set(x["coverage"])!=set(CELLS)
                            or any(type(x["coverage"][m]) is not bool for m in CELLS)
                            or len(x["original_gaussian_999_maxima"])!=B
                            or x["W3_original_OLS_HC1_oracle_error"]>TOL):
                            raise ValueError("R75 accepted source invalid Gaussian/OLS numerical contract")
                        expected_events={
                            "estimated_SE_estimated_correlation":x["truth_pivot_estimated_SE"]<=x["estimated_gaussian_critical"],
                            "known_SE_estimated_correlation":x["truth_pivot_known_SE"]<=x["estimated_gaussian_critical"],
                            "estimated_SE_known_correlation":x["truth_pivot_estimated_SE"]<=x["known_gaussian_critical"],
                            "known_SE_known_correlation":x["truth_pivot_known_SE"]<=x["known_gaussian_critical"],
                        }
                        if any(x["coverage"][k] is not v for k,v in expected_events.items()):
                            raise ValueError("R75 false original crossed source truth inclusion event")
                    elif not x["refused"] or x["exception"] is None:
                        raise ValueError("R75 source failed but not refusal-inclusive")
                good=[x for x in records if x["completed"]]
                missing=BLOCKS-len(good)
                inclusion={}
                for method in CELLS:
                    k=sum(x["coverage"][method] for x in good)
                    inclusion[method]={
                        "attempted_independent_primitive_blocks":BLOCKS,
                        "complete_sources":len(good),"source_failures":missing,
                        "truth_included":k,
                        "complete_rate":k/len(good) if good else None,
                        "full_denominator_lower":k/BLOCKS,
                        "full_denominator_upper":(k+missing)/BLOCKS,
                        "Wilson95_complete":wilson(k,len(good)),
                    }
                cells[design][support][variance]={
                    "attempted":BLOCKS,"complete":len(good),"failed":missing,
                    "inclusions":inclusion,
                    "mean_HC3_to_true_SE":float(np.mean([
                        x["mean_HC3_to_known_SE"] for x in good])) if good else None,
                    "mean_estimated_to_known_critical":float(np.mean([
                        x["estimated_critical_to_known_critical"] for x in good])) if good else None,
                    "mean_estimated_factor_energy_participation":float(np.mean([
                        x["estimated_factor_energy_participation"] for x in good])) if good else None,
                }
                for first,second in (
                    ("known_SE_estimated_correlation","estimated_SE_estimated_correlation"),
                    ("estimated_SE_known_correlation","estimated_SE_estimated_correlation"),
                    ("known_SE_known_correlation","known_SE_estimated_correlation"),
                    ("known_SE_known_correlation","estimated_SE_known_correlation"),
                ):
                    delta=[int(x["coverage"][first])-int(x["coverage"][second]) for x in good]
                    pairs[f"{design}/{support}/{variance}/{first}_minus_{second}"]={
                        "completed_primitive_blocks":len(good),
                        "refused_primitive_blocks":missing,
                        "first_only_included":sum(z==1 for z in delta),
                        "second_only_included":sum(z==-1 for z in delta),
                        "both_agree":sum(z==0 for z in delta),
                        "complete_source_change":sum(delta)/len(good) if good else None,
                        "full_denominator_lower":(sum(delta)-missing)/BLOCKS,
                        "full_denominator_upper":(sum(delta)+missing)/BLOCKS,
                        "not_causal_or_calibrated_method_superiority":True,
                    }
    return {
        "study":STUDY,
        "source_seed":SOURCE_SEED,"gaussian_seed":GAUSSIAN_SEED,
        "new_independent_primitive_blocks":BLOCKS,
        "source_cases":N_CASES,
        "designs":list(DESIGNS),"supports":list(SUPPORT),
        "variances":list(VARIANCE),"methods":list(CELLS),
        "per_source_gaussian_draw_count":B,
        "original_conditional_gaussian_vectors":N_CASES*B,
        "known_law_reference_draws_per_design":r71.ORACLE_K,
        "known_law_reference_draws_total":r71.ORACLE_TOTAL,
        "same_source_correlations_and_SEs_algebraically_crossed_not_new_data":True,
        "per_cell":cells,"paired":pairs,
        "all_90pct_inferential_calibration_claims_withheld":True,
        "known_source_components_not_real_data_estimators":True,
        "no_MNAR":True,"release_authorized":False,
    }


def shard(out,start,stop):
    if (start,stop) not in SHARDS:raise ValueError("R75 source shard not preregistered")
    out.mkdir(parents=True,exist_ok=True)
    rows=[evaluate(b,d,s,v) for b in range(start,stop) for d in DESIGNS
          for s in SUPPORT for v in VARIANCE]
    raw=(json.dumps(rows,allow_nan=False,sort_keys=True,indent=2)+"\n").encode()
    (out/"cases.json").write_bytes(raw)
    (out/"manifest.json").write_text(json.dumps({
        "study":STUDY,"start":start,"stop":stop,"source_seed":SOURCE_SEED,
        "gaussian_seed":GAUSSIAN_SEED,"original_checkout":os.environ.get("GITHUB_SHA","unverified-local"),
        "source_count":len(rows),"source_cases_sha256":sha256(raw).hexdigest(),
    },sort_keys=True,indent=2)+"\n")


def aggregate(out,parts):
    files=list(parts.glob("*/manifest.json"))
    if len(files)!=len(SHARDS):raise ValueError("R75 all four source shards required")
    checkout=os.environ.get("GITHUB_SHA","unverified-local")
    seen=set();rows=[]
    for f in files:
        m=json.loads(f.read_bytes())
        ident=(m["start"],m["stop"])
        if (ident not in SHARDS or ident in seen or m["study"]!=STUDY
            or m["source_seed"]!=SOURCE_SEED or m["gaussian_seed"]!=GAUSSIAN_SEED
            or m["original_checkout"]!=checkout):
            raise ValueError("R75 original source shard checkout/seed mismatch")
        seen.add(ident)
        raw=(f.parent/"cases.json").read_bytes()
        if sha256(raw).hexdigest()!=m["source_cases_sha256"]:
            raise ValueError("R75 original source SHA256 mismatch")
        part=json.loads(raw)
        expected={(b,d,s,v) for b in range(*ident) for d in DESIGNS
                  for s in SUPPORT for v in VARIANCE}
        if (len(part)!=m["source_count"] or len(part)!=len(expected)
            or {(q["block"],q["design"],q["support"],q["variance"]) for q in part}!=expected):
            raise ValueError("R75 original source shard complete-grid count mismatch")
        rows.extend(part)
    rows.sort(key=lambda q:(q["block"],DESIGNS.index(q["design"]),
                            SUPPORT.index(q["support"]),VARIANCE.index(q["variance"])))
    result=summarize(rows)
    reference={
        unit:r71.known_law_reference(unit)
        for unit in ("curve","participant")
    }
    for row in rows:
        if row["completed"]:
            unit="curve" if row["design"]=="curve_standard" else "participant"
            if not math.isclose(row["known_gaussian_critical"],reference[unit]["critical"],rel_tol=0,abs_tol=1e-12):
                raise ValueError("R75 frozen known Gaussian source critical changed")
    out.mkdir(parents=True,exist_ok=True)
    (out/"cases.json").write_text(json.dumps(rows,sort_keys=True,allow_nan=False)+"\n")
    (out/"summary.json").write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n")
    (out/"known_gaussian_reference.json").write_text(json.dumps(reference,sort_keys=True,allow_nan=False)+"\n")
    (out/"source-commit.txt").write_text(checkout+"\n")
    names=("cases.json","summary.json","known_gaussian_reference.json","source-commit.txt")
    (out/"SHA256SUMS").write_text("".join(
        sha256((out/n).read_bytes()).hexdigest()+"  "+n+"\n" for n in names))
    print(json.dumps({
        "study":STUDY,"original_checkout":checkout,
        "source_cases":len(rows),"refusals":sum(not q["completed"] for q in rows),
        "known_critical":{name:r["critical"] for name,r in reference.items()},
        "summary":result,
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
        raise SystemExit("R75 source --start requires --stop")
if __name__=="__main__":
    main()
