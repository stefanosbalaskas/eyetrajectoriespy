# Conformal FPCA anomaly review

Split conformal inference provides a principled way to ask whether a **new functional trajectory** is unusual relative to a reference population.

Version 0.15 adds marginal split-conformal p-values built around the package's common-grid FPCA/MFPCA representation.

This is distinct from the in-sample review diagnostics in <code>diagnose_fpca_outliers()</code>.

## Three explicit partitions

The API requires three disjoint trajectory sets:

1. **proper training** — fits the FPCA/MFPCA reference;
2. **calibration** — establishes the empirical nonconformity distribution;
3. **targets** — new curves being reviewed.

    result = split_conformal_fpca_anomaly(
        proper_training,
        calibration,
        targets,
        n_components=3,
        scaling="dimension_sd",
        nonconformity="reconstruction_rmse",
        alpha=0.05,
    )

Curve IDs must be disjoint across the three partitions.

The package does not create a random split on the analyst's behalf.

## Why no automatic split?

A random train/calibration split can materially change conformal p-values in small samples.

The 2026 multivariate-functional conformal literature explicitly discusses split sensitivity and calibration-conditional adjustments.

eyetrajectoriespy therefore makes the partition a visible study-design decision rather than hiding it inside the estimator.

## Marginal p-value

For a calibration nonconformity sample (s_1,dots,s_n) and target score (s^*),

[
hat p =
rac{1 + sum_{i=1}^n I(s_i ge s^*)}{n+1}.
]

The implementation uses the greater-than-or-equal rule.

That conservative tie handling is part of the public contract.

## P-value resolution

The smallest possible p-value is

[
p_{min} = rac{1}{n_{calib}+1}.
]

With only 9 calibration curves, for example, the smallest possible p-value is 0.10.

No interpolation or pseudo-count manipulation is used to manufacture smaller p-values.

## Reconstruction-RMSE nonconformity

    result = split_conformal_fpca_anomaly(
        proper_training,
        calibration,
        targets,
        n_components=3,
        nonconformity="reconstruction_rmse",
    )

The proper-training FPCA basis is held fixed.

Calibration and target trajectories are projected into that basis and reconstructed with the retained FPCs.

Integrated reconstruction RMSE becomes the nonconformity score.

Large values indicate structure poorly represented by the proper-training FPC span.

## Score-space Mahalanobis nonconformity

A curve can reconstruct well but still occupy an extreme location in the retained FPC score distribution.

Use:

    result = split_conformal_fpca_anomaly(
        proper_training,
        calibration,
        targets,
        n_components=3,
        nonconformity="score_mahalanobis",
        mahalanobis_covariance="robust",
        random_state=2026,
    )

The score covariance is fitted on proper-training scores only.

The analyst must choose <code>"empirical"</code> or <code>"robust"</code> explicitly.

## Why two scores instead of one hidden composite?

Reconstruction error and score-space extremeness detect different departures.

Combining them requires a scientifically meaningful scale or aggregation rule.

Version 0.15 does not invent one automatically.

If both are substantively relevant, run both as planned sensitivity analyses and report that multiplicity transparently.

## What the p-value means

Under the split-conformal assumptions, the p-value assesses how extreme a new inlier target's nonconformity is relative to the calibration sample.

The core requirement is exchangeability of inlier units relative to the reference/calibration population.

The p-value does **not** identify the cause of unusualness.

Tracker error, rare but valid viewing behavior, stimulus mismatch, preprocessing differences, and true behavioral novelty can all create small p-values.

## Repeated trials

The current conformal contract is curve-level.

Repeated trials from one participant are generally dependent.

The API does not transform them into independent observations and does not claim participant-clustered validity.

Use genuinely exchangeable units or a separately justified participant-level construction before making inferential claims.

## Multiple target curves

The 0.15 result returns one marginal p-value per target.

It does not automatically apply Benjamini-Hochberg, calibration-conditional adjustment, or any other multiplicity method.

Kim and Park (2026) combine conformal p-values with calibration-conditional adjustments and BH for FDR-controlled multivariate-functional outlier detection. That is a broader procedure than the 0.15 implementation.

## Relationship to current literature

Kim and Park (2026) propose conformal outlier detection for multivariate functional data using multivariate functional depth as the nonconformity score and discuss marginal and calibration-conditional p-values plus FDR control.

Adams et al. (2025) develop inductive conformal anomaly detection with elastic functional distances, particularly for difficult shape outliers.

eyetrajectoriespy 0.15 implements neither score verbatim.

It uses package-native FPCA reconstruction or explicitly selected score-space Mahalanobis nonconformity inside the standard split-conformal marginal p-value framework.

## Reporting example

> An FPCA reference was fitted using 40 proper-training trajectories and three retained components. Twenty disjoint calibration trajectories defined the reconstruction-RMSE nonconformity distribution. Marginal split-conformal p-values for six new target trajectories were computed as ((1+#{s_i^{calib}ge s^*})/(20+1)), using conservative greater-than-or-equal tie handling. The minimum attainable p-value was 0.0476. Curves with p ≤ .05 were flagged for review only and were not automatically excluded. No calibration-conditional adjustment or multiple-testing/FDR correction was applied.

## API links

- <code>split_conformal_fpca_anomaly()</code>
- <code>ConformalFunctionalAnomalyResult</code>
- <code>conformal_fpca_anomaly_frame()</code>
- <code>plot_conformal_fpca_anomaly()</code>
- <code>conformal_fpca_anomaly_reporting_text()</code>

See [References](../methods/references.md).
