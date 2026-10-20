"""R74-A original-archive numerical audit; independent of R74 generator/fitter.

Replays 512 NEW source X/Y arrays and all four original wild/estimated
Gaussian bootstrap maximum-statistic streams. Does not import R74 simulator,
R72 pooled-Gaussian implementation, package W3 regression or source aggregate.
Frozen original scientific PR merge checkout and three SHA256s are mandatory.
No nominal 90% coverage certification or production API promotion.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path

import numpy as np

STUDY="W3_R74_NEW_WEIGHTED_SLOPE_HC2_HC3_HETEROSKEDASTIC_GAUSSIAN_BANDS"
AUDIT="W3_R74_A_INDEPENDENT_ORIGINAL_WEIGHTED_HC2_HC3_FULL_MAXIMUM_AUDIT"
ORIGINAL_CHECKOUT="4031d3dbe5cfc5617bd939c8ea9cd00d17376bd9"
SOURCE_SEED=202610197474
NORMAL_SEED=202610197475
WILD_SEED=202610197476
BLOCKS=32
CONFIGS=("curve_small","curve_standard","participant_small","participant_standard")
SUPPORT=("ordinary","extreme")
VARIANCE=("constant","predictor_heteroskedastic")
N=512
B=999
METHODS=("original_wild_HC1","pooled_HC2_Gaussian",
         "weighted_slope_HC2_Gaussian","weighted_slope_HC3_Gaussian",
         "known_heteroskedastic_Gaussian")
ESTIMATED=METHODS[1:4]
GRID=31
DIM=2
TIME=np.linspace(0.,1.,GRID)
NUMERICAL_TOL=5e-8
CRITICAL={"curve":3.1316628143877114,
          "participant":2.484611913363955}


def _close(actual,expected,field,atol=NUMERICAL_TOL):
    try:
        a=np.asarray(actual,dtype=float)
        b=np.asarray(expected,dtype=float)
        if a.shape!=b.shape or not np.isfinite(a).all() or not np.isfinite(b).all():
            raise ValueError("nonfinite or shape mismatch")
        if not np.allclose(a,b,atol=atol,rtol=3e-8):
            raise ValueError("numeric difference")
    except (ValueError,TypeError) as e:
        raise ValueError("R74-A independent original numerical mismatch: "+field) from e


def _wilson(k,n,z=1.95996398454):
    if not n:return None
    p=k/n
    denom=1+z*z/n
    mid=(p+z*z/(2*n))/denom
    half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/denom
    return [max(0.,min(p,mid-half)),min(1.,max(p,mid+half))]


def config_info(config):
    if config=="curve_small":return 36,1,"curve"
    if config=="curve_standard":return 72,1,"curve"
    if config=="participant_small":return 24,3,"participant"
    if config=="participant_standard":return 36,3,"participant"
    raise ValueError("R74-A unknown independent-unit config")


def frozen_seed(block,config,support,variance,domain):
    if (type(block) is not int or not 0<=block<BLOCKS
        or config not in CONFIGS or support not in SUPPORT or variance not in VARIANCE):
        raise ValueError("R74-A original generating source identity invalid")
    c=CONFIGS.index(config)
    if domain=="source":return SOURCE_SEED+100003*block+10007*c
    first=NORMAL_SEED if domain=="gaussian" else WILD_SEED if domain=="wild" else None
    if first is None:raise ValueError("R74-A unknown source RNG domain")
    return first+1000003*block+10007*c+739*SUPPORT.index(support)+37*VARIANCE.index(variance)


def unit_base_variance(design):
    if design=="curve":return np.full(GRID*DIM,.04**2)
    if design=="participant":
        return np.repeat(.065**2*(1+.35*TIME)**2+.04**2/3,2)
    raise ValueError("R74-A unknown native-unit Gaussian covariance")


def source_law(block,config,support,variance):
    """Independent pure NumPy rebuild of frozen Gaussian-generating experiment."""
    n,trials,design=config_info(config)
    rng=np.random.default_rng(frozen_seed(block,config,support,variance,"source"))
    x=rng.uniform(-.95,.95,size=n)
    if support=="extreme":x[0],x[-1]=-4.,4.
    scales=(np.ones(n) if variance=="constant" else 1+.75*np.abs(x))
    intercept=np.stack((.35+.08*TIME,.25-.04*TIME),axis=1)
    slope=np.stack((.40+.11*np.cos(np.pi*TIME),-.28+.13*np.sin(np.pi*TIME)),axis=1)
    part=np.zeros((n,GRID,DIM))
    if design=="participant":
        part=rng.normal(0,.065,size=(n,1,DIM))*(1+.35*TIME[None,:,None])
    trialnoise=rng.normal(0,.04,size=(n,trials,GRID,DIM))
    y=intercept[None]+x[:,None,None]*slope[None]+(
        scales[:,None,None]*(part+trialnoise.mean(axis=1)))
    X=np.column_stack((np.ones(n),x))
    return X,y,slope,scales


def verify_source(row):
    b,c,s,v=(row["block"],row["config"],row["support"],row["variance"])
    label=f"{b}/{c}/{s}/{v}"
    n,trials,design=config_info(c)
    if (row["study"]!=STUDY or row["design"]!=design
        or row["source_seed"]!=frozen_seed(b,c,s,v,"source")
        or row["gaussian_seed"]!=frozen_seed(b,c,s,v,"gaussian")
        or row["wild_seed"]!=frozen_seed(b,c,s,v,"wild")
        or row["native_units"]!=n or row["trials_per_unit"]!=trials
        or row["observed_curves"]!=n*trials
        or row["no_calibrated_90pct_simultaneous_method"] is not True
        or row["no_source_missingness_or_MNAR"] is not True
        or row["release_authorized"] is not False):
        raise ValueError("R74-A source provenance/release invariant violated "+label)
    if not row["completed"]:
        if not row["refused"] or row["exception"] is None:
            raise ValueError("R74-A failed original source not failure-inclusive "+label)
        if any(row["method_truth_included"][m] is not None for m in METHODS):
            raise ValueError("R74-A refused source has false inclusion "+label)
        return {"completed":False,"label":label}
    if row["refused"] or row["exception"] is not None:
        raise ValueError("R74-A original accepted source contains failure "+label)
    X,Y,slope,scales=source_law(b,c,s,v)
    for k,array in {
        "original_X":X,
        "original_Y_native_unit_mean":Y,
        "original_slope_truth":slope,
        "original_unit_scales":scales,
        "unit_scale_min":np.min(scales),
        "unit_scale_max":np.max(scales),
    }.items():
        _close(row[k],array,label+"/"+k,atol=6e-13)
    y=Y.reshape(n,GRID*DIM)
    coef=np.linalg.lstsq(X,y,rcond=None)[0]
    projector=np.linalg.inv(X.T@X)@X.T
    residual=y-X@coef
    a=projector[1]
    leverage=np.sum(X*projector.T,axis=1)
    if np.min(leverage)<=0 or np.max(leverage)>=1-1e-9:
        raise ValueError("R74-A accepted original leverage violates HC2/HC3 domain")
    _close(row["max_unit_hat"],np.max(leverage),label+"/hat")
    hc1=np.sqrt((n/(n-2))*np.sum(a[:,None]**2*residual**2,axis=0))
    g11=float(np.linalg.inv(X.T@X)[1,1])
    factors={
        "pooled_HC2_Gaussian":residual/np.sqrt(1-leverage)[:,None]/np.sqrt(n)*np.sqrt(g11),
        "weighted_slope_HC2_Gaussian":residual*(a/np.sqrt(1-leverage))[:,None],
        "weighted_slope_HC3_Gaussian":residual*(a/(1-leverage))[:,None],
    }
    estimated={}
    z=np.random.default_rng(frozen_seed(b,c,s,v,"gaussian")).standard_normal((B,n))
    for name,f in factors.items():
        diag=np.sum(f**2,axis=0)
        if np.any(diag<=0) or not np.isfinite(diag).all():
            raise ValueError("R74-A estimated slope Gaussian covariance invalid "+label)
        maxima=np.max(np.abs(z@f)/np.sqrt(diag)[None],axis=1)
        estimated[name]={"se":np.sqrt(diag),"maxima":maxima}
    wild=np.random.default_rng(frozen_seed(b,c,s,v,"wild")).choice(
        np.array([-1.,1.]),size=(B,n))
    wildmax=np.max(np.abs(((wild*a[None])@residual)/hc1),axis=1)
    exactse=np.sqrt(float(np.sum((a*scales)**2))*unit_base_variance(design))
    se={
        "original_wild_HC1":hc1,
        **{name:d["se"] for name,d in estimated.items()},
        "known_heteroskedastic_Gaussian":exactse,
    }
    maxima={"original_wild_HC1":wildmax,
            **{name:d["maxima"] for name,d in estimated.items()}}
    crit={name:float(np.quantile(maxima[name],.90,method="higher")) for name in maxima}
    crit["known_heteroskedastic_Gaussian"]=CRITICAL[design]
    error=coef[1]-slope.reshape(-1)
    pivot={name:float(np.max(np.abs(error/se[name]))) for name in METHODS}
    truth={name:bool(pivot[name]<=crit[name]) for name in METHODS}
    if (row["package_OLS_HC1_max_error"] is None or
        row["package_wild_999_max_critical_error"] is None or
        max(row["package_OLS_HC1_max_error"],
            row["package_wild_999_max_critical_error"])>2e-10):
        raise ValueError("R74-A original package reference not numerically accepted "+label)
    for name in METHODS:
        _close(row["method_SE_grids"][name],se[name].reshape(GRID,DIM),label+"/"+name+"/SE")
        _close(row["method_criticals"][name],crit[name],label+"/"+name+"/critical")
        _close(row["method_truth_pivots"][name],pivot[name],label+"/"+name+"/pivot")
        if row["method_truth_included"][name] is not truth[name]:
            raise ValueError("R74-A original full-grid truth classification changed "+label+"/"+name)
    for name,values in maxima.items():
        _close(row["method_999_raw_maxima"][name],values,label+"/"+name+"/999 maximum draws")
    for name,value in {
        "mean_weighted_HC2_to_true_SE":np.mean(se["weighted_slope_HC2_Gaussian"]/exactse),
        "mean_weighted_HC3_to_true_SE":np.mean(se["weighted_slope_HC3_Gaussian"]/exactse),
        "mean_pooled_HC2_to_true_SE":np.mean(se["pooled_HC2_Gaussian"]/exactse),
    }.items():_close(row[name],value,label+"/"+name)
    return {
        "completed":True,"label":label,
        "inclusion":truth,
        "se_ratio":{name:float(np.mean(se[name]/exactse)) for name in ESTIMATED},
        "critical":crit,
        "max_hat":float(np.max(leverage)),
    }


def audit(path:Path,expected_checkout=ORIGINAL_CHECKOUT):
    files=("cases.json","summary.json","source-commit.txt")
    checks=(path/"SHA256SUMS").read_text().splitlines()
    expected=[sha256((path/name).read_bytes()).hexdigest()+"  "+name for name in files]
    if checks!=expected:raise ValueError("R74-A source archive SHA256 mismatch")
    checkout=(path/"source-commit.txt").read_text().strip()
    if checkout!=expected_checkout or len(checkout)!=40:
        raise ValueError("R74-A original source checkout mismatch")
    rows=json.loads((path/"cases.json").read_bytes())
    original=json.loads((path/"summary.json").read_bytes())
    actual=[(q["block"],q["config"],q["support"],q["variance"]) for q in rows]
    planned={(b,c,s,v) for b in range(BLOCKS) for c in CONFIGS for s in SUPPORT for v in VARIANCE}
    if len(actual)!=N or len(set(actual))!=N or set(actual)!=planned:
        raise ValueError("R74-A incomplete/duplicate independent generating-source identities")
    frozen={
        "study":STUDY,"source_seed":SOURCE_SEED,"gaussian_seed":NORMAL_SEED,
        "wild_seed":WILD_SEED,"new_independent_primitive_blocks":BLOCKS,
        "source_cases":N,"configs":list(CONFIGS),"supports":list(SUPPORT),
        "variances":list(VARIANCE),"methods":list(METHODS),
        "original_wild_multiplier_positions":N*B,
        "original_gaussian_multiplier_positions":N*B,
        "derived_gaussian_maxima_across_three_covariances":N*B*len(ESTIMATED),
        "original_full_grid_dimensionality":GRID*DIM,
        "source_cases_are_paired_not_independent_method_replicates":True,
        "known_source_covariance_never_used_in_estimators":True,
        "no_90pct_simultaneous_band_calibration":True,
        "no_missingness_or_MNAR_evaluated":True,"release_authorized":False,
    }
    for k,v in frozen.items():
        if original.get(k)!=v:raise ValueError("R74-A source summary/release invariant "+k)
    source={tuple((q["block"],q["config"],q["support"],q["variance"])):verify_source(q) for q in rows}
    results={};pairs={}
    for c in CONFIGS:
        results[c]={}
        for s in SUPPORT:
            results[c][s]={}
            for v in VARIANCE:
                sources=[source[b,c,s,v] for b in range(BLOCKS)]
                complete=[x for x in sources if x["completed"]]
                n=len(complete);missing=BLOCKS-n
                source_report=original["per_cell"][c][s][v]
                for k,target in {
                    "attempted":BLOCKS,"complete":n,"refused":missing,
                }.items():
                    if source_report[k]!=target:
                        raise ValueError("R74-A independent source count mismatch "+c+"/"+s+"/"+v)
                incl={}
                for name in METHODS:
                    count=sum(x["inclusion"][name] for x in complete)
                    row=source_report["methods"][name]
                    expected_rec={
                        "attempted_independent_blocks":BLOCKS,"complete_sources":n,
                        "failed_sources":missing,"truth_included":count,
                        "complete_rate":count/n if n else None,
                        "fixed_denominator_lower":count/BLOCKS,
                        "fixed_denominator_upper":(count+missing)/BLOCKS,
                        "Wilson95_complete":_wilson(count,n),
                    }
                    for k,val in expected_rec.items():
                        if val is None:
                            if row[k] is not None:raise ValueError("R74-A source None denominator invalid")
                        else:_close(row[k],val,c+"/"+s+"/"+v+"/"+name+"/"+k)
                    incl[name]=count
                ratios={}
                for name,key in [
                    ("pooled_HC2_Gaussian","mean_pooled_HC2_to_true_SE"),
                    ("weighted_slope_HC2_Gaussian","mean_weighted_HC2_to_true_SE"),
                    ("weighted_slope_HC3_Gaussian","mean_weighted_HC3_to_true_SE"),
                ]:
                    average=sum(q["se_ratio"][name] for q in complete)/n if n else None
                    if average is None:
                        if source_report[key] is not None:raise ValueError("R74-A source mean missingness")
                    else:_close(source_report[key],average,c+"/"+s+"/"+v+"/"+key)
                    ratios[name]=average
                critical={
                    name:sum(x["critical"][name] for x in complete)/n if n else None
                    for name in METHODS
                }
                results[c][s][v]={
                    "independent_blocks_attempted":BLOCKS,
                    "completed_source_cases":n,"failed_source_cases":missing,
                    "truth_inclusion":incl,
                    "estimated_to_true_slope_SE_ratio":ratios,
                    "mean_source_critical":critical,
                }
                for first,second in [
                    ("weighted_slope_HC2_Gaussian","pooled_HC2_Gaussian"),
                    ("weighted_slope_HC3_Gaussian","weighted_slope_HC2_Gaussian"),
                    ("known_heteroskedastic_Gaussian","weighted_slope_HC2_Gaussian"),
                ]:
                    delta=[int(x["inclusion"][first])-int(x["inclusion"][second]) for x in complete]
                    key=f"{c}/{s}/{v}/{first}_minus_{second}"
                    row=original["paired"][key]
                    expected_pair={
                        "completed_primitive_blocks":n,"refused_primitive_blocks":missing,
                        "first_only_included":sum(t==1 for t in delta),
                        "second_only_included":sum(t==-1 for t in delta),
                        "both_agree":sum(t==0 for t in delta),
                        "complete_source_change":sum(delta)/n if n else None,
                        "fixed_denominator_change_lower":(sum(delta)-missing)/BLOCKS,
                        "fixed_denominator_change_upper":(sum(delta)+missing)/BLOCKS,
                        "not_calibrated_method_superiority":True,
                    }
                    for k,val in expected_pair.items():
                        if val is None:
                            if row[k] is not None:raise ValueError("R74-A paired missingness")
                        else:_close(row[k],val,key+"/"+k)
                    pairs[key]=expected_pair
    complete=sum(q["completed"] for q in source.values())
    return {
        "study":AUDIT,
        "immutable_original_checkout":checkout,
        "original_three_SHA256_members_verified":3,
        "independent_primitive_generating_blocks":BLOCKS,
        "planned_source_cases":N,
        "original_complete_cases":complete,
        "original_refused_cases":N-complete,
        "Gaussian_X_Y_source_arrays_independently_replayed":complete,
        "original_wild_maxima_independently_replayed":complete*B,
        "original_three_Gaussian_maxima_streams_independently_replayed":complete*B*3,
        "original_maxima_all_methods_replayed":complete*B*4,
        "per_cell":results,
        "paired":pairs,
        "calibrated_90pct_simultaneous_coverage_claim":False,
        "missing_observation_MNAR_qualified":False,
        "public_inference_API_qualified":False,
        "release_authorized":False,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original",type=Path,required=True)
    p.add_argument("--expected-checkout",default=ORIGINAL_CHECKOUT)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    outcome=audit(args.original,expected_checkout=args.expected_checkout)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(outcome,sort_keys=True,indent=2)+"\n")
    print(json.dumps({
        "study":AUDIT,
        "checkout":outcome["immutable_original_checkout"],
        "complete":outcome["original_complete_cases"],
        "refused":outcome["original_refused_cases"],
        "replayed_maxima":outcome["original_maxima_all_methods_replayed"],
        "results":outcome["per_cell"],
        "release_authorized":False,
    },sort_keys=True))
if __name__=="__main__":
    main()
