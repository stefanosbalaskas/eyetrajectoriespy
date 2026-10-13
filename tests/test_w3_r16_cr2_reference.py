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
