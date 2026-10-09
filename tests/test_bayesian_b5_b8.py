"""B5/B6/B8 provisional Bayesian research contracts; NOT scientific qualification."""
from __future__ import annotations

from hashlib import sha256
import json
import numpy as np
import pandas as pd
import pytest
from eyetrajectoriespy.types import TrajectorySet, IrregularTrajectorySet
from eyetrajectoriespy.bayesian import (
    BayesianFunctionalDraws, bayesian_credible_band,
    bayesian_functional_probability, bayesian_calibration_study,
    bayesian_prior_predictive_check, bayesian_posterior_predictive_check,
    bayesian_predictive_comparison, export_bayesian_analysis,
    fit_bayesian_sparse_score_baseline, fit_bayesian_function_on_scalar,
)


def posterior_fixture(seed: int = 42) -> BayesianFunctionalDraws:
    rng = np.random.default_rng(seed)
    time = np.linspace(0, 1, 17)
    val = .5+np.sin(np.pi*time)[None, None, :, None]*.2
    samples = val + rng.normal(scale=.05, size=(2, 60, len(time), 2))
    return BayesianFunctionalDraws(
        samples, time, ("x", "y"), provenance={"synthetic": True}
    )


def test_b5_posterior_contract_and_immutable_snapshot():
    x = posterior_fixture()
    assert x.values.shape == (2, 60, 17, 2)
    assert x.sample_count == 120
    with pytest.raises(ValueError):
        x.values[0, 0, 0, 0] = 100
    with pytest.raises(ValueError, match="strictly increasing"):
        BayesianFunctionalDraws(x.values, x.time[::-1], ("x", "y"))
    with pytest.raises(ValueError, match="must all be finite"):
        data = x.values.copy()
        data[0, 0, 0, 0] = np.nan
        BayesianFunctionalDraws(data, x.time, ("x", "y"))


def test_pointwise_vs_gridwise_simultaneous_posterior_content():
    x = posterior_fixture()
    a = bayesian_credible_band(x, coverage=.9)
    b = bayesian_credible_band(x, coverage=.9, simultaneous=True)
    assert a.scope == "posterior_pointwise_equal_tailed"
    assert b.scope == "posterior_gridwise_joint_all_time_and_dimensions"
    draws = x.values.reshape(-1, 17, 2)
    simultaneous_inside = np.all(
        (draws >= b.lower) & (draws <= b.upper), axis=(1, 2)
    )
    assert simultaneous_inside.mean() >= .89
    assert not b.evidence["frequentist_coverage_qualified"]
    assert not b.evidence["continuous_time_simultaneity"]
    with pytest.raises(ValueError, match="coverage"):
        bayesian_credible_band(x, coverage=1)


def test_b5_posterior_event_and_no_p_value_conflation():
    x = posterior_fixture()
    p = bayesian_functional_probability(
        x, event="integrated_mean_above",
        threshold=.5, dimension="x",
    )
    assert .95 <= p["posterior_probability"] <= 1
    assert p["conditional_posterior_event_probability_not_p_value"]
    assert p["naive_monte_carlo_se_ignores_chain_autocorrelation"]
    with pytest.raises(ValueError, match="event"):
        bayesian_functional_probability(x, event="significant", threshold=.1, dimension="x")


def test_b5_prior_posterior_predictive_checks_preserve_provenance():
    rng = np.random.default_rng(25)
    obs = rng.normal(size=(5, 12, 2))
    pred = obs[None]+rng.normal(scale=.1, size=(32, 5, 12, 2))
    for fn, origin in (
        (bayesian_prior_predictive_check, "prior_predictive"),
        (bayesian_posterior_predictive_check, "posterior_predictive"),
    ):
        data = fn(pred, obs, statistic="pointwise_sd")
        assert data.source.tolist() == [origin] * 2
        assert len(data) == 2
        assert not data.scientific_calibration_qualified.any()
    with pytest.raises(ValueError, match="matching"):
        bayesian_prior_predictive_check(pred[:, :-1], obs)


def test_b5_sbc_rank_histogram_and_tie_seed():
    rng = np.random.default_rng(95)
    truth = rng.normal(size=24)
    posterior = rng.normal(size=(24, 99))
    frame, e = bayesian_calibration_study(
        truth, posterior, bins=10, random_state=99,
    )
    again, e2 = bayesian_calibration_study(
        truth, posterior, bins=10, random_state=99,
    )
    pd.testing.assert_frame_equal(frame, again)
    assert frame["count"].sum() == 24
    assert e["sbc_uniformity_qualified"] is False
    assert not e2["actual_prior_likelihood_sampling_verified"]
    with pytest.raises(ValueError, match="posterior"):
        bayesian_calibration_study(truth, posterior[:10])


def test_b5_heldout_predictive_no_training_leakage():
    rng = np.random.default_rng(56)
    observed = rng.normal(size=(3, 12, 2))
    draws = observed[None]+rng.normal(size=(30, 3, 12, 2)) * .1
    frame = bayesian_predictive_comparison(
        observed, draws, noise_sd=.1,
        holdout_units=["P1", "P2", "P3"], train_units=["P4", "P5"],
    )
    assert np.isfinite(frame.conditional_pointwise_log_score).all()
    assert not frame.joint_curve_predictive_density_verified.any()
    with pytest.raises(ValueError, match="disjoint"):
        bayesian_predictive_comparison(
            observed, draws, noise_sd=.1,
            holdout_units=["P1", "P2", "P3"], train_units=["P2", "P4"],
        )


def test_b5_reproducible_portable_export(tmp_path):
    posterior = posterior_fixture()
    outcome = export_bayesian_analysis(
        posterior, tmp_path/"example",
        model_name="known_synthetic_truth",
        priors={"beta_sd": 2.0},
        diagnostics={"rhat": "not_available"},
    )
    fromfile = json.loads((tmp_path/"example.json").read_text())
    assert sha256((tmp_path/"example.npz").read_bytes()).hexdigest() == outcome["sha256_npz"]
    assert fromfile["production_inference_qualified"] is False
    with np.load(outcome["npz"], allow_pickle=False) as saved:
        np.testing.assert_array_equal(saved["draws"], posterior.values)
        np.testing.assert_array_equal(saved["time"], posterior.time)
        assert saved["dimension_names"].tolist() == ["x", "y"]
    with pytest.raises(ValueError, match="priors"):
        export_bayesian_analysis(posterior, tmp_path/"fail",
                                 model_name="bad", priors={}, diagnostics={})


def sparse_fixture():
    rng = np.random.default_rng(181)
    grid = np.linspace(0, 1, 51)
    mean = .5+.2*np.sin(np.pi*grid)
    components = np.array([np.sqrt(2)*np.sin(np.pi*grid)])
    times = tuple(np.sort(rng.uniform(0, 1, 12)) for i in range(15))
    true_scores = rng.normal(scale=.3, size=15)
    values = tuple((
        np.interp(t, grid, mean)
        + np.interp(t, grid, components[0])*true_scores[i]
        + rng.normal(scale=.03, size=len(t))
    )[:,None] for i,t in enumerate(times))
    data = IrregularTrajectorySet(
        time=times, values=values,
        curve_ids=tuple(f"P{i}" for i in range(15)),
        dimension_names=("x",), coordinate_system="normalized",
        time_unit="s",
    )
    return data, grid, mean, components, true_scores


def test_b6_analytic_sparse_conditional_score_posterior_is_finite_and_sensitive():
    gaze, grid, mean, basis, scores = sparse_fixture()
    fit = fit_bayesian_sparse_score_baseline(
        gaze, dimension="x", evaluation_grid=grid,
        population_mean=mean, population_components=basis,
        score_prior_variances=np.array([.09]), noise_sd=.03,
        n_draws=200, random_state=11,
    )
    assert fit.posterior_score_mean.shape == (15, 1)
    assert fit.posterior_score_covariance.shape == (15, 1, 1)
    assert fit.conditional_latent_trajectory_draws.shape == (15, 200, 51)
    assert np.mean(np.abs(fit.posterior_score_mean[:,0]-scores)) < .1
    assert not fit.evidence["population_parameter_uncertainty"]
    assert not fit.evidence["full_native_bayesian_fpca_implemented"]
    second = fit_bayesian_sparse_score_baseline(
        gaze, dimension="x", evaluation_grid=grid,
        population_mean=mean, population_components=basis,
        score_prior_variances=np.array([.09]), noise_sd=.03,
        n_draws=200, random_state=11,
    )
    np.testing.assert_array_equal(fit.posterior_score_draws, second.posterior_score_draws)
    with pytest.raises(ValueError, match="noise_sd"):
        fit_bayesian_sparse_score_baseline(
            gaze, dimension="x", evaluation_grid=grid, population_mean=mean,
            population_components=basis, score_prior_variances=np.array([.09]),
            noise_sd=0,
        )


def function_on_scalar_fixture():
    rng = np.random.default_rng(2026)
    t = np.linspace(0, 1, 29)
    n=42
    condition = np.r_[np.zeros(n//2), np.ones(n//2)]
    effect = .36*np.sin(np.pi*t)
    data = .48 + condition[:,None]*effect[None,:] + rng.normal(size=(n,len(t))) * .04
    gaze = TrajectorySet(
        time=t, values=data[:,:,None], curve_ids=tuple(f"u{i}" for i in range(n)),
        dimension_names=("x",), time_unit="normalized",
        metadata=pd.DataFrame({"participant_id": [f"p{i}" for i in range(n)]}),
        coordinate_system="normalized",
    )
    design = pd.DataFrame({"curve_id":gaze.curve_ids,
                           "intercept":np.ones(n), "condition":condition})
    return gaze, design, effect


def test_b8_conjugate_function_on_scalar_effect_recovery_and_bands():
    gaze, design, truth = function_on_scalar_fixture()
    fit = fit_bayesian_function_on_scalar(
        gaze, design=design,
        predictors=("intercept","condition"),
        noise_sd=.04, prior_sd=2, n_basis=6,
        n_draws=300, random_state=190,
    )
    assert fit.fitted_mean.shape == gaze.values.shape
    assert fit.posterior_coefficient_draws.shape == (300,2,29,1)
    predicted = fit.coefficient_posterior("condition")
    band = bayesian_credible_band(predicted, simultaneous=True)
    assert band.lower.shape == (29,1)
    assert np.mean(np.abs(fit.posterior_mean_coefficients[1,:,0]-truth)) < .045
    assert fit.evidence["posterior_population_regression_coefficient_uncertainty"] is True
    assert fit.evidence["observation_noise_uncertainty_included"] is False
    assert fit.evidence["serial_residual_dependence_modelled"] is False
    with pytest.raises(KeyError):
        fit.coefficient_posterior("unobserved")


def test_b8_rejects_pseudoreplication_and_bad_design():
    gaze, design, _ = function_on_scalar_fixture()
    wrong = design.iloc[::-1].reset_index(drop=True)
    with pytest.raises(ValueError, match="exactly match"):
        fit_bayesian_function_on_scalar(
            gaze, design=wrong, predictors=("intercept","condition"), noise_sd=.04,
        )
    md = gaze.metadata.copy()
    md.iloc[1, md.columns.get_loc("participant_id")] = "p0"
    repeated = TrajectorySet(
        gaze.time, gaze.values, gaze.curve_ids, gaze.dimension_names,
        metadata=md, coordinate_system=gaze.coordinate_system,
        time_unit=gaze.time_unit,
    )
    with pytest.raises(ValueError, match="repeated participants"):
        fit_bayesian_function_on_scalar(
            repeated, design=design,
            predictors=("intercept","condition"), noise_sd=.04,
        )
    with pytest.raises(ValueError, match="noise_sd"):
        fit_bayesian_function_on_scalar(
            gaze, design=design,
            predictors=("intercept","condition"), noise_sd=0,
        )
