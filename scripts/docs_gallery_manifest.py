"""Machine-readable deterministic documentation-gallery contract.

Every public ``plot_*`` export in eyetrajectoriespy must have exactly one entry.
The manifest is intentionally metadata-only: generation lives in
``generate_docs_gallery.py`` / ``generate_docs_gallery_extra.py``.
"""

from __future__ import annotations


GALLERY_PLOTS: dict[str, dict[str, str]] = {
    # Core trajectories, geometry, registration.
    "plot_planar_trajectories": {"asset": "planar-trajectories.svg", "category": "geometry-registration", "quantity": "Planar trajectory overlay", "equation": "fpca", "example": "evidence-inspection"},
    "plot_trajectory_overlay": {"asset": "trajectory-curvature.svg", "category": "geometry-registration", "quantity": "Derived functional trajectory overlay", "equation": "trajectory-geometry", "example": "trajectory-geometry"},
    "plot_dynamic_time_warping_alignment": {"asset": "dtw-alignment.svg", "category": "geometry-registration", "quantity": "DTW alignment path", "equation": "dynamic-time-warping", "example": "dynamic-time-warping"},
    "plot_warping_functions": {"asset": "registration-warping.svg", "category": "geometry-registration", "quantity": "Landmark warp/displacement functions", "equation": "registration", "example": "phase-fpca"},
    "plot_registration": {"asset": "registration-before-after.svg", "category": "geometry-registration", "quantity": "Registered versus observed trajectories", "equation": "registration", "example": "phase-fpca"},

    # Dense FPCA, uncertainty, prediction, diagnostics.
    "plot_fpca_component": {"asset": "fpca-component.svg", "category": "fpca", "quantity": "FPC interpretation trajectory", "equation": "fpca", "example": "fpca-stability"},
    "plot_fpca_variance": {"asset": "fpca-variance.svg", "category": "fpca", "quantity": "Explained functional variance", "equation": "fpca", "example": "fpca-stability"},
    "plot_reconstruction_curve": {"asset": "fpca-reconstruction.svg", "category": "fpca", "quantity": "Observed versus truncated FPCA reconstruction", "equation": "fpca", "example": "fpca-stability"},
    "plot_fpca_cross_validation": {"asset": "fpca-cross-validation.svg", "category": "fpca", "quantity": "Reconstruction CV error by component count", "equation": "fpca", "example": "fpca-selection-uncertainty"},
    "plot_fpca_component_band": {"asset": "fpca-component-band.svg", "category": "fpca", "quantity": "Simultaneous FPC band", "equation": "fpca", "example": "simultaneous-fpc-bands"},
    "plot_fpca_component_envelope": {"asset": "fpca-component-envelope.svg", "category": "fpca", "quantity": "Sign-aligned FPC bootstrap envelope", "equation": "fpca", "example": "fpca-selection-uncertainty"},
    "plot_fpca_stability": {"asset": "fpca-stability.svg", "category": "fpca", "quantity": "FPC stability diagnostic", "equation": "fpca", "example": "fpca-stability"},
    "plot_fpca_subspace_stability": {"asset": "fpca-subspace-stability.svg", "category": "fpca", "quantity": "Near-tied eigenspace stability", "equation": "fpca", "example": "near-tied-subspace"},
    "plot_fpca_outlier_diagnostics": {"asset": "fpca-outlier-diagnostics.svg", "category": "fpca", "quantity": "FPCA score/reconstruction outlier review", "equation": "fpca", "example": "outlier-influence"},
    "plot_fpca_influence": {"asset": "fpca-influence.svg", "category": "fpca", "quantity": "Leave-one-curve FPCA influence", "equation": "fpca", "example": "outlier-influence"},
    "plot_conformal_fpca_anomaly": {"asset": "conformal-fpca-anomaly.svg", "category": "fpca", "quantity": "Split-conformal FPCA anomaly evidence", "equation": "conformal", "example": "conformal-fpca-anomaly"},
    "plot_fpca_score_uncertainty": {"asset": "fpca-score-uncertainty.svg", "category": "fpca", "quantity": "FPC score basis uncertainty", "equation": "fpca", "example": "fpca-score-uncertainty"},
    "plot_fpca_spectrum_uncertainty": {"asset": "fpca-spectrum-uncertainty.svg", "category": "fpca", "quantity": "Bootstrap eigenvalue-spectrum uncertainty", "equation": "fpca", "example": "fpca-spectrum-uncertainty"},
    "plot_fpca_regression_cv": {"asset": "fpca-regression-cv.svg", "category": "regression", "quantity": "FPCR predictive component-selection curve", "equation": "fpcr", "example": "predictive-fpca-regression"},
    "plot_nested_fpca_regression_cv": {"asset": "nested-fpca-regression-cv.svg", "category": "regression", "quantity": "Nested predictive FPCR validation", "equation": "fpcr", "example": "predictive-fpca-regression"},
    "plot_fpca_regression_slope_uncertainty": {"asset": "fpca-regression-slope-uncertainty.svg", "category": "regression", "quantity": "FPCR slope-function uncertainty", "equation": "fpcr", "example": "fpcr-bootstrap-inference"},
    "plot_fpca_regression_slope_band": {"asset": "fpca-regression-slope-band.svg", "category": "regression", "quantity": "Simultaneous FPCR slope band", "equation": "fpcr", "example": "fpcr-simultaneous-slope-band"},
    "plot_fpca_regression_mean_prediction_uncertainty": {"asset": "fpca-regression-mean-prediction.svg", "category": "regression", "quantity": "Mean-response FPCR prediction uncertainty", "equation": "fpcr", "example": "fpcr-bootstrap-inference"},
    "plot_fpca_regression_future_prediction_interval": {"asset": "fpca-regression-future-prediction.svg", "category": "regression", "quantity": "Future-outcome FPCR prediction interval", "equation": "fpcr", "example": "fpcr-future-prediction"},
    "plot_fpca_wild_bootstrap_projection": {"asset": "wild-bootstrap-projections.svg", "category": "regression", "quantity": "Wild-bootstrap fixed-target projection", "equation": "wild-bootstrap", "example": "fpcr-wild-bootstrap"},
    "plot_fpca_wild_bootstrap_family_test": {"asset": "wild-bootstrap-family-test.svg", "category": "regression", "quantity": "Fixed-family wild-bootstrap test", "equation": "family-tests", "example": "fpcr-wild-bootstrap-family-tests"},
    "plot_fpca_wild_bootstrap_monte_carlo_diagnostics": {"asset": "monte-carlo-precision.svg", "category": "regression", "quantity": "Bootstrap Monte Carlo precision", "equation": "monte-carlo", "example": "fpcr-wild-bootstrap-monte-carlo"},
    "plot_fpca_wild_bootstrap_simultaneous_interval": {"asset": "wild-bootstrap-simultaneous-interval.svg", "category": "regression", "quantity": "Simultaneous fixed-target wild-bootstrap interval", "equation": "simultaneous-wild-bootstrap", "example": "fpcr-wild-bootstrap-simultaneous"},
    "plot_fpca_wild_bootstrap_truncation_scan": {"asset": "wild-bootstrap-truncation-scan.svg", "category": "regression", "quantity": "Wild-bootstrap truncation sensitivity", "equation": "wild-bootstrap", "example": "fpcr-wild-bootstrap-selection"},

    # Sparse FDA.
    "plot_sparse_irregular_dimension": {"asset": "sparse-irregular-dimension.svg", "category": "sparse-fda", "quantity": "Native irregular observations", "equation": "sparse-fpca-pace", "example": "native-irregular"},
    "plot_sparse_fpca_component": {"asset": "sparse-fpca-component.svg", "category": "sparse-fda", "quantity": "Sparse PACE FPC interpretation", "equation": "sparse-fpca-pace", "example": "sparse-pace-fpca"},
    "plot_sparse_fpca_covariance": {"asset": "sparse-fpca-covariance.svg", "category": "sparse-fda", "quantity": "Smoothed sparse covariance surface", "equation": "sparse-fpca-pace", "example": "sparse-pace-fpca"},
    "plot_sparse_fpca_score_diagnostics": {"asset": "sparse-fpca-score-conditioning.svg", "category": "sparse-fda", "quantity": "PACE conditional-system diagnostics", "equation": "sparse-fpca-pace", "example": "sparse-pace-fpca"},

    # Functional summaries, regression, mixed effects.
    "plot_functional_mean_band": {"asset": "functional-mean-band.svg", "category": "regression", "quantity": "Simultaneous functional mean band", "equation": "mean-band", "example": "functional-mean-bands"},
    "plot_function_on_scalar_coefficients": {"asset": "function-on-scalar-coefficient.svg", "category": "regression", "quantity": "Function-on-scalar coefficient band", "equation": "function-on-scalar", "example": "function-on-scalar"},
    "plot_generalized_function_on_scalar_coefficients": {"asset": "generalized-fosr-coefficients.svg", "category": "regression", "quantity": "Marginal generalized coefficient functions", "equation": "generalized-function-on-scalar", "example": "generalized-function-on-scalar"},
    "plot_generalized_function_on_scalar_predictions": {"asset": "generalized-fosr-predictions.svg", "category": "regression", "quantity": "Fixed-profile marginal functional predictions", "equation": "generalized-function-on-scalar-prediction", "example": "generalized-function-on-scalar-prediction"},
    "plot_generalized_function_on_scalar_mean_difference": {"asset": "generalized-fosr-mean-difference.svg", "category": "regression", "quantity": "Predeclared marginal prediction contrast", "equation": "generalized-function-on-scalar-prediction", "example": "generalized-function-on-scalar-prediction"},
    "plot_functional_mixed_effects_coefficient": {"asset": "functional-mixed-effects-coefficient.svg", "category": "mixed-effects", "quantity": "Mixed-effects fixed coefficient function", "equation": "functional-mixed-effects", "example": "functional-mixed-effects"},
    "plot_functional_random_effects": {"asset": "functional-mixed-effects-random-slope.svg", "category": "mixed-effects", "quantity": "Participant functional random effects", "equation": "functional-mixed-effects-random-slope", "example": "functional-mixed-effects-random-slope"},
    "plot_functional_trial_random_effects": {"asset": "functional-trial-random-effects.svg", "category": "mixed-effects", "quantity": "Nested trial functional random effects", "equation": "functional-mixed-effects", "example": "functional-mixed-effects-trial-random-effect"},
    "plot_functional_mixed_effects_residual_acf": {"asset": "functional-mixed-effects-residual-acf.svg", "category": "mixed-effects", "quantity": "Mixed-effects residual ACF", "equation": "functional-mixed-effects", "example": "functional-mixed-effects-residual-diagnostics"},
    "plot_functional_mixed_effects_residual_variogram": {"asset": "functional-mixed-effects-residual-variogram.svg", "category": "mixed-effects", "quantity": "Mixed-effects residual variogram", "equation": "functional-mixed-effects", "example": "functional-mixed-effects-residual-diagnostics"},
    "plot_functional_mixed_effects_bootstrap_comparison": {"asset": "functional-mixed-effects-bootstrap-comparison.svg", "category": "mixed-effects", "quantity": "Fixed-covariance versus full-refit bootstrap", "equation": "functional-mixed-effects-full-refit-bootstrap", "example": "functional-mixed-effects-full-refit-bootstrap"},
    "plot_functional_variance_decomposition": {"asset": "functional-variance-decomposition.svg", "category": "mixed-effects", "quantity": "Participant/trial/residual functional variance", "equation": "functional-mixed-effects-covariance-sensitivity", "example": "functional-mixed-effects-covariance-sensitivity"},
    "plot_covariance_sensitivity_coefficients": {"asset": "covariance-sensitivity-coefficients.svg", "category": "mixed-effects", "quantity": "Coefficient sensitivity across covariance structures", "equation": "functional-mixed-effects-covariance-sensitivity", "example": "functional-mixed-effects-covariance-sensitivity"},
    "plot_covariance_sensitivity_band_widths": {"asset": "covariance-sensitivity-band-widths.svg", "category": "mixed-effects", "quantity": "Band-width sensitivity across covariance structures", "equation": "functional-mixed-effects-covariance-sensitivity", "example": "functional-mixed-effects-covariance-sensitivity"},

    # Simulation and recovery.
    "plot_functional_simulation_curve": {"asset": "functional-simulation-truth-audit.svg", "category": "simulation-validation", "quantity": "Observed versus latent simulated curve", "equation": "fpca", "example": "functional-simulation"},
    "plot_functional_simulation_phase_warps": {"asset": "functional-simulation-phase-warps.svg", "category": "simulation-validation", "quantity": "Declared simulated phase warps", "equation": "registration", "example": "functional-simulation"},
    "plot_functional_simulation_score_variances": {"asset": "functional-simulation-score-variances.svg", "category": "simulation-validation", "quantity": "Known latent score variance", "equation": "fpca", "example": "functional-simulation"},
    "plot_functional_recovery_summary": {"asset": "functional-recovery-summary.svg", "category": "simulation-validation", "quantity": "Known-truth recovery metrics", "equation": "fpca", "example": "functional-simulation"},

    # Distance / recurrence / nonlinear / information flow.
    "plot_trajectory_distance_rank_correlations": {"asset": "trajectory-distance-sensitivity.svg", "category": "nonlinear", "quantity": "Distance-specification rank agreement", "equation": "trajectory-distance-sensitivity", "example": "trajectory-distance-sensitivity"},
    "plot_embedding_delay_diagnostics": {"asset": "embedding-delay-diagnostics.svg", "category": "nonlinear", "quantity": "Embedding-delay diagnostics", "equation": "delay-embedding", "example": "nonlinear-dynamics"},
    "plot_embedding_dimension_diagnostics": {"asset": "embedding-dimension-diagnostics.svg", "category": "nonlinear", "quantity": "False-nearest-neighbor diagnostics", "equation": "delay-embedding", "example": "nonlinear-dynamics"},
    "plot_recurrence": {"asset": "recurrence-plot.svg", "category": "nonlinear", "quantity": "Sparse recurrence matrix", "equation": "recurrence", "example": "nonlinear-dynamics"},
    "plot_joint_recurrence": {"asset": "joint-recurrence.svg", "category": "nonlinear", "quantity": "Synchronized joint recurrence", "equation": "joint-recurrence", "example": "joint-recurrence"},
    "plot_recurrence_network_degree": {"asset": "recurrence-network-degree.svg", "category": "nonlinear", "quantity": "Recurrence-network degree profile", "equation": "recurrence-network", "example": "recurrence-networks"},
    "plot_recurrence_rate_curve": {"asset": "recurrence-radius-profile.svg", "category": "nonlinear", "quantity": "Recurrence-rate versus radius profile", "equation": "recurrence", "example": "recurrence-threshold-diagnostics"},
    "plot_rqa_metric_mean_bootstrap": {"asset": "rqa-population-bootstrap.svg", "category": "nonlinear", "quantity": "Population mean RQA bootstrap", "equation": "rqa-population-bootstrap", "example": "rqa-population-bootstrap"},
    "plot_rqa_sensitivity": {"asset": "rqa-sensitivity.svg", "category": "nonlinear", "quantity": "RQA parameter sensitivity", "equation": "recurrence", "example": "nonlinear-parameter-sensitivity"},
    "plot_windowed_rqa": {"asset": "windowed-rqa.svg", "category": "nonlinear", "quantity": "Windowed recurrence quantification", "equation": "functional-rqa-trajectories", "example": "rqa-functional-trajectories"},
    "plot_windowed_rqa_trajectories": {"asset": "functional-rqa-trajectories.svg", "category": "nonlinear", "quantity": "RQA-derived functional trajectories", "equation": "functional-rqa-trajectories", "example": "rqa-functional-trajectories"},
    "plot_windowed_rqa_sensitivity": {"asset": "windowed-rqa-sensitivity.svg", "category": "nonlinear", "quantity": "Window-length/step RQA sensitivity", "equation": "functional-rqa-trajectories", "example": "rqa-functional-sensitivity"},
    "plot_local_divergence": {"asset": "local-divergence.svg", "category": "nonlinear", "quantity": "Local divergence / Lyapunov fit", "equation": "local-divergence", "example": "nonlinear-dynamics"},
    "plot_kantz_sensitivity": {"asset": "kantz-sensitivity.svg", "category": "nonlinear", "quantity": "Kantz specification sensitivity", "equation": "kantz-local-divergence", "example": "kantz-lle"},
    "plot_lyapunov_sensitivity": {"asset": "lyapunov-sensitivity.svg", "category": "nonlinear", "quantity": "Rosenstein specification sensitivity", "equation": "local-divergence", "example": "nonlinear-parameter-sensitivity"},
    "plot_multivariate_iaaft_diagnostics": {"asset": "multivariate-iaaft-diagnostics.svg", "category": "nonlinear", "quantity": "Multivariate IAAFT preservation diagnostics", "equation": "multivariate-iaaft", "example": "multivariate-surrogates"},
    "plot_multivariate_surrogate_nonlinearity": {"asset": "multivariate-surrogate-nonlinearity.svg", "category": "nonlinear", "quantity": "Multivariate surrogate nonlinearity test", "equation": "multivariate-iaaft", "example": "multivariate-surrogates"},
    "plot_surrogate_nonlinearity": {"asset": "surrogate-nonlinearity.svg", "category": "nonlinear", "quantity": "IAAFT surrogate nonlinearity test", "equation": "surrogate-nonlinearity", "example": "nonlinear-dynamics"},
    "plot_poincare_return_map": {"asset": "return-map.svg", "category": "nonlinear", "quantity": "Empirical Poincare return map", "equation": "return-map-stability", "example": "return-map-stability"},
    "plot_transfer_entropy_circular_shift_test": {"asset": "transfer-entropy-shift-test.svg", "category": "nonlinear", "quantity": "Transfer-entropy source-shift null", "equation": "discrete-transfer-entropy", "example": "transfer-entropy"},
    "plot_transfer_entropy_sensitivity": {"asset": "transfer-entropy-sensitivity.svg", "category": "nonlinear", "quantity": "Transfer-entropy specification sensitivity", "equation": "transfer-entropy-sensitivity", "example": "transfer-entropy-sensitivity"},
    "plot_conditional_transfer_entropy_circular_shift_test": {"asset": "conditional-transfer-entropy-shift-test.svg", "category": "nonlinear", "quantity": "Conditional-TE source-shift null", "equation": "conditional-transfer-entropy", "example": "conditional-transfer-entropy"},
}


GALLERY_CATEGORIES = (
    "fpca",
    "sparse-fda",
    "regression",
    "mixed-effects",
    "geometry-registration",
    "nonlinear",
    "simulation-validation",
)
