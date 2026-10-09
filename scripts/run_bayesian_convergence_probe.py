"""Actual paired long/short Bayesian MCMC diagnostic study after 400-refit undercoverage.

Uses the EXACT existing B6/B7 matched prior/likelihood generators, same seed
and independent participants for both chain schedules, no fabricated numbers.
Optional ArviZ diagnostics concern identifiable integrated means/variances and
planar cross covariance. All sampler exceptions and NA diagnostics retained.
This is a diagnostic experiment, NOT sufficient rank SBC or qualification.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

# Direct `python scripts/runner.py` execution must resolve sibling research
# scripts without relying on editable install path side effects.
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

from eyetrajectoriespy.research.calibration_seed import calibration_replicate_seed
from scripts.run_b6_population_calibration_grid import run_one as b6_run
from scripts.run_b7_learned_planar_truth_pilot import _replicate as b7_run

CASES = {
    "B6": [
        ("matched_rank1", {"scenario":"matched_rank1"}),
        ("matched_rank2", {"scenario":"matched_rank2"}),
    ],
    "B7": [
        ("rank1_paired", {"rank":1,"asynchronous":False}),
        ("rank1_async", {"rank":1,"asynchronous":True}),
        ("rank2_paired", {"rank":2,"asynchronous":False}),
        ("rank2_async", {"rank":2,"asynchronous":True}),
    ],
}
COVERAGE = {
    "B6":("population_mean_mid_90_included",
           "population_covariance_mid_90_included"),
    "B7":("x_mean_mid_90_covered","y_mean_mid_90_covered",
           "xy_crosscov_mid_90_covered"),
}


def attempt(method: str, scenario: str, config: dict, seed: int,
            *, draws: int, warmup: int) -> dict:
    if method=="B6":
        return b6_run(seed,config["scenario"],draws=draws,warmup=warmup,
                      diagnostics=True)
    return b7_run(seed,config["rank"],config["asynchronous"],
                  draws=draws,warmup=warmup,diagnostics=True)


def summarize(cases: pd.DataFrame) -> list[dict]:
    out=[]
    for (method,scenario,schedule),group in cases.groupby(
        ["method","scenario","schedule"],sort=True):
        good=group[group.status=="ok"]
        row={
            "method":method,"scenario":scenario,"schedule":schedule,
            "attempted":len(group),"completed":len(good),
            "failed":len(group)-len(good),
            "sample_count_is_independent_dataset_replicates":True,
            "chain_mixing_qualified":False,
            "posterior_coverage_qualified":False,
        }
        for col in COVERAGE[method]:
            if col in good.columns and len(good):
                row[col]={"count":int(good[col].sum()),
                          "denominator":len(good),
                          "fraction":float(good[col].mean())}
        for col in ("convergence_rhat_max","convergence_ess_bulk_min",
                    "population_mean_mid_q90_width",
                    "population_covariance_mid_q90_width",
                    "x_mean_mid_q90_width",
                    "y_mean_mid_q90_width",
                    "xy_crosscov_mid_q90_width"):
            if col in good.columns and good[col].notna().any():
                values=good[col].dropna().astype(float)
                row[col]={"median":float(values.median()),
                          "maximum":float(values.max()),
                          "minimum":float(values.min()),
                          "nonfinite":int((~np.isfinite(values)).sum())}
        out.append(row)
    return out


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--replicates",type=int,default=8)
    ap.add_argument("--short-draws",type=int,default=70)
    ap.add_argument("--short-warmup",type=int,default=160)
    ap.add_argument("--long-draws",type=int,default=500)
    ap.add_argument("--long-warmup",type=int,default=1200)
    ap.add_argument("--master-seed",type=int,default=20261010)
    ap.add_argument("--out",required=True,type=Path)
    args=ap.parse_args()
    if (args.replicates<2 or min(args.short_draws,args.short_warmup,
        args.long_draws,args.long_warmup)<20 or
        args.long_draws<=args.short_draws or
        args.long_warmup<=args.short_warmup):
        raise ValueError("valid 2+ replicates and strictly longer warmup/draw schedule required")
    rows=[]
    for method,scenarios in CASES.items():
        for scenario,config in scenarios:
            for rep in range(args.replicates):
                seed=calibration_replicate_seed(method+"_CHAIN_PROBE",
                      master_seed=args.master_seed,shard_id=0,
                      scenario=scenario,replicate=rep)
                for schedule,draws,warmup in (
                    ("short",args.short_draws,args.short_warmup),
                    ("long",args.long_draws,args.long_warmup),
                ):
                    row={"method":method,"scenario":scenario,
                         "replicate":rep,"seed":seed,
                         "schedule":schedule,"draws_per_chain":draws,
                         "warmup_sweeps":warmup,"status":"failed",
                         "error_type":None,"error":None}
                    try:
                        row.update(attempt(method,scenario,config,seed,
                                         draws=draws,warmup=warmup))
                        row["status"]="ok"
                    except Exception as exc:
                        row["error_type"]=type(exc).__name__
                        row["error"]=str(exc)[:600]
                    rows.append(row)
    frame=pd.DataFrame(rows)
    # A failed/NA diagnostic is never recoded as a successful convergence check.
    summaries=summarize(frame)
    evidence={
        "programme":"B6_B7_paired_short_long_chain_mixing_diagnosis",
        "actual_native_Gibbs_fits":True,
        "same_prior_likelihood_datasets_across_chain_lengths":True,
        "paired_random_seeds":True,
        "source_B6_B7_400_refit_undercovers_nominal_90":True,
        "source_run_id":37965949039,
        "short_settings":{"draws_per_chain":args.short_draws,
                          "warmup":args.short_warmup,"chains":2},
        "long_settings":{"draws_per_chain":args.long_draws,
                         "warmup":args.long_warmup,"chains":2},
        "replicates_per_scenario":args.replicates,
        "attempts":len(frame),
        "failed_attempts":int((frame.status=="failed").sum()),
        "diagnostics_integrated_rotation_invariant_quantities_only":True,
        "long_chain_diagnostic_not_full_SBC":True,
        "rank_based_SBC_completed":False,
        "posterior_coverage_qualified":False,
        "scientific_inference_qualified":False,
        "release_authorized":False,
        "results":summaries,
    }
    args.out.mkdir(parents=True,exist_ok=True)
    f=args.out/"cases.csv"
    e=args.out/"evidence.json"
    frame.to_csv(f,index=False)
    e.write_text(json.dumps(evidence,sort_keys=True,indent=2)+"\n")
    (args.out/"sha256.txt").write_text(
        sha256(f.read_bytes()).hexdigest()+"  cases.csv\n"+
        sha256(e.read_bytes()).hexdigest()+"  evidence.json\n")
    print(json.dumps(evidence,sort_keys=True))


if __name__=="__main__":
    main()
