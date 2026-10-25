---
title: Optional pandas and Polars table bridge
description: Fail-closed tested example for explicit column mapping, units, clustering and dense observation support.
---

# pandas / Polars / Parquet handoff

This is a **runnable repository example, not a new stable 1.2.0 API**. It converts an already loaded pandas or optional Polars table with declared column names and units, and refuses to call the dense importer when support is not complete.

## Run the example and contract tests

~~~bash
python -m pip install -e .
python examples/interop_tabular_handoff.py
python scripts/validate_ecosystem_interop.py
~~~

To additionally check Polars to pandas conversion using official optional libraries:

~~~bash
python -m pip install polars pyarrow
python scripts/validate_ecosystem_interop.py
~~~

The example uses [invented structural CSV fixtures](../guides/input-schemas.md), not real gaze or independent reference calibration.

[View complete example source](https://github.com/stefanosbalaskas/eyetrajectoriespy/blob/main/examples/interop_tabular_handoff.py) · [View tests](https://github.com/stefanosbalaskas/eyetrajectoriespy/blob/main/scripts/validate_ecosystem_interop.py)

## Explicit Parquet / Polars conversion

Polars provides [read_parquet](https://docs.pola.rs/api/python/stable/reference/api/polars.read_parquet.html) and [to_pandas](https://docs.pola.rs/api/python/stable/reference/dataframe/api/polars.DataFrame.to_pandas.html). The latter requires pandas and PyArrow. Filenames and source fields must be supplied; there is no network download.

~~~python
import polars as pl
from examples.interop_tabular_handoff import (
    canonicalize_gaze_table,
    to_dense_trajectory_set,
)

frame = pl.read_parquet("my_local_gaze_samples.parquet")
canonical, audit = canonicalize_gaze_table(
    frame,
    column_map={
        "participant_id": "person",
        "trial_id": "trial",
        "time_s": "seconds",
        "x": "horizontal",
        "y": "vertical",
    },
    time_unit="s",
    coordinate_system="normalized",
    metadata_columns=("condition",),
)
print(audit)
# Refuses missing x/y or unequal observed time grids.
gaze = to_dense_trajectory_set(canonical, audit)
~~~

For input already prepared using [pymovements](https://pymovements.readthedocs.io/en/latest/), the [Gaze reference](https://pymovements.readthedocs.io/en/latest/reference/api/pymovements.Gaze.html) identifies its samples property as a **Polars dataframe**. Given an upstream Gaze instance, inspect its actual source columns and explicit units before mapping:

~~~python
sample_frame = gaze.samples  # Given a pymovements.Gaze object
# Review source column names, trial keys and coordinate semantics first.
# Then pass sample_frame to canonicalize_gaze_table(...).
~~~

Do not conflate event detections with raw gaze samples, infer that upstream preprocessing guarantees accurate timestamps, or treat numerical agreement with another estimator as calibrated frequentist inference.

## Why the example refuses some data

Dense conversion requires complete paired x/y observations at **identical recorded times across curves**. Missing, sparse or asynchronous gaze is not an error in itself; it simply needs a different mathematical representation. The example makes no hidden interpolation, sorting, aggregation, imputation or trial-level independence assumption.

[Native irregular representation](../guides/irregular-trajectories.md) · [Sparse planar MFPCA](../guides/sparse-multivariate-fpca.md) · [Reproducibility checklist](../reproducibility/checklist.md)
