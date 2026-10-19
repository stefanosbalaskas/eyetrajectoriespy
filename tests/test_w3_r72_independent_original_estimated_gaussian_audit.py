"""R72-A independent X/Y numerical reconstruction and original SHA256 contracts."""
from __future__ import annotations

from hashlib import sha256
import json
import numpy as np
import pytest

from scripts import audit_w3_r72_original_estimated_gaussian_independent as audit
from scripts import run_w3_r72_new_estimated_gaussian_covariance_bands as source


def _refused(block,design,support):
    return {
        "study":source.STUDY,"block":block,"design":design,"support":support,
        "source_seed":source.source_seed(block,design),
        "wild_seed":source.wild_seed(block,design,support),
        "estimated_gaussian_seed":source.gaussian_seed(block,design,support),
        "completed":False,"refused":True,
        "exception":{"type":"SyntheticRefusal","message":"fixture only"},
        "coverage":{k:None for k in source.METHODS},
        "calibrated_90pct_simultaneous_band":False,
        "source_law_not_a_real_data_covariance_estimator":True,
        "release_authorized":False,
    }


def _archive(path,*,with_one_real=False):
    rows=[_refused(b,d,s) for b in range(32)
          for d in source.DESIGNS for s in source.SUPPORT]
    if with_one_real:
        real=source.case(0,"curve","ordinary")
        assert real["completed"],real["exception"]
        rows[0]=real
    summary=source.summarize(rows)
    (path/"cases.json").write_bytes((json.dumps(
        rows,sort_keys=True,allow_nan=False)+"\n").encode())
    (path/"summary.json").write_bytes((json.dumps(
        summary,sort_keys=True,allow_nan=False)+"\n").encode())
    (path/"source-commit.txt").write_bytes((audit.ORIGINAL_CHECKOUT+"\n").encode())
    _rehash(path)
    return path


def _rehash(path):
    names=("cases.json","summary.json","source-commit.txt")
    (path/"SHA256SUMS").write_bytes("".join(
        sha256((path/name).read_bytes()).hexdigest()+"  "+name+"\n"
        for name in names
    ).encode())


def test_exact_original_source_checkout_and_independent_gaussian_law():
    assert len(audit.ORIGINAL_CHECKOUT)==40
    assert len(audit.METHODS)==3
    assert audit.BLOCKS==32 and audit.B==999
    assert len({audit.SOURCE_SEED,audit.GAUSSIAN_SEED,audit.WILD_SEED})==3
    assert audit.TRUE_LAW_CRITICAL["curve"]>audit.TRUE_LAW_CRITICAL["participant"]
    assert audit._known_diagonal("curve").shape==(62,)
    assert audit._known_diagonal("participant").shape==(62,)
    assert audit._known_diagonal("participant")[0]>0
    assert audit._wilson(0,32)[0]==0
    with pytest.raises(ValueError,match="unsupported"):
        audit._known_diagonal("invalid")


def test_independent_original_source_all_refusals_retained(tmp_path):
    root=_archive(tmp_path)
    rebuilt=audit.audit_original(root)
    assert rebuilt["source_SHA256_members_checked"]==3
    assert rebuilt["source_cases_completed"]==0
    assert rebuilt["independent_primitive_blocks"]==32
    assert rebuilt["paired_original_cases"]==128
    assert not rebuilt["release_authorized"]
    for d in audit.DESIGNS:
        for s in audit.SUPPORT:
            assert rebuilt["coverage"][d][s]["refused"]==32
            assert rebuilt["coverage"][d][s]["completed"]==0


def test_independent_XY_rebuild_matches_one_true_artificial_original_case(tmp_path):
    root=_archive(tmp_path,with_one_real=True)
    result=audit.audit_original(root)
    assert result["source_cases_completed"]==1
    assert result["original_W3_wild_maxima_reconstructed"]==999
    assert result["estimated_HC2_Gaussian_maxima_reconstructed"]==999
    assert result["coverage"]["curve"]["ordinary"]["completed"]==1


def test_original_archive_hash_and_source_checkout_tamper_fail_closed(tmp_path):
    root=_archive(tmp_path)
    (root/"cases.json").write_bytes((root/"cases.json").read_bytes()+b" ")
    with pytest.raises(ValueError,match="SHA256 digest changed"):
        audit.audit_original(root)
    root=_archive(root)
    (root/"source-commit.txt").write_bytes(("0"*40+"\n").encode())
    _rehash(root)
    with pytest.raises(ValueError,match="not pinned"):
        audit.audit_original(root)


def test_forged_source_identity_or_denominator_is_rejected_after_rehash(tmp_path):
    root=_archive(tmp_path)
    rows=json.loads((root/"cases.json").read_text())
    rows[2]["block"]=rows[0]["block"]  # same design and support as row 0
    (root/"cases.json").write_bytes((json.dumps(rows,sort_keys=True)+"\n").encode())
    _rehash(root)
    with pytest.raises(ValueError,match="missing/duplicated"):
        audit.audit_original(root)
