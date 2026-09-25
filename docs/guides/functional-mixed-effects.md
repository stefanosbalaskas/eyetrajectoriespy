# Functional mixed-effects regression

Version 0.36 adds a repeated-measures functional regression model for designs
where several trajectories come from the same participant and scalar predictors
may vary from trial to trial.

The implemented model is

$$
Y_{ij}(t)
=
\mathbf x_{ij}^{\top}\boldsymbol\beta(t)
+
b_i(t)
+
\varepsilon_{ij}(t),
$$

with participant-specific functional random intercept

$$
b_i(t)=\mathbf B_r(t)^\top\mathbf u_i.
$$

This is the repeated-measures counterpart to the 0.35 function-on-scalar
model. It keeps trial-level predictors instead of averaging them away.

## When to use it

Use this model when:

- the response is one common-grid continuous trajectory;
- multiple trials belong to the same participant;
- one or more scalar predictors may vary across those trials;
- participant-specific functional baseline deviations are scientifically
  plausible;
- a Gaussian response model and conditionally iid grid residual structure are
  acceptable for the first model.

Examples include condition effects on speed(t), curvature(t), horizontal
gaze(t), or a windowed RQA metric trajectory.

## Core fit

~~~python
from eyetrajectoriespy import fit_functional_mixed_effects_regression

fit = fit_functional_mixed_effects_regression(
    trajectories,
    design,
    predictors=("condition", "difficulty"),
    participant_column="participant_id",
    dimension="metric",
    fixed_basis_size=6,
    random_basis_size=4,
    spline_degree=3,
    reml=True,
    method="lbfgs",
)
~~~

The scalar design must contain exactly one row per source curve. A
`curve_id` column is recommended and, when present, must match the
trajectory IDs exactly and in order.

Categorical variables and interactions must be encoded explicitly before
fitting.

## What is fitted jointly

Every curve-by-time sample enters one stacked Gaussian linear mixed model.
The fixed-effect design contains predictor-by-B-spline interactions, while the
participant random-effect design contains the declared random B-spline basis.

The package does **not** run one unrelated mixed model at every time point.

This matters because the participant functional random intercept induces a
single covariance structure across the entire observed curve.

## Trial-varying predictors

Trial-varying predictors are allowed.

For example, if each participant experiences both control and treatment trials,

$$
Y_{ij}(t)
=
\beta_0(t)
+
\beta_1(t)\mathrm{Treatment}_{ij}
+
b_i(t)
+
\varepsilon_{ij}(t),
$$

the treatment indicator can vary across \(j\) within participant \(i\).

That is precisely the design that the 0.35 participant-aggregation function
rejects.

## Basis choices are explicit

The mixed-effects layer uses clamped B-spline bases for:

- fixed coefficient functions;
- participant functional random intercepts;
- in 0.45, one optional explicitly declared participant random functional slope;
- in 0.48, one optional explicitly declared nested trial functional random intercept.

The analyst chooses:

- `fixed_basis_size`;
- `random_basis_size`;
- `trial_random_basis_size` when a 0.48 trial functional effect is declared;
- `spline_degree`.

There is no automatic basis-count selection, no smoothing-parameter search,
and no hidden penalization.

A larger basis is more flexible but also increases the number of fixed
parameters and, for the random function, the number of covariance parameters.
Sensitivity analysis across defensible basis sizes is therefore preferable to
treating one arbitrary basis as uniquely correct.

## One guarded participant random functional slope

Version 0.45 can add one participant-specific functional slope for a declared
fixed predictor:

~~~python
fit = fit_functional_mixed_effects_regression(
    trajectories,
    design,
    predictors=("condition",),
    participant_column="participant_id",
    dimension="metric",
    fixed_basis_size=6,
    random_basis_size=4,
    random_slope_predictor="condition",
)
~~~

The slope predictor must vary within every participant. The package does not
select a random slope automatically or silently fall back to an intercept-only
model.

If the shared random basis has size (q), the intercept+slope random vector has
dimension (2q), giving

$
\frac{(2q)(2q+1)}{2}
$

free covariance parameters under the 0.45 unstructured covariance. The package
requires the participant count to exceed that covariance-parameter count before
fitting a random-slope model. For the default (q=4), this means more than 36
participants.

See the dedicated
[random-functional-slope guide](../methods/functional-mixed-effects-random-slope.md).

## Random-effect covariance

The random basis coefficients have an unstructured covariance matrix

$$
\mathbf u_i\sim N(\mathbf 0,\boldsymbol\Psi).
$$

This allows random functional intercept shapes to vary across basis
directions.

If an estimated covariance eigenvalue is at or very near the numerical
boundary, the result is flagged with `boundary_fit=True`. The fit is not
silently relabeled as regular.

## Nested trial functional random intercept

Version 0.48 can add one smooth trial-specific deviation:

~~~python
fit = fit_functional_mixed_effects_regression(
    trajectories,
    design,
    predictors=("condition",),
    participant_column="participant_id",
    trial_column="trial_id",
    trial_random_effect="functional_intercept",
    dimension="metric",
    fixed_basis_size=6,
    random_basis_size=4,
    trial_random_basis_size=3,
)
~~~

The trial effect uses one shared unstructured covariance across all nested
trials. It is not an independent scalar variance-component approximation.
Participant and trial covariance matrices are estimated separately.

The 0.48 nested fit uses the package's profiled Gaussian marginal-likelihood
backend. The historical `statsmodels.MixedLM` route remains unchanged when no
trial effect is requested.

Trial IDs must be unique within participant, every participant must contribute
at least two trials, and the total trial count must exceed the number of free
trial-covariance parameters. No trial effect or trial basis size is selected
automatically.

See the dedicated
[trial-functional-random-effect guide](../methods/functional-mixed-effects-trial-random-effect.md).

## Convergence

A non-converged optimizer result raises an error.

The package does not automatically switch optimizers until one converges,
because that would silently add an analyst decision. If convergence fails,
simplify or revise the declared model/basis or choose a different optimizer
explicitly and report that change.

## Coefficient table and plot

~~~python
from eyetrajectoriespy import (
    functional_mixed_effects_coefficient_frame,
    plot_functional_mixed_effects_coefficient,
)

table = functional_mixed_effects_coefficient_frame(fit)

ax = plot_functional_mixed_effects_coefficient(
    fit,
    coefficient="condition",
)
~~~

The table and plot use pointwise standard errors propagated from the fitted
fixed-parameter covariance matrix when given the raw fit. Version 0.44 also
supports participant-cluster bootstrap simultaneous bands.

## Whole-function simultaneous coefficient inference

Use whole-participant resampling when the inferential claim concerns an entire
fixed coefficient function over the observed grid:

~~~python
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
~~~

Every bootstrap draw samples participants with replacement and carries all
trials/time points for a selected participant together. The fixed coefficient
basis is re-estimated by GLS for every draw.

The fitted participant random-effect covariance, optional shared trial
random-effect covariance, and residual variance are held fixed. This makes the procedure computationally transparent and preserves the
hierarchical resampling unit, but it does **not** propagate variance-component
or basis-selection uncertainty.

Pass the band object directly to
`plot_functional_mixed_effects_coefficient()` for simultaneous rather than
pointwise uncertainty.

See the dedicated
[simultaneous-inference method guide](../methods/functional-mixed-effects-simultaneous-bands.md).

## Full-refit participant bootstrap

Version 0.46 adds a second participant-level uncertainty path:

~~~python
from eyetrajectoriespy import (
    bootstrap_functional_mixed_effects_full_refit,
)

full_boot = bootstrap_functional_mixed_effects_full_refit(
    fit,
    n_bootstrap=1000,
    random_state=2026,
)
~~~

Unlike the faster 0.44 fixed-covariance bootstrap, each replicate refits fixed
coefficients, the complete declared participant covariance, the shared trial
covariance when present, and residual variance.

Duplicate source participants receive distinct bootstrap participant identities.
For a 0.48 nested model, their trials also receive distinct bootstrap trial
identities while retaining source participant/trial IDs for auditability.
Model specification, basis sizes, preprocessing, REML/ML choice, and optimizer
remain fixed.

Use the
[full-refit bootstrap guide](../methods/functional-mixed-effects-full-refit-bootstrap.md)
for the exact inferential and failure contract.

## Residual dependence after fitting

Version 0.47 adds a separate diagnostic layer for dependence that remains in
the conditional residual functions:

~~~python
from eyetrajectoriespy import functional_mixed_effects_residual_diagnostics

residual_diagnostics = functional_mixed_effects_residual_diagnostics(
    fit,
    max_lag=6,
)
~~~

It exposes trial ACF/autocovariance, empirical semivariance, exact physical-lag
pair auditing, participant/overall stratification, and descriptive comparison
across two declared fits. It does **not** automatically choose AR(1), a
trial-level functional random effect, or another covariance structure. See
[Mixed-effects residual diagnostics](../methods/functional-mixed-effects-residual-diagnostics.md).

## Important current limitations

The current mixed-effects layer does not yet estimate:

- explicit residual serial correlation after the declared participant/trial
  functional effects;
- multiple trial random-effect terms;
- generalized/non-Gaussian functional responses;
- multivariate cross-dimension covariance;
- automatic basis-selection uncertainty.

Variance-component uncertainty is available through the 0.46 full-refit
participant bootstrap; it remains distinct from model-selection or
basis-selection uncertainty.

Those omissions are explicit rather than hidden.

## Relationship to the existing multilevel FPCA

`fit_multilevel_fpca()` remains useful for decomposing variation into
participant-level and trial-level functional components:

$$
G_{ij}(t)=\mu(t)+U_i(t)+V_{ij}(t).
$$

It is descriptive/decompositional rather than a regression model for
trial-varying experimental predictors.

`fit_functional_mixed_effects_regression()` instead models the conditional
mean with scalar predictors, a participant functional random intercept,
optionally one explicitly declared participant random functional slope, and
from 0.48 an optional nested trial functional random intercept with its own
shared covariance.

## Evidence basis

Scheipl, Staicu, and Greven (2015) developed functional additive mixed models
for correlated functional responses, including nested/crossed functional
random effects and scalar predictors whose effects vary over the functional
index. Greven and Scheipl (2017) describe the broader functional-regression
framework and the strategy of expressing functional regression through
corresponding scalar mixed/additive models. Morris and Carroll (2006)
established an earlier general functional mixed-model formulation with
functional fixed and random effects.

The implementation remains intentionally narrower than those frameworks. Its
scientific contract is a single Gaussian response dimension, explicit B-spline
bases, one participant functional random intercept, at most one guarded
participant random functional slope, and optionally one nested trial
functional random intercept. Participant-only fits retain the historical
statsmodels backend; the 0.48 nested covariance extension uses an explicit
profiled Gaussian marginal likelihood.
