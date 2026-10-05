import importlib
from dataclasses import is_dataclass

import eyetrajectoriespy as et


MODULE_SURFACES = {
    "eyetrajectoriespy.sparse_score_uncertainty": (
        "SparseFPCAScoreUncertaintyResult",
        "sparse_fpca_score_uncertainty",
        "sparse_fpca_score_uncertainty_frame",
    ),
    "eyetrajectoriespy.sparse_score_uncertainty_reporting": (
        "sparse_fpca_score_uncertainty_reporting_text",
    ),
    "eyetrajectoriespy.sparse_bandwidth_selection": (
        "SparseFPCABandwidthSelectionResult",
        "select_sparse_fpca_bandwidths",
        "sparse_fpca_bandwidth_selection_reporting_text",
    ),
    "eyetrajectoriespy.observation_process": (
        "ObservationProcessData",
        "ObservationProcessDiagnosticResult",
        "observation_process_data",
        "diagnose_observation_process",
        "observation_process_frame",
        "observation_process_reporting_text",
    ),
    "eyetrajectoriespy.sparse_multivariate_score_uncertainty": (
        "SparseMFPCAScoreUncertaintyResult",
        "sparse_mfpca_score_uncertainty",
        "sparse_mfpca_score_uncertainty_frame",
        "sparse_mfpca_score_uncertainty_reporting_text",
    ),
    "eyetrajectoriespy.sparse_multivariate_bandwidth_selection": (
        "SparseMFPCABandwidthSelectionResult",
        "select_sparse_mfpca_bandwidths",
        "sparse_mfpca_bandwidth_selection_reporting_text",
    ),
    "eyetrajectoriespy.sparse_multilevel": (
        "SparseMultilevelFPCAResult",
        "fit_sparse_multilevel_fpca",
        "sparse_multilevel_fpca_reporting_text",
    ),
    "eyetrajectoriespy.sparse_multivariate_async": (
        "SparseAsyncMFPCAResult",
        "fit_sparse_mfpca_async",
        "sparse_mfpca_async_score_frame",
        "sparse_mfpca_async_reporting_text",
    ),
    "eyetrajectoriespy.sparse_partial_prediction": (
        "SparseFPCAPartialPredictionResult",
        "sparse_fpca_partial_trajectory_prediction",
        "sparse_fpca_partial_prediction_frame",
        "sparse_fpca_partial_prediction_reporting_text",
    ),
    "eyetrajectoriespy.sparse_partial_conformal": (
        "SparseFPCAPartialConformalCalibrationResult",
        "SparseFPCAPartialConformalBandResult",
        "calibrate_sparse_fpca_partial_prediction_conformal",
        "sparse_fpca_conformal_prediction_band",
        "sparse_fpca_conformal_band_frame",
        "sparse_fpca_conformal_band_reporting_text",
    ),
}


RESULT_NAMES = {
    "SparseFPCAScoreUncertaintyResult",
    "SparseFPCABandwidthSelectionResult",
    "ObservationProcessData",
    "ObservationProcessDiagnosticResult",
    "SparseMFPCAScoreUncertaintyResult",
    "SparseMFPCABandwidthSelectionResult",
    "SparseMultilevelFPCAResult",
    "SparseAsyncMFPCAResult",
    "SparseFPCAPartialPredictionResult",
    "SparseFPCAPartialConformalCalibrationResult",
    "SparseFPCAPartialConformalBandResult",
}


def test_supported_one_dot_one_module_surface_imports():
    for module_name, names in MODULE_SURFACES.items():
        module = importlib.import_module(module_name)
        for name in names:
            assert hasattr(module, name), f"{module_name}.{name} is missing"
            value = getattr(module, name)
            if name in RESULT_NAMES:
                assert is_dataclass(value), f"{module_name}.{name} must remain a dataclass"
                assert value.__dataclass_params__.frozen is True
            else:
                assert callable(value), f"{module_name}.{name} must remain callable"


def test_one_dot_one_surface_remains_module_scoped():
    # R1 deliberately documents these specialized additions as supported
    # module-scoped 1.1 APIs rather than inflating the frozen 1.0 root namespace.
    for names in MODULE_SURFACES.values():
        for name in names:
            assert not hasattr(et, name), f"{name} was promoted to package root without review"
