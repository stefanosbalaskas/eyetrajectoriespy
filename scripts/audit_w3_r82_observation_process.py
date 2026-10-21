"""R82-A independent original-source read-only observation-mask replay.

Does not import source generator or its pointwise implementation. Requires
independent regeneration of 256 source X/Y and 1024 masks and all diagnostics.
No MNAR correction, confidence interval, or release qualification.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

STUDY="W3_R82_NEW_OBSERVATION_PROCESS_MCAR_MAR_MNAR"
SOURCE_SEED=202610208280
OBS_SEED=202610208281
CHECKOUT="06d1bb888468f1f85eee3875ae14ee5070a12400"
T=np.linspace(0.,1.,31)
CONFIGS=("curve_standard","participant_standard")
SUPPORT=("two_anchors","sixteen_anchors")
VARIANCES=("constant","predictor_heteroskedastic")
MECHANISMS=("complete","MCAR","MAR","MNAR")
BLOCKS=32
SOURCE_CONDITIONS=256
OBS_EVALUATIONS=1024
SHOCK_P=.08
SHOCK_A=.16


def close(a,b,what,tol=1e-9):
    if a is None or b is None:
        if a is not b:raise ValueError("R82-A original mismatch "+what)
        return
    x=np.asarray(a,float);y=np.asarray(b,float)
    if x.shape!=y.shape or not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)):
        raise ValueError("R82-A invalid finite field "+what)
    if not np.allclose(x,y,atol=tol,rtol=1e-8):
        raise ValueError("R82-A original numerical mismatch "+what)


def source_seed(block,config):
    return SOURCE_SEED+100003*block+10007*CONFIGS.index(config)


def observation_seed(block,config,support,variance):
    return (OBS_SEED+1000003*block+10007*CONFIGS.index(config)
            +739*SUPPORT.index(support)+97*VARIANCES.index(variance))


def truth():
    b0=np.column_stack((.35+.08*T,.25-.04*T))
    b1=np.column_stack((.40+.11*np.cos(np.pi*T),-.28+.13*np.sin(np.pi*T)))
    return b0,b1


def replay_XY(block,config,support,variance):
    n,trials=((72,1) if config=="curve_standard" else (36,3))
    rng=np.random.default_rng(source_seed(block,config))
    x=rng.uniform(-.95,.95,n)
    half=1 if support=="two_anchors" else 8
    x[:half]=-4.
    x[-half:]=4.
    scale=np.ones(n) if variance=="constant" else 1+.75*np.abs(x)
    b0,b1=truth()
    loc=b0[None]+x[:,None,None]*b1[None]
    participant=np.zeros((n,31,2))
    if config=="participant_standard":
        draws=rng.normal(0,1,size=(n,1,2))
        mixing=np.empty_like(draws)
        mixing[...,0]=draws[...,0]
        mixing[...,1]=.45*draws[...,0]+np.sqrt(1-.45**2)*draws[...,1]
        participant=.065*(1+.35*T)[None,:,None]*mixing
    white=rng.normal(0,1,size=(n,trials,31,2))
    times=np.arange(31)
    temporal=np.linalg.cholesky(.72**np.abs(times[:,None]-times[None,:]))
    latent_noise=np.einsum("tu,njud->njtd",temporal,white,optimize=True)
    q=.15+.65*T
    gaussian=np.empty_like(latent_noise)
    gaussian[...,0]=latent_noise[...,0]
    gaussian[...,1]=(q[None,None,:]*latent_noise[...,0]
                    +np.sqrt(1-q*q)[None,None,:]*latent_noise[...,1])
    gaussian=gaussian*(.04*(.70+.60*T))[None,None,:,None]
    radial=np.sqrt(3/rng.chisquare(5,size=n))
    asym=(rng.random(n)<SHOCK_P).astype(float)-SHOCK_P
    shape=(.75+.25*T[:,None])*np.array([1.,-.65])[None]
    Y=(loc[:,None]+scale[:,None,None,None]*
       (radial[:,None,None,None]*(participant[:,None]+gaussian)
        +SHOCK_A*asym[:,None,None,None]*shape[None,None]))
    return np.column_stack((np.ones(n),x)),Y,b1


def masks(X,Y,block,config,support,variance):
    rng=np.random.default_rng(observation_seed(block,config,support,variance))
    u=rng.random(Y.shape)
    n,trials,_,_=Y.shape
    idx=np.arange(trials)[None,:,None,None]
    baseline=(-2.2+np.abs(X[:,1,None,None,None])/4
              +.7*T[None,None,:,None]+.2*idx)
    p_mar=1/(1+np.exp(-baseline))
    b0,b1=truth()
    loc=b0[None]+X[:,1,None,None]*b1[None]
    p_mnar=1/(1+np.exp(-(baseline+1.1*np.tanh((Y-loc[:,None])/.08))))
    return {
        "complete":np.zeros(Y.shape,bool),
        "MCAR":u<.12,
        "MAR":u<p_mar,
        "MNAR":u<p_mnar,
    }


def digest(X):
    return sha256(np.round(np.asarray(X,float),9).astype("<f8").tobytes(order="C")).hexdigest()


def mask_digest(X):
    return sha256(np.asarray(X,dtype=np.uint8).tobytes(order="C")).hexdigest()


def slope_with_support(X,Y,mask):
    n,trials,_,_=Y.shape
    vis=~mask
    num=vis.sum(axis=1)
    Ysum=np.where(vis,Y,0.).sum(axis=1)
    native=np.divide(Ysum,num,out=np.full_like(Ysum,np.nan),where=num>0)
    native_valid=num>0
    slope=np.full((31,2),np.nan)
    refused=np.zeros((31,2),bool)
    units=native_valid.sum(axis=0)
    neg=np.zeros((31,2),int)
    pos=np.zeros((31,2),int)
    for t in range(31):
        for d in range(2):
            choose=native_valid[:,t,d]
            x=X[choose,1]
            neg[t,d]=np.count_nonzero(x==-4.)
            pos[t,d]=np.count_nonzero(x==4.)
            if len(x)<8 or neg[t,d]<1 or pos[t,d]<1 or len(np.unique(x))<2:
                refused[t,d]=True
                continue
            yy=native[choose,t,d]
            xcent=x-np.mean(x)
            denom=np.sum(xcent*xcent)
            if denom<=0:
                refused[t,d]=True
                continue
            slope[t,d]=np.sum(xcent*(yy-yy.mean()))/denom
    return slope,units,neg,pos,refused


def replay_case(row,X,Y,beta,source_full,source_masks):
    name=f"{row['block']}/{row['config']}/{row['support']}/{row['variance']}/{row['mechanism']}"
    mechanism=row["mechanism"]
    mask=source_masks[mechanism]
    if (row["study"]!=STUDY or row["source_seed"]!=source_seed(row["block"],row["config"])
        or row["observation_seed"]!=observation_seed(row["block"],row["config"],row["support"],row["variance"])
        or row["native_independent_units"]!=len(X)
        or row["source_trials"]!=Y.shape[1]
        or row["not_an_MNAR_adjustment"] is not True
        or row["no_band_calibration"] is not True
        or row["release_authorized"] is not False):
        raise ValueError("R82-A original study/release provenance mismatch "+name)
    for key,val in [("source_X_digest",digest(X)),("source_Y_digest",digest(Y)),
                    ("true_slope_digest",digest(beta)),
                    ("observed_mask_digest",mask_digest(mask))]:
        if row[key]!=val:raise ValueError("R82-A original X/Y/mask identity mismatch "+name+"/"+key)
    slope,unit_count,neg,pos,refused=slope_with_support(X,Y,mask)
    if (row["observed_gaze_samples"]!=int((~mask).sum())
        or row["missing_gaze_samples"]!=int(mask.sum())
        or row["fully_observed_curves"]!=int((~mask).all(axis=(2,3)).sum())
        or row["fully_observed_independent_units"]!=int((~mask).all(axis=(1,2,3)).sum())
        or row["grid_refused_count"]!=int(refused.sum())
        or row["grid_estimable_count"]!=int((~refused).sum())
        or row["min_independent_units"]!=int(unit_count.min())
        or row["min_negative_anchors"]!=int(neg.min())
        or row["min_positive_anchors"]!=int(pos.min())
        or row["native_missingness_refusal"] is not (mechanism!="complete")):
        raise ValueError("R82-A original descriptive/native refusal mismatch "+name)
    close(row["gaze_observation_fraction"],(~mask).mean(),name+"/retention")
    close(row["observed_unit_counts"],unit_count,name+"/unit_counts")
    close(row["negative_anchor_counts"],neg,name+"/neg")
    close(row["positive_anchor_counts"],pos,name+"/pos")
    if row["grid_refused"]!=refused.tolist():
        raise ValueError("R82-A original failed independent-unit anchor/refusal contract "+name)
    full=source_full[0]
    actual=np.array([[np.nan if z is None else z for z in line]
                     for line in row["pointwise_slope"]])
    if not np.array_equal(np.isfinite(actual),~refused):
        raise ValueError("R82-A original complete-grid estimability forged "+name)
    if (~refused).any():
        close(actual[~refused],slope[~refused],name+"/slope")
        error=slope[~refused]-beta[~refused]
        delta=slope[~refused]-full[~refused]
        for key,val in [
            ("mean_abs_slope_error",np.abs(error).mean()),
            ("max_abs_slope_error",np.abs(error).max()),
            ("mean_signed_slope_error",error.mean()),
            ("mean_available_minus_full_slope",delta.mean()),
            ("mean_abs_available_minus_full_slope",np.abs(delta).mean())
        ]:
            close(row[key],val,name+"/"+key)
    else:
        for key in ("mean_abs_slope_error","max_abs_slope_error",
                    "mean_signed_slope_error","mean_available_minus_full_slope",
                    "mean_abs_available_minus_full_slope"):
            if row[key] is not None:raise ValueError("R82-A refused grid manufactured pointwise estimate "+name)
    return {"source":name,"retention":float((~mask).mean()),
            "refused":int(refused.sum()),"native_rejected":mechanism!="complete",
            "mean_abs_slope_error":row["mean_abs_slope_error"]}


def audit(original:Path,expected_checkout=CHECKOUT):
    expected="\n".join(
        sha256((original/p).read_bytes()).hexdigest()+"  "+p
        for p in ("evidence.json","source-commit.txt"))+"\n"
    if (original/"SHA256SUMS").read_text()!=expected:
        raise ValueError("R82-A original immutable SHA256 evidence mismatch")
    checkout=(original/"source-commit.txt").read_text().strip()
    if checkout!=expected_checkout or len(checkout)!=40:
        raise ValueError("R82-A exact original science checkout mismatch")
    obj=json.loads((original/"evidence.json").read_text())
    if obj["source_checkout"]!=checkout:
        raise ValueError("R82-A source checkout manifest mismatch")
    rows=obj["source_evaluations"]
    report=obj["aggregate"]
    expected_id={(b,c,s,v,m) for b in range(BLOCKS) for c in CONFIGS
                 for s in SUPPORT for v in VARIANCES for m in MECHANISMS}
    ids=[(r["block"],r["config"],r["support"],r["variance"],r["mechanism"]) for r in rows]
    if len(rows)!=OBS_EVALUATIONS or len(set(ids))!=OBS_EVALUATIONS or set(ids)!=expected_id:
        raise ValueError("R82-A original independent source or paired-mask denominator mismatch")
    for field,value in {
        "study":STUDY,"source_seed":SOURCE_SEED,"mask_seed":OBS_SEED,
        "new_independent_primitive_blocks":BLOCKS,
        "original_source_cases":SOURCE_CONDITIONS,
        "mechanism_evaluations":OBS_EVALUATIONS,
        "observation_mechanisms":list(MECHANISMS),
        "configs":list(CONFIGS),"supports":list(SUPPORT),
        "variances":list(VARIANCES),
        "min_estimable_native_units":8,
        "native_requires_complete":True,"imputation_performed":False,
        "MNAR_correction_performed":False,
        "90percent_band_calibration_performed":False,
        "release_authorized":False}.items():
        if report.get(field)!=value:
            raise ValueError("R82-A scientific/qualification provenance mismatch "+field)
    replay={}
    for b in range(BLOCKS):
        for c in CONFIGS:
            for s in SUPPORT:
                for v in VARIANCES:
                    X,Y,beta=replay_XY(b,c,s,v)
                    masks_=masks(X,Y,b,c,s,v)
                    baseline=slope_with_support(X,Y,masks_["complete"])
                    for m in MECHANISMS:
                        k=(b,c,s,v,m)
                        row=next(x for x in rows if
                            (x["block"],x["config"],x["support"],x["variance"],x["mechanism"])==k)
                        replay[k]=replay_case(row,X,Y,beta,baseline,masks_)
    results={}
    for c in CONFIGS:
        results[c]={}
        for s in SUPPORT:
            results[c][s]={}
            for v in VARIANCES:
                results[c][s][v]={}
                for m in MECHANISMS:
                    vals=[replay[b,c,s,v,m] for b in range(BLOCKS)]
                    source=report["results"][c][s][v][m]
                    if source["independent_source_blocks"]!=BLOCKS:
                        raise ValueError("R82-A original independence denominator inflated")
                    metrics=[
                        ("mean_observed_fraction","retention"),
                        ("mean_grid_refused","refused"),
                        ("mean_abs_slope_error","mean_abs_slope_error")
                    ]
                    for k,z in metrics:
                        t=[x[z] for x in vals if x[z] is not None]
                        close(source[k],np.mean(t) if t else None,k+"/"+c+"/"+s+"/"+v+"/"+m)
                    results[c][s][v][m]={
                        "source_blocks":BLOCKS,
                        "retention":source["mean_observed_fraction"],
                        "mean_grid_refused":source["mean_grid_refused"],
                        "mean_abs_slope_error":source["mean_abs_slope_error"]}
    return {"independent_complete_XY_sources":SOURCE_CONDITIONS,
            "independent_replayed_paired_masks":OBS_EVALUATIONS,
            "independent_primitive_blocks_per_cell":BLOCKS,
            "original_checkout":checkout,
            "native_missingness_refusal_retained":True,
            "MNAR_correction_or_band_calibration":False,
            "release_authorized":False,"results":results}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original",type=Path,required=True)
    p.add_argument("--expected-checkout",default=CHECKOUT)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    report=audit(a.original,a.expected_checkout)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({"sources":report["independent_complete_XY_sources"],
                      "paired_masks":report["independent_replayed_paired_masks"],
                      "release_authorized":False},sort_keys=True))


if __name__=="__main__":main()
