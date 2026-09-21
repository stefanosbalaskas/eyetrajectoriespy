"""Simultaneous uncertainty bands for common-grid functional means."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .types import FunctionalMeanBandResult, TrajectorySet
from .validation import validate_trajectory_set


def _functional_mean_units(
    trajectories: TrajectorySet,
    *,
    unit: str,
    participant_column: str | None,
) -> tuple[np.ndarray, tuple[str, ...], dict[str, object]]:
    validate_trajectory_set(trajectories, require_complete=True)
    if not np.all(np.isfinite(trajectories.values)):
        raise ValueError("Functional mean inference requires finite trajectory values")
    if trajectories.coordinate_system == "probability_simplex":
        raise ValueError(
            "Direct Euclidean simultaneous bands are not supported for "
            "probability_simplex trajectories; use an explicit compositional/"
            "log-ratio representation first"
        )

    if unit not in {"curve", "participant"}:
        raise ValueError("unit must be 'curve' or 'participant'")

    if unit == "curve":
        if participant_column is not None:
            raise ValueError(
                "participant_column must be None when unit='curve'; "
                "use unit='participant' for equal-weight participant inference"
            )
        return (
            trajectories.values.copy(),
            trajectories.curve_ids,
            {
                "estimand": "equal_weight_curve_mean",
                "curves_per_unit": [1] * trajectories.n_curves,
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

    values = []
    counts = []
    for participant_id in unit_ids:
        index = np.flatnonzero(participant == participant_id)
        values.append(np.mean(trajectories.values[index], axis=0))
        counts.append(int(len(index)))

    return (
        np.stack(values, axis=0),
        unit_ids,
        {
            "estimand": "equal_weight_mean_of_participant_mean_trajectories",
            "curves_per_unit": counts,
        },
    )


def multiplier_functional_mean_band(
    trajectories: TrajectorySet,
    *,
    confidence_level: float = 0.95,
    n_multiplier: int = 2000,
    unit: str = "curve",
    participant_column: str | None = None,
    random_state: int | None = 0,
) -> FunctionalMeanBandResult:
    """Estimate a simultaneous band for the functional mean on the observed grid.

    The procedure uses a Gaussian multiplier bootstrap for the studentized
    empirical mean process and calibrates the band with the maximum absolute
    standardized deviation across all observed time points and functional
    dimensions.

    With unit="participant", repeated trajectories are first averaged within
    participant. The estimand is therefore the equal-weight population mean of
    participant-average trajectories, not a curve-weighted mean.

    The band is simultaneous over the observed time x dimension grid. It does
    not assert continuous-domain coverage between grid points.
    """

    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must lie in (0, 1)")
    if isinstance(n_multiplier, bool) or not isinstance(n_multiplier, int):
        raise TypeError("n_multiplier must be an integer")
    if n_multiplier < 100:
        raise ValueError("n_multiplier must be at least 100")

    unit_values, unit_ids, unit_provenance = _functional_mean_units(
        trajectories,
        unit=unit,
        participant_column=participant_column,
    )
    n_units = len(unit_ids)
    if n_units < 2:
        raise ValueError("At least two independent inference units are required")

    mean = np.mean(unit_values, axis=0)
    residual = unit_values - mean[None, :, :]
    pointwise_sd = np.std(unit_values, axis=0, ddof=1)
    pointwise_se = pointwise_sd / np.sqrt(n_units)

    positive_variance = pointwise_sd > np.finfo(float).eps
    rng = np.random.default_rng(random_state)
    max_statistics = np.zeros(n_multiplier, dtype=float)

    if np.any(positive_variance):
        batch_size = min(256, n_multiplier)
        for start in range(0, n_multiplier, batch_size):
            stop = min(start + batch_size, n_multiplier)
            multipliers = rng.normal(size=(stop - start, n_units))
            process = np.einsum(
                "bi,itd->btd",
                multipliers,
                residual,
                optimize=True,
            ) / np.sqrt(n_units)

            standardized = np.zeros_like(process)
            np.divide(
                process,
                pointwise_sd[None, :, :],
                out=standardized,
                where=positive_variance[None, :, :],
            )
            max_statistics[start:stop] = np.max(
                np.abs(standardized),
                axis=(1, 2),
            )

        critical_value = float(
            np.quantile(
                max_statistics,
                confidence_level,
                method="higher",
            )
        )
    else:
        critical_value = 0.0

    lower = mean - critical_value * pointwise_se
    upper = mean + critical_value * pointwise_se

    return FunctionalMeanBandResult(
        mean=mean,
        lower=lower,
        upper=upper,
        pointwise_se=pointwise_se,
        critical_value=critical_value,
        max_statistics=max_statistics,
        confidence_level=float(confidence_level),
        unit=unit,
        unit_ids=unit_ids,
        participant_column=participant_column if unit == "participant" else None,
        time=trajectories.time.copy(),
        dimension_names=trajectories.dimension_names,
        coordinate_system=trajectories.coordinate_system,
        time_unit=trajectories.time_unit,
        provenance={
            **dict(trajectories.provenance),
            "functional_mean_band": {
                "method": "gaussian_multiplier_studentized_maximum",
                "confidence_level": float(confidence_level),
                "n_multiplier": n_multiplier,
                "random_state": random_state,
                "unit": unit,
                "participant_column": (
                    participant_column if unit == "participant" else None
                ),
                "n_units": n_units,
                "zero_variance_grid_points": int(
                    np.size(positive_variance) - np.count_nonzero(positive_variance)
                ),
                "simultaneous_domain": "observed_time_by_dimension_grid",
                "continuous_between_grid_points": False,
                **unit_provenance,
            },
        },
    )


def functional_mean_band_frame(
    result: FunctionalMeanBandResult,
) -> pd.DataFrame:
    """Return a long-form table of simultaneous functional-mean band values."""

    rows: list[dict[str, float | str]] = []
    for dim, name in enumerate(result.dimension_names):
        for index, time in enumerate(result.time):
            rows.append(
                {
                    "time": float(time),
                    "dimension": name,
                    "mean": float(result.mean[index, dim]),
                    "pointwise_se": float(result.pointwise_se[index, dim]),
                    "lower": float(result.lower[index, dim]),
                    "upper": float(result.upper[index, dim]),
                }
            )
    return pd.DataFrame(rows)
