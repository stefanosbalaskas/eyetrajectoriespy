"""Negative tests for fail-closed final benchmark provenance."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import pytest
import importlib.util
import hashlib

_SPEC = importlib.util.spec_from_file_location(
    "record_final_one_dot_two_performance",
    Path(__file__).resolve().parents[1] / "scripts" / "record_final_one_dot_two_performance.py",
)
assert _SPEC is not None and _SPEC.loader is not None
_module = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_module)
convert = _module.convert

ROOT = Path(__file__).resolve().parents[1]

def historical():
    return json.loads((ROOT / "validation/performance/PERFORMANCE_ENVELOPE-1.2.0rc2.json").read_text())

def test_prerelease_data_cannot_be_misrepresented_as_final_performance():
    prior=historical()
    assert prior["package_version"]=="1.2.0rc2"
    raw={
        "schema_version":1,"profile":prior["profile"],
        "benchmark_kind":prior["benchmark_kind"],
        "comparative_benchmark":False,
        "environment":prior["environment"],
        "results":[],
    }
    with pytest.raises(RuntimeError,match="literal final"):
        convert(raw,original_sha256="0"*64)

def test_no_benchmark_measurements_are_fabricated():
    prior=historical()
    raw={
        "schema_version":1,"profile":"ci-qualification",
        "benchmark_kind":"single-package performance envelope",
        "comparative_benchmark":False,
        "environment":dict(prior["environment"]),
        "results":[],
    }
    raw["environment"]["packages"]=dict(raw["environment"]["packages"])
    raw["environment"]["packages"]["eyetrajectoriespy"]="1.2.0"
    with pytest.raises(RuntimeError,match="six-workload"):
        convert(raw,original_sha256="a"*64)

def test_archived_original_final_benchmark_matches_sha_and_recorded_measurements():
    raw_path = ROOT / "validation/performance/raw/PERFORMANCE_ENVELOPE-1.2.0-40121535785.json"
    # Git's text checkout can convert LF to CRLF on Windows. Restore the
    # original artifact's LF byte convention before checking its true hash.
    data = raw_path.read_bytes().replace(b"\r\n", b"\n")
    ledger = json.loads((ROOT / "PERFORMANCE_ENVELOPE.json").read_text())
    assert hashlib.sha256(data).hexdigest() == ledger["raw_artifact_member_sha256"]
    assert ledger["package_version"] == "1.2.0"
    assert ledger["qualification_run_id"] == 40121535785
    converted = convert(json.loads(data), original_sha256=hashlib.sha256(data).hexdigest())
    assert converted["results"] == ledger["results"]
    assert converted["environment"] == ledger["environment"]
    assert converted["qualification_commit"] == ledger["qualification_commit"]
