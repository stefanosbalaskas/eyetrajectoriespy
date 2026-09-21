# FPCA spectrum uncertainty

Eigenvalues and variance-explained summaries are estimated from the sample. Treating them as fixed numbers can overstate the precision of statements such as “FPC1 explains 42% of functional variation.”

Use <code>bootstrap_fpca_spectrum_uncertainty()</code> to quantify bootstrap uncertainty for:

- eigenvalues;
- per-component explained-variance ratios;
- cumulative explained variance.

## What is resampled

The function supports:

- <code>resample_unit="curve"</code> for independent trajectories;
- <code>resample_unit="participant"</code> when repeated trials are clustered within participants.

For participant resampling, entire participant trial bundles are resampled together.

## Individual component identity versus cumulative rank

These are deliberately different targets.

For an individual eigenvalue or explained-variance ratio, each bootstrap FPC is matched to the full-sample reference by maximum absolute functional similarity. The associated eigenvalue/ratio is then attached to that reference-FPC identity.

For cumulative explained variance, bootstrap components remain in descending eigenvalue rank:

> top 1, top 2, …, top k components.

This avoids changing the standard cumulative-variance estimand when near-tied FPCs swap orientation or labels.

## Component-wise calibration

    spectrum = bootstrap_fpca_spectrum_uncertainty(
        gaze,
        n_bootstrap=1000,
        n_components=3,
        confidence_level=0.95,
        simultaneous_scope="component",
        random_state=2026,
    )

Each component receives its own studentized bootstrap critical value within each metric.

## Familywise calibration across requested components

    spectrum = bootstrap_fpca_spectrum_uncertainty(
        gaze,
        n_bootstrap=1000,
        n_components=3,
        confidence_level=0.95,
        simultaneous_scope="family",
        random_state=2026,
    )

For each metric, the calibration uses the maximum standardized deviation across all requested components.

Important: familywise calibration is performed separately for:

1. eigenvalues;
2. explained-variance ratios;
3. cumulative explained-variance ratios.

It is **not** one joint familywise guarantee across all three metric families simultaneously.

## Scaling is part of the estimand

For multivariate FPCA, channel scaling changes the covariance geometry and therefore the eigenvalues and variance decomposition.

Always report the same explicit <code>scaling</code> argument used for the fitted MFPCA. A spectrum interval without its scaling rule is incomplete.

## Why bootstrap components are matched

FPC signs are arbitrary and nearby components can exchange order under resampling. Matching by functional similarity preserves the connection between an individual spectrum value and the reference FPC whose shape is being interpreted.

Matching is not used for cumulative explained variance because cumulative variance is fundamentally a rank-based quantity.

## Near-tied eigenvalues

Near ties have a much stronger first-order impact on eigenfunction estimation than on eigenvalue estimation. Therefore this API does not reject spectrum uncertainty merely because an eigengap is small.

That does **not** make a near-tied individual FPC direction uniquely interpretable. Pair spectrum uncertainty with:

- <code>fpca_eigenvalue_gap_table()</code>;
- <code>bootstrap_fpca_subspace_stability()</code>;
- simultaneous FPC-shape uncertainty where individual axes are scientifically interpreted.

## No support clipping

Studentized symmetric intervals are not silently clipped.

Therefore:

- an eigenvalue interval can extend slightly below zero;
- an explained-variance-ratio interval can extend outside [0, 1].

Clipping would change the interval without a stated inferential derivation. The raw approximation is retained and the limitation should be reported.

## Not an automatic retention rule

A narrow or positive eigenvalue interval is not, by itself, a component-selection criterion.

Component count may instead be chosen using:

- held-out reconstruction;
- outcome-tuned predictive CV;
- a pre-specified variance-explained rule;
- another study-specific method.

Spectrum uncertainty describes sampling variability in the variance decomposition. It does not silently choose the dimension.

## Bootstrap replicate count

The API minimum exists to prevent meaningless tail calibration, not to recommend a scientific number of replicates. Use enough replicates for the requested tail quantile and stability required by the study, and report the number and seed policy.

## Reporting example

> FPCA spectrum uncertainty was evaluated using 1,000 participant-level bootstrap resamples. Bootstrap FPCs were matched to the full-sample reference before individual eigenvalues and explained-variance ratios were assigned to FPC identities, whereas cumulative explained variance retained descending eigenvalue-rank order. Ninety-five-percent familywise studentized intervals were calibrated across the three requested components separately within each spectrum metric. The MFPCA used dimension-SD scaling. Intervals were reported without support clipping.

## Methodological context

Hall and Hosseini-Nasab (2006) developed stochastic expansions for FPCA and proposed bootstrap confidence regions for eigenvalues/eigenfunctions, noting that eigenvalue spacing enters eigenfunction estimation at first order but eigenvalue estimation only at second order. Cai and Hu (2024) provide asymptotically correct confidence intervals for individual eigenvalues and simultaneous inference for eigensystems under dense B-spline-smoothed functional data.

The eyetrajectoriespy implementation is not the Cai-Hu spline estimator. It is an explicit nonparametric matched bootstrap around the package’s common-grid FPCA/MFPCA estimator.

See [References](../methods/references.md).
