import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from eyetrajectoriespy import (
    SparseFPCAResult,
    plot_sparse_fpca_component,
    plot_sparse_fpca_covariance,
    plot_sparse_fpca_score_diagnostics,
    sparse_fpca_reporting_text,
)


def _native_sparse_result():
    grid = np.linspace(0.0, 1.0, 5)
    phi1 = np.sqrt(2.0) * np.sin(np.pi * grid)
    phi2 = np.sqrt(2.0) * np.sin(2.0 * np.pi * grid)
    covariance = (
        1.0 * np.outer(phi1, phi1)
        + 0.35 * np.outer(phi2, phi2)
    )
    return SparseFPCAResult(
        scores=np.array([[0.3, -0.1], [0.1, 0.2], [-0.2, 0.1]]),
        eigenvalues=np.array([1.0, 0.35]),
        dimension="x",
        curve_ids=("P1", "P2", "P3"),
        metadata=pd.DataFrame({"participant_id": ["P1", "P2", "P3"]}),
        coordinate_system="normalized",
        time_unit="s",
        n_components=2,
        fit_method="native_covariance",
        fit_smoothing="local_linear_epanechnikov",
        score_method="PACE",
        score_smoothing=None,
        tolerance=1e-10,
        normalize=False,
        provenance={
            "sparse_fpca": {
                "backend": "native",
                "sample_counts": [3, 4, 5],
                "evaluation_grid": grid.tolist(),
                "analysis_support": [0.0, 1.0],
                "analysis_support_action": "error",
                "outside_observation_count": 0,
                "noise_variance_method": "fixed",
                "noise_support": None,
                "score_ridge": 0.0,
                "covariance_psd": {
                    "applied_action": "project",
                    "relative_operator_correction_frobenius_norm": 0.002,
                },
            }
        },
        evaluation_grid=grid,
        mean=0.3 + 0.4 * grid,
        covariance=covariance,
        eigenfunctions=np.vstack((phi1, phi2)),
        noise_variance=0.01,
        quadrature_weights=np.array([0.125, 0.25, 0.25, 0.25, 0.125]),
        score_diagnostics=pd.DataFrame(
            {
                "curve_id": ["P1", "P2", "P3"],
                "n_samples": [3, 4, 5],
                "condition_number": [120.0, 40.0, 15.0],
                "status_code": ["ok", "ok", "ok"],
            }
        ),
        covariance_diagnostics={
            "relative_operator_correction_frobenius_norm": 0.002
        },
    )


def test_native_sparse_plotting_helpers_render_population_objects():
    result = _native_sparse_result()

    ax = plot_sparse_fpca_component(result, component=0)
    assert ax.get_title() == "Sparse FPC1: x(t)"
    plt.close(ax.figure)

    ax = plot_sparse_fpca_covariance(result)
    assert ax.get_title() == "Sparse FPCA fitted latent covariance"
    plt.close(ax.figure)

    ax = plot_sparse_fpca_score_diagnostics(result)
    assert ax.get_yscale() == "log"
    assert "condition number" in ax.get_ylabel().lower()
    plt.close(ax.figure)


def test_native_sparse_reporting_includes_auditable_numerical_contract():
    text = sparse_fpca_reporting_text(_native_sparse_result())

    assert "full fitted covariance surface" in text
    assert "support" in text.lower()
    assert "score ridge" in text
