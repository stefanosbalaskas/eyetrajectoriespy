"""Rank-two independent Gaussian score-marginal likelihood falsification contracts.

Research-only. Compare fully expanded observed-data Gaussian log density with
independently coded low-rank determinant-lemma evaluation. No posterior sampler,
SBC, population interval coverage, or publication gate is qualified here.
"""
from __future__ import annotations

from dataclasses import dataclass
import argparse
from hashlib import sha256
import json
from pathlib import Path
import numpy as np
import pandas as pd

from eyetrajectoriespy.bayesian.sparse_factor_gibbs import _spline_basis
from eyetrajectoriespy.types import IrregularTrajectorySet


@dataclass(frozen=True)
class RankTwoCase:
    gaze: IrregularTrajectorySet
    evaluation_grid: np.ndarray
    mean: np.ndarray  # (dimension, basis)
    loading: np.ndarray  # (dimension, basis, rank)
    noise_sd: tuple[float, ...]
    exact_matched_prior: bool


def generate_case(seed: int, *, paired: bool, near_tied: bool, participants: int = 12) -> RankTwoCase:
    """Fresh matched-prior rank-two truth; near ties are explicitly out-of-prior stress."""
    if participants < 2:
        raise ValueError("at least two participants required")
    rng = np.random.default_rng(seed)
    d, q, rank = 2, 5, 2
    grid = np.linspace(0.0, 1.0, 23)
    mean = rng.normal(0.0, .45, (d, q))
    if near_tied:
        basis = _spline_basis(grid, 0.0, 1.0, q)
        block_basis = np.zeros((d*len(grid), d*q))
        for channel in range(d):
            block_basis[channel*len(grid):(channel+1)*len(grid),
                        channel*q:(channel+1)*q] = basis
        raw = rng.normal(size=(d*q, rank))
        Q, _ = np.linalg.qr(block_basis @ raw)
        loading = np.linalg.lstsq(block_basis, .3*Q, rcond=None)[0].reshape(d, q, rank)
    else:
        loading = rng.normal(0.0, .20, (d, q, rank))
    noise = (.04, .06)
    all_t, all_v = [], []
    for i in range(participants):
        tx = np.sort(rng.uniform(.01, .99, 12+i % 3))
        ty = tx.copy() if paired else np.sort(rng.uniform(.01, .99, 11+i % 4))
        z = rng.normal(size=rank)
        x = _spline_basis(tx, 0.0, 1.0, q) @ (mean[0]+loading[0]@z)
        x += rng.normal(0.0, noise[0], len(tx))
        y = _spline_basis(ty, 0.0, 1.0, q) @ (mean[1]+loading[1]@z)
        y += rng.normal(0.0, noise[1], len(ty))
        if paired:
            tt, vv = tx, np.column_stack((x, y))
        else:
            tt = np.sort(np.r_[tx, ty])
            vv = np.full((len(tt), d), np.nan)
            vv[np.searchsorted(tt, tx), 0] = x
            vv[np.searchsorted(tt, ty), 1] = y
        all_t.append(tt)
        all_v.append(vv)
    gaze = IrregularTrajectorySet(
        time=tuple(all_t), values=tuple(all_v),
        curve_ids=tuple(f"R{i}" for i in range(participants)),
        dimension_names=("x", "y"), coordinate_system="normalized",
        time_unit="s",
        metadata=pd.DataFrame({"participant_id": [f"R{i}" for i in range(participants)]}),
        provenance={"generated_rank": 2, "near_tied_stress": near_tied},
    )
    return RankTwoCase(gaze, grid, mean, loading, noise, not near_tied)


def observed_design(case: RankTwoCase, participant: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Observed (not imputed) values, channel-major design and known variances."""
    t, v = case.gaze.time[participant], case.gaze.values[participant]
    d, q = case.mean.shape
    if case.loading.shape != (d, q, 2) or len(case.noise_sd) != d:
        raise ValueError("rank-two mean/loading/noise dimensions do not match")
    matrices, observations, variance_blocks = [], [], []
    for axis in range(d):
        yy = np.asarray(v[:, axis], float)
        times = np.asarray(t, float)
        ok = np.isfinite(yy)
        block = np.zeros((int(ok.sum()), d*q))
        block[:, axis*q:(axis+1)*q] = _spline_basis(times[ok], 0.0, 1.0, q)
        matrices.append(block)
        observations.append(yy[ok])
        if not np.isfinite(case.noise_sd[axis]) or case.noise_sd[axis] <= 0:
            raise ValueError("strictly positive finite known noise is required")
        variance_blocks.append(np.full(int(ok.sum()), case.noise_sd[axis]**2))
    X, y, vdiag = np.concatenate(matrices), np.concatenate(observations), np.concatenate(variance_blocks)
    if not len(y) or not np.isfinite(X).all() or not np.isfinite(y).all():
        raise ValueError("all participants need finite observed measurements")
    return X, y, vdiag


def dense_gaussian_loglike(case: RankTwoCase) -> float:
    """Independent full observation-space Gaussian determinant/inverse reference."""
    flat_mu = case.mean.reshape(-1)
    flat_load = case.loading.reshape(-1, 2)
    total = 0.0
    for i in range(case.gaze.n_curves):
        X, y, vdiag = observed_design(case, i)
        resid = y-X@flat_mu
        B = X@flat_load
        C = np.diag(vdiag)+B@B.T
        sign, logdet = np.linalg.slogdet(C)
        if sign <= 0:
            raise ValueError("dense covariance must be positive definite")
        total -= .5*(len(y)*np.log(2*np.pi)+logdet+resid@np.linalg.solve(C,resid))
    return float(total)


def score_marginal_loglike(case: RankTwoCase) -> float:
    """Separately coded k=2 Woodbury/determinant-lemma likelihood."""
    mu = case.mean.reshape(-1)
    L = case.loading.reshape(-1, 2)
    total = 0.0
    for i in range(case.gaze.n_curves):
        X, y, var = observed_design(case, i)
        zdesign = X @ L
        r = y-X@mu
        inv = 1./var
        W = np.eye(2)+(zdesign.T*inv)@zdesign
        v = (zdesign.T*inv)@r
        logdet = float(np.linalg.slogdet(W)[1])
        adjusted = (r*inv)@r-v@np.linalg.solve(W,v)
        total -= .5*(len(r)*np.log(2*np.pi)+np.log(var).sum()+logdet+adjusted)
    return float(total)


def population_covariance(case: RankTwoCase) -> np.ndarray:
    """Channel-major grid covariance, invariant to orthogonal factor rotations."""
    B = _spline_basis(case.evaluation_grid, 0.0, 1.0, case.mean.shape[1])
    P = np.vstack([B @ L for L in case.loading])
    return P @ P.T


def rotate_factor(case: RankTwoCase, R: np.ndarray) -> RankTwoCase:
    """Rotation is not a distinct population parameter: L @ R, R.T @ R=I."""
    rot = np.asarray(R, float)
    if rot.shape != (2, 2) or not np.allclose(rot.T@rot, np.eye(2), atol=1e-11):
        raise ValueError("only rank-two orthogonal rotations preserve covariance")
    return RankTwoCase(case.gaze, case.evaluation_grid, case.mean,
                       case.loading @ rot, case.noise_sd, case.exact_matched_prior)


def full_contract(seed: int = 20261231) -> list[dict]:
    records = []
    R = np.array([[np.cos(.73), -np.sin(.73)], [np.sin(.73), np.cos(.73)]])
    for paired in (True, False):
        for tied in (False, True):
            case = generate_case(seed + 10*int(paired)+int(tied), paired=paired, near_tied=tied)
            direct = dense_gaussian_loglike(case)
            reduced = score_marginal_loglike(case)
            rotated = rotate_factor(case, R)
            rotated_ll = score_marginal_loglike(rotated)
            cov = population_covariance(case)
            eig = np.linalg.eigvalsh(cov)
            mismatch = abs(direct-reduced)
            rotation_error = abs(rotated_ll-reduced)
            covariance_error = float(np.max(np.abs(cov-population_covariance(rotated))))
            records.append({
                "design": "paired" if paired else "asynchronous",
                "loading_geometry": "equal_grid_eigenvalues_out_of_prior" if tied else "matched_gaussian_rank2_prior",
                "observed_data_matrix_not_imputed": True,
                "exact_matched_prior": case.exact_matched_prior,
                "rank": 2, "n_participants": case.gaze.n_curves,
                "dense_gaussian_loglik": direct, "woodbury_loglik": reduced,
                "absolute_loglik_discrepancy": mismatch,
                "factor_rotation_absolute_loglik_discrepancy": rotation_error,
                "factor_rotation_max_covariance_discrepancy": covariance_error,
                "covariance_min_eigenvalue": float(eig.min()),
                "covariance_two_largest_eigenvalues": eig[-2:].tolist(),
                "mathematical_contract_passed": bool(
                    mismatch < 1e-7 and rotation_error < 1e-7
                    and covariance_error < 1e-10 and eig.min() > -1e-9),
                "posterior_computation_qualified": False,
                "SBC_completed": False, "coverage_qualified": False,
                "release_authorized": False,
            })
    return records


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--seed", type=int, default=20261231)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    rows = full_contract(a.seed)
    ledger = {
        "study": "B6_B7_RANK2_INDEPENDENT_DENSE_WOODBURY_FALSIFICATION_V1",
        "cases": len(rows), "failures": sum(not x["mathematical_contract_passed"] for x in rows),
        "out_of_prior_near_ties_not_sbc": True,
        "independent_observed_data_dense_reference": True,
        "pymc_gradient_graph_validated": False,
        "rank2_nuts_sampler_run": False, "SBC_completed": False,
        "nominal_population_coverage_qualified": False, "release_authorized": False,
    }
    for name, payload in (("cases.json",rows), ("evidence.json",ledger)):
        (a.out/name).write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
    (a.out/"SHA256SUMS").write_text("".join(
        sha256((a.out/name).read_bytes()).hexdigest()+f"  {name}\n"
        for name in ("cases.json", "evidence.json")))
    print("RANK2 DENSE-GAUSSIAN MATHEMATICS:",json.dumps(ledger,sort_keys=True))
    if ledger["failures"]:
        raise SystemExit("independent mathematical identity contract failed")


if __name__ == "__main__":
    main()
