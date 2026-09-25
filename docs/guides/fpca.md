# FPCA and MFPCA

Functional PCA finds dominant modes of variation in curves rather than isolated scalar features.

## Multivariate planar gaze

For \(G_i(t)=[x_i(t),y_i(t)]^\top\):

```python
fit = fit_mfpca(gaze, n_components=0.95, scaling="dimension_sd")
```

The core estimator uses trapezoidal quadrature weights so unequal common-grid spacing contributes according to elapsed time.

## Scaling

`scaling="none"` preserves native relative channel variance. `scaling="dimension_sd"` equalizes integrated variance across functional dimensions. Neither is universally correct.

## Component retention

An integer retains a fixed count. A float in `(0,1)` retains enough components to reach the requested in-sample variance fraction.

When the retained dimension itself is under study, use [held-out reconstruction cross-validation](component-selection.md). For repeated trials, group folds by participant so trials from one participant cannot appear in both training and test data.

Variance thresholds and held-out reconstruction answer different questions and can be reported side by side.

## Interpretation

Inspect mean ± one or two score-SD component trajectories. For planar gaze, interpret x and y jointly.

## Reconstruction

`reconstruct_fpca()` supports sensitivity checks: compare low-dimensional reconstructions with the original paths to understand what the retained representation preserves.


## Mathematical contract

The implementation performs PCA after quadrature weighting the centered functional observations. With optional dimension scaling \(s_d\), the weighted representation is

$$
Z_{i,m,d}
=
\frac{G_{id}(t_m)-\widehat\mu_d(t_m)}{s_d}\sqrt{w_m}.
$$

Reconstruction with \(K\) retained FPCs is

$$
\widehat{\mathbf G}^{(K)}_i(t)
=
\widehat{\boldsymbol\mu}(t)
+
\sum_{k=1}^{K}
\widehat\xi_{ik}\widehat{\boldsymbol\phi}_k(t).
$$

See the [mathematical reference](../methods/mathematical-reference.md#fpca) for the exact trapezoidal weights, scaling, projection, and loading back-transformation used by the package.
