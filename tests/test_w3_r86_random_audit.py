"""R86 preregistered new sources and genuinely independent audit of secondary failures."""
import numpy as np
import pytest
from scripts import run_w3_r86_random_audit as s


def test_new_independent_seeds_and_source_denominators():
    assert (s.SOURCE_SEED,s.OBS_SEED,s.RECOVERY_SEED,s.AUDIT_SEED)==(
        202610218680,202610218681,202610218682,202610218683)
    assert s.N_SOURCES==256 and s.N_RECORDS==4608 and s.RECORDS_PER_SOURCE==18
    assert s.AUDIT_LEVELS==(0.,.25,.5)
    assert s.STRATEGIES==("naive_union","audit_estimated","source_oracle_union")
    assert len({s.uniform_pair(b,c,a,v,(1,1,31,2))[2] for b in range(32)
                for c in s.CONFIGS for a in s.SUPPORT for v in s.VARIANCES})==256


@pytest.mark.parametrize("config",s.CONFIGS)
def test_new_sources_visible_pilot_and_true_missing_outcome_recovery(config):
    X,Y,beta,_=s.source(0,config,"two_anchors","predictor_heteroskedastic")
    n,trials,_=s.info(config)
    assert X.shape==(n,2) and Y.shape==(n,trials,31,2)
    assert np.isfinite(Y).all()
    orig=s.common_masks(0,config,"two_anchors","predictor_heteroskedastic",X,Y)
    U,V,_,_=s.uniform_pair(0,config,"two_anchors","predictor_heteroskedastic",Y.shape)
    true=s.actual_recovery_prob(X,Y)
    assert np.all((true>0)&(true<1)) and true.shape==Y.shape
    for m in s.LOSS_MECHANISMS:
        missing=orig[m]
        assert s.native_refusal(X,Y,missing,config)
        secondary=missing&(U<true)
        audit25=missing&(~secondary)&(V<.25)
        audit50=missing&(~secondary)&(V<.50)
        assert not np.any(secondary&audit50)
        assert np.all(audit25<=audit50)
        assert np.all(audit50<=missing)
        pilot,allowed,units=s.original_visible_pilot(X,Y,missing)
        assert pilot.shape==(31,2,2) and allowed.any()
        blank=s.estimate_recovery_selection(X,Y,missing,secondary,np.zeros_like(missing),pilot,allowed,0.)
        assert blank[0] is None and blank[1] is None and blank[2] is False
        for q,audited in ((.25,audit25),(.5,audit50)):
            alpha,gamma,ok,n,score,info,bound=s.estimate_recovery_selection(
                X,Y,missing,secondary,audited,pilot,allowed,q)
            assert ok and np.isfinite(alpha) and np.isfinite(gamma)
            assert abs(score)<1e-6 and info>0
            union=secondary|audited
            delta=s.first_stage_delta(X,Y,missing,union,pilot,allowed,np.full(Y.shape,.25+.75*q))
            assert delta[1] is True and -4<delta[0]<4


def test_source_paired_nine_strategies_per_original_mar_mnar_mask():
    rows=s.evaluate(0,"curve_standard","two_anchors","predictor_heteroskedastic")
    assert len(rows)==18
    assert len({z["source_X_digest"] for z in rows})==1
    assert len({z["source_Y_digest"] for z in rows})==1
    for m in s.LOSS_MECHANISMS:
        group=[z for z in rows if z["mechanism"]==m]
        assert len(group)==9
        for q in s.AUDIT_LEVELS:
            rr=[z for z in group if z["audit_fraction"]==q]
            assert [z["strategy"] for z in rr]==list(s.STRATEGIES)
            assert len({z["union_success_digest"] for z in rr})==1
            assert len({z["audit_success_digest"] for z in rr})==1
            assert all(z["actual_original_gaze_nans_refused"] and
                       z["unrecovered_outcomes_excluded_from_estimator"] and
                       not z["release_authorized"] and
                       not z["confidence_interval_or_band_validated"] and
                       not z["simulator_true_mean_used_in_fitted_pilot"] for z in rr)
            assert rr[2]["true_secondary_propensity_used_in_fitted_weights"]
            assert not rr[0]["true_secondary_propensity_used_in_fitted_weights"]
            if q==0:
                assert rr[1]["recovery_gamma_fit"] is None
                assert rr[1]["delta_estimate"] is None
            else:
                assert rr[1]["recovery_fit_converged"]
                assert rr[1]["recovery_gamma_fit"] is not None
                assert rr[1]["delta_estimate"] is not None


def test_incomplete_aggregate_and_invalid_preallocation_fail_closed(tmp_path):
    rows=s.evaluate(0,"curve_standard","two_anchors","constant")
    with pytest.raises(ValueError,match="source denominator"):
        s.summary(rows)
    with pytest.raises(ValueError,match="outside prospectively"):
        s.shard(tmp_path,1,5)
