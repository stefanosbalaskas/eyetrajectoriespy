"""R91: guaranteed completed random recovery enables design-based finite-target means.

Research-only finite-population Horvitz-Thompson comparison, not a package API.
The guarantee of *actual* retrieval and known independent Bernoulli inclusion
probability are substantive and may be infeasible in real sensor dropouts.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path

import numpy as np

STUDY = "W3_R91_RANDOM_COMPLETE_RECOVERY_DESIGN"
CONFIGS = ("independent_curves", "repeated_trial_participants")
MECHANISMS = ("MAR", "MNAR")
GUARANTEE_FRACTIONS = (.10, .25, .50)
ASSIGNMENT_REPLICATES = 16
BLOCKS = 32
SHARDS = tuple((i, i + 4) for i in range(0, 32, 4))
N_SOURCES = BLOCKS * len(CONFIGS)
N_RECORDS = N_SOURCES * len(MECHANISMS) * ASSIGNMENT_REPLICATES * len(GUARANTEE_FRACTIONS)
SEEDS = {"source": 202610229100, "mask": 202610229101,
         "secondary": 202610229102, "guarantee": 202610229103}
T = np.linspace(0., 1., 31)


def stream_seed(block, config, domain):
    if type(block) is not int or block not in range(BLOCKS):
        raise ValueError("R91 invalid original primitive block")
    if config not in CONFIGS or domain not in SEEDS:
        raise ValueError("R91 invalid original stream identity")
    return SEEDS[domain] + 1000003 * block + 10007 * CONFIGS.index(config)


def sigmoid(x):
    return 1. / (1. + np.exp(-np.clip(x, -35., 35.)))


def generate(block, config):
    """New R91 x/y laws independent of all previous research seeds."""
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
        raise AssertionError("R91 original source shape/finite failure")
    return x,Y,mu


def random_streams(block,config,shape):
    return {domain:np.random.default_rng(stream_seed(block,config,domain)).random(shape)
            for domain in ("mask","secondary")}


def first_stage_missing(x,Y,mu,uniforms,mechanism):
    """Frozen MAR versus outcome-dependent MNAR first-stage observation mask."""
    if mechanism not in MECHANISMS:
        raise ValueError("R91 invalid first-stage observation law")
    trial=np.arange(Y.shape[1])[None,:,None,None]
    offset=-1.5+.3*np.abs(x[:,None,None,None])+.3*T[None,None,:,None]+.10*trial
    if mechanism=="MNAR":
        offset=offset+1.2*np.tanh((Y-mu)/.35)
    return uniforms < np.broadcast_to(sigmoid(offset),Y.shape)


def complete_secondary(x,Y,mu,missing,uniform):
    """Outcome-dependent secondary validation, known observed membership."""
    p=sigmoid(-1.+.8*np.tanh((Y-mu)/.35))
    return missing & (uniform<p)


def randomized_guarantee_uniform(block,config,rep,shape):
    """Distinct prospective independently randomized *completed* retrieval."""
    if type(rep) is not int or rep not in range(ASSIGNMENT_REPLICATES):
        raise ValueError("R91 invalid randomization replicate")
    seed=stream_seed(block,config,"guarantee")+7919*(rep+1)
    return np.random.default_rng(seed).random(shape)


def design_ht(observed_y,initial_missing,secondary,guaranteed,g):
    """Observed-only Horvitz-Thompson estimator of selected finite-pop mean.

    Every outcome selected by guaranteed random recovery must ACTUALLY be
    measured, with known independent Bernoulli inclusion probability g.
    Earlier selectively recovered outcomes enter as measured census members.
    No outcome from initially missing but unreturned records may enter.
    """
    y=np.asarray(observed_y,float)
    m=np.asarray(initial_missing,bool)
    s=np.asarray(secondary,bool)
    a=np.asarray(guaranteed,bool)
    if not (.0<g<=1.):
        raise ValueError("R91 retrieval probability must be >0 and <=1")
    if y.shape!=m.shape or s.shape!=m.shape or a.shape!=m.shape:
        raise ValueError("R91 dimension mismatch")
    if np.any(s & ~m) or np.any(a & (~m|s)):
        raise ValueError("R91 invalid secondary/guaranteed provenance")
    seen=s|a
    if not np.all(np.isfinite(y[seen])) or not np.all(np.isnan(y[m & ~seen])):
        raise ValueError("R91 outcome from unobserved record leaked")
    n=int(np.sum(m))
    if n==0:
        raise ValueError("R91 empty source target")
    z_secondary=bounded_value(y[s])
    z_guaranteed=bounded_value(y[a])
    estimate=(float(z_secondary.sum())+float(z_guaranteed.sum())/g)/n
    var_hat=(1.-g)/(g*g)*float(np.dot(z_guaranteed,z_guaranteed))/(n*n)
    return {"initially_missing_n":n,"secondary_n":int(s.sum()),
            "guaranteed_n":int(a.sum()),"actual_measured_n":int(seen.sum()),
            "ht_estimate":estimate,"unbiased_design_variance_estimate":var_hat,
            "bounded_response_not_bounded_ht_estimate":True,
            "retrieval_is_actual_measurement_not_assignment_only":True}


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
        raise ValueError("R91 observed arrays have inconsistent dimensions")
    if np.any(seen & ~eligible):
        raise ValueError("R91 observed selection outside target population")
    if not np.all(np.isfinite(y[seen])):
        raise ValueError("R91 measured outcome is nonfinite")
    if not np.all(np.isnan(y[eligible & ~seen])):
        raise ValueError("R91 unreturned outcome leaked into fitting")
    n=int(eligible.sum())
    if n==0:
        raise ValueError("R91 empty finite-population estimand")
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
    if n==0:raise ValueError("R91 empty simulator truth")
    return float(bounded_value(Y[eligible_mask]).mean())


def digest(arr):
    return sha256(np.round(np.asarray(arr,float),9)
                  .astype("<f8").tobytes(order="C")).hexdigest()


def mask_digest(mask):
    return sha256(np.asarray(mask,dtype=np.uint8).tobytes(order="C")).hexdigest()


def evaluate(block,config):
    x,Y,mu=generate(block,config)
    streams=random_streams(block,config,Y.shape)
    rows=[]
    for mechanism in MECHANISMS:
        missing=first_stage_missing(x,Y,mu,streams["mask"],mechanism)
        secondary=complete_secondary(x,Y,mu,missing,streams["secondary"])
        pending=missing & ~secondary
        N=int(missing.sum())
        if N==0 or not np.any(pending):
            raise ValueError("R91 empty missing/validation target; retain refusal")
        true_mean=float(np.mean(bounded_value(Y[missing])))
        zpending=bounded_value(Y[pending])
        zsq=float(np.dot(zpending,zpending))
        for rep in range(ASSIGNMENT_REPLICATES):
            u=randomized_guarantee_uniform(block,config,rep,Y.shape)
            for g in GUARANTEE_FRACTIONS:
                guaranteed=pending & (u<g)
                measured=secondary | guaranteed
                observed=np.where(measured,Y,np.nan)
                fit=design_ht(observed,missing,secondary,guaranteed,g)
                sharp=sharp_bounds(observed,missing,measured)
                oracle_variance=(1.-g)/g*zsq/(N*N)
                naive=float(np.mean(bounded_value(observed[measured])))
                if (not sharp["lower"]-1e-12<=true_mean<=sharp["upper"]+1e-12
                    or not np.isfinite(fit["ht_estimate"])
                    or not np.isfinite(fit["unbiased_design_variance_estimate"])):
                    raise ValueError("R91 finite source algebra/variance failure")
                rows.append({
                    "study":STUDY,"block":block,"config":config,
                    "mechanism":mechanism,"assignment_rep":rep,
                    "guarantee_fraction":g,
                    "source_seed":stream_seed(block,config,"source"),
                    "guarantee_seed":stream_seed(block,config,"guarantee")+7919*(rep+1),
                    "original_X_digest":digest(x),"original_Y_digest":digest(Y),
                    "initial_missing_digest":mask_digest(missing),
                    "secondary_digest":mask_digest(secondary),
                    "guaranteed_digest":mask_digest(guaranteed),
                    "actually_measured_digest":mask_digest(measured),
                    "ht_estimate":fit["ht_estimate"],
                    "estimated_design_variance":fit["unbiased_design_variance_estimate"],
                    "oracle_conditional_design_variance_only":oracle_variance,
                    "oracle_source_true_mean_only":true_mean,
                    "ht_signed_error_diagnostic":fit["ht_estimate"]-true_mean,
                    "naive_measured_only_estimate":naive,
                    "naive_signed_error_diagnostic":naive-true_mean,
                    "sharp_bound_lower":sharp["lower"],
                    "sharp_bound_upper":sharp["upper"],
                    "sharp_bound_width":sharp["width"],
                    "initially_missing_n":N,
                    "secondary_n":fit["secondary_n"],
                    "actual_guaranteed_returned_n":fit["guaranteed_n"],
                    "measured_n":fit["actual_measured_n"],
                    "all_guaranteed_selected_y_actually_returned":True,
                    "estimator_uses_only_observed_outcomes":True,
                    "theory_unbiased_conditional_on_fixed_source":True,
                    "finite_replicate_mean_exact_unbiased_claim":False,
                    "nominal_confidence_interval_claim":False,
                    "conditional_oracle_variance_is_not_a_fitted_CI":True,
                    "public_package_unchanged":True,
                    "release_authorized":False
                })
    if len(rows)!=len(MECHANISMS)*ASSIGNMENT_REPLICATES*len(GUARANTEE_FRACTIONS):
        raise ValueError("R91 source-record counts incomplete")
    return rows


def summarize(rows):
    key=lambda r:(r["block"],r["config"],r["mechanism"],
                  r["assignment_rep"],r["guarantee_fraction"])
    expected={(b,c,m,rep,g) for b in range(BLOCKS) for c in CONFIGS
              for m in MECHANISMS for rep in range(ASSIGNMENT_REPLICATES)
              for g in GUARANTEE_FRACTIONS}
    if len(rows)!=N_RECORDS or len(set(map(key,rows)))!=N_RECORDS or set(map(key,rows))!=expected:
        raise ValueError("R91 failure-inclusive 6144-record ledger incomplete")
    d={key(r):r for r in rows}
    for b in range(BLOCKS):
      for c in CONFIGS:
       for m in MECHANISMS:
        base=d[(b,c,m,0,GUARANTEE_FRACTIONS[0])]
        for rep in range(ASSIGNMENT_REPLICATES):
          original=[d[(b,c,m,rep,g)] for g in GUARANTEE_FRACTIONS]
          for r in original:
            if (r["study"]!=STUDY or r["release_authorized"] is not False
                or r["public_package_unchanged"] is not True
                or r["theory_unbiased_conditional_on_fixed_source"] is not True
                or r["finite_replicate_mean_exact_unbiased_claim"] is not False
                or r["nominal_confidence_interval_claim"] is not False):
                raise ValueError("R91 source science contract invalid")
            for field in ("original_X_digest","original_Y_digest",
                          "initial_missing_digest","secondary_digest",
                          "oracle_source_true_mean_only","initially_missing_n","secondary_n"):
                if r[field]!=base[field]:
                    raise ValueError("R91 paired source or target changed")
          for low,high in zip(original[:-1],original[1:]):
            if (low["actual_guaranteed_returned_n"]>high["actual_guaranteed_returned_n"]
                or low["sharp_bound_width"]+1e-12<high["sharp_bound_width"]):
                raise ValueError("R91 nested randomized retrieval invariant failed")
    result={}
    for c in CONFIGS:
      result[c]={}
      for m in MECHANISMS:
        result[c][m]={}
        for g in GUARANTEE_FRACTIONS:
          cell=[d[(b,c,m,rep,g)] for b in range(BLOCKS)
                for rep in range(ASSIGNMENT_REPLICATES)]
          result[c][m][str(g)]={
            "independent_primitive_source_blocks":BLOCKS,
            "within_source_assignment_replicates":ASSIGNMENT_REPLICATES,
            "paired_source_method_records":len(cell),
            "mean_ht_signed_error_descriptive":float(np.mean([r["ht_signed_error_diagnostic"] for r in cell])),
            "rms_ht_error_descriptive":float(np.sqrt(np.mean([r["ht_signed_error_diagnostic"]**2 for r in cell]))),
            "mean_naive_measured_only_signed_error_descriptive":float(np.mean([r["naive_signed_error_diagnostic"] for r in cell])),
            "rms_naive_error_descriptive":float(np.sqrt(np.mean([r["naive_signed_error_diagnostic"]**2 for r in cell]))),
            "mean_oracle_design_variance":float(np.mean([r["oracle_conditional_design_variance_only"] for r in cell])),
            "mean_unbiased_design_variance_estimator":float(np.mean([r["estimated_design_variance"] for r in cell])),
            "mean_sharp_bound_width":float(np.mean([r["sharp_bound_width"] for r in cell])),
            "mean_actually_guaranteed_recovered":float(np.mean([r["actual_guaranteed_returned_n"] for r in cell])),
            "mean_initially_missing_target_n":float(np.mean([r["initially_missing_n"] for r in cell])),
            "source_refusals":0
          }
    return {
      "study":STUDY,"independent_complete_source_conditions":N_SOURCES,
      "paired_first_stage_masks":N_SOURCES*len(MECHANISMS),
      "guaranteed_randomization_replicates_per_source_mask":ASSIGNMENT_REPLICATES,
      "repeated_source_method_rows_not_independent":N_RECORDS,
      "guarantee_grid":list(GUARANTEE_FRACTIONS),
      "target":"finite population mean of clip((Y+1)/2,0,1) among initially missing outcomes",
      "HT_requires_known_probability_and_actual_guaranteed_complete_response":True,
      "HT_design_unbiasedness_is_analytic_not_16_draw_Monte_Carlo_evidence":True,
      "oracle_variance_not_an_interval_calibration":True,
      "no_missingness_model_or_MNAR_identification":True,
      "no_functional_slope_or_simultaneous_band_claim":True,
      "release_authorized":False,
      "results":result}



def shard(out,start,stop):
    if (start,stop) not in SHARDS:
        raise ValueError("R91 invalid four-block science shard")
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
        raise ValueError("R91 requires all eight immutable original shards")
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
            or m["row_count"]!=(pair[1]-pair[0])*len(CONFIGS)*len(MECHANISMS)*ASSIGNMENT_REPLICATES*len(GUARANTEE_FRACTIONS)):
            raise ValueError("R91 original source provenance/digest failure")
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
        parser.error("R91 --start requires --stop")


if __name__=="__main__":
    main()
