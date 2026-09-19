# Limitations and failure modes

## Not a replacement for event analysis

Whole-trajectory analysis does not make fixations, saccades, dwell, or AOI transitions obsolete.

## Sampling rate still matters

A functional curve cannot recover dynamics that were never sampled.

## Smoothing can invent motion

Over-smoothing can turn abrupt transitions and missing gaps into visually convincing but fictitious movement.

## Registration can erase the effect

If treatment changes inspection latency, registration may align away the effect of interest.

## Layout confounding

FPCA can discover stimulus geometry rather than participant strategy when layouts are pooled without defensible harmonization.

## Components are sample-dependent

FPCs are empirical modes of variation. Replication or stability analysis may be needed before strong substantive labeling.

## Current multilevel implementation

The first release uses a two-level decomposition followed by separate FPCAs, not a full Bayesian or likelihood-based functional mixed model.


## Bootstrap stability is not inferential certainty

A high matched-component similarity shows that a component shape is reproducible under the chosen resampling scheme. It does not establish construct validity, causality, or generalization to another task/stimulus population.

## Irregular projection can change the estimand

Restricting to the common overlap shortens the time window. Using the union preserves the wider window but creates edge missingness. Neither choice is neutral.

## Phase decomposition depends on registration

Phase FPCA describes the estimated warping functions from a specific registration procedure. Different landmarks or elastic penalties can produce different phase representations.

## Basis interoperability is optional

The package preserves provenance around basis projection but delegates the basis mathematics to scikit-fda. Backend-version differences should be recorded in reproducible analyses.


## Sparse PACE is currently univariate in eyetrajectoriespy

The FDApy adapter estimates one named functional dimension at a time with covariance UFPCA and PACE score recovery. Separate x(t) and y(t) fits do not preserve joint planar covariance and must not be interpreted as joint 2-D MFPCA.

## Sparse scores depend on population smoothing

PACE scores are conditional estimates based on the fitted mean/covariance model. With very few observations per curve, individual scores can be strongly informed by population structure rather than by a densely observed individual path.

## Sparse observation design can be informative

A sparse estimator addresses irregular and limited observations; it does not automatically solve informative missingness. If gaze is absent because of blinks, track loss, off-screen viewing, or condition-dependent behavior, the observation mechanism may carry scientific information or bias.

## Sparse evaluation grids do not authorize extrapolation

An explicit FDApy evaluation grid controls where smooth mean/covariance/eigenfunction estimates are represented. eyetrajectoriespy restricts that grid to the pooled observed time support; it does not interpret smoothing outside the observed domain as measured gaze.

## Backend uncertainty is not fully propagated downstream

`SparseFPCAResult` preserves scores, eigenvalues, settings, and backend objects, but downstream score regressions do not automatically propagate uncertainty from sparse mean/covariance estimation and conditional score recovery.

## Reconstruction CV optimizes reconstruction, not scientific truth

Held-out trajectory reconstruction asks how well a training-fold FPCA basis reconstructs unseen curves. A component count that minimizes reconstruction error is not automatically the best dimension for an external prediction task, causal estimand, or substantive interpretation.

For repeated trials, curve-level cross-validation can leak participant-specific structure across train and test folds. Use grouped folds when the scientific sampling unit is the participant or another cluster.

## One-standard-error selection is a heuristic

The one-standard-error rule favors a smaller model within one estimated standard error of the minimum-RMSE candidate. It is a practical parsimony rule, not a hypothesis test or proof that the smaller functional dimension is correct.

## Bootstrap component envelopes are descriptive

Matched, sign-aligned bootstrap envelopes summarize pointwise variability of estimated FPC shapes under a chosen resampling scheme. They do not have simultaneous confidence-band coverage by construction.

When eigenvalues are close, component identity can become unstable even after matching. In that setting, matched similarity and subspace-level sensitivity may be more informative than narrow pointwise interpretation.

## Stable eigenspace does not imply identifiable FPC labels

A low projector distance for an FPC block means the selected functional span is stable under the stated comparison. It does not mean that each axis inside that span has a unique interpretation when eigenvalues are close.

## Eigengap thresholds are descriptive choices

The package does not provide a universal near-tie cutoff. A relative-gap threshold supplied by the analyst is a transparent review rule, not an inferential test or a guarantee that two population eigenvalues are equal.

## Subspace stability depends on the chosen block

A two-component span can be stable even when the boundary between FPC2 and FPC3 is unstable. Inspect eigengaps around the block boundary and fit enough components to evaluate that boundary.

## Functional outlier methods do not diagnose cause

A flagged curve is unusual under a specified functional representation. The method does not determine whether the cause is tracker error, preprocessing failure, rare but valid behavior, stimulus heterogeneity, or another source.

## In-sample reconstruction can hide influential curves

An atypical curve can shape the FPCA basis and therefore reconstruct surprisingly well. This is why reconstruction error should not be the only review diagnostic.

## Influence is sample-size dependent

Leave-one-participant-out changes can be large in small samples even when every participant is valid. Influence quantifies dependence of the fitted basis on the observed sample; it is not evidence of invalid data.
