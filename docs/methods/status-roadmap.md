# Capability status and roadmap

## Current stable scientific surface — 1.0.0

`1.0.0` is the current stable production release and the compatibility baseline for the 1.x line.

The current development line is **1.0.0**. This means the repository's active package/source identity remains the released stable baseline; no `1.1` development line has been opened.

The frozen 1.0 public boundary contains **455 stable public exports** and three explicitly experimental APIs. No deprecations or removals were authorized by the 1.0 stabilization programme.

There is no automatic 1.1 estimator tranche. The package has moved from release qualification into **post-1.0 maintenance and observation**: external use, issue observation, real-data case studies, documentation, portability, performance, and dissemination should drive future changes.

Near-term work prioritizes:

- preserving stable 1.0 APIs and established scientific contracts;
- external-use and issue observation against the frozen 1.0 boundary;
- reproducible real-data case studies when licensing/consent permit;
- documentation, portability, validation and non-breaking performance work; and
- software/methodology dissemination.

Future methodology is evidence-driven rather than version-number-driven.

`eyetrajectoriespy` is intentionally an **eye-tracking functional-analysis layer**, not a reimplementation of every general FDA estimator.

## Stable core scientific routes

| Scientific object | Status | Primary API |
|---|---|---|
| Common-grid functional gaze | stable | `TrajectorySet`, `fit_fpca()`, `fit_mfpca()` |
| Native curve-specific time grids | stable | `IrregularTrajectorySet` |
| Sparse univariate covariance FPCA + PACE | stable; natively qualified since 0.10 | `fit_sparse_fpca()` |
| Sparse paired planar MFPCA + joint PACE | stable; qualified in 0.12 and frozen in 1.0 | `fit_sparse_mfpca()` |
| Functional simulation / known-truth recovery | stable validation infrastructure since 0.11 | simulation and recovery APIs |
| Function-on-scalar regression | stable | `fit_function_on_scalar_regression()` |
| Generalized Bernoulli / grouped-binomial / Poisson functional responses | stable guarded marginal GEE line | `fit_generalized_function_on_scalar_regression()` |
| Repeated-trial Gaussian functional mixed effects | stable | `fit_functional_mixed_effects_regression()` |
| Multilevel participant/trial FPCA | stable | `fit_multilevel_fpca()` |
| Registration / phase decomposition | stable | `register_to_landmarks()`, `fit_phase_fpca()` |
| Continuous trajectory geometry and distance | stable | geometry, L2, Fréchet, DTW APIs |
| Recurrence / nonlinear diagnostics | implemented; experimental status remains explicit where applicable | RQA, LLE, surrogate, TE APIs |

## What 0.12 added

The defining 0.12 addition was native sparse multivariate FPCA / joint PACE for jointly observed planar gaze. Its scientific object is

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

Final `1.0.0` preserves that frozen scientific/API surface. The RC was observed outside the checkout on Python 3.11–3.13, final `1.0.0` received fresh exact-version performance and complete PR/exact-main qualification, and production workflow #18 published the final version from exact arming commit `d90fbbeea390054019e7689badedf5011ee09c22`. Post-publication readiness is disarmed again.

## Published release sequence

### 0.10.0 — native sparse univariate FPCA / PACE

Introduced the backend-independent native sparse univariate estimator operating directly on `IrregularTrajectorySet`, with explicit pooled mean/covariance smoothing, measurement-error handling, weighted covariance eigendecomposition, PSD policy, and conditional PACE scoring.

### 0.11.0 — known-truth recovery laboratory

Added explicit latent truth, declared finite-sample scenarios, recovery metrics, deterministic qualification scenarios, descriptive stress regimes, failure retention, Monte Carlo aggregation, portable evidence, and reporting helpers. This was a validation-infrastructure tranche rather than another estimator catalogue.

### 0.12.0 — native sparse planar MFPCA / joint PACE

Added the direct joint sparse planar estimator, block-aware recovery, tied-eigenspace/Procrustes-aware score recovery, two-stage sensitivity comparison, external mGSFPCA sensitivity, observation-process stress, and dedicated runtime/RSS qualification.

### 1.0.0rc1 — frozen 1.0 API release candidate

Published the evidence-backed 1.0 API boundary as an immutable production prerelease after exact-version qualification. Post-publication installed-artifact observation closed without identifying a result-changing or public-API defect.

### 1.0.0 — stable compatibility baseline

Published 4 October 2026 after literal final-version qualification and a separate governance-only arming step. The release changes package identity and compatibility status rather than adding scientific functionality. The stable 1.0 boundary is now the maintenance contract for the 1.x line.

Published tags and release artifacts remain immutable historical records. New documentation or later APIs do not retroactively alter the scientific identity of earlier releases.

## Post-1.0 maintenance and observation

The highest-value work after 1.0 is product- and evidence-facing rather than estimator-driven:

- keep the frozen stable 1.0 API boundary machine-checked;
- preserve complete deterministic visual documentation and worked workflows;
- observe external-user friction and real-data edge cases;
- add compatible fixes, validation, portability and performance improvements without changing established scientific meaning;
- turn realistic analyses into reproducible, citable case-study material; and
- defer new methodology until a demonstrated scientific gap justifies it.

For versioning, the intended posture is:

- **1.0.x** — compatible bug fixes, documentation, portability, validation and performance improvements;
- **1.x** — additive capabilities or deliberately governed compatible extensions;
- **2.0** — breaking stable API/scientific-contract changes after explicit deprecation, except when an exceptional correction is necessary to prevent demonstrably wrong scientific results.

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
