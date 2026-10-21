"""R88-A independent immutable-original return gamma sensitivity audit.

Do not import the R88 or R87 generators/estimators, the package, or the
original summary calculator. Independently regenerate all random streams,
source/mask/audit digests and numerical selection scores from fixed equations.
Research evidence only: no MNAR identification, uncertainty bands or release.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from scipy.optimize import root

STUDY = "W3_R88_CONDITIONAL_RETURN_SENSITIVITY_NEW_SOURCE"
ORIGINAL_CHECKOUT = "194d00a14ac35b85cf25864ed5e099d0c7ffb02c"
T = np.linspace(0., 1., 31)
CONFIGS = ("curve_standard", "participant_standard")
SUPPORT = ("two_anchors",)
VARIANCES = ("predictor_heteroskedastic",)
MECHANISMS = ("MAR", "MNAR")
ASSUMED_GAMMAS = (0., .675, 1.35, 2.025)
AUDIT_LEVELS = (.25, .5)
TRUTH_GAMMA = 1.35
BLOCKS = 32
EXPECTED_ROWS = 1024
SHOCK_P = .08
SHOCK_A = .16
SOURCES = {"source": 202610218880, "mask": 202610218881,
           "secondary": 202610218882, "assignment": 202610218883,
           "return": 202610218884}

def stream_seed(block, config, domain):
    if type(block) is not int or block not in range(BLOCKS):
        raise ValueError("R88-A invalid source block")
    if config not in CONFIGS or domain not in SOURCES:
        raise ValueError("R88-A invalid source stream identity")
    return SOURCES[domain] + 1000003 * block + 10007 * CONFIGS.index(config)

def source_seed(block, config):
    return stream_seed(block, config, "source")

def observation_seed(block, config, support, variance):
    if support not in SUPPORT or variance not in VARIANCES:
        raise ValueError("R88-A invalid support or variance")
    return stream_seed(block, config, "mask")

def close(a,b,what,tol=1e-9):
    if a is None or b is None:
        if a is not b:raise ValueError("R88-A original mismatch "+what)
        return
    x=np.asarray(a,float);y=np.asarray(b,float)
    if x.shape!=y.shape or not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)):
        raise ValueError("R87-A invalid finite field "+what)
    if not np.allclose(x,y,atol=tol,rtol=1e-8):
        raise ValueError("R88-A original numerical mismatch "+what)


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




def logit_probability(X, Y, pilot, gamma):
    """Independently evaluate a hypothetical return probability, not observed gamma."""
    if gamma not in ASSUMED_GAMMAS:
        raise ValueError("R88-A unfrozen gamma assumption")
    trial_idx = np.arange(Y.shape[1])[None, :, None, None]
    baseline = (.8 - .1 * np.clip(np.abs(X[:,1,None,None,None]) / 4., 0., 1.)
                - .1 * T[None,None,:,None] - .04 * trial_idx)
    baseline = np.broadcast_to(np.clip(baseline,.15,.95),Y.shape)
    slope = pilot[None,None,:,:,1]
    predicted = pilot[None,None,:,:,0] + X[:,1,None,None,None] * slope
    h = np.tanh((Y - predicted) / .08)
    logits = np.log(baseline / (1. - baseline)) + gamma * h
    return 1. / (1. + np.exp(-np.clip(logits,-35.,35.)))


def independent_fit(X,Y,missing,initial,returned,pilot,allowed,q,gamma):
    proposed = q * logit_probability(X,Y,pilot,gamma)
    a,g,ok,n,score,info,bound = independently_fit_secondary_with_return(
        X,Y,initial,returned,pilot,allowed,proposed)
    if not ok:
        return dict(recovery_alpha=None,recovery_gamma=None,
                    recovery_converged=False,recovery_n=n,
                    first_stage_delta=None,delta_converged=False,delta_n=0,
                    delta_score=None,delta_boundary_refusal=False,
                    recovery_boundary_refusal=bound)
    predicted = (pilot[None,None,:,:,0] +
                 X[:,1,None,None,None] * pilot[None,None,:,:,1])
    residual = np.tanh((Y-predicted)/.08)
    recovery = 1. / (1. + np.exp(-np.clip(a+g*residual,-35.,35.)))
    union = recovery+(1.-recovery)*proposed
    d,dc,ds,di,dn,db = independently_fit_delta(
        X,Y,missing,initial|returned,pilot,allowed,union)
    return dict(recovery_alpha=a,recovery_gamma=g,
                recovery_converged=True,recovery_n=n,
                first_stage_delta=d,delta_converged=dc,delta_n=dn,
                delta_score=ds,delta_boundary_refusal=db,
                recovery_boundary_refusal=bound)


def verify_row(row,X,Y,missing,initial,assigned,returned,pilot,allowed,q,gamma,truth,
               block,config):
    label=f"{block}/{config}/{row['mechanism']}/{q}/{gamma}"
    expected_seeds={f"{domain}_seed":stream_seed(block,config,domain)
                    for domain in SOURCES}
    # The original names source/mask/secondary/assignment/return all match.
    if (row["study"] != STUDY or
        any(row[k] != v for k,v in expected_seeds.items()) or
        row["block"] != block or row["config"] != config or
        row["audit_fraction"] != q or row["assumed_return_gamma"] != gamma or
        row["generating_return_gamma_simulator_only"] != TRUTH_GAMMA or
        row["assumed_gamma_equals_simulator_truth"] is not (gamma == TRUTH_GAMMA) or
        row["complete_X_sha256"] != digest(X) or
        row["complete_Y_sha256"] != digest(Y) or
        row["original_missing_sha256"] != mask_digest(missing) or
        row["original_pilot_sha256"] != digest(pilot) or
        row["initial_return_sha256"] != mask_digest(initial) or
        row["assigned_sha256"] != mask_digest(assigned) or
        row["returned_sha256"] != mask_digest(returned) or
        row["original_missing_n"] != int(np.sum(missing)) or
        row["initial_return_n"] != int(np.sum(initial)) or
        row["audit_assigned_n"] != int(np.sum(assigned)) or
        row["audit_returned_n"] != int(np.sum(returned)) or
        row["audit_nonreturn_n"] != int(np.sum(assigned&~returned)) or
        row["unmeasured_missing_n"] != int(np.sum(missing&~initial&~returned)) or
        row["true_first_stage_delta_simulator_only"] != truth or
        row["assumption_is_not_identified_from_audit_returns"] is not True or
        row["known_return_baseline_simulation_assumption"] is not True or
        row["unreturned_Y_used_by_fitted_score"] is not False or
        row["nominal_confidence_band_claim"] is not False or
        row["release_authorized"] is not False):
        raise ValueError("R88-A original source provenance or release mismatch "+label)
    fitted=independent_fit(X,Y,missing,initial,returned,pilot,allowed,q,gamma)
    for field in ("recovery_converged","recovery_n","delta_converged","delta_n",
                  "delta_boundary_refusal","recovery_boundary_refusal"):
        if row[field] != fitted[field]:
            raise ValueError("R88-A independent refusal/count disagreement "+
                             label+" "+field)
    for field in ("recovery_alpha","recovery_gamma","first_stage_delta","delta_score"):
        close(row[field],fitted[field],label+"/"+field,tol=2e-6)
    if fitted["first_stage_delta"] is None:
        if row["delta_signed_error"] is not None:
            raise ValueError("R88-A refused-score error not null "+label)
    else:
        close(row["delta_signed_error"],
              fitted["first_stage_delta"]-truth,label+"/signed_error",tol=2e-6)
    return fitted


def audit_original(original):
    required=("cases.json","summary.json","source-commit.txt","SHA256SUMS")
    if any(not (original/x).is_file() for x in required):
        raise ValueError("R88-A original immutable archive missing mandatory member")
    sums=(original/"SHA256SUMS").read_text().splitlines()
    seen={}
    for line in sums:
        digest_,separator,name=line.partition("  ")
        if separator!="  " or name in seen or name not in required[:3]:
            raise ValueError("R88-A invalid SHA256 manifest")
        if sha256((original/name).read_bytes()).hexdigest()!=digest_:
            raise ValueError("R88-A original SHA256 corrupted: "+name)
        seen[name]=digest_
    if set(seen)!=set(required[:3]):
        raise ValueError("R88-A original SHA256 manifest incomplete")
    checkout=(original/"source-commit.txt").read_text().strip()
    if checkout!=ORIGINAL_CHECKOUT:
        raise ValueError("R88-A original experiment checkout mismatch")
    rows=json.loads((original/"cases.json").read_text())
    archive=json.loads((original/"summary.json").read_text())
    if len(rows)!=EXPECTED_ROWS:
        raise ValueError("R88-A incomplete original 1024 records")
    keys=[(r["block"],r["config"],r["mechanism"],
           r["audit_fraction"],r["assumed_return_gamma"]) for r in rows]
    expected={(b,c,m,q,g) for b in range(BLOCKS) for c in CONFIGS
              for m in MECHANISMS for q in AUDIT_LEVELS for g in ASSUMED_GAMMAS}
    if set(keys)!=expected or len(set(keys))!=EXPECTED_ROWS:
        raise ValueError("R88-A duplicated or missing original source identities")
    lookup=dict(zip(keys,rows))
    results={}
    for b in range(BLOCKS):
        for c in CONFIGS:
            X,Y,_=replay_XY(b,c,SUPPORT[0],VARIANCES[0])
            masks_=masks(X,Y,b,c,SUPPORT[0],VARIANCES[0])
            secondary=np.random.default_rng(stream_seed(b,c,"secondary")).random(Y.shape)
            assignment=np.random.default_rng(stream_seed(b,c,"assignment")).random(Y.shape)
            completion=np.random.default_rng(stream_seed(b,c,"return")).random(Y.shape)
            for m in MECHANISMS:
                missing=masks_[m]
                pilot,allowed,counts=visible_pilot_independently(X,Y,missing)
                if not bool(np.all(allowed)):
                    raise ValueError("R88-A independent source pilot refusal")
                initial=missing&(secondary<true_secondary_recovery(X,Y))
                return_truth=logit_probability(X,Y,pilot,TRUTH_GAMMA)
                for q in AUDIT_LEVELS:
                    assigned=missing&~initial&(assignment<q)
                    returned=assigned&(completion<return_truth)
                    if np.any(returned&~assigned) or np.any(returned&initial):
                        raise ValueError("R88-A invalid audit subset")
                    for g in ASSUMED_GAMMAS:
                        row=lookup[(b,c,m,q,g)]
                        fitted=verify_row(row,X,Y,missing,initial,assigned,
                                          returned,pilot,allowed,q,g,
                                          0. if m=="MAR" else 1.1,b,c)
                        results[(b,c,m,q,g)]=fitted
    if len(results)!=EXPECTED_ROWS:
        raise ValueError("R88-A numerical reconstruction incomplete")
    if (archive["study"]!=STUDY or archive["complete_independent_sources"]!=64
        or archive["primitive_blocks_per_fixed_cell"]!=BLOCKS
        or archive["paired_MAR_MNAR_masks"]!=128
        or archive["repeated_method_records_not_independent"]!=EXPECTED_ROWS
        or archive["assumed_return_gamma_values"]!=list(ASSUMED_GAMMAS)
        or archive["generating_return_gamma_simulator_only"]!=TRUTH_GAMMA
        or archive["release_authorized"] is not False
        or archive["no_valid_MNAR_identification_or_confidence_band_claim"] is not True):
        raise ValueError("R88-A original summary provenance/release mismatch")
    for c in CONFIGS:
        for m in MECHANISMS:
            for q in AUDIT_LEVELS:
                for g in ASSUMED_GAMMAS:
                    subset=[results[(b,c,m,q,g)] for b in range(BLOCKS)]
                    done=[r for r in subset if r["delta_converged"]
                          and r["first_stage_delta"] is not None]
                    reported=archive["results"][c][m][str(q)][str(g)]
                    if (reported["first_stage_completed"]!=len(done) or
                        reported["first_stage_refused"]!=BLOCKS-len(done) or
                        reported["independent_primitive_source_blocks"]!=BLOCKS or
                        reported["simulator_true_gamma"] is not (g==TRUTH_GAMMA)):
                        raise ValueError("R88-A summary independent unit mismatch")
                    mean=float(np.mean([r["first_stage_delta"] for r in done])) if done else None
                    close(reported["mean_delta"],mean,
                          f"summary/{c}/{m}/{q}/{g}",tol=2e-6)
                    if mean is not None:
                        truth=0. if m=="MAR" else 1.1
                        close(reported["mean_signed_error"],mean-truth,
                              f"summary-error/{c}/{m}/{q}/{g}",tol=2e-6)
    return {"study":"W3_R88_A_INDEPENDENT_ORIGINAL_SOURCE_AUDIT",
            "original_sha256":seen,"original_source_checkout":checkout,
            "replayed_independent_source_conditions":64,
            "replayed_selection_records":len(results),
            "independent_numerical_comparison_passed":True,
            "assumed_gamma_is_unidentified":True,
            "release_authorized":False}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    result=audit_original(args.original)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps(result,sort_keys=True))


if __name__=="__main__":
    main()
