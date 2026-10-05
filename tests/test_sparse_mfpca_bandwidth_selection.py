import inspect
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from eyetrajectoriespy._sparse_multivariate import PlanarCovarianceBlocks
from eyetrajectoriespy._sparse_native import SparseNativeError
from eyetrajectoriespy.sparse_multivariate import fit_sparse_mfpca
from eyetrajectoriespy.sparse_multivariate_bandwidth_selection import (
    SparseMFPCABandwidthSelectionResult,
    _candidate_table,
    _curve_planar_gaussian_nll,
    _select_minimum_candidate,
    select_sparse_mfpca_bandwidths,
    sparse_mfpca_bandwidth_selection_reporting_text,
)
from eyetrajectoriespy.types import IrregularTrajectorySet


def _planar_curves(n_curves: int = 10) -> IrregularTrajectorySet:
    rng = np.random.default_rng(20261005)
    times = []
    values = []
    participants = []
    for index in range(n_curves):
        base = np.linspace(0.05, 0.95, 9)
        time = np.sort(np.clip(base + rng.normal(0.0, 0.004, base.size), 0.02, 0.98))
        latent = np.sin(2.0 * np.pi * time) + 0.07 * index * np.cos(np.pi * time)
        x = latent + rng.normal(0.0, 0.025, time.size)
        y = 0.65 * latent + 0.25 * np.cos(2.0 * np.pi * time)
        y += rng.normal(0.0, 0.03, time.size)
        times.append(time)
        values.append(np.column_stack([x, y]))
        participants.append(f"p{index // 2}")
    return IrregularTrajectorySet(
        time=tuple(times),
        values=tuple(values),
        curve_ids=tuple(f"c{index}" for index in range(n_curves)),
        dimension_names=("x", "y"),
        metadata=pd.DataFrame({"participant": participants}),
        coordinate_system="normalized",
        time_unit="normalized",
    )


def _select(trajectories, **overrides):
    kwargs = {
        "dimensions": ("x", "y"),
        "evaluation_grid": np.linspace(0.20, 0.80, 7),
        "mean_bandwidths": (0.28, 0.38),
        "covariance_bandwidths": (0.42,),
        "measurement_error": "diagonal",
        "measurement_error_variance": (0.004, 0.006),
        "analysis_support_action": "restrict",
        "n_splits": 2,
        "psd_action": "project",
        "random_state": 17,
    }
    kwargs.update(overrides)
    return select_sparse_mfpca_bandwidths(trajectories, **kwargs)


def test_planar_gaussian_loss_matches_direct_time_major_calculation():
    grid = np.array([0.0, 1.0])
    blocks = PlanarCovarianceBlocks(
        cxx=np.array([[0.8, 0.15], [0.15, 0.6]]),
        cxy=np.array([[0.10, 0.04], [0.07, 0.08]]),
        cyx=np.array([[0.10, 0.07], [0.04, 0.08]]),
        cyy=np.array([[0.7, 0.12], [0.12, 0.5]]),
    )
    population = SimpleNamespace(
        evaluation_grid=grid,
        covariance_blocks=blocks,
        mean=np.array([[0.1, -0.2], [0.3, 0.15]]),
    )
    time = np.array([0.0, 1.0])
    observed = np.array([[0.9, 0.1], [-0.5, 0.4]])
    error = np.array([[0.25, 0.05], [0.05, 0.35]])

    loss, condition, minimum, maximum = _curve_planar_gaussian_nll(
        population,
        time,
        observed,
        measurement_error_covariance=error,
        predictive_condition_limit=1e12,
    )

    channel_major = np.block(
        [[blocks.cxx, blocks.cxy], [blocks.cyx, blocks.cyy]]
    )
    permutation = np.array([0, 2, 1, 3])
    covariance = channel_major[np.ix_(permutation, permutation)]
    sigma = covariance + np.kron(np.eye(2), error)
    mean_tm = np.array([0.1, 0.3, -0.2, 0.15])
    observed_tm = observed.reshape(-1)
    residual = observed_tm - mean_tm
    eigenvalues = np.linalg.eigvalsh(sigma)
    expected = 0.5 * (
        np.sum(np.log(eigenvalues))
        + residual @ np.linalg.solve(sigma, residual)
        + 4 * np.log(2 * np.pi)
    ) / 4

    assert loss == pytest.approx(expected)
    assert minimum == pytest.approx(eigenvalues.min())
    assert maximum == pytest.approx(eigenvalues.max())
    assert condition == pytest.approx(eigenvalues.max() / eigenvalues.min())


def test_curve_selector_retains_complete_audit_and_selects_argmin():
    trajectories = _planar_curves()
    result = _select(trajectories)

    assert isinstance(result, SparseMFPCABandwidthSelectionResult)
    assert result.status_code == "ok"
    assert result.criterion == "mean_curve_planar_gaussian_nll"
    assert result.resampling_unit == "curve"
    assert len(result.assignments) == trajectories.n_curves
    assert len(result.candidates) == 2
    assert len(result.fold_results) == 4
    assert set(result.fold_results["status_code"]) == {"ok"}
    assert result.selected_bandwidths is not None

    eligible = result.candidate_summary[result.candidate_summary["eligible"]]
    best_loss = float(eligible["mean_loss"].min())
    selected_id = result.selected_bandwidths["candidate_id"]
    selected_loss = float(
        eligible.loc[eligible["candidate_id"] == selected_id, "mean_loss"].iloc[0]
    )
    assert selected_loss == pytest.approx(best_loss)
    assert result.provenance["population_refit_inside_fold"] is True
    assert result.provenance["joint_pace_scoring_performed"] is False
    assert result.provenance["rank_k_covariance_used_for_validation"] is False
    assert result.provenance["score_ridge_included_in_validation_covariance"] is False
    assert result.provenance["measurement_error_tuned"] is False
    assert result.provenance["automatic_fit_bandwidth_selection_performed"] is False
    assert result.provenance[
        "selected_values_must_be_passed_explicitly_to_fit_sparse_mfpca"
    ] is True

    assert {
        "n_train_time_points_raw",
        "n_validation_time_points_raw",
        "n_train_time_points_effective",
        "n_validation_time_points_effective",
        "n_train_planar_observations_effective",
        "n_validation_planar_observations_effective",
        "psd_applied_action",
        "psd_relative_operator_correction",
    } <= set(result.fold_results.columns)
    assert (
        result.fold_results["n_train_time_points_effective"]
        < result.fold_results["n_train_time_points_raw"]
    ).all()
    assert (
        result.fold_results["n_validation_planar_observations_effective"]
        == 2 * result.fold_results["n_validation_time_points_effective"]
    ).all()
    assert set(result.curve_losses["observation_order"]) == {
        "time_major_interleaved_xy"
    }


def test_fixed_matrix_measurement_error_is_retained_and_not_tuned():
    trajectories = _planar_curves()
    error = np.array([[0.004, 0.0015], [0.0015, 0.006]])
    result = _select(
        trajectories,
        mean_bandwidths=(0.32,),
        measurement_error="fixed_matrix",
        measurement_error_variance=None,
        measurement_error_covariance=error,
    )

    assert result.status_code == "ok"
    assert result.provenance["measurement_error_mode"] == "fixed_matrix"
    np.testing.assert_allclose(
        result.provenance["measurement_error_covariance"], error
    )
    assert result.provenance["measurement_error_tuned"] is False


def test_group_resampling_keeps_participant_curves_together():
    trajectories = _planar_curves()
    result = _select(
        trajectories,
        mean_bandwidths=(0.32,),
        resampling_unit="group",
        group_column="participant",
        shuffle=False,
    )

    assert result.status_code == "ok"
    assert result.group_column == "participant"
    assert "group" in result.assignments.columns
    assert result.assignments.groupby("group")["fold"].nunique().eq(1).all()
    assert result.provenance["group_leakage_prevented"] is True


def test_curve_fold_assignment_is_deterministic_under_fixed_seed():
    trajectories = _planar_curves()
    first = _select(
        trajectories,
        mean_bandwidths=(0.32,),
        covariance_bandwidths=(0.42,),
        random_state=91,
    )
    second = _select(
        trajectories,
        mean_bandwidths=(0.32,),
        covariance_bandwidths=(0.42,),
        random_state=91,
    )

    pd.testing.assert_frame_equal(first.assignments, second.assignments)
    pd.testing.assert_frame_equal(first.candidate_summary, second.candidate_summary)
    assert first.selected_bandwidths == second.selected_bandwidths


def test_impossible_group_design_fails_before_candidate_evaluation():
    trajectories = _planar_curves()
    with pytest.raises(ValueError, match="unique groups"):
        _select(
            trajectories,
            mean_bandwidths=(0.32,),
            resampling_unit="group",
            group_column="participant",
            n_splits=6,
            shuffle=False,
        )


def test_failed_candidate_folds_are_retained_not_silently_dropped():
    trajectories = _planar_curves()
    result = _select(
        trajectories,
        mean_bandwidths=(1e-6, 0.32),
        covariance_bandwidths=(0.42,),
        failure_action="retain",
    )

    failed = result.fold_results[
        np.isclose(result.fold_results["mean_bandwidth"], 1e-6)
    ]
    assert len(failed) == 2
    assert set(failed["status_code"]) == {"fit_failure"}
    assert failed["failure_code"].notna().all()
    assert result.candidate_summary["n_failed_folds"].max() == 2
    assert result.selected_bandwidths is not None
    assert result.selected_bandwidths["mean_bandwidth"] == pytest.approx(0.32)


def test_candidate_grid_is_sorted_unique_cartesian_product():
    candidates = _candidate_table((0.2, 0.3), (0.4, 0.5))
    assert len(candidates) == 4
    assert candidates.iloc[0].to_dict() == {
        "candidate_id": "candidate_0000",
        "mean_bandwidth": 0.2,
        "covariance_bandwidth": 0.4,
    }
    assert candidates.iloc[-1].to_dict() == {
        "candidate_id": "candidate_0003",
        "mean_bandwidth": 0.3,
        "covariance_bandwidth": 0.5,
    }


def test_minimum_rule_has_deterministic_smoother_tie_break():
    summary = pd.DataFrame(
        {
            "candidate_id": ["candidate_0000", "candidate_0001"],
            "mean_bandwidth": [0.2, 0.3],
            "covariance_bandwidth": [0.4, 0.4],
            "mean_loss": [1.0, 1.0],
            "eligible": [True, True],
        }
    )
    selected = _select_minimum_candidate(summary)
    assert selected["candidate_id"] == "candidate_0001"
    assert selected["mean_bandwidth"] == pytest.approx(0.3)


def test_error_support_fails_and_restrict_support_succeeds():
    trajectories = _planar_curves()
    with pytest.raises(SparseNativeError) as error:
        _select(
            trajectories,
            mean_bandwidths=(0.32,),
            analysis_support_action="error",
        )
    assert error.value.code == "observations_outside_analysis_support"

    restricted = _select(
        trajectories,
        mean_bandwidths=(0.32,),
        analysis_support_action="restrict",
    )
    assert restricted.status_code == "ok"


def test_coordinate_specific_missingness_fails_closed():
    source = _planar_curves()
    values = list(source.values)
    broken = values[0].copy()
    broken[2, 1] = np.nan
    values[0] = broken
    trajectories = IrregularTrajectorySet(
        time=source.time,
        values=tuple(values),
        curve_ids=source.curve_ids,
        dimension_names=source.dimension_names,
        metadata=source.metadata.copy(),
        coordinate_system=source.coordinate_system,
        time_unit=source.time_unit,
    )

    with pytest.raises(SparseNativeError) as error:
        _select(trajectories, mean_bandwidths=(0.32,))
    assert error.value.code == "coordinate_specific_missingness_unsupported"


def test_reporting_text_names_population_likelihood_and_no_automatic_fit():
    result = _select(
        _planar_curves(),
        mean_bandwidths=(0.32,),
        covariance_bandwidths=(0.42,),
    )
    text = sparse_mfpca_bandwidth_selection_reporting_text(result)

    assert "training curves only" in text
    assert "full fitted joint covariance" in text
    assert "Joint-PACE scores were not used" in text
    assert "not applied automatically" in text


def test_sparse_mfpca_fitter_remains_explicit_and_nonautomatic():
    parameters = inspect.signature(fit_sparse_mfpca).parameters
    assert "mean_bandwidth" in parameters
    assert "covariance_bandwidth" in parameters
    assert "mean_bandwidths" not in parameters
    assert "covariance_bandwidths" not in parameters

    trajectories = _planar_curves()
    fit = fit_sparse_mfpca(
        trajectories,
        dimensions=("x", "y"),
        n_components=1,
        evaluation_grid=np.linspace(0.20, 0.80, 7),
        mean_bandwidth=0.32,
        covariance_bandwidth=0.42,
        measurement_error="diagonal",
        measurement_error_variance=(0.004, 0.006),
        analysis_support_action="restrict",
        psd_action="project",
        score_failure_action="retain_nan",
    )
    assert fit.provenance["sparse_mfpca"]["automatic_bandwidth_selection_performed"] is False
