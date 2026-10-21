"""Independently coded W3 R85-A regression/selection and source tamper gates."""
import numpy as np
import pytest
from scripts import run_w3_r85_validation_bias as orig
from scripts import audit_w3_r85_validation_bias as independent


def test_exact_new_seeds_strategies_and_nonrelease_boundary():
    assert independent.SOURCE_SEED==202610218580
    assert independent.OBS_SEED==202610218581
    assert independent.RECOVERY_SEED==202610218582
    assert independent.SOURCE_STRATEGY_ROWS==2560
    assert independent.STRATEGIES==orig.STRATEGIES
    assert len({independent.validation_uniforms(b,c,s,v,(1,1,31,2))[1]
                for b in range(32) for c in independent.CONFIGS
                for s in independent.SUPPORT for v in independent.VARIANCES})==256


@pytest.mark.parametrize("config",independent.CONFIGS)
@pytest.mark.parametrize("support",independent.SUPPORT)
def test_independent_original_XY_MAR_MNAR_masks_and_three_recovery_laws(config,support):
    X,Y,beta,scale=orig.source(0,config,support,"predictor_heteroskedastic")
    xx,yy,_=independent.replay_XY(0,config,support,"predictor_heteroskedastic")
    np.testing.assert_array_equal(X,xx)
    np.testing.assert_allclose(Y,yy,rtol=1e-10,atol=1e-10)
    a=orig.common_masks(0,config,support,"predictor_heteroskedastic",X,Y)
    b=independent.masks(xx,yy,0,config,support,"predictor_heteroskedastic")
    for law in ("MAR","MNAR"):
        np.testing.assert_array_equal(a[law],b[law])
    u,seed=orig.rescue_uniforms(0,config,support,"predictor_heteroskedastic",Y)
    uu,other=independent.validation_uniforms(0,config,support,"predictor_heteroskedastic",Y.shape)
    np.testing.assert_array_equal(u,uu)
    assert seed==other
    for law in independent.LAWS:
        np.testing.assert_allclose(orig.recovery_probabilities(X,Y,law),
                                   independent.true_validation_prob(xx,yy,law),
                                   atol=1e-11,rtol=1e-11)


def test_original_and_independent_source_score_reconstruction():
    c="participant_standard";s="two_anchors";v="predictor_heteroskedastic"
    X,Y,beta,_=orig.source(0,c,s,v)
    masks=orig.common_masks(0,c,s,v,X,Y)
    U,key=orig.rescue_uniforms(0,c,s,v,Y)
    rows=orig.evaluate(0,c,s,v)
    for m in ("MAR","MNAR"):
        missing=masks[m]
        p,valid,units=independent.observed_pilot_independent(X,Y,missing)
        q,allowed,native=orig.original_visible_pilot(X,Y,missing)
        np.testing.assert_allclose(p,q,atol=1e-10,rtol=1e-10,equal_nan=True)
        np.testing.assert_array_equal(valid,allowed)
        np.testing.assert_array_equal(units,native)
        for name in orig.STRATEGIES:
            z=next(x for x in rows if x["mechanism"]==m and x["strategy"]==name)
            independent.check_case(z,X,Y,missing,p,valid,units,U,key)
        z=next(x for x in rows if x["mechanism"]==m and x["strategy"]=="latent_oracle")
        altered=dict(z);altered["oracle_validation_propensity_used"]=False
        with pytest.raises(ValueError,match="provenance"):
            independent.check_case(altered,X,Y,missing,p,valid,units,U,key)
        altered=dict(z);altered["validation_mask_digest"]="wrong"
        with pytest.raises(ValueError,match="SHA256|provenance"):
            independent.check_case(altered,X,Y,missing,p,valid,units,U,key)


def test_immutable_original_archive_tamper_rejection(tmp_path):
    base=tmp_path/"original"
    base.mkdir()
    (base/"evidence.json").write_text('{"original_checkout":"bad","source_evaluations":[],"aggregate":{}}\n')
    (base/"source-commit.txt").write_text("f"*40+"\n")
    (base/"SHA256SUMS").write_text("invalid\n")
    with pytest.raises(ValueError,match="SHA256"):
        independent.audit(base,"f"*40)
    from hashlib import sha256
    (base/"SHA256SUMS").write_text("".join(
        sha256((base/k).read_bytes()).hexdigest()+"  "+k+"\n"
        for k in ("evidence.json","source-commit.txt")))
    with pytest.raises(ValueError,match="manifest|checkout"):
        independent.audit(base,"f"*40)
