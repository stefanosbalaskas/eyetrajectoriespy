# Phase FPCA and registration sensitivity

Registration changes the time parameterization of a trajectory. In eye tracking, that is scientifically consequential because timing may encode verification latency, hesitation, or strategy.

## Treat warping as data

After explicit landmark registration:

    registration = register_to_landmarks(
        gaze,
        observed_landmarks,
        reference_landmarks=reference_landmarks,
    )

convert the estimated warpings to a functional object:

    phase = phase_trajectory_set(
        registration,
        representation="displacement",
    )

For displacement functions,

\[
D_i(t)=h_i(t)-t,
\]

positive and negative values indicate how the source time differs from the reference time across the trial.

## FPCA of phase variation

    phase_fit = fit_phase_fpca(
        registration,
        n_components=0.95,
    )

Phase FPCA asks how **timing deformation itself varies across curves**. This is complementary to FPCA on the registered spatial trajectories.

## Keep landmark timing too

    landmark_table = phase_landmark_frame(registration)

Do not reduce all phase information to a single average warping statistic when the experiment has interpretable landmarks.

## Did registration change the scientific structure?

    sensitivity = compare_registered_unregistered_fpca(
        registration,
        n_components=3,
        scaling="dimension_sd",
    )

    registration_sensitivity_frame(sensitivity)

The comparison matches pre- and post-registration FPCs and reports:

- functional shape similarity;
- matched component identities;
- score correlations after sign alignment.

Large changes are not automatically bad. They indicate that phase variation was contributing materially to the unregistered covariance structure.

## Recommended reporting

Report both the justification for registration and what changed because of it. When timing is theoretically meaningful, include phase results or a registered-versus-unregistered sensitivity analysis rather than presenting only the aligned curves.
