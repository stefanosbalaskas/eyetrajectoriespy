"""R83-A independent original-source read-only observation-mask replay.

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

STUDY="W3_R83_NEW_MNAR_SENSITIVITY_IDENTIFIABILITY"
SOURCE_SEED=202610218380
OBS_SEED=202610218381
CHECKOUT="FROZEN_ORIGINAL_R83_SOURCE_CHECKOUT"
T=np.linspace(0.,1.,31)
CONFIGS=("curve_standard","participant_standard")
SUPPORT=("two_anchors","sixteen_anchors")
VARIANCES=("constant","predictor_heteroskedastic")
MECHANISMS=("complete","MCAR","MAR","MNAR")
BLOCKS=32
SOURCE_CONDITIONS=256
OBS_EVALUATIONS=1024
DIAGNOSTIC_RECORDS=3328
DELTA=(-1.1,-.55,0.,.55,1.1)
METHODS=("COMPLETE","MCAR_known","MAR_sensitivity","MNAR_sensitivity","MNAR_oracle")
SHOCK_P=.08
SHOCK_A=.16


def close(a,b,what,tol=1e-9):
    if a is None or b is None:
        if a is not b:raise ValueError("R83-A original mismatch "+what)
        return
    x=np.asarray(a,float);y=np.asarray(b,float)
    if x.shape!=y.shape or not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)):
        raise ValueError("R83-A invalid finite field "+what)
    if not np.allclose(x,y,atol=tol,rtol=1e-8):
        raise ValueError("R83-A original numerical mismatch "+what)


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



def trialwise_pointwise(X,Y,mask,mechanism,delta,oracle=False):
    """Independent sufficient-statistic implementation of source weighted LS.

    This is a descriptive selection-sensitivity calculation, not an
    identified MNAR model or covariance/interval estimator.
    """
    n,trials,_,_=Y.shape
    b0,b1=truth()
    mean=b0[None]+X[:,1,None,None]*b1[None]
    slope=np.full((31,2),np.nan)
    pilot=np.full((31,2),np.nan)
    refused=np.zeros((31,2),bool)
    nunits=np.zeros((31,2),int)
    neg=np.zeros((31,2),int)
    pos=np.zeros((31,2),int)
    effective=np.full((31,2),np.nan)
    maxw=np.full((31,2),np.nan)
    for t in range(31):
        for d in range(2):
            observed=np.where(~mask[:,:,t,d])
            units=np.unique(observed[0])
            nunits[t,d]=len(units)
            neg[t,d]=int(np.count_nonzero(X[units,1]==-4.))
            pos[t,d]=int(np.count_nonzero(X[units,1]==4.))
            if len(units)<8 or neg[t,d]==0 or pos[t,d]==0 or len(np.unique(X[units,1]))<2:
                refused[t,d]=True
                continue
            uid,trial=observed
            x=X[uid,1]
            y=Y[uid,trial,t,d]
            # Ordinary visible-only OLS pilot based on trial-level measured y.
            px=float(np.mean(x));py=float(np.mean(y))
            den=float(np.dot(x-px,x-px))
            if den<1e-12:
                refused[t,d]=True;continue
            pilot_slope=float(np.dot(x-px,y-py)/den)
            pilot[t,d]=pilot_slope
            pilot_intercept=py-pilot_slope*px
            if mechanism=="MCAR":
                p_obs=np.full(len(y),.88)
            else:
                logit=(-2.2+np.abs(x)/4+.7*T[t]+.2*trial)
                reference_mean=(mean[uid,t,d] if oracle
                                else pilot_intercept+pilot_slope*x)
                p_obs=1-1/(1+np.exp(-(logit+delta*np.tanh((y-reference_mean)/.08))))
            if not np.isfinite(p_obs).all() or np.min(p_obs)<.02:
                refused[t,d]=True;continue
            weights=1/p_obs
            W=float(weights.sum())
            Wx=float(np.dot(weights,x))
            Wy=float(np.dot(weights,y))
            Wxx=float(np.dot(weights,x*x))
            Wxy=float(np.dot(weights,x*y))
            resid_den=Wxx-Wx*Wx/W
            if resid_den<1e-12:
                refused[t,d]=True;continue
            slope[t,d]=(Wxy-Wx*Wy/W)/resid_den
            cluster=np.bincount(uid,weights=weights,minlength=n)
            effective[t,d]=float(cluster.sum()**2/np.dot(cluster,cluster))
            maxw[t,d]=float(weights.max())
    return slope,pilot,refused,nunits,neg,pos,effective,maxw


def same_grid(stored,reference,tag,atol=1e-8):
    z=np.array([[np.nan if v is None else v for v in r] for r in stored],float)
    y=np.asarray(reference,float)
    if z.shape!=y.shape or not np.array_equal(np.isfinite(z),np.isfinite(y)):
        raise ValueError("R83-A original refused-grid provenance mismatch "+tag)
    valid=np.isfinite(y)
    if valid.any():close(z[valid],y[valid],tag,atol)
    return z


def evaluate_row(z,X,Y,b1,masks_,full):
    m=z["observation_mechanism"];method=z["method"];delta=z["assumed_mnar_delta"]
    identity=f"{z['block']}/{z['config']}/{z['support']}/{z['variance']}/{method}/{delta}"
    mask=masks_[m]
    if (z["study"]!=STUDY
        or z["source_seed"]!=source_seed(z["block"],z["config"])
        or z["observation_seed"]!=observation_seed(z["block"],z["config"],z["support"],z["variance"])
        or z["native_independent_units"]!=len(X) or z["trials_per_unit"]!=Y.shape[1]
        or z["release_authorized"] is not False
        or z["not_identified_mnar_delta"] is not True
        or z["no_missingness_corrected_confidence_band"] is not True
        or z["no_90percent_calibration"] is not True
        or z["simulator_only_oracle"] is not (method=="MNAR_oracle")
        or z["native_nan_refusal"] is not (m!="complete")):
        raise ValueError("R83-A original nonidentified sensitivity/release provenance mismatch "+identity)
    for k,v in [("source_X_digest",digest(X)),("source_Y_digest",digest(Y)),
                ("truth_slope_digest",digest(b1)),("observation_mask_digest",mask_digest(mask))]:
        if z[k]!=v:raise ValueError("R83-A source or observation mask SHA256 identity mismatch "+identity+"/"+k)
    if method=="COMPLETE":
        slope,nunits,neg,pos,refused=full
        pilot=slope
        effective=np.full((31,2),float(len(X)))
        maxwt=np.ones((31,2))
    else:
        slope,pilot,refused,nunits,neg,pos,effective,maxwt=trialwise_pointwise(
            X,Y,mask,m,float(delta),method=="MNAR_oracle")
    valid=~refused
    if (z["grid_refused"]!=refused.tolist()
        or z["grid_refused_count"]!=int(refused.sum())
        or z["grid_estimable_count"]!=int(valid.sum())
        or z["observed_unit_counts"]!=nunits.tolist()
        or z["negative_anchor_counts"]!=neg.tolist()
        or z["positive_anchor_counts"]!=pos.tolist()
        or z["min_observed_independent_units"]!=int(nunits.min())
        or z["missing_samples"]!=int(mask.sum())):
        raise ValueError("R83-A independent-unit support or pointwise refusal mismatch "+identity)
    close(z["observed_fraction"],(~mask).mean(),identity+"/fraction")
    same_grid(z["pointwise_slopes"],slope,identity+"/slope")
    same_grid(z["observed_only_pilot_slopes"],pilot,identity+"/pilot")
    if valid.any():
        close(z["mean_effective_cluster_n"],float(np.mean(effective[valid])),identity+"/effN")
        close(z["max_inverse_observation_weight"],float(np.max(maxwt[valid])),identity+"/maxweight")
        err=slope[valid]-b1[valid]
        shift=slope[valid]-full[0][valid]
        close(z["mean_abs_slope_error"],np.abs(err).mean(),identity+"/error")
        close(z["mean_signed_slope_error"],err.mean(),identity+"/signed")
        close(z["mean_abs_shift_from_complete"],np.abs(shift).mean(),identity+"/shift")
    else:
        for name in ("mean_effective_cluster_n","max_inverse_observation_weight",
                     "mean_abs_slope_error","mean_signed_slope_error","mean_abs_shift_from_complete"):
            if z[name] is not None:raise ValueError("R83-A no support but fabricated slope metric "+identity)
    return {"method":method,"delta":float(delta),
            "observation_mechanism":m,"observed_fraction":float((~mask).mean()),
            "refusal":int(refused.sum()),
            "abs_error":z["mean_abs_slope_error"],
            "abs_shift":z["mean_abs_shift_from_complete"],
            "effective_n":z["mean_effective_cluster_n"],
            "max_weight":z["max_inverse_observation_weight"],
            "native_refusal":m!="complete",
            "slope":slope}


def audit(original:Path,expected_checkout=CHECKOUT):
    expected="".join(sha256((original/k).read_bytes()).hexdigest()+"  "+k+"\n"
                     for k in ("evidence.json","source-commit.txt"))
    if (original/"SHA256SUMS").read_text()!=expected:
        raise ValueError("R83-A original SHA256 immutability mismatch")
    checkout=(original/"source-commit.txt").read_text().strip()
    if checkout!=expected_checkout or len(checkout)!=40:
        raise ValueError("R83-A frozen original source checkout invalid")
    obj=json.loads((original/"evidence.json").read_text())
    if obj.get("source_checkout")!=checkout:
        raise ValueError("R83-A original checkout manifest mismatch")
    rows=obj["source_evaluations"];report=obj["aggregate"]
    expected_ids=set()
    for b in range(BLOCKS):
        for c in CONFIGS:
            for s in SUPPORT:
                for v in VARIANCES:
                    expected_ids.update([(b,c,s,v,"complete","COMPLETE",0.),
                                         (b,c,s,v,"MCAR","MCAR_known",0.)])
                    expected_ids.update([(b,c,s,v,m,m+"_sensitivity",float(d))
                                         for m in ("MAR","MNAR") for d in DELTA])
                    expected_ids.add((b,c,s,v,"MNAR","MNAR_oracle",1.1))
    ids=[(z["block"],z["config"],z["support"],z["variance"],
          z["observation_mechanism"],z["method"],z["assumed_mnar_delta"]) for z in rows]
    if len(rows)!=DIAGNOSTIC_RECORDS or len(set(ids))!=DIAGNOSTIC_RECORDS or set(ids)!=expected_ids:
        raise ValueError("R83-A inflated or missing original independent-source denominator")
    for k,v in {"study":STUDY,"new_source_seed":SOURCE_SEED,"new_mask_seed":OBS_SEED,
                "independent_primitive_blocks_per_cell":32,
                "original_complete_source_conditions":256,
                "paired_original_observation_masks":1024,
                "pointwise_diagnostic_records":3328,
                "sensitivity_delta_grid":list(DELTA),
                "oracle_unavailable_in_observed_data":True,
                "observation_model_identified":False,
                "confidence_band_calibration":False,
                "release_authorized":False}.items():
        if report.get(k)!=v:raise ValueError("R83-A nonidentified scientific source report qualification mismatch "+k)
    lookup={k:z for k,z in zip(ids,rows)}
    reconstructed={}
    for b in range(BLOCKS):
        for c in CONFIGS:
            for s in SUPPORT:
                for v in VARIANCES:
                    X,Y,b1=replay_XY(b,c,s,v)
                    all_masks=masks(X,Y,b,c,s,v)
                    full=slope_with_support(X,Y,all_masks["complete"])
                    original_full=(full[0],full[1],full[2],full[3],full[4])
                    bysource={}
                    for m,method,ds in [
                        ("complete","COMPLETE",(0.,)),
                        ("MCAR","MCAR_known",(0.,)),
                        ("MAR","MAR_sensitivity",DELTA),
                        ("MNAR","MNAR_sensitivity",DELTA),
                        ("MNAR","MNAR_oracle",(1.1,))]:
                        for d in ds:
                            key=(b,c,s,v,m,method,float(d))
                            bysource[key]=evaluate_row(lookup[key],X,Y,b1,all_masks,original_full)
                    ends=[bysource[(b,c,s,v,"MNAR","MNAR_sensitivity",t)]["slope"]
                          for t in (-1.1,1.1)]
                    eligible=np.isfinite(ends[0])&np.isfinite(ends[1])
                    spread=float(np.mean(np.abs(ends[1][eligible]-ends[0][eligible]))) if eligible.any() else None
                    for key,item in bysource.items():
                        row=lookup[key]
                        expected_spread=(spread if key[5] in ("MNAR_sensitivity","MNAR_oracle") else None)
                        close(row["mnar_endpoint_mean_abs_slope_spread"],expected_spread,str(key)+"/spread")
                    reconstructed.update(bysource)
    # Independent source-wise aggregate validation for all methods/deltas/cells.
    for c in CONFIGS:
        for s in SUPPORT:
            for v in VARIANCES:
                for method in METHODS:
                    ds=DELTA if method in ("MAR_sensitivity","MNAR_sensitivity") else ((1.1,) if method=="MNAR_oracle" else (0.,))
                    for d in ds:
                        sub=[z for key,z in reconstructed.items()
                             if key[1]==c and key[2]==s and key[3]==v
                             and key[5]==method and key[6]==float(d)]
                        if len(sub)!=BLOCKS:raise ValueError("R83-A true source count !=32")
                        expected=report["results"][c][s][v][method][str(float(d))]
                        if expected["new_independent_primitive_blocks"]!=BLOCKS:
                            raise ValueError("R83-A original independent-source denominator mismatch")
                        for name,k in [("mean_observed_fraction","observed_fraction"),
                                       ("mean_refused_grid","refusal"),
                                       ("mean_abs_slope_error","abs_error"),
                                       ("mean_abs_shift_from_complete","abs_shift"),
                                       ("mean_effective_cluster_n","effective_n"),
                                       ("mean_max_observation_weight","max_weight")]:
                            arr=[x[k] for x in sub if x[k] is not None]
                            close(expected[name],float(np.mean(arr)) if arr else None,
                                  c+"/"+s+"/"+v+"/"+method+"/"+name)
                        if expected["native_nan_refusal_sources"]!=sum(x["native_refusal"] for x in sub):
                            raise ValueError("R83-A native refusal source count altered")
    return {"original_source_XY_replayed":256,
            "paired_original_masks_replayed":1024,
            "individual_delta_pointwise_records_replayed":3328,
            "independent_primitive_blocks_per_fixed_cell":32,
            "original_checkout":checkout,
            "MNAR_identified_or_calibrated":False,
            "release_authorized":False}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--expected-checkout",default=CHECKOUT)
    args=p.parse_args()
    result=audit(args.original,args.expected_checkout)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))


if __name__=="__main__":main()
