"""Paired B6/B7 exact partially-collapsed mean Gibbs mixing diagnosis.

Distinct, independently seeded known-prior datasets per scenario; original
Gibbs and collapsed-population-mean Gibbs on identical observations.
No approximate Gaussian posterior, no transformed independent sample claim.
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
from eyetrajectoriespy.research.calibration_seed import calibration_replicate_seed
from scripts.run_bayes_scale_interweave_probe import DESIGNS
from scripts.run_b6_population_calibration_grid import run_one as b6_run
from scripts.run_b7_learned_planar_truth_pilot import _replicate as b7_run


def execute(replicates:int=6,draws:int=200,warmup:int=400,
            master_seed:int=20261126):
    if replicates<2 or draws<20 or warmup<20:
        raise ValueError("at least two refits and 20 posterior/warmup draws")
    cases=[]
    for method,scenario,design in DESIGNS:
        for rep in range(replicates):
            seed=calibration_replicate_seed(
                method+"_COLLAPSED_MEAN_20261126",
                master_seed=master_seed,shard_id=0,
                scenario=scenario,replicate=rep)
            for label,collapsed in (("original",False),("collapsed_mean",True)):
                row={"method":method,"scenario":scenario,
                     "replicate":rep,"seed":seed,"variant":label,
                     "collapsed_mean":collapsed,"status":"failed",
                     "exception_type":None,"exception":None}
                try:
                    if method=="B6":
                        result=b6_run(seed,design["scenario"],draws=draws,
                           warmup=warmup,diagnostics=True,
                           collapsed_population_mean_update=collapsed)
                    else:
                        result=b7_run(seed,design["rank"],
                           design["asynchronous"],draws,warmup,
                           diagnostics=True,
                           collapsed_population_mean_update=collapsed)
                    row.update(result)
                    row["status"]="ok"
                except Exception as e:
                    row["exception_type"]=type(e).__name__
                    row["exception"]=str(e)[:500]
                cases.append(row)
    frame=pd.DataFrame(cases)
    summary=[]
    for (method,scenario,variant),group in frame.groupby(
        ["method","scenario","variant"],sort=True):
        ok=group[group.status=="ok"]
        record={"method":method,"scenario":scenario,"variant":variant,
            "attempted":len(group),"successful":len(ok),
            "failed":len(group)-len(ok),
            "posterior_mixing_qualified":False,
            "posterior_coverage_qualified":False}
        for key in ("convergence_rhat_max","convergence_ess_bulk_min",
                    "population_mean_mid_90_included",
                    "population_covariance_mid_90_included",
                    "x_mean_mid_90_covered","y_mean_mid_90_covered",
                    "xy_crosscov_mid_90_covered"):
            if key in ok and ok[key].notna().any():
                x=ok[key].dropna().astype(float)
                record[key]={
                    "median":float(x.median()),
                    "mean":float(x.mean()),
                    "n":len(x)}
        summary.append(record)
    ev={"programme":"B6_B7_exact_partially_collapsed_population_mean_pilot",
        "actual_Gibbs_fit_with_real_sparse_observations":True,
        "participant_latent_scores_analytically_integrated_from_mean_conditional":True,
        "joint_planar_xy_score_induced_cross_blocks_preserved":True,
        "identical_prior_generated_data_between_variants":True,
        "master_seed":master_seed,
        "replicates_per_design":replicates,
        "attempts":len(frame),
        "failed_attempts":int(frame.status.eq("failed").sum()),
        "warmup":warmup,"posterior_draws_per_chain":draws,
        "sampler_detailed_balance_independently_verified_only_conditionally":True,
        "full_joint_posterior_target_reference_NUTS_qualified":False,
        "rank_SBC_qualified":False,
        "posterior_mixing_qualified":False,
        "scientific_inference_qualified":False,
        "release_authorized":False,"results":summary}
    return frame,ev


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--replicates",type=int,default=6)
    ap.add_argument("--draws",type=int,default=200)
    ap.add_argument("--warmup",type=int,default=400)
    ap.add_argument("--master-seed",type=int,default=20261126)
    ap.add_argument("--out",required=True,type=Path)
    a=ap.parse_args()
    cases,ev=execute(a.replicates,a.draws,a.warmup,a.master_seed)
    a.out.mkdir(parents=True,exist_ok=True)
    p=a.out/"cases.csv";e=a.out/"evidence.json"
    cases.to_csv(p,index=False)
    e.write_text(json.dumps(ev,sort_keys=True,indent=2)+"\n")
    (a.out/"sha256.txt").write_text(
        sha256(p.read_bytes()).hexdigest()+"  cases.csv\n"+
        sha256(e.read_bytes()).hexdigest()+"  evidence.json\n")
    print(json.dumps({"attempts":len(cases),
        "fit_failures":ev["failed_attempts"],
        "results":ev["results"],"scientific_inference_qualified":False},
        sort_keys=True))


if __name__=="__main__":
    main()
