"""Descriptive stress evidence for the feature-frozen 0.11 recovery laboratory.

This runner intentionally has no scientific pass/fail thresholds. It executes
the declared stress catalog, retains every failed replicate in the denominator,
and records either post-fit recovery metrics or explicit design/truth audits
appropriate to the scenario. Difficult regimes remain evidence rather than
being converted into qualification failures or silently dropped.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from eyetrajectoriespy import (
    FunctionalRecoveryRecord,
    FunctionalRecoveryResult,
    evaluate_fpca_recovery,
    evaluate_hierarchy_truth_recovery,
    evaluate_sparse_fpca_recovery,
    fit_fpca,
    fit_mfpca,
    fit_sparse_fpca,
    functional_recovery_failure_frame,
    functional_recovery_stress_scenarios,
    functional_recovery_summary_frame,
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


def _vector_mean(time):
    time = np.asarray(time, dtype=float)
    return np.column_stack(
        [0.40 + 0.10 * time, 0.60 - 0.10 * time]
    )


def _vector_phi1(time):
    time = np.asarray(time, dtype=float)
    values = np.sin(np.pi * time)
    return np.column_stack([values, values])


def _vector_phi2(time):
    time = np.asarray(time, dtype=float)
    values = np.sin(2.0 * np.pi * time)
    return np.column_stack([values, -values])


def _generation_functions(scenario):
    if len(scenario.dimension_names) > 1:
        return _vector_mean, (_vector_phi1, _vector_phi2)
    return _mean, (_phi1, _phi2)


def _failed_record(scenario, replicate, status, exc):
    return FunctionalRecoveryRecord(
        scenario_name=scenario.name,
        replicate=replicate,
        seed=scenario.seeds()[replicate],
        metrics={},
        status=status,
        error_type=type(exc).__name__,
        error_message=str(exc),
    )


def _assessment_record(
    scenario,
    replicate,
    assessment,
    *,
    stress_assessment_kind,
):
    provenance = dict(assessment.provenance)
    provenance["stress_assessment_kind"] = stress_assessment_kind
    return FunctionalRecoveryRecord(
        scenario_name=scenario.name,
        replicate=replicate,
        seed=scenario.seeds()[replicate],
        metrics=dict(assessment.as_mapping()),
        metric_values=assessment.values,
        assessment_provenance=provenance,
    )


def _raw_record(
    scenario,
    replicate,
    metrics,
    *,
    stress_assessment_kind,
):
    return FunctionalRecoveryRecord(
        scenario_name=scenario.name,
        replicate=replicate,
        seed=scenario.seeds()[replicate],
        metrics=metrics,
        assessment_provenance={
            "stress_assessment_kind": stress_assessment_kind,
            "estimator": "none",
        },
    )


def _fit_sparse(simulation, scenario):
    target = dict(scenario.labels)["scientific_target"]
    kwargs = {
        "dimension": simulation.truth.dimension_names[0],
        "n_components": 2,
        "evaluation_grid": np.asarray(
            scenario.truth_grid,
            dtype=float,
        ),
        "mean_bandwidth": 0.24,
        "covariance_bandwidth": 0.34,
        "psd_action": "project",
        "score_failure_action": "retain_nan",
    }
    if target == "sparse_fpca_pace_estimated_noise":
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
        kwargs.update(
            {
                "noise_variance_method": "fixed",
                "measurement_error_variance": float(
                    simulation.truth.measurement_noise_covariance[0, 0]
                ),
            }
        )
    return fit_sparse_fpca(simulation.observations, **kwargs)


def _phase_design_metrics(simulation):
    grid = np.asarray(simulation.truth.truth_grid, dtype=float)
    warps = np.asarray(
        simulation.truth.phase_warps_on_truth_grid,
        dtype=float,
    )
    displacement = warps - grid[None, :]
    return {
        "phase_mean_absolute_displacement": float(
            np.mean(np.abs(displacement))
        ),
        "phase_max_absolute_displacement": float(
            np.max(np.abs(displacement))
        ),
    }


def _observation_design_metrics(simulation):
    values = simulation.observations.values
    if isinstance(values, tuple):
        fractions = [
            float(np.mean(np.isfinite(curve)))
            for curve in values
        ]
    else:
        array = np.asarray(values, dtype=float)
        fractions = [
            float(np.mean(np.isfinite(array[index])))
            for index in range(array.shape[0])
        ]
    fractions = np.asarray(fractions, dtype=float)
    return {
        "observed_fraction_mean": float(np.mean(fractions)),
        "observed_fraction_minimum": float(np.min(fractions)),
        "missing_fraction_maximum": float(1.0 - np.min(fractions)),
    }


def _records_to_json(result):
    rows = []
    for record in result.records:
        rows.append(
            {
                "scenario": record.scenario_name,
                "replicate": record.replicate,
                "seed": record.seed,
                "status": record.status,
                "metrics": dict(record.metrics),
                "assessment_provenance": dict(
                    record.assessment_provenance
                ),
                "error_type": record.error_type,
                "error_message": record.error_message,
            }
        )
    return rows


def _frame_records(frame):
    clean = frame.replace({np.nan: None})
    records = clean.to_dict(orient="records")
    for row in records:
        for key, value in tuple(row.items()):
            if isinstance(value, np.generic):
                row[key] = value.item()
    return records


def _scenario_metadata(scenario):
    return {
        "name": scenario.name,
        "labels": dict(scenario.labels),
        "replicates": scenario.replicates,
        "seed_start": scenario.seed_start,
        "n_participants": scenario.n_participants,
        "trials_per_participant": scenario.trials_per_participant,
        "observation_design": scenario.observation_design,
        "samples_per_curve": scenario.samples_per_curve,
        "irregular_time_design": scenario.irregular_time_design,
        "measurement_noise_sd": scenario.measurement_noise_sd,
        "measurement_noise_covariance": (
            None
            if scenario.measurement_noise_covariance is None
            else np.asarray(
                scenario.measurement_noise_covariance,
                dtype=float,
            ).tolist()
        ),
        "missingness": (
            None
            if scenario.missingness is None
            else dict(scenario.missingness)
        ),
        "phase_variation": (
            None
            if scenario.phase_variation is None
            else dict(scenario.phase_variation)
        ),
        "score_distribution": scenario.score_distribution,
        "score_df": scenario.score_df,
        "dimension_names": list(scenario.dimension_names),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--replicates", type=int, default=10)
    parser.add_argument("--seed-start", type=int, default=204000)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("functional-simulation-stress.json"),
    )
    args = parser.parse_args()
    if args.replicates < 1:
        raise ValueError("replicates must be positive")

    scenarios = functional_recovery_stress_scenarios(
        replicates=args.replicates,
        seed_start=args.seed_start,
    )
    records = []
    definitions = {}

    for scenario in scenarios:
        target = dict(scenario.labels)["scientific_target"]
        mean, eigenfunctions = _generation_functions(scenario)
        for replicate in range(scenario.replicates):
            try:
                simulation = simulate_functional_scenario(
                    scenario,
                    mean=mean,
                    eigenfunctions=eigenfunctions,
                    replicate=replicate,
                )
            except Exception as exc:
                records.append(
                    _failed_record(
                        scenario,
                        replicate,
                        "simulation_failed",
                        exc,
                    )
                )
                continue

            try:
                if target in {
                    "sparse_fpca_pace",
                    "sparse_fpca_pace_estimated_noise",
                }:
                    fitted = _fit_sparse(simulation, scenario)
                    assessment = evaluate_sparse_fpca_recovery(
                        fitted,
                        simulation.truth,
                    )
                    record = _assessment_record(
                        scenario,
                        replicate,
                        assessment,
                        stress_assessment_kind=(
                            "post_fit_sparse_fpca_recovery"
                        ),
                    )
                elif target in {"fpca", "fpca_subspace"}:
                    fitted = fit_fpca(
                        simulation.observations,
                        n_components=2,
                        scaling="none",
                    )
                    assessment = evaluate_fpca_recovery(
                        fitted,
                        simulation.truth,
                    )
                    record = _assessment_record(
                        scenario,
                        replicate,
                        assessment,
                        stress_assessment_kind=(
                            "post_fit_fpca_recovery"
                        ),
                    )
                elif target == "mfpca":
                    fitted = fit_mfpca(
                        simulation.observations,
                        n_components=2,
                        scaling="none",
                    )
                    assessment = evaluate_fpca_recovery(
                        fitted,
                        simulation.truth,
                    )
                    record = _assessment_record(
                        scenario,
                        replicate,
                        assessment,
                        stress_assessment_kind=(
                            "post_fit_mfpca_recovery"
                        ),
                    )
                elif target == "functional_mixed_effects":
                    assessment = evaluate_hierarchy_truth_recovery(
                        simulation.truth
                    )
                    record = _assessment_record(
                        scenario,
                        replicate,
                        assessment,
                        stress_assessment_kind=(
                            "simulation_source_variance_audit"
                        ),
                    )
                elif target == "registration_phase":
                    record = _raw_record(
                        scenario,
                        replicate,
                        _phase_design_metrics(simulation),
                        stress_assessment_kind=(
                            "phase_observation_mechanism_audit"
                        ),
                    )
                elif target == "missing_data_workflow":
                    record = _raw_record(
                        scenario,
                        replicate,
                        _observation_design_metrics(simulation),
                        stress_assessment_kind=(
                            "missingness_observation_mechanism_audit"
                        ),
                    )
                else:
                    raise RuntimeError(
                        f"unsupported stress scientific target: {target}"
                    )
            except Exception as exc:
                records.append(
                    _failed_record(
                        scenario,
                        replicate,
                        "fit_failed",
                        exc,
                    )
                )
                continue

            records.append(record)
            for value in record.metric_values:
                previous = definitions.get(value.metric.name)
                if previous is not None and previous != value.metric:
                    raise RuntimeError(
                        "inconsistent metric definition for "
                        f"{value.metric.name!r}"
                    )
                definitions[value.metric.name] = value.metric

    result = FunctionalRecoveryResult(
        records=tuple(records),
        metric_definitions=tuple(definitions.values()),
    )
    summary = functional_recovery_summary_frame(result)
    failures = functional_recovery_failure_frame(result)

    payload = {
        "schema_version": 1,
        "kind": "public functional recovery descriptive stress evidence",
        "matrix_role": "stress",
        "automatic_pass_fail": False,
        "scientific_thresholds": None,
        "failure_action": "record",
        "truth_available_to_estimator": False,
        "replicates_per_scenario": args.replicates,
        "seed_start": args.seed_start,
        "scenarios": [
            _scenario_metadata(scenario)
            for scenario in scenarios
        ],
        "replicates": _records_to_json(result),
        "summary": _frame_records(summary),
        "failure_summary": _frame_records(failures),
        "interpretation": (
            "Descriptive finite-sample stress evidence only. No stress "
            "scenario has a scientific pass/fail threshold. Failed simulation, "
            "fit, or recovery replicates remain in the denominator. FPCA, "
            "MFPCA, and sparse FPCA/PACE scenarios use post-fit recovery; "
            "hierarchy, phase, and missingness scenarios use explicitly "
            "labelled truth/design audits where no estimator comparison is "
            "claimed."
        ),
    }
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
