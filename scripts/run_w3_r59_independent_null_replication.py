"""W3 R59: NEW independent TRUE-NULL Gaussian boundary-reference replication.

An external-seed, 128-primitive-block stress test of the R58 candidate
half-zero/half-chi-square-one cutoff, with ordinary/extreme predictor support
paired within each primitive block. NO alternative-truth/power simulations.
Reuses unchanged numerically scrutinized R57 nested REML objective and KKT
gates. Candidate cutoff is NOT a qualified hypothesis test or public API.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path

import numpy as np

from scripts import run_w3_r16_leverage_covariance_factorial as r16
from scripts import run_w3_r17_fresh_feasibility as fresh
from scripts import run_w3_r48_independent_fitted_cr2 as r48
from scripts import run_w3_r57_nested_zero_nonnegative_reml as r57
from scripts import run_w3_r58_boundary_null_reference as r58

STUDY = "W3_R59_INDEPENDENT_TRUE_NULL_BOUNDARY_REFERENCE_REPLICATION"
MASTER_SEED = 202610175959
BLOCKS = 128
PARTICIPANTS = 24
SUPPORT = r57.SUPPORT
SHARDS = tuple((i, i+16) for i in range(0, BLOCKS, 16))
ALPHA = r58.ALPHA
CRITICAL = r58.CRITICAL
SLOTS = BLOCKS*len(SUPPORT)
FITS = SLOTS*2
STARTS = SLOTS*(len(r57.NULL_STARTS)+len(r57.ALT_STARTS))


def independent_source(block, support):
    if type(block) is not int or not 0 <= block < BLOCKS or support not in SUPPORT:
        raise ValueError("R59 source outside preregistered primitive universe")
    return fresh.fresh_source(
        block, support, n=PARTICIPANTS, master_seed=MASTER_SEED,
        n_blocks=BLOCKS, max_n=PARTICIPANTS,
    )


def empty_case(block, support):
    return {
        "study": STUDY, "block": block, "support": support,
        "generating_state": "true_zero",
        "new_independent_primitive_block": True,
        "paired_across_leverage_not_independent": True,
        "true_slope_variance": 0.0,
        "source_status": "failed", "source_error": None,
        "slope_innovation_L2_removed": None,
        "null_fit": r57._not_attempted_model("exact_zero"),
        "alternative_fit": r57._not_attempted_model("nonnegative"),
        "comparison": {
            "status": "not_attempted", "reason": "source_unavailable",
            "raw_signed_deviance": None, "nonnegative_deviance": None,
            "candidate_half_chisquare_p": None,
            "candidate_nominal_005_exceedance": None,
            "H1_selected_exact_zero": None,
            "null_reference_validated": False,
        },
        "pointwise_or_simultaneous_CR2_qualified": False,
        "release_authorized": False,
    }


def evaluate(block, support):
    case = empty_case(block, support)
    try:
        src = independent_source(block, support)
        X, y, w, g, t, tr, x, c, truth, raw_truth = r48.native_data(src)
        ui = np.asarray(src[0]["participant_slope"], float)[
            np.asarray(g, int), 0, 0, 0]
        slope = r16.SIGMA_RANDOM_SLOPE*ui*x*(1.+.25*t)
        if not np.isfinite(slope).all() or slope.shape != y.shape:
            raise ValueError("R59 invalid Gaussian source slope alignment")
        original = np.asarray(y, float)
        zero = original - slope
        np.testing.assert_allclose(original-zero, slope,
                                   rtol=2e-13, atol=2e-13)
        case["source_status"] = "ok"
        case["slope_innovation_L2_removed"] = float(np.linalg.norm(slope))
        datum = {"X": X, "y": zero, "w": w}
        prep = r57.prepare_reml_design(
            X, zero, w, g, t, tr, x,
            slope="predictor_scaled_slope",
        )
        reference = r57._reference(datum)
        case["null_fit"] = r57.fit_model(prep, reference, "exact_zero")
        case["alternative_fit"] = r57.fit_model(prep, reference, "nonnegative")
    except Exception as exc:
        case["source_error"] = repr(exc)[:420]
        # A prepared/model failure keeps all six original start placeholders.
    a, b = case["null_fit"], case["alternative_fit"]
    comp = case["comparison"]
    if a["status"] != "accepted" or b["status"] != "accepted":
        comp["reason"] = "null_or_alternative_numeric_refusal"
        return case
    raw = float(2*(a["selected_NLL"] - b["selected_NLL"]))
    comp["raw_signed_deviance"] = raw
    if not math.isfinite(raw) or raw < -r57.NESTED_MONOTONIC_TOL:
        comp.update(status="refused", reason="nested_nonfinite_or_nonmonotone")
        return case
    dev = max(0., raw)
    comp.update(
        status="ok", reason=None, nonnegative_deviance=dev,
        candidate_half_chisquare_p=r58.candidate_boundary_pvalue(dev),
        candidate_nominal_005_exceedance=bool(dev > CRITICAL),
        H1_selected_exact_zero=bool(b["selected_slope_ratio"] <= 1e-10),
    )
    return case


def summary(rows):
    expected = {(b, s) for b in range(BLOCKS) for s in SUPPORT}
    keys = [(r["block"], r["support"]) for r in rows]
    if len(keys) != SLOTS or len(set(keys)) != SLOTS or set(keys) != expected:
        raise ValueError("R59 independent primitive block denominator missing")
    starts = sum(len(r["null_fit"]["original_starts"]) +
                 len(r["alternative_fit"]["original_starts"]) for r in rows)
    if starts != STARTS:
        raise ValueError("R59 numerical refusal/start ledger incomplete")
    cells = {}
    for s in SUPPORT:
        sample = [r for r in rows if r["support"] == s]
        qualified = [r for r in sample if r["comparison"]["status"] == "ok"]
        n = len(qualified)
        k = sum(r["comparison"]["candidate_nominal_005_exceedance"] is True
                for r in qualified)
        refused = BLOCKS - n
        cells[s] = {
            "planned_new_independent_primitive_blocks": BLOCKS,
            "recorded_null_source_cases": len(sample),
            "source_generation_failures": sum(
                r["source_status"] != "ok" for r in sample),
            "null_model_numeric_refusals": sum(
                r["null_fit"]["status"] != "accepted" for r in sample),
            "alternative_model_numeric_refusals": sum(
                r["alternative_fit"]["status"] != "accepted" for r in sample),
            "nested_reference_numeric_refusals": refused,
            "accepted_candidate_calculations": n,
            "candidate_exceedances": k,
            "candidate_exceedance_fraction_accepted_only": k/n if n else None,
            "candidate_exceedance_Wilson95_accepted_only": r58.wilson_95(k,n),
            "all_source_lower_assuming_refusals_no_exceedance": k/BLOCKS,
            "all_source_upper_assuming_refusals_all_exceedance": (k+refused)/BLOCKS,
            "selected_exact_zero_count": sum(
                r["comparison"]["H1_selected_exact_zero"] is True
                for r in qualified),
            "median_accepted_nested_deviance": (
                float(np.median([r["comparison"]["nonnegative_deviance"]
                                 for r in qualified])) if qualified else None),
            "reference_distribution_qualified": False,
        }
    paired = {
        (r["block"],r["support"]): r for r in rows
    }
    pairs = [(paired[(b,SUPPORT[0])]["comparison"],
              paired[(b,SUPPORT[1])]["comparison"])
             for b in range(BLOCKS)]
    both = [(a["candidate_nominal_005_exceedance"],
             b["candidate_nominal_005_exceedance"])
            for a,b in pairs if a["status"] == b["status"] == "ok"]
    return {
        "study": STUDY, "new_Gaussian_independent_primitive_blocks": BLOCKS,
        "source_seed": MASTER_SEED,
        "participants_per_block": PARTICIPANTS,
        "paired_ordinary_extreme_not_independent": True,
        "generating_slope_variance_exact_zero": True,
        "candidate_reference_alpha": ALPHA,
        "candidate_cutoff_strict_greater": CRITICAL,
        "planned_cases": SLOTS, "recorded_cases": len(rows),
        "planned_H0_H1_model_slots": FITS, "recorded_H0_H1_model_slots": 2*len(rows),
        "planned_optimizer_start_slots": STARTS,
        "recorded_optimizer_start_slots": starts,
        "both_leverage_candidate_comparisons_accepted": len(both),
        "paired_ordinary_only_exceedance": sum(a and not b for a,b in both),
        "paired_extreme_only_exceedance": sum(b and not a for a,b in both),
        "paired_both_exceedances": sum(a and b for a,b in both),
        "paired_neither_exceedances": sum(not a and not b for a,b in both),
        "strata": cells,
        "classical_half_mixture_reference_is_candidate_not_proven": True,
        "no_positive_source_or_power_simulation": True,
        "no_90pct_CR2_pointwise_or_simultaneous_qualification": True,
        "release_authorized": False,
    }


def shard(out, start, stop):
    if (start,stop) not in SHARDS:
        raise ValueError("R59 illegal new independent source shard")
    out.mkdir(parents=True, exist_ok=True)
    rows = [evaluate(b, s) for b in range(start,stop) for s in SUPPORT]
    r58.write_json(out/"cases.json", rows)
    r58.write_json(out/"manifest.json", {
        "study": STUDY, "start": start, "stop": stop,
        "new_seed": MASTER_SEED,
        "checkout": os.environ.get("GITHUB_SHA","unverified-local"),
        "records": len(rows),
        "sha256_cases": hashlib.sha256((out/"cases.json").read_bytes()).hexdigest(),
    })


def aggregate(out, parts):
    files = list(parts.glob("*/manifest.json"))
    if len(files) != len(SHARDS):
        raise ValueError("R59 exact eight original source shards required")
    checkout = os.environ.get("GITHUB_SHA","unverified-local")
    found, rows = set(), []
    for file in files:
        manifest = json.loads(file.read_text())
        key=(manifest["start"],manifest["stop"])
        if (key not in SHARDS or key in found or
            manifest["study"] != STUDY or manifest["new_seed"] != MASTER_SEED or
            manifest["checkout"] != checkout):
            raise ValueError("R59 original source shard or checkout mismatch")
        found.add(key)
        raw = (file.parent/"cases.json").read_bytes()
        if hashlib.sha256(raw).hexdigest() != manifest["sha256_cases"]:
            raise ValueError("R59 original numerical source SHA256 mismatch")
        batch = json.loads(raw)
        expected = {(b,s) for b in range(*key) for s in SUPPORT}
        if (len(batch) != manifest["records"] or
            {(v["block"],v["support"]) for v in batch} != expected or
            len(batch) != len(expected)):
            raise ValueError("R59 exact source keys or complete denominator absent")
        rows.extend(batch)
    if found != set(SHARDS):
        raise ValueError("R59 missing source shard partition")
    rows.sort(key=lambda x:(x["block"],SUPPORT.index(x["support"])))
    report = summary(rows)
    out.mkdir(parents=True, exist_ok=True)
    r58.write_json(out/"cases.json", rows)
    r58.write_json(out/"summary.json", report)
    (out/"source-commit.txt").write_text(checkout+"\n")
    (out/"SHA256SUMS").write_text("".join(
        hashlib.sha256((out/name).read_bytes()).hexdigest()+"  "+name+"\n"
        for name in ("cases.json","summary.json","source-commit.txt")
    ))
    print(json.dumps(report,sort_keys=True))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True,type=Path)
    m=parser.add_mutually_exclusive_group(required=True)
    m.add_argument("--start",type=int)
    m.add_argument("--merge-parts",type=Path)
    parser.add_argument("--stop",type=int)
    args=parser.parse_args()
    if args.merge_parts is not None:
        aggregate(args.out,args.merge_parts)
    elif args.stop is not None:
        shard(args.out,args.start,args.stop)
    else:
        raise SystemExit("R59 requires --start and --stop")


if __name__=="__main__":
    main()
