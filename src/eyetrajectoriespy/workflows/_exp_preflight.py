"""E2: advisory data-readiness audit without silent participant exclusion."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from ..types import IrregularTrajectorySet, TrajectorySet


@dataclass(frozen=True)
class WorkflowPreflightResult:
    """Descriptive support tables, warnings and blocking issues; no data edits."""

    layout: str
    summary: pd.DataFrame
    curve_support: pd.DataFrame
    participant_support: pd.DataFrame
    warnings: tuple[str, ...]
    blocking_issues: tuple[str, ...]
    provenance: dict[str, Any]

    @property
    def ready(self) -> bool:
        """No input-shape incompatibilities were found; not a scientific go/no-go."""
        return not self.blocking_issues


def workflow_preflight(
    data: TrajectorySet | IrregularTrajectorySet,
    *,
    participant_column: str | None = "participant_id",
    trial_column: str | None = "trial_id",
    minimum_observed_per_dimension: int = 3,
    required_dimensions: tuple[str, ...] = (),
    require_common_grid: bool = False,
) -> WorkflowPreflightResult:
    """Describe missingness, support, units, hierarchy, and incompatibilities.

    Thresholds are analyst-supplied *warnings*, not exclusion rules. A workflow
    must still validate its own scientific assumptions and design. `ready`
    does not certify statistical identification or power.
    """

    if not isinstance(data, (TrajectorySet, IrregularTrajectorySet)):
        raise TypeError("data must be TrajectorySet or IrregularTrajectorySet")
    if minimum_observed_per_dimension < 1:
        raise ValueError("minimum_observed_per_dimension must be positive")
    layout = "common_grid" if isinstance(data, TrajectorySet) else "irregular"
    warning: list[str] = []
    blockers: list[str] = []
    if require_common_grid and layout != "common_grid":
        blockers.append("Requested common-grid analysis, but observations are irregular; no interpolation was performed.")
    missing_dimensions = sorted(set(required_dimensions) - set(data.dimension_names))
    if missing_dimensions:
        blockers.append(f"Missing requested dimensions: {missing_dimensions!r}")
    if data.coordinate_system == "unknown":
        warning.append("Coordinate semantics are unknown; report pixels, normalized coordinates or degrees.")
    if data.time_unit == "unknown":
        warning.append("Time units are unknown; determine whether times represent seconds, milliseconds or normalized time.")
    if isinstance(data, TrajectorySet):
        observation_arrays = [data.values[i] for i in range(data.n_curves)]
        time_arrays = [data.time for _ in range(data.n_curves)]
    else:
        observation_arrays = list(data.values)
        time_arrays = list(data.time)
    rows: list[dict[str, Any]] = []
    total_missing = total_samples = 0
    for curve_id, times, values in zip(data.curve_ids, time_arrays, observation_arrays, strict=True):
        observed = np.isfinite(values)
        finite_by_dimension = observed.sum(axis=0)
        missing = int((~observed).sum())
        samples = int(values.size)
        total_samples += samples
        total_missing += missing
        supported_times = times[observed.any(axis=1)]
        rows.append({
            "curve_id": curve_id,
            "n_samples": len(times),
            "n_dimensions": data.n_dimensions,
            "finite_values": samples - missing,
            "missing_values": missing,
            "missing_fraction": missing / samples if samples else np.nan,
            "min_dimension_support": int(finite_by_dimension.min()),
            "max_dimension_support": int(finite_by_dimension.max()),
            "observed_time_start": float(supported_times[0]) if len(supported_times) else np.nan,
            "observed_time_end": float(supported_times[-1]) if len(supported_times) else np.nan,
            "below_declared_support_threshold": bool(
                np.any(finite_by_dimension < minimum_observed_per_dimension)
            ),
        })
    support = pd.DataFrame(rows)
    if support["below_declared_support_threshold"].any():
        n = int(support["below_declared_support_threshold"].sum())
        warning.append(
            f"{n} trajectories have at least one dimension with fewer than "
            f"{minimum_observed_per_dimension} observed samples; none were excluded."
        )
    if not support["finite_values"].gt(0).any():
        blockers.append("All trajectories contain only missing observations.")
    md = data.metadata.reset_index(drop=True)
    participant_counts = pd.DataFrame(columns=["participant_id", "n_curves", "n_trials"])
    if participant_column is not None:
        if participant_column not in md.columns:
            warning.append(f"Participant column {participant_column!r} is absent; hierarchy cannot be audited.")
        else:
            groups = md.groupby(participant_column, dropna=False)
            participant_counts = groups.size().rename("n_curves").reset_index()
            participant_counts = participant_counts.rename(columns={participant_column: "participant_id"})
            if md[participant_column].isna().any():
                warning.append("Missing participant IDs detected; no participants were removed.")
            if trial_column and trial_column in md.columns:
                nt = groups[trial_column].nunique(dropna=True).reset_index(name="n_trials")
                participant_counts = participant_counts.merge(
                    nt.rename(columns={participant_column: "participant_id"}),
                    on="participant_id", how="left"
                )
                duplicates = md.duplicated([participant_column, trial_column], keep=False)
                if duplicates.any():
                    warning.append("Repeated participant/trial pairs found; may reflect additional stimuli/conditions.")
            else:
                participant_counts["n_trials"] = pd.NA
                if trial_column:
                    warning.append(f"Trial column {trial_column!r} is absent; trial nesting was not checked.")
    summary = pd.DataFrame([{
        "layout": layout, "n_curves": data.n_curves,
        "n_dimensions": data.n_dimensions, "n_participants": len(participant_counts),
        "total_samples": total_samples, "observed_values": total_samples - total_missing,
        "missing_values": total_missing,
        "missing_fraction": total_missing / total_samples if total_samples else np.nan,
        "minimum_observed_per_dimension": minimum_observed_per_dimension,
        "low_support_curves": int(support["below_declared_support_threshold"].sum()),
        "time_unit": data.time_unit, "coordinate_system": data.coordinate_system,
    }])
    return WorkflowPreflightResult(
        layout=layout, summary=summary, curve_support=support,
        participant_support=participant_counts, warnings=tuple(warning),
        blocking_issues=tuple(blockers),
        provenance={"input_modified": False, "automatic_exclusions": False,
                    "required_dimensions": list(required_dimensions),
                    "require_common_grid": require_common_grid,
                    "minimum_observed_per_dimension": minimum_observed_per_dimension},
    )


def plot_workflow_preflight(result: WorkflowPreflightResult, *, ax: Any = None) -> Any:
    """Plot sorted per-curve missingness fractions without selecting exclusions."""

    import matplotlib.pyplot as plt

    if not isinstance(result, WorkflowPreflightResult):
        raise TypeError("result must be a WorkflowPreflightResult")
    if ax is None:
        _, ax = plt.subplots(figsize=(7.5, 3.75))
    fractions = np.sort(result.curve_support["missing_fraction"].to_numpy(dtype=float))
    ax.plot(np.arange(1, len(fractions) + 1), fractions, ".", color="tab:blue")
    ax.set_ylim(-0.02, 1.02)
    ax.set_xlabel("Trajectory rank by missing fraction (no exclusions)")
    ax.set_ylabel("Missing dimension-samples / observed grid positions")
    ax.set_title("Descriptive input missingness; no automatic quality cutoff")
    return ax
