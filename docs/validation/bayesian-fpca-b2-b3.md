---
title: Bayesian FPCA B2/B3 replication and uncertainty
---

# Bayesian FPCA B2/B3 replication and uncertainty

This tranche extends the immutable B1 comparator evidence without changing any estimator or public API.

## B2 replication and separation

The programme uses five predeclared replicates for each of eight known-truth scenarios:

- harmonic moderate sparsity;
- harmonic extreme sparsity;
- harmonic low-N;
- harmonic near-tied eigenvalues;
- localized/non-harmonic univariate truth;
- simulation-only informative observation retention;
- paired sparse planar data; and
- asynchronous coordinate-specific sparse planar data.

Low-N and near-tied regimes are deliberately separate. The informative-observation case is sensitivity evidence only and does not classify the mechanism as MAR/MNAR or imply a correction estimator.

The primary comparison preserves the frozen B1 settings. A secondary native route uses the existing audited bandwidth selectors with a predeclared candidate grid. The asynchronous planar route does not silently reuse the paired selector because no qualified asynchronous selector exists.

`bayesFPCA` is evaluated at predeclared spline-basis sizes `K = 5, 7, 9`; `K = 7` remains the primary B1-compatible setting. No truth-tuning or post-hoc favorable parameter search is permitted.

## B3 uncertainty calibration

The existing native oracle validation remains the reference for the narrow conditional PACE estimand: known population mean/covariance/eigensystem, score uncertainty conditional on those objects, and direct coverage against known latent scores.

B2/B3 additionally retains fitted-model score covariance from both native and Bayesian fits. Because component signs/order are not identified and near-tied components are especially unstable, fitted score/covariance outputs are aligned to truth through weighted orthogonal Procrustes before known-score inclusion is summarized.

Those fitted-model truth-inclusion summaries are descriptive. They are not relabelled as full population-estimation coverage for native PACE and they are not used to compare covariance magnitudes directly.

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

## B4 remains deferred

This tranche must leave `b4_decision_recorded=false`. Only after the replicated recovery, tuning sensitivity and uncertainty evidence are inspected may issue #205 record one of `external_comparator_only`, `native_feasibility_warranted`, or `not_actionable`.
