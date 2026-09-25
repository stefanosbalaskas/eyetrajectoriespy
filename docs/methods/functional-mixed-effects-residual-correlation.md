# Explicit residual covariance and whitening

Version 0.49 adds an explicit within-trial residual covariance layer to the
Gaussian functional mixed-effects model. The covariance family is always
declared by the analyst; the package does not choose among iid, exponential,
or AR(1) residuals from the observed result.

With participant effect \(b_i(t)\), optional trial functional effect
\(u_{ij}(t)\), and fixed coefficient functions \(\boldsymbol\beta(t)\),

\[
Y_{ij}(t)
=
\mathbf x_{ij}^{\top}\boldsymbol\beta(t)
+
b_i(t)
+
u_{ij}(t)
+
\epsilon_{ij}(t).
\]

The residual vector for each source curve/trial is

\[
\boldsymbol\epsilon_{ij}
\sim
N\!\left(\mathbf 0,\sigma^2\mathbf R_\theta\right).
\]

Residual covariance is **block diagonal by trial**. Observations from different
trials receive zero residual covariance even when their numerical timestamps
are close.

## Continuous-time exponential correlation

The primary physical-time model is

\[
R_\phi(t,s)
=
\exp\!\left(-\frac{|t-s|}{\phi}\right),
\qquad
\phi>0.
\]

Use:

~~~python
fit = fit_functional_mixed_effects_regression(
    trajectories,
    design,
    predictors=("condition",),
    participant_column="participant_id",
    dimension="metric",
    residual_correlation="exponential",
)
~~~

The range parameter is estimated jointly with the other covariance parameters
and is reported in `TrajectorySet.time_unit`. The numerical parameterization
is

\[
\phi=\exp(\eta_\phi).
\]

Natural- and transformed-scale optimizer bounds are retained in provenance. A
fit at or extremely near a numerical bound sets
`residual_correlation_boundary_fit=True`; it is not silently regularized or
replaced.

Because the kernel uses actual elapsed separation \(|t-s|\), it remains
meaningful on an unequally spaced common time grid.

## AR(1)

For a verified equally spaced common grid, 0.49 also permits

\[
R_{rs}=\rho^{|r-s|},
\qquad
-1<\rho<1.
\]

The AR(1) lag is an **index-step lag**. The package rejects AR(1) on an irregular
grid rather than treating one sample step as a constant physical-time interval.

The numerical parameterization is

\[
\rho=\tanh(\eta_\rho).
\]

Negative \(\rho\) is allowed. On a regular grid with spacing \(\Delta\), a
positive AR(1) can be related to an exponential process through

\[
\rho=\exp(-\Delta/\phi),
\]

but exponential correlation cannot represent negative AR(1). The two public
families therefore remain distinct.

## Marginal covariance

For all observations from participant \(i\),

\[
\mathbf V_i
=
\mathbf Z_i\boldsymbol\Psi_{\mathrm P}\mathbf Z_i^\top
+
\sum_j
\mathbf W_{ij}\boldsymbol\Psi_{\mathrm T}\mathbf W_{ij}^\top
+
\sigma^2
\operatorname{blockdiag}_j\{\mathbf R_\theta\}.
\]

The trial term is absent when no trial functional random effect is declared.
The residual-correlation term becomes the identity under
`residual_correlation="iid"`.

Participant covariance, optional trial covariance, residual variance, and the
serial parameter are optimized jointly. Fixed B-spline coefficients are
profiled by generalized least squares at each covariance-parameter evaluation.

The historical participant-only iid model retains its existing
`statsmodels.MixedLM` backend. Any explicitly serial model uses the profiled
Gaussian covariance backend.

## Retained diagnostics

`FunctionalMixedEffectsResult` records the residual-correlation family,
parameter/name/unit, within-trial correlation matrix, eigenvalues, condition
number, natural optimizer bounds, regular-grid status, raw residual functions,
whitened residual functions, and the explicit boundary flag.

The stored correlation matrix is the within-trial matrix. It is sufficient to
reconstruct the complete participant residual block because the residual
process never crosses source-curve/trial boundaries.

## Raw versus whitened residuals

Once a correlated residual process is fitted, raw residual correlation is not
expected to disappear. Under the declared model,

\[
\boldsymbol\epsilon_{ij}
\sim
N(\mathbf 0,\sigma^2\mathbf R_\theta).
\]

If

\[
\sigma^2\mathbf R_\theta=\mathbf L\mathbf L^\top,
\]

define the diagnostic whitened residual vector as

\[
\mathbf e_{ij}^{(w)}=\mathbf L^{-1}\mathbf e_{ij}.
\]

~~~python
from eyetrajectoriespy import (
    functional_mixed_effects_residual_diagnostics,
    functional_mixed_effects_whitened_residuals,
)

white = functional_mixed_effects_whitened_residuals(fit)

raw_diagnostics = functional_mixed_effects_residual_diagnostics(
    fit,
    max_lag=6,
    residual_scale="raw",
)

white_diagnostics = functional_mixed_effects_residual_diagnostics(
    fit,
    max_lag=6,
    residual_scale="whitened",
)
~~~

Raw ACF/variogram values describe the conditional residuals on their native
scale. Whitened diagnostics ask whether important serial structure remains
after applying the declared fitted residual covariance.

Whitening is diagnostic. Fitted fixed/random effects and parameter uncertainty
remain conditioned on their estimates, so the package does not claim that
whitened residuals are independent observations with known parameters.

## Covariance-decomposition diagnostics

A smooth long-range residual process can compete with a smooth trial functional
random effect. A large fitted exponential range, an ill-conditioned
\(\boldsymbol\Psi_{\mathrm T}\), a trial covariance approaching a boundary, or
large shifts in the trial covariance after adding serial correlation should be
treated as covariance-decomposition diagnostics—not automatic evidence that
one component should be deleted.

This is the motivation for the planned 0.50 covariance-structure sensitivity
layer.

## Bootstrap contracts

The fixed-covariance participant bootstrap conditions on the fitted participant
covariance, optional trial covariance, residual variance, and fitted serial
parameter. The full-refit participant bootstrap re-estimates every declared
covariance parameter in each replicate, including \(\phi\) or \(\rho\).

`functional_mixed_effects_variance_bootstrap_frame()` exposes the bootstrap
serial parameter, residual-correlation condition number, and boundary flag
alongside the existing variance-component diagnostics.

No replicate silently switches residual-correlation family.

## Interpretation boundary

Version 0.49 does not infer that serial covariance is required, select
exponential versus AR(1), choose a range from the residual ACF, allow residual
correlation to cross trial boundaries, or treat raw residual correlation as
model failure. Covariance-structure comparison remains an explicit downstream
sensitivity task.
