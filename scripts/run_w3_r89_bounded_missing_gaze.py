"""R89: sharp *finite-population* bounds with nonreturned synthetic gaze.

A negative identification test, not a package estimator or confidence procedure.
Missing-record conditional means and predictor-group contrasts use a predeclared
clipped, rescaled gaze outcome in [0,1]. Bounds need no MNAR return model.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path

import numpy as np

STUDY = "W3_R89_BOUND_NONRETURNED_GAZE_FINITE_POPULATION"
CONFIGS = ("independent_curves", "repeated_trial_participants")
MECHANISMS = ("MAR", "MNAR")
RETURN_LAWS = ("complete", "outcome_selective")
AUDIT_FRACTIONS = (.25, .50)
BLOCKS = 32
SHARDS = tuple((i, i + 4) for i in range(0, 32, 4))
N_SOURCES = BLOCKS * len(CONFIGS)
N_RECORDS = N_SOURCES * len(MECHANISMS) * len(RETURN_LAWS) * len(AUDIT_FRACTIONS)
SEEDS = {"source": 202610228900, "mask": 202610228901,
         "secondary": 202610228902, "assignment": 202610228903,
         "return": 202610228904}
T = np.linspace(0., 1., 31)


def stream_seed(block, config, domain):
    if type(block) is not int or block not in range(BLOCKS):
        raise ValueError("R89 invalid original primitive block")
    if config not in CONFIGS or domain not in SEEDS:
        raise ValueError("R89 invalid original stream identity")
    return SEEDS[domain] + 1000003 * block + 10007 * CONFIGS.index(config)


def sigmoid(x):
    return 1. / (1. + np.exp(-np.clip(x, -35., 35.)))


def generate(block, config):
    """New R89 x/y laws independent of all previous research seeds."""
    rng = np.random.default_rng(stream_seed(block, config, "source"))
    n, trials = (72, 1) if config == "independent_curves" else (36, 3)
    x = rng.uniform(-.95, .95, size=n)
    x[0], x[-1] = -3., 3.
    b0 = np.stack((.2 + .07*T, -.12 + .05*T), axis=-1)
    b1 = np.stack((.25 + .08*np.cos(np.pi*T),
                    -.16 + .09*np.sin(np.pi*T)), axis=-1)
    mu = b0[None, None] + x[:,None,None,None] * b1[None,None]
    white = rng.normal(size=(n,trials,31,2))
    grid = np.arange(31)
    C = np.linalg.cholesky(.68 ** np.abs(grid[:,None]-grid[None,:]))
    noise = np.einsum("tu,njud->njtd",C,white,optimize=True)
    if trials > 1:
        unit = rng.normal(size=(n,1,1,2)) * .10
    else:
        unit = np.zeros((n,1,1,2))
    radial = np.sqrt(3. / rng.chisquare(5, size=n))
    shocks = ((rng.random(n)<.08).astype(float)-.08)
    Y = mu + (1.+.35*np.abs(x))[:,None,None,None] * (
        radial[:,None,None,None]*(.11*noise+unit)
        + (.12*shocks[:,None,None,None]) * np.array([1.,-.6])[None,None,None,:]
    )
    if Y.shape != (n,trials,31,2) or not np.isfinite(Y).all():
        raise AssertionError("R89 original source shape/finite failure")
    return x,Y,mu


def random_streams(block,config,shape):
    return {domain:np.random.default_rng(stream_seed(block,config,domain)).random(shape)
            for domain in ("mask","secondary","assignment","return")}


def first_stage_missing(x,Y,mu,uniforms,mechanism):
    if mechanism not in MECHANISMS:
        raise ValueError("R89 invalid first-stage observation law")
    trial = np.arange(Y.shape[1])[None,:,None,None]
    offset = -1.5 + .3*np.abs(x[:,None,None,None]) + .3*T[None,None,:,None] + .10*trial
    if mechanism == "MNAR":
        offset = offset + 1.2*np.tanh((Y-mu)/.35)
    p = sigmoid(offset)
    return uniforms < np.broadcast_to(p,Y.shape)


def complete_secondary(x,Y,mu,missing,uniform):
    p=sigmoid(-1. + .8*np.tanh((Y-mu)/.35))
    return missing & (uniform<p)


def audit_outcome_probability(x,Y,mu,law):
    if law == "complete":
        return np.ones_like(Y)
    if law != "outcome_selective":
        raise ValueError("R89 invalid audit return law")
    return sigmoid(.8 - 1.1*np.tanh((Y-mu)/.35)
                   + .15*np.abs(x[:,None,None,None]))


def bounded_value(y):
    """The estimand is clipped, rescaled gaze, not unbounded raw response."""
    return np.clip((np.asarray(y,float)+1.)/2.,0.,1.)


def sharp_bounds(observed_y,eligible_mask,seen_mask):
    """Sharp infimum/supremum of a finite missing-group mean, [0,1] support.

    NaNs MUST mark unreturned outcomes. The function does not accept latent Y
    or missingness/return propensity. A nonempty eligible group is required.
    """
    eligible=np.asarray(eligible_mask,bool)
    seen=np.asarray(seen_mask,bool)
    y=np.asarray(observed_y,float)
    if y.shape != eligible.shape or seen.shape != eligible.shape:
        raise ValueError("R89 observed arrays have inconsistent dimensions")
    if np.any(seen & ~eligible):
        raise ValueError("R89 observed selection outside target population")
    if not np.all(np.isfinite(y[seen])):
        raise ValueError("R89 measured outcome is nonfinite")
    if not np.all(np.isnan(y[eligible & ~seen])):
        raise ValueError("R89 unreturned outcome leaked into fitting")
    n=int(eligible.sum())
    if n==0:
        raise ValueError("R89 empty finite-population estimand")
    observed_n=int(seen.sum())
    sum_observed=float(bounded_value(y[seen]).sum())
    lower=sum_observed/n
    upper=(sum_observed+(n-observed_n))/n
    return {"total_n":n, "returned_n":observed_n,
            "unreturned_n":n-observed_n,
            "lower":lower, "upper":upper, "width":upper-lower}


def complete_truth(Y,eligible_mask):
    """Simulation-only source truth, never called by sharp_bounds."""
    n=int(eligible_mask.sum())
    if n==0:raise ValueError("R89 empty simulator truth")
    return float(bounded_value(Y[eligible_mask]).mean())


def digest(arr):
    return sha256(np.round(np.asarray(arr,float),9)
                  .astype("<f8").tobytes(order="C")).hexdigest()


def mask_digest(mask):
    return sha256(np.asarray(mask,dtype=np.uint8).tobytes(order="C")).hexdigest()


def evaluate(block,config):
    x,Y,mu=generate(block,config)
    U=random_streams(block,config,Y.shape)
    rows=[]
    group_pos=np.broadcast_to((x>=0)[:,None,None,None],Y.shape)
    group_neg=~group_pos
    for mechanism in MECHANISMS:
        missing=first_stage_missing(x,Y,mu,U["mask"],mechanism)
        secondary=complete_secondary(x,Y,mu,missing,U["secondary"])
        for law in RETURN_LAWS:
            completion=audit_outcome_probability(x,Y,mu,law)
            for q in AUDIT_FRACTIONS:
                assigned=missing & ~secondary & (U["assignment"]<q)
                returned=assigned & (U["return"]<completion)
                seen=secondary | returned
                observed=np.where(seen,Y,np.nan)
                all_=sharp_bounds(observed,missing,seen)
                pos=sharp_bounds(observed,missing&group_pos,seen&group_pos)
                neg=sharp_bounds(observed,missing&group_neg,seen&group_neg)
                contrast_lower=pos["lower"]-neg["upper"]
                contrast_upper=pos["upper"]-neg["lower"]
                true_all=complete_truth(Y,missing)
                true_pos=complete_truth(Y,missing&group_pos)
                true_neg=complete_truth(Y,missing&group_neg)
                contrast_true=true_pos-true_neg
                if not (all_["lower"]-1e-12<=true_all<=all_["upper"]+1e-12
                        and contrast_lower-1e-12<=contrast_true<=contrast_upper+1e-12):
                    raise AssertionError("R89 finite population sharp bounds excluded truth")
                if np.any(returned & ~assigned) or np.any(returned & secondary):
                    raise AssertionError("R89 audit subset/provenance invalid")
                rows.append({
                    "study":STUDY,"block":block,"config":config,
                    "mechanism":mechanism,"return_law":law,
                    "audit_fraction":q,
                    "source_seed":stream_seed(block,config,"source"),
                    "stream_seeds":{k:stream_seed(block,config,k) for k in U},
                    "original_X_digest":digest(x),
                    "original_Y_digest":digest(Y),
                    "original_missing_digest":mask_digest(missing),
                    "secondary_measured_digest":mask_digest(secondary),
                    "audit_assigned_digest":mask_digest(assigned),
                    "audit_returned_digest":mask_digest(returned),
                    "observed_digest":mask_digest(seen),
                    "audit_assigned_n":int(assigned.sum()),
                    "audit_returned_n":int(returned.sum()),
                    "audit_failed_n":int((assigned&~returned).sum()),
                    "mean_bounds":all_,"positive_group_bounds":pos,
                    "negative_group_bounds":neg,
                    "contrast_lower":contrast_lower,
                    "contrast_upper":contrast_upper,
                    "contrast_width":contrast_upper-contrast_lower,
                    "contrast_sign_identified":contrast_lower>0 or contrast_upper<0,
                    "simulation_true_mean_only":true_all,
                    "simulation_true_contrast_only":contrast_true,
                    "mean_truth_contained_algebraically":True,
                    "contrast_truth_contained_algebraically":True,
                    "bounds_are_finite_population_not_confidence_intervals":True,
                    "unbounded_raw_gaze_or_regression_slope_identified":False,
                    "response_mechanism_identified":False,
                    "public_package_changed":False,"release_authorized":False
                })
    if len(rows)!=len(MECHANISMS)*len(RETURN_LAWS)*len(AUDIT_FRACTIONS):
        raise AssertionError("R89 original factorial truncated")
    return rows


def summarize(rows):
    key=lambda r:(r["block"],r["config"],r["mechanism"],
                  r["return_law"],r["audit_fraction"])
    expected={(b,c,m,l,q) for b in range(BLOCKS) for c in CONFIGS
              for m in MECHANISMS for l in RETURN_LAWS for q in AUDIT_FRACTIONS}
    if (len(rows)!=N_RECORDS or len(set(map(key,rows)))!=N_RECORDS
        or set(map(key,rows))!=expected):
        raise ValueError("R89 failure-inclusive independent source ledger incomplete")
    for r in rows:
        if (r["study"]!=STUDY or r["release_authorized"] is not False
            or r["public_package_changed"] is not False
            or r["response_mechanism_identified"] is not False
            or r["bounds_are_finite_population_not_confidence_intervals"] is not True
            or r["original_X_digest"] == ""
            or r["source_seed"] != stream_seed(r["block"],r["config"],"source")
            or r["audit_returned_n"] > r["audit_assigned_n"]):
            raise ValueError("R89 science boundary or source provenance invalid")
    lookup={key(r):r for r in rows}
    for b in range(BLOCKS):
      for c in CONFIGS:
       for m in MECHANISMS:
        for l in RETURN_LAWS:
         low=lookup[(b,c,m,l,.25)]
         high=lookup[(b,c,m,l,.5)]
         if (low["mean_bounds"]["returned_n"]>high["mean_bounds"]["returned_n"]
             or low["mean_bounds"]["width"]+1e-12<high["mean_bounds"]["width"]
             or low["contrast_width"]+1e-12<high["contrast_width"]
             or low["original_missing_digest"]!=high["original_missing_digest"]
             or low["simulation_true_mean_only"]!=high["simulation_true_mean_only"]):
            raise ValueError("R89 nested randomized audit width/source contract failure")
         if (l=="complete" and lookup[(b,c,m,"outcome_selective",.25)]
             ["mean_bounds"]["width"]+1e-12<low["mean_bounds"]["width"]):
             raise ValueError("R89 complete audit did not dominate selective return")
    results={}
    for c in CONFIGS:
      results[c]={}
      for m in MECHANISMS:
       results[c][m]={}
       for l in RETURN_LAWS:
        results[c][m][l]={}
        for q in AUDIT_FRACTIONS:
         cell=[lookup[(b,c,m,l,q)] for b in range(BLOCKS)]
         results[c][m][l][str(q)]={
             "independent_original_source_blocks":BLOCKS,
             "all_mean_truth_contained_by_construction":all(
                 z["mean_truth_contained_algebraically"] for z in cell),
             "all_contrast_truth_contained_by_construction":all(
                 z["contrast_truth_contained_algebraically"] for z in cell),
             "mean_mean_bound_width":float(np.mean([
                 z["mean_bounds"]["width"] for z in cell])),
             "mean_contrast_bound_width":float(np.mean([
                 z["contrast_width"] for z in cell])),
             "mean_audit_assigned":float(np.mean([z["audit_assigned_n"] for z in cell])),
             "mean_audit_returned":float(np.mean([z["audit_returned_n"] for z in cell])),
             "source_blocks_with_sign_identified":int(sum(
                 z["contrast_sign_identified"] for z in cell)),
             "source_refusals":0,
         }
    return {"study":STUDY,"new_independent_source_conditions":N_SOURCES,
            "MAR_MNAR_paired_missing_masks":N_SOURCES*len(MECHANISMS),
            "repeated_method_rows_not_independent":N_RECORDS,
            "blocks_per_fixed_cell":BLOCKS,
            "estimand":"mean and positive-minus-negative-x contrast of clipped gaze in originally missing finite population",
            "bounded_transform":"clip((Y+1)/2,0,1)",
            "no_statistical_coverage_claim":True,
            "no_general_MNAR_or_slope_identification_claim":True,
            "release_authorized":False,"results":results}


def shard(out,start,stop):
    if (start,stop) not in SHARDS:
        raise ValueError("R89 invalid four-block science shard")
    out.mkdir(parents=True,exist_ok=True)
    rows=[z for b in range(start,stop) for c in CONFIGS for z in evaluate(b,c)]
    raw=(json.dumps(rows,allow_nan=False,sort_keys=True)+"\n").encode()
    (out/"cases.json").write_bytes(raw)
    manifest={"study":STUDY,"start":start,"stop":stop,
              "row_count":len(rows),"sha256":sha256(raw).hexdigest(),
              "seeds":SEEDS,"checkout":os.environ.get("GITHUB_SHA","unverified-local")}
    (out/"manifest.json").write_text(json.dumps(manifest,sort_keys=True)+"\n")


def aggregate(out,parts):
    manifests=sorted(parts.glob("*/manifest.json"))
    if len(manifests)!=len(SHARDS):
        raise ValueError("R89 requires all eight immutable original shards")
    seen=set()
    rows=[]
    checkout=os.environ.get("GITHUB_SHA","unverified-local")
    for path in manifests:
        m=json.loads(path.read_text())
        pair=(m["start"],m["stop"])
        raw=(path.parent/"cases.json").read_bytes()
        if (pair not in SHARDS or pair in seen or m["study"]!=STUDY
            or m["checkout"]!=checkout or m["seeds"]!=SEEDS
            or sha256(raw).hexdigest()!=m["sha256"]
            or m["row_count"]!=(pair[1]-pair[0])*len(CONFIGS)*len(MECHANISMS)*len(RETURN_LAWS)*len(AUDIT_FRACTIONS)):
            raise ValueError("R89 original source provenance/digest failure")
        seen.add(pair)
        rows.extend(json.loads(raw))
    report=summarize(rows)
    out.mkdir(parents=True,exist_ok=True)
    for filename,content in (("cases.json",json.dumps(rows,allow_nan=False,sort_keys=True)+"\n"),
                             ("summary.json",json.dumps(report,allow_nan=False,sort_keys=True,indent=2)+"\n"),
                             ("source-commit.txt",checkout+"\n")):
        (out/filename).write_text(content)
    (out/"SHA256SUMS").write_text("".join(
        sha256((out/n).read_bytes()).hexdigest()+"  "+n+"\n"
        for n in ("cases.json","summary.json","source-commit.txt")))
    print(json.dumps(report,sort_keys=True))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True,type=Path)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--start",type=int)
    mode.add_argument("--merge-parts",type=Path)
    parser.add_argument("--stop",type=int)
    args=parser.parse_args()
    if args.merge_parts is not None:
        aggregate(args.out,args.merge_parts)
    elif args.stop is not None:
        shard(args.out,args.start,args.stop)
    else:
        parser.error("R89 --start requires --stop")


if __name__=="__main__":
    main()
