# FPCA and MFPCA

Functional PCA finds dominant modes of variation in curves rather than isolated scalar features.

## Multivariate planar gaze

For (G_i(t)=[x_i(t),y_i(t)]^	op):

```python
fit = fit_mfpca(gaze, n_components=0.95, scaling="dimension_sd")
```

The core estimator uses trapezoidal quadrature weights so unequal common-grid spacing contributes according to elapsed time.

## Scaling

`scaling="none"` preserves native relative channel variance. `scaling="dimension_sd"` equalizes integrated variance across functional dimensions. Neither is universally correct.

## Component retention

An integer retains a fixed count. A float in `(0,1)` retains enough components to reach the requested variance fraction.

## Interpretation

Inspect mean ± one or two score-SD component trajectories. For planar gaze, interpret x and y jointly.

## Reconstruction

`reconstruct_fpca()` supports sensitivity checks: compare low-dimensional reconstructions with the original paths to understand what the retained representation preserves.
