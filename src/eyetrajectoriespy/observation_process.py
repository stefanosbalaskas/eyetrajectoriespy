"""Diagnostics for candidate-sample observation processes in eye tracking.

This module is deliberately diagnostic. It requires an explicit candidate-sample
denominator and never reconstructs missing rows from retained irregular gaze,
imputes contemporaneous gaze at missing rows, or applies inverse-probability /
inverse-intensity corrections to downstream estimators.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit


_ALLOWED_PREDICTOR_KINDS = {"candidate_time", "externally_supplied"}
_ALLOWED_HISTORY_PREDICTORS = {
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
    """Explicit candidate-sample denominator for observation-process diagnostics.

    Every row represents one sample that was scheduled/candidate for observation.
    ``observed_column`` records whether gaze was retained at that row. The object
    does not infer candidate rows from gaps in an observed-only trajectory.
    """

    frame: pd.DataFrame
    curve_column: str
    time_column: str
    observed_column: str
    group_column: str | None = None
    predictor_kinds: Mapping[str, str] = field(default_factory=dict)
    provenance: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        frame = self.frame.copy()
        required = {self.curve_column, self.time_column, self.observed_column}
        if self.group_column is not None:
            required.add(self.group_column)
        missing = sorted(required.difference(frame.columns))
        if missing:
            raise ValueError(f"observation-process frame is missing columns: {missing}")
        if frame.empty:
            raise ValueError("observation-process frame must contain at least one candidate row")

        if frame[self.curve_column].isna().any():
            raise ValueError("curve identifier contains missing values")
        curve_ids = frame[self.curve_column].astype(str)
        if (curve_ids.str.len() == 0).any():
            raise ValueError("curve identifier must not contain empty strings")
        frame[self.curve_column] = curve_ids

        time = pd.to_numeric(frame[self.time_column], errors="coerce").to_numpy(dtype=float)
        if not np.all(np.isfinite(time)):
            raise ValueError("candidate times must be finite numeric values")
        frame[self.time_column] = time

        observed = frame[self.observed_column]
        if pd.api.types.is_bool_dtype(observed):
            observed_bool = observed.to_numpy(dtype=bool)
        else:
            numeric = pd.to_numeric(observed, errors="coerce").to_numpy(dtype=float)
            if not np.all(np.isfinite(numeric)) or not np.all(np.isin(numeric, [0.0, 1.0])):
                raise ValueError("observed indicator must contain only bool/0/1 values")
            observed_bool = numeric.astype(bool)
        frame[self.observed_column] = observed_bool

        duplicated = frame.duplicated([self.curve_column, self.time_column], keep=False)
        if duplicated.any():
            examples = (
                frame.loc[duplicated, [self.curve_column, self.time_column]]
                .head(5)
                .to_dict(orient="records")
            )
            raise ValueError(
                "candidate rows must be unique by curve and time; "
                f"examples={examples}"
            )

        for curve_id, subset in frame.groupby(self.curve_column, sort=False):
            times = subset[self.time_column].to_numpy(dtype=float)
            if times.size < 1 or (times.size > 1 and not np.all(np.diff(times) > 0)):
                raise ValueError(
                    "candidate times must be strictly increasing within each curve "
                    f"in supplied row order; curve={curve_id!r}"
                )

        if self.group_column is not None:
            if frame[self.group_column].isna().any():
                raise ValueError("group identifier contains missing values")
            frame[self.group_column] = frame[self.group_column].astype(str)
            group_counts = frame.groupby(self.curve_column, sort=False)[self.group_column].nunique()
            if (group_counts != 1).any():
                bad = group_counts[group_counts != 1].index.tolist()[:5]
                raise ValueError(
                    "group identifier must be constant within each curve; "
                    f"curves={bad}"
                )

        predictor_kinds = dict(self.predictor_kinds)
        for column, kind in predictor_kinds.items():
            if column not in frame.columns:
                raise ValueError(f"predictor column {column!r} is not present in frame")
            if kind not in _ALLOWED_PREDICTOR_KINDS:
                raise ValueError(
                    "predictor kind must be 'candidate_time' or 'externally_supplied'; "
                    f"got {kind!r} for {column!r}"
                )
            values = pd.to_numeric(frame[column], errors="coerce").to_numpy(dtype=float)
            if not np.all(np.isfinite(values)):
                raise ValueError(
                    f"candidate-time predictor {column!r} must be finite on every "
                    "candidate row; missing-row imputation is not performed"
                )
            frame[column] = values

        object.__setattr__(self, "frame", frame.reset_index(drop=True))
        object.__setattr__(self, "predictor_kinds", predictor_kinds)
        object.__setattr__(self, "provenance", dict(self.provenance))

    @property
    def n_candidates(self) -> int:
        return int(len(self.frame))

    @property
    def n_curves(self) -> int:
        return int(self.frame[self.curve_column].nunique())


@dataclass(frozen=True)
class ObservationProcessDiagnosticsResult:
    """Auditable descriptive diagnostics for an explicit observation process."""

    overall_summary: pd.DataFrame
    curve_summary: pd.DataFrame
    group_summary: pd.DataFrame | None
    time_summary: pd.DataFrame
    predictor_summary: pd.DataFrame
    history_frame: pd.DataFrame | None
    denominator_rows: int
    observed_rows: int
    missing_rows: int
    missing_fraction: float
    status_code: str
    provenance: Mapping[str, Any] = field(default_factory=dict)


def observation_process_data(
    frame: pd.DataFrame,
    *,
    curve_column: str,
    time_column: str,
    observed_column: str,
    group_column: str | None = None,
    predictor_kinds: Mapping[str, str] | None = None,
    provenance: Mapping[str, Any] | None = None,
) -> ObservationProcessData:
    """Construct and validate an explicit candidate-sample denominator."""

    if not isinstance(frame, pd.DataFrame):
        raise TypeError("frame must be a pandas DataFrame")
    return ObservationProcessData(
        frame=frame,
        curve_column=curve_column,
        time_column=time_column,
        observed_column=observed_column,
        group_column=group_column,
        predictor_kinds={} if predictor_kinds is None else predictor_kinds,
        provenance={} if provenance is None else provenance,
    )


def _longest_run(values: np.ndarray, *, target: bool) -> int:
    longest = 0
    current = 0
    for value in np.asarray(values, dtype=bool):
        if bool(value) is target:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return int(longest)


def _interval_summary(times: np.ndarray) -> tuple[float, float, float]:
    times = np.asarray(times, dtype=float)
    if times.size < 2:
        return np.nan, np.nan, np.nan
    delta = np.diff(times)
    return float(np.min(delta)), float(np.median(delta)), float(np.max(delta))


def _curve_summary(process: ObservationProcessData) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for curve_id, subset in process.frame.groupby(process.curve_column, sort=False):
        candidate = subset[process.time_column].to_numpy(dtype=float)
        observed_mask = subset[process.observed_column].to_numpy(dtype=bool)
        observed_time = candidate[observed_mask]
        cmin, cmed, cmax = _interval_summary(candidate)
        omin, omed, omax = _interval_summary(observed_time)
        rows.append(
            {
                process.curve_column: str(curve_id),
                "n_candidates": int(len(subset)),
                "n_observed": int(np.count_nonzero(observed_mask)),
                "n_missing": int(np.count_nonzero(~observed_mask)),
                "observed_fraction": float(np.mean(observed_mask)),
                "candidate_start": float(np.min(candidate)),
                "candidate_end": float(np.max(candidate)),
                "observed_start": (
                    np.nan if observed_time.size == 0 else float(np.min(observed_time))
                ),
                "observed_end": (
                    np.nan if observed_time.size == 0 else float(np.max(observed_time))
                ),
                "candidate_dt_min": cmin,
                "candidate_dt_median": cmed,
                "candidate_dt_max": cmax,
                "observed_dt_min": omin,
                "observed_dt_median": omed,
                "observed_dt_max": omax,
                "longest_observed_run": _longest_run(observed_mask, target=True),
                "longest_missing_run": _longest_run(observed_mask, target=False),
            }
        )
    return pd.DataFrame(rows)


def _group_summary(process: ObservationProcessData) -> pd.DataFrame | None:
    if process.group_column is None:
        return None
    rows: list[dict[str, Any]] = []
    for group_id, subset in process.frame.groupby(process.group_column, sort=False):
        candidate = subset[process.time_column].to_numpy(dtype=float)
        observed_mask = subset[process.observed_column].to_numpy(dtype=bool)
        observed_time = candidate[observed_mask]
        rows.append(
            {
                process.group_column: str(group_id),
                "n_curves": int(subset[process.curve_column].nunique()),
                "n_candidates": int(len(subset)),
                "n_observed": int(np.count_nonzero(observed_mask)),
                "n_missing": int(np.count_nonzero(~observed_mask)),
                "observed_fraction": float(np.mean(observed_mask)),
                "candidate_time_min": float(np.min(candidate)),
                "candidate_time_max": float(np.max(candidate)),
                "observed_time_min": (
                    np.nan if observed_time.size == 0 else float(np.min(observed_time))
                ),
                "observed_time_max": (
                    np.nan if observed_time.size == 0 else float(np.max(observed_time))
                ),
            }
        )
    return pd.DataFrame(rows)


def _time_summary(
    process: ObservationProcessData,
    *,
    time_bins: int | Sequence[float],
) -> tuple[pd.DataFrame, list[float]]:
    values = process.frame[process.time_column].to_numpy(dtype=float)
    if isinstance(time_bins, bool):
        raise TypeError("time_bins must be an integer >= 2 or explicit edges")
    if isinstance(time_bins, (int, np.integer)):
        n_bins = int(time_bins)
        if n_bins < 2:
            raise ValueError("time_bins must be at least 2")
        start = float(np.min(values))
        end = float(np.max(values))
        if not end > start:
            raise ValueError("candidate time has no variation")
        edges = np.linspace(start, end, n_bins + 1)
    else:
        edges = np.asarray(tuple(time_bins), dtype=float)
        if (
            edges.ndim != 1
            or edges.size < 3
            or not np.all(np.isfinite(edges))
            or not np.all(np.diff(edges) > 0)
        ):
            raise ValueError("time-bin edges must be finite and strictly increasing")
        if values.min() < edges[0] or values.max() > edges[-1]:
            raise ValueError("explicit time-bin edges must cover every candidate time")

    bin_index = np.searchsorted(edges, values, side="right") - 1
    bin_index[values == edges[-1]] = len(edges) - 2
    observed = process.frame[process.observed_column].to_numpy(dtype=bool)
    rows: list[dict[str, Any]] = []
    for index in range(len(edges) - 1):
        mask = bin_index == index
        n = int(np.count_nonzero(mask))
        n_observed = int(np.count_nonzero(observed[mask]))
        rows.append(
            {
                "time_bin": int(index),
                "time_start": float(edges[index]),
                "time_end": float(edges[index + 1]),
                "n_candidates": n,
                "n_observed": n_observed,
                "n_missing": int(n - n_observed),
                "observed_fraction": np.nan if n == 0 else float(n_observed / n),
                "n_curves": int(
                    process.frame.loc[mask, process.curve_column].nunique()
                ),
            }
        )
    return pd.DataFrame(rows), edges.tolist()


def observation_process_history_frame(
    process: ObservationProcessData,
    *,
    x_column: str | None = None,
    y_column: str | None = None,
    reference_center: tuple[float, float] | None = None,
) -> pd.DataFrame:
    """Derive predictors using only information available before each candidate row.

    Current-row gaze coordinates are used only after the history values for that
    row have been recorded. Missing-row coordinate values, even if present in the
    input frame, never update history state.
    """

    if not isinstance(process, ObservationProcessData):
        raise TypeError("process must be an ObservationProcessData")
    if (x_column is None) != (y_column is None):
        raise ValueError("x_column and y_column must be supplied together")
    if x_column is not None:
        for column in (x_column, y_column):
            if column not in process.frame.columns:
                raise ValueError(f"coordinate column {column!r} is not present")
        if reference_center is not None:
            center = np.asarray(reference_center, dtype=float)
            if center.shape != (2,) or not np.all(np.isfinite(center)):
                raise ValueError("reference_center must contain two finite values")
        else:
            center = None
    else:
        if reference_center is not None:
            raise ValueError("reference_center requires x_column and y_column")
        center = None

    rows: list[dict[str, Any]] = []
    for curve_id, subset in process.frame.groupby(process.curve_column, sort=False):
        last_time: float | None = None
        last_xy: np.ndarray | None = None
        previous_observed_time: float | None = None
        previous_observed_xy: np.ndarray | None = None
        last_speed = np.nan
        observed_run = 0
        missing_run = 0

        for row_index, row in subset.iterrows():
            time = float(row[process.time_column])
            observed = bool(row[process.observed_column])
            history_row: dict[str, Any] = {
                "row_index": int(row_index),
                process.curve_column: str(curve_id),
                process.time_column: time,
                process.observed_column: observed,
                "time_since_last_observed": (
                    np.nan if last_time is None else float(time - last_time)
                ),
                "preceding_observed_run_length": int(observed_run),
                "preceding_missing_run_length": int(missing_run),
                "previous_observed_speed": float(last_speed),
            }
            if process.group_column is not None:
                history_row[process.group_column] = str(row[process.group_column])

            if x_column is not None:
                history_row["previous_observed_x"] = (
                    np.nan if last_xy is None else float(last_xy[0])
                )
                history_row["previous_observed_y"] = (
                    np.nan if last_xy is None else float(last_xy[1])
                )
                history_row["previous_observed_eccentricity"] = (
                    np.nan
                    if last_xy is None or center is None
                    else float(np.linalg.norm(last_xy - center))
                )

            rows.append(history_row)

            if observed:
                if x_column is not None:
                    xy = np.asarray([row[x_column], row[y_column]], dtype=float)
                    if not np.all(np.isfinite(xy)):
                        raise ValueError(
                            "coordinate columns must be finite on observed rows; "
                            f"curve={curve_id!r}, time={time:g}"
                        )
                    if previous_observed_time is not None and previous_observed_xy is not None:
                        dt = time - previous_observed_time
                        if dt <= 0:
                            raise ValueError("observed coordinate times must be increasing")
                        last_speed = float(np.linalg.norm(xy - previous_observed_xy) / dt)
                    previous_observed_time = time
                    previous_observed_xy = xy.copy()
                    last_xy = xy.copy()
                last_time = time
                observed_run += 1
                missing_run = 0
            else:
                missing_run += 1
                observed_run = 0

    history = pd.DataFrame(rows).sort_values("row_index", kind="stable").reset_index(drop=True)
    return history


def _complete_separation(x: np.ndarray, y: np.ndarray) -> bool:
    x0 = x[y == 0]
    x1 = x[y == 1]
    if x0.size == 0 or x1.size == 0:
        return False
    return bool(np.max(x0) <= np.min(x1) or np.max(x1) <= np.min(x0))


def _descriptive_logistic(
    x: np.ndarray,
    y: np.ndarray,
) -> tuple[str, dict[str, float | str | None]]:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if x.ndim != 1 or y.ndim != 1 or x.shape != y.shape:
        raise ValueError("predictor and outcome must be one-dimensional with equal length")
    if x.size < 3:
        return "insufficient_support", {}
    if not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)):
        raise ValueError("eligible diagnostic rows must be finite")
    if np.unique(y).size < 2:
        return "outcome_constant", {}
    mean = float(np.mean(x))
    sd = float(np.std(x, ddof=0))
    if not np.isfinite(sd) or sd <= 0:
        return "predictor_constant", {}
    z = (x - mean) / sd
    if _complete_separation(z, y.astype(int)):
        return "complete_separation", {"predictor_mean": mean, "predictor_sd": sd}

    design = np.column_stack([np.ones(z.size), z])

    def objective(beta: np.ndarray) -> tuple[float, np.ndarray]:
        eta = design @ beta
        probability = expit(eta)
        tiny = np.finfo(float).eps
        probability = np.clip(probability, tiny, 1.0 - tiny)
        value = -float(np.sum(y * np.log(probability) + (1.0 - y) * np.log(1.0 - probability)))
        gradient = design.T @ (probability - y)
        return value, gradient

    fit = minimize(
        lambda beta: objective(beta)[0],
        x0=np.zeros(2, dtype=float),
        jac=lambda beta: objective(beta)[1],
        method="BFGS",
        options={"gtol": 1e-8, "maxiter": 500},
    )
    if not fit.success or not np.all(np.isfinite(fit.x)):
        return "fit_failure", {
            "predictor_mean": mean,
            "predictor_sd": sd,
            "failure_message": str(fit.message),
        }
    intercept, slope = map(float, fit.x)
    if abs(slope) > 25:
        return "near_separation", {
            "predictor_mean": mean,
            "predictor_sd": sd,
            "standardized_coefficient": slope,
        }
    return "ok", {
        "predictor_mean": mean,
        "predictor_sd": sd,
        "intercept": intercept,
        "standardized_coefficient": slope,
        "odds_ratio_per_sd": float(np.exp(slope)),
        "probability_at_minus_1sd": float(expit(intercept - slope)),
        "probability_at_mean": float(expit(intercept)),
        "probability_at_plus_1sd": float(expit(intercept + slope)),
    }


def _predictor_diagnostic_row(
    name: str,
    kind: str,
    values: np.ndarray,
    observed: np.ndarray,
    *,
    n_total: int,
) -> dict[str, Any]:
    values = np.asarray(values, dtype=float)
    observed = np.asarray(observed, dtype=bool)
    eligible = np.isfinite(values)
    n_eligible = int(np.count_nonzero(eligible))
    row: dict[str, Any] = {
        "predictor": name,
        "predictor_kind": kind,
        "n_total_candidates": int(n_total),
        "n_eligible": n_eligible,
        "n_excluded": int(n_total - n_eligible),
        "observed_fraction_eligible": (
            np.nan if n_eligible == 0 else float(np.mean(observed[eligible]))
        ),
        "status_code": None,
        "failure_message": None,
        "predictor_mean": np.nan,
        "predictor_sd": np.nan,
        "intercept": np.nan,
        "standardized_coefficient": np.nan,
        "odds_ratio_per_sd": np.nan,
        "probability_at_minus_1sd": np.nan,
        "probability_at_mean": np.nan,
        "probability_at_plus_1sd": np.nan,
    }
    if n_eligible == 0:
        row["status_code"] = "insufficient_support"
        return row
    status, details = _descriptive_logistic(values[eligible], observed[eligible].astype(float))
    row["status_code"] = status
    for key, value in details.items():
        if key in row:
            row[key] = value
        elif key == "failure_message":
            row["failure_message"] = value
    return row


def diagnose_observation_process(
    process: ObservationProcessData,
    *,
    time_bins: int | Sequence[float] = 10,
    predictors: Sequence[str] = (),
    include_linear_time_association: bool = True,
    history_predictors: Sequence[str] = (),
    x_column: str | None = None,
    y_column: str | None = None,
    reference_center: tuple[float, float] | None = None,
) -> ObservationProcessDiagnosticsResult:
    """Compute descriptive diagnostics for an explicit observation denominator.

    No iid standard errors or p-values are reported. Predictor associations are
    univariate descriptive logistic coefficients on one-SD standardized numeric
    predictors. Failed/unsupported predictors remain in ``predictor_summary``.
    """

    if not isinstance(process, ObservationProcessData):
        raise TypeError("process must be an ObservationProcessData")
    frame = process.frame
    observed = frame[process.observed_column].to_numpy(dtype=bool)
    n_candidates = int(len(frame))
    n_observed = int(np.count_nonzero(observed))
    n_missing = int(n_candidates - n_observed)
    missing_fraction = float(n_missing / n_candidates)

    curve_summary = _curve_summary(process)
    group_summary = _group_summary(process)
    time_summary, resolved_edges = _time_summary(process, time_bins=time_bins)
    overall_summary = pd.DataFrame(
        [
            {
                "n_candidates": n_candidates,
                "n_curves": int(process.n_curves),
                "n_groups": (
                    np.nan
                    if process.group_column is None
                    else int(frame[process.group_column].nunique())
                ),
                "n_observed": n_observed,
                "n_missing": n_missing,
                "observed_fraction": float(n_observed / n_candidates),
                "missing_fraction": missing_fraction,
                "candidate_time_start": float(frame[process.time_column].min()),
                "candidate_time_end": float(frame[process.time_column].max()),
            }
        ]
    )

    requested_predictors = tuple(dict.fromkeys(str(value) for value in predictors))
    unknown = [name for name in requested_predictors if name not in process.predictor_kinds]
    if unknown:
        raise ValueError(
            "predictors must be declared in process.predictor_kinds; "
            f"unknown={unknown}"
        )

    requested_history = tuple(dict.fromkeys(str(value) for value in history_predictors))
    invalid_history = sorted(set(requested_history).difference(_ALLOWED_HISTORY_PREDICTORS))
    if invalid_history:
        raise ValueError(f"unknown history predictors: {invalid_history}")
    if "previous_observed_eccentricity" in requested_history and reference_center is None:
        raise ValueError(
            "previous_observed_eccentricity requires an explicit reference_center"
        )
    coordinate_history_requested = bool(
        set(requested_history)
        & {
            "previous_observed_x",
            "previous_observed_y",
            "previous_observed_eccentricity",
            "previous_observed_speed",
        }
    )
    if coordinate_history_requested and (x_column is None or y_column is None):
        raise ValueError(
            "coordinate-based history predictors require x_column and y_column"
        )

    history_frame: pd.DataFrame | None = None
    if requested_history:
        history_frame = observation_process_history_frame(
            process,
            x_column=x_column,
            y_column=y_column,
            reference_center=reference_center,
        )

    predictor_rows: list[dict[str, Any]] = []
    included_names: set[str] = set()
    if include_linear_time_association:
        predictor_rows.append(
            _predictor_diagnostic_row(
                process.time_column,
                "candidate_time",
                frame[process.time_column].to_numpy(dtype=float),
                observed,
                n_total=n_candidates,
            )
        )
        included_names.add(process.time_column)
    for name in requested_predictors:
        if name in included_names:
            continue
        predictor_rows.append(
            _predictor_diagnostic_row(
                name,
                process.predictor_kinds[name],
                frame[name].to_numpy(dtype=float),
                observed,
                n_total=n_candidates,
            )
        )
        included_names.add(name)
    if history_frame is not None:
        for name in requested_history:
            predictor_rows.append(
                _predictor_diagnostic_row(
                    name,
                    "history_derived",
                    history_frame[name].to_numpy(dtype=float),
                    observed,
                    n_total=n_candidates,
                )
            )

    predictor_summary = pd.DataFrame(predictor_rows)
    if predictor_summary.empty:
        predictor_summary = pd.DataFrame(
            columns=[
                "predictor",
                "predictor_kind",
                "n_total_candidates",
                "n_eligible",
                "n_excluded",
                "observed_fraction_eligible",
                "status_code",
            ]
        )

    status_code = "ok"
    if n_observed == 0:
        status_code = "all_missing"
    elif n_missing == 0:
        status_code = "all_observed"

    provenance = {
        "method": "descriptive_observation_process_diagnostics",
        "denominator_required": True,
        "denominator_source": "explicit_candidate_sample_rows",
        "candidate_rows_inferred_from_observed_gaps": False,
        "missing_gaze_imputation_performed": False,
        "inverse_probability_weighting_performed": False,
        "inverse_intensity_weighting_performed": False,
        "correction_estimator_performed": False,
        "association_model": "univariate_unpenalized_logistic_descriptive_only",
        "iid_standard_errors_reported": False,
        "p_values_reported": False,
        "causal_interpretation_supported": False,
        "mar_mnar_classification_supported": False,
        "absence_of_association_proves_noninformative_missingness": False,
        "time_bin_edges": resolved_edges,
        "curve_column": process.curve_column,
        "time_column": process.time_column,
        "observed_column": process.observed_column,
        "group_column": process.group_column,
        "group_summary_contains_sequence_run_metrics": False,
        "predictor_kinds": dict(process.predictor_kinds),
        "requested_predictors": list(requested_predictors),
        "requested_history_predictors": list(requested_history),
        "history_uses_past_information_only": True,
        "coordinate_columns": (
            None if x_column is None else [str(x_column), str(y_column)]
        ),
        "reference_center": (
            None if reference_center is None else list(map(float, reference_center))
        ),
        "input_provenance": dict(process.provenance),
    }

    return ObservationProcessDiagnosticsResult(
        overall_summary=overall_summary,
        curve_summary=curve_summary,
        group_summary=group_summary,
        time_summary=time_summary,
        predictor_summary=predictor_summary,
        history_frame=history_frame,
        denominator_rows=n_candidates,
        observed_rows=n_observed,
        missing_rows=n_missing,
        missing_fraction=missing_fraction,
        status_code=status_code,
        provenance=provenance,
    )


def observation_process_reporting_text(
    result: ObservationProcessDiagnosticsResult,
) -> str:
    """Return conservative manuscript-ready text for observation-process diagnostics."""

    if not isinstance(result, ObservationProcessDiagnosticsResult):
        raise TypeError("result must be an ObservationProcessDiagnosticsResult")
    group = result.provenance.get("group_column")
    clustering = (
        "No participant/group column was declared."
        if group is None
        else f"Repeated rows were labelled by group column {group!r}."
    )
    requested = result.provenance.get("requested_predictors", [])
    history = result.provenance.get("requested_history_predictors", [])
    diagnostics = [str(value) for value in requested] + [str(value) for value in history]
    diagnostic_text = "none beyond candidate time" if not diagnostics else ", ".join(diagnostics)
    failed = 0
    if not result.predictor_summary.empty and "status_code" in result.predictor_summary:
        failed = int(np.count_nonzero(result.predictor_summary["status_code"] != "ok"))
    return (
        f"The observation-process denominator contained {result.denominator_rows} scheduled/candidate "
        f"samples, of which {result.observed_rows} were retained and {result.missing_rows} were "
        f"missing (missing fraction={result.missing_fraction:.3f}). {clustering} "
        f"Descriptive observation-probability diagnostics considered {diagnostic_text}; "
        f"{failed} requested association diagnostic(s) were unsupported or failed and were retained "
        "in the audit. Associations were descriptive univariate logistic summaries without iid "
        "standard errors or p-values. They do not establish a causal missingness mechanism, do not "
        "classify MAR/MNAR status, and absence of a detected association does not prove a "
        "non-informative observation process. No missing gaze was imputed and no inverse-probability "
        "or inverse-intensity correction was applied."
    )
