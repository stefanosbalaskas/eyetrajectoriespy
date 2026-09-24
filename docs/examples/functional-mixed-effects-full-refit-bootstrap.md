# Worked full-refit participant bootstrap

This example compares the existing fixed-covariance participant bootstrap with
the 0.46 full-refit bootstrap.

Assume \`fit\` is a converged \`FunctionalMixedEffectsResult\`.

## Fixed-covariance bootstrap

\`\`\`python
from eyetrajectoriespy import (
    bootstrap_functional_mixed_effects_coefficients,
)

fixed_boot = bootstrap_functional_mixed_effects_coefficients(
    fit,
    n_bootstrap=1000,
    random_state=2026,
)
\`\`\`

This re-estimates fixed coefficient functions while conditioning on the fitted
mixed-model covariance parameters.

## Full-refit bootstrap

\`\`\`python
from eyetrajectoriespy import (
    bootstrap_functional_mixed_effects_full_refit,
)

full_boot = bootstrap_functional_mixed_effects_full_refit(
    fit,
    n_bootstrap=1000,
    random_state=2026,
)
\`\`\`

Every bootstrap participant occurrence receives a unique bootstrap group ID.

Inspect that mapping directly:

\`\`\`python
from eyetrajectoriespy import (
    functional_mixed_effects_full_refit_audit_frame,
)

audit = functional_mixed_effects_full_refit_audit_frame(full_boot)
print(audit.head())
\`\`\`

If one source participant appears twice in a replicate, its two bootstrap group
IDs differ.

## Inspect variance-component stability

\`\`\`python
from eyetrajectoriespy import (
    functional_mixed_effects_variance_bootstrap_frame,
)

variance = functional_mixed_effects_variance_bootstrap_frame(full_boot)

print(
    variance[
        [
            "residual_variance",
            "covariance_min_eigenvalue",
            "covariance_condition_number",
            "boundary_fit",
            "singular_fit",
        ]
    ].describe()
)
\`\`\`

For a random-slope model the table also includes random-slope covariance trace
and intercept/slope cross-covariance magnitude summaries.

The complete covariance matrices remain available on the result object.

## Build a full-refit simultaneous band

\`\`\`python
from eyetrajectoriespy import (
    functional_mixed_effects_simultaneous_bands,
)

full_band = functional_mixed_effects_simultaneous_bands(
    full_boot,
    confidence_level=0.95,
    simultaneous_scope="coefficient",
)
\`\`\`

## Compare the two uncertainty contracts

\`\`\`python
from eyetrajectoriespy import (
    compare_functional_mixed_effects_bootstraps,
    plot_functional_mixed_effects_bootstrap_comparison,
)

comparison = compare_functional_mixed_effects_bootstraps(
    fixed_boot,
    full_boot,
    confidence_level=0.95,
    simultaneous_scope="coefficient",
)

ax = plot_functional_mixed_effects_bootstrap_comparison(
    comparison,
    coefficient="condition",
)
\`\`\`

A ratio above one means the full-refit band is wider at that observed time.
A ratio near one means the conditional fixed-covariance and full-refit bands are
similar there.

Do not interpret the width ratio as a hypothesis test or automatic preference
for one model.
