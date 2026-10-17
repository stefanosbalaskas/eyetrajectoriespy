"""Read-only immutable ORIGINAL R58 boundary likelihood reference audit.

Does not import the R58 generator, R57 fits, R35/R37 REML objectives or
the source summarizer. Audits archived optimizer scores, source identities,
all SHA256, 576 starts, deviance and MC Wilson bookkeeping. Does NOT audit
raw native responses (not present in the archived case JSON), validate a
half-chi-square reference, infer statistical power, or qualify public APIs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

SOURCE_CHECKOUT = "c1d4c0f5f7805d1f2dd746e6208f0087c68395d6"
ORIGINAL_RUN = 39027935413
ORIGINAL_ARTIFACT = 12098994180
SEED = 202610175858
BLOCKS = 24
SUPPORT = ("ordinary_dependent", "extreme_dependent")
STATES = ("true_zero", "true_positive")
STUDY = "W3_R58_NEW_INDEPENDENT_GAUSSIAN_BOUNDARY_REFERENCE_STRESS"
EXPECTED = {(b, s, v) for b in range(BLOCKS) for s in SUPPORT for v in STATES}
NULL_STARTS = ("null_compact", "null_spread")
ALT_STARTS = ("alt_at_exact_zero", "alt_tiny_positive",
              "alt_positive", "alt_wide")
LOW = math.exp(-13.8)
HIGH = math.exp(7.)
CRITICAL = 2.70554345409542
KKT_TOL = 0.001
NLL_TOL = 0.001
RECON_TOL = 1e-6
NEST_TOL = 1e-5
Z95 = 1.959963984540054


def close(x, y, label, *, atol=1e-8, rtol=1e-9):
    if (x is None or y is None or
        not math.isfinite(float(x)) or not math.isfinite(float(y)) or
        not math.isclose(float(x), float(y), rel_tol=rtol, abs_tol=atol)):
        raise ValueError("R58 independent original mismatch: " + label)


def verify_source(folder):
    folder = Path(folder)
    required = {"cases.json", "summary.json", "source-commit.txt"}
    entries = (folder / "SHA256SUMS").read_text().splitlines()
    if len(entries) != 3:
        raise ValueError("R58 original source SHA256 manifest incomplete")
    digest = {}
    for line in entries:
        h, sep, name = line.partition("  ")
        if not sep or name not in required or name in digest or len(h) != 64:
            raise ValueError("R58 original manifest member invalid")
        try:
            int(h, 16)
        except ValueError as exc:
            raise ValueError("R58 original nonhex SHA256") from exc
        found = hashlib.sha256((folder / name).read_bytes()).hexdigest()
        if found != h:
            raise ValueError("R58 original evidence SHA256 mismatch: " + name)
        digest[name] = found
    if set(digest) != required:
        raise ValueError("R58 original SHA256 members incomplete")
    if (folder / "source-commit.txt").read_text().strip() != SOURCE_CHECKOUT:
        raise ValueError("R58 original checkout not the frozen PR merge commit")
    return digest


def projected_kkt(ratios, physical_score, model):
    bounds = [(LOW, HIGH)] * 3 + (
        [(0., 100.)] if model == "nonnegative" else [])
    if (not isinstance(ratios, list) or
        len(ratios) != len(bounds) or
        not isinstance(physical_score, list) or
        len(physical_score) != len(bounds)):
        raise ValueError("R58 original score dimension mismatch")
    max_grad = 0.
    for theta, grad, (lo, hi) in zip(ratios, physical_score, bounds):
        theta, grad = float(theta), float(grad)
        if (not math.isfinite(theta) or not math.isfinite(grad) or
            theta < lo - 1e-9 or theta > hi + 1e-9):
            raise ValueError("R58 original variance ratio or score invalid")
        if theta <= lo + 1e-9:
            grad = min(grad, 0.)
        elif theta >= hi - 1e-9:
            grad = max(grad, 0.)
        max_grad = max(max_grad, abs(grad))
    return max_grad


def audit_fit(fit, model, label):
    names = NULL_STARTS if model == "exact_zero" else ALT_STARTS
    if (fit["model"] != model or
        [v["label"] for v in fit["original_starts"]] != list(names) or
        fit["status"] not in ("accepted", "refused")):
        raise ValueError("R58 original Gaussian fit/start contract: " + label)
    observed, eligible = [], []
    worst_kkt = 0.
    for start in fit["original_starts"]:
        nll = start["negative_loglik"]
        if nll is None:
            if start["status"] == "ok":
                raise ValueError("R58 original optimizer accepted with no likelihood")
            continue
        if not math.isfinite(float(nll)):
            raise ValueError("R58 original nonfinite NLL")
        observed.append(start)
        close(nll, start["reconstructed_loglik"], label + "/NLL reconstruction",
              atol=RECON_TOL + 1e-8)
        calc_kkt = projected_kkt(start["ratios"],
                                 start["physical_score"], model)
        close(calc_kkt, start["physical_projected_KKT"],
              label + "/physical projected KKT", atol=2e-7, rtol=5e-7)
        worst_kkt = max(worst_kkt, calc_kkt)
        good = (start["status"] == "ok" and
                start["optimizer_success"] is True and
                start["objective_reconstruction_error"] <= RECON_TOL and
                calc_kkt <= KKT_TOL)
        if good:
            eligible.append(start)
    best = min((s["negative_loglik"] for s in observed), default=None)
    if best is None:
        if fit["status"] == "accepted":
            raise ValueError("R58 fake accepted no optimizer start")
        return {"status": "refused", "starts": len(names), "kkt": worst_kkt}
    close(best, fit["best_observed_multistart_NLL"], label + "/best NLL")
    eligible = [s for s in eligible
                if s["negative_loglik"] - best <= NLL_TOL + 1e-8]
    if fit["status"] == "refused":
        if eligible:
            raise ValueError("R58 original refused despite eligible start")
        return {"status": "refused", "starts": len(names), "kkt": worst_kkt}
    if not eligible:
        raise ValueError("R58 claimed accepted fit despite failed KKT")
    target = min(s["negative_loglik"] for s in eligible)
    close(target, fit["selected_NLL"], label + "/selected Gaussian NLL")
    choices = [s for s in eligible
               if s["label"] == fit["selected_start"]]
    if len(choices) != 1:
        raise ValueError("R58 fake accepted candidate label")
    chosen = choices[0]
    close(chosen["negative_loglik"], fit["selected_NLL"],
          label + "/selected candidate NLL")
    close(chosen["physical_projected_KKT"], fit["selected_physical_KKT"],
          label + "/selected physical KKT")
    for a, b in zip(chosen["ratios"][:3],
                    fit["selected_free_component_variance_ratios"]):
        close(a, b, label + "/free nuisance variance ratio")
    if fit["global_optimum_proven"] is not False:
        raise ValueError("R58 falsely certified global optimum")
    if model == "exact_zero":
        if (fit["selected_slope_ratio"] != 0 or
            fit["null_includes_exact_zero_variance"] is not True):
            raise ValueError("R58 model null does not fix exact zero")
    else:
        if fit["alternative_includes_structural_zero"] is not True:
            raise ValueError("R58 model alternative excludes zero")
        close(chosen["ratios"][3], fit["selected_slope_ratio"],
              label + "/alternative slope ratio")
    return {
        "status": "accepted", "starts": len(names),
        "nll": float(fit["selected_NLL"]),
        "slope": float(fit["selected_slope_ratio"]),
        "kkt": float(fit["selected_physical_KKT"]),
    }


def wilson(k, n):
    if type(k) is not int or type(n) is not int or not 0 <= k <= n:
        raise ValueError("R58 independent Wilson count invalid")
    if n == 0:
        return None
    p = k / n
    d = 1 + Z95**2/n
    center = (p + Z95**2/(2*n))/d
    hw = Z95*math.sqrt(p*(1-p)/n + Z95**2/(4*n*n))/d
    return [max(0., center-hw), min(1., center+hw)]


def median(values):
    seq = sorted(values)
    if not seq:
        return None
    m = len(seq) // 2
    return (seq[m] if len(seq) % 2 else (seq[m-1]+seq[m])/2)


def audit(folder):
    digest = verify_source(folder)
    rows = json.loads((Path(folder)/"cases.json").read_text())
    source_summary = json.loads((Path(folder)/"summary.json").read_text())
    ids = [(r["block"], r["support"], r["generating_state"]) for r in rows]
    if len(ids) != 96 or len(set(ids)) != 96 or set(ids) != EXPECTED:
        raise ValueError("R58 original source identities/denominator invalid")
    expected_summary = {
        "study": STUDY, "new_independent_source_seed": SEED,
        "new_independent_primitive_blocks": BLOCKS, "participants_per_block": 24,
        "predeclared_case_slots": 96, "recorded_case_slots": 96,
        "predeclared_nested_model_slots": 192, "recorded_nested_model_slots": 192,
        "predeclared_optimizer_start_slots": 576, "recorded_optimizer_start_slots": 576,
        "all_failure_inclusive_denominators_complete": True,
        "candidate_reference_validated": False,
        "pointwise_CR2_90pct_qualified": False,
        "simultaneous_CR2_90pct_qualified": False,
        "global_REML_optimum_proven": False,
        "release_authorized": False,
    }
    for key, value in expected_summary.items():
        if source_summary.get(key) != value:
            raise ValueError("R58 original source summary contract: " + key)
    close(source_summary["candidate_reference_critical_strict_greater"],
          CRITICAL, "R58 prespecified candidate threshold", atol=1e-11)
    results = []
    starts = 0
    maximum_selected_kkt = 0.
    paired = {}
    for case in rows:
        b, support, state = (
            case["block"], case["support"], case["generating_state"]
        )
        label = f"{b}/{support}/{state}"
        if case["study"] != STUDY:
            raise ValueError("R58 changed original study")
        if (case["new_independent_primitive_block"] is not True or
            case["paired_support_and_state_not_independent"] is not True or
            case["release_authorized"] is not False or
            case["pointwise_or_simultaneous_CR2_qualified"] is not False):
            raise ValueError("R58 false source/release claim")
        close(case["generating_slope_variance"],
              0. if state == "true_zero" else 0.002025,
              label + "/generating variance")
        paired.setdefault((b, support), {})[state] = (
            case["source_innovation_slope_L2"])
        if case["source_status"] not in ("ok", "failed"):
            raise ValueError("R58 unknown source state")
        a = audit_fit(case["null_fit"], "exact_zero", label+"/H0") if (
            case["null_fit"]["status"] != "not_attempted") else {
                "status": "not_attempted", "starts": 2}
        c = audit_fit(case["alternative_fit"], "nonnegative", label+"/H1") if (
            case["alternative_fit"]["status"] != "not_attempted") else {
                "status": "not_attempted", "starts": 4}
        starts += a["starts"] + c["starts"]
        for fit in (a, c):
            maximum_selected_kkt = max(maximum_selected_kkt, fit.get("kkt", 0.))
        comp = case["nested_comparison"]
        accepted = a["status"] == c["status"] == "accepted"
        if not accepted and comp["status"] == "ok":
            raise ValueError("R58 false accepted nested comparison")
        row = {
            "block": b, "support": support, "state": state,
            "accepted": False, "rejected": None,
            "selected_zero": None, "gap": None,
            "H0_status": a["status"], "H1_status": c["status"],
            "source_status": case["source_status"],
        }
        if accepted:
            raw = 2*(a["nll"] - c["nll"])
            close(raw, comp["raw_signed_deviance"],
                  label+"/raw signed deviance", atol=1e-7)
            if raw < -NEST_TOL:
                if comp["status"] != "refused":
                    raise ValueError("R58 improper nested monotonicity acceptance")
            else:
                if comp["status"] != "ok":
                    raise ValueError("R58 unrecorded valid nested deviance")
                gap = max(0., raw)
                close(gap, comp["nonnegative_deviance"],
                      label+"/nonnegative deviance", atol=1e-8)
                candidate_p = (1. if gap == 0. else
                               0.5*math.erfc(math.sqrt(gap/2.)))
                close(candidate_p, comp["candidate_half_chi_square_p"],
                      label+"/candidate reference tail", atol=1e-10)
                rejected = bool(gap > CRITICAL)
                if (comp["candidate_nominal_005_rejection"] is not rejected or
                    comp["selected_exact_zero"] is not bool(c["slope"] <= 1e-10) or
                    comp["candidate_reference_qualified"] is not False):
                    raise ValueError("R58 false candidate null test classification")
                row.update(accepted=True, rejected=rejected,
                           selected_zero=bool(c["slope"] <= 1e-10), gap=gap)
        else:
            if (comp["candidate_nominal_005_rejection"] is not None or
                comp["candidate_half_chi_square_p"] is not None):
                raise ValueError("R58 numerical refusal reclassified as test")
        results.append(row)
    if starts != 576:
        raise ValueError("R58 did not retain all 576 original starts")
    if len(paired) != BLOCKS * len(SUPPORT) or any(
        set(pair) != set(STATES) or pair["true_zero"] != pair["true_positive"]
        for pair in paired.values()):
        raise ValueError("R58 original source/state pairing mismatch")
    strata = {}
    for support in SUPPORT:
        for state in STATES:
            subset = [r for r in results if
                      r["support"] == support and r["state"] == state]
            accepted = [r for r in subset if r["accepted"]]
            k, n = sum(r["rejected"] is True for r in accepted), len(accepted)
            zero = sum(r["selected_zero"] is True for r in accepted)
            refusals = BLOCKS - n
            output = {
                "independent_Gaussian_primitive_blocks": BLOCKS,
                "source_status_failures": sum(
                    r["source_status"] != "ok" for r in subset),
                "null_model_refusals": sum(
                    r["H0_status"] != "accepted" for r in subset),
                "alternative_model_refusals": sum(
                    r["H1_status"] != "accepted" for r in subset),
                "nested_reference_nonaccepted_or_refused": refusals,
                "accepted_comparisons": n,
                "candidate_reference_rejections": k,
                "candidate_reference_rejection_fraction_valid_only":
                    k/n if n else None,
                "wilson95_conditional_on_accepted_calculations":
                    wilson(k, n),
                "candidate_reference_mc_se_valid_only":
                    math.sqrt((k/n)*(1-k/n)/n) if n else None,
                "all_source_rejection_fraction_lower_if_refusals_not_rejected":
                    k/BLOCKS,
                "all_source_rejection_fraction_upper_if_refusals_rejected":
                    (k+refusals)/BLOCKS,
                "alternative_selected_exact_zero": zero,
                "zero_selection_fraction_valid_only": zero/n if n else None,
                "zero_selection_wilson95_valid_only": wilson(zero, n),
                "median_accepted_deviance":
                    median([r["gap"] for r in accepted]),
            }
            saved = source_summary["strata"][support + "/" + state]
            for key, value in output.items():
                actual = saved[key]
                if isinstance(value, list):
                    for v, a in zip(value, actual):
                        close(v, a, support+"/"+state+"/"+key, atol=5e-9)
                elif isinstance(value, (float, int)) and not isinstance(value, bool):
                    close(value, actual, support+"/"+state+"/"+key, atol=5e-9)
                elif value != actual:
                    raise ValueError("R58 false original summary: " + key)
            strata[support+"/"+state] = output
    return {
        "independent_read_only_original_R58_archive_audit_passed": True,
        "original_workflow_run": ORIGINAL_RUN,
        "original_artifact_id": ORIGINAL_ARTIFACT,
        "verified_SHA256": digest,
        "frozen_original_checkout": SOURCE_CHECKOUT,
        "independent_primitive_blocks": BLOCKS,
        "paired_variants_not_independent": True,
        "retained_source_variants": len(rows),
        "retained_H0_H1_model_slots": 2*len(rows),
        "retained_optimizer_start_slots": starts,
        "max_selected_physical_KKT": maximum_selected_kkt,
        "source_native_y_not_archived": True,
        "raw_Gaussian_source_replay_not_independently_verified": True,
        "candidate_half_chisquare_distribution_not_proved_or_qualified": True,
        "no_power_pointwise_or_simultaneous_CR2_release_claim": True,
        "release_authorized": False,
        "strata": strata,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    report = audit(args.original)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(args.out.read_text())


if __name__ == "__main__":
    main()
