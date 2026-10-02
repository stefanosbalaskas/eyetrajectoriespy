# Public API

For mathematical definitions of the main estimands, transformations, studentization rules, and calibration statistics, see the [function → equation index](function-equation-index.md) and [implementation-matched mathematical reference](../methods/mathematical-reference.md). For decision flow, use the [workflow atlas](../methods/workflow-atlas.md); for representative rendered outputs, see the [visual gallery](../methods/visual-gallery.md).


## Native functional simulation and recovery
::: eyetrajectoriespy.FunctionalSimulationResult
::: eyetrajectoriespy.FunctionalSimulationTruth
::: eyetrajectoriespy.FunctionalSimulationScenario
::: eyetrajectoriespy.FunctionalRecoveryMetric
::: eyetrajectoriespy.FunctionalRecoveryValue
::: eyetrajectoriespy.FunctionalRecoveryAssessment
::: eyetrajectoriespy.FunctionalRecoveryRecord
::: eyetrajectoriespy.FunctionalRecoveryResult
::: eyetrajectoriespy.simulate_functional_process
::: eyetrajectoriespy.simulate_functional_scenario
::: eyetrajectoriespy.expand_functional_simulation_scenarios
::: eyetrajectoriespy.run_functional_recovery_scenarios
::: eyetrajectoriespy.functional_simulation_scenario_frame
::: eyetrajectoriespy.functional_recovery_frame
::: eyetrajectoriespy.functional_recovery_failure_frame
::: eyetrajectoriespy.functional_recovery_summary_frame
::: eyetrajectoriespy.functional_recovery_metric_catalog
::: eyetrajectoriespy.functional_recovery_metric_catalog_frame
::: eyetrajectoriespy.functional_recovery_assessment_frame
::: eyetrajectoriespy.evaluate_fpca_recovery
::: eyetrajectoriespy.evaluate_sparse_fpca_recovery
::: eyetrajectoriespy.evaluate_sparse_mfpca_recovery
::: eyetrajectoriespy.evaluate_functional_mixed_effects_recovery
::: eyetrajectoriespy.evaluate_registration_recovery
::: eyetrajectoriespy.evaluate_hierarchy_truth_recovery
::: eyetrajectoriespy.functional_recovery_qualification_scenarios
::: eyetrajectoriespy.functional_recovery_stress_scenarios
::: eyetrajectoriespy.functional_recovery_scenario_catalog_frame
::: eyetrajectoriespy.functional_recovery_reporting_text
::: eyetrajectoriespy.plot_functional_recovery_summary
::: eyetrajectoriespy.functional_simulation_truth_frame
::: eyetrajectoriespy.functional_simulation_reporting_text
::: eyetrajectoriespy.plot_functional_simulation_curve
::: eyetrajectoriespy.plot_functional_simulation_phase_warps
::: eyetrajectoriespy.plot_functional_simulation_score_variances


## Multivariate surrogate testing
::: eyetrajectoriespy.MultivariateIAAFTResult
::: eyetrajectoriespy.MultivariateSurrogateNonlinearityResult
::: eyetrajectoriespy.generate_multivariate_iaaft_surrogates
::: eyetrajectoriespy.multivariate_iaaft_diagnostics_frame
::: eyetrajectoriespy.multivariate_surrogate_nonlinearity_test
::: eyetrajectoriespy.plot_multivariate_iaaft_diagnostics
::: eyetrajectoriespy.plot_multivariate_surrogate_nonlinearity
::: eyetrajectoriespy.multivariate_iaaft_reporting_text
::: eyetrajectoriespy.multivariate_surrogate_nonlinearity_reporting_text

## Recurrence networks
::: eyetrajectoriespy.RecurrenceNetworkResult
::: eyetrajectoriespy.recurrence_network
::: eyetrajectoriespy.recurrence_network_node_frame
::: eyetrajectoriespy.recurrence_network_summary_frame
::: eyetrajectoriespy.plot_recurrence_network_degree
::: eyetrajectoriespy.recurrence_network_reporting_text

## Joint recurrence analysis
::: eyetrajectoriespy.JointRecurrenceResult
::: eyetrajectoriespy.joint_recurrence_matrix
::: eyetrajectoriespy.joint_recurrence_component_frame
::: eyetrajectoriespy.joint_rqa_metrics
::: eyetrajectoriespy.plot_joint_recurrence
::: eyetrajectoriespy.joint_recurrence_reporting_text

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

## Reproducibility and portable results
::: eyetrajectoriespy.PortableScientificResultSnapshot
::: eyetrajectoriespy.capture_environment
::: eyetrajectoriespy.export_portable_result
::: eyetrajectoriespy.load_portable_result

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
::: eyetrajectoriespy.SparseMFPCAResult
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

## Sparse irregular FPCA / PACE
::: eyetrajectoriespy.sparse_dimension_summary
::: eyetrajectoriespy.fit_sparse_fpca
::: eyetrajectoriespy.to_fdapy_irregular
::: eyetrajectoriespy.fit_sparse_fpca_fdapy
::: eyetrajectoriespy.sparse_fpca_score_frame
::: eyetrajectoriespy.plot_sparse_irregular_dimension
::: eyetrajectoriespy.plot_sparse_fpca_component
::: eyetrajectoriespy.plot_sparse_fpca_covariance
::: eyetrajectoriespy.plot_sparse_fpca_score_diagnostics
::: eyetrajectoriespy.sparse_fpca_reporting_text

## Sparse multivariate FPCA / joint PACE
::: eyetrajectoriespy.fit_sparse_mfpca
::: eyetrajectoriespy.sparse_mfpca_score_frame
::: eyetrajectoriespy.sparse_mfpca_reporting_text
::: eyetrajectoriespy.plot_sparse_mfpca_component
::: eyetrajectoriespy.plot_sparse_mfpca_covariance_blocks
::: eyetrajectoriespy.plot_sparse_mfpca_cross_covariance
::: eyetrajectoriespy.plot_sparse_mfpca_score_diagnostics

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
::: eyetrajectoriespy.FP... (truncated)