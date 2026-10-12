"""W3 R4 observation-loss selection stress, without pretending to fit missing data.

96 fresh independently generated blocks PER source design. MCAR and
latent-response-dependent observation losses are paired within each original
generating block and use the same loss uniforms. Trial exclusion is explicit
and at the participant level, not a package-hidden preprocessing step.
This is a missingness *sensitivity* study, not a missing-data estimator.
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

from eyetrajectoriespy import TrajectorySet, IrregularTrajectorySet
from eyetrajectoriespy.workflows import (
    FunctionOnScalarWorkflowConfig, run_function_on_scalar_workflow,
)
from eyetrajectoriespy.workflows.experimental import workflow_preflight
from scripts.run_w3_known_truth_workflow_validation import TIME, DIMS, truth_coefficients

STUDY = "W3_OBSERVATION_LOSS_SELECTION_R4_V1"
SEED = 202610124217
BLOCKS = 96
DESIGNS = ("curve", "participant")
MECHANISMS = ("mcar", "latent_response_dependent")
UNITS = {"curve": 72, "participant": 48}
TRIALS = {"curve": 1, "participant": 3}
GAP = slice(11, 19)
ORACLE_TOL = 2e-10
MIN_RETAINED_UNITS = 8


def _expit(x):
    x = np.asarray(x, dtype=float)
    return 1 / (1 + np.exp(-np.clip(x,-35,35)))


def generate(block: int, design: str, mechanism: str):
    if type(block) is not int or not 0 <= block < BLOCKS:
        raise ValueError("generating block outside predeclared ledger")
    if design not in DESIGNS or mechanism not in MECHANISMS:
        raise ValueError("unplanned design or observation mechanism")
    n = UNITS[design]
    trials = TRIALS[design]
    rng = np.random.default_rng(
        SEED + 10009 * block + (0 if design == "curve" else 1)
    )
    x = rng.uniform(-.95, .95, size=n)
    truth = truth_coefficients()
    mean = truth[0][None] + x[:,None,None]*truth[1][None]
    individual = np.zeros_like(mean)
    if design == "participant":
        individual = (
            rng.normal(0,.075,size=(n,1,len(DIMS)))
            * (1+.35*TIME[None,:,None])
        )
    noise = rng.normal(0,.065,size=(n,trials,len(TIME),len(DIMS)))
    source = mean[:,None] + individual[:,None] + noise
    values = source.reshape(n*trials,len(TIME),len(DIMS))
    ids = tuple(f"P{i:03d}-T{j:02d}" for i in range(n) for j in range(trials))
    meta = pd.DataFrame({
        "participant_id": [f"P{i:03d}" for i in range(n) for _ in range(trials)],
        "trial_id": [j for _ in range(n) for j in range(trials)],
    })
    complete = TrajectorySet(
        time=TIME.copy(), values=values.copy(), curve_ids=ids,
        dimension_names=DIMS, coordinate_system="normalized", time_unit="s",
        metadata=meta, provenance={
            "study":STUDY,"block":block,"design":design,
            "simulation":True,"loss_mechanism":"none",
        }
    )
    frame = pd.DataFrame({"curve_id":ids,"condition":np.repeat(x,trials)})

    # The same generating sources and loss uniforms are used for MCAR
    # and latent-response-dependent dropout, but they are distinct paired
    # scenarios, not independent sampling blocks.
    uniforms = rng.uniform(size=n)
    if mechanism == "mcar":
        probability = np.full(n, .35)
    else:
        # The response at the subsequently hidden center of a gaze gap is
        # used by the generating process but is unavailable to the analyst.
        # This is an explicit nonignorable (MNAR) recording-loss model.
        center = source.mean(axis=1)[:,15,0]
        latent_residual = center - (truth[0,15,0] + x*truth[1,15,0])
        log_odds = -.65 + 1.35*x + 2.9*(latent_residual/.10)
        probability = _expit(log_odds)
    lost = uniforms < probability
    incomplete = source.copy()
    # For a repeatedly observed participant, one source trial receives the
    # mid-trial gap; the participant is excluded only in the *explicit*
    # alternative complete-participant analysis, never by workflow_preflight.
    incomplete[lost, 0, GAP, :] = np.nan
    masked_values = incomplete.reshape(n*trials,len(TIME),len(DIMS))
    with_gaps = TrajectorySet(
        time=TIME.copy(), values=masked_values, curve_ids=ids,
        dimension_names=DIMS, coordinate_system="normalized", time_unit="s",
        metadata=meta, provenance={
            "study":STUDY,"block":block,"design":design,
            "simulation":True,"loss_mechanism":mechanism,
            "automatic_exclusion":False,"source_units_with_gap":int(lost.sum()),
        }
    )
    # The irregular object retains native recorded timestamps for *every*
    # curve, without any interpolation/reprojection.
    native_times=[]
    native_values=[]
    for curve in masked_values:
        keep=np.isfinite(curve).all(axis=1)
        native_times.append(TIME[keep].copy())
        native_values.append(curve[keep].copy())
    irregular=IrregularTrajectorySet(
        time=tuple(native_times),values=tuple(native_values),
        curve_ids=ids,dimension_names=DIMS,metadata=meta,
        coordinate_system="normalized",time_unit="s",
        provenance={"study":STUDY,"mechanism":mechanism,
                    "no_automatic_interpolation":True}
    )
    X=np.column_stack((np.ones(n),x))
    full_unit_y=source.mean(axis=1)
    return complete,with_gaps,irregular,frame,truth,X,full_unit_y,lost,probability


def independent_ols(X,Y):
    n=len(X)
    if n < MIN_RETAINED_UNITS:
        raise ValueError("insufficient explicitly retained independent units")
    if np.linalg.matrix_rank(X)!=2:
        raise ValueError("rank deficient independently selected design")
    return np.linalg.lstsq(X,Y.reshape(n,-1),rcond=None)[0].reshape(2,len(TIME),len(DIMS))


def evaluate(block: int, design: str, mechanism: str):
    row={
        "study":STUDY,"block":block,"design":design,"mechanism":mechanism,
        "status":"failed","exception":None,
        "n_source_units":UNITS.get(design),
        "n_source_curves":UNITS.get(design,0)*TRIALS.get(design,1),
        "n_lost_units":None,"n_complete_units":None,
        "n_explicit_retained_curves":None,
        "fraction_masked_values":None,
        "probability_drop_mean":None,
        "full_slope_mid_error":None,"complete_case_slope_mid_error":None,
        "full_slope_function_rmse":None,"complete_case_slope_function_rmse":None,
        "complete_case_minus_full_slope_mid":None,
        "oracle_full_max_error":None,"oracle_cc_max_error":None,
        "missing_grid_rejected":False,"irregular_grid_rejected":False,
        "preflight_retained_all_curves":False,
        "preflight_reported_missingness":False,
        "no_interpolation_or_automatic_exclusion":False,
        "missing_data_inference_qualified":False,
        "release_authorized":False,
    }
    try:
        full,damaged,native,frame,truth,X,Y,lost,drop_p=generate(block,design,mechanism)
        config=FunctionOnScalarWorkflowConfig(
            predictors=("condition",),dimensions=DIMS,unit=design,
            participant_column="participant_id" if design=="participant" else None,
        )
        source_before=damaged.values.copy()
        try:
            run_function_on_scalar_workflow(damaged,frame,config=config)
        except ValueError as exc:
            if "complete finite common-grid" not in str(exc):
                raise
            row["missing_grid_rejected"]=True
        else:
            raise ValueError("W3 unexpectedly fitted the missing grid")
        try:
            run_function_on_scalar_workflow(native,frame,config=config)
        except TypeError as exc:
            if "IrregularTrajectorySet" not in str(exc):
                raise
            row["irregular_grid_rejected"]=True
        else:
            raise ValueError("W3 silently fitted native irregular time grids")
        np.testing.assert_array_equal(damaged.values,source_before)

        preflight=workflow_preflight(
            damaged,participant_column="participant_id",
            trial_column="trial_id",required_dimensions=DIMS,
            require_common_grid=True
        )
        preflight_native=workflow_preflight(
            native,participant_column="participant_id",
            trial_column="trial_id",required_dimensions=DIMS,
            require_common_grid=True
        )
        loss_values=int(np.isnan(damaged.values).sum())
        if loss_values != int(lost.sum())*(GAP.stop-GAP.start)*len(DIMS):
            raise ValueError("generating loss ledger inconsistent with sample mask")
        if preflight.summary.iloc[0]["missing_values"]!=loss_values:
            raise ValueError("advisory preflight did not preserve source gap count")
        if preflight_native.summary.iloc[0]["n_curves"]!=full.n_curves:
            raise ValueError("irregular native preflight dropped source curves")

        full_fit=run_function_on_scalar_workflow(full,frame,config=config).fit
        unit_indices=np.flatnonzero(~lost)
        if len(unit_indices)<MIN_RETAINED_UNITS:
            raise ValueError("too few explicitly complete units for OLS")
        keep_curves=[i*TRIALS[design]+j for i in unit_indices for j in range(TRIALS[design])]
        filtered=damaged.subset(keep_curves)
        selected_design=frame.iloc[keep_curves].reset_index(drop=True)
        cc_fit=run_function_on_scalar_workflow(filtered,selected_design,config=config).fit
        full_oracle=independent_ols(X,Y)
        cc_oracle=independent_ols(X[unit_indices],Y[unit_indices])
        d0=float(np.max(np.abs(full_fit.coefficients-full_oracle)))
        d1=float(np.max(np.abs(cc_fit.coefficients-cc_oracle)))
        if d0>ORACLE_TOL or d1>ORACLE_TOL:
            raise ValueError("independent source regression oracle mismatch")
        if len(cc_fit.unit_ids)!=len(unit_indices):
            raise ValueError("complete-case analysis violated independent-unit accounting")
        if filtered.n_curves!=len(unit_indices)*TRIALS[design]:
            raise ValueError("explicit removal did not preserve complete unit clusters")
        if not np.isfinite(filtered.values).all():
            raise ValueError("explicit filtered trajectories unexpectedly incomplete")
        if not np.array_equal(damaged.values,source_before,equal_nan=True):
            raise ValueError("original masked source changed during workflow evaluation")

        base=float(full_fit.coefficients[1,15,0]-truth[1,15,0])
        cc=float(cc_fit.coefficients[1,15,0]-truth[1,15,0])
        row.update({
            "status":"ok","n_lost_units":int(lost.sum()),
            "n_complete_units":int(len(unit_indices)),
            "n_explicit_retained_curves":filtered.n_curves,
            "fraction_masked_values":loss_values/damaged.values.size,
            "probability_drop_mean":float(np.mean(drop_p)),
            "full_slope_mid_error":base,
            "complete_case_slope_mid_error":cc,
            "full_slope_function_rmse":float(np.sqrt(
                np.mean((full_fit.coefficients[1]-truth[1])**2)
            )),
            "complete_case_slope_function_rmse":float(np.sqrt(
                np.mean((cc_fit.coefficients[1]-truth[1])**2)
            )),
            "complete_case_minus_full_slope_mid":float(
                cc_fit.coefficients[1,15,0]-full_fit.coefficients[1,15,0]
            ),
            "oracle_full_max_error":d0,"oracle_cc_max_error":d1,
            "preflight_retained_all_curves":preflight.summary.iloc[0]["n_curves"]==full.n_curves,
            "preflight_reported_missingness":loss_values>0,
            "no_interpolation_or_automatic_exclusion":True,
        })
    except Exception as exc:
        row["exception"]={"type":type(exc).__name__,"message":str(exc)[:1000]}
    return row


def percentile_block_interval(data, *,seed, draws=2000):
    if not data:
        return None
    v=np.asarray(data,dtype=float)
    rng=np.random.default_rng(seed)
    idx=rng.integers(0,len(v),size=(draws,len(v)))
    return [float(x) for x in np.quantile(v[idx].mean(axis=1),[.025,.975])]


def audit(rows):
    expected={(b,d,m) for b in range(BLOCKS) for d in DESIGNS
              for m in MECHANISMS}
    keys=[(r["block"],r["design"],r["mechanism"]) for r in rows]
    if len(keys)!=len(set(keys)) or not set(keys).issubset(expected):
        raise ValueError("duplicated or unplanned study source case")
    missing=sorted(f"{b}:{d}:{m}" for b,d,m in expected-set(keys))
    completed=[r for r in rows if r["status"]=="ok"]
    groups={}
    for di,d in enumerate(DESIGNS):
        groups[d]={}
        for mi,m in enumerate(MECHANISMS):
            x=sorted([r for r in completed if r["design"]==d and
                      r["mechanism"]==m],key=lambda z:z["block"])
            measures={}
            for field in ["n_complete_units","fraction_masked_values",
                "full_slope_mid_error","complete_case_slope_mid_error",
                "complete_case_minus_full_slope_mid",
                "full_slope_function_rmse","complete_case_slope_function_rmse"]:
                values=[r[field] for r in x]
                measures[field]={
                    "mean":float(np.mean(values)) if values else None,
                    "paired_block_bootstrap95":percentile_block_interval(
                        values,seed=SEED + 501*di+17*mi+
                        sum(ord(z) for z in field))
                }
            groups[d][m]={"attempted":BLOCKS,"completed":len(x),
                "measures":measures,
                "n_independent_units_before_selection":UNITS[d],
                "all_missing_sources_rejected":all(
                    r["missing_grid_rejected"] for r in x
                ),
                "all_irregular_sources_rejected":all(
                    r["irregular_grid_rejected"] for r in x
                ),
                "all_independent_numerical_oracles_pass":all(
                    r["oracle_full_max_error"]<=ORACLE_TOL and
                    r["oracle_cc_max_error"]<=ORACLE_TOL for r in x
                )}
    return {
        "study":STUDY,"source_seed":SEED,
        "independent_generating_blocks_per_design":BLOCKS,
        "paired_mechanisms_reuse_same_source_and_uniform_draws":True,
        "complete_case_loss_is_explicit_analyst_action_not_workflow":True,
        "planned_cases":len(expected),"observed_cases":len(rows),
        "completed_cases":len(completed),"failures":len(rows)-len(completed),
        "missing_cases":missing,"groups":groups,
        "statistical_missingness_correction_qualified":False,
        "mnar_identified_from_observed_data":False,
        "release_authorized":False,
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    rows=[evaluate(b,d,m) for b in range(BLOCKS)
          for d in DESIGNS for m in MECHANISMS]
    result=audit(rows)
    for name,obj in (("case-ledger.json",rows),("evidence.json",result)):
        (args.out/name).write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")
    (args.out/"source-commit.txt").write_text(os.getenv("GITHUB_SHA","unverified-local")+"\n")
    names=("case-ledger.json","evidence.json","source-commit.txt")
    (args.out/"SHA256SUMS").write_text("".join(
        sha256((args.out/f).read_bytes()).hexdigest()+f"  {f}\n"
        for f in names
    ))
    print("W3 OBSERVATION LOSS SELECTION SCIENCE:",json.dumps(result,sort_keys=True))
    if result["failures"] or result["missing_cases"] or result["completed_cases"]!=len(rows):
        raise SystemExit("Original W3 missingness science incomplete; retain evidence")
    # No regression-bias magnitude or relative performance becomes a CI pass gate.


if __name__=="__main__":
    main()
