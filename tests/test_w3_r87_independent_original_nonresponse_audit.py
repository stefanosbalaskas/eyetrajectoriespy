"""R87-A independent-generating-law, audit-return and immutable archive tests."""
import hashlib
import json

import numpy as np
import pytest

from scripts import audit_w3_r87_original_nonresponse_independent as auditor
from scripts import run_w3_r87_audit_return_nonresponse as source


def test_independent_source_identity_and_dedicated_seed_streams():
    assert auditor.RECORDS==2304
    assert auditor.BLOCKS==32
    assert auditor.SOURCE_SEED==source.SOURCE_SEED
    assert auditor.OBS_SEED==source.OBS_SEED
    assert auditor.AUDIT_RETURN_SEED==source.AUDIT_RETURN_SEED
    assert auditor.CHECKOUT=="2716a79ceec03ef8cf1cd0a8be3546e638c98884"
    assert auditor.RETURN_LAWS==source.RETURN_LAWS
    assert auditor.STRATEGIES==source.STRATEGIES
    assert auditor.SUPPORT==("two_anchors",)
    assert auditor.VARIANCES==("predictor_heteroskedastic",)


@pytest.mark.parametrize("config",source.CONFIGS)
def test_independent_Gaussian_source_and_MNAR_masks(config):
    s,v="two_anchors","predictor_heteroskedastic"
    X,Y,_,_=source.source(0,config,s,v)
    xa,ya,_=auditor.replay_XY(0,config,s,v)
    np.testing.assert_allclose(X,xa,atol=1e-13,rtol=0)
    np.testing.assert_allclose(Y,ya,atol=4e-14,rtol=0)
    source_masks=source.common_masks(0,config,s,v,X,Y)
    independent=auditor.masks(xa,ya,0,config,s,v)
    for mechanism in ("MAR","MNAR"):
        np.testing.assert_array_equal(source_masks[mechanism],
                                      independent[mechanism])


def test_independent_audit_completion_probability_includes_outcome_dependence():
    c,s,v="curve_standard","two_anchors","predictor_heteroskedastic"
    X,Y,_,_=source.source(0,c,s,v)
    masks=source.common_masks(0,c,s,v,X,Y)
    pilot,_,_=source.original_visible_pilot(X,Y,masks["MNAR"])
    for law in source.RETURN_LAWS:
        x=source.completion_probability(X,Y,pilot,law)
        y=auditor.audit_completion_probability(X,Y,law)
        np.testing.assert_allclose(x,y,atol=1e-13,rtol=1e-13)
    assert not np.array_equal(
        auditor.audit_completion_probability(X,Y,"recorded"),
        auditor.audit_completion_probability(X,Y,"outcome"))
    with pytest.raises(ValueError,match="unsupported"):
        auditor.audit_completion_probability(X,Y,"unknown")


def test_independent_scipy_secondary_fitting_uses_return_probability():
    c,s,v="curve_standard","two_anchors","predictor_heteroskedastic"
    X,Y,_,_=source.source(0,c,s,v)
    mask=source.common_masks(0,c,s,v,X,Y)["MAR"]
    pilot,valid,_=source.original_visible_pilot(X,Y,mask)
    U,V,_,_=source.uniform_pair(0,c,s,v,Y.shape)
    W,_=source.return_uniform(0,c,s,v,Y.shape)
    initial=mask&(U<source.actual_recovery_prob(X,Y))
    assigned=mask&~initial&(V<.25)
    p=source.completion_probability(X,Y,pilot,"outcome")
    returned=assigned&(W<p)
    assumed=.25*source.completion_probability(X,Y,pilot,"recorded")
    original=source.propensity_model(
        X,Y,mask,initial,returned,pilot,valid,assumed)
    independent=auditor.independently_fit_secondary_with_return(
        X,Y,initial,returned,pilot,valid,assumed)
    assert original[3]==independent[3]
    assert original[2] is independent[2]
    if original[2]:
        assert original[1]==pytest.approx(independent[1],abs=2e-5)
        assert original[0]==pytest.approx(independent[0],abs=2e-5)


def _fake_minimal_archive(root):
    (root/"cases.json").write_text("[]\n")
    (root/"summary.json").write_text("{}\n")
    (root/"source-commit.txt").write_text(auditor.CHECKOUT+"\n")
    (root/"SHA256SUMS").write_text("".join(
        hashlib.sha256((root/name).read_bytes()).hexdigest()+"  "+name+"\n"
        for name in ("cases.json","summary.json","source-commit.txt")
    ))


def test_sha256_and_original_source_pin_fail_closed(tmp_path):
    _fake_minimal_archive(tmp_path)
    with pytest.raises(ValueError,match="planned 2304-row"):
        auditor.audit(tmp_path)
    (tmp_path/"cases.json").write_bytes(b"[] \n")
    with pytest.raises(ValueError,match="SHA256"):
        auditor.audit(tmp_path)
    _fake_minimal_archive(tmp_path)
    (tmp_path/"source-commit.txt").write_text("0"*40+"\n")
    (tmp_path/"SHA256SUMS").write_text("".join(
        hashlib.sha256((tmp_path/name).read_bytes()).hexdigest()+"  "+name+"\n"
        for name in ("cases.json","summary.json","source-commit.txt")
    ))
    with pytest.raises(ValueError,match="checkout"):
        auditor.audit(tmp_path)
