# Functional mixed-effects residual diagnostics

Version 0.47 adds a diagnostic layer for dependence that remains after a
likelihood-based functional mixed-effects fit. The target is **not** a new
covariance model. It is an auditable description of the conditional residual
functions already produced by `fit_functional_mixed_effects_regression()`.

For trial (j), let (r_j(t_m)) be the fitted conditional residual on the
observed common grid. The diagnostics first center residuals within trial,

$$
e_j(t_m)=r_j(t_m)-\bar r_j.
$$

For an explicitly declared index lag (h),

$$
\widehat\gamma_j(h)
=
\frac{1}{T-h}
\sum_{m=1}^{T-h}
e_j(t_m)e_j(t_{m+h}),
$$

and, when the lag-zero variance is non-zero,

$$
\widehat\rho_j(h)
=
\frac{\widehat\gamma_j(h)}
     {\widehat\gamma_j(0)}.
$$

The empirical semivariance is

$$
\widehat v_j(h)
=
\frac{1}{2(T-h)}
\sum_{m=1}^{T-h}
\left[r_j(t_{m+h})-r_j(t_m)\right]^2.
$$

These are descriptive diagnostics. They do not constitute a test that the
residual process is AR(1), nor do they decide between serial residual
correlation and a smooth trial-level functional random effect.

## Core workflow

~~~python
from eyetrajectoriespy import (
    functional_mixed_effects_residual_diagnostics,
    functional_mixed_effects_residual_diagnostic_frame,
    plot_functional_mixed_effects_residual_acf,
    plot_functional_mixed_effects_residual_variogram,
)

diagnostics = functional_mixed_effects_residual_diagnostics(
    fit,
    max_lag=8,
)

trial = functional_mixed_effects_residual_diagnostic_frame(
    diagnostics,
    level="trial",
)
participant = functional_mixed_effects_residual_diagnostic_frame(
    diagnostics,
    level="participant",
)
overall = functional_mixed_effects_residual_diagnostic_frame(
    diagnostics,
    level="overall",
)

plot_functional_mixed_effects_residual_acf(
    diagnostics,
    level="overall",
)
plot_functional_mixed_effects_residual_variogram(
    diagnostics,
    level="overall",
)
~~~

`max_lag` is required. The package does not inspect the result and choose a lag
window automatically.

## Version 0.49: diagnose serial models on the whitened scale

When a correlated residual covariance is fitted, raw residuals are **supposed**
to retain the modeled correlation. Their ACF is therefore not a valid success
criterion for whitening.

Version 0.49 adds:

~~~python
white = functional_mixed_effects_residual_diagnostics(
    fit,
    max_lag=8,
    residual_scale="whitened",
)
~~~

If the fitted within-trial residual covariance is
(σ^2R_\theta=LL^\top), the diagnostic residual vector is
(e^{(w)}=L^{-1}e). The same ACF/autocovariance/semivariance summaries are then
computed on that whitened residual function. The default remains
`residual_scale="raw"` for backward compatibility.

Whitening uses only the fitted residual covariance. It does not remove
uncertainty in estimated fixed effects, random effects, variance components, or
the serial parameter. A flat whitened ACF is therefore a diagnostic target, not
proof that the complete stochastic model is correct.

## Physical lag is retained, not assumed

The mixed-effects model uses a common grid, but that grid need not be equally
spaced. For each index lag the result therefore retains the mean, minimum, and
maximum physical separation in the fit's declared time unit.

When exact pair-level physical lags matter, inspect them directly:

~~~python
from eyetrajectoriespy import functional_mixed_effects_residual_pair_frame

pairs = functional_mixed_effects_residual_pair_frame(
    diagnostics,
    lag_index=3,
)
~~~

The returned frame retains the start/end time, exact physical lag, raw residual
pair, centered-product contribution to autocovariance, and semivariance
contribution. No physical-lag bins are created automatically.

## Participant and overall summaries

Trial diagnostics are primary. Participant and overall summaries are
pair-count-weighted descriptive summaries of the trial-level quantities. The
result keeps the total number of trials and the number with defined ACF values.

A trial with exactly zero residual variance is **not** removed. Its
autocorrelation is undefined and stored as `NaN`; the covariance and
semivariance remain available and the undefined ACF count remains visible.

## Compare model specifications without selecting one

A direct sensitivity comparison is available when two fits contain the same
curves, participant mapping, response dimension, time unit, and exact time grid:

~~~python
from eyetrajectoriespy import (
    compare_functional_mixed_effects_residual_diagnostics,
)

comparison = compare_functional_mixed_effects_residual_diagnostics(
    intercept_only_fit,
    random_slope_fit,
    max_lag=8,
    reference_label="random intercept",
    comparison_label="random intercept + condition slope",
)
~~~

The output reports side-by-side overall autocovariance, autocorrelation,
semivariance, and their differences by lag. It is deliberately descriptive:
there is no winner, p-value, automatic threshold, or covariance-model selector.

## Interpretation

Persistent short-lag autocorrelation can indicate that the current covariance
hierarchy is incomplete. But the shape alone does not identify the missing
mechanism. Two scientifically distinct possibilities are:

- a smooth trial-level functional deviation (u_{ij}(t)), representing
  trial-specific departures that persist across the curve; or
- a serial residual process (epsilon_{ij}(t)), representing shorter-range
  dependence after smooth participant/trial effects.

Those structures are not interchangeable. Version 0.47 diagnoses the raw
residual pattern first; version 0.49 adds explicitly declared serial covariance
and a whitened diagnostic scale while still leaving the structural choice
explicit.

## Reporting

Report the residual type and scale (raw conditional or whitened conditional residuals), declared maximum index lag,
time unit, whether the common grid was equally spaced, the trial/participant
aggregation level, zero-variance trials, and whether diagnostics were compared
before/after a declared model extension. State that no covariance structure was
selected automatically.

Use
`functional_mixed_effects_residual_reporting_text()` for a compact methods
paragraph.

## Limitations

The diagnostics are conditional on the fitted model, basis choices,
preprocessing, participant grouping, and estimated random effects. They do not
correct a misspecified model, do not estimate an alternative serial covariance,
and do not turn residual autocorrelation into evidence for a unique mechanism.

The overall and participant ACF summaries are pair-count-weighted summaries of
trial-specific ACFs; they are not the same estimand as one pooled stationary
time-series ACF. Exact trial-level values remain available and should be
inspected when heterogeneity matters.
