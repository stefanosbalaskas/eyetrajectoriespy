# Public API

## Core objects
::: eyetrajectoriespy.TrajectorySet
::: eyetrajectoriespy.FPCAResult
::: eyetrajectoriespy.RegistrationResult
::: eyetrajectoriespy.CompositionalFPCAResult
::: eyetrajectoriespy.MultilevelFPCAResult

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

## FPCA / MFPCA
::: eyetrajectoriespy.fit_fpca
::: eyetrajectoriespy.fit_mfpca
::: eyetrajectoriespy.transform_fpca
::: eyetrajectoriespy.reconstruct_fpca
::: eyetrajectoriespy.component_trajectories
::: eyetrajectoriespy.fpca_score_frame

## Registration and phase
::: eyetrajectoriespy.register_to_landmarks
::: eyetrajectoriespy.warping_displacement
::: eyetrajectoriespy.phase_summary

## Multilevel and compositional
::: eyetrajectoriespy.fit_multilevel_fpca
::: eyetrajectoriespy.fit_compositional_fpca
::: eyetrajectoriespy.reconstruct_compositional_fpca

## Derived functions
::: eyetrajectoriespy.speed_function
::: eyetrajectoriespy.acceleration_magnitude_function
::: eyetrajectoriespy.distance_to_landmark_function
::: eyetrajectoriespy.cumulative_path_length

## Downstream analysis
::: eyetrajectoriespy.functional_l2_distance
::: eyetrajectoriespy.pairwise_functional_distances
::: eyetrajectoriespy.cluster_fpca_scores
::: eyetrajectoriespy.fit_scalar_on_function_regression

## Plotting and reporting
::: eyetrajectoriespy.plot_planar_trajectories
::: eyetrajectoriespy.plot_fpca_component
::: eyetrajectoriespy.plot_warping_functions
::: eyetrajectoriespy.summarise_fpca
::: eyetrajectoriespy.fpca_reporting_text

## Optional interoperability
::: eyetrajectoriespy.to_skfda_grid
::: eyetrajectoriespy.fit_elastic_fpca
