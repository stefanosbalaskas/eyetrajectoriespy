# Full-refit participant bootstrap for functional mixed-effects models

Version 0.46 adds a second, deliberately distinct participant bootstrap for the
functional mixed-effects layer.

The existing 0.44/0.45 bootstrap is retained unchanged:

```python
fixed_covariance_boot = bootstrap_functional_mixed_effects_coefficients(
    fit,
    n_bootstrap=1000,
    random_state=2026,
)
```

It resamples participants but conditions on the fitted participant random-
effect covariance, optional shared trial random-effect covariance, residual
variance, and any declared residual-correlation parameter.

Version 0.46 adds:

```python
full_refit_boot = bootstrap_functional_mixed_effects_full_refit(
    fit,
    n_bootstrap=1000,
    random_state=2026,
)
```

which refits the mixed model in every participant bootstrap sample.

## What is resampled?

Participants are the independent bootstrap units.

For bootstrap replicate \(b\),

$$
I_1^{*(b)},\ldots,I_n^{*(b)}
\overset{\text{iid}}{\sim}
\{1,\ldots,n\}.
$$

Every sampled participant occurrence contributes that participant's complete
repeated-trial and time-point bundle.

A duplicated source participant is **not** reused as the same mixed-model group.
For a draw such as

$$
(3,7,7,12,\ldots),
$$

the two copies of participant 7 receive distinct bootstrap group identities.

The result retains both the original source participant ID and the bootstrap
participant ID for every draw.

This distinction is essential: otherwise a mixed-effects backend could merge
duplicated source copies into one random-effect realization and the procedure
would no longer be the intended cluster bootstrap. For a 0.48 nested model,
every trial inside each sampled participant occurrence also receives a distinct
bootstrap trial identity.

## What is refitted?

Each successful bootstrap sample refits

$$
\left\{
\widehat{\boldsymbol\beta}^{*(b)}(t),
\widehat{\boldsymbol\Psi}_{P}^{*(b)},
\widehat{\boldsymbol\Psi}_{T}^{*(b)},
\widehat{\sigma}^{2*(b)},
\widehat{\theta}^{*(b)}
\right\}.
$$

This includes all fixed B-spline coefficients, the complete declared
participant random-effect covariance, random-intercept covariance,
random-slope covariance and intercept/slope cross-covariance when present, the
shared trial random-effect covariance when present, residual variance, and
any declared exponential range or AR(1) parameter.

The bootstrap does **not** rerun model specification. Held fixed are:

- fixed and random basis sizes;
- spline degree;
- common-grid knot construction;
- preprocessing;
- response dimension;
- fixed predictors;
- random-slope choice;
- trial-random-effect choice;
- residual-correlation family;
- random-effect structure;
- REML versus ML choice;
- optimizer;
- optimizer iteration limit.

Therefore “full refit” means full estimation of the declared mixed model, not
automatic repetition of the entire analysis-development workflow.

## Failed replicate policy

The sole 0.46 inferential policy is

```text
failed_replicate_policy = "raise"
```

If a bootstrap sample becomes rank deficient, reaches an invalid model state,
or fails optimization, the complete bootstrap terminates.

The package does not redraw another participant sample until the requested
number of successful fits has been reached. Such redraw-until-success behavior
would condition the bootstrap distribution on successful fitting.

Frequent failure should therefore be interpreted as evidence that the declared
mixed model is fragile for the available participant sample.

## Variance-component distributions

`FunctionalMixedEffectsFullRefitBootstrapResult` retains the complete sequence

$$
\widehat{\boldsymbol\Psi}^{*(1)},
\ldots,
\widehat{\boldsymbol\Psi}^{*(B)}
$$

and

$$
\widehat{\sigma}^{2*(1)},
\ldots,
\widehat{\sigma}^{2*(B)}.
$$

It also retains, for every replicate, covariance eigenvalues, covariance
condition number, boundary flag, singularity flag, random-slope boundary flag,
residual variance, log likelihood, convergence state, optimizer/backend
warnings, and the intercept/slope covariance blocks. For a nested 0.48 reference fit it
also retains the full trial covariance distribution, trial covariance
eigenvalues/condition numbers, and trial boundary/singularity flags. For a 0.49 serial reference it additionally
retains the bootstrap serial-parameter distribution, residual-correlation
condition numbers, and serial-parameter boundary flags.

Use

```python
variance_frame = functional_mixed_effects_variance_bootstrap_frame(
    full_refit_boot
)
```

for a replicate-level stability table.

These empirical bootstrap distributions are diagnostics and uncertainty
summaries. Version 0.46 does not automatically convert them into calibrated
variance-component confidence intervals.

## Simultaneous fixed-effect bands

The existing simultaneous-band calibration accepts either bootstrap result:

```python
full_refit_band = functional_mixed_effects_simultaneous_bands(
    full_refit_boot,
    confidence_level=0.95,
    simultaneous_scope="coefficient",
)
```

With a full-refit bootstrap, the coefficient-function sampling distribution
therefore includes re-estimation of the declared participant covariance,
optional trial covariance, residual variance, and any declared residual-
correlation parameter across participant bootstrap samples.

The band still conditions on the declared model specification and basis choices,
and still claims simultaneous coverage over the observed time grid only.

## Compare fixed-covariance and full-refit inference

```python
comparison = compare_functional_mixed_effects_bootstraps(
    fixed_covariance_boot,
    full_refit_boot,
)

ax = plot_functional_mixed_effects_bootstrap_comparison(
    comparison,
    coefficient="condition",
)
```

The comparison retains, at every observed time point,

$$
\frac{
\text{full-refit simultaneous-band width}
}{
\text{fixed-covariance simultaneous-band width}
}.
$$

Values near one indicate that variance-component re-estimation contributes
little additional band width under the declared model and bootstrap settings.

Substantial departures from one are descriptive sensitivity evidence that the
conditional-covariance approximation matters. They are not automatically a
model-selection criterion.

## Interpretation boundary

The full-refit bootstrap incorporates participant resampling and
variance-component **re-estimation**, but not uncertainty from preprocessing,
response selection, basis-size choice, spline-degree choice, predictor/model
selection, random-slope selection, optimizer selection, or residual-covariance
model selection.

It is therefore a full refit of the **declared model specification**, not a
bootstrap over all defensible analytical choices.

## Evidence basis

Park, Staicu, Xiao, and Crainiceanu (2018, DOI
`10.1093/biostatistics/kxx026`) describe fixed-effect inference for complex
functional models by bootstrapping independent units such as subjects. Version 0.46 follows that independent-unit principle while refitting the
package's declared mixed-effects model in every participant sample.
Participant-only iid fits use the established `statsmodels.MixedLM` backend.
Nested and/or serial 0.48–0.49 fits use the explicit profiled Gaussian backend;
the full-refit bootstrap re-estimates participant covariance, optional trial
covariance, residual variance, and the declared phi/rho parameter. The fixed-
covariance bootstrap instead conditions on those fitted covariance quantities.

## What comes next?

Version 0.49 propagates explicitly declared residual covariance through both
participant-bootstrap paths. Version 0.50 now provides descriptive
covariance-structure sensitivity/comparison rather than automatic selection.

See also the
[functional mixed-effects guide](../guides/functional-mixed-effects.md),
[random functional slope guide](functional-mixed-effects-random-slope.md),
[simultaneous bands](functional-mixed-effects-simultaneous-bands.md), and
[worked full-refit example](../examples/functional-mixed-effects-full-refit-bootstrap.md).
