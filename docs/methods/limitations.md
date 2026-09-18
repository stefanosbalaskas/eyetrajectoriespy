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


## Functional outlier methods do not diagnose cause

A flagged curve is unusual under a specified functional representation. The method does not determine whether the cause is tracker error, preprocessing failure, rare but valid behavior, stimulus heterogeneity, or another source.

## In-sample reconstruction can hide influential curves

An atypical curve can shape the FPCA basis and therefore reconstruct surprisingly well. This is why reconstruction error should not be the only review diagnostic.

## Influence is sample-size dependent

Leave-one-participant-out changes can be large in small samples even when every participant is valid. Influence quantifies dependence of the fitted basis on the observed sample; it is not evidence of invalid data.
