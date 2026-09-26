import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import eyetrajectoriespy as et


def _fpca_result():
    return et.FPCAResult(
        mean=np.array([[0.1], [0.2], [0.3]]),
        components=np.array([[[1.0], [0.0], [-1.0]]]),
        scores=np.array([[0.5], [-0.5]]),
        explained_variance=np.array([1.25]),
        explained_variance_ratio=np.array([1.0]),
        time=np.array([0.0, 0.5, 1.0]),
        dimension_names=("signal",),
        coordinate_system="unknown",
        time_unit="s",
        curve_ids=("c1", "c2"),
        weights=np.array([0.25, 0.5, 0.25]),
        scale=np.array([1.0]),
        provenance={
            "operation": "portable_snapshot_test",
            "preprocessing": {
                "interpolation": False,
                "smoothing": False,
            },
        },
        model=object(),
    )


def test_environment_capture_records_reproducibility_context():
    environment = et.capture_environment()

    assert environment["schema_version"] == 1
    assert environment["package"]["name"] == "eyetrajectoriespy"
    assert environment["package"]["version"] == et.__version__
    assert environment["python"]["version"]
    assert environment["platform"]["system"]
    assert environment["dependencies"]["numpy"]
    assert environment["dependencies"]["statsmodels"]
    assert set(environment["optional_backends"]) == {
        "scikit-fda",
        "FDApy",
        "fdasrsf",
    }


def test_portable_result_round_trip_preserves_scientific_state(tmp_path):
    result = _fpca_result()
    destination = tmp_path / "fpca-portable"

    exported = et.export_portable_result(result, destination)
    assert exported == destination
    assert (destination / "manifest.json").is_file()
    assert (destination / "arrays.npz").is_file()

    snapshot = et.load_portable_result(destination)
    assert snapshot.result_type.endswith(".FPCAResult")
    assert snapshot.package_version_match is True
    assert snapshot.units == {
        "coordinate_system": "unknown",
        "time_unit": "s",
    }
    assert snapshot.nonportable_fields == ("result.model",)

    payload = snapshot.payload
    assert payload["__python_type__"].endswith(".FPCAResult")
    np.testing.assert_array_equal(payload["mean"], result.mean)
    np.testing.assert_array_equal(payload["components"], result.components)
    np.testing.assert_array_equal(payload["scores"], result.scores)
    np.testing.assert_array_equal(
        payload["explained_variance"],
        result.explained_variance,
    )
    assert payload["dimension_names"] == ("signal",)
    assert payload["curve_ids"] == ("c1", "c2")
    assert payload["provenance"] == dict(result.provenance)
    assert payload["model"]["__nonportable__"] is True


def test_portable_result_round_trip_preserves_dataframe_metadata(tmp_path):
    trajectories = et.TrajectorySet(
        time=np.array([0.0, 1.0]),
        values=np.array(
            [
                [[0.1], [0.2]],
                [[0.3], [0.4]],
            ]
        ),
        curve_ids=("a", "b"),
        dimension_names=("x",),
        metadata=pd.DataFrame(
            {
                "participant_id": ["P01", "P02"],
                "trial": [1, 2],
            }
        ),
        coordinate_system="normalized",
        time_unit="s",
        provenance={"source": "synthetic audit fixture"},
    )
    destination = tmp_path / "trajectory-portable"
    et.export_portable_result(
        trajectories,
        destination,
        include_environment=False,
    )

    snapshot = et.load_portable_result(destination)
    payload = snapshot.payload
    assert snapshot.environment is None
    assert snapshot.units == {
        "coordinate_system": "normalized",
        "time_unit": "s",
    }
    pd.testing.assert_frame_equal(
        payload["metadata"],
        trajectories.metadata,
        check_names=False,
    )
    np.testing.assert_array_equal(payload["time"], trajectories.time)
    np.testing.assert_array_equal(payload["values"], trajectories.values)


def test_portable_result_checksum_detects_array_tampering(tmp_path):
    destination = tmp_path / "tampered"
    et.export_portable_result(_fpca_result(), destination)

    arrays_path = destination / "arrays.npz"
    arrays_path.write_bytes(arrays_path.read_bytes() + b"tamper")
    with pytest.raises(ValueError, match="checksum mismatch"):
        et.load_portable_result(destination)


def test_portable_result_rejects_unknown_future_schema(tmp_path):
    destination = tmp_path / "future"
    et.export_portable_result(_fpca_result(), destination)
    manifest_path = destination / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["schema_version"] = 999
    manifest_path.write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unsupported portable result schema"):
        et.load_portable_result(destination)


def test_portable_result_does_not_overwrite_nonempty_directory(tmp_path):
    destination = tmp_path / "existing"
    destination.mkdir()
    (destination / "keep.txt").write_text("keep", encoding="utf-8")

    with pytest.raises(FileExistsError, match="not empty"):
        et.export_portable_result(_fpca_result(), destination)


def test_portable_result_requires_dataclass_result(tmp_path):
    with pytest.raises(TypeError, match="dataclass-based"):
        et.export_portable_result(
            {"not": "a scientific result"},
            tmp_path / "bad",
        )
