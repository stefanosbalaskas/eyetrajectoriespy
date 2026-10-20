"""R79-A independently implemented actual-source functional HC3 regularization audit.

Does NOT import original R79 generator, W3 OLS/bootstrap, HC3 original
implementation or R79 aggregate. Replays Gaussian X/Y and all raw reference
maxima from the immutable original archive. Research only; not calibration.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path

import numpy as np

STUDY="W3_R79_NEW_NONSEPARABLE_CROSS_COORDINATE_GAUSSIAN"
AUDIT="W3_R79_A_INDEPENDENT_NEW_SOURCE_SE_CORRELATION_NUMERICAL_AUDIT"
CHECKOUT="15bcbe55d42579c9788cd94b9516850b6eabc1b2"
SOURCE_SEED=202610207990
GAUSSIAN_SEED=202610207991
WILD_SEED=202610207992
REG025_SEED=202610207993
REG050_SEED=202610207994
BLOCKS=32
B=999
CONF=.90
CONFIGS=("curve_standard","participant_standard")
SUPPORT=("two_anchors","sixteen_anchors")
ANCHORS={"two_anchors":2,"sixteen_anchors":16}
VARIANCES=("constant","predictor_heteroskedastic")
CELLS=("true_SE/true_corr","HC3_SE/HC3_corr","REG025_SE/REG025_corr","REG050_SE/REG050_corr")
MAX_ARRAYS=("wild_HC1","true_corr","HC3_corr","REG025_corr","REG050_corr")
REGULARIZATION=(("REG025",.25),("REG050",.50))
N_CASES=256
T=np.linspace(0.,1.,31)
AR_RHO=.72
LATENT_CROSS_RHO=.45
TOL=3e-8


def _same(left,right,label,tol=TOL):
    try:
        a=np.asarray(left,float);b=np.asarray(right,float)
        if a.shape!=b.shape or not np.isfinite(a).all() or not np.isfinite(b).all():
            raise ValueError("shape or finiteness")
        if not np.allclose(a,b,atol=tol,rtol=2e-8):
            raise ValueError("numerical difference")
    except (ValueError,TypeError) as exc:
        raise ValueError("R79-A original source independently reconstructed mismatch "+label) from exc


def _wilson(k,n,z=1.959963984540054):
    if n==0:return None
    p=k/n;den=1+z*z/n
    center=(p+z*z/(2*n))/den
    radius=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [max(0.,center-radius),min(1.,center+radius)]


def _ident(block,config,support,variance):
    if (type(block)is not int or not 0<=block<BLOCKS or config not in CONFIGS
        or support not in SUPPORT or variance not in VARIANCES):
        raise ValueError("R79-A original primitive source identity malformed")


def _seed(block,config,support,variance,domain):
    _ident(block,config,support,variance)
    ci=CONFIGS.index(config)
    if domain=="source":
        return SOURCE_SEED+100003*block+10007*ci
    base={"gaussian":GAUSSIAN_SEED,"wild":WILD_SEED,"reg025":REG025_SEED,"reg050":REG050_SEED}.get(domain)
    if base is None:
        raise ValueError("R79-A original RNG domain unknown")
    return base+1000003*block+10007*ci+739*SUPPORT.index(support)+37*VARIANCES.index(variance)


def _config(config):
    if config=="curve_standard":return 72,1,"curve"
    if config=="participant_standard":return 36,3,"participant"
    raise ValueError("R79-A unexpected independent-unit configuration")


def _rho_time():
    return .15+.65*T


def _mix_trial(x):
    """Separately reconstructed nonseparable time-dependent spatial mixing."""
    rho=_rho_time()
    y=np.empty_like(x)
    y[...,0]=x[...,0]
    y[...,1]=rho*x[...,0]+np.sqrt(1-rho*rho)*x[...,1]
    return y


def _mix_latent(x):
    y=np.empty_like(x)
    y[...,0]=x[...,0]
    y[...,1]=LATENT_CROSS_RHO*x[...,0]+np.sqrt(1-LATENT_CROSS_RHO**2)*x[...,1]
    return y


def _time_scale():
    return .04*(.70+.60*T)


def _trial_ar_factor():
    idx=np.arange(31)
    return np.linalg.cholesky(AR_RHO**np.abs(idx[:,None]-idx[None,:]))


def _true_variance(design):
    sd=_time_scale()
    if design=="curve":
        return np.repeat((sd**2)[:,None],2,axis=1)
    if design=="participant":
        return np.repeat((.065**2*(1+.35*T)**2+sd**2/3)[:,None],2,axis=1)
    raise ValueError("R79-A unexpected source Gaussian variance design")


def reconstruct_source(block,config,support,variance):
    n,trials,design=_config(config)
    rng=np.random.default_rng(_seed(block,config,support,variance,"source"))
    x=rng.uniform(-.95,.95,size=n)
    half=ANCHORS[support]//2
    x[:half]=-4.
    x[-half:]=4.
    scale=np.ones(n) if variance=="constant" else 1+.75*np.abs(x)
    truth_intercept=np.stack((.35+.08*T,.25-.04*T),axis=1)
    truth_slope=np.stack((.40+.11*np.cos(np.pi*T),-.28+.13*np.sin(np.pi*T)),axis=1)
    latent=np.zeros((n,31,2))
    if design=="participant":
        latent=_mix_latent(rng.normal(0,1,size=(n,1,2)))*(.065*(1+.35*T[None,:,None]))
    white=rng.normal(0,1,size=(n,trials,31,2))
    trial_noise=np.einsum("tu,njud->njtd",_trial_ar_factor(),white,optimize=True)
    trial_noise=_mix_trial(trial_noise)*_time_scale()[None,None,:,None]
    Y=(truth_intercept[None]+x[:,None,None]*truth_slope[None]
       +scale[:,None,None]*(latent+trial_noise.mean(axis=1)))
    return np.column_stack((np.ones(n),x)),Y,truth_slope,scale,design


def _correlation_maxima(design,factor,se,source_rng):
    # Independent replay of exact changed source-known correlated Gaussian law.
    white=source_rng.standard_normal((B,31,2))
    correlated=np.einsum("tu,bud->btd",_trial_ar_factor(),white,optimize=True)
    correlated=_mix_trial(correlated)*_time_scale()[None,:,None]
    if design=="curve":
        z=correlated
    elif design=="participant":
        latent=_mix_latent(source_rng.standard_normal((B,1,2)))
        z=.065*(1.+.35*T[None,:,None])*latent+correlated/math.sqrt(3)
    else:
        raise ValueError("R79-A source design not registered")
    true=np.max(np.abs(z/np.sqrt(_true_variance(design))[None]),axis=(1,2))
    # Original HC3 Gaussian reference consumes remaining same stream.
    z_est=source_rng.standard_normal((B,len(factor)))
    corr=(z_est@factor).reshape(B,31,2)/se[None]
    return true,np.max(np.abs(corr),axis=(1,2))


def _regularized_reference(factor,lam,rng):
    """Independent covariance construction, without importing original R79 study."""
    base=np.einsum("ik,il->kl",factor,factor)
    diagonals=np.diag(base).reshape(31,2)
    smoothed=np.empty_like(diagonals)
    for t in range(31):
        smoothed[t]=np.mean(diagonals[max(0,t-3):min(31,t+4)],axis=0)
    cov=(1-lam)*base+lam*np.diag(smoothed.flatten())
    chol=np.linalg.cholesky(cov)
    se=np.sqrt(np.diag(cov))
    z=rng.standard_normal((B,62))
    maximum=np.max(np.abs((z@chol.T)/se[None]),axis=1)
    return se,maximum


def check_case(row):
    block,config,support,variance=(row["block"],row["config"],row["support"],row["variance"])
    label=f"{block}/{config}/{support}/{variance}"
    n,trials,design=_config(config)
    if (row["study"]!=STUDY or row["design"]!=design or
        row["source_seed"]!=_seed(block,config,support,variance,"source") or
        row["gaussian_seed"]!=_seed(block,config,support,variance,"gaussian") or
        row["wild_seed"]!=_seed(block,config,support,variance,"wild") or
        row["reg025_seed"]!=_seed(block,config,support,variance,"reg025") or
        row["reg050_seed"]!=_seed(block,config,support,variance,"reg050") or
        row["native_units"]!=n or row["observed_curves"]!=n*trials or
        row["not_90pct_calibrated"] is not True or
        row["true_reference_is_simulation_known_AR1"] is not True or
        row["true_reference_nonseseparable_spatial_temporal"] is not True or
        row["release_authorized"] is not False or
        row["no_MNAR_missingness"] is not True or
        row["number_of_extreme_anchor_units"]!=ANCHORS[support]):
        raise ValueError("R79-A original frozen source/qualification mismatch "+label)
    if not row["completed"]:
        if not row["refused"] or row["exception"] is None:
            raise ValueError("R79-A source refusal incorrectly discarded "+label)
        if any(row["cell_truth_included"][x] is not None for x in CELLS):
            raise ValueError("R79-A refused source manufactured truth inclusion "+label)
        return {"completed":False}

    if row["refused"] or row["exception"] is not None:
        raise ValueError("R79-A completed source with original exception "+label)
    if (row["OLS_HC1_package_oracle_error"]>2e-10 or
        row["W3_wild_package_critical_error"]>2e-10):
        raise ValueError("R79-A original W3 acceptance numeric gates failed "+label)
    X,Y,truth,scale,design=reconstruct_source(block,config,support,variance)
    for key,value in {
        "observed_X":X,"observed_Y_native_unit_mean":Y,
        "truth_slope":truth,"unit_sd":scale,
    }.items():
        _same(row[key],value,label+"/"+key,tol=5e-13)
    flat=Y.reshape(n,-1)
    beta=np.linalg.lstsq(X,flat,rcond=None)[0]
    inv=np.linalg.inv(X.T@X)
    proj=inv@X.T
    a=proj[1]
    residual=flat-X@beta
    hat=np.einsum("np,pn->n",X,proj)
    if np.min(hat)<=0 or np.max(hat)>=1-1e-9:
        raise ValueError("R79-A estimated leverage boundary invalid "+label)
    _same(row["max_unit_hat"],max(hat),label+"/max_unit_hat")
    hc1=np.sqrt((n/(n-2))*np.sum((a[:,None]*residual)**2,axis=0))
    factor=(a/(1-hat))[:,None]*residual
    hc3=np.sqrt(np.sum(factor**2,axis=0))
    true=np.sqrt(np.sum((a*scale)**2)*_true_variance(design).reshape(-1))
    weights=(a*scale)**2
    weights=weights/np.sum(weights)
    effective_units=float(1./np.sum(weights**2))
    anchor_share=float(np.sum(weights[np.abs(X[:,1])==4.]))
    ratio=hc3/true
    diff=beta[1]-truth.reshape(-1)
    for key,value in {
        "known_SE_grid":true.reshape(31,2),
        "estimated_HC3_SE_grid":hc3.reshape(31,2),
        "source_slope_beta_error":diff.reshape(31,2),
        "HC3_SE_to_true_SE_mean":np.mean(ratio),
        "HC3_SE_to_true_SE_min":np.min(ratio),
        "HC3_SE_to_true_SE_p10":np.quantile(ratio,.10),
        "effective_slope_variance_units":effective_units,
        "anchor_slope_variance_share":anchor_share,
    }.items():
        _same(row[key],value,label+"/"+key)

    multiplier=np.random.default_rng(_seed(block,config,support,variance,"wild")).choice(
        np.array([-1.,1.]),size=(B,n))
    wild=np.max(np.abs(
        ((multiplier*a[None])@residual)/hc1[None]),axis=1)
    true_max,hc3_max=_correlation_maxima(
        design,factor,hc3.reshape(31,2),
        np.random.default_rng(_seed(block,config,support,variance,"gaussian")))
    regularized_se={}
    regularized_ratios={}
    regularized_max={}
    for key,lam in REGULARIZATION:
        domain="reg025" if key=="REG025" else "reg050"
        se,maximum=_regularized_reference(
            factor,lam,np.random.default_rng(_seed(block,config,support,variance,domain)))
        regularized_se[key]=se
        regularized_max[key+"_corr"]=maximum
        rat=se/true
        regularized_ratios[key]={
            "mean":float(np.mean(rat)),
            "p10":float(np.quantile(rat,.10)),
            "minimum":float(np.min(rat)),
        }
        _same(row["regularized_se_grids"][key],se.reshape(31,2),label+"/"+key+"/SE")
        for statistic in ("mean","p10","minimum"):
            _same(row["regularized_ratio_statistics"][key][statistic],
                  regularized_ratios[key][statistic],label+"/"+key+"/"+statistic)
    raw={"wild_HC1":wild,"true_corr":true_max,"HC3_corr":hc3_max,**regularized_max}
    crit={}
    for k,v in raw.items():
        _same(row["raw_reference_maxima"][k],v,label+"/"+k+"/maxima")
        crit[k]=float(np.quantile(v,.90,method="higher"))
        _same(row["reference_criticals"][k],crit[k],label+"/"+k+"/critical")

    ptruth=float(np.max(np.abs(diff/true)))
    phc3=float(np.max(np.abs(diff/hc3)))
    pwild=float(np.max(np.abs(diff/hc1)))
    pivots={
        "true_SE/true_corr":ptruth,
        "HC3_SE/HC3_corr":phc3,
        "REG025_SE/REG025_corr":float(np.max(np.abs(diff/regularized_se["REG025"]))),
        "REG050_SE/REG050_corr":float(np.max(np.abs(diff/regularized_se["REG050"]))),
    }
    covers={name:bool(pivots[name]<=crit[name.split("/")[1]]) for name in CELLS}
    for name in CELLS:
        _same(row["cell_observed_pivots"][name],pivots[name],label+"/"+name+"/pivot")
        if row["cell_truth_included"][name] is not covers[name]:
            raise ValueError("R79-A source truth inclusion falsified "+label+"/"+name)
    _same(row["wild_HC1_truth_pivot"],pwild,label+"/wild pivot")
    if row["wild_HC1_truth_included"] is not bool(pwild<=crit["wild_HC1"]):
        raise ValueError("R79-A wild source truth classification falsified "+label)
    return {
        "completed":True,"cell_truth_included":covers,
        "wild_HC1":bool(pwild<=crit["wild_HC1"]),
        "HC3_SE_to_true_SE_mean":float(np.mean(ratio)),
        "HC3_SE_to_true_SE_min":float(np.min(ratio)),
        "HC3_SE_to_true_SE_p10":float(np.quantile(ratio,.10)),
        "effective_slope_variance_units":effective_units,
        "anchor_slope_variance_share":anchor_share,
        "true_critical":crit["true_corr"],
        "HC3_critical":crit["HC3_corr"],
        "REG025_critical":crit["REG025_corr"],
        "REG050_critical":crit["REG050_corr"],
        "REG025_SE_mean":regularized_ratios["REG025"]["mean"],
        "REG025_SE_p10":regularized_ratios["REG025"]["p10"],
        "REG050_SE_mean":regularized_ratios["REG050"]["mean"],
        "REG050_SE_p10":regularized_ratios["REG050"]["p10"],
    }


def audit(folder:Path,expected_checkout=CHECKOUT):
    names=("cases.json","summary.json","source-commit.txt")
    checks=(folder/"SHA256SUMS").read_text().splitlines()
    expected=[sha256((folder/n).read_bytes()).hexdigest()+"  "+n for n in names]
    if checks!=expected:
        raise ValueError("R79-A immutable original source archive SHA256 integrity mismatch")
    checkout=(folder/"source-commit.txt").read_text().strip()
    if checkout!=expected_checkout or len(checkout)!=40:
        raise ValueError("R79-A original scientific source checkout mismatch")
    rows=json.loads((folder/"cases.json").read_bytes())
    summary=json.loads((folder/"summary.json").read_bytes())
    identities=[(x["block"],x["config"],x["support"],x["variance"]) for x in rows]
    expected_ids={(b,c,s,v) for b in range(BLOCKS) for c in CONFIGS
                  for s in SUPPORT for v in VARIANCES}
    if len(identities)!=N_CASES or set(identities)!=expected_ids or len(set(identities))!=N_CASES:
        raise ValueError("R79-A missing/duplicated original primitive source identities")
    frozen={
        "study":STUDY,"source_seed":SOURCE_SEED,
        "gaussian_seed":GAUSSIAN_SEED,"wild_seed":WILD_SEED,
        "reg025_seed":REG025_SEED,"reg050_seed":REG050_SEED,
        "new_independent_primitive_blocks":BLOCKS,"source_cases":N_CASES,
        "configs":list(CONFIGS),"supports":list(SUPPORT),
        "anchor_counts":list(ANCHORS.values()),
        "regularization_strengths":[.25,.50],
        "fixed_time_smoothing_window":7,
        "true_AR1_rho":AR_RHO,
        "true_cross_coordinate_trial_rho_endpoints":[float(_rho_time()[0]),float(_rho_time()[-1])],
        "true_latent_cross_coordinate_rho":LATENT_CROSS_RHO,
        "true_time_SD_endpoints":[float(_time_scale()[0]),float(_time_scale()[-1])],
        "variances":list(VARIANCES),"factorial_cells":list(CELLS),
        "original_wild_999_multiplier_positions":N_CASES*B,
        "known_Gaussian_maxima":N_CASES*B,
        "HC3_Gaussian_maxima":N_CASES*B,
        "REG025_Gaussian_maxima":N_CASES*B,
        "REG050_Gaussian_maxima":N_CASES*B,
        "reference_draws_not_independent_source_replications":True,
        "true_Gaussian_covariance_used_for_diagnostic_cells_only":True,
        "no_90pct_simultaneous_band_calibration":True,
        "no_MNAR_or_dropout_study":True,
        "release_authorized":False,
    }
    for k,v in frozen.items():
        if summary.get(k)!=v:
            raise ValueError("R79-A source summary calibration/identity forged "+k)
    actual={(x["block"],x["config"],x["support"],x["variance"]):check_case(x) for x in rows}
    results={}
    contrasts={}
    for config in CONFIGS:
        results[config]={}
        for support in SUPPORT:
            results[config][support]={}
            for variance in VARIANCES:
                cases=[actual[b,config,support,variance] for b in range(BLOCKS)]
                ok=[x for x in cases if x["completed"]]
                n=len(ok);missing=BLOCKS-n
                expected_source=summary["results"][config][support][variance]
                for key,value in {"attempted":BLOCKS,"complete":n,"refused":missing}.items():
                    if expected_source[key]!=value:
                        raise ValueError("R79-A source denominator corrupted")
                values={}
                for name in (*CELLS,"wild_HC1"):
                    k=sum(x["cell_truth_included"][name] if name in CELLS else x["wild_HC1"]
                          for x in ok)
                    expected_rec={
                        "attempted_primitive_source_blocks":BLOCKS,
                        "complete":n,"refused":missing,"truth_inclusion":k,
                        "failure_inclusive_lower":k/BLOCKS,
                        "failure_inclusive_upper":(k+missing)/BLOCKS,
                    }
                    old=expected_source["coverage"][name]
                    for field,value in expected_rec.items():
                        _same(old[field],value,f"{config}/{support}/{variance}/{name}/{field}")
                    if n:
                        _same(old["Wilson95_complete"],_wilson(k,n),f"{name}/Wilson")
                    elif old["Wilson95_complete"] is not None:
                        raise ValueError("R79-A refused-only condition must have no Wilson interval")
                    values[name]=k
                for field,key in [
                    ("mean_HC3_SE_over_true_SE","HC3_SE_to_true_SE_mean"),
                    ("mean_HC3_SE_minimum_over_true_SE","HC3_SE_to_true_SE_min"),
                    ("mean_HC3_SE_p10_over_true_SE","HC3_SE_to_true_SE_p10"),
                    ("mean_REG025_SE_over_true_SE","REG025_SE_mean"),
                    ("mean_REG025_SE_p10_over_true_SE","REG025_SE_p10"),
                    ("mean_REG050_SE_over_true_SE","REG050_SE_mean"),
                    ("mean_REG050_SE_p10_over_true_SE","REG050_SE_p10"),
                    ("mean_effective_slope_variance_units","effective_slope_variance_units"),
                    ("mean_anchor_slope_variance_share","anchor_slope_variance_share"),
                    ("mean_true_max_critical","true_critical"),
                    ("mean_HC3_max_critical","HC3_critical"),
                    ("mean_REG025_max_critical","REG025_critical"),
                    ("mean_REG050_max_critical","REG050_critical"),
                ]:
                    if n:
                        _same(expected_source[field],sum(x[key] for x in ok)/n,
                              f"{config}/{support}/{variance}/{field}")
                    elif expected_source[field] is not None:
                        raise ValueError("R79-A fabricated original source mean")
                results[config][support][variance]={
                    "complete":n,"refused":missing,
                    "truth_inclusions":values,
                    "mean_HC3_to_known_slope_SE":expected_source["mean_HC3_SE_over_true_SE"],
                    "mean_HC3_to_known_SE_minimum":expected_source["mean_HC3_SE_minimum_over_true_SE"],
                    "mean_HC3_to_known_SE_p10":expected_source["mean_HC3_SE_p10_over_true_SE"],
                    "mean_effective_slope_variance_units":expected_source["mean_effective_slope_variance_units"],
                    "mean_extreme_anchor_variance_share":expected_source["mean_anchor_slope_variance_share"],
                    "mean_true_reference_max_critical":expected_source["mean_true_max_critical"],
                    "mean_HC3_reference_max_critical":expected_source["mean_HC3_max_critical"],
                    "mean_REG025_reference_max_critical":expected_source["mean_REG025_max_critical"],
                    "mean_REG050_reference_max_critical":expected_source["mean_REG050_max_critical"],
                    "mean_REG025_SE_lower_tail":expected_source["mean_REG025_SE_p10_over_true_SE"],
                    "mean_REG050_SE_lower_tail":expected_source["mean_REG050_SE_p10_over_true_SE"],
                }
                for first,second in (
                    ("REG025_SE/REG025_corr","HC3_SE/HC3_corr"),
                    ("REG050_SE/REG050_corr","HC3_SE/HC3_corr"),
                    ("HC3_SE/HC3_corr","true_SE/true_corr"),
                ):
                    changes=[int(x["cell_truth_included"][first])-
                             int(x["cell_truth_included"][second]) for x in ok]
                    key=f"{config}/{support}/{variance}/{first}_minus_{second}"
                    old=summary["paired"][key]
                    expected_pair={
                        "completed_primitive_blocks":n,"refused_primitive_blocks":missing,
                        "first_only_truth_included":sum(d==1 for d in changes),
                        "second_only_truth_included":sum(d==-1 for d in changes),
                        "both_agree":sum(d==0 for d in changes),
                        "complete_change":sum(changes)/n if n else None,
                        "failure_inclusive_lower":(sum(changes)-missing)/BLOCKS,
                        "failure_inclusive_upper":(sum(changes)+missing)/BLOCKS,
                        "not_a_calibrated_method_superiority_comparison":True,
                    }
                    for field,value in expected_pair.items():
                        if value is None:
                            if old[field] is not None:
                                raise ValueError("R79-A original paired null failure forged")
                        elif isinstance(value,bool):
                            if old[field] is not value:
                                raise ValueError("R79-A original paired inference-release claim forged")
                        else:
                            _same(old[field],value,key+"/"+field)
                    contrasts[key]=expected_pair
    accepted=sum(v["completed"] for v in actual.values())
    return {
        "study":AUDIT,"original_checkout":checkout,
        "original_SHA256_archive_members":3,
        "original_source_cases":N_CASES,
        "independently_replayed_source_X_Y":accepted,
        "original_source_refusals":N_CASES-accepted,
        "independently_replayed_wild_maxima":accepted*B,
        "independently_replayed_true_correlation_maxima":accepted*B,
        "independently_replayed_HC3_correlation_maxima":accepted*B,
        "independently_replayed_REG025_maxima":accepted*B,
        "independently_replayed_REG050_maxima":accepted*B,
        "independently_reclassified_factorial_truth_events":accepted*len(CELLS),
        "source_results":results,"source_matched_contrasts":contrasts,
        "true_correlation_reference_simulation_only":True,
        "calibrated_90pct_inference":False,
        "release_authorized":False,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original",type=Path,required=True)
    p.add_argument("--expected-checkout",default=CHECKOUT)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    result=audit(args.original,expected_checkout=args.expected_checkout)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "study":AUDIT,
        "original_checkout":result["original_checkout"],
        "independent_source_replays":result["independently_replayed_source_X_Y"],
        "original_source_refusals":result["original_source_refusals"],
        "raw_maxima":result["independently_replayed_wild_maxima"]+
                     result["independently_replayed_true_correlation_maxima"]+
                     result["independently_replayed_HC3_correlation_maxima"]+
                     result["independently_replayed_REG025_maxima"]+
                     result["independently_replayed_REG050_maxima"],
        "source_results":result["source_results"],"release_authorized":False,
    },sort_keys=True))
if __name__=="__main__":
    main()
