"""Read-only Eye-Tracking-BIDS metadata and bounded physio TSV.GZ inspection.

Repository example, NOT the official BIDS validator or a BIDS data importer.
Conventions checked here follow the 2026 Eye-Tracking-BIDS / BEP020 paper.
Never infers physical screen units, repairs timestamps, or writes to source.
"""
from __future__ import annotations

import csv
import gzip
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

MAX_JSON_BYTES = 256_000
MAX_ROWS_INSPECTED = 10_000
EXPECTED_FIRST = ("timestamp", "x_coordinate", "y_coordinate")
RECORDED_EYES = {"left", "right", "cyclopean"}


@dataclass(frozen=True)
class EyeTrackingSidecarAudit:
    sidecar_path: str
    physio_type: str
    columns: tuple[str, ...]
    sampling_frequency_hz: float
    start_time_s: float
    recorded_eye: str
    sample_coordinate_system: str
    coordinate_units: tuple[str | None, str | None]
    inspected_tsv_rows: int | None
    inspection_truncated: bool
    warnings: tuple[str, ...]
    caveat: str = (
        "Read-only metadata/shape inspection only; NOT complete BIDS "
        "conformance, clock calibration, acquisition QC or inference."
    )


def _require_nonempty_string(source: dict[str, Any], name: str) -> str:
    val = source.get(name)
    if not isinstance(val, str) or not val.strip():
        raise ValueError(f"Missing/invalid required metadata field: {name}")
    return val.strip()


def inspect_sidecar(
    json_path: str | Path,
    *,
    physio_path: str | Path | None = None,
    max_rows: int = MAX_ROWS_INSPECTED,
) -> EyeTrackingSidecarAudit:
    path = Path(json_path)
    if not path.is_file() or path.suffix != ".json" or not path.name.endswith("_physio.json"):
        raise ValueError("Expected an existing eye-tracking *_physio.json sidecar.")
    if path.stat().st_size > MAX_JSON_BYTES:
        raise ValueError("Sidecar exceeds bounded JSON inspection limit.")
    with path.open("r", encoding="utf-8") as handle:
        obj = json.load(handle)
    if not isinstance(obj, dict):
        raise ValueError("BIDS physio sidecar must be a JSON object.")
    typ = _require_nonempty_string(obj, "PhysioType")
    if typ != "eyetrack":
        raise ValueError("PhysioType must be eyetrack for this narrow inspector.")
    columns = obj.get("Columns")
    if not isinstance(columns, list) or not columns or not all(isinstance(c, str) and c.strip() for c in columns):
        raise ValueError("Columns must be an ordered list of nonempty column names.")
    if len(set(columns)) != len(columns):
        raise ValueError("Columns names must be unique.")
    if tuple(columns[:3]) != EXPECTED_FIRST:
        raise ValueError("Expected the first columns timestamp, x_coordinate, y_coordinate in this restricted profile.")
    hz = obj.get("SamplingFrequency")
    if isinstance(hz, bool) or not isinstance(hz, (float, int)) or not math.isfinite(hz) or hz <= 0:
        raise ValueError("SamplingFrequency must be finite and strictly positive (Hz).")
    start = obj.get("StartTime")
    if isinstance(start, bool) or not isinstance(start, (float, int)) or not math.isfinite(start):
        raise ValueError("StartTime must be finite seconds relative to acquisition.")
    eye = _require_nonempty_string(obj, "RecordedEye")
    if eye not in RECORDED_EYES:
        raise ValueError("RecordedEye must be left, right or cyclopean.")
    system = _require_nonempty_string(obj, "SampleCoordinateSystem")
    warnings: list[str] = []
    units: list[str | None] = []
    for coord in ("x_coordinate", "y_coordinate"):
        meta = obj.get(coord, {})
        if not isinstance(meta, dict):
            raise ValueError(f"{coord} metadata must be an object if provided.")
        unit = meta.get("Units")
        if unit is not None and (not isinstance(unit, str) or not unit.strip()):
            raise ValueError(f"{coord}.Units must be a nonempty string when present.")
        if unit is None:
            warnings.append(f"{coord}.Units not declared: no coordinate conversion is possible.")
        units.append(unit)
    if units[0] is not None and units[1] is not None and units[0] != units[1]:
        warnings.append("Different x/y unit strings; investigate before numerical analysis.")
    if not 1 <= max_rows <= MAX_ROWS_INSPECTED:
        raise ValueError(f"max_rows must be between 1 and {MAX_ROWS_INSPECTED}.")
    n: int | None = None
    truncated = False
    if physio_path is not None:
        tsv = Path(physio_path)
        if not tsv.is_file() or not tsv.name.endswith("_physio.tsv.gz"):
            raise ValueError("Physio input must be an existing *_physio.tsv.gz file.")
        # BIDS physio files are headerless: Columns is stored in the JSON.
        n = 0
        with gzip.open(tsv, "rt", encoding="utf-8", newline="") as handle:
            for row in csv.reader(handle, delimiter="\t"):
                if not row:
                    continue
                if len(row) != len(columns):
                    raise ValueError(f"TSVGZ row {n + 1} has {len(row)} fields; Columns declares {len(columns)}.")
                n += 1
                if n >= max_rows:
                    truncated = True
                    break
        if n == 0:
            raise ValueError("No physical rows in physio.tsv.gz.")
        if truncated:
            warnings.append(
                f"Only the first {max_rows} rows were inspected. This is not a complete stream or missingness audit."
            )
    return EyeTrackingSidecarAudit(
        sidecar_path=path.name, physio_type=typ, columns=tuple(columns),
        sampling_frequency_hz=float(hz), start_time_s=float(start),
        recorded_eye=eye, sample_coordinate_system=system,
        coordinate_units=(units[0], units[1]),
        inspected_tsv_rows=n, inspection_truncated=truncated,
        warnings=tuple(warnings),
    )


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sidecar", help="Existing *_physio.json (read-only)")
    parser.add_argument("--tsv-gz", default=None, help="Optional corresponding *_physio.tsv.gz for bounded shape checks")
    args = parser.parse_args()
    print(json.dumps(asdict(inspect_sidecar(args.sidecar, physio_path=args.tsv_gz)), indent=2))


if __name__ == "__main__":
    main()
