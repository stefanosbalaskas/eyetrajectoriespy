"""Independent R82-A original data law, mask and pointwise audit fixture contracts."""
import json
from hashlib import sha256
import numpy as np
import pytest

from scripts import audit_w3_r82_observation_process as a
from scripts import run_w3_r82_observation_process as orig

def test_exact_frozen_independent_source_law_and_identity():
    assert a.CHECKOUT=="06d1bb888468f1f85eee3875ae14ee5070a12400"
    assert a.SOURCE_SEED==202610208280 and a.OBS_SEED==202610208281
    assert a.OBS_EVALUATIONS==1024 and a.SOURCE_CONDITIONS==256
    assert a.BLOCKS==32
    assert a.MECHANISMS==("complete","MCAR","MAR","MNAR")
    assert len({a.observation_seed(b,c,s,v) for b in range(32)
       for c in a.CONFIGS for s in a.SUPPORT for v in a.VARIANCES})==256

@pytest.mark.parametrize("config",a.CONFIGS)
@pytest.mark.parametrize("support",a.SUPPORT)
def test_independent_full_XY_source_and_masks_match_original(config,support):
    original=orig.source(0,config,support,"predictor_heteroskedastic")
    X,Y,beta=a.replay_XY(0,config,support,"predictor_heteroskedastic")
    np.testing.assert_allclose(X,original[0],rtol=0,atol=0)
    np.testing.assert_allclose(Y,original[1],rtol=2e-10,atol=2e-10)
    np.testing.assert_allclose(beta,original[2][1],rtol=0,atol=0)
    masks=a.masks(X,Y,0,config,support,"predictor_heteroskedastic")
    old=orig.common_masks(0,config,support,"predictor_heteroskedastic",original[0],original[1])
    for m in a.MECHANISMS:
        np.testing.assert_array_equal(masks[m],old[m])
        assert a.mask_digest(masks[m])==orig.mask_digest(old[m])
    assert a.digest(X)==orig.digest(original[0])
    assert a.digest(Y)==orig.digest(original[1])

def test_independent_gridwise_replay_and_native_mask_refusal():
    config="participant_standard";support="two_anchors";var="predictor_heteroskedastic"
    X,Y,beta=a.replay_XY(0,config,support,var)
    masks=a.masks(X,Y,0,config,support,var)
    baseline=a.slope_with_support(X,Y,masks["complete"])
    rows=orig.evaluate(0,config,support,var)
    assert [r["mechanism"] for r in rows]==list(a.MECHANISMS)
    for row in rows:
        report=a.replay_case(row,X,Y,beta,baseline,masks)
        assert report["native_rejected"]==(row["mechanism"]!="complete")
        assert report["refused"]==row["grid_refused_count"]
    x=dict(rows[-1])
    x["release_authorized"]=True
    with pytest.raises(ValueError,match="provenance"):
        a.replay_case(x,X,Y,beta,baseline,masks)
    x=dict(rows[-1])
    x["observed_mask_digest"]="0"*64
    with pytest.raises(ValueError,match="identity"):
        a.replay_case(x,X,Y,beta,baseline,masks)

def test_audit_rejects_false_original_sha256_and_checkout(tmp_path):
    p=tmp_path/"original";p.mkdir()
    (p/"evidence.json").write_text('{"aggregate":{},"source_evaluations":[]}\n')
    (p/"source-commit.txt").write_text(a.CHECKOUT+"\n")
    (p/"SHA256SUMS").write_text("tampered\n")
    with pytest.raises(ValueError,match="SHA256"):
        a.audit(p)
    checks="".join(sha256((p/k).read_bytes()).hexdigest()+"  "+k+"\n"
                   for k in ("evidence.json","source-commit.txt"))
    (p/"SHA256SUMS").write_text(checks)
    with pytest.raises(ValueError,match="checkout"):
        a.audit(p,expected_checkout="f"*40)
    with pytest.raises(ValueError,match="denominator"):
        a.audit(p)
