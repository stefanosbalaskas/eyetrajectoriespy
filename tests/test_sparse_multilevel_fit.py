import numpy as np
import pandas as pd
import pytest

from eyetrajectoriespy._sparse_native import SparseNativeError
from eyetrajectoriespy.sparse_multilevel import (
    SparseMultilevelFPCAResult,
    fit_sparse_multilevel_fpca,
    sparse_multilevel_fpca_reporting_text,
)
from eyetrajectoriespy.types import IrregularTrajectorySet


def _simulate_hierarchy(
    *,
    n_participants=12,
    trials_per_participant=2,
    single_trial_last=False,
    seed=174,
):
    rng = np.random.default_rng(seed)
    participant_scores = np.linspace(-1.4, 1.4, n_participants)
    times = []
    values = []
    curve_ids = []
    participant_ids = []
    for participant in range(n_participants):
        n_trials = (
            1
            if single_trial_last and participant == n_participants - 1
            else trials_per_participant
        )
        for trial in range(n_trials):
            base = np.linspace(0.0, 1.0, 11)
            jitter = rng.normal(0.0, 0.012, size=base.size)
            time = np.clip(base + jitter, 0.0, 1.0)
            time[0] = 0.0
            time[-1] = 1.0
            time = np.maximum.accumulate(time)
            # Ensure strict ordering after clipping/accumulation.
            for index in range(1, time.size):
                if time[index] <= time[index - 1]:
                    time[index] = min(1.0, time[index - 1] + 1e-5)
            time[-1] = 1.0

            trial_score = rng.normal(0.0, 0.55)
            mean = 0.15 + 0.10 * time
            between_mode = np.sqrt(2.0) * np.sin(np.pi * time)
            within_mode = np.sqrt(2.0) * np.sin(2.0 * np.pi * time)
            observed = (
                mean
                + participant_scores[participant] * between_mode
                + trial_score * within_mode
                + rng.normal(0.0, 0.10, size=time.size)
            )
            times.append(time)
            values.append(observed[:, None])
            curve_ids.append(f"p{participant:02d}_t{trial:02d}")
            participant_ids.append(f"p{participant:02d}")

    return IrregularTrajectorySet(
        time=tuple(times),
        values=tuple(values),
        curve_ids=tuple(curve_ids),
        dimension_names=("x",),
        metadata=pd.DataFrame({"participant_id": participant_ids}),
        coordinate_system="normalized",
        time_unit="normalized",
        provenance={"source": "sparse_multilevel_unit_test"},
    )


def _fit(trajectories):
    return fit_sparse_multilevel_fpca(
        trajectories,
        dimension="x",
        participant_column="participant_id",
        participant_components=1,
        trial_components=1,
        evaluation_grid=np.linspace(0.10, 0.90, 9),
        mean_bandwidth=0.35,
        total_covariance_bandwidth=0.45,
        between_covariance_bandwidth=0.45,
        analysis_support_action="restrict",
        noise_variance_method="fixed",
        measurement_error_variance=0.01,
        psd_action="project",
        score_ridge=1e-6,
        score_failure_action="error",
    )


def test_sparse_multilevel_fit_returns_audited_hierarchical_result():
    trajectories = _simulate_hierarchy()

    result = _fit(trajectories)

    assert isinstance(result, SparseMultilevelFPCAResult)
    assert result.dimension == "x"
    assert result.participant_column == "participant_id"
    assert len(result.participant_ids) == 12
    assert len(result.curve_ids) == 24
    assert result.participant_scores.shape == (12, 2)
    assert result.trial_scores.shape == (24, 3)
    assert set(result.score_diagnostics["status_code"]) == {"ok"}
    assert np.all(np.isfinite(result.participant_scores["participant_FPC1"]))
    assert np.all(np.isfinite(result.trial_scores["trial_FPC1"]))
    np.testing.assert_allclose(
        result.smoothed_within_covariance,
        result.smoothed_total_covariance - result.smoothed_between_covariance,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        result.total_covariance,
        result.between_covariance + result.within_covariance,
        atol=1e-12,
    )
    assert result.support_diagnostics["n_repeated_participants"] == 12
    assert result.support_diagnostics["single_trial_participants"] == []

    provenance = result.provenance["sparse_multilevel_fpca"]
    assert provenance["exchangeable_trials_assumed"] is True
    assert provenance["trial_fixed_effects_estimated"] is False
    assert provenance["weighting"] == "observation"
    assert provenance["equal_participant_weighting_claimed"] is False
    assert provenance["rank_k_covariance_used_for_scoring"] is False
    assert provenance["raw_sparse_trajectory_interpolation_performed"] is False
    assert provenance["automatic_bandwidth_selection_performed"] is False
    assert provenance["score_covariance_source"] == (
        "full_fitted_between_plus_within_plus_noise"
    )


def test_single_trial_participant_is_retained_but_not_used_for_between_pairs():
    trajectories = _simulate_hierarchy(single_trial_last=True)

    result = _fit(trajectories)

    assert result.support_diagnostics["n_participants"] == 12
    assert result.support_diagnostics["n_repeated_participants"] == 11
    assert result.support_diagnostics["single_trial_participants"] == ["p11"]
    assert (
        result.support_diagnostics["between_pair_counts_by_participant"]["p11"]
        == 0
    )
    assert np.all(np.isfinite(result.participant_scores["participant_FPC1"]))
    p11_trials = result.trial_scores[
        result.trial_scores["participant_id"] == "p11"
    ]
    assert len(p11_trials) == 1
    assert np.isfinite(p11_trials["trial_FPC1"].iloc[0])


def test_sparse_multilevel_reporting_states_scope_and_nonclaims():
    result = _fit(_simulate_hierarchy())

    text = sparse_multilevel_fpca_reporting_text(result)

    assert "same-participant cross-trial products" in text
    assert "full repaired between/within covariance surfaces" in text
    assert "not rank-truncated reconstructions" in text
    assert "exchangeable repeated trials" in text
    assert "does not estimate trial-condition fixed functional effects" in text
    assert "rather than equal-participant weighting" in text
    assert "does not interpolate raw sparse trajectories" in text
    assert "does not propagate population-estimation" in text


def test_sparse_multilevel_requires_participant_metadata():
    trajectories = _simulate_hierarchy()

    with pytest.raises(ValueError, match="participant column"):
        fit_sparse_multilevel_fpca(
            trajectories,
            dimension="x",
            participant_column="missing",
            participant_components=1,
            trial_components=1,
            evaluation_grid=np.linspace(0.1, 0.9, 5),
            mean_bandwidth=0.4,
            total_covariance_bandwidth=0.5,
            between_covariance_bandwidth=0.5,
            noise_variance_method="fixed",
            measurement_error_variance=0.01,
        )


def test_sparse_multilevel_requires_three_participants():
    full = _simulate_hierarchy(n_participants=3)
    keep = full.metadata["participant_id"].isin(["p00", "p01"]).to_numpy()
    indices = np.flatnonzero(keep)
    reduced = IrregularTrajectorySet(
        time=tuple(full.time[index] for index in indices),
        values=tuple(full.values[index] for index in indices),
        curve_ids=tuple(full.curve_ids[index] for index in indices),
        dimension_names=full.dimension_names,
        metadata=full.metadata.iloc[indices].reset_index(drop=True),
        coordinate_system=full.coordinate_system,
        time_unit=full.time_unit,
    )

    with pytest.raises(SparseNativeError) as error:
        fit_sparse_multilevel_fpca(
            reduced,
            dimension="x",
            participant_column="participant_id",
            participant_components=1,
            trial_components=1,
            evaluation_grid=np.linspace(0.1, 0.9, 5),
            mean_bandwidth=0.4,
            total_covariance_bandwidth=0.5,
            between_covariance_bandwidth=0.5,
            noise_variance_method="fixed",
            measurement_error_variance=0.01,
        )
    assert error.value.code == "insufficient_participants"


def test_sparse_multilevel_requires_three_repeated_participants():
    full = _simulate_hierarchy(n_participants=4, trials_per_participant=2)
    # Keep both trials for p00/p01 and one trial for p02/p03.
    keep_ids = {"p00_t00", "p00_t01", "p01_t00", "p01_t01", "p02_t00", "p03_t00"}
    indices = [
        index
        for index, curve_id in enumerate(full.curve_ids)
        if curve_id in keep_ids
    ]
    reduced = IrregularTrajectorySet(
        time=tuple(full.time[index] for index in indices),
        values=tuple(full.values[index] for index in indices),
        curve_ids=tuple(full.curve_ids[index] for index in indices),
        dimension_names=full.dimension_names,
        metadata=full.metadata.iloc[indices].reset_index(drop=True),
        coordinate_system=full.coordinate_system,
        time_unit=full.time_unit,
    )

    with pytest.raises(SparseNativeError) as error:
        fit_sparse_multilevel_fpca(
            reduced,
            dimension="x",
            participant_column="participant_id",
            participant_components=1,
            trial_components=1,
            evaluation_grid=np.linspace(0.1, 0.9, 5),
            mean_bandwidth=0.4,
            total_covariance_bandwidth=0.5,
            between_covariance_bandwidth=0.5,
            noise_variance_method="fixed",
            measurement_error_variance=0.01,
        )
    assert error.value.code == "insufficient_repeated_participants"


def test_sparse_multilevel_first_tranche_rejects_undeclared_weighting():
    trajectories = _simulate_hierarchy()

    with pytest.raises(ValueError, match="weighting must be 'observation'"):
        fit_sparse_multilevel_fpca(
            trajectories,
            dimension="x",
            participant_column="participant_id",
            participant_components=1,
            trial_components=1,
            evaluation_grid=np.linspace(0.1, 0.9, 5),
            mean_bandwidth=0.4,
            total_covariance_bandwidth=0.5,
            between_covariance_bandwidth=0.5,
            analysis_support_action="restrict",
            noise_variance_method="fixed",
            measurement_error_variance=0.01,
            weighting="participant",
        )


def test_sparse_multilevel_restrict_fails_if_a_trial_has_no_analysis_support():
    full = _simulate_hierarchy()
    times = list(full.time)
    values = list(full.values)
    times[0] = np.asarray([0.0, 0.01, 0.02])
    values[0] = np.zeros((3, 1), dtype=float)
    modified = IrregularTrajectorySet(
        time=tuple(times),
        values=tuple(values),
        curve_ids=full.curve_ids,
        dimension_names=full.dimension_names,
        metadata=full.metadata.copy(),
        coordinate_system=full.coordinate_system,
        time_unit=full.time_unit,
    )

    with pytest.raises(SparseNativeError) as error:
        fit_sparse_multilevel_fpca(
            modified,
            dimension="x",
            participant_column="participant_id",
            participant_components=1,
            trial_components=1,
            evaluation_grid=np.linspace(0.1, 0.9, 5),
            mean_bandwidth=0.4,
            total_covariance_bandwidth=0.5,
            between_covariance_bandwidth=0.5,
            analysis_support_action="restrict",
            noise_variance_method="fixed",
            measurement_error_variance=0.01,
        )
    assert error.value.code == "curve_without_analysis_support"
