"""Fresh-block W3 fixed-HC1 vs bootstrap-t under variance/temporal stress.

Scientific pilot: 24 independent seeds per design; n 36 is nested in n 144,
four regimes share innovations per block. Thus 384 fits are not independent
replications. All source outcomes and failures are retained. No API promotion.
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

from eyetrajectoriespy import TrajectorySet
from eyetrajectoriespy.types import FunctionOnScalarBootstrapResult
from eyetrajectoriespy.function_on_scalar import function_on_scalar_simultaneous_bands
from eyetrajectoriespy.workflows import (
    FunctionOnScalarWorkflowConfig, run_function_on_scalar_workflow,
)
from scripts.run_w3_known_truth_workflow_validation import TIME, DIMS, truth_coefficients
from scripts.run_w3_fixed_truth_interval_pilot import independent_hc1_oracle, wilson
from scripts.run_w3_hc1_restudenization_nested_n import independent_restudentized_maxima

STUDY = "W3_FRESH_HETEROSKEDASTIC_AR1_RESTUDENTIZATION_R2"
SEED = 2026101263
BLOCKS = 24
UNIT_COUNTS = (36, 144)
DESIGNS = ("curve", "participant")
REGIMES = ("iid", "heteroskedastic", "ar1", "heteroskedastic_ar1")
WILD_DRAWS = 199
CONFIDENCE = .90
TEMPORAL_RHO = .70
MAX_N = max(UNIT_COUNTS)
ORACLE_ATOL = 2e-10


def source(block: int, design: str, n: int, regime: str):
    if type(block) is not int or block not in range(BLOCKS):
        raise ValueError("independent generating block outside ledger")
    if design not in DESIGNS or n not in UNIT_COUNTS or regime not in REGIMES:
        raise ValueError("unplanned design, independent-unit count or regime")
    trials = 1 if design == "curve" else 3
    rng = np.random.default_rng(SEED + 17881 * block +
                                (0 if design == "curve" else 1))
    x = rng.uniform(-.95, .95, size=MAX_N)
    truth = truth_coefficients()
    means = truth[0][None] + x[:, None, None] * truth[1][None]
    person_z = rng.normal(size=(MAX_N, 1, len(DIMS)))
    trial_z = rng.normal(size=(MAX_N, trials, len(TIME), len(DIMS)))

    if regime in ("ar1", "heteroskedastic_ar1"):
        trial_errors = np.empty_like(trial_z)
        trial_errors[:, :, 0, :] = trial_z[:, :, 0, :]
        for t in range(1, len(TIME)):
            trial_errors[:, :, t, :] = (
                TEMPORAL_RHO * trial_errors[:, :, t - 1, :]
                + np.sqrt(1 - TEMPORAL_RHO**2) * trial_z[:, :, t, :]
            )
    else:
        trial_errors = trial_z

    if regime in ("heteroskedastic", "heteroskedastic_ar1"):
        # Exogenous predictor-dependent SD, distinct from a mean effect.
        scale = .60 + 1.20 * (x + .95) / 1.90
    else:
        scale = np.ones(MAX_N)

    participant_effect = np.zeros_like(means)
    if design == "participant":
        participant_effect = (
            .065 * scale[:, None, None] * person_z *
            (1 + .35 * TIME[None, :, None])
        )

    observed = (
        means[:, None, :, :] + participant_effect[:, None, :, :]
        + .04 * scale[:, None, None, None] * trial_errors
    )[:n]
    values = observed.reshape(n * trials, len(TIME), len(DIMS))
    ids = tuple(f"P{i:03d}-T{j:02d}" for i in range(n) for j in range(trials))
    meta = pd.DataFrame({
        "participant_id": [f"P{i:03d}" for i in range(n) for _ in range(trials)],
        "trial_id": [j for _ in range(n) for j in range(trials)],
    })
    ts = TrajectorySet(
        time=TIME.copy(), values=values, curve_ids=ids,
        dimension_names=DIMS, coordinate_system="normalized", time_unit="s",
        metadata=meta,
        provenance={"study": STUDY, "simulation": True,
                    "source_block": block, "regime": regime,
                    "independent_unit": design},
    )
    df = pd.DataFrame({"curve_id": ids, "condition": np.repeat(x[:n], trials)})
    X = np.column_stack((np.ones(n), x[:n]))
    Y = observed.mean(axis=1)
    return ts, df, truth, X, Y


def weights(block: int, design: str, n: int):
    if design not in DESIGNS or n not in UNIT_COUNTS:
        raise ValueError("unplanned unit contract")
    rng = np.random.default_rng(
        SEED + 31667 * block + (751 if design == "curve" else 959)
    )
    # Same 199x144 random source in all regimes and nested n values.
    return rng.choice(np.array([-1., 1.]), size=(WILD_DRAWS, MAX_N))[:, :n]


def fit_case(block: int, design: str, n: int, regime: str):
    case = {
        "study": STUDY, "block": block, "design": design, "n_units": n,
        "regime": regime, "status": "failed", "exception": None,
        "source_curves": n * (1 if design == "curve" else 3),
        "source_is_simulated": True, "nested_source_inference_units": True,
        "fixed_contains_slope_truth": None,
        "refitted_contains_slope_truth": None,
        "truth_studentized_slope_supremum": None,
        "fixed_critical": None, "refitted_critical": None,
        "fixed_median_slope_band_width": None,
        "refitted_median_slope_band_width": None,
        "pointwise_slope_mean_cell_inclusion": None,
        "maximum_beta_oracle_error": None, "maximum_hc1_oracle_error": None,
        "matched_package_fixed_band": False,
        "calibration_qualified": False, "release_authorized": False,
    }
    try:
        ts, design_df, truth, X, Y = source(block, design, n, regime)
        config = FunctionOnScalarWorkflowConfig(
            predictors=("condition",), dimensions=DIMS, unit=design,
            participant_column="participant_id" if design == "participant" else None,
        )
        fit = run_function_on_scalar_workflow(ts, design_df, config=config).fit
        beta, se = independent_hc1_oracle(X, Y)
        beta_error = float(np.max(np.abs(beta - fit.coefficients)))
        se_error = float(np.max(np.abs(se - fit.standard_errors)))
        if beta_error > ORACLE_ATOL or se_error > ORACLE_ATOL:
            raise ValueError("independent coefficient/HC1 implementation mismatch")
        if fit.unit != design or len(fit.unit_ids) != n:
            raise ValueError("pseudoreplication: incorrect inference-unit contract")

        w = weights(block, design, n)
        fixed, rest, independent_se = independent_restudentized_maxima(X, Y, w)
        critical_fixed = float(np.quantile(fixed, CONFIDENCE, method="higher"))
        critical_rest = float(np.quantile(rest, CONFIDENCE, method="higher"))

        # Independently constructed, exactly matched pseudo-response coefficients
        # are sent to the ACTUAL package band implementation for source verification.
        proj = np.linalg.inv(X.T @ X) @ X.T
        pseudo = (fit.fitted_functions[None]
                  + w[:, :, None, None] * fit.residual_functions[None])
        beta_star = np.einsum("pn,bntd->bptd", proj, pseudo, optimize=True)
        bootstrap = FunctionOnScalarBootstrapResult(
            reference=fit, bootstrap_coefficients=beta_star,
            multipliers=w, multiplier="rademacher", random_state=None,
            provenance={"source_study": STUDY, "matched_weights": True},
        )
        band = function_on_scalar_simultaneous_bands(
            bootstrap, confidence_level=CONFIDENCE,
            simultaneous_scope="coefficient",
        )
        if not np.isclose(critical_fixed, band.critical_values[1],
                          atol=ORACLE_ATOL, rtol=0):
            raise ValueError("actual package fixed-reference band mismatch")
        if not np.allclose(independent_se, se, atol=ORACLE_ATOL, rtol=0):
            raise ValueError("independently studentized base SE mismatch")

        truth_stat = float(np.max(np.abs((beta[1] - truth[1]) / se[1])))
        z = 1.6448536269514722
        pointwise = np.abs((beta[1] - truth[1]) / se[1]) <= z
        case.update(
            status="ok", maximum_beta_oracle_error=beta_error,
            maximum_hc1_oracle_error=se_error,
            fixed_critical=critical_fixed, refitted_critical=critical_rest,
            fixed_contains_slope_truth=bool(truth_stat <= critical_fixed),
            refitted_contains_slope_truth=bool(truth_stat <= critical_rest),
            truth_studentized_slope_supremum=truth_stat,
            fixed_median_slope_band_width=float(np.median(2 * critical_fixed * se[1])),
            refitted_median_slope_band_width=float(np.median(2 * critical_rest * se[1])),
            pointwise_slope_mean_cell_inclusion=float(np.mean(pointwise)),
            matched_package_fixed_band=True,
        )
    except Exception as exc:
        case["exception"] = {"type": type(exc).__name__,
                             "message": str(exc)[:900]}
    return case


def audit(rows):
    expected = {(b,d,n,r) for b in range(BLOCKS)
                for d in DESIGNS for n in UNIT_COUNTS for r in REGIMES}
    keys = [(x["block"],x["design"],x["n_units"],x["regime"]) for x in rows]
    if len(set(keys)) != len(keys) or not set(keys).issubset(expected):
        raise ValueError("duplicate/undeclared generating case")
    missing = sorted(f"{b}:{d}:{n}:{r}" for b,d,n,r in expected-set(keys))
    completed = [x for x in rows if x["status"]=="ok"]
    grouped = {}
    for d in DESIGNS:
        grouped[d] = {}
        for n in UNIT_COUNTS:
            grouped[d][str(n)] = {}
            for regime in REGIMES:
                cases=[x for x in completed if x["design"]==d
                      and x["n_units"]==n and x["regime"]==regime]
                methods={}
                for name,prefix in (("fixed","fixed"),("refitted","refitted")):
                    k=sum(x[f"{prefix}_contains_slope_truth"] for x in cases)
                    methods[name]={
                        "truth_included":int(k), "completed_denominator":len(cases),
                        "attempted_denominator":BLOCKS,
                        "attempted_inclusive_rate":k/BLOCKS,
                        "wilson95_mc_completed":wilson(k,len(cases)),
                        "mean_critical":float(np.mean([x[f"{prefix}_critical"]
                                           for x in cases])) if cases else None,
                        "mean_median_slope_band_width":float(np.mean([
                            x[f"{prefix}_median_slope_band_width"]
                            for x in cases])) if cases else None,
                    }
                grouped[d][str(n)][regime]={
                    "completed":len(cases),
                    "methods":methods,
                    "truth_inclusion_switched":sum(
                        x["fixed_contains_slope_truth"] !=
                        x["refitted_contains_slope_truth"] for x in cases),
                    "mean_critical_refitted_minus_fixed":float(np.mean([
                        x["refitted_critical"] - x["fixed_critical"]
                        for x in cases])) if cases else None,
                }
    return {
        "study":STUDY, "fresh_seed":SEED, "independent_blocks_per_design":BLOCKS,
        "source_block_is_independent_replication_unit":True,
        "same_block_n_and_regimes_are_correlated":True,
        "generating_regimes":list(REGIMES), "n_independent_units":list(UNIT_COUNTS),
        "planned_cases":len(expected), "source_case_rows":len(rows),
        "completed_cases":len(completed), "fitting_or_contract_failures":
            len(rows)-len(completed), "missing_cases":missing,
        "bootstrap_draws":WILD_DRAWS, "temporal_ar1_rho":TEMPORAL_RHO,
        "nominal_coverage":CONFIDENCE, "groups":grouped,
        "no_statistical_method_selected":True, "calibration_qualified":False,
        "release_authorized":False,
    }


def original_figure(audit_result, target):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes=plt.subplots(1,2,figsize=(13,4),sharey=True)
    for axis, design in zip(axes,DESIGNS):
        for n,marker in ((36,"o"),(144,"s")):
            for method,colour,offset in (("fixed","C0",-.08),("refitted","C1",.08)):
                y=[audit_result["groups"][design][str(n)][regime]["methods"][method][
                    "attempted_inclusive_rate"] for regime in REGIMES]
                xs=np.arange(len(REGIMES))+(offset+(0 if n==36 else .20))
                axis.plot(xs,y,marker=marker,linestyle="--" if n==36 else "-",
                          color=colour,label=f"{method} n={n}")
        axis.axhline(CONFIDENCE,color="black",linestyle=":",label="nominal 90%")
        axis.set_xticks(np.arange(len(REGIMES))+0.10,
                        ["IID","Hetero","AR(1)","Joint"])
        axis.set_ylim(0,1.03)
        axis.set_title(f"{design}: independent-unit coverage")
        axis.set_xlabel("Error structure")
        axis.legend(fontsize=7)
    axes[0].set_ylabel("Whole-slope-function truth inclusion (24 blocks)")
    fig.suptitle("W3 fixed versus refitted HC1: exploratory fresh-block stress")
    fig.tight_layout()
    target.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(target,format="svg",metadata={"Date":None})
    plt.close(fig)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    rows=[fit_case(b,d,n,r) for b in range(BLOCKS)
          for d in DESIGNS for n in UNIT_COUNTS for r in REGIMES]
    result=audit(rows)
    for name,data in (("case-ledger.json",rows),("evidence.json",result)):
        (args.out/name).write_text(json.dumps(data,indent=2,sort_keys=True)+"\n")
    original_figure(result,args.out/"source-stress-coverage.svg")
    (args.out/"source-commit.txt").write_text(os.getenv("GITHUB_SHA","unverified-local")+"\n")
    files=("case-ledger.json","evidence.json","source-stress-coverage.svg","source-commit.txt")
    (args.out/"SHA256SUMS").write_text("".join(
        sha256((args.out/f).read_bytes()).hexdigest()+f"  {f}\n" for f in files))
    print("W3 FRESH HETEROSKEDASTIC AR1 STUDY:",json.dumps(result,sort_keys=True))
    if result["fitting_or_contract_failures"] or result["missing_cases"]:
        raise SystemExit("Original case failures preserved; source audit incomplete")
    # Scientific undercoverage is a retained outcome, not a CI nonpass.


if __name__=="__main__":
    main()
