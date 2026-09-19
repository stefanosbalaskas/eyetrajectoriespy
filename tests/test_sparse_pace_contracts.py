import builtins
import sys
import types

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from eyetrajectoriespy import (
    IrregularTrajectorySet,
    fit_sparse_fpca_fdapy,
    plot_sparse_irregular_dimension,
    sparse_dimension_summary,
    sparse_fpca_reporting_text,
    sparse_fpca_score_frame,
    to_fdapy_irregular,
)


def sparse_sample():
    return IrregularTrajectorySet(
        time=(
            np.array([0.0, 0.2, 0.8]),
            np.array([0.1, 0.3, 0.7, 0.9]),
            np.array([0.0, 0.4, 0.6, 1.0]),
        ),
        values=(
            np.array([[0.1, 0.5], [0.2, 0.45], [0.7, 0.2]]),
            np.array([[0.2, 0.55], [0.3, 0.5], [0.6, 0.25], [0.8, 0.2]]),
            np.array([[0.15, 0.52], [0.4, 0.4], [0.55, 0.3], [0.82, 0.18]]),
        ),
        curve_ids=("P1|1", "P2|1", "P3|1"),
        dimension_names=("x", "y"),
        metadata=pd.DataFrame(
            {
                "participant_id": ["P1", "P2", "P3"],
                "condition": ["A", "B", "A"],
            }
        ),
        coordinate_system="normalized",
        time_unit="s",
        provenance={"source": "synthetic_sparse"},
    )


def install_fake_fdapy(monkeypatch, *, score_shape=None, bad_eigenvalues=False):
    fdapy = types.ModuleType("FDApy")
    representation = types.ModuleType("FDApy.representation")
    preprocessing = types.ModuleType("FDApy.preprocessing")

    class DenseArgvals(dict):
        pass

    class IrregularArgvals(dict):
        pass

    class IrregularValues(dict):
        pass

    class IrregularFunctionalData:
        def __init__(self, argvals, values):
            self.argvals = argvals
            self.values = values

    class UFPCA:
        last_instance = None

        def __init__(self, n_components, method, normalize=False):
            self.n_components = n_components
            self.method = method
            self.normalize = normalize
            self.eigenvalues = (
                np.array([np.nan] * n_components)
                if bad_eigenvalues
                else np.arange(n_components, 0, -1, dtype=float)
            )
            self.fit_smoothing = None
            self.transform_call = None
            UFPCA.last_instance = self

        def fit(self, data, method_smoothing=None):
            self.fit_data = data
            self.fit_smoothing = method_smoothing

        def transform(self, data, method="PACE", method_smoothing="LP", tol=1e-4):
            self.transform_call = {
                "method": method,
                "method_smoothing": method_smoothing,
                "tol": tol,
            }
            shape = score_shape or (len(data.values), self.n_components)
            return np.arange(np.prod(shape), dtype=float).reshape(shape)

        def inverse_transform(self, scores):
            return {"scores": np.asarray(scores).copy()}

    fdapy.IrregularFunctionalData = IrregularFunctionalData
    representation.DenseArgvals = DenseArgvals
    representation.IrregularArgvals = IrregularArgvals
    representation.IrregularValues = IrregularValues
    preprocessing.UFPCA = UFPCA

    monkeypatch.setitem(sys.modules, "FDApy", fdapy)
    monkeypatch.setitem(sys.modules, "FDApy.representation", representation)
    monkeypatch.setitem(sys.modules, "FDApy.preprocessing", preprocessing)
    return UFPCA


def test_sparse_summary_and_plot_preserve_native_sampling():
    gaze = sparse_sample()
    summary = sparse_dimension_summary(gaze, dimension="x")
    assert list(summary["n_sample_times"]) == [3, 4, 4]
    assert list(summary["n_observed"]) == [3, 4, 4]
    assert np.all(summary["n_nonfinite"] == 0)
    assert plot_sparse_irregular_dimension(gaze, dimension="x") is not None
    with pytest.raises(KeyError):
        sparse_dimension_summary(gaze, dimension="z")
    with pytest.raises(KeyError):
        plot_sparse_irregular_dimension(gaze, dimension="z")
    plt.close("all")


def test_fdapy_conversion_uses_curve_specific_grids(monkeypatch):
    gaze = sparse_sample()
    install_fake_fdapy(monkeypatch)
    data = to_fdapy_irregular(gaze, dimension="x")
    assert np.array_equal(data.argvals[0]["input_dim_0"], gaze.time[0])
    assert np.array_equal(data.argvals[1]["input_dim_0"], gaze.time[1])
    assert np.array_equal(data.values[2], gaze.values[2][:, 0])


def test_sparse_pace_fit_contract_and_provenance(monkeypatch):
    gaze = sparse_sample()
    UFPCA = install_fake_fdapy(monkeypatch)
    result = fit_sparse_fpca_fdapy(
        gaze,
        dimension="x",
        n_components=2,
        fit_smoothing="PS",
        score_smoothing="LP",
        tol=1e-5,
        normalize=False,
    )
    model = UFPCA.last_instance
    assert model.method == "covariance"
    assert model.fit_smoothing == "PS"
    assert model.transform_call == {
        "method": "PACE",
        "method_smoothing": "LP",
        "tol": 1e-5,
    }
    assert result.scores.shape == (3, 2)
    assert np.array_equal(result.eigenvalues, [2.0, 1.0])
    assert result.curve_ids == gaze.curve_ids
    assert list(result.metadata["condition"]) == ["A", "B", "A"]
    assert result.provenance["sparse_fpca"]["interpolation_performed"] is False
    assert result.provenance["sparse_fpca"]["sample_counts"] == [3, 4, 4]

    frame = sparse_fpca_score_frame(result)
    assert list(frame.columns) == [
        "curve_id",
        "participant_id",
        "condition",
        "SFPC1",
        "SFPC2",
    ]
    text = sparse_fpca_reporting_text(result)
    assert "PACE conditional-expectation scores" in text
    assert "No common-grid interpolation" in text


def test_sparse_contract_errors_precede_backend_import():
    gaze = sparse_sample()
    with pytest.raises(TypeError):
        fit_sparse_fpca_fdapy(gaze, dimension="x", n_components=True)
    with pytest.raises(ValueError):
        fit_sparse_fpca_fdapy(gaze, dimension="x", n_components=0)
    with pytest.raises(ValueError):
        fit_sparse_fpca_fdapy(gaze, dimension="x", n_components=4)
    with pytest.raises(ValueError):
        fit_sparse_fpca_fdapy(gaze, dimension="x", tol=0)
    with pytest.raises(TypeError):
        fit_sparse_fpca_fdapy(gaze, dimension="x", normalize=1)
    with pytest.raises(ValueError):
        fit_sparse_fpca_fdapy(gaze, dimension="x", fit_smoothing="bad")
    with pytest.raises(ValueError):
        fit_sparse_fpca_fdapy(gaze, dimension="x", score_smoothing="bad")


def test_nonfinite_selected_values_are_not_silently_dropped():
    gaze = sparse_sample()
    values = list(gaze.values)
    values[0] = values[0].copy()
    values[0][1, 0] = np.nan
    bad = IrregularTrajectorySet(
        time=gaze.time,
        values=tuple(values),
        curve_ids=gaze.curve_ids,
        dimension_names=gaze.dimension_names,
        metadata=gaze.metadata.reset_index(drop=True),
        coordinate_system=gaze.coordinate_system,
        time_unit=gaze.time_unit,
        provenance=gaze.provenance,
    )
    summary = sparse_dimension_summary(bad, dimension="x")
    assert summary.iloc[0]["n_nonfinite"] == 1
    with pytest.raises(ValueError, match="absent samples"):
        to_fdapy_irregular(bad, dimension="x")


def test_missing_backend_has_clear_sparse_extra_message(monkeypatch):
    gaze = sparse_sample()
    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name.startswith("FDApy"):
            raise ImportError("missing")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(ImportError, match="sparse"):
        to_fdapy_irregular(gaze, dimension="x")


def test_backend_shape_and_eigenvalue_failures(monkeypatch):
    gaze = sparse_sample()
    install_fake_fdapy(monkeypatch, score_shape=(3, 1))
    with pytest.raises(RuntimeError, match="score shape"):
        fit_sparse_fpca_fdapy(gaze, dimension="x", n_components=2)

    install_fake_fdapy(monkeypatch, bad_eigenvalues=True)
    with pytest.raises(RuntimeError, match="eigenvalues"):
        fit_sparse_fpca_fdapy(gaze, dimension="x", n_components=2)
