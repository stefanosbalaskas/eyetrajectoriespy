# Full-refit participant bootstrap for functional mixed-effects models

Version 0.46 adds a second, deliberately distinct participant bootstrap for the
functional mixed-effects layer.

The existing 0.44/0.45 bootstrap is retained unchanged:

\`\`\`python
fixed_covariance_boot = bootstrap_functional_mixed_effects_coefficients(
    fit,
    n_bootstrap=1000,
    random_state=2026,
)
\`\`\`

It resamples participants but conditions on the fitted random-effect covariance
and residual variance.

Version 0.46 adds:

\`\`\`python
full_refit_boot = bootstrap_functional_mixed_effects_full_refit(
    fit,
    n_bootstrap=1000,
    random_state=2026,
)
\`\`\`

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

This distinction is essential: otherwise \`MixedLM\` would merge duplicated
copies into a single random-effect group and the procedure would no longer be
the intended cluster bootstrap.

## What is refitted?

Each successful bootstrap sample refits

$$
\left\{
\widehat{\boldsymbol\beta}^{*(b)}(t),
\widehat{\boldsymbol\Psi}^{*(b)},
\widehat{\sigma}^{2*(b)}
\right\}.
$$

This includes all fixed B-spline coefficients, the complete random-effect
covariance matrix, random-intercept covariance, random-slope covariance when
present, intercept/slope cross-covariance when present, and residual variance.

The bootstrap does **not** rerun model specification. Held fixed are:

- fixed and random basis sizes;
- spline degree;
- common-grid knot construction;
- preprocessing;
- response dimension;
- fixed predictors;
- random-slope choice;
- random-effect structure;
- REML versus ML choice;
- optimizer;
- optimizer iteration limit.

Therefore “full refit” means full estimation of the declared mixed model, not
automatic repetition of the entire analysis-development workflow.

## Failed replicate policy

The sole 0.46 inferential policy is

\`\`\`text
failed_replicate_policy = "raise"
\`\`\`

If a bootstrap sample becomes rank deficient, reaches an invalid model state,
or fails optimization, the complete bootstrap terminates.

The package does not redraw another participant sample until the requested
number of successful fits has been reached. Such redraw-until-success behavior
would condition the bootstrap distribution on successful fitting.

Frequent failure should therefore be interpreted as evidence that the declared
mixed model is fragile for the available participant sample.

## Variance-component distributions

\`FunctionalMixedEffectsFullRefitBootstrapResult\` retains the complete sequence

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
warnings, and the intercept/slope covariance blocks.

Use

\`\`\`python
variance_frame = functional_mixed_effects_variance_bootstrap_frame(
    full_refit_boot
)
\`\`\`

for a replicate-level stability table.

These empirical bootstrap distributions are diagnostics and uncertainty
summaries. Version 0.46 does not automatically convert them into calibrated
variance-component confidence intervals.

## Simultaneous fixed-effect bands

The existing simultaneous-band calibration accepts either bootstrap result:

\`\`\`python
full_refit_band = functional_mixed_effects_simultaneous_bands(
    full_refit_boot,
    confidence_level=0.95,
    simultaneous_scope="coefficient",
)
\`\`\`

With a full-refit bootstrap, the coefficient-function sampling distribution
therefore includes random-effect covariance and residual-variance re-estimation
across participant bootstrap samples.

The band still conditions on the declared model specification and basis choices,
and still claims simultaneous coverage over the observed time grid only.

## Compare fixed-covariance and full-refit inference

\`\`\`python
comparison = compare_functional_mixed_effects_bootstraps(
    fixed_covariance_boot,
    full_refit_boot,
)

ax = plot_functional_mixed_effects_bootstrap_comparison(
    comparison,
    coefficient="condition",
)
\`\`\`

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
\`10.1093/biostatistics/kxx026\`) describe fixed-effect inference for complex
functional models by bootstrapping independent units such as subjects. Version
0.46 follows that independent-unit principle while refitting the package's
declared \`MixedLM\` representation in every participant sample.

The current \`statsmodels.MixedLM\` backend represents the within-group marginal
covariance through the random-effect design/covariance plus scalar residual
variance. Version 0.46 therefore refits those existing covariance parameters;
it does not introduce serial residual covariance.

## What comes next?

Version 0.47 is **residual / within-trial dependence diagnostics**, not an
automatic AR(1) implementation.

The diagnostic tranche should inspect residual ACF, lag covariance, empirical
variograms, and physical-lag correlation before deciding whether the next
structural model should be a trial-level functional random effect or an
explicit serial residual covariance model.

See also the
[functional mixed-effects guide](../guides/functional-mixed-effects.md),
[random functional slope guide](functional-mixed-effects-random-slope.md),
[simultaneous bands](functional-mixed-effects-simultaneous-bands.md), and
[worked full-refit example](../examples/functional-mixed-effects-full-refit-bootstrap.md).
