"""Research-only CR2 working-identity cluster adjustment for participant-weighted WLS.

Mathematical target is independent unit observation errors after WLS whitening,
Phi_i = I within each participant. This is NOT a known-source random-effects
covariance oracle and does NOT establish coverage for correlated gaze recordings.

If G = sum Z_i.T Z_i = L L.T (Z_i = sqrt(W_i) X_i), define
S_i = L^-1 (Z_i.T Z_i) L^-T and score_i = Z_i.T residual_white_i.
CR2 adjusted score = L (I - S_i)^(-1/2) L^-1 score_i.
Cov_CR2 = G^-1 sum adjusted_score_i adjusted_score_i.T G^-1.
Independent dense oracle applies (I-H_ii)^(-1/2) to residual_white_i,
with H_ii = Z_i G^-1 Z_i.T, then collects Z_i.T adjusted residuals.
Both constructions are computationally independent and agree algebraically.
"""
from __future__ import annotations
import numpy as np

def _inverse_symmetric_root(a, *, tol=1e-10):
    vals, vecs = np.linalg.eigh((a+a.T)/2)
    if vals.min()<=tol:
        raise ValueError("CR2 cluster residual leverage matrix not positive definite")
    return (vecs*(1/np.sqrt(vals)))@vecs.T

def cr2_wls_identity(X, y, weights, participant, contrast):
    X=np.asarray(X,float);y=np.asarray(y,float)
    weights=np.asarray(weights,float);participant=np.asarray(participant)
    contrast=np.asarray(contrast,float)
    if X.ndim!=2 or y.shape!=(len(X),) or weights.shape!=(len(X),) or participant.shape!=(len(X),):
        raise ValueError("incompatible CR2 source dimensions")
    if contrast.shape!=(X.shape[1],) or not np.isfinite(X).all() or not np.isfinite(y).all():
        raise ValueError("invalid CR2 source")
    if not np.isfinite(weights).all() or np.any(weights<=0):
        raise ValueError("CR2 requires positive finite WLS weights")
    Z=X*np.sqrt(weights)[:,None]
    yw=y*np.sqrt(weights)
    G=Z.T@Z
    L=np.linalg.cholesky(G)
    theta=np.linalg.solve(G,Z.T@yw)
    ew=yw-Z@theta
    adjusted=[]; independent=[]
    vals=[]
    for pid in np.unique(participant):
        ix=participant==pid
        Zi=Z[ix];ei=ew[ix]
        original=Zi.T@ei
        # triangular systems via dense solve keep reference implementation simple
        whitened=np.linalg.solve(L,original)
        Ui=np.linalg.solve(L,Zi.T).T
        Si=Ui.T@Ui
        C=_inverse_symmetric_root(np.eye(G.shape[0])-Si)
        adjusted.append(L@(C@whitened))
        # Independent mathematical reference: direct observation-space transform
        Hii=Zi@np.linalg.solve(G,Zi.T)
        Adense=_inverse_symmetric_root(np.eye(len(ei))-Hii)
        independent.append(Zi.T@(Adense@ei))
        vals.append(float(np.linalg.eigvalsh(Si).max()))
    b=np.linalg.solve(G,contrast)
    adjusted=np.asarray(adjusted); independent=np.asarray(independent)
    var=float(np.sum(np.square(adjusted@b)))
    independent_var=float(np.sum(np.square(independent@b)))
    if var<=0 or not np.isfinite(var):
        raise ValueError("invalid CR2 variance")
    return dict(
        cr2_se=float(np.sqrt(var)),
        independent_dense_cr2_se=float(np.sqrt(independent_var)),
        numerical_difference=float(abs(np.sqrt(var)-np.sqrt(independent_var))),
        point=float(contrast@theta),
        max_cluster_leverage=float(max(vals)),
        n_clusters=int(len(vals)),
        working_target="identity_in_weighted_observation_space",
        cr2_reference_df_qualified=False,
        correlated_source_covariance_qualified=False,
        simultaneous_bands_qualified=False,
        public_api_authorized=False,
    )
