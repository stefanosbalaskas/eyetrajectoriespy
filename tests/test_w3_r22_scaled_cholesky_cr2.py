"""R22 independent numerical contracts: reference CR2, scaling, high precision."""
import numpy as np
import pytest
from scipy.linalg import cholesky

from scripts.w3_r22_scaled_cholesky_cr2 import (
    UnstableCR2Adjustment,scaled_symmetric_adjustment,stable_cr2_blockwise_wls)
from scripts.w3_r17_cr2_blockwise import cr2_blockwise_wls
from scripts import run_w3_r17_fresh_feasibility as source
from scripts import run_w3_r16_leverage_covariance_factorial as r16


def test_absolute_scale_invariance_and_a_d_aT_identity():
    g=np.random.default_rng(2026101522)
    V=g.normal(size=(7,7));Q=g.normal(size=(7,7))
    D=V@V.T+.5*np.eye(7)
    Phi=Q@Q.T+.2*np.eye(7)
    A,diagnostics=scaled_symmetric_adjustment(Phi,D)
    np.testing.assert_allclose(A@D@A.T,Phi,rtol=2e-10,atol=2e-10)
    for scalar in (1e-7,1e-3,1e6):
        scaled,check=scaled_symmetric_adjustment(scalar*Phi,scalar*D)
        np.testing.assert_allclose(scaled,A,rtol=1e-9,atol=1e-9)
        assert check["relative_identity_error"]<1e-9
    # Previously product eigenvalues << absolute 1e-11: new algorithm
    # succeeds because this is strictly a common change of covariance scale.
    small,check=scaled_symmetric_adjustment(1e-9*Phi,1e-9*D)
    np.testing.assert_allclose(small,A,rtol=1e-9,atol=1e-9)
    assert diagnostics["symmetric_spd"]


def test_high_precision_independent_symmetric_geometric_mean():
    mp=pytest.importorskip("mpmath")
    mp.mp.dps=75
    Phi=np.array([[3.,.6,.12],[.6,1.4,.07],[.12,.07,.5]])
    D=np.array([[2.2,.2,.09],[.2,1.1,.05],[.09,.05,.3]])
    observed,_=scaled_symmetric_adjustment(Phi,D)
    # Independent 75-decimal arithmetic, using mpmath's own Cholesky/eigsy.
    pp=mp.matrix([[mp.mpf(float(x)) for x in row] for row in Phi])
    dd=mp.matrix([[mp.mpf(float(x)) for x in row] for row in D])
    L=mp.cholesky(dd)
    C=L.T*pp*L
    eigen,Q=mp.eigsy(C)
    B=Q*mp.diag([mp.sqrt(v) for v in eigen])*Q.T
    A=L.T**-1*B*L**-1
    truth=np.asarray([[float(A[i,j]) for j in range(3)] for i in range(3)])
    np.testing.assert_allclose(observed,truth,rtol=2e-11,atol=2e-11)


def test_ill_conditioned_product_is_refused_not_regularized():
    Phi=np.diag([1.,1e-13])
    D=np.diag([1.,1e-13])
    with pytest.raises(UnstableCR2Adjustment,match="condition"):
        scaled_symmetric_adjustment(Phi,D)
    with pytest.raises((UnstableCR2Adjustment,ValueError)):
        scaled_symmetric_adjustment(Phi,np.array([[1.,0],[0.,-1.]]))


@pytest.mark.parametrize("support,model",[
    ("ordinary_independent","legendre5"),
    ("ordinary_dependent","legendre5"),
    ("extreme_dependent","cubic_spline13"),
])
def test_original_well_conditioned_cr2_se_and_satterthwaite_df(support,model):
    data=source.fresh_source(2,support,n=24)
    X,y,w,g,known=source.prepare(data,model)
    k=r16.basis(np.asarray([.5]),model).shape[1]
    c=np.r_[np.zeros(k),r16.basis(
        np.asarray([r16.TIME[r16.FOCAL]]),model)[0]]
    ref=cr2_blockwise_wls(X,y,w,g,c,known)
    stable=stable_cr2_blockwise_wls(X,y,w,g,c,known)
    np.testing.assert_allclose(stable["point"],ref["point"],rtol=1e-8,atol=1e-8)
    np.testing.assert_allclose(stable["cr2_se"],ref["cr2_se"],rtol=2e-7,atol=1e-10)
    np.testing.assert_allclose(stable["satterthwaite_df"],
                               ref["satterthwaite_df"],rtol=2e-6,atol=1e-7)
    assert stable["max_relative_adjustment_identity_error"]<3e-7
    assert not stable["pointwise_coverage_qualified"]
    assert not stable["working_covariance_estimation_uncertainty_included"]
