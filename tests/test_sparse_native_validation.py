import numpy as np
import pandas as pd

from eyetrajectoriespy import IrregularTrajectorySet, fit_sparse_fpca
from eyetrajectoriespy._sparse_native import pace_scores
from eyetrajectoriespy._sparse_truth import simulate_sparse_functional_truth
from eyetrajectoriespy._sparse_validation import evaluate_sparse_truth_recovery


def _dataset_from_truth(**kwargs):
    times, values, truth = simulate_sparse_functional_truth(**kwargs)
    trajectories = IrregularTrajectorySet(
        time=times,
        values=tuple(value[:, None] for value in values),
        curve_ids=tuple(f"P{i + 1:03d}|1" for i in range(len(times))),
        dimension_names=("x",),
        metadata=pd.DataFrame(
            {
                "participant_id": [
                    f"P{i + 1:03d}" for i in range(len(times))
                ]
            }
        ),
        coordinate_system="normalized",
        time_unit="s",
        provenance={"source": "private_sparse_validation_truth"},
    )
    return trajectories, truth


def test_private_sparse_truth_supports_difficult_sampling_regimes():
    gaze, truth = _dataset_from_truth(
        n_curves=30,
        samples_per_curve=(2, 4),
        noise_sd=0.25,
        eigenvalues=(1.0, 0.9),
        observation_design="center_clustered",
        random_state=501,
    )

    assert truth.sample_counts.min() >= 2
    assert truth.sample_counts.max() <= 4
    assert len(np.unique(truth.sample_counts)) > 1
    assert truth.observation_design == "center_clustered"
    assert np.allclose(truth.eigenvalues, [1.0, 0.9])
    assert gaze.sample_counts.min() >= 2
    assert gaze.sample_counts.max() <= 4


def test_sparse_recovery_metrics_are_sign_and_subspace_aware():
    gaze, truth = _dataset_from_truth(
        n_curves=42,
        samples_per_curve=(7, 11),
        noise_sd=0.10,
        eigenvalues=(1.0, 0.45),
        observation_design="uniform",
        random_state=502,
    )
    result = fit_sparse_fpca(
        gaze,
        dimension="x",
        n_components=2,
        evaluation_grid=np.linspace(0.0, 1.0, 25),
        mean_bandwidth=0.24,
        covariance_bandwidth=0.32,
        noise_variance_method="fixed",
        measurement_error_variance=truth.noise_sd**2,
        psd_action="project",
    )
    metrics = evaluate_sparse_truth_recovery(result, truth)

    assert metrics.mean_ise >= 0
    assert metrics.covariance_ise >= 0
    assert metrics.eigenvalue_relative_error.shape == (2,)
    assert metrics.component_absolute_similarity.shape == (2,)
    assert metrics.subspace_principal_cosines.shape == (2,)
    assert metrics.score_correlation.shape == (2,)
    assert metrics.score_rmse.shape == (2,)
    assert np.min(metrics.subspace_principal_cosines) > 0.75
    assert np.nanmin(metrics.score_correlation) > 0.60
    assert 0.0 <= metrics.score_failure_rate <= 1.0


def test_score_ridge_reduces_conditioning_at_cost_of_score_shrinkage():
    grid = np.array([0.0, 0.5, 1.0])
    phi = np.array([[1.0, 1.0, 1.0]]) / np.sqrt(3.0)
    covariance = np.ones((3, 3), dtype=float)
    observed = np.array([1.0, 1.0, 1.0])

    unregularized = pace_scores(
        ("curve",),
        (grid,),
        (observed,),
        evaluation_grid=grid,
        fitted_mean=np.zeros(3),
        fitted_covariance=covariance,
        eigenvalues=np.array([1.0]),
        eigenfunctions=phi,
        noise_variance=1e-5,
        n_components=1,
        score_ridge=0.0,
        condition_limit=1e9,
    )
    regularized = pace_scores(
        ("curve",),
        (grid,),
        (observed,),
        evaluation_grid=grid,
        fitted_mean=np.zeros(3),
        fitted_covariance=covariance,
        eigenvalues=np.array([1.0]),
        eigenfunctions=phi,
        noise_variance=1e-5,
        n_components=1,
        score_ridge=0.1,
        condition_limit=1e9,
    )

    assert (
        regularized.diagnostics.loc[0, "condition_number"]
        < unregularized.diagnostics.loc[0, "condition_number"]
    )
    assert abs(regularized.scores[0, 0]) < abs(unregularized.scores[0, 0])
