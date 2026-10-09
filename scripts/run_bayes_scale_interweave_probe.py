"""Independent matched-dataset B6/B7 reversible scale-interweaving pilot.

Same exact prior truth, observation rows and RNG seeds across a baseline
Gibbs and an optional likelihood-invariant Metropolis scale move. The two
ensembles may have different random-number-consumption patterns; identical
data, not bit-identical stochastic posterior draws. No inference promotion.
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
from scripts.run_b6_population_calibration_grid import run_one as b6_run
from scripts.run_b7_learned_planar_truth_pilot import _replicate as b7_run

DESIGNS=(
    ("B6","rank1",{"scenario":"matched_rank1"}),
    ("B6","rank2",{"scenario":"matched_rank2"}),
    ("B7","rank1_paired",{"rank":1,"asynchronous":False}),
    ("B7","rank1_async",{"rank":1,"asynchronous":True}),
    ("B7","rank2_paired",{"rank":2,"asynchronous":False}),
    ("B7","rank2_async",{"rank":2,"asynchronous":True}),
)


def execute(*,replicates:int=6,draws:int=200,warmup:int=400,
            master_seed:int=20261121,proposal_sd:float=.25):
    if (replicates<2 or draws<20 or warmup<20
        or not np.isfinite(proposal_sd) or not 0<proposal_sd<=1):
        raise ValueError("positive matched replicates and proposal requirements")
    rows=[]
    for method,scenario,config in DESIGNS:
        for replicate in range(replicates):
            seed=calibration_replicate_seed(
                method+"_INVARIANT_MH_SCALE",
                master_seed=master_seed,shard_id=0,scenario=scenario,
                replicate=replicate)
            for variant,scale in (("original",0.),("reversible_scale_interweave",proposal_sd)):
                row={"method":method,"scenario":scenario,
                     "replicate":replicate,"seed":seed,
                     "variant":variant,"proposal_sd":scale,
                     "status":"failed","error_type":None,"error":None}
                try:
                    if method=="B6":
                        result=b6_run(seed,config["scenario"],draws=draws,
                           warmup=warmup,diagnostics=True,
                           scale_interweave_proposal_sd=scale)
                    else:
                        result=b7_run(seed,config["rank"],
                           config["asynchronous"],draws,warmup,
                           diagnostics=True,scale_interweave_proposal_sd=scale)
                    row.update(result)
                    row["status"]="ok"
                except Exception as err:
                    row["error_type"]=type(err).__name__
                    row["error"]=str(err)[:600]
                rows.append(row)
    frame=pd.DataFrame(rows)
    summaries=[]
    for (method,scenario,variant),group in frame.groupby(
        ["method","scenario","variant"],sort=True):
        good=group[group.status=="ok"]
        row={"method":method,"scenario":scenario,"variant":variant,
             "attempted":len(group),"failed":len(group)-len(good),
             "convergence_qualified":False,"coverage_qualified":False}
        for key in ("convergence_rhat_max","convergence_ess_bulk_min",
                    "scale_interweave_acceptance_rate"):
            if key in good and good[key].notna().any():
                val=good[key].dropna().astype(float)
                row[key]={"median":float(val.median()),
                           "minimum":float(val.min()),
                           "maximum":float(val.max())}
        summaries.append(row)
    ev={
       "programme":"B6_B7_reversible_MH_interweaving_mixing_pilot",
       "same_generated_datasets_and_hyperparameters_per_pair":True,
       "original_sampler_unmodified_at_default_zero":True,
       "exact_likelihood_invariance_of_scale_orbit":True,
       "Gaussian_prior_and_change_of_variable_jacobian_included":True,
       "reversible_MH_kernel":True,
       "independent_known_prior_truth":True,
       "n_independent_dataset_replicates_per_scenario":replicates,
       "attempts":len(frame),
       "failed_attempts":int((frame.status=="failed").sum()),
       "master_seed":master_seed,
       "warmup":warmup,"draws_per_chain":draws,"chains":2,
       "scale_proposal_sd":proposal_sd,
       "reparameterized_sampler_mixing_qualified":False,
       "posterior_coverage_qualified":False,
       "rank_SBC_qualified":False,
       "full_reference_NUTS_completed":False,
       "release_authorized":False,
       "results":summaries,
    }
    return frame,ev


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--replicates",type=int,default=6)
    ap.add_argument("--draws",type=int,default=200)
    ap.add_argument("--warmup",type=int,default=400)
    ap.add_argument("--proposal-sd",type=float,default=.25)
    ap.add_argument("--master-seed",type=int,default=20261121)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    cases,ev=execute(replicates=a.replicates,draws=a.draws,
        warmup=a.warmup,master_seed=a.master_seed,proposal_sd=a.proposal_sd)
    a.out.mkdir(parents=True,exist_ok=True)
    p=a.out/"cases.csv";e=a.out/"evidence.json"
    cases.to_csv(p,index=False)
    e.write_text(json.dumps(ev,sort_keys=True,indent=2)+"\n")
    (a.out/"sha256.txt").write_text(
       sha256(p.read_bytes()).hexdigest()+"  cases.csv\n"+
       sha256(e.read_bytes()).hexdigest()+"  evidence.json\n")
    print(json.dumps({"attempts":len(cases),"failed":ev["failed_attempts"],
                      "scientifically_qualified":False,
                      "results":ev["results"]},sort_keys=True))


if __name__=="__main__":
    main()
