# Sparse irregular FPCA with PACE

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

## eyetrajectoriespy 0.6: optional FDApy PACE interoperability

The public sparse workflow is intentionally narrow:

- source object: `IrregularTrajectorySet`;
- one explicitly named functional dimension at a time;
- FDApy covariance-operator `UFPCA`;
- PACE conditional-expectation score recovery;
- no common-grid interpolation before estimation;
- explicit fit smoothing, score smoothing, PACE tolerance, and normalization settings;
- original curve IDs, metadata, coordinate system, time unit, sample counts, and backend version retained in the result.

Install the optional backend:

```bash
pip install -e ".[sparse]"
```

## Backend compatibility

The eyetrajectoriespy core supports Python 3.11–3.13. The current FDApy 1.0.3 optional sparse backend is qualified on Python 3.11–3.12. FDApy 1.0.3 depends on NumPy <2.0, while NumPy 1.26.x supports Python only through 3.12.

Use a Python 3.11 or 3.12 environment for the `sparse` extra until the backend dependency line supports Python 3.13.

This restriction applies only to the optional FDApy interoperability layer; native irregular objects and the rest of eyetrajectoriespy remain available on Python 3.13.

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
    evaluation_grid=np.linspace(0.0, 1.0, 101),
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

## Component count

`n_components` is explicit and cannot exceed the number of observed curves.

Do not transfer a component count selected from interpolated dense FPCA automatically to sparse PACE. The estimand and score-recovery mechanism differ.

Component-number selection for sparse FPCA should be justified using the sparse estimator's own diagnostics/model-selection strategy.

## Interpretation

A sparse FPC describes a dominant mode of variation in the latent smooth process estimated from pooled sparse observations.

A PACE score is a conditional estimate of a curve's latent FPC score given its sparse observations and the fitted population mean/covariance structure.

It is not the same object as a numerical-integration score computed from a densely observed curve.

## Reporting example

> Horizontal gaze trajectories were analyzed as sparsely observed functions without common-grid interpolation. Native curve-specific observation times were retained in an `IrregularTrajectorySet`. Univariate sparse FPCA was fitted using FDApy's covariance-operator UFPCA implementation with P-spline smoothing of the fitted functional structure. Individual scores were estimated using PACE conditional expectation with tolerance 1×10⁻⁴ and local-polynomial score smoothing. Three components were retained. Per-curve observation counts ranged from 8 to 15. Sensitivity analyses varied the smoothing configuration and retained dimension.

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
- `fit_sparse_fpca_fdapy()`
- `sparse_fpca_score_frame()`
- `sparse_fpca_reporting_text()`
- `SparseFPCAResult`

## Methodological sources

Yao, Müller, and Wang (2005) developed the sparse longitudinal FPCA framework based on pooled mean/covariance estimation and conditional score recovery.

FDApy 1.0.3 documents `IrregularFunctionalData`, sparse `UFPCA`, covariance-operator estimation, and PACE score transformation.

See the [references](../methods/references.md) and the [worked sparse PACE example](../examples/sparse-pace-fpca.md).
