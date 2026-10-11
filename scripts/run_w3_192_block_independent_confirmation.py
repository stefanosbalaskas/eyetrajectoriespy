"""Fresh 192-block W3 fixed-HC1 versus refitted-HC1 confirmation study.

This work uses a new independent seed family after pilot R2. Within each
generating block IID and joint heteroskedastic AR(1) regimes are paired, and
fixed-HC1 versus bootstrap-t share the *identical* wild pseudo-responses.
Two scientific designs have distinct sources. The 768 planned fits are NOT
768 exchangeable independent datasets. No inference/release promotion.
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

STUDY = "W3_FRESH_192_BLOCK_CONFIRMATION_R3"
MASTER_SEED = 202610122177
BLOCKS = 192
DESIGNS = ("curve", "participant")
REGIMES = ("iid", "heteroskedastic_ar1")
INDEPENDENT_UNITS = 36
TRIALS_PARTICIPANT = 3
RHO = .70
BOOTSTRAP_DRAWS = 199
CONFIDENCE = .90
BLOCK_BOOTSTRAP_DRAWS = 2000
ORACLE_ATOL = 2e-10


def fresh_source(block: int, design: str, regime: str):
    if type(block) is not int or not 0 <= block < BLOCKS:
        raise ValueError("block outside prespecified fresh independent ledger")
    if design not in DESIGNS or regime not in REGIMES:
        raise ValueError("unplanned scientific design/regime")
    n = INDEPENDENT_UNITS
    trials = 1 if design == "curve" else TRIALS_PARTICIPANT
    rng = np.random.default_rng(
        MASTER_SEED + 17939 * block + (0 if design == "curve" else 1)
    )
    x = rng.uniform(-.95, .95, size=n)
    truth = truth_coefficients()
    mean = truth[0][None] + x[:, None, None] * truth[1][None]
    participant_z = rng.normal(size=(n, 1, len(DIMS)))
    innovations = rng.normal(size=(n, trials, len(TIME), len(DIMS)))
    if regime == "heteroskedastic_ar1":
        errors = np.empty_like(innovations)
        errors[:, :, 0, :] = innovations[:, :, 0, :]
        for t in range(1, len(TIME)):
            errors[:, :, t, :] = (
                RHO * errors[:, :, t - 1, :]
                + np.sqrt(1 - RHO**2) * innovations[:, :, t, :]
            )
        scale = .60 + 1.20 * (x + .95) / 1.90
    else:
        errors = innovations
        scale = np.ones(n)
    participant_effect = np.zeros_like(mean)
    if design == "participant":
        participant_effect = (
            .065 * scale[:, None, None] * participant_z *
            (1 + .35 * TIME[None, :, None])
        )
    Y = mean[:, None, :, :] + participant_effect[:, None, :, :] + (
        .04 * scale[:, None, None, None] * errors
    )
    flat = Y.reshape(n * trials, len(TIME), len(DIMS))
    ids = tuple(
        f"P{i:03d}-T{j:02d}" for i in range(n) for j in range(trials)
    )
    metadata = pd.DataFrame({
        "participant_id": [f"P{i:03d}" for i in range(n) for _ in range(trials)],
        "trial_id": [j for _ in range(n) for j in range(trials)],
    })
    trajectories = TrajectorySet(
        time=TIME.copy(), values=flat, curve_ids=ids,
        dimension_names=DIMS, coordinate_system="normalized",
        time_unit="s", metadata=metadata,
        provenance={"study": STUDY, "simulated": True, "block": block,
                    "source_design": design, "regime": regime},
    )
    frame = pd.DataFrame({"curve_id": ids, "condition": np.repeat(x, trials)})
    X = np.column_stack((np.ones(n), x))
    unit_response = Y.mean(axis=1)
    return trajectories, frame, truth, X, unit_response


def shared_weights(block: int, design: str):
    if type(block) is not int or not 0 <= block < BLOCKS or design not in DESIGNS:
        raise ValueError("unplanned bootstrap source")
    rng = np.random.default_rng(
        MASTER_SEED + 31741 * block + (823 if design == "curve" else 1021)
    )
    return rng.choice(np.array([-1., 1.]), size=(BOOTSTRAP_DRAWS, INDEPENDENT_UNITS))


def evaluate(block: int, design: str, regime: str):
    row = {
        "study": STUDY, "block": block, "design": design, "regime": regime,
        "status": "failed", "exception": None,
        "n_source_curves": INDEPENDENT_UNITS * (
            1 if design == "curve" else TRIALS_PARTICIPANT
        ),
        "n_independent_inference_units": INDEPENDENT_UNITS,
        "same_seed_innovations_across_regimes": True,
        "same_wild_pseudo_response_within_reference_comparison": True,
        "beta_oracle_max_abs": None, "hc1_oracle_max_abs": None,
        "fixed_critical": None, "restudentized_critical": None,
        "fixed_truth_included": None, "restudentized_truth_included": None,
        "fixed_median_slope_width": None, "restudentized_median_slope_width": None,
        "pointwise_slope_cell_inclusion": None,
        "package_fixed_band_checked": False,
        "calibration_qualified": False, "release_authorized": False,
    }
    try:
        ts, frame, truth, X, Y = fresh_source(block, design, regime)
        cfg = FunctionOnScalarWorkflowConfig(
            predictors=("condition",), dimensions=DIMS, unit=design,
            participant_column="participant_id" if design == "participant" else None,
        )
        fit = run_function_on_scalar_workflow(ts, frame, config=cfg).fit
        beta, independent_se = independent_hc1_oracle(X, Y)
        beta_delta = float(np.max(np.abs(fit.coefficients - beta)))
        se_delta = float(np.max(np.abs(fit.standard_errors - independent_se)))
        if beta_delta > ORACLE_ATOL or se_delta > ORACLE_ATOL:
            raise ValueError("independent OLS/HC1 oracle mismatch")
        if fit.unit != design or len(fit.unit_ids) != INDEPENDENT_UNITS:
            raise ValueError("incorrect independent-unit contract")

        w = shared_weights(block, design)
        fixed_t, rest_t, oracle_se = independent_restudentized_maxima(X, Y, w)
        fixed_critical = float(np.quantile(fixed_t, CONFIDENCE, method="higher"))
        rest_critical = float(np.quantile(rest_t, CONFIDENCE, method="higher"))
        if not np.allclose(oracle_se, independent_se, atol=ORACLE_ATOL, rtol=0):
            raise ValueError("bootstrap reference original SE mismatch")
        projector = np.linalg.inv(X.T @ X) @ X.T
        pseudo = (
            fit.fitted_functions[None]
            + w[:, :, None, None] * fit.residual_functions[None]
        )
        beta_star = np.einsum("pn,bntd->bptd", projector, pseudo, optimize=True)
        bundle = FunctionOnScalarBootstrapResult(
            reference=fit, bootstrap_coefficients=beta_star,
            multipliers=w, multiplier="rademacher", random_state=None,
            provenance={"study": STUDY, "matched_wild_weights": True},
        )
        band = function_on_scalar_simultaneous_bands(
            bundle, confidence_level=CONFIDENCE, simultaneous_scope="coefficient"
        )
        if not np.isclose(
            band.critical_values[1], fixed_critical, atol=ORACLE_ATOL, rtol=0
        ):
            raise ValueError("library fixed-HC1 band differs from independent reference")
        if np.any(independent_se[1] <= 0):
            raise ValueError("zero positive scientific slope SE")
        truth_sup = float(np.max(
            np.abs((fit.coefficients[1] - truth[1]) / independent_se[1])
        ))
        z = 1.6448536269514722
        row.update({
            "status": "ok", "beta_oracle_max_abs": beta_delta,
            "hc1_oracle_max_abs": se_delta,
            "fixed_critical": fixed_critical,
            "restudentized_critical": rest_critical,
            "fixed_truth_included": bool(truth_sup <= fixed_critical),
            "restudentized_truth_included": bool(truth_sup <= rest_critical),
            "fixed_median_slope_width": float(
                np.median(2 * fixed_critical * independent_se[1])
            ),
            "restudentized_median_slope_width": float(
                np.median(2 * rest_critical * independent_se[1])
            ),
            "pointwise_slope_cell_inclusion": float(np.mean(
                np.abs((fit.coefficients[1] - truth[1]) / independent_se[1]) <= z
            )),
            "package_fixed_band_checked": True,
        })
    except Exception as exc:
        row["exception"] = {"type": type(exc).__name__, "message": str(exc)[:900]}
    return row


def paired_block_bootstrap_interval(pairs, *, seed: int, draws: int = BLOCK_BOOTSTRAP_DRAWS):
    """Percentile CI for paired *block-level* truth-inclusion difference.

    Does not treat time cells, bootstrap draws, or paired methods as
    independent datasets. Return null when there are no completed pairs.
    """
    if not pairs:
        return None
    array = np.asarray(pairs, dtype=float)
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(array), size=(draws, len(array)))
    distribution = array[indices].mean(axis=1)
    return [float(v) for v in np.quantile(distribution, [.025, .975])]


def audit(rows):
    expected = {(b, d, r) for b in range(BLOCKS)
                for d in DESIGNS for r in REGIMES}
    keys = [(r["block"],r["design"],r["regime"]) for r in rows]
    if len(set(keys)) != len(keys) or not set(keys).issubset(expected):
        raise ValueError("duplicate or undeclared dataset")
    missing = sorted(f"{b}:{d}:{regime}" for b,d,regime in expected-set(keys))
    complete = [r for r in rows if r["status"] == "ok"]
    by_design = {}
    for i, design in enumerate(DESIGNS):
        by_design[design] = {}
        for j, regime in enumerate(REGIMES):
            data = sorted(
                [r for r in complete if r["design"] == design and r["regime"] == regime],
                key=lambda r: r["block"],
            )
            fixed_count = sum(bool(r["fixed_truth_included"]) for r in data)
            rest_count = sum(bool(r["restudentized_truth_included"]) for r in data)
            pairs = [
                int(bool(r["restudentized_truth_included"]))
                - int(bool(r["fixed_truth_included"]))
                for r in data
            ]
            interval = paired_block_bootstrap_interval(
                pairs, seed=MASTER_SEED + 313 * i + 719 * j
            )
            by_design[design][regime] = {
                "completed": len(data), "attempted": BLOCKS,
                "fixed_truth_inclusion": fixed_count,
                "refitted_truth_inclusion": rest_count,
                "fixed_rate_attempted_denominator": fixed_count/BLOCKS,
                "refitted_rate_attempted_denominator": rest_count/BLOCKS,
                "fixed_wilson95_completed_only": wilson(fixed_count,len(data)),
                "refitted_wilson95_completed_only": wilson(rest_count,len(data)),
                "paired_difference_completed_only": (
                    float(np.mean(pairs)) if pairs else None
                ),
                "paired_difference_block_bootstrap95_completed_only": interval,
                "rescued_by_restudenization": sum(p == 1 for p in pairs),
                "lost_by_restudenization": sum(p == -1 for p in pairs),
                "paired_nonchanges": sum(p == 0 for p in pairs),
                "mean_fixed_critical": (
                    float(np.mean([r["fixed_critical"] for r in data]))
                    if data else None
                ),
                "mean_refitted_critical": (
                    float(np.mean([r["restudentized_critical"] for r in data]))
                    if data else None
                ),
                "mean_median_fixed_width": (
                    float(np.mean([r["fixed_median_slope_width"] for r in data]))
                    if data else None
                ),
                "mean_median_refitted_width": (
                    float(np.mean([r["restudentized_median_slope_width"] for r in data]))
                    if data else None
                ),
                "mean_fraction_pointwise_truth_cells": (
                    float(np.mean([r["pointwise_slope_cell_inclusion"] for r in data]))
                    if data else None
                ),
                "no_failed_dataset_deleted_from_attempted_denominator": (
                    len(data)==BLOCKS
                ),
            }
    return {
        "study": STUDY, "fresh_192_block_seed": MASTER_SEED,
        "independent_blocks_per_design": BLOCKS,
        "within_block_regimes_are_paired": True,
        "number_of_independent_replicates_not_equal_to_cases": True,
        "n_inference_units_per_dataset": INDEPENDENT_UNITS,
        "planned_cases": len(expected), "present_cases": len(rows),
        "completed_cases": len(complete),
        "fitting_or_contract_failures": len(rows)-len(complete),
        "missing_cases": missing, "groups": by_design,
        "nominal_confidence": CONFIDENCE,
        "wild_draws_per_case": BOOTSTRAP_DRAWS,
        "paired_mc_draws": BLOCK_BOOTSTRAP_DRAWS,
        "interval_coverage_qualified": False,
        "research_method_winner_selected": False,
        "release_authorized": False,
    }


def original_figure(report, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(9, 4.2))
    labels = ["Curve IID","Curve joint","Participant IID","Participant joint"]
    ys_fixed = []
    ys_rest = []
    for design in DESIGNS:
        for regime in REGIMES:
            row = report["groups"][design][regime]
            ys_fixed.append(row["fixed_rate_attempted_denominator"])
            ys_rest.append(row["refitted_rate_attempted_denominator"])
    loc=np.arange(len(labels))
    ax.bar(loc - .18, ys_fixed, width=.34,label="Fixed HC1")
    ax.bar(loc + .18, ys_rest, width=.34,label="Refitted HC1 (bootstrap-t)")
    ax.axhline(CONFIDENCE, linestyle="--", color="black", label="Nominal 90%")
    ax.set_ylim(0,1.05)
    ax.set_ylabel("Full-grid known-truth inclusion across 192 datasets")
    ax.set_xticks(loc,labels)
    ax.set_title("W3 independent replication: 90% bands, two source mechanisms")
    ax.legend(fontsize=8)
    fig.tight_layout()
    output.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(output,format="svg",metadata={"Date":None})
    plt.close(fig)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    rows=[evaluate(block,design,regime)
          for block in range(BLOCKS)
          for design in DESIGNS
          for regime in REGIMES]
    evidence=audit(rows)
    for name, obj in (("case-ledger.json", rows),("evidence.json", evidence)):
        (args.out/name).write_text(json.dumps(obj, indent=2, sort_keys=True)+"\n")
    original_figure(evidence, args.out/"source-confirmation.svg")
    (args.out/"source-commit.txt").write_text(
        os.getenv("GITHUB_SHA","unverified-local")+"\n"
    )
    names=("case-ledger.json","evidence.json","source-confirmation.svg","source-commit.txt")
    (args.out/"SHA256SUMS").write_text("".join(
        sha256((args.out/f).read_bytes()).hexdigest()+f"  {f}\n" for f in names
    ))
    print("W3 192 BLOCK INDEPENDENT CONFIRMATION:",json.dumps(evidence,sort_keys=True))
    if evidence["missing_cases"] or evidence["fitting_or_contract_failures"]:
        raise SystemExit("Incomplete original scientific source, failure evidence preserved")
    if evidence["completed_cases"] != evidence["planned_cases"]:
        raise SystemExit("Original scientific source counts incorrect")
    # Deliberately do not set a desired-coverage CI gate; negative findings
    # and any undercoverage are published into the original evidence.


if __name__=="__main__":
    main()
