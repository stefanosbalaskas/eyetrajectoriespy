"""R74-A independent original 512 source and 2,045,952 wild/Gaussian maxima audit.

Imports NO original R74 generator, package W3 fitter, original W3 bootstrap,
R72 common-covariance estimator, or original source aggregator.
Independently regenerates original artificial X/Y from frozen source seeds.
Research-only audit; does not qualify 90% continuous-time or observed-data bands.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path

import numpy as np

AUDIT="W3_R74_A_INDEPENDENT_WEIGHTED_SLOPE_GAUSSIAN_ARCHIVE_AUDIT"
STUDY="W3_R74_NEW_WEIGHTED_SLOPE_HC2_HC3_HETEROSKEDASTIC_GAUSSIAN_BANDS"
CHECKOUT="4031d3dbe5cfc5617bd939c8ea9cd00d17376bd9"
SOURCE_SEED=202610197474
GAUSSIAN_SEED=202610197475
WILD_SEED=202610197476
BLOCKS=32
CONFIGS=("curve_small","curve_standard","participant_small","participant_standard")
SUPPORT=("ordinary","extreme")
VARIANCE=("constant","predictor_heteroskedastic")
METHODS=("original_wild_HC1","pooled_HC2_Gaussian",
         "weighted_slope_HC2_Gaussian","weighted_slope_HC3_Gaussian",
         "known_heteroskedastic_Gaussian")
ESTIMATED=("pooled_HC2_Gaussian","weighted_slope_HC2_Gaussian",
           "weighted_slope_HC3_Gaussian")
B=999
SOURCES=512
T=np.linspace(0.,1.,31)
CRIT={"curve":3.1316628143877114,"participant":2.484611913363955}
TOL=2e-8


def _same(a,b,label,tol=TOL):
    try:
        aa=np.asarray(a,dtype=float)
        bb=np.asarray(b,dtype=float)
        if aa.shape!=bb.shape or not np.isfinite(aa).all() or not np.isfinite(bb).all():
            raise ValueError("shape/finite")
        if not np.allclose(aa,bb,atol=tol,rtol=2e-8):
            raise ValueError("numerical difference")
    except (TypeError,ValueError) as exc:
        raise ValueError("R74-A independently reconstructed original numerical mismatch "+label) from exc


def _wilson(k,n,z=1.959963984540054):
    if not n:return None
    p=k/n;den=1+z*z/n
    center=(p+z*z/(2*n))/den
    radius=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [max(0.,center-radius),min(1.,center+radius)]


def _info(config):
    if config not in CONFIGS:
        raise ValueError("R74-A unregistered original source size")
    design="participant" if config.startswith("participant") else "curve"
    size=(24 if config=="participant_small" else
          36 if config in ("participant_standard","curve_small") else 72)
    return size,(3 if design=="participant" else 1),design


def _seed(block,config,support,variance,domain):
    if (type(block) is not int or not 0<=block<BLOCKS or config not in CONFIGS
        or support not in SUPPORT or variance not in VARIANCE):
        raise ValueError("R74-A original source ID out of bounds")
    ci=CONFIGS.index(config)
    if domain=="source":return SOURCE_SEED+100003*block+10007*ci
    base=GAUSSIAN_SEED if domain=="gaussian" else WILD_SEED if domain=="wild" else None
    if base is None:raise ValueError("R74-A unrecognized RNG domain")
    return base+1000003*block+10007*ci+739*SUPPORT.index(support)+37*VARIANCE.index(variance)


def _unit_variance(design):
    if design=="curve":return np.full(62,.04**2)
    if design=="participant":
        return np.repeat(.065**2*(1+.35*T)**2+.04**2/3,2)
    raise ValueError("R74-A unregistered original Gaussian covariance law")


def reconstruct_original_gaussian(block,config,support,variance):
    """Independent frozen source primitive replay, without original source import."""
    n,trials,design=_info(config)
    rng=np.random.default_rng(_seed(block,config,support,variance,"source"))
    x=rng.uniform(-.95,.95,size=n)
    if support=="extreme":
        x[0]=-4.;x[-1]=4.
    scale=np.ones(n) if variance=="constant" else 1+.75*np.abs(x)
    intercept=np.stack((.35+.08*T,.25-.04*T),axis=1)
    slope=np.stack((.40+.11*np.cos(np.pi*T),-.28+.13*np.sin(np.pi*T)),axis=1)
    mean=intercept[None]+x[:,None,None]*slope[None]
    part=np.zeros((n,31,2))
    if design=="participant":
        part=rng.normal(0,.065,size=(n,1,2))*(1+.35*T[None,:,None])
    trial_noise=rng.normal(0,.04,size=(n,trials,31,2))
    y=(mean[:,None]+scale[:,None,None,None]*
       (part[:,None]+trial_noise)).mean(axis=1)
    X=np.column_stack((np.ones(n),x))
    return X,y,slope,scale


def reconstruct_source(row):
    b,c,s,v=row["block"],row["config"],row["support"],row["variance"]
    n,trials,design=_info(c)
    label=f"{b}/{c}/{s}/{v}"
    if (row["study"]!=STUDY or row["design"]!=design
        or row["source_seed"]!=_seed(b,c,s,v,"source")
        or row["gaussian_seed"]!=_seed(b,c,s,v,"gaussian")
        or row["wild_seed"]!=_seed(b,c,s,v,"wild")
        or row["native_units"]!=n or row["trials_per_unit"]!=trials
        or row["observed_curves"]!=n*trials
        or row["no_calibrated_90pct_simultaneous_method"] is not True
        or row["no_source_missingness_or_MNAR"] is not True
        or row["release_authorized"] is not False):
        raise ValueError("R74-A frozen source or false release/calibration claim "+label)
    if not row["completed"]:
        if row["exception"] is None or not row["refused"]:
            raise ValueError("R74-A refused original source exception omitted")
        if any(row["method_truth_included"][m] is not None for m in METHODS):
            raise ValueError("R74-A refused original source falsely counted")
        return {"completed":False}
    if row["refused"] or row["exception"] is not None:
        raise ValueError("R74-A complete original source falsely marked refused")
    X,Y,truth,scale=reconstruct_original_gaussian(b,c,s,v)
    for key,val in {
        "original_X":X,"original_Y_native_unit_mean":Y,
        "original_slope_truth":truth,"original_unit_scales":scale,
        "unit_scale_min":float(min(scale)),"unit_scale_max":float(max(scale)),
    }.items():
        _same(row[key],val,label+"/"+key,1e-12)

    flat=Y.reshape(n,62)
    beta=np.linalg.lstsq(X,flat,rcond=None)[0]
    gram=np.linalg.inv(X.T@X)
    proj=gram@X.T
    resid=flat-X@beta
    hat=np.einsum("np,pn->n",X,proj)
    if not (np.all(hat>0) and np.all(hat<1-1e-9)):
        raise ValueError("R74-A original OLS hat invalid")
    _same(row["max_unit_hat"],max(hat),label+"/hat")
    a=proj[1]
    se_hc1=np.sqrt(n/(n-2)*np.sum(a[:,None]**2*resid**2,axis=0))
    true=np.sqrt(np.sum((a*scale)**2)*_unit_variance(design))
    pooled=(resid/np.sqrt(1-hat)[:,None]/np.sqrt(n))*math.sqrt(float(gram[1,1]))
    weighted2=(a/np.sqrt(1-hat))[:,None]*resid
    weighted3=(a/(1-hat))[:,None]*resid
    factors={
        "pooled_HC2_Gaussian":pooled,
        "weighted_slope_HC2_Gaussian":weighted2,
        "weighted_slope_HC3_Gaussian":weighted3,
    }
    se={"original_wild_HC1":se_hc1,
        **{name:np.sqrt(np.sum(factor**2,axis=0))
           for name,factor in factors.items()},
        "known_heteroskedastic_Gaussian":true}
    if any(np.min(value)<=0 for value in se.values()):
        raise ValueError("R74-A original slope covariance variance nonpositive")
    for m in METHODS:
        _same(row["method_SE_grids"][m],se[m].reshape(31,2),label+"/"+m+"/SE")
    for field,value in {
        "mean_pooled_HC2_to_true_SE":float(np.mean(se["pooled_HC2_Gaussian"]/true)),
        "mean_weighted_HC2_to_true_SE":float(np.mean(se["weighted_slope_HC2_Gaussian"]/true)),
        "mean_weighted_HC3_to_true_SE":float(np.mean(se["weighted_slope_HC3_Gaussian"]/true)),
    }.items():
        _same(row[field],value,label+"/"+field)

    # Replay original WHOLE-independent-unit wild signs on the unchanged W3
    # OLS residual, then three exactly z-matched Gaussian covariance factors.
    weights=np.random.default_rng(_seed(b,c,s,v,"wild")).choice(
        np.array([-1.,1.]),size=(B,n))
    wild_delta=(weights*a[None])@resid
    wildmax=np.max(np.abs(wild_delta/se_hc1[None]),axis=1)
    z=np.random.default_rng(_seed(b,c,s,v,"gaussian")).standard_normal((B,n))
    raw={"original_wild_HC1":wildmax}
    raw.update({m:np.max(np.abs(z@factor)/se[m][None],axis=1)
                for m,factor in factors.items()})
    crit={m:float(np.quantile(values,.90,method="higher")) for m,values in raw.items()}
    crit["known_heteroskedastic_Gaussian"]=CRIT[design]
    slope_err=beta[1]-truth.reshape(-1)
    pivot={m:float(np.max(np.abs(slope_err/se[m]))) for m in METHODS}
    coverage={m:bool(pivot[m]<=crit[m]) for m in METHODS}
    for m in raw:
        if len(row["method_999_raw_maxima"][m])!=B:
            raise ValueError("R74-A original 999 max-statistic stream incomplete "+label+"/"+m)
        _same(row["method_999_raw_maxima"][m],raw[m],label+"/"+m+"/999 maxima")
    if set(row["method_999_raw_maxima"])!=set(raw):
        raise ValueError("R74-A original source method maxima labels altered")
    for m in METHODS:
        _same(row["method_criticals"][m],crit[m],label+"/"+m+"/critical")
        _same(row["method_truth_pivots"][m],pivot[m],label+"/"+m+"/pivot")
        if row["method_truth_included"][m] is not coverage[m]:
            raise ValueError("R74-A original method truth inclusion cannot be reproduced "+label+"/"+m)
    if (row["package_OLS_HC1_max_error"]>2e-10
        or row["package_wild_999_max_critical_error"]>2e-10):
        raise ValueError("R74-A original W3 package numerical fit contract failed")
    return {
        "completed":True,"coverage":coverage,
        "ratio2":float(np.mean(se["weighted_slope_HC2_Gaussian"]/true)),
        "ratio3":float(np.mean(se["weighted_slope_HC3_Gaussian"]/true)),
        "ratioP":float(np.mean(se["pooled_HC2_Gaussian"]/true)),
    }


def audit_original(folder:Path,expected_checkout=CHECKOUT):
    folder=Path(folder)
    filenames=("cases.json","summary.json","source-commit.txt")
    sums=(folder/"SHA256SUMS").read_text().splitlines()
    expected=[sha256((folder/n).read_bytes()).hexdigest()+"  "+n for n in filenames]
    if sums!=expected:
        raise ValueError("R74-A 3-member original immutable source SHA256 mismatch")
    checkout=(folder/"source-commit.txt").read_text().strip()
    if checkout!=expected_checkout or len(checkout)!=40:
        raise ValueError("R74-A wrong exact original source scientific checkout")
    rows=json.loads((folder/"cases.json").read_bytes())
    report=json.loads((folder/"summary.json").read_bytes())
    ids=[(z["block"],z["config"],z["support"],z["variance"]) for z in rows]
    expected_ids={(b,c,s,v) for b in range(BLOCKS) for c in CONFIGS
                  for s in SUPPORT for v in VARIANCE}
    if len(ids)!=SOURCES or len(set(ids))!=SOURCES or set(ids)!=expected_ids:
        raise ValueError("R74-A duplicate or missing new independent source identities")
    frozen={
        "study":STUDY,"source_seed":SOURCE_SEED,"gaussian_seed":GAUSSIAN_SEED,
        "wild_seed":WILD_SEED,"new_independent_primitive_blocks":BLOCKS,
        "source_cases":SOURCES,"configs":list(CONFIGS),
        "supports":list(SUPPORT),"variances":list(VARIANCE),
        "methods":list(METHODS),
        "original_wild_multiplier_positions":SOURCES*B,
        "original_gaussian_multiplier_positions":SOURCES*B,
        "derived_gaussian_maxima_across_three_covariances":SOURCES*B*len(ESTIMATED),
        "original_full_grid_dimensionality":62,
        "source_cases_are_paired_not_independent_method_replicates":True,
        "known_source_covariance_never_used_in_estimators":True,
        "no_90pct_simultaneous_band_calibration":True,
        "no_missingness_or_MNAR_evaluated":True,
        "release_authorized":False,
    }
    for key,value in frozen.items():
        if report.get(key)!=value:
            raise ValueError("R74-A original source scientific/release aggregate contract violated "+key)
    verified={(z["block"],z["config"],z["support"],z["variance"]):reconstruct_source(z)
              for z in rows}
    cells={};paired={}
    for c in CONFIGS:
        cells[c]={}
        for s in SUPPORT:
            cells[c][s]={}
            for v in VARIANCE:
                complete=[verified[b,c,s,v] for b in range(BLOCKS)
                          if verified[b,c,s,v]["completed"]]
                n=len(complete);missing=BLOCKS-n
                original=report["per_cell"][c][s][v]
                for key,val in {"attempted":BLOCKS,"complete":n,"refused":missing}.items():
                    if original[key]!=val:
                        raise ValueError("R74-A original fixed independent source denominator altered")
                counts={}
                for m in METHODS:
                    k=sum(z["coverage"][m] for z in complete)
                    rec=original["methods"][m]
                    for field,value in {
                        "attempted_independent_blocks":BLOCKS,
                        "complete_sources":n,"failed_sources":missing,
                        "truth_included":k,
                        "complete_rate":k/n if n else None,
                        "fixed_denominator_lower":k/BLOCKS,
                        "fixed_denominator_upper":(k+missing)/BLOCKS,
                    }.items():
                        if value is None:
                            if rec[field] is not None:
                                raise ValueError("R74-A original empty source claim changed "+field)
                        else:_same(rec[field],value,c+s+v+m+field)
                    if n:
                        _same(rec["Wilson95_complete"],_wilson(k,n),c+s+v+m+"/Wilson")
                    elif rec["Wilson95_complete"] is not None:
                        raise ValueError("R74-A fabricated Wilson interval with n=0")
                    counts[m]=k
                for key,attribute in (
                    ("mean_weighted_HC2_to_true_SE","ratio2"),
                    ("mean_weighted_HC3_to_true_SE","ratio3"),
                    ("mean_pooled_HC2_to_true_SE","ratioP"),
                ):
                    value=float(np.mean([z[attribute] for z in complete])) if n else None
                    if value is None:
                        if original[key] is not None:
                            raise ValueError("R74-A original mean from missing sources not allowed")
                    else:_same(original[key],value,c+s+v+"/"+key)
                cells[c][s][v]={
                    "complete":n,"failed":missing,
                    "truth_inclusions":counts,
                    "mean_weighted_HC2_to_true_SE":original["mean_weighted_HC2_to_true_SE"],
                    "mean_weighted_HC3_to_true_SE":original["mean_weighted_HC3_to_true_SE"],
                    "mean_pooled_HC2_to_true_SE":original["mean_pooled_HC2_to_true_SE"],
                }
                for first,second in (
                    ("weighted_slope_HC2_Gaussian","pooled_HC2_Gaussian"),
                    ("weighted_slope_HC3_Gaussian","weighted_slope_HC2_Gaussian"),
                    ("known_heteroskedastic_Gaussian","weighted_slope_HC2_Gaussian"),
                ):
                    deltas=[int(z["coverage"][first])-int(z["coverage"][second]) for z in complete]
                    key=f"{c}/{s}/{v}/{first}_minus_{second}"
                    want={
                        "completed_primitive_blocks":n,"refused_primitive_blocks":missing,
                        "first_only_included":sum(x==1 for x in deltas),
                        "second_only_included":sum(x==-1 for x in deltas),
                        "both_agree":sum(x==0 for x in deltas),
                        "complete_source_change":sum(deltas)/n if n else None,
                        "fixed_denominator_change_lower":(sum(deltas)-missing)/BLOCKS,
                        "fixed_denominator_change_upper":(sum(deltas)+missing)/BLOCKS,
                        "not_calibrated_method_superiority":True,
                    }
                    orig=report["paired"][key]
                    for field,value in want.items():
                        if value is None:
                            if orig[field] is not None:raise ValueError("R74-A false missing paired source")
                        elif isinstance(value,bool):
                            if orig[field] is not value:raise ValueError("R74-A original inferential claim forged")
                        else:_same(orig[field],value,key+"/"+field)
                    paired[key]=want
    complete=sum(z["completed"] for z in verified.values())
    return {
        "audit_study":AUDIT,"original_checkout":checkout,
        "original_SHA256_members_verified":3,
        "original_primitive_generating_blocks":BLOCKS,
        "original_source_cases":SOURCES,
        "original_source_complete":complete,
        "original_source_refused":SOURCES-complete,
        "original_Gaussian_X_Y_datasets_regenerated":complete,
        "original_wild_maxima_replayed":complete*B,
        "original_estimated_Gaussian_maxima_replayed":complete*B*len(ESTIMATED),
        "original_source_truth_decisions_reproduced":complete*len(METHODS),
        "per_cell":cells,"source_paired":paired,
        "no_nominal_90pct_coverage_qualified":True,
        "no_real_gaze_MNAR_tested":True,
        "release_authorized":False,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original",required=True,type=Path)
    p.add_argument("--expected-checkout",default=CHECKOUT)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    report=audit_original(args.original,args.expected_checkout)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "study":AUDIT,"original_checkout":report["original_checkout"],
        "source_cases":report["original_source_cases"],
        "complete":report["original_source_complete"],
        "refused":report["original_source_refused"],
        "wild_maxima":report["original_wild_maxima_replayed"],
        "Gaussian_maxima":report["original_estimated_Gaussian_maxima_replayed"],
        "per_cell":report["per_cell"],
        "release_authorized":False,
    },sort_keys=True))
if __name__=="__main__":
    main()
