"""Summarize mGSFPCA sensitivity evidence for the pre-0.12 audit.

This is deliberately not an equivalence test. It compares invariant joint
functional and score subspaces against the frozen known-truth fixture while
retaining implementation differences between eyetrajectoriespy and mGSFPCA.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
from pathlib import Path

import numpy as np
import pandas as pd

from eyetrajectoriespy import functional_trapezoid_weights


def _numeric_matrix(path: Path) -> np.ndarray:
    frame = pd.read_csv(path)
    array = frame.apply(pd.to_numeric, errors="raise").to_numpy(dtype=float)
    if array.ndim != 2 or not np.all(np.isfinite(array)):
        raise ValueError(f"{path.name} must contain one finite numeric matrix")
    return array


def _eigenfunction_matrix(
    path: Path,
    *,
    n_time: int,
    n_components: int,
) -> np.ndarray:
    array = _numeric_matrix(path)
    if array.shape == (n_time, n_components):
        return array.T
    if array.shape == (n_components, n_time):
        return array
    raise ValueError(
        f"{path.name} must have shape ({n_time}, {n_components}) "
        f"or ({n_components}, {n_time}); got {array.shape}"
    )


def _normalize_functions(
    functions: np.ndarray,
    weights: np.ndarray,
) -> np.ndarray:
    functions = np.asarray(functions, dtype=float).copy()
    for component in range(functions.shape[0]):
        norm = np.sqrt(
            np.sum(
                functions[component] ** 2
                * weights[None, :, None],
            )
        )
        if not np.isfinite(norm) or norm <= 1e-12:
            raise ValueError("mGSFPCA eigenfunction has zero/invalid norm")
        functions[component] /= norm
    return functions


def _functional_subspace_cosines(
    estimated: np.ndarray,
    truth: np.ndarray,
    weights: np.ndarray,
) -> np.ndarray:
    estimated = _normalize_functions(estimated, weights)
    truth = _normalize_functions(truth, weights)
    cross = np.einsum(
        "ktd,ltd,t->kl",
        estimated,
        truth,
        weights,
        optimize=True,
    )
    return np.clip(
        np.linalg.svd(cross, compute_uv=False),
        0.0,
        1.0,
    )


def _column_subspace_cosines(
    estimated: np.ndarray,
    truth: np.ndarray,
) -> np.ndarray:
    estimated = np.asarray(estimated, dtype=float)
    truth = np.asarray(truth, dtype=float)
    if (
        estimated.ndim != 2
        or truth.ndim != 2
        or estimated.shape[0] != truth.shape[0]
    ):
        raise ValueError("estimated/truth score matrices must share row count")
    estimated = estimated - estimated.mean(axis=0, keepdims=True)
    truth = truth - truth.mean(axis=0, keepdims=True)
    q_est, _ = np.linalg.qr(estimated)
    q_truth, _ = np.linalg.qr(truth)
    return np.clip(
        np.linalg.svd(q_est.T @ q_truth, compute_uv=False),
        0.0,
        1.0,
    )


def evaluate(output_dir: Path) -> dict[str, object]:
    truth_payload = json.loads(
        (output_dir / "external_fixture_truth.json").read_text(
            encoding="utf-8"
        )
    )
    grid = np.asarray(truth_payload["truth_grid"], dtype=float)
    weights = functional_trapezoid_weights(grid)
    truth_functions = np.asarray(
        truth_payload["eigenfunctions"],
        dtype=float,
    )
    n_components = len(truth_payload["eigenvalues"])
    if truth_functions.shape != (
        n_components,
        grid.size,
        2,
    ):
        raise ValueError("external fixture truth eigenfunction shape is invalid")

    eig_x = _eigenfunction_matrix(
        output_dir / "mgsfpca_eigenfunctions_x.csv",
        n_time=grid.size,
        n_components=n_components,
    )
    eig_y = _eigenfunction_matrix(
        output_dir / "mgsfpca_eigenfunctions_y.csv",
        n_time=grid.size,
        n_components=n_components,
    )
    estimated_functions = np.stack((eig_x, eig_y), axis=2)
    functional_cosines = _functional_subspace_cosines(
        estimated_functions,
        truth_functions,
        weights,
    )

    eigenvalue_frame = pd.read_csv(
        output_dir / "mgsfpca_eigenvalues.csv"
    )
    eigenvalues = pd.to_numeric(
        eigenvalue_frame["eigenvalue"],
        errors="raise",
    ).to_numpy(dtype=float)
    if eigenvalues.size < n_components:
        raise ValueError("mGSFPCA returned fewer components than requested")
    if not np.all(np.isfinite(eigenvalues[:n_components])):
        raise ValueError("mGSFPCA returned non-finite eigenvalues")

    scores_frame = pd.read_csv(output_dir / "mgsfpca_scores.csv")
    if "ID" not in scores_frame.columns:
        raise ValueError("mGSFPCA score export must retain subject IDs")
    estimated_scores = scores_frame.drop(columns=["ID"]).apply(
        pd.to_numeric,
        errors="raise",
    ).to_numpy(dtype=float)[:, :n_components]

    truth_scores = np.asarray(
        truth_payload["scores"],
        dtype=float,
    )
    truth_ids = list(truth_payload["curve_ids"])
    score_ids = scores_frame["ID"].astype(str).tolist()
    if score_ids != truth_ids:
        order = {identifier: index for index, identifier in enumerate(score_ids)}
        try:
            estimated_scores = estimated_scores[
                [order[identifier] for identifier in truth_ids]
            ]
        except KeyError as exc:
            raise ValueError(
                "mGSFPCA score IDs do not match the frozen fixture"
            ) from exc

    score_cosines = _column_subspace_cosines(
        estimated_scores,
        truth_scores[:, :n_components],
    )

    payload = {
        "schema_version": 1,
        "audit": "pre-0.12 external sparse multivariate sensitivity",
        "comparator": "mGSFPCA::spMultFPCA",
        "comparator_version": "0.2.2",
        "eyetrajectoriespy_version": importlib.metadata.version(
            "eyetrajectoriespy"
        ),
        "equivalence_claim": False,
        "fixture_rho_xy": float(truth_payload["rho_xy"]),
        "n_curves": len(truth_ids),
        "n_components": n_components,
        "functional_subspace_principal_cosines": [
            float(value) for value in functional_cosines
        ],
        "functional_subspace_min_principal_cosine": float(
            np.min(functional_cosines)
        ),
        "score_subspace_principal_cosines": [
            float(value) for value in score_cosines
        ],
        "score_subspace_min_principal_cosine": float(
            np.min(score_cosines)
        ),
        "estimated_eigenvalues": [
            float(value) for value in eigenvalues[:n_components]
        ],
        "truth_eigenvalues": [
            float(value) for value in truth_payload["eigenvalues"]
        ],
        "interpretation": (
            "Descriptive cross-implementation sensitivity evidence only. "
            "Different sparse smoothing, likelihood, univariate truncation, "
            "score construction, and normalization contracts preclude an "
            "exact-equivalence claim."
        ),
    }
    (output_dir / "mgsfpca_sensitivity.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    payload = evaluate(args.output_dir)
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
