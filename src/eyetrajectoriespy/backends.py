"""Optional interoperability with general-purpose functional-data packages."""

from __future__ import annotations

from .types import BasisProjectionResult, TrajectorySet
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



def to_skfda_basis(
    trajectories: TrajectorySet,
    *,
    dimension: str,
    basis: str = "bspline",
    n_basis: int = 15,
    order: int = 4,
) -> BasisProjectionResult:
    """Project one functional dimension to an explicit scikit-fda basis.

    Basis projection is an approximation/smoothing decision. The selected
    basis family and size are returned in a provenance-preserving wrapper.
    """

    validate_trajectory_set(trajectories, require_complete=True)
    if dimension not in trajectories.dimension_names:
        raise KeyError(f"Unknown dimension {dimension!r}")
    if n_basis < 2:
        raise ValueError("n_basis must be at least 2")
    if order < 1:
        raise ValueError("order must be positive")
    if basis not in {"bspline", "fourier"}:
        raise ValueError("basis must be 'bspline' or 'fourier'")
    if basis == "bspline" and n_basis < order:
        raise ValueError("For B-splines, n_basis must be at least order")
    try:
        from skfda import FDataGrid
        from skfda.representation.basis import BSplineBasis, FourierBasis
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise ImportError(
            "scikit-fda is optional. Install eyetrajectoriespy with the 'fda' extra."
        ) from exc

    index = trajectories.dimension_names.index(dimension)
    data = trajectories.values[:, :, index][:, :, None]
    grid = FDataGrid(
        data_matrix=data,
        grid_points=trajectories.time,
        dataset_name=f"eyetrajectoriespy {dimension}",
        coordinate_names=(dimension,),
    )
    domain = (float(trajectories.time[0]), float(trajectories.time[-1]))
    if basis == "bspline":
        basis_object = BSplineBasis(
            domain_range=domain,
            n_basis=n_basis,
            order=order,
        )
    elif basis == "fourier":
        basis_object = FourierBasis(
            domain_range=domain,
            n_basis=n_basis,
        )
    else:  # validated before optional backend import
        raise AssertionError("unreachable basis family")

    projected = grid.to_basis(basis_object)
    return BasisProjectionResult(
        backend_object=projected,
        dimension=dimension,
        basis_type=basis,
        n_basis=n_basis,
        time_domain=domain,
        provenance={
            **dict(trajectories.provenance),
            "basis_projection": {
                "backend": "scikit-fda",
                "basis": basis,
                "n_basis": n_basis,
                "order": order if basis == "bspline" else None,
            },
        },
    )
