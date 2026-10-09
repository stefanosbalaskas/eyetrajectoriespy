"""F4: independent-curve holdout reconstruction comparison for AOI geometry.

Both models are trained *only* on declared training curves and reconstruct
holdout functions by projection. This is not a new constrained FPCA estimator.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd
from eyetrajectoriespy.types import TrajectorySet
from eyetrajectoriespy.fpca import fit_mfpca, transform_fpca, reconstruct_fpca
from eyetrajectoriespy.compositional import (
    fit_compositional_fpca, inverse_alr, alr_transform,
)
from eyetrajectoriespy.validation import validate_simplex
from .aoi_feasibility import project_simplex


@dataclass(frozen=True)
class AOIGeometryHoldout:
    summary: pd.DataFrame
    alr_reconstruction: np.ndarray
    projected_reconstruction: np.ndarray
    n_train: int
    n_test: int
    reference_dimension: int
    epsilon: float
    leakage_guard_passed: bool = True
    provisional: bool = True


def compare_aoi_functional_geometries_holdout(
    train: TrajectorySet,
    test: TrajectorySet,
    *,
    n_components: int = 2,
    reference_dimension: int = -1,
    epsilon: float = 1e-6,
    participant_column: str | None = "participant_id",
) -> AOIGeometryHoldout:
    """Compare held-out functional approximation, never extrapolated scores.

    The held-out curves are projected onto frozen bases learned from train.
    Evaluation is **reconstruction**, not out-of-sample prediction or causal
    group recovery; heldout observed time samples are used to obtain scores.
    """
    if not isinstance(train, TrajectorySet) or not isinstance(test, TrajectorySet):
        raise TypeError("both inputs must be TrajectorySet")
    if not np.array_equal(train.time, test.time) or (
        train.dimension_names != test.dimension_names
    ):
        raise ValueError("holdout requires an identical grid and AOI order")
    if len(train.dimension_names) < 3:
        raise ValueError("existing ALR-MFPCA requires at least three AOI channels")
    if set(train.curve_ids) & set(test.curve_ids):
        raise ValueError("overlapping curve identities violate train/holdout isolation")
    if participant_column is not None:
        if participant_column not in train.metadata.columns or (
            participant_column not in test.metadata.columns
        ):
            raise ValueError("explicit holdout requires participant metadata in both groups")
        first = set(train.metadata[participant_column].astype(str))
        second = set(test.metadata[participant_column].astype(str))
        if first & second:
            raise ValueError("train/test participant overlap violates grouped holdout")
    if not np.isfinite(train.values).all() or not np.isfinite(test.values).all():
        raise ValueError("missing observations cannot be silently imputed")
    validate_simplex(train.values)
    validate_simplex(test.values)
    if not isinstance(n_components, int) or isinstance(n_components, bool) or n_components < 1:
        raise ValueError("n_components must be a positive integer")
    if not np.isfinite(epsilon) or epsilon <= 0:
        raise ValueError("epsilon must be finite and positive")
    ref = reference_dimension % train.n_dimensions
    alr = fit_compositional_fpca(
        train, reference_dimension=ref, epsilon=epsilon,
        n_components=n_components, scaling="none",
    )
    raw = fit_mfpca(train, n_components=n_components, scaling="none")
    transformed = TrajectorySet(
        time=test.time, values=alr_transform(
            test.values, reference_dimension=ref, epsilon=epsilon,
        ),
        curve_ids=test.curve_ids,
        dimension_names=alr.fpca.dimension_names,
        metadata=test.metadata.reset_index(drop=True),
        coordinate_system="simplex_logratio",
        time_unit=test.time_unit,
    )
    alr_scores = transform_fpca(alr.fpca, transformed)
    raw_scores = transform_fpca(raw, test)
    predicted_alr = inverse_alr(
        reconstruct_fpca(alr.fpca, scores=alr_scores),
        reference_dimension=ref,
        n_dimensions=train.n_dimensions,
    )
    predicted_raw = project_simplex(reconstruct_fpca(raw, scores=raw_scores))
    mse_alr = float(np.mean((predicted_alr - test.values)**2))
    mse_projected = float(np.mean((predicted_raw - test.values)**2))
    results = pd.DataFrame([
        {"geometry": "existing_ALR_FPCA", "holdout_reconstruction_mse": mse_alr,
         "reference_AOI": train.dimension_names[ref], "epsilon": epsilon},
        {"geometry": "raw_FPCA_then_simplex_projection",
         "holdout_reconstruction_mse": mse_projected,
         "reference_AOI": "not_applicable", "epsilon": np.nan},
    ])
    return AOIGeometryHoldout(
        summary=results,
        alr_reconstruction=predicted_alr,
        projected_reconstruction=predicted_raw,
        n_train=train.n_curves, n_test=test.n_curves,
        reference_dimension=ref, epsilon=epsilon,
    )
