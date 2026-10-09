"""Predeclared actual F5 unknown-dependence null and moderate-break study.

Generates an independent stationary baseline and a never-shared change-point
test series for each replicate. New seed namespace, never reuses the known-phi
oracle comparison's datasets. AR1 and deliberately misspecified AR2,
heavy-tailed and piecewise-dependence nulls remain scientifically distinct.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
from scipy.stats import binomtest

from eyetrajectoriespy.types import TrajectorySet
from eyetrajectoriespy.research.calibration_seed import calibration_replicate_seed
from eyetrajectoriespy.research.functional_changepoints_baseline_ar1 import (
    infer_ordered_functional_changepoint_baseline_ar1)
from eyetrajectoriespy.research.functional_changepoints_ar1_reference import (
    infer_ordered_functional_changepoint_ar1_reference)
from eyetrajectoriespy.research.functional_changepoints import (
    detect_ordered_functional_changepoint)

SCENARIOS={
    "iid":dict(phi=0.,kind="ar1",heavy_tail=False),
    "ar1_weak":dict(phi=.35,kind="ar1",heavy_tail=False),
    "ar1_strong":dict(phi=.8,kind="ar1",heavy_tail=False),
    "ar2_misspecified":dict(phi=None,kind="ar2",heavy_tail=False),
    "heavy_tail_ar1":dict(phi=.65,kind="ar1",heavy_tail=True),
}


def _series(seed:int,scenario:str,*,n:int,truth:str,prefix:str,
            phi_shift:float=0.)->TrajectorySet:
    if scenario not in SCENARIOS or truth not in ("null","one_break"):
        raise ValueError("predeclared scenario and null or one_break required")
    rng=np.random.default_rng(seed)
    spec=SCENARIOS[scenario]
    t=np.linspace(0.,1.,17)
    length=n+300
    if spec["heavy_tail"]:
        innovations=rng.standard_t(5,size=(length,17,2))*(.07/np.sqrt(5/3))
    else:
        innovations=rng.normal(0.,.07,size=(length,17,2))
    # Dense temporally smooth functional means that vanish from the CUSUM
    # null but nonstationary dependence must be diagnosed independently.
    z=np.zeros_like(innovations)
    for i in range(2,length):
        if spec["kind"]=="ar2":
            z[i]=.64*z[i-1]+.24*z[i-2]+innovations[i]
        else:
            phi=float(spec["phi"])+phi_shift
            z[i]=phi*z[i-1]+np.sqrt(1-phi**2)*innovations[i]
    curves=z[-n:].copy()
    if truth=="one_break":
        curves[n//2:,:,0] += .12*np.sin(np.pi*t)[None,:]
    return TrajectorySet(
        time=t,values=curves,
        curve_ids=tuple(f"{prefix}-{i}" for i in range(n)),
        dimension_names=("x","y"),coordinate_system="normalized",
        time_unit="s",
        metadata=pd.DataFrame({"participant_id":[f"{prefix}-{i}" for i in range(n)]}),
    )


def study(*,null_reps:int=120,alt_reps:int=60,
          n_bootstrap:int=149,phi_bootstrap:int=119,
          master_seed:int=20261204)->tuple[pd.DataFrame,dict]:
    if (min(null_reps,alt_reps)<2 or
        min(n_bootstrap,phi_bootstrap)<99):
        raise ValueError("at least two independent replicates and 99 null/parameter draws")
    records=[]
    for scenario,spec in SCENARIOS.items():
        for truth,count in (("null",null_reps),("one_break",alt_reps)):
            for replicate in range(count):
                seed=calibration_replicate_seed(
                    "F5_NEW_UNKNOWN_PHI_BASELINE",
                    master_seed=master_seed,shard_id=0,
                    scenario=scenario+"_"+truth,replicate=replicate)
                train=_series(seed,scenario,n=80,truth="null",prefix=f"train-{seed}")
                test=_series(seed+811,scenario,n=36,truth=truth,prefix=f"test-{seed}")
                methods=("external_baseline_unknown_phi","legacy_block4")
                if spec["kind"]=="ar1":
                    methods+=("oracle_known_phi",)
                for method in methods:
                    item={
                        "scenario":scenario,"truth":truth,
                        "replicate":replicate,"seed":seed,
                        "method":method,"status":"failed",
                        "p_value":None,"estimated_break_index":None,
                        "phi_estimated_from_baseline":None,
                        "phi_approx_q025":None,"phi_approx_q975":None,
                        "error_type":None,"exception":None,
                    }
                    try:
                        if method=="external_baseline_unknown_phi":
                            fit=infer_ordered_functional_changepoint_baseline_ar1(
                                test,independent_stationary_baseline=train,
                                n_null_simulations=n_bootstrap,
                                n_parameter_bootstrap=phi_bootstrap,
                                min_segment=6,random_state=seed+991)
                            ev=fit.evidence
                            item["phi_estimated_from_baseline"]=ev["baseline_pooled_phi_ols"]
                            item["phi_approx_q025"]=ev["approximate_phi_uncertainty_quantiles_025_50_975"][0]
                            item["phi_approx_q975"]=ev["approximate_phi_uncertainty_quantiles_025_50_975"][2]
                        elif method=="oracle_known_phi":
                            fit=infer_ordered_functional_changepoint_ar1_reference(
                                test,ar1_coefficient_from_independent_baseline=float(spec["phi"]),
                                n_bootstrap=n_bootstrap,min_segment=6,
                                random_state=seed+991)
                        else:
                            fit=detect_ordered_functional_changepoint(
                                test,dependence=("weak_block" if scenario!="iid" else "independent"),
                                block_length=(4 if scenario!="iid" else None),
                                min_segment=6,n_bootstrap=n_bootstrap,
                                random_state=seed+991)
                        item.update(
                            status="ok",p_value=float(fit.p_value_experimental),
                            estimated_break_index=int(fit.split_index))
                    except Exception as exc:
                        item["error_type"]=type(exc).__name__
                        item["exception"]=str(exc)[:600]
                    records.append(item)
    cases=pd.DataFrame(records)
    results=[]
    for (sc,truth,method),group in cases.groupby(
        ["scenario","truth","method"],sort=True):
        ok=group[group.status=="ok"]
        result={
            "scenario":sc,"truth":truth,"method":method,
            "attempted":len(group),"failed":len(group)-len(ok),
            "model_assumptions_satisfied":SCENARIOS[sc]["kind"]=="ar1",
            "scientific_operating_characteristics_qualified":False,
        }
        for alpha in (.01,.05,.10):
            k=int((ok.p_value<=alpha).sum());n=len(ok)
            ci=binomtest(k,n).proportion_ci(.95,method="exact") if n else None
            result[f"alpha_{alpha:g}"]={
                "rejections":k,"successful":n,
                "fraction":k/n if n else None,
                "all_attempts":len(group),
                "failure_inclusive_fraction":k/len(group),
                "exact_95_MC_interval":[float(ci.low),float(ci.high)] if ci else None}
        results.append(result)
    ev={
        "programme":"F5_fully_independent_baseline_unknown_phi_nonAR1_stress",
        "master_seed":master_seed,
        "historical_F5_oracle_study_reused":False,
        "test_series_n":36,"independent_baseline_n":80,
        "true_null_attempts_per_scenario":null_reps,
        "moderate_one_break_attempts_per_scenario":alt_reps,
        "n_null_resamples_per_fit":n_bootstrap,
        "n_phi_uncertainty_refits_per_fit":phi_bootstrap,
        "all_model_attempts":len(cases),
        "fit_failures":int(cases.status.eq("failed").sum()),
        "truly_no_test_series_nuisance_leakage":True,
        "AR2_misspecification_explicit":True,
        "whole_function_innovation_resampling":True,
        "baseline_to_test_transfer_validated":False,
        "unknown_phi_statistical_calibration_qualified":False,
        "non_AR1_calibration_qualified":False,
        "scientific_inference_qualified":False,
        "release_authorized":False,
        "results":results,
    }
    return cases,ev


def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--null-reps",type=int,default=120)
    ap.add_argument("--alt-reps",type=int,default=60)
    ap.add_argument("--bootstrap",type=int,default=149)
    ap.add_argument("--phi-bootstrap",type=int,default=119)
    ap.add_argument("--master-seed",type=int,default=20261204)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    cases,ev=study(null_reps=a.null_reps,alt_reps=a.alt_reps,
        n_bootstrap=a.bootstrap,phi_bootstrap=a.phi_bootstrap,
        master_seed=a.master_seed)
    a.out.mkdir(parents=True,exist_ok=True)
    p=a.out/"cases.csv";e=a.out/"evidence.json"
    cases.to_csv(p,index=False)
    e.write_text(json.dumps(ev,sort_keys=True,indent=2)+"\n")
    (a.out/"sha256.txt").write_text(
        sha256(p.read_bytes()).hexdigest()+"  cases.csv\n"+
        sha256(e.read_bytes()).hexdigest()+"  evidence.json\n")
    print(json.dumps({"attempts":len(cases),
        "failures":ev["fit_failures"],"science_qualified":False,
        "summary":ev["results"]},sort_keys=True))


if __name__=="__main__":
    main()
