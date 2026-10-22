"""Independent R92-A new-source, response-law, observed-only and archive gates."""
from pathlib import Path
import numpy as np
import pytest
from scripts import audit_w3_r92_original_return_fragility_independent as a
from scripts import run_w3_r92_return_fragility as original


def test_frozen_identity_source_and_randomness():
    assert a.EXPECTED_ROWS==14336
    assert a.ORIGINAL_CHECKOUT=="2b0c29cbe342919c204c445be4f80639b2261efb"
    assert a.SOURCE_SEEDS==original.SEEDS
    assert a.SCENARIOS==original.SCENARIOS
    assert a.REPETITIONS==8
    for config in a.CONFIGS:
        x,Y,mu=a.source(0,config)
        X,Yorig,mean=original.generate(0,config)
        np.testing.assert_array_equal(x,X)
        np.testing.assert_allclose(Y,Yorig,atol=1e-12,rtol=1e-12)
        np.testing.assert_allclose(mu,mean,atol=1e-12,rtol=1e-12)
        assert a.sha_float(Y)==original.digest(Yorig)
        U=a.uniform(0,config,"mask",Y.shape)
        for law in a.MECHANISMS:
            M=a.stage_one(x,Y,mu,U,law)
            same=original.first_stage_missing(X,Yorig,mean,U,law)
            np.testing.assert_array_equal(M,same)
        p,q=a.paired_uniforms(0,config,0,Y.shape)
        s,t=original.paired_audit_uniforms(0,config,0,Y.shape)
        np.testing.assert_array_equal(p,s)
        np.testing.assert_array_equal(q,t)


def test_completeness_nominal_uniform_oracle_controls():
    Y=np.array([-.8,-.1,.4,3.])
    for law,d in a.SCENARIOS:
        c=a.return_chance(Y,law,d)
        np.testing.assert_allclose(c,original.actual_return_probability(Y,law,d))
        assert np.all((c>=0)&(c<=1))
        if law=="complete":
            np.testing.assert_array_equal(c,np.ones_like(Y))
        if law=="uniform":
            np.testing.assert_array_equal(c,np.full_like(Y,1-d))


def test_independent_observed_y_only_leakage_rejection():
    M=np.array([1,1,1,1],bool)
    S=np.array([1,0,0,0],bool)
    R=np.array([0,1,0,0],bool)
    visible=np.array([-.2,.6,np.nan,np.nan])
    estimate=a.visible_ht(visible,M,S,R,.25,.05)
    fitted=original.observed_only_nominal_ht(visible,M,S,R,.25,.05)
    assert estimate[0]==pytest.approx(fitted["assignment_only"])
    assert estimate[1]==pytest.approx(fitted["nominal_uniform_completion"])
    assert estimate[2]==pytest.approx(.5)
    with pytest.raises(ValueError,match="hidden unreturned outcome leaked"):
        a.visible_ht(np.array([-.2,.6,.5,np.nan]),M,S,R,.25,.05)
    with pytest.raises(ValueError,match="provenance"):
        a.visible_ht(visible,M,S,S,.25,.05)
    with pytest.raises(ValueError,match="actual original archive incomplete"):
        a.audit(Path("/nonexistent/original-r92-folder"))


def test_one_source_all_scenarios_against_independent_equations():
    config="independent_curves"
    X,Y,mu=a.source(0,config)
    mu0=a.uniform(0,config,"mask",Y.shape)
    sec0=a.uniform(0,config,"secondary",Y.shape)
    archived=original.evaluate(0,config)
    assert len(archived)==2*8*2*7
    for law in a.MECHANISMS:
        M=a.stage_one(X,Y,mu,mu0,law)
        S=a.secondary_success(Y,mu,M,sec0)
        U,V=a.paired_uniforms(0,config,0,Y.shape)
        for g in a.ASSIGNMENT_FRACTIONS:
            assigned=(M&~S)&(U<g)
            for completion,d in a.SCENARIOS:
                chance=a.return_chance(Y,completion,d)
                actual=assigned&(V<chance)
                row=next(r for r in archived if
                         (r["mechanism"],r["rep"],r["g"],r["return_law"],
                          r["nominal_failure"])==(law,0,g,completion,d))
                result=a.validate_record(row,(0,config,law,0,g,completion,d),
                                         X,Y,M,S,assigned,actual,chance)
                assert np.isfinite(result[0]) and np.isfinite(result[1])
