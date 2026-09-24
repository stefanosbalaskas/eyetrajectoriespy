# Worked full-refit mixed-effects bootstrap

Assume `fit` is a previously fitted
`FunctionalMixedEffectsResult`.

## Run the full-refit participant bootstrap

```python
from eyetrajectoriespy import (
    bootstrap_functional_mixed_effects_full_refit,
)

full = bootstrap_functional_mixed_effects_full_refit(
    fit,
    n_bootstrap=1000,
    random_state=2026,
)
```

Each bootstrap replicate samples whole participants. A duplicate source
participant receives a new group identity for each occurrence.

## Audit participant identities

```python
from eyetrajectoriespy import (
    functional_mixed_effects_bootstrap_identity_frame,
)

identity = functional_mixed_effects_bootstrap_identity_frame(full)

print(
    identity[
        [
            "replicate",
            "draw_position",
            "source_participant_id",
            "bootstrap_participant_id",
        ]
    ].head()
)
```

The source identifier preserves provenance. The bootstrap identifier is the
group label actually used for the refitted mixed model.

## Inspect covariance stability

```python
from eyetrajectoriespy import (
    functional_mixed_effects_variance_bootstrap_frame,
)

variance = functional_mixed_effects_variance_bootstrap_frame(full)

print(
    variance[
        [
            "replicate",
            "residual_variance",
            "covariance_condition_number",
            "boundary_fit",
            "random_effect_singular",
            "random_slope_boundary_fit",
        ]
    ]
)
```

The complete covariance matrices and covariance blocks remain available on the
bootstrap result object itself.

## Build a full-refit simultaneous band

```python
from eyetrajectoriespy import (
    functional_mixed_effects_simultaneous_bands,
)

full_band = functional_mixed_effects_simultaneous_bands(
    full,
    confidence_level=0.95,
    simultaneous_scope="coefficient",
)
```

The band provenance records that variance components were refit.

## Compare with the fixed-covariance bootstrap

```python
from eyetrajectoriespy import (
    bootstrap_functional_mixed_effects_coefficients,
    compare_functional_mixed_effects_bootstraps,
)

fixed = bootstrap_functional_mixed_effects_coefficients(
    fit,
    n_bootstrap=1000,
    random_state=2026,
)

comparison = compare_functional_mixed_effects_bootstraps(
    fixed,
    full,
)

print(
    comparison[
        [
            "coefficient",
            "time",
            "fixed_covariance_band_width",
            "full_refit_band_width",
            "full_to_fixed_width_ratio",
        ]
    ]
)
```

Interpret the width ratio descriptively. It measures sensitivity of fixed-effect
uncertainty to variance-component refitting; it is not a p-value, Bayes factor,
or model-selection criterion.

## Reporting boundary

State explicitly that the bootstrap refits fixed effects,
\(\widehat{\Psi}\), and \(\widehat{\sigma}^2\) in every participant resample,
while preprocessing, predictor specification, random-slope choice, random-effect
structure, bases, optimizer and REML/ML choice remain fixed.
