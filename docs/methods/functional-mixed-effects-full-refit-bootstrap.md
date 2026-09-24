# Full-refit participant bootstrap for functional mixed-effects models

Version 0.46 adds a second, deliberately distinct participant bootstrap for the
likelihood-based functional mixed-effects layer.

The existing \`bootstrap_functional_mixed_effects_coefficients()\` resamples
whole participants but holds the fitted random-effect covariance and residual
variance fixed. It therefore provides conditional fixed-effect inference under
the reference covariance model.

Version 0.46 adds:

\`\`\`python
from eyetrajectoriespy import (
    bootstrap_functional_mixed_effects_full_refit,
)

boot = bootstrap_functional_mixed_effects_full_refit(
    fit,
    n_bootstrap=1000,
    random_state=2026,
)
\`\`\`

For bootstrap replicate \(b\),

$$
\mathcal D^{*(b)}
\longrightarrow
\left\{
\widehat{\boldsymbol\beta}^{*(b)}(t),
\widehat{\boldsymbol\Psi}^{*(b)},
\widehat\sigma^{2*(b)}
\right\}.
$$

This refits the complete **declared mixed model** in every participant resample.

## Independent resampling unit

Participants are sampled with replacement. If a draw is

$$
(3,7,7,12,\ldots),
$$

the two copies of source participant 7 receive **different bootstrap group
identities** before fitting, for example:

\`\`\`text
source_participant_id = 7
bootstrap_participant_id = bootstrap_0002_group_0001

source_participant_id = 7
bootstrap_participant_id = bootstrap_0002_group_0002
\`\`\`

This is essential. Reusing the original participant ID would cause
\`MixedLM\` to merge both bootstrap copies into one random-effect group.

Both identities remain auditable through
\`functional_mixed_effects_bootstrap_identity_frame()\`.

## What is refitted

Every bootstrap replicate re-estimates:

- fixed B-spline coefficient parameters and coefficient functions;
- the complete declared random-effect covariance
  \(\widehat{\boldsymbol\Psi}^{*(b)}\);
- residual variance \(\widehat\sigma^{2*(b)}\);
- log likelihood and covariance diagnostics.

For a one-random-slope model, the complete intercept/slope covariance is
therefore refit in every replicate.

## What remains fixed

"Full refit" is conditional on the declared model specification. Version 0.46
does not rerun or change preprocessing, response dimension, predictors,
random-slope choice, random-effect structure, basis sizes, deterministic knot
construction, spline degree, REML versus ML, optimizer, or \`maxiter\`.

Thus 0.46 propagates variance-component estimation variability **within the
declared model**; it does not rerun the entire analytical workflow.

## Failure policy

The only inferential behavior is

\`\`\`text
failed_replicate_policy = "raise"
\`\`\`

If a bootstrap sample is rank deficient, fails optimization, or otherwise
cannot produce the declared fit, the entire bootstrap raises immediately.
Failed samples are never silently discarded or redrawn.

## Variance-component stability

The result retains, for every replicate:

- full random-effect covariance;
- intercept covariance block;
- slope covariance block when present;
- intercept/slope cross-covariance when present;
- covariance eigenvalues and condition number;
- boundary and singularity flags;
- random-slope boundary flag;
- residual variance;
- log likelihood;
- convergence state;
- backend warnings.

Use:

\`\`\`python
from eyetrajectoriespy import (
    functional_mixed_effects_variance_bootstrap_frame,
)

variance = functional_mixed_effects_variance_bootstrap_frame(boot)
\`\`\`

These empirical distributions are **stability diagnostics**. Version 0.46 does
not automatically reinterpret them as calibrated variance-component confidence
intervals.

## Simultaneous fixed-effect bands

The existing simultaneous-band calibrator accepts either bootstrap type:

\`\`\`python
from eyetrajectoriespy import (
    functional_mixed_effects_simultaneous_bands,
)

band = functional_mixed_effects_simultaneous_bands(
    boot,
    confidence_level=0.95,
    simultaneous_scope="coefficient",
)
\`\`\`

The returned provenance records \`bootstrap_type="full_refit"\` and
\`variance_components_refit=True\`.

## Compare fixed-covariance and full-refit inference

\`\`\`python
from eyetrajectoriespy import (
    bootstrap_functional_mixed_effects_coefficients,
    compare_functional_mixed_effects_bootstraps,
    plot_functional_mixed_effects_bootstrap_comparison,
)

fixed = bootstrap_functional_mixed_effects_coefficients(
    fit,
    n_bootstrap=1000,
    random_state=2026,
)

comparison = compare_functional_mixed_effects_bootstraps(
    fixed,
    boot,
)

ax = plot_functional_mixed_effects_bootstrap_comparison(
    comparison,
    coefficient="condition",
)
\`\`\`

For coefficient \(p\) and observed time \(t_m\),

$$
R_p(t_m)
=
\frac{
W_{p,\mathrm{full}}(t_m)
}{
W_{p,\mathrm{fixed}}(t_m)
}.
$$

Ratios near one indicate little practical difference between the two
uncertainty procedures at that location. Large departures indicate sensitivity
to variance-component re-estimation. The ratio is descriptive, not a
probability or model-selection statistic.

## Evidence basis

Subject-level resampling is established for fixed-effect inference with
correlated functional data. Park et al. (2018, DOI
\`10.1093/biostatistics/kxx026\`) explicitly resample independent subjects and
carry all within-subject observations together.

Version 0.46 follows that independent-unit principle but applies it to the
package's declared likelihood-based mixed model by refitting its variance
components in every bootstrap sample.

## Next methodological step

Version 0.47 will diagnose residual and within-trial dependence before any
serial covariance structure is selected. Planned diagnostics include residual
ACF by trial, lag covariance, empirical within-trial variograms, and
correlation versus physical lag.

That diagnostic tranche will determine whether the next structural extension
should be a trial-level functional random effect or an explicit serial residual
covariance model.
