# Worked example: Monte Carlo precision for wild-bootstrap family tests

This example extends the fixed-family test workflow with a finite-bootstrap precision audit.

## 1. Fit the heteroscedastic wild-bootstrap projection model

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
        random_state=2030,
    )
    fpca = fit_mfpca(gaze, n_components=3, scaling="dimension_sd")
    rng = np.random.default_rng(2030)

    score1 = fpca.scores[:, 0]
    score2 = fpca.scores[:, 1]
    noise_sd = 0.25 + 0.30 * (
        np.abs(score1) / max(np.std(score1, ddof=1), 1e-8)
    )
    outcome = (
        1.0
        + 1.2 * score1
        - 0.5 * score2
        + rng.normal(0.0, noise_sd)
    )

    base = wild_bootstrap_fpca_projection(
        gaze,
        outcome,
        targets=gaze.subset([0, 1, 2, 3]),
        n_bootstrap=500,
        residual_components=2,
        inference_components=3,
        scaling="dimension_sd",
        multiplier="normal",
        independent_unit_column="participant_id",
        random_state=2030,
    )

The four targets are fixed before testing. Participant IDs are unique because this example uses one trajectory per participant.

## 2. Run the fixed-family test

    from eyetrajectoriespy import (
        fpca_wild_bootstrap_projection_family_test,
    )

    tests = fpca_wild_bootstrap_projection_family_test(
        base,
        null_values=0.0,
        significance_level=0.05,
        pvalue_correction="plus_one",
    )

These p-values and rejection indicators are the inferential output from version 0.19.

## 3. Diagnose finite-bootstrap precision

    from eyetrajectoriespy import (
        fpca_wild_bootstrap_family_test_monte_carlo_diagnostics,
        fpca_wild_bootstrap_monte_carlo_diagnostic_frame,
    )

    diagnostics = fpca_wild_bootstrap_family_test_monte_carlo_diagnostics(
        tests,
        confidence_level=0.95,
    )

    table = fpca_wild_bootstrap_monte_carlo_diagnostic_frame(diagnostics)
    print(table)

For each target, compare the unchanged reported adjusted p-value with the raw exceedance count, raw tail fraction, MCSE, exact interval, and adjusted precision status.

## 4. Visualize the precision

    from eyetrajectoriespy import (
        plot_fpca_wild_bootstrap_monte_carlo_diagnostics,
    )

    ax = plot_fpca_wild_bootstrap_monte_carlo_diagnostics(
        diagnostics,
        show_targetwise=True,
    )

The vertical intervals are Monte Carlo precision intervals around bootstrap exceedance probabilities. They are not scientific confidence intervals for target projections.

## 5. Generate reporting text

    from eyetrajectoriespy import (
        fpca_wild_bootstrap_monte_carlo_reporting_text,
    )

    print(fpca_wild_bootstrap_monte_carlo_reporting_text(diagnostics))

## Interpretation

Suppose a target has a plus-one adjusted p-value just above .05 and its exact binomial interval spans .05. The appropriate interpretation is that the finite bootstrap run has limited Monte Carlo precision near the decision threshold.

Do not reinterpret the interval as evidence that the scientific null is true or false with the stated confidence. Do not report the raw r/B value as though it replaced the configured plus-one p-value.

## When to increase B

A sensitivity flag can justify a preplanned larger bootstrap run or a transparently reported precision analysis.

Version 0.20 does not provide a sequential stopping rule. Repeatedly increasing B until a desired significance decision appears is outside the method contract.

## Limitations

This diagnostic does not repair repeated-participant dependence, adaptive target-family selection, k/g/h selection uncertainty, FPCA basis-estimation uncertainty, the null-enforcement boundary of the 0.19 test, the absence of a universal strong-FWER claim for arbitrary subset nulls, or future-outcome prediction uncertainty.
