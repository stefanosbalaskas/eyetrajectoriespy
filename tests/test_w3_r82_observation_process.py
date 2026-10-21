"""R82 frozen MCAR/MAR/MNAR observation-process contract tests; no inference calibration."""
import json
import numpy as np
import pytest
from scripts import run_w3_r82_observation_process as r

def test_frozen_laws_and_all_source_streams():
    assert r.SOURCE_SEED==202610208280 and r.OBS_SEED==202610208281
    assert r.N_SOURCES==256 and r.N_CASES==1024 and r.BLOCKS==32
    assert r.MECHANISMS==("complete","MCAR","MAR","MNAR")
    assert len({r.seed(b,c,s,v,"mask") for b in range(32) for c in r.CONFIGS
                for s in r.SUPPORT for v in r.VARIANCES})==256
    with pytest.raises(ValueError,match="identity"):
        r.seed(32,"curve_standard","two_anchors","constant","source")
    with pytest.raises(ValueError,match="stream"):
        r.seed(0,"curve_standard","two_anchors","constant","unknown")

@pytest.mark.parametrize("config",r.CONFIGS)
def test_one_true_complete_source_and_mask_process(config):
    X,Y,beta,scale=r.source(0,config,"two_anchors","predictor_heteroskedastic")
    n,trials,unit=r.info(config)
    assert X.shape==(n,2) and Y.shape==(n,trials,31,2)
    assert beta.shape==(2,31,2)
    assert np.all(np.isfinite(Y))
    assert np.count_nonzero(X[:,1]==-4)==1
    assert np.count_nonzero(X[:,1]==4)==1
    assert np.allclose(scale,1+.75*np.abs(X[:,1]))
    masks=r.common_masks(0,config,"two_anchors","predictor_heteroskedastic",X,Y)
    assert not masks["complete"].any()
    assert 0.05<masks["MCAR"].mean()<.20
    assert masks["MAR"].shape==Y.shape
    assert masks["MNAR"].shape==Y.shape
    for name in r.MECHANISMS:
        assert masks[name].dtype==np.bool_
    assert r.common_masks(0,config,"two_anchors","predictor_heteroskedastic",X,Y)["MNAR"].tobytes()==masks["MNAR"].tobytes()
    # MCAR probabilities constant; MAR does NOT depend on Y; MNAR must.
    np.testing.assert_allclose(r.probabilities(X,Y,"MCAR"),.12)
    np.testing.assert_allclose(r.probabilities(X,Y,"MAR"),
                               r.probabilities(X,Y+1.2,"MAR"))
    assert not np.array_equal(r.probabilities(X,Y,"MNAR"),
                              r.probabilities(X,Y+1.2,"MNAR"))
    for m in ("MCAR","MAR","MNAR"):
        assert masks[m].any()
        assert r.native_refusal(X,Y,masks[m],config) is True
    assert r.native_refusal(X,Y,masks["complete"],config) is False
    full=r.pointwise_diagnostic(X,Y,masks["complete"],config,beta)
    assert full["grid_refused_count"]==0
    assert full["grid_estimable_count"]==62
    assert full["min_independent_units"]==n
    assert full["min_negative_anchors"]==1
    assert full["min_positive_anchors"]==1
    assert np.isfinite(full["mean_abs_slope_error"])

def test_participant_repeated_trial_native_units_not_pseudoreplicated():
    X,Y,beta,_=r.source(0,"participant_standard","two_anchors","constant")
    assert X.shape[0]==36 and Y.shape[:2]==(36,3)
    masks=np.zeros(Y.shape,bool)
    masks[0,0,0,0]=True
    native,obs=r.as_independent_units(Y,masks,"participant_standard")
    assert obs[0,0,0] and native.shape==(36,31,2)
    assert native[0,0,0]==pytest.approx(np.mean(Y[0,1:,0,0]))
    masks[0,:,0,0]=True
    native,obs=r.as_independent_units(Y,masks,"participant_standard")
    assert not obs[0,0,0] and np.isnan(native[0,0,0])

def test_grid_fail_closed_for_missing_influential_units_and_no_imputation():
    X,Y,beta,_=r.source(0,"curve_standard","two_anchors","constant")
    missing=np.zeros(Y.shape,bool)
    missing[0,:,:,:]=True   # the only negative extreme anchor
    z=r.pointwise_diagnostic(X,Y,missing,"curve_standard",beta)
    assert z["grid_refused_count"]==62
    assert z["grid_estimable_count"]==0
    assert z["mean_abs_slope_error"] is None
    assert all(v is None for row in z["pointwise_slope"] for v in row)

def test_original_observation_evaluations_and_source_identity():
    q=r.evaluate(0,"curve_standard","two_anchors","predictor_heteroskedastic")
    assert [z["mechanism"] for z in q]==list(r.MECHANISMS)
    assert len({z["source_X_digest"] for z in q})==1
    assert len({z["source_Y_digest"] for z in q})==1
    assert len({z["observed_mask_digest"] for z in q})==4
    assert [z["native_missingness_refusal"] for z in q]==[False,True,True,True]
    assert q[0]["gaze_observation_fraction"]==1.
    assert q[0]["grid_refused_count"]==0
    assert all(not z["release_authorized"] and z["no_band_calibration"]
               and z["not_an_MNAR_adjustment"] for z in q)
    for z in q:
        assert z["grid_refused_count"]+z["grid_estimable_count"]==62
        assert z["observed_gaze_samples"]+z["missing_gaze_samples"]==72*31*2
        assert z["source_seed"]==r.seed(0,z["config"],z["support"],z["variance"],"source")

def test_full_grid_identity_refusal_and_immutable_shard(tmp_path):
    q=r.evaluate(0,"curve_standard","two_anchors","constant")
    # Cannot claim a full factorial result with only one primitive source block.
    with pytest.raises(ValueError,match="incomplete or duplicated|missing or duplicated"):
        r.summary(q)
    with pytest.raises(ValueError,match="not pre-registered"):
        r.shard(tmp_path/"x",1,5)
    assert r.digest(np.ones((3,2)))==r.digest(np.ones((3,2)))
    assert r.mask_digest(np.ones((3,31,2),bool))!=r.mask_digest(np.zeros((3,31,2),bool))
    a=dict(q[0]);a["release_authorized"]=True
    assert a["release_authorized"]
