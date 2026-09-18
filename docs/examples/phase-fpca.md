# Worked example: phase as an outcome

Suppose every trial contains an interpretable inspection landmark.

    registration = register_to_landmarks(
        gaze,
        observed_landmarks=inspection_times,
        reference_landmarks=np.array([1.0]),
    )

## Analyze timing deformation

    phase_fit = fit_phase_fpca(
        registration,
        n_components=2,
    )

The phase FPCs describe dominant ways in which traversal timing departs from the reference.

## Preserve raw landmark latency

    landmark_frame = phase_landmark_frame(registration)

The phase function and the observed landmark times answer related but not identical questions.

## Check what registration changed

    sensitivity = compare_registered_unregistered_fpca(
        registration,
        n_components=3,
        scaling="dimension_sd",
    )

    registration_sensitivity_frame(sensitivity)

If matched component similarity or score correlation falls substantially, registration has changed the covariance structure rather than merely producing a cleaner plot.
