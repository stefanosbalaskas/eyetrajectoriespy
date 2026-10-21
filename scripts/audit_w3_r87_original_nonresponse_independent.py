"""R87-A independent original-source read-only observation-mask replay.

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

STUDY="W3_R87_AUDIT_COMPLETION_NONRESPONSE_FALSIFICATION"
SOURCE_SEED=202610218780
OBS_SEED=202610218781
CHECKOUT="2716a79ceec03ef8cf1cd0a8be3546e638c98884"
T=np.linspace(0.,1.,31)
CONFIGS=("curve_standard","participant_standard")
SUPPORT=("two_anchors",)
VARIANCES=("predictor_heteroskedastic",)
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
        if a is not b:raise ValueError("R87-A original mismatch "+what)
        return
    x=np.asarray(a,float);y=np.asarray(b,float)
    if x.shape!=y.shape or not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)):
        raise ValueError("R87-A invalid finite field "+what)
    if not np.allclose(x,y,atol=tol,rtol=1e-8):
        raise ValueError("R87-A original numerical mismatch "+what)


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

RECOVERY_SEED=202610218782
AUDIT_SEED=202610218783
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



RECOVERY_SEED=202610218782
AUDIT_SEED=202610218783
AUDIT_RETURN_SEED=202610218784
RETURN_LAWS=("complete","recorded","outcome")
STRATEGIES=("assignment_only","recorded_propensity","outcome_oracle")
AUDIT_LEVELS=(.25,.5)
RECORDS=2304

def audit_completion_probability(X,Y,law):
    """Independently compute observational versus hidden-Y audit return laws."""
    if law not in RETURN_LAWS:
        raise ValueError("R87-A unsupported audit return law")
    if law=="complete":
        return np.ones_like(Y)
    trials=Y.shape[1]
    xmag=np.abs(X[:,1,None,None,None])
    idx=np.arange(trials)[None,:,None,None]
    logit_recorded=(.8-.1*np.clip(xmag/4,0,1)
                    -.1*T[None,None,:,None]-.04*idx)
    p0=np.broadcast_to(np.clip(logit_recorded,.15,.95),Y.shape)
    if law=="recorded":return p0.copy()
    b0,b1=truth()
    mu=b0[None]+X[:,1,None,None]*b1[None]
    h=np.tanh((Y-mu[:,None])/.08)
    logit=np.log(p0/(1.-p0))+1.35*h
    return 1./(1.+np.exp(-np.clip(logit,-35.,35.)))

def independently_fit_secondary_with_return(X,Y,initial,audited,pilot,allowed,prob):
    """Independent SciPy root, not the source's clipped Newton solver."""
    uid,tr,t,d=np.where((initial|audited)&allowed[None,None,:,:])
    if len(uid)<20 or not (audited&allowed[None,None,:,:]).any():
        return None,None,False,len(uid),None,None,False
    response=Y[uid,tr,t,d]
    m=pilot[t,d,0]+pilot[t,d,1]*X[uid,1]
    h=np.tanh((response-m)/.08)
    label=initial[uid,tr,t,d].astype(float)
    pi=prob[uid,tr,t,d]
    if (not np.isfinite(pi).all() or (pi<=0).any() or (pi>1).any()):
        return None,None,False,len(uid),None,None,True
    weights=np.where(label>0,1.,1./pi)
    A=np.stack((np.ones(len(h)),h),axis=1)
    def f(theta):
        p=1/(1+np.exp(-np.clip(A@theta,-45.,45.)))
        return A.T@(weights*(label-p))
    def jac(theta):
        p=1/(1+np.exp(-np.clip(A@theta,-45.,45.)))
        return -(A.T@((weights*p*(1-p))[:,None]*A))
    out=root(f,np.array([np.log(.25/.75),0.]),jac=jac,method="hybr",
             options={"xtol":1e-11,"maxfev":600})
    theta=np.asarray(out.x,float)
    score=f(theta)
    eigen=float(np.linalg.eigvalsh(-jac(theta))[0])
    bound=bool(abs(theta[0])>=7.999999 or abs(theta[1])>=3.999999)
    accepted=(np.isfinite(theta).all() and
              abs(theta[0])<8. and abs(theta[1])<4. and
              eigen>1e-10 and np.isfinite(score).all() and
              np.max(np.abs(score))<1e-6)
    if not accepted:
        return None,None,False,len(uid),float(np.max(np.abs(score))),eigen,bound
    return float(theta[0]),float(theta[1]),True,len(uid),float(np.max(np.abs(score))),eigen,bound

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



def verify_record(row,X,Y,missing,initial,assigned,returned,
                  pilot,allowed,true_secondary,return_p,return_seed,seeds):
    block,c,s,v,m,q,law,strategy=(row[k] for k in (
        "block","config","support","variance","mechanism",
        "audit_fraction","audit_return_law","strategy"))
    label="/".join(map(str,(block,c,m,q,law,strategy)))
    measured=initial|returned
    if (row["study"]!=STUDY or row["source_seed"]!=source_seed(block,c)
        or row["mask_seed"]!=observation_seed(block,c,s,v)
        or row["secondary_seed"]!=seeds[0] or row["audit_seed"]!=seeds[1]
        or row["return_seed"]!=return_seed
        or row["original_X_digest"]!=digest(X)
        or row["original_Y_digest"]!=digest(Y)
        or row["original_missing_digest"]!=mask_digest(missing)
        or row["original_pilot_digest"]!=digest(np.nan_to_num(pilot,nan=0.))
        or row["secondary_success_digest"]!=mask_digest(initial)
        or row["audit_assigned_digest"]!=mask_digest(assigned)
        or row["audit_returned_digest"]!=mask_digest(returned)
        or row["union_measured_digest"]!=mask_digest(measured)
        or row["return_probability_digest"]!=digest(return_p)
        or row["true_secondary_gamma_source_only"]!=1.
        or row["true_first_stage_delta_source_only"]!=(0. if m=="MAR" else 1.1)
        or row["audit_assigned_independently"] is not True
        or row["audit_completion_independent_only_for_complete_law"] is not (law=="complete")
        or row["unreturned_outcomes_not_used_in_fitted_scores"] is not True
        or row["oracle_propensity_is_non_field_identifiable"] is not (strategy=="outcome_oracle")
        or row["original_missing_trajectories_rejected"] is not True
        or row["confidence_interval_or_band_validated"] is not False
        or row["release_authorized"] is not False):
        raise ValueError("R87-A original source/mask/audit provenance mismatch "+label)
    if (row["original_gaze_missing"]!=int(missing.sum())
        or row["secondary_returned"]!=int(initial.sum())
        or row["audit_assigned"]!=int(assigned.sum())
        or row["audit_returned"]!=int(returned.sum())
        or row["audit_failed_return"]!=int(np.sum(assigned&~returned))
        or row["valid_original_pilot_grid"]!=int(allowed.sum())):
        raise ValueError("R87-A original audit response denominator mismatch "+label)
    if strategy=="assignment_only":
        candidate_return=np.ones_like(Y)
    elif strategy=="recorded_propensity":
        candidate_return=audit_completion_probability(X,Y,"recorded")
    else:
        candidate_return=return_p
    assumed=q*candidate_return
    alpha,gamma,fit,n,sc,info,bound=independently_fit_secondary_with_return(
        X,Y,initial,returned,pilot,allowed,assumed)
    if (row["recovery_fit_converged"] is not fit
        or row["n_recovery_likelihood"]!=n
        or row["recovery_fit_boundary"] is not bound):
        raise ValueError("R87-A observed-gaze-only secondary fit/refusal mismatch "+label)
    if fit:
        close(row["recovery_alpha_fit"],alpha,label+"/alpha",tol=2e-5)
        close(row["recovery_gamma_fit"],gamma,label+"/gamma",tol=2e-5)
        residual=np.tanh(
            (Y-(pilot[None,None,:,:,0]
                +X[:,1,None,None,None]*pilot[None,None,:,:,1]))/.08)
        predicted=1/(1+np.exp(-np.clip(alpha+gamma*residual,-45,45)))
        union=predicted+(1-predicted)*assumed
        delta,ok,score,info2,nmeasured,dbound=independently_fit_delta(
            X,Y,missing,measured,pilot,allowed,union)
    else:
        if row["recovery_alpha_fit"] is not None or row["recovery_gamma_fit"] is not None:
            raise ValueError("R87-A source fabricated secondary recovery coefficient "+label)
        delta,ok,score,info2,nmeasured,dbound=(None,False,None,None,0,False)
    if (row["first_stage_delta_converged"] is not ok
        or row["first_stage_n"]!=nmeasured
        or row["first_stage_boundary_refusal"] is not dbound):
        raise ValueError("R87-A source original first-stage refusal/count mismatch "+label)
    if ok:
        close(row["first_stage_delta_fit"],delta,label+"/delta",tol=5e-5)
        close(row["first_stage_delta_signed_error"],
              delta-(0. if m=="MAR" else 1.1),label+"/delta signed error",tol=5e-5)
        close(row["first_stage_delta_abs_error"],
              abs(delta-(0. if m=="MAR" else 1.1)),label+"/delta absolute error",tol=5e-5)
    elif row["first_stage_delta_fit"] is not None:
        raise ValueError("R87-A refused original source fabricated delta "+label)
    return row

def audit(path,expected_checkout=CHECKOUT):
    path=Path(path)
    names=("cases.json","summary.json","source-commit.txt")
    expected="".join(sha256((path/name).read_bytes()).hexdigest()+"  "+name+"\n"
                     for name in names)
    if (path/"SHA256SUMS").read_text()!=expected:
        raise ValueError("R87-A immutable original SHA256 mismatch")
    checkout=(path/"source-commit.txt").read_text().strip()
    if checkout!=expected_checkout or len(checkout)!=40:
        raise ValueError("R87-A source checkout not the frozen original")
    rows=json.loads((path/"cases.json").read_text())
    original=json.loads((path/"summary.json").read_text())
    keys={(b,c,s,v,m,q,law,k) for b in range(BLOCKS) for c in CONFIGS
          for s in SUPPORT for v in VARIANCES for m in ("MAR","MNAR")
          for q in AUDIT_LEVELS for law in RETURN_LAWS for k in STRATEGIES}
    ids=[(z["block"],z["config"],z["support"],z["variance"],
          z["mechanism"],z["audit_fraction"],z["audit_return_law"],
          z["strategy"]) for z in rows]
    if (len(ids)!=RECORDS or len(set(ids))!=RECORDS or set(ids)!=keys):
        raise ValueError("R87-A original planned 2304-row source identities missing")
    frozen={
        "study":STUDY,"new_source_seed":SOURCE_SEED,
        "original_mask_seed":OBS_SEED,"secondary_seed":RECOVERY_SEED,
        "audit_assignment_seed":AUDIT_SEED,
        "audit_completion_seed":AUDIT_RETURN_SEED,
        "primitive_blocks_per_cell":BLOCKS,
        "complete_synthetic_source_conditions":64,
        "MAR_MNAR_source_masks":128,
        "third_stage_strategy_records":RECORDS,
        "audit_assignment_levels":list(AUDIT_LEVELS),
        "audit_completion_laws":list(RETURN_LAWS),
        "selection_model_assumptions":list(STRATEGIES),
        "outcome_oracle_not_a_field_method":True,
        "independent_audit_assignment_not_sufficient_if_return_is_selective":True,
        "no_MNAR_point_identification_or_90pct_band_claim":True,
        "release_authorized":False,
    }
    for k,v in frozen.items():
        if original.get(k)!=v:
            raise ValueError("R87-A original aggregate scientific/release contract changed "+k)
    lookup=dict(zip(ids,rows))
    checked=[]
    for b in range(BLOCKS):
        for c in CONFIGS:
            for s in SUPPORT:
                for v in VARIANCES:
                    X,Y,_=replay_XY(b,c,s,v)
                    original_masks=masks(X,Y,b,c,s,v)
                    U,V,seedU,seedV=two_uniforms(b,c,s,v,Y.shape)
                    offset=(1000003*b+10007*CONFIGS.index(c)
                            +739*SUPPORT.index(s)+97*VARIANCES.index(v))
                    W=np.random.default_rng(AUDIT_RETURN_SEED+offset).random(Y.shape)
                    true_p=true_secondary_recovery(X,Y)
                    for m in ("MAR","MNAR"):
                        missing=original_masks[m]
                        primary=missing&(U<true_p)
                        pilot,allowed,_=visible_pilot_independently(X,Y,missing)
                        for q in AUDIT_LEVELS:
                            assigned=missing&(~primary)&(V<q)
                            for law in RETURN_LAWS:
                                returned_p=audit_completion_probability(X,Y,law)
                                returned=assigned&(W<returned_p)
                                for k in STRATEGIES:
                                    z=lookup[(b,c,s,v,m,q,law,k)]
                                    checked.append(verify_record(
                                        z,X,Y,missing,primary,assigned,returned,
                                        pilot,allowed,true_p,returned_p,
                                        AUDIT_RETURN_SEED+offset,(seedU,seedV)))
    results={}
    for c in CONFIGS:
        results[c]={}
        for m in ("MAR","MNAR"):
            results[c][m]={}
            for q in AUDIT_LEVELS:
                results[c][m][str(q)]={}
                for law in RETURN_LAWS:
                    results[c][m][str(q)][law]={}
                    for k in STRATEGIES:
                        cell=[z for z in checked if z["config"]==c and z["mechanism"]==m
                              and z["audit_fraction"]==q and
                              z["audit_return_law"]==law and z["strategy"]==k]
                        if len(cell)!=32 or len({z["block"] for z in cell})!=32:
                            raise ValueError("R87-A original independent-block denominator mismatch")
                        target=original["results"][c][m][str(q)][law][k]
                        gamma=[z for z in cell if z["recovery_fit_converged"] and z["recovery_gamma_fit"] is not None]
                        delta=[z for z in cell if z["first_stage_delta_converged"] and z["first_stage_delta_fit"] is not None]
                        if (target["independent_original_source_blocks"]!=32 or
                            target["complete_secondary_gamma_fits"]!=len(gamma) or
                            target["complete_first_stage_delta_fits"]!=len(delta) or
                            target["source_first_stage_fit_refusals"]!=32-len(delta)):
                            raise ValueError("R87-A original numerical fit count mismatch")
                        means=[("mean_third_stage_audit_assigned","audit_assigned",cell),
                               ("mean_third_stage_audit_returned","audit_returned",cell),
                               ("mean_audit_failed_returns","audit_failed_return",cell),
                               ("mean_fitted_gamma","recovery_gamma_fit",gamma),
                               ("mean_fitted_first_stage_delta","first_stage_delta_fit",delta),
                               ("mean_first_stage_abs_error","first_stage_delta_abs_error",delta)]
                        for summary_field,row_field,subset in means:
                            val=[z[row_field] for z in subset if z[row_field] is not None]
                            want=float(np.mean(val)) if val else None
                            close(target[summary_field],want,
                                  c+m+str(q)+law+k+summary_field,tol=1e-8)
                        results[c][m][str(q)][law][k]={
                            "independent_source_blocks":32,
                            "accepted_secondary":len(gamma),
                            "accepted_first_stage":len(delta),
                            "original_mean_first_stage_delta":target["mean_fitted_first_stage_delta"]}
    return {
        "independently_reconstructed_original_R87":True,
        "original_source_checkout":checkout,
        "verified_sha256_members":len(names),
        "new_independent_source_blocks_per_fixed_cell":32,
        "original_complete_sources":64,
        "original_MAR_MNAR_masks":128,
        "replayed_selection_strategy_rows":len(checked),
        "full_source_XY_and_realized_audit_return_replayed":True,
        "release_authorized":False,
        "not_MNAR_identification_or_confidence_band_coverage":True,
        "results":results,
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--expected-checkout",default=CHECKOUT)
    args=p.parse_args()
    report=audit(args.original,expected_checkout=args.expected_checkout)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print(json.dumps({
        "independent_source_audit_passed":True,
        "replayed_original_rows":report["replayed_selection_strategy_rows"]
    },sort_keys=True))

if __name__=="__main__":main()
