"""R58 research-only boundary-reference stress test on NEW Gaussian blocks.

The half-chi-square(1)/half-point-mass-at-zero asymptotic law is a
CANDIDATE reference, not a proved null distribution for this irregular
finite-participant REML design. No general p-value or release claims.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path

import numpy as np
from scipy.stats import chi2, norm

from scripts import run_w3_r16_leverage_covariance_factorial as r16
from scripts import run_w3_r17_fresh_feasibility as fresh
from scripts import run_w3_r48_independent_fitted_cr2 as r48
from scripts import run_w3_r57_nested_zero_nonnegative_reml as r57

STUDY = "W3_R58_NEW_INDEPENDENT_GAUSSIAN_BOUNDARY_REFERENCE_STRESS"
MASTER_SEED = 202610175858
BLOCKS = 24
PARTICIPANTS = 24
SUPPORT = r57.SUPPORT
STATES = r57.STATES
SHARDS = tuple((j, j + 4) for j in range(0, BLOCKS, 4))
ALPHA = 0.05
CRITICAL = float(chi2.isf(2.0 * ALPHA, 1))
N_SOURCE_CASES = BLOCKS * len(SUPPORT) * len(STATES)
N_MODEL_FITS = N_SOURCE_CASES * 2
N_SOLVER_STARTS = N_SOURCE_CASES * (
    len(r57.NULL_STARTS) + len(r57.ALT_STARTS)
)


def candidate_boundary_pvalue(t):
    """Asymptotic 50:50 mixture ONLY; value 1 at the zero atom."""
    if not math.isfinite(t) or t < 0:
        raise ValueError("R58 candidate deviance must be finite/nonnegative")
    return 1.0 if t == 0.0 else float(0.5 * chi2.sf(t, 1))


def wilson_95(k, n):
    """Bernoulli Wilson interval; never substitute planned for valid n."""
    if not (isinstance(k, int) and isinstance(n, int)
            and 0 <= k <= n):
        raise ValueError("R58 invalid Monte Carlo numerator/denominator")
    if n == 0:
        return None
    z = float(norm.isf(0.025))
    p = k / n
    den = 1.0 + z*z/n
    center = (p + z*z/(2*n))/den
    half = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n))/den
    return [max(0.0, center-half), min(1.0, center+half)]


def independent_source(block, support):
    if type(block) is not int or block not in range(BLOCKS) or support not in SUPPORT:
        raise ValueError("R58 unregistered Gaussian primitive block/support")
    return fresh.fresh_source(
        block, support, n=PARTICIPANTS, master_seed=MASTER_SEED,
        n_blocks=BLOCKS, max_n=PARTICIPANTS,
    )


def empty_case(block, support, state):
    return {
        "study": STUDY, "block": block, "support": support,
        "generating_state": state,
        "new_independent_primitive_block": True,
        "paired_support_and_state_not_independent": True,
        "generating_slope_variance": 0.0 if state == "true_zero"
                                   else r16.SIGMA_RANDOM_SLOPE**2,
        "source_status": "failed", "source_error": None,
        "source_innovation_slope_L2": None,
        "null_fit": r57._not_attempted_model("exact_zero"),
        "alternative_fit": r57._not_attempted_model("nonnegative"),
        "nested_comparison": {
            "status": "not_attempted", "reason": "source_unavailable",
            "raw_signed_deviance": None, "nonnegative_deviance": None,
            "candidate_half_chi_square_p": None,
            "candidate_nominal_005_rejection": None,
            "selected_exact_zero": None,
            "candidate_reference_qualified": False,
        },
        "pointwise_or_simultaneous_CR2_qualified": False,
        "release_authorized": False,
    }


def evaluate_pair(block, support):
    rows = [empty_case(block, support, state) for state in STATES]
    try:
        src = independent_source(block, support)
        X, y, w, g, t, tr, x, c, truth, raw_truth = r48.native_data(src)
        ui = np.asarray(src[0]["participant_slope"], float)[
            np.asarray(g, int), 0, 0, 0
        ]
        slope = r16.SIGMA_RANDOM_SLOPE * ui * x * (1.0 + 0.25*t)
        if not np.isfinite(slope).all() or slope.shape != y.shape:
            raise ValueError("R58 Gaussian slope source misalignment")
        states = {
            "true_zero": np.asarray(y, float) - slope,
            "true_positive": np.asarray(y, float).copy(),
        }
        np.testing.assert_allclose(
            states["true_positive"] - states["true_zero"], slope,
            rtol=2e-13, atol=2e-13,
        )
        for row in rows:
            row["source_status"] = "ok"
            row["source_innovation_slope_L2"] = float(np.linalg.norm(slope))
            datum = {"X": X, "y": states[row["generating_state"]],
                     "w": w, "group": g, "time": t, "trial": tr, "x": x}
            try:
                prepared = r57.prepare_reml_design(
                    X, datum["y"], w, g, t, tr, x,
                    slope="predictor_scaled_slope",
                )
                reference = r57._reference(datum)
                row["null_fit"] = r57.fit_model(prepared, reference, "exact_zero")
                row["alternative_fit"] = r57.fit_model(
                    prepared, reference, "nonnegative"
                )
            except Exception as exc:
                row["source_error"] = "model_preparation_or_optimizer:" + repr(exc)[:350]
            a, b = row["null_fit"], row["alternative_fit"]
            compare = row["nested_comparison"]
            if a["status"] != "accepted" or b["status"] != "accepted":
                compare["reason"] = "null_or_alternative_numerical_refusal"
                continue
            raw = float(2.0*(a["selected_NLL"] - b["selected_NLL"]))
            compare["raw_signed_deviance"] = raw
            if not math.isfinite(raw) or raw < -r57.NESTED_MONOTONIC_TOL:
                compare.update(status="refused",
                               reason="nonfinite_or_nested_monotonicity_failure")
                continue
            gap = max(0.0, raw)
            compare.update(
                status="ok", reason=None, nonnegative_deviance=gap,
                candidate_half_chi_square_p=candidate_boundary_pvalue(gap),
                candidate_nominal_005_rejection=bool(gap > CRITICAL),
                selected_exact_zero=bool(b["selected_slope_ratio"] <= 1e-10),
            )
    except Exception as exc:
        for row in rows:
            row["source_error"] = repr(exc)[:350]
    return rows


def summarize(rows):
    expected = {(b, s, state) for b in range(BLOCKS)
                for s in SUPPORT for state in STATES}
    keys = [(r["block"], r["support"], r["generating_state"]) for r in rows]
    if len(keys) != len(set(keys)) or set(keys) != expected:
        raise ValueError("R58 complete unique new-source denominator required")
    starts = sum(len(r["null_fit"]["original_starts"]) +
                 len(r["alternative_fit"]["original_starts"]) for r in rows)
    if starts != N_SOLVER_STARTS or len(rows) != N_SOURCE_CASES:
        raise ValueError("R58 failure-inclusive 576-start evidence missing")
    cells = {}
    for support in SUPPORT:
        for state in STATES:
            sample = [r for r in rows if r["support"] == support
                      and r["generating_state"] == state]
            accepted = [r for r in sample if
                        r["nested_comparison"]["status"] == "ok"]
            rejected = sum(r["nested_comparison"][
                "candidate_nominal_005_rejection"] is True for r in accepted)
            selected_zero = sum(r["nested_comparison"][
                "selected_exact_zero"] is True for r in accepted)
            n = len(accepted)
            fails = BLOCKS - n
            gaps = [r["nested_comparison"]["nonnegative_deviance"]
                    for r in accepted]
            cells[support + "/" + state] = {
                "independent_Gaussian_primitive_blocks": BLOCKS,
                "source_status_failures": sum(r["source_status"] != "ok"
                                              for r in sample),
                "null_model_refusals": sum(
                    r["null_fit"]["status"] != "accepted" for r in sample),
                "alternative_model_refusals": sum(
                    r["alternative_fit"]["status"] != "accepted" for r in sample),
                "nested_reference_nonaccepted_or_refused": fails,
                "accepted_comparisons": n,
                "candidate_reference_rejections": rejected,
                "candidate_reference_rejection_fraction_valid_only":
                    rejected/n if n else None,
                "wilson95_conditional_on_accepted_calculations":
                    wilson_95(rejected, n),
                "all_source_rejection_fraction_lower_if_refusals_not_rejected":
                    rejected/BLOCKS,
                "all_source_rejection_fraction_upper_if_refusals_rejected":
                    (rejected+fails)/BLOCKS,
                "candidate_reference_mc_se_valid_only":
                    math.sqrt((rejected/n)*(1-rejected/n)/n) if n else None,
                "alternative_selected_exact_zero": selected_zero,
                "zero_selection_fraction_valid_only":
                    selected_zero/n if n else None,
                "zero_selection_wilson95_valid_only":
                    wilson_95(selected_zero, n),
                "median_accepted_deviance":
                    float(np.median(gaps)) if gaps else None,
                "not_qualified_null_TypeI_or_power": True,
            }
    return {
        "study": STUDY, "new_independent_source_seed": MASTER_SEED,
        "new_independent_primitive_blocks": BLOCKS,
        "participants_per_block": PARTICIPANTS,
        "paired_support_and_generating_state": True,
        "candidate_asymptotic_half_atom_half_chisquare": True,
        "asymptotic_boundary_regular_conditions_not_proven": True,
        "candidate_reference_alpha": ALPHA,
        "candidate_reference_critical_strict_greater": CRITICAL,
        "candidate_reference_validated": False,
        "predeclared_case_slots": N_SOURCE_CASES,
        "recorded_case_slots": len(rows),
        "predeclared_nested_model_slots": N_MODEL_FITS,
        "recorded_nested_model_slots": len(rows)*2,
        "predeclared_optimizer_start_slots": N_SOLVER_STARTS,
        "recorded_optimizer_start_slots": starts,
        "all_failure_inclusive_denominators_complete": True,
        "pointwise_CR2_90pct_qualified": False,
        "simultaneous_CR2_90pct_qualified": False,
        "global_REML_optimum_proven": False,
        "release_authorized": False,
        "strata": cells,
    }


def write_json(path, obj):
    path.write_text(json.dumps(r57.r53._json_plain(obj), indent=2,
                               sort_keys=True, allow_nan=False) + "\n")


def shard(out, start, stop):
    if (start, stop) not in SHARDS:
        raise ValueError("R58 original source shard outside frozen partition")
    out.mkdir(parents=True, exist_ok=True)
    rows = [row for b in range(start, stop) for s in SUPPORT
            for row in evaluate_pair(b, s)]
    write_json(out / "cases.json", rows)
    write_json(out / "manifest.json", {
        "study": STUDY, "start": start, "stop": stop, "seed": MASTER_SEED,
        "original_checkout": os.environ.get("GITHUB_SHA", "unverified-local"),
        "records": len(rows),
        "SHA256_cases": hashlib.sha256((out/"cases.json").read_bytes()).hexdigest(),
    })


def aggregate(out, parts):
    manifests = list(parts.glob("*/manifest.json"))
    if len(manifests) != len(SHARDS):
        raise ValueError("R58 expected six immutable original source shards")
    found, rows = set(), []
    sha = os.environ.get("GITHUB_SHA", "unverified-local")
    for path in manifests:
        manifest = json.loads(path.read_text())
        key = (manifest["start"], manifest["stop"])
        if (key not in SHARDS or key in found or
                manifest["study"] != STUDY or
                manifest["seed"] != MASTER_SEED or
                manifest["original_checkout"] != sha):
            raise ValueError("R58 source-shard/checkout identity mismatch")
        found.add(key)
        raw = (path.parent/"cases.json").read_bytes()
        if hashlib.sha256(raw).hexdigest() != manifest["SHA256_cases"]:
            raise ValueError("R58 original case evidence SHA256 mismatch")
        batch = json.loads(raw)
        expected = {(b, s, state) for b in range(*key)
                    for s in SUPPORT for state in STATES}
        if (len(batch) != manifest["records"] or
            len(batch) != len(expected) or
            {(r["block"], r["support"], r["generating_state"])
             for r in batch} != expected):
            raise ValueError("R58 original case-shard source identities invalid")
        rows.extend(batch)
    if found != set(SHARDS):
        raise ValueError("R58 incomplete exact source shard set")
    rows.sort(key=lambda r: (r["block"], SUPPORT.index(r["support"]),
                             STATES.index(r["generating_state"])))
    report = summarize(rows)
    out.mkdir(parents=True, exist_ok=True)
    write_json(out/"cases.json", rows)
    write_json(out/"summary.json", report)
    (out/"source-commit.txt").write_text(sha+"\n")
    (out/"SHA256SUMS").write_text("".join(
        hashlib.sha256((out/f).read_bytes()).hexdigest()+"  "+f+"\n"
        for f in ("cases.json", "summary.json", "source-commit.txt")
    ))
    print(json.dumps(report, sort_keys=True))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--start", type=int)
    g.add_argument("--merge-parts", type=Path)
    ap.add_argument("--stop", type=int)
    args = ap.parse_args()
    if args.merge_parts is not None:
        aggregate(args.out, args.merge_parts)
    elif args.stop is not None:
        shard(args.out, args.start, args.stop)
    else:
        raise SystemExit("R58 requires --start and --stop")


if __name__ == "__main__":
    main()
