"""R84 prospective validation-rescue identification diagnostics; no confidence bands."""
import numpy as np
import pytest
from scripts import run_w3_r84_external_validation as s


def test_fixed_new_validation_stream_and_strict_grid():
    assert s.SOURCE_SEED==202610218480
    assert s.OBS_SEED==202610218481
    assert s.RECOVERY_SEED==202610218482
    assert s.RECOVERY_LEVELS==(0.,.25,.50)
    assert s.N_SOURCES==256 and s.N_RECORDS==1536
    assert s.RECORDS_PER_SOURCE==6
    assert len({s.recovery_uniforms(b,c,a,v,np.zeros((1,1,31,2)))[1] for b in range(32)
                for c in s.CONFIGS for a in s.SUPPORT for v in s.VARIANCES})==256


@pytest.mark.parametrize("config",s.CONFIGS)
def test_mnar_and_mar_paired_source_outcomes_and_nested_recovery(config):
    X,y,beta,scale=s.source(0,config,"two_anchors","predictor_heteroskedastic")
    n,trials,design=s.info(config)
    assert X.shape==(n,2) and y.shape==(n,trials,31,2)
    assert np.isfinite(y).all()
    masks=s.common_masks(0,config,"two_anchors","predictor_heteroskedastic",X,y)
    assert s.native_refusal(X,y,masks["MNAR"],config)
    assert s.native_refusal(X,y,masks["MAR"],config)
    uniform,key=s.recovery_uniforms(0,config,"two_anchors","predictor_heteroskedastic",y)
    assert uniform.shape==y.shape
    for mechanism in s.LOSS_MECHANISMS:
        mask=masks[mechanism]
        p,good,counts=s.observed_pilot(X,y,mask)
        assert p.shape==(31,2,2) and good.shape==(31,2)
        assert np.any(good)
        a=mask&(uniform<.25)
        b=mask&(uniform<.5)
        assert np.all(a<=b)
        assert np.all(b<=mask)
        empty=s.recover_delta(X,y,mask,np.zeros_like(mask),p,good,0.)
        assert empty["delta_estimate"] is None
        assert empty["identified_with_external_validation"] is False
        for rate,validated in ((.25,a),(.5,b)):
            out=s.recover_delta(X,y,mask,validated,p,good,rate)
            assert out["included_measured_responses"]>0
            assert out["delta_estimate"] is not None
            assert np.isfinite(out["delta_estimate"])
            assert -4<=out["delta_estimate"]<=4
            assert abs(out["weighted_score_residual"])<1.e-6
            assert out["converged"] is True


def test_no_recovery_does_not_infer_delta_or_fake_simulator_identification():
    rows=s.evaluate(0,"curve_standard","two_anchors","predictor_heteroskedastic")
    assert len(rows)==6
    assert len({z["source_X_digest"] for z in rows})==1
    assert len({z["source_Y_digest"] for z in rows})==1
    assert len({z["original_mask_digest"] for z in rows})==2
    for m in s.LOSS_MECHANISMS:
        group=[z for z in rows if z["mechanism"]==m]
        assert [z["recovery_rate"] for z in group]==[0.,.25,.50]
        assert group[0]["delta_estimate"] is None
        assert group[0]["delta_abs_error"] is None
        assert group[0]["identified_with_external_validation"] is False
        assert group[0]["externally_recovered_count"]==0
        assert group[1]["externally_recovered_count"]<=group[2]["externally_recovered_count"]
        assert group[1]["recovered_missing_mask_digest"]!=group[2]["recovered_missing_mask_digest"]
        assert all(z["native_public_missing_gaze_refused"] for z in group)
        assert all(not z["source_known_truth_used_by_estimator"]
                   and not z["release_authorized"]
                   and z["no_interval_no_band_no_mnar_nonparametric_identification"] for z in group)
        assert {z["observed_only_pilot_digest"] for z in group}.__len__()==1


def test_incomplete_original_source_grid_and_invalid_shard_rejected(tmp_path):
    rows=s.evaluate(0,"curve_standard","two_anchors","constant")
    with pytest.raises(ValueError,match="incomplete"):
        s.summary(rows)
    with pytest.raises(ValueError,match="not pre-registered"):
        s.shard(tmp_path,1,5)
