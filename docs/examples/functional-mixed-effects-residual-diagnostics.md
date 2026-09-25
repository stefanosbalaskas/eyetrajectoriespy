# Mixed-effects residual diagnostics

This worked example starts from a converged
`FunctionalMixedEffectsResult` called `fit`.

## Compute a declared lag window

~~~python
from eyetrajectoriespy import (
    functional_mixed_effects_residual_diagnostics,
    functional_mixed_effects_residual_diagnostic_frame,
    functional_mixed_effects_residual_pair_frame,
)

diagnostics = functional_mixed_effects_residual_diagnostics(
    fit,
    max_lag=6,
)

overall = functional_mixed_effects_residual_diagnostic_frame(
    diagnostics,
    level="overall",
)

overall[
    [
        "lag_index",
        "lag_time_mean",
        "autocorrelation",
        "autocovariance",
        "semivariance",
        "n_trials_acf_defined",
    ]
]
~~~

The lag window is analyst-declared. The package does not increase or shorten it
after inspecting the ACF.

## Inspect one participant or trial

~~~python
participant = functional_mixed_effects_residual_diagnostic_frame(
    diagnostics,
    level="participant",
    participant_id=fit.participant_ids[0],
)

trial = functional_mixed_effects_residual_diagnostic_frame(
    diagnostics,
    level="trial",
    curve_id=fit.source_curve_ids[0],
)
~~~

The participant summary does not replace the trial diagnostics. It is a
pair-count-weighted descriptive summary of them.

## Audit exact physical lag

~~~python
pairs = functional_mixed_effects_residual_pair_frame(
    diagnostics,
    lag_index=2,
    curve_id=fit.source_curve_ids[0],
)

pairs[
    [
        "time_start",
        "time_end",
        "physical_lag",
        "residual_start",
        "residual_end",
        "centered_product",
        "semivariance_contribution",
    ]
]
~~~

This is especially important when the common grid is not equally spaced.
Version 0.47 does not create hidden physical-lag bins.

## Plot ACF and empirical variogram

~~~python
from eyetrajectoriespy import (
    plot_functional_mixed_effects_residual_acf,
    plot_functional_mixed_effects_residual_variogram,
)

plot_functional_mixed_effects_residual_acf(
    diagnostics,
    level="overall",
)

plot_functional_mixed_effects_residual_variogram(
    diagnostics,
    level="overall",
)
~~~

## Compare two declared mixed-effects specifications

~~~python
from eyetrajectoriespy import (
    compare_functional_mixed_effects_residual_diagnostics,
)

comparison = compare_functional_mixed_effects_residual_diagnostics(
    intercept_only_fit,
    random_slope_fit,
    max_lag=6,
    reference_label="intercept only",
    comparison_label="intercept + random condition slope",
)
~~~

Interpret the differences as residual-structure sensitivity evidence, not as an
automatic model-selection criterion.

## Reporting text

~~~python
from eyetrajectoriespy import functional_mixed_effects_residual_reporting_text

print(
    functional_mixed_effects_residual_reporting_text(
        diagnostics,
    )
)
~~~

A defensible report should make clear that these are conditional residuals and
that 0.47 does not choose AR(1), a trial-level functional random effect, or any
other covariance structure.
