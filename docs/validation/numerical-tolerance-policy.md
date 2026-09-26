# Numerical tolerance policy

Version 0.56 makes numerical tolerances part of the scientific validation
contract rather than a collection of unexplained `rtol` and `atol` values.

The machine-readable policy lives in `VALIDATION_TOLERANCES.json`.

## Principle

A tolerance should reflect the **kind of quantity and reference evidence**, not
developer convenience. The package therefore does not use one universal
floating-point tolerance.

### Exact combinatorial quantities

Examples include line counts, support counts, exact discrete paths when unique
and integer event counts. Prefer exact equality. If a derived ratio or
logarithm introduces floating arithmetic, use zero relative tolerance and an
absolute tolerance near machine precision.

A wrong recurrence-line convention must not be hidden by relaxing a tolerance.

### Deterministic geometry

Fréchet/DTW toy problems should use hand-computable optima where possible.
Validate the path/coupling audit as well as the final scalar distance.
Representable values can be exact; otherwise use tight floating-point
tolerances.

### Linear-algebra invariants

FPCA eigenfunction signs are arbitrary and near-tied eigenvectors can rotate.
Validation should therefore compare eigenvalues, reconstruction, weighted
absolute inner products, principal angles or projector/subspace quantities
rather than requiring elementwise signed eigenfunction equality.

### Optimizer equivalence

For MixedLM, GEE and other optimizer-backed comparisons:

1. require the same estimand, likelihood/link and covariance specification;
2. require convergence;
3. map parameterizations explicitly;
4. compare scientifically meaningful parameters, covariance/scale and fitted
   quantities or objective values;
5. state tolerances per validation row.

Optimizer-backed validation must not use an unexplained loose global tolerance.

### External backend equivalence

Record the external implementation/version and any normalization,
parameterization or default differences. Tolerance is justified per case; the
package does not assume that two implementations should be bitwise identical.

### Simulation recovery

Simulation recovery is not machine-precision validation. Record seed, sample
size, data-generating parameters, estimand and a predeclared finite-sample
recovery criterion. It is explicitly classified as weaker evidence than an
analytical truth or independent implementation equivalence.

### Bootstrap and Monte Carlo summaries

Identical stored draws/seeds may be checked deterministically where appropriate.
Comparisons across independently generated resamples should be based on Monte
Carlo uncertainty rather than arbitrary decimal-place agreement.

## Changing a tolerance

A tolerance may be changed only with an explanation of which numerical or
scientific property changed. A test failure is not, by itself, justification
for widening the tolerance.

Every qualified reference case records its tolerance class and its actual
comparison rule in the [reference-validation ledger](reference-validation-ledger.md).
