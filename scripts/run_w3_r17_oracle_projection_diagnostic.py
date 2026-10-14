"""R17 original-source oracle undercoverage: truth versus fixed-basis projection.

Same 96 independent seeds and original observations; no new data, no
redefinition of primary R17 90% truth inclusion. Diagnostic checks whether
known-variance oracle intervals cover the discrete-design weighted mean
projection, rather than only the generating continuous-time midpoint truth.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np
from scipy.stats import norm, t as student_t

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts import run_w3_r16_leverage_covariance_factorial as r16
from scripts import run_w3_r17_fresh_feasibility as fresh
from scripts import run_w3_r17_independent_96block_calibration as original

STUDY="W3_R17_ORIGINAL_SOURCE_BASIS_PROJECTION_ORACLE_DIAGNOSTIC"
NOMINAL=.90
CRITICAL_NORMAL=float(norm.ppf((1+NOMINAL)/2))


def diagnose(block,n,support,model):
    row={"block":block,"n_participants":n,"support":support,"model":model,
         "status":"failed","error":None,"release_authorized":False,
         "original_truth_target_preserved":True,"original_source_reused":True}
    try:
        case=fresh.fresh_source(block,support,n=n,master_seed=original.MASTER_SEED,
                                n_blocks=original.BLOCKS,max_n=max(original.SIZES))
        fit=r16.fit(case,model)
        true=float(fit["known_mid_slope"])
        projected=float(fit["project"])
        point=float(fit["point"])
        se=float(fit["oracle_se"])
        if not np.isfinite([true,projected,point,se]).all() or se<=0:
            raise ValueError("invalid known-oracle scientific diagnostic")
        zcrit=CRITICAL_NORMAL
        tcrit=float(student_t.ppf((1+NOMINAL)/2,n-1))
        true_z=(point-true)/se
        projected_z=(point-projected)/se
        bias=(projected-true)/se
        row.update(status="ok",
            source_midpoint_truth=true,
            weighted_basis_projection=projected,
            point_estimate=point,
            oracle_se=se,
            projection_minus_truth=projected-true,
            projection_displacement_oracle_se_units=bias,
            estimated_point_minus_projection_oracle_se_units=projected_z,
            estimated_point_minus_truth_oracle_se_units=true_z,
            oracle_truth_included_t=bool(abs(true_z)<=tcrit),
            oracle_projection_included_t=bool(abs(projected_z)<=tcrit),
            oracle_truth_included_normal=bool(abs(true_z)<=zcrit),
            oracle_projection_included_normal=bool(abs(projected_z)<=zcrit),
            original_pointwise_coverage_qualified=False,
            projection_target_is_new_primary_estimand=False)
    except Exception as exc:
        row["error"]={"type":type(exc).__name__,"message":str(exc)[:650]}
    return row


def cell_summary(rows):
    if not rows:
        return {"completed":0,"failed":0}
    good=[x for x in rows if x["status"]=="ok"]
    if not good:
        return {"completed":0,"failed":len(rows)}
    def fraction(k):
        ksum=sum(int(x[k]) for x in good)
        return {"count":ksum,"total":len(good),"rate":ksum/len(good),
                "wilson_95pct":original.wilson_interval(ksum,len(good))}
    u=np.array([x["estimated_point_minus_projection_oracle_se_units"] for x in good])
    v=np.array([x["projection_displacement_oracle_se_units"] for x in good])
    return {"completed":len(good),"failed":len(rows)-len(good),
      "oracle_truth_t":fraction("oracle_truth_included_t"),
      "oracle_projection_t":fraction("oracle_projection_included_t"),
      "oracle_truth_normal":fraction("oracle_truth_included_normal"),
      "oracle_projection_normal":fraction("oracle_projection_included_normal"),
      "projection_shift_in_oracle_SE_units_mean":float(v.mean()),
      "projection_shift_in_oracle_SE_units_mean_absolute":float(np.mean(abs(v))),
      "projection_shift_in_oracle_SE_units_max_absolute":float(np.max(abs(v))),
      "noise_about_projection_standardized_mean":float(u.mean()),
      "noise_about_projection_standardized_sample_sd":float(u.std(ddof=1)) if len(u)>1 else None,
      "mean_squared_noise_about_projection":float(np.mean(u*u)),
      "original_truth_target_remains_primary":True}


def summarize(rows):
    expected={(b,n,s,m) for b in range(original.BLOCKS)
              for n in original.SIZES for s in r16.SUPPORT for m in r16.MODELS}
    observed={(x["block"],x["n_participants"],x["support"],x["model"]) for x in rows}
    if len(observed)!=len(rows):
        raise ValueError("duplicate original-source observations")
    groups={}
    for n in original.SIZES:
        for s in r16.SUPPORT:
            for m in r16.MODELS:
                key=f"n{n}/{s}/{m}"
                cell=[x for x in rows if x["n_participants"]==n and x["support"]==s and x["model"]==m]
                groups[key]=cell_summary(cell)
    return {"study":STUDY,
        "master_seed":original.MASTER_SEED,
        "source_equivalence_expected":True,
        "independent_generating_blocks":original.BLOCKS,
        "planned_source_model_diagnostics":len(expected),
        "recorded_source_model_diagnostics":len(rows),
        "missing_source_model_diagnostics":len(expected-observed),
        "failed_source_model_diagnostics":sum(x["status"]!="ok" for x in rows),
        "groups":groups,
        "changes_original_R17_coverage":False,
        "promotes_projected_target_to_primary":False,
        "method_winner_selected":False,
        "pointwise_inference_qualified":False,
        "simultaneous_inference_qualified":False,
        "production_release_ready":False}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    rows=[diagnose(b,n,s,m) for b in range(original.BLOCKS)
          for n in original.SIZES for s in r16.SUPPORT for m in r16.MODELS]
    summary=summarize(rows)
    for name,obj in (("case-ledger.json",rows),("summary.json",summary)):
        (args.out/name).write_text(json.dumps(obj,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    (args.out/"source-commit.txt").write_text(os.environ.get("GITHUB_SHA","unverified-local")+"\n")
    filenames=["case-ledger.json","summary.json","source-commit.txt"]
    (args.out/"SHA256SUMS").write_text("".join(hashlib.sha256((args.out/name).read_bytes()).hexdigest()+"  "+name+"\n" for name in filenames))
    headline={k:v for k,v in summary.items() if k!="groups"}
    print("R17 ORACLE PROJECTION AUDIT:",json.dumps(headline,sort_keys=True))
    for name,statistics in summary["groups"].items():
        print("R17 ORACLE PROJECTION GROUP:",json.dumps({"name":name,**statistics},sort_keys=True))
    if summary["missing_source_model_diagnostics"] or summary["failed_source_model_diagnostics"]:
        raise SystemExit("R17 diagnostic failures retained; not qualified")


if __name__=="__main__":
    main()
