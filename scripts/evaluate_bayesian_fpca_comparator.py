"""Evaluate invariant native-vs-bayesFPCA sensitivity evidence.

The comparison is descriptive. Different likelihood, spline, smoothing, posterior,
and score constructions preclude exact-equivalence claims or automatic method
selection. Near-tied components are evaluated primarily through invariant
functional and score subspaces rather than componentwise signs/order.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
from pathlib import Path

import numpy as np
import pandas as pd


def _trap_weights(grid: np.ndarray) -> np.ndarray:
    grid = np.asarray(grid, dtype=float)
    if grid.ndim != 1 or grid.size < 2 or not np.all(np.diff(grid) > 0):
        raise ValueError("truth grid must be strictly increasing")
    weights = np.empty_like(grid)
    weights[0] = 0.5 * (grid[1] - grid[0])
    weights[-1] = 0.5 * (grid[-1] - grid[-2])
    if grid.size > 2:
        weights[1:-1] = 0.5 * (grid[2:] - grid[:-2])
    return weights


def _read_mean(
    path: Path,
    grid: np.ndarray,
    dimensions: tuple[str, ...],
) -> np.ndarray:
    frame = pd.read_csv(path)
    if "time" not in frame.columns:
        raise ValueError(f"{path.name} must contain time")
    time_values = frame["time"].to_numpy(dtype=float)
    if time_values.shape != grid.shape or not np.allclose(
        time_values,
        grid,
        atol=1e-12,
        rtol=0.0,
    ):
        raise ValueError(f"{path.name} grid mismatch")
    missing = [dimension for dimension in dimensions if dimension not in frame]
    if missing:
        raise ValueError(f"{path.name} missing mean dimensions {missing}")
    return frame.loc[:, dimensions].to_numpy(dtype=float)


def _read_functions(
    path: Path,
    grid: np.ndarray,
    dimensions: tuple[str, ...],
    n_components: int,
) -> np.ndarray:
    frame = pd.read_csv(path)
    required = {"component", "dimension", "time", "value"}
    if not required.issubset(frame.columns):
        raise ValueError(f"{path.name} missing eigenfunction columns")
    out = np.full(
        (n_components, grid.size, len(dimensions)),
        np.nan,
        dtype=float,
    )
    for component in range(1, n_components + 1):
        for dim_index, dimension in enumerate(dimensions):
            subset = frame[
                (frame["component"] == component)
                & (frame["dimension"] == dimension)
            ].sort_values("time")
            if len(subset) != grid.size:
                raise ValueError(
                    f"{path.name} incomplete component {component}, {dimension}"
                )
            times = subset["time"].to_numpy(dtype=float)
            if not np.allclose(times, grid, atol=1e-12, rtol=0.0):
                raise ValueError(f"{path.name} eigenfunction grid mismatch")
            out[component - 1, :, dim_index] = subset["value"].to_numpy(
                dtype=float
            )
    if not np.all(np.isfinite(out)):
        raise ValueError(f"{path.name} contains non-finite eigenfunctions")
    return out


def _read_scores(
    path: Path,
    curve_ids: tuple[str, ...],
    n_components: int,
) -> np.ndarray:
    frame = pd.read_csv(path)
    if "curve_id" not in frame:
        raise ValueError(f"{path.name} must contain curve_id")
    frame["curve_id"] = frame["curve_id"].astype(str)
    if frame["curve_id"].duplicated().any():
        raise ValueError(f"{path.name} contains duplicate curve IDs")
    frame = frame.set_index("curve_id")
    missing = [curve_id for curve_id in curve_ids if curve_id not in frame.index]
    if missing:
        raise ValueError(f"{path.name} missing curve IDs {missing[:3]}")
    columns = [f"PC{index + 1}" for index in range(n_components)]
    if any(column not in frame.columns for column in columns):
        raise ValueError(f"{path.name} missing score columns")
    return frame.loc[list(curve_ids), columns].to_numpy(dtype=float)


def _read_eigenvalues(path: Path, n_components: int) -> np.ndarray:
    frame = pd.read_csv(path)
    if "eigenvalue" not in frame:
        raise ValueError(f"{path.name} must contain eigenvalue")
    values = frame["eigenvalue"].to_numpy(dtype=float)
    if values.size < n_components:
        raise ValueError(f"{path.name} returned too few eigenvalues")
    return values[:n_components]


def _weighted_function_basis(
    functions: np.ndarray,
    weights: np.ndarray,
) -> np.ndarray:
    functions = np.asarray(functions, dtype=float)
    if functions.ndim != 3:
        raise ValueError("functional basis must have shape (K, G, D)")
    metric = np.tile(np.sqrt(weights), functions.shape[2])
    flat = functions.transpose(0, 2, 1).reshape(functions.shape[0], -1)
    weighted = flat * metric[None, :]
    q, _ = np.linalg.qr(weighted.T)
    return q[:, : functions.shape[0]]


def functional_subspace_cosines(
    first: np.ndarray,
    second: np.ndarray,
    weights: np.ndarray,
) -> np.ndarray:
    qa = _weighted_function_basis(first, weights)
    qb = _weighted_function_basis(second, weights)
    singular = np.linalg.svd(qa.T @ qb, compute_uv=False)
    return np.clip(singular, 0.0, 1.0)


def score_subspace_cosines(first: np.ndarray, second: np.ndarray) -> np.ndarray:
    first = np.asarray(first, dtype=float)
    second = np.asarray(second, dtype=float)
    if first.shape != second.shape:
        raise ValueError("score matrices must have identical shape")
    keep = np.all(np.isfinite(first), axis=1) & np.all(
        np.isfinite(second), axis=1
    )
    if np.count_nonzero(keep) <= first.shape[1]:
        return np.full(first.shape[1], np.nan)
    first = first[keep] - np.mean(first[keep], axis=0, keepdims=True)
    second = second[keep] - np.mean(second[keep], axis=0, keepdims=True)
    qa, _ = np.linalg.qr(first)
    qb, _ = np.linalg.qr(second)
    singular = np.linalg.svd(
        qa[:, : first.shape[1]].T @ qb[:, : second.shape[1]],
        compute_uv=False,
    )
    return np.clip(singular, 0.0, 1.0)


def _mean_ise(
    estimated: np.ndarray,
    truth: np.ndarray,
    weights: np.ndarray,
) -> float:
    return float(
        np.sum((np.asarray(estimated) - np.asarray(truth)) ** 2 * weights[:, None])
    )


def _reconstruction_ise(
    mean: np.ndarray,
    functions: np.ndarray,
    scores: np.ndarray,
    truth_latent: np.ndarray,
    weights: np.ndarray,
) -> float:
    keep = np.all(np.isfinite(scores), axis=1)
    if not np.any(keep):
        return float("nan")
    reconstruction = mean[None, :, :] + np.einsum(
        "nk,kgd->ngd",
        scores[keep],
        functions,
        optimize=True,
    )
    error = (reconstruction - truth_latent[keep]) ** 2
    per_curve = np.sum(error * weights[None, :, None], axis=(1, 2))
    return float(np.mean(per_curve))


def _pve_l1(estimated: np.ndarray, truth: np.ndarray) -> float:
    estimated = np.asarray(estimated, dtype=float)
    truth = np.asarray(truth, dtype=float)
    if (
        not np.all(np.isfinite(estimated))
        or np.sum(estimated) <= 0
        or np.sum(truth) <= 0
    ):
        return float("nan")
    return float(
        np.sum(
            np.abs(
                estimated / np.sum(estimated)
                - truth / np.sum(truth)
            )
        )
    )


def _score_covariance_summary(path: Path) -> dict[str, float]:
    frame = pd.read_csv(path)
    required = {"curve_id", "component_i", "component_j", "covariance"}
    if not required.issubset(frame.columns):
        raise ValueError(f"{path.name} missing score covariance columns")
    values = frame["covariance"].to_numpy(dtype=float)
    finite_fraction = float(np.mean(np.isfinite(values)))
    traces = []
    for _, group in frame.groupby("curve_id", sort=False):
        diagonal = group[group["component_i"] == group["component_j"]]
        if len(diagonal):
            traces.append(float(np.sum(diagonal["covariance"])))
    return {
        "finite_fraction": finite_fraction,
        "median_trace": (
            float(np.nanmedian(np.asarray(traces, dtype=float)))
            if traces
            else float("nan")
        ),
    }


def evaluate_scenario(scenario_dir: Path) -> dict[str, object]:
    truth = json.loads((scenario_dir / "truth.json").read_text(encoding="utf-8"))
    contract = truth.get("contract", {})
    if contract.get("equivalence_claim") is not False:
        raise ValueError("known-truth fixture must forbid equivalence claims")
    if contract.get("architecture_winner_selected") is not False:
        raise ValueError("fixture must not select an architecture winner")
    if contract.get("external_runtime_backend") is not False:
        raise ValueError("external comparator cannot be a runtime backend")

    grid = np.asarray(truth["truth_grid"], dtype=float)
    weights = _trap_weights(grid)
    dimensions = tuple(str(value) for value in truth["dimension_names"])
    curve_ids = tuple(str(value) for value in truth["curve_ids"])
    true_functions = np.asarray(truth["eigenfunctions"], dtype=float)
    true_scores = np.asarray(truth["scores"], dtype=float)
    true_eigenvalues = np.asarray(truth["eigenvalues"], dtype=float)
    true_mean = np.asarray(truth["mean"], dtype=float)
    true_latent = np.asarray(truth["latent_on_truth_grid"], dtype=float)
    n_components = true_eigenvalues.size

    methods: dict[str, dict[str, object]] = {}
    for method, prefix in (
        ("native", "native"),
        ("bayesfpca", "bayesfpca"),
    ):
        mean = _read_mean(
            scenario_dir / f"{prefix}_mean.csv",
            grid,
            dimensions,
        )
        functions = _read_functions(
            scenario_dir / f"{prefix}_eigenfunctions.csv",
            grid,
            dimensions,
            n_components,
        )
        scores = _read_scores(
            scenario_dir / f"{prefix}_scores.csv",
            curve_ids,
            n_components,
        )
        eigenvalues = _read_eigenvalues(
            scenario_dir / f"{prefix}_eigenvalues.csv",
            n_components,
        )
        function_cosines = functional_subspace_cosines(
            functions,
            true_functions,
            weights,
        )
        score_cosines = score_subspace_cosines(scores, true_scores)
        methods[method] = {
            "mean_ise": _mean_ise(mean, true_mean, weights),
            "reconstruction_ise": _reconstruction_ise(
                mean,
                functions,
                scores,
                true_latent,
                weights,
            ),
            "truth_functional_subspace_principal_cosines": [
                float(value) for value in function_cosines
            ],
            "truth_functional_subspace_min_cosine": float(
                np.min(function_cosines)
            ),
            "truth_score_subspace_principal_cosines": [
                float(value) for value in score_cosines
            ],
            "truth_score_subspace_min_cosine": (
                float(np.nanmin(score_cosines))
                if np.any(np.isfinite(score_cosines))
                else float("nan")
            ),
            "spectrum_pve_l1_error": _pve_l1(
                eigenvalues,
                true_eigenvalues,
            ),
            "score_failure_rate": float(
                np.mean(~np.all(np.isfinite(scores), axis=1))
            ),
            "eigenvalues": [float(value) for value in eigenvalues],
        }

    native_bayes_functions = functional_subspace_cosines(
        _read_functions(
            scenario_dir / "native_eigenfunctions.csv",
            grid,
            dimensions,
            n_components,
        ),
        _read_functions(
            scenario_dir / "bayesfpca_eigenfunctions.csv",
            grid,
            dimensions,
            n_components,
        ),
        weights,
    )
    native_bayes_scores = score_subspace_cosines(
        _read_scores(
            scenario_dir / "native_scores.csv",
            curve_ids,
            n_components,
        ),
        _read_scores(
            scenario_dir / "bayesfpca_scores.csv",
            curve_ids,
            n_components,
        ),
    )

    metadata = pd.read_csv(scenario_dir / "bayesfpca_metadata.csv").iloc[0]
    score_covariance = _score_covariance_summary(
        scenario_dir / "bayesfpca_score_covariance.csv"
    )

    return {
        "scenario": truth["scenario"],
        "design": truth["design"],
        "n_curves": len(curve_ids),
        "n_components": int(n_components),
        "truth_eigenvalues": [float(value) for value in true_eigenvalues],
        "native": methods["native"],
        "bayesfpca": {
            **methods["bayesfpca"],
            "elapsed_seconds": float(metadata["elapsed_seconds"]),
            "n_iter": int(metadata["n_iter"]),
            "final_elbo": float(metadata["final_elbo"]),
            "score_covariance": score_covariance,
        },
        "native_bayesfpca_functional_subspace_principal_cosines": [
            float(value) for value in native_bayes_functions
        ],
        "native_bayesfpca_score_subspace_principal_cosines": [
            float(value) for value in native_bayes_scores
        ],
        "uncertainty_contract": {
            "bayesfpca_score_covariance_exported": True,
            "direct_uncertainty_superiority_claim": False,
            "native_conditional_pace_covariance_is_not_full_estimation_uncertainty": True,
            "posterior_population_uncertainty_evaluated": False,
        },
    }


def evaluate(root: Path) -> dict[str, object]:
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("equivalence_claim") is not False:
        raise ValueError("manifest must forbid equivalence claims")
    if manifest.get("architecture_winner_selected") is not False:
        raise ValueError("manifest must not select an architecture winner")
    if manifest.get("external_runtime_backend") is not False:
        raise ValueError("bayesFPCA must remain external-only")
    if manifest.get("source_code_ported") is not False:
        raise ValueError("GPL source code must not be ported")

    scenario_rows = pd.read_csv(root / "manifest.csv")
    results = [
        evaluate_scenario(root / "scenarios" / str(name))
        for name in scenario_rows["scenario"]
    ]
    payload = {
        "schema_version": 1,
        "programme": "post-1.1-bayesian-fpca-comparator-b1",
        "evidence_type": "cross_implementation_sensitivity",
        "comparison": "native_sparse_fpca_mfpca_vs_bayesFPCA_MFVB",
        "eyetrajectoriespy_version": importlib.metadata.version(
            "eyetrajectoriespy"
        ),
        "bayesfpca_version": manifest["external_comparator_version"],
        "bayesfpca_commit": manifest["external_comparator_commit"],
        "bayesfpca_license": manifest["external_comparator_license"],
        "external_runtime_backend": False,
        "source_code_ported": False,
        "equivalence_claim": False,
        "architecture_winner_selected": False,
        "automatic_promotion_decision": False,
        "qualification_thresholds_introduced": False,
        "scenarios": results,
        "interpretation": (
            "Descriptive independent-implementation sensitivity only. Native "
            "covariance/PACE and bayesFPCA variational latent-basis methods "
            "differ in estimation architecture, smoothing/basis assumptions, "
            "and uncertainty semantics. Invariant subspace and reconstruction "
            "targets are reported without declaring numerical equivalence, an "
            "architecture winner, or a public-API promotion decision."
        ),
    }
    (root / "bayesian_fpca_sensitivity.json").write_text(
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
