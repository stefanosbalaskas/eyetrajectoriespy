#!/usr/bin/env python3
"""Known-truth qualification for A3 observation-process diagnostics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from eyetrajectoriespy._observation_process_simulation import (
    observation_process_from_functional_simulation,
    simulate_informative_time_retention,
)
from eyetrajectoriespy.observation_process import diagnose_observation_process
from eyetrajectoriespy.simulate import simulate_functional_process


def _mean(time):
    time = np.asarray(time, dtype=float)
    return np.column_stack((0.4 + 0.1 * time, 0.6 - 0.05 * time))


def _phi_x(time):
    time = np.asarray(time, dtype=float)
    return np.column_stack((np.ones_like(time), np.zeros_like(time)))


def _phi_y(time):
    time = np.asarray(time, dtype=float)
    return np.column_stack((np.zeros_like(time), np.ones_like(time)))


def _functional_simulation(
    *,
    n_participants: int,
    n_time: int,
    missingness: dict[str, Any] | None,
    random_state: int,
):
    return simulate_functional_process(
        mean=_mean,
        eigenfunctions=(_phi_x, _phi_y),
        eigenvalues=(0.05, 0.02),
        truth_grid=np.linspace(0.0, 1.0, n_time),
        n_participants=n_participants,
        trials_per_participant=2,
        dimension_names=("x", "y"),
        coordinate_system="normalized",
        time_unit="normalized",
        observation_design="dense",
        measurement_noise_sd=(0.01, 0.01),
        missingness=missingness,
        random_state=random_state,
    )


def _assert_accounting(simulated, result, *, name: str) -> None:
    summary = result.global_summary.iloc[0]
    if int(summary["candidate_count"]) != simulated.n_candidates:
        raise AssertionError(f"{name}: candidate denominator mismatch")
    if int(summary["missing_count"]) != simulated.n_missing:
        raise AssertionError(f"{name}: missing-count mismatch")
    if int(summary["observed_count"]) + int(summary["missing_count"]) != int(
        summary["candidate_count"]
    ):
        raise AssertionError(f"{name}: observed + missing != candidates")
    if result.provenance["iid_sample_level_inference_performed"] is not False:
        raise AssertionError(f"{name}: iid sample-level inference was unexpectedly enabled")
    if result.provenance["inverse_probability_weighting_performed"] is not False:
        raise AssertionError(f"{name}: inverse-probability weighting was unexpectedly enabled")
    if result.provenance["inverse_intensity_correction_performed"] is not False:
        raise AssertionError(f"{name}: inverse-intensity correction was unexpectedly enabled")
    if result.provenance["current_missing_gaze_imputed"] is not False:
        raise AssertionError(f"{name}: current missing gaze was unexpectedly imputed")
    if result.provenance["sparse_estimator_modified"] is not False:
        raise AssertionError(f"{name}: sparse estimator contract was unexpectedly modified")
    if "p_value" in result.associations.columns:
        raise AssertionError(f"{name}: naive sample-level p-values appeared in diagnostics")


def _association(result, predictor: str) -> pd.Series:
    rows = result.associations[result.associations["predictor"] == predictor]
    if len(rows) != 1:
        raise AssertionError(f"expected one association row for {predictor!r}, found {len(rows)}")
    return rows.iloc[0]


def _mcar_scenario(*, n_participants: int, n_time: int) -> dict[str, Any]:
    simulation = _functional_simulation(
        n_participants=n_participants,
        n_time=n_time,
        missingness={"kind": "mcar", "probability": 0.25},
        random_state=1661,
    )
    simulated = observation_process_from_functional_simulation(simulation)
    result = diagnose_observation_process(
        simulated.process,
        predictors=("trial_id",),
        history_predictors=("previous_observed_x", "time_since_last_observed"),
        time_basis="linear",
        time_bins=5,
        association_bins=5,
    )
    _assert_accounting(simulated, result, name="mcar")

    time_row = _association(result, "candidate_time")
    previous_x = _association(result, "previous_observed_x")
    if abs(float(time_row["spearman_rho"])) >= 0.10:
        raise AssertionError("mcar: candidate-time association exceeds null tolerance")
    if abs(float(previous_x["spearman_rho"])) >= 0.12:
        raise AssertionError("mcar: past-position association exceeds null tolerance")

    fractions = result.time_summary["observed_fraction"].to_numpy(dtype=float)
    if float(np.max(fractions) - np.min(fractions)) >= 0.12:
        raise AssertionError("mcar: binned observation fractions vary beyond Monte Carlo tolerance")

    expected_probability = 0.75
    realized_fraction = float(result.global_summary.iloc[0]["observed_fraction"])
    if abs(realized_fraction - expected_probability) >= 0.04:
        raise AssertionError("mcar: realized retention fraction is implausibly far from truth")

    return {
        "name": "mcar_null",
        "candidate_count": simulated.n_candidates,
        "missing_count": simulated.n_missing,
        "true_retention_probability": expected_probability,
        "realized_retention_fraction": realized_fraction,
        "candidate_time_spearman_rho": float(time_row["spearman_rho"]),
        "previous_observed_x_spearman_rho": float(previous_x["spearman_rho"]),
        "time_bin_observed_fraction_range": float(np.max(fractions) - np.min(fractions)),
        "group_count": int(result.global_summary.iloc[0]["group_count"]),
    }


def _block_scenario(*, n_participants: int, n_time: int) -> dict[str, Any]:
    fraction = 0.30
    simulation = _functional_simulation(
        n_participants=n_participants,
        n_time=n_time,
        missingness={"kind": "block", "fraction": fraction},
        random_state=1662,
    )
    simulated = observation_process_from_functional_simulation(simulation)
    result = diagnose_observation_process(
        simulated.process,
        predictors=(),
        time_basis="linear",
        time_bins=5,
        association_bins=None,
    )
    _assert_accounting(simulated, result, name="block")

    expected_block = int(np.floor(fraction * n_time))
    if fraction > 0 and expected_block == 0:
        expected_block = 1
    longest = result.curve_summary["longest_missing_run"].to_numpy(dtype=int)
    if not np.all(longest == expected_block):
        raise AssertionError("block: contiguous missing-run length was not localized exactly")

    for curve_index, mask in enumerate(simulated.missingness_mask):
        missing_index = np.flatnonzero(mask)
        if missing_index.size != expected_block:
            raise AssertionError(f"block: curve {curve_index} has unexpected missing count")
        if missing_index.size > 1 and not np.all(np.diff(missing_index) == 1):
            raise AssertionError(f"block: curve {curve_index} missing block is not contiguous")

    return {
        "name": "contiguous_block_loss",
        "candidate_count": simulated.n_candidates,
        "missing_count": simulated.n_missing,
        "expected_block_length": expected_block,
        "minimum_longest_missing_run": int(np.min(longest)),
        "maximum_longest_missing_run": int(np.max(longest)),
        "all_truth_blocks_contiguous": True,
        "group_count": int(result.global_summary.iloc[0]["group_count"]),
    }


def _informative_scenario(*, n_participants: int, n_time: int) -> dict[str, Any]:
    base = _functional_simulation(
        n_participants=n_participants,
        n_time=n_time,
        missingness=None,
        random_state=1663,
    )
    simulated = simulate_informative_time_retention(
        base,
        intercept=0.8,
        slope=-2.4,
        random_state=1664,
    )
    replay = simulate_informative_time_retention(
        base,
        intercept=0.8,
        slope=-2.4,
        random_state=1664,
    )
    for first, second in zip(simulated.missingness_mask, replay.missingness_mask, strict=True):
        np.testing.assert_array_equal(first, second)
    for first, second in zip(
        simulated.retention_probability or (),
        replay.retention_probability or (),
        strict=True,
    ):
        np.testing.assert_allclose(first, second, rtol=0.0, atol=0.0)

    result = diagnose_observation_process(
        simulated.process,
        predictors=("trial_id",),
        history_predictors=("previous_observed_x", "time_since_last_observed"),
        time_basis="linear",
        time_bins=5,
        association_bins=5,
    )
    _assert_accounting(simulated, result, name="informative_time")

    time_row = _association(result, "candidate_time")
    rho = float(time_row["spearman_rho"])
    if rho >= -0.25:
        raise AssertionError("informative_time: diagnostic did not recover negative time association")

    time_summary = result.time_summary.sort_values("lower").reset_index(drop=True)
    first_fraction = float(time_summary.iloc[0]["observed_fraction"])
    last_fraction = float(time_summary.iloc[-1]["observed_fraction"])
    if first_fraction - last_fraction <= 0.35:
        raise AssertionError("informative_time: binned diagnostic did not localize retention decline")

    if simulated.retention_probability is None:
        raise AssertionError("informative_time: exact retention probability truth is missing")
    frame = simulated.process.frame.copy()
    frame["true_retention_probability"] = np.concatenate(simulated.retention_probability)
    edges = np.linspace(
        float(frame["candidate_time"].min()),
        float(frame["candidate_time"].max()),
        6,
    )
    frame["bin"] = pd.cut(
        frame["candidate_time"],
        bins=edges,
        include_lowest=True,
        right=True,
    )
    truth_by_bin = frame.groupby("bin", observed=False)["true_retention_probability"].mean().to_numpy()
    empirical_by_bin = time_summary["observed_fraction"].to_numpy(dtype=float)
    calibration_error = np.abs(empirical_by_bin - truth_by_bin)
    if float(np.max(calibration_error)) >= 0.10:
        raise AssertionError("informative_time: binned observed fractions are poorly calibrated to truth")

    if int(result.global_summary.iloc[0]["group_count"]) != n_participants:
        raise AssertionError("informative_time: participant grouping was not retained")

    return {
        "name": "known_informative_candidate_time",
        "candidate_count": simulated.n_candidates,
        "missing_count": simulated.n_missing,
        "mechanism": simulated.mechanism,
        "intercept": simulated.specification["intercept"],
        "slope": simulated.specification["slope"],
        "candidate_time_spearman_rho": rho,
        "first_time_bin_observed_fraction": first_fraction,
        "last_time_bin_observed_fraction": last_fraction,
        "maximum_binned_probability_calibration_error": float(np.max(calibration_error)),
        "group_count": int(result.global_summary.iloc[0]["group_count"]),
        "deterministic_replay": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-participants", type=int, default=40)
    parser.add_argument("--n-time", type=int, default=31)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.n_participants < 20:
        raise ValueError("--n-participants must be >= 20")
    if args.n_time < 21:
        raise ValueError("--n-time must be >= 21")

    scenarios = [
        _mcar_scenario(n_participants=args.n_participants, n_time=args.n_time),
        _block_scenario(n_participants=args.n_participants, n_time=args.n_time),
        _informative_scenario(n_participants=args.n_participants, n_time=args.n_time),
    ]
    payload = {
        "method": "a3_observation_process_known_truth_qualification",
        "qualified_scope": "descriptive_observation_process_diagnostics_only",
        "candidate_denominator_required": True,
        "informative_mechanism": "logistic_candidate_time",
        "iid_sample_level_inference_performed": False,
        "missing_mechanism_classification_performed": False,
        "inverse_probability_weighting_performed": False,
        "inverse_intensity_correction_performed": False,
        "current_missing_gaze_imputed": False,
        "sparse_estimator_modified": False,
        "claim_scope": (
            "Qualification establishes denominator accounting, descriptive null behavior, "
            "contiguous-block localization, direction/calibration under one known candidate-time "
            "retention mechanism, participant grouping retention, and deterministic replay. "
            "It does not establish a formal MAR/MNAR test or a correction estimator."
        ),
        "scenario_count": len(scenarios),
        "scenarios": scenarios,
    }
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
