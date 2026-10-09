"""Prespecified F5 baseline-estimated AR1 versus AR2 model-misspecification study.

Research-only, no automatic model selection. Explicit moving-average and
within-test nonstationary counterexamples are retained, not tuned away.
Independent baseline/test trajectories and replicate failures are archived.
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
    infer_ordered_functional_changepoint_baseline_ar1 as ar1)
from eyetrajectoriespy.research.functional_changepoints_baseline_ar2 import (
    infer_ordered_functional_changepoint_baseline_ar2 as ar2)
from scripts.run_f5_unknown_phi_independent_baseline_validation import _series

SCENARIOS=("iid","ar1_strong","ar2_misspecified","ma1_unmodelled",
           "nonstationary_ar1_transfer")
METHODS=("AR1_external_baseline","AR2_external_baseline")


def _test_series(seed:int,scenario:str,*,n:int,truth:str,prefix:str,
                 baseline:bool)->TrajectorySet:
    if scenario in ("iid","ar1_strong","ar2_misspecified"):
        return _series(seed,scenario,n=n,truth=truth,prefix=prefix)
    if scenario not in SCENARIOS or truth not in ("null","one_break"):
        raise ValueError("unknown prespecified dependence stress")
    rng=np.random.default_rng(seed)
    time=np.linspace(0,1,17)
    count=n+300
    eps=rng.normal(scale=.07,size=(count,17,2))
    z=np.zeros_like(eps)
    if scenario=="ma1_unmodelled":
        for i in range(1,count):
            z[i]=eps[i]+.7*eps[i-1]
    else:
        for i in range(1,count):
            # Deliberate transfer failure: stationary baseline phi=.35,
            # test sequence changes dependence from .35 to .85 halfway
            # through *without changing mean*. The mean-null is still true.
            local_phi=.35 if baseline or i<count-n//2 else .85
            z[i]=local_phi*z[i-1]+np.sqrt(1-local_phi**2)*eps[i]
    curves=z[-n:].copy()
    if truth=="one_break":
        curves[n//2:,:,0]+=.12*np.sin(np.pi*time)[None,:]
    return TrajectorySet(
        time=time,values=curves,
        curve_ids=tuple(f"{prefix}-{i}" for i in range(n)),
        dimension_names=("x","y"),coordinate_system="normalized",time_unit="s",
        metadata=pd.DataFrame({"participant_id":[f"{prefix}-{i}" for i in range(n)]}),
    )


def study(*,null_reps:int=120,alternative_reps:int=60,
    n_null:int=149,n_parameter:int=119,master_seed:int=20261207,
    scenarios:tuple[str,...]=SCENARIOS):
    if (not scenarios or not set(scenarios).issubset(SCENARIOS) or
        len(scenarios)!=len(set(scenarios)) or
        min(null_reps,alternative_reps)<2 or min(n_null,n_parameter)<99):
        raise ValueError("must preserve declared model/null/scenario contracts")
    cases=[]
    for scenario in scenarios:
        for truth,count in (("null",null_reps),("one_break",alternative_reps)):
            for rep in range(count):
                base_seed=calibration_replicate_seed(
                    "F5_INDEPENDENT_BASELINE_AR2_MODEL_STRESS_V1",
                    master_seed=master_seed,shard_id=0,
                    scenario=scenario+"_"+truth+"_baseline",replicate=rep)
                test_seed=calibration_replicate_seed(
                    "F5_INDEPENDENT_BASELINE_AR2_MODEL_STRESS_V1",
                    master_seed=master_seed,shard_id=0,
                    scenario=scenario+"_"+truth+"_test",replicate=rep)
                base=_test_series(
                    base_seed,scenario,n=80,truth="null",
                    prefix=f"BASE-{base_seed}",baseline=True)
                test=_test_series(
                    test_seed,scenario,n=36,truth=truth,
                    prefix=f"TEST-{test_seed}",baseline=False)
                for name,method in (("AR1_external_baseline",ar1),
                                    ("AR2_external_baseline",ar2)):
                    item=dict(scenario=scenario,truth=truth,replicate=rep,
                        train_seed=base_seed,test_seed=test_seed,method=name,
                        status="failed",p_value=None,
                        estimated_ar1=None,estimated_ar2_phi1=None,
                        estimated_ar2_phi2=None,
                        nonstationary_parameter_draws=None,
                        exception_type=None,exception=None,
                        scientific_inference_qualified=False)
                    try:
                        fitted=method(
                            test,independent_stationary_baseline=base,
                            n_null_simulations=n_null,
                            n_parameter_bootstrap=n_parameter,
                            min_segment=6,random_state=test_seed+701)
                        item["status"]="ok"
                        item["p_value"]=fitted.p_value_experimental
                        if name=="AR1_external_baseline":
                            item["estimated_ar1"]=fitted.evidence[
                                "baseline_pooled_phi_ols"]
                        else:
                            item["estimated_ar2_phi1"],item["estimated_ar2_phi2"]=(
                                fitted.evidence["estimated_ar2_coefficient"])
                            item["nonstationary_parameter_draws"]=fitted.evidence[
                                "n_parameter_draws_rejected_nonstationary"]
                    except Exception as err:
                        item["exception_type"]=type(err).__name__
                        item["exception"]=str(err)[:500]
                    cases.append(item)
    frame=pd.DataFrame(cases)
    summary=[]
    for (scenario,truth,method),group in frame.groupby(
        ["scenario","truth","method"],sort=True):
        ok=group[group.status=="ok"]
        entry=dict(scenario=scenario,truth=truth,method=method,
            actual_attempts=len(group),successful=len(ok),
            failures=len(group)-len(ok),alpha_results={},
            inference_scientifically_qualified=False)
        for alpha in (.01,.05,.10):
            k=int((ok.p_value<=alpha).sum())
            n=len(ok)
            ci=binomtest(k,n).proportion_ci(.95,method="exact") if n else None
            entry["alpha_results"][str(alpha)]=dict(
                rejection_count=k,n_success=n,
                rate_success_conditional=k/n if n else None,
                failure_inclusive_rate=k/len(group),
                exact95_mc_ci=([float(ci.low),float(ci.high)] if ci else None))
        summary.append(entry)
    evidence=dict(
        programme="F5_independent_baseline_AR2_vs_AR1_null_model_stress",
        data_new_seed_namespace="F5_INDEPENDENT_BASELINE_AR2_MODEL_STRESS_V1",
        master_seed=master_seed,
        scenarios=list(scenarios),methods=list(METHODS),
        no_automatic_model_selection=True,
        original_model_defaults_unchanged=True,
        independent_baseline_length=80,test_length=36,
        genuine_independent_test_datasets=len(scenarios)*(null_reps+alternative_reps),
        n_null_dataset_per_scenario=null_reps,
        n_alt_dataset_per_scenario=alternative_reps,
        actual_method_attempts=len(frame),
        all_failure_cases_retained=True,
        method_fit_errors=int(frame.status.eq("failed").sum()),
        stationarity_broken_in_test_counterexample_included="nonstationary_ar1_transfer" in scenarios,
        misspecified_MA1_counterexample_included="ma1_unmodelled" in scenarios,
        null_parameter_uncertainty_is_approximate=True,
        claims_of_nominal_size_qualified=False,
        release_authorized=False,
        scientific_inference_qualified=False,summary=summary)
    return frame,evidence


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--scenario",choices=SCENARIOS,action="append")
    ap.add_argument("--null-reps",type=int,default=120)
    ap.add_argument("--alternative-reps",type=int,default=60)
    ap.add_argument("--n-null",type=int,default=149)
    ap.add_argument("--n-parameter",type=int,default=119)
    ap.add_argument("--seed",type=int,default=20261207)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    frame,ev=study(null_reps=a.null_reps,alternative_reps=a.alternative_reps,
        n_null=a.n_null,n_parameter=a.n_parameter,master_seed=a.seed,
        scenarios=tuple(a.scenario) if a.scenario else SCENARIOS)
    a.out.mkdir(parents=True,exist_ok=True)
    f=a.out/"cases.csv";e=a.out/"evidence.json"
    frame.to_csv(f,index=False)
    e.write_text(json.dumps(ev,sort_keys=True,indent=2)+"\n")
    (a.out/"SHA256SUMS").write_text(
        sha256(f.read_bytes()).hexdigest()+"  cases.csv\n"+
        sha256(e.read_bytes()).hexdigest()+"  evidence.json\n")
    print(json.dumps({
        "attempts":len(frame),"errors":ev["method_fit_errors"],
        "scientific_qualification":False,"summary":ev["summary"]},sort_keys=True))


if __name__=="__main__":
    main()
