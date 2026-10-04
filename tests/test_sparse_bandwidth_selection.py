import numpy as np
import pandas as pd
import pytest

from eyetrajectoriespy.sparse_bandwidth_selection import (
    SparseFPCABandwidthSelectionResult,
    _candidate_table,
    _make_folds,
    _select_minimum_candidate,
    select_sparse_fpca_bandwidths,
    sparse_fpca_bandwidth_selection_reporting_text,
)
from eyetrajectoriespy.types import IrregularTrajectorySet


def _sparse_curves(n_curves: int = 8) -> IrregularTrajectorySet:
    rng = np.random.default_rng(20261005)
    times = []
    values = []
    participants = []
    for index in range(n_curves):
        base = np.linspace(0.05, 0.95, 8)
        jitter = rng.normal(0.0, 0.006, size=base.size)
        time = np.clip(base + jitter, 0.02, 0.98)
        time = np.sort(time)
        signal = (
            np.sin(2.0 * np.pi * time)
            + 0.18 * np.cos(np.pi * time) * (index - (n_curves - 1) / 2.0)
            + rng.normal(0.0, 0.04, size=time.size)
        )
        times.append(time)
        values.append(signal[:, None])
        participants.append(f"p{index // 2}")
    return IrregularTrajectorySet(
        time=tuple(times),
        values=tuple(values),
        curve_ids=tuple(f"c{index}" for index in range(n_curves)),
        dimension_names=("x",),
        metadata=pd.DataFrame({"participant": participants}),
        coordinate_system="normalized",
        time_unit="normalized",
    )


def _select(trajectories, **kwargs):
    return select_sparse_fpca_bandwidths(
        trajectories,
        dimension="x",
        evaluation_grid=np.linspace(0.20, 0.80, 7),
        mean_bandwidths=(0.22, 0.32),
        covariance_bandwidths=(0.35,),
        noise_variance_method="fixed",
        measurement_error_variance=0.01,
        analysis_support_action="restrict",
        n_splits=2,
        psd_action="project",
        **kwargs,
    )


def test_curve_level_selector_retains_complete_audit_and_selects_argmin():
    trajectories = _sparse_curves()

    result = _select(trajectories, random_state=17)

    assert isinstance(result, SparseFPCABandwidthSelectionResult)
    assert result.status_code == "ok"
    assert result.criterion == "mean_curve_gaussian_nll"
    assert result.resampling_unit == "curve"
    assert len(result.assignments) == trajectories.n_curves
    assert result.assignments["curve_id"].nunique() == trajectories.n_curves
    assert len(result.candidates) == 2
    assert len(result.fold_results) == 4
    assert set(result.fold_results["status_code"]) == {"ok"}
    assert result.min_valid_folds == 2

    eligible = result.candidate_summary[result.candidate_summary["eligible"]]
    best_loss = float(eligible["mean_loss"].min())
    selected_id = result.selected_bandwidths["candidate_id"]
    selected_loss = float(
        eligible.loc[eligible["candidate_id"] == selected_id, "mean_loss"].iloc[0]
    )
    assert selected_loss == pytest.approx(best_loss)
    assert result.provenance["fit_inside_fold"] is True
    assert result.provenance["validation_observations_used_for_training"] is False
    assert result.provenance["validation_observations_used_for_pace_scoring"] is False
    assert result.provenance["automatic_fit_bandwidth_selection_performed"] is False


def test_curve_fold_assignment_is_deterministic_under_fixed_seed():
    trajectories = _sparse_curves()

    splits_a, assignments_a, _ = _make_folds(
        trajectories,
        n_splits=4,
        resampling_unit="curve",
        group_column=None,
        shuffle=True,
        random_state=91,
    )
    splits_b, assignments_b, _ = _make_folds(
        trajectories,
        n_splits=4,
        resampling_unit="curve",
        group_column=None,
        shuffle=True,
        random_state=91,
    )

    pd.testing.assert_frame_equal(assignments_a, assignments_b)
    assert len(splits_a) == len(splits_b) == 4
    for (train_a, test_a), (train_b, test_b) in zip(splits_a, splits_b, strict=True):
        np.testing.assert_array_equal(train_a, train_b)
        np.testing.assert_array_equal(test_a, test_b)
        assert np.intersect1d(train_a, test_a).size == 0


def test_group_resampling_keeps_participant_curves_together():
    trajectories = _sparse_curves()

    result = _select(
        trajectories,
        mean_bandwidths=(0.28,),
        resampling_unit="group",
        group_column="participant",
        shuffle=False,
    )

    assert result.status_code == "ok"
    assert result.group_column == "participant"
    assert "group" in result.assignments.columns
    counts = result.assignments.groupby("group")["fold"].nunique()
    assert counts.eq(1).all()
    assert result.provenance["group_leakage_prevented"] is True


def test_failed_candidate_folds_are_retained_not_silently_dropped():
    trajectories = _sparse_curves()

    result = select_sparse_fpca_bandwidths(
        trajectories,
        dimension="x",
        evaluation_grid=np.linspace(0.20, 0.80, 7),
        mean_bandwidths=(1e-6, 0.28),
        covariance_bandwidths=(0.35,),
        noise_variance_method="fixed",
        measurement_error_variance=0.01,
        analysis_support_action="restrict",
        n_splits=2,
        psd_action="project",
        failure_action="retain",
        random_state=11,
    )

    failed = result.fold_results[
        result.fold_results["mean_bandwidth"] == pytest.approx(1e-6)
    ]
    # pandas does not vectorize pytest.approx comparisons reliably; use isclose.
    failed = result.fold_results[
        np.isclose(result.fold_results["mean_bandwidth"], 1e-6)
    ]
    assert len(failed) == 2
    assert set(failed["status_code"]) == {"fit_failure"}
    assert failed["failure_code"].notna().all()
    assert result.candidate_summary["n_failed_folds"].max() == 2
    assert result.selected_bandwidths is not None
    assert result.selected_bandwidths["mean_bandwidth"] == pytest.approx(0.28)


def test_candidate_grid_is_sorted_unique_cartesian_product():
    candidates = _candidate_table(
        (0.3, 0.2),
        (0.5, 0.4),
        (0.2, 0.1),
    )

    assert len(candidates) == 8
    assert candidates.iloc[0].to_dict() == {
        "candidate_id": "candidate_0000",
        "mean_bandwidth": 0.3,
        "covariance_bandwidth": 0.5,
        "noise_bandwidth": 0.2,
    }


def test_minimum_rule_has_deterministic_smoother_tie_break():
    summary = pd.DataFrame(
        {
            "candidate_id": ["candidate_0000", "candidate_0001"],
            "mean_bandwidth": [0.2, 0.3],
            "covariance_bandwidth": [0.4, 0.4],
            "noise_bandwidth": [np.nan, np.nan],
            "mean_loss": [1.0, 1.0],
            "eligible": [True, True],
        }
    )

    selected = _select_minimum_candidate(summary)

    assert selected["candidate_id"] == "candidate_0001"
    assert selected["mean_bandwidth"] == pytest.approx(0.3)


def test_reporting_text_states_training_only_loss_and_no_automatic_fit():
    trajectories = _sparse_curves()
    result = _select(
        trajectories,
        mean_bandwidths=(0.28,),
        covariance_bandwidths=(0.35,),
    )

    text = sparse_fpca_bandwidth_selection_reporting_text(result)

    assert "training curves only" in text
    assert "Gaussian negative log predictive density" in text
    assert "not used for population fitting or PACE score estimation" in text
    assert "not applied automatically to the fitter" in text


def test_fixed_noise_rejects_noise_bandwidth_grid():
    trajectories = _sparse_curves()

    with pytest.raises(ValueError, match="noise_bandwidths must be None"):
        select_sparse_fpca_bandwidths(
            trajectories,
            dimension="x",
            evaluation_grid=np.linspace(0.20, 0.80, 7),
            mean_bandwidths=(0.28,),
            covariance_bandwidths=(0.35,),
            noise_bandwidths=(0.2,),
            noise_variance_method="fixed",
            measurement_error_variance=0.01,
            analysis_support_action="restrict",
            n_splits=2,
        )
