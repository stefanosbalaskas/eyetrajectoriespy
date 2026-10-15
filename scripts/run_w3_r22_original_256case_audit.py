"""R22: original 256-case, immutable R20 numerical feasibility comparison.

The original R20 estimator must still reproduce exactly 41 failures.
The new scaled-Cholesky numerical method is scored separately: passes,
refusals, adjustment identity, CR2 SE and df discrepancies are all retained.
No coverage or statistical inference qualification from surviving cases.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts import run_w3_r16_leverage_covariance_factorial as r16
from scripts import run_w3_r17_fresh_feasibility as source
from scripts import run_w3_r20_estimated_target_pilot as pilot
from scripts import run_w3_r21_estimated_target_spectral_audit as original
from scripts.w3_r20_estimated_working_target import (
    observed_weighted_rows,estimate_feasible_working_target)
from scripts.w3_r22_scaled_cholesky_cr2 import (
    UnstableCR2Adjustment,stable_cr2_blockwise_wls)

STUDY="W3_R22_ORIGINAL_256CASE_SCALED_CHOLESKY_NUMERICAL_AUDIT"
SE_RELATIVE_TOL=5e-5
DF_RELATIVE_TOL=5e-5


def evaluate(block,n,support,model,family):
    record={"block":block,"n_participants":n,
            "source_support":support,"mean_basis":model,"working_family":family,
            "new_status":"refused","new_error":None,
            "original_status_unmodified":True,
            "pointwise_coverage_qualified":False,
            "release_authorized":False}
    try:
        raw=source.fresh_source(block,support,n=n,master_seed=pilot.MASTER_SEED,
                    n_blocks=pilot.BLOCKS,max_n=max(pilot.SIZES))
        X,y,w,g,t,tr,x=observed_weighted_rows(
                   (None,raw[1],raw[2],raw[3],raw[4],None),model)
        estimated=estimate_feasible_working_target(
                   X,y,w,g,t,tr,x,slope=family)
        k=r16.basis(np.asarray([.5]),model).shape[1]
        c=np.r_[np.zeros(k),r16.basis(np.asarray([r16.TIME[r16.FOCAL]]),model)[0]]
        calculated=stable_cr2_blockwise_wls(
                 X,y,w,g,c,estimated["working_blocks"])
        record.update(new_status="ok",
           stable_cr2_se=calculated["cr2_se"],
           stable_satterthwaite_df=calculated["satterthwaite_df"],
           relative_identity_error=calculated["max_relative_adjustment_identity_error"],
           maximum_product_condition=calculated["max_normalized_product_condition"],
           estimated_sensor_floor_applied=estimated["sensor_floor_applied"],
           nuisance_component_condition=estimated["component_condition_number"])
    except Exception as exc:
        record["new_error"]={"type":type(exc).__name__,"message":str(exc)[:400]}
    return record


def summarize(rows,old):
    if len(rows)!=pilot.PLANNED or len(old)!=pilot.PLANNED:
        raise ValueError("incomplete source case results")
    expected={(b,n,s,m,f) for b in range(pilot.BLOCKS) for n in pilot.SIZES
              for s in pilot.SUPPORT for m in pilot.BASES for f in pilot.WORKING_FAMILIES}
    def key(v):
        return (v["block"],v["n_participants"],v["source_support"],
                v["mean_basis"],v["working_family"])
    new_by={key(v):v for v in rows}
    old_by={key(v):v for v in old}
    if set(new_by)!=expected or set(old_by)!=expected:
        raise ValueError("model/source identities differ")
    original_failed=sorted(original.case_key(x) for x in old if x["status"]!="ok")
    signature=hashlib.sha256(("\n".join(original_failed)+"\n").encode()).hexdigest()
    original_contract=(signature==original.ORIGINAL_FAILURE_KEY_SHA256
                       and len(original_failed)==original.ORIGINAL_FAILED_CASES)
    new_ok=[x for x in rows if x["new_status"]=="ok"]
    new_bad=[x for x in rows if x["new_status"]!="ok"]
    originally_ok_pairs=[(old_by[k],new_by[k]) for k in expected
                           if old_by[k]["status"]=="ok" and new_by[k]["new_status"]=="ok"]
    drift=[]
    for x,y in originally_ok_pairs:
        se_error=abs(y["stable_cr2_se"]/x["estimated_cr2_standard_error"]-1)
        df_error=abs(y["stable_satterthwaite_df"]/x["conditional_satterthwaite_df"]-1)
        if max(se_error,df_error)>max(SE_RELATIVE_TOL,DF_RELATIVE_TOL):
            drift.append({"source":key(x),"cr2_se_relative_difference":se_error,
                          "satterthwaite_df_relative_difference":df_error})
    old_failure_new_success=sum(old_by[key(x)]["status"]!="ok" for x in new_ok)
    return {
      "study":STUDY,"source_seed":pilot.MASTER_SEED,
      "source_independent_blocks":pilot.BLOCKS,
      "original_source_evaluations":len(old),
      "original_source_failed":len(original_failed),
      "original_failure_hash":signature,
      "original_41_failures_unchanged":original_contract,
      "new_numerical_success":len(new_ok),"new_numerical_refusal":len(new_bad),
      "new_numerically_accepted_original_failures":old_failure_new_success,
      "new_accepted_original_successes":len(originally_ok_pairs),
      "new_refused_original_successes":sum(
         old_by[key(x)]["status"]=="ok" for x in new_bad),
      "new_refused_original_failures":sum(
         old_by[key(x)]["status"]!="ok" for x in new_bad),
      "new_refusal_types":dict(Counter(x["new_error"]["message"].split(":",1)[0]
                  if x["new_error"] else "unclassified" for x in new_bad)),
      "numerical_SE_df_disagreement_count":len(drift),
      "numerical_disagreement_examples":drift[:10],
      "max_relative_adjustment_identity_error":max(
          (x["relative_identity_error"] for x in new_ok),default=None),
      "new_algorithm_qualifies_original_failures":False,
      "estimated_nuisance_uncertainty_accounted_for":False,
      "original_source_inference_qualified":False,
      "simultaneous_bands_qualified":False,"release_authorized":False,
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    fresh=[];historical=[]
    for b in range(pilot.BLOCKS):
        for n in pilot.SIZES:
            for s in pilot.SUPPORT:
                for m in pilot.BASES:
                    for f in pilot.WORKING_FAMILIES:
                        historical.append(pilot.evaluate(b,n,s,m,f))
                        fresh.append(evaluate(b,n,s,m,f))
    summary=summarize(fresh,historical)
    for name,obj in (("stable-case-ledger.json",fresh),
                     ("original-source-case-ledger.json",historical),
                     ("summary.json",summary)):
        (args.out/name).write_text(json.dumps(obj,sort_keys=True,indent=2)+"\n")
    (args.out/"source-commit.txt").write_text(os.getenv("GITHUB_SHA","unverified-local")+"\n")
    files=("stable-case-ledger.json","original-source-case-ledger.json",
           "summary.json","source-commit.txt")
    (args.out/"SHA256SUMS").write_text("".join(
         hashlib.sha256((args.out/name).read_bytes()).hexdigest()+"  "+name+"\n"
         for name in files))
    print("R22 ORIGINAL NUMERICAL AUDIT:",json.dumps(
         {k:v for k,v in summary.items() if k!="numerical_disagreement_examples"},
         sort_keys=True))
    if not summary["original_41_failures_unchanged"] or summary["numerical_SE_df_disagreement_count"]:
        raise SystemExit("R22 original source or SE/df contract failed; no numerical qualification")


if __name__=="__main__":
    main()
