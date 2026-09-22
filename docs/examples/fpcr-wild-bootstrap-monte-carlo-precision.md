# Worked example: Monte Carlo precision of wild-bootstrap p-values

This example extends the fixed-family wild-bootstrap testing workflow with finite-B precision diagnostics.

```python
import numpy as np

from eyetrajectoriespy import (
    fit_mfpca,
    fpca_wild_bootstrap_family_test_monte_carlo_precision,
    fpca_wild_bootstrap_monte_carlo_precision_frame,
    fpca_wild_bootstrap_monte_carlo_precision_reporting_text,
    fpca_wild_bootstrap_projection_family_test,
    simulate_planar_trajectories,
    wild_bootstrap_fpca_projection,
)

gaze = simulate_planar_trajectories(
    n_participants=48,
    trials_per_participant=1,
    n_time=41,
    random_state=320,
)
fpca = fit_mfpca(gaze, n_components=3, scaling="dimension_sd")
rng = np.random.default_rng(320)
score1 = fpca.scores[:, 0]
score2 = fpca.scores[:, 1]
scale = 0.20 + 0.20 * np.abs(score1) / max(np.std(score1, ddof=1), 1e-8)
outcome = 0.4 + 0.9 * score1 - 0.25 * score2 + rng.normal(0.0, scale)

base = wild_bootstrap_fpca_projection(
    gaze,
    outcome,
    targets=gaze.subset([0, 1, 2]),
    n_bootstrap=199,
    residual_components=2,
    inference_components=3,
    scaling="dimension_sd",
    multiplier="normal",
    random_state=320,
)

tests = fpca_wild_bootstrap_projection_family_test(
    base,
    null_values=0.0,
    significance_level=0.05,
)

precision = fpca_wild_bootstrap_family_test_monte_carlo_precision(
    tests,
    confidence_level=0.95,
)

print(fpca_wild_bootstrap_monte_carlo_precision_frame(precision))
print(fpca_wild_bootstrap_monte_carlo_precision_reporting_text(precision))
```

## What to inspect

Focus on the adjusted exceedance count, adjusted raw tail probability, exact interval, and `adjusted_alpha_relation`. If an exact interval overlaps alpha, the finite bootstrap run does not sharply separate that resampling probability from the threshold.

The original plus-one p-values remain unchanged. The precision layer is therefore auditable post-processing of the same retained roots rather than a second analysis.

## Failure case

Passing an object other than `FPCAWildBootstrapFamilyTestResult`, a confidence level outside (0, 1), non-finite observed statistics, or a root matrix inconsistent with the stored target/bootstrap dimensions fails explicitly.

## Reporting boundary

The exact interval is about Monte Carlo exceedance probability, not a confidence interval for the centered FPCR projection and not a new family-wise error guarantee.
