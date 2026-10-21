"""R86-A genuinely independently regenerated synthetic audit and double-selection roots."""
import numpy as np
import pytest
from scripts import run_w3_r86_random_audit as original
from scripts import audit_w3_r86_random_audit as independent


def test_frozen_source_identity_and_independent_denominator():
    assert independent.SOURCE_SEED==202610218680
    assert independent.OBS_SEED==202610218681
    assert independent.RECOVERY_SEED==202610218682
    assert independent.AUDIT_SEED==202610218683
    assert independent.RECORDS==4608
    assert independent.CHECKOUT=="21a3d42045f56d810d273c83f7e2be645a20160c"


@pytest.mark.parametrize("design",independent.CONFIGS)
@pytest.mark.parametrize("leverage",independent.SUPPORT)
def test_true_complete_XY_original_masks_and_both_random_fields(design,leverage):
    X,Y,beta,_=original.source(0,design,leverage,"predictor_heteroskedastic")
    xx,yy,_=independent.replay_XY(0,design,leverage,"predictor_heteroskedastic")
    np.testing.assert_array_equal(X,xx)
    np.testing.assert_allclose(Y,yy,atol=1e-10,rtol=1e-10)
    old=original.common_masks(0,design,leverage,"predictor_heteroskedastic",X,Y)
    new=independent.masks(xx,yy,0,design,leverage,"predictor_heteroskedastic")
    for m in ("MAR","MNAR"):np.testing.assert_array_equal(old[m],new[m])
    U,V,seedU,seedV=original.uniform_pair(0,design,leverage,"predictor_heteroskedastic",Y.shape)
    uu,vv,su,sv=independent.two_uniforms(0,design,leverage,"predictor_heteroskedastic",Y.shape)
    np.testing.assert_array_equal(U,uu)
    np.testing.assert_array_equal(V,vv)
    assert (seedU,seedV)==(su,sv)
    np.testing.assert_allclose(
        original.actual_recovery_prob(X,Y),
        independent.true_secondary_recovery(xx,yy),
        rtol=1e-11,atol=1e-11)


def test_independent_gamma_and_first_stage_delta_scores():
    c="participant_standard";v="predictor_heteroskedastic";s="two_anchors"
    X,Y,beta,_=original.source(0,c,s,v)
    mask=original.common_masks(0,c,s,v,X,Y)
    U,V,seedU,seedV=original.uniform_pair(0,c,s,v,Y.shape)
    rtrue=original.actual_recovery_prob(X,Y)
    rows=original.evaluate(0,c,s,v)
    for m in ("MAR","MNAR"):
        missing=mask[m]
        initial=missing&(U<rtrue)
        pilot,allowed,units=independent.visible_pilot_independently(X,Y,missing)
        op,oa,ou=original.original_visible_pilot(X,Y,missing)
        np.testing.assert_allclose(pilot,op,rtol=1e-10,atol=1e-10,equal_nan=True)
        np.testing.assert_array_equal(allowed,oa)
        np.testing.assert_array_equal(units,ou)
        for q in independent.AUDIT_LEVELS:
            third=missing&(~initial)&(V<q)
            total=initial|third
            for strategy in independent.STRATEGIES:
                z=next(x for x in rows if x["mechanism"]==m and x["audit_fraction"]==q
                       and x["strategy"]==strategy)
                independent.verify_one(z,X,Y,missing,initial,third,total,pilot,allowed,
                                       units,rtrue,(seedU,seedV))
        victim=next(x for x in rows if x["mechanism"]==m and x["strategy"]=="audit_estimated"
                    and x["audit_fraction"]==.25)
        wrong=dict(victim);wrong["recovery_gamma_fit"]=999
        third=missing&(~initial)&(V<.25)
        with pytest.raises(ValueError,match="gamma mismatch"):
            independent.verify_one(wrong,X,Y,missing,initial,third,initial|third,pilot,
                                   allowed,units,rtrue,(seedU,seedV))


def test_original_immutable_source_archive_fail_closed(tmp_path):
    p=tmp_path/"original";p.mkdir()
    (p/"evidence.json").write_text('{"original_checkout":"fake","source_evaluations":[],"aggregate":{}}\n')
    (p/"source-commit.txt").write_text(independent.CHECKOUT+"\n")
    (p/"SHA256SUMS").write_text("wrong\n")
    with pytest.raises(ValueError,match="SHA256"):
        independent.audit(p)
    from hashlib import sha256
    (p/"SHA256SUMS").write_text("".join(sha256((p/z).read_bytes()).hexdigest()+"  "+z+"\n"
                                     for z in ("evidence.json","source-commit.txt")))
    with pytest.raises(ValueError,match="manifest"):
        independent.audit(p)
