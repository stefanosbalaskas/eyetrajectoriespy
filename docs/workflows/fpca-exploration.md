# Continuous gaze exploration and FPCA

Use this route when the primary scientific object is a continuous gaze
trajectory or derived function and the first question is **how trajectories
vary**, not yet how a predictor changes them.

## 1. Start from an explicit trajectory representation

Import or construct a `TrajectorySet` with time units, coordinate semantics,
curve IDs and participant/trial metadata. Do not silently interpolate,
normalize time, smooth or register curves.

For planar gaze, use `fit_mfpca()`; for one functional dimension, use
`fit_fpca()`.

~~~python
fit = fit_mfpca(
    trajectories,
    n_components=0.95,
    scaling="dimension_sd",
)
~~~

## 2. Check the representation before interpreting components

Inspect data completeness, time support, scaling choice and whether phase
variation is scientifically meaningful. Registration is not a default
preprocessing step. Sparse/irregular PACE, compositional AOI trajectories and
phase analysis are **advanced branches**, not replacements for the canonical
common-grid workflow.

## 3. Quantify stability rather than treating components as fixed truths

When component interpretation matters, use held-out reconstruction,
bootstrap-matched component stability, eigengap/subspace diagnostics or
component uncertainty as appropriate. Near-tied eigenvalues should shift
interpretation toward the subspace rather than individual component labels.

## 4. Interpret the scientific object

Report explained variation, component functions/scores and reconstruction
quality. Do not interpret sign conventions as substantive; matched components
may be sign-aligned for comparison.

## 5. Produce an auditable report

Use `summarise_fpca()` and `fpca_reporting_text()`, and retain preprocessing
and basis provenance.

### Do not use this route when

- the primary target is a trial-varying experimental coefficient function;
- repeated-trial covariance is central to inference;
- the response is Bernoulli/count rather than approximately Gaussian;
- recurrence/nonlinear structure is the actual scientific target.

Those questions have separate canonical routes.
