"""R18: independent Gaussian-source oracle variance and coverage replication.

Research-only: 192 genuinely fresh source blocks, n=96 ordinary predictor
support, independent/dependent within-person covariance, Legendre-5 and
cubic-spline-13. The generating time observations are native/asynchronous.
Neither original R17 results nor fixed finite-basis estimands are changed.
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
from scripts import run_w3_r17_fresh_feasibility as r17
from scripts import run_w3_r17_independent_96block_calibration as prior

STUDY="W3_R18_FRESH_GAUSSIAN_ORACLE_REPLICATION"
MASTER_SEED=202610142621
BLOCKS=192
PARTICIPANTS=96
SUPPORT=("ordinary_independent","ordinary_dependent")
BASES=r16.MODELS
NOMINAL=.90
EXPECTED=BLOCKS*len(SUPPORT)*len(BASES)
T_CRITICAL=float(student_t.ppf(.95,PARTICIPANTS-1))
N_CRITICAL=float(norm.ppf(.95))


def generate(block,support):
    return r17.fresh_source(block,support,n=PARTICIPANTS,
         master_seed=MASTER_SEED,n_blocks=BLOCKS,max_n=PARTICIPANTS)


def direct_oracle_variance(data,model):
    """Independently reconstruct participant block covariance from native rows."""
    X,y,w,group,phi=r17.prepare(data,model)
    k=r16.basis(np.asarray([.5]),model).shape[1]
    c=np.r_[np.zeros(k),r16.basis(np.asarray([r16.TIME[r16.FOCAL]]),model)[0]]
    Z=X*np.sqrt(w)[:,None]
    b=np.linalg.solve(Z.T@Z,c)
    independent_variance=0.0
    for i,P in enumerate(phi):
        z=Z[group==i]@b
        independent_variance+=float(z@P@z)
    return independent_variance, X,y,w,group,c


def evaluate(block,support,model):
    record={"study":STUDY,"block":block,"support":support,"model":model,
        "n_participants":PARTICIPANTS,"status":"failed","exception":None,
        "independent_replicate":True,"inference_qualified":False,
        "release_authorized":False}
    try:
        data=generate(block,support)
        ref=r16.fit(data,model)
        independent,X,y,w,groups,c=direct_oracle_variance(data,model)
        if abs(independent-ref["oracle_se"]**2)>2e-7:
            raise ValueError("independent block Gaussian covariance variance mismatch")
        if independent<=0 or not np.isfinite(independent):
            raise ValueError("invalid analytical Gaussian covariance")
        Z=X*np.sqrt(w)[:,None]
        beta=np.linalg.solve(Z.T@Z,Z.T@(np.sqrt(w)*y))
        point=float(c@beta)
        if abs(point-ref["point"])>r16.NUMERICAL_TOL:
            raise ValueError("independent Gaussian WLS point mismatch")
        # y-mu comprises only independent Gaussian generating innovations;
        # direct conditional projection is the mean of the same WLS estimator.
        mu=np.concatenate([np.asarray(a) for a in data[5]])
        if len(mu)!=len(y):
            raise ValueError("native conditional mean/observation map mismatch")
        projection=float(c@np.linalg.solve(Z.T@Z,Z.T@(np.sqrt(w)*mu)))
        if abs(projection-ref["project"])>r16.NUMERICAL_TOL:
            raise ValueError("independent known-mean projection mismatch")
        se=np.sqrt(independent)
        z_projection=(point-projection)/se
        z_truth=(point-ref["known_mid_slope"])/se
        shift=(projection-ref["known_mid_slope"])/se
        if not np.isfinite([z_projection,z_truth,shift]).all():
            raise ValueError("nonfinite standardized Gaussian source error")
        record.update(status="ok",point=point,truth=float(ref["known_mid_slope"]),
            projected_truth=projection,oracle_se=float(se),oracle_variance_direct=float(independent),
            oracle_variance_R16=float(ref["oracle_se"]**2),
            independent_covariance_difference=float(abs(independent-ref["oracle_se"]**2)),
            gaussian_error_z_projected=float(z_projection),
            gaussian_error_z_continuous_truth=float(z_truth),
            projection_shift_oracle_SE=float(shift),
            truth_included_normal=bool(abs(z_truth)<=N_CRITICAL),
            projection_included_normal=bool(abs(z_projection)<=N_CRITICAL),
            truth_included_tGminus1=bool(abs(z_truth)<=T_CRITICAL),
            projection_included_tGminus1=bool(abs(z_projection)<=T_CRITICAL),
            original_R17_results_unchanged=True)
    except Exception as exc:
        record["exception"]={"type":type(exc).__name__,"message":str(exc)[:600]}
    return record


def wilson(success,total,alpha=.05):
    if total<=0:return None
    z=float(norm.ppf(1-alpha/2))
    p=success/total
    d=1+z*z/total
    m=(p+z*z/(2*total))/d
    h=z*np.sqrt(p*(1-p)/total+z*z/(4*total*total))/d
    return [0.0 if success==0 else float(max(0.,m-h)),
            1.0 if success==total else float(min(1.,m+h))]


def summarize(rows):
    expected={(i,s,m) for i in range(BLOCKS) for s in SUPPORT for m in BASES}
    actual={(x["block"],x["support"],x["model"]) for x in rows}
    if len(rows)!=len(actual):raise ValueError("duplicate R18 source/design cases")
    results={}
    for s in SUPPORT:
        for model in BASES:
            cell=[x for x in rows if x["support"]==s and x["model"]==model]
            ok=[x for x in cell if x["status"]=="ok"]
            key=f"{s}/{model}"
            empirical=np.array([x["gaussian_error_z_projected"] for x in ok])
            rates={}
            for outcome in ("truth_included_normal","projection_included_normal",
                             "truth_included_tGminus1","projection_included_tGminus1"):
                k=sum(bool(x[outcome]) for x in ok)
                rates[outcome]={"included":int(k),"complete":len(ok),
                    "rate":float(k/len(ok)) if ok else None,
                    "wilson_95pct":wilson(k,len(ok))}
            results[key]={
                "planned_independent_blocks":BLOCKS,
                "completed_independent_blocks":len(ok),
                "failed_cases":len(cell)-len(ok),
                "coverage":rates,
                "mean_z_projected":float(empirical.mean()) if len(ok) else None,
                "sd_z_projected":float(empirical.std(ddof=1)) if len(ok)>1 else None,
                "mean_z_projected_squared":float(np.mean(empirical**2)) if len(ok) else None,
                "max_abs_independent_variance_difference":float(max(x["independent_covariance_difference"] for x in ok)) if ok else None,
                "mean_abs_projection_displacement_SE":float(np.mean([abs(x["projection_shift_oracle_SE"]) for x in ok])) if ok else None,
            }
    return {
        "study":STUDY,"master_seed":MASTER_SEED,
        "original_R17_seed":prior.MASTER_SEED,
        "R17_feasibility_seed":r17.R17_SEED,
        "original_R16_seed":r16.SEED,
        "participants":PARTICIPANTS,
        "independent_source_blocks":BLOCKS,
        "planned_evaluations":EXPECTED,"completed_evaluations":sum(x["status"]=="ok" for x in rows),
        "recorded_evaluations":len(rows),
        "failed_evaluations":sum(x["status"]!="ok" for x in rows),
        "missing_evaluations":len(expected-actual),
        "supports":SUPPORT,"mean_bases":BASES,"cells":results,
        "conditional_gaussian_oracle_only":True,
        "changes_original_R17_data":False,
        "general_empirical_coverage_qualified":False,
        "simultaneous_inference_qualified":False,
        "production_release_ready":False
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    rows=[evaluate(i,s,b) for i in range(BLOCKS) for s in SUPPORT for b in BASES]
    summary=summarize(rows)
    for name,obj in (("case-ledger.json",rows),("summary.json",summary)):
        (args.out/name).write_text(json.dumps(obj,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    (args.out/"source-commit.txt").write_text(os.environ.get("GITHUB_SHA","unverified-local")+"\n")
    names=["case-ledger.json","summary.json","source-commit.txt"]
    (args.out/"SHA256SUMS").write_text("".join(
        hashlib.sha256((args.out/name).read_bytes()).hexdigest()+"  "+name+"\n" for name in names))
    short={k:v for k,v in summary.items() if k!="cells"}
    print("R18 GAUSSIAN ORACLE AUDIT:",json.dumps(short,sort_keys=True))
    for name,values in summary["cells"].items():
        print("R18 GAUSSIAN ORACLE CELL:",json.dumps({"name":name,**values},sort_keys=True))
    if summary["failed_evaluations"] or summary["missing_evaluations"] or summary["completed_evaluations"]!=EXPECTED:
        raise SystemExit("R18 original source failure preserved")


if __name__=="__main__":
    main()
