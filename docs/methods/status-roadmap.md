# Capability status and roadmap

## Current stable scientific surface — 0.12.0

`0.12.0` is the current stable release.

The 0.12 sparse-MFPCA/joint-PACE line is complete and frozen. The package is not currently committed to another estimator tranche.

Near-term work prioritizes:

- real-use and API audit;
- documentation and worked examples;
- complete plotting/gallery coverage;
- public benchmark/case-study material;
- software/methodology dissemination; and
- evaluation of 1.0 API-stability requirements.

Future methodology is evidence-driven rather than version-number-driven.

`eyetrajectoriespy` is intentionally an **eye-tracking functional-analysis layer**, not a reimplementation of every general FDA estimator.

## Stable core scientific routes

| Scientific object | Status | Primary API |
|---|---|---|
| Common-grid functional gaze | stable | `TrajectorySet`, `fit_fpca()`, `fit_mfpca()` |
| Native curve-specific time grids | stable | `IrregularTrajectorySet` |
| Sparse univariate covariance FPCA + PACE | stable; natively qualified since 0.10 | `fit_sparse_fpca()` |
| Sparse paired planar MFPCA + joint PACE | stable; qualified in 0.12 | `fit_sparse_mfpca()` |
| Functional simulation / known-truth recovery | stable validation infrastructure since 0.11 | simulation and recovery APIs |
| Function-on-scalar regression | stable | `fit_function_on_scalar_regression()` |
| Generalized Bernoulli / grouped-binomial / Poisson functional responses | stable guarded marginal GEE line | `fit_generalized_function_on_scalar_regression()` |
| Repeated-trial Gaussian functional mixed effects | stable | `fit_functional_mixed_effects_regression()` |
| Multilevel participant/trial FPCA | stable | `fit_multilevel_fpca()` |
| Registration / phase decomposition | stable | `register_to_landmarks()`, `fit_phase_fpca()` |
| Continuous trajectory geometry and distance | stable | geometry, L2, Fréchet, DTW APIs |
| Recurrence / nonlinear diagnostics | implemented; experimental status remains explicit where applicable | RQA, LLE, surrogate, TE APIs |

## What 0.12 added

The defining 0.12 addition is native sparse multivariate FPCA / joint PACE for jointly observed planar gaze. Its scientific object is

$$
\mathbf X_i(t)=
\begin{bmatrix}X_i(t)\\Y_i(t)\end{bmatrix},
$$

with full block covariance

$$
\mathbf C(s,t)=
\begin{bmatrix}
C_{xx}(s,t) & C_{xy}(s,t)\\
C_{yx}(s,t) & C_{yy}(s,t)
\end{bmatrix}.
$$

The canonical estimator directly estimates the directional cross-channel covariance, performs PSD handling on the joint weighted operator, retains the declared measurement-error covariance, and uses the **full fitted joint covariance** in the joint PACE conditional system. `n_components` controls the returned eigensystem/scores rather than reconstructing the conditional covariance at rank K.

See the [stable sparse planar guide](../guides/sparse-multivariate-fpca.md), [mathematical reference](mathematical-reference.md#sparse-mfpca-joint-pace), [recovery evidence](../validation/sparse-mfpca-recovery.md), [comparator sensitivity](../validation/sparse-mfpca-comparator-sensitivity.md), and [0.12.0 release notes](../releases/0.12.0.md).

## Optional specialist interoperability

| Capability | Backend | Package role |
|---|---|---|
| B-spline/Fourier basis representation | scikit-fda | preserve provenance while delegating basis mathematics |
| Functional boxplot / magnitude-shape review | scikit-fda | optional sensitivity/review diagnostics |
| Sparse covariance UFPCA + PACE | FDApy | optional compatibility/reference backend for the univariate route |
| Elastic SRVF trajectory alignment | fdasrsf | specialist phase/amplitude backend |
| Sparse multivariate external comparison | mGSFPCA | qualification/sensitivity comparator, not the canonical estimator |

Optional backends are never imported until the corresponding feature is requested.

## Not silently approximated

The package does not replace scientifically distinct targets with convenient substitutes. Examples include:

- separate univariate sparse x/y fits are not labelled joint sparse MFPCA;
- review flags are not automatic inferential exclusions;
- covariance-sensitivity outputs do not rank or select a preferred model automatically;
- generalized marginal GEE coefficients are not labelled conditional generalized functional random effects;
- recurrence or transfer-entropy sensitivity grids are not automatic parameter selectors;
- raw sparse samples are not silently interpolated to make them compatible with dense-grid estimators.

## Validation and qualification model

Scientific qualification remains separated into:

1. exact or analytical truth where available;
2. independent implementation/reference comparisons where scientifically appropriate;
3. known-truth finite-sample recovery;
4. descriptive stress evidence for difficult observation regimes; and
5. runtime / peak-memory evidence that does not weaken scientific gates.

The 0.11 recovery laboratory remains the standing infrastructure for future methodology. The 0.12 sparse-MFPCA line was promoted only after native recovery, observation-process stress, direct/two-stage sensitivity, external mGSFPCA comparison, performance qualification, exact-version package qualification, production-installed observation, and the complete release matrix were closed.

## Published release sequence

### 0.10.0 — native sparse univariate FPCA / PACE

Introduced the backend-independent native sparse univariate estimator operating directly on `IrregularTrajectorySet`, with explicit pooled mean/covariance smoothing, measurement-error handling, weighted covariance eigendecomposition, PSD policy, and conditional PACE scoring.

### 0.11.0 — known-truth recovery laboratory

Added explicit latent truth, declared finite-sample scenarios, recovery metrics, deterministic qualification scenarios, descriptive stress regimes, failure retention, Monte Carlo aggregation, portable evidence, and reporting helpers. This was a validation-infrastructure tranche rather than another estimator catalogue.

### 0.12.0 — native sparse planar MFPCA / joint PACE

Added the direct joint sparse planar estimator, block-aware recovery, tied-eigenspace/Procrustes-aware score recovery, two-stage sensitivity comparison, external mGSFPCA sensitivity, observation-process stress, and dedicated runtime/RSS qualification. Final `0.12.0` is published on GitHub and production PyPI and the publication-readiness flags are disarmed again after release.

Published tags and release artifacts remain immutable historical records. New documentation or later APIs do not retroactively alter the scientific identity of `0.12.0`.

## Near-term documentation and API work

The post-0.12 phase is deliberately product-facing rather than estimator-driven:

- make the stable sparse-planar workflow first-class throughout the user site;
- make every public plotting API discoverable through deterministic visual documentation;
- standardize method-page structure around scientific question → estimand → mathematical contract → API → executable example → plot → assumptions/failures → provenance → validation → reporting;
- evaluate small visualization/API additions only on a new development version, never by modifying the immutable 0.12.0 release.

## Future methodology

A sparse participant/trial functional decomposition remains a plausible later candidate because it targets a different scientific object from the existing complete-grid mixed-effects regression surface. Bayesian sparse MFPCA, additional generalized families, and broad nonlinear simulation expansion remain research possibilities rather than scheduled releases.

The intended methodological progression remains:

```text
dense functional gaze
        ->
sparse univariate gaze
        ->
sparse joint planar gaze
        ->
sparse hierarchical gaze (only if recovery evidence justifies it)
```

No version number by itself commits the project to the final arrow.
