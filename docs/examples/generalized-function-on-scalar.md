# Generalized function-on-scalar regression

This example treats a binary AOI-occupancy trajectory as a repeated,
non-Gaussian functional response.

## Model

Suppose every trial contains a binary trajectory

\[
Y_{ij}(t)\in\{0,1\},
\]

where 1 means that the gaze sample belongs to the target AOI. The marginal
model is

\[
\operatorname{logit}
\Pr\{Y_{ij}(t)=1\mid x_{ij}\}
=
\beta_0(t)+x_{ij}\beta_1(t).
\]

## Fit

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

The condition predictor may vary from trial to trial within participant. The
participant remains the independent cluster for robust GEE inference.

## Inspect coefficient functions

~~~python
fit.coefficient_functions
fit.coefficient_standard_errors
fit.mean_functions
~~~

The coefficient curves are on the logit scale. `mean_functions` contains the
fitted marginal Bernoulli probabilities for the observed trial predictor rows.

~~~python
from eyetrajectoriespy import (
    generalized_function_on_scalar_coefficient_frame,
)

coefficient_frame = generalized_function_on_scalar_coefficient_frame(
    fit
)
~~~

## Whole-participant bootstrap

~~~python
from eyetrajectoriespy import (
    bootstrap_generalized_function_on_scalar_coefficients,
    generalized_function_on_scalar_simultaneous_bands,
)

bootstrap = bootstrap_generalized_function_on_scalar_coefficients(
    fit,
    n_bootstrap=1000,
    random_state=51,
)

band = generalized_function_on_scalar_simultaneous_bands(
    bootstrap,
    confidence_level=0.95,
    simultaneous_scope="coefficient",
)
~~~

The bootstrap resamples complete participant bundles. Trials and time points are
never independently resampled.

If a participant is selected twice in one bootstrap replicate, the two sampled
copies receive different GEE cluster IDs.

## Plot

~~~python
from eyetrajectoriespy import (
    plot_generalized_function_on_scalar_coefficients,
)

plot_generalized_function_on_scalar_coefficients(
    band,
    coefficient="condition",
)
~~~

A positive condition coefficient at time \(t\) indicates larger marginal
log-odds of target-AOI occupancy at that time, holding the other declared
predictors fixed.

## Count-valued response

For non-negative integer count functions use the same interface with
`family="poisson"`:

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

The coefficient functions are then on the log scale.

## Reporting

~~~python
from eyetrajectoriespy import (
    generalized_function_on_scalar_reporting_text,
)

print(
    generalized_function_on_scalar_reporting_text(
        fit,
        band=band,
    )
)
~~~

Report the family/link, explicit basis dimension, participant cluster definition,
working-independence choice, robust sandwich covariance, bootstrap resampling
unit and simultaneous scope. Do not describe these marginal coefficients as
conditional random-effects coefficients.
