# Sparse irregular FPCA with PACE

!!! note "Current backend and native roadmap"
    In 0.9.1, `fit_sparse_fpca_fdapy()` is an explicitly backend-named
    compatibility path. FDApy is not a core dependency. The 0.10 development
    branch now contains the native `fit_sparse_fpca()` estimator, while FDApy
    remains a validation/reference implementation. See the
    [0.10 development contract](../development/native-sparse-fpca.md).


Irregular sampling and sparse sampling are related but different problems.

A trajectory can be **irregular but dense**: many observations are available, but their exact times differ across curves.

A trajectory can also be **sparse and irregular**: only a small number of noisy observations are available per curve and their times differ across curves.

Those settings should not be forced into the same preprocessing pipeline.

## Dense irregular trajectories

When trajectories are well observed and interpolation fills only modest gaps, an explicit common-grid projection can be reasonable:

```python
irregular = from_irregular_long_dataframe_native(...)
grid = make_common_grid(
    irregular,
    n_time=121,
    domain="overlap",
)

gaze = resample_irregular_to_grid(
    irregular,
    grid,
    max_gap=0.10,
)
```

The common-grid decision remains visible in provenance.

## Sparse irregular trajectories

When interpolation would create a large fraction of the analyzed curve, use a sparse functional estimator instead of fabricating a dense observation process.

PACE-style FPCA estimates population mean/covariance structure from pooled irregular observations and recovers individual FPC scores through conditional expectation.

The original sparse-FDA framework is designed for irregularly spaced longitudinal observations with relatively few repeated measurements per observational unit and explicitly models measurement error.

## Native 0.10 development estimator

The 0.10 development branch contains a native univariate sparse FPCA + PACE
estimator whose statistical and numerical choices are explicit rather than
delegated to an external backend.

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

The native estimator smooths the pooled mean directly from irregular
observations, constructs off-diagonal within-curve covariance products,
smooths the latent covariance surface, audits positive-semidefinite repair on
the quadrature-weighted operator, and computes PACE scores from the **full
fitted covariance surface** rather than a covariance reconstructed from only
the retained components.

The evaluation-grid endpoints define the analysis support. Observations outside
that interval cause an error by default. They are excluded only when
`analysis_support_action="restrict"` is supplied explicitly, with exclusion
counts retained in provenance.

When diagonal-difference noise estimation is used, `noise_support=` is
mandatory. This prevents the package from silently treating the whole fitted
domain as the preferred noise-estimation interval.

### Native diagnostic plots

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

The component plot shows the fitted mean and a declared multiple of the
retained eigenfunction mode. The covariance plot displays the fitted latent
covariance surface. The score diagnostic shows each PACE conditional
covariance condition number against the number of native observations used.

### Validation interpretation

The 0.10 stress matrix distinguishes population-subspace recovery from
individual-score recovery. In the qualified very-sparse 2–4 sample regime,
the leading two-dimensional functional subspace remained reasonably aligned
with truth while one component's individual PACE-score correlation could be
weak. In the well-powered low-noise regime, subspace and score recovery were
strong and eigenvalue error decreased substantially.

Therefore, recovering the population subspace does **not** by itself guarantee
precise individual PACE scores for extremely sparse curves.

A deliberately too-narrow bandwidth regime fails closed when local support is
insufficient rather than silently extrapolating or dropping unsupported grid
locations.

See [native sparse FPCA/PACE validation](../validation/sparse-fpca-validation.md)
for the evidence classes, stress design, FDApy comparison boundary, and
performance envelope.
## Current 0.9.1 compatibility backend: FDApy PACE interoperability

The currently released backend-specific sparse workflow is intentionally narrow:

- source object: `IrregularTrajectorySet`;
- one explicitly named functional dimension at a time;
- FDApy covariance-operator `UFPCA`;
- PACE conditional-expectation score recovery;
- eyetrajectoriespy does not pre-interpolate raw curves before backend fitting;
- FDApy's irregular PACE score path may smooth/interpolate internally;
- explicit fit smoothing, score smoothing, PACE tolerance, and normalization settings;
- original curve IDs, metadata, coordinate system, time unit, sample counts, and backend version retained in the result.

Install the optional backend:

```bash
pip install -e ".[sparse]"
```

## Backend compatibility

The eyetrajectoriespy core supports Python 3.11–3.13. The current FDApy 1.0.3 optional sparse backend is qualified on Python 3.11–3.12. FDApy 1.0.3 depends on NumPy <2.0, while NumPy 1.26.x supports Python only through 3.12.

Use a Python 3.11 or 3.12 environment for the `sparse` extra until the backend dependency line supports Python 3.13.

This restriction applies only to the optional FDApy interoperability layer; native irregular objects and the rest of eyetrajectoriespy remain available on Python 3.13. The planned native 0.10 sparse estimator is specifically intended to remove this backend constraint from the canonical sparse workflow.

## Inspect sparse sampling first

```python
summary = sparse_dimension_summary(
    irregular,
    dimension="x",
)

print(summary)
plot_sparse_irregular_dimension(
    irregular,
    dimension="x",
)
```

The summary includes observed counts, non-finite values, domain span, and observed-interval diagnostics.

### Missing observations

For the sparse backend, an absent observation should be represented as an **absent sample**, not a `NaN` value retained at a sampled time.

`fit_sparse_fpca_fdapy()` therefore rejects non-finite values in the selected dimension instead of silently dropping or interpolating them.

If a tracker export contains rows with missing gaze, clean the native sparse representation explicitly before fitting and report that rule.

## Fit sparse FPCA and recover PACE scores

```python
result = fit_sparse_fpca_fdapy(
    irregular,
    dimension="x",
    n_components=3,
    fit_smoothing="PS",
    score_smoothing="LP",
    tol=1e-4,
    normalize=False,
    evaluation_grid=np.unique(np.concatenate(irregular.time)),
)
```

The backend estimator is FDApy `UFPCA(method="covariance")`. Scores are recovered with:

```text
transform(..., method="PACE")
```

FDApy documents PACE score estimation for sparse UFPCA and exposes the tolerance used when inverting the conditional score system.

### Evaluation grid

The sparse observations remain on their native grids, but the estimated mean, covariance, and eigenfunctions are represented on evaluation points.

Use `evaluation_grid=` when you want that grid to be explicit and reproducible. It must be finite, one-dimensional, and strictly increasing.

Leaving it as `None` delegates the evaluation-point choice to FDApy and records that choice as a backend default.

### Advanced smoothing parameters

FDApy exposes separate keyword dictionaries for sparse mean and covariance smoothing. eyetrajectoriespy passes them explicitly:

```python
result = fit_sparse_fpca_fdapy(
    irregular,
    dimension="x",
    n_components=3,
    evaluation_grid=np.linspace(0.0, 1.0, 101),
    kwargs_mean={"bandwidth": 0.08},
    kwargs_covariance={"bandwidth": 0.10},
)
```

These dictionaries are retained in provenance. Use only parameters supported by the installed FDApy version and report them.

## Preserve metadata with scores

```python
scores = sparse_fpca_score_frame(result)
print(scores.head())
```

The output starts with `curve_id`, preserves curve metadata, and then adds `SFPC1`, `SFPC2`, and so on.

## Why only one gaze dimension?

The current public contract is deliberately **univariate sparse PACE**.

FDApy supports sparse multivariate functional-data representations and sparse MFPCA. However, the documented MFPCA score transform currently uses numerical integration or inner-product scores rather than PACE conditional-expectation scoring.

Therefore:

- `fit_sparse_fpca_fdapy(..., dimension="x")` is a valid sparse univariate PACE analysis of x(t);
- fitting y(t) separately is another univariate analysis;
- two separate univariate analyses are **not** equivalent to joint multivariate FPCA of [x(t), y(t)];
- eyetrajectoriespy does not label the current adapter “multivariate PACE.”

## Smoothing is part of the model

The sparse estimator must estimate smooth mean/covariance structure from irregular observations.

The defaults are explicit:

- `fit_smoothing="PS"`;
- `score_smoothing="LP"`;
- `tol=1e-4`.

These are not universally optimal values. Treat them as model settings and conduct sensitivity analysis when conclusions depend on them.

If an explicit `evaluation_grid` is supplied, it must be finite, strictly increasing, remain inside the pooled support, **and equal the sorted unique pooled observed sample times** under the validated FDApy 1.0.x PACE path.

## Component count

For the native 0.10 estimator, `n_components` is not capped automatically at
`n_curves - 1`. The smoothed irregular covariance surface is not the ordinary
centered empirical covariance matrix of fully observed curves. Availability is
instead governed by the positive spectrum of the fitted quadrature-weighted
covariance operator above the declared `positive_eigen_tolerance`.

For the FDApy 1.0.x compatibility path, backend-specific rank and component
constraints still apply.

Do not transfer a component count selected from interpolated dense FPCA
automatically to sparse PACE. The estimand and score-recovery mechanism differ.

## Interpretation

A sparse FPC describes a dominant mode of variation in the latent smooth process estimated from pooled sparse observations.

A PACE score is a conditional estimate of a curve's latent FPC score given its sparse observations and the fitted population mean/covariance structure.

It is not the same object as a numerical-integration score computed from a densely observed curve.

## Reporting example

> Horizontal gaze trajectories were supplied to the sparse FDApy backend on their native curve-specific observation grids without an eyetrajectoriespy preprocessing step that interpolated raw curves to a common grid. FDApy's irregular PACE implementation may smooth/interpolate internally as part of its score path. Univariate sparse FPCA used FDApy's covariance-operator UFPCA implementation with P-spline fitting smoothness. Individual scores were estimated using PACE conditional expectation with tolerance 1×10⁻⁴ and local-polynomial score smoothing. Three components were retained. Per-curve observation counts ranged from 8 to 15. Sensitivity analyses varied the smoothing configuration and retained dimension.

Use `sparse_fpca_reporting_text()` as a reproducible starting point.

## Limitations

The current adapter does not:

- provide joint x/y PACE scoring;
- estimate a full sparse functional mixed model;
- choose smoothing parameters automatically on theoretical grounds;
- convert `NaN` placeholders into absent observations;
- claim equivalence between PACE scores and dense-grid projection scores;
- propagate all sparse-FPCA estimation uncertainty into downstream models.

## API links

- `sparse_dimension_summary()`
- `plot_sparse_irregular_dimension()`
- `to_fdapy_irregular()`
- `fit_sparse_fpca()`
- `fit_sparse_fpca_fdapy()`
- `sparse_fpca_score_frame()`
- `plot_sparse_fpca_component()`
- `plot_sparse_fpca_covariance()`
- `plot_sparse_fpca_score_diagnostics()`
- `sparse_fpca_reporting_text()`
- `SparseFPCAResult`

## Methodological sources

Yao, Müller, and Wang (2005) developed the sparse longitudinal FPCA framework based on pooled mean/covariance estimation and conditional score recovery.

FDApy 1.0.3 documents `IrregularFunctionalData`, sparse `UFPCA`, covariance-operator estimation, and PACE score transformation.

See the [references](../methods/references.md) and the [worked sparse PACE example](../examples/sparse-pace-fpca.md).
