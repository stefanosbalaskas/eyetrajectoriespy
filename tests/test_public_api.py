import eyetrajectoriespy as et

def test_version_and_public_symbols():
    assert et.__version__=="0.5.0.dev0"
    required={
        "TrajectorySet","fit_fpca","fit_mfpca","fit_multilevel_fpca","fit_compositional_fpca",
        "register_to_landmarks","fit_elastic_fpca","simulate_planar_trajectories",
        "fit_scalar_on_function_regression","plot_fpca_component",
        "IrregularTrajectorySet","from_irregular_long_dataframe_native","bootstrap_fpca_stability",
        "fit_phase_fpca","compare_registered_unregistered_fpca","to_skfda_basis",
        "diagnose_fpca_outliers","leave_one_group_out_fpca_influence",
        "FunctionalOutlierResult","FPCAInfluenceResult","detect_functional_outliers_skfda",
        "plot_fpca_outlier_diagnostics","plot_fpca_influence",
        "FPCACrossValidationResult","FPCAComponentEnvelopeResult",
        "cross_validate_fpca_reconstruction","summarise_fpca_cross_validation",
        "select_fpca_components_cv","bootstrap_fpca_component_envelopes",
        "plot_fpca_cross_validation","plot_fpca_component_envelope",
        "fpca_cross_validation_reporting_text","fpca_component_envelope_reporting_text",
        "FPCASubspaceComparisonResult","FPCASubspaceStabilityResult",
        "fpca_eigenvalue_gap_table","compare_fpca_subspaces",
        "bootstrap_fpca_subspace_stability","summarise_fpca_subspace_stability",
        "plot_fpca_subspace_stability","fpca_eigengap_reporting_text",
        "fpca_subspace_stability_reporting_text",
    }
    assert required <= set(et.__all__)
    for name in required:
        assert hasattr(et,name)
