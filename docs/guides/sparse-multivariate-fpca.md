# Sparse planar MFPCA / joint PACE

`fit_sparse_mfpca()` is the stable 1.x route for **jointly observed sparse planar gaze** when x and y are observed at the same retained native timestamps within each curve. The estimator was introduced and scientifically qualified in the 0.12 line and is part of the frozen 1.0 compatibility baseline.

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

The stable API does not silently estimate an arbitrary cross-channel noise covariance. Use a defensible declared structure/variance and report it.

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

## Conditional joint-PACE score uncertainty

The 1.1 development line adds a dedicated, additive uncertainty surface without changing `fit_sparse_mfpca()` defaults or the frozen 1.0 root API:

```python
from eyetrajectoriespy.sparse_multivariate_score_uncertainty import (
    sparse_mfpca_score_uncertainty,
    sparse_mfpca_score_uncertainty_frame,
    sparse_mfpca_score_uncertainty_reporting_text,
)

uncertainty = sparse_mfpca_score_uncertainty(fit, irregular)
print(sparse_mfpca_score_uncertainty_frame(uncertainty).head())
print(sparse_mfpca_score_uncertainty_reporting_text(uncertainty))
```

For retained score vector $\boldsymbol\xi_i$, the reported covariance is

$$
\operatorname{Var}(\boldsymbol\xi_i\mid\mathbf Y_i,\text{ fitted population})
=\mathbf\Lambda
-\mathbf\Lambda\mathbf\Phi_i^\top
\mathbf\Sigma_i^{-1}
\mathbf\Phi_i\mathbf\Lambda.
$$

This calculation reuses the exact native joint-PACE score system: full fitted C_xx/C_xy/C_yx/C_yy covariance, `time_major_interleaved_xy` observation order, the declared 2x2 measurement-error covariance as $I_m\otimes\mathbf R_\epsilon$, and the fitted score ridge. It uses linear solves rather than an explicit inverse and does not interpolate raw sparse trajectories.

The scope is intentionally narrow. The result is **conditional on the fitted joint mean/covariance/eigensystem, measurement-error covariance, support policy, and score regularization**. It does not include uncertainty from estimating those population objects, bandwidth selection, joint PSD repair, or measurement-error estimation. It also does not support asynchronous x/y observation grids.

See the [joint-PACE score-uncertainty qualification](../validation/sparse-mfpca-score-uncertainty.md) for the oracle-population calibration design and exact evidence boundary.

## Plots

Stable `1.0.0` includes four public visualization helpers that operate only on quantities already retained by `SparseMFPCAResult`:

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

Use the [native sparse-MFPCA recovery](../validation/sparse-mfpca-recovery.md), [joint-PACE score-uncertainty qualification](../validation/sparse-mfpca-score-uncertainty.md), [comparator sensitivity](../validation/sparse-mfpca-comparator-sensitivity.md), and [stress/performance](../validation/sparse-mfpca-observation-performance.md) pages. Population eigenspace recovery, individual joint-PACE score recovery, and conditional score uncertainty are distinct targets.

The core scientific-method evidence remains traceable to the 0.12 estimator programme. Final `1.0.0` subsequently reran the exact-version package, sparse-MFPCA, cross-platform, performance and external-comparator qualification matrix without changing the estimator's scientific contract.

## Reporting

```python
from eyetrajectoriespy import sparse_mfpca_reporting_text, sparse_mfpca_score_frame

print(sparse_mfpca_score_frame(fit).head())
print(sparse_mfpca_reporting_text(fit))
```

Report native sampling, paired-timestamp requirements, analysis grid/support, mean/covariance bandwidths, measurement-error covariance, PSD action, score ridge/failure policy, retained components, and failed-score counts. If conditional score uncertainty is reported, state explicitly that it conditions on the fitted joint population objects and declared measurement-error covariance and excludes population-estimation and bandwidth uncertainty.

## Limitations

The stable 1.x estimator does not imply automatic bandwidth selection, arbitrary unpaired x/y observation times, automatic cross-channel noise estimation, full uncertainty propagation from sparse population estimation into joint scores or downstream models, or equivalence to dense-grid projection scores. The 1.1 conditional uncertainty surface covers only the fitted-population joint-PACE posterior covariance described above. The plotting helpers are views over retained fitted quantities and do not alter any of those scientific boundaries.
