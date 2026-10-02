import numpy as np
import pytest

from eyetrajectoriespy import (
    component_trajectories,
    fit_fpca,
    reconstruct_fpca,
    select_n_components,
    transform_fpca,
)
from eyetrajectoriespy.compositional import inverse_alr
from eyetrajectoriespy.types import TrajectorySet


def _univariate(values: np.ndarray, *, time: np.ndarray | None = None, name: str = "x") -> TrajectorySet:
    values = np.asarray(values, dtype=float)
    if time is None:
        time = np.linspace(0.0, 1.0, values.shape[1])
    return TrajectorySet(
        time=np.asarray(time, dtype=float),
        values=values[:, :, None],
        curve_ids=tuple(f"C{i + 1}" for i in range(values.shape[0])),
        dimension_names=(name,),
        coordinate_system="normalized",
        time_unit="s",
    )


def _fit_source() -> TrajectorySet:
    time = np.linspace(0.0, 1.0, 7)
    values = np.vstack(
        [
            np.sin(np.pi * time),
            0.5 * np.sin(np.pi * time) + 0.2 * time,
            -0.4 * np.sin(np.pi * time) + 0.1,
        ]
    )
    return _univariate(values, time=time)


def test_fpca_rejects_single_curve_and_constant_dimension_scaling():
    one = _univariate(np.array([[0.0, 0.3, 0.5, 0.4]]))
    with pytest.raises(ValueError, match="At least two trajectories"):
        fit_fpca(one, n_components=1)

    constant_across_curves = _univariate(
        np.tile(np.linspace(0.0, 1.0, 5), (3, 1))
    )
    with pytest.raises(ValueError, match="constant functional dimensions"):
        fit_fpca(
            constant_across_curves,
            n_components=1,
            scaling="dimension_sd",
        )


def test_fpca_rejects_invalid_component_specifications():
    source = _fit_source()
    with pytest.raises(TypeError, match="n_components"):
        fit_fpca(source, n_components=True)
    with pytest.raises(ValueError, match="n_components"):
        fit_fpca(source, n_components=0)
    with pytest.raises(ValueError, match="variance proportion"):
        fit_fpca(source, n_components=1.0)


def test_projection_and_reconstruction_contracts_fail_closed():
    source = _fit_source()
    fit = fit_fpca(source, n_components=2)

    shifted = _univariate(
        source.values[:, :, 0],
        time=source.time + 0.01,
    )
    with pytest.raises(ValueError, match="grid must match"):
        transform_fpca(fit, shifted)

    renamed = _univariate(source.values[:, :, 0], time=source.time, name="z")
    with pytest.raises(ValueError, match="dimension names/order"):
        transform_fpca(fit, renamed)

    with pytest.raises(ValueError, match="one- or two-dimensional"):
        reconstruct_fpca(fit, scores=np.zeros((1, 1, 1)))
    with pytest.raises(ValueError, match="outside the fitted range"):
        reconstruct_fpca(fit, n_components=0)
    with pytest.raises(ValueError, match="fewer columns"):
        reconstruct_fpca(fit, scores=np.zeros((1, 1)), n_components=2)

    with pytest.raises(IndexError, match="outside the fitted range"):
        component_trajectories(fit, -1)
    with pytest.raises(ValueError, match="threshold"):
        select_n_components(fit, threshold=0.0)


def test_inverse_alr_rejects_incompatible_shape():
    with pytest.raises(ValueError, match="incompatible dimensions"):
        inverse_alr(
            np.zeros((3, 4)),
            reference_dimension=1,
            n_dimensions=3,
        )
