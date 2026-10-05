# Asynchronous sparse planar MFPCA / joint PACE

`fit_sparse_mfpca_async()` is the 1.1 development-line route for sparse planar gaze when x and y are observed on **different native time grids within the same curve**.

Use it only when the scientific observation process is genuinely coordinate-specific. If x and y are jointly observed at the same retained timestamps, keep using the stable [`fit_sparse_mfpca()`](sparse-multivariate-fpca.md) route.

## Scientific target

For curve $i$ and coordinate $d\in\{x,y\}$,

$$
Y_{id}(t_{idj})=X_{id}(t_{idj})+\epsilon_{idj},
$$

with no requirement that

$$
T_{ix}=T_{iy}.
$$

The estimator generalizes the observation model itself. It does **not** align unmatched x/y samples by interpolation, nearest-neighbour matching, binning, or a synthetic raw common grid.

## Input representation

The existing `IrregularTrajectorySet` is reused. For each curve:

- `time[i]` is the exact sorted union of native timestamps where at least one requested coordinate was observed;
- a finite x value means x was observed at that exact timestamp;
- a finite y value means y was observed at that exact timestamp;
- `NaN` in only one requested coordinate means that coordinate was not observed at that timestamp;
- a row where both requested coordinates are missing is invalid.

This union is only a storage representation. It does not create a value for an unobserved coordinate/time pair.

## Population estimation

The fitter extracts separate native views

$$
\{(t_{ixj},x_{ixj})\}_{j=1}^{m_{ix}}
\qquad\text{and}\qquad
\{(t_{iyk},y_{iyk})\}_{k=1}^{m_{iy}}.
$$

It estimates:

- $\mu_x(t)$ from observed x samples only;
- $\mu_y(t)$ from observed y samples only;
- $C_{xx}(s,t)$ from off-diagonal x-x residual products;
- $C_{yy}(s,t)$ from off-diagonal y-y residual products;
- directional $C_{xy}(s,t)$ from x residuals at native x times and y residuals at native y times.

No hidden synchronization is required for cross-covariance products. A valid contribution may have $s\neq t$.

## Why simultaneous x-y products are excluded from latent Cxy

When x and y are observed at the same instant, the cross moment may contain contemporaneous measurement-error covariance. Therefore same-time x-y residual products are excluded from latent $C_{xy}$ smoothing within the declared equality tolerance.

Unequal-time x-y products remain latent cross-covariance evidence under the assumption that measurement errors are independent across distinct times.

The result retains the number of excluded simultaneous cross-products so this decision is auditable.

## Joint covariance operator

The fitted operator remains

$$
\mathbf C(s,t)=
\begin{bmatrix}
C_{xx}(s,t) & C_{xy}(s,t)\\
C_{yx}(s,t) & C_{yy}(s,t)
\end{bmatrix},
\qquad
C_{yx}(s,t)=C_{xy}(t,s).
$$

The same joint weighted PSD audit/eigendecomposition used by the qualified synchronous sparse-MFPCA line is reused. `Cxy` is directional and is not self-symmetrized.

## Asynchronous joint PACE scoring

Each retained scalar coordinate observation is represented by its native time and channel. The deterministic score order is:

1. increasing native time;
2. x before y when timestamps are equal.

For a fully paired curve this reduces exactly to the stable `time_major_interleaved_xy` order.

The score covariance uses the **full repaired fitted covariance operator** evaluated at every observed channel/time pair. `n_components` controls the retained score vector and eigenfunctions; it does not replace the observation covariance by a rank-$K$ reconstruction.

## Measurement-error covariance

A declared planar measurement-error matrix

$$
\mathbf R_\epsilon=
\begin{bmatrix}
\sigma_x^2 & \sigma_{xy}\\
\sigma_{xy} & \sigma_y^2
\end{bmatrix}
$$

is applied according to the actual scalar observation layout:

- each x observation receives $\sigma_x^2$ on its diagonal;
- each y observation receives $\sigma_y^2$ on its diagonal;
- $\sigma_{xy}$ is added only between x and y observations that are simultaneous within `same_time_tolerance`;
- observations at different timestamps receive no measurement-error cross-covariance.

This is distinct from latent $C_{xy}$ estimation: simultaneous cross-products are excluded from the latent surface but their declared measurement-error covariance is included in the score system.

## Minimal fit

```python
import numpy as np
from eyetrajectoriespy.sparse_multivariate_async import (
    fit_sparse_mfpca_async,
    sparse_mfpca_async_reporting_text,
    sparse_mfpca_async_score_frame,
)

fit = fit_sparse_mfpca_async(
    irregular,
    dimensions=("x", "y"),
    n_components=2,
    evaluation_grid=np.linspace(0.0, 1.0, 41),
    mean_bandwidth=0.20,
    covariance_bandwidth=0.30,
    measurement_error="fixed_matrix",
    measurement_error_covariance=np.array(
        [[0.0025, 0.0005], [0.0005, 0.0030]]
    ),
    same_time_tolerance=1e-12,
    psd_action="project",
    score_failure_action="retain_nan",
)

print(sparse_mfpca_async_score_frame(fit).head())
print(sparse_mfpca_async_reporting_text(fit))
```

The API is intentionally in a dedicated 1.1 module and is not added to the frozen 1.0 root export boundary.

## Analysis support

The `evaluation_grid` is a fitted-population grid, not a raw sampling grid. It must lie within the pooled observed support of **both** coordinates.

With `analysis_support_action="restrict"`, only actually observed coordinate samples outside the declared support are removed. The implementation never fabricates the missing coordinate at a retained timestamp. Raw/effective x and y sample counts remain visible in `support_diagnostics`.

## Diagnostics to inspect

Before downstream analysis, inspect:

- `result.score_diagnostics`;
- `result.support_diagnostics`;
- `result.covariance_pair_counts`;
- `result.covariance_diagnostics`;
- `result.provenance["sparse_mfpca_async"]`.

Important fields include per-curve x/y/scalar observation counts, simultaneous pairs, score-system conditioning, excluded same-time latent cross-products, actual measurement-error cross-links, joint PSD correction, and whether score failures were retained.

## Relationship to the synchronous estimator

The asynchronous implementation is additive; it does not alter `fit_sparse_mfpca()` or its failure semantics. The stable synchronous estimator still fails closed on coordinate-specific missingness.

In the qualified fully paired design, the asynchronous path reduced numerically to the synchronous estimator with maximum absolute differences of exactly `0.0` for the fitted mean, all covariance blocks, eigenvalues, and joint PACE scores.

## Current qualification boundary

Known-truth qualification covers:

- a fully paired reduction case;
- staggered x/y grids with only endpoint overlap;
- mixed simultaneous and coordinate-specific observations;
- diagonal and correlated declared measurement-error covariance;
- separate Cxx/Cxy/Cyy recovery;
- joint eigenspace and score recovery;
- exact same-time latent/error covariance accounting;
- deterministic replay;
- explicit failure when cross-channel support is eliminated.

See [asynchronous sparse-MFPCA validation](../validation/sparse-mfpca-async.md) for the exact observed metrics and nonclaims.

## Deliberate limitations

This tranche does **not** add:

- automatic asynchronous bandwidth selection;
- conditional score uncertainty for asynchronous layouts;
- full population-refit uncertainty;
- multilevel + multivariate sparse decomposition;
- heteroskedastic/time-varying measurement error;
- device-clock synchronization;
- partial/future trajectory prediction.

Those are separate estimands and require separate validation.

## Reporting

Report the union-of-native-timestamps representation, coordinate-specific sample counts, evaluation support, mean/covariance bandwidths, same-time tolerance, measurement-error covariance, joint PSD policy, retained components, score ridge/failure policy, excluded same-time latent cross-product count, and failed-score count.

State explicitly that raw x/y observations were not synchronized or interpolated and that the score covariance used the full fitted joint covariance rather than a rank-$K$ reconstruction.
