# Fixed-profile marginal prediction and contrasts

Version 0.52 extends the marginal generalized function-on-scalar model from
link-scale coefficient functions to fixed-profile marginal response functions.
Version 0.53 preserves that prediction system and adds explicit rate versus
expected-count semantics for exposure-adjusted Poisson fits.

For a predeclared scalar predictor profile \(\mathbf x_r\),

\[
\eta_r^{\mathrm{rate}}(t)
=
\mathbf x_r^\top\widehat{\boldsymbol\beta}(t)
\]

is the Poisson log-rate predictor when the fitted model used exposure, and

\[
\lambda_r(t)
=
\exp\{\eta_r^{\mathrm{rate}}(t)\}
\]

is the exposure-adjusted rate. If an explicit target exposure \(E_r(t)>0\) is
supplied,

\[
\eta_r^{\mathrm{count}}(t)
=
\log E_r(t)+\eta_r^{\mathrm{rate}}(t),
\qquad
\mu_r(t)=E_r(t)\lambda_r(t)
\]

gives the expected count.

Bernoulli/logit prediction is unchanged: the inverse-logit of the declared
profile linear predictor is the marginal probability.

## Fixed scientific targets

Prediction profiles are supplied explicitly:

~~~python
import pandas as pd

profiles = pd.DataFrame(
    {
        "profile_id": ["control", "treatment"],
        "condition": [0.0, 1.0],
    }
)
~~~

The table must contain exactly one unique non-missing profile identifier and one
numeric column for every fitted predictor. Profile values are never estimated,
centered, scaled, encoded, averaged, selected, or resampled by the package.

For Bernoulli models or Poisson models fitted without exposure, the established
0.52 call remains valid:

~~~python
from eyetrajectoriespy import generalized_function_on_scalar_predict

prediction = generalized_function_on_scalar_predict(
    fit,
    profiles,
)
~~~

## Exposure-adjusted Poisson prediction

For a Poisson fit estimated with exposure, the default prediction scale is
`"rate"`:

~~~python
rate_prediction = generalized_function_on_scalar_predict(
    rate_fit,
    profiles,
    prediction_scale="rate",
)
~~~

No target exposure is required because the rate estimand is independent of the
amount of exposure.

Expected counts require a new, explicit target exposure:

~~~python
expected_count_prediction = generalized_function_on_scalar_predict(
    rate_fit,
    profiles,
    exposure_profiles=target_exposure,
    prediction_scale="expected_count",
)
~~~

`exposure_profiles` may have shape `(n_profiles, n_time)` or
`(n_profiles,)`; the latter is explicitly expanded over time. Every value must
be finite and strictly positive. If a model was fitted with exposure and
expected-count prediction is requested without target exposure, the function
fails rather than silently assuming \(E=1\). Conversely, target exposure is not
accepted for a rate prediction.

The result retains the selected response scale together with
`rate_functions`, `expected_count_functions`, `linear_predictor_rate`,
`linear_predictor_count`, and the supplied target exposure where applicable.

## Prediction uncertainty

Let \(\widehat{\boldsymbol\Sigma}_\theta\) be the robust covariance of the
B-spline coefficient vector and let \(\mathbf z_r(t)\) be the expanded
profile-by-basis design row. Then

\[
\widehat{\operatorname{Var}}\{\eta_r(t)\}
=
\mathbf z_r(t)^\top
\widehat{\boldsymbol\Sigma}_\theta
\mathbf z_r(t).
\]

Because exposure is treated as fixed, adding \(\log E_r(t)\) changes the
linear-predictor location but not this coefficient-estimation variance.
Response-scale pointwise standard errors use the inverse-link delta method.

## Extrapolation is explicit

For each declared scalar predictor, the package records the observed minimum
and maximum from the fitted data. A profile is flagged when any predictor lies
outside its observed range. An extrapolative profile is retained rather than
silently rejected or clipped, because the target may be intentionally
counterfactual.

This is a scalar-predictor support audit only; it is not a multivariate
positivity, convex-hull, or causal-identification guarantee.

## Participant-bootstrap propagation

The existing whole-participant coefficient bootstrap is reused without drawing
new resampling indices:

~~~python
from eyetrajectoriespy import (
    bootstrap_generalized_function_on_scalar_predictions,
)

rate_bootstrap = bootstrap_generalized_function_on_scalar_predictions(
    coefficient_bootstrap,
    profiles,
    prediction_scale="rate",
)
~~~

For expected-count prediction, the same fixed target exposure is propagated
through every bootstrap draw:

~~~python
count_bootstrap = bootstrap_generalized_function_on_scalar_predictions(
    coefficient_bootstrap,
    profiles,
    exposure_profiles=target_exposure,
    prediction_scale="expected_count",
)
~~~

Profile values and target exposures are not resampled. The coefficient
bootstrap itself resamples the observed source-participant response, design,
and fitted exposure together as one bundle.

## Simultaneous prediction bands

~~~python
from eyetrajectoriespy import (
    generalized_function_on_scalar_prediction_bands,
)

prediction_band = generalized_function_on_scalar_prediction_bands(
    rate_bootstrap,
    confidence_level=0.95,
    simultaneous_scope="profile",
)
~~~

For profile \(r\), bootstrap replicate \(b\), and observed grid point \(t_m\),

\[
M_r^{*(b)}
=
\max_m
\left|
\frac{
\eta_r^{*(b)}(t_m)-\eta_r(t_m)
}{
\widehat{\operatorname{SE}}\{\eta_r(t_m)\}
}
\right|.
\]

With `simultaneous_scope="profile"`, each profile receives its own maximum
critical value. With `simultaneous_scope="family"`, one maximum is taken over
all declared profiles and observed time points.

The calibrated linear-predictor endpoints are transformed through the monotone
inverse link. Bernoulli probability bands therefore remain in \((0,1)\), and
Poisson rate or expected-count bands remain positive without clipping. The
coverage claim is over the observed grid only.

## One predeclared contrast scale

The API retains the one-predeclared-pair philosophy. For Bernoulli models the
available contrast is the probability difference. For an exposure-adjusted
Poisson fit, choose one explicit scale:

~~~python
rate_difference = generalized_function_on_scalar_mean_difference_band(
    rate_bootstrap,
    profile_a="treatment",
    profile_b="control",
    contrast_scale="rate_difference",
)

rate_ratio = generalized_function_on_scalar_mean_difference_band(
    rate_bootstrap,
    profile_a="treatment",
    profile_b="control",
    contrast_scale="rate_ratio",
)
~~~

The quantities are

\[
D_{ab}^{\mathrm{rate}}(t)
=
\lambda_a(t)-\lambda_b(t)
\]

and

\[
RR_{ab}(t)
=
\frac{\lambda_a(t)}{\lambda_b(t)}
=
\exp\{(\mathbf x_a-\mathbf x_b)^\top
\widehat{\boldsymbol\beta}(t)\}.
\]

The rate-ratio band is calibrated on the log-rate-ratio scale and
exponentiated, preserving positivity.

When expected-count predictions were created with explicit target exposures,
the same paired bootstrap draws can instead produce

~~~python
count_difference = generalized_function_on_scalar_mean_difference_band(
    count_bootstrap,
    profile_a="treatment",
    profile_b="control",
    contrast_scale="expected_count_difference",
)
~~~

corresponding to

\[
D_{ab}^{\mathrm{count}}(t)=\mu_a(t)-\mu_b(t).
\]

The package does not automatically generate all three Poisson contrasts, search
over profile pairs, report a best contrast, or claim familywise control over
multiple post-hoc contrasts.

## Frames, plots, and reporting

`generalized_function_on_scalar_prediction_frame()` now records the selected
prediction scale and, where available, rate, expected count, and target
exposure. `generalized_function_on_scalar_mean_difference_frame()` records
both `contrast_scale` and the scale on which inference was calibrated.

The existing plotting and manuscript-reporting helpers adapt their labels to
probability, rate, rate ratio, or expected-count interpretation.

Report at minimum:

- fitted family/link and whether exposure was used;
- exposure definition and units, including why proportional scaling of the
  expected count with exposure is scientifically defensible;
- every fixed profile and scalar predictor value;
- target exposure for expected-count prediction;
- whether any profile was flagged as extrapolative;
- participant-bootstrap size/seed and that exposure travelled with each source
  participant bundle;
- prediction and contrast scales;
- that rate-ratio bands were calibrated on the log scale and exponentiated;
- simultaneous scope and observed-grid-only coverage;
- that profile values, target exposure, and observed exposure are treated as
  fixed rather than measurement-error variables.

## Scope boundary

These functions estimate marginal rate, probability, or expected-count
functions. They do not provide predictive intervals for future stochastic
Bernoulli/count realizations.

The package does not infer exposure, model exposure measurement uncertainty,
expose arbitrary generic offsets, add grouped-binomial denominators, choose a
working correlation automatically, add generalized random effects, or provide
multiple-contrast family adjustment.
