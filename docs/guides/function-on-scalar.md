# Function-on-scalar regression

Version 0.35 adds function-on-scalar regression for asking how scalar experimental predictors change a functional gaze response over trial time.

The model is

$$
Y_i(t)
=
\beta_0(t)
+
\beta_1(t)X_{i1}
+
\cdots
+
\beta_p(t)X_{ip}
+
\varepsilon_i(t).
$$

Typical functional responses include horizontal or vertical gaze position, speed, signed curvature, turning rate, or RQA-derived trajectories such as recurrence rate, determinism, and laminarity.

## Core fit

~~~python
from eyetrajectoriespy import fit_function_on_scalar_regression

fit = fit_function_on_scalar_regression(
    trajectories,
    design,
    predictors=("condition", "difficulty", "condition_x_difficulty"),
    dimensions=("metric",),
)
~~~

The design must contain exactly one row per source trajectory. A `curve_id` column is recommended and, when present, must match `trajectories.curve_ids` exactly and in order. Without `curve_id`, the design must retain the default row index so alignment is explicit.

Version 0.35 always adds an intercept. Every predictor must already be numeric and finite.

The package does **not** automatically:

- dummy-code categorical variables;
- create interactions;
- center or standardize predictors;
- smooth coefficient functions;
- expand coefficients in a spline/basis system;
- regularize coefficients;
- select predictors or time windows.

These are analysis decisions rather than hidden preprocessing.

## What the result contains

`FunctionOnScalarResult` retains:

- coefficient functions with shape coefficient × time × selected dimension;
- HC1 pointwise sandwich standard errors;
- fitted and residual functions;
- the functional responses actually used for inference;
- the exact design matrix and its rank;
- residual degrees of freedom;
- coefficient and predictor names;
- inference-unit IDs and curves per unit;
- time, coordinate, and functional-dimension semantics;
- source curve IDs and full provenance.

## Independent curves

Use `unit="curve"` only when each trajectory is genuinely an independent sampling unit for the inferential claim.

~~~python
fit = fit_function_on_scalar_regression(
    gaze,
    design,
    predictors=("condition",),
    unit="curve",
)
~~~

Supplying a participant column while asking for curve-level inference is rejected. The package does not silently cluster or infer a participant identifier from a column name.

## Repeated trials: participant aggregation only in 0.35

For repeated trials from the same participant, version 0.35 supports a deliberately limited route:

~~~python
fit = fit_function_on_scalar_regression(
    gaze,
    design,
    predictors=("expert", "age"),
    unit="participant",
    participant_column="participant_id",
)
~~~

The response trajectories are averaged within participant, every participant receives one inferential unit, and every declared predictor must be constant within that participant.

This supports between-participant function-on-scalar questions such as

$$
Y_i(t)
=
\beta_0(t)
+
\beta_1(t)\mathrm{Expert}_i
+
\beta_2(t)\mathrm{Age}_i
+
\varepsilon_i(t).
$$

It does **not** support trial-varying within-participant condition effects. If `condition` changes across trials within the same participant, participant mode raises an error instead of averaging the predictor or pretending trials are independent.

That case belongs to the planned repeated-measures functional regression / functional mixed-effects tranche.

## Wild-bootstrap coefficient functions

~~~python
from eyetrajectoriespy import bootstrap_function_on_scalar_coefficients

boot = bootstrap_function_on_scalar_coefficients(
    fit,
    n_bootstrap=1000,
    multiplier="rademacher",
    random_state=2026,
)
~~~

The bootstrap keeps the design fixed and multiplies each **complete residual function** by one random multiplier per independent inference unit. Supported multipliers are `"rademacher"` and `"normal"`.

Holding the design fixed has an important audit advantage: a valid full-rank design does not become singular because a pairs bootstrap happened to omit a predictor level.

## Simultaneous coefficient bands

~~~python
from eyetrajectoriespy import function_on_scalar_simultaneous_bands

band = function_on_scalar_simultaneous_bands(
    boot,
    confidence_level=0.95,
    simultaneous_scope="coefficient",
)
~~~

With `simultaneous_scope="coefficient"`, each coefficient receives its own critical value based on the maximum absolute studentized bootstrap deviation across every selected time point and functional dimension.

With `simultaneous_scope="family"`, one maximum is taken across coefficient × time × dimension, producing one shared critical value for the declared coefficient family.

The claim is simultaneous on the **observed grid** only. Version 0.35 does not claim continuous-domain coverage between observed times.

## Plot and export

~~~python
from eyetrajectoriespy import (
    function_on_scalar_coefficient_frame,
    plot_function_on_scalar_coefficients,
)

ax = plot_function_on_scalar_coefficients(
    band,
    coefficient="condition",
    dimension="metric",
)

table = function_on_scalar_coefficient_frame(
    fit,
    band=band,
)
~~~

A simultaneous band excluding zero over a region is evidence that the coefficient is incompatible with zero over that observed-grid region under the declared model and bootstrap procedure. Do not convert this into an automatically discovered onset/offset claim without a predeclared excursion-set or multiplicity procedure.

## Derived nonlinear and geometric responses

The main reason this model belongs in eyetrajectoriespy is that it connects continuous derived trajectories to experimental predictors.

Examples include

$$
\kappa_i(t)
=
\beta_0(t)
+
\beta_1(t)\mathrm{Expert}_i
+
\varepsilon_i(t),
$$

and, after `windowed_rqa_trajectory_set()`,

$$
\mathrm{DET}_i(t)
=
\beta_0(t)
+
\beta_1(t)\mathrm{Condition}_i
+
\varepsilon_i(t).
$$

The regression does not erase the provenance of how curvature, speed, or RQA trajectories were constructed. Report those upstream analytical decisions together with the regression specification.

## Methodological boundary

Version 0.35 is intentionally not a functional mixed-effects model. It does not estimate participant-specific random functional intercepts/slopes, within-participant covariance, or trial-level repeated-measures effects.

The next repeated-measures tranche should be researched and specified as a genuine functional mixed model rather than approximated by a collection of unrelated pointwise mixed models.

## Evidence basis

Morris (2015) classifies functional response regression / function-on-scalar regression as one of the three fundamental functional-regression configurations. Chang, Lin, and Ogden (2017) study simultaneous confidence bands for general function-on-scalar regression and propose wild-bootstrap calibration that accommodates multiple covariates and heteroscedastic functional responses.

The 0.35 contribution is therefore not novelty of function-on-scalar regression itself. It is the package-specific contract: explicit design alignment, no hidden smoothing/encoding, fail-closed repeated-trial handling, provenance, deterministic bootstrap seeding, and observed-grid simultaneous inference.
