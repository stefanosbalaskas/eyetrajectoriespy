# Generalized FoSR fixed-profile prediction

This example turns a fitted Bernoulli functional GEE into marginal probability
trajectories for two predeclared condition profiles.

## Declare profiles

~~~python
import pandas as pd

profiles = pd.DataFrame(
    {
        "profile_id": ["low", "high"],
        "condition": [-0.7, 0.7],
    }
)
~~~

The profiles are fixed scientific targets. Their values are not estimated or
resampled.

## Predict marginal probabilities

~~~python
from eyetrajectoriespy import (
    generalized_function_on_scalar_predict,
)

prediction = generalized_function_on_scalar_predict(
    fit,
    profiles,
)

prediction.mean_functions
prediction.extrapolation_flags
~~~

For a Bernoulli/logit fit, `mean_functions` contains marginal probabilities.

## Propagate the participant bootstrap

~~~python
from eyetrajectoriespy import (
    bootstrap_generalized_function_on_scalar_predictions,
    generalized_function_on_scalar_prediction_bands,
)

prediction_bootstrap = (
    bootstrap_generalized_function_on_scalar_predictions(
        coefficient_bootstrap,
        profiles,
    )
)

prediction_band = generalized_function_on_scalar_prediction_bands(
    prediction_bootstrap,
    confidence_level=0.95,
    simultaneous_scope="family",
)
~~~

No new bootstrap sample is drawn. Each coefficient-bootstrap replicate is
projected through both profiles.

The simultaneous calibration is performed on the logit scale and the endpoints
are transformed back to probabilities.

## Inspect the probability functions

~~~python
from eyetrajectoriespy import (
    generalized_function_on_scalar_prediction_frame,
    plot_generalized_function_on_scalar_predictions,
)

frame = generalized_function_on_scalar_prediction_frame(
    prediction_band
)

plot_generalized_function_on_scalar_predictions(
    prediction_band
)
~~~

The response-scale bands remain inside the valid probability range.

## Compare two profiles directly

~~~python
from eyetrajectoriespy import (
    generalized_function_on_scalar_mean_difference_band,
    generalized_function_on_scalar_mean_difference_frame,
    plot_generalized_function_on_scalar_mean_difference,
)

difference = generalized_function_on_scalar_mean_difference_band(
    prediction_bootstrap,
    profile_a="high",
    profile_b="low",
)

difference_frame = (
    generalized_function_on_scalar_mean_difference_frame(
        difference
    )
)

plot_generalized_function_on_scalar_mean_difference(
    difference
)
~~~

For a Bernoulli response this is the marginal probability difference

\[
P(Y=1\mid\text{high})-
P(Y=1\mid\text{low})
\]

at each observed time point.

The same bootstrap replicate is used for both profiles, so the contrast does
not incorrectly treat their prediction errors as independent.

## Extrapolative target

~~~python
profiles_extra = pd.DataFrame(
    {
        "profile_id": ["observed_high", "beyond_observed"],
        "condition": [0.7, 1.5],
    }
)

extra_prediction = generalized_function_on_scalar_predict(
    fit,
    profiles_extra,
)

extra_prediction.extrapolation_flags
~~~

The second profile is retained and flagged. The package does not silently
truncate it to the observed predictor range.

## Reporting

~~~python
from eyetrajectoriespy import (
    generalized_function_on_scalar_prediction_reporting_text,
    generalized_function_on_scalar_mean_difference_reporting_text,
)

print(
    generalized_function_on_scalar_prediction_reporting_text(
        prediction_band
    )
)

print(
    generalized_function_on_scalar_mean_difference_reporting_text(
        difference
    )
)
~~~

For Poisson/log models the same workflow returns marginal expected-count
functions and expected-count differences.
