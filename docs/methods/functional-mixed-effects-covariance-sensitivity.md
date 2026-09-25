# Covariance-structure sensitivity

Version 0.50 is the capstone covariance-robustness layer for the Gaussian
functional mixed-effects subsystem. Its question is deliberately not *which
covariance model wins?* but:

\[
\boxed{
\text{How much do the scientific conclusions change under defensible covariance structures?}
}
\]

The sensitivity layer compares **already fitted, predeclared models**. It does
not generate covariance combinations, refit models, rank models, choose a
winner, or compute likelihood-ratio p-values.

## Declare the structures first

A covariance declaration is explicit:

~~~python
from eyetrajectoriespy import (
    FunctionalMixedEffectsCovarianceSpecification,
)

specifications = (
    FunctionalMixedEffectsCovarianceSpecification(
        name="M1",
        random_slope_predictor="condition",
        trial_random_effect=None,
        residual_correlation="iid",
    ),
    FunctionalMixedEffectsCovarianceSpecification(
        name="M2",
        random_slope_predictor="condition",
        trial_random_effect="functional_intercept",
        residual_correlation="iid",
    ),
    FunctionalMixedEffectsCovarianceSpecification(
        name="M3",
        random_slope_predictor="condition",
        trial_random_effect=None,
        residual_correlation="exponential",
    ),
    FunctionalMixedEffectsCovarianceSpecification(
        name="M4",
        random_slope_predictor="condition",
        trial_random_effect="functional_intercept",
        residual_correlation="exponential",
    ),
)
~~~

Fit each model independently with
`fit_functional_mixed_effects_regression()`. The sensitivity routine receives
those fitted objects:

~~~python
from eyetrajectoriespy import (
    functional_mixed_effects_covariance_sensitivity,
)

sensitivity = functional_mixed_effects_covariance_sensitivity(
    fits={
        "M1": fit_m1,
        "M2": fit_m2,
        "M3": fit_m3,
        "M4": fit_m4,
    },
    specifications=specifications,
    reference="M1",
    max_lag=6,
)
~~~

There is no `best_model` field and the model table is not sorted by an
information criterion.

## Strict comparability contract

The routine fails before numerical comparison unless successful fits use the
same:

- source curves and curve order;
- observed response functions;
- fixed-effect scalar design;
- fixed coefficient names and predictors;
- fixed B-spline basis and knots;
- participant random-effect basis and knots;
- participant identities and curve-to-participant mapping;
- response dimension and coordinate semantics;
- observed time grid and time unit;
- spline degree;
- ML/REML mode.

When two successful fits both contain a trial functional random effect, their
source trial identities and trial basis must also match.

Models may differ in the covariance structures being examined: presence of one
declared participant random slope, a trial functional intercept, and
iid/exponential/AR(1) residual correlation. Participant random-basis changes
are not treated as covariance sensitivity because they alter the
parameterization being compared.

## Failed declared structures remain visible

A sensitivity analysis should not become conditional on only the structures
that happened to converge. Failed models can therefore be retained explicitly:

~~~python
sensitivity = functional_mixed_effects_covariance_sensitivity(
    fits={
        "M1": fit_m1,
        "M2": fit_m2,
        "M3": fit_m3,
    },
    specifications=specifications,
    failures={
        "M4": "Optimizer did not converge under the predeclared specification."
    },
    reference="M1",
    max_lag=6,
)
~~~

The failed row is retained with `status="failed"`,
`converged=False`, the supplied reason, and NaN numerical comparison fields.
It is never replaced, silently omitted, or redrawn.

This contract differs intentionally from the inferential bootstrap, where a
failed replicate invalidates the requested bootstrap calculation.

## Fixed coefficient sensitivity

For model \(m\) relative to declared reference \(r\),

\[
\Delta\beta_m(t)
=
\widehat\beta_m(t)-\widehat\beta_r(t).
\]

The result retains every observed-grid difference and summarizes, for each
coefficient,

\[
D_{\infty,m}
=
\sup_t |\Delta\beta_m(t)|
\]

and

\[
D_{2,m}
=
\left[
\int
\{\Delta\beta_m(t)\}^2\,dt
\right]^{1/2},
\]

using trapezoidal integration on the observed time grid.

These are descriptive robustness measures. They are not thresholds for
automatic model rejection or selection.

~~~python
sensitivity.coefficient_frame
sensitivity.coefficient_summary
~~~

~~~python
from eyetrajectoriespy import plot_covariance_sensitivity_coefficients

plot_covariance_sensitivity_coefficients(
    sensitivity,
    coefficient="condition",
)
~~~

The reference appears as the zero-difference function.

## Simultaneous-band sensitivity

If simultaneous-band objects are supplied, they must:

- refer to the supplied fit objects;
- use the same confidence level;
- use the same coefficient/family simultaneous scope;
- use the same fixed-covariance or full-refit bootstrap contract;
- use the same number of participant bootstrap replicates;
- contain **identical participant bootstrap draws**.

This paired-resampling requirement prevents Monte Carlo draw differences from
being confounded with covariance-structure sensitivity.

For model \(m\),

\[
w_m(t)=U_m(t)-L_m(t),
\]

and 0.50 reports

\[
\frac{w_m(t)}{w_r(t)}
\]

against the declared reference. It does not color or annotate a preferred
model.

~~~python
plot_covariance_sensitivity_band_widths(
    sensitivity,
    coefficient="condition",
)
~~~

## Functional variance decomposition

Raw basis covariance matrices can be difficult to compare directly. Version
0.50 therefore reconstructs variance functions.

For the participant random intercept,

\[
v_{\mathrm P0}(t)
=
\mathbf B_P(t)^\top
\boldsymbol\Psi_{\mathrm P0}
\mathbf B_P(t).
\]

When a participant random slope is present, 0.50 retains separately

\[
v_{\mathrm P1}(t)
=
\mathbf B_P(t)^\top
\boldsymbol\Psi_{\mathrm P1}
\mathbf B_P(t)
\]

and the intercept/slope cross-covariance function

\[
c_{\mathrm P01}(t)
=
\mathbf B_P(t)^\top
\boldsymbol\Psi_{\mathrm P01}
\mathbf B_P(t).
\]

The trial functional variance is

\[
v_{\mathrm T}(t)
=
\mathbf B_T(t)^\top
\boldsymbol\Psi_{\mathrm T}
\mathbf B_T(t),
\]

while the pointwise residual marginal variance is

\[
v_\epsilon(t)=\sigma^2.
\]

No participant intercept, slope, and cross-covariance terms are collapsed into
one percentage.

~~~python
from eyetrajectoriespy import (
    functional_mixed_effects_variance_decomposition,
    plot_functional_variance_decomposition,
)

variance = functional_mixed_effects_variance_decomposition(
    fit_m4,
    model_label="M4",
)

plot_functional_variance_decomposition(
    sensitivity,
    model="M4",
)
~~~

## Raw and whitened residual diagnostics

Each successful model is diagnosed on both scales:

- raw ACF/autocovariance;
- raw empirical variogram;
- whitened ACF/autocovariance;
- whitened empirical variogram;
- global residual RMS;
- retained pair counts.

For positive lags \(h=1,\ldots,H\), 0.50 also records

\[
\max_{1\le h\le H}
|\widehat\rho_w(h)|
\]

and

\[
\sum_{h=1}^{H}
\widehat\rho_w(h)^2.
\]

These are descriptive residual-dependence summaries. The package never
minimizes them to choose a covariance structure.

For serial models, the whitened scale remains the relevant diagnostic for
remaining serial structure; raw residuals are expected to retain the modeled
correlation.

## Likelihood, AIC, and BIC

Information criteria are reported only after the strict comparability contract
passes. 0.50 does not compare an ML fit with a REML fit and refuses fixed-design
or fixed-basis changes.

For ML fits, the recorded parameter count for information criteria is

\[
k_{\mathrm{ML}}
=
k_{\mathrm{fixed}}
+
k_{\mathrm{covariance}}.
\]

For REML fits with the same fixed design and basis, the recorded restricted
likelihood convention uses

\[
k_{\mathrm{REML}}
=
k_{\mathrm{covariance}}.
\]

The table retains both the total free-parameter count and the exact
information-criterion parameter count.

The reported quantities are

\[
\mathrm{AIC}
=
-2\ell+2k
\]

and

\[
\mathrm{BIC}
=
-2\ell+k\log n.
\]

For BIC, 0.50 explicitly defines

\[
n
=
n_{\mathrm{curves}}\times n_{\mathrm{observed\ time\ points}}.
\]

That conventional observation count is an auditable calculation rule, not a
claim that clustered functional data have an uncontroversial philosophical
effective sample size.

Every model is compared with the declared reference through
\(\Delta\ell\), \(\Delta\mathrm{AIC}\), and \(\Delta\mathrm{BIC}\). Models are
not sorted by these quantities.

## No naive likelihood-ratio testing

Version 0.50 intentionally does not compute automatic likelihood-ratio
p-values. Covariance comparisons may place variance components or serial
parameters on boundaries, and many declared structures are not regular nested
models. A regular chi-square reference distribution is therefore not assumed.

A separately derived bootstrap LRT could be considered in the future only if a
clear scientific need justifies it.

## Trial-versus-serial competition

The participant–trial–serial hierarchy makes covariance decomposition
scientifically interpretable but also creates possible competition between

\[
u_{ij}(t)
\quad\text{and}\quad
\epsilon_{ij}(t).
\]

For example, compare a trial+iid model with a trial+exponential model using:

- \(\operatorname{tr}(\widehat\Psi_T)\);
- the full \(v_T(t)\) curve;
- \(\widehat\phi\);
- \(\widehat\sigma^2\);
- trial covariance eigenvalues, condition number, and boundary diagnostics;
- raw and whitened residual dependence.

A collapsing trial-variance curve accompanied by a very long fitted residual
range is evidence of covariance-decomposition sensitivity. It is **not** an
automatic instruction to delete either component.

## Reporting

~~~python
from eyetrajectoriespy import (
    functional_mixed_effects_covariance_sensitivity_reporting_text,
)

print(
    functional_mixed_effects_covariance_sensitivity_reporting_text(
        sensitivity
    )
)
~~~

A suitable reporting statement is:

> Covariance structures were compared as a predeclared sensitivity analysis.
> Information criteria, residual diagnostics, fixed coefficient changes,
> simultaneous-band widths where available, and variance-component shifts were
> reported descriptively; no covariance structure was automatically selected.

## Scope boundary

Version 0.50 closes the planned Gaussian covariance-engineering sequence. The
package now supports participant functional intercepts, one participant
functional slope, trial functional intercepts, iid/exponential/AR(1) residuals,
fixed-covariance and full-refit participant bootstrap inference, raw/whitened
residual diagnostics, and explicit covariance sensitivity.

Further development should prioritize distinct scientific capabilities rather
than adding another Gaussian covariance knob.
