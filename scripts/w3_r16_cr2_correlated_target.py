"""Research-only generalized CR2 for WLS with block-correlated working targets.

For whitened weighted design Z, H=Z(Z'Z)^-1 Z'; working covariance
Phi=blockdiag(Phi_i). E_i=[(I-H)Phi(I-H)']_ii. A_i E_i A_i'=Phi_i
with A_i=Phi_i^(1/2)(Phi_i^(-1/2) E_i Phi_i^(-1/2))^(-1/2)
Phi_i^(-1/2). Corrects expected cluster score covariance under
specified working target. No degrees-of-freedom or coverage qualification.
"""
import numpy as np

def _symmetric_power(a,power,tol=1e-11):
    ev,U=np.linalg.eigh((a+a.T)*.5)
    if not np.all(np.isfinite(ev)) or min(ev)<=tol:
        raise ValueError("nonpositive or ill-conditioned working covariance")
    return (U*(ev**power))@U.T

def cr2_correlated_wls(X,y,weights,cluster,contrast,target_blocks):
    X=np.asarray(X,float);y=np.asarray(y,float);weights=np.asarray(weights,float)
    cluster=np.asarray(cluster);contrast=np.asarray(contrast,float)
    if X.ndim!=2 or y.shape!=(len(X),) or cluster.shape!=(len(X),) or weights.shape!=(len(X),):
        raise ValueError("invalid source dimensions")
    if contrast.shape!=(X.shape[1],) or not np.all(np.isfinite(X)) or not np.all(np.isfinite(y)):
        raise ValueError("invalid source or contrast")
    if not np.all(np.isfinite(weights)) or np.any(weights<=0):
        raise ValueError("working WLS weights must be positive")
    groups=np.unique(cluster)
    if len(target_blocks)!=len(groups):
        raise ValueError("one covariance block required for every cluster")
    Z=X*np.sqrt(weights)[:,None];v=y*np.sqrt(weights)
    G=Z.T@Z; beta=np.linalg.solve(G,Z.T@v)
    e=v-Z@beta;b=np.linalg.solve(G,contrast)
    U=[Z[cluster==g] for g in groups]
    P=[np.asarray(t,float) for t in target_blocks]
    for Zi,phi in zip(U,P):
        if phi.shape!=(len(Zi),len(Zi)):
            raise ValueError("incorrect working covariance block")
        _symmetric_power(phi,.5)
    # Completely independent dense residual-covariance assembly across blocks.
    adjustments=[]; numer=[]; max_error=0.; max_asymmetry=0.
    for i,(Zi,phi) in enumerate(zip(U,P)):
        D=np.zeros_like(phi)
        for j,(Zj,phij) in enumerate(zip(U,P)):
            Bij=(-Zi@np.linalg.solve(G,Zj.T))
            if i==j:Bij=Bij+np.eye(len(Zi))
            D+=Bij@phij@Bij.T
        root=_symmetric_power(phi,.5)
        # Unique symmetric positive-definite CR2 factor, consistent with
        # R clubSandwich's Cholesky-based adjustment construction.
        A=root@_symmetric_power(root@D@root,-.5)@root
        max_error=max(max_error,float(np.max(np.abs(A@D@A.T-phi))))
        max_asymmetry=max(max_asymmetry,float(np.max(np.abs(A-A.T))))
        ei=e[cluster==groups[i]]
        adjusted=Zi.T@(A@ei)
        adjustments.append(adjusted)
        numer.append(float((adjusted@b)**2))
    var=float(sum(numer))
    if var<=0 or not np.isfinite(var):raise ValueError("nonpositive CR2 variance")
    return dict(point=float(contrast@beta),cr2_se=float(np.sqrt(var)),
                covariance_adjustment_error=max_error,
                covariance_adjustment_asymmetry=max_asymmetry,
                clusters=len(groups),
                working_target="specified_block_covariance_after_wls_whitening",
                reference_degrees_freedom_qualified=False,
                source_covariance_estimated=False,
                public_api_authorized=False)
