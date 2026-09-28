"""Recovery validation for the public 0.11 functional simulator.

This script checks whether public simulator truth can be recovered by existing
package estimators under declared finite-sample regimes. It is not an automatic
tuning routine and does not use the generating truth to choose estimator
settings.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from eyetrajectoriespy import (
    fit_fpca,
    fit_sparse_fpca,
    simulate_functional_process,
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


def _normalize(functions, weights):
    functions = np.asarray(functions, dtype=float)
    norms = np.sqrt(
        np.sum(functions**2 * weights[None, :], axis=1)
    )
    return functions / norms[:, None]


def _component_metrics(
    estimated,
    truth,
    weights,
    estimated_scores,
    truth_scores,
):
    estimated = _normalize(estimated, weights)
    truth = _normalize(truth, weights)
    signed = estimated @ np.diag(weights) @ truth.T
    similarity = np.abs(signed)
    signs = np.sign(np.diag(signed))
    signs[signs == 0] = 1.0
    score_correlations = np.asarray(
        [
            abs(
                np.corrcoef(
                    signs[index] * estimated_scores[:, index],
                    truth_scores[:, index],
                )[0, 1]
            )
            for index in range(estimated.shape[0])
        ],
        dtype=float,
    )

    weighted_estimated = estimated.T * np.sqrt(weights)[:, None]
    weighted_truth = truth.T * np.sqrt(weights)[:, None]
    q_estimated, _ = np.linalg.qr(weighted_estimated)
    q_truth, _ = np.linalg.qr(weighted_truth)
    principal_cosines = np.linalg.svd(
        q_estimated.T @ q_truth,
        compute_uv=False,
    )
    return {
        "component_similarity": np.diag(similarity).tolist(),
        "minimum_component_similarity": float(
            np.min(np.diag(similarity))
        ),
        "score_correlations": score_correlations.tolist(),
        "minimum_score_correlation": float(
            np.min(score_correlations)
        ),
        "principal_cosines": principal_cosines.tolist(),
        "minimum_principal_cosine": float(
            np.min(principal_cosines)
        ),
    }


def _dense_case(*, seed, score_distribution="normal"):
    grid = np.linspace(0.0, 1.0, 81)
    simulation = simulate_functional_process(
        mean=_mean,
        eigenfunctions=(_phi1, _phi2),
        eigenvalues=(1.0, 0.35),
        truth_grid=grid,
        n_participants=200,
        score_distribution=score_distribution,
        score_df=6.0,
        measurement_noise_sd=0.05,
        random_state=seed,
    )
    fitted = fit_fpca(
        simulation.observations,
        n_components=2,
        scaling="none",
    )
    metrics = _component_metrics(
        fitted.components[:, :, 0],
        simulation.truth.eigenfunctions[:, :, 0],
        fitted.weights,
        fitted.scores,
        simulation.truth.scores,
    )
    metrics["eigenvalue_relative_error"] = (
        np.abs(
            fitted.explained_variance
            - simulation.truth.eigenvalues
        )
        / simulation.truth.eigenvalues
    ).tolist()
    metrics["maximum_eigenvalue_relative_error"] = float(
        np.max(metrics["eigenvalue_relative_error"])
    )
    return metrics


def _sparse_case(*, seed):
    grid = np.linspace(0.0, 1.0, 31)
    simulation = simulate_functional_process(
        mean=_mean,
        eigenfunctions=(_phi1, _phi2),
        eigenvalues=(1.0, 0.35),
        truth_grid=grid,
        n_participants=64,
        observation_design="irregular",
        samples_per_curve=(8, 12),
        irregular_time_design="uniform",
        measurement_noise_sd=0.08,
        random_state=seed,
    )
    fitted = fit_sparse_fpca(
        simulation.observations,
        dimension="value",
        n_components=2,
        evaluation_grid=grid,
        mean_bandwidth=0.24,
        covariance_bandwidth=0.34,
        noise_variance_method="fixed",
        measurement_error_variance=0.08**2,
        psd_action="project",
        score_failure_action="retain_nan",
    )
    metrics = _component_metrics(
        fitted.eigenfunctions,
        simulation.truth.eigenfunctions[:, :, 0],
        fitted.quadrature_weights,
        fitted.scores,
        simulation.truth.scores,
    )
    metrics["score_failure_rate"] = float(
        np.mean(
            fitted.score_diagnostics["status_code"].to_numpy()
            != "ok"
        )
    )
    return metrics


def _hierarchy_case(*, seed):
    simulation = simulate_functional_process(
        mean=_mean,
        eigenfunctions=(_phi1, _phi2),
        eigenvalues=(1.0, 0.35),
        truth_grid=np.linspace(0.0, 1.0, 31),
        n_participants=300,
        trials_per_participant=2,
        participant_eigenvalues=(0.20, 0.08),
        trial_eigenvalues=(0.10, 0.04),
        measurement_noise_sd=0.0,
        random_state=seed,
    )
    truth = simulation.truth
    empirical = {
        "curve": np.var(truth.curve_scores, axis=0, ddof=0),
        "participant": np.var(
            truth.participant_scores,
            axis=0,
            ddof=0,
        ),
        "trial": np.var(truth.trial_scores, axis=0, ddof=0),
    }
    target = {
        "curve": truth.eigenvalues,
        "participant": truth.participant_eigenvalues,
        "trial": truth.trial_eigenvalues,
    }
    relative = {
        key: (
            np.abs(empirical[key] - target[key])
            / target[key]
        ).tolist()
        for key in target
    }
    return {
        "relative_variance_error": relative,
        "maximum_relative_variance_error": float(
            max(max(values) for values in relative.values())
        ),
    }


SCENARIOS = {
    "dense_gaussian": {
        "runner": lambda seed: _dense_case(
            seed=seed,
            score_distribution="normal",
        ),
        "minimum_principal_cosine": 0.95,
        "minimum_score_correlation": 0.90,
        "maximum_eigenvalue_relative_error": 0.30,
    },
    "dense_student_t": {
        "runner": lambda seed: _dense_case(
            seed=seed,
            score_distribution="student_t",
        ),
        "minimum_principal_cosine": 0.90,
        "minimum_score_correlation": 0.85,
        "maximum_eigenvalue_relative_error": 0.45,
    },
    "native_sparse": {
        "runner": _sparse_case,
        "minimum_principal_cosine": 0.80,
        "minimum_score_correlation": 0.55,
        "maximum_score_failure_rate": 0.05,
    },
    "hierarchy_sources": {
        "runner": _hierarchy_case,
        "maximum_relative_variance_error": 0.30,
    },
}


def _summarize(name, rows):
    summary = {"name": name, "replicates": len(rows)}
    keys = set().union(*(row.keys() for row in rows))
    for key in (
        "minimum_principal_cosine",
        "minimum_score_correlation",
    ):
        if key in keys:
            summary[key] = float(min(row[key] for row in rows))
    for key in (
        "maximum_eigenvalue_relative_error",
        "score_failure_rate",
        "maximum_relative_variance_error",
    ):
        if key in keys:
            summary[key] = float(max(row[key] for row in rows))
    return summary


def _check(name, spec, summary):
    if "minimum_principal_cosine" in spec:
        if summary["minimum_principal_cosine"] < spec[
            "minimum_principal_cosine"
        ]:
            raise RuntimeError(
                f"{name}: subspace recovery below declared threshold"
            )
    if "minimum_score_correlation" in spec:
        if summary["minimum_score_correlation"] < spec[
            "minimum_score_correlation"
        ]:
            raise RuntimeError(
                f"{name}: score recovery below declared threshold"
            )
    if "maximum_eigenvalue_relative_error" in spec:
        if summary["maximum_eigenvalue_relative_error"] > spec[
            "maximum_eigenvalue_relative_error"
        ]:
            raise RuntimeError(
                f"{name}: eigenvalue error above declared threshold"
            )
    if "maximum_score_failure_rate" in spec:
        if summary["score_failure_rate"] > spec[
            "maximum_score_failure_rate"
        ]:
            raise RuntimeError(
                f"{name}: sparse score failure rate above threshold"
            )
    if "maximum_relative_variance_error" in spec:
        if summary["maximum_relative_variance_error"] > spec[
            "maximum_relative_variance_error"
        ]:
            raise RuntimeError(
                f"{name}: hierarchy variance recovery above threshold"
            )


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

    scenarios = []
    for scenario_index, (name, spec) in enumerate(SCENARIOS.items()):
        rows = [
            spec["runner"](
                202800 + 100 * scenario_index + replicate
            )
            for replicate in range(args.replicates)
        ]
        summary = _summarize(name, rows)
        _check(name, spec, summary)
        scenarios.append(
            {
                "name": name,
                "thresholds": {
                    key: value
                    for key, value in spec.items()
                    if key != "runner"
                },
                "summary": summary,
                "replicates": rows,
            }
        )

    payload = {
        "schema_version": 1,
        "kind": "public functional simulation recovery validation",
        "automatic_tuning": False,
        "comparative_benchmark": False,
        "replicates_per_scenario": args.replicates,
        "scenarios": scenarios,
        "interpretation": (
            "Finite-sample integration checks between the public simulator "
            "and existing dense/sparse estimators. Thresholds are declared "
            "qualification guards, not universal recovery guarantees."
        ),
    }
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
