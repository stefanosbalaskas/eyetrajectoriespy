# Simultaneous inference for functional mixed-effects coefficients

Version 0.44 adds observed-grid simultaneous confidence bands for the fixed
coefficient functions from `fit_functional_mixed_effects_regression()`.

The goal is to support a whole-function statement about, for example,

[
eta_{mathrm{condition}}(t),
]

rather than treating every time point as an unrelated inferential claim.

## Bootstrap unit

The resampling unit is the **participant**. Every selected participant
contributes all of that participant's trials and all observed time points.

```python
from eyetrajectoriespy import (
    bootstrap_functional_mixed_effects_coefficients,
    functional_mixed_effects_simultaneous_bands,
)

boot = bootstrap_functional_mixed_effects_coefficients(
    fit,
    n_bootstrap=1000,
    random_state=2026,
)

band = functional_mixed_effects_simultaneous_bands(
    boot,
    confidence_level=0.95,
    simultaneous_scope="coefficient",
)
```

Curves are never sampled independently. That would break the repeated-measures
structure the mixed model was introduced to preserve.

## What is re-estimated

For participant (i), let

[
mathbf V_i
=
mathbf Z_iwidehat{oldsymbolPsi}mathbf Z_i^	op
+
widehatsigma^2mathbf I.
]

The participant's fixed-effect information and score contributions are

[
mathbf A_i
=
mathbf X_i^	opmathbf V_i^{-1}mathbf X_i,
qquad
mathbf s_i
=
mathbf X_i^	opmathbf V_i^{-1}mathbf y_i.
]

For each bootstrap replicate, participants are sampled with replacement and
the fixed B-spline coefficients are re-estimated by GLS:

[
widehat{oldsymbol	heta}^{*(b)}
=
left[
sum_{r=1}^{n}mathbf A_{I_r^{(b)}}
ight]^{-1}
sum_{r=1}^{n}mathbf s_{I_r^{(b)}}.
]

The fitted random-effect covariance, residual variance, fixed basis, random
basis, spline degree, model specification, and preprocessing decisions are
held fixed.

This makes the procedure a **participant-cluster case bootstrap conditional on
the fitted covariance model**, not a full mixed-model parametric bootstrap and
not a variance-component bootstrap.

## Simultaneous calibration

For coefficient (p), bootstrap pointwise standard deviations are calculated
from the participant-resampled coefficient functions. The centered,
studentized bootstrap process is summarized by

[
M_p^{*(b)}
=
max_m
left|
rac{
widehateta_p^{*(b)}(t_m)
-
overline{widehateta_p^*}(t_m)
}{
widehat{mathrm{SE}}_p^*(t_m)
}
ight|.
]

The empirical (1-alpha) quantile gives

[
widehateta_p(t_m)
pm
c_{p,1-alpha}
widehat{mathrm{SE}}_p^*(t_m).
]

The bootstrap mean is used only to center the calibration process. The reported
band remains centered on the reference mixed-model estimate; no automatic
bootstrap bias correction is applied.

## Coefficient versus family scope

With `simultaneous_scope="coefficient"`, each fixed coefficient receives its
own maximum-statistic calibration over the observed time grid.

With `simultaneous_scope="family"`, one maximum is taken jointly over every
fixed coefficient and every observed time point. This is more conservative but
supports a single declared fixed-effect family.

Neither mode claims coverage between unsampled time points.

## Fail-closed behavior

The procedure refuses to silently repair or discard problematic resamples.

A bootstrap replicate raises if the resampled participant information matrix is
rank deficient or cannot be solved. The package does not redraw another sample
until the requested number of successful replicates is reached.

The reference fit is also reconstructed through the same fixed-covariance GLS
equations before resampling. If that reconstruction does not reproduce the
stored MixedLM fixed coefficients within numerical tolerance, the bootstrap
raises rather than proceeding under an inconsistent covariance contract.

## Interpretation

A simultaneous band supports a statement about the complete **observed-grid
coefficient function** under the declared model and bootstrap contract.

For example, if a 95% coefficient-scope band for
(eta_{mathrm{condition}}(t)) stays above zero at every observed grid point,
the estimated condition coefficient is positive over that entire observed
grid under this model-based inference procedure.

It does **not** imply:

- 95% pointwise coverage at each location independently;
- coverage at arbitrary unsampled time points;
- uncertainty propagation from basis-size selection;
- uncertainty from estimating the random-effect covariance or residual
  variance;
- robustness to a different covariance model;
- causal interpretation of the fixed effect.

## Evidence basis

Functional mixed-effects methodology has long treated simultaneous bands as a
distinct inferential target from pointwise intervals. Zhu et al. (2019,
DOI `10.5705/ss.202017.0505`) develop simultaneous bands for fixed-effect
functions in longitudinal functional mixed-effects models using a resampling
approach that preserves within-subject dependence.

More recently, Gunning et al. (2025, DOI
`10.1007/s00180-024-01591-1`) use subject-level bootstrap resampling and
simulation for simultaneous fixed-effect bands in a functional mixed-effects
analysis of repeated kinematic data.

Version 0.44 follows the same hierarchical principle—resample participants,
not individual repeated curves—but implements a deliberately narrower
fixed-covariance GLS bootstrap matched to the package's existing 0.36 model.

## Next methodological boundary

Version 0.44 closes the most important inferential gap in the current
functional mixed-effects layer. The next natural extension is participant
**random functional slopes**, not another transfer-entropy method.

See the
[worked example](../examples/functional-mixed-effects-simultaneous-bands.md),
[functional mixed-effects guide](../guides/functional-mixed-effects.md),
and
[mathematical reference](mathematical-reference.md#functional-mixed-effects-simultaneous).
