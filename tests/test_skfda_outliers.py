import builtins
import importlib.util

import pytest

from eyetrajectoriespy import (
    detect_functional_outliers_skfda,
    simulate_planar_trajectories,
)


@pytest.mark.skipif(importlib.util.find_spec("skfda") is None, reason="optional scikit-fda not installed")
def test_skfda_boxplot_outlier_wrapper_returns_review_flags():
    gaze = simulate_planar_trajectories(
        n_participants=6,
        trials_per_participant=2,
        n_time=41,
        random_state=12,
    )
    result = detect_functional_outliers_skfda(
        gaze,
        dimension="x",
        method="boxplot",
        factor=1.5,
    )
    assert len(result.diagnostics) == gaze.n_curves
    assert set(result.diagnostics["backend_label"].unique()) <= {-1, 1}
    assert result.method == "skfda_boxplot"


@pytest.mark.skipif(importlib.util.find_spec("skfda") is None, reason="optional scikit-fda not installed")
def test_skfda_outlier_wrapper_contracts():
    gaze = simulate_planar_trajectories(
        n_participants=5,
        trials_per_participant=2,
        n_time=31,
    )
    with pytest.raises(KeyError):
        detect_functional_outliers_skfda(gaze, dimension="missing")
    with pytest.raises(ValueError):
        detect_functional_outliers_skfda(gaze, dimension="x", method="bad")
    with pytest.raises(ValueError):
        detect_functional_outliers_skfda(gaze, dimension="x", factor=0)



def test_skfda_outlier_bridge_clear_error_when_backend_missing(monkeypatch):
    gaze = simulate_planar_trajectories(
        n_participants=4,
        trials_per_participant=2,
        n_time=31,
    )
    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name.startswith("skfda"):
            raise ImportError("missing")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(ImportError, match="scikit-fda"):
        detect_functional_outliers_skfda(
            gaze,
            dimension="x",
            method="boxplot",
        )
