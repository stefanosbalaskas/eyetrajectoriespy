"""R21: immutable-source eigen diagnostics for R20 estimated-CR2 failures.

Replays all 256 original R20 cases using the frozen source seed. Separates
(1) fitted covariance Phi positivity/scale, (2) CR2 residual covariance D,
(3) the symmetric SPD adjustment's Phi^(1/2) D Phi^(1/2) conditioning.
Never changes the original estimator, acceptance threshold or 41 failed
cases. This is diagnostic, not corrected interval inference.
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
from scripts import run_w3_r16_leverage_covariance_factorial as r16
from scripts import run_w3_r17_fresh_feasibility as source
from scripts import run_w3_r20_estimated_target_pilot as pilot
from scripts.w3_r20_estimated_working_target import (
    observed_weighted_rows,estimate_feasible_working_target)

STUDY="W3_R21_ORIGINAL_ESTIMATED_COVARIANCE_SPECTRAL_AUDIT"
ORIGINAL_FAILED_CASES=41
ORIGINAL_FAILURE_KEY_SHA256="a75ffbf14fb632ffa7ce18ad0203e25141c3ff9d83bbb676ecf6ac55dbc0010e"
ABSOLUTE_REFERENCE_EIG_TOL=1e-11


def diagnose(block,n,support,model,family):
    row={"study":STUDY,"block":block,"n_participants":n,
         "source_support":support,"mean_basis":model,"working_family":family,
         "status":"diagnostic_failed","exception":None,
         "original_source_unchanged":True,"release_authorized":False}
    try:
        data=source.fresh_source(block,support,n=n,
             master_seed=pilot.MASTER_SEED,n_blocks=pilot.BLOCKS,max_n=max(pilot.SIZES))
        X,y,w,ids,t,tr,x=observed_weighted_rows(
             (None,data[1],data[2],data[3],data[4],None),model)
        target=estimate_feasible_working_target(
             X,y,w,ids,t,tr,x,slope=family)
        Z=X*np.sqrt(w)[:,None]
        invG=np.linalg.solve(Z.T@Z,np.eye(X.shape[1]))
        participants=np.unique(ids)
        slices=[np.flatnonzero(ids==i) for i in participants]
        blocks=target["working_blocks"]
        M=np.zeros((X.shape[1],X.shape[1]))
        for ix,Phi in zip(slices,blocks):
            zi=Z[ix]
            M+=zi.T@Phi@zi
        diagnostics=[]
        for i,(ix,Phi) in enumerate(zip(slices,blocks)):
            zi=Z[ix]
            hii=zi@invG@zi.T
            D=Phi-hii@Phi-Phi@hii+zi@invG@M@invG@zi.T
            D=(D+D.T)/2
            ep=np.linalg.eigvalsh((Phi+Phi.T)/2)
            ed=np.linalg.eigvalsh(D)
            if ep.min()>0:
                val,U=np.linalg.eigh((Phi+Phi.T)/2)
                root=(U*np.sqrt(val))@U.T
                B=root@D@root
                eb=np.linalg.eigvalsh((B+B.T)/2)
                b_min=float(eb.min())
                b_max=float(eb.max())
            else:
                b_min=None;b_max=None
            diagnostics.append({
                "participant":int(i),
                "phi_min_eigenvalue":float(ep.min()),
                "phi_max_eigenvalue":float(ep.max()),
                "D_min_eigenvalue":float(ed.min()),
                "D_max_eigenvalue":float(ed.max()),
                "sandwich_min_eigenvalue":b_min,
                "sandwich_max_eigenvalue":b_max,
            })
        minphi=min(v["phi_min_eigenvalue"] for v in diagnostics)
        minD=min(v["D_min_eigenvalue"] for v in diagnostics)
        minB=min(v["sandwich_min_eigenvalue"] for v in diagnostics
                 if v["sandwich_min_eigenvalue"] is not None) if minphi>0 else None
        if minphi<=0:
            mechanism="fitted_covariance_nonpositive"
        elif minphi<=ABSOLUTE_REFERENCE_EIG_TOL:
            mechanism="fitted_covariance_below_absolute_threshold"
        elif minD<=0:
            mechanism="residual_covariance_nonpositive"
        elif minB is None or minB<=0:
            mechanism="symmetric_cr2_sandwich_nonpositive"
        elif minB<=ABSOLUTE_REFERENCE_EIG_TOL:
            mechanism="symmetric_cr2_sandwich_below_absolute_threshold"
        else:
            mechanism="reference_eigenvalues_above_threshold"
        row.update(status="ok",
            mechanism=mechanism,
            min_fitted_phi_eigenvalue=float(minphi),
            min_residual_D_eigenvalue=float(minD),
            min_symmetric_cr2_sandwich_eigenvalue=minB,
            working_variance_components=target["variance_components"],
            nnls_moment_condition_number=target["component_condition_number"],
            sensor_floor_applied=target["sensor_floor_applied"],
            observed_only_estimation=True,
            source_covariance_oracle_not_used=True)
    except Exception as exc:
        row["exception"]={"type":type(exc).__name__,"message":str(exc)[:700]}
    return row


def case_key(x):
    return (f'{x["block"]}|{x["n_participants"]}|{x["source_support"]}|'
            f'{x["mean_basis"]}|{x["working_family"]}')


def summarize(rows,original_status):
    expected={(b,n,s,m,f) for b in range(pilot.BLOCKS) for n in pilot.SIZES
              for s in pilot.SUPPORT for m in pilot.BASES for f in pilot.WORKING_FAMILIES}
    actual={(x["block"],x["n_participants"],x["source_support"],x["mean_basis"],x["working_family"]) for x in rows}
    if len(actual)!=len(rows):raise ValueError("duplicate diagnostic")
    failures=sorted(case_key(x) for x in original_status if x["status"]!="ok")
    failures_digest=hashlib.sha256(("\n".join(failures)+"\n").encode()).hexdigest()
    mechanisms={}
    for x in rows:
        classification=x.get("mechanism","diagnostic_failed")
        mechanisms[classification]=mechanisms.get(classification,0)+1
    original_fail=[x for x in rows if case_key(x) in failures]
    original_pass=[x for x in rows if case_key(x) not in failures]
    return {"study":STUDY,
      "original_R20_master_seed":pilot.MASTER_SEED,
      "independent_original_blocks":pilot.BLOCKS,
      "planned_original_cases":len(expected),
      "recorded_original_cases":len(rows),
      "completed_spectral_diagnostics":sum(x["status"]=="ok" for x in rows),
      "failed_spectral_diagnostics":sum(x["status"]!="ok" for x in rows),
      "missing_diagnostics":len(expected-actual),
      "original_source_failed_cases":len(failures),
      "original_failure_keys_digest":failures_digest,
      "matches_frozen_original_failure_set":(
          len(failures)==ORIGINAL_FAILED_CASES
          and failures_digest==ORIGINAL_FAILURE_KEY_SHA256),
      "mechanism_counts":mechanisms,
      "original_failed_case_mechanisms":{
         k:sum(x.get("mechanism")==k for x in original_fail) for k in mechanisms},
      "original_passed_case_mechanisms":{
         k:sum(x.get("mechanism")==k for x in original_pass) for k in mechanisms},
      "changes_original_source_results":False,
      "inference_qualified":False,
      "simultaneous_bands_qualified":False,
      "release_authorized":False}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    rows=[];original=[]
    for b in range(pilot.BLOCKS):
        for n in pilot.SIZES:
            for s in pilot.SUPPORT:
                for m in pilot.BASES:
                    for f in pilot.WORKING_FAMILIES:
                        rows.append(diagnose(b,n,s,m,f))
                        original.append(pilot.evaluate(b,n,s,m,f))
    summary=summarize(rows,original)
    for name,obj in (("case-ledger.json",rows),
                     ("original-R20-case-status.json",original),
                     ("summary.json",summary)):
        (args.out/name).write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")
    (args.out/"source-commit.txt").write_text(os.getenv("GITHUB_SHA","unverified-local")+"\n")
    files=("case-ledger.json","original-R20-case-status.json","summary.json","source-commit.txt")
    (args.out/"SHA256SUMS").write_text("".join(
        hashlib.sha256((args.out/name).read_bytes()).hexdigest()+"  "+name+"\n"
        for name in files))
    print("R21 ORIGINAL SPECTRAL AUDIT:",json.dumps(summary,sort_keys=True))
    if (summary["failed_spectral_diagnostics"] or summary["missing_diagnostics"]
        or not summary["matches_frozen_original_failure_set"]):
        raise SystemExit("R21 diagnostic failure or original 41-case source mismatch")


if __name__=="__main__":
    main()
