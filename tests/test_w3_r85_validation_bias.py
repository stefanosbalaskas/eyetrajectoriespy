"""R85 frozen external validation-bias sources, paired recovery and fail-closed fitting."""
import numpy as np
import pytest
from scripts import run_w3_r85_validation_bias as r


def test_frozen_new_source_denominators_and_seed_distinctness():
    assert r.SOURCE_SEED==202610218580
    assert r.OBS_SEED==202610218581
    assert r.RECOVERY_SEED==202610218582
    assert r.N_SOURCES==256 and r.N_RECORDS==2560 and r.RECORDS_PER_SOURCE==10
    assert r.RECOVERY_LAWS==("independent","recorded","latent")
    assert r.STRATEGIES==("independent_known","recorded_naive","recorded_correct","latent_naive","latent_oracle")
    seeds={r.rescue_uniforms(b,c,s,v,np.zeros((1,1,31,2)))[1] for b in range(32)
           for c in r.CONFIGS for s in r.SUPPORT for v in r.VARIANCES}
    assert len(seeds)==256


@pytest.mark.parametrize("config",r.CONFIGS)
def test_single_fresh_source_three_fixed_recovery_laws(config):
    X,Y,beta,scale=r.source(0,config,"two_anchors","predictor_heteroskedastic")
    n,trials,_=r.info(config)
    assert X.shape==(n,2) and Y.shape==(n,trials,31,2)
    assert np.isfinite(Y).all()
    masks=r.common_masks(0,config,"two_anchors","predictor_heteroskedastic",X,Y)
    U,seed=r.rescue_uniforms(0,config,"two_anchors","predictor_heteroskedastic",Y)
    assert U.shape==Y.shape and np.all((0<=U)&(U<1))
    P={x:r.recovery_probabilities(X,Y,x) for x in r.RECOVERY_LAWS}
    np.testing.assert_allclose(P["independent"],.25)
    assert np.all((P["recorded"]>0)&(P["recorded"]<1))
    assert np.all((P["latent"]>0)&(P["latent"]<1))
    assert not np.allclose(P["recorded"],P["latent"])
    Y2=Y+1.0
    np.testing.assert_allclose(P["recorded"],r.recovery_probabilities(X,Y2,"recorded"))
    assert not np.allclose(P["latent"],r.recovery_probabilities(X,Y2,"latent"))
    for mech in r.LOSS_MECHANISMS:
        mask=masks[mech]
        assert r.native_refusal(X,Y,mask,config)
        pilot,valid,units=r.original_visible_pilot(X,Y,mask)
        assert valid.any() and pilot.shape==(31,2,2)
        for law in r.RECOVERY_LAWS:
            recovery=mask&(U<P[law])
            assert not np.any(recovery&(~mask))
            out=r.weighted_delta(X,Y,mask,recovery,pilot,valid,np.full(Y.shape,.25))
            assert out[4]>0 and out[1]
            assert -4<=out[0]<=4 and abs(out[2])<1e-6


def test_five_strategy_rows_are_paired_source_and_oracle_is_explicit():
    rows=r.evaluate(0,"curve_standard","two_anchors","predictor_heteroskedastic")
    assert len(rows)==10
    assert len({z["source_X_digest"] for z in rows})==1
    assert len({z["source_Y_digest"] for z in rows})==1
    assert len({z["original_missing_mask_digest"] for z in rows})==2
    for m in r.LOSS_MECHANISMS:
        z=[x for x in rows if x["mechanism"]==m]
        assert [x["strategy"] for x in z]==list(r.STRATEGIES)
        assert z[1]["validation_mask_digest"]==z[2]["validation_mask_digest"]
        assert z[3]["validation_mask_digest"]==z[4]["validation_mask_digest"]
        assert z[1]["n_recovered"]==z[2]["n_recovered"]
        assert z[3]["n_recovered"]==z[4]["n_recovered"]
        assert all(x["no_inference_or_calibration_claim"] and x["validated_outcomes_not_imputed"]
                   and x["true_first_stage_delta_not_used_for_fitting"]
                   and x["original_public_regression_refused"]
                   and not x["release_authorized"] for x in z)
        assert [x["oracle_validation_propensity_used"] for x in z]==[False,False,False,False,True]
        assert all(x["delta_estimate"] is not None for x in z)
        assert all(x["converged"] for x in z)


def test_original_full_grid_and_no_recovery_refuse(tmp_path):
    X,Y,beta,_=r.source(0,"participant_standard","two_anchors","constant")
    m=r.common_masks(0,"participant_standard","two_anchors","constant",X,Y)["MNAR"]
    pilot,valid,counts=r.original_visible_pilot(X,Y,m)
    no=r.weighted_delta(X,Y,m,np.zeros_like(m),pilot,valid,np.full(Y.shape,.25))
    assert no[0] is None and no[1] is False
    with pytest.raises(ValueError,match="missing or duplicated"):
        r.summary(r.evaluate(0,"participant_standard","two_anchors","constant"))
    with pytest.raises(ValueError,match="not prespecified"):
        r.shard(tmp_path,1,5)
