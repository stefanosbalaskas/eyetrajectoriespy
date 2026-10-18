"""R64 research: source-matched true-zero vs positive random-slope detection pilot.

Frozen known structural slopes 0, 1/2 and 1 times original Gaussian
participant-slope SD 0.045, with paired leverage and *common source*
innovations for each primitive independent block. R63's original
H0/H1 REML and null-Gaussian nuisance-refitted bootstrap are UNCHANGED.
Candidate exceedance among nonzero sources is exploratory detection, not
power of a validated 5%-size test, and is never calibration of 90% CR2.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path

import numpy as np

from scripts import run_w3_r16_leverage_covariance_factorial as r16
from scripts import run_w3_r17_fresh_feasibility as fresh
from scripts import run_w3_r48_independent_fitted_cr2 as r48
from scripts import run_w3_r58_boundary_null_reference as r58
from scripts import run_w3_r63_independent_null_replication as core

STUDY="W3_R64_ZERO_VS_POSITIVE_SLOPE_GAUSSIAN_DETECTION_PILOT"
MASTER_SEED=202610186464
DRAW_SEED=202610186465
BLOCKS=32
PARTICIPANTS=24
SUPPORT=("ordinary_dependent","extreme_dependent")
LEVELS=("zero","half","full")
MULTIPLIERS={"zero":0.0,"half":0.5,"full":1.0}
B=63
SHARDS=tuple((i,i+4) for i in range(0,BLOCKS,4))
CASES=BLOCKS*len(SUPPORT)*len(LEVELS)
DRAWS=CASES*B
NESTED_MODELS=2*(CASES+DRAWS)
OPTIMIZER_STARTS=6*(CASES+DRAWS)
ALPHA=.05
CLASSICAL=r58.CRITICAL


def source(block,support,level):
    if type(block) is not int or block<0 or block>=BLOCKS:
        raise ValueError("R64 original source outside frozen primitive blocks")
    if support not in SUPPORT or level not in LEVELS:
        raise ValueError("R64 undeclared paired support/slope level")
    case=fresh.fresh_source(
        block,support,n=PARTICIPANTS,master_seed=MASTER_SEED,
        n_blocks=BLOCKS,max_n=PARTICIPANTS)
    X,y,w,g,t,tr,x,*_=r48.native_data(case)
    z=np.asarray(case[0]["participant_slope"],float)[
        np.asarray(g,int),0,0,0]
    gaussian_slope=r16.SIGMA_RANDOM_SLOPE*z*x*(1.+.25*t)
    m=MULTIPLIERS[level]
    # Original response includes full random slope. Scale *only* this
    # component, keeping original intercept/trial/sensor/fixed mean intact.
    response=np.asarray(y,float)-(1.-m)*gaussian_slope
    if not np.isfinite(response).all():
        raise ValueError("R64 nonfinite matched Gaussian source response")
    np.testing.assert_allclose(
        np.asarray(y,float)-response,(1.-m)*gaussian_slope,
        rtol=4e-13,atol=4e-13)
    return {
        "X":X,"y":response,"w":w,"group":g,"time":t,
        "trial":tr,"x":x,
        "true_slope_variance":float((m*r16.SIGMA_RANDOM_SLOPE)**2),
        "full_slope_component_L2":float(np.linalg.norm(gaussian_slope)),
        "retained_slope_component_L2":float(m*np.linalg.norm(gaussian_slope)),
    }


def conditional_h0_response(data,beta,covs,block,support,level,draw):
    if type(draw) is not int or draw<0 or draw>=B:
        raise ValueError("R64 Gaussian pseudodraw index outside frozen 0..62")
    if type(block) is not int or not 0<=block<BLOCKS or support not in SUPPORT or level not in LEVELS:
        raise ValueError("R64 unregistered Gaussian H0 pseudodraw source")
    # Separate pseudodraw stream for each independent block, support,
    # true-slope level, and draw. No collisions across these dimensions.
    seed=(DRAW_SEED+100003*block+739*SUPPORT.index(support)
          +1009*LEVELS.index(level)+draw)
    rng=np.random.default_rng(seed)
    y=np.asarray(data["X"]@beta,float).copy()
    weights=np.asarray(data["w"],float)
    visited=np.zeros(len(y),bool)
    for ix,L in covs:
        if np.any(visited[ix]):
            raise ValueError("R64 duplicated native participant rows")
        visited[ix]=True
        y[ix]+=(L@rng.standard_normal(len(ix)))/np.sqrt(weights[ix])
    if not visited.all() or not np.isfinite(y).all():
        raise ValueError("R64 incomplete nonfinite Gaussian conditional response")
    return {**data,"y":y},seed


def empty_case(block,support,level):
    return {
        "study":STUDY,"block":block,"support":support,"level":level,
        "structural_slope_multiplier":MULTIPLIERS[level],
        "true_slope_variance":float(
            (MULTIPLIERS[level]*r16.SIGMA_RANDOM_SLOPE)**2),
        "source_status":"refused","source_error":None,
        "observed":core.nested_on_invalid(),
        "fitted_null_theta":None,"bootstrap":[],
        "planned_bootstrap_slots":B,
        "candidate_5pct_exceedance":None,
        "conditional_bootstrap_p":None,
        "bootstrap_5pct_exceedance":None,
        "null_size_or_power_qualified":False,
        "fitted_CR2_90pct_qualified":False,
        "release_authorized":False,
    }


def empty_draw(draw):
    return {"draw":draw,"status":"not_attempted","seed":None,
            "nested":core.nested_on_invalid()}


def evaluate(block,support,level):
    out=empty_case(block,support,level)
    out["bootstrap"]=[empty_draw(j) for j in range(B)]
    try:
        data=source(block,support,level)
        out["source_status"]="ok"
        out["full_slope_component_L2"]=data["full_slope_component_L2"]
        out["retained_slope_component_L2"]=data["retained_slope_component_L2"]
        out["observed"]=core.nested_on(data)
        if out["observed"]["status"]!="accepted":
            return out
        beta,cov,theta=core.h0_gls_covariance(
            data,out["observed"]["null_fit"],
            out["observed"]["observed_reference"])
        out["fitted_null_theta"]=theta
        out["candidate_5pct_exceedance"]=bool(
            out["observed"]["nonnegative_deviance"]>CLASSICAL)
        for draw in range(B):
            try:
                pseudo,seed=conditional_h0_response(
                    data,beta,cov,block,support,level,draw)
                fitted=core.nested_on(pseudo)
                out["bootstrap"][draw]={
                    "draw":draw,"status":fitted["status"],
                    "seed":seed,"nested":fitted,
                }
            except Exception as exc:
                out["bootstrap"][draw]={
                    "draw":draw,"status":"refused","seed":None,
                    "nested":core.nested_on_invalid(),
                    "error":repr(exc)[:450],
                }
        accepted=[z for z in out["bootstrap"]
                  if z["nested"]["status"]=="accepted"]
        if len(accepted)==B:
            t=out["observed"]["nonnegative_deviance"]
            n=sum(z["nested"]["nonnegative_deviance"]>=t for z in accepted)
            out["conditional_bootstrap_p"]=(1+n)/(B+1)
            out["bootstrap_5pct_exceedance"]=bool(
                out["conditional_bootstrap_p"]<=ALPHA)
    except Exception as exc:
        out["source_error"]=repr(exc)[:450]
    return out


def summarize(rows):
    expected={(b,s,l) for b in range(BLOCKS) for s in SUPPORT for l in LEVELS}
    ids=[(v["block"],v["support"],v["level"]) for v in rows]
    if len(ids)!=CASES or len(set(ids))!=CASES or set(ids)!=expected:
        raise ValueError("R64 missing/duplicated complete true-slope source identities")
    if sum(len(x["bootstrap"]) for x in rows)!=DRAWS:
        raise ValueError("R64 wrong full refusal-inclusive bootstrap denominator")
    if any([v["draw"] for v in r["bootstrap"]]!=list(range(B)) for r in rows):
        raise ValueError("R64 original draw slots are not complete")
    starts=sum(
        len(n["null_fit"]["original_starts"])+
        len(n["alternative_fit"]["original_starts"])
        for row in rows for n in [row["observed"]]+
        [draw["nested"] for draw in row["bootstrap"]])
    if starts!=OPTIMIZER_STARTS:
        raise ValueError("R64 original optimizer-start ledger incomplete")
    cells={}
    for support in SUPPORT:
        for level in LEVELS:
            sub=[r for r in rows if r["support"]==support and r["level"]==level]
            passed=[r for r in sub if r["conditional_bootstrap_p"] is not None]
            n=len(passed)
            bootstrap=sum(r["bootstrap_5pct_exceedance"] is True for r in passed)
            original=[r for r in sub if r["observed"]["status"]=="accepted"]
            classical=sum(r["candidate_5pct_exceedance"] is True for r in original)
            refuses=BLOCKS-n
            cells[f"{support}/{level}"]={
                "independent_source_blocks":BLOCKS,
                "true_slope_variance":float(
                    (MULTIPLIERS[level]*r16.SIGMA_RANDOM_SLOPE)**2),
                "original_source_cases":len(sub),
                "accepted_original_nested_fits":len(original),
                "planned_gaussian_bootstrap_draw_slots":BLOCKS*B,
                "recorded_gaussian_bootstrap_draw_slots":
                    sum(len(r["bootstrap"]) for r in sub),
                "accepted_nuisance_refitted_bootstrap_draws":
                    sum(z["nested"]["status"]=="accepted"
                        for r in sub for z in r["bootstrap"]),
                "complete_63_draw_sources":n,
                "refused_incomplete_sources":refuses,
                "bootstrap_candidate_rejections":bootstrap,
                "bootstrap_candidate_detection_fraction_complete":
                    bootstrap/n if n else None,
                "bootstrap_Wilson95_complete":r58.wilson_95(bootstrap,n),
                "refusal_as_nonrejection_all_source_lower":bootstrap/BLOCKS,
                "refusal_as_rejection_all_source_upper":
                    (bootstrap+refuses)/BLOCKS,
                "classical_candidate_rejections":classical,
                "classical_Wilson95_accepted":r58.wilson_95(classical,len(original)),
                "null_size_or_power_qualified":False,
            }
    return {
        "study":STUDY,
        "new_independent_primitive_block_source_seed":MASTER_SEED,
        "new_conditional_Gaussian_draw_seed":DRAW_SEED,
        "independent_Gaussian_primitive_blocks":BLOCKS,
        "participants_per_primitive_source":PARTICIPANTS,
        "leverage_supports":list(SUPPORT),
        "structural_slope_multipliers":list(LEVELS),
        "true_slope_variances":{
            level:float((MULTIPLIERS[level]*r16.SIGMA_RANDOM_SLOPE)**2)
            for level in LEVELS},
        "support_and_level_paired_within_independent_block":True,
        "planned_source_cases":CASES,"recorded_source_cases":len(rows),
        "draws_per_original_source":B,
        "planned_gaussian_conditional_H0_draw_slots":DRAWS,
        "recorded_gaussian_conditional_H0_draw_slots":
            sum(len(x["bootstrap"]) for x in rows),
        "nested_H0_H1_model_fit_slots":NESTED_MODELS,
        "optimizer_start_records":starts,
        "fitted_null_nuisance_reestimated_for_each_bootstrap_draw":True,
        "conditional_candidate_p_grid_denominator":64,
        "exploratory_detection_not_validated_power":True,
        "no_validated_null_type_I_calibration":True,
        "no_fitted_CR2_pointwise_or_simultaneous_90pct_qualification":True,
        "release_authorized":False,"strata":cells,
    }


def shard(out,start,stop):
    if (start,stop) not in SHARDS:
        raise ValueError("R64 unregistered original 4-primitive-block shard")
    out.mkdir(parents=True,exist_ok=True)
    rows=[evaluate(b,s,l) for b in range(start,stop)
          for s in SUPPORT for l in LEVELS]
    raw=json.dumps(rows,sort_keys=True,allow_nan=False,indent=2)+"\n"
    (out/"cases.json").write_bytes(raw.encode("utf-8"))
    (out/"manifest.json").write_bytes((json.dumps({
        "study":STUDY,"start":start,"stop":stop,
        "source_seed":MASTER_SEED,"draw_seed":DRAW_SEED,
        "checkout":os.environ.get("GITHUB_SHA","unverified-local"),
        "source_cases":len(rows),
        "sha256_cases":hashlib.sha256(raw.encode("utf-8")).hexdigest(),
    },sort_keys=True,indent=2)+"\n").encode("utf-8"))


def aggregate(out,parts):
    files=list(parts.glob("*/manifest.json"))
    if len(files)!=len(SHARDS):
        raise ValueError("R64 all eight original source-shard artifacts required")
    checkout=os.environ.get("GITHUB_SHA","unverified-local")
    rows=[]; seen=set()
    for path in files:
        info=json.loads(path.read_bytes())
        pair=(info["start"],info["stop"])
        if (pair not in SHARDS or pair in seen or
            info["study"]!=STUDY or
            info["source_seed"]!=MASTER_SEED or
            info["draw_seed"]!=DRAW_SEED or
            info["checkout"]!=checkout):
            raise ValueError("R64 original source provenance/mixed checkout")
        seen.add(pair)
        original=(path.parent/"cases.json").read_bytes()
        if hashlib.sha256(original).hexdigest()!=info["sha256_cases"]:
            raise ValueError("R64 original source shard SHA256 byte-integrity violation")
        cases=json.loads(original)
        if (len(cases)!=info["source_cases"] or
            {(row["block"],row["support"],row["level"]) for row in cases}!=
            {(b,s,l) for b in range(*pair) for s in SUPPORT for l in LEVELS}):
            raise ValueError("R64 source shard has wrong or duplicated cases")
        rows.extend(cases)
    rows.sort(key=lambda z:(z["block"],SUPPORT.index(z["support"]),LEVELS.index(z["level"])))
    report=summarize(rows)
    out.mkdir(parents=True,exist_ok=True)
    (out/"cases.json").write_bytes((json.dumps(
        rows,sort_keys=True,indent=2,allow_nan=False)+"\n").encode("utf-8"))
    (out/"summary.json").write_bytes((json.dumps(
        report,sort_keys=True,indent=2,allow_nan=False)+"\n").encode("utf-8"))
    (out/"source-commit.txt").write_bytes((checkout+"\n").encode("utf-8"))
    (out/"SHA256SUMS").write_bytes("".join(
        hashlib.sha256((out/name).read_bytes()).hexdigest()+"  "+name+"\n"
        for name in ("cases.json","summary.json","source-commit.txt")
    ).encode("utf-8"))
    print(json.dumps(report,sort_keys=True))


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
        raise SystemExit("R64 source shard requires --start --stop")

if __name__=="__main__":
    main()
