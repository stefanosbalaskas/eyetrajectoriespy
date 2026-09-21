# Worked example: FPC score basis uncertainty

This example asks how much fixed target scores change when the FPCA basis is re-estimated.

## Generate repeated-trial trajectories

    from eyetrajectoriespy import simulate_planar_trajectories

    gaze = simulate_planar_trajectories(
        n_participants=24,
        trials_per_participant=2,
        n_time=61,
        random_state=2026,
    )

## Choose fixed targets

    targets = gaze.subset([0, 1, 2, 3, 4, 5])

The targets remain fixed throughout the bootstrap. Only the participant sample used to estimate the basis changes.

## Bootstrap the basis and re-project the same targets

    from eyetrajectoriespy import bootstrap_fpca_score_uncertainty

    result = bootstrap_fpca_score_uncertainty(
        gaze,
        targets=targets,
        n_bootstrap=500,
        n_components=2,
        scaling="dimension_sd",
        resample_unit="participant",
        participant_column="participant_id",
        level=0.95,
        random_state=2026,
    )

## Inspect a tidy table

    from eyetrajectoriespy import fpca_score_uncertainty_frame

    table = fpca_score_uncertainty_frame(result)
    print(table)

Each row contains a target trajectory × FPC combination with the reference score, bootstrap median, bootstrap standard deviation, percentile envelope, and median component-matching similarity.

## Plot the uncertainty

    from eyetrajectoriespy import plot_fpca_score_uncertainty

    plot_fpca_score_uncertainty(
        result,
        component=0,
        max_targets=6,
    )

The cross marks the full-sample reference score. The bootstrap median and percentile envelope show movement attributable to re-estimating the basis.

## Generate reporting text

    from eyetrajectoriespy import fpca_score_uncertainty_reporting_text

    print(fpca_score_uncertainty_reporting_text(result))

## Interpretation

A wide envelope means that the target’s coordinate on that named reference FPC is sensitive to which participants were used to estimate the basis.

A narrow envelope means only that this score is stable with respect to the stated basis-resampling scheme.

It does **not** mean the target was measured without error or that a downstream coefficient using this score has a narrow confidence interval.

## What if matching similarity is poor?

Poor matching similarity suggests that an individual FPC identity is unstable across bootstrap samples. In that case:

1. inspect eigengaps;
2. inspect subspace stability;
3. avoid strong component-specific labels;
4. consider whether a multicomponent subspace is the more stable scientific object.

## Training-curve targets

Omit <code>targets</code> to evaluate all training curves as fixed targets:

    training_scores = bootstrap_fpca_score_uncertainty(
        gaze,
        n_bootstrap=500,
        n_components=2,
        scaling="dimension_sd",
        resample_unit="participant",
        participant_column="participant_id",
        random_state=2026,
    )

The full-sample reference scores then equal the ordinary fitted training scores.

## Next steps

- [FPC score basis uncertainty](../guides/score-uncertainty.md)
- [FPC stability](../guides/stability.md)
- [Near-tied FPC subspaces](../guides/subspace-stability.md)
- [FPCA spectrum uncertainty](../guides/spectrum-uncertainty.md)
- [Reporting checklist](../methods/reporting.md)
