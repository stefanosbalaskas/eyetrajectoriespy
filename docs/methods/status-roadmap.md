# Capability status and roadmap

## Current stable scientific surface — 1.1.0

`1.1.0` is the current stable production release. The frozen 1.0 package-root compatibility boundary remains the baseline contract for the 1.x line, while the qualified A1–C1 additions are stable module-scoped 1.1 APIs.

The current development line is **1.1.0**. Post-1.1 research and workflow branches retain that source/distribution identity until a separate reviewed version-governance tranche authorizes a future 1.2 development version; feature work alone does not change package identity.

Final `1.1.0` publication completed on 7 October 2026 after fresh literal-version qualification, production-installed observation, a separate governance-only arming step, and exact protected-main verification. Post-publication GitHub/PyPI readiness is jointly disarmed.

The frozen 1.0 public boundary contains **455 stable public exports** and three explicitly experimental APIs. No deprecations or removals were authorized by the 1.0 stabilization programme, and 1.1 did not mechanically expand that package-root boundary.

The post-1.0 sparse/irregular programme (#158) and integration/readiness programme (#183) are complete. Their RC, final-qualification, publication and closeout records remain immutable historical evidence.

Active post-1.1 development is again evidence-driven rather than version-number-driven:

1. **Bayesian sparse comparator programme (#205):** B1 external-comparator evidence is complete and merged; B2 replication/tuning sensitivity and B3 uncertainty calibration are in progress. B4 remains undecided, and no native Bayesian public API is authorized.
2. **Transparent workflow programme (#209):** W1 infrastructure begins the 1.2 product/orchestration line. Workflow APIs must preserve explicit analyst decisions, ordered composition, diagnostics, provenance and underlying primitive results rather than infer a preferred analysis automatically.

`eyetrajectoriespy` remains intentionally an **eye-tracking functional-analysis layer**, not a reimplementation of every general FDA estimator or an auto-analysis system.

## Stable core scientific routes

| Scientific object | Status | Primary API |
|---|---|---|
| Common-grid functional gaze | stable 1.0 | `TrajectorySet`, `fit_fpca()`, `fit_mfpca()` |
| Native curve-specific time grids | stable 1.0 | `IrregularTrajectorySet` |
| Sparse univariate covariance FPCA + PACE | stable 1.0; natively qualified since 0.10 | `fit_sparse_fpca()` |
| Sparse paired planar MFPCA + joint PACE | stable 1.0; qualified in 0.12 | `fit_sparse_mfpca()` |
| Functional simulation / known-truth recovery | stable validation infrastructure | simulation and recovery APIs |
| Function-on-scalar regression | stable 1.0 | `fit_function_on_scalar_regression()` |
| Generalized Bernoulli / grouped-binomial / Poisson functional responses | stable guarded marginal GEE line | `fit_generalized_function_on_scalar_regression()` |
| Repeated-trial Gaussian functional mixed effects | stable 1.0 | `fit_functional_mixed_effects_regression()` |
| Multilevel participant/trial FPCA | stable 1.0 | `fit_multilevel_fpca()` |
| Registration / phase decomposition | stable 1.0 | `register_to_landmarks()`, `fit_phase_fpca()` |
| Continuous trajectory geometry and distance | stable 1.0 | geometry, L2, Fréchet, DTW APIs |
| Recurrence / nonlinear diagnostics | implemented; experimental status remains explicit where applicable | RQA, LLE, surrogate, TE APIs |

## Completed 1.1 scientific surface — A1–C1

The completed post-1.0 programme is additive and module-scoped. These APIs were developed on `1.1.0.dev0`, qualified and observed through immutable `1.1.0rc1`, freshly requalified under literal final `1.1.0`, and are now part of the published stable 1.1 release.

| Tranche | Scientific capability | Supported module/API | Qualified boundary |
|---|---|---|---|
| A1 | conditional sparse-PACE score uncertainty | `sparse_score_uncertainty` | conditional on fitted population objects; not full estimation uncertainty |
| A2 | audited sparse-FPCA bandwidth selection | `sparse_bandwidth_selection` | opt-in curve/group CV; no hidden fitter selection |
| A3 | candidate-sample observation-process diagnostics | `observation_process` | descriptive diagnostics only; no MAR/MNAR identification or inverse-intensity correction |
| A4 | conditional joint-PACE score uncertainty | `sparse_multivariate_score_uncertainty` | full fitted joint score system; not full population-estimation uncertainty |
| A5 | audited sparse-MFPCA bandwidth selection | `sparse_multivariate_bandwidth_selection` | mean/covariance bandwidths only; measurement-error specification remains fixed |
| B1 | native sparse participant/trial multilevel FPCA | `sparse_multilevel` | univariate two-level hierarchy with explicit identifiability/PSD/BLUP diagnostics |
| B2 | asynchronous coordinate-specific sparse planar MFPCA | `sparse_multivariate_async` | exact native x/y grids; no hidden synchronization/interpolation |
| C1 | future/partially observed sparse trajectory prediction | `sparse_partial_prediction` | Gaussian conditional moments using the full fitted covariance |
| C1 | participant-aware split-conformal future bands | `sparse_partial_conformal` | finite-grid future-observation coverage under the declared grouping/exchangeability contract |

See the [1.1 module API](../reference/one-dot-one-module-api.md) and [1.1 integration audit](../reference/one-dot-one-integration-audit.md). The frozen/root 1.0 API remains separately documented and machine-checked.

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
- raw sparse samples are not silently interpolated to make them compatible with dense-grid estimators;
- asynchronous x/y observations are not synchronized by interpolation before B2 fitting;
- conditional PACE or prediction covariance is not labelled full population-estimation uncertainty;
- conformal finite-grid future-observation coverage is not labelled continuous latent-function coverage.

## Validation and qualification model

Scientific qualification remains separated into:

1. exact or analytical truth where available;
2. independent implementation/reference comparisons where scientifically appropriate;
3. known-truth finite-sample recovery;
4. descriptive stress evidence for difficult observation regimes; and
5. runtime / peak-memory evidence that does not weaken scientific gates.

The 0.11 recovery laboratory remains the standing infrastructure for later methodology. The 0.12 sparse-MFPCA line was promoted only after native recovery, observation-process stress, direct/two-stage sensitivity, external mGSFPCA comparison, performance qualification, exact-version package qualification, production-installed observation, and the complete release matrix were closed.

Final `1.0.0` preserves that frozen scientific/API surface. The RC was observed outside the checkout on Python 3.11–3.13, final `1.0.0` received fresh exact-version performance and complete PR/exact-main qualification, and production workflow #18 published the final version from exact arming commit `d90fbbeea390054019e7689badedf5011ee09c22`. Post-publication readiness is disarmed again.

The R4 `1.1.0.dev0` development-readiness ledger, published `1.1.0rc1` qualification/observation evidence, fresh literal-final `1.1.0` qualification, production publication and post-publication closeout remain immutable historical records. Frozen 1.0, R4, RC and final records are not relabelled for later development programmes.

## Published release sequence

### 0.10.0 — native sparse univariate FPCA / PACE

Introduced the backend-independent native sparse univariate estimator operating directly on `IrregularTrajectorySet`, with explicit pooled mean/covariance smoothing, measurement-error handling, weighted covariance eigendecomposition, PSD policy, and conditional PACE scoring.

### 0.11.0 — known-truth recovery laboratory

Added explicit latent truth, declared finite-sample scenarios, recovery metrics, deterministic qualification scenarios, descriptive stress regimes, failure retention, Monte Carlo aggregation, portable evidence, and reporting helpers. This was a validation-infrastructure tranche rather than another estimator catalogue.

### 0.12.0 — native sparse planar MFPCA / joint PACE

Added the direct joint sparse planar estimator, block-aware recovery, tied-eigenspace/Procrustes-aware score recovery, two-stage sensitivity comparison, external mGSFPCA sensitivity, observation-process stress, and dedicated runtime/RSS qualification.

### 1.0.0rc1 — frozen 1.0 API release candidate

Published 4 October 2026 as the evidence-backed 1.0 API candidate after exact-version qualification. Post-publication installed-artifact observation closed without identifying a result-changing or frozen-public-API defect.

### 1.0.0 — stable compatibility baseline

Published 4 October 2026 after literal final-version qualification and a separate governance-only arming step. The release changed package identity and compatibility status rather than adding scientific functionality. The stable 1.0 boundary is the compatibility contract for the 1.x line.

### 1.1.0rc1 — production-observed 1.1 release candidate

Published 6 October 2026 after exact-version qualification. Production-installed observation exercised the 1.1 sparse/irregular module surface on Python 3.11–3.13 before final promotion.

### 1.1.0 — current stable release

Published 7 October 2026 after fresh literal-final qualification and a separate governance-only publication arming step. The release promotes the qualified A1–C1 module-scoped surface to stable 1.1 status while preserving the frozen 1.0 package-root compatibility boundary. Post-publication readiness is disarmed and the complete closeout matrix is green.

Published tags and release artifacts remain immutable historical records. New documentation or later APIs do not retroactively alter the scientific identity of earlier releases.

## Completed post-1.0 sparse/irregular inference programme

Issue #158 closed after the following evidence-driven sequence completed:

1. conditional PACE and joint-PACE score uncertainty with full-refit uncertainty kept distinct;
2. audited opt-in univariate and planar bandwidth selection with declared resampling units and retained failures;
3. candidate-sample observation-process diagnostics before any correction estimator;
4. sparse participant/trial multilevel FPCA;
5. asynchronous/coordinate-specific sparse planar MFPCA without hidden interpolation; and
6. future/partially observed trajectory prediction with participant-aware conformal calibration.

R1–R4 under issue #183 subsequently qualified the integrated product surface and R5 approved entry into exact-version RC qualification. The scientific programme is therefore no longer the active roadmap.

## Later or conditional methodology

Irregular functional mixed effects, shape/manifold analysis, genuinely functional clustering/classification, focused Bayesian sparse modelling, and additional nonlinear/state-space methods remain later or conditional work. Device/clock synchronization remains outside the package except for narrow audit interfaces.

For versioning, the intended posture is:

- **1.0.x** — compatible bug fixes, documentation, portability, validation and performance improvements;
- **1.x** — additive capabilities or deliberately governed compatible extensions;
- **2.0** — breaking stable API/scientific-contract changes after explicit deprecation, except when an exceptional correction is necessary to prevent demonstrably wrong scientific results.

No version number by itself commits the project to a scientific capability or release. Promotion remains contingent on product evidence, method-specific validation, integrated qualification and the package's release-governance gates.
