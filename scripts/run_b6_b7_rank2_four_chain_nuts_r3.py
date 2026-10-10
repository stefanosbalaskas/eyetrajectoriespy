"""Research-only rank-two NUTS R3 computational pilot on TWO fresh datasets.

One new independently prior-generated matched-loading-prior dataset per
paired/asynchronous planar observation design. No rank-two SBC or posterior
coverage claims; identified population mean/variance/cross-covariance only.
The scientific workflow must preserve nonconvergence and fitting exceptions.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np

from eyetrajectoriespy.bayesian.sparse_factor_gibbs import _spline_basis
from eyetrajectoriespy.research.calibration_seed import calibration_replicate_seed
from scripts.run_b6_b7_rank2_likelihood_contract import (
    generate_case, population_covariance, RankTwoCase,
)
from scripts.run_b6_b7_rank2_pymc_graph_contract import build_actual_pymc_model
from scripts.run_b6_b7_four_chain_reference import numerical_reference_diagnostics

STUDY = "B6_B7_RANK2_FOUR_CHAIN_NUTS_COMPUTATIONAL_R3_V1"
DESIGNS = ("paired", "asynchronous")
SAMPLE = dict(chains=4, cores=2, tune=700, draws=400, target_accept=0.94)
PARTICIPANTS = 4


def source_seed(design: str, master_seed: int = 20261011) -> int:
    if design not in DESIGNS:
        raise ValueError("unknown declared rank-two design")
    return calibration_replicate_seed(
        STUDY, master_seed=master_seed, shard_id=0,
        scenario=design, replicate=0,
    )


def invariant_functionals(case: RankTwoCase, posterior_mean: np.ndarray,
                          posterior_loading: np.ndarray) -> dict:
    """Rank-two sign- and rotation-invariant functionals at three positions."""
    mean = np.asarray(posterior_mean, float)
    loading = np.asarray(posterior_loading, float)
    if mean.ndim != 4 or loading.ndim != 5 or mean.shape[:2] != loading.shape[:2]:
        raise ValueError("expect 4-chain posterior arrays for mean and load")
    chains, draws, dimension, basis_count = mean.shape
    if (chains != 4 or draws < 100 or dimension != 2
            or loading.shape != (chains, draws, 2, basis_count, 2)):
        raise ValueError("rank-two planar posterior shape mismatch")
    if case.mean.shape != (2, basis_count) or case.loading.shape != (2, basis_count, 2):
        raise ValueError("generating model shape mismatch")
    grid = case.evaluation_grid
    basis = _spline_basis(grid, 0., 1., basis_count)
    pmu = np.einsum("tq,csdq->csdt", basis, mean)
    pL = np.einsum("tq,csdqr->csdtr", basis, loading)
    truth_mean = basis @ case.mean.T
    truth_cov = population_covariance(case)
    n = len(grid)
    if truth_cov.shape != (2*n, 2*n):
        raise ValueError("truth covariance order mismatch")
    rows = {}
    for i, suffix in ((n//4, "quarter"), (n//2, "midpoint"),
                      (3*n//4, "three_quarters")):
        rows["x_mean_"+suffix] = (pmu[:, :, 0, i], float(truth_mean[i, 0]))
        rows["y_mean_"+suffix] = (pmu[:, :, 1, i], float(truth_mean[i, 1]))
        rows["x_variance_"+suffix] = (
            np.sum(pL[:, :, 0, i, :]**2, axis=-1), float(truth_cov[i, i]))
        rows["y_variance_"+suffix] = (
            np.sum(pL[:, :, 1, i, :]**2, axis=-1),
            float(truth_cov[n+i, n+i]))
        rows["xy_covariance_"+suffix] = (
            np.sum(pL[:, :, 0, i, :]*pL[:, :, 1, i, :], axis=-1),
            float(truth_cov[i, n+i]))
    if len(rows) != 15:
        raise ValueError("expected fifteen rotation-invariant functionals")
    return rows


def run_one(design: str, master_seed: int = 20261011,
            draws: int = 400, tune: int = 700, cores: int = 2) -> dict:
    if design not in DESIGNS or draws < 100 or tune < 100 or cores not in (1, 2):
        raise ValueError("invalid or unregistered rank-two study configuration")
    seed = source_seed(design, master_seed)
    row = {
        "study": STUDY, "design": design, "generation_seed": seed,
        "dataset_replicate": 0, "new_independent_prior_generated_dataset": True,
        "out_of_prior_near_tied_stress": False, "rank": 2,
        "n_participants": PARTICIPANTS, "status": "failed",
        "error_type": None, "error": None, "warmup_per_chain": tune,
        "draws_per_chain": draws, "n_chains": 4, "cores": cores,
        "full_fit_wall_seconds": None, "reference_checks": None,
        "identified_ess_per_full_fit_second": {},
        "mathematical_pymc_graph_reference": "PR #277, workflow #38095088126",
        "sbc_completed": False, "fixed_truth_coverage_tested": False,
        "posterior_calibration_qualified": False,
        "production_backend_selected": False, "release_authorized": False,
    }
    try:
        import pymc as pm
        case = generate_case(seed, paired=(design == "paired"),
                             near_tied=False, participants=PARTICIPANTS)
        if not case.exact_matched_prior:
            raise ValueError("production pilot must be matched prior, no near ties")
        model, _, _ = build_actual_pymc_model(case)
        start = time.perf_counter()
        with model:
            idata = pm.sample(draws=draws, tune=tune, chains=4, cores=cores,
                              random_seed=seed + 202, target_accept=0.94,
                              progressbar=False, compute_convergence_checks=True,
                              return_inferencedata=True)
        elapsed = time.perf_counter()-start
        func = invariant_functionals(
            case, np.asarray(idata.posterior["mean"]),
            np.asarray(idata.posterior["load"]))
        checks = numerical_reference_diagnostics(idata, func)
        row.update(status="ok", n_identified_functionals=len(func),
                   full_fit_wall_seconds=float(elapsed),
                   reference_checks=checks,
                   identified_ess_per_full_fit_second={
                       k: float(v["bulk_ess"]/elapsed)
                       for k, v in checks["functionals"].items()})
    except Exception as exc:
        row["error_type"] = type(exc).__name__
        row["error"] = str(exc)[:1000]
    return row


def write_case(row: dict, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    ledger = {
        "study": STUDY, "attempts": 1, "independent_datasets": 1,
        "fit_exceptions": int(row["status"] != "ok"),
        "screen_failure": (int(not row["reference_checks"]["all_identified_functionals_pass_exploratory_screen"])
                           if row["status"] == "ok" else None),
        "prior_generated_rank_two": True,
        "original_source_sha": os.environ.get("GITHUB_SHA"),
        "sample_settings": {"chains": row.get("n_chains"), "cores": row.get("cores"),
                            "tune": row.get("warmup_per_chain"),
                            "draws": row.get("draws_per_chain"),
                            "target_accept": SAMPLE["target_accept"]},
        "computed_15_rotation_invariant_functionals": row["status"] == "ok",
        "convergence_screen_is_exploratory_not_scientific_qualification": True,
        "rank2_posterior_qualified": False, "SBC_completed": False,
        "nominal_coverage_qualified": False, "release_authorized": False,
    }
    for name, obj in (("case.json", row), ("evidence.json", ledger)):
        (out/name).write_text(json.dumps(obj, indent=2, sort_keys=True)+"\n")
    (out/"SHA256SUMS").write_text("".join(
        sha256((out/name).read_bytes()).hexdigest()+"  "+name+"\n"
        for name in ("case.json", "evidence.json")))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--design", choices=DESIGNS, required=True)
    ap.add_argument("--master-seed", type=int, default=20261011)
    ap.add_argument("--draws", type=int, default=400)
    ap.add_argument("--tune", type=int, default=700)
    ap.add_argument("--cores", type=int, default=2)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    row = run_one(design=args.design, master_seed=args.master_seed,
                  draws=args.draws, tune=args.tune, cores=args.cores)
    write_case(row, args.out)
    print("RANK2 FOUR-CHAIN NUTS ACTUAL STUDY:",
          json.dumps({"status": row["status"], "design": row["design"],
                      "n_identified_functionals": row.get("n_identified_functionals"),
                      "all_screen_pass": row["reference_checks"]["all_identified_functionals_pass_exploratory_screen"]
                      if row["status"] == "ok" else None,
                      "full_fit_wall_seconds": row["full_fit_wall_seconds"],
                      "error_type": row["error_type"],
                      "release_authorized": False}, sort_keys=True))
    # Convergence-screen failures are *science*, not CI failures. Errors are
    # separately visible via status, and source JSON is always retained.
    if row["status"] != "ok":
        raise SystemExit("posterior fit failed, source evidence retained")


if __name__ == "__main__":
    main()
