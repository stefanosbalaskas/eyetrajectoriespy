"""Research-only rank-two actual PyMC posterior graph and gradient verification.

Compares a real compiled PyMC model and its automatically differentiated
log posterior to a separate dense observation-space Gaussian posterior and
finite-difference derivatives. NO NUTS fits, SBC or coverage are claimed.
"""
from __future__ import annotations

import argparse
from dataclasses import replace
from hashlib import sha256
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
from scipy.stats import norm

from scripts.run_b6_b7_rank2_likelihood_contract import (
    RankTwoCase, dense_gaussian_loglike, generate_case,
    observed_design, population_covariance, rotate_factor,
    score_marginal_loglike,
)

STUDY = "B6_B7_RANK2_PYMC_FULL_POSTERIOR_AND_GRADIENT_R2_V1"
PRIOR_MEAN_SD = .45
PRIOR_LOADING_SD = .20
N_PARTICIPANTS = 4
SEED = 20261331
LOGP_ABS_TOL = 5e-6
GRAD_REL_MAX_TOL = 3e-3


def independent_dense_logposterior(case: RankTwoCase) -> float:
    """True observed-data dense likelihood plus proper normal prior constants."""
    return float(dense_gaussian_loglike(case)
                 + np.sum(norm.logpdf(case.mean, loc=0, scale=PRIOR_MEAN_SD))
                 + np.sum(norm.logpdf(case.loading, loc=0, scale=PRIOR_LOADING_SD)))


def finite_difference_gradient(case: RankTwoCase, epsilon: float = 2e-6) -> np.ndarray:
    """Central differences of independently coded dense posterior, NOT PyTensor."""
    if not np.isfinite(epsilon) or epsilon <= 0:
        raise ValueError("positive finite difference step required")
    shape_m, shape_L = case.mean.shape, case.loading.shape
    msize = case.mean.size
    start = np.r_[case.mean.ravel(), case.loading.ravel()]
    result = np.empty(start.size, dtype=float)

    def at(theta: np.ndarray) -> float:
        modified = replace(
            case, mean=theta[:msize].reshape(shape_m),
            loading=theta[msize:].reshape(shape_L))
        return independent_dense_logposterior(modified)

    for i in range(start.size):
        left, right = start.copy(), start.copy()
        left[i] -= epsilon
        right[i] += epsilon
        result[i] = (at(right)-at(left))/(2*epsilon)
    return result


def build_actual_pymc_model(case: RankTwoCase):
    """Construct the actual PyMC normal-prior/Potential posterior (k=2)."""
    import pymc as pm
    import pytensor.tensor as pt

    d, q = case.mean.shape
    if case.loading.shape != (d, q, 2):
        raise ValueError("rank-two loading shape is required")

    with pm.Model() as model:
        mean = pm.Normal("mean", mu=0.0, sigma=PRIOR_MEAN_SD, shape=(d, q))
        load = pm.Normal("load", mu=0.0, sigma=PRIOR_LOADING_SD, shape=(d, q, 2))
        mu = pt.reshape(mean, (d*q,))
        L = pt.reshape(load, (d*q, 2))
        terms = []
        for i in range(case.gaze.n_curves):
            X, y, var = observed_design(case, i)
            Xt = pt.as_tensor_variable(X)
            yt = pt.as_tensor_variable(y)
            inv = pt.as_tensor_variable(1.0 / var)
            r = yt - pt.dot(Xt, mu)
            Z = pt.dot(Xt, L)
            small_precision = pt.eye(2, dtype="float64") + pt.dot(
                Z.T, inv[:, None] * Z)
            v = pt.dot(Z.T, inv * r)
            adjusted = pt.sum(inv * r * r) - pt.dot(
                v, pt.linalg.solve(small_precision, v))
            log_det = pt.log(pt.linalg.det(small_precision))
            terms.append(-0.5 * (len(y) * np.log(2*np.pi)
                                  + np.log(var).sum() + log_det + adjusted))
        pm.Potential("observed_score_marginal_likelihood", pt.sum(pt.stack(terms)))
    return model, mean, load


def evaluate_case(*, paired: bool, near_tied: bool, seed: int = SEED) -> dict:
    from math import cos, sin
    case = generate_case(
        seed + 100 * int(paired) + int(near_tied), paired=paired,
        near_tied=near_tied, participants=N_PARTICIPANTS)
    info = {
        "study": STUDY, "seed": seed, "paired": paired, "near_tied": near_tied,
        "matched_prior_generated": case.exact_matched_prior,
        "n_participants": case.gaze.n_curves,
        "observed_data_not_imputed": True,
        "status": "failed", "error_type": None, "error": None,
        "rank2_nuts_sampler_run": False, "SBC_completed": False,
        "posterior_calibration_qualified": False, "release_authorized": False,
    }
    try:
        dense = dense_gaussian_loglike(case)
        woodbury = score_marginal_loglike(case)
        model, mean, load = build_actual_pymc_model(case)
        point = {"mean": case.mean.copy(), "load": case.loading.copy()}
        actual_logp = float(model.compile_logp()(point))
        actual_grad = np.asarray(
            model.compile_dlogp(vars=[mean, load])(point), dtype=float).ravel()
        independent_logp = independent_dense_logposterior(case)
        independent_grad = finite_difference_gradient(case)
        if actual_grad.shape != independent_grad.shape:
            raise ValueError("PyMC and independent gradient shapes differ")
        grad_max_scaled = float(np.max(
            np.abs(actual_grad-independent_grad) /
            np.maximum(1.0, np.abs(independent_grad))))
        rotation_angle = .73
        R = np.array([[cos(rotation_angle), -sin(rotation_angle)],
                      [sin(rotation_angle), cos(rotation_angle)]])
        rotated = rotate_factor(case, R)
        rotate_point = {"mean": case.mean.copy(), "load": rotated.loading.copy()}
        rotated_logp = float(model.compile_logp()(rotate_point))
        cov_error = float(np.max(np.abs(
            population_covariance(case)-population_covariance(rotated))))
        value_error = abs(actual_logp-independent_logp)
        rotation_error = abs(rotated_logp-actual_logp)
        checks_pass = bool(
            abs(dense-woodbury) < 1e-7 and
            value_error < LOGP_ABS_TOL and
            grad_max_scaled < GRAD_REL_MAX_TOL and
            rotation_error < 1e-7 and
            cov_error < 1e-10)
        info.update(
            status="ok",
            dense_loglik=float(dense), woodbury_loglik=float(woodbury),
            actual_pymc_logposterior=float(actual_logp),
            independent_dense_logposterior=float(independent_logp),
            actual_minus_dense_abs_logp=float(value_error),
            max_abs_analytic_gradient=float(np.max(np.abs(actual_grad))),
            gradient_number_of_parameters=int(actual_grad.size),
            max_scaled_pymc_vs_dense_finite_difference_gradient_error=grad_max_scaled,
            finite_difference_step=2e-6,
            rotated_logposterior_abs_discrepancy=float(rotation_error),
            rotated_population_covariance_max_abs_discrepancy=cov_error,
            pymc_full_graph_and_gradient_contract_passed=checks_pass,
            near_tied_is_out_of_prior_stress_not_sbc=near_tied)
    except Exception as exc:
        info["error_type"] = type(exc).__name__
        info["error"] = str(exc)[:900]
    return info


def write_artifact(record: dict, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    ledger = {
        "study": STUDY, "attempts": 1,
        "contract_failures": int(record["status"] != "ok" or
                                 not record.get("pymc_full_graph_and_gradient_contract_passed", False)),
        "includes_actual_pymc_logp_and_gradient": True,
        "source_sha": os.environ.get("GITHUB_SHA"),
        "rank2_four_chain_nuts_validated": False,
        "fixed_truth_coverage_studied": False,
        "prior_SBC_completed": False, "release_authorized": False,
    }
    for name, item in (("case.json", record), ("evidence.json", ledger)):
        (out/name).write_text(json.dumps(item, sort_keys=True, indent=2)+"\n")
    (out/"SHA256SUMS").write_text("".join(
        sha256((out/name).read_bytes()).hexdigest()+f"  {name}\n"
        for name in ("case.json", "evidence.json")))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--paired", type=int, choices=[0, 1], required=True)
    p.add_argument("--near-tied", type=int, choices=[0, 1], required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    record = evaluate_case(paired=bool(args.paired), near_tied=bool(args.near_tied))
    write_artifact(record, args.out)
    print("RANK2 ACTUAL PYMC POSTERIOR GRAPH:", json.dumps(record, sort_keys=True))
    if record["status"] != "ok" or not record["pymc_full_graph_and_gradient_contract_passed"]:
        raise SystemExit("rank-two PyMC posterior mathematical contract failed; preserve artifact")


if __name__ == "__main__":
    main()
