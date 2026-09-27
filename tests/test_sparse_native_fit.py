import numpy as np
import pandas as pd
import pytest

from eyetrajectoriespy import (
    IrregularTrajectorySet,
    fit_sparse_fpca,
    sparse_fpca_reporting_text,
    sparse_fpca_score_frame,
)
from eyetrajectoriespy._sparse_native import SparseNativeError
from eyetrajectoriespy._sparse_truth import simulate_sparse_functional_truth


def _truth_dataset(
    *,
    n_curves=48,
    samples_per_curve=12,
    noise_sd=0.12,
    random_state=202610,
):
    times, values, truth = simulate_sparse_functional_truth(
        n_curves=n_curves,
        samples_per_curve=samples_per_curve,
        noise_sd=noise_sd,
        random_state=random_state,
    )
    return (
        IrregularTrajectorySet(
            time=times,
            values=tuple(value[:, None] for value in values),
            curve_ids=tuple(f"P{i + 1:03d}|1" for i in range(n_curves)),
            dimension_names=("x",),
            metadata=pd.DataFrame(
                {
                    "participant_id": [
                        f"P{i + 1:03d}"
                        for i in range(n_curves)
                    ]
                }
            ),
            coordinate_system="normalized",
            time_unit="s",
            provenance={"source": "private_sparse_truth"},
        ),
        truth,
    )


def test_native_sparse_fit_recovers_components_and_pace_scores():
    gaze, truth = _truth_dataset()
    grid = np.linspace(0.0, 1.0, 25)

    result = fit_sparse_fpca(
        gaze,
        dimension="x",
        n_components=2,
        evaluation_grid=grid,
        mean_bandwidth=0.20,
        covariance_bandwidth=0.28,
        noise_variance_method="fixed",
        measurement_error_variance=truth.noise_sd**2,
        psd_action="project",
    )

    assert result.provenance["sparse_fpca"]["backend"] == "native"
    assert result.provenance["sparse_fpca"][
        "raw_sparse_trajectory_interpolation_performed"
    ] is False
    assert result.provenance["sparse_fpca"][
        "population_function_evaluation_at_native_times"
    ] is True
    assert result.provenance["sparse_fpca"][
        "score_covariance_source"
    ] == "full_fitted_covariance_plus_noise"
    assert result.provenance["sparse_fpca"][
        "cross_channel_covariance_modeled"
    ] is False

    assert result.evaluation_grid.shape == (25,)
    assert result.mean.shape == (25,)
    assert result.covariance.shape == (25, 25)
    assert result.eigenfunctions.shape == (2, 25)
    assert result.scores.shape == (gaze.n_curves, 2)
    assert result.noise_variance == pytest.approx(truth.noise_sd**2)
    assert np.isfinite(result.scores).all()
    assert np.all(result.score_diagnostics["status_code"] == "ok")
    assert np.all(result.score_diagnostics["solve_status"] == "solved")

    true_phi = np.vstack(
        [function(grid) for function in truth.eigenfunctions]
    )
    weighted_similarity = np.abs(
        result.eigenfunctions
        @ np.diag(result.quadrature_weights)
        @ true_phi.T
    )
    assert weighted_similarity[0, 0] > 0.80
    assert weighted_similarity[1, 1] > 0.80

    score_correlation_1 = abs(
        np.corrcoef(result.scores[:, 0], truth.scores[:, 0])[0, 1]
    )
    score_correlation_2 = abs(
        np.corrcoef(result.scores[:, 1], truth.scores[:, 1])[0, 1]
    )
    assert score_correlation_1 > 0.75
    assert score_correlation_2 > 0.55

    frame = sparse_fpca_score_frame(result)
    assert list(frame.columns[:2]) == ["curve_id", "participant_id"]
    assert {"SFPC1", "SFPC2"} <= set(frame.columns)

    text = sparse_fpca_reporting_text(result)
    assert "fitted natively" in text
    assert "full fitted covariance surface" in text
    assert "did not model cross-channel covariance" in text
    assert "FDApy's covariance-operator estimator" not in text


def test_native_diagonal_difference_noise_is_audited_without_clipping():
    gaze, _ = _truth_dataset(
        n_curves=40,
        samples_per_curve=12,
        noise_sd=0.15,
        random_state=17,
    )
    result = fit_sparse_fpca(
        gaze,
        dimension="x",
        n_components=2,
        evaluation_grid=np.linspace(0.0, 1.0, 21),
        mean_bandwidth=0.22,
        covariance_bandwidth=0.30,
        noise_bandwidth=0.22,
        noise_variance_method="diagonal_difference",
        psd_action="project",
    )

    assert result.noise_variance > 0
    assert result.noise_raw_diagonal.shape == (21,)
    assert result.noise_diagonal_difference.shape == (21,)
    assert (
        result.provenance["sparse_fpca"]["noise_variance_method"]
        == "diagonal_difference"
    )


def test_native_sparse_fit_retains_explicit_psd_correction_audit():
    gaze, truth = _truth_dataset(
        n_curves=24,
        samples_per_curve=9,
        random_state=31,
    )
    result = fit_sparse_fpca(
        gaze,
        dimension="x",
        n_components=2,
        evaluation_grid=np.linspace(0.0, 1.0, 17),
        mean_bandwidth=0.28,
        covariance_bandwidth=0.38,
        noise_variance_method="fixed",
        measurement_error_variance=truth.noise_sd**2,
        psd_action="project",
    )

    audit = result.covariance_diagnostics
    assert audit["requested_action"] == "project"
    assert audit["negative_eigenvalue_count"] >= 0
    assert audit["substantial_negative_eigenvalue_count"] >= 0
    assert audit["correction_frobenius_norm"] >= 0
    assert audit["relative_correction_frobenius_norm"] >= 0
    assert isinstance(audit["pre_repair_operator_eigenvalues"], list)


def test_native_sparse_fit_requires_explicit_noise_bandwidth_when_estimated():
    gaze, _ = _truth_dataset(
        n_curves=12,
        samples_per_curve=8,
        random_state=9,
    )
    with pytest.raises(ValueError, match="noise_bandwidth"):
        fit_sparse_fpca(
            gaze,
            dimension="x",
            n_components=2,
            evaluation_grid=np.linspace(0.0, 1.0, 13),
            mean_bandwidth=0.30,
            covariance_bandwidth=0.40,
            noise_variance_method="diagonal_difference",
            psd_action="project",
        )


def test_native_sparse_fit_rejects_invalid_noise_variance_contracts():
    gaze, truth = _truth_dataset(
        n_curves=12,
        samples_per_curve=8,
        random_state=11,
    )
    common = dict(
        trajectories=gaze,
        dimension="x",
        n_components=2,
        evaluation_grid=np.linspace(0.0, 1.0, 13),
        mean_bandwidth=0.30,
        covariance_bandwidth=0.40,
        psd_action="project",
    )

    with pytest.raises(ValueError, match="required"):
        fit_sparse_fpca(
            **common,
            noise_variance_method="fixed",
        )
    with pytest.raises(ValueError, match="must be None"):
        fit_sparse_fpca(
            **common,
            noise_bandwidth=0.30,
            noise_variance_method="diagonal_difference",
            measurement_error_variance=truth.noise_sd**2,
        )


def test_native_sparse_fit_rejects_nonfinite_observed_placeholders():
    gaze, truth = _truth_dataset(
        n_curves=12,
        samples_per_curve=8,
        random_state=21,
    )
    values = list(gaze.values)
    values[0] = values[0].copy()
    values[0][2, 0] = np.nan
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

    with pytest.raises(SparseNativeError) as exc:
        fit_sparse_fpca(
            bad,
            dimension="x",
            n_components=2,
            evaluation_grid=np.linspace(0.0, 1.0, 13),
            mean_bandwidth=0.30,
            covariance_bandwidth=0.40,
            noise_variance_method="fixed",
            measurement_error_variance=truth.noise_sd**2,
            psd_action="project",
        )
    assert exc.value.code == "nonfinite_sparse_observation"


def test_native_sparse_fit_requires_grid_to_span_pooled_support():
    gaze, truth = _truth_dataset(
        n_curves=12,
        samples_per_curve=8,
        random_state=41,
    )
    with pytest.raises(SparseNativeError) as exc:
        fit_sparse_fpca(
            gaze,
            dimension="x",
            n_components=2,
            evaluation_grid=np.linspace(0.1, 0.9, 13),
            mean_bandwidth=0.30,
            covariance_bandwidth=0.40,
            noise_variance_method="fixed",
            measurement_error_variance=truth.noise_sd**2,
            psd_action="project",
        )
    assert exc.value.code == "evaluation_grid_support_mismatch"


def test_two_univariate_fits_do_not_claim_sparse_multivariate_pace():
    x_gaze, truth = _truth_dataset(
        n_curves=18,
        samples_per_curve=9,
        random_state=51,
    )
    two_dimensional = IrregularTrajectorySet(
        time=x_gaze.time,
        values=tuple(
            np.column_stack([value[:, 0], 0.5 * value[:, 0]])
            for value in x_gaze.values
        ),
        curve_ids=x_gaze.curve_ids,
        dimension_names=("x", "y"),
        metadata=x_gaze.metadata.reset_index(drop=True),
        coordinate_system=x_gaze.coordinate_system,
        time_unit=x_gaze.time_unit,
        provenance=x_gaze.provenance,
    )
    settings = dict(
        n_components=2,
        evaluation_grid=np.linspace(0.0, 1.0, 15),
        mean_bandwidth=0.30,
        covariance_bandwidth=0.40,
        noise_variance_method="fixed",
        measurement_error_variance=truth.noise_sd**2,
        psd_action="project",
    )

    fit_x = fit_sparse_fpca(
        two_dimensional,
        dimension="x",
        **settings,
    )
    fit_y = fit_sparse_fpca(
        two_dimensional,
        dimension="y",
        **settings,
    )

    assert fit_x.dimension == "x"
    assert fit_y.dimension == "y"
    assert fit_x.provenance["sparse_fpca"][
        "cross_channel_covariance_modeled"
    ] is False
    assert fit_y.provenance["sparse_fpca"][
        "cross_channel_covariance_modeled"
    ] is False
