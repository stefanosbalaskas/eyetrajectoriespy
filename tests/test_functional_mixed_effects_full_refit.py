import numpy as np
import pandas as pd
import pytest

from eyetrajectoriespy import (
    FunctionalMixedEffectsFullRefitBootstrapResult,
    TrajectorySet,
    bootstrap_functional_mixed_effects_coefficients,
    bootstrap_functional_mixed_effects_full_refit,
    compare_functional_mixed_effects_bootstraps,
    fit_functional_mixed_effects_regression,
    functional_mixed_effects_full_refit_audit_frame,
    functional_mixed_effects_simultaneous_bands,
    functional_mixed_effects_variance_bootstrap_frame,
    plot_functional_mixed_effects_bootstrap_comparison,
)


def _data(*, seed=460, n_participants=12, random_slope=False):
    rng = np.random.default_rng(seed)
    trials_per_participant = 3
    time = np.linspace(0.0, 1.0, 6)
    basis = np.column_stack([1.0 - time, time])
    participants = np.repeat(
        [f"P{i:03d}" for i in range(n_participants)],
        trials_per_participant,
    )
    condition = np.tile(np.array([-0.5, 0.0, 0.5]), n_participants)
    beta0 = 0.25 + 0.10 * time
    beta1 = 0.15 + 0.25 * time

    if random_slope:
        covariance = np.array(
            [
                [0.030, 0.004, 0.006, 0.001],
                [0.004, 0.020, 0.001, 0.005],
                [0.006, 0.001, 0.015, 0.002],
                [0.001, 0.005, 0.002, 0.012],
            ]
        )
        random_coefficients = rng.multivariate_normal(
            np.zeros(4),
            covariance,
            size=n_participants,
        )
        random_intercepts = random_coefficients[:, :2] @ basis.T
        random_slopes = random_coefficients[:, 2:] @ basis.T
    else:
        covariance = np.array([[0.030, 0.004], [0.004, 0.020]])
        random_coefficients = rng.multivariate_normal(
            np.zeros(2),
            covariance,
            size=n_participants,
        )
        random_intercepts = random_coefficients @ basis.T
        random_slopes = np.zeros_like(random_intercepts)

    values = []
    curve_ids = []
    for participant_index in range(n_participants):
        for trial_index in range(trials_per_participant):
            row = participant_index * trials_per_participant + trial_index
            response = (
                beta0
                + condition[row] * beta1
                + random_intercepts[participant_index]
                + condition[row] * random_slopes[participant_index]
                + rng.normal(0.0, 0.035, size=time.size)
            )
            values.append(response[:, None])
            curve_ids.append(f"C{row:04d}")

    trajectories = TrajectorySet(
        time=time,
        values=np.asarray(values),
        curve_ids=tuple(curve_ids),
        dimension_names=("metric",),
        metadata=pd.DataFrame({"participant_id": participants}),
        coordinate_system="unknown",
        time_unit="s",
    )
    design = pd.DataFrame(
        {
            "curve_id": trajectories.curve_ids,
            "condition": condition,
        }
    )
    return trajectories, design


def _fit(*, seed=460, random_slope=False):
    trajectories, design = _data(
        seed=seed,
        random_slope=random_slope,
    )
    return fit_functional_mixed_effects_regression(
        trajectories,
        design,
        predictors=("condition",),
        participant_column="participant_id",
        dimension="metric",
        fixed_basis_size=2,
        random_basis_size=2,
        random_slope_predictor=(
            "condition" if random_slope else None
        ),
        spline_degree=1,
        reml=True,
        method="lbfgs",
        maxiter=1000,
    )


@pytest.fixture(scope="module")
def intercept_full_refit():
    fit = _fit(seed=461, random_slope=False)
    boot = bootstrap_functional_mixed_effects_full_refit(
        fit,
        n_bootstrap=20,
        random_state=46,
    )
    return fit, boot


def test_full_refit_bootstrap_refits_variance_components_and_retains_audit(
    intercept_full_refit,
):
    fit, boot = intercept_full_refit

    assert isinstance(
        boot,
        FunctionalMixedEffectsFullRefitBootstrapResult,
    )
    assert boot.n_bootstrap == 20
    assert boot.n_participants == fit.n_participants
    assert boot.bootstrap_coefficient_functions.shape == (
        20,
        fit.n_coefficients,
        fit.time.size,
    )
    assert boot.random_effect_covariances.shape == (
        20,
        fit.random_effect_dimension,
        fit.random_effect_dimension,
    )
    assert boot.residual_variances.shape == (20,)
    assert np.all(np.isfinite(boot.residual_variances))
    assert np.std(boot.residual_variances) > 0
    assert np.all(boot.convergence_flags)

    provenance = boot.provenance[
        "functional_mixed_effects_full_refit_bootstrap"
    ]
    assert provenance["variance_components_refit"] is True
    assert provenance["fixed_effects_refit"] is True
    assert provenance["random_effect_covariance_refit"] is True
    assert provenance["residual_variance_refit"] is True
    assert provenance["failed_replicate_policy"] == "raise"
    assert provenance["preprocessing_repeated"] is False
    assert provenance["predictors_reselected"] is False
    assert provenance["optimizer_reselected"] is False

    audit = functional_mixed_effects_full_refit_audit_frame(boot)
    assert len(audit) == 20 * fit.n_participants
    duplicate_sources = audit[
        audit.duplicated(
            ["bootstrap_replicate", "source_participant_id"],
            keep=False,
        )
    ]
    assert not duplicate_sources.empty
    grouped = duplicate_sources.groupby(
        ["bootstrap_replicate", "source_participant_id"]
    )
    assert all(
        group["bootstrap_participant_id"].nunique() == len(group)
        for _, group in grouped
    )


def test_variance_bootstrap_frame_and_full_refit_band_are_explicit(
    intercept_full_refit,
):
    fit, boot = intercept_full_refit

    frame = functional_mixed_effects_variance_bootstrap_frame(boot)
    assert len(frame) == 20
    assert {
        "residual_variance",
        "covariance_min_eigenvalue",
        "covariance_max_eigenvalue",
        "covariance_condition_number",
        "boundary_fit",
        "singular_fit",
        "converged",
    } <= set(frame.columns)

    band = functional_mixed_effects_simultaneous_bands(
        boot,
        confidence_level=0.95,
        simultaneous_scope="coefficient",
    )
    assert band.bootstrap is boot
    assert band.provenance[
        "functional_mixed_effects_simultaneous_bands"
    ]["variance_components_refit"] is True
    assert np.all(band.lower < fit.coefficient_functions)
    assert np.all(fit.coefficient_functions < band.upper)


def test_full_refit_random_slope_retains_covariance_blocks():
    fit = _fit(seed=462, random_slope=True)
    boot = bootstrap_functional_mixed_effects_full_refit(
        fit,
        n_bootstrap=20,
        random_state=47,
    )

    assert boot.random_slope_covariances is not None
    assert boot.random_intercept_slope_covariances is not None
    assert boot.random_slope_covariances.shape == (
        20,
        fit.random_basis_size,
        fit.random_basis_size,
    )
    assert boot.random_intercept_slope_covariances.shape == (
        20,
        fit.random_basis_size,
        fit.random_basis_size,
    )
    frame = functional_mixed_effects_variance_bootstrap_frame(boot)
    assert "random_slope_covariance_trace" in frame.columns
    assert "intercept_slope_cross_covariance_frobenius" in frame.columns


def test_compare_fixed_covariance_and_full_refit_band_widths(
    intercept_full_refit,
):
    fit, full = intercept_full_refit
    fixed = bootstrap_functional_mixed_effects_coefficients(
        fit,
        n_bootstrap=100,
        random_state=46,
    )

    comparison = compare_functional_mixed_effects_bootstraps(
        fixed,
        full,
        confidence_level=0.95,
        simultaneous_scope="coefficient",
    )
    assert len(comparison) == fit.n_coefficients * fit.time.size
    ratio = comparison[
        "full_refit_to_fixed_covariance_width_ratio"
    ].to_numpy()
    assert np.all(np.isfinite(ratio))
    assert np.all(ratio > 0)

    ax = plot_functional_mixed_effects_bootstrap_comparison(
        comparison,
        coefficient="condition",
    )
    assert "condition" in ax.get_title()
    assert ax.get_ylabel() == (
        "Full-refit / fixed-covariance band width"
    )


def test_full_refit_bootstrap_controls_and_type_guards(
    intercept_full_refit,
):
    fit, boot = intercept_full_refit

    with pytest.raises(ValueError, match="at least 20"):
        bootstrap_functional_mixed_effects_full_refit(
            fit,
            n_bootstrap=19,
        )
    with pytest.raises(TypeError, match="n_bootstrap"):
        bootstrap_functional_mixed_effects_full_refit(
            fit,
            n_bootstrap=True,
        )
    with pytest.raises(TypeError, match="random_state"):
        bootstrap_functional_mixed_effects_full_refit(
            fit,
            n_bootstrap=20,
            random_state=True,
        )
    with pytest.raises(TypeError):
        functional_mixed_effects_full_refit_audit_frame(object())
    with pytest.raises(TypeError):
        functional_mixed_effects_variance_bootstrap_frame(object())
    with pytest.raises(TypeError):
        compare_functional_mixed_effects_bootstraps(
            object(),
            boot,
        )


def test_fixed_covariance_bootstrap_provenance_remains_unchanged(
    intercept_full_refit,
):
    fit, _ = intercept_full_refit
    fixed = bootstrap_functional_mixed_effects_coefficients(
        fit,
        n_bootstrap=100,
        random_state=48,
    )
    assert fixed.provenance[
        "functional_mixed_effects_bootstrap"
    ]["variance_components_refit"] is False
    band = functional_mixed_effects_simultaneous_bands(fixed)
    assert band.provenance[
        "functional_mixed_effects_simultaneous_bands"
    ]["variance_components_refit"] is False
