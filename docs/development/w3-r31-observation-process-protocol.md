# R31 — explicit sample loss and trial dropout in original native Gaussian trajectories

**Research-only estimator reliability study, not inferred pointwise or simultaneous confidence-interval coverage.** R26–R30 established that estimated covariance-component recovery can be difficult, especially for random-slope variance. Their sources were complete irregular Gaussian trajectory sets. The actual observation process—missing gaze samples and trial dropout—must therefore be audited before a covariance estimator is judged adequate for irregular eye tracking.

## Original source and fully prespecified observation mechanisms

New master seed **202610153131**, **12 independent Gaussian generating source blocks**, nested participant n24 and n96, original jittered/irregular time grids with 1–3 native trials/participant, ordinary predictor-independent and predictor-dependent covariance mechanisms, and fixed Legendre-5 functional mean basis. Four within-block observation regimes are evaluated:

- **Complete:** All original observed rows and trial series, unchanged.
- **MCAR point loss:** Each original timepoint deleted with independent probability 0.20. Masks use deterministic participant/trial seed `202610153132`.
- **Observed-time MAR point loss:** The deletion probability rises from 0.05 at the first observed native time to 0.35 at the last (about 0.20 on average); depends only on observed time, never gaze outcome.
- **Predictor-dependent MAR trial dropout:** For a participant with more than one trial, drop at most one of the later recorded trials with probability 0.35 (x≤0) or 0.60 (x>0), preserving at least one participant trial. Dropout depends on the observed participant predictor and trial order, not unobserved outcomes.

This yields **192 paired source evaluations** (12 independently seeded blocks × 2 sample sizes × 2 source covariance mechanisms × 4 observation regimes), but only **12 independent generating blocks**. There is no MNAR arm; none of these experiments identifies an MNAR mechanism. Across observed regimes, use the identical latent random effects and native source values, with sample/trial indices deleted but **never interpolated, shifted, regenerated or imputed**. Retained source `IrregularTrajectorySet` time and value arrays must exactly equal the matching subarrays of the original generating trajectories. Participant IDs, original trial IDs, ordered curve IDs, trial metadata and native timestamps remain aligned; no participant may disappear. The same participant- and trial-specific observation masks should be nested and identical for n24 within n96 original source designs.

The original observation-only WLS weighting scheme assigns each retained participant total weight one, splitting weight among its **remaining** trials and timepoints. This is part of the predeclared observed-data estimator procedure, not a claim that weighting makes MAR ignorable. In particular, selective loss of later times or participant-predictor-correlated trials may bias mean and covariance estimation despite exactly preserving native measurements.

## Fitted covariance reliability comparisons

In every source/observation case, fit (1) unchanged leverage-adjusted nonnegative covariance-component NNLS and (2) independent Gaussian restricted-likelihood REML, both on **the identical retained observed gaze samples**, using the predeclared matching shared or predictor-scaled random-slope covariance kernel. The nuisance estimators receive no Gaussian innovations or known source variance components, only retained native trajectory responses, times, identifiers, predictor labels and weights.

Report sample missingness and trial dropout achieved for each generating block and observation cell, both estimators' fitting failures, REML optimizer nonconvergence, NNLS floors and covariance boundary frequencies, and absolute relative component recovery error. Source-known positive component variance is used only after fitting, for a common simulation diagnostic of **estimated component below 5% true variance** for both methods. The Gaussian population covariance structure is matched before observation selection, but observation-related bias is not assumed away.

The primary paired diagnostic is the *difference in slope absolute-relative component error* (each incomplete-observation regime minus its own complete-data source baseline). Resample **whole generating blocks** 2,000 times for descriptive 95% Monte Carlo bootstrap intervals, separately by n, covariance mechanism, observation regime and estimator, retaining all source and optimizer failure/refusal counts. Do not select a winner from a 12-block study. All estimators' unsuccessful numerical outcomes remain in original recorded rows and are never silently skipped from denominator summaries.

## Scientific boundaries and next gate

These are deliberately controlled **MCAR and observation-time/predictor-MAR** data deletions, not actual empirical gaze recordings, MNAR selection, or realistic calibration/sensor artifacts. A successful numerical covariance fit does not account for working covariance estimation uncertainty in coefficient-specific Satterthwaite df, establish robust Gaussian REML under informative source loss, or guarantee coverage of 90% pointwise or function-wide simultaneous intervals. The original R20 41/256 failures, R22 32 explicit numerical refusals and R23–R30 findings must remain immutable.

Scientific blockers #289 and #296 stay OPEN. Isolate all work on a draft PR, do not modify protected main or supported public API, and do not publish eyetrajectoriespy 1.2 tags or PyPI releases.
