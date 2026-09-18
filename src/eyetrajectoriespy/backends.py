"""Optional interoperability with general-purpose functional-data packages."""

from __future__ import annotations

from .types import TrajectorySet
from .validation import validate_trajectory_set


def to_skfda_grid(trajectories: TrajectorySet):
    """Convert trajectories to ``skfda.FDataGrid`` without changing values.

    The optional dependency is not required for the package's core FPCA.
    """

    validate_trajectory_set(trajectories)
    try:
        from skfda import FDataGrid
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise ImportError(
            "scikit-fda is optional. Install eyetrajectoriespy with the 'fda' extra."
        ) from exc
    return FDataGrid(
        data_matrix=trajectories.values,
        grid_points=trajectories.time,
        dataset_name="eyetrajectoriespy trajectories",
        coordinate_names=trajectories.dimension_names,
    )
