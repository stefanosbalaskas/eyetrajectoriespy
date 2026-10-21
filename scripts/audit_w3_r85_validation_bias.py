"""R85-A independent original-source read-only observation-mask replay.

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

STUDY="W3_R85_VALIDATION_ASCERTAINMENT_BIAS"
SOURCE_SEED=202610218580
OBS_SEED=202610218581
CHECKOUT="ORIGINAL_R85_SCIENCE_CHECKOUT_TO_PIN"
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
        if a is not b:raise ValueError("R85-A original mismatch "+what)
        return
    x=np.asarray(a,float);y=np.asarray(b,float)
    if x.shape!=y.shape or not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)):
        raise ValueError("R85-A invalid finite field "+what)
    if not np.allclose(x,y,atol=tol,rtol=1e-8):
        raise ValueError("R85-A original numerical mismatch "+what)


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



RECOVERY_SEED=202610218582
STRATEGIES=("independent_known","recorded_naive","recorded_correct","latent_naive","latent_oracle")
LAWS=("independent","recorded","latent")
SOURCE_STRATEGY_ROWS=2560


def validation_uniforms(block,config,support,variance,shape):
    key=RECOVERY_SEED+1000003*block+10007*CONFIGS.index(config)+739*SUPPORT.index(support)+97*VARIANCES.index(variance)
    return np.random.default_rng(key).random(shape),key


def true_validation_prob(X,Y,law):
    if law=="independent":return np.full(Y.shape,.25)
    base=np.log(.25/.75)
    x=np.abs(X[:,1,None,None,None])
    if law=="recorded":
        z=base+.7*x/4.+.7*T[None,None,:,None]
        return np.broadcast_to(1/(1+np.exp(-z)),Y.shape).copy()
    if law!="latent":raise ValueError("R85-A unprespecified validation family")
    b0,b1=truth()
    source_mean=b0[None]+X[:,1,None,None]*b1[None]
    z=base+np.tanh((Y-source_mean[:,None])/.08)
    return 1/(1+np.exp(-z))


def observed_pilot_independent(X,Y,missing):
    beta=np.full((31,2,2),np.nan)
    allowed=np.zeros((31,2),bool)
    independent_unit_count=np.zeros((31,2),int)
    for t in range(31):
        for d in range(2):
            uid,j=np.where(~missing[:,:,t,d])
            independent_unit_count[t,d]=len(np.unique(uid))
            if independent_unit_count[t,d]<8:continue
            x=X[uid,1]; y=Y[uid,j,t,d]
            centered=x-x.mean()
            denom=float(centered@centered)
            if denom<=1e-12:continue
            slope=float(centered@(y-y.mean())/denom)
            beta[t,d]=(y.mean()-slope*x.mean(),slope)
            allowed[t,d]=True
    return beta,allowed,independent_unit_count


def independent_newton_score(X,Y,missing,recovered,pilot,valid,recovery_probability):
    included=(~missing|recovered)&valid[None,None,:,:]
    uid,j,t,d=np.nonzero(included)
    if not len(uid) or not (recovered&valid[None,None,:,:]).any():
        return None,False,None,None,len(uid),False
    y=Y[uid,j,t,d]
    x=X[uid,1]
    mean=pilot[t,d,0]+pilot[t,d,1]*x
    h=np.tanh((y-mean)/.08)
    offset=-2.2+np.abs(x)/4+.7*T[t]+.2*j
    m=missing[uid,j,t,d].astype(bool)
    p_validation=recovery_probability[uid,j,t,d]
    if np.any(~np.isfinite(p_validation)) or np.any(p_validation[m]<=0):
        return None,False,None,None,len(uid),False
    weight=np.where(m,1/p_validation,1.)
    def sufficient(delta):
        pi=1/(1+np.exp(-np.clip(offset+delta*h,-45,45)))
        score=float(np.dot(weight*h,m.astype(float)-pi))
        fisher=float(np.dot(weight*h*h,pi*(1-pi)))
        return score,fisher
    low,high=-4.,4.
    if sufficient(low)[0]<0 or sufficient(high)[0]>0:
        return None,False,None,None,len(uid),True
    delta=0.
    for iteration in range(45):
        score,information=sufficient(delta)
        if not np.isfinite(score) or not np.isfinite(information) or information<1e-12:
            return None,False,None,None,len(uid),False
        if abs(score)<1e-8:break
        update=float(np.clip(delta+score/information,low,high))
        if update==delta:
            break
        delta=update
    score,information=sufficient(delta)
    if not np.isfinite(score) or not np.isfinite(information) or information<1e-12 or abs(score)>1e-6:
        return None,False,score,information,len(uid),False
    return float(delta),True,score,information,len(uid),False


def check_case(z,X,Y,m,pilot,valid,native_counts,U,recovery_seed):
    strategy=z["strategy"]
    law="independent" if strategy=="independent_known" else "recorded" if strategy.startswith("recorded") else "latent"
    actual=true_validation_prob(X,Y,law)
    recovery=m&(U<actual)
    assumed=np.full(Y.shape,.25) if strategy.endswith("naive") else actual
    identity="/".join(map(str,(z["block"],z["config"],z["support"],z["variance"],z["mechanism"],strategy)))
    if (z["study"]!=STUDY or z["strategy"] not in STRATEGIES or z["validation_law"]!=law
        or z["source_seed"]!=source_seed(z["block"],z["config"])
        or z["original_mask_seed"]!=observation_seed(z["block"],z["config"],z["support"],z["variance"])
        or z["validation_uniform_seed"]!=recovery_seed
        or z["source_X_digest"]!=digest(X) or z["source_Y_digest"]!=digest(Y)
        or z["original_missing_mask_digest"]!=mask_digest(m)
        or z["validation_mask_digest"]!=mask_digest(recovery)
        or z["validation_probability_digest"]!=digest(actual)
        or z["original_visible_only_pilot_digest"]!=digest(np.nan_to_num(pilot,nan=0.))
        or z["release_authorized"] is not False
        or z["no_inference_or_calibration_claim"] is not True
        or z["validated_outcomes_not_imputed"] is not True
        or z["true_first_stage_delta_not_used_for_fitting"] is not True
        or z["original_public_regression_refused"] is not True
        or z["oracle_validation_propensity_used"] is not (strategy=="latent_oracle")
        or z["true_mean_only_used_for_latent_oracle_weight"] is not (strategy=="latent_oracle")):
        raise ValueError("R85-A source/validation provenance, oracle boundary or SHA256 mismatch "+identity)
    if (z["n_original_missing"]!=int(m.sum()) or z["n_recovered"]!=int(recovery.sum())
        or z["pilot_refused_grid"]!=int((~valid).sum())
        or z["pilot_min_native_units"]!=int(native_counts.min())
        or abs(z["original_observed_fraction"]-(~m).mean())>1e-12):
        raise ValueError("R85-A real source sample counts or independent pilot refusal mismatch "+identity)
    delta,converged,score,information,n_included,bound=independent_newton_score(
        X,Y,m,recovery,pilot,valid,assumed)
    if (z["converged"] is not converged or z["boundary_refused"] is not bound or
        z["included_measured_outcomes"]!=n_included):
        raise ValueError("R85-A independent solver/refusal source disagreement "+identity)
    truth=0. if z["mechanism"]=="MAR" else 1.1
    if z["true_first_stage_delta_simulator_only"]!=truth:
        raise ValueError("R85-A actual source first-stage truth identity mismatch "+identity)
    if converged:
        if (z["delta_estimate"] is None or abs(z["delta_estimate"]-delta)>2e-6 or
            abs(z["delta_error_signed"]-(delta-truth))>2e-6 or
            abs(z["delta_error_absolute"]-abs(delta-truth))>2e-6 or
            abs(z["weighted_score"])>2e-6 or z["pseudo_information"] is None):
            raise ValueError("R85-A original observed/recovered weighted score mismatch "+identity)
    else:
        if z["delta_estimate"] is not None or z["delta_error_absolute"] is not None:
            raise ValueError("R85-A manufactured coefficient on refused original source "+identity)
    return z


def audit(path:Path,checkout=CHECKOUT):
    checksum="".join(sha256((path/p).read_bytes()).hexdigest()+"  "+p+"\n"
                     for p in ("evidence.json","source-commit.txt"))
    if (path/"SHA256SUMS").read_text()!=checksum:
        raise ValueError("R85-A original immutable archive SHA256 altered")
    original_sha=(path/"source-commit.txt").read_text().strip()
    if len(original_sha)!=40 or checkout!=original_sha:
        raise ValueError("R85-A pinned original science checkout mismatch")
    obj=json.loads((path/"evidence.json").read_text())
    if obj.get("original_checkout")!=original_sha:
        raise ValueError("R85-A original checkout evidence manifest mismatch")
    rows=obj["source_evaluations"]
    agg=obj["aggregate"]
    known={(b,c,s,v,m,k) for b in range(BLOCKS) for c in CONFIGS for s in SUPPORT
           for v in VARIANCES for m in ("MAR","MNAR") for k in STRATEGIES}
    identifiers=[(z["block"],z["config"],z["support"],z["variance"],z["mechanism"],z["strategy"]) for z in rows]
    if len(rows)!=SOURCE_STRATEGY_ROWS or len(set(identifiers))!=SOURCE_STRATEGY_ROWS or set(identifiers)!=known:
        raise ValueError("R85-A genuine independent original source denominator mismatch")
    for k,v in {"study":STUDY,"new_source_seed":SOURCE_SEED,
                "original_mask_seed":OBS_SEED,"new_validation_seed":RECOVERY_SEED,
                "primitive_independent_blocks_per_cell":32,
                "complete_source_conditions":256,"original_MAR_MNAR_masks":512,
                "source_strategy_rows":2560,"strategies":list(STRATEGIES),
                "validation_laws":list(LAWS),
                "nonrandom_validation_can_be_identified_from_original_missing_gaze":False,
                "simulator_only_validation_oracle_is_deployable":False,
                "confidence_bands_evaluated":False,"release_authorized":False}.items():
        if agg.get(k)!=v:raise ValueError("R85-A reported original scientific/release provenance mismatch "+k)
    lookup=dict(zip(identifiers,rows))
    verified=[]
    for b in range(BLOCKS):
        for c in CONFIGS:
            for s in SUPPORT:
                for v in VARIANCES:
                    X,Y,_=replay_XY(b,c,s,v)
                    masks_original=masks(X,Y,b,c,s,v)
                    U,key=validation_uniforms(b,c,s,v,Y.shape)
                    for m in ("MAR","MNAR"):
                        original_missing=masks_original[m]
                        p,allowed,units=observed_pilot_independent(X,Y,original_missing)
                        for strategy in STRATEGIES:
                            z=lookup[(b,c,s,v,m,strategy)]
                            verified.append(check_case(z,X,Y,original_missing,p,allowed,units,U,key))
    for c in CONFIGS:
        for s in SUPPORT:
            for v in VARIANCES:
                for m in ("MAR","MNAR"):
                    for strategy in STRATEGIES:
                        group=[z for z in verified if z["config"]==c and z["support"]==s and
                               z["variance"]==v and z["mechanism"]==m and z["strategy"]==strategy]
                        if len(group)!=BLOCKS:raise ValueError("R85-A original source count not 32")
                        original=agg["results"][c][s][v][m][strategy]
                        fitted=[z for z in group if z["converged"] and z["delta_estimate"] is not None]
                        if original["primitive_blocks"]!=32 or original["converged_sources"]!=len(fitted):
                            raise ValueError("R85-A per-strategy source failure count mismatch")
                        for title,k,gg in [("mean_recovered","n_recovered",group),
                                           ("mean_original_missing","n_original_missing",group),
                                           ("mean_pilot_refused","pilot_refused_grid",group),
                                           ("mean_estimated_delta","delta_estimate",fitted),
                                           ("mean_signed_delta_error","delta_error_signed",fitted),
                                           ("mean_abs_delta_error","delta_error_absolute",fitted),
                                           ("mean_pseudo_information","pseudo_information",fitted)]:
                            values=[z[k] for z in gg if z[k] is not None]
                            check=float(np.mean(values)) if values else None
                            close(original[title],check,"R85-A "+title,tol=1e-7)
                        if original["boundary_refused_sources"]!=sum(z["boundary_refused"] for z in group):
                            raise ValueError("R85-A original boundary refusal record mismatch")
    return {"original_source_XY_replayed":256,
            "original_MAR_MNAR_masks_replayed":512,
            "original_selection_strategy_rows_replayed":2560,
            "true_independent_primitive_blocks_per_cell":32,
            "source_checkout":original_sha,
            "nonrandom_external_validation_identified_from_original_data":False,
            "true_outcome_oracle_is_deployable":False,
            "confidence_bands_calibrated":False,"release_authorized":False}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--original",type=Path,required=True)
    parser.add_argument("--expected-checkout",default=CHECKOUT)
    parser.add_argument("--out",type=Path,required=True)
    opt=parser.parse_args()
    report=audit(opt.original,opt.expected_checkout)
    opt.out.parent.mkdir(parents=True,exist_ok=True)
    opt.out.write_text(json.dumps(report,sort_keys=True)+"\n")
    print(json.dumps(report,sort_keys=True))

if __name__=="__main__":main()
