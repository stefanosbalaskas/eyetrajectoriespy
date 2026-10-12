"""W3 R8 independent participant-cluster and mean-model uncertainty contracts."""
import json
from pathlib import Path
import sys
import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.run_w3_r8_cluster_inference_model_stress import (
    BLOCKS, N, SCHEMES, LOSSES, TRUTHS, METHODS, FOCAL_TIME, TIME,
    original_source,weighted_source_design,fit_pointwise_cluster_variances,
    evaluate,audit,wilson,bump,
)


def test_fresh_block_pairing_and_scenario_source_truth():
    original={}
    for sch in SCHEMES:
        for loss in LOSSES:
            for truth_mode in TRUTHS:
                r=original_source(0,sch,loss,truth_mode)
                original[(sch,loss,truth_mode)]=r
                gaze,mu,x,u,q,true,k,missing=r
                assert len(set(u))==N
                assert len(q)==int(k.sum())
                assert np.array_equal(q,np.unique(q))
                assert np.isfinite(np.concatenate(gaze.values)).all()
                for i,(tt,yy) in enumerate(zip(gaze.time,gaze.values)):
                    assert np.all(np.diff(tt)>0)
                    assert len(tt) in (len(TIME),len(TIME)-8)
                    assert len(tt)==len(yy)
    a=original[("balanced3","mcar","baseline")]
    b=original[("balanced3","mcar","localized_bump")]
    assert np.array_equal(a[6],b[6]) and np.array_equal(a[7],b[7])
    assert np.array_equal(a[2],b[2])
    np.testing.assert_allclose(b[5][1,FOCAL_TIME,0]-a[5][1,FOCAL_TIME,0],bump(TIME[FOCAL_TIME]))
    # Noise/participant effects and loss uniforms are reused across mean-truth regimes.
    for xa,xb in zip(a[1],b[1]):
        assert len(xa)==len(xb)
    assert not np.array_equal(np.vstack(a[0].values),np.vstack(b[0].values))


@pytest.mark.parametrize("scheme",SCHEMES)
@pytest.mark.parametrize("loss",LOSSES)
@pytest.mark.parametrize("truth_mode",TRUTHS)
def test_actual_sandwich_source_and_observation_cluster_membership(scheme,loss,truth_mode):
    r=evaluate(0,scheme,loss,truth_mode)
    assert r["status"]=="ok",r["exception"]
    assert r["native_source_preserved"]
    assert r["existing_W3_rejects_native"]
    assert r["qr_max_discrepancy"]<=3e-8
    assert r["n_independent_participants"]==N
    assert r["n_points"]>N
    assert np.isfinite(r["model_projection_bias"])
    assert isinstance(r["methods"]["participant_cr1"]["included_known_truth"],bool)
    assert r["methods"]["naive_hc1"]["n_claimed_clusters"]==r["n_points"]
    assert r["methods"]["trial_cr1"]["n_claimed_clusters"]==r["n_trials"]
    assert r["methods"]["participant_cr1"]["n_claimed_clusters"]==N
    assert all(r["methods"][m]["se"]>0 for m in METHODS)
    assert not r["cluster_inference_qualified"]
    assert not r["valid_90pct_simultaneous_band"]
    assert json.loads(json.dumps(r))["status"]=="ok"


def test_participant_weights_total_one_independent_person_even_with_unequal_trials():
    source=original_source(1,"unbalanced1to3","mcar")
    X,Y,mean,w,units,trials=weighted_source_design(
        source[0],source[1],source[2],source[3],source[4]
    )
    assert X.shape[1]==12
    assert len(Y)==len(w)==len(units)==len(trials)
    np.testing.assert_allclose(np.bincount(units,weights=w,minlength=N),1.)
    assert len(np.unique(units))==N
    assert len(np.unique(trials))==len(source[0].curve_ids)
    assert len(np.unique(trials))>N


def test_participant_level_sandwich_not_observation_level_when_trials_cluster():
    source=original_source(0,"balanced3","mcar","baseline")
    _,_,se,interval,delta,n=fit_pointwise_cluster_variances(
        source[0],source[1],source[2],source[3],source[4]
    )
    assert se["participant_cr1"]!=se["naive_hc1"]
    assert interval["participant_cr1"]["groups"]==N
    assert interval["trial_cr1"]["groups"]==3*N
    assert interval["naive_hc1"]["groups"]==n
    assert interval["participant_cr1"]["critical"]>interval["trial_cr1"]["critical"]
    assert delta<=3e-8


def test_pointwise_wilson_finite_and_failure_inclusive_source_contract():
    assert wilson(0,0) is None
    assert wilson(0,64)[0]==0
    assert wilson(64,64)[1]==1
    a=evaluate(0,"balanced3","mcar","baseline")
    b=dict(a,loss="latent_response_dependent",status="failed",
           exception={"type":"ControlledOriginalSourceFailure"})
    info=audit([a,b])
    assert info["planned_cases"]==BLOCKS*len(SCHEMES)*len(LOSSES)*len(TRUTHS)
    assert info["recorded_cases"]==2
    assert info["completed_cases"]==1
    assert info["failed_cases"]==1
    assert len(info["missing_cases"])==info["planned_cases"]-2
    assert info["groups"]["balanced3"]["mcar"]["baseline"]["attempted"]==BLOCKS
    assert not info["scientific_cluster_calibration_qualified"]
    with pytest.raises(ValueError,match="duplicate"):
        audit([a,a])


def test_invalid_or_future_generation_never_silently_included():
    with pytest.raises(ValueError,match="outside"):
        original_source(BLOCKS,"balanced3","mcar","baseline")
    with pytest.raises(ValueError,match="not in"):
        original_source(0,"balanced3","mcar","after_observing_outcomes")
    a=original_source(0,"balanced3","mcar","baseline")
    b=original_source(1,"balanced3","mcar","baseline")
    assert not np.array_equal(a[2],b[2])
