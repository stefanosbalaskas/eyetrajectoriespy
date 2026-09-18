import importlib.util

import pytest

from eyetrajectoriespy import simulate_planar_trajectories, to_skfda_basis


def test_basis_projection_input_contracts_do_not_require_backend():
    gaze = simulate_planar_trajectories(
        n_participants=3,
        trials_per_participant=2,
        n_time=31,
    )
    with pytest.raises(KeyError):
        to_skfda_basis(gaze, dimension="missing")
    with pytest.raises(ValueError):
        to_skfda_basis(gaze, dimension="x", n_basis=1)
    with pytest.raises(ValueError):
        to_skfda_basis(gaze, dimension="x", basis="bspline", n_basis=3, order=4)


@pytest.mark.skipif(importlib.util.find_spec("skfda") is None, reason="optional scikit-fda not installed")
def test_bspline_and_fourier_basis_projection():
    gaze = simulate_planar_trajectories(
        n_participants=4,
        trials_per_participant=2,
        n_time=41,
    )
    bspline = to_skfda_basis(
        gaze,
        dimension="x",
        basis="bspline",
        n_basis=8,
        order=4,
    )
    assert bspline.dimension == "x"
    assert bspline.basis_type == "bspline"
    assert bspline.n_basis == 8
    assert bspline.backend_object.coefficients.shape[0] == gaze.n_curves

    fourier = to_skfda_basis(
        gaze,
        dimension="y",
        basis="fourier",
        n_basis=7,
    )
    assert fourier.dimension == "y"
    assert fourier.basis_type == "fourier"
    assert fourier.backend_object.coefficients.shape[0] == gaze.n_curves


@pytest.mark.skipif(importlib.util.find_spec("skfda") is None, reason="optional scikit-fda not installed")
def test_basis_projection_rejects_unknown_family():
    gaze = simulate_planar_trajectories(
        n_participants=3,
        trials_per_participant=2,
        n_time=31,
    )
    with pytest.raises(ValueError):
        to_skfda_basis(gaze, dimension="x", basis="mystery", n_basis=8)
