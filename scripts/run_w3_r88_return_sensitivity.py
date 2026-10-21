"""W3 R88 prospectively frozen synthetic return-selection sensitivity grid.

Research only; conditional point-estimate sensitivity, not MNAR identification,
not a usable method for missing gaze reconstruction, and not band calibration.
Uses fresh primitive sources and the unchanged R87 scientific score functions.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path

import numpy as np

from scripts import run_w3_r87_audit_return_nonresponse as r87

STUDY = "W3_R88_CONDITIONAL_RETURN_SENSITIVITY_NEW_SOURCE"
BLOCKS = 32
CONFIGS = ("curve_standard", "participant_standard")
MECHANISMS = ("MAR", "MNAR")
AUDIT_LEVELS = (.25, .5)
ASSUMED_GAMMAS = (0., .675, 1.35, 2.025)
GENERATING_GAMMA = 1.35
SOURCES = {"source": 202610218880, "mask": 202610218881,
           "secondary": 202610218882, "assignment": 202610218883,
           "return": 202610218884}
SHARDS = tuple((i, i + 4) for i in range(0, BLOCKS, 4))
SUPPORT = "two_anchors"
VARIANCE = "predictor_heteroskedastic"
ROWS_PER_BLOCK_CONFIG = len(MECHANISMS) * len(AUDIT_LEVELS) * len(ASSUMED_GAMMAS)
N_SOURCES = BLOCKS * len(CONFIGS)
N_RECORDS = N_SOURCES * ROWS_PER_BLOCK_CONFIG


def stream_seed(block, config, domain):
    if type(block) is not int or block not in range(BLOCKS):
        raise ValueError("R88 invalid primitive block")
    if config not in CONFIGS or domain not in SOURCES:
        raise ValueError("R88 invalid configuration or random stream")
    return SOURCES[domain] + 1000003 * block + 10007 * CONFIGS.index(config)


def sigmoid(z):
    return 1. / (1. + np.exp(-np.clip(z, -35., 35.)))


def new_source(block, config):
    """Fresh independent generator matching the R87 source family, never R87 seeds."""
    n, trials, design = r87.info(config)
    rng = np.random.default_rng(stream_seed(block, config, "source"))
    x = rng.uniform(-.95, .95, size=n)
    x[0] = -4.
    x[-1] = 4.
    X = np.column_stack((np.ones(n), x))
    beta = r87.truth_coefficients()
    mean = beta[0][None] + x[:, None, None] * beta[1][None]
    scale = 1. + .75 * np.abs(x)
    latent = np.zeros((n, len(r87.T), 2))
    if design == "participant":
        g = rng.normal(0., 1., size=(n, 1, 2))
        mixed = np.empty_like(g)
        mixed[..., 0] = g[..., 0]
        mixed[..., 1] = .45 * g[..., 0] + np.sqrt(1. - .45 ** 2) * g[..., 1]
        latent = .065 * (1. + .35 * r87.T[None, :, None]) * mixed
    white = rng.normal(0., 1., size=(n, trials, len(r87.T), 2))
    noise = np.einsum("tu,njud->njtd", r87.trial_chol(), white, optimize=True)
    noise = r87.mix_trials(noise) * r87.trial_time_sd()[None, None, :, None]
    radial = np.sqrt(3. / rng.chisquare(5, size=n))
    indicator = (rng.random(n) < .08).astype(float) - .08
    profile = (.75 + .25 * r87.T[:, None]) * np.array([1., -.65])[None]
    shock = .16 * indicator[:, None, None] * profile[None]
    Y = mean[:, None] + scale[:, None, None, None] * (
        radial[:, None, None, None] * (latent[:, None] + noise)
        + shock[:, None]
    )
    if Y.shape != (n, trials, len(r87.T), 2):
        raise AssertionError("R88 source dimensional contract failed")
    return X, Y


def prepare(block, config):
    """Generate complete source and independently seeded selection uniforms."""
    X, Y = new_source(block, config)
    shape = Y.shape
    masks_u = np.random.default_rng(stream_seed(block, config, "mask")).random(shape)
    initial_u = np.random.default_rng(stream_seed(block, config, "secondary")).random(shape)
    assignment_u = np.random.default_rng(stream_seed(block, config, "assignment")).random(shape)
    completion_u = np.random.default_rng(stream_seed(block, config, "return")).random(shape)
    return X, Y, masks_u, initial_u, assignment_u, completion_u


def return_probability(X, Y, pilot, assumed_gamma):
    """Known recorded baseline plus *assumed* outcome coefficient.

    The baseline is simulator-calibrated, NOT estimated or certified from field
    data. The outcome is used by this function to define hypothetical return
    probabilities; in fitting it is evaluated ONLY for returned outcomes.
    """
    if not np.isfinite(assumed_gamma) or abs(assumed_gamma) > 3.:
        raise ValueError("R88 outside prespecified return sensitivity support")
    base = r87.completion_probability(X, Y, pilot, "recorded")
    logit = np.log(base / (1. - base))
    fitted = pilot[None, None, :, :, 0] + (
        X[:, 1, None, None, None] * pilot[None, None, :, :, 1]
    )
    residual = np.tanh((Y - fitted) / .08)
    return sigmoid(logit + assumed_gamma * residual)


def fit_assumption(X, Y, loss, initial, returned, pilot, allowed, q, gamma):
    """All scores use originally visible or actually returned Y only."""
    proposed = return_probability(X, Y, pilot, gamma)
    sampled = q * proposed
    a, g, ok, n, score, info, bound = r87.propensity_model(
        X, Y, loss, initial, returned, pilot, allowed, sampled
    )
    if not ok:
        return {"recovery_alpha": None, "recovery_gamma": None,
                "recovery_converged": False, "recovery_n": n,
                "first_stage_delta": None, "delta_converged": False,
                "delta_n": 0, "delta_score": None,
                "delta_boundary_refusal": False,
                "recovery_boundary_refusal": bound}
    residual = np.tanh((Y - (
        pilot[None, None, :, :, 0]
        + X[:, 1, None, None, None] * pilot[None, None, :, :, 1]
    )) / .08)
    p_rec = sigmoid(a + g * residual)
    union = p_rec + (1. - p_rec) * sampled
    d, dc, ds, di, dn, db = r87.first_stage_delta(
        X, Y, loss, initial | returned, pilot, allowed, union
    )
    return {"recovery_alpha": a, "recovery_gamma": g,
            "recovery_converged": True, "recovery_n": n,
            "first_stage_delta": d, "delta_converged": dc,
            "delta_n": dn, "delta_score": ds,
            "delta_boundary_refusal": db, "recovery_boundary_refusal": bound}


def evaluate(block, config):
    X, Y, mask_u, sec_u, assign_u, return_u = prepare(block, config)
    rows = []
    for mechanism in MECHANISMS:
        loss = mask_u < r87.probabilities(X, Y, mechanism)
        if not r87.native_refusal(X, Y, loss, config):
            raise AssertionError("R88 unmodified stable API accepted incomplete gaze")
        pilot, allowed, _ = r87.original_visible_pilot(X, Y, loss)
        if not bool(np.all(allowed)):
            raise ValueError("R88 source pilot grid refused: record explicit shard failure")
        initial = loss & (sec_u < r87.actual_recovery_prob(X, Y))
        true_return = return_probability(X, Y, pilot, GENERATING_GAMMA)
        for q in AUDIT_LEVELS:
            assigned = loss & ~initial & (assign_u < q)
            returned = assigned & (return_u < true_return)
            if np.any(returned & initial) or np.any(returned & ~assigned):
                raise AssertionError("R88 audit subset invariant broken")
            held_out = loss & ~initial & ~returned
            for assumed in ASSUMED_GAMMAS:
                fitted = fit_assumption(
                    X, Y, loss, initial, returned, pilot, allowed, q, assumed
                )
                d = fitted["first_stage_delta"]
                target = 0. if mechanism == "MAR" else 1.1
                rows.append({
                    "study": STUDY, "block": block, "config": config,
                    "mechanism": mechanism, "audit_fraction": q,
                    "assumed_return_gamma": assumed,
                    "generating_return_gamma_simulator_only": GENERATING_GAMMA,
                    "assumed_gamma_equals_simulator_truth": assumed == GENERATING_GAMMA,
                    "source_seed": stream_seed(block, config, "source"),
                    "mask_seed": stream_seed(block, config, "mask"),
                    "secondary_seed": stream_seed(block, config, "secondary"),
                    "assignment_seed": stream_seed(block, config, "assignment"),
                    "return_seed": stream_seed(block, config, "return"),
                    "complete_Y_sha256": r87.digest(Y),
                    "complete_X_sha256": r87.digest(X),
                    "original_missing_sha256": r87.mask_digest(loss),
                    "original_pilot_sha256": r87.digest(pilot),
                    "initial_return_sha256": r87.mask_digest(initial),
                    "assigned_sha256": r87.mask_digest(assigned),
                    "returned_sha256": r87.mask_digest(returned),
                    "original_missing_n": int(loss.sum()),
                    "initial_return_n": int(initial.sum()),
                    "audit_assigned_n": int(assigned.sum()),
                    "audit_returned_n": int(returned.sum()),
                    "audit_nonreturn_n": int((assigned & ~returned).sum()),
                    "unmeasured_missing_n": int(held_out.sum()),
                    "true_first_stage_delta_simulator_only": target,
                    "delta_signed_error": None if d is None else d - target,
                    "assumption_is_not_identified_from_audit_returns": True,
                    "known_return_baseline_simulation_assumption": True,
                    "unreturned_Y_used_by_fitted_score": False,
                    "nominal_confidence_band_claim": False,
                    "release_authorized": False,
                    **fitted,
                })
    if len(rows) != ROWS_PER_BLOCK_CONFIG:
        raise AssertionError("R88 prospective source factorial truncated")
    return rows


def summarize(rows):
    expected = {(b, c, m, q, gamma)
                for b in range(BLOCKS) for c in CONFIGS
                for m in MECHANISMS for q in AUDIT_LEVELS
                for gamma in ASSUMED_GAMMAS}
    key = lambda r: (r["block"], r["config"], r["mechanism"],
                     r["audit_fraction"], r["assumed_return_gamma"])
    keys = [key(r) for r in rows]
    if len(rows) != N_RECORDS or len(set(keys)) != N_RECORDS or set(keys) != expected:
        raise ValueError("R88 incomplete or duplicated original source denominator")
    for row in rows:
        if (row["study"] != STUDY or row["release_authorized"] is not False
            or row["nominal_confidence_band_claim"] is not False
            or row["unreturned_Y_used_by_fitted_score"] is not False
            or row["assumption_is_not_identified_from_audit_returns"] is not True
            or row["known_return_baseline_simulation_assumption"] is not True
            or row["source_seed"] != stream_seed(row["block"], row["config"], "source")
            or row["mask_seed"] != stream_seed(row["block"], row["config"], "mask")
            or row["audit_returned_n"] > row["audit_assigned_n"]
            or row["audit_assigned_n"] - row["audit_returned_n"] != row["audit_nonreturn_n"]):
            raise ValueError("R88 provenance, measurement, or release gate failed")
    output = {}
    for c in CONFIGS:
        output[c] = {}
        for m in MECHANISMS:
            output[c][m] = {}
            for q in AUDIT_LEVELS:
                cell = [r for r in rows if r["config"] == c
                        and r["mechanism"] == m and r["audit_fraction"] == q]
                # All four assumed mechanisms see *exactly the same* returned values.
                for block in range(BLOCKS):
                    group = [r for r in cell if r["block"] == block]
                    if len(group) != len(ASSUMED_GAMMAS):
                        raise ValueError("R88 block-level pairing lost")
                    paired_fields = ("complete_Y_sha256", "original_missing_sha256",
                                     "initial_return_sha256", "assigned_sha256",
                                     "returned_sha256", "audit_returned_n")
                    if any(len({r[field] for r in group}) != 1 for field in paired_fields):
                        raise ValueError("R88 gamma strategies did not share measurements")
                output[c][m][str(q)] = {}
                for g in ASSUMED_GAMMAS:
                    group = [r for r in cell if r["assumed_return_gamma"] == g]
                    valid = [r for r in group if r["delta_converged"]
                             and r["first_stage_delta"] is not None]
                    def mean(field, collection):
                        return float(np.mean([r[field] for r in collection])) if collection else None
                    output[c][m][str(q)][str(g)] = {
                        "independent_primitive_source_blocks": BLOCKS,
                        "first_stage_completed": len(valid),
                        "first_stage_refused": BLOCKS - len(valid),
                        "mean_delta": mean("first_stage_delta", valid),
                        "mean_signed_error": mean("delta_signed_error", valid),
                        "mean_assigned": mean("audit_assigned_n", group),
                        "mean_returned": mean("audit_returned_n", group),
                        "simulator_true_gamma": g == GENERATING_GAMMA,
                    }
    return {
        "study": STUDY, "complete_independent_sources": N_SOURCES,
        "primitive_blocks_per_fixed_cell": BLOCKS,
        "paired_MAR_MNAR_masks": N_SOURCES * len(MECHANISMS),
        "repeated_method_records_not_independent": N_RECORDS,
        "assumed_return_gamma_values": list(ASSUMED_GAMMAS),
        "generating_return_gamma_simulator_only": GENERATING_GAMMA,
        "known_recorded_return_baseline_is_simulation_assumption": True,
        "unidentified_return_sensitivity_not_estimated_from_data": True,
        "no_valid_MNAR_identification_or_confidence_band_claim": True,
        "stable_1_1_0_api_unchanged": True,
        "release_authorized": False, "results": output,
    }


def shard(out, start, stop):
    if (start, stop) not in SHARDS:
        raise ValueError("R88 source block bounds outside frozen shards")
    out.mkdir(parents=True, exist_ok=True)
    rows = [r for b in range(start, stop) for c in CONFIGS for r in evaluate(b, c)]
    raw = (json.dumps(rows, sort_keys=True, allow_nan=False) + "\n").encode()
    (out / "cases.json").write_bytes(raw)
    manifest = {"study": STUDY, "start": start, "stop": stop,
                "rows": len(rows), "sha256": sha256(raw).hexdigest(),
                "master_seeds": SOURCES,
                "checkout": os.environ.get("GITHUB_SHA", "unverified-local")}
    (out / "manifest.json").write_text(json.dumps(manifest, sort_keys=True) + "\n")


def aggregate(out, parts):
    manifests = sorted(parts.glob("*/manifest.json"))
    if len(manifests) != len(SHARDS):
        raise ValueError("R88 all eight original science shards required")
    checkout = os.environ.get("GITHUB_SHA", "unverified-local")
    all_rows, seen = [], set()
    for f in manifests:
        m = json.loads(f.read_text())
        pair = (m["start"], m["stop"])
        if (pair not in SHARDS or pair in seen or m["study"] != STUDY
            or m["master_seeds"] != SOURCES or m["checkout"] != checkout):
            raise ValueError("R88 invalid or mixed-checkout shard")
        seen.add(pair)
        raw = (f.parent / "cases.json").read_bytes()
        if sha256(raw).hexdigest() != m["sha256"]:
            raise ValueError("R88 original source integrity failure")
        part = json.loads(raw)
        if len(part) != (pair[1] - pair[0]) * len(CONFIGS) * ROWS_PER_BLOCK_CONFIG:
            raise ValueError("R88 truncated science source shard")
        all_rows.extend(part)
    report = summarize(all_rows)
    out.mkdir(parents=True, exist_ok=True)
    for name, payload in (
        ("cases.json", json.dumps(all_rows, allow_nan=False, sort_keys=True) + "\n"),
        ("summary.json", json.dumps(report, allow_nan=False, sort_keys=True, indent=2) + "\n"),
        ("source-commit.txt", checkout + "\n"),
    ):
        (out / name).write_text(payload)
    (out / "SHA256SUMS").write_text("".join(
        sha256((out / name).read_bytes()).hexdigest() + "  " + name + "\n"
        for name in ("cases.json", "summary.json", "source-commit.txt")
    ))
    print(json.dumps(report, sort_keys=True))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True, type=Path)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--start", type=int)
    mode.add_argument("--merge-parts", type=Path)
    p.add_argument("--stop", type=int)
    args = p.parse_args()
    if args.merge_parts is not None:
        aggregate(args.out, args.merge_parts)
    elif args.stop is not None:
        shard(args.out, args.start, args.stop)
    else:
        p.error("--start requires --stop")


if __name__ == "__main__":
    main()
