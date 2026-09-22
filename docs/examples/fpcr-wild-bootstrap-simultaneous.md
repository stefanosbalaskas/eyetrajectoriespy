# Worked example: simultaneous fixed-target FPCR wild bootstrap

This example first constructs the ordinary heteroscedastic target-wise wild-bootstrap result and then post-calibrates the same bootstrap roots across a declared four-target family.

## Simulate independent trajectories and a heteroscedastic outcome

    import numpy as np

    from eyetrajectoriespy import (
        fit_mfpca,
        simulate_planar_trajectories,
        wild_bootstrap_fpca_projection,
    )

    gaze = simulate_planar_trajectories(
        n_participants=60,
        trials_per_participant=1,
        n_time=41,
        random_state=2028,
    )

    reference = fit_mfpca(
        gaze,
        n_components=3,
        scaling="dimension_sd",
    )

    rng = np.random.default_rng(2028)
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
        + rng.normal(0.0, noise_sd)
    )

## Declare the target family in the base analysis

    targets = gaze.subset([0, 1, 2, 3])

    base = wild_bootstrap_fpca_projection(
        gaze,
        outcome,
        targets=targets,
        n_bootstrap=500,
        residual_components=2,
        inference_components=3,
        scaling="dimension_sd",
        multiplier="normal",
        confidence_level=0.95,
        independent_unit_column="participant_id",
        random_state=2028,
    )

The four targets above define the family. Adding or removing targets changes the familywise question.

## Calibrate one maximum statistic across targets

    from eyetrajectoriespy import (
        fpca_wild_bootstrap_projection_simultaneous_interval,
    )

    simultaneous = fpca_wild_bootstrap_projection_simultaneous_interval(base)

No FPCA fit, regression fit, residual calculation, multiplier draw, or bootstrap replicate is rerun here.

## Compare marginal and familywise intervals

    from eyetrajectoriespy import fpca_wild_bootstrap_simultaneous_frame

    table = fpca_wild_bootstrap_simultaneous_frame(simultaneous)
    print(table)

The table exposes both target-wise and simultaneous limits and their corresponding critical values.

## Plot both layers

    from eyetrajectoriespy import plot_fpca_wild_bootstrap_simultaneous_interval

    plot_fpca_wild_bootstrap_simultaneous_interval(
        simultaneous,
        max_targets=4,
        show_targetwise=True,
    )

The familywise bars should be at least as wide as the target-wise bars at the same confidence level.

## Recalibrate the same roots at a different confidence level

    high = fpca_wild_bootstrap_projection_simultaneous_interval(
        base,
        confidence_level=0.99,
    )

Changing the confidence level recalibrates the stored roots. It does not trigger a new bootstrap.

## Reporting text

    from eyetrajectoriespy import fpca_wild_bootstrap_simultaneous_reporting_text

    print(fpca_wild_bootstrap_simultaneous_reporting_text(simultaneous))

## Interpretation

The simultaneous interval controls the declared family of fixed centered FPCR projections under the base independent-curve wild-bootstrap contract.

It is not a future-outcome prediction interval, does not authorize adding targets after inspection, and does not solve repeated-participant dependence.

## Next steps

- [Simultaneous fixed-target FPCR wild-bootstrap guide](../guides/fpcr-wild-bootstrap-simultaneous.md)
- [Heteroscedastic FPCR wild bootstrap](../guides/fpcr-wild-bootstrap.md)
- [Stabilized-volatility FPCR selection](../guides/fpcr-wild-bootstrap-selection.md)
- [Reporting checklist](../methods/reporting.md)
