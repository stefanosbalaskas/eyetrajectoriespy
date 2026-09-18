# Scientific contracts

`eyetrajectoriespy` treats analytical choices as part of the result.

## Canonical `TrajectorySet`

Every trajectory carries a common monotone time grid, values with shape `curve × time × dimension`, unique IDs, dimension names, curve metadata, coordinate semantics, time units, and provenance.

## No silent transformations

The library will not silently convert missing gaze to zero, interpolate long tracker-loss intervals, smooth, rescale time to `[0,1]`, standardize dimensions, register curves, or resolve duplicate timestamps.

## Provenance as scientific metadata

Preprocessing helpers append their specification to trajectory provenance. This supports exact reporting and sensitivity analysis; it does not replace a study protocol.
