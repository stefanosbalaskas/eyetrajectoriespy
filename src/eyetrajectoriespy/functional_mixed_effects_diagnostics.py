"""Residual-dependence diagnostics for functional mixed-effects fits.

This module is deliberately diagnostic rather than model-selecting.  It exposes
within-trial residual autocovariance, autocorrelation, empirical semivariance,
and exact physical-lag pair contributions without automatically choosing a
serial covariance model or a trial-level functional random effect.
"""

from __future__ import annotations

from typing import Literal

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .types import (
    FunctionalMixedEffectsResidualDiagnosticsResult,
    FunctionalMixedEffectsResult,
)


def _validate_reference(result: FunctionalMixedEffectsResult) -> None:
    if not isinstance(result, FunctionalMixedEffectsResult):
        raise TypeError("result must be a FunctionalMixedEffectsResult")
    if not result.converged:
        raise ValueError("Residual diagnostics require a converged mixed-effects fit")

    residuals = np.asarray(result.residual_functions, dtype=float)
    if residuals.shape != (result.n_curves, result.time.size):
        raise ValueError(
            "residual_functions must have shape (n_curves, n_time)"
        )
    if not np.all(np.isfinite(residuals)):
        raise ValueError(
            "residual_functions contains non-finite values; residual diagnostics "
            "do not silently omit grid points"
        )
    if len(result.curve_participant_ids) != result.n_curves:
        raise ValueError(
            "curve_participant_ids length must equal the number of fitted curves"
        )
    if len(result.source_curve_ids) != result.n_curves:
        raise ValueError(
            "source_curve_ids length must equal the number of fitted curves"
        )


def _validate_max_lag(max_lag: int, n_time: int) -> int:
    if isinstance(max_lag, bool) or not isinstance(max_lag, (int, np.integer)):
        raise TypeError("max_lag must be an integer")
    value = int(max_lag)
    if value < 1:
        raise ValueError("max_lag must be at least 1")
    if value >= n_time:
        raise ValueError(
            "max_lag must be smaller than the number of observed time points"
        )
    return value


def _lag_time_summary(time: np.ndarray, lag: int) -> tuple[float, float, float]:
    if lag == 0:
        return 0.0, 0.0, 0.0
    delta = np.asarray(time[lag:] - time[:-lag], dtype=float)
    return float(np.mean(delta)), float(np.min(delta)), float(np.max(delta))


def _weighted_finite_mean(
    values: np.ndarray,
    weights: np.ndarray,
) -> tuple[float, int]:
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    valid = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    if not np.any(valid):
        return float("nan"), 0
    return (
        float(np.sum(values[valid] * weights[valid]) / np.sum(weights[valid])),
        int(np.sum(valid)),
    )


def _aggregate_diagnostics(
    trial: pd.DataFrame,
    group_columns: list[str],
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    grouper: str | list[str]
    if len(group_columns) == 1:
        grouper = group_columns[0]
    else:
        grouper = group_columns

    for keys, frame in trial.groupby(grouper, sort=False, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(group_columns, keys, strict=True))
        weights = frame["n_pairs"].to_numpy(dtype=float)

        autocovariance, _ = _weighted_finite_mean(
            frame["autocovariance"].to_numpy(),
            weights,
        )
        autocorrelation, n_defined = _weighted_finite_mean(
            frame["autocorrelation"].to_numpy(),
            weights,
        )
        semivariance, _ = _weighted_finite_mean(
            frame["semivariance"].to_numpy(),
            weights,
        )

        row.update(
            {
                "lag_time_mean": float(frame["lag_time_mean"].iloc[0]),
                "lag_time_min": float(frame["lag_time_min"].iloc[0]),
                "lag_time_max": float(frame["lag_time_max"].iloc[0]),
                "n_pairs": int(frame["n_pairs"].sum()),
                "n_trials_total": int(len(frame)),
                "n_trials_acf_defined": int(n_defined),
                "autocovariance": autocovariance,
                "autocorrelation": autocorrelation,
                "semivariance": semivariance,
                "trial_autocorrelation_min": (
                    float(frame["autocorrelation"].min(skipna=True))
                    if frame["autocorrelation"].notna().any()
                    else float("nan")
                ),
                "trial_autocorrelation_max": (
                    float(frame["autocorrelation"].max(skipna=True))
                    if frame["autocorrelation"].notna().any()
                    else float("nan")
                ),
            }
        )
        rows.append(row)

    return pd.DataFrame(rows)


def functional_mixed_effects_residual_diagnostics(
    result: FunctionalMixedEffectsResult,
    *,
    max_lag: int,
) -> FunctionalMixedEffectsResidualDiagnosticsResult:
    """Compute descriptive residual-dependence diagnostics.

    Parameters
    ----------
    result:
        Converged likelihood-based functional mixed-effects fit.
    max_lag:
        Largest within-trial index lag to inspect. The value is always explicit;
        no automatic lag selection is performed.

    Returns
    -------
    FunctionalMixedEffectsResidualDiagnosticsResult
        Trial-level diagnostics plus pair-count-weighted participant and overall
        summaries.

    Notes
    -----
    Diagnostics use the fitted model's conditional residual functions. For
    trial j with residuals r_j(t_m), the within-trial centered residual is

        e_j(t_m) = r_j(t_m) - mean_m r_j(t_m).

    At index lag h, autocovariance is the mean of
    e_j(t_m)e_j(t_{m+h}), autocorrelation divides by the lag-zero
    autocovariance, and semivariance is half the mean squared residual
    difference. Trials with exactly zero residual variance are retained;
    autocorrelation is undefined (NaN) and explicitly counted in summaries.

    The common time grid is not assumed equally spaced. Each index lag retains
    its mean, minimum, and maximum physical time separation. Use
    :func:`functional_mixed_effects_residual_pair_frame` when the exact
    physical lag for every residual pair is needed.
    """

    _validate_reference(result)
    residuals = np.asarray(result.residual_functions, dtype=float)
    time = np.asarray(result.time, dtype=float)
    max_lag_value = _validate_max_lag(max_lag, time.size)

    lag_summaries = {
        lag: _lag_time_summary(time, lag)
        for lag in range(max_lag_value + 1)
    }

    rows: list[dict[str, object]] = []
    for curve_index, residual in enumerate(residuals):
        residual_mean = float(np.mean(residual))
        centered = residual - residual_mean
        variance = float(np.mean(centered * centered))
        zero_variance = bool(variance == 0.0)
        residual_rms = float(np.sqrt(np.mean(residual * residual)))
        residual_sd = float(np.sqrt(variance))

        for lag in range(max_lag_value + 1):
            left = centered[: time.size - lag] if lag else centered
            right = centered[lag:] if lag else centered
            raw_left = residual[: time.size - lag] if lag else residual
            raw_right = residual[lag:] if lag else residual
            n_pairs = int(left.size)

            autocovariance = float(np.mean(left * right))
            autocorrelation = (
                float(autocovariance / variance)
                if not zero_variance
                else float("nan")
            )
            semivariance = float(
                0.5 * np.mean((raw_right - raw_left) ** 2)
            )

            lag_mean, lag_min, lag_max = lag_summaries[lag]
            rows.append(
                {
                    "curve_index": int(curve_index),
                    "curve_id": result.source_curve_ids[curve_index],
                    "participant_id": result.curve_participant_ids[curve_index],
                    "lag_index": int(lag),
                    "lag_time_mean": lag_mean,
                    "lag_time_min": lag_min,
                    "lag_time_max": lag_max,
                    "n_pairs": n_pairs,
                    "residual_mean": residual_mean,
                    "residual_sd": residual_sd,
                    "residual_rms": residual_rms,
                    "zero_residual_variance": zero_variance,
                    "autocovariance": autocovariance,
                    "autocorrelation": autocorrelation,
                    "semivariance": semivariance,
                }
            )

    trial = pd.DataFrame(rows)
    participant = _aggregate_diagnostics(
        trial,
        ["participant_id", "lag_index"],
    )
    overall = _aggregate_diagnostics(trial, ["lag_index"])

    provenance = {
        "functional_mixed_effects_residual_diagnostics": {
            "residual_type": "conditional_residual_function",
            "within_trial_centering": True,
            "max_lag_index": max_lag_value,
            "automatic_lag_selection": False,
            "physical_lag_binning": False,
            "participant_summary": "pair_count_weighted_mean_of_trial_diagnostics",
            "overall_summary": "pair_count_weighted_mean_of_trial_diagnostics",
            "zero_variance_trial_policy": "retain_with_undefined_autocorrelation",
            "automatic_covariance_structure_selection": False,
            "automatic_ar1_selection": False,
            "automatic_trial_random_effect_selection": False,
            "time_unit": result.time_unit,
            "dimension": result.dimension_name,
            "source_model_random_slope_predictor": result.random_slope_predictor,
        }
    }

    return FunctionalMixedEffectsResidualDiagnosticsResult(
        reference=result,
        trial_diagnostics=trial,
        participant_diagnostics=participant,
        overall_diagnostics=overall,
        max_lag=max_lag_value,
        provenance=provenance,
    )


def functional_mixed_effects_residual_diagnostic_frame(
    result: FunctionalMixedEffectsResidualDiagnosticsResult,
    *,
    level: Literal["trial", "participant", "overall"] = "trial",
    curve_id: str | None = None,
    participant_id: str | None = None,
) -> pd.DataFrame:
    """Return one auditable residual-diagnostic summary level."""

    if not isinstance(result, FunctionalMixedEffectsResidualDiagnosticsResult):
        raise TypeError(
            "result must be a FunctionalMixedEffectsResidualDiagnosticsResult"
        )
    if level not in {"trial", "participant", "overall"}:
        raise ValueError("level must be 'trial', 'participant', or 'overall'")

    if level == "trial":
        if participant_id is not None:
            raise ValueError(
                "participant_id is not accepted for level='trial'; use curve_id "
                "or request the complete trial frame"
            )
        frame = result.trial_diagnostics
        if curve_id is not None:
            curve_id = str(curve_id)
            frame = frame.loc[frame["curve_id"].astype(str) == curve_id]
            if frame.empty:
                raise KeyError(f"Unknown curve_id {curve_id!r}")
        return frame.reset_index(drop=True).copy()

    if level == "participant":
        if curve_id is not None:
            raise ValueError(
                "curve_id is not accepted for level='participant'"
            )
        frame = result.participant_diagnostics
        if participant_id is not None:
            participant_id = str(participant_id)
            frame = frame.loc[
                frame["participant_id"].astype(str) == participant_id
            ]
            if frame.empty:
                raise KeyError(f"Unknown participant_id {participant_id!r}")
        return frame.reset_index(drop=True).copy()

    if curve_id is not None or participant_id is not None:
        raise ValueError(
            "curve_id and participant_id are not accepted for level='overall'"
        )
    return result.overall_diagnostics.reset_index(drop=True).copy()


def functional_mixed_effects_residual_pair_frame(
    result: FunctionalMixedEffectsResidualDiagnosticsResult,
    *,
    lag_index: int,
    curve_id: str | None = None,
    participant_id: str | None = None,
) -> pd.DataFrame:
    """Expose exact within-trial residual pairs for one declared index lag.

    No physical-lag bins are created. This helper is intended for auditing
    non-equally-spaced common grids or for analyst-declared downstream
    physical-lag summaries.
    """

    if not isinstance(result, FunctionalMixedEffectsResidualDiagnosticsResult):
        raise TypeError(
            "result must be a FunctionalMixedEffectsResidualDiagnosticsResult"
        )
    if isinstance(lag_index, bool) or not isinstance(
        lag_index, (int, np.integer)
    ):
        raise TypeError("lag_index must be an integer")
    lag = int(lag_index)
    if lag < 0 or lag > result.max_lag:
        raise ValueError(
            f"lag_index must be between 0 and {result.max_lag}, inclusive"
        )

    reference = result.reference
    residuals = np.asarray(reference.residual_functions, dtype=float)
    time = np.asarray(reference.time, dtype=float)
    rows: list[dict[str, object]] = []

    for curve_index, residual in enumerate(residuals):
        this_curve = str(reference.source_curve_ids[curve_index])
        this_participant = str(reference.curve_participant_ids[curve_index])
        if curve_id is not None and this_curve != str(curve_id):
            continue
        if participant_id is not None and this_participant != str(participant_id):
            continue

        centered = residual - float(np.mean(residual))
        starts = range(time.size - lag) if lag else range(time.size)
        for start in starts:
            end = start + lag
            rows.append(
                {
                    "curve_index": int(curve_index),
                    "curve_id": this_curve,
                    "participant_id": this_participant,
                    "lag_index": lag,
                    "start_index": int(start),
                    "end_index": int(end),
                    "time_start": float(time[start]),
                    "time_end": float(time[end]),
                    "physical_lag": float(time[end] - time[start]),
                    "residual_start": float(residual[start]),
                    "residual_end": float(residual[end]),
                    "centered_product": float(centered[start] * centered[end]),
                    "semivariance_contribution": float(
                        0.5 * (residual[end] - residual[start]) ** 2
                    ),
                }
            )

    frame = pd.DataFrame(rows)
    if curve_id is not None and frame.empty:
        raise KeyError(f"Unknown curve_id {str(curve_id)!r}")
    if participant_id is not None and frame.empty:
        raise KeyError(f"Unknown participant_id {str(participant_id)!r}")
    return frame


def compare_functional_mixed_effects_residual_diagnostics(
    reference: FunctionalMixedEffectsResult,
    comparison: FunctionalMixedEffectsResult,
    *,
    max_lag: int,
    reference_label: str = "reference",
    comparison_label: str = "comparison",
) -> pd.DataFrame:
    """Compare overall residual-dependence diagnostics for two nested analyses.

    This is a descriptive sensitivity comparison. It does not rank the fits,
    choose a covariance structure, or perform a hypothesis test.
    """

    _validate_reference(reference)
    _validate_reference(comparison)

    if reference.dimension_name != comparison.dimension_name:
        raise ValueError("Fits must use the same response dimension")
    if reference.time_unit != comparison.time_unit:
        raise ValueError("Fits must use the same time unit")
    if tuple(reference.source_curve_ids) != tuple(comparison.source_curve_ids):
        raise ValueError("Fits must contain the same source curves in the same order")
    if tuple(reference.curve_participant_ids) != tuple(
        comparison.curve_participant_ids
    ):
        raise ValueError(
            "Fits must contain the same participant mapping in the same order"
        )
    if reference.time.shape != comparison.time.shape or not np.allclose(
        reference.time,
        comparison.time,
        rtol=0.0,
        atol=0.0,
    ):
        raise ValueError("Fits must use exactly the same observed time grid")

    first = functional_mixed_effects_residual_diagnostics(
        reference,
        max_lag=max_lag,
    ).overall_diagnostics
    second = functional_mixed_effects_residual_diagnostics(
        comparison,
        max_lag=max_lag,
    ).overall_diagnostics

    keep = [
        "lag_index",
        "lag_time_mean",
        "lag_time_min",
        "lag_time_max",
        "n_pairs",
        "n_trials_total",
        "n_trials_acf_defined",
        "autocovariance",
        "autocorrelation",
        "semivariance",
    ]
    merged = first[keep].merge(
        second[keep],
        on=[
            "lag_index",
            "lag_time_mean",
            "lag_time_min",
            "lag_time_max",
            "n_pairs",
            "n_trials_total",
        ],
        suffixes=("_reference", "_comparison"),
        validate="one_to_one",
    )

    for metric in ("autocovariance", "autocorrelation", "semivariance"):
        merged[f"delta_{metric}"] = (
            merged[f"{metric}_comparison"]
            - merged[f"{metric}_reference"]
        )

    merged.insert(0, "reference_label", str(reference_label))
    merged.insert(1, "comparison_label", str(comparison_label))
    return merged


def _plot_residual_metric(
    result: FunctionalMixedEffectsResidualDiagnosticsResult,
    *,
    metric: Literal["autocorrelation", "semivariance"],
    level: Literal["trial", "participant", "overall"],
    curve_id: str | None,
    participant_id: str | None,
    ax,
):
    frame = functional_mixed_effects_residual_diagnostic_frame(
        result,
        level=level,
        curve_id=curve_id,
        participant_id=participant_id,
    )
    if level == "trial" and curve_id is None:
        raise ValueError(
            "curve_id is required when plotting level='trial'; "
            "the plotting helper does not silently average across trials"
        )
    if level == "participant" and participant_id is None:
        raise ValueError(
            "participant_id is required when plotting level='participant'; "
            "use level='overall' for the declared aggregate summary"
        )

    if ax is None:
        _, ax = plt.subplots()

    x = frame["lag_time_mean"].to_numpy(dtype=float)
    y = frame[metric].to_numpy(dtype=float)
    ax.plot(x, y, marker="o")
    if metric == "autocorrelation":
        ax.axhline(0.0, linewidth=1.0)
        ax.set_ylabel("Residual autocorrelation")
    else:
        ax.set_ylabel("Residual semivariance")
    ax.set_xlabel(f"Physical lag ({result.reference.time_unit})")

    nonuniform = np.any(
        frame["lag_time_min"].to_numpy(dtype=float)
        != frame["lag_time_max"].to_numpy(dtype=float)
    )
    if nonuniform:
        ax.set_title(
            "Index-lag diagnostic (x = mean physical lag; inspect min/max or pair frame)"
        )
    return ax


def plot_functional_mixed_effects_residual_acf(
    result: FunctionalMixedEffectsResidualDiagnosticsResult,
    *,
    level: Literal["trial", "participant", "overall"] = "overall",
    curve_id: str | None = None,
    participant_id: str | None = None,
    ax=None,
):
    """Plot residual autocorrelation against retained physical lag."""

    return _plot_residual_metric(
        result,
        metric="autocorrelation",
        level=level,
        curve_id=curve_id,
        participant_id=participant_id,
        ax=ax,
    )


def plot_functional_mixed_effects_residual_variogram(
    result: FunctionalMixedEffectsResidualDiagnosticsResult,
    *,
    level: Literal["trial", "participant", "overall"] = "overall",
    curve_id: str | None = None,
    participant_id: str | None = None,
    ax=None,
):
    """Plot empirical residual semivariance against retained physical lag."""

    return _plot_residual_metric(
        result,
        metric="semivariance",
        level=level,
        curve_id=curve_id,
        participant_id=participant_id,
        ax=ax,
    )


def functional_mixed_effects_residual_reporting_text(
    result: FunctionalMixedEffectsResidualDiagnosticsResult,
) -> str:
    """Return compact manuscript-oriented residual-diagnostic reporting text."""

    if not isinstance(result, FunctionalMixedEffectsResidualDiagnosticsResult):
        raise TypeError(
            "result must be a FunctionalMixedEffectsResidualDiagnosticsResult"
        )

    lag0 = result.trial_diagnostics.loc[
        result.trial_diagnostics["lag_index"] == 0
    ]
    zero_variance_count = int(lag0["zero_residual_variance"].sum())
    structure = (
        "random functional intercept only"
        if result.reference.random_slope_predictor is None
        else (
            "random functional intercept plus the declared random functional "
            f"slope for {result.reference.random_slope_predictor!r}"
        )
    )

    return (
        "Within-trial residual dependence was inspected using the conditional "
        "residual functions from the converged functional mixed-effects fit "
        f"({structure}). Diagnostics were computed through the explicitly "
        f"declared maximum index lag {result.max_lag}. For each trial, residuals "
        "were centered within trial before calculating autocovariance and "
        "autocorrelation; empirical semivariance used one-half of the mean "
        "squared residual difference at each lag. The observed common time grid "
        f"was retained in {result.reference.time_unit!r}; index lags retain their "
        "mean/minimum/maximum physical separations and no physical-lag binning "
        "was performed. Participant and overall summaries are descriptive "
        "pair-count-weighted summaries of trial-level diagnostics. "
        f"{zero_variance_count} trial(s) had exactly zero residual variance; "
        "such trials were retained and their autocorrelation was marked "
        "undefined. These diagnostics do not automatically select AR(1), a "
        "trial-level functional random effect, or any other residual covariance "
        "structure."
    )
