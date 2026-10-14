"""R20 research-only leverage-adjusted covariance-component moments.

Estimates a *specified parametric covariance family* from observable gaze
responses, observed times, trial IDs and predictor values, never from true
source innovations or generating covariance parameters. The family is a
deliberately restricted simulation analogue, NOT an automatically valid
empirical gaze covariance model or covariance-estimation qualification.
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import nnls

from scripts.run_w3_r16_leverage_covariance_factorial import basis

MODELS=("shared_slope","predictor_scaled_slope")
COMPONENTS=("participant_intercept","participant_slope","trial","sensor")


def observed_weighted_rows(source_case,model):
    """Use only observations; ignore source_case[0] and source_case[5] oracles."""
    _,gaze,values,participant,trials,_=source_case
    participant=np.asarray(participant)
    values=np.asarray(values,float)
    trials=np.asarray(trials)
    if len(gaze.time)!=len(participant) or len(values)!=len(participant):
        raise ValueError("incompatible native trial labels")
    unique=np.unique(participant)
    if len(unique)<6:
        raise ValueError("six or more independent participants required")
    X=[];Y=[];W=[];IDs=[];TT=[];TR=[];XX=[]
    for who in unique:
        ix=np.flatnonzero(participant==who)
        if not len(ix):
            raise ValueError("empty cluster")
        for j in ix:
            t=np.asarray(gaze.time[j],float)
            if t.ndim!=1 or not np.all(np.diff(t)>0):
                raise ValueError("native times must be strictly increasing")
            Bj=basis(t,model)
            if Bj.ndim!=2 or not len(Bj)==len(t):
                raise ValueError("incorrect design basis")
            xi=float(values[j])
            if not np.isfinite(xi):
                raise ValueError("nonfinite predictor")
            yj=np.asarray(gaze.values[j],float)[:,0]
            if yj.shape!=(len(t),) or not np.isfinite(yj).all():
                raise ValueError("invalid native outcome")
            X.append(np.column_stack([Bj,Bj*xi]))
            Y.append(yj)
            W.append(np.full(len(t),1/(len(ix)*len(t))))
            IDs.append(np.full(len(t),who))
            TT.append(t)
            TR.append(np.full(len(t),trials[j]))
            XX.append(np.full(len(t),xi))
    return (np.vstack(X),np.concatenate(Y),np.concatenate(W),
            np.concatenate(IDs),np.concatenate(TT),np.concatenate(TR),
            np.concatenate(XX))


def _kernels(time,trial,x,weight,slope):
    """Four unit-variance component covariance kernels, WLS-whitened."""
    r=np.sqrt(weight)
    u=(1+.30*time)*r
    v=(1+.25*time)*(x if slope=="predictor_scaled_slope" else 1.)*r
    group=(trial[:,None]==trial[None,:]).astype(float)
    return (np.outer(u,u),np.outer(v,v),
            (r[:,None]*group)*r[None,:],np.diag(weight))


def estimate_feasible_working_target(X,y,weight,cluster,time,trial,x,*,slope):
    if slope not in MODELS:
        raise ValueError("undeclared nuisance covariance family")
    X=np.asarray(X,float);y=np.asarray(y,float);weight=np.asarray(weight,float)
    cluster=np.asarray(cluster);time=np.asarray(time,float)
    trial=np.asarray(trial);x=np.asarray(x,float)
    if X.ndim!=2 or len(X)<=X.shape[1] or any(
       np.asarray(v).shape!=(len(X),) for v in (y,weight,cluster,time,trial,x)):
        raise ValueError("invalid observable source dimensions")
    if not np.isfinite(X).all() or not np.isfinite(y).all() or not np.isfinite(weight).all() or not np.isfinite(time).all() or not np.isfinite(x).all():
        raise ValueError("nonfinite source")
    if np.any(weight<=0):
        raise ValueError("positive weights required")
    groups=np.unique(cluster)
    Z=X*np.sqrt(weight)[:,None]
    G=Z.T@Z
    invG=np.linalg.solve(G,np.eye(X.shape[1]))
    beta=invG@Z.T@(y*np.sqrt(weight))
    e=y*np.sqrt(weight)-Z@beta
    indices=[np.flatnonzero(cluster==g) for g in groups]
    kernels=[]
    m_component=[np.zeros_like(G) for _ in COMPONENTS]
    for ix in indices:
        if not np.allclose(x[ix],x[ix][0],rtol=0,atol=1e-12):
            raise ValueError("predictor must remain constant within participant")
        ki=_kernels(time[ix],trial[ix],x[ix],weight[ix],slope)
        kernels.append(ki)
        zi=Z[ix]
        for k,K in enumerate(ki):
            m_component[k]+=zi.T@K@zi
    # Frisch-Waugh fitted residual covariance accounting for leverage:
    # E(e_i e_i^T) = sum_k theta_k [(I-H) K_k (I-H)]_ii.
    # Never substitute e_i e_i^T directly for K_i in high-leverage designs.
    rows=[];rhs=[];unit=[]
    for i,ix in enumerate(indices):
        zi=Z[ix];h=zi@invG@zi.T
        cols=[]
        for k,K in enumerate(kernels[i]):
            D=K-h@K-K@h+zi@invG@m_component[k]@invG@zi.T
            cols.append(((D+D.T)/2).ravel())
        rows.append(np.column_stack(cols))
        rhs.append(np.outer(e[ix],e[ix]).ravel())
        unit.append(ix)
    A=np.concatenate(rows,axis=0)
    response=np.concatenate(rhs)
    scale=np.linalg.norm(A,axis=0)
    if not np.isfinite(scale).all() or np.min(scale)<1e-14:
        raise ValueError("variance component not identified by observed design")
    scaled=A/scale
    recovered, residual_norm=nnls(scaled,response,maxiter=1000)
    theta=recovered/scale
    # Sensor coefficient is strictly positive for robust CR2 SPD reference.
    # Report floor use rather than silently claiming four identified components.
    sensor_floor=max(float(np.mean(weight))*1e-10,1e-14)
    floor_applied=theta[-1]<sensor_floor
    theta[-1]=max(float(theta[-1]),sensor_floor)
    blocks=[]
    for ker in kernels:
        phi=sum(float(v)*K for v,K in zip(theta,ker))
        phi=(phi+phi.T)/2
        if np.linalg.eigvalsh(phi).min()<=0:
            raise ValueError("estimated covariance target not SPD")
        blocks.append(phi)
    return {
        "variance_components":{k:float(v) for k,v in zip(COMPONENTS,theta)},
        "component_rank":int(np.linalg.matrix_rank(scaled)),
        "component_condition_number":float(np.linalg.cond(scaled)),
        "nnls_normalized_residual":float(np.linalg.norm(A@theta-response)/max(1e-15,np.linalg.norm(response))),
        "nnls_raw_residual":float(residual_norm),
        "sensor_floor_applied":bool(floor_applied),
        "working_blocks":blocks,
        "clusters":len(groups),
        "observations":len(X),
        "slope_family":slope,
        "estimated_from_outcomes":True,
        "uses_generating_truth_oracle":False,
        "working_model_correctness_assumed":False,
        "df_accounts_for_covariance_estimation":False,
        "pointwise_inference_qualified":False,
        "simultaneous_bands_qualified":False,
        "public_api_authorized":False,
    }
