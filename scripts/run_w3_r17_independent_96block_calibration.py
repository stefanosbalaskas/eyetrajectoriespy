"""R17 larger independently generated pointwise CR2 calibration research.

96 independent source blocks; nested participant sample sizes 24, 48 and 96.
Two-by-two leverage/covariance, two fixed bases, true (simulation only) and
diagonally misspecified CR2 working targets. No production qualification.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np
from scipy.stats import norm

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts import run_w3_r16_leverage_covariance_factorial as r16
from scripts import run_w3_r17_fresh_feasibility as fresh

STUDY="W3_R17_NEW96_INDEPENDENT_SOURCE_POINTWISE_CALIBRATION"
MASTER_SEED=202610142424
BLOCKS=96
SIZES=(24,48,96)
TARGETS=fresh.TARGETS
METHODS=("cr1_tGminus1","cr2_tGminus1","cr2_satterthwaite",
         "cv3j_tGminus1","oracle_tGminus1")
PLANNED=BLOCKS*len(SIZES)*len(r16.SUPPORT)*len(r16.MODELS)*len(TARGETS)
BOOTSTRAP_DRAWS=2500
BOOTSTRAP_SEED=202610142425


def wilson_interval(success,total,alpha=.05):
    if total<=0:
        return None
    p=success/total
    z=float(norm.ppf(1-alpha/2))
    d=1+z*z/total
    center=(p+z*z/(2*total))/d
    half=z*np.sqrt(p*(1-p)/total+z*z/(4*total*total))/d
    lower=0.0 if success==0 else float(max(0.0,center-half))
    upper=1.0 if success==total else float(min(1.0,center+half))
    return [lower,upper]


def paired_bootstrap_delta(rows,first,second,seed):
    """Paired by the independent generating block, never by case/model."""
    if len(rows)<2:
        return None
    order=sorted(rows,key=lambda x:x["block"])
    d=np.asarray([int(v["coverage"][first])-int(v["coverage"][second])
                  for v in order],float)
    rng=np.random.default_rng(seed)
    idx=rng.integers(0,len(d),size=(BOOTSTRAP_DRAWS,len(d)))
    replicates=np.mean(d[idx],axis=1)
    return {"observed_difference":float(np.mean(d)),
            "bootstrap_95_interval":list(map(float,np.quantile(replicates,[.025,.975]))),
            "n_independent_paired_blocks":len(d),
            "replicates":BOOTSTRAP_DRAWS}


def summarize(rows):
    groups={}
    expected={(b,n,s,m,t) for b in range(BLOCKS) for n in SIZES
              for s in r16.SUPPORT for m in r16.MODELS for t in TARGETS}
    actual={(v["block"],v["n_participants"],v["support"],v["model"],v["target"]) for v in rows}
    if len(actual)!=len(rows):
        raise ValueError("duplicated model/source/target entries")
    missing=len(expected-actual)
    for n in SIZES:
        for s in r16.SUPPORT:
            for m in r16.MODELS:
                for t in TARGETS:
                    cell=[r for r in rows if r["n_participants"]==n and r["support"]==s and r["model"]==m and r["target"]==t]
                    ok=[r for r in cell if r["status"]=="ok"]
                    counts={method:sum(int(v["coverage"][method]) for v in ok) for method in METHODS}
                    key=f"n{n}/{s}/{m}/{t}"
                    groups[key]={
                        "planned_independent_blocks":BLOCKS,
                        "completed_independent_blocks":len(ok),
                        "failed_blocks":len(cell)-len(ok),
                        "observed_90pct_pointwise_coverage":{method:float(counts[method]/len(ok)) if ok else None for method in METHODS},
                        "truth_inclusion_counts":counts,
                        "wilson_95pct_mc_intervals":{method:wilson_interval(counts[method],len(ok)) for method in METHODS},
                        "paired_cr2_sat_minus_cr1":paired_bootstrap_delta(
                            ok,"cr2_satterthwaite","cr1_tGminus1",
                            BOOTSTRAP_SEED+SIZES.index(n)*137+r16.SUPPORT.index(s)*37+r16.MODELS.index(m)*11+TARGETS.index(t)),
                        "paired_cr2_sat_minus_cr2_tGminus1":paired_bootstrap_delta(
                            ok,"cr2_satterthwaite","cr2_tGminus1",
                            BOOTSTRAP_SEED+1000+SIZES.index(n)*137+r16.SUPPORT.index(s)*37+r16.MODELS.index(m)*11+TARGETS.index(t)),
                        "mean_satterthwaite_df":float(np.mean([v["satterthwaite_df"] for v in ok])) if ok else None,
                        "mean_cr2_to_oracle_se":float(np.mean([v["cr2_to_oracle_se"] for v in ok])) if ok else None,
                    }
    fail=[v for v in rows if v["status"]!="ok"]
    return {
        "study":STUDY,
        "fresh_master_seed":MASTER_SEED,
        "original_R16_seed":r16.SEED,
        "earlier_R17_feasibility_seed":fresh.R17_SEED,
        "independent_generating_blocks":BLOCKS,
        "participant_sizes":SIZES,
        "support_conditions":r16.SUPPORT,
        "fixed_mean_bases":r16.MODELS,
        "working_targets":TARGETS,
        "planned_evaluations":PLANNED,
        "recorded_evaluations":len(rows),
        "successful_evaluations":len(rows)-len(fail),
        "failed_evaluations":len(fail),
        "missing_evaluations":missing,
        "failure_examples":fail[:12],
        "groups":groups,
        "simultaneous_bands_qualified":False,
        "empirically_estimated_covariance_qualified":False,
        "method_selected":False,
        "production_release_ready":False,
        "independent_replication_of_prior_seed":True,
        "coverage_result_not_automatic_qualification":True,
    }


def run_case(block,n,support,model,target):
    out=fresh.evaluate(block,support,model,target,n=n,
                       master_seed=MASTER_SEED,n_blocks=BLOCKS,max_n=max(SIZES))
    out["study"]=STUDY
    out["fresh_master_seed"]=MASTER_SEED
    return out


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True,type=Path)
    parser.add_argument("--blocks",type=int,default=BLOCKS,
                        help="Only full prespecified 96-block study accepted")
    args=parser.parse_args()
    if args.blocks!=BLOCKS:
        raise SystemExit("The preregistered research execution requires all 96 source blocks")
    args.out.mkdir(parents=True,exist_ok=True)
    cases=[run_case(block,n,s,m,target)
           for block in range(BLOCKS)
           for n in SIZES for s in r16.SUPPORT for m in r16.MODELS for target in TARGETS]
    summary=summarize(cases)
    for name,obj in (("case-ledger.json",cases),("summary.json",summary)):
        (args.out/name).write_text(json.dumps(obj,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    (args.out/"source-commit.txt").write_text(os.environ.get("GITHUB_SHA","unverified-local")+"\n")
    files=("case-ledger.json","summary.json","source-commit.txt")
    (args.out/"SHA256SUMS").write_text("".join(
        hashlib.sha256((args.out/name).read_bytes()).hexdigest()+"  "+name+"\n" for name in files))
    headline={k:v for k,v in summary.items() if k not in ("groups","failure_examples")}
    print("R17 96-BLOCK ORIGINAL SOURCE AUDIT:",json.dumps(headline,sort_keys=True))
    for key,value in summary["groups"].items():
        print("R17 GROUP:",json.dumps({"group":key,**value},sort_keys=True))
    if summary["missing_evaluations"] or summary["failed_evaluations"] or summary["successful_evaluations"]!=PLANNED:
        raise SystemExit("R17 source failures retained; no qualification allowed")


if __name__=="__main__":
    main()
