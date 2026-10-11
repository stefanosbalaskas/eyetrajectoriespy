"""W3 frequentist 90% uncertainty pilot; independent fixed-truth datasets.

This tests *frequentist* inclusion, not posterior/SBC calibration, for observed
grid function-on-scalar inference. All fits/failures and source checksums persist.
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
from scipy.stats import norm

from eyetrajectoriespy import TrajectorySet
from eyetrajectoriespy.function_on_scalar import (
    bootstrap_function_on_scalar_coefficients, function_on_scalar_simultaneous_bands,
)
from eyetrajectoriespy.workflows import FunctionOnScalarWorkflowConfig, run_function_on_scalar_workflow
from scripts.run_w3_known_truth_workflow_validation import TIME, DIMS, truth_coefficients

STUDY = "W3_FIXED_TRUTH_FREQUENTIST_INTERVAL_PILOT_V1"
MASTER_SEED = 2026101207
PLANNED_BLOCKS = 64
DESIGNS = ("curve", "participant")
BOOTSTRAP_DRAWS = 199
CONFIDENCE = .90
ORACLE_ATOL = 2e-10
TIME_SHAPE = (2, len(TIME), len(DIMS))


def simulate(block: int, design: str):
    if type(block) is not int or not 0 <= block < PLANNED_BLOCKS:
        raise ValueError("block outside prespecified independent dataset ledger")
    if design not in DESIGNS:
        raise ValueError("unknown generating design")
    n, trials = (72, 1) if design == "curve" else (36, 3)
    rng = np.random.default_rng(MASTER_SEED + block * 10007 + (0 if design == "curve" else 1))
    condition = rng.uniform(-.95, .95, size=n)
    truth = truth_coefficients()
    mean = truth[0][None] + condition[:, None, None] * truth[1][None]
    participant_effect = np.zeros_like(mean)
    if design == "participant":
        participant_effect = (rng.normal(0, .065, (n, 1, 2))
                              * (1 + .35 * TIME[None, :, None]))
    independent_trial_noise = rng.normal(0, .04, (n, trials, len(TIME), 2))
    observed = (mean + participant_effect)[:, None] + independent_trial_noise
    values = observed.reshape(n * trials, len(TIME), 2)
    ids = tuple(f"P{i:03d}-T{j:02d}" for i in range(n) for j in range(trials))
    metadata = pd.DataFrame({
        "participant_id": [f"P{i:03d}" for i in range(n) for _ in range(trials)],
        "trial_id": [j for _ in range(n) for j in range(trials)],
    })
    trajectories = TrajectorySet(
        time=TIME.copy(), values=values, curve_ids=ids,
        dimension_names=DIMS, coordinate_system="normalized", time_unit="s",
        metadata=metadata, provenance={
            "simulation": True, "study": STUDY, "block": block,
            "independent_unit": design,
        },
    )
    frame = pd.DataFrame({"curve_id": ids, "condition": np.repeat(condition, trials)})
    # The oracle unit is a participant mean when there are repeated trials.
    oracle_y = observed.mean(axis=1)
    X = np.column_stack((np.ones(n), condition))
    return trajectories, frame, truth, X, oracle_y


def independent_hc1_oracle(X, Y):
    """Independent projection and HC1 sandwich; no package private helpers."""
    n, p = X.shape
    flat = Y.reshape(n, -1)
    coefficients = np.linalg.lstsq(X, flat, rcond=None)[0]
    residuals = flat - X @ coefficients
    inv = np.linalg.inv(X.T @ X)
    influences = X @ inv
    variance = n / (n - p) * np.einsum(
        "np,nk->pk", influences**2, residuals**2, optimize=True
    )
    return coefficients.reshape(TIME_SHAPE), np.sqrt(variance).reshape(TIME_SHAPE)


def evaluate(block: int, design: str, *, bootstrap_draws: int = BOOTSTRAP_DRAWS):
    row = {
        "block": block, "design": design, "study": STUDY,
        "completed": False, "exception": None,
        "independent_units": 36 if design == "participant" else 72,
        "source_curves": 108 if design == "participant" else 72,
        "bootstrap_draws": bootstrap_draws, "bootstrap_unit": design,
        "maximum_coefficient_oracle_difference": None,
        "maximum_hc1_oracle_difference": None,
        "slope_pointwise_cell_inclusion_rate": None,
        "slope_pointwise_all_cells_included": None,
        "slope_simultaneous_coefficient_included": None,
        "full_family_simultaneous_included": None,
        "slope_median_pointwise_interval_width": None,
        "slope_median_simultaneous_interval_width": None,
        "slope_hc1_mean_se": None,
        "bootstrap_critical_slope": None,
        "bootstrap_critical_family": None,
        "calibration_qualified": False, "release_authorized": False,
    }
    try:
        gaze, frame, truth, X, oracle_y = simulate(block, design)
        config = FunctionOnScalarWorkflowConfig(
            predictors=("condition",), dimensions=DIMS, unit=design,
            participant_column="participant_id" if design == "participant" else None,
        )
        result = run_function_on_scalar_workflow(gaze, frame, config=config)
        fitted = result.fit
        oracle_beta, oracle_se = independent_hc1_oracle(X, oracle_y)
        if fitted.coefficients.shape != truth.shape or fitted.standard_errors.shape != truth.shape:
            raise ValueError("incompatible parameter and uncertainty shapes")
        if not np.all(np.isfinite(fitted.standard_errors)) or np.any(fitted.standard_errors <= 0):
            raise ValueError("nonpositive/nonfinite HC1 standard error")
        if fitted.unit != design or len(fitted.unit_ids) != len(X):
            raise ValueError("unit-of-analysis contract failed")
        delta_beta = float(np.max(np.abs(fitted.coefficients - oracle_beta)))
        delta_se = float(np.max(np.abs(fitted.standard_errors - oracle_se)))
        if delta_beta > ORACLE_ATOL or delta_se > ORACLE_ATOL:
            raise ValueError("independent coefficient/HC1 numerical oracle disagreement")
        bootstrap = bootstrap_function_on_scalar_coefficients(
            fitted, n_bootstrap=bootstrap_draws, multiplier="rademacher",
            random_state=MASTER_SEED + block * 317 + (11 if design == "curve" else 29),
        )
        if bootstrap.multipliers.shape != (bootstrap_draws, len(X)):
            raise ValueError("bootstrap multipliers count trials instead of inference units")
        coefficient_band = function_on_scalar_simultaneous_bands(
            bootstrap, confidence_level=CONFIDENCE, simultaneous_scope="coefficient"
        )
        family_band = function_on_scalar_simultaneous_bands(
            bootstrap, confidence_level=CONFIDENCE, simultaneous_scope="family"
        )
        if coefficient_band.lower.shape != truth.shape or family_band.lower.shape != truth.shape:
            raise ValueError("band shape contract failed")
        # Independent numerical reference: rederive maximum studentized deviations
        # directly from *stored* bootstrap coefficients, not package critical values.
        deviation = (bootstrap.bootstrap_coefficients - fitted.coefficients[None]) / oracle_se[None]
        slope_max = np.max(np.abs(deviation[:, 1]), axis=(1, 2))
        family_max = np.max(np.abs(deviation), axis=(1, 2, 3))
        oracle_slope_critical = float(np.quantile(slope_max, CONFIDENCE, method="higher"))
        oracle_family_critical = float(np.quantile(family_max, CONFIDENCE, method="higher"))
        if not np.isclose(coefficient_band.critical_values[1], oracle_slope_critical, atol=ORACLE_ATOL):
            raise ValueError("simultaneous slope maximum-statistic reference mismatch")
        if not np.allclose(family_band.critical_values, oracle_family_critical, atol=ORACLE_ATOL):
            raise ValueError("family-wise maximum-statistic reference mismatch")
        z = float(norm.ppf((1 + CONFIDENCE) / 2))
        lower_pt = fitted.coefficients - z * oracle_se
        upper_pt = fitted.coefficients + z * oracle_se
        inside_pointwise = (lower_pt[1] <= truth[1]) & (truth[1] <= upper_pt[1])
        inside_slope = (coefficient_band.lower[1] <= truth[1]) & (truth[1] <= coefficient_band.upper[1])
        inside_family = (family_band.lower <= truth) & (truth <= family_band.upper)
        row.update({
            "completed": True,
            "maximum_coefficient_oracle_difference": delta_beta,
            "maximum_hc1_oracle_difference": delta_se,
            "slope_pointwise_cell_inclusion_rate": float(np.mean(inside_pointwise)),
            "slope_pointwise_all_cells_included": bool(np.all(inside_pointwise)),
            "slope_simultaneous_coefficient_included": bool(np.all(inside_slope)),
            "full_family_simultaneous_included": bool(np.all(inside_family)),
            "slope_median_pointwise_interval_width": float(np.median(2 * z * oracle_se[1])),
            "slope_median_simultaneous_interval_width": float(np.median(
                coefficient_band.upper[1] - coefficient_band.lower[1])),
            "slope_hc1_mean_se": float(np.mean(oracle_se[1])),
            "bootstrap_critical_slope": oracle_slope_critical,
            "bootstrap_critical_family": oracle_family_critical,
        })
    except Exception as error:
        row["exception"] = {"type": type(error).__name__, "message": str(error)[:700]}
    return row


def wilson(k: int, n: int, z: float = 1.95996398454):
    if n <= 0:
        return None
    phat = k / n
    denom = 1 + z*z/n
    mid = (phat + z*z/(2*n))/denom
    half = z*np.sqrt(phat*(1-phat)/n+z*z/(4*n*n))/denom
    # Clamp roundoff at the exact binomial boundary (k=0 or k=n).
    return [float(max(0, min(phat, mid-half))),
            float(min(1, max(phat, mid+half)))]


def audit(rows: list[dict], *, blocks: int):
    if not 1 <= blocks <= PLANNED_BLOCKS:
        raise ValueError("illegal independent block count")
    declared = {(i, d) for i in range(blocks) for d in DESIGNS}
    keys = [(r["block"], r["design"]) for r in rows]
    if len(keys) != len(set(keys)) or not set(keys).issubset(declared):
        raise ValueError("duplicate/undeclared scientific cases")
    missing = sorted(f"{i}:{d}" for i, d in declared-set(keys))
    complete = [r for r in rows if r["completed"]]
    per_design = {}
    for d in DESIGNS:
        sample = [r for r in rows if r["design"] == d]
        observed = [r for r in sample if r["completed"]]
        criteria = {}
        for name in (
            "slope_simultaneous_coefficient_included",
            "full_family_simultaneous_included",
            "slope_pointwise_all_cells_included",
        ):
            successes = sum(bool(r[name]) for r in observed)
            criteria[name] = {
                "truth_inclusion": successes,
                "completed_denominator": len(observed),
                "attempted_denominator": blocks,
                "completed_only_rate": successes/len(observed) if observed else None,
                "attempted_inclusive_rate": successes/blocks,
                "wilson95_interval_completed_only": wilson(successes, len(observed)),
                "missing_or_fitting_failures_not_dropped": len(observed)!=blocks,
            }
        per_design[d] = {
            "attempted": len(sample), "completed": len(observed),
            "numerical_oracle_passes": sum(
                r["maximum_coefficient_oracle_difference"] <= ORACLE_ATOL and
                r["maximum_hc1_oracle_difference"] <= ORACLE_ATOL
                for r in observed
            ),
            "mean_fraction_of_slope_time_dimension_pointwise_cells_included":
                float(np.mean([r["slope_pointwise_cell_inclusion_rate"] for r in observed])) if observed else None,
            "mean_slope_hc1_se": float(np.mean([r["slope_hc1_mean_se"] for r in observed])) if observed else None,
            "slope_simultaneous_width_mean": float(np.mean([
                r["slope_median_simultaneous_interval_width"] for r in observed])) if observed else None,
            "coverage": criteria,
        }
    return {
        "study": STUDY, "planned_independent_generating_blocks": blocks,
        "cases_within_block_not_independent": True, "nominal_confidence": CONFIDENCE,
        "bootstrap_draws_per_case": BOOTSTRAP_DRAWS, "planned_fits": 2*blocks,
        "observed_original_cases": len(rows), "completed_fits": len(complete),
        "missing_cases": missing, "failures": len(rows)-len(complete),
        "design": per_design,
        "status": "complete" if not missing and len(complete)==len(declared) else "incomplete_with_retained_failures",
        "exploratory_fixed_truth_frequentist_coverage_not_general_calibration": True,
        "scientific_coverage_qualification_passed": False, "release_authorized": False,
    }


def plot_summary(summary, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    names = ["curve", "participant"]
    values = [summary["design"][x]["coverage"]["slope_simultaneous_coefficient_included"]["completed_only_rate"] for x in names]
    fig, ax=plt.subplots(figsize=(7.2,4.2))
    for i,(name,value) in enumerate(zip(names,values)):
        interval = summary["design"][name]["coverage"]["slope_simultaneous_coefficient_included"]["wilson95_interval_completed_only"]
        if interval is not None and value is not None:
            ax.errorbar(i,value,yerr=np.array([[value-interval[0]],[interval[1]-value]]),
                        fmt="o",capsize=5,markersize=7,label=None)
        else:
            ax.plot(i,0.0,"x",label="No completed cases" if i == 0 else None)
    ax.axhline(CONFIDENCE,linestyle="--",color="black",label="Nominal 90% (reference)")
    ax.set_xticks(range(2),["Independent curves","Participant means (3 trials)"])
    ax.set_ylim(0,1.05)
    ax.set_ylabel("Simultaneous slope-band truth inclusion over full observed grid")
    ax.set_title("Exploratory 90% simultaneous band coverage (simulation)")
    ax.text(.5,.05,"Wilson 95% intervals across completed fits; failed/missing cases reported separately",ha="center",transform=ax.transAxes,fontsize=8)
    ax.legend(loc="lower left")
    fig.tight_layout()
    path.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(path,format="svg",metadata={"Date":None})
    plt.close(fig)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--blocks",type=int,default=PLANNED_BLOCKS)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    if not 1 <= args.blocks <= PLANNED_BLOCKS:
        parser.error("blocks must lie within 1..64 prespecified generating blocks")
    out=args.out
    out.mkdir(parents=True,exist_ok=True)
    rows=[evaluate(i,d) for i in range(args.blocks) for d in DESIGNS]
    result=audit(rows,blocks=args.blocks)
    for name,obj in [("case-ledger.json",rows),("evidence.json",result)]:
        (out/name).write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")
    plot_summary(result,out/"fixed-truth-coverage.svg")
    (out/"source-commit.txt").write_text(os.getenv("GITHUB_SHA","unverified-local")+"\n")
    sourcefiles=("case-ledger.json","evidence.json","fixed-truth-coverage.svg","source-commit.txt")
    (out/"SHA256SUMS").write_text("".join(
        sha256((out/f).read_bytes()).hexdigest()+f"  {f}\n" for f in sourcefiles))
    print("W3 FIXED TRUTH UNCERTAINTY AUDIT:",json.dumps(result,sort_keys=True))
    if result["status"] != "complete":
        raise SystemExit("scientific source cases incomplete or failed; artifacts retained")
    if any(result["design"][d]["numerical_oracle_passes"] != args.blocks for d in DESIGNS):
        raise SystemExit("HC1 or coefficient oracle mismatch; artifacts retained")
    # Deliberately DO NOT turn coverage under- or over-shoot into a CI failure:
    # it is the subject of this research and may falsify calibration.


if __name__=="__main__":
    main()
