"""Experimental F1-F6 research prototypes (NOT 1.2 stable public exports).

These symbols are deliberately opt-in under eyetrajectoriespy.research and
must not be presented as validated production inferential procedures.
"""
from .power_planning import FunctionalPowerSimulation, simulate_functional_study_power
from .reliability import FunctionalReliabilityResult, fit_functional_reliability, functional_reliability_frame
from .paired_contrasts import PairedFunctionalContrast, compare_repeated_functional_groups, repeated_functional_contrast_frame
from .sparse_group_inference import (
    SparseFunctionalGroupTest,
    test_sparse_functional_groups,
    functional_group_contrast_frame,
    plot_functional_group_contrast,
)
from .validation_targets import summarize_gaze_validation_targets
from .measurement_quality import (
    GazeMeasurementQualityAudit,
    audit_gaze_measurement_quality,
    measurement_quality_reporting_frame,
)
from .bids_interchange import (
    from_bids_eyetracking,
    validate_eyetracking_metadata,
)
from .aoi_feasibility import (
    AOIGeometryFeasibility,
    compare_aoi_functional_geometries,
    project_simplex,
)
from .aoi_holdout import (
    AOIGeometryHoldout, compare_aoi_functional_geometries_holdout,
)
from .functional_changepoints import (
    FunctionalChangepointResult,
    detect_ordered_functional_changepoint,
)
from .weighted_geometry import (
    WeightedMFPCAResult,
    fit_weighted_mfpca,
    reconstruct_weighted_mfpca,
    weighted_component_geometry,
)

__all__ = [
    "FunctionalPowerSimulation", "simulate_functional_study_power",
    "FunctionalReliabilityResult", "fit_functional_reliability", "functional_reliability_frame",
    "PairedFunctionalContrast", "compare_repeated_functional_groups", "repeated_functional_contrast_frame",
    "SparseFunctionalGroupTest", "test_sparse_functional_groups",
    "functional_group_contrast_frame", "plot_functional_group_contrast",
    "summarize_gaze_validation_targets",
    "GazeMeasurementQualityAudit", "audit_gaze_measurement_quality",
    "measurement_quality_reporting_frame", "from_bids_eyetracking",
    "validate_eyetracking_metadata", "AOIGeometryFeasibility",
    "compare_aoi_functional_geometries", "project_simplex",
    "AOIGeometryHoldout", "compare_aoi_functional_geometries_holdout",
    "FunctionalChangepointResult", "detect_ordered_functional_changepoint",
    "WeightedMFPCAResult", "fit_weighted_mfpca",
    "reconstruct_weighted_mfpca", "weighted_component_geometry",
]
