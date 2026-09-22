# Worked example: stabilized-volatility wild-bootstrap selection

This example chooses the inference truncation h for heteroscedastic Gaussian FPCR projection inference after fixing k=g.

## Simulate independent trajectories and an outcome

    import numpy as np

    from eyetrajectoriespy import (
        fit_mfpca,
        simulate_planar_trajectories,
    )

    gaze = simulate_planar_trajectories(
        n_participants=64,
        trials_per_participant=1,
        n_time=61,
        random_state=2027,
    )

    fit = fit_mfpca(
        gaze,
        n_components=6,
        scaling="dimension_sd",
    )

    rng = np.random.default_rng(2027)
    s1 = fit.scores[:, 0]
    s2 = fit.scores[:, 1]

    noise_sd = (
        0.20
        + 0.25 * np.abs(s1)
        / max(np.std(s1, ddof=1), 1e-8)
    )

    outcome = (
        0.8
        + 1.0 * s1
        - 0.4 * s2
        + rng.normal(0.0, noise_sd)
    )

## Scan consecutive h values

    from eyetrajectoriespy import scan_wild_bootstrap_fpca_truncations

    scan = scan_wild_bootstrap_fpca_truncations(
        gaze,
        outcome,
        targets=gaze.subset([0, 1, 2]),
        candidate_components=(2, 3, 4, 5, 6),
        n_bootstrap=500,
        residual_components=2,
        scaling="dimension_sd",
        multiplier="normal",
        confidence_level=0.95,
        independent_unit_column="participant_id",
        random_state=2027,
    )

The same bootstrap pseudo-response is reused across h=2,...,6 for each replicate.

## Inspect every candidate interval

    from eyetrajectoriespy import fpca_wild_bootstrap_truncation_scan_frame

    table = fpca_wild_bootstrap_truncation_scan_frame(scan)
    print(table)

For each target × h row, inspect center and width alongside the actual interval limits.

## Apply the stabilized-volatility rule

    from eyetrajectoriespy import select_fpca_wild_bootstrap_truncation

    selected = select_fpca_wild_bootstrap_truncation(
        scan,
        width_threshold=0.15,
        center_threshold=0.10,
        stability_run=1,
    )

Here r=1 means that two consecutive transitions must satisfy both stability conditions.

The thresholds are examples in the scalar outcome's units. They are not package defaults.

## Inspect target-specific h values

    from eyetrajectoriespy import (
        fpca_wild_bootstrap_truncation_selection_frame,
    )

    print(
        fpca_wild_bootstrap_truncation_selection_frame(selected)
    )

Different targets may legitimately select different h values.

## Visualize width stabilization

    from eyetrajectoriespy import (
        plot_fpca_wild_bootstrap_truncation_scan,
    )

    plot_fpca_wild_bootstrap_truncation_scan(
        selected,
        target=0,
        metric="width",
    )

Plot the center separately:

    plot_fpca_wild_bootstrap_truncation_scan(
        selected,
        target=0,
        metric="center",
    )

## Failure case

If no candidate begins a sufficiently long stable run, the selector raises an error by default.

For exploratory inspection only:

    diagnostic = select_fpca_wild_bootstrap_truncation(
        scan,
        width_threshold=0.01,
        center_threshold=0.01,
        stability_run=2,
        on_failure="warn",
    )

Targets without a qualifying run remain unselected.

The package never fills them with max(H).

## Reporting

    from eyetrajectoriespy import (
        fpca_wild_bootstrap_truncation_reporting_text,
    )

    print(
        fpca_wild_bootstrap_truncation_reporting_text(selected)
    )

## Checklist

Report:

1. how k was chosen;
2. that g=k;
3. candidate H;
4. multiplier family and bootstrap count;
5. shared multiplier draws across h;
6. confidence level;
7. rho_w and rho_c in outcome units;
8. r;
9. selected h for each target;
10. any target that failed to stabilize.

## Next steps

- [Heteroscedastic FPCR wild bootstrap](../guides/fpcr-wild-bootstrap.md)
- [Predictive FPCA selection](../guides/predictive-component-selection.md)
- [Reporting checklist](../methods/reporting.md)
