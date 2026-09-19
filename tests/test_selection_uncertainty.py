import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from eyetrajectoriespy import (
    FPCACrossValidationResult,
    TrajectorySet,
    bootstrap_fpca_component_envelopes,
    cross_validate_fpca_reconstruction,
    fpca_component_envelope_reporting_text,
    fpca_cross_validation_reporting_text,
    plot_fpca_component_envelope,
    plot_fpca_cross_validation,
    select_fpca_components_cv,
    simulate_planar_trajectories,
    summarise_fpca_cross_validation,
)


def sample():
    return simulate_planar_trajectories(
        n_participants=10,
        trials_per_participant=3,
        n_time=41,
        random_state=19,
    )


def test_curve_cv_is_reproducible_and_sorts_candidate_counts():
    gaze = sample()
    first = cross_validate_fpca_reconstruction(
        gaze,
        candidate_components=[4, 1, 2, 3],
        n_splits=5,
        scaling="dimension_sd",
        random_state=7,
    )
    second = cross_validate_fpca_reconstruction(
        gaze,
        candidate_components=[1, 2, 3, 4],
        n_splits=5,
        scaling="dimension_sd",
        random_state=7,
    )
    assert first.component_counts == (1, 2, 3, 4)
    assert np.allclose(
        first.fold_errors["mean_integrated_rmse"],
        second.fold_errors["mean_integrated_rmse"],
    )
    assert len(first.assignments) == gaze.n_curves
    summary = summarise_fpca_cross_validation(first)
    assert list(summary["n_components"]) == [1, 2, 3, 4]
    assert np.isfinite(summary[["mean_rmse", "se_rmse"]]).all().all()


def test_group_cv_keeps_each_participant_in_one_test_fold():
    gaze = sample()
    result = cross_validate_fpca_reconstruction(
        gaze,
        candidate_components=[1, 2, 3],
        n_splits=5,
        scaling="dimension_sd",
        cv_unit="group",
        group_column="participant_id",
    )
    fold_counts = result.assignments.groupby("group")["fold"].nunique()
    assert (fold_counts == 1).all()
    assert result.assignments["group"].nunique() == 10
    assert len(result.assignments) == gaze.n_curves
    assert result.provenance["fit_inside_fold"] is True
    assert result.provenance["group_leakage_prevented"] is True


def test_selection_rules_are_explicit():
    rows = []
    for fold, value in enumerate([0.98, 1.04, 0.92, 0.98]):
        rows.append(
            {
                "fold": fold,
                "n_components": 1,
                "mean_integrated_rmse": value,
            }
        )
    for fold, value in enumerate([0.95, 1.05, 0.85, 0.95]):
        rows.append(
            {
                "fold": fold,
                "n_components": 2,
                "mean_integrated_rmse": value,
            }
        )
    for fold, value in enumerate([1.00, 1.10, 0.90, 1.00]):
        rows.append(
            {
                "fold": fold,
                "n_components": 3,
                "mean_integrated_rmse": value,
            }
        )
    result = FPCACrossValidationResult(
        fold_errors=pd.DataFrame(rows),
        assignments=pd.DataFrame(),
        component_counts=(1, 2, 3),
        cv_unit="curve",
        n_splits=4,
        group_column=None,
        scaling="none",
        random_state=0,
        provenance={},
    )
    assert select_fpca_components_cv(result, rule="minimum") == 2
    assert select_fpca_components_cv(result, rule="one_se") == 1
    with pytest.raises(ValueError):
        select_fpca_components_cv(result, rule="mystery")


def test_cross_validation_contract_errors():
    gaze = sample()
    with pytest.raises(ValueError):
        cross_validate_fpca_reconstruction(gaze, candidate_components=[])
    with pytest.raises(TypeError):
        cross_validate_fpca_reconstruction(gaze, candidate_components=[True])
    with pytest.raises(ValueError):
        cross_validate_fpca_reconstruction(gaze, candidate_components=[0, 1])
    with pytest.raises(ValueError):
        cross_validate_fpca_reconstruction(gaze, n_splits=1)
    with pytest.raises(ValueError):
        cross_validate_fpca_reconstruction(gaze, cv_unit="bad")
    with pytest.raises(ValueError):
        cross_validate_fpca_reconstruction(
            gaze,
            cv_unit="group",
            n_splits=3,
        )
    with pytest.raises(ValueError):
        cross_validate_fpca_reconstruction(
            gaze,
            cv_unit="group",
            group_column="missing",
            n_splits=3,
        )
    with pytest.raises(ValueError):
        cross_validate_fpca_reconstruction(
            gaze,
            candidate_components=[29],
            n_splits=5,
        )


def test_group_cross_validation_rejects_missing_group_values():
    gaze = sample()
    metadata = gaze.metadata.reset_index(drop=True).copy()
    metadata.loc[0, "participant_id"] = np.nan
    bad = TrajectorySet(
        gaze.time,
        gaze.values,
        gaze.curve_ids,
        gaze.dimension_names,
        metadata,
        gaze.coordinate_system,
        gaze.time_unit,
        gaze.provenance,
    )
    with pytest.raises(ValueError, match="missing"):
        cross_validate_fpca_reconstruction(
            bad,
            candidate_components=[1, 2],
            n_splits=3,
            cv_unit="group",
            group_column="participant_id",
        )


def test_bootstrap_component_envelopes_are_reproducible_and_ordered():
    gaze = sample()
    first = bootstrap_fpca_component_envelopes(
        gaze,
        n_bootstrap=12,
        n_components=3,
        scaling="dimension_sd",
        random_state=5,
    )
    second = bootstrap_fpca_component_envelopes(
        gaze,
        n_bootstrap=12,
        n_components=3,
        scaling="dimension_sd",
        random_state=5,
    )
    expected = (3, gaze.n_time, gaze.n_dimensions)
    assert first.lower.shape == expected
    assert first.median.shape == expected
    assert first.upper.shape == expected
    assert first.similarities.shape == (12, 3)
    assert np.all(first.lower <= first.median)
    assert np.all(first.median <= first.upper)
    assert np.all((first.similarities >= 0) & (first.similarities <= 1 + 1e-12))
    assert np.allclose(first.lower, second.lower)
    assert np.allclose(first.upper, second.upper)
    assert first.provenance["coverage_claim"] == "descriptive_pointwise_only"


def test_participant_bootstrap_envelope_and_contracts():
    gaze = sample()
    result = bootstrap_fpca_component_envelopes(
        gaze,
        n_bootstrap=8,
        n_components=2,
        scaling="dimension_sd",
        resample_unit="participant",
        participant_column="participant_id",
        level=0.90,
        random_state=8,
    )
    assert result.resampling_unit == "participant"
    assert result.level == pytest.approx(0.90)

    with pytest.raises(ValueError):
        bootstrap_fpca_component_envelopes(gaze, n_bootstrap=1)
    with pytest.raises(ValueError):
        bootstrap_fpca_component_envelopes(gaze, resample_unit="participant")
    with pytest.raises(ValueError):
        bootstrap_fpca_component_envelopes(gaze, resample_unit="bad")
    with pytest.raises(ValueError):
        bootstrap_fpca_component_envelopes(gaze, level=1.0)


def test_selection_uncertainty_reporting_and_plotting():
    gaze = sample()
    cv = cross_validate_fpca_reconstruction(
        gaze,
        candidate_components=[1, 2, 3],
        n_splits=3,
        scaling="dimension_sd",
        cv_unit="group",
        group_column="participant_id",
    )
    text = fpca_cross_validation_reporting_text(cv, rule="one_se")
    assert "refitted inside every training fold" in text
    assert "parsimony heuristic" in text
    assert plot_fpca_cross_validation(cv) is not None

    envelopes = bootstrap_fpca_component_envelopes(
        gaze,
        n_bootstrap=6,
        n_components=2,
        scaling="dimension_sd",
        random_state=1,
    )
    envelope_text = fpca_component_envelope_reporting_text(envelopes)
    assert "not simultaneous confidence bands" in envelope_text
    assert plot_fpca_component_envelope(
        envelopes,
        component=0,
        dimension="x",
    ) is not None
    with pytest.raises(IndexError):
        plot_fpca_component_envelope(envelopes, component=99)
    with pytest.raises(KeyError):
        plot_fpca_component_envelope(envelopes, dimension="z")
    plt.close("all")
