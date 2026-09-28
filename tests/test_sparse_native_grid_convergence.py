import numpy as np
import pandas as pd

from eyetrajectoriespy import IrregularTrajectorySet, fit_sparse_fpca
from eyetrajectoriespy._sparse_truth import simulate_sparse_functional_truth
from eyetrajectoriespy.fpca import functional_trapezoid_weights


def _grid_convergence_dataset():
    times, values, truth = simulate_sparse_functional_truth(
        n_curves=36,
        samples_per_curve=10,
        noise_sd=0.10,
        random_state=202611,
    )
    gaze = IrregularTrajectorySet(
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
        provenance={"source": "private_sparse_grid_convergence_truth"},
    )
    return gaze, truth


def _fit_on_grid(gaze, truth, n_grid):
    return fit_sparse_fpca(
        gaze,
        dimension="x",
        n_components=2,
        evaluation_grid=np.linspace(0.0, 1.0, n_grid),
        mean_bandwidth=0.24,
        covariance_bandwidth=0.32,
        noise_variance_method="fixed",
        measurement_error_variance=truth.noise_sd**2,
        psd_action="project",
    )


def _normalized_on_reference_grid(result, reference_grid):
    weights = functional_trapezoid_weights(reference_grid)
    interpolated = np.vstack(
        [
            np.interp(
                reference_grid,
                result.evaluation_grid,
                component,
            )
            for component in result.eigenfunctions
        ]
    )
    norms = np.sqrt(
        np.sum(interpolated**2 * weights[None, :], axis=1)
    )
    return interpolated / norms[:, None], weights


def _subspace_min_cosine(left, right, reference_grid):
    left_phi, weights = _normalized_on_reference_grid(
        left,
        reference_grid,
    )
    right_phi, _ = _normalized_on_reference_grid(
        right,
        reference_grid,
    )
    cross = left_phi @ np.diag(weights) @ right_phi.T
    return float(np.min(np.linalg.svd(cross, compute_uv=False)))


def _minimum_score_correlation(left, right):
    correlations = []
    for component in range(left.n_components):
        correlations.append(
            abs(
                np.corrcoef(
                    left.scores[:, component],
                    right.scores[:, component],
                )[0, 1]
            )
        )
    return float(min(correlations))


def test_native_sparse_estimator_stabilizes_under_grid_refinement():
    gaze, truth = _grid_convergence_dataset()
    fit_21 = _fit_on_grid(gaze, truth, 21)
    fit_41 = _fit_on_grid(gaze, truth, 41)
    fit_81 = _fit_on_grid(gaze, truth, 81)

    relative_21 = np.abs(
        fit_21.eigenvalues - fit_81.eigenvalues
    ) / np.abs(fit_81.eigenvalues)
    relative_41 = np.abs(
        fit_41.eigenvalues - fit_81.eigenvalues
    ) / np.abs(fit_81.eigenvalues)

    assert np.max(relative_21) < 0.20
    assert np.max(relative_41) < 0.10

    reference_grid = fit_81.evaluation_grid
    assert _subspace_min_cosine(fit_21, fit_81, reference_grid) > 0.90
    assert _subspace_min_cosine(fit_41, fit_81, reference_grid) > 0.95

    assert _minimum_score_correlation(fit_21, fit_81) > 0.95
    assert _minimum_score_correlation(fit_41, fit_81) > 0.98

    assert (
        fit_21.provenance["sparse_fpca"][
            "raw_sparse_trajectory_interpolation_performed"
        ]
        is False
    )
    assert (
        fit_81.provenance["sparse_fpca"][
            "population_function_evaluation_at_native_times"
        ]
        is True
    )
