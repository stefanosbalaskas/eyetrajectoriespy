# Object contracts

## `TrajectorySet`

Shape: `n_curves × n_time × n_dimensions`.

Key semantics:
- finite, strictly increasing time;
- unique curve and dimension names;
- one metadata row per curve;
- missing observations represented as `NaN`;
- explicit coordinate and time semantics;
- preserved provenance.

## `FPCAResult`

Stores the mean function, component functions, scores, explained variance, quadrature weights, scale factors, and original coordinate/time semantics.

## `RegistrationResult`

Keeps both original and registered curves. Warping functions are first-class outputs.

## `CompositionalFPCAResult`

Records log-ratio reference and zero-replacement epsilon.

## `MultilevelFPCAResult`

Separates participant-level and within-participant trial-level component fits and score tables.


## IrregularTrajectorySet

Stores one strictly increasing time vector and one value matrix per curve. It preserves curve-specific sampling without implying interpolation or a common grid.

Key semantics:

- every curve has at least two finite time points;
- all curves share the same functional dimension names;
- value matrices may contain missing observations;
- metadata remains one row per curve;
- projection to a common grid is a separate operation.

## FPCAStabilityResult

Stores the full-sample reference FPCA plus matched bootstrap component similarities, signs, assignments, explained-variance ratios, curve counts, resampling unit, random seed, and provenance.

## RegistrationSensitivityResult

Stores paired unregistered/registered FPCA fits, component matching, signed shape similarity, and sign-aligned score correlations.

## BasisProjectionResult

Wraps an optional backend basis object together with the selected functional dimension, basis family, number of basis functions, time domain, and analysis provenance.


## FunctionalOutlierResult

Contains a diagnostic table, method identifier, optional FPCA reference, backend object where relevant, and provenance. Review flags are never interpreted as exclusions by the object.

## FPCAInfluenceResult

Stores the full-sample reference FPCA, group-level influence summary, component-level matched similarities/variance changes, the grouping variable, component count, and provenance.


## FPCACrossValidationResult

Stores fold-level held-out reconstruction error, curve-to-fold assignments,
candidate component counts, cross-validation unit, grouping variable, scaling,
random seed where applicable, and provenance.

The object records diagnostics only. Component selection remains an explicit
separate operation.

## FPCAComponentEnvelopeResult

Stores the full-sample reference FPCA, pointwise lower/median/upper matched
bootstrap component functions, matched component similarities, envelope level,
resampling unit, random seed, and provenance.

The envelope is explicitly descriptive; the object does not assert pointwise or
simultaneous confidence coverage.
