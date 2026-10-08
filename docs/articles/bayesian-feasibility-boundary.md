---
title: Bayesian FPCA feasibility boundary
---

# Bayesian FPCA after B4: promising comparison, separate research programme

**Status (8 October 2026):** The B1–B4 external-comparator/feasibility programme is closed. The recorded decision is **native feasibility warranted**, not architectural replacement or production promotion.

## What was compared?

The definitive B2/B3 design retained **eight frozen known-truth scenarios** with **16 replicates per scenario**, separately exercising ordinary and extreme sparse univariate observations, low sample size, near-tied modes, localized nonharmonic truth, informative observation retention as a simulation-only sensitivity, paired planar data, and coordinate-specific asynchronous planar sampling. External `bayesFPCA` is pinned in a dedicated environment; the package's native covariance/PACE fitting contracts remain unchanged.

The external comparator completed **128/128 primary fits** at `K=7`, and its mean reconstruction integrated squared error was below the frozen native comparator across all eight scenarios. That is a useful result on *latent reconstruction under these tested conditions*, not a general guarantee on all sampling regimes, all methods or other performance targets.

## What uncertainty did—and did not—show?

The B3 repeated-dataset assessment refitted population objects and examined empirical 95% score-ellipsoid inclusion under fitted conditional covariance information. Where both routes exposed covariance results, the external comparator had higher 95% ellipsoid inclusion, yet empirical inclusion still generally fell well below 95%. A fitted conditional score covariance is **not** the same estimand as full population-parameter/posterior estimation uncertainty. Calibration must be independently addressed before making nominal-coverage claims.

## Recorded decision

| B4 field | Decision |
| --- | --- |
| `native_bayesian_feasibility_warranted` | `true` |
| `architecture_winner_selected` | `false` |
| `automatic_promotion_decision` | `false` |

A new native Bayesian method, if pursued, requires independent mathematical design, known-truth recovery/calibration, architectural and licensing review, runtime evidence, public API review and release governance. The GPL external comparator must **not** be copied or vendored into the MIT implementation.

## Relationship to the 1.2 workflow release

The ten 1.2 workflows **compose existing qualified estimators**. No Bayesian estimator, model-choice switch or Bayesian runtime dependency is added by the orchestration programme. Treat B4 as an invitation to a future **separate design/feasibility** investigation, not a recommendation to replace `fit_sparse_fpca()` or `fit_sparse_mfpca()` today.

The definitive records are [issue #205 (B4)](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/205), [PR #215 (B2/B3)](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/215) and the [methodological validation note](../validation/bayesian-fpca-b2-b3.md). The retained raw evidence artifact remains authoritative for scenario-level diagnostics; this article is not a substitute for its analysis.
