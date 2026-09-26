# Fixed-profile marginal prediction and contrasts

Version 0.52 extends the 0.51 marginal generalized function-on-scalar model from
link-scale coefficient functions to directly interpretable **fixed-profile
marginal response functions**.

For a predeclared scalar predictor profile \(\mathbf x_r\),

\[
\eta_r(t)
=
\mathbf x_r^\top\widehat{\boldsymbol\beta}(t)
\]

is the fitted linear predictor and

\[
\mu_r(t)
=
g^{-1}\{\eta_r(t)\}
\]

is the fitted marginal response function.

For Bernoulli/logit models, \(\mu_r(t)\) is a marginal probability function.
For Poisson/log models, it is a marginal expected-count function under the
current no-offset contract.

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

The table must contain exactly:

- one unique non-missing profile identifier column;
- one numeric column for every predictor used in the fitted model.

No profile values are estimated, centered, scaled, encoded, averaged, or
resampled by the package.

~~~python
from eyetrajectoriespy import (
    generalized_function_on_scalar_predict,
)

prediction = generalized_function_on_scalar_predict(
    fit,
    profiles,
)
~~~

## Prediction uncertainty

Let \(\widehat{\boldsymbol\Sigma}_\theta\) be the retained robust covariance of
the B-spline coefficient vector and let \(\mathbf z_r(t)\) be the expanded
profile-by-basis design row. Then

\[
\widehat{\operatorname{Var}}\{\eta_r(t)\}
=
\mathbf z_r(t)^\top
\widehat{\boldsymbol\Sigma}_\theta
\mathbf z_r(t).
\]

The pointwise standard error of the marginal mean uses the inverse-link delta
method,

\[
\widehat{\operatorname{SE}}\{\mu_r(t)\}
=
\left|
\frac{d\,g^{-1}(\eta)}{d\eta}
\right|_{\eta=\eta_r(t)}
\widehat{\operatorname{SE}}\{\eta_r(t)\}.
\]

For logit,

\[
\frac{d\mu}{d\eta}=\mu(1-\mu),
\]

and for log,

\[
\frac{d\mu}{d\eta}=\mu.
\]

## Extrapolation is explicit

For each declared scalar predictor, version 0.52 records the observed minimum
and maximum from the fitted data. A profile is flagged when any predictor lies
outside its observed range.

An extrapolative profile is **retained**, not silently rejected or clipped,
because the scientific target may be intentionally counterfactual. The flag
must therefore be reported and interpreted.

The check is scalar-predictor support only. It does not claim multivariate
convex-hull support or causal identification.

## Participant-bootstrap propagation

The 0.51 whole-participant coefficient bootstrap is reused without drawing any
new resampling indices:

~~~python
from eyetrajectoriespy import (
    bootstrap_generalized_function_on_scalar_predictions,
)

prediction_bootstrap = (
    bootstrap_generalized_function_on_scalar_predictions(
        coefficient_bootstrap,
        profiles,
    )
)
~~~

Every bootstrap coefficient draw is projected through **all** fixed profiles.
This preserves the dependence among profile predictions because all profiles
use the same participant-bootstrap replicate.

The targets themselves are not resampled.

## Simultaneous prediction bands

~~~python
from eyetrajectoriespy import (
    generalized_function_on_scalar_prediction_bands,
)

prediction_band = generalized_function_on_scalar_prediction_bands(
    prediction_bootstrap,
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

With \`simultaneous_scope="profile"\`, each profile receives its own maximum
critical value. With \`simultaneous_scope="family"\`, one maximum is taken over
all declared profiles and observed time points.

The calibrated linear-predictor interval

\[
[\eta_{r,L}(t),\eta_{r,U}(t)]
\]

is transformed through the strictly monotone inverse link,

\[
[
g^{-1}\{\eta_{r,L}(t)\},
g^{-1}\{\eta_{r,U}(t)\}
].
\]

Consequently, Bernoulli bands remain inside \((0,1)\), and Poisson expected-count
bands remain positive without clipping.

The coverage claim is over the **observed grid** only.

## One predeclared response-scale mean difference

Version 0.52 also supports one explicit profile contrast,

\[
D_{ab}(t)
=
\mu_a(t)-\mu_b(t).
\]

For Bernoulli outcomes this is a marginal probability/risk difference. For
Poisson outcomes it is an expected-count difference under the current
no-offset model.

~~~python
from eyetrajectoriespy import (
    generalized_function_on_scalar_mean_difference_band,
)

difference = generalized_function_on_scalar_mean_difference_band(
    prediction_bootstrap,
    profile_a="treatment",
    profile_b="control",
    confidence_level=0.95,
)
~~~

The same participant-bootstrap draws are propagated through both profiles, so
their covariance is retained automatically.

The pointwise bootstrap standard deviation is used to studentize the
mean-difference function, and one maximum over observed time calibrates the
simultaneous band.

The package does **not** search over profile pairs, report a best contrast, or
claim familywise error control across multiple post-hoc contrasts.

For Bernoulli models the logical range of a probability difference is
\([-1,1]\). If an untrimmed studentized band extends outside that range, version
0.52 records this diagnostic and retains the actual interval rather than
silently clipping it.

## Frames and plots

~~~python
from eyetrajectoriespy import (
    generalized_function_on_scalar_prediction_frame,
    generalized_function_on_scalar_mean_difference_frame,
    plot_generalized_function_on_scalar_predictions,
    plot_generalized_function_on_scalar_mean_difference,
)

prediction_frame = generalized_function_on_scalar_prediction_frame(
    prediction_band
)

difference_frame = (
    generalized_function_on_scalar_mean_difference_frame(
        difference
    )
)

plot_generalized_function_on_scalar_predictions(
    prediction_band
)

plot_generalized_function_on_scalar_mean_difference(
    difference
)
~~~

## Reporting

Report:

- the fitted family/link and original 0.51 coefficient-basis contract;
- every fixed profile and its scalar predictor values;
- whether each profile was flagged as extrapolative;
- the participant-bootstrap size and seed inherited from the coefficient
  bootstrap;
- whether simultaneous scope was profile-specific or across the complete
  declared profile family;
- that calibration occurred on the linear-predictor scale and response bands
  were obtained by monotone inverse-link transformation;
- the exact predeclared profile pair for a mean difference;
- whether a Bernoulli difference band exceeded the logical \([-1,1]\) range;
- that no between-grid simultaneous coverage or automatic profile/contrast
  selection is claimed.

## Scope boundary

Version 0.52 predicts **marginal mean functions**, not future individual
Bernoulli/count trajectories. It therefore does not provide predictive
intervals for new stochastic response realizations.

The fixed profile values are treated as known targets. Their own measurement or
estimation uncertainty is not propagated.

The tranche also does not add Poisson exposure offsets, grouped-binomial
denominators, alternative working correlations, generalized random effects, or
multiple-contrast family adjustment.
