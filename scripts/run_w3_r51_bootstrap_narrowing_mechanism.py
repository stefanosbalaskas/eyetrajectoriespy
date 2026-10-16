"""W3 R51: prospectively frozen mechanism decomposition of bootstrap-t narrowing.

Research only. NEW eight Gaussian primitive blocks × paired ordinary/extreme
predictor support, native n24 complete gaze, positive predictor-scaled
Gaussian random slope. Use 63 COMMON Gaussian standard-normal innovations
per source for two parametric GENERATION targets:
  fitted estimated covariance (empirically implementable), and
  true generating covariance (oracle diagnostic only; never an estimator).
Within fitted draws calculate frozen-covariance studentization AND full
4-component positive-physical REML refit studentization on identical y*.
Within oracle draws use same common normals, with full REML refits. Keep
all original/replicate optimizer start, CR2 refusal, source and intervals.
No global REML optimum, nominal pointwise 90% or functional simultaneous
coverage qualification. Original source numerical/identification gates frozen.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np
from scipy.stats import t as student_t

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts import run_w3_r17_fresh_feasibility as fresh
from scripts import run_w3_r48_independent_fitted_cr2 as r48
from scripts import run_w3_r49_nuisance_refit_bootstrap_t as r49
from scripts import run_w3_r50_independent_bootstrap_calibration as r50

STUDY="W3_R51_GAUSSIAN_BOOTSTRAP_T_NARROWING_MECHANISM_DECOMPOSITION"
SOURCE_SEED=202610165151
DRAW_SEED=202610165152
BLOCKS=8
PARTICIPANTS=24
SUPPORT=("ordinary_dependent","extreme_dependent")
DRAW_TYPES=("fitted_generation","oracle_generation")
N_BOOT=63
PARTITIONS=((0,4),(4,8))
NOMINAL=.90
METHODS=(
    "known_covariance_oracle_conditional_CR2",
    "fitted_covariance_conditional_CR2",
    "fitted_generation_fixed_nuisance_bootstrap_t",
    "fitted_generation_refit_nuisance_bootstrap_t",
    "oracle_generation_refit_nuisance_diagnostic_t",
)
N_SOURCE_CASES=BLOCKS*len(SUPPORT)
N_INTERVALS=N_SOURCE_CASES*len(METHODS)
N_DRAW_RECORDS=N_SOURCE_CASES*len(DRAW_TYPES)*N_BOOT
N_FITTED_REML_REFITS=N_DRAW_RECORDS
N_OPT_STARTS=(N_SOURCE_CASES+N_FITTED_REML_REFITS)*len(r49.START_RATIOS)


def source(block,support):
    if type(block) is not int or block not in range(BLOCKS) or support not in SUPPORT:
        raise ValueError("R51 source outside frozen independent primitive design")
    return fresh.fresh_source(
        block,support,n=PARTICIPANTS,master_seed=SOURCE_SEED,
        n_blocks=BLOCKS,max_n=PARTICIPANTS)


def problem(block,support):
    original=source(block,support)
    X,y,w,g,t,tr,x,c,truth,raw_truth=r48.native_data(original)
    oracle=r48.r32.known_gaussian_blocks(
        g,t,tr,x,w,r49.SLOPE_FAMILY)
    return {
        "X":X,"y":y,"w":w,"group":g,"time":t,"trial":tr,"x":x,
        "contrast":c,"truth":float(truth),"raw_truth":float(raw_truth),
        "oracle_covariance":oracle,
    }


def paired_draw(data,covariance,block,support,rep):
    """Use identical Gaussian innovations for fitted/oracle covariance draws.

    This is a paired *simulation diagnostic*: oracle covariance must never
    reach the original fitted model or fitted-generation bootstrap arm.
    """
    X,y,w=data["X"],data["y"],data["w"]
    Z=X*np.sqrt(w)[:,None]
    beta=np.linalg.lstsq(Z,y*np.sqrt(w),rcond=None)[0]
    pseudo=(X@beta).copy()
    groups=np.unique(data["group"])
    if len(groups)!=len(covariance):
        raise ValueError("covariance not aligned to 24 participant blocks")
    seed=int(DRAW_SEED+100003*block+711*SUPPORT.index(support)+rep)
    rng=np.random.default_rng(seed)
    for group,V in zip(groups,covariance):
        ids=np.flatnonzero(data["group"]==group)
        noise=rng.standard_normal(size=len(ids))
        pseudo[ids]+=(np.linalg.cholesky(V)@noise)/np.sqrt(w[ids])
    if not np.isfinite(pseudo).all():
        raise ValueError("nonfinite Gaussian pseudo-responses")
    return pseudo,seed


def observed_fit(data):
    """Exactly R49 two-start physical REML/KKT/NLL gate; never oracle."""
    return r49.fit_nuisance(
        {k:v for k,v in data.items() if k!="oracle_covariance"}
    )


def refused(name,why):
    return {"method":name,"status":"refused","reason":str(why)[:370],
            "truth_included":False,"not_qualified":True}


def interval(name,original_cr2,q,truth,diagnostic=False):
    point=float(original_cr2["point"])
    se=float(original_cr2["cr2_se"])
    if not all(np.isfinite(v) and v>0 for v in (se,q)):
        raise ValueError("R51 nonfinite/bootstrap critical refusal")
    half=se*float(q)
    return {
        "method":name,"status":"ok",
        "point":point,"critical_value":float(q),
        "half_width":float(half),
        "truth_included":bool(abs(point-truth)<=half),
        "oracle_generation_diagnostic_not_implementable":bool(diagnostic),
        "not_qualified":True,
    }


def diagnostic_record(rep,draw_type):
    return {
        "replicate":rep,"draw_type":draw_type,
        "status":"not_attempted","failure":None,"seed":None,
        "pivot_refit":None,"pivot_fixed":None,
        "refit_cr2_se":None,
        "numerical_starts":[
            {"label":label,"status":"not_attempted"}
            for label,_ in r49.START_RATIOS],
    }


def evaluate(block,support):
    row={
        "block":block,"support":support,"study":STUDY,
        "source_status":"failed","source_error":None,
        "projected_focal_truth":None,
        "original_fitted_nuisance":None,
        "intervals":[],"draws":[],
        "draw_generation_covariance_is_oracle_only_in_diagnostic":True,
        "original_Gaussian_blocks_independent_across_block_index":True,
        "support_variants_share_Gaussian_primitives":True,
        "release_authorized":False,
    }
    data=None
    original_oracle=None
    try:
        data=problem(block,support)
        row["source_status"]="ok"
        row["projected_focal_truth"]=data["truth"]
        row["generating_mean_projection_discrepancy"]=float(
            data["truth"]-data["raw_truth"])
        original_oracle=r49.cr2_on(data,data["oracle_covariance"])
        q=float(student_t.ppf(.95,original_oracle["satterthwaite_df"]))
        row["intervals"].append(interval(
            METHODS[0],original_oracle,q,data["truth"]))
    except Exception as exc:
        row["source_error"]=repr(exc)[:360]
        row["intervals"].append(refused(METHODS[0],row["source_error"]))
    fitted=None
    fitted_cr2=None
    if data is not None:
        fitted=observed_fit(data)
        row["original_fitted_nuisance"]={
            k:v for k,v in fitted.items() if k!="working_blocks"}
    else:
        row["original_fitted_nuisance"]={
            "status":"not_attempted",
            "numerical_starts":[{"label":label,"status":"not_attempted"}
                               for label,_ in r49.START_RATIOS],
        }
    if fitted is not None and fitted["status"]=="accepted":
        try:
            fitted_cr2=r49.cr2_on(data,fitted["working_blocks"])
            q=float(student_t.ppf(.95,fitted_cr2["satterthwaite_df"]))
            row["intervals"].append(interval(
                METHODS[1],fitted_cr2,q,data["truth"]))
            row["fitted_cr2_satterthwaite_df"]=float(
                fitted_cr2["satterthwaite_df"])
        except Exception as exc:
            row["intervals"].append(refused(METHODS[1],repr(exc)))
    else:
        row["intervals"].append(refused(
            METHODS[1],"original fitted Gaussian REML numerical refusal"))

    for rep in range(N_BOOT):
        # Preserve original replicate order and fitted/oracle pairing;
        # computation order does not define statistical independence.
        for kind in DRAW_TYPES:
            record=diagnostic_record(rep,kind)
            if fitted_cr2 is not None and fitted is not None and data is not None:
                try:
                    cov=(fitted["working_blocks"] if kind==DRAW_TYPES[0]
                         else data["oracle_covariance"])
                    y_star,seed=paired_draw(data,cov,block,support,rep)
                    record["seed"]=seed
                    pseudo={k:v for k,v in data.items()
                            if k!="oracle_covariance"}
                    pseudo["y"]=y_star

                    # Fitted generation, fixed covariance studentization:
                    # same simulated pseudo response as nuisance-refit arm.
                    if kind==DRAW_TYPES[0]:
                        fixed=r49.cr2_on(pseudo,fitted["working_blocks"])
                        record["pivot_fixed"]=float(
                            (fixed["point"]-fitted_cr2["point"])/
                            fixed["cr2_se"])
                        if not np.isfinite(record["pivot_fixed"]):
                            raise ValueError("fixed-nuisance pivot not finite")

                    reestimated=observed_fit(pseudo)
                    record["numerical_starts"]=reestimated["numerical_starts"]
                    if reestimated["status"]!="accepted":
                        raise ValueError("two-start physical KKT/NLL refusal")
                    refit_cr2=r49.cr2_on(pseudo,reestimated["working_blocks"])
                    record["refit_cr2_se"]=float(refit_cr2["cr2_se"])
                    record["pivot_refit"]=float(
                        (refit_cr2["point"]-fitted_cr2["point"])/
                        refit_cr2["cr2_se"])
                    if not np.isfinite(record["pivot_refit"]):
                        raise ValueError("refit-nuisance pivot not finite")
                    record["status"]="ok"
                except Exception as exc:
                    record["status"]="refused"
                    record["failure"]=repr(exc)[:360]
            row["draws"].append(record)

    # Require all 126 original draw/refit slots before reporting any
    # simulated critical; no success-conditioning or redraw allowed.
    complete=len(row["draws"])==N_BOOT*len(DRAW_TYPES) and all(
        rec["status"]=="ok" for rec in row["draws"])
    if fitted_cr2 is not None and complete:
        fit_samples=[x for x in row["draws"]
                     if x["draw_type"]==DRAW_TYPES[0]]
        oracle_samples=[x for x in row["draws"]
                        if x["draw_type"]==DRAW_TYPES[1]]
        pivots={
            METHODS[2]:[abs(v["pivot_fixed"]) for v in fit_samples],
            METHODS[3]:[abs(v["pivot_refit"]) for v in fit_samples],
            METHODS[4]:[abs(v["pivot_refit"]) for v in oracle_samples],
        }
        for name in METHODS[2:]:
            try:
                q=float(np.quantile(pivots[name],NOMINAL,method="linear"))
                row["intervals"].append(interval(
                    name,fitted_cr2,q,data["truth"],
                    diagnostic=(name==METHODS[4])))
            except Exception as exc:
                row["intervals"].append(refused(name,repr(exc)))
    else:
        for name in METHODS[2:]:
            row["intervals"].append(refused(
                name,"missing one or more of 126 frozen original nuisance pivots"))
    return row


def summary(rows):
    universe={(b,s) for b in range(BLOCKS) for s in SUPPORT}
    ids=[(r["block"],r["support"]) for r in rows]
    if len(ids)!=len(set(ids)) or not set(ids).issubset(universe):
        raise ValueError("duplicate or unregistered R51 primitive source")
    for r in rows:
        if tuple(v["method"] for v in r["intervals"])!=METHODS:
            raise ValueError("R51 missing ordered interval arm/refusal")
        if len(r["draws"])!=N_BOOT*len(DRAW_TYPES):
            raise ValueError("R51 missing fixed bootstrap draw slots")
        if any(
            (v["replicate"],v["draw_type"])!=(i//2,DRAW_TYPES[i%2])
            for i,v in enumerate(r["draws"])
        ):
            raise ValueError("R51 bootstrap pairing/order compromised")
        if len(r["original_fitted_nuisance"]["numerical_starts"])!=2 or any(
            len(v["numerical_starts"])!=2 for v in r["draws"]
        ):
            raise ValueError("R51 physical nuisance start slots missing")

    intervals=[v for r in rows for v in r["intervals"]]
    draws=[v for r in rows for v in r["draws"]]
    all_starts=(sum(len(r["original_fitted_nuisance"]["numerical_starts"])
                    for r in rows)+sum(len(v["numerical_starts"]) for v in draws))
    strata={}
    for support in SUPPORT:
        cases=[r for r in rows if r["support"]==support]
        stats={}
        for method in METHODS:
            values=[i for r in cases for i in r["intervals"]
                    if i["method"]==method]
            valid=[v for v in values if v["status"]=="ok"]
            yes=sum(v["truth_included"] for v in valid)
            stats[method]={
                "planned_independent_blocks":BLOCKS,
                "recorded":len(values),"accepted":len(valid),
                "refused":len(values)-len(valid),
                "included_truth":yes,
                "all_planned_block_fraction":yes/BLOCKS,
                "wilson95_MC":r48.wilson(int(yes),BLOCKS),
                "mean_half_width_success_only":(
                    float(np.mean([v["half_width"] for v in valid]))
                    if valid else None),
            }
        pairs=[r for r in cases
               if all(v["status"]=="ok" for v in r["intervals"][1:])]
        strata[support]={
            "independent_primitive_blocks":BLOCKS,
            "recorded_sources":len(cases),
            "original_nuisance_fit_accepted":sum(
                r["original_fitted_nuisance"]["status"]=="accepted"
                for r in cases),
            "draws_accepted":sum(v["status"]=="ok"
                                 for r in cases for v in r["draws"]),
            "draws_refused":sum(v["status"]=="refused"
                                for r in cases for v in r["draws"]),
            "draws_not_attempted":sum(v["status"]=="not_attempted"
                                      for r in cases for v in r["draws"]),
            "fully_paired_valid_sources":len(pairs),
            "median_refit_over_fixed_critical_fitted_generation":(
                float(np.median([r["intervals"][3]["critical_value"]/
                                 r["intervals"][2]["critical_value"]
                                 for r in pairs])) if pairs else None),
            "median_oracle_over_fitted_generation_refit_critical":(
                float(np.median([r["intervals"][4]["critical_value"]/
                                 r["intervals"][3]["critical_value"]
                                 for r in pairs])) if pairs else None),
            "paired_refit_vs_fixed_inclusion_disagreements":sum(
                r["intervals"][2]["truth_included"]!=
                r["intervals"][3]["truth_included"] for r in pairs),
            "paired_oracle_vs_fitted_generation_refit_inclusion_disagreements":sum(
                r["intervals"][3]["truth_included"]!=
                r["intervals"][4]["truth_included"] for r in pairs),
            "methods":stats,
        }
    return {
        "study":STUDY,"master_seed":SOURCE_SEED,
        "independent_draw_seed":DRAW_SEED,
        "new_independent_primitive_blocks":BLOCKS,
        "paired_support_cases_not_independent_source_draws":True,
        "planned_source_cases":N_SOURCE_CASES,"recorded_source_cases":len(rows),
        "planned_interval_records":N_INTERVALS,
        "recorded_interval_records":len(intervals),
        "planned_Gaussian_draw_and_refit_records":N_DRAW_RECORDS,
        "recorded_Gaussian_draw_and_refit_records":len(draws),
        "planned_nuisance_two_start_outcomes":N_OPT_STARTS,
        "recorded_nuisance_two_start_outcomes":all_starts,
        "full_original_failure_inclusive_ledger":(
            len(rows)==N_SOURCE_CASES and len(intervals)==N_INTERVALS
            and len(draws)==N_DRAW_RECORDS and all_starts==N_OPT_STARTS),
        "strata":strata,
        "oracle_generated_pseudodata_only_diagnostic_NOT_feasible_estimator":True,
        "no_global_REML_optimum_certificate":True,
        "no_90pct_pointwise_coverage_qualification":True,
        "no_simultaneous_90pct_whole_function_bands":True,
        "no_boundary_null_variance_test_qualification":True,
        "no_MNAR_or_whole_participant_selection_identification":True,
        "release_authorized":False,
    }


def _write(path,obj):
    path.write_text(json.dumps(obj,sort_keys=True,indent=2,allow_nan=False)+"\n")


def shard(out,start,stop):
    if (start,stop) not in PARTITIONS:
        raise ValueError("R51 refused unregistered source shard")
    out.mkdir(parents=True,exist_ok=True)
    cases=[evaluate(i,s) for i in range(start,stop) for s in SUPPORT]
    _write(out/"cases.json",cases)
    _write(out/"manifest.json",{
        "study":STUDY,"start":start,"stop":stop,
        "cases":len(cases),"seed":SOURCE_SEED,
        "source_checkout":os.environ.get("GITHUB_SHA","unverified-local"),
        "sha256_cases":hashlib.sha256((out/"cases.json").read_bytes()).hexdigest(),
    })


def aggregate(out,parts):
    manifests=sorted(parts.glob("*/manifest.json"))
    if len(manifests)!=len(PARTITIONS):
        raise ValueError("R51 missing required original shards")
    cases=[]
    found=set()
    source_sha=os.environ.get("GITHUB_SHA","unverified-local")
    for path in manifests:
        m=json.loads(path.read_text())
        part=(m["start"],m["stop"])
        if (part not in PARTITIONS or part in found or
                m["study"]!=STUDY or m["seed"]!=SOURCE_SEED or
                m["source_checkout"]!=source_sha):
            raise ValueError("R51 duplicated, wrong-seed or wrong-checkout shard")
        found.add(part)
        blob=(path.parent/"cases.json").read_bytes()
        if hashlib.sha256(blob).hexdigest()!=m["sha256_cases"]:
            raise ValueError("R51 shard checksum mismatch")
        case=json.loads(blob)
        required={(b,s) for b in range(*part) for s in SUPPORT}
        if len(case)!=m["cases"] or {(r["block"],r["support"])
                                     for r in case}!=required:
            raise ValueError("R51 expected per-shard primitive IDs not found")
        cases.extend(case)
    if found!=set(PARTITIONS):
        raise ValueError("R51 some original primitive blocks absent")
    cases.sort(key=lambda r:(r["block"],SUPPORT.index(r["support"])))
    report=summary(cases)
    out.mkdir(parents=True,exist_ok=True)
    _write(out/"cases.json",cases)
    _write(out/"summary.json",report)
    (out/"source-commit.txt").write_text(source_sha+"\n")
    files=("cases.json","summary.json","source-commit.txt")
    (out/"SHA256SUMS").write_text("".join(
        hashlib.sha256((out/f).read_bytes()).hexdigest()+"  "+f+"\n"
        for f in files))
    print("R51 original mechanism decomposition:",json.dumps(report,sort_keys=True))
    if not report["full_original_failure_inclusive_ledger"]:
        raise SystemExit("R51 original incomplete numerical/source evidence")


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--start",type=int)
    group.add_argument("--merge-parts",type=Path)
    parser.add_argument("--stop",type=int)
    args=parser.parse_args()
    if args.merge_parts is not None:
        aggregate(args.out,args.merge_parts)
    elif args.stop is not None:
        shard(args.out,args.start,args.stop)
    else:
        raise SystemExit("R51 original source shard needs --stop")


if __name__=="__main__":
    main()
