"""Independent R50 postprocessor contracts; no scientific generator or estimator imports."""
import hashlib
import json
from pathlib import Path

import pytest

from scripts.audit_w3_r50_original_evidence_independent import (
    BLOCKS, SUPPORT, METHODS, N_BOOT, _q_linear, _wilson, audit_original,
)


def _write_json(path, value):
    path.write_text(json.dumps(value,sort_keys=True,indent=2)+"\n")


def _refresh_hashes(path):
    (path/"SHA256SUMS").write_text("".join(
        hashlib.sha256((path/f).read_bytes()).hexdigest()+f"  {f}\n"
        for f in ("cases.json","summary.json","source-commit.txt")
    ))


def _mock_artifact(tmp_path):
    """Construct a complete but uniformly refused 24-block experiment."""
    cases=[]
    strata={}
    for support in SUPPORT:
        methods={}
        for m in METHODS:
            methods[m]={
                "accepted":0,"failed_or_refused":BLOCKS,
                "truth_inclusion_numerator":0,
                "all_block_coverage_fraction":0.0,
                "Wilson95_MC":list(_wilson(0,BLOCKS)),
                "mean_half_width_success_only":None,
            }
        strata[support]={
            "methods":methods,
            "bootstrap_refit_successes":0,
            "bootstrap_refit_refused":0,
            "bootstrap_refit_not_attempted":BLOCKS*N_BOOT,
            "31_vs_63_critical_ratio_median":None,
            "31_vs_63_truth_inclusion_disagreements":0,
        }
    for block in range(BLOCKS):
        for support in SUPPORT:
            starts=[{"label":"start1","status":"not_attempted"},
                    {"label":"start2","status":"not_attempted"}]
            cases.append({
                "block":block,"support":support,
                "source_status":"failed",
                "original_correct_nuisance":{"numerical_starts":starts},
                "original_wrong_nuisance":{"numerical_starts":starts},
                "intervals":[{"method":m,"status":"refused",
                              "truth_included":False} for m in METHODS],
                "bootstrap_refit_attempts":[
                    {"replicate":i,"status":"not_attempted",
                     "numerical_starts":starts} for i in range(N_BOOT)],
            })
    summary={
        "complete_original_failure_inclusive_design":True,
        "source_seed":202610165050,
        "bootstrap_draw_seed":202610165051,
        "release_authorized":False,
        "strata":strata,
    }
    _write_json(tmp_path/"cases.json",cases)
    _write_json(tmp_path/"summary.json",summary)
    (tmp_path/"source-commit.txt").write_text("f"*40+"\n")
    _refresh_hashes(tmp_path)
    return tmp_path


def test_independent_report_all_blocks_and_refused_denominators(tmp_path):
    root=_mock_artifact(tmp_path)
    report=audit_original(root)
    assert report["original_independent_primitive_blocks"]==24
    assert report["paired_source_cases"]==48
    assert report["interval_slots"]==240
    assert report["bootstrap_refit_attempts"]==3024
    assert report["optimizer_start_slots"]==6240
    assert report["sha256_verified"]==3
    assert not report["coverage_calibrated"]
    assert not report["release_authorized"]
    assert report["strata"][SUPPORT[0]][METHODS[0]]["denominator"]==24
    assert report["strata"][SUPPORT[1]][METHODS[-1]]["refused"]==24


def test_hash_corruption_and_duplicate_source_refused(tmp_path):
    root=_mock_artifact(tmp_path)
    cases=json.loads((root/"cases.json").read_text())
    cases[0]["block"]=cases[2]["block"]  # duplicated block/support
    _write_json(root/"cases.json",cases)
    with pytest.raises(ValueError,match="SHA256"):
        audit_original(root)
    _refresh_hashes(root)
    with pytest.raises(ValueError,match="missing, duplicated"):
        audit_original(root)


def test_independent_summary_mismatch_detected_after_checksum_refresh(tmp_path):
    root=_mock_artifact(tmp_path)
    summary=json.loads((root/"summary.json").read_text())
    summary["strata"][SUPPORT[0]]["methods"][METHODS[0]]["accepted"]=1
    _write_json(root/"summary.json",summary)
    _refresh_hashes(root)
    with pytest.raises(ValueError,match="accepted-record count"):
        audit_original(root)


def test_independent_bootstrap_quantile_rule_and_invalid_order(tmp_path):
    assert _q_linear([1,2,3,4],.9)==pytest.approx(3.7)
    assert _q_linear([0,1,2,3,4],.5)==pytest.approx(2)
    root=_mock_artifact(tmp_path)
    cases=json.loads((root/"cases.json").read_text())
    cases[0]["bootstrap_refit_attempts"][1]["replicate"]=0
    _write_json(root/"cases.json",cases)
    _refresh_hashes(root)
    with pytest.raises(ValueError,match="invalid original 63-refit"):
        audit_original(root)
