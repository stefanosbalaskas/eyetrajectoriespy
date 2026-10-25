"""Independent synthetic contract tests for optional table interoperability."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd


def load():
    path = Path(__file__).resolve().parents[1] / "examples/interop_tabular_handoff.py"
    spec = importlib.util.spec_from_file_location("interop_tabular_handoff", path)
    module = importlib.util.module_from_spec(spec)
    import sys
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def main() -> None:
    e = load()
    data = pd.DataFrame({
        "person": ["001", "001", "002", "002"],
        "trial": ["A", "A", "A", "A"],
        "seconds": [0.0, 0.1, 0.0, 0.1],
        "horizontal": [0.1, 0.2, 0.3, 0.4],
        "vertical": [0.6, 0.7, 0.8, 0.9],
        "condition": ["C", "C", "D", "D"],
    })
    mapping = dict(participant_id="person", trial_id="trial", time_s="seconds",
                   x="horizontal", y="vertical")
    def build(df=data):
        return e.canonicalize_gaze_table(
            df, column_map=mapping, time_unit="s", coordinate_system="normalized",
            metadata_columns=("condition",),
        )
    canonical, audit = build()
    assert list(canonical.columns) == ["participant_id", "trial_id", "time_s", "x", "y", "condition"]
    assert audit.common_grid and audit.complete_xy
    assert audit.participants == 2 and audit.curves == 2
    assert list(canonical["participant_id"].unique()) == ["001", "002"]
    assert canonical.equals(canonical.copy(deep=True))
    def refuses(frame: pd.DataFrame, expected: str):
        try:
            build(frame)
        except ValueError as exc:
            assert expected in str(exc), (expected, str(exc))
        else:
            raise AssertionError("Expected fail-closed rejection: " + expected)
    duplicate = data.copy(); duplicate.loc[1, "seconds"] = 0.0
    refuses(duplicate, "Duplicate")
    backwards = data.copy(); backwards.loc[1, "seconds"] = -1.0
    refuses(backwards, "Nonincreasing")
    out_of_bounds = data.copy(); out_of_bounds.loc[0, "horizontal"] = 2.0
    refuses(out_of_bounds, "outside")
    conflicting_metadata = data.copy(); conflicting_metadata.loc[1, "condition"] = "other"
    refuses(conflicting_metadata, "Metadata")
    missing_both = data.copy(); missing_both.loc[1, ["horizontal", "vertical"]] = np.nan
    refuses(missing_both, "either coordinate")
    sparse = data.copy(); sparse.loc[1, "horizontal"] = np.nan
    _, support = build(sparse)
    assert support.complete_xy is False
    try:
        e.to_dense_trajectory_set(*build(sparse))
    except ValueError as exc:
        assert "Refusing" in str(exc)
    else:
        raise AssertionError("Missing x cannot be sent to dense importer.")
    irregular = data.copy(); irregular.loc[3, "seconds"] = 0.2
    _, support = build(irregular)
    assert support.common_grid is False
    try:
        e.to_dense_trajectory_set(*build(irregular))
    except ValueError as exc:
        assert "Refusing" in str(exc)
    else:
        raise AssertionError("Unequal grids cannot be coerced to dense.")
    try:
        e.canonicalize_gaze_table(data, column_map=mapping, time_unit="guess",
                                  coordinate_system="normalized")
    except ValueError:
        pass
    else:
        raise AssertionError("Unspecified units should refuse.")
    try:
        import polars as pl
    except ImportError:
        print("SKIP optional Polars round-trip: install polars and pyarrow")
    else:
        alternate, polars_audit = build(pl.from_pandas(data))
        assert polars_audit == audit
        pd.testing.assert_frame_equal(canonical, alternate, check_dtype=False)
        print("PASS optional Polars-to-pandas parity")
    print("PASS tabular interoperability boundary and rejection tests")


if __name__ == "__main__":
    main()
