"""Independent qualification tranche for native sparse MFPCA.

The preceding threshold-free pilot freezes the signal-subspace definition and
these qualification limits. This script uses distinct random seeds so the same
simulation realizations do not both define and pass the gate.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from run_sparse_mfpca_recovery import (
    SIGNAL_RELATIVE_EIGENVALUE_FLOOR,
    _recovery_row,
)


RHO_LEVELS = (0.0, 0.3, 0.6, 0.9)
REPLICATES_PER_RHO = 3
QUALIFICATION_SEED_START = 311000

QUALIFICATION_LIMITS = {
    "mean_rmse_max": 0.20,
    "full_block_covariance_relative_error_max": 0.50,
    "cross_covariance_error_scaled_to_marginal_max": 0.40,
    "signal_functional_subspace_min_principal_cosine_min": 0.95,
    "signal_score_subspace_min_principal_cosine_min": 0.95,
    "score_failure_rate_max": 0.0,
    "block_psd_relative_operator_correction_max": 0.10,
}


def _evaluate_row(row):
    checks = {
        "mean_rmse": (
            row["mean_rmse"] <= QUALIFICATION_LIMITS["mean_rmse_max"]
        ),
        "full_block_covariance_relative_error": (
            row["full_block_covariance_relative_error"]
            <= QUALIFICATION_LIMITS[
                "full_block_covariance_relative_error_max"
            ]
        ),
        "cross_covariance_error_scaled_to_marginal": (
            row["cross_covariance_error_scaled_to_marginal"]
            <= QUALIFICATION_LIMITS[
                "cross_covariance_error_scaled_to_marginal_max"
            ]
        ),
        "signal_functional_subspace": (
            row["signal_functional_subspace_min_principal_cosine"]
            >= QUALIFICATION_LIMITS[
                "signal_functional_subspace_min_principal_cosine_min"
            ]
        ),
        "signal_score_subspace": (
            row["signal_score_subspace_min_principal_cosine"]
            >= QUALIFICATION_LIMITS[
                "signal_score_subspace_min_principal_cosine_min"
            ]
        ),
        "score_failure_rate": (
            row["score_failure_rate"]
            <= QUALIFICATION_LIMITS["score_failure_rate_max"]
        ),
        "block_psd_relative_operator_correction": (
            row["block_psd_relative_operator_correction"]
            <= QUALIFICATION_LIMITS[
                "block_psd_relative_operator_correction_max"
            ]
        ),
    }
    return checks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        default="sparse-mfpca-qualification",
    )
    args = parser.parse_args()

    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)

    rows = []
    scenario_index = 0
    for rho in RHO_LEVELS:
        for replicate in range(REPLICATES_PER_RHO):
            seed = (
                QUALIFICATION_SEED_START
                + scenario_index * 100
                + replicate
            )
            row = _recovery_row(rho, seed)
            checks = _evaluate_row(row)
            row["replicate"] = replicate
            row["qualification_checks"] = checks
            row["qualification_pass"] = bool(all(checks.values()))
            rows.append(row)
        scenario_index += 1

    flat_rows = []
    for row in rows:
        flat = {
            key: value
            for key, value in row.items()
            if not isinstance(value, (list, dict))
        }
        for name, passed in row["qualification_checks"].items():
            flat[f"check_{name}"] = passed
        flat_rows.append(flat)
    pd.DataFrame(flat_rows).to_csv(
        output / "sparse_mfpca_qualification.csv",
        index=False,
    )

    failed = [
        {
            "rho_xy": row["rho_xy"],
            "replicate": row["replicate"],
            "seed": row["seed"],
            "failed_checks": [
                name
                for name, passed in row["qualification_checks"].items()
                if not passed
            ],
        }
        for row in rows
        if not row["qualification_pass"]
    ]
    payload = {
        "schema_version": 1,
        "audit": "native sparse multivariate FPCA independent qualification",
        "qualification_gate": True,
        "pilot_seeds_reused": False,
        "signal_relative_eigenvalue_floor": (
            SIGNAL_RELATIVE_EIGENVALUE_FLOOR
        ),
        "signal_subspace_definition": (
            "truth eigenvalue >= 0.05 times the leading truth eigenvalue; "
            "weaker requested components remain reported as tail diagnostics"
        ),
        "rho_levels": list(RHO_LEVELS),
        "replicates_per_rho": REPLICATES_PER_RHO,
        "seed_start": QUALIFICATION_SEED_START,
        "limits": QUALIFICATION_LIMITS,
        "scenarios": rows,
        "failed_scenarios": failed,
        "qualification_pass": len(failed) == 0,
        "interpretation": (
            "Pass/fail applies to the predeclared signal subspace and block "
            "recovery/conditioning contract. Weak-tail components remain "
            "visible but do not define qualification when their truth "
            "eigenvalue is below the frozen relative-signal floor."
        ),
    }
    (output / "sparse_mfpca_qualification.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2))

    if failed:
        raise SystemExit(
            "sparse MFPCA independent qualification failed: "
            + json.dumps(failed)
        )


if __name__ == "__main__":
    main()
