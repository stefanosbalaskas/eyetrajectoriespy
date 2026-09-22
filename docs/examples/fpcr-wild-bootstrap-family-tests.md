# Worked example: fixed-family FPCR wild-bootstrap tests

This example tests four fixed centered FPCR projections against zero while preserving the joint wild-bootstrap dependence across targets.

## Simulate independent trajectories

    import numpy as np

    from eyetrajectoriespy import fit_mfpca, simulate_planar_trajectories

    gaze = simulate_planar_trajectories(
        n_participants=60,
        trials_per_participant=1,
        n_time=41,
        random_state=2029,
    )

    reference = fit_mfpca(
        gaze,
        n_components=3,
        scaling="dimension_sd",
    )

    rng = np.random.default_rng(2029)
    score1 = reference.scores[:, 0]
    score2 = reference.scores[:, 1]
    noise_sd = 0.25 + 0.30 * (
        np.abs(score1) / max(np.std(score1, ddof=1), 1e-8)
    )
    outcome = 1.0 + 1.2 * score1 - 0.5 * score2 + rng.normal(0.0, noise_sd)

## Build the base heteroscedastic wild-bootstrap result

    from eyetrajectoriespy import wild_bootstrap_fpca_projection

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
        independent_unit_column="participant_id",
        random_state=2029,
    )

The four target trajectories define the testing family.

## Test all target projections against zero

    from eyetrajectoriespy import fpca_wild_bootstrap_projection_family_test

    tests = fpca_wild_bootstrap_projection_family_test(
        base,
        null_values=0.0,
        significance_level=0.05,
        pvalue_correction="plus_one",
    )

## Inspect marginal and adjusted evidence

    from eyetrajectoriespy import fpca_wild_bootstrap_family_test_frame

    table = fpca_wild_bootstrap_family_test_frame(tests)
    print(table)

The target-wise p-value asks about one target using its own root distribution.

The adjusted p-value compares the same observed statistic with the bootstrap maximum across the complete family.

The global p-value asks whether the largest observed absolute statistic is unusual under the joint bootstrap root distribution.

## Plot the multiplicity effect

    from eyetrajectoriespy import plot_fpca_wild_bootstrap_family_test

    plot_fpca_wild_bootstrap_family_test(
        tests,
        max_targets=4,
        show_targetwise=True,
    )

The horizontal line is the declared alpha level. Adjusted probabilities cannot be smaller than their corresponding target-wise values because every replicate-wise maximum is at least as large as the target-specific absolute root.

## Test target-specific null values

    nulls = np.array([0.0, 0.0, 0.25, -0.25])

    specific = fpca_wild_bootstrap_projection_family_test(
        base,
        null_values=nulls,
        significance_level=0.05,
    )

Null values are in the scalar-response projection units.

## Reporting text

    from eyetrajectoriespy import fpca_wild_bootstrap_family_test_reporting_text

    print(fpca_wild_bootstrap_family_test_reporting_text(tests))

## Interpretation

These are approximate bootstrap tests for fixed centered FPCR projections. The bootstrap distribution is not regenerated under an explicitly imposed null. The package does not claim strong FWER for arbitrary subsets of null hypotheses without additional subset-pivotality conditions.

## Next steps

- [Fixed-family FPCR wild-bootstrap hypothesis tests](../guides/fpcr-wild-bootstrap-family-tests.md)
- [Simultaneous fixed-target FPCR wild bootstrap](../guides/fpcr-wild-bootstrap-simultaneous.md)
- [Heteroscedastic FPCR wild bootstrap](../guides/fpcr-wild-bootstrap.md)
- [Reporting checklist](../methods/reporting.md)
