"""Correlated-target CR2 numerical matrix identity contracts."""
import numpy as np
import pytest
from scripts.w3_r16_cr2_correlated_target import cr2_correlated_wls
from scripts.w3_r16_cr2_reference import cr2_wls_identity

def fixture(seed=131):
    rng=np.random.default_rng(seed)
    n=8;m=3
    x=np.repeat(np.linspace(-.8,.8,n),m)
    t=np.tile([.1,.5,.9],n)
    X=np.column_stack([np.ones(len(x)),x,t,x*t])
    y=X@np.array([.2,.7,-.1,.2])+rng.normal(size=len(x))*.15
    w=np.ones(len(x));g=np.repeat(np.arange(n),m)
    c=np.array([0.,1.,0.,.5])
    return X,y,w,g,c

def test_identity_target_matches_externally_validated_identity_cr2():
    X,y,w,g,c=fixture()
    phi=[np.eye(3) for _ in range(8)]
    a=cr2_correlated_wls(X,y,w,g,c,phi)
    b=cr2_wls_identity(X,y,w,g,c)
    np.testing.assert_allclose(a["cr2_se"],b["cr2_se"],rtol=2e-8,atol=2e-10)
    assert a["covariance_adjustment_error"]<1e-8
    assert a["covariance_adjustment_asymmetry"]<1e-10
    assert not a["reference_degrees_freedom_qualified"]

def test_correlated_target_reproduces_cluster_covariance_identity():
    X,y,w,g,c=fixture()
    r=.6
    phi=[(1-r)*np.eye(3)+r*np.ones((3,3)) for _ in range(8)]
    a=cr2_correlated_wls(X,y,w,g,c,phi)
    assert a["cr2_se"]>0
    assert a["covariance_adjustment_error"]<1e-8
    assert a["covariance_adjustment_asymmetry"]<1e-10
    assert a["clusters"]==8

def test_arbitrary_positive_weighting_and_targets():
    X,y,w,g,c=fixture(312)
    rng=np.random.default_rng(123)
    w=rng.uniform(.4,1.5,len(w))
    matrices=[rng.normal(size=(3,3)) for _ in range(8)]
    blocks=[A@A.T+np.eye(3)*.5 for A in matrices]
    a=cr2_correlated_wls(X,y,w,g,c,blocks)
    assert np.isfinite(a["cr2_se"])
    assert a["covariance_adjustment_error"]<1e-7

def test_invalid_target_rejected():
    X,y,w,g,c=fixture()
    with pytest.raises(ValueError,match="incorrect"):
        cr2_correlated_wls(X,y,w,g,c,[np.eye(2) for _ in range(8)])
    with pytest.raises(ValueError,match="nonpositive"):
        cr2_correlated_wls(X,y,w,g,c,[np.zeros((3,3)) for _ in range(8)])
