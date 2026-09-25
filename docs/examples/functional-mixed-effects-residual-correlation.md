# Functional mixed effects with serial residual covariance

This example shows the 0.49 workflow for fitting physical-time exponential
residual correlation and checking the model on the whitened residual scale.

## Fit the serial model

~~~python
from eyetrajectoriespy import fit_functional_mixed_effects_regression

serial_fit = fit_functional_mixed_effects_regression(
    trajectories,
    design,
    predictors=("condition",),
    participant_column="participant_id",
    trial_column="trial_id",
    trial_random_effect="functional_intercept",
    dimension="metric",
    fixed_basis_size=4,
    random_basis_size=3,
    trial_random_basis_size=3,
    residual_correlation="exponential",
    spline_degree=2,
    reml=True,
    method="lbfgs",
)
~~~

The residual model is

\[
\operatorname{Cov}
\left[\epsilon_{ij}(t),\epsilon_{ij}(s)\right]
=
\sigma^2
\exp\!\left(-\frac{|t-s|}{\phi}\right).
\]

`serial_fit.residual_correlation_parameter` is \(\widehat\phi\), in the same
physical time unit recorded by the trajectories.

## Inspect the covariance contract

~~~python
serial_fit.residual_correlation
serial_fit.residual_correlation_parameter_name
serial_fit.residual_correlation_parameter
serial_fit.residual_correlation_parameter_unit
serial_fit.residual_correlation_optimizer_bounds
serial_fit.residual_correlation_condition_number
serial_fit.residual_correlation_boundary_fit
~~~

A boundary flag should be reported rather than hidden or converted into an iid
fit.

## Diagnose raw residuals

~~~python
from eyetrajectoriespy import functional_mixed_effects_residual_diagnostics

raw = functional_mixed_effects_residual_diagnostics(
    serial_fit,
    max_lag=6,
    residual_scale="raw",
)
~~~

Raw residual correlation can remain visible because correlated residuals are
part of the fitted model.

## Diagnose whitened residuals

~~~python
white = functional_mixed_effects_residual_diagnostics(
    serial_fit,
    max_lag=6,
    residual_scale="whitened",
)

white.overall_diagnostics[
    ["lag_index", "lag_time_mean", "autocorrelation", "semivariance"]
]
~~~

Whitened ACF/variogram summaries are the more relevant residual-structure
diagnostic after fitting a serial covariance.

## Plot raw and whitened ACFs

~~~python
from eyetrajectoriespy import plot_functional_mixed_effects_residual_acf

plot_functional_mixed_effects_residual_acf(
    raw,
    level="overall",
)

plot_functional_mixed_effects_residual_acf(
    white,
    level="overall",
)
~~~

Do not interpret a non-flat raw ACF as evidence that the serial model failed.
Inspect whether important dependence remains after whitening.

## Regular-grid AR(1)

When the common grid is equally spaced, AR(1) is available explicitly:

~~~python
ar1_fit = fit_functional_mixed_effects_regression(
    trajectories_regular,
    design_regular,
    predictors=("condition",),
    participant_column="participant_id",
    dimension="metric",
    residual_correlation="ar1",
)
~~~

The fitted parameter is \(\widehat\rho\). Negative values are allowed. The same
call fails closed on an irregular grid.

## Full-refit participant bootstrap

~~~python
from eyetrajectoriespy import (
    bootstrap_functional_mixed_effects_full_refit,
    functional_mixed_effects_variance_bootstrap_frame,
)

boot = bootstrap_functional_mixed_effects_full_refit(
    serial_fit,
    n_bootstrap=1000,
    random_state=49,
)

variance_audit = functional_mixed_effects_variance_bootstrap_frame(boot)
~~~

Whole participants are resampled and their complete trial bundles travel with
them. Each replicate re-estimates the declared serial parameter together with
participant covariance, trial covariance when present, residual variance, and
fixed coefficient functions. The residual-correlation family is held fixed.
