"""R84-A independently implemented original-source and rescue-score numerical contracts."""
import numpy as np
import pytest
from scripts import run_w3_r84_external_validation as source
from scripts import audit_w3_r84_independent_recovery as audit


def test_frozen_independent_original_source_identity():
    assert audit.SOURCE_SEED==202610218480
    assert audit.OBS_SEED==202610218481
    assert audit.RECOVERY_SEED==202610218482
    assert audit.RECORD_COUNT==1536
    assert audit.CHECKOUT=="6170c5b5941f55a5083cf57dc11293a229d2f9e1"


@pytest.mark.parametrize("config",audit.CONFIGS)
@pytest.mark.parametrize("support",audit.SUPPORT)
def test_separate_original_XY_selection_masks_and_nested_recoveries(config,support):
    orig=source.source(0,config,support,"predictor_heteroskedastic")
    X,Y,beta=audit.replay_XY(0,config,support,"predictor_heteroskedastic")
    np.testing.assert_array_equal(X,orig[0])
    np.testing.assert_allclose(Y,orig[1],atol=1e-11,rtol=1e-11)
    old=source.common_masks(0,config,support,"predictor_heteroskedastic",orig[0],orig[1])
    new=audit.masks(X,Y,0,config,support,"predictor_heteroskedastic")
    for m in audit.LOSS_MECHANISMS:
        np.testing.assert_array_equal(old[m],new[m])
    u,k=audit.rescue_uniforms(0,config,support,"predictor_heteroskedastic",Y.shape)
    v,j=source.recovery_uniforms(0,config,support,"predictor_heteroskedastic",orig[1])
    np.testing.assert_array_equal(u,v)
    assert k==j
    assert np.all((new["MNAR"]&(u<.25))<=(new["MNAR"]&(u<.5)))


def test_independent_visible_only_pilot_and_weighted_bisection_agree():
    config="participant_standard";support="two_anchors";variance="predictor_heteroskedastic"
    X,Y,beta,_=source.source(0,config,support,variance)
    masks=source.common_masks(0,config,support,variance,X,Y)
    u,key=source.recovery_uniforms(0,config,support,variance,Y)
    for m in audit.LOSS_MECHANISMS:
        mask=masks[m]
        pilot,good,counts=audit.pilot_from_visible(X,Y,mask)
        orig_p,orig_good,orig_count=source.observed_pilot(X,Y,mask)
        np.testing.assert_allclose(pilot,orig_p,equal_nan=True,atol=1e-11,rtol=1e-11)
        np.testing.assert_array_equal(good,orig_good)
        np.testing.assert_array_equal(counts,orig_count)
        rows=source.evaluate(0,config,support,variance)
        for rate in audit.RECOVERY_RATES:
            row=next(z for z in rows if z["mechanism"]==m and z["recovery_rate"]==rate)
            out=audit.check_row(row,X,Y,mask,pilot,good,counts,u,key)
            assert out["recovery_rate"]==rate
        z=next(q for q in rows if q["mechanism"]==m and q["recovery_rate"]==.25)
        bad=dict(z);bad["source_known_truth_used_by_estimator"]=True
        with pytest.raises(ValueError,match="provenance"):
            audit.check_row(bad,X,Y,mask,pilot,good,counts,u,key)
        bad=dict(z);bad["recovered_missing_mask_digest"]="wrong"
        with pytest.raises(ValueError,match="SHA256"):
            audit.check_row(bad,X,Y,mask,pilot,good,counts,u,key)


def test_original_immutable_archive_is_fail_closed(tmp_path):
    d=tmp_path/"orig";d.mkdir()
    (d/"evidence.json").write_text('{"source_checkout":"fake","source_evaluations":[],"aggregate":{}}\n')
    (d/"source-commit.txt").write_text(audit.CHECKOUT+"\n")
    (d/"SHA256SUMS").write_text("tamper\n")
    with pytest.raises(ValueError,match="SHA256"):
        audit.audit(d)
    from hashlib import sha256
    (d/"SHA256SUMS").write_text("".join(sha256((d/k).read_bytes()).hexdigest()+"  "+k+"\n"
                                     for k in ("evidence.json","source-commit.txt")))
    with pytest.raises(ValueError,match="checkout"):
        audit.audit(d)
