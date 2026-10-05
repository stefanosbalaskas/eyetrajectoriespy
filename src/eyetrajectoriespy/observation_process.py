"""Diagnostics for potentially informative sparse observation processes.

This module is deliberately diagnostic. It requires an explicit candidate-sample
schedule/denominator and never reconstructs missing rows from retained gaze,
nominal sampling rate, or timestamp gaps. The first qualified tranche is
strictly descriptive: it reports support, run structure, time dependence, and
associations with always-available or past-information predictors. It does not
perform inverse-probability weighting, inverse-intensity correction, selection
modeling, or missing-gaze imputation.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype


_SCOPE = "descriptive_observation_process_diagnostics"
_ALLOWED_SOURCES = {"candidate_time", "design", "external_candidate_time"}
_HISTORY_NAMES = {
    "previous_observed_x",
    "previous_observed_y",
    "previous_observed_eccentricity",
    "previous_observed_speed",
    "time_since_last_observed",
    "preceding_observed_run_length",
    "preceding_missing_run_length",
}


@dataclass(frozen=True)
class ObservationProcessData:
    """Validated explicit denominator for an observation-process diagnostic.

    ``frame`` contains one row for every candidate/scheduled sample that could
    have been observed. The binary ``observed_column`` identifies retained gaze.
    Rows are stored in curve/time order after validation; no missing rows are
    created and no current missing gaze value is filled.
    """

    frame: pd.DataFrame
    curve_column: str
    time_column: str
    observed_column: str
    group_column: str | None
    candidate_predictors: tuple[str, ...]
    predictor_sources: Mapping[str, str]
    coordinate_columns: tuple[str, ...]
    time_unit: str = "unknown"
    coordinate_system: str = "unknown"
    provenance: Mapping[str, Any] = field(default_factory=dict)

    @property
    def n_candidates(self) -> int:
        return int(len(self.frame))

    @property
    def n_observed(self) -> int:
        return int(self.frame[self.observed_column].sum())

    @property
    def n_missing(self) -> int:
        return self.n_candidates - self.n_observed

    @property
    def observed_fraction(self) -> float:
        return float(self.n_observed / self.n_candidates)

    @property
    def curve_ids(self) -> tuple[str, ...]:
        return tuple(self.frame[self.curve_column].drop_duplicates().astype(str))


@dataclass(frozen=True)
class ObservationProcessDiagnosticResult:
    """Auditable descriptive diagnostics for an explicit observation process."""

    process: ObservationProcessData
    candidate_frame: pd.DataFrame
    global_summary: pd.DataFrame
    curve_summary: pd.DataFrame
    group_summary: pd.DataFrame
    time_summary: pd.DataFrame
    associations: pd.DataFrame
    profiles: pd.DataFrame
    failures: pd.DataFrame
    risk_set: str
    time_basis: str | None
    association_bins: int | tuple[float, ...] | None
    time_bins: int | tuple[float, ...] | None
    scope: str = _SCOPE
    provenance: Mapping[str, Any] = field(default_factory=dict)


def _require_columns(frame: pd.DataFrame, columns: Sequence[str]) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"frame is missing required column(s): {missing}")


def _validate_binary(series: pd.Series, *, name: str) -> np.ndarray:
    if series.isna().any():
        raise ValueError(f"{name} must not contain missing values")
    values = series.to_numpy()
    if values.dtype == bool:
        return values.astype(int)
    try:
        numeric = np.asarray(values, dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be binary 0/1 or boolean") from exc
    if not np.all(np.isfinite(numeric)) or not np.all(np.isin(numeric, [0.0, 1.0])):
        raise ValueError(f"{name} must be binary 0/1 or boolean")
    return numeric.astype(int)


def observation_process_data(
    frame: pd.DataFrame,
    *,
    curve_column: str,
    time_column: str,
    observed_column: str,
    group_column: str | None = None,
    candidate_predictors: Sequence[str] = (),
    predictor_sources: Mapping[str, str] | None = None,
    coordinate_columns: Sequence[str] = (),
    time_unit: str = "unknown",
    coordinate_system: str = "unknown",
    provenance: Mapping[str, Any] | None = None,
) -> ObservationProcessData:
    """Validate an explicit candidate-sample denominator.

    Candidate predictors must be available on every candidate row. Raw gaze
    coordinate columns, when supplied, must contain finite values on observed
    rows and must be missing on unobserved rows; complete externally supplied
    state variables belong in ``candidate_predictors`` instead.
    """

    if not isinstance(frame, pd.DataFrame):
        raise TypeError("frame must be a pandas DataFrame")
    if frame.empty:
        raise ValueError("frame must contain at least one candidate sample")
    predictors = tuple(dict.fromkeys(map(str, candidate_predictors)))
    coordinates = tuple(map(str, coordinate_columns))
    if len(coordinates) not in {0, 2}:
        raise ValueError("coordinate_columns must be empty or contain exactly two columns")

    required = [curve_column, time_column, observed_column, *predictors, *coordinates]
    if group_column is not None:
        required.append(group_column)
    _require_columns(frame, required)

    reserved = {curve_column, time_column, observed_column}
    if len(reserved) != 3:
        raise ValueError("curve_column, time_column, and observed_column must be distinct")
    if group_column is not None and group_column in reserved:
        raise ValueError("group_column must be distinct from core denominator columns")

    data = frame.copy(deep=True)
    if data[curve_column].isna().any():
        raise ValueError("curve identifiers must not be missing")
    data[curve_column] = data[curve_column].astype(str)
    if group_column is not None:
        if data[group_column].isna().any():
            raise ValueError("group identifiers must not be missing")
        data[group_column] = data[group_column].astype(str)

    try:
        candidate_time = pd.to_numeric(data[time_column], errors="raise").to_numpy(dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError("candidate times must be numeric") from exc
    if not np.all(np.isfinite(candidate_time)):
        raise ValueError("candidate times must be finite")
    data[time_column] = candidate_time
    data[observed_column] = _validate_binary(data[observed_column], name=observed_column)

    duplicates = data.duplicated([curve_column, time_column], keep=False)
    if duplicates.any():
        examples = data.loc[duplicates, [curve_column, time_column]].head(5).to_dict("records")
        raise ValueError(
            "candidate rows must be unique within curve/time; "
            f"duplicate examples: {examples}"
        )

    for curve_id, group in data.groupby(curve_column, sort=False):
        times = group[time_column].to_numpy(dtype=float)
        if times.size > 1 and not np.all(np.diff(times) > 0):
            raise ValueError(
                "candidate times must be strictly increasing in supplied row order "
                f"within curve {curve_id!r}"
            )

    source_map = dict(predictor_sources or {})
    unknown_sources = sorted(set(source_map) - set(predictors))
    if unknown_sources:
        raise ValueError(
            "predictor_sources contains names absent from candidate_predictors: "
            f"{unknown_sources}"
        )
    resolved_sources: dict[str, str] = {}
    for predictor in predictors:
        source = source_map.get(predictor, "candidate_time")
        if source not in _ALLOWED_SOURCES:
            raise ValueError(
                f"predictor source for {predictor!r} must be one of "
                f"{sorted(_ALLOWED_SOURCES)}"
            )
        if data[predictor].isna().any():
            raise ValueError(
                f"candidate-time predictor {predictor!r} is unavailable on some "
                "candidate rows; do not fill contemporaneous missing gaze implicitly"
            )
        resolved_sources[predictor] = source

    observed = data[observed_column].to_numpy(dtype=int).astype(bool)
    for coordinate in coordinates:
        numeric = pd.to_numeric(data[coordinate], errors="coerce").to_numpy(dtype=float)
        if np.any(~np.isfinite(numeric[observed])):
            raise ValueError(
                f"coordinate column {coordinate!r} must be finite on observed rows"
            )
        if np.any(np.isfinite(numeric[~observed])):
            raise ValueError(
                f"coordinate column {coordinate!r} contains values on unobserved rows; "
                "label complete external state as a candidate predictor instead"
            )
        data[coordinate] = numeric

    data = data.sort_values([curve_column, time_column], kind="stable").reset_index(drop=True)
    merged_provenance = dict(provenance or {})
    merged_provenance.update(
        {
            "denominator_source": "explicit_candidate_rows",
            "denominator_reconstructed_from_retained_timestamps": False,
            "nominal_sampling_rate_used_to_infer_missing_rows": False,
            "current_missing_gaze_imputed": False,
            "candidate_predictor_sources": dict(resolved_sources),
        }
    )
    return ObservationProcessData(
        frame=data,
        curve_column=str(curve_column),
        time_column=str(time_column),
        observed_column=str(observed_column),
        group_column=None if group_column is None else str(group_column),
        candidate_predictors=predictors,
        predictor_sources=resolved_sources,
        coordinate_columns=coordinates,
        time_unit=str(time_unit),
        coordinate_system=str(coordinate_system),
        provenance=merged_provenance,
    )


def _longest_run(values: np.ndarray, target: int) -> int:
    best = 0
    current = 0
    for value in values:
        if int(value) == target:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def _median_interval(times: np.ndarray) -> float:
    if times.size < 2:
        return np.nan
    return float(np.median(np.diff(times)))


def _summarize_curves(process: ObservationProcessData) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for curve_id, group in process.frame.groupby(process.curve_column, sort=False):
        observed = group[process.observed_column].to_numpy(dtype=int)
        times = group[process.time_column].to_numpy(dtype=float)
        retained_times = times[observed.astype(bool)]
        rows.append(
            {
                "curve_id": str(curve_id),
                "candidate_count": int(times.size),
                "observed_count": int(observed.sum()),
                "missing_count": int(times.size - observed.sum()),
                "observed_fraction": float(observed.mean()),
                "candidate_start": float(times[0]),
                "candidate_end": float(times[-1]),
                "observed_start": float(retained_times[0]) if retained_times.size else np.nan,
                "observed_end": float(retained_times[-1]) if retained_times.size else np.nan,
                "candidate_median_interval": _median_interval(times),
                "observed_median_interval": _median_interval(retained_times),
                "longest_observed_run": _longest_run(observed, 1),
                "longest_missing_run": _longest_run(observed, 0),
            }
        )
    return pd.DataFrame(rows)


def _summarize_groups(process: ObservationProcessData) -> pd.DataFrame:
    if process.group_column is None:
        return pd.DataFrame(
            columns=[
                "group_id",
                "curve_count",
                "candidate_count",
                "observed_count",
                "missing_count",
                "observed_fraction",
            ]
        )
    rows: list[dict[str, Any]] = []
    for group_id, group in process.frame.groupby(process.group_column, sort=False):
        observed = group[process.observed_column].to_numpy(dtype=int)
        rows.append(
            {
                "group_id": str(group_id),
                "curve_count": int(group[process.curve_column].nunique()),
                "candidate_count": int(len(group)),
                "observed_count": int(observed.sum()),
                "missing_count": int(len(group) - observed.sum()),
                "observed_fraction": float(observed.mean()),
            }
        )
    return pd.DataFrame(rows)


def _resolve_edges(
    values: np.ndarray,
    bins: int | Sequence[float] | None,
    *,
    name: str,
) -> tuple[float, ...] | None:
    if bins is None:
        return None
    if isinstance(bins, bool):
        raise TypeError(f"{name} must be an integer >= 2, edge sequence, or None")
    if isinstance(bins, int):
        if bins < 2:
            raise ValueError(f"{name} integer must be >= 2")
        lo = float(np.min(values))
        hi = float(np.max(values))
        if not hi > lo:
            raise ValueError(f"{name} cannot be constructed for constant values")
        return tuple(np.linspace(lo, hi, bins + 1))
    edges = np.asarray(tuple(bins), dtype=float)
    if edges.ndim != 1 or edges.size < 3 or not np.all(np.isfinite(edges)):
        raise ValueError(f"{name} edges must contain at least three finite values")
    if not np.all(np.diff(edges) > 0):
        raise ValueError(f"{name} edges must be strictly increasing")
    if edges[0] > np.min(values) or edges[-1] < np.max(values):
        raise ValueError(f"{name} edges must cover all evaluated values")
    return tuple(map(float, edges))


def _binned_summary(
    values: np.ndarray,
    observed: np.ndarray,
    edges: tuple[float, ...],
    *,
    predictor: str,
    source: str,
) -> pd.DataFrame:
    categories = pd.cut(
        values,
        bins=np.asarray(edges, dtype=float),
        include_lowest=True,
        right=True,
        duplicates="drop",
    )
    rows: list[dict[str, Any]] = []
    for category in categories.categories:
        mask = np.asarray(categories == category)
        if not np.any(mask):
            continue
        y = observed[mask]
        rows.append(
            {
                "predictor": predictor,
                "source": source,
                "profile_type": "numeric_bin",
                "level": str(category),
                "lower": float(category.left),
                "upper": float(category.right),
                "candidate_count": int(mask.sum()),
                "observed_count": int(y.sum()),
                "observed_fraction": float(y.mean()),
            }
        )
    return pd.DataFrame(rows)


def _categorical_profile(
    values: pd.Series,
    observed: np.ndarray,
    *,
    predictor: str,
    source: str,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    labels = values.astype(str).to_numpy()
    for level in pd.unique(labels):
        mask = labels == level
        y = observed[mask]
        rows.append(
            {
                "predictor": predictor,
                "source": source,
                "profile_type": "category",
                "level": str(level),
                "lower": np.nan,
                "upper": np.nan,
                "candidate_count": int(mask.sum()),
                "observed_count": int(y.sum()),
                "observed_fraction": float(y.mean()),
            }
        )
    return pd.DataFrame(rows)


def _numeric_association(
    values: np.ndarray,
    observed: np.ndarray,
    *,
    predictor: str,
    source: str,
) -> dict[str, Any]:
    if not np.all(np.isfinite(values)):
        return {
            "predictor": predictor,
            "source": source,
            "predictor_type": "numeric",
            "status_code": "predictor_nonfinite",
        }
    unique = np.unique(values)
    if unique.size < 2:
        return {
            "predictor": predictor,
            "source": source,
            "predictor_type": "numeric",
            "status_code": "predictor_constant",
            "n_rows": int(values.size),
            "n_unique": int(unique.size),
        }
    if np.unique(observed).size < 2:
        return {
            "predictor": predictor,
            "source": source,
            "predictor_type": "numeric",
            "status_code": "outcome_constant",
            "n_rows": int(values.size),
            "n_unique": int(unique.size),
        }

    observed_values = values[observed == 1]
    missing_values = values[observed == 0]
    pooled_sd = float(np.std(values, ddof=1))
    standardized_difference = (
        float((np.mean(observed_values) - np.mean(missing_values)) / pooled_sd)
        if pooled_sd > 0
        else np.nan
    )
    ranks = pd.Series(values).rank(method="average").to_numpy(dtype=float)
    rho = float(np.corrcoef(ranks, observed.astype(float))[0, 1])
    return {
        "predictor": predictor,
        "source": source,
        "predictor_type": "numeric",
        "status_code": "ok",
        "n_rows": int(values.size),
        "n_unique": int(unique.size),
        "observed_mean": float(np.mean(observed_values)),
        "missing_mean": float(np.mean(missing_values)),
        "standardized_mean_difference": standardized_difference,
        "spearman_rho": rho,
        "min_observed_fraction": np.nan,
        "max_observed_fraction": np.nan,
        "observed_fraction_range": np.nan,
    }


def _categorical_association(
    values: pd.Series,
    observed: np.ndarray,
    *,
    predictor: str,
    source: str,
) -> dict[str, Any]:
    labels = values.astype(str).to_numpy()
    unique = pd.unique(labels)
    if unique.size < 2:
        return {
            "predictor": predictor,
            "source": source,
            "predictor_type": "categorical",
            "status_code": "predictor_constant",
            "n_rows": int(labels.size),
            "n_unique": int(unique.size),
        }
    if np.unique(observed).size < 2:
        return {
            "predictor": predictor,
            "source": source,
            "predictor_type": "categorical",
            "status_code": "outcome_constant",
            "n_rows": int(labels.size),
            "n_unique": int(unique.size),
        }
    rates = []
    for level in unique:
        mask = labels == level
        rates.append(float(observed[mask].mean()))
    return {
        "predictor": predictor,
        "source": source,
        "predictor_type": "categorical",
        "status_code": "ok",
        "n_rows": int(labels.size),
        "n_unique": int(unique.size),
        "observed_mean": np.nan,
        "missing_mean": np.nan,
        "standardized_mean_difference": np.nan,
        "spearman_rho": np.nan,
        "min_observed_fraction": float(np.min(rates)),
        "max_observed_fraction": float(np.max(rates)),
        "observed_fraction_range": float(np.max(rates) - np.min(rates)),
    }


def _derive_history(
    process: ObservationProcessData,
    *,
    eccentricity_reference: tuple[float, float] | None,
) -> pd.DataFrame:
    data = process.frame.copy(deep=True)
    for column in _HISTORY_NAMES:
        data[column] = np.nan

    x_column = process.coordinate_columns[0] if process.coordinate_columns else None
    y_column = process.coordinate_columns[1] if process.coordinate_columns else None
    for _, index in data.groupby(process.curve_column, sort=False).groups.items():
        positions = list(index)
        last_observed_time: float | None = None
        last_observed_xy: tuple[float, float] | None = None
        previous_observed_xy: tuple[float, float] | None = None
        previous_observed_time: float | None = None
        observed_run = 0
        missing_run = 0
        for row_index in positions:
            row = data.loc[row_index]
            current_time = float(row[process.time_column])
            if last_observed_time is not None:
                data.at[row_index, "time_since_last_observed"] = current_time - last_observed_time
            data.at[row_index, "preceding_observed_run_length"] = float(observed_run)
            data.at[row_index, "preceding_missing_run_length"] = float(missing_run)

            if last_observed_xy is not None:
                data.at[row_index, "previous_observed_x"] = last_observed_xy[0]
                data.at[row_index, "previous_observed_y"] = last_observed_xy[1]
                if eccentricity_reference is not None:
                    data.at[row_index, "previous_observed_eccentricity"] = float(
                        np.hypot(
                            last_observed_xy[0] - eccentricity_reference[0],
                            last_observed_xy[1] - eccentricity_reference[1],
                        )
                    )
            if (
                last_observed_xy is not None
                and previous_observed_xy is not None
                and last_observed_time is not None
                and previous_observed_time is not None
                and last_observed_time > previous_observed_time
            ):
                data.at[row_index, "previous_observed_speed"] = float(
                    np.hypot(
                        last_observed_xy[0] - previous_observed_xy[0],
                        last_observed_xy[1] - previous_observed_xy[1],
                    )
                    / (last_observed_time - previous_observed_time)
                )

            if int(row[process.observed_column]) == 1:
                observed_run += 1
                missing_run = 0
                if x_column is not None and y_column is not None:
                    previous_observed_xy = last_observed_xy
                    previous_observed_time = last_observed_time
                    last_observed_xy = (float(row[x_column]), float(row[y_column]))
                last_observed_time = current_time
            else:
                missing_run += 1
                observed_run = 0
    return data


def _risk_mask(process: ObservationProcessData, frame: pd.DataFrame, risk_set: str) -> np.ndarray:
    if risk_set == "all_candidates":
        return np.ones(len(frame), dtype=bool)
    if risk_set != "after_observed":
        raise ValueError("risk_set must be 'all_candidates' or 'after_observed'")
    mask = np.zeros(len(frame), dtype=bool)
    for _, index in frame.groupby(process.curve_column, sort=False).groups.items():
        positions = list(index)
        for prior, current in zip(positions[:-1], positions[1:], strict=True):
            if int(frame.at[prior, process.observed_column]) == 1:
                mask[current] = True
    return mask


def _empty_failure_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=["item", "source", "status_code", "message"])


def diagnose_observation_process(
    process: ObservationProcessData,
    *,
    predictors: Sequence[str] | None = None,
    history_predictors: Sequence[str] = (),
    eccentricity_reference: tuple[float, float] | None = None,
    risk_set: str = "all_candidates",
    time_basis: str | None = "linear",
    time_bins: int | Sequence[float] | None = None,
    association_bins: int | Sequence[float] | None = 4,
) -> ObservationProcessDiagnosticResult:
    """Describe dependence and support in an explicit observation process.

    No iid sample-level standard errors or p-values are reported. Association
    summaries are descriptive and do not identify MAR/MNAR mechanisms.
    """

    if not isinstance(process, ObservationProcessData):
        raise TypeError("process must be an ObservationProcessData")
    if time_basis not in {None, "linear"}:
        raise ValueError("time_basis must be None or 'linear' in the A3 tranche")
    requested_predictors = (
        process.candidate_predictors
        if predictors is None
        else tuple(dict.fromkeys(map(str, predictors)))
    )
    unknown = sorted(set(requested_predictors) - set(process.candidate_predictors))
    if unknown:
        raise ValueError(
            "predictors must have been declared as complete candidate-time predictors: "
            f"{unknown}"
        )
    requested_history = tuple(dict.fromkeys(map(str, history_predictors)))
    unknown_history = sorted(set(requested_history) - _HISTORY_NAMES)
    if unknown_history:
        raise ValueError(f"unknown history predictor(s): {unknown_history}")

    if eccentricity_reference is not None:
        reference = np.asarray(eccentricity_reference, dtype=float)
        if reference.shape != (2,) or not np.all(np.isfinite(reference)):
            raise ValueError("eccentricity_reference must contain two finite coordinates")
        resolved_reference = (float(reference[0]), float(reference[1]))
    else:
        resolved_reference = None

    candidate_frame = _derive_history(
        process,
        eccentricity_reference=resolved_reference,
    )
    risk_mask = _risk_mask(process, candidate_frame, risk_set)
    evaluated = candidate_frame.loc[risk_mask].copy()
    if evaluated.empty:
        raise ValueError("selected risk_set contains no candidate rows")
    observed = evaluated[process.observed_column].to_numpy(dtype=int)

    curve_summary = _summarize_curves(process)
    group_summary = _summarize_groups(process)
    global_summary = pd.DataFrame(
        [
            {
                "candidate_count": process.n_candidates,
                "observed_count": process.n_observed,
                "missing_count": process.n_missing,
                "observed_fraction": process.observed_fraction,
                "missing_fraction": 1.0 - process.observed_fraction,
                "curve_count": len(process.curve_ids),
                "group_count": (
                    int(process.frame[process.group_column].nunique())
                    if process.group_column is not None
                    else np.nan
                ),
                "risk_set": risk_set,
                "risk_candidate_count": int(len(evaluated)),
                "risk_observed_count": int(observed.sum()),
                "risk_missing_count": int(len(evaluated) - observed.sum()),
            }
        ]
    )

    failures: list[dict[str, Any]] = []
    association_rows: list[dict[str, Any]] = []
    profile_frames: list[pd.DataFrame] = []

    if time_basis == "linear":
        time_values = evaluated[process.time_column].to_numpy(dtype=float)
        association_rows.append(
            _numeric_association(
                time_values,
                observed,
                predictor=process.time_column,
                source="candidate_time",
            )
        )
    resolved_time_edges = _resolve_edges(
        process.frame[process.time_column].to_numpy(dtype=float),
        time_bins,
        name="time_bins",
    )
    if resolved_time_edges is None:
        time_summary = pd.DataFrame(
            columns=[
                "predictor",
                "source",
                "profile_type",
                "level",
                "lower",
                "upper",
                "candidate_count",
                "observed_count",
                "observed_fraction",
            ]
        )
    else:
        time_summary = _binned_summary(
            process.frame[process.time_column].to_numpy(dtype=float),
            process.frame[process.observed_column].to_numpy(dtype=int),
            resolved_time_edges,
            predictor=process.time_column,
            source="candidate_time",
        )

    for predictor in requested_predictors:
        series = evaluated[predictor]
        source = process.predictor_sources[predictor]
        if is_numeric_dtype(series):
            values = pd.to_numeric(series, errors="coerce").to_numpy(dtype=float)
            association_rows.append(
                _numeric_association(
                    values,
                    observed,
                    predictor=predictor,
                    source=source,
                )
            )
            try:
                edges = _resolve_edges(values, association_bins, name="association_bins")
            except ValueError as exc:
                failures.append(
                    {
                        "item": predictor,
                        "source": source,
                        "status_code": "profile_unavailable",
                        "message": str(exc),
                    }
                )
                edges = None
            if edges is not None:
                profile_frames.append(
                    _binned_summary(
                        values,
                        observed,
                        edges,
                        predictor=predictor,
                        source=source,
                    )
                )
        else:
            association_rows.append(
                _categorical_association(
                    series,
                    observed,
                    predictor=predictor,
                    source=source,
                )
            )
            profile_frames.append(
                _categorical_profile(
                    series,
                    observed,
                    predictor=predictor,
                    source=source,
                )
            )

    history_requires_coordinates = {
        "previous_observed_x",
        "previous_observed_y",
        "previous_observed_speed",
        "previous_observed_eccentricity",
    }
    for predictor in requested_history:
        if predictor in history_requires_coordinates and not process.coordinate_columns:
            failures.append(
                {
                    "item": predictor,
                    "source": "history",
                    "status_code": "history_coordinates_unavailable",
                    "message": "raw observed coordinate columns were not supplied",
                }
            )
            continue
        if predictor == "previous_observed_eccentricity" and resolved_reference is None:
            failures.append(
                {
                    "item": predictor,
                    "source": "history",
                    "status_code": "reference_definition_required",
                    "message": "eccentricity_reference is required for this history predictor",
                }
            )
            continue
        values = evaluated[predictor].to_numpy(dtype=float)
        finite = np.isfinite(values)
        if not np.any(finite):
            failures.append(
                {
                    "item": predictor,
                    "source": "history",
                    "status_code": "history_unavailable",
                    "message": "no candidate rows have sufficient prior observed history",
                }
            )
            continue
        history_values = values[finite]
        history_observed = observed[finite]
        row = _numeric_association(
            history_values,
            history_observed,
            predictor=predictor,
            source="history",
        )
        row["n_excluded_insufficient_history"] = int((~finite).sum())
        association_rows.append(row)
        try:
            edges = _resolve_edges(
                history_values,
                association_bins,
                name="association_bins",
            )
        except ValueError as exc:
            failures.append(
                {
                    "item": predictor,
                    "source": "history",
                    "status_code": "profile_unavailable",
                    "message": str(exc),
                }
            )
            edges = None
        if edges is not None:
            profile_frames.append(
                _binned_summary(
                    history_values,
                    history_observed,
                    edges,
                    predictor=predictor,
                    source="history",
                )
            )

    associations = pd.DataFrame(association_rows)
    profiles = (
        pd.concat(profile_frames, ignore_index=True)
        if profile_frames
        else pd.DataFrame(
            columns=[
                "predictor",
                "source",
                "profile_type",
                "level",
                "lower",
                "upper",
                "candidate_count",
                "observed_count",
                "observed_fraction",
            ]
        )
    )
    failure_frame = pd.DataFrame(failures) if failures else _empty_failure_frame()

    provenance = {
        "scope": _SCOPE,
        "denominator_source": "explicit_candidate_rows",
        "time_basis": time_basis,
        "time_bins": None if resolved_time_edges is None else list(resolved_time_edges),
        "association_bins": (
            association_bins
            if isinstance(association_bins, int) or association_bins is None
            else list(map(float, association_bins))
        ),
        "risk_set": risk_set,
        "predictor_sources": dict(process.predictor_sources),
        "history_predictors": list(requested_history),
        "history_uses_past_information_only": True,
        "eccentricity_reference": (
            None if resolved_reference is None else list(resolved_reference)
        ),
        "iid_sample_level_inference_performed": False,
        "p_values_reported": False,
        "missing_mechanism_classification_performed": False,
        "inverse_probability_weighting_performed": False,
        "inverse_intensity_correction_performed": False,
        "current_missing_gaze_imputed": False,
        "sparse_estimator_modified": False,
    }
    return ObservationProcessDiagnosticResult(
        process=process,
        candidate_frame=candidate_frame,
        global_summary=global_summary,
        curve_summary=curve_summary,
        group_summary=group_summary,
        time_summary=time_summary,
        associations=associations,
        profiles=profiles,
        failures=failure_frame,
        risk_set=risk_set,
        time_basis=time_basis,
        association_bins=(
            association_bins
            if isinstance(association_bins, int) or association_bins is None
            else tuple(map(float, association_bins))
        ),
        time_bins=(
            time_bins
            if isinstance(time_bins, int) or time_bins is None
            else tuple(map(float, time_bins))
        ),
        provenance=provenance,
    )


def observation_process_frame(
    result: ObservationProcessDiagnosticResult,
    *,
    table: str = "associations",
) -> pd.DataFrame:
    """Return one audited diagnostic table as a defensive copy."""

    if not isinstance(result, ObservationProcessDiagnosticResult):
        raise TypeError("result must be an ObservationProcessDiagnosticResult")
    tables = {
        "global": result.global_summary,
        "curves": result.curve_summary,
        "groups": result.group_summary,
        "time": result.time_summary,
        "associations": result.associations,
        "profiles": result.profiles,
        "failures": result.failures,
        "candidates": result.candidate_frame,
    }
    if table not in tables:
        raise ValueError(f"table must be one of {sorted(tables)}")
    return tables[table].copy(deep=True)


def observation_process_reporting_text(
    result: ObservationProcessDiagnosticResult,
) -> str:
    """Return conservative manuscript-ready descriptive reporting text."""

    if not isinstance(result, ObservationProcessDiagnosticResult):
        raise TypeError("result must be an ObservationProcessDiagnosticResult")
    summary = result.global_summary.iloc[0]
    ok = (
        result.associations.loc[result.associations["status_code"] == "ok", "predictor"]
        .astype(str)
        .tolist()
        if not result.associations.empty and "status_code" in result.associations
        else []
    )
    failed = int(len(result.failures))
    group_phrase = (
        f", across {int(summary['group_count'])} declared groups"
        if np.isfinite(summary["group_count"])
        else ""
    )
    predictor_phrase = ", ".join(ok) if ok else "no estimable requested predictors"
    return (
        "Observation-process diagnostics used an explicit denominator of "
        f"{int(summary['candidate_count'])} candidate samples across "
        f"{int(summary['curve_count'])} curves{group_phrase}; "
        f"{int(summary['missing_count'])} samples "
        f"({100.0 * float(summary['missing_fraction']):.1f}%) were not retained. "
        f"Descriptive associations were estimable for {predictor_phrase}. "
        f"{failed} diagnostic item(s) were retained with explicit failure/status records. "
        "The analysis reports descriptive observation-process associations only: it "
        "does not provide iid sample-level inference, classify the process as MAR/MNAR, "
        "impute current missing gaze, or apply inverse-probability/intensity correction."
    )
