"""R71-A independent original known-Gaussian-law maximum and W3 wild audit contracts."""
from __future__ import annotations

from hashlib import sha256
import json
import numpy as np
import pytest

from scripts import audit_w3_r71_independent_known_gaussian_archive as audit
from scripts import run_w3_r71_new_known_gaussian_band_oracle as orig


def _source(block,design,support):
    law=orig.known_law_reference(design)
    v=np.sqrt(audit._unit_var(design))*.10
    err=.4*v
    hc1=.8*v
    raw=[2.]*audit.B
    seed=audit.WILD_SEED+100003*block+10007*audit.DESIGNS.index(design)+739*audit.SUPPORT.index(support)
    return {
        "study":audit.STUDY,"block":block,"design":design,"support":support,
        "source_seed":audit.SOURCE_SEED+10007*block+audit.DESIGNS.index(design),
        "wild_seed":seed,"independent_units":72 if design=="curve" else 36,
        "observed_curves":72 if design=="curve" else 108,
        "completed":True,"exception":None,
        "OLS_oracle_max_error":0.,"HC1_oracle_max_error":0.,
        "package_wild_max_reference_error":0.,
        "observed_max_hat":.1 if support=="ordinary" else .4,
        "known_law_critical":law["critical"],"original_wild_critical":2.,
        "known_law_slope_truth_included":True,
        "original_wild_HC1_slope_truth_included":True,
        "known_law_slope_max_pivot":.4,
        "original_wild_HC1_slope_max_pivot":.5,
        "min_HC1_over_known_SE":.8,"mean_HC1_over_known_SE":.8,
        "max_HC1_over_known_SE":.8,
        "wild_critical_over_known_law_critical":2./law["critical"],
        "observed_slope_beta_error_grid":err.tolist(),
        "observed_HC1_slope_SE_grid":hc1.tolist(),
        "known_law_true_slope_SE_grid":v.tolist(),
        "wild_999_raw_slope_maxima":raw,
        "no_nominal_90pct_wild_band_qualification":True,
        "known_covariance_not_observed_data_estimator":True,
        "release_authorized":False,
    }


def _fixture(path):
    path.mkdir(parents=True,exist_ok=True)
    rows=[_source(b,d,s) for b in range(audit.BLOCKS)
          for d in audit.DESIGNS for s in audit.SUPPORT]
    refs={d:orig.known_law_reference(d) for d in audit.DESIGNS}
    sums=orig.summarize(rows)
    for name,data in {
        "cases.json":rows,
        "summary.json":sums,
        "known_gaussian_reference.json":refs,
    }.items():
        (path/name).write_text(json.dumps(data,sort_keys=True)+"\n")
    (path/"source-commit.txt").write_text(audit.CHECKOUT+"\n")
    _hash(path)
    return path


def _hash(path):
    names=("cases.json","summary.json","known_gaussian_reference.json","source-commit.txt")
    (path/"SHA256SUMS").write_text("".join(
        sha256((path/n).read_bytes()).hexdigest()+"  "+n+"\n"
        for n in names))


def test_exact_Gaussian_reference_laws_and_all_original_raw_draw_counts():
    assert audit.BLOCKS==32 and audit.SOURCE_CASES==128
    assert audit.K==32767 and audit.B==999
    assert audit.CHECKOUT=="1102b57fe9605e46303921989842ee3f7a0e1f84"
    for design in audit.DESIGNS:
        reference=orig.known_law_reference(design)
        np.testing.assert_allclose(
            audit._rebuild_reference(design),
            reference["raw_standardized_maxima"],rtol=0,atol=2e-11)
        assert audit._higher(reference["raw_standardized_maxima"],audit.K)==reference["critical"]
    with pytest.raises(ValueError,match="raw Gaussian/wild"):
        audit._higher([1.]*(audit.K-1),audit.K)


def test_original_complete_synthetic_archive_recovers_all_source_critical_events(tmp_path):
    p=_fixture(tmp_path/"original")
    d=audit.audit(p)
    assert d["original_SHA256_members_verified"]==4
    assert d["original_archived_gaussian_max_draws_independently_resimulated"]==65534
    assert d["original_wild_maxima_independently_requantiled"]==127872
    assert d["original_source_true_vs_HC1_slopes_reclassified"]==256
    assert d["source_truth_inclusion"]["curve"]["extreme"]["known_included"]==32
    assert d["source_truth_inclusion"]["participant"]["ordinary"]["wild_included"]==32
    assert d["source_design_X_not_archived_cannot_independently_check_OLS_XtX_scalar"]
    assert not d["release_authorized"]


def test_archive_checkout_and_SHA256_original_failure_gate(tmp_path):
    p=_fixture(tmp_path/"original")
    with pytest.raises(ValueError,match="checkout"):
        audit.audit(p,expected_checkout="d"*40)
    q=p/"cases.json"
    q.write_bytes(q.read_bytes()+b" ")
    with pytest.raises(ValueError,match="SHA256"):
        audit.audit(p)


def test_wild_999_quantile_trusted_only_after_recomputation(tmp_path):
    p=_fixture(tmp_path/"original")
    rows=json.loads((p/"cases.json").read_text())
    rows[0]["original_wild_critical"]+=.2
    (p/"cases.json").write_text(json.dumps(rows,sort_keys=True)+"\n")
    _hash(p)
    with pytest.raises(ValueError,match="wild 999 higher quantile"):
        audit.audit(p)


def test_known_Gaussian_draws_or_true_covariance_cannot_be_forged(tmp_path):
    p=_fixture(tmp_path/"original")
    refs=json.loads((p/"known_gaussian_reference.json").read_text())
    refs["participant"]["raw_standardized_maxima"][7]+=.25
    (p/"known_gaussian_reference.json").write_text(json.dumps(refs,sort_keys=True)+"\n")
    _hash(p)
    with pytest.raises(ValueError,match="reference simulation"):
        audit.audit(p)
    p=_fixture(tmp_path/"other")
    refs=json.loads((p/"known_gaussian_reference.json").read_text())
    refs["curve"]["true_unit_variance_grid"][0][0]+=.01
    (p/"known_gaussian_reference.json").write_text(json.dumps(refs,sort_keys=True)+"\n")
    _hash(p)
    with pytest.raises(ValueError,match="covariance diagonal"):
        audit.audit(p)


def test_true_SE_grid_or_source_coverage_claim_tamper_rejected(tmp_path):
    p=_fixture(tmp_path/"original")
    cases=json.loads((p/"cases.json").read_text())
    cases[0]["known_law_true_slope_SE_grid"][0][0]*=2
    (p/"cases.json").write_text(json.dumps(cases,sort_keys=True)+"\n")
    _hash(p)
    with pytest.raises(ValueError,match="Gaussian covariance shape"):
        audit.audit(p)
    p=_fixture(tmp_path/"other")
    cases=json.loads((p/"cases.json").read_text())
    cases[0]["known_law_slope_truth_included"]=False
    (p/"cases.json").write_text(json.dumps(cases,sort_keys=True)+"\n")
    _hash(p)
    with pytest.raises(ValueError,match="truth inclusion"):
        audit.audit(p)


def test_extra_source_ids_and_false_release_are_refused(tmp_path):
    p=_fixture(tmp_path/"original")
    rows=json.loads((p/"cases.json").read_text())
    rows[0]["block"]=31
    (p/"cases.json").write_text(json.dumps(rows,sort_keys=True)+"\n")
    _hash(p)
    with pytest.raises(ValueError,match="source grid"):
        audit.audit(p)
    p=_fixture(tmp_path/"other")
    summary=json.loads((p/"summary.json").read_text())
    summary["release_authorized"]=True
    (p/"summary.json").write_text(json.dumps(summary,sort_keys=True)+"\n")
    _hash(p)
    with pytest.raises(ValueError,match="mismatch"):
        audit.audit(p)
