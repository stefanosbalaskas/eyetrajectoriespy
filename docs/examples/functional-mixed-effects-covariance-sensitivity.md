# Covariance-structure sensitivity

This worked example compares four independently fitted covariance structures
against one declared reference without asking the package to select among them.

## Predeclare the structures

~~~python
from eyetrajectoriespy import (
    FunctionalMixedEffectsCovarianceSpecification,
)

specifications = (
    FunctionalMixedEffectsCovarianceSpecification(
        "M1",
        residual_correlation="iid",
    ),
    FunctionalMixedEffectsCovarianceSpecification(
        "M2",
        trial_random_effect="functional_intercept",
        residual_correlation="iid",
    ),
    FunctionalMixedEffectsCovarianceSpecification(
        "M3",
        residual_correlation="exponential",
    ),
    FunctionalMixedEffectsCovarianceSpecification(
        "M4",
        trial_random_effect="functional_intercept",
        residual_correlation="exponential",
    ),
)
~~~

## Fit the models independently

~~~python
fit_m1 = fit_functional_mixed_effects_regression(
    trajectories,
    design,
    predictors=("condition",),
    participant_column="participant_id",
    dimension="metric",
    fixed_basis_size=3,
    random_basis_size=2,
    residual_correlation="iid",
    reml=False,
)

fit_m2 = fit_functional_mixed_effects_regression(
    trajectories,
    design,
    predictors=("condition",),
    participant_column="participant_id",
    trial_column="trial_id",
    trial_random_effect="functional_intercept",
    trial_random_basis_size=2,
    dimension="metric",
    fixed_basis_size=3,
    random_basis_size=2,
    residual_correlation="iid",
    reml=False,
)

fit_m3 = fit_functional_mixed_effects_regression(
    trajectories,
    design,
    predictors=("condition",),
    participant_column="participant_id",
    dimension="metric",
    fixed_basis_size=3,
    random_basis_size=2,
    residual_correlation="exponential",
    reml=False,
)

fit_m4 = fit_functional_mixed_effects_regression(
    trajectories,
    design,
    predictors=("condition",),
    participant_column="participant_id",
    trial_column="trial_id",
    trial_random_effect="functional_intercept",
    trial_random_basis_size=2,
    dimension="metric",
    fixed_basis_size=3,
    random_basis_size=2,
    residual_correlation="exponential",
    reml=False,
)
~~~

The response functions, fixed design, fixed basis, participant mapping, time
grid, response dimension, and likelihood mode are unchanged. Only declared
covariance structure changes.

## Compare against M1

~~~python
from eyetrajectoriespy import (
    functional_mixed_effects_covariance_sensitivity,
)

result = functional_mixed_effects_covariance_sensitivity(
    fits={
        "M1": fit_m1,
        "M2": fit_m2,
        "M3": fit_m3,
        "M4": fit_m4,
    },
    specifications=specifications,
    reference="M1",
    max_lag=3,
)
~~~

Inspect the model-level table without sorting it:

~~~python
result.model_summary[
    [
        "model",
        "status",
        "log_likelihood",
        "n_parameters",
        "aic",
        "bic",
        "delta_aic",
        "delta_bic",
        "trial_covariance_trace",
        "residual_variance",
        "residual_correlation_parameter",
        "whitened_max_abs_acf_positive_lags",
    ]
]
~~~

These values are descriptive. No row is labelled best.

## Inspect the scientific estimand first

~~~python
result.coefficient_summary
~~~

For each fixed coefficient, this reports the observed-grid supremum and
integrated \(L_2\) difference from M1.

~~~python
from eyetrajectoriespy import (
    plot_covariance_sensitivity_coefficients,
)

plot_covariance_sensitivity_coefficients(
    result,
    coefficient="condition",
)
~~~

If the condition coefficient changes sign, timing, or shape materially across
defensible covariance structures, that sensitivity is scientifically more
important than a small information-criterion difference.

## Inspect covariance attribution

~~~python
result.variance_decomposition
~~~

~~~python
from eyetrajectoriespy import plot_functional_variance_decomposition

plot_functional_variance_decomposition(
    result,
    model="M4",
)
~~~

Participant intercept variance, participant slope variance when present,
intercept/slope cross-covariance, trial variance, and residual variance remain
separate.

## Inspect raw and whitened residual structure

~~~python
diagnostics = result.residual_diagnostics

diagnostics.loc[
    diagnostics["model"].eq("M4"),
    [
        "residual_scale",
        "lag_index",
        "lag_time_mean",
        "n_pairs",
        "autocorrelation",
        "semivariance",
    ],
]
~~~

For correlated-error models, raw residual dependence is expected. The whitened
rows diagnose remaining structure after applying the fitted residual covariance.

## Include a failed predeclared model

Suppose a fifth predeclared AR(1) model cannot be fitted because the observed
time grid is irregular. Keep the failure in the sensitivity analysis:

~~~python
specifications_with_failure = specifications + (
    FunctionalMixedEffectsCovarianceSpecification(
        "M5",
        trial_random_effect="functional_intercept",
        residual_correlation="ar1",
    ),
)

result = functional_mixed_effects_covariance_sensitivity(
    fits={
        "M1": fit_m1,
        "M2": fit_m2,
        "M3": fit_m3,
        "M4": fit_m4,
    },
    specifications=specifications_with_failure,
    failures={
        "M5": "AR(1) rejected because the common grid is irregular."
    },
    reference="M1",
    max_lag=3,
)
~~~

M5 remains in \`model_summary\` with status \`failed\`. Its numerical fields
are NaN; it is not silently removed.

## Add paired simultaneous-band sensitivity

If band-width sensitivity is required, create the bands with the same
participant bootstrap draws for each supplied model:

~~~python
boot_m1 = bootstrap_functional_mixed_effects_coefficients(
    fit_m1,
    n_bootstrap=1000,
    random_state=50,
)
boot_m3 = bootstrap_functional_mixed_effects_coefficients(
    fit_m3,
    n_bootstrap=1000,
    random_state=50,
)

band_m1 = functional_mixed_effects_simultaneous_bands(boot_m1)
band_m3 = functional_mixed_effects_simultaneous_bands(boot_m3)

result = functional_mixed_effects_covariance_sensitivity(
    fits={"M1": fit_m1, "M3": fit_m3},
    reference="M1",
    max_lag=3,
    bands={"M1": band_m1, "M3": band_m3},
)
~~~

The paired-draw guard prevents different bootstrap samples from masquerading as
covariance sensitivity.

## Report the analysis

~~~python
from eyetrajectoriespy import (
    functional_mixed_effects_covariance_sensitivity_reporting_text,
)

print(
    functional_mixed_effects_covariance_sensitivity_reporting_text(
        result
    )
)
~~~

The reporting helper explicitly states that the analysis is predeclared,
descriptive, and does not rank or automatically select a covariance structure.
