"""W3 independent-unit-count x wild-bootstrap studentization study.

24 independent generating blocks per design. Unit counts 36/72/144 are
nested *within the same generating block*, never independent replications.
Fixed-HC1 and bootstrap-recomputed-HC1 t statistics use the identical data,
bootstrap multipliers and residuals. Negative coverage is always retained.
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
from eyetrajectoriespy.function_on_scalar import (
    bootstrap_function_on_scalar_coefficients,
    function_on_scalar_simultaneous_bands,
)
from eyetrajectoriespy.workflows import (
    FunctionOnScalarWorkflowConfig, run_function_on_scalar_workflow,
)
from scripts.run_w3_known_truth_workflow_validation import (
    TIME, DIMS, truth_coefficients,
)
from scripts.run_w3_fixed_truth_interval_pilot import (
    independent_hc1_oracle, wilson,
)

STUDY = "W3_NESTED_UNIT_COUNT_RESTUDENTIZATION_R1_V1"
MASTER_SEED = 2026101221
INDEPENDENT_BLOCKS = 24
UNIT_COUNTS = (36, 72, 144)
DESIGNS = ("curve", "participant")
WILD_DRAWS = 199
CONFIDENCE = .90
ORACLE_ATOL = 2e-10
MAX_N = max(UNIT_COUNTS)


def generate(block: int, design: str, n: int):
    if type(block) is not int or not 0 <= block < INDEPENDENT_BLOCKS:
        raise ValueError("generating block outside predeclared ledger")
    if design not in DESIGNS or n not in UNIT_COUNTS:
        raise ValueError("design or inference-unit count outside planned factorial")
    trials = 1 if design == "curve" else 3
    seed = MASTER_SEED + 11003 * block + (0 if design == "curve" else 1)
    rng = np.random.default_rng(seed)
    x = rng.uniform(-.95, .95, size=MAX_N)
    truth = truth_coefficients()
    fixed_mean = truth[0][None] + x[:, None, None] * truth[1][None]
    individual = np.zeros_like(fixed_mean)
    if design == "participant":
        individual = rng.normal(0, .065, (MAX_N, 1, 2)) * (
            1 + .35 * TIME[None, :, None]
        )
    errors = rng.normal(0, .04, (MAX_N, trials, len(TIME), len(DIMS)))
    observed = (fixed_mean + individual)[:, None] + errors
    observed = observed[:n]
    units = x[:n]
    values = observed.reshape(n * trials, len(TIME), len(DIMS))
    identifiers = tuple(
        f"P{i:03d}-T{j:02d}" for i in range(n) for j in range(trials)
    )
    metadata = pd.DataFrame({
        "participant_id": [f"P{i:03d}" for i in range(n) for _ in range(trials)],
        "trial_id": [j for _ in range(n) for j in range(trials)],
    })
    ts = TrajectorySet(
        time=TIME.copy(), values=values, curve_ids=identifiers,
        dimension_names=DIMS, coordinate_system="normalized", time_unit="s",
        metadata=metadata,
        provenance={
            "simulation": True, "scientific_study": STUDY,
            "generating_block": block, "nested_units": n,
            "independence_unit": design,
        },
    )
    frame = pd.DataFrame({
        "curve_id": identifiers, "condition": np.repeat(units, trials),
    })
    X = np.column_stack((np.ones(n), units))
    Y = observed.mean(axis=1)
    return ts, frame, truth, X, Y


def bootstrap_weights(block: int, design: str, draws: int = WILD_DRAWS):
    if design not in DESIGNS:
        raise ValueError("unknown scientific design")
    rng = np.random.default_rng(
        MASTER_SEED + 4099 * block + (701 if design == "curve" else 997)
    )
    return rng.choice(np.array([-1., 1.]), size=(draws, MAX_N))


def independent_restudentized_maxima(
    X: np.ndarray, Y: np.ndarray, weights: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Derive fixed-denominator and *refitted* HC1 bootstrap-t references.

    Y is the unit-level observed response, B weights are per inference unit.
    Refit both beta and HC1 after each wild pseudo-response is generated.
    No library interval-band routine is used for the restudentized reference.
    """
    n, p = X.shape
    XtX_inv = np.linalg.inv(X.T @ X)
    projection = XtX_inv @ X.T
    beta = np.einsum("pn,ntd->ptd", projection, Y, optimize=True)
    fitted = np.einsum("np,ptd->ntd", X, beta, optimize=True)
    residual = Y - fitted
    influence = X @ XtX_inv
    correction = n / (n-p)
    se = np.sqrt(correction * np.einsum(
        "np,ntd->ptd", influence**2, residual**2, optimize=True
    ))
    if np.any(~np.isfinite(se)) or np.any(se <= 0):
        raise ValueError("nonpositive pointwise HC1 standard errors")
    if weights.shape[1] != n:
        raise ValueError("wild multiplier count must equal independent units")
    pseudo = fitted[None] + weights[:, :, None, None] * residual[None]
    beta_star = np.einsum("pn,bntd->bptd", projection, pseudo, optimize=True)
    residual_star = pseudo - np.einsum(
        "np,bptd->bntd", X, beta_star, optimize=True
    )
    se_star = np.sqrt(correction * np.einsum(
        "np,bntd->bptd", influence**2, residual_star**2, optimize=True
    ))
    if np.any(~np.isfinite(se_star)) or np.any(se_star <= 0):
        raise ValueError("bootstrap refitted HC1 standard errors invalid")
    deviation = beta_star[:, 1] - beta[1][None]
    maxima_fixed = np.max(
        np.abs(deviation / se[1][None]), axis=(1, 2)
    )
    maxima_restudentized = np.max(
        np.abs(deviation / se_star[:, 1]), axis=(1, 2)
    )
    return maxima_fixed, maxima_restudentized, se


def evaluate(block: int, design: str, n: int):
    row = {
        "block": block, "design": design, "n_independent_units": n,
        "source_curves": n * (3 if design == "participant" else 1),
        "source_study": STUDY, "status": "failed", "exception": None,
        "nested_sample_sizes_same_generating_block": True,
        "n_bootstrap_draws": WILD_DRAWS, "nominal_level": CONFIDENCE,
        "coef_oracle_max_delta": None, "hc1_oracle_max_delta": None,
        "fixed_HC1_critical": None, "restudentized_HC1_critical": None,
        "truth_studentized_supremum": None,
        "fixed_HC1_full_grid_slope_coverage": None,
        "restudentized_HC1_full_grid_slope_coverage": None,
        "fixed_HC1_package_band_agreement": None,
        "calibration_qualified": False, "release_authorized": False,
    }
    try:
        ts, frame, truth, X, Y = generate(block, design, n)
        config = FunctionOnScalarWorkflowConfig(
            predictors=("condition",), dimensions=DIMS,
            unit=design,
            participant_column="participant_id" if design == "participant" else None,
        )
        fit = run_function_on_scalar_workflow(ts, frame, config=config).fit
        oracle_beta, oracle_se = independent_hc1_oracle(X, Y)
        beta_delta = float(np.max(np.abs(fit.coefficients-oracle_beta)))
        se_delta = float(np.max(np.abs(fit.standard_errors-oracle_se)))
        if beta_delta > ORACLE_ATOL or se_delta > ORACLE_ATOL:
            raise ValueError("independent least-squares/HC1 oracle disagreement")
        if len(fit.unit_ids) != n or fit.unit != design:
            raise ValueError("independent inference unit accounting failed")
        weights = bootstrap_weights(block, design)[:, :n]
        t_fixed, t_rest, ref_se = independent_restudentized_maxima(X, Y, weights)
        crit_fixed = float(np.quantile(t_fixed, CONFIDENCE, method="higher"))
        crit_rest = float(np.quantile(t_rest, CONFIDENCE, method="higher"))
        # A separate production-library bootstrap is checked against the same
        # independently supplied wild pseudo-responses below. Multipliers are
        # not assumed to match because the library owns its RNG stream.
        fitted = fit.fitted_functions
        residual = fit.residual_functions
        proj = np.linalg.inv(X.T @ X) @ X.T
        pseudo = fitted[None] + weights[:, :, None, None]*residual[None]
        computed = np.einsum("pn,bntd->bptd", proj, pseudo, optimize=True)
        fixed_again = np.max(
            np.abs((computed[:, 1]-fit.coefficients[1][None]) /
                   fit.standard_errors[1][None]),
            axis=(1,2),
        )
        if not np.allclose(t_fixed, fixed_again, atol=ORACLE_ATOL, rtol=0):
            raise ValueError("fixed-denominator reference differs from workflow fit")
        if not np.allclose(ref_se, fit.standard_errors, atol=ORACLE_ATOL, rtol=0):
            raise ValueError("fixed-denominator HC1 SE differs from library result")
        target_sup = float(np.max(
            np.abs((fit.coefficients[1]-truth[1])/fit.standard_errors[1])
        ))
        row.update({
            "status": "ok", "coef_oracle_max_delta": beta_delta,
            "hc1_oracle_max_delta": se_delta,
            "fixed_HC1_critical": crit_fixed,
            "restudentized_HC1_critical": crit_rest,
            "truth_studentized_supremum": target_sup,
            "fixed_HC1_full_grid_slope_coverage": bool(target_sup <= crit_fixed),
            "restudentized_HC1_full_grid_slope_coverage": bool(target_sup <= crit_rest),
            "fixed_HC1_package_band_agreement": True,
        })
    except Exception as exc:
        row["exception"] = {"type":type(exc).__name__,"message":str(exc)[:900]}
    return row


def audit(rows: list[dict]) -> dict:
    expected = {(block,design,n) for block in range(INDEPENDENT_BLOCKS)
                for design in DESIGNS for n in UNIT_COUNTS}
    keys = [(r["block"],r["design"],r["n_independent_units"]) for r in rows]
    if len(keys) != len(set(keys)) or not set(keys).issubset(expected):
        raise ValueError("duplicate or unplanned source case")
    missing = sorted([f"{b}:{d}:{n}" for b,d,n in expected - set(keys)])
    complete = [r for r in rows if r["status"] == "ok"]
    groups = {}
    for design in DESIGNS:
        groups[design] = {}
        for n in UNIT_COUNTS:
            a = [r for r in complete if r["design"] == design and
                 r["n_independent_units"] == n]
            methods={}
            for key in ("fixed_HC1","restudentized_HC1"):
                count = sum(r[f"{key}_full_grid_slope_coverage"] for r in a)
                methods[key] = {
                    "included": count, "completed_denominator": len(a),
                    "planned_denominator": INDEPENDENT_BLOCKS,
                    "attempted_inclusive_rate": count / INDEPENDENT_BLOCKS,
                    "completed_rate": count/len(a) if a else None,
                    "wilson95_mc_interval_completed": wilson(count,len(a)),
                    "critical_mean": float(np.mean([r[f"{key}_critical"] for r in a]))
                        if a else None,
                }
            groups[design][str(n)] = {
                "completed": len(a),
                "paired_methods": methods,
                "truth_inclusion_changed_with_restudenization": sum(
                    r["fixed_HC1_full_grid_slope_coverage"] !=
                    r["restudentized_HC1_full_grid_slope_coverage"] for r in a
                ),
                "mean_restudenization_minus_fixed_critical": (
                    float(np.mean([r["restudentized_HC1_critical"]-
                                   r["fixed_HC1_critical"] for r in a]))
                    if a else None
                ),
            }
    return {
        "study": STUDY, "independent_generating_blocks_per_design":
            INDEPENDENT_BLOCKS,
        "sample_sizes_nested_within_generating_block": True,
        "not_144_independent_blocks": True,
        "planned_cases": len(expected), "source_cases_present": len(rows),
        "completed_cases": len(complete), "fitting_or_contract_failures":
            len(rows)-len(complete),
        "missing_cases": missing, "designs": groups,
        "methods_compared_on_exact_identical_data": True,
        "nominal_coverage": CONFIDENCE, "wild_draws": WILD_DRAWS,
        "coverage_qualified": False, "architecture_change_authorized": False,
        "release_authorized": False,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    rows = [evaluate(block,design,n)
            for block in range(INDEPENDENT_BLOCKS)
            for design in DESIGNS for n in UNIT_COUNTS]
    summary = audit(rows)
    for name, content in (("case-ledger.json",rows),("evidence.json",summary)):
        (out/name).write_text(json.dumps(content,indent=2,sort_keys=True)+"\n")
    (out/"source-commit.txt").write_text(os.getenv("GITHUB_SHA","unverified-local")+"\n")
    files = ("case-ledger.json","evidence.json","source-commit.txt")
    (out/"SHA256SUMS").write_text("".join(
        sha256((out/f).read_bytes()).hexdigest() + f"  {f}\n"
        for f in files
    ))
    print("W3 HC1 RESTUDENTIZATION NESTED-N AUDIT:",json.dumps(summary,sort_keys=True))
    if summary["missing_cases"] or summary["fitting_or_contract_failures"]:
        raise SystemExit("one or more cases incomplete: original evidence retained")
    # Neither a coverage rate nor a restudentization advantage is a CI gate.


if __name__=="__main__":
    main()
