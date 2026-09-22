import numpy as np
import pytest

from eyetrajectoriespy import (
    TrajectorySet,
    fit_local_return_map,
    poincare_crossings,
    return_map_stability,
)


def _spiral_cycles():
    time = np.linspace(0.0, 20.0 * np.pi, 2001)
    amplitude = np.exp(-0.02 * time)
    x = amplitude * np.sin(time)
    y = amplitude * np.cos(time)
    return TrajectorySet(
        time=time,
        values=np.stack([x, y], axis=1)[None, :, :],
        curve_ids=("spiral",),
        dimension_names=("x", "y"),
        time_unit="s",
        coordinate_system="arbitrary",
    )


def test_poincare_crossings_interpolate_declared_section():
    data = _spiral_cycles()
    crossings = poincare_crossings(
        data,
        curve=0,
        section_dimension="x",
        section_value=0.0,
        direction="positive",
        state_dimensions=("y",),
    )

    assert crossings.n_crossings >= 8
    assert crossings.states.shape[1] == 1
    assert crossings.state_dimensions == ("y",)
    assert np.all((crossings.fractions >= 0) & (crossings.fractions <= 1))
    assert crossings.provenance["experimental"] is True


def test_local_return_map_recovers_contracting_cycle_map():
    data = _spiral_cycles()
    crossings = poincare_crossings(
        data,
        curve=0,
        section_dimension="x",
        section_value=0.0,
        direction="positive",
        state_dimensions=("y",),
    )
    fit = fit_local_return_map(
        crossings,
        reference="mean",
        n_neighbors=8,
    )
    stability = return_map_stability(fit)

    assert fit.jacobian.shape == (1, 1)
    assert fit.n_transitions == 8
    assert 0 < stability.spectral_radius < 1
    assert stability.classification == "contracting"
    assert stability.provenance["experimental"] is True


def test_return_map_requires_explicit_neighborhood_policy():
    data = _spiral_cycles()
    crossings = poincare_crossings(
        data,
        curve=0,
        section_dimension="x",
        section_value=0.0,
        direction="positive",
        state_dimensions=("y",),
    )
    with pytest.raises(ValueError, match="exactly one"):
        fit_local_return_map(crossings, reference="mean")


def test_return_map_rejects_rank_deficient_constant_state():
    time = np.linspace(0.0, 12.0 * np.pi, 1201)
    x = np.sin(time)
    y = np.ones_like(time)
    data = TrajectorySet(
        time=time,
        values=np.stack([x, y], axis=1)[None, :, :],
        curve_ids=("circle",),
        dimension_names=("x", "y"),
        time_unit="s",
    )
    crossings = poincare_crossings(
        data,
        curve=0,
        section_dimension="x",
        section_value=0.0,
        direction="positive",
        state_dimensions=("y",),
    )
    with pytest.raises(ValueError, match="rank deficient"):
        fit_local_return_map(
            crossings,
            reference="mean",
            n_neighbors=min(5, crossings.n_crossings - 1),
        )


def test_poincare_requires_nonempty_state_dimensions():
    data = TrajectorySet(
        time=np.arange(10, dtype=float),
        values=np.sin(np.arange(10, dtype=float))[None, :, None],
        curve_ids=("x",),
        dimension_names=("x",),
        time_unit="samples",
    )
    with pytest.raises(ValueError, match="state_dimensions"):
        poincare_crossings(
            data,
            curve=0,
            section_dimension="x",
            section_value=0.0,
            direction="both",
        )
