"""Optional pandas/Polars handoff for a *dense, complete-grid* teaching route.

This file is an executable interoperability example, NOT a published
eyetrajectoriespy API, a device reader, an interpolation tool, or a qualified
inference procedure. It never silently guesses units, groups, or column names.

Run (from repository root):
    python examples/interop_tabular_handoff.py
Optional:
    python -m pip install polars pyarrow
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np
import pandas as pd


REQUIRED = ("participant_id", "trial_id", "time_s", "x", "y")


@dataclass(frozen=True)
class TableAudit:
    rows: int
    participants: int
    curves: int
    repeated_participants: bool
    common_grid: bool
    complete_xy: bool
    coordinate_system: str
    time_unit: str
    caveat: str = (
        "Table structure is not device QC, MNAR identification, "
        "model qualification or inferential calibration."
    )


def _pandas_copy(table: object) -> pd.DataFrame:
    if isinstance(table, pd.DataFrame):
        return table.copy(deep=True)
    # Avoid importing an optional dependency when the caller uses pandas.
    try:
        import polars as pl
    except ImportError as exc:
        raise TypeError(
            "Expected pandas.DataFrame. For Polars install polars AND pyarrow."
        ) from exc
    if isinstance(table, pl.DataFrame):
        # Polars documents this conversion; pyarrow is required by to_pandas().
        return table.to_pandas(use_pyarrow_extension_array=False)
    raise TypeError("Expected pandas.DataFrame or polars.DataFrame; no implicit file readers.")


def canonicalize_gaze_table(
    table: object,
    *,
    column_map: Mapping[str, str],
    time_unit: str,
    coordinate_system: str,
    metadata_columns: Sequence[str] = (),
) -> tuple[pd.DataFrame, TableAudit]:
    """Fail-closed structural handoff without interpolation or imputation.

    column_map keys are canonical names, values are exact source column names.
    All five required keys must be declared explicitly. No name guessing,
    sorting, interpolation, aggregation or conversion is performed.
    """
    if time_unit not in {"s", "ms", "normalized"}:
        raise ValueError("Explicit time_unit must be s, ms or normalized.")
    if coordinate_system not in {"normalized", "pixels", "degrees"}:
        raise ValueError("Explicit coordinate_system must be normalized, pixels or degrees.")
    if set(column_map) != set(REQUIRED):
        raise ValueError("column_map must explicitly map exactly " + ", ".join(REQUIRED))
    values = list(column_map.values())
    if len(set(values)) != len(values):
        raise ValueError("Different canonical columns cannot share a source column.")
    frame = _pandas_copy(table)
    if not frame.columns.is_unique:
        raise ValueError("Source column names must be unique.")
    extra = list(metadata_columns)
    if len(set(extra)) != len(extra) or any(col in values for col in extra):
        raise ValueError("Metadata must be unique and separate from mapped columns.")
    missing = sorted((set(values) | set(extra)) - set(frame.columns))
    if missing:
        raise ValueError("Missing source columns: " + ", ".join(missing))
    out = frame.loc[:, values + extra].copy(deep=True)
    out.columns = list(REQUIRED) + extra
    if len(out) == 0:
        raise ValueError("No gaze rows provided.")
    for col in ("participant_id", "trial_id"):
        if out[col].isna().any() or out[col].astype("string").str.strip().eq("").any():
            raise ValueError(col + " must be present for every row.")
        out[col] = out[col].astype(str)
    for col in ("time_s", "x", "y"):
        try:
            out[col] = pd.to_numeric(out[col], errors="raise").astype(float)
        except (TypeError, ValueError) as exc:
            raise ValueError(col + " contains a non-numeric value.") from exc
    if not np.isfinite(out["time_s"].to_numpy()).all():
        raise ValueError("Observed timestamps must be finite and nonmissing.")
    for col in ("x", "y"):
        arr = out[col].to_numpy()
        if np.isinf(arr).any():
            raise ValueError(col + " contains an infinite coordinate.")
        if coordinate_system == "normalized":
            finite = arr[np.isfinite(arr)]
            if ((finite < 0) | (finite > 1)).any():
                raise ValueError(col + " is outside declared [0,1] coordinates.")
    if out[["x", "y"]].isna().all(axis=1).any():
        raise ValueError("Rows without either coordinate must remain in a separately audited raw archive.")
    groups = list(out.groupby(["participant_id", "trial_id"], sort=False, dropna=False))
    grids: list[np.ndarray] = []
    for (participant, trial), g in groups:
        grid = g["time_s"].to_numpy(dtype=float)
        if len(grid) != len(np.unique(grid)):
            raise ValueError(f"Duplicate timestamps in participant={participant}, trial={trial}.")
        if np.any(np.diff(grid) <= 0):
            raise ValueError(f"Nonincreasing timestamps in participant={participant}, trial={trial}; "
                             "no automatic sorting is performed.")
        for col in extra:
            if g[col].nunique(dropna=False) > 1:
                raise ValueError(f"Metadata {col} varies within participant={participant}, trial={trial}.")
        grids.append(grid)
    common = all(np.array_equal(grid, grids[0]) for grid in grids[1:])
    complete = bool(out[["x", "y"]].notna().all().all())
    participants = out["participant_id"].nunique()
    audit = TableAudit(
        rows=len(out), participants=int(participants), curves=len(groups),
        repeated_participants=len(groups) > participants,
        common_grid=common, complete_xy=complete,
        coordinate_system=coordinate_system, time_unit=time_unit,
    )
    return out, audit


def to_dense_trajectory_set(table: pd.DataFrame, audit: TableAudit):
    """Call the existing 1.2 importer ONLY for complete, genuinely aligned x/y."""
    if not audit.complete_xy or not audit.common_grid:
        raise ValueError(
            "Refusing to manufacture a dense grid. Keep irregular and channel-specific "
            "support for the appropriate stable sparse/asynchronous methods."
        )
    if audit.time_unit not in {"s", "ms"}:
        raise ValueError("Dense importer example requires explicitly physical time units.")
    from eyetrajectoriespy import from_long_dataframe

    metadata = [col for col in table if col not in REQUIRED]
    return from_long_dataframe(
        table,
        curve_columns=["participant_id", "trial_id"],
        time_column="time_s",
        value_columns=["x", "y"],
        metadata_columns=metadata,
        coordinate_system=audit.coordinate_system,
        time_unit=audit.time_unit,
    )


def main() -> None:
    path = Path(__file__).resolve().parents[1] / "docs/data-schemas/common-grid.csv"
    # Read ID columns as strings to preserve distinctions such as 001 and 1.
    frame = pd.read_csv(path, dtype={"participant_id": str, "trial_id": str})
    mapping = {name: name for name in REQUIRED}
    canonical, audit = canonicalize_gaze_table(
        frame, column_map=mapping, time_unit="s",
        coordinate_system="normalized", metadata_columns=("condition",),
    )
    gaze = to_dense_trajectory_set(canonical, audit)
    print(asdict(audit))
    print("PASS: complete-grid tabular import", type(gaze).__name__)
    print("No interpolation, inferred independence or inferential validation performed.")


if __name__ == "__main__":
    main()
