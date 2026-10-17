"""R61-A independent, read-only ORIGINAL raw-native Gaussian H0 covariance audit.

Do NOT import R61, R60, R57, the original simulator, REML optimizer or its
_kernel helper. Independently rebuild participant WLS covariance from the
archived synthetic native arrays, solve H0 GLS, generate seeded standard
normal witnesses and verify all 192 block SPD/Cholesky identities + 16
weighted/whitened diagnostics against the frozen original archive.

Independent algebra and numerical replay of archived data is NOT an audit of
the *original* simulation's unrecorded latent random innovations, proof of
Gaussian model adequacy, a calibrated bootstrap p-value or CR2 inference.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from scipy.linalg import cho_factor, cho_solve, solve_triangular

ORIGINAL_RUN = 39068871584
FROZEN_CHECKOUT = "92af2f707a6e9c608e405b84693165b507900143"
STUDY = "W3_R61_GAUSSIAN_FITTED_H0_DRAW_COVARIANCE_FIDELITY"
SOURCE_SEED = 202610176161
DRAW_SEED = 202610176162
BLOCKS = 4
SUPPORT = ("ordinary_dependent", "extreme_dependent")
N_PARTICIPANTS = 24
WITNESS_PARTICIPANTS = (0, 23)
WITNESS_DRAWS = 1024
EXPECTED = {(b, s) for b in range(BLOCKS) for s in SUPPORT}
COV_TOL = 1e-8
BACKTRANSFORM_TOL = 2e-8


def close(x, y, what, *, atol=1e-9, rtol=1e-9):
    if x is None or y is None:
        raise ValueError("R61-A missing original numerical comparison " + what)
    if not math.isfinite(float(x)) or not math.isfinite(float(y)):
        raise ValueError("R61-A nonfinite numerical comparison " + what)
    if not math.isclose(float(x), float(y), abs_tol=atol, rel_tol=rtol):
        raise ValueError("R61-A numerical reconstruction mismatch " + what)


def verify_archive(root):
    root = Path(root)
    names = ("cases.json", "summary.json", "source-commit.txt")
    manifest = (root / "SHA256SUMS").read_text().splitlines()
    if len(manifest) != 3:
        raise ValueError("R61-A original immutable SHA256 source has wrong count")
    seen = {}
    for line in manifest:
        digest, separator, name = line.partition("  ")
        if not separator or name not in names or name in seen or len(digest) != 64:
            raise ValueError("R61-A invalid or duplicated original SHA256 member")
        try:
            int(digest, 16)
        except ValueError as exc:
            raise ValueError("R61-A non-hex SHA256 digest") from exc
        actual = hashlib.sha256((root / name).read_bytes()).hexdigest()
        if actual != digest:
            raise ValueError("R61-A immutable original source SHA256 mismatch " + name)
        seen[name] = actual
    if set(seen) != set(names):
        raise ValueError("R61-A required original evidence member absent")
    if (root / "source-commit.txt").read_text().strip() != FROZEN_CHECKOUT:
        raise ValueError("R61-A original PR merge checkout is not frozen source")
    return seen


def read_native(case):
    archive = case["native_synthetic_source"]
    names = ("X", "y", "w", "group", "time", "trial", "x")
    if set(archive) != set(names):
        raise ValueError("R61-A original raw-native variable contract incomplete")
    X = np.asarray(archive["X"], float)
    y, w, t, tr, x = (
        np.asarray(archive[k], float) for k in ("y", "w", "time", "trial", "x"))
    groups = np.asarray(archive["group"])
    rows = len(y)
    if (X.ndim != 2 or X.shape[0] != rows or rows <= X.shape[1]
        or any(a.shape != (rows,) for a in (w, t, tr, x, groups))
        or not all(np.isfinite(z).all() for z in (X, y, w, t, tr, x))
        or np.any(w <= 0) or not np.all(tr == np.round(tr))):
        raise ValueError("R61-A invalid raw synthetic native weighted source design")
    unique = np.unique(groups)
    if len(unique) != N_PARTICIPANTS:
        raise ValueError("R61-A original participant-cluster denominator changed")
    for g in unique:
        idx = np.flatnonzero(groups == g)
        if not np.allclose(x[idx], x[idx][0], atol=1e-12, rtol=0):
            raise ValueError("R61-A native predictor not constant per participant")
        if np.any(np.diff(t[idx]) < -1.1):
            # Trial-local times are sorted within trial, not necessarily across trials.
            raise ValueError("R61-A corrupted native temporal source structure")
    return X, y, w, groups, t, tr, x, unique


def independent_fitted_null_covariance(time, trial, x, weight, theta):
    """Rebuild from raw weights/time/trial: no shared R20/R57 kernel import."""
    root = np.sqrt(weight)
    shape = root * (1.0 + 0.30 * time)
    trial_equal = (trial[:, None] == trial[None, :]).astype(float)
    # The exact-zero null excludes participant x time predictor slope innovation.
    V = (theta[0] * np.outer(shape, shape)
         + theta[2] * (trial_equal * np.outer(root, root))
         + theta[3] * np.diag(weight))
    return (V + V.T) / 2.0


def recompute_case(case):
    label = str(case["block"]) + "/" + case["support"]
    if (case["study"] != STUDY or case["source_status"] != "accepted"
        or case["true_generating_random_slope_variance"] != 0.0
        or case["new_independent_Gaussian_primitive_block"] is not True
        or case["paired_leverage_same_primitive_not_independent"] is not True
        or case["null_test_size_or_power_qualified"] is not False
        or case["CR2_90pct_pointwise_or_simultaneous_qualified"] is not False
        or case["release_authorized"] is not False):
        raise ValueError("R61-A original source provenance/qualification mismatch " + label)
    X, y, w, groups, t, trial, x, group_labels = read_native(case)
    theta = np.asarray(case["fitted_H0_theta"], float)
    original_beta = np.asarray(case["fitted_H0_GLS_beta"], float)
    if (theta.shape != (4,) or original_beta.shape != (X.shape[1],)
        or not np.isfinite(theta).all() or not np.isfinite(original_beta).all()
        or theta[1] != 0 or np.any(theta[[0, 2, 3]] <= 0)):
        raise ValueError("R61-A fitted H0 nuisance must be SPD and slope EXACT ZERO")
    original_fit = case["observed_fit"]
    if original_fit["status"] != "accepted":
        raise ValueError("R61-A falsely accepted H0 native-source fit")
    original_h0 = original_fit["null_fit"]
    if original_h0["status"] != "accepted":
        raise ValueError("R61-A original H0 model not numerically accepted")
    if original_h0["selected_slope_ratio"] != 0:
        raise ValueError("R61-A original H0 excluded structural zero")
    reference = original_fit["observed_reference"]
    if reference is None or reference <= 0:
        raise ValueError("R61-A fitted H0 original reference absent")
    for got, ratio in zip(theta[[0, 2, 3]],
                          original_h0["selected_free_component_variance_ratios"]):
        close(got, float(reference) * float(ratio),
              label + "/null nuisance theta", atol=1e-8)

    q = X.shape[1]
    gram = np.zeros((q, q))
    score = np.zeros(q)
    cov_blocks = []
    max_identity_error = 0.
    for participant, group in enumerate(group_labels):
        idx = np.flatnonzero(groups == group)
        Z = X[idx] * np.sqrt(w[idx])[:, None]
        yy = y[idx] * np.sqrt(w[idx])
        V = independent_fitted_null_covariance(t[idx], trial[idx], x[idx], w[idx], theta)
        factor = cho_factor(V, lower=True, check_finite=True)
        L = np.tril(factor[0])
        identity_error = float(np.max(np.abs(L @ L.T - V)))
        if identity_error > COV_TOL:
            raise ValueError("R61-A independently rebuilt H0 Gaussian block mismatch")
        max_identity_error = max(max_identity_error, identity_error)
        gram += Z.T @ cho_solve(factor, Z)
        score += Z.T @ cho_solve(factor, yy)
        cov_blocks.append((participant, idx, L))
    beta = np.linalg.solve(gram, score)
    np.testing.assert_allclose(
        beta, original_beta, atol=2e-8, rtol=2e-8,
        err_msg="R61-A archived original GLS beta not independently reproduced",
    )
    if len(cov_blocks) != N_PARTICIPANTS or (
        case["n_original_participant_covariances"] != N_PARTICIPANTS
    ):
        raise ValueError("R61-A participant covariance count changed")
    close(case["maximum_H0_kernel_to_cholesky_covariance_error"],
          max_identity_error, label + "/all original covariance identities",
          atol=1e-11, rtol=1e-8)

    witnesses = case["fidelity_records"]
    if (len(witnesses) != len(WITNESS_PARTICIPANTS)
        or [v["participant"] for v in witnesses] != list(WITNESS_PARTICIPANTS)):
        raise ValueError("R61-A 16 original whitened-witness record slots incomplete")
    max_whitening_error = 0.
    values = []
    for witness in witnesses:
        pid = witness["participant"]
        _, idx, L = cov_blocks[pid]
        if (witness["native_cluster_rows"] != len(idx)
            or witness["gaussian_draws"] != WITNESS_DRAWS
            or witness["moments_are_descriptive_not_a_null_size_test"] is not True):
            raise ValueError("R61-A original Gaussian draw witness dimensions changed")
        seed = DRAW_SEED + 100003 * case["block"] + (
            739 * SUPPORT.index(case["support"]) + pid)
        if witness["independent_draw_seed"] != seed:
            raise ValueError("R61-A original Gaussian draw seed changed")
        # Independent replay directly from the archived native data & H0
        # nuisance covariance, not from the original R61 simulator module.
        rng = np.random.default_rng(seed)
        z = rng.standard_normal((WITNESS_DRAWS, len(idx)))
        weighted = z @ L.T
        synthetic = X[idx] @ beta + weighted / np.sqrt(w[idx])[None, :]
        recovered = (synthetic - X[idx] @ beta) * np.sqrt(w[idx])[None, :]
        z_again = solve_triangular(L, recovered.T, lower=True).T
        err = float(np.max(np.abs(z_again - z)))
        if err > BACKTRANSFORM_TOL:
            raise ValueError("R61-A source native/weighted whitening algebra inconsistent")
        mean = z_again.mean(axis=0)
        centered = z_again - mean[None, :]
        covariance = centered.T @ centered / (WITNESS_DRAWS - 1)
        d = len(idx)
        mean_rms = math.sqrt(float(np.mean(mean ** 2)))
        cov_rms = float(np.linalg.norm(
            covariance - np.eye(d), ord="fro") / math.sqrt(d))
        sampling_rms = math.sqrt((d + 1) / WITNESS_DRAWS)
        close(witness["max_weighted_backtransform_whitening_error"],
              err, label + "/whitening maximum", atol=8e-12)
        close(witness["empirical_whitened_mean_RMS"],
              mean_rms, label + "/whitened mean RMS", atol=5e-12)
        close(witness["empirical_whitened_covariance_Frobenius_RMS"],
              cov_rms, label + "/whitened covariance RMS", atol=5e-12)
        close(witness["theoretical_approx_Frobenius_RMS"],
              sampling_rms, label + "/sampling noise scale", atol=1e-12)
        values.append({"participant":pid, "whitening_error":err,
                       "mean_rms":mean_rms, "covariance_rms":cov_rms})
        max_whitening_error = max(max_whitening_error, err)
    return {"block":case["block"], "support":case["support"],
            "participant_covariances":len(cov_blocks),
            "max_covariance_identity_error":max_identity_error,
            "max_native_weighted_whitening_error":max_whitening_error,
            "n_empirical_witnesses":len(values),
            "witnesses":values}


def audit(root):
    hashes = verify_archive(root)
    archive = Path(root)
    original = json.loads((archive / "summary.json").read_text())
    cases = json.loads((archive / "cases.json").read_text())
    ids = [(x["block"], x["support"]) for x in cases]
    if len(ids) != 8 or len(set(ids)) != 8 or set(ids) != EXPECTED:
        raise ValueError("R61-A independent original Gaussian primitive identities missing")
    frozen = {
        "study": STUDY, "source_seed": SOURCE_SEED,
        "draw_seed": DRAW_SEED, "new_independent_Gaussian_primitive_blocks": BLOCKS,
        "paired_leverage_variants_not_independent": True,
        "planned_source_variants": 8, "recorded_source_variants": 8,
        "accepted_source_cases": 8, "refused_source_cases": 0,
        "participants_per_primitive_source": N_PARTICIPANTS,
        "planned_participant_covariance_identity_checks": 192,
        "completed_participant_covariance_identity_checks": 192,
        "planned_empirical_whitened_draw_witnesses": 16,
        "recorded_empirical_whitened_draw_witnesses": 16,
        "planned_Gaussian_draws_per_witness": WITNESS_DRAWS,
        "raw_synthetic_native_y_X_w_group_time_trial_x_archived": True,
        "fitted_H0_theta_and_GLS_beta_archived": True,
        "bootstrap_null_type_I_or_power_qualified": False,
        "pointwise_or_simultaneous_90pct_fitted_CR2_qualified": False,
        "release_authorized": False,
    }
    for k, v in frozen.items():
        if original.get(k) != v:
            raise ValueError("R61-A original scientific denominator changed: " + k)
    reconstructed = [recompute_case(case) for case in cases]
    maximum_covariance = max(v["max_covariance_identity_error"] for v in reconstructed)
    maximum_whitening = max(v["max_native_weighted_whitening_error"] for v in reconstructed)
    close(original["max_analytic_covariance_identity_error"],
          maximum_covariance, "all original covariance blocks", atol=1e-11)
    close(original["max_exact_weighted_backtransform_whitening_error"],
          maximum_whitening, "all weighted whitened original witnesses", atol=8e-12)
    return {
        "R61_original_immutable_native_Gaussian_fidelity_audit_passed": True,
        "original_science_workflow": ORIGINAL_RUN,
        "frozen_original_PR_merge_checkout": FROZEN_CHECKOUT,
        "immutable_original_evidence_SHA256": hashes,
        "independent_Gaussian_primitive_blocks": BLOCKS,
        "paired_original_source_variants": len(reconstructed),
        "source_participant_covariance_identities": sum(
            z["participant_covariances"] for z in reconstructed),
        "reconstructed_original_gaussian_witness_records": sum(
            z["n_empirical_witnesses"] for z in reconstructed),
        "Gaussian_draws_per_original_witness": WITNESS_DRAWS,
        "max_independent_analytic_covariance_identity_error": maximum_covariance,
        "max_independent_native_weighted_whitening_error": maximum_whitening,
        "synthetic_native_y_from_original_archive_used": True,
        "original_latent_Gaussian_innovations_not_archived": True,
        "source_randomness_distribution_not_statistically_qualified": True,
        "bootstrap_null_hypothesis_test_calibration_not_qualified": True,
        "CR2_pointwise_simultaneous_90pct_inference_not_qualified": True,
        "release_authorized": False,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--original", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    arg = p.parse_args()
    out = audit(arg.original)
    arg.out.parent.mkdir(parents=True, exist_ok=True)
    arg.out.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out, sort_keys=True))


if __name__ == "__main__":
    main()
