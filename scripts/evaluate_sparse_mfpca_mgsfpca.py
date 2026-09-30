"""Evaluate mGSFPCA 0.2.2 against the same frozen 0.12 planar fixture.

This script reports invariant cross-implementation sensitivity only. It
compares mGSFPCA with both known truth and the canonical native direct sparse
MFPCA fit, using functional and score subspaces rather than raw signs.
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
    array = frame.apply(
        pd.to_numeric,
        errors="raise",
    ).to_numpy(dtype=float)
    if array.ndim != 2 or not np.all(np.isfinite(array)):
        raise ValueError(
            f"{path.name} must contain one finite numeric matrix"
        )
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
    array = np.asarray(functions, dtype=float).copy()
    norms = np.sqrt(
        np.einsum(
            "ktd,t,ktd->k",
            array,
            weights,
            array,
            optimize=True,
        )
    )
    if np.any(~np.isfinite(norms)) or np.any(norms <= 1e-12):
        raise ValueError(
            "comparator eigenfunction has zero/invalid norm"
        )
    return array / norms[:, None, None]


def functional_subspace_cosines(
    first: np.ndarray,
    second: np.ndarray,
    weights: np.ndarray,
) -> np.ndarray:
    first_n = _normalize_functions(first, weights)
    second_n = _normalize_functions(second, weights)
    cross = np.einsum(
        "ktd,ltd,t->kl",
        first_n,
        second_n,
        weights,
        optimize=True,
    )
    return np.clip(
        np.linalg.svd(cross, compute_uv=False),
        0.0,
        1.0,
    )


def score_subspace_cosines(
    first: np.ndarray,
    second: np.ndarray,
) -> np.ndarray:
    first_array = np.asarray(first, dtype=float)
    second_array = np.asarray(second, dtype=float)
    if (
        first_array.ndim != 2
        or second_array.ndim != 2
        or first_array.shape[0] != second_array.shape[0]
    ):
        raise ValueError(
            "score matrices must be two-dimensional with shared row count"
        )
    finite = np.all(np.isfinite(first_array), axis=1) & np.all(
        np.isfinite(second_array),
        axis=1,
    )
    if np.count_nonzero(finite) < 3:
        raise ValueError(
            "too few finite score rows for subspace comparison"
        )
    first_centered = first_array[finite] - np.mean(
        first_array[finite],
        axis=0,
        keepdims=True,
    )
    second_centered = second_array[finite] - np.mean(
        second_array[finite],
        axis=0,
        keepdims=True,
    )
    q_first, _ = np.linalg.qr(first_centered)
    q_second, _ = np.linalg.qr(second_centered)
    return np.clip(
        np.linalg.svd(q_first.T @ q_second, compute_uv=False),
        0.0,
        1.0,
    )


def _read_scores(
    path: Path,
    truth_ids: list[str],
    n_components: int,
) -> np.ndarray:
    frame = pd.read_csv(path)
    if "ID" not in frame.columns:
        raise ValueError(
            f"{path.name} must retain subject IDs"
        )
    ids = frame["ID"].astype(str).tolist()
    values = frame.drop(columns=["ID"]).apply(
        pd.to_numeric,
        errors="raise",
    ).to_numpy(dtype=float)
    if values.shape[1] < n_components:
        raise ValueError(
            f"{path.name} returned fewer components than required"
        )
    if ids != truth_ids:
        order = {identifier: index for index, identifier in enumerate(ids)}
        try:
            values = values[
                [order[identifier] for identifier in truth_ids]
            ]
        except KeyError as exc:
            raise ValueError(
                f"{path.name} IDs do not match the frozen fixture"
            ) from exc
    values = values[:, :n_components]
    if not np.all(np.isfinite(values)):
        raise ValueError(
            f"{path.name} contains non-finite scores"
        )
    return values


def _read_eigenvalues(
    path: Path,
    n_components: int,
) -> np.ndarray:
    frame = pd.read_csv(path)
    if "eigenvalue" not in frame.columns:
        raise ValueError(
            f"{path.name} must contain an eigenvalue column"
        )
    values = pd.to_numeric(
        frame["eigenvalue"],
        errors="raise",
    ).to_numpy(dtype=float)
    if values.size < n_components:
        raise ValueError(
            f"{path.name} returned fewer components than required"
        )
    values = values[:n_components]
    if not np.all(np.isfinite(values)):
        raise ValueError(
            f"{path.name} contains non-finite eigenvalues"
        )
    return values


def evaluate(output_dir: Path) -> dict[str, object]:
    truth_payload = json.loads(
        (output_dir / "external_fixture_truth.json").read_text(
            encoding="utf-8"
        )
    )
    if truth_payload["contract"]["equivalence_claim"] is not False:
        raise ValueError(
            "fixture contract must forbid exact equivalence claims"
        )

    grid = np.asarray(
        truth_payload["truth_grid"],
        dtype=float,
    )
    weights = functional_trapezoid_weights(grid)
    truth_functions = np.asarray(
        truth_payload["eigenfunctions"],
        dtype=float,
    )
    truth_scores = np.asarray(
        truth_payload["scores"],
        dtype=float,
    )
    truth_eigenvalues = np.asarray(
        truth_payload["eigenvalues"],
        dtype=float,
    )
    truth_ids = [
        str(value)
        for value in truth_payload["curve_ids"]
    ]
    n_components = truth_eigenvalues.size
    if truth_functions.shape != (
        n_components,
        grid.size,
        2,
    ):
        raise ValueError(
            "external fixture truth eigenfunction shape is invalid"
        )

    native_x = _eigenfunction_matrix(
        output_dir / "native_eigenfunctions_x.csv",
        n_time=grid.size,
        n_components=n_components,
    )
    native_y = _eigenfunction_matrix(
        output_dir / "native_eigenfunctions_y.csv",
        n_time=grid.size,
        n_components=n_components,
    )
    native_functions = np.stack(
        (native_x, native_y),
        axis=2,
    )
    native_scores = _read_scores(
        output_dir / "native_scores.csv",
        truth_ids,
        n_components,
    )
    native_eigenvalues = _read_eigenvalues(
        output_dir / "native_eigenvalues.csv",
        n_components,
    )

    mgs_x = _eigenfunction_matrix(
        output_dir / "mgsfpca_eigenfunctions_x.csv",
        n_time=grid.size,
        n_components=n_components,
    )
    mgs_y = _eigenfunction_matrix(
        output_dir / "mgsfpca_eigenfunctions_y.csv",
        n_time=grid.size,
        n_components=n_components,
    )
    mgs_functions = np.stack(
        (mgs_x, mgs_y),
        axis=2,
    )
    mgs_scores = _read_scores(
        output_dir / "mgsfpca_scores.csv",
        truth_ids,
        n_components,
    )
    mgs_eigenvalues = _read_eigenvalues(
        output_dir / "mgsfpca_eigenvalues.csv",
        n_components,
    )

    native_truth_functional = functional_subspace_cosines(
        native_functions,
        truth_functions,
        weights,
    )
    mgs_truth_functional = functional_subspace_cosines(
        mgs_functions,
        truth_functions,
        weights,
    )
    mgs_native_functional = functional_subspace_cosines(
        mgs_functions,
        native_functions,
        weights,
    )
    native_truth_scores = score_subspace_cosines(
        native_scores,
        truth_scores,
    )
    mgs_truth_scores = score_subspace_cosines(
        mgs_scores,
        truth_scores,
    )
    mgs_native_scores = score_subspace_cosines(
        mgs_scores,
        native_scores,
    )

    payload = {
        "schema_version": 1,
        "evidence_type": "cross_implementation_sensitivity",
        "comparison": "native_sparse_mfpca_vs_mGSFPCA",
        "comparator": "mGSFPCA::spMultFPCA",
        "comparator_version": "0.2.2",
        "eyetrajectoriespy_version": importlib.metadata.version(
            "eyetrajectoriespy"
        ),
        "equivalence_claim": False,
        "architecture_winner_selected": False,
        "fixture_rho_xy": float(truth_payload["rho_xy"]),
        "n_curves": len(truth_ids),
        "n_components": int(n_components),
        "native_truth_functional_subspace_principal_cosines": [
            float(value) for value in native_truth_functional
        ],
        "mgsfpca_truth_functional_subspace_principal_cosines": [
            float(value) for value in mgs_truth_functional
        ],
        "mgsfpca_native_functional_subspace_principal_cosines": [
            float(value) for value in mgs_native_functional
        ],
        "native_truth_score_subspace_principal_cosines": [
            float(value) for value in native_truth_scores
        ],
        "mgsfpca_truth_score_subspace_principal_cosines": [
            float(value) for value in mgs_truth_scores
        ],
        "mgsfpca_native_score_subspace_principal_cosines": [
            float(value) for value in mgs_native_scores
        ],
        "native_truth_functional_subspace_min_cosine": float(
            np.min(native_truth_functional)
        ),
        "mgsfpca_truth_functional_subspace_min_cosine": float(
            np.min(mgs_truth_functional)
        ),
        "mgsfpca_native_functional_subspace_min_cosine": float(
            np.min(mgs_native_functional)
        ),
        "native_truth_score_subspace_min_cosine": float(
            np.min(native_truth_scores)
        ),
        "mgsfpca_truth_score_subspace_min_cosine": float(
            np.min(mgs_truth_scores)
        ),
        "mgsfpca_native_score_subspace_min_cosine": float(
            np.min(mgs_native_scores)
        ),
        "truth_eigenvalues": [
            float(value) for value in truth_eigenvalues
        ],
        "native_eigenvalues": [
            float(value) for value in native_eigenvalues
        ],
        "mgsfpca_eigenvalues": [
            float(value) for value in mgs_eigenvalues
        ],
        "interpretation": (
            "Descriptive cross-implementation sensitivity only. "
            "Differences in smoothing, basis construction, likelihood, "
            "marginal truncation, normalization, and score construction "
            "preclude an exact-equivalence claim or automatic architecture "
            "selection."
        ),
    }
    (output_dir / "mgsfpca_sensitivity.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    payload = evaluate(args.output_dir)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
