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
| Split-conformal new-trajectory anomaly review | implemented | `split_conformal_fpca_anomaly()` |
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
| Heteroscedastic Gaussian FPCR centered-projection intervals | implemented | `wild_bootstrap_fpca_projection()` |
| Familywise simultaneous fixed-target FPCR wild-bootstrap intervals | implemented | `fpca_wild_bootstrap_projection_simultaneous_interval()` |
| Fixed-family FPCR wild-bootstrap hypothesis tests | implemented | `fpca_wild_bootstrap_projection_family_test()` |
| Finite-bootstrap Monte Carlo precision diagnostics | implemented | `fpca_wild_bootstrap_family_test_monte_carlo_diagnostics()` |
| Stabilized-volatility wild-bootstrap h selection | implemented | `scan_wild_bootstrap_fpca_truncations()` / `select_fpca_wild_bootstrap_truncation()` |
| Derived speed/acceleration/distance/path functions | implemented | kinematic helpers |
| Delay-coordinate state reconstruction | implemented | `delay_embed_trajectory()` |
| AMI / false-nearest-neighbor diagnostics | implemented, diagnostic-only | `embedding_delay_diagnostics()` / `embedding_dimension_diagnostics()` |
| Sparse recurrence / RQA | implemented | `recurrence_matrix()` / `rqa_metrics()` |
| Windowed and cross recurrence | implemented | `windowed_rqa()` / `cross_recurrence_matrix()` |
| RQA-derived functional trajectories | implemented; descriptive functional bridge | `windowed_rqa_trajectory_set()` |
| Rosenstein local divergence / LLE | implemented with explicit fit interval | `local_divergence_curve()` / `estimate_largest_lyapunov_rosenstein()` |
| IAAFT surrogate nonlinearity test | implemented | `surrogate_nonlinearity_test()` |
| Empirical Poincare return-map stability | experimental | `poincare_crossings()` / `fit_local_return_map()` / `return_map_stability()` |

## Documentation and mathematical contracts

Versions 0.21–0.24 treat documentation and mathematical metadata as tested package surfaces:

- the repository-level `MATHEMATICAL_CONTRACTS.md` renders the core equations directly on GitHub;
- the site mathematical reference maps those equations to the exact public APIs and scope boundaries;
- a deterministic SVG gallery is generated from seeded synthetic data and the real plotting functions;
- documentation CI regenerates gallery assets and validates navigation, mathematical API mappings, MathJax wiring, and documented public exports before the strict MkDocs build;
- the Material-for-MkDocs line is intentionally constrained to compatible 9.x releases with MkDocs <2 for this tranche.
- version 0.22 adds a public machine-readable mathematical-contract registry plus deterministic GitHub/site function → equation indexes;
- the same tranche adds a rendered workflow atlas and expands the deterministic SVG gallery to eight figures;
- CI checks that generated equation indexes still match the package registry before the strict site build.

A future documentation-platform migration can be evaluated independently of the scientific API. No site-framework migration is allowed to alter numerical or scientific contracts.

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

Still not provided are full uncertainty procedures that jointly include target measurement error, latent-curve uncertainty, preprocessing uncertainty, data-driven component-selection uncertainty, sparse PACE score uncertainty, clustered/repeated-participant wild-bootstrap inference, coverage-optimal automatic wild-bootstrap truncation tuning, heteroscedastic future-outcome prediction, or non-Gaussian/binomial functional-regression inference.

## Research/development candidates

Future tranches may evaluate:

- richer multilevel functional mixed-effects backends;
- explicit system-identification models for gaze dynamics;
- model-based continuation / Floquet analysis only after a validated dynamical-system contract exists.

Classical `floquet_multipliers(gaze)`, monodromy matrices from raw observations, and `detect_bifurcation(gaze)` remain intentionally **not** implemented in 0.24.

A candidate enters the public API only when it can preserve the package rules: explicit estimand, deterministic behavior or seed, provenance, failure diagnostics, synthetic truth tests, documentation, and runnable examples.

## Development status

The current development line is **0.24.0.dev0**. The package remains pre-release while scientific contracts, optional-backend validation, documentation, and cross-platform qualification continue to mature.
