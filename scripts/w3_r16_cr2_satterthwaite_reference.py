"""Research-only CR2 coefficient-specific Satterthwaite df under specified Phi.

For a fixed WLS contrast c, CR2 variance is sum_i (q_i' e)^2,
q_i=(I-H)[:,i] A_i' Z_i (Z'Z)^-1 c. Under e_source~N(0,Phi),
the adjusted score coefficients in independent whitened innovations have
quadratic-form matrix K = Phi^(1/2) (sum q_i q_i') Phi^(1/2).
df = tr(K)^2 / tr(K^2), matching mean/variance of weighted chi-squares.
This is a reference calculation conditional on a KNOWN specified target.
"""
import numpy as np
from scripts.w3_r16_cr2_correlated_target import _symmetric_power

def cr2_satterthwaite_reference(X, weights, cluster, contrast, target_blocks):
    X=np.asarray(X,float);weights=np.asarray(weights,float)
    cluster=np.asarray(cluster);contrast=np.asarray(contrast,float)
    if X.ndim!=2 or weights.shape!=(len(X),) or cluster.shape!=(len(X),):
        raise ValueError("invalid source")
    if np.any(weights<=0) or not np.isfinite(weights).all():
        raise ValueError("positive weights required")
    Z=X*np.sqrt(weights)[:,None]; G=Z.T@Z
    beta_direction=np.linalg.solve(G,contrast)
    H=Z@np.linalg.solve(G,Z.T)
    R=np.eye(len(Z))-H
    groups=np.unique(cluster)
    if len(target_blocks)!=len(groups):raise ValueError("wrong number of covariance blocks")
    phi=np.zeros((len(Z),len(Z)))
    indices=[np.where(cluster==g)[0] for g in groups]
    for idx,block in zip(indices,target_blocks):
        P=np.asarray(block,float)
        if P.shape!=(len(idx),len(idx)):raise ValueError("wrong covariance block dimensions")
        _symmetric_power(P,.5)
        phi[np.ix_(idx,idx)]=P
    D=R@phi@R.T
    q=[]
    for idx in indices:
        Pi=phi[np.ix_(idx,idx)]
        Di=D[np.ix_(idx,idx)]
        root=_symmetric_power(Pi,.5)
        # Use identical canonical SPD factor as covariance CR2 estimator.
        A=root@_symmetric_power(root@Di@root,-.5)@root
        v=np.zeros(len(Z));v[idx]=A.T@(Z[idx]@beta_direction)
        q.append(R@v)
    B=np.stack(q,axis=1)
    C=B.T@phi@B
    ev=np.linalg.eigvalsh((C+C.T)/2)
    if np.min(ev)<-1e-8:raise ValueError("invalid quadratic form")
    tr=float(np.trace(C));tr2=float(np.sum(C*C))
    if tr<=0 or tr2<=0:raise ValueError("nonpositive moments")
    df=tr*tr/tr2
    return {"df":float(df),"expected_variance":tr,"variance_of_variance":2*tr2,
            "effective_eigenvalues":ev.tolist(),"n_clusters":len(groups),
            "working_covariance_is_specified":True,
            "empirical_covariance_estimated":False,
            "coverage_qualified":False,"public_api_authorized":False}
