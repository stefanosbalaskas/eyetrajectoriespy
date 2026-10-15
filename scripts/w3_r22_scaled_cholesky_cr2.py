"""R22 experimental scaled-Cholesky symmetric CR2 adjustment.

This is a numerically distinct implementation of the UNIQUE symmetric SPD
solution A D A' = Phi. It does not lower R16's eigenvalue cutoff. It may
refuse severely conditioned cases; such refusals are scientific outcomes.
Nothing in this file qualifies estimated covariance nuisance uncertainty,
pointwise coverage, simultaneous bands or any package public API.
"""
from __future__ import annotations

import numpy as np
from scipy.linalg import cholesky, solve_triangular


class UnstableCR2Adjustment(ValueError):
    """Conditioning/identity check prevents reporting a misleading CR2 result."""


def _sym(a):
    return (a+a.T)*.5


def scaled_symmetric_adjustment(phi,d,*,max_product_condition=1e11,
                                identity_rtol=3e-7):
    """Return symmetric SPD A, diagnostics, or refuse if accuracy unverified.

    With D=L L', unique SPD A is L^(-T) sqrt(L' Phi L) L^(-1).
    Phi and D are normalized independently before computing their factors.
    This avoids the absolute eigenvalue threshold on Phi^.5 D Phi^.5,
    but cannot rescue intrinsically weakly identified covariance directions.
    """
    phi=np.asarray(phi,float)
    d=np.asarray(d,float)
    if (phi.ndim!=2 or phi.shape!=d.shape or phi.shape[0]!=phi.shape[1]
        or not np.isfinite(phi).all() or not np.isfinite(d).all()):
        raise ValueError("two same-sized finite square matrices required")
    if not np.allclose(phi,phi.T,atol=1e-12,rtol=1e-11):
        raise ValueError("Phi not symmetric")
    if not np.allclose(d,d.T,atol=1e-12,rtol=1e-11):
        raise ValueError("D not symmetric")
    phi=_sym(phi);d=_sym(d)
    scale_phi=float(np.max(np.diag(phi)))
    scale_d=float(np.max(np.diag(d)))
    if not np.isfinite([scale_phi,scale_d]).all() or min(scale_phi,scale_d)<=0:
        raise UnstableCR2Adjustment("invalid covariance matrix scales")
    pn=phi/scale_phi
    dn=d/scale_d
    try:
        L=cholesky(dn,lower=True,check_finite=True)
        cholesky(pn,lower=True,check_finite=True)
    except np.linalg.LinAlgError as exc:
        raise UnstableCR2Adjustment("non-SPD Phi or D, Cholesky refused") from exc
    product=_sym(L.T@pn@L)
    eig,Q=np.linalg.eigh(product)
    if not np.isfinite(eig).all() or eig[0]<=0:
        raise UnstableCR2Adjustment("nonpositive normalized product eigenvalue")
    condition=float(eig[-1]/eig[0])
    if condition>max_product_condition:
        raise UnstableCR2Adjustment(
            f"normalized product condition {condition:.5g} exceeds {max_product_condition:.5g}")
    B=_sym((Q*np.sqrt(eig))@Q.T)
    left=solve_triangular(L.T,B,lower=False,check_finite=True)
    normalized=solve_triangular(L.T,left.T,lower=False,check_finite=True).T
    A=_sym(normalized)*np.sqrt(scale_phi/scale_d)
    if not np.isfinite(A).all():
        raise UnstableCR2Adjustment("nonfinite adjustment")
    check=_sym(A@d@A.T)
    rel=float(np.linalg.norm(check-phi,ord="fro")/np.linalg.norm(phi,ord="fro"))
    if rel>identity_rtol:
        raise UnstableCR2Adjustment(
            f"CR2 relative identity error {rel:.5g} exceeds {identity_rtol:.5g}")
    try:
        cholesky(A,lower=True,check_finite=True)
    except np.linalg.LinAlgError as exc:
        raise UnstableCR2Adjustment("computed symmetric adjustment not SPD") from exc
    return A,{"normalized_product_condition":condition,
              "relative_identity_error":rel,
              "phi_scale":scale_phi,"d_scale":scale_d,
              "minimum_normalized_product_eigenvalue":float(eig[0]),
              "maximum_normalized_product_eigenvalue":float(eig[-1]),
              "symmetric_spd":True,
              "working_covariance_estimation_uncertainty_included":False,
              "public_api_authorized":False}


def stable_cr2_blockwise_wls(X,y,weights,cluster,contrast,target_blocks,
                            *,max_product_condition=1e11):
    """Independent CR2/Satterthwaite calculation with explicit refusal."""
    X=np.asarray(X,float);y=np.asarray(y,float)
    weights=np.asarray(weights,float);cluster=np.asarray(cluster)
    contrast=np.asarray(contrast,float)
    if X.ndim!=2 or X.shape[0]<=X.shape[1]:
        raise ValueError("overdetermined full-rank design required")
    N,p=X.shape
    if any(v.shape!=(N,) for v in (y,weights,cluster)) or contrast.shape!=(p,):
        raise ValueError("incompatible shapes")
    if (not np.isfinite(X).all() or not np.isfinite(y).all()
        or not np.isfinite(contrast).all() or not np.isfinite(weights).all()
        or np.any(weights<=0)):
        raise ValueError("invalid finite WLS input")
    groups=np.unique(cluster)
    if len(target_blocks)!=len(groups):
        raise ValueError("target block count differs from cluster count")
    Z=X*np.sqrt(weights)[:,None]
    yy=y*np.sqrt(weights)
    G=Z.T@Z
    invG=np.linalg.solve(G,np.eye(p))
    beta=invG@(Z.T@yy)
    bc=invG@contrast
    resid=yy-Z@beta
    ixlist=[np.flatnonzero(cluster==g) for g in groups]
    M=np.zeros((p,p))
    blocks=[]
    for ix,phi in zip(ixlist,target_blocks):
        phi=np.asarray(phi,float)
        zi=Z[ix]
        if phi.shape!=(len(ix),len(ix)):
            raise ValueError("working covariance block dimension mismatch")
        M+=zi.T@phi@zi
        blocks.append((ix,zi,phi))
    M=_sym(M)
    aa=[];bb=[];diagonal=[];score=[];checks=[]
    for ix,zi,phi in blocks:
        H=zi@invG@zi.T
        D=_sym(phi-H@phi-phi@H+zi@invG@M@invG@zi.T)
        A,check=scaled_symmetric_adjustment(
            phi,D,max_product_condition=max_product_condition)
        checks.append(check)
        g=A@(zi@bc)
        a=zi.T@g
        b=zi.T@(phi@g)
        aa.append(a);bb.append(b)
        diagonal.append(float(g@phi@g))
        score.append(float(g@resid[ix]))
    a=np.stack(aa);b=np.stack(bb)
    C=_sym(np.diag(diagonal)-a@invG@b.T-b@invG@a.T+a@invG@M@invG@a.T)
    eig=np.linalg.eigvalsh(C)
    scale=float(max(np.max(np.abs(eig)),np.finfo(float).tiny))
    if eig[0]<-1e-8*scale:
        raise UnstableCR2Adjustment("contrast variance quadratic form not PSD")
    expected=float(np.trace(C))
    variance_of_variance=float(2*np.sum(C*C))
    if min(expected,variance_of_variance)<=0:
        raise UnstableCR2Adjustment("nonpositive Satterthwaite moments")
    se=float(np.linalg.norm(score))
    if se<=0 or not np.isfinite(se):
        raise UnstableCR2Adjustment("nonpositive CR2 standard error")
    return {
        "point":float(contrast@beta),
        "cr2_se":se,
        "satterthwaite_df":float(2*expected**2/variance_of_variance),
        "conditional_expectation":expected,
        "theoretical_contrast_variance":float(bc@M@bc),
        "expectation_identity_error":float(abs(expected-bc@M@bc)),
        "max_relative_adjustment_identity_error":max(c["relative_identity_error"] for c in checks),
        "max_normalized_product_condition":max(c["normalized_product_condition"] for c in checks),
        "clusters":len(groups),
        "numerical_refusal_policy_active":True,
        "working_covariance_estimation_uncertainty_included":False,
        "pointwise_coverage_qualified":False,
        "simultaneous_bands_qualified":False,
        "public_api_authorized":False,
    }
