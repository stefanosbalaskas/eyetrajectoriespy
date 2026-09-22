import eyetrajectoriespy as et

def test_version_and_public_symbols():
    assert et.__version__=="0.17.0.dev0"
    required={
        "TrajectorySet","fit_fpca","fit_mfpca","fit_multilevel_fpca","fit_compositional_fpca","FPCAScoreUncertaintyResult","FPCASpectrumUncertaintyResult",
        "register_to_landmarks","fit_elastic_fpca","simulate_planar_trajectories",
        "fit_scalar_on_function_regression","plot_fpca_component",
        "IrregularTrajectorySet","from_irregular_long_dataframe_native","bootstrap_fpca_stability",
        "fit_phase_fpca","compare_registered_unregistered_fpca","to_skfda_basis",
        "split_conformal_fpca_anomaly","conformal_fpca_anomaly_frame","plot_conformal_fpca_anomaly","conformal_fpca_anomaly_reporting_text","diagnose_fpca_outliers","leave_one_group_out_fpca_influence",
        "ConformalFunctionalAnomalyResult","FunctionalOutlierResult","FPCAInfluenceResult","detect_functional_outliers_skfda",
        "plot_fpca_outlier_diagnostics","plot_fpca_influence",
        "FPCACrossValidationResult","FPCAComponentBandResult","FPCAComponentEnvelopeResult",
        "cross_validate_fpca_reconstruction","summarise_fpca_cross_validation",
        "select_fpca_components_cv","bootstrap_fpca_component_bands","fpca_component_band_frame","bootstrap_fpca_component_envelopes",
        "plot_fpca_cross_validation","plot_fpca_component_band","plot_fpca_component_envelope",
        "fpca_cross_validation_reporting_text","fpca_component_band_reporting_text","fpca_component_envelope_reporting_text",
        "FPCASubspaceComparisonResult","FPCASubspaceStabilityResult",
        "fpca_eigenvalue_gap_table","compare_fpca_subspaces",
        "bootstrap_fpca_subspace_stability","summarise_fpca_subspace_stability",
        "plot_fpca_subspace_stability","fpca_eigengap_reporting_text",
        "fpca_subspace_stability_reporting_text",
        "SparseFPCAResult","sparse_dimension_summary","to_fdapy_irregular",
        "fit_sparse_fpca_fdapy","sparse_fpca_score_frame",
        "sparse_fpca_reporting_text","plot_sparse_irregular_dimension",
        "FunctionalMeanBandResult","multiplier_functional_mean_band",
        "functional_mean_band_frame","plot_functional_mean_band",
        "functional_mean_band_reporting_text","bootstrap_fpca_score_uncertainty","fpca_score_uncertainty_frame","plot_fpca_score_uncertainty","fpca_score_uncertainty_reporting_text","bootstrap_fpca_spectrum_uncertainty","fpca_spectrum_uncertainty_frame","plot_fpca_spectrum_uncertainty","fpca_spectrum_uncertainty_reporting_text",
        "FPCARegressionCVResult","FPCARegressionPredictionIntervalResult","FPCARegressionSlopeBandResult","FPCARegressionUncertaintyResult","FPCAWildBootstrapProjectionResult","FPCAWildBootstrapTruncationScanResult","FPCAWildBootstrapTruncationSelectionResult","FPCANestedRegressionCVResult",
        "bootstrap_fpca_regression_uncertainty","wild_bootstrap_fpca_projection","scan_wild_bootstrap_fpca_truncations","select_fpca_wild_bootstrap_truncation","fpca_wild_bootstrap_truncation_scan_frame","fpca_wild_bootstrap_truncation_selection_frame","plot_fpca_wild_bootstrap_truncation_scan","fpca_wild_bootstrap_truncation_reporting_text","fpca_wild_bootstrap_projection_frame","plot_fpca_wild_bootstrap_projection","fpca_wild_bootstrap_projection_reporting_text","fpca_regression_future_prediction_interval","fpca_regression_future_prediction_frame","plot_fpca_regression_future_prediction_interval","fpca_regression_future_prediction_reporting_text","fpca_regression_slope_simultaneous_band","fpca_regression_slope_band_frame","plot_fpca_regression_slope_band","fpca_regression_slope_band_reporting_text","fpca_regression_slope_uncertainty_frame","fpca_regression_prediction_uncertainty_frame","plot_fpca_regression_slope_uncertainty","plot_fpca_regression_mean_prediction_uncertainty","fpca_regression_uncertainty_reporting_text","cross_validate_fpca_regression","summarise_fpca_regression_cv",
        "select_fpca_regression_components","nested_cross_validate_fpca_regression",
        "plot_fpca_regression_cv","plot_nested_fpca_regression_cv",
        "fpca_regression_cv_reporting_text","fpca_nested_regression_cv_reporting_text",
    }
    assert required <= set(et.__all__)
    for name in required:
        assert hasattr(et,name)
