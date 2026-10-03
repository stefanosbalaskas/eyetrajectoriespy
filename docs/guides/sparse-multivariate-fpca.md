# Sparse planar MFPCA / joint PACE

`fit_sparse_mfpca()` is the stable 0.12 route for **jointly observed sparse planar gaze** when x and y are observed at the same retained native timestamps within each curve.

## When should I use this?

Use the estimator when x(t) and y(t) are both scientific functional coordinates, observations are sparse/irregular enough that pre-interpolating every raw trajectory would manufacture much of the analyzed curve, x and y are paired at the same retained timestamps, and cross-channel covariance is part of the target.

For one sparse functional coordinate, use [`fit_sparse_fpca()`](sparse-irregular-fpca.md). For defensibly common-grid planar trajectories, use `fit_mfpca()`.

## When should I not use it?

Do not use sparse MFPCA merely because timestamps differ slightly across otherwise dense curves. Do not use it when x and y have unmatched retained timestamps within a curve. Do not replace an unpaired observation process with silent alignment.

## Observation contract

For curve i and paired native time t_ij,

$$
\mathbf Y_{ij}=\mathbf X_i(t_{ij})+\boldsymbol\epsilon_{ij},
\qquad
\mathbf X_i(t)=
\begin{bmatrix}X_i(t)\\Y_i(t)\end{bmatrix}.
$$

The native sparse sample is preserved. Fitted population functions are later evaluated at native times for conditional scoring; that is **fitted-model evaluation, not raw-trajectory interpolation**.

## The joint planar model

$$
\mathbf C(s,t)=
\begin{bmatrix}
C_{xx}(s,t) & C_{xy}(s,t)\\
C_{yx}(s,t) & C_{yy}(s,t)
\end{bmatrix},
$$

with

$$
C_{yx}(s,t)=C_{xy}(t,s),
$$

while generally

$$
C_{xy}(s,t)\neq C_{xy}(t,s).
$$

## Why two separate x/y PACE fits are not equivalent

Two independent univariate models discard C_xy and C_yx. They can recover marginal x and y modes, but they do not estimate the eigenfunctions of the joint planar covariance operator and do not produce joint conditional scores.

## Directional cross-covariance products

Latent covariance smoothing uses temporally off-diagonal within-curve products, including cross-channel products with j != l. Same-index products are excluded so contemporaneous measurement-error covariance is not absorbed into the latent cross-channel surface under the declared error model.

## Full joint PSD handling

With quadrature matrix W,

$$
\mathbf W_2=I_2\otimes W,
\qquad
\mathbf K=\mathbf W_2^{1/2}\widehat{\mathbf C}\mathbf W_2^{1/2}.
$$

PSD inspection/projection is applied to the **joint weighted operator**, not independently to C_xx and C_yy.

## Measurement error

$$
\mathbf R_\epsilon=
\begin{bmatrix}
\sigma_x^2 & \sigma_{xy}\\
\sigma_{xy} & \sigma_y^2
\end{bmatrix}.
$$

The stable 0.12 API does not silently estimate an arbitrary cross-channel noise covariance. Use a defensible declared structure/variance and report it.

## Joint PACE scoring

For m_i paired native observations,

$$
\widehat{\boldsymbol\Sigma}_i
=\widehat{\mathbf C}_i^{TM}
+I_{m_i}\otimes\mathbf R_\epsilon
+\gamma I_{2m_i},
$$

and

$$
\widehat\xi_{ik}
=\widehat\lambda_k
\widehat{\boldsymbol\phi}_{ik}^{\top}
\widehat{\boldsymbol\Sigma}_i^{-1}
(\mathbf y_i-\widehat{\boldsymbol\mu}_i).
$$

The conditional system uses the **full fitted joint covariance**, not a rank-K reconstruction. `n_components` controls only the returned eigensystem/scores.

## Minimal fit

```python
import numpy as np
from eyetrajectoriespy import fit_sparse_mfpca

fit = fit_sparse_mfpca(
    irregular,
    dimensions=("x", "y"),
    n_components=2,
    evaluation_grid=np.linspace(0.0, 1.0, 41),
    mean_bandwidth=0.20,
    covariance_bandwidth=0.30,
    measurement_error="diagonal",
    measurement_error_variance=(0.0025, 0.0025),
    psd_action="project",
    score_ridge=0.0,
    score_failure_action="retain_nan",
)
```

## Understanding `SparseMFPCAResult`

The result retains `mean`, `eigenfunctions`, `eigenvalues`, joint PACE `scores`, the C_xx/C_xy/C_yx/C_yy covariance blocks, measurement-error covariance and quadrature weights, support/pair counts, score diagnostics, units, curve IDs, metadata, and provenance.

## Score diagnostics and failure codes

Inspect `result.score_diagnostics` before downstream use. `score_failure_action="retain_nan"` keeps failed conditional systems visible rather than silently removing curves or replacing scores.

## Plots

The published 0.12.0 artifact is unchanged. The post-0.12 `1.0.0rc1` source line adds four public visualization helpers that operate only on the already-retained `SparseMFPCAResult` quantities:

```python
from eyetrajectoriespy import (
    plot_sparse_mfpca_component,
    plot_sparse_mfpca_covariance_blocks,
    plot_sparse_mfpca_cross_covariance,
    plot_sparse_mfpca_score_diagnostics,
)

plot_sparse_mfpca_component(fit, component=0)
plot_sparse_mfpca_covariance_blocks(fit, stage="used")
plot_sparse_mfpca_cross_covariance(fit, stage="used")
plot_sparse_mfpca_score_diagnostics(fit)
```

`plot_sparse_mfpca_component()` interprets the retained vector eigenfunction as coordinate-specific mean ± mode curves. `plot_sparse_mfpca_covariance_blocks()` displays all four covariance blocks together. `plot_sparse_mfpca_cross_covariance()` keeps the directional C_xy/C_yx orientation explicit. `plot_sparse_mfpca_score_diagnostics()` shows conditional-system conditioning against paired native observation counts and preserves failed/non-finite systems as visible diagnostics.

For covariance plots, `stage="used"` displays the blocks after the declared joint PSD policy—the blocks actually used downstream—whereas `stage="smoothed"` displays the retained directly smoothed pre-PSD blocks. Neither option refits or resmooths the model.

![Sparse planar covariance blocks](../assets/gallery/sparse-mfpca-covariance-blocks.svg)

![Sparse planar first eigenfunction](../assets/gallery/sparse-mfpca-eigenfunction.svg)

## Recovery and comparator evidence

Use the [native sparse-MFPCA recovery](../validation/sparse-mfpca-recovery.md), [comparator sensitivity](../validation/sparse-mfpca-comparator-sensitivity.md), and [stress/performance](../validation/sparse-mfpca-observation-performance.md) pages. Population eigenspace recovery and individual joint-PACE score recovery are distinct targets. Those scientific qualification records remain explicitly attributed to 0.12.0 until a later package version receives fresh exact-version qualification.

## Reporting

```python
from eyetrajectoriespy import sparse_mfpca_reporting_text, sparse_mfpca_score_frame

print(sparse_mfpca_score_frame(fit).head())
print(sparse_mfpca_reporting_text(fit))
```

Report native sampling, paired-timestamp requirements, analysis grid/support, mean/covariance bandwidths, measurement-error covariance, PSD action, score ridge/failure policy, retained components, and failed-score counts.

## Limitations

The stable 0.12 estimator does not imply automatic bandwidth selection, arbitrary unpaired x/y observation times, automatic cross-channel noise estimation, complete sparse-FPCA uncertainty propagation into downstream models, or equivalence to dense-grid projection scores. The 0.12.1 development plotting helpers do not alter any of those boundaries.
