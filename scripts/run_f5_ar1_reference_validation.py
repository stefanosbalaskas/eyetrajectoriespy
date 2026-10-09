"""New independently seeded F5 stationary-AR1 oracle experiment (research only).

Paired comparison on NEW datasets, not the 20261009 prior validation seeds.
The innovation-permutation comparator receives the *known simulation phi*;
real-data nuisance estimation is a separate scientific problem. The legacy
weak-block competitor is run without modifying its implementation.
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

from eyetrajectoriespy.research.calibration_seed import calibration_replicate_seed
from eyetrajectoriespy.research.functional_changepoints_ar1_reference import (
    infer_ordered_functional_changepoint_ar1_reference,
)
from eyetrajectoriespy.research import detect_ordered_functional_changepoint
from scripts.run_f1_f5_scientific_stress import _ordered_fixture,F5_SCENARIOS

SCENARIOS=("iid_gaussian","weak_AR1","strong_AR1")
TRUTHS=("null","one_break")


def study(*,null_reps:int=200,alt_reps:int=100,n_bootstrap:int=199,
          master_seed:int=20261120)->tuple[pd.DataFrame,dict]:
    if (min(null_reps,alt_reps)<2 or n_bootstrap<99 or
        isinstance(n_bootstrap,bool)):
        raise ValueError("positive independent replicates and >=99 draws")
    rows=[]
    for scenario in SCENARIOS:
        phi=F5_SCENARIOS[scenario]["phi"]
        for change,reps in (("null",null_reps),("one_break",alt_reps)):
            for replicate in range(reps):
                seed=calibration_replicate_seed(
                    "F5_AR1_ORACLE_REFERENCE",master_seed=master_seed,
                    shard_id=0,scenario=scenario+"_"+change,replicate=replicate)
                trial=_ordered_fixture(seed,scenario,change)
                for method in ("AR1_known_coefficient","legacy_block_4"):
                    record={
                        "scenario":scenario,"change":change,
                        "method":method,"phi_truth":phi,
                        "replicate":replicate,"seed":seed,
                        "status":"failed","p_value":None,
                        "estimated_break_index":None,
                        "error_type":None,"exception":None,
                    }
                    try:
                        if method=="AR1_known_coefficient":
                            fit=infer_ordered_functional_changepoint_ar1_reference(
                                trial,ar1_coefficient_from_independent_baseline=phi,
                                n_bootstrap=n_bootstrap,min_segment=6,
                                random_state=seed+101)
                        else:
                            dependence="weak_block" if phi else "independent"
                            fit=detect_ordered_functional_changepoint(
                                trial,dependence=dependence,
                                block_length=(4 if phi else None),
                                min_segment=6,n_bootstrap=n_bootstrap,
                                random_state=seed+101)
                        record.update(
                            status="ok",p_value=float(fit.p_value_experimental),
                            estimated_break_index=int(fit.split_index))
                    except Exception as exc:
                        record["error_type"]=type(exc).__name__
                        record["exception"]=str(exc)[:500]
                    rows.append(record)
    frame=pd.DataFrame(rows)
    results=[]
    for (scenario,change,method),sub in frame.groupby(
        ["scenario","change","method"],sort=True):
        ok=sub[sub.status=="ok"]
        result={
            "scenario":scenario,"change":change,"method":method,
            "attempted":len(sub),"failed":len(sub)-len(ok),
            "conditioning_on_successful_fit":True,
            "independent_null_truth_for_test":change=="null",
            "operating_characteristics_qualified":False,
        }
        for alpha in (.01,.05,.10):
            n=len(ok)
            k=int((ok.p_value<=alpha).sum())
            ci=binomtest(k,n).proportion_ci(.95,method="exact") if n else None
            result[f"alpha_{alpha:g}"]={
                "rejections":k,"n_successful":n,
                "fraction":k/n if n else None,
                "exact_95_mc_interval":[float(ci.low),float(ci.high)] if ci else None,
            }
        results.append(result)
    evidence={
        "programme":"F5_independent_stationary_AR1_reference_comparator",
        "source_wave_reference_id":37965949039,
        "source_seed_reused":False,
        "experiment_master_seed":master_seed,
        "oracle_ar1_coefficients_used":True,
        "independently_estimated_real_data_phi_validated":False,
        "model_assumption":"whole_function_scalar_stationary_AR1_iid_innovation_vectors",
        "baseline_method":"existing_weak_block_length4_or_independent",
        "case_random_seed_pairing_across_methods":True,
        "null_reps_per_scenario":null_reps,
        "alternative_reps_per_scenario":alt_reps,
        "bootstrap_per_fit":n_bootstrap,
        "total_attempts":len(frame),
        "fit_failures":int((frame.status=="failed").sum()),
        "hypothesis_test_scientifically_qualified":False,
        "dependent_F5_original_method_scientifically_qualified":False,
        "release_authorized":False,
        "results":results,
    }
    return frame,evidence


def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--null-reps",type=int,default=200)
    ap.add_argument("--alt-reps",type=int,default=100)
    ap.add_argument("--bootstrap",type=int,default=199)
    ap.add_argument("--master-seed",type=int,default=20261120)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    frame,ev=study(null_reps=a.null_reps,alt_reps=a.alt_reps,
                   n_bootstrap=a.bootstrap,master_seed=a.master_seed)
    a.out.mkdir(parents=True,exist_ok=True)
    p=a.out/"cases.csv";e=a.out/"evidence.json"
    frame.to_csv(p,index=False)
    e.write_text(json.dumps(ev,sort_keys=True,indent=2)+"\n")
    (a.out/"sha256.txt").write_text(
        sha256(p.read_bytes()).hexdigest()+"  cases.csv\n"+
        sha256(e.read_bytes()).hexdigest()+"  evidence.json\n")
    print(json.dumps({"total_attempts":len(frame),
        "fit_failures":ev["fit_failures"],"qualification":False,
        "scenario_summaries":ev["results"]},sort_keys=True))


if __name__=="__main__":
    main()
