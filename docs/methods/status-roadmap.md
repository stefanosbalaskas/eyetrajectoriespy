# Capability status and roadmap

## 0.12 final-promotion checkpoint

The current development line is **0.12.0**.

The sparse-MFPCA/joint-PACE methodology surface is frozen. Production-installed `0.12.0rc1` observation is complete, so the next release step is literal final `0.12.0` exact-version qualification. This checkpoint adds no methodology and does not reopen tuning, estimator, or API decisions.


eyetrajectoriespy is intentionally an **eye-tracking functional-analysis layer**, not a reimplementation of every general FDA estimator.

This page distinguishes implemented scientific contracts from optional interoperability and future work.

## Implemented in the core

| Capability | Status | Primary API |
|---|---|---|
| Common-grid functional gaze objects | implemented | `TrajectorySet` |
| Native curve-specific time grids | implemented | `IrregularTrajectorySet` |
| Sparse univariate covariance FPCA + PACE scores | implemented and qualified natively in 0.10; FDApy retained as compatibility/reference backend | `fit_sparse_fpca()`; optional `fit_sparse_fpca_fdapy()` |
| Simultaneous functional mean band | implemented | `multiplier_functional_mean_band()` |
| Function-on-scalar regression | implemented; observed-grid OLS with explicit design and HC1 standard errors | `fit_function_on_scalar_regression()` |
| Function-on-scalar simultaneous coefficient bands | implemented; fixed-design wild bootstrap with coefficient/family scope | `function_on_scalar_simultaneous_bands()` |
| Generalized function-on-scalar regression | implemented; Bernoulli/logit and Poisson/log marginal GEE with participant clusters, explicit B-spline coefficient functions, robust sandwich covariance, participant bootstrap simultaneous bands, optional explicit strictly-positive Poisson exposure, and no automatic working-correlation selection | `fit_generalized_function_on_scalar_regression()` / `generalized_function_on_scalar_simultaneous_bands()` |
| Generalized FoSR fixed-profile prediction | implemented; fixed marginal profiles, extrapolation audit, explicit Poisson rate versus expected-count prediction, participant-bootstrap simultaneous bands, one predeclared probability/rate/count contrast scale, and no automatic target/contrast selection | `generalized_function_on_scalar_predict()` / `generalized_function_on_scalar_prediction_bands()` |
| Functional mixed-effects regression | implemented; one Gaussian response dimension, B-spline fixed effects, participant functional random intercept, optional one guarded participant random functional slope, joint MixedLM fit | `fit_functional_mixed_effects_regression()` |
| Functional mixed-effects simultaneous coefficient bands | implemented; whole-participant case bootstrap, fixed-covariance GLS coefficient refits, coefficient/family observed-grid maxima | `bootstrap_functional_mixed_effects_coefficients()` / `functional_mixed_effects_simultaneous_bands()` |
| Full-refit participant bootstrap | implemented; unique bootstrap group IDs for duplicate participant draws, complete MixedLM refit under fixed declared specification, retained variance-component distributions | `bootstrap_functional_mixed_effects_full_refit()` |
| Participant random functional slope | implemented; one declared predictor, shared random basis size, full unstructured intercept/slope covariance, strict within-participant variation and covariance-complexity guards | `fit_functional_mixed_effects_regression(..., random_slope_predictor=...)` |
| Mixed-effects residual / within-trial dependence diagnostics | implemented; explicit trial ACF/autocovariance, empirical semivariance, exact physical-lag pair audit, participant/overall stratification, and descriptive fit-vs-fit comparison | `functional_mixed_effects_residual_diagnostics()` |
| Trial-level functional random effect | implemented; explicit nested trial identifier, one shared unstructured trial-basis covariance, profiled Gaussian marginal likelihood, separate trial BLUPs/covariance diagnostics, participant-level bootstrap propagation | `fit_functional_mixed_effects_regression(..., trial_random_effect="functional_intercept")` / `functional_trial_random_effect_frame()` |
| Explicit mixed-effects residual covariance + whitening | implemented; physical-time exponential correlation on irregular common grids, signed index-step AR(1) on verified regular grids, block-diagonal trial residual covariance, jointly estimated serial parameter, raw/whitened diagnostics and bootstrap propagation | `fit_functional_mixed_effects_regression(..., residual_correlation=...)` / `functional_mixed_effects_whitened_residuals()` |
| Mixed-effects covariance-structure sensitivity | implemented; predeclared already fitted structures, explicit reference, strict comparability, retained failures, coefficient/band/variance/residual/IC diagnostics, no ranking or automatic winner | `functional_mixed_effects_covariance_sensitivity()` / `functional_mixed_effects_variance_decomposition()` |
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
| Discrete Fréchet trajectory distance | implemented; monotone order-preserving coupling, no elapsed-time correspondence | `discrete_frechet_distance()` / `pairwise_discrete_frechet_distances()` |
| Dynamic time warping trajectory distance | implemented; backward-compatible symmetric1 raw cost plus explicit normalizable symmetric2/N+M option and Sakoe-Chiba sample-index band | `dynamic_time_warping_distance()` / `pairwise_dynamic_time_warping_distances()` |
| Trajectory-distance sensitivity | implemented; native-scale L2/Fréchet/DTW matrices, descriptive rank/neighbor agreement, cutoff-tie diagnostics, no automatic winner | `trajectory_distance_sensitivity()` |
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
| Continuous planar trajectory geometry | implemented; wrapped heading, signed curvature, turning rate, explicit tortuosity | `heading_function()` / `signed_curvature_function()` / `turning_rate_function()` / `trajectory_tortuosity()` |
| Delay-coordinate state reconstruction | implemented | `delay_embed_trajectory()` |
| AMI / false-nearest-neighbor diagnostics | implemented, diagnostic-only | `embedding_delay_diagnostics()` / `embedding_dimension_diagnostics()` |
| Sparse recurrence / RQA | implemented | `recurrence_matrix()` / `rqa_metrics()` |
| Recurrence radius / pair-distance profile | implemented; exact declared grid, no automatic threshold selector | `recurrence_radius_profile()` |
| Population mean RQA bootstrap | implemented; curve/participant units, fixed specification, percentile intervals | `bootstrap_rqa_metric_means()` |
| Reconstructed-state RQA parameter sensitivity | implemented; descriptive multiverse, no automatic selector | `rqa_parameter_sensitivity()` |
| Windowed and cross recurrence | implemented | `windowed_rqa()` / `cross_recurrence_matrix()` |
| Synchronized joint recurrence / JRQA | implemented; exact common grid, shared Theiler, independently declared component thresholds, sparse logical intersection | `joint_recurrence_matrix()` / `joint_rqa_metrics()` |
