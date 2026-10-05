---
title: Guides
---

# Guides

Use the guides when you know the scientific task but need help choosing the
representation, estimator, diagnostics, uncertainty procedure, or reporting
contract.

## Data & representation

Start here when the main issue is how gaze should be represented before
modeling.

- [Preparing trajectories](preprocessing.md)
- [Native irregular trajectories](irregular-trajectories.md)
- [Sparse irregular / PACE FPCA](sparse-irregular-fpca.md)
- [Sparse planar MFPCA / joint PACE](sparse-multivariate-fpca.md)
- [Asynchronous sparse planar MFPCA / joint PACE](sparse-multivariate-async.md)
- [Observation-process diagnostics](observation-process-diagnostics.md)
- [Basis representations](basis-representations.md)
- [Derived continuous functions](derived-functions.md)

## FPCA, uncertainty & review

Use these guides for functional decomposition, component retention, stability,
uncertainty, anomaly review, participant-aware resampling, and prediction from
partially observed sparse histories.

- [FPCA & MFPCA](fpca.md)
- [FPCA stability & validation](stability-validation.md)
- [Selecting FPC count](component-selection.md)
- [Predictive FPC selection](predictive-component-selection.md)
- [FPC shape uncertainty](component-uncertainty.md)
- [Simultaneous FPC bands](simultaneous-fpc-bands.md)
- [FPCA spectrum uncertainty](spectrum-uncertainty.md)
- [FPC score basis uncertainty](score-uncertainty.md)
- [Sparse partial-trajectory prediction](sparse-partial-trajectory-prediction.md)
- [Simultaneous functional mean bands](simultaneous-mean-bands.md)
- [Near-tied FPC subspaces](subspace-stability.md)
- [Outliers & influence](outliers-influence.md)
- [Conformal anomaly review](conformal-fpca-anomaly.md)

## Registration, multilevel & composition

Use these when timing deformation, participant/trial hierarchy, or AOI
composition is itself part of the scientific object.

- [Registration & phase](registration.md)
- [Phase FPCA & registration sensitivity](phase-fpca.md)
- [Multilevel FPCA](multilevel.md)
- [AOI probability functions](compositional.md)
- [Elastic trajectory analysis](elastic.md)

## Functional regression & repeated measures

Use these for experimental predictors, functional outcomes, repeated trials,
generalized outcomes, and FPCR uncertainty.

- [Functional regression & clustering](downstream.md)
- [Function-on-scalar regression](function-on-scalar.md)
- [Functional mixed-effects regression](functional-mixed-effects.md)
- [Gaussian FPCR bootstrap uncertainty](fpcr-bootstrap-inference.md)
- [Heteroscedastic FPCR wild bootstrap](fpcr-wild-bootstrap.md)

The navigation expands this category into the full set of generalized,
mixed-effects, simultaneous-inference, covariance, and prediction guides.

## Geometry & nonlinear dynamics

Use these when the research question concerns trajectory shape, ordered-path
distance, recurrence, nonlinear structure, Lyapunov behavior, or directed
information flow.

- [Nonlinear trajectory dynamics](nonlinear-dynamics.md)
- [Interpretation boundaries](interpretation.md)
- [Full capability inventory](../reference/capability-inventory.md)
