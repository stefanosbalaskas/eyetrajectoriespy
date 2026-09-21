# Worked example: simultaneous FPC-shape bands

This example uses repeated synthetic eye-tracking trials and treats participants as the independent resampling units.

## Generate continuous planar gaze trajectories

    from eyetrajectoriespy import simulate_planar_trajectories

    gaze = simulate_planar_trajectories(
        n_participants=24,
        trials_per_participant=2,
        n_time=61,
        random_state=2026,
    )

## Calibrate component-wise bands

    from eyetrajectoriespy import bootstrap_fpca_component_bands

    bands = bootstrap_fpca_component_bands(
        gaze,
        n_bootstrap=500,
        n_components=2,
        scaling="dimension_sd",
        resample_unit="participant",
        participant_column="participant_id",
        confidence_level=0.95,
        simultaneous_scope="component",
        random_state=2026,
    )

## Inspect and export the evidence

    from eyetrajectoriespy import fpca_component_band_frame

    print(bands.critical_values)
    print(bands.similarities.mean(axis=0))
    frame = fpca_component_band_frame(bands)
    print(frame.head())

## Plot one functional dimension

    from eyetrajectoriespy import plot_fpca_component_band

    plot_fpca_component_band(
        bands,
        component=0,
        dimension="x",
    )

## Familywise sensitivity analysis

    family = bootstrap_fpca_component_bands(
        gaze,
        n_bootstrap=500,
        n_components=2,
        scaling="dimension_sd",
        resample_unit="participant",
        participant_column="participant_id",
        confidence_level=0.95,
        simultaneous_scope="family",
        random_state=2026,
    )

    assert (family.critical_values >= bands.critical_values).all()

## Optional pre-specified near-tie screen

If the study protocol defines 0.05 as a descriptive relative-gap review threshold:

    screened = bootstrap_fpca_component_bands(
        gaze,
        n_bootstrap=500,
        n_components=2,
        scaling="dimension_sd",
        resample_unit="participant",
        participant_column="participant_id",
        relative_gap_threshold=0.05,
        on_near_tie="warn",
        random_state=2026,
    )

A warning is not a license to ignore the identification problem. Inspect eigengap and subspace diagnostics before interpreting a warned individual FPC.

## Manuscript wording

    from eyetrajectoriespy import fpca_component_band_reporting_text

    print(fpca_component_band_reporting_text(bands))

## Interpretation

The result answers how much the matched, oriented FPC estimate moves under the selected bootstrap design while controlling the maximum standardized excursion over the observed grid.

It does not show that every unobserved time point is covered, that the FPC is causal, or that near-tied axes have unique population labels.

## Next steps

- [FPC shape uncertainty](../guides/component-uncertainty.md)
- [Simultaneous FPC bands](../guides/simultaneous-fpc-bands.md)
- [Near-tied FPC subspaces](../guides/subspace-stability.md)
- [Reporting checklist](../methods/reporting.md)
- [Pre-registration checklist](../methods/preregistration.md)
