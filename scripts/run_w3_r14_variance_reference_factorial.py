"""W3 R14: deconfound covariance-scale and reference-quantile choices in R13.

Reproduce the EXACT R13 original source blocks and fitted point estimates. Cross
two variance sources (participant CR1, known conditional Gaussian oracle) with
two critical values (t(47), standard normal). This is a numerical decomposition
on the SAME datasets, not 384 new independent generating blocks, a new fitted
covariance method, or evidence of simultaneous functional calibration.
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
from scipy.stats import norm, t

from scripts.run_w3_r13_exact_r11_conditional_oracle import (
    BLOCKS, COHORTS, MODELS, N_PARTICIPANTS, CONFIDENCE,
    HISTORICAL_SEED, FRESH_SEED, case as r13_case,
    audit as r13_audit, wilson, bootstrap_ci,
)

STUDY = "W3_R14_R13_CROSSED_VARIANCE_CRITICAL_AUDIT_20261013"
METHODS = ("cr1_t", "cr1_normal", "oracle_t", "oracle_normal")
CONTRASTS = {
    "critical_t_minus_normal_at_cr1": ("cr1_t", "cr1_normal"),
    "critical_t_minus_normal_at_oracle": ("oracle_t", "oracle_normal"),
    "oracle_minus_cr1_at_t": ("oracle_t", "cr1_t"),
    "oracle_minus_cr1_at_normal": ("oracle_normal", "cr1_normal"),
}
TOL = 1e-10


def crossed_case(row: dict) -> dict:
    """Preserve a failure or reconstruct all four intervals for a successful R13 fit."""
    result = {
        "study": STUDY, "block": row["block"],
        "cohort": row["cohort"], "model": row["model"],
        "status": "failed", "exception": None, "methods": {},
        "independent_source_block": f'{row["cohort"]}:{row["block"]}',
        "source_is_existing_r13_not_new_replication": True,
        "pointwise_only": True, "release_authorized": False,
    }
    if row.get("status") != "ok":
        result["exception"] = row.get("exception") or {
            "type": "UpstreamSourceFailure", "message": "R13 case did not fit"
        }
        return result
    try:
        if row["cohort"] not in COHORTS or row["model"] not in MODELS:
            raise ValueError("unplanned cohort or basis")
        truth = float(row["known_truth"])
        estimate = float(row["estimate"])
        r13 = row["methods"]
        cr1 = float(r13["participant_cr1_t"]["se"])
        oracle = float(r13["conditional_gaussian_oracle_normal"]["se"])
        if not np.isfinite([truth, estimate, cr1, oracle]).all() or min(cr1, oracle) <= 0:
            raise ValueError("nonfinite or nonpositive source estimate / SE")
        critical = {
            "t": float(t.ppf((1 + CONFIDENCE) / 2, N_PARTICIPANTS - 1)),
            "normal": float(norm.ppf((1 + CONFIDENCE) / 2)),
        }
        se = {"cr1": cr1, "oracle": oracle}
        for variance in ("cr1", "oracle"):
            for reference in ("t", "normal"):
                method = f"{variance}_{reference}"
                half = float(se[variance] * critical[reference])
                result["methods"][method] = {
                    "se": se[variance],
                    "critical": critical[reference],
                    "width": 2 * half,
                    "known_truth_included": bool(abs(estimate - truth) <= half),
                }
        # The diagonal comparisons MUST reproduce original R13 decisions.
        for method, reference in (
            ("cr1_t", "participant_cr1_t"),
            ("oracle_normal", "conditional_gaussian_oracle_normal"),
        ):
            original = r13[reference]
            rerun = result["methods"][method]
            if (not np.isclose(rerun["width"], float(original["width"]),
                               atol=TOL, rtol=0)
                    or rerun["known_truth_included"] != bool(original["known_truth_included"])):
                raise ValueError("R13 original interval was not reproduced")
        result.update({
            "status": "ok", "estimate": estimate, "known_truth": truth,
            "source_cr1_se": cr1, "source_oracle_se": oracle,
            "original_r13_diagnostic_identity_verified": True,
        })
    except Exception as exc:
        result["methods"] = {}
        result["exception"] = {"type": type(exc).__name__, "message": str(exc)[:1000]}
    return result


def audit(rows: list[dict]) -> dict:
    expected = {(b, c, m) for c in COHORTS for b in range(BLOCKS) for m in MODELS}
    keys = [(r["block"], r["cohort"], r["model"]) for r in rows]
    if len(set(keys)) != len(keys) or not set(keys).issubset(expected):
        raise ValueError("duplicate or unplanned R14 source record")
    missing = sorted(f"{b}:{c}:{m}" for b, c, m in expected - set(keys))
    completed = [r for r in rows if r["status"] == "ok"]
    groups = {}
    for cohort in COHORTS:
        groups[cohort] = {}
        for model in MODELS:
            records = sorted(
                (r for r in completed if r["cohort"] == cohort and r["model"] == model),
                key=lambda r: r["block"],
            )
            methods = {}
            for method in METHODS:
                n = len(records)
                k = sum(r["methods"][method]["known_truth_included"] for r in records)
                methods[method] = {
                    "attempted_blocks": BLOCKS, "completed_blocks": n,
                    "truth_inclusion_count": int(k),
                    "pointwise_truth_inclusion_conditional_on_completed": k / n if n else None,
                    "wilson95_completed_block_MC": wilson(k, n),
                    "mean_width": float(np.mean([
                        r["methods"][method]["width"] for r in records
                    ])) if n else None,
                }
            contrasts = {}
            for name, (left, right) in CONTRASTS.items():
                diffs = [
                    int(r["methods"][left]["known_truth_included"]) -
                    int(r["methods"][right]["known_truth_included"])
                    for r in records
                ]
                contrasts[name] = {
                    "paired_inclusion_difference": float(np.mean(diffs)) if diffs else None,
                    "paired_independent_block_bootstrap95": bootstrap_ci(
                        diffs, HISTORICAL_SEED + FRESH_SEED +
                        sum(map(ord, cohort + model + name))
                    ),
                }
            interaction = [
                (int(r["methods"]["oracle_t"]["known_truth_included"]) -
                 int(r["methods"]["oracle_normal"]["known_truth_included"])) -
                (int(r["methods"]["cr1_t"]["known_truth_included"]) -
                 int(r["methods"]["cr1_normal"]["known_truth_included"]))
                for r in records
            ]
            contrasts["variance_by_critical_inclusion_interaction"] = {
                "paired_inclusion_difference_of_differences":
                    float(np.mean(interaction)) if interaction else None,
                "paired_independent_block_bootstrap95": bootstrap_ci(
                    interaction, HISTORICAL_SEED + sum(map(ord, cohort + model))
                ),
            }
            groups[cohort][model] = {
                "attempted_independent_blocks": BLOCKS,
                "completed_blocks": len(records),
                "methods": methods, "paired_within_block_contrasts": contrasts,
            }
    original_reproduced = (
        groups["historical_R11"]["legendre5"]["methods"]["cr1_t"]["truth_inclusion_count"] == 80 and
        groups["historical_R11"]["cubic_spline13"]["methods"]["cr1_t"]["truth_inclusion_count"] == 77
    )
    return {
        "study": STUDY, "original_r13_source_recomputed_unchanged": True,
        "source_historical_seed": HISTORICAL_SEED,
        "source_fresh_seed": FRESH_SEED,
        "independent_generating_blocks_per_cohort": BLOCKS,
        "distinct_independent_source_blocks_across_cohorts": BLOCKS * len(COHORTS),
        "fitted_basis_cases_per_source_block": len(MODELS),
        "planned_cases": len(expected), "recorded_cases": len(rows),
        "completed_cases": len(completed), "failed_cases": len(rows) - len(completed),
        "missing_cases": missing, "groups": groups,
        "original_r11_counts_reproduced": original_reproduced,
        "no_new_independent_source_replications": True,
        "variance_by_critical_factorial_is_descriptive": True,
        "oracle_uses_simulation_known_covariance": True,
        "no_simultaneous_band_inference": True,
        "pointwise_inference_qualified": False,
        "publication_authorized": False, "release_authorized": False,
    }


def plot(audit_result: dict, out: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), sharey=True)
    for ax, cohort in zip(axes, COHORTS):
        for model, marker in zip(MODELS, ("o", "s")):
            values = [
                audit_result["groups"][cohort][model]["methods"][method][
                    "pointwise_truth_inclusion_conditional_on_completed"
                ]
                for method in METHODS
            ]
            ax.plot(range(4), values, marker=marker, label=model)
        ax.axhline(.9, linestyle="--", color="black", linewidth=1)
        ax.set_title(cohort)
        ax.set_xticks(range(4), ("CR1 / t", "CR1 / normal",
                                 "Oracle / t", "Oracle / normal"), rotation=22)
        ax.set_ylim(0, 1)
        ax.set_ylabel("90% pointwise known-truth inclusion (96 blocks)")
        ax.legend(fontsize=8)
    fig.suptitle("R14: cross variance source and reference distribution on unchanged R13 data")
    fig.tight_layout()
    fig.savefig(out, format="svg", metadata={"Date": None})
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    original_rows = [
        r13_case(block, cohort, model)
        for cohort in COHORTS for block in range(BLOCKS) for model in MODELS
    ]
    original_audit = r13_audit(original_rows)
    crossed = [crossed_case(row) for row in original_rows]
    report = audit(crossed)

    for name, value in (
        ("r13-source-case-ledger.json", original_rows),
        ("r13-source-summary.json", original_audit),
        ("r14-crossed-case-ledger.json", crossed),
        ("r14-evidence.json", report),
    ):
        (args.out / name).write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")

    plot(report, args.out / "source-r14-factorial-pointwise.svg")
    (args.out / "source-commit.txt").write_text(
        os.getenv("GITHUB_SHA", "unverified-local") + "\n"
    )
    names = (
        "r13-source-case-ledger.json", "r13-source-summary.json",
        "r14-crossed-case-ledger.json", "r14-evidence.json",
        "source-r14-factorial-pointwise.svg", "source-commit.txt",
    )
    (args.out / "SHA256SUMS").write_text("".join(
        sha256((args.out / name).read_bytes()).hexdigest() + "  " + name + "\n"
        for name in names
    ))
    print("W3 R14 ORIGINAL SOURCE FACTORIAL AUDIT:", json.dumps(report, sort_keys=True))
    if (report["failed_cases"] or report["missing_cases"] or
        original_audit["failed_cases"] or original_audit["missing_cases"] or
        not report["original_r11_counts_reproduced"] or
        not original_audit["historical_counts_reproduced"]):
        raise SystemExit("R14 preserved incomplete original source or failed reproduction")
    # No target-coverage or release readiness gate: negative outcomes must be retained.


if __name__ == "__main__":
    main()
