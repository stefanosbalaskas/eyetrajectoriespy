"""R64-A independent frozen matched structural-slope archive contracts."""
from __future__ import annotations

import hashlib
import json

import pytest

from scripts.audit_w3_r64_original_positive_slope_independent import (
    ALPHA, BLOCKS, B, LEVELS, SUPPORT, SOURCE_CASES, SOURCE_DRAWS,
    SOURCE_MODELS, SOURCE_STARTS, _variance, _wilson, audit_original
)
from scripts import run_w3_r64_nonzero_slope_detection_pilot as source


def _refresh(root):
    (root/"SHA256SUMS").write_bytes("".join(
        hashlib.sha256((root/name).read_bytes()).hexdigest()+"  "+name+"\n"
        for name in ("cases.json","summary.json","source-commit.txt")
    ).encode("utf-8"))


def _archive(folder):
    """Fixture deliberately all numerical refusals, NOT original outcome."""
    cases=[source.empty_case(b,s,l)
           for b in range(BLOCKS)
           for s in SUPPORT for l in LEVELS]
    for row in cases:
        row["bootstrap"]=[source.empty_draw(i) for i in range(B)]
    report=source.summarize(cases)
    (folder/"cases.json").write_bytes(
        (json.dumps(cases,sort_keys=True,indent=2)+"\n").encode("utf-8"))
    (folder/"summary.json").write_bytes(
        (json.dumps(report,sort_keys=True,indent=2)+"\n").encode("utf-8"))
    (folder/"source-commit.txt").write_bytes(("a"*40+"\n").encode("utf-8"))
    _refresh(folder)
    return folder


def test_frozen_source_and_slope_variances_and_bootstrap_grid():
    assert BLOCKS==32 and B==63 and SOURCE_CASES==192
    assert SOURCE_DRAWS==12096 and SOURCE_MODELS==24576
    assert SOURCE_STARTS==73728
    assert LEVELS==("zero","half","full")
    assert _variance("zero")==0
    assert _variance("half")==pytest.approx(.00050625)
    assert _variance("full")==pytest.approx(.002025)
    assert (1+2)/(B+1)==.046875
    assert (1+3)/(B+1)==.0625
    assert ALPHA==.05
    assert _wilson(0,32)==pytest.approx([0.,.107179198255])
    with pytest.raises(ValueError,match="Wilson"):
        _wilson(33,32)


def test_original_full_denominator_accepts_only_frozen_all_refusal_fixture(tmp_path):
    report=audit_original(_archive(tmp_path),expected_original_checkout="a"*40)
    assert report["R64_independent_original_numerical_archive_reproduced"] is True
    assert report["original_sha256_entries_verified"]==3
    assert report["paired_source_cases"]==192
    assert report["bootstrap_draw_slots"]==12096
    assert report["nested_model_fit_positions"]==24576
    assert report["optimizer_start_positions"]==73728
    assert not report["release_authorized"]
    assert all(x["refused_incomplete_sources"]==32 for x in report["strata"].values())
    assert all(x["bootstrap_Wilson95_complete"] is None
               for x in report["strata"].values())
    assert all(x["refusal_as_rejection_all_source_upper"]==1
               for x in report["strata"].values())
    assert all(x["complete_matched_primitive_blocks"]==0
               for x in report["matched_source_detection_transitions"].values())


def test_immutable_SHA256_tampering_and_duplicate_level_fail_closed(tmp_path):
    root=_archive(tmp_path)
    cases=root/"cases.json"
    cases.write_bytes(cases.read_bytes()+b"\n")
    with pytest.raises(ValueError,match="SHA256 mismatch"):
        audit_original(root)
    source_cases=json.loads(cases.read_bytes())
    source_cases[0]["level"]="full"
    cases.write_bytes((json.dumps(source_cases,sort_keys=True,indent=2)+"\n").encode("utf-8"))
    _refresh(root)
    with pytest.raises(ValueError,match="source-level grid"):
        audit_original(root)


def test_invalid_structural_slope_and_forged_power_claims_fail_closed(tmp_path):
    root=_archive(tmp_path)
    cases=json.loads((root/"cases.json").read_bytes())
    cases[0]["true_slope_variance"]=1.
    (root/"cases.json").write_bytes((json.dumps(cases,sort_keys=True,indent=2)+"\n").encode())
    _refresh(root)
    with pytest.raises(ValueError,match="true slope variance"):
        audit_original(root)
    cases[0]["true_slope_variance"]=0.
    cases[0]["null_size_or_power_qualified"]=True
    (root/"cases.json").write_bytes((json.dumps(cases,sort_keys=True,indent=2)+"\n").encode())
    _refresh(root)
    with pytest.raises(ValueError,match="qualification gate"):
        audit_original(root)


def test_separate_192_source_and_64_conditional_rank_gate(tmp_path):
    root=_archive(tmp_path)
    original=audit_original(root)
    assert original["paired_source_cases"]==192
    summary=json.loads((root/"summary.json").read_bytes())
    assert summary["conditional_candidate_p_grid_denominator"]==64
    summary["conditional_candidate_p_grid_denominator"]=192
    (root/"summary.json").write_bytes(
        (json.dumps(summary,sort_keys=True,indent=2)+"\n").encode("utf-8"))
    _refresh(root)
    with pytest.raises(ValueError,match="denominator"):
        audit_original(root)


def test_pin_original_checkout_identity_explicitly(tmp_path):
    root=_archive(tmp_path)
    assert audit_original(root,expected_original_checkout="a"*40)["original_source_checkout"]=="a"*40
    with pytest.raises(ValueError,match="pinned SHA"):
        audit_original(root,expected_original_checkout="b"*40)
