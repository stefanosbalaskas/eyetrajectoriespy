"""R86-A independent original-source read-only observation-mask replay.

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

STUDY="W3_R86_THIRD_STAGE_INDEPENDENT_VALIDATION_AUDIT"
SOURCE_SEED=202610218680
OBS_SEED=202610218681
CHECKOUT="PIN_ORIGINAL_R86_MERGE_SHA"
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
        if a is not b:raise ValueError("R86-A original mismatch "+what)
        return
    x=np.asarray(a,float);y=np.asarray(b,float)
    if x.shape!=y.shape or not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)):
        raise ValueError("R86-A invalid finite field "+what)
    if not np.allclose(x,y,atol=tol,rtol=1e-8):
        raise ValueError("R86-A original numerical mismatch "+what)


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



from scipy.optimize import root

RECOVERY_SEED=202610218682
AUDIT_SEED=202610218683
AUDIT_LEVELS=(0.,.25,.5)
STRATEGIES=("naive_union","audit_estimated","source_oracle_union")
RECORDS=4608


def two_uniforms(block,config,support,variance,shape):
    off=1000003*block+10007*CONFIGS.index(config)+739*SUPPORT.index(support)+97*VARIANCES.index(variance)
    return (np.random.default_rng(RECOVERY_SEED+off).random(shape),
            np.random.default_rng(AUDIT_SEED+off).random(shape),
            RECOVERY_SEED+off,AUDIT_SEED+off)


def true_secondary_recovery(X,Y):
    b0,b1=truth()
    true_mu=b0[None]+X[:,1,None,None]*b1[None]
    return 1/(1+np.exp(-(np.log(.25/.75)+np.tanh((Y-true_mu[:,None])/.08))))


def visible_pilot_independently(X,Y,missing):
    out=np.full((31,2,2),np.nan)
    permitted=np.zeros((31,2),bool)
    unit_count=np.zeros((31,2),int)
    for t in range(31):
        for d in range(2):
            row,trial=np.where(~missing[:,:,t,d])
            unit_count[t,d]=len(np.unique(row))
            if unit_count[t,d]<8:continue
            x=X[row,1]
            y=Y[row,trial,t,d]
            centered=x-x.mean()
            denominator=float(centered@centered)
            if denominator<=1e-12:continue
            slope=float(centered@(y-y.mean())/denominator)
            out[t,d]=[y.mean()-slope*x.mean(),slope]
            permitted[t,d]=True
    return out,permitted,unit_count


def independently_fit_secondary(X,Y,initial,audit,pilot,allowed,q):
    if q==0:return None,None,False,0,None,None,False
    uid,tr,t,d=np.where((initial|audit)&allowed[None,None,:,:])
    if len(uid)<20 or not (audit&allowed[None,None,:,:]).any():
        return None,None,False,len(uid),None,None,False
    response=Y[uid,tr,t,d]
    pilot_mu=pilot[t,d,0]+pilot[t,d,1]*X[uid,1]
    h=np.tanh((response-pilot_mu)/.08)
    indicators=initial[uid,tr,t,d].astype(float)
    weights=np.where(indicators>0,1.,1./q)
    feature=np.stack((np.ones(len(h)),h),axis=1)
    def f(theta):
        pi=1/(1+np.exp(-np.clip(feature@theta,-45.,45.)))
        return feature.T@(weights*(indicators-pi))
    def jac(theta):
        pi=1/(1+np.exp(-np.clip(feature@theta,-45.,45.)))
        return -(feature.T@((weights*pi*(1-pi))[:,None]*feature))
    result=root(f,np.array([np.log(.25/.75),0.]),jac=jac,method="hybr",
                options={"xtol":1e-11,"maxfev":600})
    theta=np.asarray(result.x,float)
    val=f(theta)
    information=-jac(theta)
    info_eig=float(np.linalg.eigvalsh(information)[0])
    bound=bool(abs(theta[0])>=7.999999 or abs(theta[1])>=3.999999)
    valid=(np.isfinite(theta).all() and abs(theta[0])<8. and abs(theta[1])<4.
           and info_eig>1e-10 and np.isfinite(val).all() and np.max(np.abs(val))<1e-6)
    if not valid:return None,None,False,len(uid),float(np.max(np.abs(val))),info_eig,bound
    return float(theta[0]),float(theta[1]),True,len(uid),float(np.max(np.abs(val))),info_eig,bound


def independently_fit_delta(X,Y,missing,recovered,pilot,allowed,assumed_union):
    uid,tr,t,d=np.where((~missing|recovered)&allowed[None,None,:,:])
    if not len(uid) or not (recovered&allowed[None,None,:,:]).any():
        return None,False,None,None,0,False
    x=X[uid,1]; response=Y[uid,tr,t,d]
    residual=np.tanh((response-(pilot[t,d,0]+pilot[t,d,1]*x))/.08)
    offset=-2.2+np.abs(x)/4.+.7*T[t]+.2*tr
    m=missing[uid,tr,t,d]
    probability=assumed_union[uid,tr,t,d]
    if not np.isfinite(probability).all() or (probability[m]<=0).any():
        return None,False,None,None,len(uid),False
    w=np.where(m,1./probability,1.)
    def stats(z):
        p=1/(1+np.exp(-np.clip(offset+z*residual,-45,45)))
        return float(np.dot(w*residual,m.astype(float)-p)),float(np.dot(w*residual**2,p*(1-p)))
    if stats(-4.)[0]<0 or stats(4.)[0]>0:
        return None,False,None,None,len(uid),True
    delta=0.
    for iteration in range(60):
        sc,info=stats(delta)
        if not np.isfinite(sc) or not np.isfinite(info) or info<=1e-12:
            return None,False,None,None,len(uid),False
        if abs(sc)<1e-8:break
        new=float(np.clip(delta+sc/info,-4,4))
        if new==delta:break
        delta=new
    score,info=stats(delta)
    if not np.isfinite(score) or not np.isfinite(info) or info<=1e-12 or abs(score)>1e-6:
        return None,False,score,info,len(uid),False
    return float(delta),True,score,info,len(uid),False


def verify_one(row,X,Y,missing,primary,audit_,total,pilot,allowed,units,true_prop,seeds):
    label="/".join(map(str,(row["block"],row["config"],row["support"],row["variance"],
                              row["mechanism"],row["audit_fraction"],row["strategy"])))
    q=row["audit_fraction"];strategy=row["strategy"]
    oracle=strategy=="source_oracle_union"
    if (row["study"]!=STUDY or row["source_seed"]!=source_seed(row["block"],row["config"])
        or row["mask_seed"]!=observation_seed(row["block"],row["config"],row["support"],row["variance"])
        or row["secondary_seed"]!=seeds[0] or row["audit_seed"]!=seeds[1]
        or row["source_X_digest"]!=digest(X) or row["source_Y_digest"]!=digest(Y)
        or row["source_mask_digest"]!=mask_digest(missing)
        or row["secondary_success_digest"]!=mask_digest(primary)
        or row["audit_success_digest"]!=mask_digest(audit_)
        or row["union_success_digest"]!=mask_digest(total)
        or row["true_secondary_propensity_digest"]!=digest(true_prop)
        or row["original_only_pilot_digest"]!=digest(np.nan_to_num(pilot,nan=0.))
        or row["trials_per_unit"]!=Y.shape[1] or row["source_native_independent_units"]!=len(X)
        or row["true_secondary_propensity_used_in_fitted_weights"] is not oracle
        or row["simulator_true_first_stage_delta_used_in_fit"] is not False
        or row["simulator_true_mean_used_in_fitted_pilot"] is not False
        or row["audit_selection_independent_by_construction"] is not True
        or row["recovery_model_identifiable_without_audit"] is not False
        or row["confidence_interval_or_band_validated"] is not False
        or row["release_authorized"] is not False
        or row["unrecovered_outcomes_excluded_from_estimator"] is not True
        or row["actual_original_gaze_nans_refused"] is not True):
        raise ValueError("R86-A original source SHA256 or scientific privilege mismatch "+label)
    if (row["original_missing"]!=int(missing.sum()) or row["secondary_recovered"]!=int(primary.sum())
        or row["third_stage_audited"]!=int(audit_.sum()) or
        row["pilot_refused_grid"]!=int((~allowed).sum()) or
        row["pilot_min_distinct_units"]!=int(units.min())):
        raise ValueError("R86-A original source denominator or audit provenance mismatch "+label)
    if strategy=="audit_estimated":
        alpha,gamma,fit,n,sc,info,bound=independently_fit_secondary(
            X,Y,primary,audit_,pilot,allowed,q)
        if (row["recovery_fit_converged"] is not fit or row["n_recovery_likelihood"]!=n or
            row["recovery_fit_boundary"] is not bound):
            raise ValueError("R86-A audit selection fitting/refusal disagreement "+label)
        if fit:
            if (abs(row["recovery_alpha_fit"]-alpha)>1e-5 or
                abs(row["recovery_gamma_fit"]-gamma)>1e-5 or
                abs(row["recovery_gamma_abs_error"]-abs(gamma-1.))>1e-5):
                raise ValueError("R86-A original and independent recovered-sample gamma mismatch "+label)
            residual=np.tanh((Y-(pilot[None,None,:,:,0]+X[:,1,None,None,None]*pilot[None,None,:,:,1]))/.08)
            pp=1/(1+np.exp(-np.clip(alpha+gamma*residual,-45,45)))
            probability=q+(1-q)*pp
        else:
            probability=None
            if row["recovery_gamma_fit"] is not None:
                raise ValueError("R86-A original source fabricated gamma after secondary failure "+label)
    elif oracle:
        probability=q+(1-q)*true_prop
    else:
        probability=np.full(Y.shape,.25+.75*q)
    if probability is None:
        delta,successful,score,info,n_in,bound=(None,False,None,None,0,False)
    else:
        delta,successful,score,info,n_in,bound=independently_fit_delta(
            X,Y,missing,total,pilot,allowed,probability)
    if (row["delta_converged"] is not successful or row["n_in_first_stage_score"]!=n_in or
        row["first_stage_bound_refused"] is not bound):
        raise ValueError("R86-A first-stage selection refusal/count mismatch "+label)
    truth=0. if row["mechanism"]=="MAR" else 1.1
    if row["true_first_stage_delta_source_only"]!=truth or row["true_secondary_gamma_source_only"]!=1.:
        raise ValueError("R86-A source law/scientific truth changed "+label)
    if successful:
        if (row["delta_estimate"] is None or abs(row["delta_estimate"]-delta)>2e-5 or
            abs(row["delta_error_signed"]-(delta-truth))>2e-5 or
            abs(row["delta_error_absolute"]-abs(delta-truth))>2e-5 or
            abs(row["delta_score"])>1e-5):
            raise ValueError("R86-A independent original first-stage weighted delta mismatch "+label)
    elif row["delta_estimate"] is not None:
        raise ValueError("R86-A first-stage delta fabricated on refused fit "+label)
    return row


def audit(path:Path,expected_checkout=CHECKOUT):
    expected="".join(sha256((path/f).read_bytes()).hexdigest()+"  "+f+"\n"
                     for f in ("evidence.json","source-commit.txt"))
    if (path/"SHA256SUMS").read_text()!=expected:
        raise ValueError("R86-A actual original source SHA256 altered")
    sha=(path/"source-commit.txt").read_text().strip()
    if len(sha)!=40 or sha!=expected_checkout:
        raise ValueError("R86-A pinned original science source checkout invalid")
    content=json.loads((path/"evidence.json").read_text())
    if content.get("original_checkout")!=sha:
        raise ValueError("R86-A scientific source checkout manifest mismatch")
    rows=content["source_evaluations"];agg=content["aggregate"]
    keys={(b,c,s,v,m,q,k) for b in range(BLOCKS) for c in CONFIGS for s in SUPPORT for v in VARIANCES
          for m in ("MAR","MNAR") for q in AUDIT_LEVELS for k in STRATEGIES}
    ids=[(z["block"],z["config"],z["support"],z["variance"],z["mechanism"],z["audit_fraction"],z["strategy"]) for z in rows]
    if len(rows)!=RECORDS or len(set(ids))!=RECORDS or set(ids)!=keys:
        raise ValueError("R86-A original independent unit/strategy denominator violated")
    for k,v in {"study":STUDY,"source_seed":SOURCE_SEED,"original_mask_seed":OBS_SEED,
                "secondary_seed":RECOVERY_SEED,"audit_seed":AUDIT_SEED,
                "primitive_blocks_per_cell":32,"complete_source_conditions":256,
                "original_first_stage_MAR_MNAR_masks":512,"analysis_records":4608,
                "audit_fractions":list(AUDIT_LEVELS),"strategies":list(STRATEGIES),
                "no_audit_recovers_gamma":False,
                "external_audit_available_in_real_gaze":False,
                "confidence_bands_validated":False,"release_authorized":False}.items():
        if agg.get(k)!=v:raise ValueError("R86-A source scientific/release identity mismatch "+k)
    lookup=dict(zip(ids,rows))
    checked=[]
    for b in range(BLOCKS):
        for c in CONFIGS:
            for s in SUPPORT:
                for v in VARIANCES:
                    X,Y,_=replay_XY(b,c,s,v)
                    mm=masks(X,Y,b,c,s,v)
                    U,V,seedU,seedV=two_uniforms(b,c,s,v,Y.shape)
                    rtrue=true_secondary_recovery(X,Y)
                    for m in ("MAR","MNAR"):
                        missing=mm[m]
                        primary=missing&(U<rtrue)
                        pilot,allowed,unit_counts=visible_pilot_independently(X,Y,missing)
                        for q in AUDIT_LEVELS:
                            recovered_failed=missing&(~primary)&(V<q)
                            total=primary|recovered_failed
                            for k in STRATEGIES:
                                z=lookup[(b,c,s,v,m,q,k)]
                                checked.append(verify_one(
                                    z,X,Y,missing,primary,recovered_failed,total,pilot,
                                    allowed,unit_counts,rtrue,(seedU,seedV)))
    for c in CONFIGS:
        for s in SUPPORT:
            for v in VARIANCES:
                for m in ("MAR","MNAR"):
                    for q in AUDIT_LEVELS:
                        for k in STRATEGIES:
                            cell=[z for z in checked if z["config"]==c and z["support"]==s
                                  and z["variance"]==v and z["mechanism"]==m
                                  and z["audit_fraction"]==q and z["strategy"]==k]
                            if len(cell)!=32:
                                raise ValueError("R86-A source block denominator not 32")
                            original=agg["results"][c][s][v][m][str(q)][k]
                            good=[z for z in cell if z["delta_converged"] and z["delta_estimate"] is not None]
                            gg=[z for z in cell if z["recovery_fit_converged"] and z["recovery_gamma_fit"] is not None]
                            if (original["true_new_source_blocks"]!=32 or
                                original["converged_first_stage"]!=len(good) or
                                original["converged_recovery_fit"]!=len(gg)):
                                raise ValueError("R86-A source-level convergence count mismatch")
                            for outkey,rowkey,subset in [
                                ("mean_secondary_recovered","secondary_recovered",cell),
                                ("mean_audited_failed_validation","third_stage_audited",cell),
                                ("mean_refused_pilot_positions","pilot_refused_grid",cell),
                                ("mean_estimated_gamma","recovery_gamma_fit",gg),
                                ("mean_absolute_gamma_error","recovery_gamma_abs_error",gg),
                                ("mean_estimated_first_stage_delta","delta_estimate",good),
                                ("mean_absolute_first_stage_delta_error","delta_error_absolute",good)]:
                                vals=[z[rowkey] for z in subset if z[rowkey] is not None]
                                want=float(np.mean(vals)) if vals else None
                                close(original[outkey],want,"R86-A "+outkey,tol=1e-7)
    return {"actual_original_complete_XY_replayed":256,
            "original_first_stage_masks_replayed":512,
            "secondary_and_third_stage_audit_strategy_rows_replayed":4608,
            "independent_generating_blocks_per_cell":32,
            "exact_source_checkout":sha,
            "external_audit_in_real_data":False,
            "general_MNAR_or_confidence_bands_validated":False,
            "release_authorized":False}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original",type=Path,required=True)
    p.add_argument("--expected-checkout",default=CHECKOUT)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=audit(a.original,a.expected_checkout)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))


if __name__=="__main__":main()
