import numpy as np
import pandas as pd
import pytest
from dataclasses import replace

from eyetrajectoriespy import (
    FunctionalMixedEffectsResidualDiagnosticsResult,
    TrajectorySet,
    compare_functional_mixed_effects_residual_diagnostics,
    fit_functional_mixed_effects_regression,
    functional_mixed_effects_residual_diagnostic_frame,
    functional_mixed_effects_residual_diagnostics,
    functional_mixed_effects_residual_pair_frame,
    functional_mixed_effects_residual_reporting_text,
    plot_functional_mixed_effects_residual_acf,
    plot_functional_mixed_effects_residual_variogram,
)


def _repeated_functional_data(seed=2026):
    rng = np.random.default_rng(seed)
    n_participants = 12
    trials_per_participant = 3
    time = np.linspace(0.0, 1.0, 9)

    participants = np.repeat(
        [f"P{i:02d}" for i in range(n_participants)],
        trials_per_participant,
    )
    condition = np.tile(np.array([0.0, 1.0, 0.5]), n_participants)
    intercept = 0.20 + 0.15 * time
    condition_effect = 0.15 + 0.40 * time
    covariance = np.array([[0.030, 0.004], [0.004, 0.020]])
    random_basis_coefficients = rng.multivariate_normal(
        np.zeros(2),
        covariance,
        size=n_participants,
    )
    linear_basis = np.column_stack([1.0 - time, time])

    values = []
    curve_ids = []
    for participant_index in range(n_participants):
        random_function = (
            random_basis_coefficients[participant_index] @ linear_basis.T
        )
        for trial_index in range(trials_per_participant):
            curve_index = (
                participant_index * trials_per_participant + trial_index
            )
            curve_ids.append(f"C{curve_index:03d}")
            response = (
                intercept
                + condition[curve_index] * condition_effect
                + random_function
                + rng.normal(0.0, 0.04, size=time.size)
            )
            values.append(response[:, None])

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


def _fit(seed=2026):
    trajectories, design = _repeated_functional_data(seed)
    return fit_functional_mixed_effects_regression(
        trajectories,
        design,
        predictors=("condition",),
        participant_column="participant_id",
        dimension="metric",
        fixed_basis_size=2,
        random_basis_size=2,
        spline_degree=1,
        reml=True,
        method="lbfgs",
        maxiter=500,
    )


def test_residual_diagnostics_match_manual_trial_quantities():
    fit = _fit()
    diagnostics = functional_mixed_effects_residual_diagnostics(
        fit,
        max_lag=3,
    )

    assert isinstance(
        diagnostics,
        FunctionalMixedEffectsResidualDiagnosticsResult,
    )
    assert diagnostics.max_lag == 3
    assert diagnostics.n_curves == fit.n_curves
    assert diagnostics.n_participants == fit.n_participants
    assert len(diagnostics.trial_diagnostics) == fit.n_curves * 4
    assert len(diagnostics.participant_diagnostics) == fit.n_participants * 4
    assert len(diagnostics.overall_diagnostics) == 4

    residual = fit.residual_functions[0]
    centered = residual - np.mean(residual)
    variance = np.mean(centered**2)
    lag = 1
    manual_covariance = np.mean(centered[:-lag] * centered[lag:])
    manual_correlation = manual_covariance / variance
    manual_semivariance = 0.5 * np.mean((residual[lag:] - residual[:-lag]) ** 2)

    row = diagnostics.trial_diagnostics.loc[
        (diagnostics.trial_diagnostics["curve_id"] == fit.source_curve_ids[0])
        & (diagnostics.trial_diagnostics["lag_index"] == lag)
    ].iloc[0]

    assert row["n_pairs"] == fit.time.size - lag
    assert row["lag_time_mean"] == pytest.approx(0.125)
    assert row["lag_time_min"] == pytest.approx(0.125)
    assert row["lag_time_max"] == pytest.approx(0.125)
    assert row["autocovariance"] == pytest.approx(manual_covariance)
    assert row["autocorrelation"] == pytest.approx(manual_correlation)
    assert row["semivariance"] == pytest.approx(manual_semivariance)

    contract = diagnostics.provenance[
        "functional_mixed_effects_residual_diagnostics"
    ]
    assert contract["automatic_lag_selection"] is False
    assert contract["physical_lag_binning"] is False
    assert contract["automatic_covariance_structure_selection"] is False
    assert contract["automatic_ar1_selection"] is False
    assert contract["automatic_trial_random_effect_selection"] is False


def test_residual_frames_pair_audit_plots_and_reporting():
    fit = _fit(seed=77)
    diagnostics = functional_mixed_effects_residual_diagnostics(
        fit,
        max_lag=2,
    )

    trial = functional_mixed_effects_residual_diagnostic_frame(
        diagnostics,
        level="trial",
        curve_id=fit.source_curve_ids[0],
    )
    participant = functional_mixed_effects_residual_diagnostic_frame(
        diagnostics,
        level="participant",
        participant_id=fit.participant_ids[0],
    )
    overall = functional_mixed_effects_residual_diagnostic_frame(
        diagnostics,
        level="overall",
    )
    pairs = functional_mixed_effects_residual_pair_frame(
        diagnostics,
        lag_index=2,
        curve_id=fit.source_curve_ids[0],
    )

    assert len(trial) == 3
    assert len(participant) == 3
    assert len(overall) == 3
    assert len(pairs) == fit.time.size - 2
    np.testing.assert_allclose(pairs["physical_lag"], 0.25)

    centered = fit.residual_functions[0] - np.mean(fit.residual_functions[0])
    np.testing.assert_allclose(
        pairs["centered_product"].to_numpy(),
        centered[:-2] * centered[2:],
    )

    ax_acf = plot_functional_mixed_effects_residual_acf(
        diagnostics,
        level="overall",
    )
    ax_variogram = plot_functional_mixed_effects_residual_variogram(
        diagnostics,
        level="trial",
        curve_id=fit.source_curve_ids[0],
    )
    assert ax_acf.get_ylabel() == "Residual autocorrelation"
    assert ax_variogram.get_ylabel() == "Residual semivariance"

    text = functional_mixed_effects_residual_reporting_text(diagnostics)
    assert "conditional residual functions" in text
    assert "no physical-lag binning" in text
    assert "do not automatically select AR(1)" in text


def test_zero_variance_trial_is_retained_and_flagged():
    fit = _fit(seed=123)
    residuals = fit.residual_functions.copy()
    residuals[0] = 0.0
    modified = replace(fit, residual_functions=residuals)

    diagnostics = functional_mixed_effects_residual_diagnostics(
        modified,
        max_lag=2,
    )
    first = diagnostics.trial_diagnostics.loc[
        diagnostics.trial_diagnostics["curve_id"] == fit.source_curve_ids[0]
    ]

    assert first["zero_residual_variance"].all()
    assert first["autocorrelation"].isna().all()
    assert len(first) == 3
    assert (
        diagnostics.overall_diagnostics["n_trials_acf_defined"]
        == fit.n_curves - 1
    ).all()


def test_residual_comparison_is_descriptive_and_exact_for_identical_fit():
    fit = _fit(seed=98)
    comparison = compare_functional_mixed_effects_residual_diagnostics(
        fit,
        fit,
        max_lag=3,
        reference_label="before",
        comparison_label="after",
    )

    assert (comparison["reference_label"] == "before").all()
    assert (comparison["comparison_label"] == "after").all()
    np.testing.assert_allclose(comparison["delta_autocovariance"], 0.0)
    np.testing.assert_allclose(comparison["delta_autocorrelation"], 0.0)
    np.testing.assert_allclose(comparison["delta_semivariance"], 0.0)


def test_residual_diagnostics_fail_closed():
    fit = _fit(seed=42)

    with pytest.raises(ValueError, match="at least 1"):
        functional_mixed_effects_residual_diagnostics(fit, max_lag=0)
    with pytest.raises(ValueError, match="smaller than"):
        functional_mixed_effects_residual_diagnostics(
            fit,
            max_lag=fit.time.size,
        )
    with pytest.raises(TypeError, match="integer"):
        functional_mixed_effects_residual_diagnostics(fit, max_lag=1.5)

    diagnostics = functional_mixed_effects_residual_diagnostics(
        fit,
        max_lag=2,
    )
    with pytest.raises(ValueError, match="curve_id is required"):
        plot_functional_mixed_effects_residual_acf(
            diagnostics,
            level="trial",
        )
    with pytest.raises(ValueError, match="participant_id is required"):
        plot_functional_mixed_effects_residual_variogram(
            diagnostics,
            level="participant",
        )
    with pytest.raises(KeyError, match="Unknown curve_id"):
        functional_mixed_effects_residual_pair_frame(
            diagnostics,
            lag_index=1,
            curve_id="missing",
        )
