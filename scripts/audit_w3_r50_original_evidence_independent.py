"""Independent read-only audit of R50 original Gaussian bootstrap evidence.

Consumes the ORIGINAL completed R50 Actions artifact; never imports the R50
simulation or estimator and never regenerates a source outcome. Recomputes
all 48 paired source records, 240 interval slots, 3024 refit attempts,
6240 solver-start slots, observed truth-inclusion denominators, Wilson
Monte Carlo intervals and original 31/63 pivot quantiles. Intended to catch
reporting/aggregation errors independently of the generating source.
Not a coverage-validation certificate, estimator or release gate.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
from statistics import NormalDist, median

BLOCKS = 24
SUPPORT = ("ordinary_dependent", "extreme_dependent")
METHODS = (
    "generating_covariance_oracle_conditional_CR2",
    "correct_family_fitted_conditional_CR2",
    "correct_family_refit_bootstrap_t_31_prefix",
    "correct_family_refit_bootstrap_t_63",
    "wrong_shared_slope_fitted_conditional_CR2",
)
N_BOOT = 63
N_STARTS = 2
EXPECTED_SHA_FILES = ("cases.json", "summary.json", "source-commit.txt")
TOL = 2e-8


def _assert_close(actual, expected, label):
    if actual is None or expected is None or not math.isclose(
        float(actual), float(expected), rel_tol=TOL, abs_tol=TOL
    ):
        raise ValueError(f"R50 independent evidence mismatch: {label}")


def _q_linear(values, level):
    """NumPy linear percentile rule, independently coded."""
    if not values:
        raise ValueError("quantile of empty independent pivot sample")
    data = sorted(float(v) for v in values)
    location = (len(data) - 1) * level
    lo = math.floor(location)
    hi = math.ceil(location)
    return data[lo] + (location - lo) * (data[hi] - data[lo])


def _wilson(count, total):
    if total < 1:
        raise ValueError("invalid independent Monte Carlo denominator")
    z = NormalDist().inv_cdf(.975)
    p = count / total
    d = 1 + z*z/total
    centre = (p + z*z/(2*total))/d
    radius = z * math.sqrt(p*(1-p)/total + z*z/(4*total*total))/d
    return (max(0.0, centre-radius), min(1.0, centre+radius))


KKT_LIMIT = .001
NLL_GAP_LIMIT = .001
RECONSTRUCTION_LIMIT = 1e-6


def _verify_physical_starts(starts, status, label, selected=None):
    """Independently verify R50's recorded two-start physical REML gate."""
    if len(starts) != 2 or tuple(x.get("label") for x in starts) != ("interior", "spread"):
        raise ValueError(f"R50 invalid physical optimizer-start identities: {label}")
    finite = []
    for start in starts:
        if start.get("status") not in ("ok", "nonconverged", "failed", "not_attempted"):
            raise ValueError(f"R50 unrecognized optimizer status: {label}")
        nll = start.get("negative_loglik")
        if nll is None:
            if start["status"] == "ok":
                raise ValueError(f"R50 successful optimizer missing NLL: {label}")
            continue
        if not math.isfinite(float(nll)):
            raise ValueError(f"R50 nonfinite NLL: {label}")
        finite.append(start)
        if start["status"] == "ok":
            if start.get("optimizer_success") is not True:
                raise ValueError(f"R50 inconsistent optimizer success flag: {label}")
            recon = float(start["objective_reconstruction_error"])
            if not math.isfinite(recon) or recon > RECONSTRUCTION_LIMIT + 1e-10:
                raise ValueError(f"R50 failed likelihood reconstruction: {label}")
            ratios = start.get("ratios") or []
            if len(ratios) != 4 or any(
                not math.isfinite(float(x)) or float(x) <= 0 for x in ratios
            ):
                raise ValueError(f"R50 nonphysical nuisance variance ratios: {label}")
    eligible = []
    if finite:
        best = min(float(x["negative_loglik"]) for x in finite)
        for x in finite:
            kkt = x.get("physical_projected_KKT")
            if kkt is None:
                continue
            kkt = float(kkt)
            if not math.isfinite(kkt) or kkt < 0:
                raise ValueError(f"R50 invalid physical KKT record: {label}")
            if (x["status"] == "ok" and kkt <= KKT_LIMIT + 1e-10
                    and float(x["negative_loglik"]) - best <= NLL_GAP_LIMIT + 1e-10):
                eligible.append(x)
    if status in ("accepted", "ok"):
        if not eligible:
            raise ValueError(f"R50 accepted nuisance violates KKT/NLL: {label}")
        if selected is not None:
            selected_nll = float(selected["selected_NLL"])
            selected_kkt = float(selected["physical_projected_KKT"])
            _assert_close(selected_nll, min(float(x["negative_loglik"]) for x in eligible), label+"/selected-NLL")
            if not any(
                math.isclose(float(x["negative_loglik"]), selected_nll, rel_tol=TOL, abs_tol=TOL)
                and math.isclose(float(x["physical_projected_KKT"]), selected_kkt, rel_tol=TOL, abs_tol=TOL)
                for x in eligible
            ):
                raise ValueError(f"R50 selected nuisance does not match accepted start: {label}")
    return len(eligible)


def _sha256_files(directory):
    manifest = (directory / "SHA256SUMS").read_text().splitlines()
    parsed = {}
    for line in manifest:
        digest, filename = line.split("  ", 1)
        if filename in parsed:
            raise ValueError("duplicate SHA256 manifest entry")
        parsed[filename] = digest
    if set(parsed) != set(EXPECTED_SHA_FILES):
        raise ValueError("R50 independent artifact checksum manifest incomplete")
    for filename, digest in parsed.items():
        actual = hashlib.sha256((directory / filename).read_bytes()).hexdigest()
        if actual != digest:
            raise ValueError(f"SHA256 evidence mismatch for {filename}")
    return parsed


def audit_original(directory):
    """Return independently reconstructed descriptive rates and checks."""
    directory = Path(directory)
    digests = _sha256_files(directory)
    source_sha = (directory / "source-commit.txt").read_text().strip()
    if len(source_sha) < 8:
        raise ValueError("invalid original source identity")
    cases = json.loads((directory / "cases.json").read_text())
    source_summary = json.loads((directory / "summary.json").read_text())
    if len(cases) != BLOCKS * len(SUPPORT):
        raise ValueError("R50 original source does not contain 48 cases")
    keys = [(r["block"], r["support"]) for r in cases]
    expected = {(i, support) for i in range(BLOCKS) for support in SUPPORT}
    if len(set(keys)) != len(keys) or set(keys) != expected:
        raise ValueError("missing, duplicated or unplanned primitive block/support")
    if not source_summary["complete_original_failure_inclusive_design"]:
        raise ValueError("original science reports incomplete structural case ledger")
    if source_summary["source_seed"] != 202610165050:
        raise ValueError("original R50 source seed changed")
    if source_summary["bootstrap_draw_seed"] != 202610165051:
        raise ValueError("original R50 bootstrap draw seed changed")
    if source_summary["release_authorized"]:
        raise ValueError("research artifact authorized release")

    observed = defaultdict(dict)
    optimizer_start_slots = 0
    original_refusals = defaultdict(int)
    for row in cases:
        block, support = row["block"], row["support"]
        if row["source_status"] not in ("ok", "failed"):
            raise ValueError("invalid original source status")
        if len(row["intervals"]) != len(METHODS) or tuple(
            method["method"] for method in row["intervals"]
        ) != METHODS:
            raise ValueError("lost or reordered original interval arm")
        boot = row["bootstrap_refit_attempts"]
        if len(boot) != N_BOOT or {
            b["replicate"] for b in boot
        } != set(range(N_BOOT)):
            raise ValueError("invalid original 63-refit record sequence")
        if any(b["replicate"] != i for i, b in enumerate(boot)):
            raise ValueError("bootstrap pivot replication order was reordered")
        nuisance = (row["original_correct_nuisance"],
                    row["original_wrong_nuisance"])
        for family, data in zip(("correct", "misspecified"), nuisance):
            _verify_physical_starts(
                data["numerical_starts"], data.get("status", "not_attempted"),
                f"{block}:{support}:original-{family}",
                selected=data if data.get("status") == "accepted" else None,
            )
            optimizer_start_slots += N_STARTS
        for b in boot:
            _verify_physical_starts(
                b["numerical_starts"], b["status"],
                f"{block}:{support}:bootstrap-{b['replicate']}",
            )
            optimizer_start_slots += N_STARTS
            if b["status"] not in ("ok", "refused", "not_attempted"):
                raise ValueError("unregistered bootstrap status")
            if b["status"] == "ok" and not math.isfinite(
                float(b["signed_studentized_pivot"])
            ):
                raise ValueError("nonfinite accepted bootstrap pivot")
            original_refusals[(support, b["status"])] += 1

        truth = row.get("projected_focal_truth")
        for meth in row["intervals"]:
            name = meth["method"]
            if meth["status"] not in ("ok", "refused"):
                raise ValueError("invalid original interval status")
            if meth["status"] == "ok":
                if truth is None:
                    raise ValueError("accepted interval without true simulation target")
                point = float(meth["point"])
                half = float(meth["half_width"])
                crit = float(meth["critical_value"])
                if not all(map(math.isfinite, (point, half, crit))) or min(half, crit) <= 0:
                    raise ValueError("nonpositive or nonfinite accepted interval")
                incl = abs(point - float(truth)) <= half
                if incl != meth["truth_included"]:
                    raise ValueError("original reported truth inclusion does not match interval")
            else:
                if meth["truth_included"] is not False:
                    raise ValueError("failed interval counted as containing truth")
            observed[(support,name)][block] = meth

        first, last = row["intervals"][2:4]
        pivots = [float(b["signed_studentized_pivot"]) for b in boot
                  if b["status"] == "ok"]
        if first["status"] == "ok" or last["status"] == "ok":
            if len(pivots) != N_BOOT or first["status"] != "ok" or last["status"] != "ok":
                raise ValueError("incomplete bootstrap intervals condition on successes")
            _assert_close(first["critical_value"],
                          _q_linear([abs(v) for v in pivots[:31]], .9),
                          f"{block}:{support}:31")
            _assert_close(last["critical_value"],
                          _q_linear([abs(v) for v in pivots], .9),
                          f"{block}:{support}:63")
        elif first["status"] != "refused" or last["status"] != "refused":
            raise ValueError("the two bootstrap arms do not share original refusals")

    if optimizer_start_slots != 6240:
        raise ValueError("wrong total original optimizer start slots")
    results = {}
    for support in SUPPORT:
        source = source_summary["strata"][support]
        results[support] = {}
        for name in METHODS:
            original = source["methods"][name]
            records = [observed[(support, name)][i] for i in range(BLOCKS)]
            passed = [x for x in records if x["status"] == "ok"]
            included = sum(x["truth_included"] for x in passed)
            _assert_close(original["truth_inclusion_numerator"], included,
                          f"{support}/{name}/count")
            if original["accepted"] != len(passed):
                raise ValueError(f"{support}/{name} accepted-record count mismatch")
            if original["failed_or_refused"] != BLOCKS-len(passed):
                raise ValueError(f"{support}/{name} refusal count mismatch")
            _assert_close(original["all_block_coverage_fraction"], included/BLOCKS,
                          f"{support}/{name}/full-denominator")
            for a,b in zip(original["Wilson95_MC"], _wilson(included, BLOCKS)):
                _assert_close(a,b,f"{support}/{name}/Wilson")
            width = (sum(x["half_width"] for x in passed)/len(passed)
                     if passed else None)
            if width is not None:
                _assert_close(original["mean_half_width_success_only"],width,
                              f"{support}/{name}/width")
            elif original["mean_half_width_success_only"] is not None:
                raise ValueError("empty accepted sample has nonempty mean width")
            results[support][name] = {
                "included": included, "denominator": BLOCKS,
                "accepted": len(passed), "refused": BLOCKS-len(passed),
                "Wilson95": _wilson(included, BLOCKS),
                "mean_half_width_success_only": width,
            }
        for status in ("ok", "refused", "not_attempted"):
            key = ("bootstrap_refit_successes" if status=="ok" else
                   "bootstrap_refit_refused" if status=="refused" else
                   "bootstrap_refit_not_attempted")
            if source[key] != original_refusals[(support,status)]:
                raise ValueError(f"{support}: bootstrap {status} source summary mismatch")
        qratios = [
            observed[(support,METHODS[3])][i]["critical_value"] /
            observed[(support,METHODS[2])][i]["critical_value"]
            for i in range(BLOCKS) if all(
                observed[(support,method)][i]["status"] == "ok"
                for method in (METHODS[2],METHODS[3])
            )
        ]
        if qratios:
            _assert_close(source["31_vs_63_critical_ratio_median"],
                          median(qratios), f"{support}:31vs63 ratio")
        disagreement = sum(
            observed[(support,METHODS[2])][i]["truth_included"] !=
            observed[(support,METHODS[3])][i]["truth_included"]
            for i in range(BLOCKS) if all(
                observed[(support,method)][i]["status"] == "ok"
                for method in (METHODS[2],METHODS[3])
            )
        )
        if disagreement != source["31_vs_63_truth_inclusion_disagreements"]:
            raise ValueError(f"{support}:31vs63 disagreement mismatch")
    return {
        "source_commit": source_sha,
        "sha256_verified": len(digests),
        "original_independent_primitive_blocks": BLOCKS,
        "paired_source_cases": len(cases),
        "interval_slots": sum(len(r["intervals"]) for r in cases),
        "bootstrap_refit_attempts": sum(len(r["bootstrap_refit_attempts"]) for r in cases),
        "optimizer_start_slots": optimizer_start_slots,
        "strata": results,
        "independent_postprocess_only": True,
        "coverage_calibrated": False,
        "release_authorized": False,
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--original-artifact-dir",type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(audit_original(args.original_artifact_dir),
                     sort_keys=True,indent=2))


if __name__ == "__main__":
    main()
