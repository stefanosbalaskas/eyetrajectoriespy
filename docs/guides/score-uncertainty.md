# FPC score basis-resampling uncertainty

FPC scores are often treated as fixed once FPCA has been fitted. That can hide an important source of variability: the estimated mean, scaling, and eigenfunctions would change if the training sample changed.

Use <code>bootstrap_fpca_score_uncertainty()</code> to ask:

> For these fixed target trajectories, how much would their FPC scores move if the FPCA basis were re-estimated under the stated bootstrap design?

This is a narrower question than full score uncertainty, and the package keeps that boundary explicit.

## What is fixed and what is resampled

The target trajectories are fixed.

The FPCA training sample is resampled, the basis is refitted, and the fixed targets are projected again.

This isolates one source of uncertainty: **basis estimation**.

It does not resample or perturb the target trajectory itself.

## Training targets

If <code>targets=None</code>, all training trajectories are used as fixed projection targets:

    result = bootstrap_fpca_score_uncertainty(
        gaze,
        n_bootstrap=1000,
        n_components=3,
        scaling="dimension_sd",
        random_state=2026,
    )

The reference target scores are the ordinary full-sample FPCA scores.

## Compatible external targets

A separate target set can be supplied:

    targets = new_gaze

    result = bootstrap_fpca_score_uncertainty(
        training_gaze,
        targets=targets,
        n_bootstrap=1000,
        n_components=3,
        scaling="dimension_sd",
        random_state=2026,
    )

Targets must match the training functional representation exactly:

- identical time grid;
- identical functional dimension names and order;
- identical coordinate system;
- identical time unit;
- complete finite values.

The function refuses silent resampling, coordinate conversion, unit conversion, or dimension reordering.

## Why component matching and sign alignment are required

FPC signs are arbitrary. Nearby FPCs may also exchange order across bootstrap samples.

For every bootstrap basis, eyetrajectoriespy:

1. compares bootstrap FPC shapes with the full-sample reference;
2. solves the maximum-absolute-similarity matching problem;
3. reorders bootstrap score columns to reference component identities;
4. sign-aligns each score column using the matched signed similarity.

Without these steps, a harmless sign flip could look like extreme score uncertainty.

## Repeated trials

When participants are independent sampling units and contribute repeated trials:

    result = bootstrap_fpca_score_uncertainty(
        gaze,
        targets=targets,
        n_bootstrap=1000,
        n_components=2,
        scaling="dimension_sd",
        resample_unit="participant",
        participant_column="participant_id",
        random_state=2026,
    )

Whole participant trial bundles are resampled together.

This preserves within-participant trial clustering in the basis-resampling design. It does not turn the resulting score envelopes into a mixed-effects analysis.

## What the percentile envelope means

For each fixed target curve and matched FPC, the result stores:

- full-sample reference score;
- bootstrap score median;
- bootstrap score standard deviation;
- lower and upper percentile limits;
- component-matching similarity diagnostics.

The percentile limits are **descriptive bootstrap envelopes for basis-induced score variation**.

They are not advertised as exact finite-sample confidence intervals.

## What is not included

The implementation does not include:

- measurement error in the target trajectory;
- uncertainty about an unobserved latent target function;
- PACE conditional-score uncertainty for sparse data;
- future-subject or future-curve sampling variability;
- uncertainty from interpolation, smoothing, registration, normalization, or other preprocessing decisions;
- uncertainty in a downstream regression/classifier fitted to the scores;
- joint uncertainty in outcomes, covariates, basis, and model coefficients.

These exclusions are stored in provenance and repeated by the reporting helper.

## Near-tied FPCs

Matching does not make a weakly identified individual FPC axis scientifically unique.

Inspect the returned matching similarities. If components are unstable or eigenvalues are near tied, use eigengap and subspace diagnostics before interpreting component-specific score envelopes.

A stable subspace may still support a multicomponent representation even when individual FPC1/FPC2 score labels are unstable.

## Relationship to the uncertainty literature

Goldsmith, Greven & Crainiceanu (2013) showed that curve estimates and intervals can be misleading when uncertainty in the FPC decomposition is ignored. Their method combines conditional model uncertainty across bootstrap decompositions using iterated expectation/variance.

The 0.11 eyetrajectoriespy routine is more limited: it exposes the decomposition-induced movement of fixed-target projection scores directly. It does not reproduce the full mixed-model uncertainty construction of Goldsmith et al.

Recent fully Bayesian FPCA work likewise emphasizes that downstream analyses which condition on estimated FPCs can understate uncertainty. eyetrajectoriespy remains a transparent frequentist/bootstrap layer rather than a Bayesian FPCA engine.

## Sparse/PACE scores are different

For sparse irregular trajectories, conditional-expectation score uncertainty is a different inferential problem. The optional FDApy/PACE adapter estimates sparse scores but this 0.11 routine does not bootstrap PACE conditional-score uncertainty.

Do not transfer dense/common-grid score envelopes to sparse PACE scores without a method designed for that setting.

## Reporting example

> Sensitivity of FPC scores to estimation of the functional basis was evaluated with 1,000 participant-level bootstrap refits. The four target trajectories were held fixed while participants were resampled to re-estimate the dimension-SD-scaled MFPCA basis. Bootstrap components were matched and sign-aligned to the full-sample basis before target projection. Ninety-five-percent percentile envelopes summarize basis-resampling variability only and do not incorporate target measurement error, latent-curve uncertainty, preprocessing uncertainty, future-curve variability, or downstream regression uncertainty.

## API links

- <code>bootstrap_fpca_score_uncertainty()</code>
- <code>FPCAScoreUncertaintyResult</code>
- <code>fpca_score_uncertainty_frame()</code>
- <code>plot_fpca_score_uncertainty()</code>
- <code>fpca_score_uncertainty_reporting_text()</code>
- <code>transform_fpca()</code>
- <code>bootstrap_fpca_stability()</code>
- <code>bootstrap_fpca_subspace_stability()</code>

See [References](../methods/references.md).
