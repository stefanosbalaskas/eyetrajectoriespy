import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from eyetrajectoriespy import (
    TrajectorySet,
    cross_validate_fpca_regression,
    fpca_nested_regression_cv_reporting_text,
    fpca_regression_cv_reporting_text,
    nested_cross_validate_fpca_regression,
    plot_fpca_regression_cv,
    plot_nested_fpca_regression_cv,
    select_fpca_regression_components,
    simulate_planar_trajectories,
    summarise_fpca_regression_cv,
)


def repeated_sample():
    return simulate_planar_trajectories(
        n_participants=18,
        trials_per_participant=2,
        n_time=41,
        random_state=31,
    )


def gaussian_outcome(gaze, seed=4):
    rng = np.random.default_rng(seed)
    signal = gaze.values[:, :, 0].mean(axis=1)
    return 3.0 * signal + rng.normal(scale=0.03, size=gaze.n_curves)


def test_grouped_gaussian_predictive_cv_is_leakage_safe_and_deterministic():
    gaze = repeated_sample()
    outcome = gaussian_outcome(gaze)
    first = cross_validate_fpca_regression(
        gaze,
        outcome,
        candidate_components=[3, 1, 2],
        n_splits=6,
        scaling="dimension_sd",
        cv_unit="group",
        group_column="participant_id",
        random_state=8,
    )
    second = cross_validate_fpca_regression(
        gaze,
        outcome,
        candidate_components=[1, 2, 3],
        n_splits=6,
        scaling="dimension_sd",
        cv_unit="group",
        group_column="participant_id",
        random_state=8,
    )

    assert first.component_counts == (1, 2, 3)
    assert np.allclose(first.fold_losses["loss"], second.fold_losses["loss"])
    assert (first.assignments.groupby("group")["fold"].nunique() == 1).all()
    assert first.provenance["fit_fpca_inside_fold"] is True
    assert first.provenance["fit_regression_inside_fold"] is True
    assert first.provenance["group_leakage_prevented"] is True
    assert np.isfinite(first.predictions["prediction"]).all()

    summary = summarise_fpca_regression_cv(first)
    assert set(summary.columns) == {
        "n_components",
        "mean_loss",
        "sd_loss",
        "n_folds",
        "se_loss",
    }
    assert select_fpca_regression_components(first, rule="minimum") in {1, 2, 3}
    assert select_fpca_regression_components(first, rule="one_se") in {1, 2, 3}


def test_gaussian_mae_with_numeric_covariates():
    gaze = repeated_sample()
    rng = np.random.default_rng(9)
    covariates = pd.DataFrame(
        {
            "age_z": rng.normal(size=gaze.n_curves),
            "trial_load": rng.normal(size=gaze.n_curves),
        }
    )
    outcome = gaussian_outcome(gaze) + 0.2 * covariates["age_z"].to_numpy()

    result = cross_validate_fpca_regression(
        gaze,
        outcome,
        candidate_components=[1, 2],
        family="gaussian",
        loss="mae",
        covariates=covariates,
        n_splits=4,
        scaling="dimension_sd",
        random_state=5,
    )
    assert result.loss == "mae"
    assert (result.fold_losses["loss"] >= 0).all()
    assert result.provenance["covariates"] == ["age_z", "trial_load"]


def test_binomial_log_loss_and_brier_use_probabilities():
    gaze = simulate_planar_trajectories(
        n_participants=60,
        trials_per_participant=1,
        n_time=41,
        random_state=17,
    )
    signal = gaze.values[:, :, 0].mean(axis=1)
    centered = (signal - signal.mean()) / signal.std()
    rng = np.random.default_rng(22)
    probability = 1.0 / (1.0 + np.exp(-0.8 * centered))
    outcome = rng.binomial(1, probability).astype(float)

    logloss = cross_validate_fpca_regression(
        gaze,
        outcome,
        candidate_components=[1, 2],
        family="binomial",
        loss="log_loss",
        n_splits=5,
        random_state=12,
    )
    brier = cross_validate_fpca_regression(
        gaze,
        outcome,
        candidate_components=[1, 2],
        family="binomial",
        loss="brier",
        n_splits=5,
        random_state=12,
    )
    assert (logloss.fold_losses["loss"] >= 0).all()
    assert ((brier.fold_losses["loss"] >= 0) & (brier.fold_losses["loss"] <= 1)).all()
    assert (
        (logloss.predictions["prediction"] >= 0)
        & (logloss.predictions["prediction"] <= 1)
    ).all()


def test_nested_grouped_cv_is_deterministic_and_outer_fold_is_unseen():
    gaze = repeated_sample()
    outcome = gaussian_outcome(gaze, seed=11)

    first = nested_cross_validate_fpca_regression(
        gaze,
        outcome,
        candidate_components=[1, 2, 3],
        outer_splits=5,
        inner_splits=4,
        selection_rule="one_se",
        scaling="dimension_sd",
        cv_unit="group",
        group_column="participant_id",
        random_state=101,
    )
    second = nested_cross_validate_fpca_regression(
        gaze,
        outcome,
        candidate_components=[1, 2, 3],
        outer_splits=5,
        inner_splits=4,
        selection_rule="one_se",
        scaling="dimension_sd",
        cv_unit="group",
        group_column="participant_id",
        random_state=101,
    )

    assert np.allclose(first.outer_folds["loss"], second.outer_folds["loss"])
    assert np.array_equal(
        first.outer_folds["selected_n_components"],
        second.outer_folds["selected_n_components"],
    )
    assert (first.predictions.groupby("group")["outer_fold"].nunique() == 1).all()
    assert first.provenance["outer_performance_unseen_by_inner_selection"] is True
    assert set(first.inner_summaries["outer_fold"]) == set(range(5))


def test_predictive_selection_contract_errors():
    gaze = repeated_sample()
    outcome = gaussian_outcome(gaze)

    with pytest.raises(ValueError):
        cross_validate_fpca_regression(gaze, outcome, candidate_components=[])
    with pytest.raises(TypeError):
        cross_validate_fpca_regression(gaze, outcome, candidate_components=[True])
    with pytest.raises(ValueError):
        cross_validate_fpca_regression(gaze, outcome, family="bad")
    with pytest.raises(ValueError):
        cross_validate_fpca_regression(gaze, outcome, loss="log_loss")
    with pytest.raises(ValueError):
        cross_validate_fpca_regression(
            gaze,
            (outcome > np.median(outcome)).astype(float),
            family="binomial",
            loss="rmse",
        )
    with pytest.raises(ValueError):
        cross_validate_fpca_regression(
            gaze,
            outcome,
            cv_unit="group",
            group_column=None,
        )
    with pytest.raises(TypeError):
        cross_validate_fpca_regression(
            gaze,
            outcome,
            covariates=[1] * gaze.n_curves,
        )
    with pytest.raises(ValueError, match="rank deficient"):
        cross_validate_fpca_regression(
            gaze,
            outcome,
            candidate_components=[1],
            covariates=pd.DataFrame(
                {
                    "a": np.ones(gaze.n_curves),
                    "b": np.ones(gaze.n_curves),
                }
            ),
            n_splits=3,
        )
    with pytest.raises(ValueError):
        select_fpca_regression_components(
            cross_validate_fpca_regression(
                gaze,
                outcome,
                candidate_components=[1],
                n_splits=3,
            ),
            rule="bad",
        )


def test_binomial_training_fold_without_both_classes_fails():
    gaze = simulate_planar_trajectories(
        n_participants=6,
        trials_per_participant=1,
        n_time=31,
        random_state=14,
    )
    outcome = np.array([0, 0, 1, 1, 1, 1], dtype=float)
    with pytest.raises(ValueError, match="both outcome classes"):
        cross_validate_fpca_regression(
            gaze,
            outcome,
            candidate_components=[1],
            family="binomial",
            loss="brier",
            n_splits=3,
            shuffle=False,
        )


def test_predictive_reporting_and_plots():
    gaze = repeated_sample()
    outcome = gaussian_outcome(gaze)

    cv = cross_validate_fpca_regression(
        gaze,
        outcome,
        candidate_components=[1, 2],
        n_splits=3,
        scaling="dimension_sd",
        cv_unit="group",
        group_column="participant_id",
    )
    text = fpca_regression_cv_reporting_text(cv, rule="one_se")
    assert "refitted inside every training fold" in text
    assert "parsimony heuristic" in text
    assert plot_fpca_regression_cv(cv) is not None

    nested = nested_cross_validate_fpca_regression(
        gaze,
        outcome,
        candidate_components=[1, 2],
        outer_splits=3,
        inner_splits=3,
        scaling="dimension_sd",
        cv_unit="group",
        group_column="participant_id",
    )
    nested_text = fpca_nested_regression_cv_reporting_text(nested)
    assert "outer folds were untouched by selection" in nested_text
    assert plot_nested_fpca_regression_cv(nested) is not None
    plt.close("all")
