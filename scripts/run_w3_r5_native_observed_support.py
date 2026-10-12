"""W3 R5: observed-support-only irregular regression, original research pilot.

No interpolation, imputation, extrapolation or silent curve exclusion.
Independent-curve setting only: 128 *fresh* generating blocks, with
MCAR, x-dependent MAR and latent-response-dependent MNAR paired on identical
source data and uniforms. Complete-case, native observed-support OLS, and
known-probability MAR IPW are explicit *research contrasts*, not package APIs.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd

from eyetrajectoriespy import IrregularTrajectorySet, TrajectorySet
from eyetrajectoriespy.workflows import (
    FunctionOnScalarWorkflowConfig,
    run_function_on_scalar_workflow,
)
from scripts.run_w3_known_truth_workflow_validation import (
    TIME, DIMS, truth_coefficients,
)

STUDY = "W3_R5_NATIVE_OBSERVED_SUPPORT_128_BLOCK_V1"
MASTER_SEED = 20261012903
BLOCKS = 128
N_UNITS = 96
MECHANISMS = ("mcar", "mar_x", "latent_mnar")
MISSING_SLICE = slice(11, 19)
MIDPOINT = 15
MIN_SUPPORT = 8
ORACLE_TOL = 2e-10
MC_BOOTSTRAP_DRAWS = 2000


def logistic(z):
    z = np.asarray(z, dtype=float)
    return 1 / (1 + np.exp(-np.clip(z, -35, 35)))


def source(block: int, mechanism: str):
    if type(block) is not int or not 0 <= block < BLOCKS:
        raise ValueError("block outside predeclared independent source ledger")
    if mechanism not in MECHANISMS:
        raise ValueError("unplanned recording-loss mechanism")

    rng = np.random.default_rng(MASTER_SEED + 10007 * block)
    x = rng.uniform(-.95, .95, size=N_UNITS)
    truth = truth_coefficients()
    mu = truth[0][None] + x[:, None, None] * truth[1][None]
    subject = rng.normal(0, .075, size=(N_UNITS, 1, len(DIMS))) * (
        1 + .30 * TIME[None, :, None]
    )
    sensor = rng.normal(0, .055, size=(N_UNITS, len(TIME), len(DIMS)))
    y = mu + subject + sensor
    uniforms = rng.uniform(size=N_UNITS)

    if mechanism == "mcar":
        probability = np.full(N_UNITS, .35)
    elif mechanism == "mar_x":
        probability = logistic(-.62 + 1.30 * x)
    else:
        residual = y[:, MIDPOINT, 0] - mu[:, MIDPOINT, 0]
        probability = logistic(-.62 + 1.30 * x + 2.7 * residual / .105)

    lost = uniforms < probability
    if lost.sum() == 0:
        raise ValueError("no source recording gaps in prespecified scenario")

    ids = tuple(f"Curve_{i:03d}" for i in range(N_UNITS))
    meta = pd.DataFrame({"participant_id": ids, "trial_id": 0})
    full = TrajectorySet(
        time=TIME.copy(), values=y.copy(), curve_ids=ids,
        dimension_names=DIMS, coordinate_system="normalized", time_unit="s",
        metadata=meta, provenance={
            "study": STUDY, "block": block, "simulated": True,
            "recording_loss": "none", "unit": "independent_curve",
        },
    )
    frame = pd.DataFrame({"curve_id": ids, "condition": x})
    native_times = []
    native_values = []
    observed_mask = np.ones((N_UNITS, len(TIME)), dtype=bool)
    observed_mask[lost, MISSING_SLICE] = False
    for i in range(N_UNITS):
        native_times.append(TIME[observed_mask[i]].copy())
        native_values.append(y[i, observed_mask[i]].copy())
    native = IrregularTrajectorySet(
        time=tuple(native_times),
        values=tuple(native_values), curve_ids=ids,
        dimension_names=DIMS, coordinate_system="normalized", time_unit="s",
        metadata=meta, provenance={
            "study": STUDY, "block": block, "mechanism": mechanism,
            "simulated": True, "native_times_retained": True,
            "interpolation_performed": False,
        },
    )
    return full, native, frame, truth, x, y, lost, probability, observed_mask


def ols_unitwise(X, Y, *, weights=None):
    """Return explicit least-squares estimates, no package method promotion."""
    X = np.asarray(X, float)
    Y = np.asarray(Y, float)
    if X.ndim != 2 or X.shape[1] != 2 or Y.ndim != 2 or Y.shape[0] != X.shape[0]:
        raise ValueError("incorrect independent-unit OLS input shape")
    if len(X) < MIN_SUPPORT or np.linalg.matrix_rank(X) < 2:
        raise ValueError("inadequate independent-unit support or rank")
    if weights is not None:
        weights = np.asarray(weights, float)
        if weights.shape != (len(X),) or np.any(~np.isfinite(weights)) or np.any(weights <= 0):
            raise ValueError("invalid observed-data analysis weights")
        scale = np.sqrt(weights)
        X = X * scale[:, None]
        Y = Y * scale[:, None]
    return np.linalg.lstsq(X, Y, rcond=None)[0]


def observed_support_fit(native: IrregularTrajectorySet, x, *, probability=None):
    """Use only exactly observed native timestamps, never fill missing grid cells.

    The externally specified TIME grid is an evaluation target, not an
    interpolation grid. At each target time, only units with a genuine
    recorded sample at *that exact time* contribute to weighted OLS.
    Missing coefficient locations are not estimated if support/rank fails.
    """
    if not isinstance(native, IrregularTrajectorySet):
        raise TypeError("native irregular gaze representation required")
    x = np.asarray(x, float)
    if len(x) != len(native.curve_ids):
        raise ValueError("independent-unit condition map length mismatch")
    if probability is not None:
        probability = np.asarray(probability, float)
        if probability.shape != (len(x),) or np.any(probability <= 0) or np.any(probability >= 1):
            raise ValueError("invalid known observation probabilities")

    X = np.column_stack((np.ones(len(x)), x))
    beta = np.full((2, len(TIME), len(DIMS)), np.nan)
    support = np.zeros(len(TIME), dtype=int)
    for t_idx, t in enumerate(TIME):
        indices = []
        responses = []
        for idx, (native_t, native_y) in enumerate(zip(native.time, native.values)):
            k = int(np.searchsorted(native_t, t))
            if k < len(native_t) and native_t[k] == t:
                indices.append(idx)
                responses.append(native_y[k])
        support[t_idx] = len(indices)
        if support[t_idx] < MIN_SUPPORT:
            continue
        idx = np.array(indices, dtype=int)
        # No observations are missing outside the common gap window; the\n        # probability of observation there is exactly 1, even when a unit\n        # was selected for a mid-trial gap. Never weight complete time slices.\n        in_loss_window = MISSING_SLICE.start <= t_idx < MISSING_SLICE.stop\n        w = (1 / (1 - probability[idx])) if (probability is not None and in_loss_window) else None
        beta[:, t_idx, :] = ols_unitwise(X[idx], np.asarray(responses), weights=w)
    return beta, support


def block_mc_interval(values, *, seed: int):
    if not values:
        return None
    x = np.asarray(values, float)
    rng = np.random.default_rng(seed)
    sampled = rng.integers(0, len(x), size=(MC_BOOTSTRAP_DRAWS, len(x)))
    return [float(v) for v in np.quantile(x[sampled].mean(axis=1), [.025,.975])]


def evaluate(block: int, mechanism: str):
    row = {
        "study": STUDY, "block": block, "mechanism": mechanism,
        "status": "failed", "exception": None, "n_source_units": N_UNITS,
        "n_explicit_complete_units": None, "n_source_curve_records": N_UNITS,
        "n_ever_missing": None, "fraction_observations_masked": None,
        "observed_time_support": None, "minimum_native_support": None,
        "full_slope_rmse": None, "complete_case_slope_rmse": None,
        "available_time_slope_rmse": None,
        "known_probability_ipw_slope_rmse": None,
        "complete_case_mid_slope_minus_full": None,
        "available_time_mid_slope_minus_full": None,
        "known_probability_ipw_mid_slope_minus_full": None,
        "available_outside_gap_equals_full": False,
        "available_inside_gap_equals_explicit_complete_case": False,
        "irregular_input_rejected_by_current_W3": False,
        "package_full_ols_oracle_delta": None,
        "package_cc_ols_oracle_delta": None,
        "native_source_unchanged": False,
        "known_probability_ipw_is_oracle_research_only": mechanism != "latent_mnar",
        "mnar_probability_unavailable_to_real_analyst": mechanism == "latent_mnar",
        "missingness_correction_qualified": False,
        "statistical_calibration_qualified": False,
        "release_authorized": False,
    }
    try:
        full, native, frame, truth, x, y, lost, prob, expected_support = source(block,mechanism)
        n_lost = int(np.sum(lost))
        unit_kept = np.flatnonzero(~lost)
        if len(unit_kept) < MIN_SUPPORT:
            raise ValueError("insufficient genuinely complete curves")

        cfg = FunctionOnScalarWorkflowConfig(
            predictors=("condition",), dimensions=DIMS, unit="curve",
        )
        native_before = [(v.copy(),t.copy()) for t,v in zip(native.time,native.values)]
        try:
            run_function_on_scalar_workflow(native, frame, config=cfg)
        except TypeError as exc:
            if "IrregularTrajectorySet" not in str(exc):
                raise
            row["irregular_input_rejected_by_current_W3"] = True
        else:
            raise ValueError("current complete-grid W3 silently fit irregular data")

        full_pkg = run_function_on_scalar_workflow(full,frame,config=cfg).fit
        selected = full.subset(unit_kept.tolist())
        cc_pkg = run_function_on_scalar_workflow(
            selected, frame.iloc[unit_kept].reset_index(drop=True), config=cfg
        ).fit
        X = np.column_stack((np.ones(len(x)), x))
        full_oracle = ols_unitwise(X, y.reshape(len(x),-1)).reshape(
            2,len(TIME),len(DIMS)
        )
        cc_oracle = ols_unitwise(
            X[unit_kept], y[unit_kept].reshape(len(unit_kept),-1)
        ).reshape(2,len(TIME),len(DIMS))
        full_delta = float(np.max(np.abs(full_pkg.coefficients-full_oracle)))
        cc_delta = float(np.max(np.abs(cc_pkg.coefficients-cc_oracle)))
        if max(full_delta, cc_delta)>ORACLE_TOL:
            raise ValueError("separately calculated dense OLS reference mismatch")

        available, support = observed_support_fit(native,x)
        if np.any(~np.isfinite(available)):
            raise ValueError("missing native time-specific statistical support")
        if not np.array_equal(support,expected_support.sum(axis=0)):
            raise ValueError("native original observed-time support tally changed")
        available_outside = np.allclose(
            available[:,list(range(0,MISSING_SLICE.start))+list(range(MISSING_SLICE.stop,len(TIME)))],
            full_oracle[:,list(range(0,MISSING_SLICE.start))+list(range(MISSING_SLICE.stop,len(TIME)))],
            atol=ORACLE_TOL,rtol=0,
        )
        available_inside = np.allclose(
            available[:,MISSING_SLICE],cc_oracle[:,MISSING_SLICE],
            atol=ORACLE_TOL,rtol=0,
        )
        if not available_outside or not available_inside:
            raise ValueError("observed-time OLS does not match exact source support")
        for (before_val,before_t), now_t, now_val in zip(
            native_before,native.time,native.values
        ):
            if not np.array_equal(before_t,now_t) or not np.array_equal(before_val,now_val):
                raise ValueError("native gaze source was modified")

        # Known conditional observation probabilities are accessible
        # *only in the simulation*. Never claim they are estimated by W3.
        ipw = None
        if mechanism in ("mcar","mar_x"):
            ipw, ipw_support = observed_support_fit(native,x,probability=prob)
            if not np.array_equal(support,ipw_support):
                raise ValueError("oracle probability weighting changed source support")
            if not np.isfinite(ipw).all():
                raise ValueError("oracle probability-weighted OLS was unidentifiable")

        row.update({
            "status":"ok", "n_explicit_complete_units":int(len(unit_kept)),
            "n_ever_missing":n_lost,
            "fraction_observations_masked":float(1-expected_support.mean()),
            "observed_time_support":[int(v) for v in support],
            "minimum_native_support":int(support.min()),
            "full_slope_rmse":float(np.sqrt(np.mean((full_oracle[1]-truth[1])**2))),
            "complete_case_slope_rmse":float(np.sqrt(np.mean((cc_oracle[1]-truth[1])**2))),
            "available_time_slope_rmse":float(np.sqrt(np.mean((available[1]-truth[1])**2))),
            "known_probability_ipw_slope_rmse":(
                float(np.sqrt(np.mean((ipw[1]-truth[1])**2))) if ipw is not None else None
            ),
            "complete_case_mid_slope_minus_full":float(
                cc_oracle[1,MIDPOINT,0]-full_oracle[1,MIDPOINT,0]
            ),
            "available_time_mid_slope_minus_full":float(
                available[1,MIDPOINT,0]-full_oracle[1,MIDPOINT,0]
            ),
            "known_probability_ipw_mid_slope_minus_full":(
                float(ipw[1,MIDPOINT,0]-full_oracle[1,MIDPOINT,0])
                if ipw is not None else None
            ),
            "available_outside_gap_equals_full":True,
            "available_inside_gap_equals_explicit_complete_case":True,
            "package_full_ols_oracle_delta":full_delta,
            "package_cc_ols_oracle_delta":cc_delta,
            "native_source_unchanged":True,
        })
    except Exception as exc:
        row["exception"] = {"type":type(exc).__name__,"message":str(exc)[:900]}
    return row


def audit(rows):
    expected={(block,m) for block in range(BLOCKS) for m in MECHANISMS}
    keys=[(r["block"],r["mechanism"]) for r in rows]
    if len(keys)!=len(set(keys)) or not set(keys).issubset(expected):
        raise ValueError("duplicate or unplanned original research scenario")
    missing=sorted(f"{b}:{m}" for b,m in expected-set(keys))
    completed=[r for r in rows if r["status"]=="ok"]
    groups={}
    for mi,m in enumerate(MECHANISMS):
        part=[r for r in completed if r["mechanism"]==m]
        def agg(field):
            vals=[r[field] for r in part if r[field] is not None]
            return {
                "mean":float(np.mean(vals)) if vals else None,
                "independent_block_bootstrap95":block_mc_interval(
                    vals,seed=MASTER_SEED+127*mi+sum(map(ord,field))
                ),
                "completed_denominator":len(vals),
                "planned_denominator":BLOCKS,
            }
        groups[m]={"completed":len(part),"attempted":BLOCKS,
            "mean_outcomes":{field:agg(field) for field in (
                "n_ever_missing","n_explicit_complete_units",
                "fraction_observations_masked","minimum_native_support",
                "full_slope_rmse","complete_case_slope_rmse",
                "available_time_slope_rmse","known_probability_ipw_slope_rmse",
                "complete_case_mid_slope_minus_full",
                "available_time_mid_slope_minus_full",
                "known_probability_ipw_mid_slope_minus_full"
            )},
            "source_integrity_passes":sum(
                r["native_source_unchanged"] and
                r["available_outside_gap_equals_full"] and
                r["available_inside_gap_equals_explicit_complete_case"] and
                r["irregular_input_rejected_by_current_W3"] for r in part
            ),
            "oracle_probability_weighting_not_run_under_mnar": m=="latent_mnar",
        }
    return {
        "study":STUDY,"seed":MASTER_SEED,
        "independent_blocks":BLOCKS,
        "paired_mechanisms_reuse_same_original_data_and_uniforms":True,
        "inference_unit":"independent_curve",
        "participant_repeated_trials_not_qualified":True,
        "planned_cases":len(expected),"source_rows_present":len(rows),
        "completed_cases":len(completed),"failed_cases":len(rows)-len(completed),
        "missing_cases":missing,"groups":groups,
        "available_time_estimator_is_experimental_research_only":True,
        "known_probability_ipw_is_oracle_only":True,
        "mnar_identified_from_observed_gaze":False,
        "confidence_band_calibration_qualified":False,
        "release_authorized":False,
    }


def original_figure(evidence, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    labels=["MCAR","MAR on observed x","Latent MNAR"]
    keys=("full_slope_rmse","complete_case_slope_rmse",
          "available_time_slope_rmse","known_probability_ipw_slope_rmse")
    names=("Full source reference","Explicit full-curve deletion",
           "Available native timestamps","Known-probability oracle IPW")
    x=np.arange(3)
    fig,ax=plt.subplots(figsize=(10,4.5))
    for j,(key,name) in enumerate(zip(keys,names)):
        vals=[evidence["groups"][m]["mean_outcomes"][key]["mean"] for m in MECHANISMS]
        ax.plot(x,vals,marker="o",linestyle="--" if j==3 else "-",label=name)
    ax.set_xticks(x,labels)
    ax.set_ylabel("Mean full-grid slope RMSE relative to known truth")
    ax.set_title("W3 R5: observed-support-only fits do not recreate missing gaze")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path,format="svg",metadata={"Date":None})
    plt.close(fig)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    rows=[evaluate(b,m) for b in range(BLOCKS) for m in MECHANISMS]
    result=audit(rows)
    for name,obj in (("case-ledger.json",rows),("evidence.json",result)):
        (args.out/name).write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")
    original_figure(result,args.out/"source-observed-support.svg")
    (args.out/"source-commit.txt").write_text(os.getenv("GITHUB_SHA","unverified-local")+"\n")
    names=("case-ledger.json","evidence.json","source-observed-support.svg","source-commit.txt")
    (args.out/"SHA256SUMS").write_text("".join(
        sha256((args.out/n).read_bytes()).hexdigest()+f"  {n}\n" for n in names
    ))
    print("W3 R5 NATIVE OBSERVATION SUPPORT AUDIT:",json.dumps(result,sort_keys=True))
    if result["missing_cases"] or result["failed_cases"] or result["completed_cases"]!=len(rows):
        raise SystemExit("source case(s) incomplete; retain original case ledger")
    # No estimation-bias or precision target is used as a CI gate.


if __name__=="__main__":
    main()
