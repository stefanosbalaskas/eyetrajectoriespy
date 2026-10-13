"""Independent numerical checks for research-only CR2 working-identity B.R.L."""
import numpy as np
import pytest
from scripts.w3_r16_cr2_reference import cr2_wls_identity

@pytest.mark.parametrize("n,seed",[(12,10),(24,11),(48,12)])
def test_low_rank_adjustment_matches_direct_dense_cluster_oracle(n,seed):
    rng=np.random.default_rng(seed)
    x=np.repeat(rng.uniform(-.9,.9,n),3)
    t=np.tile(np.array([.11,.47,.93]),n)
    person=np.repeat(np.arange(n),3)
    X=np.column_stack([np.ones(len(x)),x,t,x*t])
    w=np.repeat(rng.uniform(.5,1.5,n),3)/3
    y=X@np.array([.2,.7,-.2,.5])+rng.standard_normal(len(x))*.2
    h=np.array([0.,1.,0.,.5])
    result=cr2_wls_identity(X,y,w,person,h)
    assert result["numerical_difference"]<1e-10
    assert result["cr2_se"]>0
    assert result["n_clusters"]==n
    assert 0<result["max_cluster_leverage"]<1
    assert not result["cr2_reference_df_qualified"]
    assert not result["public_api_authorized"]

def test_wls_scale_invariance():
    rng=np.random.default_rng(982)
    n=20
    person=np.repeat(np.arange(n),4)
    X=np.column_stack([np.ones(4*n),rng.uniform(-1,1,4*n)])
    y=X@np.array([1.,.4])+rng.normal(size=4*n)
    w=rng.uniform(.3,2,4*n)
    a=cr2_wls_identity(X,y,w,person,np.array([0.,1.]))
    b=cr2_wls_identity(X,y,17*w,person,np.array([0.,1.]))
    np.testing.assert_allclose(a["cr2_se"],b["cr2_se"],rtol=1e-9)
    np.testing.assert_allclose(a["point"],b["point"],rtol=1e-9)

def test_reject_nonpositive_weights():
    X=np.arange(12,dtype=float).reshape(6,2)
    with pytest.raises(ValueError,match="positive"):
        cr2_wls_identity(X,np.ones(6),np.zeros(6),np.repeat(range(3),2),np.array([1.,0.]))

def test_single_observation_clusters_reduce_to_hc2_exactly():
    rng=np.random.default_rng(1127)
    n=30
    x=np.linspace(-.8,.8,n)
    X=np.column_stack([np.ones(n),x])
    w=np.linspace(.65,1.45,n)
    y=0.4 + 0.8*x + rng.normal(0,.3,n)
    direction=np.array([0.,1.])
    result=cr2_wls_identity(X,y,w,np.arange(n),direction)
    Z=X*np.sqrt(w)[:,None]
    yw=y*np.sqrt(w)
    G=Z.T@Z
    b=np.linalg.solve(G,Z.T@yw)
    e=yw-Z@b
    h=np.einsum("ij,jk,ik->i",Z,np.linalg.inv(G),Z)
    assert np.all((h>=0)&(h<1))
    u=(Z* (e/np.sqrt(1-h))[:,None])
    independently=np.sqrt(direction@np.linalg.solve(G,u.T@u)@np.linalg.solve(G,direction))
    np.testing.assert_allclose(result["cr2_se"],independently,atol=1e-11,rtol=1e-10)

def test_invariance_under_reparameterization():
    rng=np.random.default_rng(212)
    n=32
    groups=np.repeat(np.arange(n),3)
    X=np.column_stack([np.ones(n*3),rng.normal(size=n*3),rng.normal(size=n*3)])
    y=X@np.array([.1,.3,-.2])+rng.normal(size=n*3)
    w=rng.uniform(.5,2.,size=n*3)
    c=np.array([0.,1.,0.])
    transform=np.array([[1.,.2,0.], [0.,1.4,.3], [0.,0.,.75]])
    a=cr2_wls_identity(X,y,w,groups,c)
    # Design reparameterized as X T; contrast must transform as T^T c.
    v=cr2_wls_identity(X@transform,y,w,groups,transform.T@c)
    np.testing.assert_allclose(a["cr2_se"],v["cr2_se"],atol=1e-10,rtol=1e-9)
