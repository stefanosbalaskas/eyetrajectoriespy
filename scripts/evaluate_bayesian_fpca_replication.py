"""Evaluate replicated Bayesian FPCA B2 recovery and B3 score uncertainty.

B2 is descriptive replicated recovery/fairness evidence. B3 evaluates score
uncertainty against known latent scores after weighted orthogonal alignment.
The fitted-model truth-inclusion summaries are not interpreted as full
population-estimation coverage for native PACE; the existing oracle conditional
PACE validation remains the reference for that narrower estimand.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from scipy.stats import chi2, norm

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import evaluate_bayesian_fpca_comparator as b1  # noqa: E402


PRIMARY_K = 7
K_VALUES = (5, 6, 7, 8, 9)


def _read_covariance_long(
    path: Path,
    curve_ids: tuple[str, ...],
    n_components: int,
) -> np.ndarray:
    frame = pd.read_csv(path)
    required = {"curve_id", "component_i", "component_j", "covariance"}
    if not required.issubset(frame.columns):
        raise ValueError(f"{path.name} missing covariance columns")
    frame["curve_id"] = frame["curve_id"].astype(str)
    output = np.full(
        (len(curve_ids), n_components, n_components),
        np.nan,
        dtype=float,
    )
    for curve_index, curve_id in enumerate(curve_ids):
        subset = frame[frame["curve_id"] == curve_id]
        if len(subset) != n_components * n_components:
            raise ValueError(
                f"{path.name} incomplete covariance for {curve_id!r}"
            )
        for row in subset.itertuples(index=False):
            first = int(row.component_i) - 1
            second = int(row.component_j) - 1
            output[curve_index, first, second] = float(row.covariance)
    return output


def _weighted_flat(
    functions: np.ndarray,
    weights: np.ndarray,
) -> np.ndarray:
    functions = np.asarray(functions, dtype=float)
    flat = functions.transpose(0, 2, 1).reshape(functions.shape[0], -1)
    metric = np.tile(np.sqrt(weights), functions.shape[2])
    return flat * metric[None, :]


def _alignment(
    estimated_functions: np.ndarray,
    truth_functions: np.ndarray,
    weights: np.ndarray,
) -> np.ndarray:
    estimated = _weighted_flat(estimated_functions, weights)
    truth = _weighted_flat(truth_functions, weights)
    cross = truth @ estimated.T
    left, _, right_t = np.linalg.svd(cross, full_matrices=False)
    return left @ right_t


def _align_scores_covariance(
    scores: np.ndarray,
    covariance: np.ndarray,
    transform: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    aligned_scores = np.asarray(scores, dtype=float) @ transform.T
    aligned_covariance = np.einsum(
        "ab,nbc,dc->nad",
        transform,
        np.asarray(covariance, dtype=float),
        transform,
        optimize=True,
    )
    return aligned_scores, aligned_covariance


def _uncertainty_summary(
    *,
    scores: np.ndarray,
    covariance: np.ndarray,
    estimated_functions: np.ndarray,
    truth_scores: np.ndarray,
    truth_functions: np.ndarray,
    weights: np.ndarray,
    near_tied: bool,
) -> dict[str, object]:
    transform = _alignment(
        estimated_functions,
        truth_functions,
        weights,
    )
    aligned_scores, aligned_covariance = _align_scores_covariance(
        scores,
        covariance,
        transform,
    )

    threshold = float(chi2.ppf(0.95, df=truth_scores.shape[1]))
    z = float(norm.ppf(0.975))
    ellipsoid_hits: list[bool] = []
    marginal_hits: list[list[bool]] = [
        [] for _ in range(truth_scores.shape[1])
    ]
    standardized: list[list[float]] = [
        [] for _ in range(truth_scores.shape[1])
    ]
    failed = 0

    for index in range(truth_scores.shape[0]):
        estimate = aligned_scores[index]
        cov = aligned_covariance[index]
        if not (
            np.all(np.isfinite(estimate))
            and np.all(np.isfinite(cov))
            and np.all(np.isfinite(truth_scores[index]))
        ):
            failed += 1
            continue
        cov = 0.5 * (cov + cov.T)
        eigenvalues = np.linalg.eigvalsh(cov)
        if float(np.min(eigenvalues)) <= 0:
            failed += 1
            continue
        error = truth_scores[index] - estimate
        squared = float(error @ np.linalg.solve(cov, error))
        ellipsoid_hits.append(squared <= threshold)

        standard_error = np.sqrt(np.diag(cov))
        for component in range(truth_scores.shape[1]):
            if standard_error[component] <= 0:
                continue
            value = float(error[component] / standard_error[component])
            standardized[component].append(value)
            marginal_hits[component].append(abs(value) <= z)

    component_records = []
    for component in range(truth_scores.shape[1]):
        values = np.asarray(standardized[component], dtype=float)
        hits = marginal_hits[component]
        component_records.append(
            {
                "component": component + 1,
                "componentwise_identified_as_primary": not near_tied,
                "n_valid": int(values.size),
                "standardized_error_mean": (
                    float(np.mean(values)) if values.size else float("nan")
                ),
                "standardized_error_sd": (
                    float(np.std(values, ddof=1))
                    if values.size > 1
                    else float("nan")
                ),
                "marginal_95_truth_inclusion": (
                    float(np.mean(hits)) if hits else float("nan")
                ),
                "marginal_95_truth_inclusion_hits": int(sum(hits)),
                "standardized_error_sum": (
                    float(np.sum(values)) if values.size else 0.0
                ),
                "standardized_error_sum_squares": (
                    float(np.sum(values**2)) if values.size else 0.0
                ),
            }
        )

    return {
        "alignment": "weighted_orthogonal_procrustes_to_known_truth",
        "ellipsoid_probability": 0.95,
        "ellipsoid_truth_inclusion": (
            float(np.mean(ellipsoid_hits))
            if ellipsoid_hits
            else float("nan")
        ),
        "n_valid_curves": int(len(ellipsoid_hits)),
        "ellipsoid_truth_inclusion_hits": int(sum(ellipsoid_hits)),
        "n_failed_or_nonpositive_covariance": int(failed),
        "components": component_records,
        "interpretation": (
            "empirical known-score inclusion after invariant alignment; "
            "not full population-estimation coverage"
        ),
    }


def _method_metrics(
    scenario_dir: Path,
    *,
    prefix: str,
    truth: dict[str, object],
    covariance_path: Path | None,
) -> dict[str, object]:
    grid = np.asarray(truth["truth_grid"], dtype=float)
    dimensions = tuple(str(value) for value in truth["dimension_names"])
    curve_ids = tuple(str(value) for value in truth["curve_ids"])
    truth_functions = np.asarray(truth["eigenfunctions"], dtype=float)
    truth_scores = np.asarray(truth["scores"], dtype=float)
    truth_eigenvalues = np.asarray(truth["eigenvalues"], dtype=float)
    truth_mean = np.asarray(truth["mean"], dtype=float)
    truth_latent = np.asarray(truth["latent_on_truth_grid"], dtype=float)
    n_components = truth_eigenvalues.size
    weights = b1._trap_weights(grid)

    mean = b1._read_mean(
        scenario_dir / f"{prefix}_mean.csv",
        grid,
        dimensions,
    )
    functions = b1._read_functions(
        scenario_dir / f"{prefix}_eigenfunctions.csv",
        grid,
        dimensions,
        n_components,
    )
    scores = b1._read_scores(
        scenario_dir / f"{prefix}_scores.csv",
        curve_ids,
        n_components,
    )
    eigenvalues = b1._read_eigenvalues(
        scenario_dir / f"{prefix}_eigenvalues.csv",
        n_components,
    )
    functional_cosines = b1.functional_subspace_cosines(
        functions,
        truth_functions,
        weights,
    )
    score_cosines = b1.score_subspace_cosines(scores, truth_scores)
    payload: dict[str, object] = {
        "mean_ise": b1._mean_ise(mean, truth_mean, weights),
        "reconstruction_ise": b1._reconstruction_ise(
            mean,
            functions,
            scores,
            truth_latent,
            weights,
        ),
        "truth_functional_subspace_principal_cosines": [
            float(value) for value in functional_cosines
        ],
        "truth_functional_subspace_min_cosine": float(
            np.min(functional_cosines)
        ),
        "truth_score_subspace_principal_cosines": [
            float(value) for value in score_cosines
        ],
        "truth_score_subspace_min_cosine": (
            float(np.nanmin(score_cosines))
            if np.any(np.isfinite(score_cosines))
            else float("nan")
        ),
        "spectrum_pve_l1_error": b1._pve_l1(
            eigenvalues,
            truth_eigenvalues,
        ),
        "score_failure_rate": float(
            np.mean(~np.all(np.isfinite(scores), axis=1))
        ),
        "eigenvalues": [float(value) for value in eigenvalues],
    }
    if covariance_path is not None and covariance_path.exists():
        covariance = _read_covariance_long(
            covariance_path,
            curve_ids,
            n_components,
        )
        payload["score_uncertainty"] = _uncertainty_summary(
            scores=scores,
            covariance=covariance,
            estimated_functions=functions,
            truth_scores=truth_scores,
            truth_functions=truth_functions,
            weights=weights,
            near_tied=truth["scenario"] == "univariate_near_tied",
        )
    return payload


def _finite(values) -> np.ndarray:
    array = np.asarray(list(values), dtype=float)
    return array[np.isfinite(array)]


def _summary(values) -> dict[str, float | int]:
    array = _finite(values)
    if not array.size:
        return {
            "n": 0,
            "mean": float("nan"),
            "median": float("nan"),
            "q1": float("nan"),
            "q3": float("nan"),
            "minimum": float("nan"),
            "maximum": float("nan"),
        }
    return {
        "n": int(array.size),
        "mean": float(np.mean(array)),
        "median": float(np.median(array)),
        "q1": float(np.quantile(array, 0.25)),
        "q3": float(np.quantile(array, 0.75)),
        "minimum": float(np.min(array)),
        "maximum": float(np.max(array)),
    }


def _aggregate_uncertainty(
    rows: list[dict[str, object]],
) -> dict[str, object]:
    valid_curves = int(sum(row["n_valid_curves"] for row in rows))
    ellipsoid_hits = int(
        sum(row["ellipsoid_truth_inclusion_hits"] for row in rows)
    )
    component_count = max(len(row["components"]) for row in rows)
    components = []
    for component_index in range(component_count):
        records = [
            row["components"][component_index]
            for row in rows
            if len(row["components"]) > component_index
        ]
        n_valid = int(sum(record["n_valid"] for record in records))
        marginal_hits = int(
            sum(
                record["marginal_95_truth_inclusion_hits"]
                for record in records
            )
        )
        z_sum = float(
            sum(record["standardized_error_sum"] for record in records)
        )
        z_sumsq = float(
            sum(
                record["standardized_error_sum_squares"]
                for record in records
            )
        )
        z_mean = z_sum / n_valid if n_valid else float("nan")
        if n_valid > 1:
            centered = max(0.0, z_sumsq - n_valid * z_mean**2)
            z_sd = float(np.sqrt(centered / (n_valid - 1)))
        else:
            z_sd = float("nan")
        components.append(
            {
                "component": component_index + 1,
                "componentwise_identified_as_primary": all(
                    record["componentwise_identified_as_primary"]
                    for record in records
                ),
                "n_valid": n_valid,
                "pooled_standardized_error_mean": z_mean,
                "pooled_standardized_error_sd": z_sd,
                "pooled_marginal_95_truth_inclusion": (
                    marginal_hits / n_valid if n_valid else float("nan")
                ),
                "replicate_standardized_error_mean": _summary(
                    record["standardized_error_mean"] for record in records
                ),
                "replicate_standardized_error_sd": _summary(
                    record["standardized_error_sd"] for record in records
                ),
                "replicate_marginal_95_truth_inclusion": _summary(
                    record["marginal_95_truth_inclusion"]
                    for record in records
                ),
            }
        )
    return {
        "replicate_count": len(rows),
        "ellipsoid_95_truth_inclusion": _summary(
            row["ellipsoid_truth_inclusion"] for row in rows
        ),
        "pooled_ellipsoid_95_truth_inclusion": (
            ellipsoid_hits / valid_curves if valid_curves else float("nan")
        ),
        "valid_curves": valid_curves,
        "failed_or_nonpositive_covariance": int(
            sum(row["n_failed_or_nonpositive_covariance"] for row in rows)
        ),
        "components": components,
        "population_objects_reestimated_per_replicate": True,
        "fitted_covariance_includes_population_estimation_uncertainty": False,
        "coverage_interpretation": (
            "empirical calibration after population objects are re-estimated "
            "in every replicate; fitted score covariance itself remains "
            "conditional on fitted population objects"
        ),
    }


def _aggregate_scenario(records: list[dict[str, object]]) -> dict[str, object]:
    name = str(records[0]["scenario"])
    method_names = [
        "native_frozen",
        "native_selected",
        "bayesfpca_selected",
    ] + [f"bayesfpca_k{k}" for k in K_VALUES]
    methods: dict[str, object] = {}
    for method in method_names:
        available = [
            record[method]
            for record in records
            if method in record and record[method] is not None
        ]
        if not available:
            continue
        methods[method] = {
            "replicate_count": len(available),
            "reconstruction_ise": _summary(
                row["reconstruction_ise"] for row in available
            ),
            "mean_ise": _summary(row["mean_ise"] for row in available),
            "functional_subspace_min_cosine": _summary(
                row["truth_functional_subspace_min_cosine"]
                for row in available
            ),
            "score_subspace_min_cosine": _summary(
                row["truth_score_subspace_min_cosine"]
                for row in available
            ),
            "spectrum_pve_l1_error": _summary(
                row["spectrum_pve_l1_error"] for row in available
            ),
            "score_failure_rate": _summary(
                row["score_failure_rate"] for row in available
            ),
        }
        uncertainty = [
            row["score_uncertainty"]
            for row in available
            if "score_uncertainty" in row
        ]
        if uncertainty:
            methods[method]["score_uncertainty"] = _aggregate_uncertainty(
                uncertainty
            )

    native = methods.get("native_frozen")
    bayes = methods.get("bayesfpca_k7")
    paired_ratio = []
    paired_difference = []
    if native is not None and bayes is not None:
        for record in records:
            native_value = float(
                record["native_frozen"]["reconstruction_ise"]
            )
            bayes_value = float(record["bayesfpca_k7"]["reconstruction_ise"])
            if np.isfinite(native_value) and np.isfinite(bayes_value):
                paired_difference.append(native_value - bayes_value)
                if bayes_value > 0:
                    paired_ratio.append(native_value / bayes_value)

    k_sensitivity = {}
    for k in K_VALUES:
        values = [
            float(record[f"bayesfpca_k{k}"]["reconstruction_ise"])
            for record in records
            if record.get(f"bayesfpca_k{k}") is not None
        ]
        k_sensitivity[str(k)] = _summary(values)

    selected_k_counts = {
        str(k): sum(record.get("bayesfpca_selected_k") == k for record in records)
        for k in K_VALUES
    }
    selected_differences = []
    for record in records:
        native_selected = record.get("native_selected")
        bayes_selected = record.get("bayesfpca_selected")
        if native_selected is None or bayes_selected is None:
            continue
        native_value = float(native_selected["reconstruction_ise"])
        bayes_value = float(bayes_selected["reconstruction_ise"])
        if np.isfinite(native_value) and np.isfinite(bayes_value):
            selected_differences.append(native_value - bayes_value)

    return {
        "scenario": name,
        "design": records[0]["design"],
        "truth_family": records[0]["truth_family"],
        "observation_mechanism": records[0]["observation_mechanism"],
        "replicate_count": len(records),
        "methods": methods,
        "native_minus_bayes_k7_reconstruction_ise": _summary(
            paired_difference
        ),
        "native_to_bayes_k7_reconstruction_ratio": _summary(
            paired_ratio
        ),
        "bayesfpca_k_sensitivity_reconstruction_ise": k_sensitivity,
        "bayesfpca_selected_k_counts": selected_k_counts,
        "native_selected_minus_bayes_selected_reconstruction_ise": _summary(
            selected_differences
        ),
        "informative_observation_is_sensitivity_only": (
            name == "univariate_informative_time"
        ),
    }


def evaluate(root: Path) -> dict[str, object]:
    manifest = json.loads(
        (root / "replication_manifest.json").read_text(encoding="utf-8")
    )
    if manifest.get("b1_evidence_immutable") is not True:
        raise ValueError("B1 evidence must remain immutable")
    for key in (
        "equivalence_claim",
        "architecture_winner_selected",
        "automatic_promotion_decision",
        "b4_decision_recorded",
    ):
        if manifest.get(key) is not False:
            raise ValueError(f"{key} must remain false in B2/B3")

    rows = pd.read_csv(root / "replication_manifest.csv")
    records: list[dict[str, object]] = []
    for row in rows.itertuples(index=False):
        scenario_dir = root / str(row.relative_path)
        truth = json.loads(
            (scenario_dir / "truth.json").read_text(encoding="utf-8")
        )
        record: dict[str, object] = {
            "scenario": str(row.scenario),
            "replicate": int(row.replicate),
            "seed": int(row.seed),
            "design": str(row.design),
            "truth_family": str(row.truth_family),
            "observation_mechanism": str(row.observation_mechanism),
        }
        record["native_frozen"] = _method_metrics(
            scenario_dir,
            prefix="native_frozen",
            truth=truth,
            covariance_path=(
                scenario_dir / "native_frozen_score_covariance.csv"
            ),
        )
        if (scenario_dir / "native_selected_mean.csv").exists():
            record["native_selected"] = _method_metrics(
                scenario_dir,
                prefix="native_selected",
                truth=truth,
                covariance_path=None,
            )
        else:
            record["native_selected"] = None

        for k in K_VALUES:
            prefix = f"bayesfpca_k{k}"
            metadata_path = scenario_dir / f"{prefix}_metadata.csv"
            if not metadata_path.exists():
                record[prefix] = None
                continue
            record[prefix] = _method_metrics(
                scenario_dir,
                prefix=prefix,
                truth=truth,
                covariance_path=(
                    scenario_dir / f"{prefix}_score_covariance.csv"
                ),
            )
            metadata = pd.read_csv(metadata_path).iloc[0]
            record[prefix]["elapsed_seconds"] = float(
                metadata["elapsed_seconds"]
            )
            record[prefix]["n_iter"] = int(metadata["n_iter"])
            record[prefix]["final_elbo"] = float(metadata["final_elbo"])

        selected_metadata = scenario_dir / "bayesfpca_selected_metadata.csv"
        if selected_metadata.exists():
            record["bayesfpca_selected"] = _method_metrics(
                scenario_dir,
                prefix="bayesfpca_selected",
                truth=truth,
                covariance_path=(
                    scenario_dir / "bayesfpca_selected_score_covariance.csv"
                ),
            )
            metadata = pd.read_csv(selected_metadata).iloc[0]
            record["bayesfpca_selected_k"] = int(
                metadata["spline_basis_size"]
            )
            record["bayesfpca_selected"]["final_elbo"] = float(
                metadata["final_elbo"]
            )
        else:
            record["bayesfpca_selected"] = None
            record["bayesfpca_selected_k"] = None
        records.append(record)

    aggregates = [
        _aggregate_scenario(
            [record for record in records if record["scenario"] == scenario]
        )
        for scenario in rows["scenario"].drop_duplicates().tolist()
    ]

    oracle_path = root / "native-oracle-conditional-uncertainty.json"
    oracle_reference = None
    if oracle_path.exists():
        oracle_reference = json.loads(oracle_path.read_text(encoding="utf-8"))
        if oracle_reference.get("validation_passed") is not True:
            raise ValueError("native oracle conditional uncertainty reference failed")

    payload = {
        "schema_version": 1,
        "programme": "post-1.1-bayesian-fpca-b2-b3",
        "evidence_type": (
            "replicated_cross_implementation_recovery_and_score_uncertainty"
        ),
        "eyetrajectoriespy_version": importlib.metadata.version(
            "eyetrajectoriespy"
        ),
        "bayesfpca_version": manifest["external_comparator_version"],
        "bayesfpca_commit": manifest["external_comparator_commit"],
        "replicates_per_scenario": manifest["replicates_per_scenario"],
        "b1_evidence_immutable": True,
        "truth_tuning_performed": False,
        "post_hoc_favorable_search_performed": False,
        "native_secondary_tuning": manifest["native_secondary_tuning"],
        "bayesfpca_k_sensitivity": manifest["bayesfpca_k_sensitivity"],
        "native_oracle_conditional_uncertainty_reference": {
            "source": "scripts/run_sparse_score_uncertainty_validation.py",
            "retained_evidence": oracle_reference,
            "estimand": (
                "conditional PACE score uncertainty with known population objects"
            ),
        },
        "population_estimation_calibration_scope": {
            "population_objects_reestimated_per_replicate": True,
            "empirical_truth_coverage_quantified": True,
            "standardized_error_behavior_quantified": True,
            "fit_score_and_covariance_failure_quantified": True,
            "fitted_covariance_includes_population_estimation_uncertainty": False,
        },
        "native_fitted_uncertainty_interpretation": (
            "conditional score covariance given fitted population objects; "
            "repeated-dataset truth coverage and standardized errors quantify "
            "the calibration gap created when population objects are estimated, "
            "without relabelling the covariance as full estimation uncertainty"
        ),
        "bayesian_uncertainty_interpretation": (
            "variational fitted-model score covariance; empirical known-score "
            "truth inclusion is reported after invariant alignment"
        ),
        "direct_covariance_magnitude_comparison_performed": False,
        "equivalence_claim": False,
        "architecture_winner_selected": False,
        "automatic_promotion_decision": False,
        "b4_decision_recorded": False,
        "replicate_records": records,
        "scenario_aggregates": aggregates,
        "interpretation": (
            "B2/B3 research evidence only. Replication, truth-family changes, "
            "predeclared tuning sensitivity and aligned score-truth inclusion "
            "are reported without selecting an architecture winner or "
            "authorizing a native Bayesian public API."
        ),
    }
    (root / "b2_b3_summary.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence_dir", type=Path)
    args = parser.parse_args()
    payload = evaluate(args.evidence_dir)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
