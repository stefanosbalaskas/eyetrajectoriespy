"""R69-A original-archive source/coverage audit integrity and refusal contracts."""
from __future__ import annotations

from hashlib import sha256
import json

import pytest

from scripts import audit_w3_r69_independent_original_coverage as audit
from scripts import run_w3_r69_fresh_simultaneous_bootstrap_sensitivity as source


def _row(block,design,complete=True):
    n=72 if design=="curve" else 36
    cells={}
    if complete:
        for multiplier in audit.MULT:
            for budget in audit.BUDGETS:
                cells[f"{multiplier}/{budget}"]={
                    "multiplier":multiplier,"draws":budget,
                    "seed":audit.SEED+1000003*block+
                        10007*audit.DESIGNS.index(design)+
                        557*audit.MULT.index(multiplier)+41,
                    "source_units":n,
                    "truth_slope_simultaneous_all_grid":block%5!=0,
                    "truth_joint_family_simultaneous_all_grid":block%5!=0 and block%2==0,
                    "critical_slope":2.4+budget*.00001,
                    "critical_family":3.0+budget*.00001,
                    "slope_median_band_width":.3,
                    "family_median_band_width":.4,
                    "bootstrap_prefix_of_same_999draw_stream":True,
                }
    return {
        "study":audit.STUDY,"block":block,"design":design,
        "source_seed":audit.SEED+10007*block+audit.DESIGNS.index(design),
        "independent_units":n,"total_observed_curves":72 if design=="curve" else 108,
        "completed":complete,
        "exception":None if complete else {"type":"TestRefusal","message":"synthetic"},
        "max_beta_oracle_error":0. if complete else None,
        "max_HC1_oracle_error":0. if complete else None,
        "mean_slope_pointwise_truth_inclusion":.87 if complete else None,
        "conditions":cells,"new_primitive_source_blocks":16,
        "bootstrap_draws_are_not_independent_source_units":True,
        "simultaneous_90pct_coverage_qualified":False,"release_authorized":False,
    }


def _folder(path,rows=None):
    path.mkdir(parents=True,exist_ok=True)
    rows=rows or [_row(b,d) for b in range(audit.BLOCKS) for d in audit.DESIGNS]
    summary=source.summarize(rows)
    (path/"cases.json").write_text(json.dumps(rows,sort_keys=True,indent=2)+"\n")
    (path/"summary.json").write_text(json.dumps(summary,sort_keys=True,indent=2)+"\n")
    (path/"source-commit.txt").write_text(audit.CHECKOUT+"\n")
    _hash(path)
    return path


def _hash(path):
    (path/"SHA256SUMS").write_text("".join(
        sha256((path/n).read_bytes()).hexdigest()+"  "+n+"\n"
        for n in ("cases.json","summary.json","source-commit.txt")
    ))


def test_original_R69_independent_audit_preserves_source_unit_counts():
    assert audit.BLOCKS==16 and audit.DRAW_STREAMS==63936
    assert audit.CHECKOUT=="72f7acf6fac9f973ec96b672e30e926a6ec63c75"
    assert audit.ATOL==2e-10
    assert audit._wilson(0,16)[0]==0.


def test_synthetic_complete_original_SHAs_paired_coverage_and_source_denominator(tmp_path):
    root=_folder(tmp_path/"original")
    evidence=audit.check_archive(root)
    assert evidence["actual_original_source_level_evidence_independently_reconstructed"]
    assert evidence["original_source_archive_SHA256_verified"]==3
    assert evidence["new_original_source_datasets"]==32
    assert evidence["original_conditionally_generated_wild_draws"]==63936
    assert evidence["independent_source_coverage"]["curve"]["normal/199"]["denominator"]==16
    assert evidence["conditional_bootstrap_critical_values_not_independently_recomputed_from_raw_wild_draws"]
    assert not evidence["release_authorized"]
    assert evidence["nominal_90pct_coverage_not_qualified"]


def test_wrong_original_SHA_source_identity_or_release_claim_fails_closed(tmp_path):
    p=_folder(tmp_path/"a")
    with pytest.raises(ValueError,match="checkout"):
        audit.check_archive(p,expected_checkout="f"*40)
    (p/"cases.json").write_bytes((p/"cases.json").read_bytes()+b" ")
    with pytest.raises(ValueError,match="SHA256"):
        audit.check_archive(p)
    p=_folder(tmp_path/"b")
    cases=json.loads((p/"cases.json").read_text())
    cases[0]["block"]=15
    (p/"cases.json").write_text(json.dumps(cases,sort_keys=True)+"\n")
    _hash(p)
    with pytest.raises(ValueError,match="identities"):
        audit.check_archive(p)
    p=_folder(tmp_path/"c")
    summary=json.loads((p/"summary.json").read_text())
    summary["no_calibrated_90pct_simultaneous_coverage_claim"]=False
    (p/"summary.json").write_text(json.dumps(summary,sort_keys=True)+"\n")
    _hash(p)
    with pytest.raises(ValueError,match="mismatch"):
        audit.check_archive(p)


def test_paired_contrast_tampering_and_false_bootstrap_stream_evidence_refused(tmp_path):
    p=_folder(tmp_path/"a")
    summary=json.loads((p/"summary.json").read_text())
    key="curve/199/rademacher_to_normal"
    summary["paired_diagnostics"][key]["later_only_truth_included"]+=1
    (p/"summary.json").write_text(json.dumps(summary,sort_keys=True)+"\n")
    _hash(p)
    with pytest.raises(ValueError,match="mismatch"):
        audit.check_archive(p)
    p=_folder(tmp_path/"b")
    cases=json.loads((p/"cases.json").read_text())
    cases[0]["conditions"]["rademacher/199"]["seed"]+=1
    (p/"cases.json").write_text(json.dumps(cases,sort_keys=True)+"\n")
    _hash(p)
    with pytest.raises(ValueError,match="wild source condition"):
        audit.check_archive(p)


def test_failure_inclusive_original_16_primitive_blocks_preserved(tmp_path):
    rows=[_row(b,d,complete=not (b==7 and d=="participant"))
          for b in range(16) for d in audit.DESIGNS]
    p=_folder(tmp_path/"original",rows)
    report=audit.check_archive(p)
    assert report["independent_source_coverage"]["participant"]["normal/999"][
        "complete_sources"]==15
    paired=report["original_source_paired_contrasts"]["participant/normal/199_to_999"]
    assert paired["missing_or_failed_primitive_blocks"]==1
    assert paired["failure_inclusive_lower"]<=paired["failure_inclusive_upper"]


def test_family_wider_band_may_include_truth_when_slope_only_does_not(tmp_path):
    # Family critical values are generally larger. Their wider bands can
    # include the full coefficient truth even when the narrower slope-only
    # band misses one slope grid cell. This is NOT archive corruption.
    rows=[_row(b,d) for b in range(audit.BLOCKS) for d in audit.DESIGNS]
    row=next(x for x in rows if x["block"]==0 and x["design"]=="curve")
    cell=row["conditions"]["normal/999"]
    assert cell["critical_family"]>=cell["critical_slope"]
    cell["truth_slope_simultaneous_all_grid"]=False
    cell["truth_joint_family_simultaneous_all_grid"]=True
    path=_folder(tmp_path/"legitimate_family_only",rows)
    verified=audit.check_archive(path)
    assert verified["actual_original_source_level_evidence_independently_reconstructed"]
    assert verified["independent_source_coverage"]["curve"]["normal/999"][
        "joint_family_inclusions"
    ]>verified["independent_source_coverage"]["curve"]["normal/999"][
        "numerator"
    ] or verified["original_source_archive_SHA256_verified"]==3
