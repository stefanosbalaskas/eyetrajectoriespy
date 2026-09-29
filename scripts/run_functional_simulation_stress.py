"""Descriptive 0.11 functional recovery stress evidence.

This runner executes the already-declared stress catalog. It deliberately
contains no scientific pass/fail thresholds. Replicate failures are retained in
the denominator and serialized as evidence rather than dropped or converted to
successes.

The estimator callback receives observations plus the declared scenario only.
Latent truth enters only in post-fit recovery evaluators. The phase-variation
stress case is generation-audited only because the frozen 0.11 simulator does
not expose observed landmark events; deriving them from latent phase truth
inside the estimator path would violate the truth boundary.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from eyetrajectoriespy import (
    FunctionalRecoveryResult,
    evaluate_fpca_recovery,
    evaluate_functional_mixed_effects_recovery,
    evaluate_sparse_fpca_recovery,
    fit_fpca,
    fit_functional_mixed_effects_regression,
    fit_mfpca,
    fit_sparse_fpca,
    functional_recovery_failure_frame,
    functional_recovery_frame,
    functional_recovery_stress_scenarios,
    functional_recovery_summary_frame,
    functional_simulation_scenario_frame,
    run_functional_recovery_scenarios,
    simulate_functional_scenario,
)


def _mean(time):
    time = np.asarray(time, dtype=float)
    return 0.25 + 0.30 * time


def _phi1(time):
    time = np.asarray(time, dtype=float)
    return np.sqrt(2.0) * np.sin(np.pi * time)


def _phi2(time):
    time = np.asarray(time, dtype=float)
    return np.sqrt(2.0) * np.sin(2.0 * np.pi * time)


def _mean_planar(time):
    time = np.asarray(time, dtype=float)
    return np.column_stack(
        [
            0.25 + 0.30 * time,
            -0.10 + 0.20 * time,
        ]
    )


def _phi1_planar(time):
    base = _phi1(time) / np.sqrt(2.0)
    return np.column_stack([base, base])


def _phi2_planar(time):
    base = _phi2(time) / np.sqrt(2.0)
    return np.column_stack([base, -base])


def _sparse_estimator(observations, scenario):
    kwargs = {
        "dimension": scenario.dimension_names[0],
        "n_components": 2,
        "evaluation_grid": np.asarray(scenario.truth_grid, dtype=float),
        "psd_action": "project",
        "score_failure_action": "retain_nan",
    }
    if scenario.name == "stress_estimated_noise_diagonal_difference":
        kwargs.update(
            {
                "mean_bandwidth": 0.22,
                "covariance_bandwidth": 0.30,
                "noise_variance_method": "diagonal_difference",
                "noise_bandwidth": 0.24,
                "noise_support": (0.20, 0.80),
            }
        )
    else:
        declared_noise = float(
            np.asarray(
                scenario.measurement_noise_covariance,
                dtype=float,
            )[0, 0]
        )
        kwargs.update(
            {
                "mean_bandwidth": 0.24,
                "covariance_bandwidth": 0.34,
                "noise_variance_method": "fixed",
                "measurement_error_variance": declared_noise,
            }
        )
    return fit_sparse_fpca(observations, **kwargs)


def _sparse_recovery(fitted, truth, _scenario):
    return evaluate_sparse_fpca_recovery(fitted, truth)


def _dense_estimator(observations, scenario):
    if len(scenario.dimension_names) > 1:
        return fit_mfpca(
            observations,
            n_components=2,
            scaling="none",
        )
    return fit_fpca(
        observations,
        n_components=2,
        scaling="none",
    )


def _dense_recovery(fitted, truth, _scenario):
    return evaluate_fpca_recovery(fitted, truth)


def _mixed_estimator(observations, scenario):
    trial = pd.to_numeric(
        observations.metadata["trial_id"],
        errors="raise",
    ).to_numpy(dtype=float)
    condition = trial - float(np.mean(trial))
    scale = float(np.max(np.abs(condition)))
    if scale > 0:
        condition = condition / scale
    design = pd.DataFrame(
        {
            "curve_id": observations.curve_ids,
            "condition": condition,
        }
    )
    return fit_functional_mixed_effects_regression(
        observations,
        design,
        predictors=("condition",),
        participant_column="participant_id",
        trial_column="trial_id",
        trial_random_effect="functional_intercept",
        dimension=scenario.dimension_names[0],
        fixed_basis_size=4,
        random_basis_size=3,
        trial_random_basis_size=3,
        spline_degree=2,
        reml=True,
        method="lbfgs",
        maxiter=1000,
    )


def _mixed_recovery(fitted, truth, _scenario):
    return evaluate_functional_mixed_effects_recovery(
        fitted,
        truth,
    )


def _combine(results):
    records = []
    definitions = {}
    for result in results:
        records.extend(result.records)
        for definition in result.metric_definitions:
            previous = definitions.get(definition.name)
            if previous is not None and previous != definition:
                raise RuntimeError(
                    "stress evidence produced inconsistent metric definitions "
                    f"for {definition.name!r}"
                )
            definitions[definition.name] = definition
    return FunctionalRecoveryResult(
        records=tuple(records),
        metric_definitions=tuple(definitions.values()),
    )


def _json_records(frame):
    if frame.empty:
        return []
    clean = frame.replace({np.nan: None})
    rows = clean.to_dict(orient="records")
    for row in rows:
        for key, value in tuple(row.items()):
            if isinstance(value, np.generic):
                row[key] = value.item()
    return rows


def _record_rows(result, strategy_by_name):
    rows = []
    for record in result.records:
        rows.append(
            {
                "scenario": record.scenario_name,
                "strategy": strategy_by_name[record.scenario_name],
                "replicate": record.replicate,
                "seed": record.seed,
                "status": record.status,
                "error_type": record.error_type,
                "error_message": record.error_message,
                "metrics": dict(record.metrics),
                "assessment_provenance": dict(
                    record.assessment_provenance
                ),
            }
        )
    return rows


def _phase_generation_audit(scenario):
    rows = []
    for replicate, seed in enumerate(scenario.seeds()):
        try:
            simulation = simulate_functional_scenario(
                scenario,
                mean=_mean,
                eigenfunctions=(_phi1, _phi2),
                replicate=replicate,
            )
        except Exception as exc:
            rows.append(
                {
                    "scenario": scenario.name,
                    "strategy": "generation_only_phase",
                    "replicate": replicate,
                    "seed": seed,
                    "status": "simulation_failed",
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                }
            )
            continue
        exponents = np.asarray(
            simulation.truth.provenance["phase_exponents"],
            dtype=float,
        )
        rows.append(
            {
                "scenario": scenario.name,
                "strategy": "generation_only_phase",
                "replicate": replicate,
                "seed": seed,
                "status": "generated",
                "phase_exponent_median": float(np.median(exponents)),
                "phase_exponent_min": float(np.min(exponents)),
                "phase_exponent_max": float(np.max(exponents)),
                "reason_recovery_not_fit": (
                    "Frozen 0.11 does not generate observed landmark events; "
                    "constructing them from latent phase truth in the estimator "
                    "path would violate the post-fit truth boundary."
                ),
            }
        )
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--replicates", type=int, default=3)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("functional-simulation-stress-evidence.json"),
    )
    args = parser.parse_args()
    if args.replicates < 1:
        raise ValueError("replicates must be positive")

    scenarios = functional_recovery_stress_scenarios(
        replicates=args.replicates,
        seed_start=204000,
    )
    if any(
        dict(scenario.labels).get("matrix_role") != "stress"
        or dict(scenario.labels).get("automatic_thresholds") is not False
        for scenario in scenarios
    ):
        raise RuntimeError(
            "stress evidence requires descriptive scenarios with automatic "
            "thresholds disabled"
        )

    by_name = {scenario.name: scenario for scenario in scenarios}
    expected_names = {
        "stress_very_sparse",
        "stress_unequal_sample_counts",
        "stress_center_clustered_times",
        "stress_boundary_poor_times",
        "stress_estimated_noise_diagonal_difference",
        "stress_high_measurement_noise",
        "stress_nearly_tied_eigenvalues",
        "stress_heavy_tailed_scores",
        "stress_participant_heavy_hierarchy",
        "stress_trial_heavy_hierarchy",
        "stress_phase_variation",
        "stress_mcar_missingness",
        "stress_block_missingness",
        "stress_correlated_multichannel_noise",
    }
    if set(by_name) != expected_names:
        raise RuntimeError(
            "stress scenario catalog changed without updating the evidence "
            "runner explicitly"
        )

    sparse_names = (
        "stress_very_sparse",
        "stress_unequal_sample_counts",
        "stress_center_clustered_times",
        "stress_boundary_poor_times",
        "stress_estimated_noise_diagonal_difference",
        "stress_high_measurement_noise",
    )
    dense_names = (
        "stress_nearly_tied_eigenvalues",
        "stress_heavy_tailed_scores",
        "stress_mcar_missingness",
        "stress_block_missingness",
    )
    mixed_names = (
        "stress_participant_heavy_hierarchy",
        "stress_trial_heavy_hierarchy",
    )

    results = [
        run_functional_recovery_scenarios(
            [by_name[name] for name in sparse_names],
            mean=_mean,
            eigenfunctions=(_phi1, _phi2),
            estimator=_sparse_estimator,
            recovery=_sparse_recovery,
            failure_action="record",
        ),
        run_functional_recovery_scenarios(
            [by_name[name] for name in dense_names],
            mean=_mean,
            eigenfunctions=(_phi1, _phi2),
            estimator=_dense_estimator,
            recovery=_dense_recovery,
            failure_action="record",
        ),
        run_functional_recovery_scenarios(
            [by_name[name] for name in mixed_names],
            mean=_mean,
            eigenfunctions=(_phi1, _phi2),
            estimator=_mixed_estimator,
            recovery=_mixed_recovery,
            failure_action="record",
        ),
        run_functional_recovery_scenarios(
            [by_name["stress_correlated_multichannel_noise"]],
            mean=_mean_planar,
            eigenfunctions=(_phi1_planar, _phi2_planar),
            estimator=_dense_estimator,
            recovery=_dense_recovery,
            failure_action="record",
        ),
    ]
    result = _combine(results)

    strategy_by_name = {
        **{name: "native_sparse_fpca" for name in sparse_names},
        **{name: "dense_fpca" for name in dense_names},
        **{name: "functional_mixed_effects" for name in mixed_names},
        "stress_correlated_multichannel_noise": "dense_mfpca",
    }
    records = _record_rows(result, strategy_by_name)
    phase_rows = _phase_generation_audit(
        by_name["stress_phase_variation"]
    )

    expected_recovery_records = (
        (len(scenarios) - 1) * args.replicates
    )
    if len(records) != expected_recovery_records:
        raise RuntimeError(
            "stress evidence lost or duplicated declared recovery replicates"
        )
    if len(phase_rows) != args.replicates:
        raise RuntimeError(
            "phase generation audit lost or duplicated declared replicates"
        )

    payload = {
        "schema_version": 1,
        "kind": "descriptive functional recovery stress evidence",
        "matrix_role": "stress",
        "package_line": "0.11.0.dev0",
        "automatic_thresholds": False,
        "comparative_benchmark": False,
        "truth_available_to_estimator": False,
        "failure_action": "record",
        "replicates_per_scenario": args.replicates,
        "scenario_count": len(scenarios),
        "interpretation": (
            "Descriptive finite-sample stress evidence only. There are no "
            "automatic scientific pass/fail thresholds, no tuning from truth, "
            "and no silent deletion of failed replicates. Failure proportions "
            "are evidence about the declared regimes, not release scores."
        ),
        "scenario_catalog": _json_records(
            functional_simulation_scenario_frame(scenarios)
        ),
        "recovery_records": records,
        "failure_summary": _json_records(
            functional_recovery_failure_frame(result)
        ),
        "metric_summary": _json_records(
            functional_recovery_summary_frame(result)
        ),
        "metric_rows": _json_records(
            functional_recovery_frame(result)
        ),
        "generation_only_phase_evidence": phase_rows,
    }
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "artifact": str(args.output),
                "automatic_thresholds": False,
                "scenario_count": len(scenarios),
                "recovery_records": len(records),
                "phase_generation_records": len(phase_rows),
                "failed_recovery_replicates": sum(
                    row["status"] != "ok"
                    for row in records
                ),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
