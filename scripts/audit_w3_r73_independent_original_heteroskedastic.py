"""R73-A independent ORIGINAL heteroskedastic 32-block source numerical auditor.

NO import of R73/R72 source simulators, W3 estimator, wild bootstrap, or
original aggregate. Independently replays primitive source RNG from original
Gaussian law and reconstitutes 256 source X/Y arrays and both 999-max streams.
Not real-data 90% functional inference qualification.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path

import numpy as np

STUDY="W3_R73_PREDICTOR_HETEROSKEDASTIC_GAUSSIAN_HC2_STRESS"
AUDIT="W3_R73_A_INDEPENDENT_PREDICTOR_HETEROSKEDASTIC_HC2_ARCHIVE_AUDIT"
CHECKOUT="9d09b04ba49d6be34d16339c92eef457f71fcf31"
SOURCE_SEED=202610197373
WILD_SEED=202610197374
EST_SEED=202610197375
BLOCKS=32
B=999
DESIGNS=("curve","participant")
SUPPORT=("ordinary","extreme")
VARIANCE=("constant","predictor_heteroskedastic")
METHODS=("original_wild_HC1","estimated_HC2_Gaussian","known_heteroskedastic_Gaussian")
TOTAL=256
T=np.linspace(0.,1.,31)
TOL=2e-8
REFERENCE={"curve":3.1316628143877114,"participant":2.484611913363955}


def _near(a,b,tag,atol=TOL):
    try:
        left=np.asarray(a,float);right=np.asarray(b,float)
        if left.shape!=right.shape or not np.isfinite(left).all() or not np.isfinite(right).all():
            raise ValueError("shape/finite")
        if not np.allclose(left,right,atol=atol,rtol=2e-8):
            raise ValueError("numeric disagreement")
    except (ValueError,TypeError) as error:
        raise ValueError("R73-A independently reconstructed source differs "+tag) from error


def _wilson(k,n,z=1.959963984540054):
    if not n:return None
    p=k/n;d=1+z*z/n;mu=(p+z*z/(2*n))/d
    delta=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return [max(0.,mu-delta),min(1.,mu+delta)]


def _true_covariance_diag(design):
    if design=="curve":return np.full(62,.04**2)
    if design=="participant":
        return np.repeat(.065**2*(1+.35*T)**2+.04**2/3,2)
    raise ValueError("R73-A source design invalid")


def _seed(block,design,support,variance,domain):
    if (type(block)is not int or not 0<=block<BLOCKS or design not in DESIGNS
        or support not in SUPPORT or variance not in VARIANCE):
        raise ValueError("R73-A original source identifier invalid")
    if domain=="source":return SOURCE_SEED+10007*block+DESIGNS.index(design)
    base=WILD_SEED if domain=="wild" else EST_SEED if domain=="estimated" else None
    if base is None:raise ValueError("R73-A unknown original draw domain")
    return (base+100003*block+10007*DESIGNS.index(design)
            +739*SUPPORT.index(support)+37*VARIANCE.index(variance))


def regenerate_primitive(block,design,support,variance):
    """Independent duplicate of exact FROZEN source law, not import from R73."""
    n,trials=(72,1) if design=="curve" else (36,3)
    rng=np.random.default_rng(_seed(block,design,support,variance,"source"))
    x=rng.uniform(-.95,.95,size=n)
    if support=="extreme":
        x[0]=-4.;x[-1]=4.
    scale=np.ones(n) if variance=="constant" else 1+.75*np.abs(x)
    intercept=np.stack((.35+.08*T,.25-.04*T),axis=1)
    slope=np.stack((.40+.11*np.cos(np.pi*T),-.28+.13*np.sin(np.pi*T)),axis=1)
    part=np.zeros((n,31,2))
    if design=="participant":
        part=rng.normal(0,.065,size=(n,1,2))*(1+.35*T[None,:,None])
    independent_noise=rng.normal(0,.04,size=(n,trials,31,2))
    y=(intercept[None]+x[:,None,None]*slope[None]
       +scale[:,None,None]*(part+independent_noise.mean(axis=1)))
    X=np.column_stack((np.ones(n),x))
    return X,y,slope,scale


def source_case(row):
    block,design,support,variance=(row["block"],row["design"],row["support"],row["variance"])
    ident=f"{block}/{design}/{support}/{variance}"
    n=72 if design=="curve" else 36
    if (row["study"]!=STUDY or row["source_seed"]!=_seed(block,design,support,variance,"source")
        or row["wild_seed"]!=_seed(block,design,support,variance,"wild")
        or row["estimated_seed"]!=_seed(block,design,support,variance,"estimated")
        or row["source_units"]!=n or row["observed_curves"]!=(n if design=="curve" else 3*n)
        or row["not_calibrated_90pct_simultaneous_bands"] is not True
        or row["release_authorized"] is not False):
        raise ValueError("R73-A frozen source or withheld inference gate changed "+ident)
    if not row["completed"]:
        if not row["refused"] or row["exception"] is None:
            raise ValueError("R73-A hidden refused independent source "+ident)
        if any(row["coverage"][m] is not None for m in METHODS):
            raise ValueError("R73-A failed source falsely counted toward original coverage")
        return {"completed":False,"coverage":None}
    if row["refused"] or row["exception"] is not None:
        raise ValueError("R73-A completed source falsely refused "+ident)
    X,Y,truth,scale=regenerate_primitive(block,design,support,variance)
    for field,value in {
        "full_X":X,
        "full_Y_native_unit_mean":Y,
        "full_slope_truth":truth,
        "unit_scales":scale,
        "unit_scale_min":min(scale),
        "unit_scale_max":max(scale),
    }.items():
        _near(row[field],value,ident+"/"+field,atol=3e-13)
    flat=Y.reshape(n,-1)
    beta=np.linalg.lstsq(X,flat,rcond=None)[0]
    projector=np.linalg.inv(X.T@X)@X.T
    residual=flat-X@beta
    hat=np.einsum("np,pn->n",X,projector)
    if np.any(hat<=0) or np.any(hat>=1-1e-9):
        raise ValueError("R73-A original leverage at invalid boundary")
    _near(row["max_unit_leverage"],max(hat),ident+"/hat")
    slope_weight=projector[1]
    hc1=np.sqrt((n/(n-2))*np.sum(
        slope_weight[:,None]**2*residual**2,axis=0))
    factor=residual/np.sqrt(1-hat)[:,None]/np.sqrt(n)
    cdiag=np.sum(factor**2,axis=0)
    if np.any(cdiag<=1e-14):
        raise ValueError("R73-A HC2 covariance has nonpositive diagonal")
    hc2=np.sqrt(float(np.linalg.inv(X.T@X)[1,1])*cdiag)
    known=np.sqrt(np.sum((slope_weight*scale)**2)*_true_covariance_diag(design))
    if min(np.min(hc1),np.min(hc2),np.min(known))<=0:
        raise ValueError("R73-A negative reference SE in accepted source")
    for field,value in {
        "original_HC1_slope_SE_grid":hc1.reshape(31,2),
        "estimated_HC2_slope_SE_grid":hc2.reshape(31,2),
        "heteroskedastic_true_slope_SE_grid":known.reshape(31,2),
        "mean_HC1_to_heteroskedastic_true_SE":float(np.mean(hc1/known)),
        "mean_HC2_to_heteroskedastic_true_SE":float(np.mean(hc2/known)),
    }.items():
        _near(row[field],value,ident+"/"+field)

    wild=np.random.default_rng(_seed(block,design,support,variance,"wild")).choice(
        np.array([-1.,1.]),size=(B,n))
    wmax=np.max(np.abs(((wild*slope_weight[None])@residual)/hc1),axis=1)
    z=np.random.default_rng(_seed(block,design,support,variance,"estimated")).standard_normal((B,n))
    gmax=np.max(np.abs((z@factor)/np.sqrt(cdiag)),axis=1)
    for field,value in {
        "original_wild_999_maxima":wmax,
        "estimated_HC2_999_maxima":gmax,
    }.items():
        _near(row[field],value,ident+"/"+field)
    crit={
        "original_wild_HC1":float(np.quantile(wmax,.9,method="higher")),
        "estimated_HC2_Gaussian":float(np.quantile(gmax,.9,method="higher")),
        "known_heteroskedastic_Gaussian":REFERENCE[design],
    }
    diff=beta[1]-truth.reshape(-1)
    pivot={
        "original_wild_HC1":float(np.max(np.abs(diff/hc1))),
        "estimated_HC2_Gaussian":float(np.max(np.abs(diff/hc2))),
        "known_heteroskedastic_Gaussian":float(np.max(np.abs(diff/known))),
    }
    result={m:bool(pivot[m]<=crit[m]) for m in METHODS}
    for m in METHODS:
        _near(row["criticals"][m],crit[m],ident+"/"+m+"/critical")
        _near(row["pivots"][m],pivot[m],ident+"/"+m+"/pivot")
        if row["coverage"][m] is not result[m]:
            raise ValueError("R73-A source inclusion falsified "+ident+"/"+m)
    if row["package_OLS_HC1_oracle_error"]>2e-10 or row["package_wild_critical_oracle_error"]>2e-10:
        raise ValueError("R73-A original package numerical source failure hidden")
    return {
        "completed":True,"coverage":result,
        "ratio1":float(np.mean(hc1/known)),
        "ratio2":float(np.mean(hc2/known)),
        "hat":float(max(hat)),
        "label":ident,
    }


def audit(folder:Path,expected_checkout=CHECKOUT):
    file_names=("cases.json","summary.json","source-commit.txt")
    actual=(folder/"SHA256SUMS").read_text().splitlines()
    expected=[sha256((folder/n).read_bytes()).hexdigest()+"  "+n for n in file_names]
    if actual!=expected:
        raise ValueError("R73-A original artifact SHA256 three-member mismatch")
    if (folder/"source-commit.txt").read_text().strip()!=expected_checkout:
        raise ValueError("R73-A original exact science checkout mismatch")
    rows=json.loads((folder/"cases.json").read_bytes())
    summary=json.loads((folder/"summary.json").read_bytes())
    identity=[(x["block"],x["design"],x["support"],x["variance"]) for x in rows]
    wanted={(b,d,s,v) for b in range(BLOCKS) for d in DESIGNS for s in SUPPORT for v in VARIANCE}
    if len(identity)!=TOTAL or len(set(identity))!=TOTAL or set(identity)!=wanted:
        raise ValueError("R73-A 32 independent generating block original source identities incomplete/duplicate")
    frozen={
        "study":STUDY,"new_primitive_independent_generating_blocks":BLOCKS,
        "source_cases":TOTAL,"source_seed":SOURCE_SEED,"wild_seed":WILD_SEED,
        "estimated_Gaussian_seed":EST_SEED,"heteroskedastic_scale_rate":.75,
        "designs":list(DESIGNS),"supports":list(SUPPORT),
        "variance_regimes":list(VARIANCE),"methods":list(METHODS),
        "original_source_wild_multiplier_draw_positions":TOTAL*B,
        "source_estimated_Gaussian_draw_positions":TOTAL*B,
        "true_covariance_in_HC2_estimator":False,
        "known_law_critical_reused_by_design_only":True,
        "no_nominal_90pct_coverage_claim":True,
        "no_missingness_or_MNAR_experiment":True,
        "release_authorized":False,
    }
    for key,value in frozen.items():
        if summary.get(key)!=value:
            raise ValueError("R73-A forbidden source aggregate qualification/seed changed "+key)
    verified={(row["block"],row["design"],row["support"],row["variance"]):source_case(row) for row in rows}
    out={};pairs={}
    for design in DESIGNS:
        out[design]={}
        for support in SUPPORT:
            out[design][support]={}
            for variance in VARIANCE:
                collection=[verified[b,design,support,variance] for b in range(BLOCKS)]
                ok=[x for x in collection if x["completed"]]
                n=len(ok);m=BLOCKS-n
                stored=summary["per_cell"][design][support][variance]
                for field,value in {"attempted":BLOCKS,"complete":n,"failed":m}.items():
                    if stored[field]!=value:
                        raise ValueError("R73-A source independent denominator changed")
                original_methods=stored["methods"]
                inclusions={}
                for method in METHODS:
                    k=sum(x["coverage"][method] for x in ok)
                    rec=original_methods[method]
                    for field,value in {
                        "attempted_independent_generating_blocks":BLOCKS,
                        "complete_sources":n,"refused_sources":m,
                        "truth_inclusions":k,
                        "observed_complete_rate":k/n if n else None,
                        "full_denominator_lower":k/BLOCKS,
                        "full_denominator_upper":(k+m)/BLOCKS,
                    }.items():
                        if value is None and rec[field] is not None:
                            raise ValueError("R73-A source denominator None not preserved")
                        if value is not None:_near(rec[field],value,f"{design}/{support}/{variance}/{method}/{field}")
                    if n:
                        _near(rec["Wilson95_complete"],_wilson(k,n),
                              f"{design}/{support}/{variance}/{method}/Wilson")
                    elif rec["Wilson95_complete"] is not None:
                        raise ValueError("R73-A source Wilson 95 cannot be reported with zero accepted blocks")
                    inclusions[method]=k
                for field,value in {
                    "mean_HC1_over_true_SE":float(np.mean([x["ratio1"] for x in ok])) if n else None,
                    "mean_HC2_over_true_SE":float(np.mean([x["ratio2"] for x in ok])) if n else None,
                    "mean_max_hat":float(np.mean([x["hat"] for x in ok])) if n else None,
                }.items():
                    if value is None:
                        if stored[field] is not None:raise ValueError("R73-A missing-source mean invalid")
                    else:_near(stored[field],value,f"{design}/{support}/{variance}/{field}")
                out[design][support][variance]={
                    "original_cases_complete":n,"source_failures":m,
                    "truth_inclusions":inclusions,
                    "mean_HC2_over_heteroskedastic_true_SE":stored["mean_HC2_over_true_SE"],
                    "mean_HC1_over_heteroskedastic_true_SE":stored["mean_HC1_over_true_SE"],
                }
                for first,second in (
                    ("estimated_HC2_Gaussian","original_wild_HC1"),
                    ("known_heteroskedastic_Gaussian","estimated_HC2_Gaussian"),
                ):
                    changes=[int(x["coverage"][first])-int(x["coverage"][second]) for x in ok]
                    key=f"{design}/{support}/{variance}/{first}_minus_{second}"
                    original_pair=summary["paired"][key]
                    expected_pair={
                        "completed_primitive_blocks":n,"refused_primitive_blocks":m,
                        "first_only_truth_included":sum(v==1 for v in changes),
                        "second_only_truth_included":sum(v==-1 for v in changes),
                        "both_agree":sum(v==0 for v in changes),
                        "mean_change_completed":sum(changes)/n if n else None,
                        "full_denominator_lower":(sum(changes)-m)/BLOCKS,
                        "full_denominator_upper":(sum(changes)+m)/BLOCKS,
                        "not_a_calibrated_method_superiority_test":True,
                    }
                    for field,value in expected_pair.items():
                        if value is None and original_pair[field] is not None:
                            raise ValueError("R73-A source paired missing value changed")
                        if value is not None:_near(original_pair[field],value,key+"/"+field)
                    pairs[key]=expected_pair
    return {
        "audit_study":AUDIT,"original_source_checkout":expected_checkout,
        "archive_SHA256_members":3,
        "independent_generating_blocks":BLOCKS,
        "original_source_cases":TOTAL,
        "independently_replayed_Gaussian_X_Y_source_cases":TOTAL,
        "full_original_wild_maxima_independently_reconstructed":sum(
            B for v in verified.values() if v["completed"]),
        "full_original_HC2_Gaussian_maxima_independently_reconstructed":sum(
            B for v in verified.values() if v["completed"]),
        "results":out,"paired_reconstruction":pairs,
        "estimated_HC2_not_promoted_to_public_inference":True,
        "calibrated_90pct_full_grid_claim":False,
        "original_source_missingness_not_simulated":True,
        "release_authorized":False,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original",type=Path,required=True)
    p.add_argument("--expected-checkout",default=CHECKOUT)
    p.add_argument("--out",type=Path,required=True)
    arg=p.parse_args()
    evidence=audit(arg.original,expected_checkout=arg.expected_checkout)
    arg.out.parent.mkdir(parents=True,exist_ok=True)
    arg.out.write_text(json.dumps(evidence,sort_keys=True,indent=2)+"\n")
    print(json.dumps({
        "study":AUDIT,"original_source_checkout":evidence["original_source_checkout"],
        "original_source_cases":evidence["original_source_cases"],
        "wild_maxima":evidence["full_original_wild_maxima_independently_reconstructed"],
        "HC2_maxima":evidence["full_original_HC2_Gaussian_maxima_independently_reconstructed"],
        "coverage":evidence["results"],
        "release_authorized":False,
    },sort_keys=True))
if __name__=="__main__":
    main()
