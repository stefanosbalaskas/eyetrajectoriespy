# R40 — fresh-source Gaussian REML optimizer stress: log vs linear nuisance variances

**Research-only prespecified numerical falsification study.** No variance significance test, global-likelihood certificate, CR2 confidence interval, simultaneous band, API support, or release qualification. Draft stacked on [R39](w3-r39-nuisance-coordinate-results.md), not protected main.

## Question

R39 observed that a **raw-NLL optimizer using positive linear nuisance variance ratios** found the best observed restricted Gaussian likelihood across all 60 of its original single-block optimization configurations, compared with 54/60 converged near-best fits using log variance ratios. That result reused a single R37 primitive Gaussian source block. R40 asks whether the raw linear-coordinate advantage *persists on genuinely new Gaussian primitive blocks* under deliberately difficult near-boundary nuisance initialization, or whether it was a local numerical accident.

## Fresh generating blocks and exact design

Master seed **202610164040**, distinct from R37–R39. Generate **8 independent primitive Gaussian source blocks**, each with **24 participants**, native irregular repeated trials, under original R17 participant/trial/sensor innovations and Gaussian model. Within each block, ordinary and extreme predictor support and genuine true-zero vs positive participant-slope variants are **paired** on the source innovation structure. The true-zero variant removes the actual participant-slope innovations and reconstructs trajectories from the remaining identical primitive draws, not a variance label applied to data that still contain a slope.

Number of independent primitive generating blocks = **8**; there are **32 paired support/state source evaluations** (not 32 independent blocks). Only the *observed* responses, covariates, design matrices, trial IDs and time points may enter the Gaussian likelihood. No true covariance components or simulator innovations are provided to the estimator.

Evaluate two frozen **nonnegative** fixed participant random-slope variance ratios: **0** (mathematical exact zero) and **0.75** relative to the observed-only residual reference scale. In each, optimize strictly **positive** intercept, trial and sensor nuisance variances from three fixed, observed-data-blind starting triples (in observed-reference ratio units):

| Start | Intercept | Trial | Sensor |
|---|---:|---:|---:|
| Interior | 0.2 | 0.2 | 1 |
| Intercept near positive lower bound | exp(-13.8) × 1.01 | 0.5 | 1 |
| Trial near positive lower bound | 0.5 | exp(-13.8) × 1.01 | 1 |

Comparison is **raw Gaussian restricted negative loglikelihood only** (no centering). Use exactly the R39 L-BFGS-B settings and physical nuisance box bounds **[exp(-13.8), exp(7)]** for both parameterizations:

1. Log nuisance variances with analytic log-gradient.
2. Direct positive linear nuisance variance ratios with analytic chain-rule variance-ratio gradient.

Thus **8 primitive blocks × 2 predictor supports × 2 generating slope states × 2 fixed slope ratios × 3 numerical starts × 2 parameterizations = 384 planned fits**. Every optimizer status, error, fitted NLL and physical-coordinate projected first-order residual remains in the original case ledger.

## Prespecified comparisons and strict numerical gate

Within each paired source and fixed-slope profile, determine the *lowest observed NLL among all converged candidates* as a **conditional numerical reference only**, not a global likelihood optimum. A converged fit is considered near-best when its NLL exceeds that within-source reference by at most **0.001**. Compare both methods using the identical case/start and report negative or positive matched NLL differences and failures with the *full denominator*.

Additionally, independently recompute the R35 Gaussian restricted likelihood at every finite fitted solution and inspect the **physical linear-variance-ratio projected KKT gradient**, with a stringent numerical threshold of **0.001**. This threshold is a diagnostic, not a statistical cutoff and not a guarantee of global optimality. A strong preliminary **numerical-only** gate requires *all 384 fits* to be present, no source failures, no optimizer failures or nonconvergence, no converged inferior NLL endpoints >0.001 and no accepted finite fits exceeding the physical KKT threshold. **Failure of any part remains a negative finding.** Passing this gate would not certify a global optimum or statistical validity.

Do not drop failed starts or quote 384 as independent draws. The source-level independent denominator remains **8 primitive blocks**.

## Next steps and exclusions

A finding that positive linear coordinates reduce unsuccessful optimization would justify more numerical stress under fresh sources with missing observations, trial imbalance, incorrect covariance structure, and independent model implementations. It would **not** qualify an estimated-covariance CR2 standard error, Satterthwaite reference, nominal 90% pointwise regression coefficient coverage, or simultaneous 90% function-wide confidence bands.

Keep scientific blockers [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) open, preserve the original R20, R22, R33–R39 negative outcomes, and do not merge into main, alter stable APIs or publish eyetrajectoriespy 1.2 to PyPI.
