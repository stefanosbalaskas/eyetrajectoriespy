"""Numerical contracts for blockwise R17 CR2 and Satterthwaite reference."""
import numpy as np
import pytest
from scripts.w3_r17_cr2_blockwise import cr2_blockwise_wls
from scripts.w3_r16_cr2_correlated_target import cr2_correlated_wls
from scripts.w3_r16_cr2_satterthwaite_reference import cr2_satterthwaite_reference

@pytest.mark.parametrize("rho,unequal,weighted",[
    (0.,False,False),(.4,False,False),
    (.4,True,True),(.65,True,False)
])
def test_blockwise_matches_independent_dense_references(rho,unequal,weighted):
    rng=np.random.default_rng(41)
    counts=np.array([2+i%3 for i in range(9)]) if unequal else np.full(9,3)
    cl=np.repeat(np.arange(9),counts)
    n=len(cl)
    x=np.repeat(np.linspace(-.8,.8,9),counts)
    t=np.concatenate([np.linspace(.1,.9,j) for j in counts])
    X=np.column_stack([np.ones(n),x,t,x*t])
    y=X@np.array([.2,.7,-.1,.25])+rng.normal(size=n)*.2
    w=rng.uniform(.5,1.5,n) if weighted else np.ones(n)
    Ph=[(1-rho)*np.eye(m)+rho*np.ones((m,m)) for m in counts]
    for c in [np.array([0.,1.,0.,.5]), np.array([0.,0.,1.,0.])]:
        a=cr2_blockwise_wls(X,y,w,cl,c,Ph)
        b=cr2_correlated_wls(X,y,w,cl,c,Ph)
        d=cr2_satterthwaite_reference(X,w,cl,c,Ph)
        np.testing.assert_allclose(a["point"],b["point"],rtol=1e-9,atol=1e-10)
        np.testing.assert_allclose(a["cr2_se"],b["cr2_se"],rtol=1e-7,atol=1e-9)
        np.testing.assert_allclose(a["satterthwaite_df"],d["df"],rtol=1e-7,atol=1e-8)
        np.testing.assert_allclose(a["conditional_expectation"],d["expected_variance"],rtol=1e-7)
        assert a["expectation_identity_error"]<1e-7
        assert a["max_adjustment_covariance_error"]<1e-7
        assert a["max_adjustment_asymmetry"]<1e-10
        assert not a["pointwise_coverage_qualified"]
        assert not a["public_api_authorized"]

def test_reject_malformed_target_and_weight():
    X=np.column_stack([np.ones(18),np.linspace(-1,1,18)])
    y=np.arange(18,dtype=float)
    g=np.repeat(np.arange(6),3)
    c=np.array([0.,1.])
    with pytest.raises(ValueError):
        cr2_blockwise_wls(X,y,np.ones(18),g,c,[np.eye(2)]*6)
    with pytest.raises(ValueError):
        cr2_blockwise_wls(X,y,np.zeros(18),g,c,[np.eye(3)]*6)
