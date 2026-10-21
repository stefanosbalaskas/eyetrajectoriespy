"""Independent R89-A original-source numerical/provenance replay.

Does NOT import R89 source code, estimators or package. The original immutable
source is downloaded by mandatory CI. Reconstructs all primitive X/Y streams,
selective returns and sharp finite-population bound endpoints with distinct
code paths. No MNAR model identification or confidence band.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

ORIGINAL_STUDY="W3_R89_BOUND_NONRETURNED_GAZE_FINITE_POPULATION"
ORIGINAL_CHECKOUT="fe9dc0447f651979db5b62ca4311e00827c601b0"
SOURCE_SEEDS={"source":202610228900,"mask":202610228901,
              "secondary":202610228902,"assignment":202610228903,
              "return":202610228904}
CONFIGS=("independent_curves","repeated_trial_participants")
MECHANISMS=("MAR","MNAR")
RETURN_LAWS=("complete","outcome_selective")
AUDITS=(.25,.5)
BLOCKS=32
EXPECTED_ROWS=512
T=np.arange(31,dtype=float)/30.


def seed(block,config,domain):
    if block not in range(BLOCKS) or config not in CONFIGS or domain not in SOURCE_SEEDS:
        raise ValueError("R89-A invalid frozen source domain or block")
    return SOURCE_SEEDS[domain]+1000003*block+10007*CONFIGS.index(config)


def logistic(x):
    return 1/(1+np.exp(-np.clip(x,-35,35)))


def source(block,config):
    """Independent source law using separately arranged original equations."""
    n,trials=(72,1) if config==CONFIGS[0] else (36,3)
    rng=np.random.default_rng(seed(block,config,"source"))
    x=rng.uniform(-.95,.95,n)
    x[0]=-3.;x[-1]=3.
    intercept=np.column_stack((.2+.07*T,-.12+.05*T))
    slope=np.column_stack((.25+.08*np.cos(np.pi*T),
                           -.16+.09*np.sin(np.pi*T)))
    mu=intercept[None,None]+x[:,None,None,None]*slope[None,None]
    gaussian=rng.standard_normal((n,trials,31,2))
    grid=np.arange(31)
    chol=np.linalg.cholesky(.68**np.abs(grid[:,None]-grid[None,:]))
    temporal=np.einsum("tu,njud->njtd",chol,gaussian,optimize=True)
    if trials==3:
        participant=.10*rng.standard_normal((n,1,1,2))
    else:
        participant=np.zeros((n,1,1,2))
    unit_t=np.sqrt(3./rng.chisquare(5,size=n))
    contam=(rng.random(n)<.08).astype(float)-.08
    noise=(unit_t[:,None,None,None]*(.11*temporal+participant)
           +.12*contam[:,None,None,None]*np.array([1.,-.6])[None,None,None,:])
    Y=mu+(1.+.35*np.abs(x))[:,None,None,None]*noise
    return x,Y,mu


def uniform(block,config,domain,shape):
    return np.random.default_rng(seed(block,config,domain)).uniform(size=shape)


def stage_one(x,Y,mu,U,law):
    trial=np.arange(Y.shape[1])[None,:,None,None]
    v=-1.5+.3*np.abs(x[:,None,None,None])+.3*T[None,None,:,None]+.10*trial
    if law=="MNAR":
        v=v+1.2*np.tanh((Y-mu)/.35)
    elif law!="MAR":
        raise ValueError("R89-A unknown first-stage law")
    return U<np.broadcast_to(logistic(v),Y.shape)


def secondary_success(Y,mu,missing,V):
    return missing&(V<logistic(-1.+.8*np.tanh((Y-mu)/.35)))


def audit_completion(x,Y,mu,law):
    if law=="complete":
        return np.ones_like(Y)
    if law!="outcome_selective":
        raise ValueError("R89-A unknown return law")
    return logistic(.8-1.1*np.tanh((Y-mu)/.35)+.15*np.abs(x[:,None,None,None]))


def sha_float(arr):
    return sha256(np.round(np.asarray(arr,float),9).astype("<f8")
                  .tobytes(order="C")).hexdigest()


def sha_bool(arr):
    return sha256(np.asarray(arr,np.uint8).tobytes(order="C")).hexdigest()


def bounded(y):
    return np.minimum(1.,np.maximum(0.,(.5+.5*np.asarray(y,float))))


def compute_interval(visible_y,target,returned):
    """Observed-only, sharp infimum/supremum of a bounded finite mean."""
    if np.any(returned&~target) or np.any(np.isfinite(visible_y[target&~returned])):
        raise ValueError("R89-A unreturned response leaked into observed interval")
    n=int(np.count_nonzero(target))
    if not n:raise ValueError("R89-A zero target denominator")
    k=int(np.count_nonzero(returned&target))
    observed_sum=float(np.sum(bounded(visible_y[returned&target])))
    return {"total_n":n,"returned_n":k,"unreturned_n":n-k,
            "lower":observed_sum/n,
            "upper":(observed_sum+n-k)/n,
            "width":(n-k)/n}


def numeric_equal(a,b,identity,tol=1e-10):
    if isinstance(a,bool) or isinstance(b,bool):
        if a is not b:raise ValueError("R89-A boolean mismatch "+identity)
        return
    if isinstance(a,(float,int)) and isinstance(b,(float,int)):
        if not np.isfinite(a) or not np.isfinite(b) or abs(a-b)>tol:
            raise ValueError("R89-A original numerical disagreement "+identity)
    elif a != b:
        raise ValueError("R89-A original field mismatch "+identity)


def review_row(row,block,config,mechanism,law,q,x,Y,missing,secondary,assigned,returned):
    id_=f"{block}/{config}/{mechanism}/{law}/{q}"
    if (row["study"]!=ORIGINAL_STUDY or row["block"]!=block
        or row["config"]!=config or row["mechanism"]!=mechanism
        or row["return_law"]!=law or row["audit_fraction"]!=q
        or row["source_seed"]!=seed(block,config,"source")
        or row["stream_seeds"]!={k:seed(block,config,k) for k in
                                 ("mask","secondary","assignment","return")}
        or row["original_X_digest"]!=sha_float(x)
        or row["original_Y_digest"]!=sha_float(Y)
        or row["original_missing_digest"]!=sha_bool(missing)
        or row["secondary_measured_digest"]!=sha_bool(secondary)
        or row["audit_assigned_digest"]!=sha_bool(assigned)
        or row["audit_returned_digest"]!=sha_bool(returned)
        or row["observed_digest"]!=sha_bool(secondary|returned)
        or row["bounds_are_finite_population_not_confidence_intervals"] is not True
        or row["mean_truth_contained_algebraically"] is not True
        or row["contrast_truth_contained_algebraically"] is not True
        or row["unbounded_raw_gaze_or_regression_slope_identified"] is not False
        or row["response_mechanism_identified"] is not False
        or row["release_authorized"] is not False
        or row["public_package_changed"] is not False):
        raise ValueError("R89-A original source/digest/release mismatch "+id_)
    measured=secondary|returned
    visible=np.where(measured,Y,np.nan)
    positive=np.broadcast_to((x>=0)[:,None,None,None],Y.shape)
    target_groups=[missing, missing&positive, missing&~positive]
    result=[compute_interval(visible,z,measured&z) for z in target_groups]
    names=("mean_bounds","positive_group_bounds","negative_group_bounds")
    for name,val in zip(names,result):
        for field,expected in val.items():
            numeric_equal(row[name][field],expected,id_+"/"+name+"/"+field)
    contrast_l=result[1]["lower"]-result[2]["upper"]
    contrast_u=result[1]["upper"]-result[2]["lower"]
    for name,expected in (
      ("contrast_lower",contrast_l),("contrast_upper",contrast_u),
      ("contrast_width",contrast_u-contrast_l),
      ("audit_assigned_n",int(assigned.sum())),
      ("audit_returned_n",int(returned.sum())),
      ("audit_failed_n",int((assigned&~returned).sum())),
      ("contrast_sign_identified",contrast_l>0 or contrast_u<0)):
        numeric_equal(row[name],expected,id_+"/"+name)
    oracle=float(np.mean(bounded(Y[missing])))
    plus=float(np.mean(bounded(Y[missing&positive])))
    minus=float(np.mean(bounded(Y[missing&~positive])))
    numeric_equal(row["simulation_true_mean_only"],oracle,id_+"/simulation_mean")
    numeric_equal(row["simulation_true_contrast_only"],plus-minus,
                  id_+"/simulation_contrast")
    if not (result[0]["lower"]-1e-12<=oracle<=result[0]["upper"]+1e-12
            and contrast_l-1e-12<=plus-minus<=contrast_u+1e-12):
        raise ValueError("R89-A original sharpness contract excludes simulator truth")
    return {"mean_width":result[0]["width"],
            "contrast_width":contrast_u-contrast_l,
            "assigned":int(assigned.sum()),
            "returned":int(returned.sum()),
            "sign":contrast_l>0 or contrast_u<0}


def audit(original):
    required=("cases.json","summary.json","source-commit.txt","SHA256SUMS")
    if any(not (original/n).is_file() for n in required):
        raise ValueError("R89-A original immutable archive incomplete")
    lines=(original/"SHA256SUMS").read_text().splitlines()
    proofs={}
    for line in lines:
        digest,sep,filename=line.partition("  ")
        if sep!="  " or filename not in required[:3] or filename in proofs:
            raise ValueError("R89-A original SHA256 manifest invalid")
        if sha256((original/filename).read_bytes()).hexdigest()!=digest:
            raise ValueError("R89-A original source member modified")
        proofs[filename]=digest
    if set(proofs)!=set(required[:3]):
        raise ValueError("R89-A incomplete original SHA256 manifest")
    checkout=(original/"source-commit.txt").read_text().strip()
    if checkout!=ORIGINAL_CHECKOUT:
        raise ValueError("R89-A original generating checkout mismatch")
    cases=json.loads((original/"cases.json").read_text())
    summary=json.loads((original/"summary.json").read_text())
    if len(cases)!=EXPECTED_ROWS:
        raise ValueError("R89-A full 512-row original archive required")
    lookup={}
    for row in cases:
        key=(row["block"],row["config"],row["mechanism"],
             row["return_law"],row["audit_fraction"])
        if key in lookup:raise ValueError("R89-A duplicate source row")
        lookup[key]=row
    expected={(b,c,m,l,q) for b in range(BLOCKS) for c in CONFIGS
              for m in MECHANISMS for l in RETURN_LAWS for q in AUDITS}
    if set(lookup)!=expected:raise ValueError("R89-A original factorial missing")
    verified={}
    for b in range(BLOCKS):
      for c in CONFIGS:
        x,Y,mu=source(b,c)
        streams={k:uniform(b,c,k,Y.shape) for k in
                 ("mask","secondary","assignment","return")}
        for m in MECHANISMS:
          missing=stage_one(x,Y,mu,streams["mask"],m)
          initial=secondary_success(Y,mu,missing,streams["secondary"])
          for l in RETURN_LAWS:
            completion=audit_completion(x,Y,mu,l)
            for q in AUDITS:
              assigned=missing&~initial&(streams["assignment"]<q)
              returned=assigned&(streams["return"]<completion)
              key=(b,c,m,l,q)
              verified[key]=review_row(lookup[key],b,c,m,l,q,x,Y,missing,
                                       initial,assigned,returned)
    if (summary["study"]!=ORIGINAL_STUDY
        or summary["new_independent_source_conditions"]!=64
        or summary["MAR_MNAR_paired_missing_masks"]!=128
        or summary["repeated_method_rows_not_independent"]!=EXPECTED_ROWS
        or summary["blocks_per_fixed_cell"]!=BLOCKS
        or summary["bounded_transform"]!="clip((Y+1)/2,0,1)"
        or summary["no_statistical_coverage_claim"] is not True
        or summary["no_general_MNAR_or_slope_identification_claim"] is not True
        or summary["release_authorized"] is not False):
        raise ValueError("R89-A original summary boundaries invalid")
    for c in CONFIGS:
      for m in MECHANISMS:
        for l in RETURN_LAWS:
          for q in AUDITS:
            cases_=[verified[(b,c,m,l,q)] for b in range(BLOCKS)]
            archived=summary["results"][c][m][l][str(q)]
            numeric_equal(archived["independent_original_source_blocks"],BLOCKS,
                          "summary/denominator")
            numeric_equal(archived["source_refusals"],0,"summary/refusals")
            for key,calculated in (
              ("mean_mean_bound_width",float(np.mean([z["mean_width"] for z in cases_]))),
              ("mean_contrast_bound_width",float(np.mean([z["contrast_width"] for z in cases_]))),
              ("mean_audit_assigned",float(np.mean([z["assigned"] for z in cases_]))),
              ("mean_audit_returned",float(np.mean([z["returned"] for z in cases_]))),
              ("source_blocks_with_sign_identified",sum(z["sign"] for z in cases_))):
                numeric_equal(archived[key],calculated,
                              f"summary/{c}/{m}/{l}/{q}/{key}")
    return {"study":"W3_R89_A_INDEPENDENT_ORIGINAL_FINITE_BOUNDS_AUDIT",
            "original_sha256_manifest":proofs,
            "original_frozen_checkout":checkout,
            "independent_complete_sources":64,
            "independently_replayed_source_method_rows":len(verified),
            "independent_numerical_audit_passed":True,
            "bounds_are_finite_population_not_confidence_intervals":True,
            "no_MNAR_response_law_or_slope_identification":True,
            "release_authorized":False}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--original",required=True,type=Path)
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args()
    result=audit(args.original)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps(result,sort_keys=True))


if __name__=="__main__":
    main()
