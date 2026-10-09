"""B6 research-only population calibration grid (never a release gate).

Matched scenarios generate population parameters from the *fitted* Gaussian
factor prior and observations from its likelihood. Near-tie and misspecified
scenarios are stress tests, NOT simulation-based calibration (SBC).
Each attempt refits the actual native Gibbs sampler and retains failures.
All posterior summaries are rotation-invariant; no eigenfunction label claim.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import ndtr
from scipy.stats import binomtest

from eyetrajectoriespy.bayesian import fit_bayesian_sparse_fpca
from eyetrajectoriespy.bayesian.sparse_factor_gibbs import _spline_basis
from eyetrajectoriespy.types import IrregularTrajectorySet
from eyetrajectoriespy.research.calibration_seed import (calibration_replicate_seed, calibration_manifest)


SCENARIOS = {
    "matched_rank1": dict(rank=1, mode="prior", n=18, sparse=False,
                          fitted_noise=.05, generated_noise=.05,
                          fitted_loading_prior=.20, generating_loading_prior=.20),
    "matched_rank2": dict(rank=2, mode="prior", n=22, sparse=False,
                          fitted_noise=.05, generated_noise=.05,
                          fitted_loading_prior=.20, generating_loading_prior=.20),
    "unequal_sparse_rank2": dict(rank=2, mode="prior", n=22, sparse=True,
                                fitted_noise=.05, generated_noise=.05,
                                fitted_loading_prior=.20, generating_loading_prior=.20),
    "nearly_tied_rank2": dict(rank=2, mode="near_tie", n=24, sparse=False,
                             fitted_noise=.05, generated_noise=.05,
                             fitted_loading_prior=.20, generating_loading_prior=None),
    "noise_misspecified_rank2": dict(rank=2, mode="prior", n=22, sparse=False,
                                    fitted_noise=.05, generated_noise=.10,
                                    fitted_loading_prior=.20, generating_loading_prior=.20),
    "prior_misspecified_rank2": dict(rank=2, mode="prior", n=22, sparse=False,
                                    fitted_noise=.05, generated_noise=.05,
                                    fitted_loading_prior=.20, generating_loading_prior=.40),
}
MEAN_PRIOR_SD = .45
GRID = np.linspace(0, 1, 27)
N_BASIS = 5


def _known_truth(seed: int, scenario: str):
    """Return exact prior/likelihood truth and an untouched heldout participant."""
    if scenario not in SCENARIOS:
        raise ValueError(f"unknown scenario: {scenario}")
    spec = SCENARIOS[scenario]
    rng = np.random.default_rng(seed)
    basis = _spline_basis(GRID, GRID[0], GRID[-1], N_BASIS)
    coefficients = rng.normal(0, MEAN_PRIOR_SD, N_BASIS)
    if spec["mode"] == "prior":
        loading = rng.normal(0, spec["generating_loading_prior"],
                             (N_BASIS, spec["rank"]))
    else:
        raw = rng.normal(size=(N_BASIS, 2))
        aligned, _ = np.linalg.qr(basis @ raw, mode="reduced")
        # Precisely equal population eigenvalues on the declared grid.
        loading = np.linalg.lstsq(basis, .5 * aligned, rcond=None)[0]
    projected = basis @ loading
    times, values = [], []
    for i in range(spec["n"]):
        n_obs = int(rng.integers(6, 21)) if spec["sparse"] else 14 + i % 4
        ti = np.sort(rng.uniform(.02, .98, n_obs))
        latent = rng.normal(size=spec["rank"])
        yi = _spline_basis(ti, 0, 1, N_BASIS) @ (coefficients + loading @ latent)
        yi += rng.normal(0, spec["generated_noise"], size=len(ti))
        times.append(ti)
        values.append(yi[:, None])
    gaze = IrregularTrajectorySet(
        time=tuple(times), values=tuple(values),
        curve_ids=tuple(f"p{i}" for i in range(spec["n"])),
        dimension_names=("x",), coordinate_system="normalized",
        time_unit="normalized",
        metadata=pd.DataFrame({"participant_id": [f"p{i}" for i in range(spec["n"])]}),
        provenance={"synthetic": True, "scientific_calibration_scenario": scenario},
    )
    # A NEW participant is never included in the Gibbs fit.
    heldout_indices = np.sort(rng.choice(np.arange(2, len(GRID)-2), size=5, replace=False))
    z_test = rng.normal(size=spec["rank"])
    heldout = (basis[heldout_indices] @ (coefficients + loading @ z_test)
               + rng.normal(0, spec["generated_noise"], len(heldout_indices)))
    return gaze, basis @ coefficients, projected @ projected.T, heldout_indices, heldout


def _mixture_quantile(mean_draws: np.ndarray, sd_draws: np.ndarray, p: float) -> float:
    """Deterministic quantile of a posterior mixture of marginal Gaussians."""
    if not 0 < p < 1:
        raise ValueError("probability must be interior")
    means = np.asarray(mean_draws, dtype=float).reshape(-1)
    sd = np.asarray(sd_draws, dtype=float).reshape(-1)
    if means.shape != sd.shape or not np.isfinite(means).all() or not np.all(sd > 0):
        raise ValueError("invalid normal mixture")
    low, high = float(np.min(means-10*sd)), float(np.max(means+10*sd))
    for _ in range(55):
        mid = (low+high)/2
        if float(np.mean(ndtr((mid-means)/sd))) < p:
            low = mid
        else:
            high = mid
    return (low+high)/2


def _projector(cov: np.ndarray, rank: int) -> np.ndarray:
    eigvals, eigvecs = np.linalg.eigh(cov)
    top = eigvecs[:, -rank:]
    return top @ top.T


def run_one(seed: int, scenario: str, *, draws: int, warmup: int, diagnostics: bool=False, scale_interweave_proposal_sd: float=0.0) -> dict:
    gaze, truth_mean, truth_cov, indices, holdout = _known_truth(seed, scenario)
    spec = SCENARIOS[scenario]
    fit = fit_bayesian_sparse_fpca(
        gaze, dimension="x", evaluation_grid=GRID, n_components=spec["rank"],
        n_basis=N_BASIS, noise_sd=spec["fitted_noise"],
        mean_prior_sd=MEAN_PRIOR_SD,
        loading_prior_sd=spec["fitted_loading_prior"],
        scale_interweave_proposal_sd=scale_interweave_proposal_sd,
        n_chains=2, n_draws=draws, warmup=warmup, thin=1,
        random_state=seed+937,
    )
    mid = len(GRID)//2
    mu = fit.population_mean_draws[:, :, mid].reshape(-1)
    cv = fit.population_covariance_draws[:, :, mid, mid].reshape(-1)
    truth_projector = _projector(truth_cov, spec["rank"])
    posterior_projectors = [
        _projector(c, spec["rank"]) for c in
        fit.population_covariance_draws.reshape(-1, len(GRID), len(GRID))
    ]
    subspace_error = float(np.mean([
        np.linalg.norm(p-truth_projector, ord="fro") /
        np.sqrt(2*spec["rank"]) for p in posterior_projectors
    ]))
    covered = []
    for index, measured in zip(indices, holdout, strict=True):
        m = fit.population_mean_draws[:, :, index].reshape(-1)
        v = fit.population_covariance_draws[:, :, index, index].reshape(-1)
        # Whole-participant predictive marginal includes latent population
        # variation AND observation noise; do not use reconstructed train scores.
        sd = np.sqrt(np.maximum(v, 0) + spec["fitted_noise"]**2)
        q05, q95 = _mixture_quantile(m, sd, .05), _mixture_quantile(m, sd, .95)
        covered.append(q05 <= measured <= q95)
    qmu = np.quantile(mu, [.05, .95])
    qcov = np.quantile(cv, [.05, .95])
    # Optional independent-chain ArviZ diagnostics on rotation-invariant
    # population summaries. Explicit opt-in avoids extra dependencies
    # and changing older, archived pilot outputs.
    diag = fit.diagnostics_frame() if diagnostics else None
    max_rhat = float(diag.rhat_max.max()) if diag is not None else None
    min_bulk = float(diag.ess_bulk_min.min()) if diag is not None else None
    return {
        "scale_interweave_acceptance_rate":fit.evidence["scale_interweave_acceptance_rate"],
        "convergence_rhat_max":max_rhat,
        "convergence_ess_bulk_min":min_bulk,
        "population_mean_mid_q90_width":float(qmu[1]-qmu[0]),
        "population_covariance_mid_q90_width":float(qcov[1]-qcov[0]),
        "population_mean_mid_90_included": bool(qmu[0] <= truth_mean[mid] <= qmu[1]),
        "population_covariance_mid_90_included": bool(
            qcov[0] <= truth_cov[mid, mid] <= qcov[1]),
        "population_mean_mid_abs_error": float(abs(mu.mean()-truth_mean[mid])),
        "population_covariance_mid_abs_error": float(abs(cv.mean()-truth_cov[mid, mid])),
        "rotation_invariant_subspace_projector_error": subspace_error,
        "holdout_marginal_90_included": int(sum(covered)),
        "holdout_marginal_n": len(covered),
        "n_independent_train_units": gaze.n_curves,
        "minimum_observations_per_curve": min(len(t) for t in gaze.time),
        "n_components": spec["rank"], "n_chains": fit.n_chains,
        "posterior_draws_per_chain": fit.n_draws_per_chain,
    }


def _binomial(records: pd.DataFrame, key: str) -> dict:
    if records.empty:
        return {"n": 0, "successes": 0, "rate": None, "exact_95_mc_interval": None}
    if key == "holdout_marginal_90_included":
        n = int(records["holdout_marginal_n"].sum())
        k = int(records[key].sum())
        # Marginal outcomes within each held-out trajectory are dependent:
        # this exact binomial interval is NOT justified for that pooled tally.
        return {"n": n, "successes": k, "rate": k/n,
                "exact_95_mc_interval": None,
                "dependence_warning": "same_participant_holdout_points_correlated"}
    n = len(records)
    k = int(records[key].sum())
    ci = binomtest(k, n).proportion_ci(.95, method="exact")
    return {"n": n, "successes": k, "rate": k/n,
            "exact_95_mc_interval": [float(ci.low), float(ci.high)]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replicates", type=int, default=8)
    parser.add_argument("--master-seed",type=int,default=249103)
    parser.add_argument("--shard-id",type=int,default=0)
    parser.add_argument("--draws", type=int, default=60)
    parser.add_argument("--warmup", type=int, default=120)
    parser.add_argument("--scenarios", nargs="+", choices=tuple(SCENARIOS),
                        default=list(SCENARIOS))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.replicates < 2 or args.draws < 20 or args.warmup < 20:
        raise ValueError("at least two replications and 20 posterior/warmup draws")
    rows = []
    for scenario in args.scenarios:
        for rep in range(args.replicates):
            seed = calibration_replicate_seed("B6",master_seed=args.master_seed,
                shard_id=args.shard_id,scenario=scenario,replicate=rep)
            record = dict(scenario=scenario, replicate=rep, seed=seed,
                          shard_id=args.shard_id,
                          status="failed", exception_type=None, exception=None)
            try:
                record.update(run_one(seed, scenario, draws=args.draws, warmup=args.warmup))
                record["status"] = "ok"
            except Exception as error:
                record["exception_type"] = type(error).__name__
                record["exception"] = str(error)[:500]
            rows.append(record)
    frame = pd.DataFrame(rows)
    summaries = []
    for scenario in args.scenarios:
        trials = frame.loc[frame.scenario == scenario]
        good = trials.loc[trials.status == "ok"]
        summaries.append({
            "scenario": scenario,
            "matched_prior_likelihood": (
                SCENARIOS[scenario]["mode"] == "prior" and
                SCENARIOS[scenario]["fitted_noise"] == SCENARIOS[scenario]["generated_noise"] and
                SCENARIOS[scenario]["fitted_loading_prior"] ==
                SCENARIOS[scenario]["generating_loading_prior"]),
            "attempted": len(trials), "successful": len(good),
            "failed": int((trials.status == "failed").sum()),
            "population_mean_90": _binomial(good, "population_mean_mid_90_included"),
            "population_covariance_90": _binomial(good, "population_covariance_mid_90_included"),
            "new_participant_marginal_90": _binomial(good, "holdout_marginal_90_included"),
            "subspace_projector_error_average": (
                float(good.rotation_invariant_subspace_projector_error.mean())
                if len(good) else None),
        })
    evidence = {
        "schema_version": 1, "programme": "B6_learned_population_calibration_grid",
        "master_seed":args.master_seed,"shard_id":args.shard_id,
        "not_rank_based_SBC": True,
        "matched_scenarios_generate_exact_declared_prior_and_likelihood": True,
        "near_tie_and_misspecified_scenarios_are_STRESS_NOT_SBC": True,
        "future_participant_never_in_training": True,
        "predictive_coverage_is_marginal_pointwise_not_joint_functional": True,
        "failures_are_retained": True,
        "n_attempts": len(frame), "n_failed": int((frame.status=="failed").sum()),
        "draws_per_chain": args.draws, "warmup": args.warmup,
        "scientifically_qualified": False,
        "rank_and_mixing_diagnostics_qualified": False,
        "release_authorized": False, "scenarios": summaries,
    }
    args.out.mkdir(parents=True, exist_ok=True)
    cases = args.out/"cases.csv"
    case_summary = args.out/"evidence.json"
    frame.to_csv(cases, index=False)
    (args.out/"manifest.json").write_text(json.dumps(calibration_manifest(
        "B6",master_seed=args.master_seed,shard_id=args.shard_id,
        records_per_scenario=args.replicates,case_files=("cases.csv",)),
        indent=2,sort_keys=True)+"\n")
    case_summary.write_text(json.dumps(evidence, indent=2, sort_keys=True)+"\n")
    (args.out/"sha256.txt").write_text(
        sha256(cases.read_bytes()).hexdigest()+"  cases.csv\n"+
        sha256(case_summary.read_bytes()).hexdigest()+"  evidence.json\n"+
        sha256((args.out/"manifest.json").read_bytes()).hexdigest()+"  manifest.json\n")
    print(json.dumps(evidence, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
