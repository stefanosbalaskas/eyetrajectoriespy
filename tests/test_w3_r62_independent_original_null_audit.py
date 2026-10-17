"""Independent R62 audit: frozen denominators, integrity and p-grid tampering tests."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.audit_w3_r62_original_null_independent import (
    BLOCKS, B, SUPPORT, _wilson, audit_original
)
from scripts import run_w3_r62_independent_outer_null_bootstrap as source


def _archive(tmp_path):
    """Construct an all-refusal but structurally complete ORIGINAL-style fixture.

    Source simulator is used only to construct test fixtures; the independent
    auditor itself imports no source, model, R57 or R62 estimator code.
    """
    cases=[source.empty_case(b,s) for b in range(BLOCKS) for s in SUPPORT]
    for row in cases:
        row["bootstrap"]=[source.empty_draw(i) for i in range(B)]
    summary=source.summarize(cases)
    (tmp_path/"cases.json").write_bytes(
        (json.dumps(cases,sort_keys=True,indent=2)+"\n").encode("utf-8")
    )
    (tmp_path/"summary.json").write_bytes(
        (json.dumps(summary,sort_keys=True,indent=2)+"\n").encode("utf-8")
    )
    (tmp_path/"source-commit.txt").write_bytes(("a"*40+"\n").encode("utf-8"))
    _refresh(tmp_path)
    return tmp_path


def _refresh(root):
    (root/"SHA256SUMS").write_bytes("".join(
        hashlib.sha256((root/name).read_bytes()).hexdigest()+"  "+name+"\n"
        for name in ("cases.json","summary.json","source-commit.txt")
    ).encode("utf-8"))


def test_read_only_audit_accepts_complete_refused_source_design(tmp_path):
    folder=_archive(tmp_path)
    report=audit_original(folder)
    assert report["original_R62_independent_numerical_evidence_reproduced"]
    assert report["original_sha256_entries_verified"]==3
    assert report["independent_blocks"]==32
    assert report["paired_source_cases"]==64
    assert report["original_bootstrap_draw_slots"]==4032
    assert report["nested_model_slots"]==8192
    assert report["optimizer_start_slots"]==24576
    assert report["paired"]["paired_both_complete"]==0
    for support in SUPPORT:
        cell=report["strata"][support]
        assert cell["source_cases_with_refused_or_incomplete_bootstrap"]==32
        assert cell["bootstrap_Wilson95_complete"] is None
        assert cell["bootstrap_all_source_upper_refusals_as_rejection"]==1
    assert not report["release_authorized"]


def test_sha256_byte_tampering_and_duplicate_case_fail_closed(tmp_path):
    folder=_archive(tmp_path)
    path=folder/"cases.json"
    path.write_bytes(path.read_bytes()+b"\n")
    with pytest.raises(ValueError,match="SHA256 mismatch"):
        audit_original(folder)
    cases=json.loads(path.read_text())
    cases[1]["block"]=cases[0]["block"]
    path.write_bytes((json.dumps(cases,sort_keys=True,indent=2)+"\n").encode())
    _refresh(folder)
    with pytest.raises(ValueError,match="32 independent primitive blocks"):
        audit_original(folder)


def test_falsified_original_summary_and_release_flag_are_rejected(tmp_path):
    folder=_archive(tmp_path)
    summary=json.loads((folder/"summary.json").read_text())
    summary["strata"][SUPPORT[0]][
        "source_cases_with_refused_or_incomplete_bootstrap"]=31
    (folder/"summary.json").write_bytes(
        (json.dumps(summary,sort_keys=True,indent=2)+"\n").encode()
    )
    _refresh(folder)
    with pytest.raises(ValueError,match="source summary count mismatch"):
        audit_original(folder)
    summary["strata"][SUPPORT[0]][
        "source_cases_with_refused_or_incomplete_bootstrap"]=32
    summary["release_authorized"]=True
    (folder/"summary.json").write_bytes(
        (json.dumps(summary,sort_keys=True,indent=2)+"\n").encode()
    )
    _refresh(folder)
    with pytest.raises(ValueError,match="frozen original summary mismatch"):
        audit_original(folder)


def test_source_level_Wilson_and_fixed_bootstrap_grid():
    assert _wilson(0,32)==pytest.approx([0.,.107179198255])
    assert _wilson(32,32)[1]==pytest.approx(1.)
    assert (1+2)/(B+1)==.046875
    assert (1+3)/(B+1)==.0625
    with pytest.raises(ValueError,match="Wilson"):
        _wilson(40,32)
