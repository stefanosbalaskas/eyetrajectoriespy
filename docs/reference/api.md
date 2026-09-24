# Public API

For mathematical definitions of the main estimands, transformations, studentization rules, and calibration statistics, see the [function → equation index](function-equation-index.md) and [implementation-matched mathematical reference](../methods/mathematical-reference.md). For decision flow, use the [workflow atlas](../methods/workflow-atlas.md); for representative rendered outputs, see the [visual gallery](../methods/visual-gallery.md).


## Nonlinear trajectory dynamics

### Delay reconstruction and embedding diagnostics
::: eyetrajectoriespy.DelayEmbeddingResult
::: eyetrajectoriespy.EmbeddingDelayDiagnosticResult
::: eyetrajectoriespy.EmbeddingDimensionDiagnosticResult
::: eyetrajectoriespy.delay_embed_trajectory
::: eyetrajectoriespy.embedding_delay_diagnostics
::: eyetrajectoriespy.embedding_dimension_diagnostics
::: eyetrajectoriespy.plot_embedding_delay_diagnostics
::: eyetrajectoriespy.plot_embedding_dimension_diagnostics

### Sparse recurrence and RQA
::: eyetrajectoriespy.RecurrenceResult
::: eyetrajectoriespy.RecurrenceRadiusProfileResult
::: eyetrajectoriespy.RQAResult
::: eyetrajectoriespy.WindowedRQAResult
::: eyetrajectoriespy.WindowedRQAFunctionalResult
::: eyetrajectoriespy.WindowedRQASensitivityResult
::: eyetrajectoriespy.WindowedRQAMeanBandResult
::: eyetrajectoriespy.recurrence_matrix
::: eyetrajectoriespy.recurrence_radius_profile
::: eyetrajectoriespy.rqa_metrics
::: eyetrajectoriespy.windowed_rqa
::: eyetrajectoriespy.windowed_rqa_trajectory_set
::: eyetrajectoriespy.windowed_rqa_sensitivity
::: eyetrajectoriespy.windowed_rqa_functional_mean_band
::: eyetrajectoriespy.cross_recurrence_matrix
::: eyetrajectoriespy.cross_rqa_metrics
::: eyetrajectoriespy.plot_recurrence
::: eyetrajectoriespy.plot_recurrence_rate_curve
::: eyetrajectoriespy.plot_windowed_rqa
::: eyetrajectoriespy.plot_windowed_rqa_trajectories
::: eyetrajectoriespy.plot_windowed_rqa_sensitivity

### Population uncertainty for RQA summaries
::: eyetrajectoriespy.RQAMeanBootstrapResult
::: eyetrajectoriespy.bootstrap_rqa_metric_means
::: eyetrajectoriespy.plot_rqa_metric_mean_bootstrap

### Declared nonlinear parameter sensitivity
::: eyetrajectoriespy.RQAParameterSensitivityResult
::: eyetrajectoriespy.LyapunovParameterSensitivityResult
::: eyetrajectoriespy.KantzParameterSensitivityResult
::: eyetrajectoriespy.rqa_parameter_sensitivity
::: eyetrajectoriespy.lyapunov_parameter_sensitivity
::: eyetrajectoriespy.kantz_parameter_sensitivity
::: eyetrajectoriespy.plot_rqa_sensitivity
::: eyetrajectoriespy.plot_lyapunov_sensitivity
::: eyetrajectoriespy.plot_kantz_sensitivity

### Local divergence and surrogate testing
::: eyetrajectoriespy.LocalDivergenceResult
::: eyetrajectoriespy.KantzDivergenceResult
::: eyetrajectoriespy.LargestLyapunovResult
::: eyetrajectoriespy.SurrogateNonlinearityResult
::: eyetrajectoriespy.local_divergence_curve
::: eyetrajectoriespy.kantz_divergence_curve
::: eyetrajectoriespy.estimate_largest_lyapunov_rosenstein
::: eyetrajectoriespy.estimate_largest_lyapunov_kantz
::: eyetrajectoriespy.surrogate_nonlinearity_test
::: eyetrajectoriespy.plot_local_divergence
::: eyetrajectoriespy.plot_surrogate_nonlinearity

### Nonlinear reporting helpers
::: eyetrajectoriespy.recurrence_radius_profile_reporting_text
::: eyetrajectoriespy.rqa_metric_mean_bootstrap_reporting_text
::: eyetrajectoriespy.rqa_reporting_text
::: eyetrajectoriespy.rqa_parameter_sensitivity_reporting_text
::: eyetrajectoriespy.windowed_rqa_reporting_text
::: eyetrajectoriespy.windowed_rqa_functional_reporting_text
::: eyetrajectoriespy.windowed_rqa_sensitivity_reporting_text
::: eyetrajectoriespy.windowed_rqa_mean_band_reporting_text
::: eyetrajectoriespy.kantz_parameter_sensitivity_reporting_text
::: eyetrajectoriespy.largest_lyapunov_reporting_text
::: eyetrajectoriespy.lyapunov_parameter_sensitivity_reporting_text
::: eyetrajectoriespy.surrogate_nonlinearity_reporting_text
::: eyetrajectoriespy.return_map_stability_reporting_text

### Experimental empirical return maps
::: eyetrajectoriespy.PoincareCrossingResult
::: eyetrajectoriespy.LocalReturnMapResult
::: eyetrajectoriespy.ReturnMapStabilityResult
::: eyetrajectoriespy.poincare_crossings
::: eyetrajectoriespy.fit_local_return_map
::: eyetrajectoriespy.return_map_stability
::: eyetrajectoriespy.plot_poincare_return_map

## Mathematical contracts
::: eyetrajectoriespy.MathematicalContract
::: eyetrajectoriespy.list_mathematical_contracts
::: eyetrajectoriespy.get_mathematical_contract
::: eyetrajectoriespy.mathematical_contract_frame

## Core objects
::: eyetrajectoriespy.TrajectorySet
::: eyetrajectoriespy.DiscreteFrechetResult
::: eyetrajectoriespy.FPCAResult
::: eyetrajectoriespy.RegistrationResult
::: eyetrajectoriespy.CompositionalFPCAResult
::: eyetrajectoriespy.MultilevelFPCAResult
::: eyetrajectoriespy.FPCAStabilityResult
::: eyetrajectoriespy.FPCACrossValidationResult
::: eyetrajectoriespy.FPCAComponentEnvelopeResult
::: eyetrajectoriespy.FPCARegressionCVResult
::: eyetrajectoriespy.FPCANestedRegressionCVResult
::: eyetrajectoriespy.FPCASubspaceComparisonResult
::: eyetrajectoriespy.FPCASubspaceStabilityResult
::: eyetrajectoriespy.SparseFPCAResult
::: eyetrajectoriespy.FunctionalMeanBandResult
::: eyetrajectoriespy.FPCAInfluenceResult
::: eyetrajectoriespy.FunctionalOutlierResult

## Native and common-grid import
::: eyetrajectoriespy.from_irregular_long_dataframe_native
::: eyetrajectoriespy.irregular_sampling_summary
::: eyetrajectoriespy.common_overlap_interval
::: eyetrajectoriespy.make_common_grid
::: eyetrajectoriespy.resample_irregular_to_grid
::: eyetrajectoriespy.resample_irregular_to_common_grid

## Import and validation
::: eyetrajectoriespy.from_long_dataframe
::: eyetrajectoriespy.from_irregular_long_dataframe
::: eyetrajectoriespy.validate_trajectory_set
::: eyetrajectoriespy.validate_simplex

## Preprocessing
::: eyetrajectoriespy.resample_to_grid
::: eyetrajectoriespy.interpolate_short_gaps
::: eyetrajectoriespy.smooth_trajectories
::: eyetrajectoriespy.normalize_time
::: eyetrajectoriespy.normalize_coordinates
::: eyetrajectoriespy.center_on_landmark

## Sparse irregular PACE FPCA
::: eyetrajectoriespy.sparse_dimension_summary
::: eyetrajectoriespy.to_fdapy_irregular
::: eyetrajectoriespy.fit_sparse_fpca_fdapy
::: eyetrajectoriespy.sparse_fpca_score_frame
::: eyetrajectoriespy.plot_sparse_irregular_dimension
::: eyetrajectoriespy.sparse_fpca_reporting_text

## Functional mean inference
::: eyetrajectoriespy.multiplier_functional_mean_band
::: eyetrajectoriespy.functional_mean_band_frame
::: eyetrajectoriespy.plot_functional_mean_band
::: eyetrajectoriespy.functional_mean_band_reporting_text

## FPCA / MFPCA
::: eyetrajectoriespy.fit_fpca
::: eyetrajectoriespy.fit_mfpca
::: eyetrajectoriespy.transform_fpca
::: eyetrajectoriespy.reconstruct_fpca
::: eyetrajectoriespy.component_trajectories
::: eyetrajectoriespy.fpca_score_frame

## FPCA component selection
::: eyetrajectoriespy.cross_validate_fpca_reconstruction
::: eyetrajectoriespy.summarise_fpca_cross_validation
::: eyetrajectoriespy.select_fpca_components_cv
::: eyetrajectoriespy.plot_fpca_cross_validation
::: eyetrajectoriespy.fpca_cross_validation_reporting_text

## Stabilized-volatility FPCR wild-bootstrap truncation selection
::: eyetrajectoriespy.FPCAWildBootstrapTruncationScanResult
::: eyetrajectoriespy.FPCAWildBootstrapTruncationSelectionResult
::: eyetrajectoriespy.scan_wild_bootstrap_fpca_truncations
::: eyetrajectoriespy.select_fpca_wild_bootstrap_truncation
::: eyetrajectoriespy.fpca_wild_bootstrap_truncation_scan_frame
::: eyetrajectoriespy.fpca_wild_bootstrap_truncation_selection_frame
::: eyetrajectoriespy.plot_fpca_wild_bootstrap_truncation_scan
::: eyetrajectoriespy.fpca_wild_bootstrap_truncation_reporting_text

## Heteroscedastic Gaussian FPCR wild-bootstrap projection inference
::: eyetrajectoriespy.FPCAWildBootstrapProjectionResult
::: eyetrajectoriespy.wild_bootstrap_fpca_projection
::: eyetrajectoriespy.fpca_wild_bootstrap_projection_frame
::: eyetrajectoriespy.plot_fpca_wild_bootstrap_projection
::: eyetrajectoriespy.fpca_wild_bootstrap_projection_reporting_text

## Simultaneous fixed-target Gaussian FPCR wild-bootstrap inference
::: eyetrajectoriespy.FPCAWildBootstrapSimultaneousResult
::: eyetrajectoriespy.fpca_wild_bootstrap_projection_simultaneous_interval
::: eyetrajectoriespy.fpca_wild_bootstrap_simultaneous_frame
::: eyetrajectoriespy.plot_fpca_wild_bootstrap_simultaneous_interval
::: eyetrajectoriespy.fpca_wild_bootstrap_simultaneous_reporting_text

## Fixed-family Gaussian FPCR wild-bootstrap hypothesis tests
::: eyetrajectoriespy.FPCAWildBootstrapFamilyTestResult
::: eyetrajectoriespy.fpca_wild_bootstrap_projection_family_test
::: eyetrajectoriespy.fpca_wild_bootstrap_family_test_frame
::: eyetrajectoriespy.plot_fpca_wild_bootstrap_family_test
::: eyetrajectoriespy.fpca_wild_bootstrap_family_test_reporting_text

## Wild-bootstrap finite Monte Carlo precision diagnostics
::: eyetrajectoriespy.FPCAWildBootstrapMonteCarloDiagnosticResult
::: eyetrajectoriespy.fpca_wild_bootstrap_family_test_monte_carlo_diagnostics
::: eyetrajectoriespy.fpca_wild_bootstrap_monte_carlo_diagnostic_frame
::: eyetrajectoriespy.plot_fpca_wild_bootstrap_monte_carlo_diagnostics
::: eyetrajectoriespy.fpca_wild_bootstrap_monte_carlo_reporting_text

## Gaussian FPCR future-outcome prediction
::: eyetrajectoriespy.FPCARegressionPredictionIntervalResult
::: eyetrajectoriespy.fpca_regression_future_prediction_interval
::: eyetrajectoriespy.fpca_regression_future_prediction_frame
::: eyetrajectoriespy.plot_fpca_regression_future_prediction_interval
::: eyetrajectoriespy.fpca_regression_future_prediction_reporting_text

## Gaussian FPCR simultaneous slope band
::: eyetrajectoriespy.FPCARegressionSlopeBandResult
::: eyetrajectoriespy.fpca_regression_slope_simultaneous_band
::: eyetrajectoriespy.fpca_regression_slope_band_frame
::: eyetrajectoriespy.plot_fpca_regression_slope_band
::: eyetrajectoriespy.fpca_regression_slope_band_reporting_text

## Gaussian FPCR bootstrap uncertainty
::: eyetrajectoriespy.FPCARegressionUncertaintyResult
::: eyetrajectoriespy.bootstrap_fpca_regression_uncertainty
::: eyetrajectoriespy.fpca_regression_slope_uncertainty_frame
::: eyetrajectoriespy.fpca_regression_prediction_uncertainty_frame
::: eyetrajectoriespy.plot_fpca_regression_slope_uncertainty
::: eyetrajectoriespy.plot_fpca_regression_mean_prediction_uncertainty
::: eyetrajectoriespy.fpca_regression_uncertainty_reporting_text

## Predictive FPCA regression selection
::: eyetrajectoriespy.cross_validate_fpca_regression
::: eyetrajectoriespy.summarise_fpca_regression_cv
::: eyetrajectoriespy.select_fpca_regression_components
::: eyetrajectoriespy.nested_cross_validate_fpca_regression
::: eyetrajectoriespy.plot_fpca_regression_cv
::: eyetrajectoriespy.plot_nested_fpca_regression_cv
::: eyetrajectoriespy.fpca_regression_cv_reporting_text
::: eyetrajectoriespy.fpca_nested_regression_cv_reporting_text

## FPC shape uncertainty
::: eyetrajectoriespy.FPCAComponentBandResult
::: eyetrajectoriespy.bootstrap_fpca_component_bands
::: eyetrajectoriespy.fpca_component_band_frame
::: eyetrajectoriespy.plot_fpca_component_band
::: eyetrajectoriespy.fpca_component_band_reporting_text
::: eyetrajectoriespy.bootstrap_fpca_component_envelopes
::: eyetrajectoriespy.plot_fpca_component_envelope
::: eyetrajectoriespy.fpca_component_envelope_reporting_text

## FPC score basis uncertainty
::: eyetrajectoriespy.FPCAScoreUncertaintyResult
::: eyetrajectoriespy.bootstrap_fpca_score_uncertainty
::: eyetrajectoriespy.fpca_score_uncertainty_frame
::: eyetrajectoriespy.plot_fpca_score_uncertainty
::: eyetrajectoriespy.fpca_score_uncertainty_reporting_text

## FPCA spectrum uncertainty
::: eyetrajectoriespy.FPCASpectrumUncertaintyResult
::: eyetrajectoriespy.bootstrap_fpca_spectrum_uncertainty
::: eyetrajectoriespy.fpca_spectrum_uncertainty_frame
::: eyetrajectoriespy.plot_fpca_spectrum_uncertainty
::: eyetrajectoriespy.fpca_spectrum_uncertainty_reporting_text

## Near-tied eigenvalues and eigenspaces
::: eyetrajectoriespy.fpca_eigenvalue_gap_table
::: eyetrajectoriespy.compare_fpca_subspaces
::: eyetrajectoriespy.bootstrap_fpca_subspace_stability
::: eyetrajectoriespy.summarise_fpca_subspace_stability
::: eyetrajectoriespy.plot_fpca_subspace_stability
::: eyetrajectoriespy.fpca_eigengap_reporting_text
::: eyetrajectoriespy.fpca_subspace_stability_reporting_text

## Split-conformal FPCA anomaly review
::: eyetrajectoriespy.ConformalFunctionalAnomalyResult
::: eyetrajectoriespy.split_conformal_fpca_anomaly
::: eyetrajectoriespy.conformal_fpca_anomaly_frame
::: eyetrajectoriespy.plot_conformal_fpca_anomaly
::: eyetrajectoriespy.conformal_fpca_anomaly_reporting_text

## Functional outliers and influence
::: eyetrajectoriespy.diagnose_fpca_outliers
::: eyetrajectoriespy.leave_one_group_out_fpca_influence
::: eyetrajectoriespy.detect_functional_outliers_skfda
::: eyetrajectoriespy.plot_fpca_outlier_diagnostics
::: eyetrajectoriespy.plot_fpca_influence
::: eyetrajectoriespy.fpca_outlier_reporting_text
::: eyetrajectoriespy.fpca_influence_reporting_text

## FPCA stability and reconstruction
::: eyetrajectoriespy.component_similarity_matrix
::: eyetrajectoriespy.match_fpca_components
::: eyetrajectoriespy.bootstrap_fpca_stability
::: eyetrajectoriespy.summarise_fpca_stability
::: eyetrajectoriespy.reconstruction_error_by_curve
::: eyetrajectoriespy.fpca_reconstruction_curve

## Registration and phase
::: eyetrajectoriespy.register_to_landmarks
::: eyetrajectoriespy.warping_displacement
::: eyetrajectoriespy.phase_summary
::: eyetrajectoriespy.phase_trajectory_set
::: eyetrajectoriespy.fit_phase_fpca
::: eyetrajectoriespy.phase_landmark_frame
::: eyetrajectoriespy.compare_registered_unregistered_fpca
::: eyetrajectoriespy.registration_sensitivity_frame

## Multilevel and compositional
::: eyetrajectoriespy.fit_multilevel_fpca
::: eyetrajectoriespy.fit_compositional_fpca
::: eyetrajectoriespy.reconstruct_compositional_fpca

## Derived functions
::: eyetrajectoriespy.speed_function
::: eyetrajectoriespy.acceleration_magnitude_function
::: eyetrajectoriespy.distance_to_landmark_function
::: eyetrajectoriespy.cumulative_path_length
::: eyetrajectoriespy.heading_function
::: eyetrajectoriespy.signed_curvature_function
::: eyetrajectoriespy.turning_rate_function
::: eyetrajectoriespy.trajectory_tortuosity

## Function-on-scalar regression
::: eyetrajectoriespy.FunctionOnScalarResult
::: eyetrajectoriespy.FunctionOnScalarBootstrapResult
::: eyetrajectoriespy.FunctionOnScalarBandResult
::: eyetrajectoriespy.fit_function_on_scalar_regression
::: eyetrajectoriespy.bootstrap_function_on_scalar_coefficients
::: eyetrajectoriespy.function_on_scalar_simultaneous_bands
::: eyetrajectoriespy.function_on_scalar_coefficient_frame
::: eyetrajectoriespy.plot_function_on_scalar_coefficients
::: eyetrajectoriespy.function_on_scalar_reporting_text

## Downstream analysis
::: eyetrajectoriespy.functional_l2_distance
::: eyetrajectoriespy.pairwise_functional_distances
::: eyetrajectoriespy.discrete_frechet_distance
::: eyetrajectoriespy.pairwise_discrete_frechet_distances
::: eyetrajectoriespy.dynamic_time_warping_distance
::: eyetrajectoriespy.pairwise_dynamic_time_warping_distances
::: eyetrajectoriespy.cluster_fpca_scores
::: eyetrajectoriespy.fit_scalar_on_function_regression

## Plotting and reporting
::: eyetrajectoriespy.plot_planar_trajectories
::: eyetrajectoriespy.plot_dynamic_time_warping_alignment
::: eyetrajectoriespy.plot_fpca_component
::: eyetrajectoriespy.plot_warping_functions
::: eyetrajectoriespy.plot_fpca_stability
::: eyetrajectoriespy.plot_reconstruction_curve
::: eyetrajectoriespy.dynamic_time_warping_reporting_text
::: eyetrajectoriespy.fpca_stability_reporting_text
::: eyetrajectoriespy.registration_sensitivity_reporting_text
::: eyetrajectoriespy.summarise_fpca
::: eyetrajectoriespy.fpca_reporting_text

## Optional interoperability
::: eyetrajectoriespy.to_skfda_grid
::: eyetrajectoriespy.to_skfda_basis
::: eyetrajectoriespy.fit_elastic_fpca
