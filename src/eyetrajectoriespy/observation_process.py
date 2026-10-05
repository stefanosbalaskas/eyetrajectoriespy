"""Diagnostics for potentially informative sparse observation processes.

A3 requires an explicit candidate-sample denominator. It never reconstructs
missing rows from retained timestamps or nominal sampling rate, and it never
fills contemporaneous missing gaze. The qualified scope is descriptive only:
support, run structure, time dependence, candidate-time predictors, and
past-information history variables. No weighting/correction estimator is
implemented here.
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
    """Validated explicit denominator for observation-process diagnostics."""

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
    support_summary: pd.DataFrame
    associations: pd.DataFrame
    profiles: pd.DataFrame
    failures: pd.DataFrame
    risk_set: str
    time_basis: str | None
    association_bins: int | tuple[float, ...] | None
    time_bins: int | tuple[float, ...] | None
    low_support_threshold: float
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
    """Validate one explicit row per candidate/scheduled sample.

    Candidate predictors must be available on every candidate row. Raw gaze
    coordinates, when supplied, must be finite on retained rows and genuinely
    missing (NaN) on unretained rows. Complete external state belongs in
    ``candidate_predictors`` instead of being presented as recovered gaze.
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
        if np.any(~np.isnan(numeric[~observed])):
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
    best = current = 0
    for value in values:
        if int(value) == target:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def _median_interval(times: np.ndarray) -> float:
    return np.nan if times.size < 2 else float(np.median(np.diff(times)))


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
    columns = [
        "group_id",
        "curve_count",
        "candidate_count",
        "observed_count",
        "missing_count",
        "observed_fraction",
    ]
    if process.group_column is None:
        return pd.DataFrame(columns=columns)
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
    return pd.DataFrame(rows, columns=columns)


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


def _regional_support(
    process: ObservationProcessData,
    edges: tuple[float, ...] | None,
    *,
    low_support_threshold: float,
) -> pd.DataFrame:
    columns = [
        "scope",
        "scope_id",
        "time_bin",
        "lower",
        "upper",
        "candidate_count",
        "observed_count",
        "missing_count",
        "observed_fraction",
        "no_candidate_support",
        "zero_observed_support",
        "near_zero_observed_support",
    ]
    if edges is None:
        return pd.DataFrame(columns=columns)

    data = process.frame.copy()
    data["__time_bin"] = pd.cut(
        data[process.time_column],
        bins=np.asarray(edges, dtype=float),
        include_lowest=True,
        right=True,
    )
    categories = tuple(data["__time_bin"].cat.categories)
    scopes: list[tuple[str, str, pd.DataFrame]] = [
        ("curve", str(curve_id), group)
        for curve_id, group in data.groupby(process.curve_column, sort=False)
    ]
    if process.group_column is not None:
        scopes.extend(
            ("group", str(group_id), group)
            for group_id, group in data.groupby(process.group_column, sort=False)
        )

    rows: list[dict[str, Any]] = []
    for scope, scope_id, group in scopes:
        for category in categories:
            subset = group[group["__time_bin"] == category]
            candidate_count = int(len(subset))
            observed_count = int(subset[process.observed_column].sum()) if candidate_count else 0
            fraction = observed_count / candidate_count if candidate_count else np.nan
            rows.append(
                {
                    "scope": scope,
                    "scope_id": scope_id,
                    "time_bin": str(category),
                    "lower": float(category.left),
                    "upper": float(category.right),
                    "candidate_count": candidate_count,
                    "observed_count": observed_count,
                    "missing_count": candidate_count - observed_count,
                    "observed_fraction": float(fraction) if candidate_count else np.nan,
                    "no_candidate_support": candidate_count == 0,
                    "zero_observed_support": candidate_count > 0 and observed_count == 0,
                    "near_zero_observed_support": (
                        candidate_count > 0 and fraction < low_support_threshold
                    ),
                }
            )
    return pd.DataFrame(rows, columns=columns)


def _categorical_profile(
    values: pd.Series,
    observed: np.ndarray,
    *,
    predictor: str,
    source: str,
) -> pd.DataFrame:
    labels = values.astype(str).to_numpy()
    rows = []
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
    base = {"predictor": predictor, "source": source, "predictor_type": "numeric"}
    if not np.all(np.isfinite(values)):
        return {**base, "status_code": "predictor_nonfinite"}
    unique = np.unique(values)
    if unique.size < 2:
        return {
            **base,
            "status_code": "predictor_constant",
            "n_rows": int(values.size),
            "n_unique": int(unique.size),
        }
    if np.unique(observed).size < 2:
        return {
            **base,
            "status_code": "outcome_constant",
            "n_rows": int(values.size),
            "n_unique": int(unique.size),
        }

    observed_values = values[observed == 1]
    missing_values = values[observed == 0]
    n_observed = observed_values.size
    n_missing = missing_values.size
    pooled_variance = np.nan
    if n_observed > 1 and n_missing > 1 and n_observed + n_missing > 2:
        pooled_variance = (
            (n_observed - 1) * np.var(observed_values, ddof=1)
            + (n_missing - 1) * np.var(missing_values, ddof=1)
        ) / (n_observed + n_missing - 2)
    pooled_sd = float(np.sqrt(pooled_variance)) if np.isfinite(pooled_variance) else np.nan
    standardized_difference = (
        float((np.mean(observed_values) - np.mean(missing_values)) / pooled_sd)
        if np.isfinite(pooled_sd) and pooled_sd > 0
        else np.nan
    )
    ranks = pd.Series(values).rank(method="average").to_numpy(dtype=float)
    rho = float(np.corrcoef(ranks, observed.astype(float))[0, 1])
    return {
        **base,
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
    base = {"predictor": predictor, "source": source, "predictor_type": "categorical"}
    if unique.size < 2:
        return {
            **base,
            "status_code": "predictor_constant",
            "n_rows": int(labels.size),
            "n_unique": int(unique.size),
        }
    if np.unique(observed).size < 2:
        return {
            **base,
            "status_code": "outcome_constant",
            "n_rows": int(labels.size),
            "n_unique": int(unique.size),
        }
    rates = [float(observed[labels == level].mean()) for level in unique]
    return {
        **base,
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
        last_time: float | None = None
        last_xy: tuple[float, float] | None = None
        previous_xy: tuple[float, float] | None = None
        previous_time: float | None = None
        observed_run = missing_run = 0
        for row_index in list(index):
            row = data.loc[row_index]
            current_time = float(row[process.time_column])
            if last_time is not None:
                data.at[row_index, "time_since_last_observed"] = current_time - last_time
            data.at[row_index, "preceding_observed_run_length"] = float(observed_run)
            data.at[row_index, "preceding_missing_run_length"] = float(missing_run)

            if last_xy is not None:
                data.at[row_index, "previous_observed_x"] = last_xy[0]
                data.at[row_index, "previous_observed_y"] = last_xy[1]
                if eccentricity_reference is not None:
                    data.at[row_index, "previous_observed_eccentricity"] = float(
                        np.hypot(
                            last_xy[0] - eccentricity_reference[0],
                            last_xy[1] - eccentricity_reference[1],
                        )
                    )
            if (
                last_xy is not None
                and previous_xy is not None
                and last_time is not None
                and previous_time is not None
                and last_time > previous_time
            ):
                data.at[row_index, "previous_observed_speed"] = float(
                    np.hypot(last_xy[0] - previous_xy[0], last_xy[1] - previous_xy[1])
                    / (last_time - previous_time)
                )

            if int(row[process.observed_column]) == 1:
                observed_run += 1
                missing_run = 0
                if x_column is not None and y_column is not None:
                    previous_xy, previous_time = last_xy, last_time
                    last_xy = (float(row[x_column]), float(row[y_column]))
                last_time = current_time
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
    low_support_threshold: float = 0.10,
) -> ObservationProcessDiagnosticResult:
    """Describe dependence and support in an explicit observation process.

    No iid sample-level standard errors or p-values are reported. Association
    summaries are descriptive and do not identify MAR/MNAR mechanisms.
    """

    if not isinstance(process, ObservationProcessData):
        raise TypeError("process must be an ObservationProcessData")
    if time_basis not in {None, "linear"}:
        raise ValueError("time_basis must be None or 'linear' in the A3 tranche")
    low_support_threshold = float(low_support_threshold)
    if not np.isfinite(low_support_threshold) or not 0.0 <= low_support_threshold <= 1.0:
        raise ValueError("low_support_threshold must be finite and within [0, 1]")

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

    candidate_frame = _derive_history(process, eccentricity_reference=resolved_reference)
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

    resolved_time_edges = _resolve_edges(
        process.frame[process.time_column].to_numpy(dtype=float),
        time_bins,
        name="time_bins",
    )
    support_summary = _regional_support(
        process,
        resolved_time_edges,
        low_support_threshold=low_support_threshold,
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
            evaluated[process.time_column].to_numpy(dtype=float),
            observed,
            resolved_time_edges,
            predictor=process.time_column,
            source="candidate_time",
        )

    failures: list[dict[str, Any]] = []
    association_rows: list[dict[str, Any]] = []
    profile_frames: list[pd.DataFrame] = []
    if time_basis == "linear":
        association_rows.append(
            _numeric_association(
                evaluated[process.time_column].to_numpy(dtype=float),
                observed,
                predictor=process.time_column,
                source="candidate_time",
            )
        )

    for predictor in requested_predictors:
        series = evaluated[predictor]
        source = process.predictor_sources[predictor]
        if is_numeric_dtype(series):
            values = pd.to_numeric(series, errors="coerce").to_numpy(dtype=float)
            association_rows.append(
                _numeric_association(values, observed, predictor=predictor, source=source)
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
                _categorical_association(series, observed, predictor=predictor, source=source)
            )
            profile_frames.append(
                _categorical_profile(series, observed, predictor=predictor, source=source)
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
        "low_support_threshold": low_support_threshold,
        "time_summary_uses_selected_risk_set": True,
        "support_summary_uses_full_candidate_denominator": True,
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
        support_summary=support_summary,
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
        low_support_threshold=low_support_threshold,
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
        "support": result.support_summary,
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
