import importlib.util

import numpy as np
import pandas as pd
import pytest

from eyetrajectoriespy import IrregularTrajectorySet, fit_sparse_fpca_fdapy


pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("FDApy") is None,
    reason="optional FDApy backend not installed",
)


def synthetic_sparse_curves(n_curves=18, random_state=123):
    rng = np.random.default_rng(random_state)
    dense = np.linspace(0.0, 1.0, 31)
    times = []
    values = []
    ids = []
    participants = []
    for i in range(n_curves):
        keep = np.sort(rng.choice(len(dense), size=12, replace=False))
        time = dense[keep]
        amplitude = rng.normal(scale=0.25)
        curve = np.sin(2 * np.pi * time) + amplitude * np.cos(np.pi * time)
        times.append(time)
        values.append(curve[:, None])
        ids.append(f"P{i+1:02d}|1")
        participants.append(f"P{i+1:02d}")
    return IrregularTrajectorySet(
        time=tuple(times),
        values=tuple(values),
        curve_ids=tuple(ids),
        dimension_names=("x",),
        metadata=pd.DataFrame({"participant_id": participants}),
        coordinate_system="normalized",
        time_unit="s",
        provenance={"source": "synthetic_sparse_optional_backend"},
    )


def test_real_fdapy_sparse_pace_smoke():
    gaze = synthetic_sparse_curves()
    result = fit_sparse_fpca_fdapy(
        gaze,
        dimension="x",
        n_components=2,
        fit_smoothing="PS",
        score_smoothing="LP",
        tol=1e-4,
        normalize=False,
    )
    assert result.scores.shape == (gaze.n_curves, 2)
    assert np.isfinite(result.scores).all()
    assert result.eigenvalues.shape == (2,)
    assert np.isfinite(result.eigenvalues).all()
    assert result.provenance["sparse_fpca"]["backend"] == "FDApy"
    assert result.provenance["sparse_fpca"]["interpolation_performed"] is False
