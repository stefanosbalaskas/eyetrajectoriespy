# Worked example: heteroscedastic FPCR wild bootstrap

This example creates a scalar outcome whose noise variance changes with the first FPC score and then evaluates centered target projections with a fixed-regressor wild bootstrap.

## Simulate independent functional trajectories

    import numpy as np

    from eyetrajectoriespy import (
        fit_mfpca,
        simulate_planar_trajectories,
    )

    gaze = simulate_planar_trajectories(
        n_participants=60,
        trials_per_participant=1,
        n_time=61,
        random_state=2026,
    )

One trajectory per participant keeps the curve rows independent for this example.

## Construct a heteroscedastic scalar outcome

    reference = fit_mfpca(
        gaze,
        n_components=3,
        scaling="dimension_sd",
    )

    generator = np.random.default_rng(2026)

    score1 = reference.scores[:, 0]
    score2 = reference.scores[:, 1]

    noise_sd = (
        0.25
        + 0.30 * np.abs(score1)
        / max(np.std(score1, ddof=1), 1e-8)
    )

    outcome = (
        1.0
        + 1.2 * score1
        - 0.5 * score2
        + generator.normal(0.0, noise_sd)
    )

## Run the wild bootstrap

    from eyetrajectoriespy import wild_bootstrap_fpca_projection

    result = wild_bootstrap_fpca_projection(
        gaze,
        outcome,
        targets=gaze.subset([0, 1, 2, 3]),
        n_bootstrap=500,
        residual_components=2,
        inference_components=3,
        scaling="dimension_sd",
        multiplier="normal",
        confidence_level=0.95,
        independent_unit_column="participant_id",
        random_state=2026,
    )

The participant IDs are unique because this synthetic example contains one trajectory per participant.

If repeated trials were present, the function would stop instead of silently treating them as independent.

## Inspect target-wise intervals

    from eyetrajectoriespy import fpca_wild_bootstrap_projection_frame

    table = fpca_wild_bootstrap_projection_frame(result)
    print(table)

The reference projection uses h=3 FPCs.

The bootstrap pseudo-truth uses g=k=2 FPCs.

The interval therefore preserves the declared truncation distinction.

## Plot the projections

    from eyetrajectoriespy import plot_fpca_wild_bootstrap_projection

    plot_fpca_wild_bootstrap_projection(
        result,
        max_targets=4,
    )

Zero on the y-axis corresponds to no centered FPCR projection relative to the training functional mean.

## Use Mammen multipliers explicitly

    mammen = wild_bootstrap_fpca_projection(
        gaze,
        outcome,
        targets=gaze.subset([0, 1, 2, 3]),
        n_bootstrap=500,
        residual_components=2,
        inference_components=3,
        scaling="dimension_sd",
        multiplier="mammen",
        random_state=2026,
    )

Changing multiplier family is an explicit sensitivity choice rather than an automatic fallback.

## Generate reporting language

    from eyetrajectoriespy import fpca_wild_bootstrap_projection_reporting_text

    print(fpca_wild_bootstrap_projection_reporting_text(result))

## Interpretation checklist

Before interpreting a target interval:

1. verify curve rows are independent sampling units;
2. report k, g=k, and h explicitly;
3. report the multiplier family;
4. report that the FPCA basis remained fixed;
5. report bootstrap-level heteroscedastic studentization;
6. distinguish the centered projection from a future observed outcome;
7. do not claim simultaneous coverage across targets;
8. do not treat h as if its data-driven selection uncertainty were included.

## Next steps

- [Heteroscedastic FPCR wild bootstrap](../guides/fpcr-wild-bootstrap.md)
- [Gaussian FPCR bootstrap uncertainty](../guides/fpcr-bootstrap-inference.md)
- [Gaussian FPCR future-outcome prediction](../guides/fpcr-future-prediction.md)
- [Reporting checklist](../methods/reporting.md)
