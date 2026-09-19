"""Optional sparse functional PCA interoperability through FDApy."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version as package_version
from collections.abc import Mapping
from typing import Any

import numpy as np
import pandas as pd

from .types import IrregularTrajectorySet, SparseFPCAResult


def _fdapy_version() -> str | None:
    try:
        return package_version("FDApy")
    except PackageNotFoundError:
        return None


def sparse_dimension_summary(
    trajectories: IrregularTrajectorySet,
    *,
    dimension: str,
) -> pd.DataFrame:
    """Summarize curve-specific observation density for one sparse dimension."""

    if dimension not in trajectories.dimension_names:
        raise KeyError(f"Unknown dimension {dimension!r}")
    index = trajectories.dimension_names.index(dimension)
    rows = []
    for curve_id, time, values in zip(
        trajectories.curve_ids,
        trajectories.time,
        trajectories.values,
        strict=True,
    ):
        observed = np.isfinite(values[:, index])
        intervals = np.diff(time[observed]) if np.count_nonzero(observed) >= 2 else np.array([])
        rows.append(
            {
                "curve_id": curve_id,
                "n_sample_times": int(len(time)),
                "n_observed": int(np.count_nonzero(observed)),
                "n_nonfinite": int(np.count_nonzero(~observed)),
                "observed_fraction": float(np.mean(observed)),
                "time_start": float(time[0]),
                "time_end": float(time[-1]),
                "time_span": float(time[-1] - time[0]),
                "median_observed_interval": (
                    float(np.median(intervals)) if intervals.size else np.nan
                ),
                "max_observed_interval": (
                    float(np.max(intervals)) if intervals.size else np.nan
                ),
            }
        )
    return pd.DataFrame(rows)


def _validate_sparse_dimension(
    trajectories: IrregularTrajectorySet,
    *,
    dimension: str,
) -> int:
    if dimension not in trajectories.dimension_names:
        raise KeyError(f"Unknown dimension {dimension!r}")
    index = trajectories.dimension_names.index(dimension)
    for curve_id, values in zip(
        trajectories.curve_ids,
        trajectories.values,
        strict=True,
    ):
        selected = values[:, index]
        if not np.all(np.isfinite(selected)):
            raise ValueError(
                f"Curve {curve_id!r} contains non-finite values in dimension "
                f"{dimension!r}. Sparse FDA requires absent observations to be "
                "represented by absent samples, not NaN/Inf placeholders."
            )
    return index


def to_fdapy_irregular(
    trajectories: IrregularTrajectorySet,
    *,
    dimension: str,
):
    """Convert one native irregular dimension to FDApy without interpolation."""

    index = _validate_sparse_dimension(trajectories, dimension=dimension)
    try:
        from FDApy import IrregularFunctionalData
        from FDApy.representation import (
            DenseArgvals,
            IrregularArgvals,
            IrregularValues,
        )
    except ImportError as exc:
        raise ImportError(
            "FDApy is optional. Install eyetrajectoriespy with the 'sparse' extra in a Python 3.11 or 3.12 environment."
        ) from exc

    argvals = IrregularArgvals(
        {
            i: DenseArgvals({"input_dim_0": time.copy()})
            for i, time in enumerate(trajectories.time)
        }
    )
    values = IrregularValues(
        {
            i: curve[:, index].copy()
            for i, curve in enumerate(trajectories.values)
        }
    )
    return IrregularFunctionalData(argvals=argvals, values=values)


def fit_sparse_fpca_fdapy(
    trajectories: IrregularTrajectorySet,
    *,
    dimension: str,
    n_components: int = 3,
    fit_smoothing: str | None = "PS",
    score_smoothing: str = "LP",
    tol: float = 1e-4,
    normalize: bool = False,
    evaluation_grid: np.ndarray | None = None,
    kwargs_mean: Mapping[str, Any] | None = None,
    kwargs_covariance: Mapping[str, Any] | None = None,
) -> SparseFPCAResult:
    """Fit univariate sparse FPCA and recover scores with FDApy PACE.

    The estimator uses FDApy's covariance-operator UFPCA path and PACE
    conditional-expectation scoring. No common-grid interpolation is performed.
    """

    if isinstance(n_components, bool) or not isinstance(n_components, int):
        raise TypeError("n_components must be an integer")
    if n_components < 1:
        raise ValueError("n_components must be positive")
    if n_components > trajectories.n_curves:
        raise ValueError("n_components cannot exceed number of curves")
    if tol <= 0 or not np.isfinite(tol):
        raise ValueError("tol must be finite and positive")
    if not isinstance(normalize, bool):
        raise TypeError("normalize must be boolean")
    allowed_fit_smoothing = {None, "PS", "LP"}
    if fit_smoothing not in allowed_fit_smoothing:
        raise ValueError("fit_smoothing must be None, 'PS', or 'LP'")
    if score_smoothing not in {"PS", "LP"}:
        raise ValueError("score_smoothing must be 'PS' or 'LP'")
    if kwargs_mean is not None and not isinstance(kwargs_mean, Mapping):
        raise TypeError("kwargs_mean must be a mapping or None")
    if kwargs_covariance is not None and not isinstance(kwargs_covariance, Mapping):
        raise TypeError("kwargs_covariance must be a mapping or None")

    grid = None
    if evaluation_grid is not None:
        grid = np.asarray(evaluation_grid, dtype=float)
        if (
            grid.ndim != 1
            or len(grid) < 2
            or not np.all(np.isfinite(grid))
            or not np.all(np.diff(grid) > 0)
        ):
            raise ValueError(
                "evaluation_grid must be a finite, strictly increasing one-dimensional array"
            )

    data = to_fdapy_irregular(trajectories, dimension=dimension)
    try:
        from FDApy.preprocessing import UFPCA
        from FDApy.representation import DenseArgvals
    except ImportError as exc:
        raise ImportError(
            "FDApy is optional. Install eyetrajectoriespy with the 'sparse' extra in a Python 3.11 or 3.12 environment."
        ) from exc

    model = UFPCA(
        n_components=n_components,
        method="covariance",
        normalize=normalize,
    )
    points = (
        None
        if grid is None
        else DenseArgvals({"input_dim_0": grid.copy()})
    )
    mean_kwargs = dict(kwargs_mean or {})
    covariance_kwargs = dict(kwargs_covariance or {})
    model.fit(
        data,
        points=points,
        method_smoothing=fit_smoothing,
        kwargs_mean=mean_kwargs,
        kwargs_covariance=covariance_kwargs,
    )
    scores = np.asarray(
        model.transform(
            data,
            method="PACE",
            method_smoothing=score_smoothing,
            tol=tol,
        ),
        dtype=float,
    )
    if scores.shape != (trajectories.n_curves, n_components):
        raise RuntimeError(
            "FDApy returned an unexpected PACE score shape; expected "
            f"{(trajectories.n_curves, n_components)}, got {scores.shape}"
        )
    if not np.all(np.isfinite(scores)):
        raise RuntimeError("FDApy returned non-finite PACE scores")

    eigenvalues = np.asarray(model.eigenvalues, dtype=float)
    if eigenvalues.shape != (n_components,) or not np.all(np.isfinite(eigenvalues)):
        raise RuntimeError("FDApy returned invalid sparse-FPCA eigenvalues")

    reconstructed = model.inverse_transform(scores)

    return SparseFPCAResult(
        scores=scores,
        eigenvalues=eigenvalues,
        dimension=dimension,
        curve_ids=trajectories.curve_ids,
        metadata=trajectories.metadata.reset_index(drop=True),
        coordinate_system=trajectories.coordinate_system,
        time_unit=trajectories.time_unit,
        n_components=n_components,
        fit_method="covariance",
        fit_smoothing=fit_smoothing,
        score_method="PACE",
        score_smoothing=score_smoothing,
        tolerance=float(tol),
        normalize=normalize,
        provenance={
            **dict(trajectories.provenance),
            "sparse_fpca": {
                "backend": "FDApy",
                "backend_version": _fdapy_version(),
                "dimension": dimension,
                "fit_method": "covariance",
                "fit_smoothing": fit_smoothing,
                "score_method": "PACE",
                "score_smoothing": score_smoothing,
                "tolerance": float(tol),
                "normalize": normalize,
                "evaluation_grid": None if grid is None else grid.tolist(),
                "kwargs_mean": mean_kwargs,
                "kwargs_covariance": covariance_kwargs,
                "sample_counts": trajectories.sample_counts.tolist(),
                "interpolation_performed": False,
            },
        },
        backend_object=model,
        backend_data=data,
        reconstructed_backend=reconstructed,
    )


def sparse_fpca_score_frame(result: SparseFPCAResult) -> pd.DataFrame:
    """Return PACE scores with curve IDs and preserved curve metadata."""

    frame = result.metadata.reset_index(drop=True).copy()
    frame.insert(0, "curve_id", result.curve_ids)
    for component in range(result.n_components):
        frame[f"SFPC{component + 1}"] = result.scores[:, component]
    return frame
