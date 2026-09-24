"""Function-on-scalar regression for common-grid functional responses."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

from .types import (
    FunctionOnScalarBandResult,
    FunctionOnScalarBootstrapResult,
    FunctionOnScalarResult,
    TrajectorySet,
)
from .validation import validate_trajectory_set


def _validate_design_alignment(
    trajectories: TrajectorySet,
    design: pd.DataFrame,
    predictors: Sequence[str],
) -> tuple[pd.DataFrame, tuple[str, ...]]:
    if not isinstance(design, pd.DataFrame):
        raise TypeError("design must be a pandas DataFrame")
    if len(design) != trajectories.n_curves:
        raise ValueError(
            "design must contain exactly one row per source trajectory"
        )
    if isinstance(predictors, (str, bytes)):
        raise TypeError("predictors must be a non-string sequence")
    raw_predictors = tuple(predictors)
    if not all(isinstance(name, str) for name in raw_predictors):
        raise TypeError("predictor names must be strings")
    predictor_names = raw_predictors
    if not predictor_names:
        raise ValueError("predictors must contain at least one column name")
    if len(set(predictor_names)) != len(predictor_names):
        raise ValueError("predictors must not contain duplicates")
    if "Intercept" in predictor_names:
        raise ValueError(
            "predictors must not contain the reserved coefficient name 'Intercept'"
        )
    missing = [name for name in predictor_names if name not in design.columns]
    if missing:
        raise KeyError(f"design is missing predictor columns: {missing}")

    aligned = design.copy()
    if "curve_id" in aligned.columns:
        curve_ids = tuple(aligned["curve_id"].astype(str))
        if curve_ids != trajectories.curve_ids:
            raise ValueError(
                "design['curve_id'] must match trajectories.curve_ids exactly "
                "and in the same order"
            )
        alignment = "curve_id_column"
    else:
        expected = pd.RangeIndex(trajectories.n_curves)
        if not aligned.index.equals(expected):
            raise ValueError(
                "design without a curve_id column must use the default "
                "RangeIndex in trajectory row order"
            )
        alignment = "explicit_row_order"

    for name in predictor_names:
        try:
            values = pd.to_numeric(aligned[name], errors="raise").to_numpy(
                dtype=float
            )
        except (TypeError, ValueError) as exc:
            raise TypeError(
                f"predictor {name!r} must be numeric; encode categorical "
                "variables explicitly before fitting"
            ) from exc
        if not np.all(np.isfinite(values)):
            raise ValueError(f"predictor {name!r} contains non-finite values")
        aligned[name] = values

    aligned.attrs["eyetrajectoriespy_alignment"] = alignment
    return aligned, predictor_names


def _select_dimensions(
    trajectories: TrajectorySet,
    dimensions: Sequence[str] | None,
) -> tuple[tuple[str, ...], np.ndarray]:
    if dimensions is None:
        names = trajectories.dimension_names
    else:
        if isinstance(dimensions, (str, bytes)):
            raise TypeError("dimensions must be a non-string sequence")
        raw_names = tuple(dimensions)
        if not all(isinstance(name, str) for name in raw_names):
            raise TypeError("dimension names must be strings")
        names = raw_names
        if not names:
            raise ValueError("dimensions must contain at least one name")
        if len(set(names)) != len(names):
            raise ValueError("dimensions must not contain duplicates")
        missing = [name for name in names if name not in trajectories.dimension_names]
        if missing:
            raise KeyError(f"Unknown trajectory dimensions: {missing}")
    indices = np.asarray(
        [trajectories.dimension_names.index(name) for name in names],
        dtype=int,
    )
    return names, indices


def _participant_units(
    trajectories: TrajectorySet,
    design: pd.DataFrame,
    predictor_names: tuple[str, ...],
    values: np.ndarray,
    *,
    unit: str,
    participant_column: str | None,
) -> tuple[
    np.ndarray,
    np.ndarray,
    tuple[str, ...],
    tuple[int, ...],
    dict[str, object],
]:
    if unit not in {"curve", "participant"}:
        raise ValueError("unit must be 'curve' or 'participant'")

    x_predictors = design.loc[:, list(predictor_names)].to_numpy(dtype=float)

    if unit == "curve":
        if participant_column is not None:
            raise ValueError(
                "participant_column must be None when unit='curve'; use "
                "unit='participant' to avoid treating repeated trials as "
                "independent"
            )
        return (
            values.copy(),
            x_predictors.copy(),
            trajectories.curve_ids,
            tuple(1 for _ in trajectories.curve_ids),
            {
                "estimand": "curve_level_functional_mean_response",
                "independence_contract": (
                    "source curves are asserted to be independent inference units"
                ),
                "participant_predictor_policy": None,
            },
        )

    if participant_column is None:
        raise ValueError("participant_column is required when unit='participant'")
    if participant_column not in trajectories.metadata.columns:
        raise ValueError(
            f"metadata does not contain participant column {participant_column!r}"
        )
    if trajectories.metadata[participant_column].isna().any():
        raise ValueError("participant_column contains missing values")

    participant = trajectories.metadata[participant_column].astype(str).to_numpy()
    unit_ids = tuple(pd.unique(participant))
    if len(unit_ids) < 2:
        raise ValueError("At least two unique participants are required")

    unit_values: list[np.ndarray] = []
    unit_design: list[np.ndarray] = []
    counts: list[int] = []

    for participant_id in unit_ids:
        index = np.flatnonzero(participant == participant_id)
        participant_design = x_predictors[index]
        reference = participant_design[0]
        if not np.all(participant_design == reference[None, :]):
            varying = [
                predictor_names[j]
                for j in range(len(predictor_names))
                if not np.all(participant_design[:, j] == reference[j])
            ]
            raise ValueError(
                "unit='participant' requires predictors to be constant within "
                f"participant; {participant_id!r} varies on {varying}. "
                "Trial-varying predictors require a repeated-measures/"
                "functional mixed-effects model rather than participant "
                "aggregation."
            )
        unit_values.append(np.mean(values[index], axis=0))
        unit_design.append(reference.copy())
        counts.append(int(index.size))

    return (
        np.stack(unit_values, axis=0),
        np.stack(unit_design, axis=0),
        unit_ids,
        tuple(counts),
        {
            "estimand": (
                "equal_weight_participant_mean_function_conditional_on_"
                "participant_level_predictors"
            ),
            "independence_contract": (
                "participants are the independent inference units"
            ),
            "participant_predictor_policy": (
                "all declared predictors must be constant within participant"
            ),
        },
    )


def _fit_arrays(
    y: np.ndarray,
    predictor_matrix: np.ndarray,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    int,
    int,
]:
    n_units = int(y.shape[0])
    x = np.column_stack([np.ones(n_units, dtype=float), predictor_matrix])
    n_coefficients = int(x.shape[1])
    rank = int(np.linalg.matrix_rank(x))
    if rank != n_coefficients:
        raise ValueError(
            "design matrix is rank deficient; remove redundant predictors or "
            "encode the model explicitly before fitting"
        )
    residual_df = n_units - rank
    if residual_df <= 0:
        raise ValueError(
            "function-on-scalar regression requires positive residual degrees "
            "of freedom"
        )

    xtx_inverse = np.linalg.inv(x.T @ x)
    projector = xtx_inverse @ x.T
    coefficients = np.einsum("pn,ntd->ptd", projector, y, optimize=True)
    fitted = np.einsum("np,ptd->ntd", x, coefficients, optimize=True)
    residuals = y - fitted

    influence_weight = x @ xtx_inverse
    influence = influence_weight[:, :, None, None] * residuals[:, None, :, :]
    correction = n_units / residual_df
    variance = correction * np.sum(influence**2, axis=0)
    standard_errors = np.sqrt(np.maximum(variance, 0.0))

    return (
        x,
        coefficients,
        fitted,
        residuals,
        standard_errors,
        rank,
        residual_df,
    )


def fit_function_on_scalar_regression(
    trajectories: TrajectorySet,
    design: pd.DataFrame,
    predictors: Sequence[str],
    *,
    dimensions: Sequence[str] | None = None,
    participant_column: str | None = None,
    unit: str = "curve",
) -> FunctionOnScalarResult:
    """Fit common-grid function-on-scalar OLS with explicit inference units.

    The model is fitted independently at every observed time by dimension grid
    point using one shared scalar design matrix. No smoothing, basis expansion,
    coefficient regularization, categorical encoding, centering, scaling,
    interaction construction, or model selection is performed.

    With unit='participant', repeated source curves are first averaged within
    participant and every declared predictor must be constant within
    participant. This supports participant-level between-subject regression
    without pseudo-replicating trials. It is not a functional mixed-effects
    model and deliberately refuses trial-varying predictors.
    """

    validate_trajectory_set(trajectories, require_complete=True)
    if not np.all(np.isfinite(trajectories.values)):
        raise ValueError(
            "function-on-scalar regression requires finite complete trajectories"
        )
    if trajectories.coordinate_system == "probability_simplex":
        raise ValueError(
            "Direct Euclidean function-on-scalar regression is not supported "
            "for probability_simplex trajectories; transform to an explicit "
            "log-ratio representation first"
        )

    aligned_design, predictor_names = _validate_design_alignment(
        trajectories,
        design,
        predictors,
    )
    dimension_names, dimension_indices = _select_dimensions(
        trajectories,
        dimensions,
    )
    selected_values = trajectories.values[:, :, dimension_indices]

    (
        unit_values,
        unit_predictors,
        unit_ids,
        curves_per_unit,
        unit_provenance,
    ) = _participant_units(
        trajectories,
        aligned_design,
        predictor_names,
        selected_values,
        unit=unit,
        participant_column=participant_column,
    )

    (
        design_matrix,
        coefficients,
        fitted,
        residuals,
        standard_errors,
        rank,
        residual_df,
    ) = _fit_arrays(unit_values, unit_predictors)

    coefficient_names = ("Intercept",) + predictor_names
    return FunctionOnScalarResult(
        coefficients=coefficients,
        standard_errors=standard_errors,
        fitted_functions=fitted,
        residual_functions=residuals,
        observed_functions=unit_values,
        design_matrix=design_matrix,
        coefficient_names=coefficient_names,
        predictor_names=predictor_names,
        design_rank=rank,
        residual_degrees_of_freedom=residual_df,
        unit=unit,
        unit_ids=unit_ids,
        curves_per_unit=curves_per_unit,
        participant_column=participant_column if unit == "participant" else None,
        time=trajectories.time.copy(),
        dimension_names=dimension_names,
        coordinate_system=trajectories.coordinate_system,
        time_unit=trajectories.time_unit,
        source_curve_ids=trajectories.curve_ids,
        provenance={
            **dict(trajectories.provenance),
            "function_on_scalar_regression": {
                "method": "observed_grid_ordinary_least_squares",
                "pointwise_standard_errors": "HC1_sandwich",
                "coefficient_regularization": False,
                "smoothing": False,
                "basis_expansion": False,
                "categorical_encoding": False,
                "predictor_centering": False,
                "predictor_scaling": False,
                "interaction_construction": False,
                "automatic_model_selection": False,
                "intercept": True,
                "predictors": list(predictor_names),
                "dimensions": list(dimension_names),
                "design_alignment": aligned_design.attrs[
                    "eyetrajectoriespy_alignment"
                ],
                "source_n_curves": trajectories.n_curves,
                "n_inference_units": len(unit_ids),
                "unit": unit,
                "participant_column": (
                    participant_column if unit == "participant" else None
                ),
                "curves_per_unit": list(curves_per_unit),
                "design_rank": rank,
                "residual_degrees_of_freedom": residual_df,
                "simultaneous_inference": False,
                "functional_mixed_effects_model": False,
                **unit_provenance,
            },
        },
    )


def bootstrap_function_on_scalar_coefficients(
    result: FunctionOnScalarResult,
    *,
    n_bootstrap: int = 1000,
    multiplier: str = "rademacher",
    random_state: int | None = 0,
) -> FunctionOnScalarBootstrapResult:
    """Wild-bootstrap function-on-scalar coefficient curves."""

    if not isinstance(result, FunctionOnScalarResult):
        raise TypeError("result must be a FunctionOnScalarResult")
    if isinstance(n_bootstrap, bool) or not isinstance(n_bootstrap, int):
        raise TypeError("n_bootstrap must be an integer")
    if n_bootstrap < 100:
        raise ValueError("n_bootstrap must be at least 100")
    if multiplier not in {"rademacher", "normal"}:
        raise ValueError("multiplier must be 'rademacher' or 'normal'")

    rng = np.random.default_rng(random_state)
    n_units = result.design_matrix.shape[0]
    n_coefficients = result.design_matrix.shape[1]
    xtx_inverse = np.linalg.inv(result.design_matrix.T @ result.design_matrix)
    projector = xtx_inverse @ result.design_matrix.T

    bootstrap_coefficients = np.empty(
        (
            n_bootstrap,
            n_coefficients,
            result.time.size,
            len(result.dimension_names),
        ),
        dtype=float,
    )
    multipliers = np.empty((n_bootstrap, n_units), dtype=float)

    for bootstrap_index in range(n_bootstrap):
        if multiplier == "rademacher":
            weights = rng.choice(
                np.array([-1.0, 1.0]),
                size=n_units,
                replace=True,
            )
        else:
            weights = rng.normal(size=n_units)
        multipliers[bootstrap_index] = weights
        y_star = (
            result.fitted_functions
            + weights[:, None, None] * result.residual_functions
        )
        bootstrap_coefficients[bootstrap_index] = np.einsum(
            "pn,ntd->ptd",
            projector,
            y_star,
            optimize=True,
        )

    return FunctionOnScalarBootstrapResult(
        reference=result,
        bootstrap_coefficients=bootstrap_coefficients,
        multipliers=multipliers,
        multiplier=multiplier,
        random_state=random_state,
        provenance={
            **dict(result.provenance),
            "function_on_scalar_bootstrap": {
                "method": "fixed_design_wild_bootstrap",
                "n_bootstrap": n_bootstrap,
                "multiplier": multiplier,
                "random_state": random_state,
                "unit": result.unit,
                "n_units": n_units,
                "design_resampled": False,
                "residual_functions_multiplied_as_whole_functions": True,
                "simultaneous_band_calibration": False,
            },
        },
    )


def function_on_scalar_simultaneous_bands(
    bootstrap: FunctionOnScalarBootstrapResult,
    *,
    confidence_level: float = 0.95,
    simultaneous_scope: str = "coefficient",
) -> FunctionOnScalarBandResult:
    """Calibrate observed-grid simultaneous bands for coefficient functions."""

    if not isinstance(bootstrap, FunctionOnScalarBootstrapResult):
        raise TypeError("bootstrap must be a FunctionOnScalarBootstrapResult")
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must lie in (0, 1)")
    if simultaneous_scope not in {"coefficient", "family"}:
        raise ValueError(
            "simultaneous_scope must be 'coefficient' or 'family'"
        )

    reference = bootstrap.reference
    standard_errors = reference.standard_errors
    positive = standard_errors > np.finfo(float).eps

    deviations = bootstrap.bootstrap_coefficients - reference.coefficients[None]
    standardized = np.zeros_like(deviations)
    np.divide(
        deviations,
        standard_errors[None],
        out=standardized,
        where=positive[None],
    )
    absolute = np.abs(standardized)

    if simultaneous_scope == "coefficient":
        max_statistics = np.max(absolute, axis=(2, 3))
        critical_values = np.quantile(
            max_statistics,
            confidence_level,
            axis=0,
            method="higher",
        )
    else:
        family_max = np.max(absolute, axis=(1, 2, 3))
        critical = float(
            np.quantile(
                family_max,
                confidence_level,
                method="higher",
            )
        )
        max_statistics = family_max[:, None]
        critical_values = np.full(
            len(reference.coefficient_names),
            critical,
            dtype=float,
        )

    lower = (
        reference.coefficients
        - critical_values[:, None, None] * standard_errors
    )
    upper = (
        reference.coefficients
        + critical_values[:, None, None] * standard_errors
    )

    return FunctionOnScalarBandResult(
        reference=reference,
        lower=lower,
        upper=upper,
        critical_values=np.asarray(critical_values, dtype=float),
        max_statistics=np.asarray(max_statistics, dtype=float),
        confidence_level=float(confidence_level),
        simultaneous_scope=simultaneous_scope,
        bootstrap=bootstrap,
        provenance={
            **dict(bootstrap.provenance),
            "function_on_scalar_simultaneous_bands": {
                "method": "wild_bootstrap_reference_studentized_maximum",
                "confidence_level": float(confidence_level),
                "simultaneous_scope": simultaneous_scope,
                "simultaneous_domain": (
                    "observed_time_by_dimension_grid_per_coefficient"
                    if simultaneous_scope == "coefficient"
                    else "coefficient_by_time_by_dimension_observed_grid"
                ),
                "continuous_between_grid_points": False,
                "pointwise_standard_errors": "HC1_sandwich",
                "zero_standard_error_cells": int(
                    np.size(positive) - np.count_nonzero(positive)
                ),
                "zero_standard_error_cells_receive_zero_width": True,
            },
        },
    )


def function_on_scalar_coefficient_frame(
    result: FunctionOnScalarResult,
    *,
    band: FunctionOnScalarBandResult | None = None,
) -> pd.DataFrame:
    """Return coefficient functions and optional simultaneous bands in long form."""

    if not isinstance(result, FunctionOnScalarResult):
        raise TypeError("result must be a FunctionOnScalarResult")
    if band is not None:
        if not isinstance(band, FunctionOnScalarBandResult):
            raise TypeError("band must be a FunctionOnScalarBandResult or None")
        if band.reference is not result:
            raise ValueError("band.reference must be the supplied result object")

    rows: list[dict[str, float | str]] = []
    for coefficient_index, coefficient_name in enumerate(result.coefficient_names):
        for dimension_index, dimension_name in enumerate(result.dimension_names):
            for time_index, time in enumerate(result.time):
                row: dict[str, float | str] = {
                    "coefficient": coefficient_name,
                    "time": float(time),
                    "dimension": dimension_name,
                    "estimate": float(
                        result.coefficients[
                            coefficient_index,
                            time_index,
                            dimension_index,
                        ]
                    ),
                    "standard_error": float(
                        result.standard_errors[
                            coefficient_index,
                            time_index,
                            dimension_index,
                        ]
                    ),
                }
                if band is not None:
                    row["lower"] = float(
                        band.lower[
                            coefficient_index,
                            time_index,
                            dimension_index,
                        ]
                    )
                    row["upper"] = float(
                        band.upper[
                            coefficient_index,
                            time_index,
                            dimension_index,
                        ]
                    )
                    row["critical_value"] = float(
                        band.critical_values[coefficient_index]
                    )
                rows.append(row)
    return pd.DataFrame(rows)
