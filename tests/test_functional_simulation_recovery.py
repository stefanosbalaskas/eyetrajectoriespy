import numpy as np

from eyetrajectoriespy import (
    fit_fpca,
    fit_sparse_fpca,
    simulate_functional_process,
)


def _mean(time):
    time = np.asarray(time, dtype=float)
    return 0.25 + 0.30 * time


def _phi1(time):
    time = np.asarray(time, dtype=float)
    return np.sqrt(2.0) * np.sin(np.pi * time)


def _phi2(time):
    time = np.asarray(time, dtype=float)
    return np.sqrt(2.0) * np.sin(2.0 * np.pi * time)


def _weighted_similarity(estimated, truth, weights):
    estimated = np.asarray(estimated, dtype=float)
    truth = np.asarray(truth, dtype=float)
    estimated = estimated / np.sqrt(
        np.sum(estimated**2 * weights[None, :], axis=1)
    )[:, None]
    truth = truth / np.sqrt(
        np.sum(truth**2 * weights[None, :], axis=1)
    )[:, None]
    return np.abs(estimated @ np.diag(weights) @ truth.T)


def test_public_simulator_supports_dense_fpca_recovery():
    grid = np.linspace(0.0, 1.0, 81)
    simulation = simulate_functional_process(
        mean=_mean,
        eigenfunctions=(_phi1, _phi2),
        eigenvalues=(1.0, 0.35),
        truth_grid=grid,
        n_participants=240,
        measurement_noise_sd=0.05,
        random_state=831,
    )
    fitted = fit_fpca(
        simulation.observations,
        n_components=2,
        scaling="none",
    )

    truth_phi = simulation.truth.eigenfunctions[:, :, 0]
    estimated_phi = fitted.components[:, :, 0]
    similarity = _weighted_similarity(
        estimated_phi,
        truth_phi,
        fitted.weights,
    )

    assert similarity[0, 0] > 0.97
    assert similarity[1, 1] > 0.95
    relative_eigenvalue_error = np.abs(
        fitted.explained_variance - simulation.truth.eigenvalues
    ) / simulation.truth.eigenvalues
    assert np.max(relative_eigenvalue_error) < 0.20

    signs = np.sign(
        np.diag(
            estimated_phi
            @ np.diag(fitted.weights)
            @ truth_phi.T
        )
    )
    signs[signs == 0] = 1.0
    correlations = [
        np.corrcoef(
            signs[component] * fitted.scores[:, component],
            simulation.truth.scores[:, component],
        )[0, 1]
        for component in range(2)
    ]
    assert min(correlations) > 0.95


def test_public_simulator_supports_native_sparse_fpca_recovery():
    truth_grid = np.linspace(0.0, 1.0, 31)
    simulation = simulate_functional_process(
        mean=_mean,
        eigenfunctions=(_phi1, _phi2),
        eigenvalues=(1.0, 0.35),
        truth_grid=truth_grid,
        n_participants=64,
        observation_design="irregular",
        samples_per_curve=(8, 12),
        irregular_time_design="uniform",
        measurement_noise_sd=0.08,
        random_state=832,
    )
    fitted = fit_sparse_fpca(
        simulation.observations,
        dimension="value",
        n_components=2,
        evaluation_grid=truth_grid,
        mean_bandwidth=0.24,
        covariance_bandwidth=0.34,
        noise_variance_method="fixed",
        measurement_error_variance=0.08**2,
        psd_action="project",
    )

    truth_phi = simulation.truth.eigenfunctions[:, :, 0]
    similarity = _weighted_similarity(
        fitted.eigenfunctions,
        truth_phi,
        fitted.quadrature_weights,
    )
    assert similarity[0, 0] > 0.80
    assert similarity[1, 1] > 0.75

    signed_inner = (
        fitted.eigenfunctions
        @ np.diag(fitted.quadrature_weights)
        @ truth_phi.T
    )
    signs = np.sign(np.diag(signed_inner))
    signs[signs == 0] = 1.0
    correlations = [
        abs(
            np.corrcoef(
                signs[component] * fitted.scores[:, component],
                simulation.truth.scores[:, component],
            )[0, 1]
        )
        for component in range(2)
    ]
    assert min(correlations) > 0.60
    assert np.all(fitted.score_diagnostics["status_code"] == "ok")
