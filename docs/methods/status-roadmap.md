# Capability status and roadmap

eyetrajectoriespy is intentionally an **eye-tracking functional-analysis layer**, not a reimplementation of every general FDA estimator.

This page distinguishes implemented scientific contracts from optional interoperability and future work.

## Implemented in the core

| Capability | Status | Primary API |
|---|---|---|
| Common-grid functional gaze objects | implemented | `TrajectorySet` |
| Native curve-specific time grids | implemented | `IrregularTrajectorySet` |
| Sparse univariate covariance FPCA + PACE scores | implemented (optional FDApy backend) | `fit_sparse_fpca_fdapy()` |
| Simultaneous functional mean band | implemented | `multiplier_functional_mean_band()` |
| Explicit irregular → common-grid projection | implemented | `resample_irregular_to_grid()` |
| Univariate FPCA | implemented | `fit_fpca()` |
| Joint multivariate FPCA | implemented | `fit_mfpca()` |
| Component reconstruction | implemented | `reconstruct_fpca()` |
| Reconstruction diagnostics | implemented | `fpca_reconstruction_curve()` |
| Held-out reconstruction component selection | implemented | `cross_validate_fpca_reconstruction()` |
| Outcome-tuned FPCA regression selection | implemented | `cross_validate_fpca_regression()` |
| Nested predictive FPCA selection evaluation | implemented | `nested_cross_validate_fpca_regression()` |
| Explicit minimum / one-SE selection rules | implemented | `select_fpca_components_cv()` |
| Bootstrap FPC stability | implemented | `bootstrap_fpca_stability()` |
| Matched pointwise FPC envelopes | implemented | `bootstrap_fpca_component_envelopes()` |
| Bootstrap-calibrated simultaneous FPC-shape bands | implemented | `bootstrap_fpca_component_bands()` |
| Bootstrap FPCA spectrum uncertainty | implemented | `bootstrap_fpca_spectrum_uncertainty()` |
| FPC score basis-resampling uncertainty | implemented | `bootstrap_fpca_score_uncertainty()` |
| Adjacent retained eigengap diagnostics | implemented | `fpca_eigenvalue_gap_table()` |
| Principal-angle FPC subspace comparison | implemented | `compare_fpca_subspaces()` |
| Bootstrap eigenspace stability | implemented | `bootstrap_fpca_subspace_stability()` |
| FPCA anomaly review | implemented | `diagnose_fpca_outliers()` |
| Participant/group influence | implemented | `leave_one_group_out_fpca_influence()` |
| Landmark registration | implemented | `register_to_landmarks()` |
| Phase-function FPCA | implemented | `fit_phase_fpca()` |
| Registered vs unregistered sensitivity | implemented | `compare_registered_unregistered_fpca()` |
| Two-level participant/trial FPCA | implemented | `fit_multilevel_fpca()` |
| Compositional AOI FPCA | implemented | `fit_compositional_fpca()` |
| Functional distances | implemented | `functional_l2_distance()` |
| FPCA-score clustering | implemented | `cluster_fpca_scores()` |
| Score-based scalar-on-function regression | implemented | `fit_scalar_on_function_regression()` |
| Paired-bootstrap Gaussian FPCR uncertainty | implemented | `bootstrap_fpca_regression_uncertainty()` |
| Observed-grid simultaneous Gaussian FPCR slope bands | implemented | `fpca_regression_slope_simultaneous_band()` |
| Gaussian FPCR future-outcome prediction intervals | implemented | `fpca_regression_future_prediction_interval()` |
| Derived speed/acceleration/distance/path functions | implemented | kinematic helpers |

## Optional specialist interoperability

| Capability | Backend | Package role |
|---|---|---|
| B-spline/Fourier basis representation | scikit-fda | preserve eye-tracking provenance while delegating basis mathematics |
| Functional boxplot screening | scikit-fda | optional sensitivity/review diagnostic |
| Magnitude-shape outlier screening | scikit-fda | optional sensitivity/review diagnostic |
| Sparse covariance UFPCA + PACE scores | FDApy | preserve native irregular grids while delegating sparse estimation |
| Elastic SRVF trajectory alignment | fdasrsf | specialist phase/amplitude backend |

Optional backends are never imported until the corresponding feature is requested.

## Not silently approximated

The following are **not** replaced with convenient but scientifically weaker substitutes:

### Full functional mixed models

The multilevel implementation currently provides a transparent participant/trial functional decomposition followed by FPCA. It is not described as a full likelihood/Bayesian functional mixed-effects model.

### Confirmatory functional outlier tests

Review flags are descriptive diagnostics. The package does not turn them into automatic inferential exclusions.

### Full downstream uncertainty propagation beyond Gaussian FPCR

`bootstrap_fpca_regression_uncertainty()` now refits the common-grid Gaussian FPCR pipeline under paired resampling and propagates basis/regression sampling variability into the reconstructed slope and fitted conditional means.

Still not provided are full uncertainty procedures that jointly include target measurement error, latent-curve uncertainty, preprocessing uncertainty, data-driven component-selection uncertainty, sparse PACE score uncertainty, heteroscedastic future-response modelling, or non-Gaussian/binomial functional-regression inference.

## Research/development candidates

Future tranches may evaluate:

- conformal functional anomaly detection;
- richer multilevel functional mixed-effects backends.

A candidate enters the public API only when it can preserve the package rules: explicit estimand, deterministic behavior or seed, provenance, failure diagnostics, synthetic truth tests, documentation, and runnable examples.

## Development status

The current development line is **0.14.0.dev0**. The package remains pre-release while scientific contracts, optional-backend validation, documentation, and cross-platform qualification continue to mature.
