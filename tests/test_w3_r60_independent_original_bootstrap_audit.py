"""R60-A archive and numerical audit contracts, independent of source estimator."""
import hashlib
import math

import pytest

from scripts import audit_w3_r60_original_bootstrap_independent as a


def fake_fit():
    starts=[{"label":name,"status":"ok","optimizer_success":True,
             "negative_loglik":100.,"reconstructed_loglik":100.,
             "objective_reconstruction_error":0.,
             "physical_projected_KKT":0.,
             "physical_score":[0.,0.,0.],"ratios":[.1,.2,1.]}
            for name in a.NULL_STARTS]
    return {"model":"exact_zero","status":"accepted",
            "original_starts":starts,
            "best_observed_multistart_NLL":100.,
            "selected_NLL":100.,"selected_start":a.NULL_STARTS[0],
            "selected_physical_KKT":0.,
            "selected_free_component_variance_ratios":[.1,.2,1.],
            "selected_slope_ratio":0.,
            "null_includes_exact_zero_variance":True,
            "global_optimum_proven":False}


def test_independent_source_bootstrap_and_fit_slot_contract():
    assert a.BLOCKS==4
    assert a.B==31
    assert len(a.EXPECTED)==8
    assert 8*(a.B+1)*6==1536
    assert a.ORIGINAL_RUN==39067797968
    assert a.SOURCE_CHECKOUT=="9424d2507a9ba38132bec1feee9af4c40263f52a"


def test_boundary_projected_physical_kkt_recomputed():
    assert a.projected_kkt([.1,.2,1.,0.],[0.,0.,0.,2.],
                           "nonnegative")==0.
    assert a.projected_kkt([.1,.2,1.,0.],[0.,0.,0.,-2.],
                           "nonnegative")==2.
    with pytest.raises(ValueError,match="bound"):
        a.projected_kkt([.1,.2,1.,-0.05],
                        [0.,0.,0.,0.],"nonnegative")


def test_failed_likelihood_selected_wrongly_refused():
    good=fake_fit()
    assert a.audit_fit(good,"exact_zero","test")["status"]=="accepted"
    bad=fake_fit()
    bad["selected_NLL"]=99.
    with pytest.raises(ValueError,match="mismatch"):
        a.audit_fit(bad,"exact_zero","wrong NLL")
    bad=fake_fit()
    bad["selected_slope_ratio"]=.001
    with pytest.raises(ValueError,match="exact zero"):
        a.audit_fit(bad,"exact_zero","fake H0")


def test_original_nested_refusal_never_counted_as_accepted():
    null=fake_fit()
    invalid={"status":"not_attempted","original_starts":[
        {"label":name,"status":"not_attempted"} for name in a.ALT_STARTS],
        "model":"nonnegative"}
    nested={"status":"accepted","null_fit":null,
            "alternative_fit":invalid,
            "raw_deviance":None,"nonnegative_deviance":None}
    with pytest.raises(ValueError):
        a.audit_nested(nested,"forged accepted")


def test_sha256_source_and_checkout_tamper_refused(tmp_path,monkeypatch):
    files={"cases.json":"[]\n","summary.json":"{}\n",
           "source-commit.txt":"original-pr-merge\n"}
    for name,v in files.items():(tmp_path/name).write_text(v)
    hashes={name:hashlib.sha256((tmp_path/name).read_bytes()).hexdigest()
            for name in files}
    (tmp_path/"SHA256SUMS").write_text("".join(
        digest+"  "+name+"\n" for name,digest in hashes.items()))
    monkeypatch.setattr(a,"SOURCE_CHECKOUT","original-pr-merge")
    assert a.verify_original(tmp_path)==hashes
    (tmp_path/"summary.json").write_text("altered")
    with pytest.raises(ValueError,match="SHA256 mismatch"):
        a.verify_original(tmp_path)


def test_bootstrap_p_exact_rank_minimum_and_candidate_cutoff():
    assert 1/(a.B+1)==.03125
    assert 2/(a.B+1)==.0625
    assert .5*math.erfc(math.sqrt(a.CRITICAL/2))==pytest.approx(.05)
