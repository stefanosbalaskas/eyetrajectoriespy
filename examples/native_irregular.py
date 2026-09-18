"""Keep irregular gaze grids native until an explicit projection is chosen."""

import numpy as np
import pandas as pd

from eyetrajectoriespy import (
    from_irregular_long_dataframe_native,
    irregular_sampling_summary,
    make_common_grid,
    resample_irregular_to_grid,
)


def main() -> None:
    data = pd.DataFrame(
        {
            "participant_id": ["P01"] * 4 + ["P02"] * 5,
            "trial_id": [1] * 9,
            "time_s": [0.00, 0.12, 0.26, 0.95, 0.05, 0.18, 0.31, 0.62, 1.00],
            "x": [0.50, 0.52, 0.55, 0.79, 0.48, 0.50, 0.56, 0.73, 0.81],
            "y": [0.50, 0.48, 0.44, 0.31, 0.51, 0.49, 0.43, 0.34, 0.30],
        }
    )
    irregular = from_irregular_long_dataframe_native(
        data,
        curve_columns=["participant_id", "trial_id"],
        time_column="time_s",
        coordinate_system="normalized",
        time_unit="s",
    )
    print(irregular_sampling_summary(irregular).to_string(index=False))

    grid = make_common_grid(irregular, n_time=41, domain="overlap")
    projected = resample_irregular_to_grid(
        irregular,
        grid,
        max_gap=0.20,
    )
    print("projected shape:", projected.values.shape)
    print("retained missing samples:", int(np.isnan(projected.values).any(axis=2).sum()))


if __name__ == "__main__":
    main()
