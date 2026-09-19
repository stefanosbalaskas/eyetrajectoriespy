# Changelog

## 0.4.0.dev0 — 2026-09-19

Fourth development tranche.

- leakage-aware held-out reconstruction cross-validation for FPCA/MFPCA component counts;
- grouped cross-validation that keeps repeated participant/group trials out of both train and test simultaneously;
- explicit minimum-RMSE and one-standard-error component-selection rules;
- fold assignment and reconstruction-error diagnostics with retained provenance;
- matched, sign-aligned bootstrap pointwise envelopes for functional principal-component shapes;
- participant- or curve-level bootstrap resampling with deterministic seeds;
- explicit descriptive-only envelope semantics; no simultaneous confidence-band claim;
- plotting and manuscript-reporting helpers for component selection and component-shape uncertainty;
- worked grouped-CV/bootstrap example, methodological guidance, interpretation, limitations, preregistration, and API documentation.


## 0.3.0.dev0 — 2026-09-18

Third development tranche.

- FPCA anomaly screening combining integrated reconstruction error and FPC score-space Mahalanobis distance;
- robust Minimum Covariance Determinant or explicit empirical score covariance;
- participant-/group-aware leave-one-group-out FPCA influence analysis;
- matched component-shape and explained-variance sensitivity summaries;
- functional review flags that never trigger automatic exclusion;
- optional scikit-fda functional boxplot and magnitude-shape outlier screening;
- plotting and manuscript-reporting helpers for outlier/influence diagnostics;
- synthetic truth example with an injected atypical trajectory;
- sparse-irregular FPCA decision guidance and expanded pre-registration/reporting safeguards;
- backend-independent basis-family/B-spline contract validation before optional scikit-fda import.

## 0.2.0.dev0 — 2026-09-18

Second development tranche.

- native `IrregularTrajectorySet` objects preserve curve-specific sampling without forced interpolation;
- explicit overlap/union common-grid construction and gap-protected irregular-to-grid projection;
- bootstrap FPCA component stability with curve- or participant-level resampling and deterministic seeds;
- matched functional-component similarity and reconstruction diagnostics;
- phase functions and phase FPCA from registration warpings;
- registered-versus-unregistered FPCA sensitivity diagnostics;
- provenance-preserving optional B-spline/Fourier projection through scikit-fda;
- expanded examples for irregular data, stability, phase analysis, and basis interoperability;
- tutorial gallery, pre-registration checklist, and expanded methods/site navigation;
- optional FDA interoperability CI.

## 0.1.0.dev0 — 2026-09-18

Initial development release.

- canonical functional trajectory data model with provenance;
- long-format gaze import and explicit coordinate/time semantics;
- conservative resampling, gap handling, smoothing, and time normalization;
- grid-based univariate and multivariate FPCA;
- reconstruction, score extraction, and component interpretation helpers;
- multilevel participant/trial FPCA decomposition;
- compositional AOI-probability FPCA with simplex-preserving inverse transform;
- landmark registration and explicit phase/amplitude outputs;
- optional elastic SRVF integration through `fdasrsf`;
- functional L2 distances, FPCA-score clustering, and scalar-on-function regression;
- synthetic trajectory generators and manuscript-oriented reporting helpers;
- MkDocs methods site, worked examples, interpretation guidance, and CI workflows.
