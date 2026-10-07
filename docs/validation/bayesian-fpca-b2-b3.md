---
title: Definitive Bayesian FPCA B2/B3 replication and calibration
---

# Definitive Bayesian FPCA B2/B3 replication and calibration

This evidence tranche executes the **original issue #205 design freeze**. PR #208 is retained unchanged as pilot/feasibility evidence because its realized replication and tuning grids were smaller than the earlier frozen design. This definitive tranche starts from the non-publishing `1.2.0.dev0` development line and does not add an estimator, public API, runtime backend, dependency, or release-readiness change.

## Frozen B2 design

All eight known-truth scenarios use **16 deterministic replicates**, rank 2, and Gaussian measurement noise SD = 0.05 per observed coordinate.

| Scenario | Design | N | Observation design | Eigenvalues | Fixed native mean/covariance bandwidth |
|---|---|---:|---|---|---|
| `univariate_moderate` | harmonic sparse irregular | 32 | 12–18 | (1.00, 0.40) | (0.20, 0.30) |
| `univariate_extreme_sparse` | harmonic sparse irregular | 32 | 6–9 | (1.00, 0.40) | (0.28, 0.38) |
| `univariate_low_n` | harmonic sparse irregular | 14 | 12–18 | (1.00, 0.40) | (0.22, 0.32) |
| `univariate_near_tied` | harmonic sparse irregular | 32 | 12–18 | (1.00, 0.90) | (0.20, 0.30) |
| `univariate_localized` | localized triangular modes | 32 | 12–18 | (1.00, 0.40) | (0.18, 0.28) |
| `univariate_informative_time` | harmonic + stochastic candidate-time retention | 32 | candidate grid / stochastic retention | (1.00, 0.40) | (0.20, 0.30) |
| `planar_paired` | harmonic paired x/y | 28 | 12–18 | (1.10, 0.55) | (0.22, 0.32) |
| `planar_async` | coordinate-specific x/y grids | 28 | 8–12 per coordinate | (1.10, 0.55) | (0.25, 0.36) |

The informative-time case remains simulation-only sensitivity evidence. The asynchronous case preserves coordinate-specific grids with no interpolation, nearest-neighbour synchronization, or time binning.

The primary comparison uses the fixed design above and `bayesFPCA` at K = 7 for all 16 replicates. Secondary fairness/tuning sensitivity is restricted to the **first four replicates** of `univariate_extreme_sparse`, `univariate_low_n`, `univariate_near_tied`, `univariate_localized`, and `planar_paired`.

- Native bandwidth candidates are the Cartesian product of the frozen mean and covariance bandwidths multiplied by {0.75, 1.00, 1.25}, using the already-qualified 3-fold curve-level held-out Gaussian predictive criterion.
- Bayesian candidates are K ∈ {5, 6, 7, 8, 9}; the retained sensitivity fit maximizes final ELBO, with the smaller K breaking an exact tie.
- Truth quantities never enter either selector. No post-hoc favorable search is permitted.

## B3 population-estimation calibration

The existing oracle conditional-PACE validation remains the narrow-estimand reference. In this definitive programme, population mean/covariance/eigensystem objects are re-estimated in every Monte Carlo replicate, and fitted native/Bayesian score covariance is evaluated against the known latent scores after weighted orthogonal Procrustes alignment.

For each eligible method/scenario the evidence retains:

- pooled and replicate-level 95% ellipsoid truth inclusion;
- pooled componentwise 95% marginal truth inclusion where componentwise interpretation is identified;
- pooled standardized-error mean and SD, plus replicate distributions;
- score-failure and non-positive/invalid covariance counts; and
- near-tied-component flags so componentwise summaries are not treated as primary when eigenvectors are weakly identified.

This assesses the **calibration gap under population re-estimation**. It does not relabel fitted conditional PACE covariance as full population-estimation uncertainty, and it does not treat covariance magnitude as a method-comparison target.

## External comparator environment

The external comparator remains `hruffieux/bayesFPCA` at exact commit `f05b0615632cffe5c63838858d9a956af6588a73`, with the locked R 4.6.1 environment and retained package/session/BLAS/LAPACK provenance. GPL source remains external to the MIT package.

## B4 remains deferred

This tranche must leave `b4_decision_recorded=false`, `architecture_winner_selected=false`, and `automatic_promotion_decision=false`. B4 is a subsequent written governance decision after the definitive B2/B3 artifact is inspected.
