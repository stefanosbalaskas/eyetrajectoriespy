"""R87 source, audit-response, score weighting and failure-inclusive contracts."""
import hashlib
import json

import numpy as np
import pytest

from scripts import run_w3_r87_audit_return_nonresponse as r87
from scripts import run_w3_r86_random_audit as r86


def test_frozen_new_independent_source_and_factorial():
    assert r87.BLOCKS==32
    assert r87.CONFIGS==("curve_standard","participant_standard")
    assert r87.SUPPORT==("two_anchors",)
    assert r87.VARIANCES==("predictor_heteroskedastic",)
    assert r87.AUDIT_LEVELS==(.25,.5)
    assert r87.RETURN_LAWS==("complete","recorded","outcome")
    assert r87.STRATEGIES==(
        "assignment_only","recorded_propensity","outcome_oracle")
    assert r87.RECORDS_PER_SOURCE==36
    assert r87.N_SOURCES==64
    assert r87.N_RECORDS==2304
    assert len(r87.SHARDS)==8
    assert len({r87.SOURCE_SEED,r87.OBS_SEED,r87.RECOVERY_SEED,
                r87.AUDIT_SEED,r87.AUDIT_RETURN_SEED,
                r86.SOURCE_SEED,r86.AUDIT_SEED})==7
    with pytest.raises(ValueError,match="source identity"):
        r87.source(32,"curve_standard","two_anchors",
                   "predictor_heteroskedastic")


def test_new_source_pair_and_audit_nonresponse_mechanisms():
    c,s,v="curve_standard","two_anchors","predictor_heteroskedastic"
    X,Y,beta,_=r87.source(0,c,s,v)
    _,oldY,_,_=r86.source(0,c,s,v)
    assert not np.array_equal(Y,oldY)
    assert Y.shape==(72,1,31,2)
    mask=r87.common_masks(0,c,s,v,X,Y)["MNAR"]
    pilot,valid,_=r87.original_visible_pilot(X,Y,mask)
    a=r87.completion_probability(X,Y,pilot,"complete")
    b=r87.completion_probability(X,Y,pilot,"recorded")
    d=r87.completion_probability(X,Y,pilot,"outcome")
    assert np.array_equal(a,np.ones_like(Y))
    assert (b>0).all() and (b<1).all()
    assert (d>0).all() and (d<1).all()
    assert d.shape==b.shape
    assert not np.array_equal(d,b)
    u,seed=r87.return_uniform(0,c,s,v,Y.shape)
    uu,ss=r87.return_uniform(0,c,s,v,Y.shape)
    assert seed==ss
    np.testing.assert_array_equal(u,uu)
    with pytest.raises(ValueError,match="return law"):
        r87.completion_probability(X,Y,pilot,"unknown")


def test_original_secondary_model_suppresses_unmeasured_failed_audit_y():
    c,s,v="curve_standard","two_anchors","predictor_heteroskedastic"
    X,Y,_,_=r87.source(0,c,s,v)
    missing=r87.common_masks(0,c,s,v,X,Y)["MAR"]
    pilot,valid,_=r87.original_visible_pilot(X,Y,missing)
    U,V,_,_=r87.uniform_pair(0,c,s,v,Y.shape)
    W,_=r87.return_uniform(0,c,s,v,Y.shape)
    p=r87.actual_recovery_prob(X,Y)
    initial=missing&(U<p)
    assigned=missing&(~initial)&(V<.5)
    returned=assigned&(W<r87.completion_probability(
        X,Y,pilot,"recorded"))
    assert np.sum(returned)<=np.sum(assigned)
    assert not np.any(initial&returned)
    candidate=np.full(Y.shape,.5)
    a,g,ok,n,score,info,bound=r87.propensity_model(
        X,Y,missing,initial,returned,pilot,valid,candidate)
    assert n>0 and (ok or a is None)
    # Exactly the same measured data with a different assumed
    # assignment/completion probability changes the fitted score.
    candidate2=.5*r87.completion_probability(X,Y,pilot,"recorded")
    x=r87.propensity_model(
        X,Y,missing,initial,returned,pilot,valid,candidate2)
    assert x[3]==n
    assert all(z is not None for z in [x[3],x[5]])
    with pytest.raises(TypeError):
        r87.propensity_model()


def _refused_grid():
    rows=[]
    for b in range(r87.BLOCKS):
        for c in r87.CONFIGS:
            for m in r87.LOSS_MECHANISMS:
                for q in r87.AUDIT_LEVELS:
                    for law in r87.RETURN_LAWS:
                        for strategy in r87.STRATEGIES:
                            rows.append({
                                "study":r87.STUDY,
                                "block":b,"config":c,
                                "support":r87.SUPPORT[0],
                                "variance":r87.VARIANCES[0],
                                "mechanism":m,"audit_fraction":q,
                                "audit_return_law":law,"strategy":strategy,
                                "source_seed":r87.seed(
                                    b,c,r87.SUPPORT[0],
                                    r87.VARIANCES[0],"source"),
                                "mask_seed":r87.seed(
                                    b,c,r87.SUPPORT[0],
                                    r87.VARIANCES[0],"mask"),
                                "release_authorized":False,
                                "confidence_interval_or_band_validated":False,
                                "unreturned_outcomes_not_used_in_fitted_scores":True,
                                "first_stage_delta_converged":False,
                                "first_stage_delta_fit":None,
                                "recovery_fit_converged":False,
                                "recovery_gamma_fit":None,
                                "audit_assigned":0,"audit_returned":0,
                                "audit_failed_return":0,
                                "first_stage_delta_abs_error":None,
                            })
    return rows


def test_failure_inclusive_source_denominators_and_mutations():
    rows=_refused_grid()
    report=r87.summary(rows)
    assert len(rows)==2304
    assert report["third_stage_strategy_records"]==2304
    assert report["complete_synthetic_source_conditions"]==64
    assert report["MAR_MNAR_source_masks"]==128
    assert not report["release_authorized"]
    for c in r87.CONFIGS:
        for m in r87.LOSS_MECHANISMS:
            for q in r87.AUDIT_LEVELS:
                for law in r87.RETURN_LAWS:
                    for strategy in r87.STRATEGIES:
                        v=report["results"][c][m][str(q)][law][strategy]
                        assert v["independent_original_source_blocks"]==32
                        assert v["source_first_stage_fit_refusals"]==32
    with pytest.raises(ValueError,match="denominator"):
        r87.summary(rows[:-1])
    rows=_refused_grid()
    rows[0]["release_authorized"]=True
    with pytest.raises(ValueError,match="release gate"):
        r87.summary(rows)


def test_one_real_source_preserves_audit_subset_and_bounds():
    results=r87.evaluate(0,"curve_standard",
                         "two_anchors","predictor_heteroskedastic")
    assert len(results)==36
    for row in results:
        assert row["audit_returned"]<=row["audit_assigned"]
        assert row["audit_failed_return"]==(
            row["audit_assigned"]-row["audit_returned"])
        assert not row["release_authorized"]
        assert not row["confidence_interval_or_band_validated"]
        assert row["unreturned_outcomes_not_used_in_fitted_scores"]
        assert row["true_first_stage_delta_source_only"] in (0.,1.1)
    assert len({r["original_X_digest"] for r in results})==1
    assert len({r["original_Y_digest"] for r in results})==1
