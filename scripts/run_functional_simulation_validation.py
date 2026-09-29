"""Qualification recovery validation for the public 0.11 simulator.

Qualification scenarios are deliberately small, deterministic, and gated.
They are distinct from the broader descriptive stress matrix. Generating truth
is supplied only after fitting to semantic recovery evaluators.
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
    fit_sparse_fpca,
    functional_recovery_qualification_scenarios,
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


def _record_from_assessment(scenario, replicate, assessment):
    return FunctionalRecoveryRecord(
        scenario_name=scenario.name,
        replicate=replicate,
        seed=scenario.seeds()[replicate],
        metrics=dict(assessment.as_mapping()),
        metric_values=assessment.values,
        assessment_provenance=assessment.provenance,
    )


def _dense_case(scenario, replicate):
    simulation = simulate_functional_scenario(
        scenario,
        mean=_mean,
        eigenfunctions=(_phi1, _phi2),
        replicate=replicate,
    )
    fitted = fit_fpca(
        simulation.observations,
        n_components=2,
        scaling="none",
    )
    return evaluate_fpca_recovery(fitted, simulation.truth)


def _sparse_case(scenario, replicate, *, estimated_noise):
    simulation = simulate_functional_scenario(
        scenario,
        mean=_mean,
        eigenfunctions=(_phi1, _phi2),
        replicate=replicate,
    )
    kwargs = {
        "dimension": "value",
        "n_components": 2,
        "evaluation_grid": np.asarray(
            scenario.truth_grid,
            dtype=float,
        ),
        "mean_bandwidth": 0.24 if not estimated_noise else 0.22,
        "covariance_bandwidth": 0.34 if not estimated_noise else 0.30,
        "psd_action": "project",
        "score_failure_action": "retain_nan",
    }
    if estimated_noise:
        kwargs.update(
            {
                "noise_variance_method": "diagonal_difference",
                "noise_bandwidth": 0.24,
                "noise_support": (0.20, 0.80),
            }
        )
    else:
        kwargs.update(
            {
                "noise_variance_method": "fixed",
                "measurement_error_variance": 0.08**2,
            }
        )
    fitted = fit_sparse_fpca(
        simulation.observations,
        **kwargs,
    )
    return evaluate_sparse_fpca_recovery(
        fitted,
        simulation.truth,
    )


def _hierarchy_case(scenario, replicate):
    simulation = simulate_functional_scenario(
        scenario,
        mean=_mean,
        eigenfunctions=(_phi1, _phi2),
        replicate=replicate,
    )
    return evaluate_hierarchy_truth_recovery(simulation.truth)


CASE_SPECS = {
    "dense_gaussian": {
        "runner": _dense_case,
        "minimum_principal_cosine": 0.95,
        "minimum_score_correlation": 0.90,
        "maximum_eigenvalue_relative_error": 0.30,
    },
    "dense_student_t": {
        "runner": _dense_case,
        "minimum_principal_cosine": 0.90,
        "minimum_score_correlation": 0.85,
        "maximum_eigenvalue_relative_error": 0.45,
    },
    "native_sparse": {
        "runner": lambda scenario, replicate: _sparse_case(
            scenario,
            replicate,
            estimated_noise=False,
        ),
        "minimum_principal_cosine": 0.80,
        "minimum_score_correlation": 0.55,
        "maximum_score_failure_rate": 0.05,
    },
    "hierarchy_sources": {
        "runner": _hierarchy_case,
        "maximum_source_variance_relative_error": 0.30,
    },
}


def _values(records, prefix):
    return [
        value
        for record in records
        for key, value in record.metrics.items()
        if key.startswith(prefix)
    ]


def _qualification_summary(name, records):
    summary = {
        "name": name,
        "replicates": len(records),
    }

    principal = _values(records, "subspace_principal_cosine")
    score_correlation = _values(records, "score_correlation")
    eigenvalue_error = _values(records, "eigenvalue_relative_error")
    score_failure = _values(records, "score_failure_rate")
    noise_error = _values(records, "noise_variance_relative_error")
    hierarchy_error = _values(
        records,
        "source_variance_relative_error",
    )

    if principal:
        summary["minimum_principal_cosine"] = float(min(principal))
    if score_correlation:
        summary["minimum_score_correlation"] = float(
            min(score_correlation)
        )
    if eigenvalue_error:
        summary["maximum_eigenvalue_relative_error"] = float(
            max(eigenvalue_error)
        )
    if score_failure:
        summary["maximum_score_failure_rate"] = float(
            max(score_failure)
        )
    if noise_error:
        summary["maximum_noise_variance_relative_error"] = float(
            max(noise_error)
        )
    if hierarchy_error:
        summary["maximum_source_variance_relative_error"] = float(
            max(hierarchy_error)
        )
    return summary


def _check(name, spec, summary):
    minimums = {
        "minimum_principal_cosine": "subspace recovery",
        "minimum_score_correlation": "score recovery",
    }
    maximums = {
        "maximum_eigenvalue_relative_error": "eigenvalue error",
        "maximum_score_failure_rate": "sparse score failure rate",
        "maximum_noise_variance_relative_error": "noise-variance error",
        "maximum_source_variance_relative_error": (
            "hierarchy source-variance error"
        ),
    }

    for key, label in minimums.items():
        if key in spec and summary[key] < spec[key]:
            raise RuntimeError(
                f"{name}: {label} below declared qualification threshold"
            )
    for key, label in maximums.items():
        if key in spec and summary[key] > spec[key]:
            raise RuntimeError(
                f"{name}: {label} above declared qualification threshold"
            )


def _summary_rows(result):
    frame = functional_recovery_summary_frame(result)
    records = frame.replace({np.nan: None}).to_dict(orient="records")
    for row in records:
        for key, value in tuple(row.items()):
            if isinstance(value, np.generic):
                row[key] = value.item()
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--replicates", type=int, default=3)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("functional-simulation-validation.json"),
    )
    args = parser.parse_args()
    if args.replicates < 1:
        raise ValueError("replicates must be positive")

    declared = functional_recovery_qualification_scenarios(
        replicates=args.replicates,
        seed_start=202800,
    )
    scenarios = []
    for scenario in declared:
        spec = CASE_SPECS[scenario.name]
        assessments = [
            spec["runner"](scenario, replicate)
            for replicate in range(scenario.replicates)
        ]
        records = tuple(
            _record_from_assessment(
                scenario,
                replicate,
                assessment,
            )
            for replicate, assessment in enumerate(assessments)
        )
        definitions = {
            value.metric.name: value.metric
            for assessment in assessments
            for value in assessment.values
        }
        result = FunctionalRecoveryResult(
            records=records,
            metric_definitions=tuple(definitions.values()),
        )
        summary = _qualification_summary(
            scenario.name,
            records,
        )
        print(
            json.dumps(
                {
                    "qualification_summary": summary,
                    "scenario": scenario.name,
                },
                sort_keys=True,
            )
        )
        _check(scenario.name, spec, summary)

        scenarios.append(
            {
                "name": scenario.name,
                "scenario_labels": dict(scenario.labels),
                "thresholds": {
                    key: value
                    for key, value in spec.items()
                    if key != "runner"
                },
                "summary": summary,
                "monte_carlo_summary": _summary_rows(result),
                "replicates": [
                    {
                        "replicate": record.replicate,
                        "seed": record.seed,
                        "metrics": dict(record.metrics),
                        "assessment_provenance": dict(
                            record.assessment_provenance
                        ),
                    }
                    for record in records
                ],
            }
        )

    payload = {
        "schema_version": 2,
        "kind": "public functional recovery qualification",
        "automatic_tuning": False,
        "comparative_benchmark": False,
        "matrix_role": "qualification",
        "stress_matrix_is_separate": True,
        "truth_available_to_estimator": False,
        "replicates_per_scenario": args.replicates,
        "scenarios": scenarios,
        "interpretation": (
            "Finite-sample integration qualification for declared seeded "
            "workloads. Thresholds are CI guards, not universal recovery "
            "guarantees. Fixed-noise and estimated-noise sparse PACE are "
            "separate qualification problems."
        ),
    }
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
