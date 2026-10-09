"""High-precision independent F1 native sparse-PACE null/power qualification evidence.

Exactly the same native sparse group statistical test as previous pilot,
never a cached permutation statistic or substituted Gaussian surrogate.
Each full study fit on an independently generated irregular participant-level
dataset with separate SHA256-keyed random stream.
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
from eyetrajectoriespy.research.power_planning import _generate_sparse_two_group
from eyetrajectoriespy.research.sparse_group_inference import test_sparse_functional_groups
from scripts.run_f1_f5_scientific_stress import F1_DESIGNS


def run(design:str,*,null_replicates:int=1000,
        alternative_replicates:int=500,permutations:int=199,
        master_seed:int=20261125,effect_amplitude:float=.04):
    if design not in F1_DESIGNS:
        raise ValueError("unknown prespecified F1 design")
    if (null_replicates<2 or alternative_replicates<2 or permutations<99
        or not np.isfinite(effect_amplitude) or effect_amplitude<=0):
        raise ValueError("require adequate independent replicates and permutations")
    params=F1_DESIGNS[design]
    observation_noise=.015
    settings={
        "n_components":2,
        "evaluation_grid":np.linspace(0.,1.,21),
        "mean_bandwidth":.3,
        "covariance_bandwidth":.45,
        "measurement_error":"diagonal",
        "measurement_error_variance":(observation_noise**2,)*2,
        "psd_action":"project",
        "score_failure_action":"retain_nan",
    }
    rows=[]
    for condition,num in (("null",null_replicates),
                          ("alternative",alternative_replicates)):
        effect=0. if condition=="null" else effect_amplitude
        for replicate in range(num):
            seed=calibration_replicate_seed(
                "F1_HIGH_PRECISION_NATIVE_FULL_FIT",
                master_seed=master_seed,shard_id=0,
                scenario=design+"|"+condition,replicate=replicate)
            record={
                "design":design,"condition":condition,
                "replicate":replicate,"seed":seed,
                "effect_amplitude":effect,
                "status":"failed","p_value":None,
                "test_statistic":None,"exception_type":None,
                "exception":None,
            }
            try:
                rng=np.random.default_rng(seed)
                gaze,groups,participants=_generate_sparse_two_group(
                    rng,units_per_group=params["units_per_group"],
                    other_group_size=params["other_group_size"],
                    group_noise_multiplier=params["group_noise_multiplier"],
                    trials_per_participant=params["trials_per_participant"],
                    samples_per_trial=params["samples_per_trial"],
                    noise_sd=observation_noise,effect_amplitude=effect,
                )
                fit=test_sparse_functional_groups(
                    gaze,groups,unit_ids=participants,fit_kwargs=settings,
                    n_permutations=permutations,random_state=seed)
                p=float(fit.p_value)
                if not np.isfinite(p) or not 0<=p<=1:
                    raise RuntimeError("native F1 test returned invalid p-value")
                record.update(status="ok",p_value=p,
                              test_statistic=float(fit.statistic))
            except Exception as exc:
                record["exception_type"]=type(exc).__name__
                record["exception"]=str(exc)[:500]
            rows.append(record)
    frame=pd.DataFrame(rows)
    summaries=[]
    for condition in ("null","alternative"):
        all_cases=frame[frame.condition==condition]
        successful=all_cases[all_cases.status=="ok"]
        item={"condition":condition,"attempted":len(all_cases),
              "completed":len(successful),
              "failed":len(all_cases)-len(successful),
              "rate_conditional_on_fit_not_unconditional":True,
              "treat_failure_as_nonrejection_not_validity_proof":True}
        for alpha in (.01,.05,.10):
            k=int((successful.p_value<=alpha).sum())
            n=len(successful)
            ci=binomtest(k,n).proportion_ci(.95,method="exact") if n else None
            item[f"alpha_{alpha:g}"]={
                "rejections":k,
                "conditional_n":n,
                "rejection_rate_conditional":k/n if n else None,
                "attempts_including_failures":len(all_cases),
                "rejection_fraction_all_attempts":k/len(all_cases),
                "exact_95_MC_interval":([float(ci.low),float(ci.high)]
                                      if ci is not None else None),
            }
        summaries.append(item)
    ev={
        "programme":"F1_native_sparse_PACE_predeclared_larger_operating_characteristics",
        "design":design,"master_seed":master_seed,
        "null_attempts":null_replicates,
        "alternative_attempts":alternative_replicates,
        "moderate_alternative_effect":effect_amplitude,
        "permutations_per_fitted_test":permutations,
        "independent_unit_count_group_A":params["units_per_group"],
        "independent_unit_count_group_B":params["other_group_size"],
        "trials_per_participant":params["trials_per_participant"],
        "heteroscedasticity_multiplier":params["group_noise_multiplier"],
        "observed_times_per_trial":params["samples_per_trial"],
        "native_real_full_sparse_PACE_fit_for_each_attempt":True,
        "group_label_permutation_may_violate_exchangeability":(
            params["group_noise_multiplier"]!=1.),
        "all_fit_failures_retained":True,
        "total_attempts":len(frame),
        "fit_failures":int((frame.status=="failed").sum()),
        "statistical_null_size_qualified":False,
        "statistical_power_qualified":False,
        "independent_comparator_completed":False,
        "release_authorized":False,
        "summary":summaries,
    }
    return frame,ev


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--design",required=True,choices=tuple(F1_DESIGNS))
    ap.add_argument("--null-replicates",type=int,default=1000)
    ap.add_argument("--alternative-replicates",type=int,default=500)
    ap.add_argument("--permutations",type=int,default=199)
    ap.add_argument("--effect-amplitude",type=float,default=.04)
    ap.add_argument("--master-seed",type=int,default=20261125)
    ap.add_argument("--out",required=True,type=Path)
    a=ap.parse_args()
    cases,ev=run(a.design,null_replicates=a.null_replicates,
                 alternative_replicates=a.alternative_replicates,
                 permutations=a.permutations,
                 effect_amplitude=a.effect_amplitude,
                 master_seed=a.master_seed)
    a.out.mkdir(parents=True,exist_ok=True)
    p=a.out/"cases.csv";e=a.out/"evidence.json"
    cases.to_csv(p,index=False)
    e.write_text(json.dumps(ev,indent=2,sort_keys=True)+"\n")
    (a.out/"sha256.txt").write_text(
        sha256(p.read_bytes()).hexdigest()+"  cases.csv\n"+
        sha256(e.read_bytes()).hexdigest()+"  evidence.json\n")
    print(json.dumps({"design":a.design,"attempted":len(cases),
        "failed":ev["fit_failures"],"statistically_qualified":False,
        "summary":ev["summary"]},sort_keys=True))


if __name__=="__main__":
    main()
