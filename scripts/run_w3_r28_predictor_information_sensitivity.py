"""R28 hypothetical predictor-range sensitivity for Gaussian variance information.

Reuses EXACT two R27 frozen original R26 source blocks; hypothetically
rescales the between-participant predictor across the same participants.
No new observed gaze values or independent generating source blocks.
The matching predictor-dependent covariance term is rescaled consistently;
predictor-independent source covariance serves as a negative control.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts import run_w3_r27_reml_information_audit as r27

STUDY="W3_R28_HYPOTHETICAL_PREDICTOR_SPREAD_INFORMATION"
PREDICTOR_MULTIPLIERS=(0.5,1.0,2.0,4.0)
ORIGINAL_BLOCKS=r27.ORIGINAL_BLOCKS
ORIGINAL_N=r27.ORIGINAL_N
ORIGINAL_SUPPORT=r27.ORIGINAL_SUPPORT
PLANNED=(len(ORIGINAL_BLOCKS)*len(ORIGINAL_N)*
         len(ORIGINAL_SUPPORT)*len(PREDICTOR_MULTIPLIERS))


def evaluate(block,n,support,multiplier):
    item={"source_block":block,"participants":n,"support":support,
          "predictor_multiplier":float(multiplier),
          "hypothetical_information_sensitivity":True,
          "new_independent_source_block":False,
          "status":"failed","exception":None}
    try:
        ref=r27.information_for_original_design(
            block,n,support,predictor_multiplier=float(multiplier))
        logse=ref["relative_local_component_SE"]
        item.update(
            status="ok",
            slope_log_variance_local_SE=float(logse[
                r27.COMPONENTS.index("participant_slope")]),
            intercept_log_variance_local_SE=float(logse[
                r27.COMPONENTS.index("participant_intercept")]),
            trial_log_variance_local_SE=float(logse[
                r27.COMPONENTS.index("trial")]),
            sensor_log_variance_local_SE=float(logse[
                r27.COMPONENTS.index("sensor")]),
            min_log_information_eigenvalue=float(
                np.linalg.eigvalsh(ref["info_log"])[0]),
            log_information_eigen_condition=float(ref["information_eigen_condition"]),
            is_exact_original_predictor_design=bool(multiplier==1.0))
    except Exception as exc:
        item["exception"]={"type":type(exc).__name__,
                           "message":str(exc)[:600]}
    return item


def summarize(rows):
    original_keys={(b,n,s,m) for b in ORIGINAL_BLOCKS for n in ORIGINAL_N
        for s in ORIGINAL_SUPPORT for m in PREDICTOR_MULTIPLIERS}
    received={(x["source_block"],x["participants"],x["support"],
               x["predictor_multiplier"]) for x in rows}
    if len(received)!=len(rows):
        raise ValueError("duplicate R28 original design")
    grouped={}
    for n in ORIGINAL_N:
        for support in ORIGINAL_SUPPORT:
            source=[x for x in rows if x["participants"]==n and x["support"]==support]
            per_mult={}
            for multiplier in PREDICTOR_MULTIPLIERS:
                subset=[x for x in source if x["predictor_multiplier"]==multiplier]
                ok=[x for x in subset if x["status"]=="ok"]
                per_mult[str(multiplier)]={
                    "original_source_blocks":len(ok),
                    "failed_source_information_calculations":len(subset)-len(ok),
                    "median_slope_log_variance_local_SE":(
                      float(np.median([x["slope_log_variance_local_SE"] for x in ok]))
                      if ok else None),
                    "median_trial_log_variance_local_SE":(
                      float(np.median([x["trial_log_variance_local_SE"] for x in ok]))
                      if ok else None),
                    "median_intercept_log_variance_local_SE":(
                      float(np.median([x["intercept_log_variance_local_SE"] for x in ok]))
                      if ok else None),
                }
            baseline=per_mult["1.0"]["median_slope_log_variance_local_SE"]
            for key,v in per_mult.items():
                value=v["median_slope_log_variance_local_SE"]
                v["slope_local_SE_ratio_to_original"]=(
                    float(value/baseline) if baseline and value else None)
            grouped[f"n{n}/{support}"]=per_mult
    return {
       "study":STUDY,
       "planned_hypothetical_cases":PLANNED,
       "recorded_cases":len(rows),
       "missing_cases":len(original_keys-received),
       "failed_cases":sum(x["status"]!="ok" for x in rows),
       "original_independent_generating_blocks":len(ORIGINAL_BLOCKS),
       "new_independent_generating_blocks":0,
       "original_native_observation_and_trial_map_unchanged":True,
       "hypothetical_predictor_multipliers":PREDICTOR_MULTIPLIERS,
       "source_designs_only_no_new_empirical_observations":True,
       "groups":grouped,
       "pointwise_coverage_evaluated":False,
       "fitted_covariance_estimators_evaluated":False,
       "study_design_inference_qualified":False,
       "release_authorized":False,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    rows=[evaluate(b,n,s,m) for b in ORIGINAL_BLOCKS for n in ORIGINAL_N
          for s in ORIGINAL_SUPPORT for m in PREDICTOR_MULTIPLIERS]
    report=summarize(rows)
    for name,obj in (("case-ledger.json",rows),("summary.json",report)):
        (args.out/name).write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")
    (args.out/"source-commit.txt").write_text(os.getenv("GITHUB_SHA","unverified-local")+"\n")
    files=("case-ledger.json","summary.json","source-commit.txt")
    (args.out/"SHA256SUMS").write_text("".join(
        hashlib.sha256((args.out/name).read_bytes()).hexdigest()+"  "+name+"\n"
        for name in files))
    print("R28 PREDICTOR INFORMATION AUDIT:",json.dumps(
        {k:v for k,v in report.items() if k!="groups"},sort_keys=True))
    for name,x in report["groups"].items():
        print("R28 INFORMATION GROUP:",json.dumps({"name":name,"multipliers":x},sort_keys=True))
    if report["failed_cases"] or report["missing_cases"]:
        raise SystemExit("R28 prespecified hypothetical original-design information failed")


if __name__=="__main__":
    main()
