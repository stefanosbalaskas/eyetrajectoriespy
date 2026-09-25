# Trial-level functional random effects

Version 0.48 extends the Gaussian functional mixed-effects layer from a
participant-only covariance hierarchy to an explicitly nested
participant → trial → time model.

For participant \(i\), trial \(j\), and observed time \(t\),

\[
Y_{ij}(t)
=
\mathbf{x}_{ij}^{\top}\boldsymbol{\beta}(t)
+
b_i(t)
+
u_{ij}(t)
+
\epsilon_{ij}(t).
\]

The participant functional effect remains

\[
b_i(t)=\mathbf B_b(t)^\top\mathbf a_i,
\qquad
\mathbf a_i\sim N(\mathbf 0,\boldsymbol\Psi_{\mathrm{participant}}).
\]

The new trial functional intercept is

\[
u_{ij}(t)=\mathbf B_u(t)^\top\mathbf v_{ij},
\qquad
\mathbf v_{ij}\sim N(\mathbf 0,\boldsymbol\Psi_{\mathrm{trial}}).
\]

\(\boldsymbol\Psi_{\mathrm{trial}}\) is one shared unstructured covariance
across trials. The implementation does **not** estimate one covariance per
trial and does not replace the functional covariance with an independent
scalar variance component.

## Marginal covariance

For all observations from participant \(i\),

\[
\mathbf V_i
=
\mathbf Z_i
\boldsymbol\Psi_{\mathrm{participant}}
\mathbf Z_i^\top
+
\sum_j
\mathbf W_{ij}
\boldsymbol\Psi_{\mathrm{trial}}
\mathbf W_{ij}^\top
+
\sigma^2\mathbf I.
\]

Participant and trial covariance matrices are parameterized through their
Cholesky factors. Fixed B-spline coefficients are profiled by generalized
least squares for every covariance-parameter evaluation.

The historical participant-only model continues to use the established
`statsmodels.MixedLM` backend. The nested backend is activated only when the
trial effect is explicitly requested.

## Explicit API

~~~python
fit = fit_functional_mixed_effects_regression(
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
    spline_degree=2,
)
~~~

There is no Boolean shorthand. The explicit string leaves the public contract
open to future trial structures without silently changing today's semantics.

## Trial identity

Version 0.48 treats one trajectory as one observed trial. The `trial_column`
therefore provides the scientific trial label attached to each curve.

Trial labels need only be unique **within participant**. Reused labels such as
`T01` across different participants are valid. Internally the nested identity
is the participant/trial pair.

The model fails closed when:

- `trial_column` is absent or contains missing values;
- a participant/trial pair appears more than once;
- any participant contributes fewer than two observed trials;
- the trial basis is rank deficient on the observed grid;
- the number of observed nested trials does not exceed
  \(q_u(q_u+1)/2\), the number of free parameters in the unstructured
  \(q_u\times q_u\) trial covariance;
- optimization fails to converge.

The trial-count rule is a **minimum covariance-complexity guard**, not a theorem
that the covariance is estimated precisely.

## Covariance diagnostics

The result retains:

- `trial_random_effect_covariance`;
- covariance eigenvalues;
- condition number;
- free covariance-parameter count;
- boundary and singularity flags;
- trial B-spline basis and knots;
- trial BLUP coefficients;
- reconstructed trial random functions;
- source and composite trial identifiers.

A boundary estimate is retained. The package does not automatically delete the
trial effect or refit a simpler model.

## Inspect the trial effects

~~~python
from eyetrajectoriespy import (
    functional_trial_random_effect_frame,
    plot_functional_trial_random_effects,
)

trial_effects = functional_trial_random_effect_frame(fit)

plot_functional_trial_random_effects(
    fit,
    participant_id=fit.participant_ids[0],
)
~~~

These are conditional BLUPs under the fitted covariance model. They should not
be interpreted as independently estimated trial trajectories.

## Residual diagnostics after the extension

The 0.47 diagnostic API can be applied directly to a 0.48 fit:

~~~python
from eyetrajectoriespy import (
    functional_mixed_effects_residual_diagnostics,
)

post_trial_diagnostics = functional_mixed_effects_residual_diagnostics(
    fit,
    max_lag=6,
)
~~~

The relevant scientific question is whether smooth residual dependence that was
present under the participant-only model is reduced after accounting for the
trial-specific smooth process. A residual ACF or variogram is diagnostic
evidence, not an automatic covariance selector.

## Bootstrap inference

Both existing participant-level bootstrap contracts remain participant-level.

The fixed-covariance bootstrap resamples whole participants and carries all
their trials. It re-estimates fixed coefficients by GLS while conditioning on:

- \(\widehat{\boldsymbol\Psi}_{\mathrm{participant}}\);
- \(\widehat{\boldsymbol\Psi}_{\mathrm{trial}}\);
- \(\widehat{\sigma}^2\);
- the declared bases and model structure.

The full-refit bootstrap also resamples whole participants. Every sampled
participant occurrence receives a new bootstrap participant identity, and every
nested source trial receives a new bootstrap trial identity. Each replicate
refits both covariance matrices and residual variance.

~~~python
from eyetrajectoriespy import (
    bootstrap_functional_mixed_effects_full_refit,
    functional_mixed_effects_full_refit_trial_audit_frame,
)

boot = bootstrap_functional_mixed_effects_full_refit(
    fit,
    n_bootstrap=1000,
    random_state=48,
)

audit = functional_mixed_effects_full_refit_trial_audit_frame(boot)
~~~

Trials are not independently resampled in this inferential contract.

## Interpretation boundary

A smooth trial functional random effect and serial residual correlation are
different covariance mechanisms. Version 0.48 addresses the former only.

Short-range dependence remaining after conditioning on participant and trial
functional effects is a candidate motivation for the planned 0.49 explicit
residual covariance layer. The package does not infer that conclusion
automatically.
