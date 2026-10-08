# Input schemas and preparation

These CSVs are **minimal invented structural examples**, *not actual observations*. They are designed to make participant/trial identity, timestamp units, coordinate semantics and missingness visible before any model is fitted.

| Observation contract | Downloadable small example | Important distinction |
|---|---|---|
| Dense common grid | [common-grid.csv](../data-schemas/common-grid.csv) | Same genuinely measured timestamps across curves; no automatic gap filling |
| Paired sparse gaze | [paired-sparse.csv](../data-schemas/paired-sparse.csv) | Both x and y observed at each retained native timestamp |
| Asynchronous sparse gaze | [asynchronous-sparse.csv](../data-schemas/asynchronous-sparse.csv) | x and y may have different sampled times; missing cells must remain explicit |
| Repeated participant trials | [repeated-trials.csv](../data-schemas/repeated-trials.csv) | Stable participant cluster and separate trial key; preserve trial-varying condition |

**Mandatory decisions:** coordinate system (pixels, normalized screen fraction, degrees); time unit (seconds, milliseconds, normalized 0–1); source time origin; blink/invalid flags; whether device software already smoothed or interpolated; whether rows represent raw points or fixations; and whether repeated trials share participants. A missing coordinate is *not* gaze coordinate zero. The supplied rows are tiny schema illustrations, **not full valid statistical datasets**.

## Dense tabular input

```python
import pandas as pd
from eyetrajectoriespy import from_long_dataframe, summarise_trajectory_set
df = pd.read_csv("docs/data-schemas/common-grid.csv")
gaze = from_long_dataframe(
    df, curve_columns=["participant_id", "trial_id"],
    time_column="time_s", value_columns=["x", "y"],
    metadata_columns=["condition"],
    coordinate_system="normalized", time_unit="s",
)
print(summarise_trajectory_set(gaze))
```

The constructor does **not** silently interpolate, smooth or select subjects. Validate the time grid, duplicate timestamps, provenance and missing cells upstream.

## Native sparse versus asynchronous data

For paired native sparse, construct an `IrregularTrajectorySet` from per-curve arrays with both dimensions observed on the same timestamps. For asynchronous coordinates retain separate time-masks and use the dedicated asynchronous estimator; do **not** pair by nearest-neighbour matching without a separate scientifically justified operation. See [native irregular preparation](irregular-trajectories.md) and [paired sparse MFPCA](sparse-multivariate-fpca.md).

## Repeated trials and independence

A row may be a gaze sample, a curve is usually a trial, and participants may contribute several curves. The experimental condition may vary by trial. Keep the participant/trial nesting in metadata, align predictor design on a unique `curve_id`, and choose a cluster-aware estimator where required. See [functional mixed effects](../workflows/repeated-trial-mixed-effects.md).

!!! warning "Schema files are not an importer"
    The files do not convert a Tobii, Gazepoint or EyeLink recording automatically and do not qualify device-specific sampling, synchronisation or event-classification assumptions. They only show canonical fields and the decisions that must be declared.
