"""R5 stage-0: one new independent 2x2 rank-two generating block.

Each replicate is one independent generating population and twelve-subject
superpopulation. Paired versus asynchronous arms use identical latent truth,
participants, x data, y noise and y counts; four-subject n nests in n=12.
No four-cell table is four independent SBC replications.
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

from eyetrajectoriespy.research.calibration_seed import calibration_replicate_seed
from scripts.run_b6_b7_rank2_controlled_observation_r4 import (
    DESIGNS, PARTICIPANT_COUNTS, SEED as ORIGINAL_R4_SEED, paired_cases,
    verify_matched_case_design, run_one as r4_run_one,
)

STUDY = "B6_B7_RANK2_INDEPENDENT_PAIRED_REPLICATION_R5_V1"
MASTER_SEED = 2026111105
REPLICATES = tuple(range(8))
PRIMARY_BUDGET = {"chains": 4, "cores": 2, "tune": 700,
                  "draws": 400, "target_accept": .94}
FUNCTIONAL_FAMILIES = ("mean", "variance", "crosscovariance")


def replicate_seed(replicate: int) -> int:
    if replicate not in REPLICATES:
        raise ValueError("replicate outside the prespecified R5 seed ledger")
    seed = calibration_replicate_seed(
        STUDY, master_seed=MASTER_SEED, shard_id=0,
        scenario="rank2_common_truth_schedule_by_n", replicate=replicate)
    if seed == ORIGINAL_R4_SEED:
        raise ValueError("R5 must not recycle the R4 source seed")
    return seed


def functional_family(name: str) -> str:
    if name.startswith(("x_mean_", "y_mean_")):
        return "mean"
    if name.startswith(("x_variance_", "y_variance_")):
        return "variance"
    if name.startswith("xy_covariance_"):
        return "crosscovariance"
    raise ValueError("unexpected identified population functional: " + name)


def functional_report(checks: dict) -> dict:
    """Preserve diagnostic failure, signed error, MCSE and interval evidence."""
    f = checks["functionals"]
    if len(f) != 15:
        raise ValueError("all fifteen population functionals are required")
    report = {}
    for name, v in sorted(f.items()):
        family = functional_family(name)
        mean = float(v["posterior_mean"])
        truth = float(v["single_dataset_truth_value"])
        q05 = float(v["posterior_q05"])
        q95 = float(v["posterior_q95"])
        mcse = float(v["mcse_mean_spectral"])
        if not np.isfinite([mean, truth, q05, q95, mcse]).all() or q95 < q05:
            raise ValueError("nonfinite or incoherent posterior evidence")
        report[name] = {
            "family": family,
            "posterior_mean": mean, "generating_truth": truth,
            "single_dataset_signed_error_not_bias": mean-truth,
            "posterior_90pct_q05": q05, "posterior_90pct_q95": q95,
            "posterior_90pct_interval_width": q95-q05,
            "single_dataset_truth_in_interval": bool(v[
                "single_dataset_90pct_interval_contains_truth"]),
            "mean_mcse_spectral": mcse,
            "rank_rhat": float(v["rank_rhat"]),
            "bulk_ess": float(v["bulk_ess"]),
            "tail_ess": float(v["tail_ess"]),
            "passes_declared_screen": bool(v["passes_declared_functional_screen"]),
        }
    if set(p["family"] for p in report.values()) != set(FUNCTIONAL_FAMILIES):
        raise ValueError("missing one identified functional family")
    return report


def run_one(replicate: int, design: str, n: int) -> dict:
    if design not in DESIGNS or n not in PARTICIPANT_COUNTS:
        raise ValueError("cell outside predeclared R5 design")
    seed = replicate_seed(replicate)
    contract = verify_matched_case_design(paired_cases(seed, n))
    if not contract["matched_design_verified"]:
        raise ValueError("R5 matched schedule generation falsified")
    case = r4_run_one(design=design, participants=n, seed=seed,
                      draws=PRIMARY_BUDGET["draws"], tune=PRIMARY_BUDGET["tune"],
                      cores=PRIMARY_BUDGET["cores"])
    case.update(study=STUDY, replicate=replicate,
                independent_generating_block_seed=seed,
                original_R4_seed_not_reused=True,
                n_is_nested_within_12=True,
                not_independent_of_other_cells_in_block=True,
                stage0_not_an_estimate_of_schedule_effect=True)
    if case["status"] == "ok":
        try:
            case["per_functional_evidence"] = functional_report(case["reference_checks"])
        except Exception as exc:
            case.update(status="evidence_failed",
                        error_type=type(exc).__name__, error=str(exc)[:900])
    return case


def paired_block_audit(cases: list[dict], replicate: int) -> dict:
    """Failure-inclusive planned-cell audit, never drop nonconverged fits."""
    cells = {(x["design"], int(x["participants"])): x for x in cases}
    expected = {(d, n) for d in DESIGNS for n in PARTICIPANT_COUNTS}
    if len(cases) != len(cells) or not set(cells).issubset(expected):
        raise ValueError("duplicate or undeclared cell")
    seed = replicate_seed(replicate)
    if any(x["replicate"] != replicate or
           x["independent_generating_block_seed"] != seed for x in cases):
        raise ValueError("cell reuses a different generating block")
    missing = sorted(f"{d}-n{n}" for d,n in expected-set(cells))
    success = [x for x in cases if x["status"] == "ok"]
    adequate = [x for x in success if
                x["reference_checks"]["all_identified_functionals_pass_exploratory_screen"]]
    contrasts = {}
    for n in PARTICIPANT_COUNTS:
        a, b = cells.get(("paired",n)), cells.get(("asynchronous",n))
        if a is not None and b is not None and a["status"] == b["status"] == "ok":
            group = {}
            for key in a["per_functional_evidence"]:
                u = a["per_functional_evidence"][key]
                v = b["per_functional_evidence"][key]
                if not np.isclose(u["generating_truth"], v["generating_truth"],
                                  rtol=0, atol=1e-12):
                    raise ValueError("paired schedule truth changed")
                group[key] = {
                    "family": u["family"],
                    "paired_minus_async_signed_error": (
                        u["single_dataset_signed_error_not_bias"]-
                        v["single_dataset_signed_error_not_bias"]),
                    "paired_minus_async_interval_width": (
                        u["posterior_90pct_interval_width"]-
                        v["posterior_90pct_interval_width"]),
                    "paired_screen_pass": u["passes_declared_screen"],
                    "async_screen_pass": v["passes_declared_screen"],
                }
            contrasts[str(n)] = group
    return {
        "study": STUDY, "replicate": replicate,
        "independent_generating_blocks": 1 if cases else 0,
        "four_cells_are_correlated_not_four_independent_datasets": True,
        "planned_cells": 4, "artifacts_present": len(cases),
        "missing_cells": missing, "fit_successes": len(success),
        "fitting_or_evidence_failures": len(cases)-len(success),
        "computational_screen_passes": len(adequate),
        "screen_failures_in_completed_fits": len(success)-len(adequate),
        "paired_schedule_descriptive_contrasts_by_n": contrasts,
        "no_population_schedule_effect_estimate_from_one_block": True,
        "no_r5_independent_sbc_ranks": True,
        "nominal_coverage_qualified": False,
        "release_authorized": False,
    }


def write_case(row: dict, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    ledger = {
        "study": STUDY, "replicate": row["replicate"],
        "n_nested_not_independent": True,
        "completed_sampling": row["status"] == "ok",
        "source_sha": os.environ.get("GITHUB_SHA"),
        "fit_exceptions": int(row["status"] != "ok"),
        "exploratory_screen_failures": (
            int(not row["reference_checks"][
                "all_identified_functionals_pass_exploratory_screen"])
            if row["status"] == "ok" else None),
        "calibration_qualified": False, "release_authorized": False,
    }
    for fname, obj in (("case.json",row), ("evidence.json",ledger)):
        (out/fname).write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")
    (out/"SHA256SUMS").write_text("".join(
        sha256((out/f).read_bytes()).hexdigest()+f"  {f}\n"
        for f in ("case.json", "evidence.json")))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--replicate",type=int,choices=REPLICATES,required=True)
    ap.add_argument("--design",choices=DESIGNS,required=True)
    ap.add_argument("--participants",type=int,choices=PARTICIPANT_COUNTS,required=True)
    ap.add_argument("--out",required=True,type=Path)
    args=ap.parse_args()
    row=run_one(args.replicate,args.design,args.participants)
    write_case(row,args.out)
    print("R5 INDEPENDENT BLOCK FIT:",json.dumps({
        "replicate":row["replicate"],"design":row["design"],
        "participants":row["participants"],"status":row["status"],
        "screen_pass":row["reference_checks"][
            "all_identified_functionals_pass_exploratory_screen"]
            if row["status"]=="ok" else None,"release_authorized":False},sort_keys=True))
    if row["status"]!="ok":
        raise SystemExit("original fit/evidence failure retained")


if __name__=="__main__":
    main()
