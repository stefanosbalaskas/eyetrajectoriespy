"""R20: small new-seed feasibility pilot for *estimated* CR2 working covariance.

Eight independent blocks, n=24,48; four leverage/covariance source cells, two
fixed bases, two prespecified competing estimated covariance families.
Neither family is selected by knowledge of the generator. Conditional CR2
Satterthwaite df ignores covariance nuisance-estimation uncertainty.
These results are exploratory and cannot establish nominal coverage.
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
from scripts import run_w3_r17_fresh_feasibility as source
from scripts.w3_r20_estimated_working_target import (
    MODELS,observed_weighted_rows,estimate_feasible_working_target)
from scripts.w3_r17_cr2_blockwise import cr2_blockwise_wls

STUDY="W3_R20_FRESH_FEASIBLE_TARGET_PAIRED_PILOT"
MASTER_SEED=202610150821
BLOCKS=8
SIZES=(24,48)
SUPPORT=r16.SUPPORT
BASES=r16.MODELS
WORKING_FAMILIES=MODELS
METHODS=("cr1","cr2_conventional","cr2_conditional_satterthwaite","participant_jackknife","oracle")
PLANNED=BLOCKS*len(SIZES)*len(SUPPORT)*len(BASES)*len(WORKING_FAMILIES)


def evaluate(block,n,support,model,family):
    row={"study":STUDY,"block":block,"n_participants":n,
         "source_support":support,"mean_basis":model,"working_family":family,
         "status":"failed","error":None,"release_authorized":False,
         "working_covariance_estimated_from_responses":True,
         "covariance_estimation_uncertainty_accounted_for":False,
         "nominal_coverage_qualified":False}
    try:
        data=source.fresh_source(block,support,n=n,master_seed=MASTER_SEED,
                 n_blocks=BLOCKS,max_n=max(SIZES))
        fitted=r16.fit(data,model)
        # The following covariance estimator receives observation-only fields.
        observable=(None,data[1],data[2],data[3],data[4],None)
        X,y,w,g,t,trial,x=observed_weighted_rows(observable,model)
        nuisance=estimate_feasible_working_target(
                 X,y,w,g,t,trial,x,slope=family)
        K=r16.basis(np.array([.5]),model).shape[1]
        c=np.r_[np.zeros(K),r16.basis(
                    np.asarray([r16.TIME[r16.FOCAL]]),model)[0]]
        feasible=cr2_blockwise_wls(X,y,w,g,c,nuisance["working_blocks"])
        if abs(feasible["point"]-fitted["point"])>r16.NUMERICAL_TOL:
            raise ValueError("feasible WLS point differs from known source reference")
        if max(feasible["max_adjustment_covariance_error"],
               feasible["max_adjustment_asymmetry"],
               feasible["expectation_identity_error"])>2e-7:
            raise ValueError("feasible-target CR2 matrix identity failure")
        nu=feasible["satterthwaite_df"]
        if not 0<nu<=n+1e-6:
            raise ValueError("invalid conditional degrees of freedom")
        methods={
           "cr1":(fitted["cr1_se"],n-1),
           "cr2_conventional":(feasible["cr2_se"],n-1),
           "cr2_conditional_satterthwaite":(feasible["cr2_se"],nu),
           "participant_jackknife":(fitted["jack_se"],n-1),
           "oracle":(fitted["oracle_se"],n-1),
        }
        truth=fitted["known_mid_slope"]
        included={k:bool(abs(fitted["point"]-truth)<=student_t.ppf(.95,df)*se)
                  for k,(se,df) in methods.items()}
        truth_structural_family=("predictor_scaled_slope"
                    if support.endswith("_dependent") else "shared_slope")
        known={key:float(value**2) for key,value in
               zip(("participant_intercept","participant_slope","trial","sensor"),
               (r16.SIGMA_INTERCEPT,r16.SIGMA_RANDOM_SLOPE,
                r16.SIGMA_TRIAL,r16.SIGMA_SENSOR))}
        measured=nuisance["variance_components"]
        row.update(status="ok",inclusion=included,
          true_source_family_for_diagnostic_only=truth_structural_family,
          matching_assumed_covariance_shape=(family==truth_structural_family),
          component_variances=measured,
          source_true_component_variances_for_reporting_only=known,
          conditional_satterthwaite_df=float(nu),
          estimated_cr2_standard_error=float(feasible["cr2_se"]),
          simulation_known_oracle_standard_error=float(fitted["oracle_se"]),
          estimated_cr2_to_oracle_se=float(feasible["cr2_se"]/fitted["oracle_se"]),
          normalized_moment_residual=nuisance["nnls_normalized_residual"],
          component_rank=nuisance["component_rank"],
          component_condition_number=nuisance["component_condition_number"],
          sensor_floor_applied=nuisance["sensor_floor_applied"],
          fitted_point=float(fitted["point"]),known_truth=float(truth),
          source_uses_known_covariance_in_estimator=False,
          conditional_df_ignores_estimated_covariance_uncertainty=True)
    except Exception as exc:
        row["error"]={"type":type(exc).__name__,"message":str(exc)[:600]}
    return row


def wilson(k,n):
    if n<=0:return None
    z=float(norm.ppf(.975));p=k/n;d=1+z*z/n
    a=(p+z*z/(2*n))/d
    b=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return [0. if k==0 else float(max(0,a-b)),1. if k==n else float(min(1,a+b))]


def summarize(rows):
    expected={(b,n,s,m,f) for b in range(BLOCKS) for n in SIZES
        for s in SUPPORT for m in BASES for f in WORKING_FAMILIES}
    actual={(x["block"],x["n_participants"],x["source_support"],
        x["mean_basis"],x["working_family"]) for x in rows}
    if len(actual)!=len(rows):
        raise ValueError("duplicate case in R20 study")
    groups={}
    for n in SIZES:
        for support in SUPPORT:
            for model in BASES:
                for family in WORKING_FAMILIES:
                    cell=[x for x in rows if x["n_participants"]==n
                          and x["source_support"]==support
                          and x["mean_basis"]==model
                          and x["working_family"]==family]
                    ok=[x for x in cell if x["status"]=="ok"]
                    counts={method:sum(int(x["inclusion"][method]) for x in ok)
                            for method in METHODS}
                    groups[f"n{n}/{support}/{model}/{family}"]={
                        "planned_independent_blocks":BLOCKS,
                        "completed_independent_blocks":len(ok),
                        "failed_cases":len(cell)-len(ok),
                        "inclusion_counts":counts,
                        "wilson_95pct_mc_interval":{
                            method:wilson(counts[method],len(ok)) for method in METHODS},
                        "matching_structural_family":(
                          bool(ok[0]["matching_assumed_covariance_shape"]) if ok else None),
                        "mean_conditional_satterthwaite_df":(
                          float(np.mean([x["conditional_satterthwaite_df"] for x in ok])) if ok else None),
                        "mean_cr2_oracle_se_ratio":(
                          float(np.mean([x["estimated_cr2_to_oracle_se"] for x in ok])) if ok else None),
                        "sensor_floor_cases":sum(int(x["sensor_floor_applied"]) for x in ok),
                        "mean_component_condition_number":(
                          float(np.mean([x["component_condition_number"] for x in ok])) if ok else None),
                    }
    return {"study":STUDY,"master_seed":MASTER_SEED,
      "independent_generating_blocks":BLOCKS,"participants":SIZES,
      "support_conditions":SUPPORT,"mean_bases":BASES,"estimated_working_families":WORKING_FAMILIES,
      "planned_evaluations":PLANNED,"recorded_evaluations":len(rows),
      "completed_evaluations":sum(x["status"]=="ok" for x in rows),
      "failed_evaluations":sum(x["status"]!="ok" for x in rows),
      "missing_evaluations":len(expected-actual),
      "failures":[x for x in rows if x["status"]!="ok"][:24],
      "groups":groups,
      "pilot_only":True,"estimated_target_df_qualified":False,
      "pointwise_coverage_qualified":False,
      "simultaneous_band_qualified":False,"release_authorized":False}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    rows=[evaluate(b,n,s,m,f)
          for b in range(BLOCKS) for n in SIZES for s in SUPPORT
          for m in BASES for f in WORKING_FAMILIES]
    summary=summarize(rows)
    for name,obj in (("case-ledger.json",rows),("summary.json",summary)):
        (args.out/name).write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")
    (args.out/"source-commit.txt").write_text(os.getenv("GITHUB_SHA","unverified-local")+"\n")
    files=("case-ledger.json","summary.json","source-commit.txt")
    (args.out/"SHA256SUMS").write_text("".join(
       hashlib.sha256((args.out/name).read_bytes()).hexdigest()+"  "+name+"\n" for name in files))
    summary_line={k:v for k,v in summary.items() if k not in ("groups","failures")}
    print("R20 ESTIMATED TARGET SOURCE AUDIT:",json.dumps(summary_line,sort_keys=True))
    for key,value in summary["groups"].items():
        print("R20 ESTIMATED TARGET CELL:",json.dumps({"cell":key,**value},sort_keys=True))
    if summary["failed_evaluations"] or summary["missing_evaluations"] or summary["completed_evaluations"]!=PLANNED:
        raise SystemExit("R20 pilot source failures retained; no qualification")


if __name__=="__main__":
    main()
