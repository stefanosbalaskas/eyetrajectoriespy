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
