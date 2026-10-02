# Sparse univariate FPCA / PACE

!!! success "Stable native univariate sparse workflow"
    `fit_sparse_fpca()` is the stable native univariate sparse FPCA/PACE route. FDApy remains an optional compatibility/reference backend rather than a core dependency.

!!! info "Need jointly modelled sparse x/y gaze?"
    `fit_sparse_fpca()` models one functional coordinate. For jointly observed sparse planar gaze with direct $C_{xy}(s,t)$ estimation and joint PACE scores, use [`fit_sparse_mfpca()`](sparse-multivariate-fpca.md).

Irregular sampling and sparse sampling are related but different problems. A trajectory may be irregular but dense enough for a scientifically defensible explicit common-grid projection, or sparse enough that interpolation would manufacture much of the analyzed curve.

## Choose the representation first

For dense irregular trajectories, an explicit projection may be reasonable:

```python
irregular = from_irregular_long_dataframe_native(...)
grid = make_common_grid(irregular, n_time=121, domain="overlap")
gaze = resample_irregular_to_grid(irregular, grid, max_gap=0.10)
```

For sparse trajectories, use a sparse functional estimator instead of fabricating a dense observation process.

## Native stable estimator

```python
import numpy as np
from eyetrajectoriespy import fit_sparse_fpca

result = fit_sparse_fpca(
    irregular,
    dimension="x",
    n_components=2,
    evaluation_grid=np.linspace(0.0, 1.0, 41),
    mean_bandwidth=0.24,
    covariance_bandwidth=0.34,
    noise_variance_method="diagonal_difference",
    noise_bandwidth=0.24,
    noise_support=(0.20, 0.80),
    psd_action="project",
    score_ridge=0.0,
)
```

The native estimator pools irregular observations to estimate a latent mean and covariance surface, diagonalizes the quadrature-weighted covariance operator, and estimates individual scores using PACE conditional expectation.

For curve $i$,

$$
\widehat\Sigma_i=
\widehat G(T_i,T_i)+\widehat\sigma_\epsilon^2 I+\gamma I,
$$

and

$$
\widehat\xi_{ik}
=
\widehat\lambda_k\widehat\phi_k(T_i)^\top
\widehat\Sigma_i^{-1}
\{Y_i-\widehat\mu(T_i)\}.
$$

The conditional system uses the **full fitted covariance surface**. `n_components` controls the returned eigensystem/scores; it does not replace the full covariance by a rank-K reconstruction for scoring.

## Analysis support and noise estimation

The evaluation-grid endpoints define the declared analysis support. Observations outside that interval raise by default and are excluded only when `analysis_support_action="restrict"` is explicitly supplied, with exclusions retained in provenance.

When `noise_variance_method="diagonal_difference"` is used, `noise_support=` is mandatory. This prevents the package from silently treating the whole domain as the preferred noise-estimation interval.

If a defensible external/design-based measurement-error variance is available, `noise_variance_method="fixed"` remains the explicit alternative.

## Native diagnostic plots

```python
from eyetrajectoriespy import (
    plot_sparse_fpca_component,
    plot_sparse_fpca_covariance,
    plot_sparse_fpca_score_diagnostics,
)

plot_sparse_fpca_component(result, component=0)
plot_sparse_fpca_covariance(result)
plot_sparse_fpca_score_diagnostics(result)
```

The component plot shows the fitted mean plus/minus a declared multiple of an eigenfunction mode. The covariance plot shows the fitted latent covariance surface. The score diagnostic shows conditional-system conditioning against native observation counts.

## Sparse samples are not raw interpolation

```text
native sparse sample
    !=
raw-trajectory interpolation

fitted population function evaluated at native time
    !=
raw-trajectory interpolation
```

The estimator evaluates fitted population objects at native observation times as part of PACE. That does not create an interpolated raw trajectory.

## Validation interpretation

The qualified sparse-FPCA evidence distinguishes population-subspace recovery from individual-score recovery. In extremely sparse regimes, the leading population subspace may remain recoverable while individual PACE scores are imprecise. Therefore population recovery does not by itself guarantee precise subject-level scores.

A deliberately too-narrow bandwidth regime fails closed when local support is insufficient rather than silently extrapolating unsupported grid locations.

See [native sparse FPCA/PACE validation](../validation/sparse-fpca-validation.md).

## Optional FDApy compatibility/reference backend

`fit_sparse_fpca_fdapy()` remains an explicitly backend-named interoperability/reference path. It is not required by the native estimator and does not define the canonical scientific contract.

```bash
pip install -e ".[sparse]"
```

The package core supports Python 3.11–3.13. FDApy 1.0.3 is separately qualified only where its NumPy/Python dependency line permits it.

## Inspect sparse sampling first

```python
summary = sparse_dimension_summary(irregular, dimension="x")
print(summary)
plot_sparse_irregular_dimension(irregular, dimension="x")
```

An absent observation should be represented as an absent sample, not as a retained sampled time with a `NaN` value that the estimator silently repairs.

## Preserve metadata with scores

```python
scores = sparse_fpca_score_frame(result)
print(scores.head())
```

Curve IDs and metadata are retained alongside `SFPC1`, `SFPC2`, and later score columns.

## Why this page remains univariate

Two separate univariate sparse analyses are **not** equivalent to joint multivariate FPCA of $[x(t),y(t)]$ because they omit cross-channel covariance. Stable native joint x/y PACE is documented separately in the [sparse planar MFPCA / joint PACE guide](sparse-multivariate-fpca.md).

The optional FDApy adapter remains explicitly backend-named and should not be relabelled as the native joint estimator.

## Component count

For the native estimator, component availability is governed by the positive spectrum of the fitted quadrature-weighted covariance operator above the declared tolerance, not by mechanically applying the rank of a complete common-grid empirical covariance matrix.

Do not transfer a component count selected from interpolated dense FPCA automatically to sparse PACE; the estimand and score-recovery mechanism differ.

## Interpretation

A sparse FPC is a dominant mode of variation in the latent smooth population process estimated from pooled sparse observations. A PACE score is a conditional estimate of a curve's latent FPC coordinate given its sparse observations and the fitted population model.

It is not the same object as a numerical-integration score from a densely observed curve.

## Reporting

Use `sparse_fpca_reporting_text()` as a reproducible starting point and report native sampling, analysis support, mean/covariance bandwidths, noise-variance method/support, PSD policy, score ridge, retained components, and any score failures.

## Limitations

The univariate route does not:

- model cross-channel covariance when x and y are fitted separately;
- select smoothing parameters automatically on theoretical grounds;
- turn `NaN` placeholders into absent observations;
- claim equivalence between PACE and dense-grid projection scores; or
- propagate all sparse-FPCA estimation uncertainty automatically into downstream models.

## API links

- `sparse_dimension_summary()`
- `plot_sparse_irregular_dimension()`
- `fit_sparse_fpca()`
- `fit_sparse_fpca_fdapy()`
- `sparse_fpca_score_frame()`
- `plot_sparse_fpca_component()`
- `plot_sparse_fpca_covariance()`
- `plot_sparse_fpca_score_diagnostics()`
- `sparse_fpca_reporting_text()`
- `SparseFPCAResult`

See the [worked sparse PACE example](../examples/sparse-pace-fpca.md), [mathematical reference](../methods/mathematical-reference.md#sparse-fpca-pace), and [references](../methods/references.md).
