"""B6 rank-one independent-NUTS prior-SBC / 90% interval pilot.

Four FRESH independent prior-generated datasets. Every original fit retained,
including failures/nonconvergence. Pilot is too small for inferential claims.
Only x-midpoint mean and variance are independent-dataset-level primary targets.
This does not assess fixed-parameter frequentist coverage.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import os
import time
import numpy as np
from scipy.stats import binomtest

from eyetrajectoriespy.bayesian.sparse_factor_gibbs import _spline_basis
from eyetrajectoriespy.research.calibration_seed import calibration_replicate_seed
from scripts.run_b6_population_calibration_grid import (
    _known_truth, GRID, MEAN_PRIOR_SD, N_BASIS,
)
from scripts.run_b6_b7_independent_pymc_nuts import _pymc_marginal
from scripts.run_b6_b7_four_chain_reference import (
    identified_functionals, numerical_reference_diagnostics,
)

STUDY = "B6_RANK1_INDEPENDENT_NUTS_PRIOR_SBC_STAGE0_V1"
REPLICATES = tuple(range(4))
PRIMARY = ("x_mean_midpoint", "x_variance_midpoint")
SEED = 20261227
SAMPLE = {"chains": 4, "cores": 2, "draws_per_chain": 400,
          "warmup_per_chain": 700, "target_accept": 0.94}
BIN_COUNT = 10


def fresh_seed(master_seed: int, replicate: int) -> int:
    if replicate not in REPLICATES:
        raise ValueError("outside predeclared Stage-0 replicate set")
    return calibration_replicate_seed(
        STUDY, master_seed=master_seed, shard_id=0,
        scenario="B6_matched_rank1_prior", replicate=replicate)


def rank_in_posterior(draws: np.ndarray, truth: float, seed: int) -> dict:
    """Discrete SBC rank in {0,...,N}; tie-breaking is seeded and transparent."""
    x = np.asarray(draws, dtype=float).reshape(-1)
    if not x.size or not np.isfinite(x).all() or not np.isfinite(truth):
        raise ValueError("finite posterior samples and truth required for SBC rank")
    below = int((x < truth).sum())
    equal = int((x == truth).sum())
    offset = int(np.random.default_rng(seed).integers(0, equal+1)) if equal else 0
    rank = below + offset
    return {"posterior_sample_count": int(len(x)),
            "posterior_truth_rank": rank,
            "exact_tie_count": equal,
            "uniformized_rank_fraction": float((rank + .5)/(len(x)+1)),
            "rank_histogram_bin_0_to_9": min(
                BIN_COUNT-1, BIN_COUNT*rank//(len(x)+1))}


def summarize_primary(dataset_rows: list[dict]) -> dict:
    """Dataset is the sampling unit; failures stay in denominator."""
    ids = [(x["replicate"], x["generation_seed"]) for x in dataset_rows]
    if len(set(ids)) != len(dataset_rows):
        raise ValueError("independent calibration rows must have distinct replicate and seed")
    attempts = len(dataset_rows)
    completed = [r for r in dataset_rows if r["status"] == "ok"]
    result = {
        "independent_dataset_attempts": attempts,
        "completed_fits": len(completed), "failed_fits": attempts-len(completed),
        "nonconverged_exploratory_screen": sum(
            not x["all_functional_screen_passed"] for x in completed),
        "fixed_truth_coverage_studied": False,
        "prior_generated_sbc_and_coverage_pilot_only": True,
        "posterior_calibration_qualified": False,
        "release_authorized": False,
        "primary_targets": {},
    }
    for target in PRIMARY:
        observed = [r["primary_targets"][target] for r in completed]
        successes = sum(o["marginal_90pct_interval_contains_truth"] for o in observed)
        ci = (binomtest(successes,len(observed)).proportion_ci(
            confidence_level=.95, method="exact") if observed else None)
        hist = [0]*BIN_COUNT
        for o in observed:
            hist[o["rank"]["rank_histogram_bin_0_to_9"]] += 1
        result["primary_targets"][target] = {
            "completed_dataset_count": len(observed),
            "fit_attempt_denominator": attempts,
            "truth_contained_count": successes,
            "truth_missed_count": len(observed)-successes,
            "observed_fraction_among_completed_fits": (
                successes/len(observed) if observed else None),
            "exact_95pct_binomial_interval_completed_fits_only": (
                [float(ci.low),float(ci.high)] if ci else None),
            "sbc_ranks": [o["rank"]["posterior_truth_rank"] for o in observed],
            "sbc_rank_histogram_n10": hist,
            "rank_histogram_qualified": False,
            "nominal_interval_coverage_qualified": False,
        }
    return result


def run_one(replicate: int, *, master_seed: int = SEED) -> dict:
    generation_seed=fresh_seed(master_seed,replicate)
    case={
        "study":STUDY,"replicate":replicate,"generation_seed":generation_seed,
        "status":"failed","error_type":None,"error":None,
        "sample_configuration":SAMPLE,"matched_prior_likelihood":True,
        "independent_prior_generated_dataset":True,
        "fit_wall_seconds_including_compilation":None,
        "all_functional_screen_passed":None,
        "n_identified_functionals":None,"primary_targets":{},
        "all_functional_diagnostics":{},
        "fit_exception_retained":True,
        "rank2_covered":False,
        "fixed_parameter_coverage_tested":False,
        "posterior_calibration_qualified":False,
        "release_authorized":False,
    }
    try:
        gaze, mean_truth, cov_truth, _, _ = _known_truth(
            generation_seed, "matched_rank1")
        began=time.perf_counter()
        inference=_pymc_marginal(
            gaze,dimensions=("x",),noise_sd=(.05,),q=N_BASIS,k=1,
            mean_sd=MEAN_PRIOR_SD,load_sd=.20,
            draws=SAMPLE["draws_per_chain"],warmup=SAMPLE["warmup_per_chain"],
            chains=SAMPLE["chains"],cores=SAMPLE["cores"],
            random_state=generation_seed+202)
        elapsed=time.perf_counter()-began
        m=np.asarray(inference.posterior["mean"])
        L=np.asarray(inference.posterior["load"])
        functionals=identified_functionals(
            m,L,GRID,("x",),mean_truth[:,None],cov_truth)
        checks=numerical_reference_diagnostics(inference,functionals)
        primary={}
        for j,key in enumerate(PRIMARY):
            draws,truth=functionals[key]
            summary=checks["functionals"][key]
            primary[key]={
                "rank":rank_in_posterior(draws,truth,generation_seed+4862+j),
                "single_prior_generated_truth":float(truth),
                "marginal_90pct_interval_contains_truth":summary[
                    "single_dataset_90pct_interval_contains_truth"],
                "exploratory_functional_screen_passed":summary[
                    "passes_declared_functional_screen"],
            }
        case.update(status="ok",error_type=None,error=None,
            fit_wall_seconds_including_compilation=float(elapsed),
            all_functional_screen_passed=checks[
                "all_identified_functionals_pass_exploratory_screen"],
            n_identified_functionals=len(functionals),
            primary_targets=primary,
            all_functional_diagnostics=checks)
    except Exception as exc:
        case["error_type"]=type(exc).__name__
        case["error"]=str(exc)[:800]
    return case


def write_case(case: dict, directory: Path, master_seed: int) -> None:
    directory.mkdir(parents=True,exist_ok=True)
    ledger={
        "study":STUDY,"master_seed":master_seed,
        "predeclared_replicate_ids":list(REPLICATES),
        "attempted_this_artifact":1,
        "fit_failures_this_artifact":int(case["status"]!="ok"),
        "four_chain_fits_with_reduced_pilot_draws":True,
        "original_evidence_not_selected_on_good_mixing":True,
        "rank_histogram_calibration_qualified":False,
        "prior_predictive_90pct_coverage_qualified":False,
        "fixed_parameter_coverage_tested":False,
        "publication_authorized":False,"release_authorized":False,
        "source_sha":os.environ.get("GITHUB_SHA"),
    }
    for name,payload in (("cases.json",[case]),("evidence.json",ledger)):
        (directory/name).write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
    (directory/"SHA256SUMS").write_text("".join(
        f"{sha256((directory/name).read_bytes()).hexdigest()}  {name}\n"
        for name in ("cases.json","evidence.json")))


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--replicate",type=int,choices=REPLICATES,required=True)
    ap.add_argument("--master-seed",type=int,default=SEED)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    row=run_one(a.replicate,master_seed=a.master_seed)
    write_case(row,a.out,a.master_seed)
    print("B6 PRIOR-SBC STAGE-0 CASE:",json.dumps(row,sort_keys=True))
    if row["status"]!="ok":
        raise SystemExit("original posterior fit failed; retain artifact and count")


if __name__=="__main__":
    main()
