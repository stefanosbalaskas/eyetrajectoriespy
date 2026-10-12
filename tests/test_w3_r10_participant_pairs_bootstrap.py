"""W3 R10 independent participant pairs-bootstrap scientific source contracts."""
import json
from pathlib import Path
import sys
import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.run_w3_r10_participant_pairs_bootstrap import (
    BLOCKS,N_PARTICIPANTS,BOOTSTRAP_DRAWS,SCHEMES,LOSSES,TRUTHS,
    MODELS,INTERVALS,TIME,FOCAL,source,source_crossproducts,
    cluster_bootstrap,evaluate,audit,wilson
)


def test_original_generating_sources_share_recorded_values_not_fake_times():
    a=source(0,"balanced3","mcar","baseline")
    b=source(0,"balanced3","mcar","localized_bump")
    c=source(0,"balanced3","latent_response_dependent","baseline")
    for z in (b,c):
        np.testing.assert_array_equal(a[2],z[2])
        np.testing.assert_array_equal(a[3],z[3])
        np.testing.assert_array_equal(a[4],z[4])
        np.testing.assert_array_equal(a[6],z[6])
    for ta,tb in zip(a[0].time,b[0].time):
        np.testing.assert_array_equal(ta,tb)
    for (ta,va),(tc,vc) in zip(
        zip(a[0].time,a[0].values),zip(c[0].time,c[0].values)
    ):
        _,ia,ic=np.intersect1d(ta,tc,return_indices=True)
        assert len(ia)>=15
        np.testing.assert_array_equal(va[ia],vc[ic])


@pytest.mark.parametrize("model",MODELS)
def test_whole_participant_replication_equals_direct_group_crossproduct_fit(model):
    gaze,mu,x,u,trials,truth,k=source(0,"unbalanced1to3","mcar","baseline")
    gram,cross,contrast,theta,estimate,projection,qr,score,nobs=(
        source_crossproducts(gaze,mu,x,u,trials,model)
    )
    assert gram.shape==(N_PARTICIPANTS,len(theta),len(theta))
    assert cross.shape==(N_PARTICIPANTS,len(theta))
    assert qr<=4e-7 and score<=4e-7
    b=cluster_bootstrap(gram,cross,contrast,estimate,seed=135,draws=20)
    assert b["n_refits_completed"]==20
    multiplicity=np.asarray(b["original_draw_multiplicity_first"])
    assert int(multiplicity.sum())==N_PARTICIPANTS
    assert len(b["original_draw_indices_first"])==N_PARTICIPANTS
    # Independently reconstruct one participant-resampled WLS normal equation.
    manual_gram=sum((int(c)*m for c,m in zip(multiplicity,gram)),np.zeros_like(gram[0]))
    manual_cross=sum((int(c)*v for c,v in zip(multiplicity,cross)),np.zeros_like(cross[0]))
    direct=float(contrast@np.linalg.solve(manual_gram,manual_cross))
    np.testing.assert_allclose(b["first_refit_estimate"],direct,atol=2e-8,rtol=0)
    for typ in ("percentile","basic"):
        lo,hi=b[typ]
        assert np.isfinite([lo,hi]).all() and lo<=hi


@pytest.mark.parametrize("scheme",SCHEMES)
@pytest.mark.parametrize("loss",LOSSES)
@pytest.mark.parametrize("truth_mode",TRUTHS)
def test_original_source_cases_have_numerical_oracles_and_real_source_units(scheme,loss,truth_mode):
    r=evaluate(0,scheme,loss,truth_mode)
    assert r["status"]=="ok",r["exception"]
    assert r["native_source_unchanged"]
    assert r["dense_W3_rejected_native"]
    assert r["n_independent_participants"]==N_PARTICIPANTS
    assert len(r["models"])==len(MODELS)
    for model in MODELS:
        m=r["models"][model]
        assert m["source_qr_oracle_delta"]<=4e-7
        assert m["source_cluster_score_oracle_delta"]<=4e-7
        assert m["bootstrap_planned"]==BOOTSTRAP_DRAWS
        assert m["bootstrap_completed"]==BOOTSTRAP_DRAWS
        assert int(sum(m["first_resampled_multiplicity"]))==N_PARTICIPANTS
        assert len(m["first_resampled_source_cluster_indices"])==N_PARTICIPANTS
        for typ in INTERVALS:
            assert m["intervals"][typ]["width"]>0
            assert isinstance(m["intervals"][typ]["known_truth_included"],bool)
    assert json.loads(json.dumps(r))["status"]=="ok"
    assert not r["bootstrap_inference_qualified"]
    assert not r["familywise_functional_coverage_qualified"]


def test_each_participant_retain_all_native_trials_at_resampling_level():
    gaze,mu,x,u,trials,truth,k=source(1,"unbalanced1to3","mcar","baseline")
    assert len(np.unique(u))==N_PARTICIPANTS
    assert 1<=int(k.min())<int(k.max())<=3
    assert len(gaze.time)==sum(k)
    assert len(np.unique(trials))==len(gaze.time)
    for t,v in zip(gaze.time,gaze.values):
        assert len(t) in (len(TIME),len(TIME)-8)
        assert len(t)==len(v)
        assert np.all(np.diff(t)>0)


def test_source_seed_guard_and_failure_inclusive_original_mc_denominators():
    a=source(0,"balanced3","mcar","baseline")
    b=source(1,"balanced3","mcar","baseline")
    assert not np.array_equal(a[2],b[2])
    with pytest.raises(ValueError,match="outside"):
        source(BLOCKS,"balanced3","mcar","baseline")
    with pytest.raises(ValueError,match="unplanned"):
        source(0,"balanced3","mcar","posthoc")
    with pytest.raises(ValueError,match="unplanned"):
        source(0,"invalid","mcar","baseline")
    assert wilson(0,0) is None
    assert wilson(0,64)[0]==0
    assert wilson(64,64)[1]==1
    good=evaluate(0,"balanced3","mcar","baseline")
    failed=dict(good,loss="latent_response_dependent",status="failed",
                exception={"type":"IntentionalReferenceFailure"})
    report=audit([good,failed])
    assert report["planned_cases"]==BLOCKS*len(SCHEMES)*len(LOSSES)*len(TRUTHS)
    assert report["completed_cases"]==1 and report["failed_cases"]==1
    assert report["recorded_cases"]==2
    assert len(report["missing_cases"])==report["planned_cases"]-2
    assert not report["participant_bootstrap_calibration_qualified"]
    with pytest.raises(ValueError,match="duplicate"):
        audit([good,good])
