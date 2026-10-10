"""Four-chain independent PyMC/NUTS rank-one B6/B7 reference pilot.

Experimental research ONLY. Refits independently prior-generated rank-one
sparse univariate and paired/asynchronous planar participant datasets.
All identified midpoint/quarter functionals are checked. Repeated coverage,
rank-two mixing and rank-based SBC are NOT established by this pilot.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import time
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from eyetrajectoriespy.bayesian.sparse_factor_gibbs import _spline_basis
from eyetrajectoriespy.research.calibration_seed import calibration_replicate_seed
from scripts.run_b6_population_calibration_grid import (
    _known_truth, GRID as B6_GRID, MEAN_PRIOR_SD, N_BASIS,
)
from scripts.run_b6_b7_independent_pymc_nuts import _planar_data, _pymc_marginal
from scripts.run_b6_b7_longchain_identified_geometry import identified_mcse_geometry

DESIGNS = ("B6_rank1", "B7_rank1_paired", "B7_rank1_asynchronous")
STUDY = "B6_B7_FOUR_CHAIN_NUTS_INDEPENDENT_REFERENCE_V1"
SCREEN = {"max_rank_rhat": 1.01, "min_bulk_ess": 400.0,
          "min_tail_ess": 400.0, "min_energy_bfmi": 0.3,
          "max_divergences": 0}
REF_DEFAULTS = {"draws_per_chain": 800, "tune_per_chain": 1200,
                "chains": 4, "cores": 2, "target_accept": 0.94}


def declared_seed(master_seed: int, design: str, replicate: int) -> int:
    """Fresh namespace, not a replay/tuned subset of the prior nine-fit study."""
    if design not in DESIGNS or replicate not in (0, 1):
        raise ValueError("four-chain pilot requires declared design and replicate 0 or 1")
    return calibration_replicate_seed(
        STUDY, master_seed=master_seed, shard_id=0,
        scenario=design, replicate=replicate)


def source_truth(seed: int, design: str) -> tuple:
    """Exact matched generating prior/noise, untouched original data geometry."""
    if design == "B6_rank1":
        gaze, mean, cov, _, _ = _known_truth(seed, "matched_rank1")
        return gaze, B6_GRID, (.05,), ("x",), mean[:, None], cov, MEAN_PRIOR_SD
    if design in DESIGNS[1:]:
        gaze, grid, noise, mean, cov = _planar_data(
            seed, design == "B7_rank1_asynchronous")
        return gaze, grid, noise, ("x", "y"), mean, cov, .45
    raise ValueError("unknown design")


def identified_functionals(
    posterior_mean: np.ndarray,
    posterior_loading: np.ndarray,
    grid: np.ndarray,
    dimensions: tuple[str, ...],
    generating_mean: np.ndarray,
    generating_covariance: np.ndarray,
) -> dict[str, tuple[np.ndarray, float]]:
    """Project four-chain rank-one source coefficients, invariant to sign flips."""
    m = np.asarray(posterior_mean, dtype=float)
    L = np.asarray(posterior_loading, dtype=float)
    if m.ndim != 4 or L.ndim != 5 or m.shape[0:2] != L.shape[0:2]:
        raise ValueError("incorrect (chains, draws, dimension, basis[,rank]) arrays")
    chains, draws, d, q = m.shape
    if chains != 4 or draws < 100 or d != len(dimensions) or L.shape != (chains, draws, d, q, 1):
        raise ValueError("four-chain rank-one identification dimensions required")
    basis = _spline_basis(grid, 0.0, 1.0, q)
    projected_mean = np.einsum("tq,cdkq->cdkt", basis, m)
    projected_load = np.einsum("tq,cdkq->cdkt", basis, L[..., 0])
    n = len(grid)
    if generating_mean.shape != (n, d) or generating_covariance.shape != (d*n, d*n):
        raise ValueError("truth and population covariance must use channel-major ordering")
    idx = (n//4, n//2, (3*n)//4)
    results: dict[str, tuple[np.ndarray, float]] = {}
    for i in idx:
        suffix = ("quarter", "midpoint", "three_quarters")[idx.index(i)]
        results[f"x_mean_{suffix}"] = (projected_mean[:, :, 0, i],
                                        float(generating_mean[i, 0]))
        results[f"x_variance_{suffix}"] = (projected_load[:, :, 0, i]**2,
                                            float(generating_covariance[i, i]))
        if d == 2:
            results[f"y_mean_{suffix}"] = (projected_mean[:, :, 1, i],
                                            float(generating_mean[i, 1]))
            results[f"y_variance_{suffix}"] = (projected_load[:, :, 1, i]**2,
                                                float(generating_covariance[n+i, n+i]))
            results[f"xy_covariance_{suffix}"] = (
                projected_load[:, :, 0, i]*projected_load[:, :, 1, i],
                float(generating_covariance[i, n+i]))
    return results


def numerical_reference_diagnostics(idata, functionals: dict) -> dict:
    """Full four-chain NUTS checks on rotation-invariant population quantities."""
    import arviz as az

    stats = idata.sample_stats
    required = ("diverging", "energy")
    if not all(x in stats for x in required):
        raise ValueError("NUTS sample_stats missing required diagnostics")
    divergences = int(np.asarray(stats["diverging"], dtype=int).sum())
    bfmi = np.asarray(az.bfmi(idata), dtype=float)
    if bfmi.shape != (4,) or not np.isfinite(bfmi).all():
        raise ValueError("four-chain finite energy-BFMI required")
    depth = (np.asarray(stats["tree_depth"], dtype=float)
             if "tree_depth" in stats else None)
    rows = {}
    for name, (draws, truth) in functionals.items():
        result = identified_mcse_geometry(draws)
        result["single_dataset_truth_value"] = float(truth)
        result["single_dataset_90pct_interval_contains_truth"] = bool(
            result["posterior_q05"] <= truth <= result["posterior_q95"])
        result["passes_declared_functional_screen"] = bool(
            result["rank_rhat"] <= SCREEN["max_rank_rhat"]
            and result["bulk_ess"] >= SCREEN["min_bulk_ess"]
            and result["tail_ess"] >= SCREEN["min_tail_ess"])
        result["nominal_interval_coverage_qualified"] = False
        rows[name] = result
    sampler = {
        "divergences": divergences,
        "per_chain_energy_bfmi": bfmi.tolist(),
        "min_energy_bfmi": float(bfmi.min()),
        "max_observed_tree_depth": float(depth.max()) if depth is not None else None,
        "tree_depth_ge_10_draws": int(np.sum(depth >= 10)) if depth is not None else None,
        "tree_depth_diagnostic_available": depth is not None,
        "sample_stats_chains": int(np.asarray(stats["diverging"]).shape[0]),
        "sample_stats_draws_per_chain": int(np.asarray(stats["diverging"]).shape[1]),
    }
    sampler["passes_exploratory_sampler_screen"] = bool(
        divergences == 0 and bfmi.min() >= SCREEN["min_energy_bfmi"])
    return {"sampler": sampler, "functionals": rows,
            "all_identified_functionals_pass_exploratory_screen": bool(
                sampler["passes_exploratory_sampler_screen"]
                and all(x["passes_declared_functional_screen"] for x in rows.values())),
            "independent_posterior_scientifically_qualified": False}


def run_one(*, design: str, replicate: int, master_seed: int = 20261219,
            draws: int = 800, warmup: int = 1200, cores: int = 2) -> dict:
    if design not in DESIGNS or replicate not in (0, 1):
        raise ValueError("undeclared design or replicate")
    if draws < 100 or warmup < 100 or cores not in (1, 2, 4):
        raise ValueError("invalid independent reference chain configuration")
    seed = declared_seed(master_seed, design, replicate)
    result = {
        "design": design, "replicate": replicate, "generation_seed": seed,
        "status": "failed", "error_type": None, "error": None,
        "rank": 1, "n_chains": 4, "draws_per_chain": draws, "tune_per_chain": warmup,
        "cores": cores, "same_prior_as_original_B6_B7": True,
        "same_exact_score_marginal_model_as_prior_PyMC_reference": True,
        "new_prior_generated_dataset": True,
        "wall_seconds_full_reference_fit": None,
        "timing_includes_compilation_tuning_sampling": True,
        "memory_peak_measured": False, "memory_peak_bytes": None,
        "reference_checks": None, "identified_ess_per_full_fit_second": {},
        "scientific_reference_validated": False,
        "posterior_coverage_qualified": False, "rank_sbc_completed": False,
        "production_backend_selected": False, "release_authorized": False,
    }
    try:
        gaze, grid, noise, dimensions, mean_truth, cov_truth, prior_sd = source_truth(
            seed, design)
        start = time.perf_counter()
        idata = _pymc_marginal(
            gaze, dimensions=dimensions, noise_sd=noise, q=N_BASIS,
            k=1, mean_sd=prior_sd, load_sd=.20, draws=draws,
            warmup=warmup, random_state=seed+202, chains=4, cores=cores)
        elapsed = time.perf_counter()-start
        mean = np.asarray(idata.posterior["mean"], dtype=float)
        load = np.asarray(idata.posterior["load"], dtype=float)
        functionals = identified_functionals(
            mean, load, grid, dimensions, mean_truth, cov_truth)
        checks = numerical_reference_diagnostics(idata, functionals)
        result.update(
            status="ok", error=None, error_type=None,
            n_participants=int(gaze.n_curves),
            n_identified_functionals=len(functionals),
            wall_seconds_full_reference_fit=float(elapsed),
            reference_checks=checks,
            identified_ess_per_full_fit_second={
                name: float(obj["bulk_ess"]/elapsed) for name, obj
                in checks["functionals"].items()},
        )
    except Exception as exc:
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)[:650]
    return result


def write_case(result: dict, output_dir: Path, master_seed: int) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    ledger = {
        "programme": STUDY, "master_seed": master_seed,
        "attempts_in_this_shard": 1, "independent_truth_datasets_in_this_shard": 1,
        "fit_exceptions_in_this_shard": int(result["status"] != "ok"),
        "two_fresh_replicates_per_design_predeclared": True,
        "tested_designs": list(DESIGNS), "replicate_ids": [0, 1],
        "preregistered_exploratory_screen": SCREEN,
        "sampler_defaults": REF_DEFAULTS,
        "primary_backend": "independently_derived_score_integrated_PyMC_NUTS",
        "native_gibbs": "retained_as_experimental_comparator_not_refit",
        "source_github_sha": os.environ.get("GITHUB_SHA"),
        "zero_divergences_does_not_prove_posterior_validity": True,
        "one_dataset_truth_contains_not_coverage_estimate": True,
        "reference_posterior_qualified": False, "rank_two_validated": False,
        "sbc_completed": False, "nominal_coverage_qualified": False,
        "release_authorized": False,
    }
    outputs = {"cases.json": [result], "evidence.json": ledger}
    for name, value in outputs.items():
        (output_dir/name).write_text(json.dumps(value, indent=2, sort_keys=True)+"\n")
    sums = [f"{sha256((output_dir/name).read_bytes()).hexdigest()}  {name}"
            for name in outputs]
    (output_dir/"SHA256SUMS").write_text("\n".join(sums)+"\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--design", choices=DESIGNS, required=True)
    ap.add_argument("--replicate", type=int, choices=(0, 1), required=True)
    ap.add_argument("--master-seed", type=int, default=20261219)
    ap.add_argument("--draws", type=int, default=800)
    ap.add_argument("--warmup", type=int, default=1200)
    ap.add_argument("--cores", type=int, default=2)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    row = run_one(design=a.design, replicate=a.replicate,
                  master_seed=a.master_seed, draws=a.draws,
                  warmup=a.warmup, cores=a.cores)
    write_case(row, a.out, a.master_seed)
    print("FOUR-CHAIN INDEPENDENT NUTS:", json.dumps({
        "design": a.design, "replicate": a.replicate, "status": row["status"],
        "error_type": row["error_type"],
        "duration_sec": row["wall_seconds_full_reference_fit"],
        "all_functionals_pass_screen": (
            row["reference_checks"]["all_identified_functionals_pass_exploratory_screen"]
            if row["status"] == "ok" else None),
        "posterior_reference_scientifically_qualified": False,
        "release_authorized": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
