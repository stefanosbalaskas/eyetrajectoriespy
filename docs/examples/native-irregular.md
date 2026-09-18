# Worked example: native irregular sampling

This workflow separates **representation** from **projection**.

## 1. Keep the original grids

    irregular = from_irregular_long_dataframe_native(
        samples,
        curve_columns=["participant_id", "trial_id"],
        time_column="time_s",
        value_columns=["x", "y"],
        coordinate_system="normalized",
        time_unit="s",
    )

## 2. Audit sampling

    irregular_sampling_summary(irregular)

A large maximum interval may reflect a blink, dropped packets, tracker loss, or another acquisition issue. The package does not guess which.

## 3. Define the common interval

    grid = make_common_grid(
        irregular,
        n_time=121,
        domain="overlap",
    )

## 4. Project with a maximum permitted gap

    gaze = resample_irregular_to_grid(
        irregular,
        grid,
        method="linear",
        max_gap=0.10,
    )

If unresolved missing values remain, grid FPCA will refuse them. That failure is intentional: the analyst must decide how the study treats those trials.
