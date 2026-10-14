"""Research-only blockwise CR2 and conditional Satterthwaite calculation.

Avoids constructing the N x N residual-maker R or target Phi. Assumes
independent clusters with specified SPD block-diagonal covariance targets in
the weighted observation space. Not an empirically estimated covariance and
not an inference qualification. Validated against exact small dense oracles.
"""
from __future__ import annotations

import numpy as np

from scripts.w3_r16_cr2_correlated_target import _symmetric_power


def cr2_blockwise_wls(X, y, weights, cluster, contrast, target_blocks):
    X=np.asarray(X,float)
    y=np.asarray(y,float)
    weights=np.asarray(weights,float)
    cluster=np.asarray(cluster)
    contrast=np.asarray(contrast,float)
    if X.ndim!=2 or X.shape[0]<=X.shape[1]:
        raise ValueError("full-rank overdetermined WLS required")
    N,p=X.shape
    if y.shape!=(N,) or weights.shape!=(N,) or cluster.shape!=(N,) or contrast.shape!=(p,):
        raise ValueError("incompatible input dimensions")
    if not np.isfinite(X).all() or not np.isfinite(y).all() or not np.isfinite(contrast).all():
        raise ValueError("nonfinite input")
    if not np.isfinite(weights).all() or np.any(weights<=0):
        raise ValueError("positive finite WLS weights required")
    groups=np.unique(cluster)
    if len(groups)!=len(target_blocks):
        raise ValueError("one specified target covariance per cluster")
    Z=X*np.sqrt(weights)[:,None]
    wY=y*np.sqrt(weights)
    G=Z.T@Z
    invG=np.linalg.solve(G,np.eye(p))
    beta=invG@(Z.T@wY)
    bread_contrast=invG@contrast
    resid=wY-Z@beta
    indices=[np.flatnonzero(cluster==g) for g in groups]
    blocks=[]
    M=np.zeros((p,p))
    for ix,Ph in zip(indices,target_blocks):
        Zi=Z[ix]
        Phi=np.asarray(Ph,float)
        if Phi.shape!=(len(ix),len(ix)):
            raise ValueError("target block dimension mismatch")
        root=_symmetric_power(Phi,.5)
        blocks.append((ix,Zi,Phi,root))
        M+=Zi.T@Phi@Zi
    M=(M+M.T)/2
    point=float(contrast@beta)
    diag_terms=[]
    a_rows=[]
    b_rows=[]
    scores=[]
    max_id=0.
    max_asym=0.
    for ix,Zi,Phi,root in blocks:
        Hii=Zi@invG@Zi.T
        Di=Phi-Hii@Phi-Phi@Hii+Zi@invG@M@invG@Zi.T
        Di=(Di+Di.T)/2
        A=root@_symmetric_power(root@Di@root,-.5)@root
        max_id=max(max_id,float(np.max(np.abs(A@Di@A.T-Phi))))
        max_asym=max(max_asym,float(np.max(np.abs(A-A.T))))
        gi=A@(Zi@bread_contrast)
        a=Zi.T@gi
        b=Zi.T@(Phi@gi)
        diag_terms.append(float(gi@Phi@gi))
        a_rows.append(a)
        b_rows.append(b)
        scores.append(float(gi@resid[ix]))
    a=np.stack(a_rows)
    b=np.stack(b_rows)
    # C_ij=Cov(gi' ehat_i,gj' ehat_j) under the declared working target.
    C=(np.diag(diag_terms)-a@invG@b.T-b@invG@a.T
       +a@invG@M@invG@a.T)
    C=(C+C.T)/2
    eig=np.linalg.eigvalsh(C)
    if eig.min()<-1e-8:
        raise ValueError("negative eigenvalue in conditional variance quadratic form")
    evar=float(np.trace(C))
    vvar=float(2*np.sum(C*C))
    if evar<=0 or vvar<=0:
        raise ValueError("nonpositive conditional quadratic moments")
    satt_df=2*evar**2/vvar
    se=np.sqrt(float(np.sum(np.square(scores))))
    oracle_expectation=float(bread_contrast@M@bread_contrast)
    if se<=0 or not np.isfinite(se):
        raise ValueError("invalid CR2 standard error")
    return {
        "point":point,
        "cr2_se":float(se),
        "satterthwaite_df":float(satt_df),
        "conditional_expectation":evar,
        "theoretical_contrast_variance":oracle_expectation,
        "expectation_identity_error":float(abs(evar-oracle_expectation)),
        "variance_of_variance":vvar,
        "max_adjustment_covariance_error":max_id,
        "max_adjustment_asymmetry":max_asym,
        "n_clusters":len(groups),
        "n_observations":N,
        "working_target_specified":True,
        "working_target_estimated":False,
        "pointwise_coverage_qualified":False,
        "simultaneous_bands_qualified":False,
        "public_api_authorized":False,
    }
