import numpy as np
import pandas as pd
import pytest

from eyetrajectoriespy.sparse_score_uncertainty import sparse_fpca_score_uncertainty
from eyetrajectoriespy.types import IrregularTrajectorySet, SparseFPCAResult


def _fit(score_ridge: float) -> SparseFPCAResult:
    grid = np.array([0.0, 0.5, 1.0])
    return SparseFPCAResult(
        scores=np.zeros((1, 1)),
        eigenvalues=np.array([2.0]),
        dimension="x",
        curve_ids=("c1",),
        metadata=pd.DataFrame(index=[0]),
        coordinate_system="normalized",
        time_unit="s",
        n_components=1,
        fit_method="native_covariance",
        fit_smoothing="local_linear_epanechnikov",
        score_method="PACE",
        score_smoothing=None,
        tolerance=1e-10,
        normalize=False,
        provenance={
            "sparse_fpca": {
                "backend": "native",
                "score_ridge": score_ridge,
                "score_condition_limit": 1e12,
                "min_score_samples": 2,
                "sample_counts": [2],
                "analysis_support_action": "error",
            }
        },
        evaluation_grid=grid,
        mean=np.zeros(3),
        covariance=2.0 * np.ones((3, 3)),
        eigenfunctions=np.ones((1, 3)),
        noise_variance=1.0,
        quadrature_weights=np.ones(3),
        score_diagnostics=pd.DataFrame(),
        covariance_diagnostics={},
        mean_support_counts=np.ones(3, dtype=int),
        covariance_support_counts=np.ones((3, 3), dtype=int),
    )


def _trajectory() -> IrregularTrajectorySet:
    return IrregularTrajectorySet(
        time=(np.array([0.0, 1.0]),),
        values=(np.zeros((2, 1)),),
        curve_ids=("c1",),
        dimension_names=("x",),
        coordinate_system="normalized",
        time_unit="s",
    )


def test_uncertainty_inherits_fitted_score_ridge():
    unregularized = sparse_fpca_score_uncertainty(_fit(0.0), _trajectory())
    regularized = sparse_fpca_score_uncertainty(_fit(3.0), _trajectory())

    assert unregularized.covariance[0, 0, 0] == pytest.approx(0.4)
    assert regularized.covariance[0, 0, 0] == pytest.approx(1.0)
    assert regularized.covariance[0, 0, 0] > unregularized.covariance[0, 0, 0]
    assert regularized.provenance["score_ridge"] == pytest.approx(3.0)
    assert regularized.provenance["covariance_source"] == (
        "full_fitted_covariance_plus_noise_and_declared_score_ridge"
    )
