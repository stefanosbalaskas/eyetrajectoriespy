"""R83 prospective visible-only missingness sensitivity, source identity and no-band gates."""
import numpy as np
import pytest
from scripts import run_w3_r83_observation_sensitivity as s

def test_fixed_new_sources_and_assumption_grid():
    assert s.SOURCE_SEED==202610218380 and s.OBS_SEED==202610218381
    assert s.N_SOURCES==256 and s.N_RECORDS==3328 and s.RECORDS_PER_SOURCE==13
    assert s.DELTA==(-1.1,-.55,0.,.55,1.1)
    assert s.WEIGHT_POSITIVITY==.02
    assert len({s.seed(b,c,a,v,"mask") for b in range(32) for c in s.CONFIGS
                for a in s.SUPPORT for v in s.VARIANCES})==256

@pytest.mark.parametrize("config",s.CONFIGS)
def test_fresh_sources_and_assumed_probabilities(config):
    X,Y,beta,scale=s.source(0,config,"two_anchors","predictor_heteroskedastic")
    n,trials,unit=s.info(config)
    assert X.shape==(n,2) and Y.shape==(n,trials,31,2)
    assert np.isfinite(Y).all()
    mask=s.common_masks(0,config,"two_anchors","predictor_heteroskedastic",X,Y)
    assert not mask["complete"].any()
    assert mask["MNAR"].any() and mask["MAR"].any()
    assert s.native_refusal(X,Y,mask["MNAR"],config)
    assert s.native_refusal(X,Y,mask["MAR"],config)
    d=s.weighted_pointwise(X,Y,mask["MNAR"],"MNAR",0.,False)
    assert len(d)==8 and d[0].shape==(31,2)
    assert 0<np.mean(d[2])<1
    for field in d[:5]:
        assert field.shape==(31,2)
    pilot=d[1];same=s.weighted_pointwise(X,Y,mask["MNAR"],"MNAR",1.1,False)
    np.testing.assert_allclose(pilot,same[1],equal_nan=True)
    visible=np.isfinite(d[0])&np.isfinite(same[0])
    assert np.any(visible)
    assert not np.allclose(d[0][visible],same[0][visible])
    oracle=s.weighted_pointwise(X,Y,mask["MNAR"],"MNAR",1.1,True)
    assert not np.allclose(oracle[0][visible],same[0][visible])

def test_complete_and_failed_local_support_do_not_get_sensitivity_estimates():
    X,Y,beta,_=s.source(0,"curve_standard","two_anchors","constant")
    complete=np.zeros(Y.shape,bool)
    d=s.pointwise_diagnostic(X,Y,complete,"curve_standard",beta)
    assert d["grid_estimable_count"]==62
    missing=complete.copy()
    missing[0,:,:,:]=True
    z=s.weighted_pointwise(X,Y,missing,"MAR",0.,False)
    assert z[2].all() and not np.isfinite(z[0]).any()

def test_thirteen_original_case_evaluations_with_fixed_mask_identity():
    rows=s.evaluate(0,"curve_standard","two_anchors","predictor_heteroskedastic")
    assert len(rows)==13
    assert {z["source_X_digest"] for z in rows}.__len__()==1
    assert {z["source_Y_digest"] for z in rows}.__len__()==1
    assert len({z["observation_mask_digest"] for z in rows})==4
    assert len([z for z in rows if z["method"]=="MAR_sensitivity"])==5
    assert len([z for z in rows if z["method"]=="MNAR_sensitivity"])==5
    assert len([z for z in rows if z["method"]=="MNAR_oracle"])==1
    assert rows[0]["grid_estimable_count"]==62
    assert rows[0]["observed_fraction"]==1.
    assert all(z["grid_refused_count"]+z["grid_estimable_count"]==62 for z in rows)
    assert all(z["not_identified_mnar_delta"] and z["no_90percent_calibration"]
               and z["no_missingness_corrected_confidence_band"]
               and not z["release_authorized"] for z in rows)
    spread={z["mnar_endpoint_mean_abs_slope_spread"] for z in rows
            if z["method"]=="MNAR_sensitivity"}
    assert len(spread)==1
    assert all(z["simulator_only_oracle"]==(z["method"]=="MNAR_oracle") for z in rows)

def test_frozen_source_denominator_and_no_invalid_shard(tmp_path):
    rows=s.evaluate(0,"curve_standard","two_anchors","constant")
    with pytest.raises(ValueError,match="missing or duplicated"):
        s.summary(rows)
    with pytest.raises(ValueError,match="not pre-registered"):
        s.shard(tmp_path,1,5)
    q=dict(rows[-1]);q["release_authorized"]=True
    assert q["release_authorized"] and not rows[-1]["release_authorized"]
