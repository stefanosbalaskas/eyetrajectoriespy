# Worked example: conformal FPCA anomaly review

This example uses a clean reference sample, a disjoint calibration sample, and genuinely held-out target trajectories.

## Create three partitions

    import numpy as np

    from eyetrajectoriespy import simulate_planar_trajectories

    gaze = simulate_planar_trajectories(
        n_participants=42,
        trials_per_participant=1,
        n_time=51,
        random_state=2026,
    )

    proper = gaze.subset(np.arange(0, 24))
    calibration = gaze.subset(np.arange(24, 36))
    targets = gaze.subset(np.arange(36, 42))

No curve ID appears in more than one partition.

## Inject one shape anomaly for demonstration

    values = targets.values.copy()
    shape = np.where(np.arange(targets.n_time) % 2 == 0, 1.0, -1.0)
    values[0, :, 0] += 8.0 * shape
    targets = targets.with_values(values)

This synthetic distortion is used only to demonstrate truth recovery.

## Calibrate reconstruction nonconformity

    from eyetrajectoriespy import split_conformal_fpca_anomaly

    result = split_conformal_fpca_anomaly(
        proper,
        calibration,
        targets,
        n_components=3,
        scaling="dimension_sd",
        nonconformity="reconstruction_rmse",
        alpha=0.10,
    )

## Inspect p-values

    from eyetrajectoriespy import conformal_fpca_anomaly_frame

    table = conformal_fpca_anomaly_frame(result)
    print(table)

With 12 calibration curves, the p-value grid has minimum (1/13).

A target cannot receive a p-value below that resolution.

## Plot review evidence

    from eyetrajectoriespy import plot_conformal_fpca_anomaly

    plot_conformal_fpca_anomaly(result)

## Alternative: score-space extremeness

If the scientific anomaly is expected to lie inside the retained FPC span but have unusually large scores:

    score_result = split_conformal_fpca_anomaly(
        proper,
        calibration,
        targets,
        n_components=3,
        scaling="dimension_sd",
        nonconformity="score_mahalanobis",
        mahalanobis_covariance="robust",
        random_state=2026,
        alpha=0.10,
    )

The covariance choice is explicit.

## Reporting text

    from eyetrajectoriespy import conformal_fpca_anomaly_reporting_text

    print(conformal_fpca_anomaly_reporting_text(result))

## Interpretation checklist

Before treating a small conformal p-value as scientific anomaly evidence:

1. confirm proper-training and calibration data represent the intended inlier population;
2. confirm target preprocessing, grid, dimensions, coordinate system, and time unit match the reference;
3. report the nonconformity score and retained FPC count;
4. report calibration size and minimum attainable p-value;
5. do not treat repeated participant trials as independent merely because they are separate curves;
6. do not call review flags automatic exclusions;
7. do not claim CCV or FDR control from the 0.15 marginal p-values.

## Next steps

- [Conformal FPCA anomaly review](../guides/conformal-fpca-anomaly.md)
- [Outliers & influence](../guides/outliers-influence.md)
- [FPCA stability & validation](../guides/stability-validation.md)
- [Reporting checklist](../methods/reporting.md)
