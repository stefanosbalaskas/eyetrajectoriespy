"""Explicit irregular-grid resampling with long-gap protection."""
import numpy as np
import pandas as pd
from eyetrajectoriespy import from_irregular_long_dataframe

def main() -> None:
    data = pd.DataFrame({
        "participant_id": ["P01"] * 5,
        "trial_id": [1] * 5,
        "time": [0.00, 0.10, 0.20, 0.85, 1.00],
        "x": [0.50, 0.51, 0.53, 0.78, 0.80],
        "y": [0.50, 0.48, 0.46, 0.30, 0.31],
    })
    gaze = from_irregular_long_dataframe(
        data,
        curve_columns=["participant_id", "trial_id"],
        time_column="time",
        grid=np.linspace(0, 1, 21),
        max_gap=0.25,
        coordinate_system="normalized",
        time_unit="s",
    )
    print("missing grid samples retained:", int(np.isnan(gaze.values).any(axis=2).sum()))

if __name__ == "__main__":
    main()
