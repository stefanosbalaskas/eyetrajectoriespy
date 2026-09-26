"""Portable scientific-result snapshots and environment capture.

The portable format deliberately excludes backend-native fitted objects. It
stores scientific arrays, identifiers, specifications, units, diagnostics and
provenance in an explicit JSON + NPZ bundle that can be audited independently
of pickle compatibility.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import datetime, timezone
from hashlib import sha256
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from typing import Any, Mapping

import numpy as np
import pandas as pd


PORTABLE_RESULT_SCHEMA_VERSION = 1
PORTABLE_RESULT_FORMAT = "eyetrajectoriespy-portable-scientific-result"
ENVIRONMENT_SCHEMA_VERSION = 1

_CORE_DEPENDENCIES = (
    "numpy",
    "pandas",
    "scipy",
    "scikit-learn",
    "matplotlib",
    "statsmodels",
)
_OPTIONAL_BACKENDS = (
    "scikit-fda",
    "FDApy",
    "fdasrsf",
)


@dataclass(frozen=True)
class PortableScientificResultSnapshot:
    """Loaded portable scientific snapshot.

    This is intentionally not a reconstruction of the original fitted backend
    object. The payload contains portable scientific state; nonportable_fields
    records excluded opaque/backend-native fields explicitly.
    """

    result_type: str
    source_package_version: str
    loaded_package_version: str
    payload: Any
    environment: Mapping[str, Any] | None
    units: Mapping[str, Any]
    nonportable_fields: tuple[str, ...]
    manifest: Mapping[str, Any]

    @property
    def package_version_match(self) -> bool:
        return self.source_package_version == self.loaded_package_version


def _package_version() -> str:
    try:
        return importlib.metadata.version("eyetrajectoriespy")
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


def _distribution_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _git_commit() -> str | None:
    for variable in ("GITHUB_SHA", "EYETRAJECTORIESPY_GIT_COMMIT"):
        value = os.environ.get(variable)
        if value:
            return value
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    commit = completed.stdout.strip()
    return commit or None


def capture_environment() -> dict[str, Any]:
    """Capture the software/platform environment relevant to reproducibility."""

    return {
        "schema_version": ENVIRONMENT_SCHEMA_VERSION,
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "package": {
            "name": "eyetrajectoriespy",
            "version": _package_version(),
            "git_commit": _git_commit(),
        },
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "executable": sys.executable,
        },
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "platform": platform.platform(),
            "processor": platform.processor() or None,
            "logical_cpu_count": os.cpu_count(),
        },
        "dependencies": {
            name: _distribution_version(name)
            for name in _CORE_DEPENDENCIES
        },
        "optional_backends": {
            name: _distribution_version(name)
            for name in _OPTIONAL_BACKENDS
        },
        "numerical_thread_environment": {
            name: os.environ.get(name)
            for name in (
                "OMP_NUM_THREADS",
                "OPENBLAS_NUM_THREADS",
                "MKL_NUM_THREADS",
                "NUMEXPR_NUM_THREADS",
            )
        },
    }


class _PortableEncoder:
    def __init__(self) -> None:
        self.arrays: dict[str, np.ndarray] = {}
        self.nonportable_fields: list[str] = []
        self._array_counter = 0

    def _array_key(self) -> str:
        key = f"array_{self._array_counter:05d}"
        self._array_counter += 1
        return key

    def encode(self, value: Any, path: str) -> Any:
        if value is None or isinstance(value, (str, bool, int, float)):
            return value
        if isinstance(value, np.generic):
            return self.encode(value.item(), path)
        if isinstance(value, Path):
            return {
                "__portable_type__": "path",
                "value": str(value),
            }
        if isinstance(value, np.ndarray):
            if value.dtype == object:
                return {
                    "__portable_type__": "object_array",
                    "shape": list(value.shape),
                    "items": self.encode(value.tolist(), path),
                }
            key = self._array_key()
            self.arrays[key] = np.asarray(value)
            return {
                "__portable_type__": "ndarray",
                "key": key,
                "dtype": str(value.dtype),
                "shape": list(value.shape),
            }
        if isinstance(value, pd.DataFrame):
            return {
                "__portable_type__": "dataframe",
                "columns": self.encode(list(value.columns), f"{path}.columns"),
                "index": self.encode(list(value.index), f"{path}.index"),
                "data": [
                    self.encode(
                        value.iloc[:, column_index].to_numpy(),
                        f"{path}.column[{column_index}]",
                    )
                    for column_index in range(value.shape[1])
                ],
            }
        if isinstance(value, pd.Series):
            return {
                "__portable_type__": "series",
                "name": self.encode(value.name, f"{path}.name"),
                "index": self.encode(list(value.index), f"{path}.index"),
                "data": self.encode(value.to_numpy(), f"{path}.data"),
            }
        if is_dataclass(value) and not isinstance(value, type):
            encoded_fields = {}
            for field in fields(value):
                field_path = f"{path}.{field.name}"
                encoded_fields[field.name] = self.encode(
                    getattr(value, field.name),
                    field_path,
                )
            return {
                "__portable_type__": "dataclass",
                "python_type": (
                    f"{value.__class__.__module__}.{value.__class__.__qualname__}"
                ),
                "fields": encoded_fields,
            }
        if isinstance(value, Mapping):
            entries = []
            for key, item in value.items():
                key_path = f"{path}.<key>"
                entries.append(
                    [
                        self.encode(key, key_path),
                        self.encode(item, f"{path}[{key!r}]"),
                    ]
                )
            return {
                "__portable_type__": "mapping",
                "entries": entries,
            }
        if isinstance(value, tuple):
            return {
                "__portable_type__": "tuple",
                "items": [
                    self.encode(item, f"{path}[{index}]")
                    for index, item in enumerate(value)
                ],
            }
        if isinstance(value, list):
            return [
                self.encode(item, f"{path}[{index}]")
                for index, item in enumerate(value)
            ]

        self.nonportable_fields.append(path)
        return {
            "__portable_type__": "nonportable",
            "python_type": (
                f"{value.__class__.__module__}.{value.__class__.__qualname__}"
            ),
            "representation": repr(value)[:500],
        }


def _decode(value: Any, arrays: Mapping[str, np.ndarray]) -> Any:
    if isinstance(value, list):
        return [_decode(item, arrays) for item in value]
    if not isinstance(value, dict):
        return value

    marker = value.get("__portable_type__")
    if marker is None:
        return {
            key: _decode(item, arrays)
            for key, item in value.items()
        }
    if marker == "ndarray":
        return np.asarray(arrays[value["key"]]).copy()
    if marker == "object_array":
        decoded = _decode(value["items"], arrays)
        return np.asarray(decoded, dtype=object).reshape(value["shape"])
    if marker == "path":
        return Path(value["value"])
    if marker == "tuple":
        return tuple(_decode(item, arrays) for item in value["items"])
    if marker == "mapping":
        return {
            _decode(key, arrays): _decode(item, arrays)
            for key, item in value["entries"]
        }
    if marker == "dataframe":
        columns = _decode(value["columns"], arrays)
        index = _decode(value["index"], arrays)
        data = {
            column: _decode(encoded, arrays)
            for column, encoded in zip(
                columns,
                value["data"],
                strict=True,
            )
        }
        return pd.DataFrame(data, index=index)
    if marker == "series":
        return pd.Series(
            _decode(value["data"], arrays),
            index=_decode(value["index"], arrays),
            name=_decode(value["name"], arrays),
        )
    if marker == "dataclass":
        return {
            "__python_type__": value["python_type"],
            **{
                key: _decode(item, arrays)
                for key, item in value["fields"].items()
            },
        }
    if marker == "nonportable":
        return {
            "__nonportable__": True,
            "python_type": value["python_type"],
            "representation": value["representation"],
        }
    raise ValueError(f"Unknown portable payload marker {marker!r}")


def _sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _extract_units(result: Any) -> dict[str, Any]:
    units = {}
    for name in (
        "time_unit",
        "coordinate_system",
        "exposure_units",
        "response_unit",
    ):
        if hasattr(result, name):
            value = getattr(result, name)
            if value is not None:
                units[name] = value
    return units


def export_portable_result(
    result: Any,
    directory: str | Path,
    *,
    include_environment: bool = True,
    overwrite: bool = False,
) -> Path:
    """Export scientific result state as explicit JSON + NPZ.

    The bundle is a portable snapshot, not a pickle. Unsupported backend
    objects are represented by an explicit nonportable marker and listed in the
    manifest instead of being silently dropped.
    """

    if not is_dataclass(result) or isinstance(result, type):
        raise TypeError("result must be a dataclass-based scientific result object")

    destination = Path(directory)
    if destination.exists() and any(destination.iterdir()):
        if not overwrite:
            raise FileExistsError(
                f"portable result directory is not empty: {destination}"
            )
        for child in destination.iterdir():
            if child.is_dir():
                raise ValueError(
                    "overwrite does not recursively remove existing directories"
                )
            child.unlink()
    destination.mkdir(parents=True, exist_ok=True)

    encoder = _PortableEncoder()
    payload = encoder.encode(result, "result")

    arrays_path = destination / "arrays.npz"
    np.savez_compressed(arrays_path, **encoder.arrays)

    package_version = _package_version()
    manifest = {
        "schema_version": PORTABLE_RESULT_SCHEMA_VERSION,
        "format": PORTABLE_RESULT_FORMAT,
        "source_package_version": package_version,
        "result_type": (
            f"{result.__class__.__module__}.{result.__class__.__qualname__}"
        ),
        "portable_scope": (
            "Scientific arrays, identifiers, specifications, units, diagnostics "
            "and provenance. Backend-native/opaque objects are not promised "
            "portable or reconstructible."
        ),
        "arrays_file": arrays_path.name,
        "arrays_sha256": _sha256(arrays_path),
        "units": _extract_units(result),
        "nonportable_fields": sorted(set(encoder.nonportable_fields)),
        "environment": capture_environment() if include_environment else None,
        "payload": payload,
    }
    manifest_path = destination / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return destination


def load_portable_result(
    directory: str | Path,
) -> PortableScientificResultSnapshot:
    """Load and integrity-check a portable scientific snapshot."""

    source = Path(directory)
    manifest_path = source / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"portable result manifest not found: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("format") != PORTABLE_RESULT_FORMAT:
        raise ValueError("not an eyetrajectoriespy portable scientific result")
    schema_version = manifest.get("schema_version")
    if schema_version != PORTABLE_RESULT_SCHEMA_VERSION:
        raise ValueError(
            "unsupported portable result schema version "
            f"{schema_version!r}; supported={PORTABLE_RESULT_SCHEMA_VERSION}"
        )

    arrays_path = source / manifest["arrays_file"]
    if not arrays_path.is_file():
        raise FileNotFoundError(f"portable result array payload not found: {arrays_path}")
    actual_hash = _sha256(arrays_path)
    if actual_hash != manifest["arrays_sha256"]:
        raise ValueError("portable result array checksum mismatch")

    with np.load(arrays_path, allow_pickle=False) as archive:
        arrays = {
            key: np.asarray(archive[key])
            for key in archive.files
        }
    payload = _decode(manifest["payload"], arrays)

    return PortableScientificResultSnapshot(
        result_type=str(manifest["result_type"]),
        source_package_version=str(manifest["source_package_version"]),
        loaded_package_version=_package_version(),
        payload=payload,
        environment=manifest.get("environment"),
        units=dict(manifest.get("units", {})),
        nonportable_fields=tuple(manifest.get("nonportable_fields", ())),
        manifest=manifest,
    )
