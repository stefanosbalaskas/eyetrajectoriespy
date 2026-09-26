# Canonical workflows

Version 0.55 introduces a **canonical workflow layer**. It does not add a new
estimator. Its purpose is to make the existing package navigable by scientific
question rather than by function count.

Start with one of five routes:

| Scientific question | Canonical route | Primary entry point |
|---|---|---|
| What are the dominant modes of continuous gaze variation? | [Continuous gaze exploration + FPCA](fpca-exploration.md) | `fit_fpca()` / `fit_mfpca()` |
| How does an experimental predictor change a continuous response over time? | [Experimental functional regression](experimental-functional-regression.md) | `fit_function_on_scalar_regression()` |
| How does a repeated-trial functional response vary with predictors while respecting participant/trial hierarchy? | [Repeated-trial functional mixed effects](repeated-trial-mixed-effects.md) | `fit_functional_mixed_effects_regression()` |
| How does a repeated binary/count functional response change with predictors? | [Generalized binary/count responses](generalized-responses.md) | `fit_generalized_function_on_scalar_regression()` |
| Is the scientific target recurrent or nonlinear temporal structure rather than a mean trajectory? | [Nonlinear/recurrence analysis](nonlinear-recurrence.md) | `recurrence_matrix()` / `rqa_metrics()` |

Each route follows the same discipline:

1. define the scientific response and sampling unit;
2. make preprocessing choices explicit;
3. fit one declared model/specification;
4. inspect uncertainty and diagnostics appropriate to that model;
5. perform sensitivity analysis only when scientifically predeclared;
6. report the estimand, clustering/resampling unit, assumptions, failures and
   provenance.

The [capability inventory](../reference/capability-inventory.md) contains the
full advanced surface. The [API stability policy](../reference/api-stability.md)
explains canonical, advanced, diagnostic and experimental status.
