# Worked example: FPCA stability

Start with repeated synthetic gaze trials:

    gaze = simulate_planar_trajectories(
        n_participants=30,
        trials_per_participant=6,
        random_state=27,
    )

Run participant-level bootstrap because trials are nested within participants:

    stability = bootstrap_fpca_stability(
        gaze,
        n_bootstrap=200,
        n_components=3,
        scaling="dimension_sd",
        resample_unit="participant",
        participant_column="participant_id",
        random_state=27,
    )

Summarize and visualize:

    table = summarise_fpca_stability(stability)
    plot_fpca_stability(stability)

## What to inspect

A component can explain substantial variance yet have modest bootstrap similarity. Conversely, a lower-variance component may have a very consistent shape.

Use stability to qualify interpretation, not to create a new significance threshold.

## Add reconstruction

    curve = fpca_reconstruction_curve(
        stability.reference,
        gaze,
    )

    plot_reconstruction_curve(curve)

This separates two questions:

1. **Are the retained components stable?**
2. **Do the retained components reconstruct the trajectories adequately?**
