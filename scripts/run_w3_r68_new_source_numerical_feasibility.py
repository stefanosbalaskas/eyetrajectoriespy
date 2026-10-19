"""R68 prospectively frozen NEW-Gaussian-source solver feasibility only.

Never use this four-draw study for test size, candidate detection, power, or
confidence intervals. Original R66 source artifacts and refusals stay immutable.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from collections import Counter
from pathlib import Path

import numpy as np

from scripts import run_w3_r16_leverage_covariance_factorial as r16
from scripts import run_w3_r17_fresh_feasibility as fresh
from scripts import run_w3_r48_independent_fitted_cr2 as r48
from scripts import run_w3_r58_boundary_null_reference as r58
from scripts import run_w3_r63_independent_null_replication as core

STUDY="W3_R68_PROSPECTIVE_NEW_SOURCE_NUMERICAL_FEASIBILITY_ONLY"
MASTER_SEED=202610196868
DRAW_SEED=202610196869
BLOCKS=8
PARTICIPANTS=24
SUPPORT=("ordinary_dependent","extreme_dependent")
LEVELS=("zero","half","full")
MULTIPLIERS={"zero":0.,"half":.5,"full":1.}
B=4
SHARDS=((0,4),(4,8))
CASES=BLOCKS*len(SUPPORT)*len(LEVELS)
DRAWS=CASES*B
NESTED_POSITIONS=2*(CASES+DRAWS)
START_POSITIONS=6*(CASES+DRAWS)
KKT_TOL=.001
NLL_TOL=.001
NEST_TOL=1e-5


def source(block:int,support:str,level:str)->dict:
    if type(block) is not int or not 0<=block<BLOCKS or support not in SUPPORT or level not in LEVELS:
        raise ValueError("R68 NEW original source outside frozen primitive paired design")
    case=fresh.fresh_source(block,support,n=PARTICIPANTS,master_seed=MASTER_SEED,
                             n_blocks=BLOCKS,max_n=PARTICIPANTS)
    X,y,w,g,t,tr,x,*_=r48.native_data(case)
    z=np.asarray(case[0]["participant_slope"],float)[np.asarray(g,int),0,0,0]
    component=r16.SIGMA_RANDOM_SLOPE*z*x*(1.+.25*t)
    multiplier=MULTIPLIERS[level]
    response=np.asarray(y,float)-(1.-multiplier)*component
    if not np.isfinite(response).all():
        raise ValueError("R68 nonfinite new Gaussian source")
    return {
        "X":X,"y":response,"w":w,"group":g,"time":t,"trial":tr,"x":x,
        "true_slope_variance":float((multiplier*r16.SIGMA_RANDOM_SLOPE)**2),
        "full_slope_component_L2":float(np.linalg.norm(component)),
        "retained_slope_component_L2":float(multiplier*np.linalg.norm(component)),
    }


def conditional_h0_response(data:dict,beta,cov,block:int,support:str,level:str,draw:int):
    if type(block) is not int or not 0<=block<BLOCKS or support not in SUPPORT or level not in LEVELS or type(draw) is not int or not 0<=draw<B:
        raise ValueError("R68 conditional Gaussian source/draw outside frozen design")
    seed=DRAW_SEED+100003*block+739*SUPPORT.index(support)+1009*LEVELS.index(level)+draw
    rng=np.random.default_rng(seed)
    y=np.asarray(data["X"]@beta,float).copy()
    weights=np.asarray(data["w"],float)
    visited=np.zeros(len(y),bool)
    for ix,L in cov:
        if np.any(visited[ix]):
            raise ValueError("R68 repeated participant covariance rows")
        visited[ix]=True
        y[ix]+=(L@rng.standard_normal(len(ix)))/np.sqrt(weights[ix])
    if not visited.all() or not np.isfinite(y).all():
        raise ValueError("R68 incomplete conditional H0 Gaussian response")
    return {**data,"y":y},seed


def diagnostic(nested:dict)->dict:
    """Summarise ORIGINAL optimiser records; never reselect/start/reclassify."""
    a=nested["null_fit"]; b=nested["alternative_fit"]
    starts=b["original_starts"]
    finite=[s for s in starts if s.get("negative_loglik") is not None and
            math.isfinite(float(s["negative_loglik"]))]
    accepted=[s for s in finite if
              s["status"]=="ok" and s.get("optimizer_success") is True
              and s.get("objective_reconstruction_error") is not None
              and float(s["objective_reconstruction_error"])<=1e-6
              and s.get("physical_projected_KKT") is not None
              and float(s["physical_projected_KKT"])<=KKT_TOL]
    best=min((float(s["negative_loglik"]) for s in finite),default=None)
    eligible=min((float(s["negative_loglik"]) for s in accepted),default=None)
    gap=eligible-best if best is not None and eligible is not None else None
    best_start=next((s for s in finite if float(s["negative_loglik"])==best),None)
    raw=nested.get("raw_deviance")
    if a["status"]=="accepted" and b["status"]=="accepted":
        raw=2*(float(a["selected_NLL"])-float(b["selected_NLL"]))
    elif raw is not None:
        raise ValueError("R68 raw deviance without accepted original H0/H1")
    return {
        "observed_nested_status":nested["status"],
        "null_status":a["status"],
        "alternative_status":b["status"],
        "original_error":nested.get("error"),
        "H1_best_observed_NLL":best,
        "H1_best_KKT_eligible_NLL":eligible,
        "H1_eligible_minus_raw_best_NLL":gap,
        "H1_raw_best_KKT":None if best_start is None else best_start.get("physical_projected_KKT"),
        "H1_raw_best_label":None if best_start is None else best_start.get("label"),
        "H1_best_KKT_exceeds_original_001":None if best_start is None or best_start.get("physical_projected_KKT") is None else float(best_start["physical_projected_KKT"])>KKT_TOL,
        "H1_eligible_gap_exceeds_original_001":None if gap is None else gap>NLL_TOL,
        "raw_nested_deviance":raw,
        "negative_nested_deviance_beyond_original_tolerance":None if raw is None else raw<-NEST_TOL,
    }


def empty_draw(j:int)->dict:
    return {"draw":j,"seed":None,"status":"not_attempted","nested":core.nested_on_invalid(),
            "error":None}


def evaluate(block:int,support:str,level:str)->dict:
    row={
        "study":STUDY,"block":block,"support":support,"level":level,
        "true_slope_variance":float((MULTIPLIERS[level]*r16.SIGMA_RANDOM_SLOPE)**2),
        "source_status":"refused","source_error":None,
        "observed":core.nested_on_invalid(),
        "bootstrap":[empty_draw(i) for i in range(B)],
        "original_test_p_value":None,"candidate_rejection":None,
        "statistical_power_qualified":False,
        "fitted_CR2_90pct_qualified":False,"release_authorized":False,
    }
    try:
        data=source(block,support,level)
        row["source_status"]="ok"
        row["full_slope_component_L2"]=data["full_slope_component_L2"]
        row["retained_slope_component_L2"]=data["retained_slope_component_L2"]
        row["observed"]=core.nested_on(data)
        if row["observed"]["status"]!="accepted":
            return row
        beta,cov,_=core.h0_gls_covariance(
            data,row["observed"]["null_fit"],
            row["observed"]["observed_reference"])
        for k in range(B):
            try:
                pseudo,seed=conditional_h0_response(data,beta,cov,block,support,level,k)
                nested=core.nested_on(pseudo)
                row["bootstrap"][k]={
                    "draw":k,"status":nested["status"],"seed":seed,
                    "nested":nested,"error":None,
                }
            except Exception as exc:
                row["bootstrap"][k]={
                    "draw":k,"status":"refused","seed":None,
                    "nested":core.nested_on_invalid(),"error":repr(exc)[:450],
                }
    except Exception as exc:
        row["source_error"]=repr(exc)[:450]
    return row


def summarize(rows:list[dict])->dict:
    expect={(b,s,l) for b in range(BLOCKS) for s in SUPPORT for l in LEVELS}
    ids=[(q["block"],q["support"],q["level"]) for q in rows]
    if len(ids)!=CASES or len(set(ids))!=CASES or set(ids)!=expect:
        raise ValueError("R68 missing/duplicate original new Gaussian source IDs")
    all_draws=[]
    counts=Counter()
    gaps=[]
    deviances=[]
    all_seeds=[]
    refusals=[]
    for row in rows:
        if row["study"]!=STUDY or row["statistical_power_qualified"] is not False or row["fitted_CR2_90pct_qualified"] is not False or row["release_authorized"] is not False or row["original_test_p_value"] is not None or row["candidate_rejection"] is not None:
            raise ValueError("R68 source scientific claim or release gate altered")
        if len(row["bootstrap"])!=B or [x["draw"] for x in row["bootstrap"]]!=list(range(B)):
            raise ValueError("R68 missing or duplicated Gaussian numerical pseudodraw slots")
        for name,nested,draw in [("observed",row["observed"],None)]+[
              ("conditional",rec["nested"],rec) for rec in row["bootstrap"]]:
            d=diagnostic(nested)
            counts[f"{name}/{nested['status']}"]+=1
            if draw is not None:
                if draw["status"]!=nested["status"] and draw["error"] is None:
                    raise ValueError("R68 draw nested status mismatch without archived exception")
                if draw["seed"] is not None:
                    expected_seed=(DRAW_SEED+100003*row["block"]
                                   +739*SUPPORT.index(row["support"])
                                   +1009*LEVELS.index(row["level"])+draw["draw"])
                    if draw["seed"]!=expected_seed or draw["seed"] in all_seeds:
                        raise ValueError("R68 duplicated or forged conditional Gaussian seed")
                    all_seeds.append(draw["seed"])
                all_draws.append(draw)
            if d["H1_eligible_minus_raw_best_NLL"] is not None:
                gaps.append(d["H1_eligible_minus_raw_best_NLL"])
            if d["raw_nested_deviance"] is not None:
                deviances.append(d["raw_nested_deviance"])
            if nested["status"]=="refused":
                counts[f"{name}/H0_{d['null_status']}/H1_{d['alternative_status']}"]+=1
                failures={
                    "block":row["block"],"support":row["support"],"level":row["level"],
                    "phase":name,"draw":None if draw is None else draw["draw"],
                    "draw_seed":None if draw is None else draw["seed"],
                    "nested":d,
                }
                refusals.append(failures)
            if d["H1_eligible_gap_exceeds_original_001"] is True:
                counts[f"{name}/H1_gap_above_001"]+=1
            if d["negative_nested_deviance_beyond_original_tolerance"] is True:
                counts[f"{name}/nested_negative_beyond_1e5"]+=1
    if len(all_draws)!=DRAWS or counts["observed/accepted"]+counts["observed/refused"]+counts["observed/not_attempted"]!=CASES:
        raise ValueError("R68 source or draw failure-inclusive denominator mismatch")
    if any(not math.isfinite(x) for x in gaps+deviances):
        raise ValueError("R68 nonfinite numerical diagnostic escaped")
    return {
        "study":STUDY,"master_seed":MASTER_SEED,"draw_seed":DRAW_SEED,
        "new_independent_primitive_Gaussian_blocks":BLOCKS,
        "matched_original_source_cases":CASES,
        "conditional_Gaussian_draw_slots":DRAWS,
        "original_nested_H0_H1_model_positions":NESTED_POSITIONS,
        "original_optimizer_start_slots":START_POSITIONS,
        "recorded_distinct_attempted_draw_seeds":len(all_seeds),
        "recorded_source_case_identifiers":len(ids),
        "original_fit_status_counts":dict(sorted(counts.items())),
        "source_and_draw_refusal_ledger":refusals,
        "observed_max_H1_eligible_minus_best_NLL":max(gaps,default=None),
        "observed_min_raw_nested_deviance":min(deviances,default=None),
        "frozen_H1_KKT_threshold":KKT_TOL,
        "frozen_H1_multistart_NLL_threshold":NLL_TOL,
        "frozen_nested_negative_tolerance":-NEST_TOL,
        "num_new_5pct_test_calibrations":0,
        "no_statistical_candidate_p_or_power":True,
        "no_fitted_CR2_90pct_pointwise_or_simultaneous_qualification":True,
        "no_original_R66_refusal_repair_or_interval_recovery":True,
        "release_authorized":False,
    }


def shard(out:Path,start:int,stop:int)->None:
    if (start,stop) not in SHARDS:
        raise ValueError("R68 unregistered source original 4-block shard")
    out.mkdir(parents=True,exist_ok=True)
    cases=[evaluate(b,s,l) for b in range(start,stop) for s in SUPPORT for l in LEVELS]
    payload=json.dumps(cases,sort_keys=True,allow_nan=False,indent=2,
                       default=r58.r57.r53._json_plain)+"\n"
    (out/"cases.json").write_bytes(payload.encode())
    (out/"manifest.json").write_bytes((json.dumps({
        "study":STUDY,"source_seed":MASTER_SEED,"draw_seed":DRAW_SEED,
        "source_checkout":os.environ.get("GITHUB_SHA","unverified-local"),
        "start":start,"stop":stop,"count":len(cases),
        "sha256_cases":hashlib.sha256(payload.encode()).hexdigest(),
    },indent=2,sort_keys=True)+"\n").encode())


def aggregate(out:Path,parts:Path)->None:
    manifests=list(parts.glob("*/manifest.json"))
    if len(manifests)!=len(SHARDS):
        raise ValueError("R68 all two independent NEW source shard artifacts required")
    source_checkout=os.environ.get("GITHUB_SHA","unverified-local")
    all_cases=[];seen=set()
    for f in manifests:
        info=json.loads(f.read_bytes())
        key=(info["start"],info["stop"])
        if (key in seen or key not in SHARDS or info["study"]!=STUDY
            or info["source_seed"]!=MASTER_SEED or info["draw_seed"]!=DRAW_SEED
            or info["source_checkout"]!=source_checkout):
            raise ValueError("R68 original SHA/seed provenance mismatch")
        seen.add(key)
        raw=(f.parent/"cases.json").read_bytes()
        if hashlib.sha256(raw).hexdigest()!=info["sha256_cases"]:
            raise ValueError("R68 source shard SHA256 byte integrity check failed")
        rows=json.loads(raw)
        required={(b,s,l) for b in range(*key) for s in SUPPORT for l in LEVELS}
        if len(rows)!=info["count"] or {(q["block"],q["support"],q["level"]) for q in rows}!=required:
            raise ValueError("R68 original source shard incomplete/duplicated")
        all_cases.extend(rows)
    all_cases.sort(key=lambda q:(q["block"],SUPPORT.index(q["support"]),LEVELS.index(q["level"])))
    report=summarize(all_cases)
    out.mkdir(parents=True,exist_ok=True)
    (out/"cases.json").write_bytes((json.dumps(all_cases,indent=2,sort_keys=True,allow_nan=False)+"\n").encode())
    (out/"summary.json").write_bytes((json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+"\n").encode())
    (out/"source-commit.txt").write_text(source_checkout+"\n")
    (out/"SHA256SUMS").write_text("".join(
        hashlib.sha256((out/n).read_bytes()).hexdigest()+"  "+n+"\n"
        for n in ("cases.json","summary.json","source-commit.txt")))
    print(json.dumps(report,sort_keys=True))


def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("--out",required=True,type=Path)
    sub=cli.add_mutually_exclusive_group(required=True)
    sub.add_argument("--start",type=int)
    sub.add_argument("--merge-parts",type=Path)
    cli.add_argument("--stop",type=int)
    args=cli.parse_args()
    if args.merge_parts is not None:
        aggregate(args.out,args.merge_parts)
    elif args.stop is not None:
        shard(args.out,args.start,args.stop)
    else:
        raise SystemExit("R68 must use original registered --start and --stop")
if __name__=="__main__":
    main()
