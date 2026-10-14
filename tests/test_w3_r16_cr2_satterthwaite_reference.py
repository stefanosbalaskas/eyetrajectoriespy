"""Small deterministic moment checks for conditional CR2 Satterthwaite df."""
import numpy as np
import pytest
from scripts.w3_r16_cr2_satterthwaite_reference import cr2_satterthwaite_reference
from scripts.w3_r16_cr2_correlated_target import cr2_correlated_wls

@pytest.mark.parametrize("rho",[0.,.35,.65])
def test_moments_and_positive_eigenvalues(rho):
    n=9;m=3
    x=np.repeat(np.linspace(-.8,.8,n),m)
    t=np.tile([.1,.5,.9],n)
    X=np.column_stack((np.ones(len(x)),x,t,x*t))
    weights=np.ones(len(x))
    g=np.repeat(np.arange(n),m)
    c=np.array([0.,1.,0.,.5])
    P=[(1-rho)*np.eye(m)+rho*np.ones((m,m)) for _ in range(n)]
    r=cr2_satterthwaite_reference(X,weights,g,c,P)
    ev=np.array(r["effective_eigenvalues"])
    assert 0<r["df"]<=n+1e-7
    np.testing.assert_allclose(r["expected_variance"],ev.sum(),rtol=1e-10)
    np.testing.assert_allclose(r["variance_of_variance"],2*(ev@ev),rtol=1e-10)
    assert not r["coverage_qualified"]

def test_scalar_rescaling_target_preserves_df():
    n=8;m=3
    x=np.repeat(np.linspace(-.8,.8,n),m)
    t=np.tile([.1,.5,.9],n)
    X=np.column_stack((np.ones(len(x)),x,t,x*t))
    g=np.repeat(np.arange(n),m)
    c=np.array([0.,1.,0.,.5])
    P=[.7*np.eye(m)+.3*np.ones((m,m)) for _ in range(n)]
    a=cr2_satterthwaite_reference(X,np.ones(len(x)),g,c,P)
    b=cr2_satterthwaite_reference(X,np.ones(len(x)),g,c,[5*p for p in P])
    np.testing.assert_allclose(a["df"],b["df"],rtol=1e-9)

def test_reject_singular_target():
    X=np.column_stack((np.ones(18),np.linspace(-1,1,18)))
    with pytest.raises(ValueError):
        cr2_satterthwaite_reference(X,np.ones(18),np.repeat(np.arange(6),3),
                                      np.array([0.,1.]),[np.zeros((3,3))]*6)
