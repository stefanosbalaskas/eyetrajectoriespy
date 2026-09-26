# Marginal generalized function-on-scalar regression

Version 0.51 adds a distinct non-Gaussian functional-response model after the
Gaussian mixed-effects covariance sequence was closed at 0.50. Version 0.53
adds an explicit Poisson exposure/rate observation contract without changing
the marginal GEE estimand.

For participant \(i\), trial \(j\), and observed time \(t\),

\[
g\{\mu_{ij}(t)\}
=
\mathbf x_{ij}^{\top}\boldsymbol\beta(t),
\qquad
\mu_{ij}(t)=E\{Y_{ij}(t)\mid\mathbf x_{ij}\}.
\]

The coefficient functions are represented in an analyst-declared clamped
B-spline basis,

\[
\beta_k(t)
=
\mathbf B(t)^\top\boldsymbol\theta_k.
\]

The generalized layer supports two deliberately narrow families:

- Bernoulli responses with logit link;
- Poisson count responses with log link, optionally with an explicit strictly
  positive exposure in version 0.53.

The estimand is **marginal / population averaged**. There are no functional
random effects in this model.

## Why GEE rather than another mixed model

For non-Gaussian outcomes, conditional mixed-model coefficients and marginal
population-average coefficients are not generally numerically equivalent. The
0.51 API therefore makes the estimand explicit instead of reusing the Gaussian
mixed-effects interface.

Every participant is one independent GEE cluster. All of that participant's
trial-by-time observations remain in the fit, so predictors may vary across
trials.

The first tranche fixes the working dependence structure to independence and
uses the robust sandwich covariance. The working correlation is not estimated,
compared, or selected.

## API

~~~python
from eyetrajectoriespy import (
    fit_generalized_function_on_scalar_regression,
)

fit = fit_generalized_function_on_scalar_regression(
    trajectories,
    design,
    predictors=("condition",),
    participant_column="participant_id",
    dimension="target_aoi",
    family="binomial",
    basis_size=4,
    spline_degree=2,
)
~~~

For a count trajectory:

~~~python
count_fit = fit_generalized_function_on_scalar_regression(
    count_trajectories,
    design,
    predictors=("condition",),
    participant_column="participant_id",
    dimension="fixation_count",
    family="poisson",
    basis_size=4,
    spline_degree=2,
)
~~~

No family, link, basis size, interaction, categorical encoding, working
correlation, or model is chosen automatically.

## Expanded design

Let

\[
\mathbf x_{ij}
=
(1,x_{ij1},\ldots,x_{ijp})^\top
\]

and let

\[
\mathbf B(t)
=
(B_1(t),\ldots,B_q(t))^\top.
\]

The stacked GEE design contains the products

\[
x_{ijk}B_r(t),
\]

so each scalar coefficient receives its own \(q\)-dimensional basis coefficient
vector.

The expanded design must be full rank.

## Cluster-count guard

If there are \(K\) scalar coefficients including the intercept and \(q\)
B-spline functions per coefficient, the expanded coefficient vector has

\[
Kq
\]

free parameters.

Version 0.51 requires

\[
n_{\mathrm{participants}}>Kq.
\]

This is a **minimum structural guard**, not a theorem that the robust sandwich
covariance is accurately estimated. The number and heterogeneity of independent
participants remain scientifically important.

## Response contracts

### Bernoulli

The binary response is required to be coded exactly as

\[
Y_{ij}(t)\in\{0,1\}.
\]

Aggregated proportions are not treated as Bernoulli observations and trial
denominators are never inferred silently.

The model is

\[
\operatorname{logit}\{\mu_{ij}(t)\}
=
\mathbf x_{ij}^{\top}\boldsymbol\beta(t).
\]

### Poisson

The count response must be a non-negative integer:

\[
Y_{ij}(t)\in\{0,1,2,\ldots\}.
\]

The model is

\[
\log\{\mu_{ij}(t)\}
=
\mathbf x_{ij}^{\top}\boldsymbol\beta(t).
\]

Without an exposure argument, this remains the 0.51/0.52 expected-count model.

With a scientifically meaningful exposure \(E_{ij}(t)>0\), version 0.53 fits

\[
\log \mu_{ij}(t)
=
\log E_{ij}(t)
+
\mathbf x_{ij}^{\top}\boldsymbol\beta(t),
\]

so that

\[
\lambda_{ij}(t)
=
\frac{\mu_{ij}(t)}{E_{ij}(t)}
=
\exp\{\mathbf x_{ij}^{\top}\boldsymbol\beta(t)\}.
\]

The package exposes **exposure**, not a generic arbitrary offset. Exposure must
be supplied explicitly with shape \`(n_curves, n_time)\`, or with shape
\`(n_curves,)\` when one value applies to a complete curve. Curve-level values
are expanded over time and that expansion is recorded in provenance. Exposure
must be finite and strictly positive everywhere; zero exposure is rejected even
when the observed count is zero.

~~~python
rate_fit = fit_generalized_function_on_scalar_regression(
    count_trajectories,
    design,
    predictors=("condition",),
    participant_column="participant_id",
    dimension="fixation_count",
    family="poisson",
    exposure=observed_duration,
    exposure_units="seconds",
    basis_size=4,
    spline_degree=2,
)
~~~

The package never infers exposure from grid spacing, trial duration, sample
counts, or metadata. The scientific assumption is substantive:
\(E[Y\mid x,E]=E\lambda(x)\), so expected counts are assumed to scale
proportionally with the declared opportunity/time denominator.

## Robust covariance

With working independence, the GEE point estimate is combined with the robust
cluster sandwich covariance,

\[
\widehat{\operatorname{Var}}_{\mathrm{robust}}
(\widehat{\boldsymbol\theta})
=
\mathbf A^{-1}
\mathbf B_{\mathrm{sand}}
\mathbf A^{-1},
\]

where the middle empirical term accumulates cluster-level score contributions.

The package reports coefficient-function pointwise standard errors obtained by
mapping the robust basis-parameter covariance back through \(\mathbf B(t)\).

Naive working-correlation standard errors are not exposed in 0.51.

## Whole-participant bootstrap

For whole-function simultaneous inference, 0.51 resamples participants, not
trial-time rows:

~~~python
from eyetrajectoriespy import (
    bootstrap_generalized_function_on_scalar_coefficients,
)

bootstrap = bootstrap_generalized_function_on_scalar_coefficients(
    fit,
    n_bootstrap=1000,
    random_state=51,
)
~~~

Every sampled participant occurrence carries all of its curves and observed
time points. If a source participant is sampled more than once, each occurrence
receives a distinct bootstrap GEE group identity so duplicated source clusters
are not incorrectly treated as one cluster.

Every bootstrap replicate refits the same family, link, basis and
working-independence GEE.

Failed replicates are not silently dropped or redrawn.

## Simultaneous bands

~~~python
from eyetrajectoriespy import (
    generalized_function_on_scalar_simultaneous_bands,
)

band = generalized_function_on_scalar_simultaneous_bands(
    bootstrap,
    confidence_level=0.95,
    simultaneous_scope="coefficient",
)
~~~

For coefficient \(k\), bootstrap replicate \(b\), and observed grid point
\(t_m\),

\[
M_k^{*(b)}
=
\max_m
\left|
\frac{
\widehat\beta_k^{*(b)}(t_m)
-
\widehat\beta_k(t_m)
}{
\widehat{\mathrm{SE}}\{\widehat\beta_k(t_m)\}
}
\right|.
\]

The resulting band is

\[
\widehat\beta_k(t_m)
\pm
c_{k,1-\alpha}
\widehat{\mathrm{SE}}\{\widehat\beta_k(t_m)\}.
\]

With `simultaneous_scope="family"`, one maximum is taken across all declared
coefficient functions and observed time points.

These are **link-scale coefficient bands**. They are not automatically
converted into probability/count-mean bands because a response-scale effect
depends on the full scalar predictor vector.

Version 0.52 adds that downstream interpretation only after the analyst
declares the complete scalar predictor profile(s). See
[fixed-profile marginal prediction and contrasts](generalized-function-on-scalar-prediction.md).

## Exposure audit

For an exposure-adjusted Poisson fit, inspect the observation contract directly:

~~~python
from eyetrajectoriespy import generalized_function_on_scalar_exposure_frame

exposure_audit = generalized_function_on_scalar_exposure_frame(rate_fit)
print(exposure_audit)
print(exposure_audit.attrs["exposure_audit"])
~~~

The audit reports per-curve minimum/maximum exposure, within-curve range,
whether exposure varies over time, declared units, global minimum/maximum,
between-curve variation, and the global maximum/minimum exposure ratio. Large
ratios are exposed for review rather than automatically rejected.

## Inspect and report

~~~python
from eyetrajectoriespy import (
    generalized_function_on_scalar_coefficient_frame,
    generalized_function_on_scalar_reporting_text,
    plot_generalized_function_on_scalar_coefficients,
)

frame = generalized_function_on_scalar_coefficient_frame(band)

plot_generalized_function_on_scalar_coefficients(
    band,
    coefficient="condition",
)

print(
    generalized_function_on_scalar_reporting_text(
        fit,
        band=band,
    )
)
~~~

## Interpretation

For a Bernoulli/logit model, \(\beta_k(t)\) is a time-varying marginal
log-odds coefficient.

For a Poisson/log model **without exposure**, \(\beta_k(t)\) remains a
time-varying marginal log-mean-count coefficient.

For a Poisson/log model **with explicit exposure**, \(\beta_k(t)\) is a
time-varying marginal log-rate coefficient and
\(\exp\{\beta_k(t)\}\) is a multiplicative rate ratio for a one-unit predictor
change, holding exposure fixed.

These coefficients are not subject-specific effects conditional on functional
random effects.

## Limitations

The generalized contract intentionally does not include:

- aggregated binomial proportions with explicit denominators;
- arbitrary user-defined offsets or silently inferred exposure;
- exposure-measurement-error models;
- negative-binomial or zero-inflated families;
- automatically selected working correlation;
- penalized/smoothing-parameter selection;
- generalized functional random effects;
- sparse/irregular response grids;
- between-grid simultaneous coverage.

Those extensions require separate estimands and validation and are not silently
approximated.
