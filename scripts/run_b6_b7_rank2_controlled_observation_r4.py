"""R4 controlled rank-two observation-schedule contrast. Research only.

Within each participant count, exact same Gaussian population parameters,
participant scores, x observations, y noise innovations, and y observation counts.
Only the y observation times differ (paired versus asynchronous). n=4 is nested
within n=12; these are NOT independent replicate datasets or calibration data.
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
import pandas as pd

from eyetrajectoriespy.bayesian.sparse_factor_gibbs import _spline_basis
from eyetrajectoriespy.types import IrregularTrajectorySet
from scripts.run_b6_b7_rank2_likelihood_contract import RankTwoCase, population_covariance
from scripts.run_b6_b7_rank2_pymc_graph_contract import build_actual_pymc_model
from scripts.run_b6_b7_rank2_four_chain_nuts_r3 import invariant_functionals
from scripts.run_b6_b7_four_chain_reference import numerical_reference_diagnostics

STUDY = "B6_B7_RANK2_CONTROLLED_PAIRED_ASYNCHRONOUS_R4_V1"
SEED = 2026101117
DESIGNS = ("paired", "asynchronous")
PARTICIPANT_COUNTS = (4, 12)
TOTAL_PARTICIPANTS = max(PARTICIPANT_COUNTS)
SAMPLE = {"chains": 4, "cores": 2, "tune": 700, "draws": 400, "target_accept": 0.94}
NOISE = (.04, .06)


def paired_cases(seed: int, participants: int) -> dict[str, RankTwoCase]:
    """Build matched observations via common random numbers and nesting.

    The same 12-person superpopulation draw is generated for either requested n.
    Person-specific x-channel values and noises are bitwise identical across
    schedule arms. Y observation counts and noise draws match, but Y times vary.
    """
    if participants not in PARTICIPANT_COUNTS:
        raise ValueError("participant count must be one of the predeclared levels")
    rng = np.random.default_rng(seed)
    d, q, k = 2, 5, 2
    mu = rng.normal(0.0, .45, size=(d, q))
    L = rng.normal(0.0, .20, size=(d, q, k))
    B = lambda t: _spline_basis(np.asarray(t, float), 0.0, 1.0, q)
    inputs = []
    for i in range(TOTAL_PARTICIPANTS):
        size = 12 + (i % 3)
        tx = np.sort(rng.uniform(.01, .99, size))
        ty = np.sort(rng.uniform(.01, .99, size))
        z = rng.normal(size=k)
        eps_x = rng.normal(0.0, NOISE[0], size)
        eps_y = rng.normal(0.0, NOISE[1], size)
        x = B(tx) @ (mu[0] + L[0] @ z) + eps_x
        y_paired = B(tx) @ (mu[1] + L[1] @ z) + eps_y
        y_async = B(ty) @ (mu[1] + L[1] @ z) + eps_y
        inputs.append((tx, ty, x, y_paired, y_async, z))

    cases = {}
    for design in DESIGNS:
        times, values = [], []
        for tx, ty, x, yp, ya, _ in inputs[:participants]:
            if design == "paired":
                t = tx.copy()
                val = np.column_stack((x, yp))
            else:
                t = np.sort(np.r_[tx, ty])
                val = np.full((len(t), 2), np.nan)
                val[np.searchsorted(t, tx), 0] = x
                val[np.searchsorted(t, ty), 1] = ya
            times.append(t)
            values.append(val)
        gaze = IrregularTrajectorySet(
            time=tuple(times), values=tuple(values),
            curve_ids=tuple(f"P{i}" for i in range(participants)),
            dimension_names=("x", "y"), coordinate_system="normalized",
            time_unit="s",
            metadata=pd.DataFrame({"participant_id": [f"P{i}" for i in range(participants)]}),
            provenance={"study": STUDY, "seed": seed, "schedule": design,
                        "common_latent_truth": True, "nested_n": True},
        )
        cases[design] = RankTwoCase(
            gaze, np.linspace(0.0, 1.0, 23), mu.copy(), L.copy(),
            NOISE, True)
    return cases


def verify_matched_case_design(cases: dict[str, RankTwoCase]) -> dict:
    if set(cases) != set(DESIGNS):
        raise ValueError("exactly two observation schedules required")
    paired, asynchronous = (cases[k] for k in DESIGNS)
    if paired.gaze.n_curves != asynchronous.gaze.n_curves:
        raise ValueError("participant counts differ")
    if not np.array_equal(paired.mean, asynchronous.mean) or not np.array_equal(
            paired.loading, asynchronous.loading):
        raise ValueError("population truth has changed")
    x_identical, matched_counts, altered_y_times = True, True, 0
    for j in range(paired.gaze.n_curves):
        p_t, p_v = paired.gaze.time[j], paired.gaze.values[j]
        a_t, a_v = asynchronous.gaze.time[j], asynchronous.gaze.values[j]
        xmask = np.isfinite(a_v[:, 0])
        ymask = np.isfinite(a_v[:, 1])
        x_identical &= bool(np.array_equal(p_t, a_t[xmask])
                            and np.array_equal(p_v[:, 0], a_v[xmask, 0]))
        matched_counts &= bool(len(p_t) == int(ymask.sum())
                               and len(p_t) == int(xmask.sum()))
        altered_y_times += int(not np.array_equal(p_t, a_t[ymask]))
    cov_equal = bool(np.array_equal(
        population_covariance(paired), population_covariance(asynchronous)))
    return {
        "n_participants": paired.gaze.n_curves, "x_observations_identical": x_identical,
        "y_observation_counts_identical": matched_counts,
        "participants_with_modified_y_schedule": altered_y_times,
        "population_mean_and_loading_identical": True,
        "population_covariance_identical": cov_equal,
        "matched_design_verified": bool(x_identical and matched_counts and cov_equal
                                        and altered_y_times == paired.gaze.n_curves),
    }


def run_one(*, design: str, participants: int, seed: int = SEED,
            draws: int = SAMPLE["draws"], tune: int = SAMPLE["tune"],
            cores: int = SAMPLE["cores"]) -> dict:
    if design not in DESIGNS or participants not in PARTICIPANT_COUNTS:
        raise ValueError("outside declared 2x2 observation design")
    if draws < 100 or tune < 100 or cores not in (1, 2):
        raise ValueError("invalid sampler budget")
    row = {
        "study": STUDY, "design": design, "participants": participants,
        "common_master_seed": seed, "schedule_only_contrast": True,
        "nested_participant_sample_not_independent": True,
        "same_population_truth_across_all_four_cells": True,
        "sample": {"chains": 4, "cores": cores, "draws": draws, "tune": tune,
                   "target_accept": SAMPLE["target_accept"]},
        "status": "failed", "error_type": None, "error": None,
        "design_contract": None, "reference_checks": None,
        "full_fit_wall_seconds": None, "n_identified_functionals": None,
        "SBC_completed": False, "nominal_coverage_qualified": False,
        "posterior_calibration_qualified": False, "release_authorized": False,
    }
    try:
        import pymc as pm
        pair = paired_cases(seed, participants)
        design_contract = verify_matched_case_design(pair)
        if not design_contract["matched_design_verified"]:
            raise ValueError("controlled latent-data contract failed")
        case = pair[design]
        model, _, _ = build_actual_pymc_model(case)
        start = time.perf_counter()
        with model:
            fit = pm.sample(
                draws=draws, tune=tune, chains=4, cores=cores,
                random_seed=seed+202+participants, target_accept=SAMPLE["target_accept"],
                progressbar=False, compute_convergence_checks=True,
                return_inferencedata=True)
        elapsed = time.perf_counter() - start
        func = invariant_functionals(
            case, np.asarray(fit.posterior["mean"]), np.asarray(fit.posterior["load"]))
        checks = numerical_reference_diagnostics(fit, func)
        row.update(
            status="ok", design_contract=design_contract,
            reference_checks=checks, full_fit_wall_seconds=float(elapsed),
            n_identified_functionals=len(func))
    except Exception as exc:
        row["error_type"] = type(exc).__name__
        row["error"] = str(exc)[:1000]
    return row


def write_case(row: dict, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    summary = {
        "study": STUDY, "attempts": 1,
        "fitting_exceptions": int(row["status"] != "ok"),
        "screen_failures": (int(not row["reference_checks"][
            "all_identified_functionals_pass_exploratory_screen"])
            if row["status"] == "ok" else None),
        "not_four_independent_datasets": True,
        "paired_observation_design_contrast": True,
        "source_sha": os.environ.get("GITHUB_SHA"),
        "SBC_completed": False, "rank2_posterior_qualified": False,
        "nominal_coverage_qualified": False, "release_authorized": False,
    }
    for name, obj in (("case.json", row), ("evidence.json", summary)):
        (out/name).write_text(json.dumps(obj, indent=2, sort_keys=True)+"\n")
    (out/"SHA256SUMS").write_text("".join(
        sha256((out/name).read_bytes()).hexdigest()+f"  {name}\n"
        for name in ("case.json", "evidence.json")))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--design", choices=DESIGNS, required=True)
    ap.add_argument("--participants", type=int, choices=PARTICIPANT_COUNTS, required=True)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--draws", type=int, default=SAMPLE["draws"])
    ap.add_argument("--tune", type=int, default=SAMPLE["tune"])
    ap.add_argument("--cores", type=int, default=SAMPLE["cores"])
    ap.add_argument("--out", type=Path, required=True)
    arg = ap.parse_args()
    row = run_one(design=arg.design, participants=arg.participants,
                  seed=arg.seed, draws=arg.draws, tune=arg.tune, cores=arg.cores)
    write_case(row, arg.out)
    print("RANK2 CONTROLLED OBSERVATION R4:", json.dumps({
        "design": row["design"], "participants": row["participants"],
        "status": row["status"],
        "screen_pass": row["reference_checks"][
            "all_identified_functionals_pass_exploratory_screen"]
            if row["status"] == "ok" else None,
        "fit_seconds": row["full_fit_wall_seconds"],
        "error": row["error"], "release_authorized": False,
    }, sort_keys=True))
    if row["status"] != "ok":
        raise SystemExit("original fit exception retained in evidence")


if __name__ == "__main__":
    main()
