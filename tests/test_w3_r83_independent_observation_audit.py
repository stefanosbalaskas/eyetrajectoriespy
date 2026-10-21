"""Independently coded R83 source and delta weighting numerical contracts."""
import numpy as np
import pytest
from scripts import run_w3_r83_observation_sensitivity as original
from scripts import audit_w3_r83_observation_sensitivity as independent

def test_new_exact_original_source_contract():
    assert independent.SOURCE_SEED==202610218380
    assert independent.OBS_SEED==202610218381
    assert independent.DIAGNOSTIC_RECORDS==3328
    assert independent.DELTA==(-1.1,-.55,0.,.55,1.1)
    assert independent.CHECKOUT=="4aaf792457c789b3fafd218e3dd94ae46af47e86"

@pytest.mark.parametrize("config",independent.CONFIGS)
@pytest.mark.parametrize("support",independent.SUPPORT)
def test_original_full_source_and_mcar_mar_mnar_masks_are_rebuilt(config,support):
    X,Y,beta,scale=original.source(0,config,support,"predictor_heteroskedastic")
    xx,yy,bb=independent.replay_XY(0,config,support,"predictor_heteroskedastic")
    np.testing.assert_array_equal(X,xx)
    np.testing.assert_allclose(Y,yy,rtol=1e-10,atol=1e-10)
    np.testing.assert_array_equal(beta[1],bb)
    q=original.common_masks(0,config,support,"predictor_heteroskedastic",X,Y)
    o=independent.masks(xx,yy,0,config,support,"predictor_heteroskedastic")
    for method in independent.MECHANISMS:
        np.testing.assert_array_equal(q[method],o[method])

def test_visible_pilot_and_assumed_delta_weighted_pointwise_numerical_identity():
    config="participant_standard";support="two_anchors";variance="predictor_heteroskedastic"
    X,Y,beta,scale=original.source(0,config,support,variance)
    masks=original.common_masks(0,config,support,variance,X,Y)
    full=independent.slope_with_support(X,Y,masks["complete"])
    original_rows=original.evaluate(0,config,support,variance)
    for row in original_rows:
        out=independent.evaluate_row(row,X,Y,beta[1],masks,full)
        assert out["refusal"]==row["grid_refused_count"]
    for d in independent.DELTA:
        v=original.weighted_pointwise(X,Y,masks["MNAR"],"MNAR",d,False)
        z=independent.trialwise_pointwise(X,Y,masks["MNAR"],"MNAR",d,False)
        np.testing.assert_array_equal(v[2],z[2])
        np.testing.assert_allclose(v[0],z[0],rtol=1e-8,atol=1e-8,equal_nan=True)
        np.testing.assert_allclose(v[1],z[1],rtol=1e-8,atol=1e-8,equal_nan=True)
    q=dict(original_rows[-1]);q["simulator_only_oracle"]=False
    with pytest.raises(ValueError,match="provenance"):
        independent.evaluate_row(q,X,Y,beta[1],masks,full)
    q=dict(original_rows[-1]);q["observation_mask_digest"]="wrong"
    with pytest.raises(ValueError,match="SHA256"):
        independent.evaluate_row(q,X,Y,beta[1],masks,full)

def test_fail_closed_sha256_and_missing_original_evidence(tmp_path):
    p=tmp_path/"fake";p.mkdir()
    (p/"evidence.json").write_text('{"source_checkout":"wrong","source_evaluations":[],"aggregate":{}}\n')
    (p/"source-commit.txt").write_text(independent.CHECKOUT+"\n")
    (p/"SHA256SUMS").write_text("corrupt\n")
    with pytest.raises(ValueError,match="SHA256"):
        independent.audit(p)
    from hashlib import sha256
    (p/"SHA256SUMS").write_text("".join(
        sha256((p/k).read_bytes()).hexdigest()+"  "+k+"\n"
        for k in ("evidence.json","source-commit.txt")))
    with pytest.raises(ValueError,match="manifest"):
        independent.audit(p)
