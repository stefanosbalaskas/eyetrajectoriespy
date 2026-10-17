"""Independent R59 immutable original numerical evidence contracts."""
import hashlib
import math

import pytest

from scripts import audit_w3_r59_original_null_independent as a


def _null_fit():
    starts=[{
        "label":label,"status":"ok",
        "negative_loglik":100.,"reconstructed_loglik":100.,
        "objective_reconstruction_error":0.,
        "physical_projected_KKT":0.,
        "physical_score":[0.,0.,0.],"ratios":[.1,.2,1.],
        "optimizer_success":True,
    } for label in a.NULL_STARTS]
    return {
        "model":"exact_zero","status":"accepted","original_starts":starts,
        "best_observed_multistart_NLL":100.,"selected_NLL":100.,
        "selected_start":a.NULL_STARTS[0],"selected_physical_KKT":0.,
        "selected_free_component_variance_ratios":[.1,.2,1.],
        "selected_slope_ratio":0.,"null_includes_exact_zero_variance":True,
        "global_optimum_proven":False,
    }


def test_physical_zero_face_one_sided_KKT():
    assert a.projected_kkt([.1,.2,1.,0.],
                           [0.,0.,0.,2.],"nonnegative")==0.
    assert a.projected_kkt([.1,.2,1.,0.],
                           [0.,0.,0.,-2.],"nonnegative")==2.
    with pytest.raises(ValueError,match="bound"):
        a.projected_kkt([.1,.2,1.,-.0001],
                        [0.,0.,0.,0.],"nonnegative")


def test_frozen_candidate_and_wilson_precision():
    assert a.CRITICAL==pytest.approx(2.705543454095404,rel=1e-11)
    assert a.wilson(0,128)[1]==pytest.approx(.02913799,abs=1e-5)
    assert a.wilson(0,0) is None
    with pytest.raises(ValueError):a.wilson(129,128)
    assert a.median([1.,2.,3.,4.])==pytest.approx(2.5)


def test_forged_gaussian_NLL_boundary_and_KKT_refused():
    f=_null_fit()
    assert a.audit_fit(f,"exact_zero","test")["status"]=="accepted"
    f=_null_fit();f["selected_slope_ratio"]=.01
    with pytest.raises(ValueError,match="exact zero"):
        a.audit_fit(f,"exact_zero","fake null")
    f=_null_fit();f["selected_NLL"]=99.
    with pytest.raises(ValueError,match="mismatch"):
        a.audit_fit(f,"exact_zero","selected wrong")
    f=_null_fit();f["selected_physical_KKT"]=.2
    with pytest.raises(ValueError,match="mismatch"):
        a.audit_fit(f,"exact_zero","KKT forged")
    f=_null_fit();f["global_optimum_proven"]=True
    with pytest.raises(ValueError,match="global optimum"):
        a.audit_fit(f,"exact_zero","unearned theorem")


def test_original_source_hashes_and_checkout_fail_closed(tmp_path,monkeypatch):
    data={"cases.json":"[]\n","summary.json":"{}\n",
          "source-commit.txt":"original-pr-merge-checkout\n"}
    for name,value in data.items():
        (tmp_path/name).write_text(value)
    hashes={name:hashlib.sha256((tmp_path/name).read_bytes()).hexdigest()
            for name in data}
    (tmp_path/"SHA256SUMS").write_text("".join(
        digest+"  "+name+"\n" for name,digest in hashes.items()))
    monkeypatch.setattr(a,"SOURCE_CHECKOUT","original-pr-merge-checkout")
    assert a.verify_original(tmp_path)==hashes
    (tmp_path/"cases.json").write_text("tampered")
    with pytest.raises(ValueError,match="SHA256 mismatch"):
        a.verify_original(tmp_path)


def test_independent_source_provenance_contract_not_inference():
    assert a.BLOCKS==128 and len(a.EXPECTED)==256
    assert a.SEED==202610175959
    assert a.CRITICAL>0
    assert .5*math.erfc(math.sqrt(a.CRITICAL/2))==pytest.approx(.05)
    with pytest.raises(ValueError,match="mismatch"):
        a.assert_close(1.,float("nan"),"missing")
