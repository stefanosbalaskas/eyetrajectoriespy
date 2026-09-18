"""Concise reporting helpers for functional gaze analyses."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .types import FPCAResult, MultilevelFPCAResult, TrajectorySet


def summarise_trajectory_set(trajectories: TrajectorySet) -> pd.DataFrame:
    """Return a one-row representation summary without making exclusion decisions."""
    missing = np.isnan(trajectories.values)
    return pd.DataFrame([{
        "n_curves": trajectories.n_curves,
        "n_time": trajectories.n_time,
        "n_dimensions": trajectories.n_dimensions,
        "time_start": trajectories.time[0],
        "time_end": trajectories.time[-1],
        "time_unit": trajectories.time_unit,
        "coordinate_system": trajectories.coordinate_system,
        "missing_fraction": float(missing.mean()),
        "dimensions": ", ".join(trajectories.dimension_names),
    }])


def summarise_fpca(result: FPCAResult) -> pd.DataFrame:
    """Return a component-level explained-variance table."""
    return pd.DataFrame({
        "component": np.arange(1, result.n_components + 1),
        "explained_variance": result.explained_variance,
        "explained_variance_ratio": result.explained_variance_ratio,
        "cumulative_variance_ratio": np.cumsum(result.explained_variance_ratio),
    })


def fpca_reporting_text(result: FPCAResult, *, digits: int = 1) -> str:
    """Generate compact manuscript-ready descriptive text for an FPCA fit."""
    pct = 100 * result.cumulative_explained_variance()[-1]
    individual = 100 * result.explained_variance_ratio
    head = ", ".join(f"FPC{i + 1}={v:.{digits}f}%" for i, v in enumerate(individual[:4]))
    scaling = result.provenance.get("fpca", {}).get("scaling", "unknown")
    return (
        f"Functional PCA retained {result.n_components} component(s), explaining {pct:.{digits}f}% of the "
        f"weighted functional variance ({head}). The analysis used {result.coordinate_system} coordinates, "
        f"time unit '{result.time_unit}', and channel scaling='{scaling}'."
    )


def multilevel_fpca_reporting_text(result: MultilevelFPCAResult, *, digits: int = 1) -> str:
    """Generate a compact description of participant/trial functional decomposition."""
    p = 100 * result.participant_fpca.cumulative_explained_variance()[-1]
    t = 100 * result.trial_fpca.cumulative_explained_variance()[-1]
    return (
        "Two-level functional decomposition separated participant-level from within-participant trial variation. "
        f"The retained participant components explained {p:.{digits}f}% of fitted participant-level variance; "
        f"the retained trial components explained {t:.{digits}f}% of fitted trial-level variance."
    )
