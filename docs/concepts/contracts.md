# Scientific contracts

`eyetrajectoriespy` treats analytical choices as part of the result.

## Canonical `TrajectorySet`

Every trajectory carries a common monotone time grid, values with shape `curve × time × dimension`, unique IDs, dimension names, curve metadata, coordinate semantics, time units, and provenance.

## No silent transformations

The library will not silently convert missing gaze to zero, interpolate long tracker-loss intervals, smooth, rescale time to `[0,1]`, standardize dimensions, register curves, or resolve duplicate timestamps.

## Provenance as scientific metadata

Preprocessing helpers append their specification to trajectory provenance. This supports exact reporting and sensitivity analysis; it does not replace a study protocol.

## Evidence provenance is separate from numerical provenance

A numerical result can be reproducible while its methodological justification is overstated. Version 0.25 therefore treats evidence metadata as another tested scientific surface for the nonlinear-dynamics layer.

The nonlinear evidence registry separates:

- direct behavioral-gaze applications;
- direct eye/pupil signal applications;
- general methodological sources.

Each verified record carries both a **supports** statement and a **does not support** boundary. Candidate citations that were not verified remain in the audit trail but cannot silently enter the ordinary bibliography.

A failed literature or package search is not proof of novelty. See the [nonlinear evidence audit](../methods/nonlinear-evidence-audit.md).

