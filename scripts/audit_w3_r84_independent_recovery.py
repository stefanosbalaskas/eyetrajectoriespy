"""R84-A independent original-source read-only observation-mask replay.

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

STUDY="W3_R84_EXTERNAL_OUTCOME_VALIDATION_FOR_MNAR"
SOURCE_SEED=202610218480
OBS_SEED=202610218481
CHECKOUT="6170c5b5941f55a5083cf57dc11293a229d2f9e1"
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
        if a is not b:raise ValueError("R84-A original mismatch "+what)
        return
    x=np.asarray(a,float);y=np.asarray(b,float)
    if x.shape!=y.shape or not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)):
        raise ValueError("R84-A invalid finite field "+what)
    if not np.allclose(x,y,atol=tol,rtol=1e-8):
        raise ValueError("R84-A original numerical mismatch "+what)


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



RECOVERY_SEED=202610218482
RECOVERY_RATES=(0.,.25,.5)
LOSS_MECHANISMS=("MAR","MNAR")
RECORD_COUNT=1536


def rescue_uniforms(block,config,support,variance,shape):
    key=(RECOVERY_SEED+1000003*block+10007*CONFIGS.index(config)
         +739*SUPPORT.index(support)+97*VARIANCES.index(variance))
    return np.random.default_rng(key).random(shape),key


def pilot_from_visible(X,Y,mask):
    """Independent centered-covariance formula using ONLY originally visible outcomes."""
    alpha=np.full((31,2,2),np.nan)
    permitted=np.zeros((31,2),bool)
    observed_units=np.zeros((31,2),int)
    for t in range(31):
        for d in range(2):
            uid,trial=np.where(~mask[:,:,t,d])
            observed_units[t,d]=len(np.unique(uid))
            if observed_units[t,d]<8:continue
            x=X[uid,1]
            y=Y[uid,trial,t,d]
            x0=x.mean()
            denom=np.dot(x-x0,x-x0)
            if denom<=1e-10:continue
            slope=np.dot(x-x0,y-y.mean())/denom
            intercept=y.mean()-slope*x0
            alpha[t,d]=[intercept,slope]
            permitted[t,d]=True
    return alpha,permitted,observed_units


def score_root(X,Y,mask,recovered,pilot,admissible,rate):
    """Independent bounded bisection on monotone weighted Bernoulli score."""
    if rate==0:
        return None,False,0,None,None,False,0
    uid,tr,t,d=np.where((~mask|recovered)&admissible[None,None,:,:])
    included=int(len(uid))
    if not included or not (recovered&admissible[None,None,:,:]).any():
        return None,False,0,None,None,False,included
    x=X[uid,1]
    y=Y[uid,tr,t,d]
    residual=(y-(pilot[t,d,0]+pilot[t,d,1]*x))/.08
    h=np.tanh(residual)
    offset=-2.2+np.abs(x)/4+.7*T[t]+.2*tr
    missing=mask[uid,tr,t,d].astype(float)
    weights=np.where(missing>0,1/rate,1)
    def calc(delta):
        eta=np.clip(offset+delta*h,-45,45)
        prop=1/(1+np.exp(-eta))
        sc=float(np.dot(weights*h,missing-prop))
        info=float(np.dot(weights*h*h,prop*(1-prop)))
        return sc,info
    a,b=-4.,4.
    low=calc(a)[0]
    high=calc(b)[0]
    if low<0 or high>0:
        # Frozen original Newton cannot solve interior if root lies outside
        # [-4,4]; explicitly refuse rather than manufacture certainty.
        bound=a if low<0 else b
        score,inf=calc(bound)
        return None,False,35,score,inf,True,included
    delta=0.
    for _ in range(80):
        delta=(a+b)/2
        score,info=calc(delta)
        if abs(score)<1e-9 or b-a<1e-12:break
        if score>0:a=delta
        else:b=delta
    score,info=calc(delta)
    return float(delta),True,35,float(score),float(info),False,included


def check_row(row,X,Y,mask,pilot,admissible,observed_units,recovery_uniform,key):
    label=f"{row['block']}/{row['config']}/{row['support']}/{row['variance']}/{row['mechanism']}/{row['recovery_rate']}"
    if (row["study"]!=STUDY or row["release_authorized"] is not False
        or row["source_known_truth_used_by_estimator"] is not False
        or row["no_interval_no_band_no_mnar_nonparametric_identification"] is not True
        or row["recoveries_independent_given_original_missing"] is not True
        or row["native_public_missing_gaze_refused"] is not True
        or row["source_seed"]!=source_seed(row["block"],row["config"])
        or row["mask_seed"]!=observation_seed(row["block"],row["config"],row["support"],row["variance"])
        or row["recovery_seed"]!=key or row["source_independent_units"]!=len(X)
        or row["trials_per_independent_unit"]!=Y.shape[1]):
        raise ValueError("R84-A source truth leakage or release provenance mismatch "+label)
    rate=row["recovery_rate"]
    rec=mask&(recovery_uniform<rate)
    for k,expected in [
        ("source_X_digest",digest(X)),
        ("source_Y_digest",digest(Y)),
        ("original_mask_digest",mask_digest(mask)),
        ("recovered_missing_mask_digest",mask_digest(rec)),
        ("observed_only_pilot_digest",digest(np.nan_to_num(pilot,nan=0.)))]:
        if row[k]!=expected:
            raise ValueError("R84-A independent original X/Y/mask/pilot SHA256 mismatch "+label+"/"+k)
    if (row["original_missing_count"]!=int(mask.sum())
        or row["externally_recovered_count"]!=int(rec.sum())
        or row["pilot_grid_refused_count"]!=int((~admissible).sum())
        or row["pilot_min_distinct_observed_units"]!=int(observed_units.min())):
        raise ValueError("R84-A recovered count or visible pilot refusal mismatch "+label)
    if not np.isclose(row["original_observed_fraction"],(~mask).mean(),atol=1e-12):
        raise ValueError("R84-A original observed source proportion mismatch "+label)
    delta,success,steps,score,info,bound,included=score_root(
        X,Y,mask,rec,pilot,admissible,rate)
    if (row["converged"] is not success
        or row["identified_with_external_validation"] is not success
        or row["boundary_saturated"] is not bound
        or row["included_measured_responses"]!=included):
        raise ValueError("R84-A estimator convergence or identified-information flag mismatch "+label)
    if success:
        if row["delta_estimate"] is None or abs(row["delta_estimate"]-delta)>2e-6:
            raise ValueError("R84-A independent scalar weighted score root disagreement "+label)
        dtruth=0. if row["mechanism"]=="MAR" else 1.1
        if abs(row["delta_abs_error"]-abs(delta-dtruth))>2e-6:
            raise ValueError("R84-A simulated truth evaluation mismatch "+label)
        if abs(row["weighted_score_residual"])>1e-5:
            raise ValueError("R84-A nonzero weighted selection score "+label)
    else:
        if row["delta_estimate"] is not None or row["delta_abs_error"] is not None:
            raise ValueError("R84-A zero-ascertainment generated fake δ estimate "+label)
    return row


def audit(original:Path,expected_checkout=CHECKOUT):
    checks="".join(sha256((original/k).read_bytes()).hexdigest()+"  "+k+"\n"
                   for k in ("evidence.json","source-commit.txt"))
    if (original/"SHA256SUMS").read_text()!=checks:
        raise ValueError("R84-A immutable original SHA256 evidence altered")
    checkout=(original/"source-commit.txt").read_text().strip()
    if checkout!=expected_checkout or len(checkout)!=40:
        raise ValueError("R84-A original exact scientific checkout invalid")
    obj=json.loads((original/"evidence.json").read_text())
    if obj.get("source_checkout")!=checkout:
        raise ValueError("R84-A original checkout provenance mismatch")
    rows=obj["source_evaluations"]
    report=obj["aggregate"]
    all_ids={(b,c,s,v,m,r) for b in range(BLOCKS)
             for c in CONFIGS for s in SUPPORT for v in VARIANCES
             for m in LOSS_MECHANISMS for r in RECOVERY_RATES}
    actual=[(z["block"],z["config"],z["support"],z["variance"],z["mechanism"],z["recovery_rate"]) for z in rows]
    if len(rows)!=RECORD_COUNT or len(set(actual))!=RECORD_COUNT or set(actual)!=all_ids:
        raise ValueError("R84-A source-denominator and nested-validation grid mismatch")
    fields={"study":STUDY,"new_source_seed":SOURCE_SEED,"new_mask_seed":OBS_SEED,
            "new_recovery_seed":RECOVERY_SEED,"true_independent_blocks_per_cell":32,
            "complete_XY_source_conditions":256,"original_mask_conditions":512,
            "diagnostic_recovery_evaluations":1536,"recovery_fractions":list(RECOVERY_RATES),
            "mechanisms":list(LOSS_MECHANISMS),"no_validation_identifies_delta":False,
            "nonparametric_MNAR_identification":False,
            "any_confidence_interval_or_band":False,"release_authorized":False}
    for k,v in fields.items():
        if report.get(k)!=v:raise ValueError("R84-A original source study provenance mismatch "+k)
    idx=dict(zip(actual,rows))
    recovered=[]
    for block in range(BLOCKS):
        for config in CONFIGS:
            for support in SUPPORT:
                for variance in VARIANCES:
                    X,Y,beta=replay_XY(block,config,support,variance)
                    source_masks=masks(X,Y,block,config,support,variance)
                    field,key=rescue_uniforms(block,config,support,variance,Y.shape)
                    for mechanism in LOSS_MECHANISMS:
                        mask=source_masks[mechanism]
                        pilot,valid,counts=pilot_from_visible(X,Y,mask)
                        for rate in RECOVERY_RATES:
                            row=idx[(block,config,support,variance,mechanism,rate)]
                            recovered.append(check_row(row,X,Y,mask,pilot,valid,counts,field,key))
    for config in CONFIGS:
        for support in SUPPORT:
            for variance in VARIANCES:
                for mechanism in LOSS_MECHANISMS:
                    for rate in RECOVERY_RATES:
                        rows_=[z for z in recovered if z["config"]==config and z["support"]==support
                               and z["variance"]==variance and z["mechanism"]==mechanism
                               and z["recovery_rate"]==rate]
                        if len(rows_)!=32:raise ValueError("R84-A independent source block count invalid")
                        actual=report["results"][config][support][variance][mechanism][str(rate)]
                        valid=[z for z in rows_ if z["delta_estimate"] is not None]
                        def mean(field,items=rows_):
                            vals=[z[field] for z in items if z[field] is not None]
                            return float(np.mean(vals)) if vals else None
                        for field,k,subset in [
                            ("mean_missing_fraction","original_observed_fraction",rows_),
                            ("mean_recovered_missing_count","externally_recovered_count",rows_),
                            ("mean_refused_pilot_grid","pilot_grid_refused_count",rows_),
                            ("mean_delta_estimate_converged_only","delta_estimate",valid),
                            ("mean_absolute_delta_error_converged_only","delta_abs_error",valid)]:
                            value=1-mean(k,subset) if field=="mean_missing_fraction" else mean(k,subset)
                            if (value is None)!=(actual[field] is None) or (value is not None and abs(value-actual[field])>1e-8):
                                raise ValueError("R84-A independently reconstructed aggregate error "+field)
                        if actual["independent_source_blocks"]!=32 or actual["converged_sources"]!=len(valid):
                            raise ValueError("R84-A source denominator/converged count forged")
    return {"original_complete_XY_sources_replayed":256,
            "original_paired_MAR_MNAR_masks_replayed":512,
            "nested_external_recovery_records_replayed":1536,
            "independent_primitive_blocks_per_cell":32,
            "original_source_checkout":checkout,
            "nonparametric_MNAR_identification":False,
            "any_confidence_band_calibrated":False,
            "release_authorized":False}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--expected-checkout",default=CHECKOUT)
    q=p.parse_args()
    report=audit(q.original,q.expected_checkout)
    q.out.parent.mkdir(parents=True,exist_ok=True)
    q.out.write_text(json.dumps(report,sort_keys=True)+"\n")
    print(json.dumps(report,sort_keys=True))

if __name__=="__main__":
    main()
