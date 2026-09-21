# Worked example: FPCA spectrum uncertainty

This example treats participants as independent bootstrap units while preserving repeated trials within participant.

## Simulate trajectories

    from eyetrajectoriespy import simulate_planar_trajectories

    gaze = simulate_planar_trajectories(
        n_participants=24,
        trials_per_participant=2,
        n_time=61,
        random_state=2026,
    )

## Fit bootstrap spectrum uncertainty

    from eyetrajectoriespy import bootstrap_fpca_spectrum_uncertainty

    spectrum = bootstrap_fpca_spectrum_uncertainty(
        gaze,
        n_bootstrap=500,
        n_components=3,
        scaling="dimension_sd",
        resample_unit="participant",
        participant_column="participant_id",
        confidence_level=0.95,
        simultaneous_scope="component",
        random_state=2026,
    )

## Inspect the component table

    from eyetrajectoriespy import fpca_spectrum_uncertainty_frame

    table = fpca_spectrum_uncertainty_frame(spectrum)
    print(table)

The individual eigenvalue and explained-variance-ratio rows refer to matched reference FPC identities.

The cumulative columns use descending eigenvalue rank. They therefore answer the standard “how much variance is explained by the top k components?” question even if two bootstrap FPC shapes swap.

## Familywise sensitivity

    family = bootstrap_fpca_spectrum_uncertainty(
        gaze,
        n_bootstrap=500,
        n_components=3,
        scaling="dimension_sd",
        resample_unit="participant",
        participant_column="participant_id",
        confidence_level=0.95,
        simultaneous_scope="family",
        random_state=2026,
    )

Familywise critical values are at least as conservative as the corresponding component-wise values under the same bootstrap draws, separately for each metric family.

## Plot the variance decomposition

    from eyetrajectoriespy import plot_fpca_spectrum_uncertainty

    plot_fpca_spectrum_uncertainty(
        family,
        metric="explained_variance_ratio",
    )

    plot_fpca_spectrum_uncertainty(
        family,
        metric="cumulative_variance_ratio",
    )

## Generate manuscript wording

    from eyetrajectoriespy import fpca_spectrum_uncertainty_reporting_text

    print(fpca_spectrum_uncertainty_reporting_text(family))

## Interpretation

Use the result to describe uncertainty in the variance decomposition, not to claim that a component is substantively valid or automatically retained.

If adjacent eigenvalues are close, supplement the spectrum with eigengap and subspace-stability diagnostics before naming individual FPC shapes.

## Next steps

- [FPCA spectrum uncertainty](../guides/spectrum-uncertainty.md)
- [Near-tied FPC subspaces](../guides/subspace-stability.md)
- [Selecting FPC count](../guides/component-selection.md)
- [Predictive FPC selection](../guides/predictive-component-selection.md)
- [Reporting checklist](../methods/reporting.md)
