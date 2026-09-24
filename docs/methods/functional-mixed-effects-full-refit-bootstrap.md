# Full-refit participant bootstrap for functional mixed-effects models

Version 0.46 adds a second, deliberately distinct participant bootstrap for the
likelihood-based functional mixed-effects layer.

The existing 0.44/0.45 procedure,

`bootstrap_functional_mixed_effects_coefficients()`,

resamples whole participants but **holds the fitted random-effect covariance and
residual variance fixed**. It therefore provides conditional fixed-effect
inference under the reference covariance model.

Version 0.46 adds

```python
from eyetrajectoriespy import (
    bootstrap_functional_mixed_effects_full_refit,
)

boot = bootstrap_functional_mixed_effects_full_refit(
    fit,
    n_bootstrap=1000,
    random_state=2026,
)
```

For bootstrap replicate (b),

[
mathcal D^{*(b)}
longrightarrow
left{
widehat{oldsymboleta}^{*(b)}(t),
widehat{oldsymbolPsi}^{*(b)},
widehatsigma^{2*(b)}
ight}.
]

This refits the complete **declared mixed model** in every participant resample.

## Independent resampling unit

Participants are sampled with replacement.

If a draw is

$
(3,7,7,12,\ldots),
$

the two copies of source participant 7 receive **different bootstrap group
identities** before fitting. For example,

```text
source_participant_id = 7
bootstrap_participant_id = bootstrap_0002_group_0001

source_participant_id = 7
bootstrap_participant_id = bootstrap_0002_group_0002
```

This is essential. If duplicate source participants retained the same group
label, `MixedLM` would merge their observations into one random-effect group
and the procedure would no longer be the intended participant-cluster
bootstrap.

Both identities are retained in the bootstrap audit object and can be exported
with

```python
from eyetrajectoriespy import (
    functional_mixed_effects_bootstrap_identity_frame,
)

identity = functional_mixed_effects_bootstrap_identity_frame(boot)
```

## What is refitted

Every bootstrap replicate re-estimates:

- fixed B-spline coefficient parameters and coefficient functions;
- the complete declared random-effect covariance matrix
  (widehat{oldsymbolPsi}^{*(b)});
- residual variance (widehatsigma^{2*(b)});
- participant BLUPs required internally by the fitted mixed model;
- log likelihood and covariance diagnostics.

For a one-random-slope model, this means the full intercept/slope covariance is
refit in every replicate.

## What is held fixed

"Full refit" is conditional on the declared model specification. Version 0.46
does **not** rerun or change:

- preprocessing;
- response dimension;
- predictor specification;
- random-slope choice;
- random-effect structure;
- fixed or random B-spline basis size;
- deterministic knot construction from the common grid;
- spline degree;
- REML versus ML choice;
- optimizer choice or `maxiter`.

The procedure therefore propagates variance-component estimation uncertainty
within the declared model; it does not repeat the entire analytical workflow.

## Failure policy

The only 0.46 policy is

```text
failed_replicate_policy = "raise"
```

If a bootstrap sample is rank deficient, hits an unrecoverable optimizer
failure, or otherwise cannot produce the declared model, the complete bootstrap
raises immediately.

The package does not silently discard failed replicates and does not redraw
until it has accumulated the requested number of successful fits. Such a
failure is scientifically informative evidence that the declared mixed-effects
model is fragile under participant resampling.

## Variance-component stability

The bootstrap result stores, for every replicate:

- full random-effect covariance;
- random-intercept covariance block;
- random-slope covariance block when present;
- intercept/slope cross-covariance when present;
- covariance eigenvalues;
- covariance condition number;
- boundary flag;
- singularity flag;
- random-slope boundary flag;
- residual variance;
- log likelihood;
- convergence state;
- backend warnings.

Use

```python
from eyetrajectoriespy import (
    functional_mixed_effects_variance_bootstrap_frame,
)

variance = functional_mixed_effects_variance_bootstrap_frame(boot)
```

These empirical distributions are **stability diagnostics**. Version 0.46 does
not automatically reinterpret them as calibrated confidence intervals for
variance components.

## Simultaneous fixed-effect bands

The same observed-grid simultaneous-band calibrator accepts either bootstrap
type:

```python
from eyetrajectoriespy import (
    functional_mixed_effects_simultaneous_bands,
)

band = functional_mixed_effects_simultaneous_bands(
    boot,
    confidence_level=0.95,
    simultaneous_scope="coefficient",
)
```

The returned provenance records

```text
bootstrap_type = "full_refit"
variance_components_refit = True
```

so the inferential contract cannot be confused with the faster fixed-covariance
bootstrap.

## Compare the two bootstrap contracts

```python
from eyetrajectoriespy import (
    bootstrap_functional_mixed_effects_coefficients,
    compare_functional_mixed_effects_bootstraps,
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
```

For coefficient (p) and observed time (t_m), the comparison reports

[
R_p(t_m)
=
rac{
W_{p,mathrm{full}}(t_m)
}{
W_{p,mathrm{fixed}}(t_m)
},
]

where (W) is the simultaneous-band width.

Ratios near one indicate little practical difference between the two
uncertainty procedures at that location. Large departures are descriptive
evidence that variance-component re-estimation materially changes uncertainty.
The ratio is not a probability or a formal model-selection statistic.

## Evidence basis

Subject-level resampling is established for fixed-effect inference with
correlated functional data. The Biostatistics paper *Simple fixed-effects
inference for complex functional models* explicitly resamples independent
subjects and carries all within-subject observations together.

Version 0.46 adopts that independent-unit principle but is more specific to the
package's likelihood-based mixed model: it refits the declared `MixedLM`
variance components in every participant bootstrap sample.

This implementation should therefore be described as a **whole-participant
case bootstrap with complete mixed-model refitting conditional on the declared
model specification**.

## Next methodological step

Version 0.47 should diagnose residual and within-trial dependence rather than
preselect an AR(1) model. The planned diagnostics include residual ACF, lag
covariance, empirical within-trial variograms, and correlation versus physical
lag, stratified by participant/trial where useful.

That diagnostic tranche will determine whether the next structural extension
should be a trial-level functional random effect or an explicit serial residual
covariance model.
