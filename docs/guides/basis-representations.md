# Basis representations

Grid values are not the only way to represent a function. A basis expansion represents a curve as

\[
f(t)=\sum_{k=1}^{K} c_k \phi_k(t).
\]

General FDA libraries support B-spline, Fourier, and other basis families. Basis choice and basis size are analytical decisions because they determine which shapes can be represented.

## Optional scikit-fda projection

Install the optional FDA interoperability extra, then project one trajectory dimension:

    projection = to_skfda_basis(
        gaze,
        dimension="x",
        basis="bspline",
        n_basis=10,
        order=4,
    )

The returned <code>BasisProjectionResult</code> preserves the selected dimension, basis family, basis count, time domain, and upstream provenance alongside the backend object.

## B-splines

B-splines are flexible for non-periodic trial trajectories. Increasing the number of basis functions increases representational flexibility but can also reproduce more high-frequency variation.

## Fourier basis

Fourier bases are most natural when periodic structure is scientifically plausible. A generic screen-based decision trial is not automatically periodic.

## Basis projection is not neutral smoothing

Projection to a finite basis is an approximation. Compare basis sizes and, where the scientific question concerns abrupt transitions, verify that the basis has not replaced genuine gaze changes with an overly smooth curve.

## Why the package delegates estimation

<code>eyetrajectoriespy</code> keeps the eye-tracking semantics and provenance while delegating mature general FDA mathematics to specialist libraries where appropriate. It does not reimplement basis algebra merely to own another estimator.
