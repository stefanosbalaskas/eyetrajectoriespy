"""R68-A independent exact-source numerical audit synthetic integrity contracts."""
from __future__ import annotations

import hashlib
import json

import pytest

from scripts import audit_w3_r68_independent_original_feasibility as audit
from scripts import run_w3_r68_new_source_numerical_feasibility as source
from scripts import run_w3_r63_independent_null_replication as core


def _rows():
    return [
        {
            "study":audit.STUDY,"block":b,"support":s,"level":l,
            "source_status":"refused","source_error":"original source fixture deliberately refused",
            "true_slope_variance":(source.MULTIPLIERS[l]*.045)**2,
            "observed":core.nested_on_invalid(),
            "bootstrap":[source.empty_draw(d) for d in range(audit.B)],
            "original_test_p_value":None,"candidate_rejection":None,
            "statistical_power_qualified":False,
            "fitted_CR2_90pct_qualified":False,"release_authorized":False,
        }
        for b in range(audit.BLOCKS) for s in audit.SUPPORT for l in audit.LEVELS
    ]


def _archive(folder):
    folder.mkdir(parents=True,exist_ok=True)
    cases=_rows()
    report=source.summarize(cases)
    (folder/"cases.json").write_text(json.dumps(cases,sort_keys=True,indent=2)+"\n")
    (folder/"summary.json").write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    (folder/"source-commit.txt").write_text("c"*40+"\n")
    _rehash(folder)
    return folder


def _rehash(folder):
    (folder/"SHA256SUMS").write_text("".join(
        hashlib.sha256((folder/n).read_bytes()).hexdigest()+"  "+n+"\n"
        for n in ("cases.json","summary.json","source-commit.txt")))


def test_frozen_new_source_params_and_independent_original_auditor_contract():
    assert audit.BLOCKS==8 and audit.CASES==48
    assert audit.DRAWS==192 and audit.START_SLOTS==1440
    assert audit.MODEL_POSITIONS==480
    assert audit.MASTER_SEED==202610196868
    assert audit.DRAW_SEED==202610196869
    assert (audit.KKT,audit.NLL,audit.NEST)==(.001,.001,.00001)
    assert not getattr(audit,"source",None)


def test_original_complete_archive_refusal_fixture_is_independently_audited(tmp_path):
    root=_archive(tmp_path/"original")
    result=audit.audit_original(root,expected_checkout="c"*40)
    assert result["independent_original_archive_reproduced"]
    assert result["sha256_entries_verified"]==3
    assert result["original_source_checkout"]=="c"*40
    assert result["matched_source_case_positions"]==48
    assert result["Gaussian_draw_positions"]==192
    assert result["optimizer_start_positions"]==1440
    assert result["unattempted_conditional_numerical_fits"]==192
    assert result["accepted_conditional_numerical_fits"]==0
    assert result["R66_missing_primary_confidence_interval_not_recomputed"]
    assert result["release_authorized"] is False


def test_SHA256_original_checkout_missing_block_and_claim_tamper_fail_closed(tmp_path):
    root=_archive(tmp_path/"original")
    with pytest.raises(ValueError,match="wrong original"):
        audit.audit_original(root,expected_checkout="d"*40)
    cases=root/"cases.json"
    cases.write_bytes(cases.read_bytes()+b" ")
    with pytest.raises(ValueError,match="SHA256"):
        audit.audit_original(root)
    root=_archive(tmp_path/"other")
    rows=json.loads((root/"cases.json").read_text())
    rows[0]["block"]=7
    (root/"cases.json").write_text(json.dumps(rows,sort_keys=True)+"\n")
    _rehash(root)
    with pytest.raises(ValueError,match="grid"):
        audit.audit_original(root)
    root=_archive(tmp_path/"third")
    report=json.loads((root/"summary.json").read_text())
    report["release_authorized"]=True
    (root/"summary.json").write_text(json.dumps(report,sort_keys=True)+"\n")
    _rehash(root)
    with pytest.raises(ValueError,match="mismatch"):
        audit.audit_original(root)


def test_refusal_ledger_and_original_conditional_slots_cannot_be_discarded(tmp_path):
    root=_archive(tmp_path/"original")
    rows=json.loads((root/"cases.json").read_text())
    rows[1]["bootstrap"].pop()
    (root/"cases.json").write_text(json.dumps(rows,sort_keys=True)+"\n")
    _rehash(root)
    with pytest.raises(ValueError,match="draw index"):
        audit.audit_original(root)
    root=_archive(tmp_path/"other")
    report=json.loads((root/"summary.json").read_text())
    report["original_fit_status_counts"]["conditional/not_attempted"]=191
    (root/"summary.json").write_text(json.dumps(report,sort_keys=True)+"\n")
    _rehash(root)
    with pytest.raises(ValueError,match="status counts"):
        audit.audit_original(root)
