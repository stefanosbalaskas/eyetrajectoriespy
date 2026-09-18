"""eyetrajectoriespy: functional and continuous eye-tracking trajectory analysis."""

from .analysis import (
    cluster_fpca_scores,
    fit_scalar_on_function_regression,
    functional_l2_distance,
    nearest_trajectory_indices,
    pairwise_functional_distances,
    score_distance_matrix,
)
from .backends import to_skfda_grid
from .compositional import (
    alr_transform,
    fit_compositional_fpca,
    inverse_alr,
    reconstruct_compositional_fpca,
)
from .elastic import fit_elastic_fpca
from .fpca import (
    component_trajectories,
    fit_fpca,
    fit_mfpca,
    fpca_score_frame,
    functional_trapezoid_weights,
    reconstruct_fpca,
    select_n_components,
    transform_fpca,
)
from .io import from_irregular_long_dataframe, from_long_dataframe
from .kinematics import (
    acceleration_magnitude_function,
    cumulative_path_length,
    differentiate_trajectories,
    distance_to_landmark_function,
    speed_function,
)
from .multilevel import fit_multilevel_fpca
from .plotting import (
    plot_fpca_component,
    plot_fpca_variance,
    plot_planar_trajectories,
    plot_registration,
    plot_trajectory_overlay,
    plot_warping_functions,
)
from .preprocessing import (
    center_on_landmark,
    interpolate_short_gaps,
    normalize_coordinates,
    normalize_time,
    resample_to_grid,
    smooth_trajectories,
)
from .registration import phase_summary, register_to_landmarks, warping_displacement
from .reporting import (
    fpca_reporting_text,
    multilevel_fpca_reporting_text,
    summarise_fpca,
    summarise_trajectory_set,
)
from .simulate import simulate_aoi_probability_trajectories, simulate_planar_trajectories
from .types import (
    ClusterResult,
    CompositionalFPCAResult,
    ElasticFPCAResult,
    FPCAResult,
    FunctionalRegressionResult,
    MultilevelFPCAResult,
    RegistrationResult,
    TrajectorySet,
)
from .validation import (
    validate_common_grid,
    validate_no_long_missing_runs,
    validate_simplex,
    validate_trajectory_set,
)

__version__ = "0.1.0.dev0"

__all__ = [
    "TrajectorySet",
    "FPCAResult",
    "RegistrationResult",
    "CompositionalFPCAResult",
    "MultilevelFPCAResult",
    "ElasticFPCAResult",
    "FunctionalRegressionResult",
    "ClusterResult",
    "from_long_dataframe",
    "from_irregular_long_dataframe",
    "validate_trajectory_set",
    "validate_common_grid",
    "validate_simplex",
    "validate_no_long_missing_runs",
    "resample_to_grid",
    "interpolate_short_gaps",
    "smooth_trajectories",
    "normalize_time",
    "normalize_coordinates",
    "center_on_landmark",
    "functional_trapezoid_weights",
    "fit_fpca",
    "fit_mfpca",
    "transform_fpca",
    "reconstruct_fpca",
    "component_trajectories",
    "select_n_components",
    "fpca_score_frame",
    "register_to_landmarks",
    "warping_displacement",
    "phase_summary",
    "alr_transform",
    "inverse_alr",
    "fit_compositional_fpca",
    "reconstruct_compositional_fpca",
    "fit_multilevel_fpca",
    "fit_elastic_fpca",
    "differentiate_trajectories",
    "speed_function",
    "acceleration_magnitude_function",
    "distance_to_landmark_function",
    "cumulative_path_length",
    "functional_l2_distance",
    "pairwise_functional_distances",
    "nearest_trajectory_indices",
    "score_distance_matrix",
    "cluster_fpca_scores",
    "fit_scalar_on_function_regression",
    "simulate_planar_trajectories",
    "simulate_aoi_probability_trajectories",
    "summarise_trajectory_set",
    "summarise_fpca",
    "fpca_reporting_text",
    "multilevel_fpca_reporting_text",
    "plot_trajectory_overlay",
    "plot_planar_trajectories",
    "plot_fpca_variance",
    "plot_fpca_component",
    "plot_registration",
    "plot_warping_functions",
    "to_skfda_grid",
]
