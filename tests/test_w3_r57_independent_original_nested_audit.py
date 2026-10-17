"""Immutable original exact-zero nested Gaussian KKT and likelihood-audit contracts."""
import hashlib
import numpy as np
import pytest

from scripts.audit_w3_r57_original_nested_zero_independent import (
    close,projected_physical,verify_source,audit_model,
)


def test_true_zero_boundary_KKT_keeps_nonstationary_negative_slope_score():
    x=[.1,.2,1.,0.]
    neg=projected_physical([0.,0.,0.,-3.],x,"nonnegative")
    assert neg==pytest.approx(3.)
    pos=projected_physical([0.,0.,0.,3.],x,"nonnegative")
    assert pos==pytest.approx(0.)
    assert projected_physical([0.,0.,0.],x[:3],"exact_zero")==pytest.approx(0.)
    with pytest.raises(ValueError,match="bounds"):
        projected_physical([0.,0.,0.,0.],[.1,.2,1.,-1e-4],"nonnegative")


def _fit():
    return {
        "model":"exact_zero","status":"accepted",
        "null_includes_exact_zero_variance":True,
        "alternative_includes_structural_zero":False,
        "original_starts":[
            {
                "label":label,"status":"ok",
                "negative_loglik":100.,
                "reconstructed_loglik":100.,
                "objective_reconstruction_error":0.,
                "physical_projected_KKT":0.,
                "ratios":[.1,.2,1.],
                "physical_score":[0.,0.,0.],
                "optimizer_success":True,
            } for label in ("null_compact","null_spread")
        ],
        "best_observed_multistart_NLL":100.,
        "selected_NLL":100.,
        "selected_start":"null_compact",
        "selected_physical_KKT":0.,
        "selected_free_component_variance_ratios":[.1,.2,1.],
        "selected_slope_ratio":0.,
    }


def test_reject_false_selected_original_KKT_or_nonzero_structural_null():
    fit=_fit()
    assert audit_model(fit,"exact_zero","fake")["selected_slope_ratio"]==0.
    fit["selected_slope_ratio"]=.01
    with pytest.raises(ValueError,match="exact null"):
        audit_model(fit,"exact_zero","false structural zero")
    fit=_fit()
    fit["selected_physical_KKT"]=.02
    with pytest.raises(ValueError,match="mismatch"):
        audit_model(fit,"exact_zero","false selected KKT")


def test_reject_original_best_candidate_outside_frozen_NLL_acceptance():
    f=_fit()
    f["original_starts"][1]["negative_loglik"]=99.
    f["original_starts"][1]["reconstructed_loglik"]=99.
    with pytest.raises(ValueError,match="mismatch"):
        audit_model(f,"exact_zero","selected not observed best")


def test_original_sha256_integrity_and_checkout_fail_closed(tmp_path,monkeypatch):
    import scripts.audit_w3_r57_original_nested_zero_independent as auditor
    values={
        "cases.json":"[]\n",
        "summary.json":"{}\n",
        "source-commit.txt":"original-R57-checkout\n",
    }
    for name,data in values.items():
        (tmp_path/name).write_text(data)
    sha={name:hashlib.sha256((tmp_path/name).read_bytes()).hexdigest()
         for name in values}
    (tmp_path/"SHA256SUMS").write_text("".join(
        h+"  "+name+"\n" for name,h in sha.items()))
    monkeypatch.setattr(auditor,"CASE_SHA",sha["cases.json"])
    monkeypatch.setattr(auditor,"SUMMARY_SHA",sha["summary.json"])
    monkeypatch.setattr(auditor,"SOURCE_CHECKOUT","original-R57-checkout")
    assert verify_source(tmp_path)==sha
    (tmp_path/"cases.json").write_text("tampered")
    with pytest.raises(ValueError,match="SHA256 mismatch"):
        verify_source(tmp_path)


def test_nonfinite_and_unsupported_evidence_mismatches_are_errors():
    with pytest.raises(ValueError,match="mismatch"):
        close(1.,2.,"false Gaussian likelihood gap")
    with pytest.raises(ValueError,match="mismatch"):
        close(float("nan"),0.,"nonfinite")
    with pytest.raises(ValueError,match="unknown nested model"):
        projected_physical([0.],[1.],"not a true likelihood model")
