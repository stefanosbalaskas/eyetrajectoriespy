"""Negative tests for fail-closed final benchmark provenance."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import pytest
from scripts.record_final_one_dot_two_performance import convert

ROOT = Path(__file__).resolve().parents[1]

def historical():
    return json.loads((ROOT / "PERFORMANCE_ENVELOPE.json").read_text())

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
