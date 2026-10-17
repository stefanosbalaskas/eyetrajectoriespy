"""Tamper/denominator tests for read-only ORIGINAL R53/R55 Gaussian switch audit."""
import hashlib

import pytest

from scripts.audit_w3_r55_original_face_switch_independent import (
    LEVELS,SIGNS,transition_original,verify_original,close,
)


def _node(level,sign,change=False,status="ok"):
    return {
        "level":level,"sign":sign,"status":status,
        "face_changed_from_original":bool(change),
    }


def test_frozen_grid_switch_brackets_and_no_off_grid_extrapolation():
    n=[_node(l,s,change=(l>=.05 and s==1))
       for l in LEVELS for s in SIGNS]
    observed=transition_original(n,1)
    assert observed["status"]=="first_observed_active_face_change_bracket"
    assert observed["previous_no_switch_level"]==.005
    assert observed["first_changed_level"]==.05
    assert observed["true_crossing_time_identified"] is False
    stable=transition_original(n,-1)
    assert stable["status"]=="no_changed_face_on_frozen_grid"
    assert stable["switch_absence_between_grid_nodes_not_proven"]


def test_refusal_is_censoring_not_deleted_success():
    n=[_node(l,s) for l in LEVELS for s in SIGNS]
    n[4]["status"]="refused"
    n[6]["face_changed_from_original"]=True
    result=transition_original(n,-1)
    assert result["status"]=="unresolved_after_fit_or_CR2_refusal"
    assert result["previous_no_switch_level"]==.005
    assert result["first_refused_level"]==.05
    with pytest.raises(ValueError,match="missing original signed path"):
        transition_original(n[:-1],1)


def test_original_immutable_SHA256_member_identity_and_corruption(tmp_path):
    for key,value in (
        ("cases.json","[]\n"),
        ("summary.json","{}\n"),
        ("source-commit.txt","exact-original-checkout\n"),
    ):
        (tmp_path/key).write_text(value)
    digests={file:hashlib.sha256((tmp_path/file).read_bytes()).hexdigest()
             for file in ("cases.json","summary.json","source-commit.txt")}
    (tmp_path/"SHA256SUMS").write_text("".join(
        h+"  "+file+"\n" for file,h in digests.items()))
    assert verify_original(
        tmp_path,"exact-original-checkout",
        digests["cases.json"],digests["summary.json"])==digests
    (tmp_path/"cases.json").write_text("[manipulated]")
    with pytest.raises(ValueError,match="checksum mismatch"):
        verify_original(
            tmp_path,"exact-original-checkout",
            digests["cases.json"],digests["summary.json"])


def test_original_source_checkout_and_aggregate_identity_fail_closed(tmp_path):
    for key,value in (
        ("cases.json","[]\n"),
        ("summary.json","{}\n"),
        ("source-commit.txt","source-A\n"),
    ):
        (tmp_path/key).write_text(value)
    digests={file:hashlib.sha256((tmp_path/file).read_bytes()).hexdigest()
             for file in ("cases.json","summary.json","source-commit.txt")}
    (tmp_path/"SHA256SUMS").write_text("".join(
        h+"  "+file+"\n" for file,h in digests.items()))
    with pytest.raises(ValueError,match="checkout mismatch"):
        verify_original(tmp_path,"source-B",digests["cases.json"])
    with pytest.raises(ValueError,match="aggregate summary"):
        verify_original(tmp_path,"source-A",digests["cases.json"],"0"*64)
    with pytest.raises(ValueError,match="mismatch"):
        close(.01,.02,"forged CR2 pivot error")
