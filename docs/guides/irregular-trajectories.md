# Native irregular trajectories

Eye trackers and synchronized experiment logs do not always produce identical sample times for every trial. A common grid is useful for grid-based FPCA, but it should be an **explicit analytical projection**, not an undocumented import side effect.

## Keep the original sampling first

Use <code>from_irregular_long_dataframe_native()</code> to retain each curve's own time vector.

    irregular = from_irregular_long_dataframe_native(
        samples,
        curve_columns=["participant_id", "trial_id"],
        time_column="time_s",
        coordinate_system="normalized",
        time_unit="s",
    )

The resulting <code>IrregularTrajectorySet</code> keeps one time vector and one value matrix per curve.

## Inspect sampling before projection

    summary = irregular_sampling_summary(irregular)

Report at least the number of samples, observed time span, median inter-sample interval, maximum interval, and missing-value fraction.

## Choose the target domain

<code>make_common_grid()</code> supports two explicit domains.

**Overlap** uses only time observed by every curve. It reduces edge missingness but may shorten the scientific observation window.

**Union** covers the full observed range. It preserves the broadest time window but necessarily leaves some curves missing at the edges.

Neither is universally preferable.

## Protect long unobserved intervals

    grid = make_common_grid(irregular, n_time=121, domain="overlap")
    gaze = resample_irregular_to_grid(
        irregular,
        grid,
        method="linear",
        max_gap=0.10,
    )

The <code>max_gap</code> argument prevents interpolation through long tracker-loss intervals.

!!! warning
    A visually smooth interpolation through an unobserved interval is not evidence that the eye followed that path.

## When not to project immediately

Keep the irregular object when you still need to:

- audit sampling irregularity;
- compare candidate common grids;
- quantify how many samples would be interpolated;
- use a specialist sparse/irregular FDA backend;
- preserve original time support for reproducibility.

Current general FDA ecosystems support irregular functional representations directly, which is one reason this package now preserves the native representation before any grid conversion.


## When the data are genuinely sparse

A native irregular object does not force you to create a common grid.

If observation counts are low enough that interpolation would construct much of the analyzed curve, move to the [sparse PACE FPCA workflow](sparse-irregular-fpca.md) instead of increasing grid density.

The sparse route keeps each curve's observed times, analyzes one named functional dimension, and delegates covariance UFPCA plus conditional-expectation scores to FDApy.
