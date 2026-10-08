---
title: Bayesian FPCA B2/B3 replication and uncertainty
---

# Bayesian FPCA B2/B3 replication and uncertainty

This definitive tranche extends the immutable B1 comparator evidence without changing any estimator or public API. The earlier PR #208 evidence is retained as pilot/feasibility evidence because its realized replication and tuning grids differed from the design freeze recorded in issue #205.

## B2 replication and separation

The primary programme uses **16 deterministic replicates per scenario** for each of eight known-truth scenarios:

- harmonic moderate sparsity;
- harmonic extreme sparsity;
- harmonic low-N;
- harmonic near-tied eigenvalues;
- localized/non-harmonic **triangular-mode** univariate truth;
- simulation-only informative observation retention;
- paired sparse planar data; and
- asynchronous coordinate-specific sparse planar data.

Low-N and near-tied regimes are deliberately separate. The informative-observation case is sensitivity evidence only and does not classify the mechanism as MAR/MNAR or imply a correction estimator.

The primary comparison preserves the frozen B1 settings. A secondary native route uses the existing audited bandwidth selectors with a predeclared candidate grid. The asynchronous planar route does not silently reuse the paired selector because no qualified asynchronous selector exists.

The secondary fairness/tuning sensitivity is restricted to the **first four replicates** of extreme sparsity, low-N, near-tied, localized, and paired-planar scenarios. Native candidates use the Cartesian product of frozen mean/covariance bandwidths multiplied by `{0.75, 1.00, 1.25}` with the already-qualified 3-fold curve-level predictive criterion. `bayesFPCA` candidates use `K = {5, 6, 7, 8, 9}` and retain the successful fit with maximum final ELBO. `K = 7` remains the primary B1-compatible setting outside the fairness subset. No truth-tuning or post-hoc favorable parameter search is permitted.

## B3 uncertainty calibration

The existing native oracle validation remains the reference for the narrow conditional PACE estimand: known population mean/covariance/eigensystem, score uncertainty conditional on those objects, and direct coverage against known latent scores.

B2/B3 additionally retains fitted-model score covariance from both native and Bayesian fits. Because component signs/order are not identified and near-tied components are especially unstable, fitted score/covariance outputs are aligned to truth through weighted orthogonal Procrustes before known-score inclusion is summarized.

Population objects are re-estimated in every Monte Carlo replicate. The definitive B3 summaries therefore report empirical truth inclusion, pooled and replicate-level standardized-error behavior, covariance failures, and score failures across repeated datasets. These diagnostics quantify the calibration gap that appears when population objects are estimated, but the fitted conditional covariance itself is **not** relabelled as full population-estimation uncertainty and covariance magnitudes are not compared directly.

## Environment lock

The external comparator remains `hruffieux/bayesFPCA` at exact commit `f05b0615632cffe5c63838858d9a956af6588a73`.

The CI environment additionally pins:

- R `4.6.1`;
- `abind 1.4-8`;
- `ellipse 0.5.0`;
- `magic 1.6.1.1`;
- `matrixcalc 1.0.6`; and
- `pracma 2.4.6`.

`sessionInfo()`, R runtime details, BLAS/LAPACK details, exact package versions and checkout SHA are retained in the evidence artifact.

## B4 decision — feasibility, not promotion

B4 has been recorded in [issue #205](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/205), based on the definitive [PR #215 evidence](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/215):

- `native_bayesian_feasibility_warranted=true`
- `architecture_winner_selected=false`
- `automatic_promotion_decision=false`

The primary `K=7` external `bayesFPCA` comparison completed **128/128** fits (eight frozen scenarios × 16 replicates) and produced lower mean latent-curve reconstruction ISE than the frozen native comparator in every scenario. Where fitted score covariances were available from both routes, repeated-dataset 95% ellipsoid inclusion was higher for the external Bayesian comparator, but generally remained well below nominal coverage. This is evidence to **design and test** a native Bayesian approach, not evidence that it should replace the qualified native covariance/PACE routes. Full population-estimation uncertainty remains unresolved.

The comparator is external-only, runs in isolated evidence jobs and is not copied/ported into this MIT codebase or introduced as a runtime dependency.
