"""F5 independent-baseline duration × nuisance-uncertainty ablation.

A priori research-only comparison: independent stationary baselines at
40, 80, 160 observations; AR1 phi=0, .35, .8 and deliberately
misspecified AR2; null and fixed .12 break. Every tested sequence
and its paired baseline are independent, and test data are held
identical across baseline sizes and the two null coefficient policies.

No estimated threshold correction, inference qualification, or promotion.
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
from eyetrajectoriespy.research.functional_changepoints_baseline_ar1 import (
    infer_ordered_functional_changepoint_baseline_ar1 as infer_unknown_phi,
)
from scripts.run_f5_unknown_phi_independent_baseline_validation import _series, SCENARIOS

PROCESSES=("iid","ar1_weak","ar1_strong","ar2_misspecified")
BASELINE_LENGTHS=(40,80,160)
COEFFICIENT_POLICIES=("baseline_uncertainty","baseline_plugin")
TRUTHS=("null","one_break")
ALPHA=(.01,.05,.10)


def _seed(master_seed:int,scenario:str,truth:str,replicate:int,kind:str)->int:
    return calibration_replicate_seed(
        "F5_BASELINE_LENGTH_NUISANCE_ABLATION_INDEPENDENT_V1",
        master_seed=master_seed,shard_id=0,
        scenario=f"{scenario}_{truth}_{kind}",replicate=replicate)


def study(
    *,null_replicates:int=100,alternative_replicates:int=50,
    bootstrap:int=119,phi_bootstrap:int=99,
    master_seed:int=20261205,
    scenario_subset:tuple[str,...]=PROCESSES
)->tuple[pd.DataFrame,dict]:
    if not isinstance(null_replicates,int) or not isinstance(alternative_replicates,int):
        raise ValueError("replication counts must be integers")
    if min(null_replicates,alternative_replicates)<2:
        raise ValueError("at least two independent null and alternative replicates")
    if min(bootstrap,phi_bootstrap)<99:
        raise ValueError("at least 99 null draws and nuisance refits")
    if not set(scenario_subset).issubset(PROCESSES) or len(set(scenario_subset))!=len(scenario_subset):
        raise ValueError("scenario subset must contain unique predeclared generators")
    rows=[]
    for scenario in scenario_subset:
        for truth,iterations in (("null",null_replicates),
                                 ("one_break",alternative_replicates)):
            for rep in range(iterations):
                test_seed=_seed(master_seed,scenario,truth,rep,"test")
                tested=_series(test_seed,scenario,n=36,truth=truth,
                               prefix=f"test-{test_seed}")
                for n_baseline in BASELINE_LENGTHS:
                    # Baselines are different from tests and each other;
                    # tests are *identical* across all six method comparisons.
                    baseline_seed=_seed(
                        master_seed,scenario,truth,rep,
                        f"independent_baseline_length_{n_baseline}")
                    baseline=_series(
                        baseline_seed,scenario,n=n_baseline,truth="null",
                        prefix=f"baseline-{baseline_seed}")
                    for policy in COEFFICIENT_POLICIES:
                        row={
                            "scenario":scenario,"truth":truth,
                            "replicate":rep,"test_seed":test_seed,
                            "baseline_seed":baseline_seed,
                            "n_baseline":n_baseline,"n_test":36,
                            "policy":policy,
                            "status":"failed","p_value":None,
                            "fitted_baseline_phi":None,
                            "phi_uncertainty_width":None,
                            "error_type":None,"error":None,
                            "calibrated_inference":False,
                        }
                        try:
                            result=infer_unknown_phi(
                                tested,independent_stationary_baseline=baseline,
                                n_parameter_bootstrap=phi_bootstrap,
                                n_null_simulations=bootstrap,min_segment=6,
                                null_coefficient_policy=policy,
                                random_state=test_seed+105+baseline_seed%100000)
                            q=result.evidence["approximate_phi_uncertainty_quantiles_025_50_975"]
                            row.update(
                                status="ok",
                                p_value=result.p_value_experimental,
                                fitted_baseline_phi=result.evidence["baseline_pooled_phi_ols"],
                                phi_uncertainty_width=q[2]-q[0])
                        except Exception as err:
                            row["error_type"]=type(err).__name__
                            row["error"]=str(err)[:500]
                        rows.append(row)
    frame=pd.DataFrame(rows)
    summary=[]
    for (scenario,truth,n_baseline,policy),grp in frame.groupby(
        ["scenario","truth","n_baseline","policy"],sort=True):
        ok=grp.loc[grp.status=="ok"]
        result={
            "scenario":scenario,"truth":truth,
            "n_baseline":int(n_baseline),"n_test":36,
            "policy":policy,"attempts":len(grp),
            "failed_attempts":len(grp)-len(ok),
            "calibration_qualified":False,
            "alpha":{},
        }
        for alpha in ALPHA:
            k=int((ok.p_value<=alpha).sum())
            n=len(ok)
            ci=binomtest(k,n).proportion_ci(.95,method="exact") if n else None
            result["alpha"][str(alpha)]={
                "rejected":k,"successful_fits":n,"attempts":len(grp),
                "failure_inclusive_rejection":k/len(grp),
                "conditional_rejection":k/n if n else None,
                "exact_95_mc_interval":(
                    [float(ci.low),float(ci.high)] if ci else None),
            }
        if len(ok):
            result["baseline_phi_mean"]=float(ok.fitted_baseline_phi.mean())
            result["baseline_phi_approx_95_width_mean"]=float(
                ok.phi_uncertainty_width.mean())
        summary.append(result)
    evidence={
        "programme":"F5_baseline_duration_by_nuisance_uncertainty_ablation",
        "seed_namespace":"F5_BASELINE_LENGTH_NUISANCE_ABLATION_INDEPENDENT_V1",
        "master_seed":master_seed,
        "independent_baseline_sizes":list(BASELINE_LENGTHS),
        "test_size":36,
        "processes":list(scenario_subset),
        "truths":list(TRUTHS),
        "null_replicates_per_process":null_replicates,
        "alternative_replicates_per_process":alternative_replicates,
        "policies":list(COEFFICIENT_POLICIES),
        "method_attempts":len(frame),
        "independent_test_datasets":len(scenario_subset)*(
            null_replicates+alternative_replicates),
        "fit_errors":int(frame.status.eq("failed").sum()),
        "all_fits_including_failures_represented":True,
        "no_threshold_tuning":True,
        "same_test_curves_across_baseline_lengths":True,
        "same_baseline_between_policies":True,
        "same_null_bootstrap_random_stream_between_policies":True,
        "independent_baseline_and_test_by_simulator_seed":True,
        "AR2_diagnostic_is_deliberate_model_misspecification":True,
        "comparison_is_not_validated_inferential_method":True,
        "nuisance_model_and_baseline_transferability_qualified":False,
        "power_or_calibration_qualified":False,
        "production_release_authorized":False,
        "scenario_results":summary,
    }
    return frame,evidence


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--null-replicates",type=int,default=100)
    parser.add_argument("--alternative-replicates",type=int,default=50)
    parser.add_argument("--bootstrap",type=int,default=119)
    parser.add_argument("--phi-bootstrap",type=int,default=99)
    parser.add_argument("--master-seed",type=int,default=20261205)
    parser.add_argument("--scenario",action="append",
        choices=PROCESSES,default=None)
    parser.add_argument("--out",type=Path,required=True)
    a=parser.parse_args()
    frame,evidence=study(
        null_replicates=a.null_replicates,
        alternative_replicates=a.alternative_replicates,
        bootstrap=a.bootstrap,phi_bootstrap=a.phi_bootstrap,
        master_seed=a.master_seed,
        scenario_subset=tuple(a.scenario) if a.scenario else PROCESSES)
    a.out.mkdir(parents=True,exist_ok=True)
    f=a.out/"cases.csv"
    e=a.out/"evidence.json"
    frame.to_csv(f,index=False)
    e.write_text(json.dumps(evidence,sort_keys=True,indent=2)+"\n")
    (a.out/"SHA256SUMS").write_text(
        f"{sha256(f.read_bytes()).hexdigest()}  cases.csv\n"
        f"{sha256(e.read_bytes()).hexdigest()}  evidence.json\n")
    print(json.dumps({
        "attempted":len(frame),"failures":evidence["fit_errors"],
        "scientific_qualification":False,
        "summary":evidence["scenario_results"]},sort_keys=True))


if __name__=="__main__":
    main()
