"""R92: a small outcome-dependent completion failure breaks nominal design weighting.

New-source finite-population synthetic identification falsification, no package API.
Audit invitation randomness is different from the returned measurement law.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path

import numpy as np

STUDY = "W3_R92_NEAR_COMPLETE_AUDIT_RETURN_FRAGILITY"
CONFIGS = ("independent_curves", "repeated_trial_participants")
MECHANISMS = ("MAR", "MNAR")
ASSIGNMENT_FRACTIONS = (.25, .50)
NOMINAL_FAILURE_RATES = (.01, .05, .15)
RETURN_LAWS = ("complete", "uniform", "outcome_selective")
ASSIGNMENT_REPLICATES = 8
SCENARIOS = (("complete",0.),)+tuple((law,d) for law in ("uniform","outcome_selective") for d in NOMINAL_FAILURE_RATES)
BLOCKS = 32
SHARDS = tuple((i, i + 4) for i in range(0, 32, 4))
N_SOURCES = BLOCKS * len(CONFIGS)
N_RECORDS = N_SOURCES * len(MECHANISMS) * ASSIGNMENT_REPLICATES * len(ASSIGNMENT_FRACTIONS)*len(SCENARIOS)
SEEDS = {"source": 202610229200, "mask": 202610229201,
         "secondary": 202610229202, "assignment": 202610229203,
         "return": 202610229204}
T = np.linspace(0., 1., 31)


def stream_seed(block, config, domain):
    if type(block) is not int or block not in range(BLOCKS):
        raise ValueError("R92 invalid original primitive block")
    if config not in CONFIGS or domain not in SEEDS:
        raise ValueError("R92 invalid original stream identity")
    return SEEDS[domain] + 1000003 * block + 10007 * CONFIGS.index(config)


def sigmoid(x):
    return 1. / (1. + np.exp(-np.clip(x, -35., 35.)))


def generate(block, config):
    """New R92 X/Y sources independent of all earlier research seeds."""
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
        raise AssertionError("R92 original source shape/finite failure")
    return x,Y,mu


def random_streams(block,config,shape):
    return {domain:np.random.default_rng(stream_seed(block,config,domain)).random(shape)
            for domain in ("mask","secondary")}


def first_stage_missing(x,Y,mu,uniforms,mechanism):
    """Frozen MAR versus outcome-dependent MNAR first-stage observation mask."""
    if mechanism not in MECHANISMS:
        raise ValueError("R92 invalid first-stage observation law")
    trial=np.arange(Y.shape[1])[None,:,None,None]
    offset=-1.5+.3*np.abs(x[:,None,None,None])+.3*T[None,None,:,None]+.10*trial
    if mechanism=="MNAR":
        offset=offset+1.2*np.tanh((Y-mu)/.35)
    return uniforms < np.broadcast_to(sigmoid(offset),Y.shape)


def complete_secondary(x,Y,mu,missing,uniform):
    """Outcome-dependent secondary validation, known observed membership."""
    p=sigmoid(-1.+.8*np.tanh((Y-mu)/.35))
    return missing & (uniform<p)


def paired_audit_uniforms(block,config,rep,shape):
    """Common nested assignment and return draws across all failure scenarios."""
    if type(rep) is not int or rep not in range(ASSIGNMENT_REPLICATES):
        raise ValueError("R92 invalid assignment repetition")
    return tuple(np.random.default_rng(stream_seed(block,config,domain)+7919*(rep+1)).random(shape)
                 for domain in ("assignment","return"))


def actual_return_probability(Y,law,nominal_failure):
    """Selection law is a privileged data generator, NEVER a fitted propensity."""
    if (law,nominal_failure) not in SCENARIOS:
        raise ValueError("R92 unregistered actual return scenario")
    if law=="complete":
        return np.ones_like(Y,dtype=float)
    if law=="uniform":
        return np.full_like(Y,1.-nominal_failure,dtype=float)
    return 1.-nominal_failure*(.5+bounded_value(Y))


def observed_only_nominal_ht(observed_y,target,secondary,actually_returned,
                             assignment_probability,assumed_failure):
    """Original assignment-only and nominal-uniform correction from observed Y.

    The actual return law is not supplied or estimated. Every unreturned
    target value MUST be NaN; propensity depends only on stated policy values.
    """
    y=np.asarray(observed_y,float)
    M=np.asarray(target,bool)
    S=np.asarray(secondary,bool)
    R=np.asarray(actually_returned,bool)
    if not (0<assignment_probability<=1) or not (0<=assumed_failure<1):
        raise ValueError("R92 invalid nominal policy probabilities")
    if y.shape!=M.shape or y.shape!=S.shape or y.shape!=R.shape:
        raise ValueError("R92 dimensions disagree")
    if np.any(S&~M) or np.any(R&(~M|S)):
        raise ValueError("R92 invalid observed-outcome provenance")
    seen=S|R
    if not np.all(np.isfinite(y[seen])) or not np.all(np.isnan(y[M&~seen])):
        raise ValueError("R92 hidden unreturned outcome leaked")
    N=int(M.sum())
    if N==0:
        raise ValueError("R92 empty finite target")
    sum_S=float(bounded_value(y[S]).sum())
    sum_R=float(bounded_value(y[R]).sum())
    assign_only=(sum_S+sum_R/assignment_probability)/N
    nominal=(sum_S+sum_R/(assignment_probability*(1.-assumed_failure)))/N
    return {"assignment_only":assign_only,"nominal_uniform_completion":nominal,
            "initial_missing_n":N,"secondary_measured_n":int(S.sum()),
            "actual_recovered_n":int(R.sum()),"actually_measured_n":int(seen.sum())}


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
        raise ValueError("R92 observed arrays have inconsistent dimensions")
    if np.any(seen & ~eligible):
        raise ValueError("R92 observed selection outside target population")
    if not np.all(np.isfinite(y[seen])):
        raise ValueError("R92 measured outcome is nonfinite")
    if not np.all(np.isnan(y[eligible & ~seen])):
        raise ValueError("R92 unreturned outcome leaked into fitting")
    n=int(eligible.sum())
    if n==0:
        raise ValueError("R92 empty finite-population estimand")
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
    if n==0:raise ValueError("R92 empty simulator truth")
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
        pending=missing&~secondary
        N=int(missing.sum())
        if N==0 or not np.any(pending):
            raise ValueError("R92 source target/refusal cannot be excluded")
        full_true=complete_truth(Y,missing)
        zU=bounded_value(Y[pending])
        sumS=float(bounded_value(Y[secondary]).sum())
        sumU=float(zU.sum())
        for rep in range(ASSIGNMENT_REPLICATES):
            invitationU,completionU=paired_audit_uniforms(block,config,rep,Y.shape)
            for g in ASSIGNMENT_FRACTIONS:
                assigned=pending&(invitationU<g)
                for law,delta in SCENARIOS:
                    true_c=actual_return_probability(Y,law,delta)
                    actually_returned=assigned&(completionU<true_c)
                    measured=secondary|actually_returned
                    observed=np.where(measured,Y,np.nan)
                    fitted=observed_only_nominal_ht(observed,missing,secondary,
                                                    actually_returned,g,delta)
                    bounds=sharp_bounds(observed,missing,measured)
                    analytic_assignment_bias=-float(np.sum((1.-true_c[pending])*zU))/N
                    analytic_nominal_bias=float(np.sum((true_c[pending]/(1.-delta)-1.)*zU))/N
                    fitted_assign_error=fitted["assignment_only"]-full_true
                    fitted_nominal_error=fitted["nominal_uniform_completion"]-full_true
                    if (bounds["lower"]-1e-12>full_true or
                        bounds["upper"]+1e-12<full_true or
                        not np.isfinite(fitted_nominal_error) or
                        (law=="complete" and (np.any(assigned & ~actually_returned)
                        or abs(analytic_assignment_bias)>1e-12
                        or abs(analytic_nominal_bias)>1e-12)) or
                        (law=="uniform" and abs(analytic_nominal_bias)>1e-10)):
                        raise ValueError("R92 source algebra/bounded identification failed")
                    rows.append({
                        "study":STUDY,"block":block,"config":config,"mechanism":mechanism,
                        "rep":rep,"g":g,"return_law":law,"nominal_failure":delta,
                        "source_seed":stream_seed(block,config,"source"),
                        "assignment_seed":stream_seed(block,config,"assignment")+7919*(rep+1),
                        "return_seed":stream_seed(block,config,"return")+7919*(rep+1),
                        "X_digest":digest(x),"Y_digest":digest(Y),
                        "initial_missing_digest":mask_digest(missing),
                        "secondary_digest":mask_digest(secondary),
                        "assigned_digest":mask_digest(assigned),
                        "actually_returned_digest":mask_digest(actually_returned),
                        "actually_measured_digest":mask_digest(measured),
                        "assigned_n":int(assigned.sum()),
                        "return_n":fitted["actual_recovered_n"],
                        "failure_n":int(np.sum(assigned & ~actually_returned)),
                        "target_n":N,
                        "actual_return_probability_mean_simulator_only":
                            float(np.mean(true_c[assigned])) if assigned.any() else 1.,
                        "true_target_mean_simulator_only":full_true,
                        "assignment_only_ht":fitted["assignment_only"],
                        "nominal_uniform_correction_ht":fitted["nominal_uniform_completion"],
                        "assignment_only_realized_error":fitted_assign_error,
                        "nominal_correction_realized_error":fitted_nominal_error,
                        "oracle_design_assignment_bias_simulator_only":analytic_assignment_bias,
                        "oracle_design_nominal_bias_simulator_only":analytic_nominal_bias,
                        "oracle_mean_initially_unobserved_Z_simulator_only":sumU/max(1,int(pending.sum())),
                        "sharp_finite_bounds_width":bounds["width"],
                        "nominal_is_not_true_selective_response_propensity":law=="outcome_selective",
                        "no_nominal_confidence_coverage":True,
                        "no_field_MNAR_or_slope_identification":True,
                        "data_fitting_did_not_receive_hidden_return_probability":True,
                        "research_only":True,"release_authorized":False
                    })
    expected=len(MECHANISMS)*ASSIGNMENT_REPLICATES*len(ASSIGNMENT_FRACTIONS)*len(SCENARIOS)
    if len(rows)!=expected:
        raise ValueError("R92 primitive source method ledger incomplete")
    return rows


def summarize(rows):
    key=lambda r:(r["block"],r["config"],r["mechanism"],
                  r["rep"],r["g"],r["return_law"],r["nominal_failure"])
    expected={(b,c,m,rep,g,law,delta) for b in range(BLOCKS)
              for c in CONFIGS for m in MECHANISMS
              for rep in range(ASSIGNMENT_REPLICATES) for g in ASSIGNMENT_FRACTIONS
              for law,delta in SCENARIOS}
    if len(rows)!=N_RECORDS or len(set(map(key,rows)))!=N_RECORDS or set(map(key,rows))!=expected:
        raise ValueError("R92 failure-inclusive 14336 original method ledger incomplete")
    lookup={key(r):r for r in rows}
    for b in range(BLOCKS):
      for c in CONFIGS:
       for m in MECHANISMS:
        baseline=lookup[(b,c,m,0,ASSIGNMENT_FRACTIONS[0],"complete",0.)]
        for rep in range(ASSIGNMENT_REPLICATES):
         for g in ASSIGNMENT_FRACTIONS:
          at=[lookup[(b,c,m,rep,g,law,delta)] for law,delta in SCENARIOS]
          for r in at:
           if (r["study"]!=STUDY or r["release_authorized"] is not False
             or r["research_only"] is not True or r["no_nominal_confidence_coverage"] is not True
             or r["no_field_MNAR_or_slope_identification"] is not True
             or r["data_fitting_did_not_receive_hidden_return_probability"] is not True):
                raise ValueError("R92 science boundary violation")
           for name in ("X_digest","Y_digest","initial_missing_digest",
                        "secondary_digest","target_n","true_target_mean_simulator_only"):
             if r[name]!=baseline[name]:
                raise ValueError("R92 coupled complete source/mask mismatch")
           if r["assigned_digest"]!=at[0]["assigned_digest"] or r["assigned_n"]!=at[0]["assigned_n"]:
                raise ValueError("R92 cross-law randomized invitation changed")
           if r["return_n"]>r["assigned_n"]:
                raise ValueError("R92 nonreturn accounting invalid")
          if at[0]["failure_n"]!=0:
            raise ValueError("R92 ideal completion should not fail")
          for delta in NOMINAL_FAILURE_RATES:
            uniform=lookup[(b,c,m,rep,g,"uniform",delta)]
            selective=lookup[(b,c,m,rep,g,"outcome_selective",delta)]
            if abs(uniform["oracle_design_nominal_bias_simulator_only"])>1e-10:
                raise ValueError("R92 uniform calibrated response cannot be biased")
          for law in ("uniform","outcome_selective"):
            for d0,d1 in zip(NOMINAL_FAILURE_RATES[:-1],NOMINAL_FAILURE_RATES[1:]):
                low=lookup[(b,c,m,rep,g,law,d0)]
                high=lookup[(b,c,m,rep,g,law,d1)]
                if (low["return_n"]<high["return_n"] or
                    low["failure_n"]>high["failure_n"] or
                    low["sharp_finite_bounds_width"]>high["sharp_finite_bounds_width"]+1e-12):
                    raise ValueError("R92 coupled increasing nonreturn not monotone")
         for law,delta in SCENARIOS:
          low=lookup[(b,c,m,rep,ASSIGNMENT_FRACTIONS[0],law,delta)]
          high=lookup[(b,c,m,rep,ASSIGNMENT_FRACTIONS[1],law,delta)]
          if (low["return_n"]>high["return_n"] or
              low["sharp_finite_bounds_width"]+1e-12<high["sharp_finite_bounds_width"]):
              raise ValueError("R92 increasing randomized invitations not nested")
    result={}
    for c in CONFIGS:
      result[c]={}
      for m in MECHANISMS:
       result[c][m]={}
       for g in ASSIGNMENT_FRACTIONS:
        result[c][m][str(g)]={}
        for law,delta in SCENARIOS:
         cell=[lookup[(b,c,m,rep,g,law,delta)] for b in range(BLOCKS)
              for rep in range(ASSIGNMENT_REPLICATES)]
         result[c][m][str(g)][f"{law}:{delta}"]={
          "independent_sources":BLOCKS,
          "conditional_retrieval_repetitions":ASSIGNMENT_REPLICATES,
          "repeated_method_records":len(cell),
          "mean_empirical_assignment_only_signed_error":float(np.mean([r["assignment_only_realized_error"] for r in cell])),
          "mean_empirical_nominal_corrected_signed_error":float(np.mean([r["nominal_correction_realized_error"] for r in cell])),
          "mean_oracle_assignment_design_bias":float(np.mean([r["oracle_design_assignment_bias_simulator_only"] for r in cell])),
          "mean_oracle_nominal_design_bias":float(np.mean([r["oracle_design_nominal_bias_simulator_only"] for r in cell])),
          "rmse_assignment_only":float(np.sqrt(np.mean([r["assignment_only_realized_error"]**2 for r in cell]))),
          "rmse_nominal_corrected":float(np.sqrt(np.mean([r["nominal_correction_realized_error"]**2 for r in cell]))),
          "mean_actual_failed_eligible_audits":float(np.mean([r["failure_n"] for r in cell])),
          "mean_actual_returned_audits":float(np.mean([r["return_n"] for r in cell])),
          "mean_sharp_finite_bound_width":float(np.mean([r["sharp_finite_bounds_width"] for r in cell])),
          "source_refusals":0}
    return {
      "study":STUDY,"new_independent_complete_source_conditions":N_SOURCES,
      "paired_source_first_stage_masks":N_SOURCES*len(MECHANISMS),
      "assignment_replicates_per_source_mask":ASSIGNMENT_REPLICATES,
      "method_records_not_independent":N_RECORDS,
      "assignment_probability_grid":list(ASSIGNMENT_FRACTIONS),
      "nominal_failure_grid":list(NOMINAL_FAILURE_RATES),
      "laws":list(RETURN_LAWS),
      "target":"realized mean of clipped transformed original missing finite-population gaze",
      "known_random_audit_assignment_does_not_guarantee_random_return":True,
      "nominal_completion_adjustment_requires_true_uniform_response":True,
      "selective_completion_propensity_not_observed_or_estimable_from_sources":True,
      "privileged_oracle_bias_not_an_observed_estimator":True,
      "uncertainty_interval_coverage_not_established":True,
      "release_authorized":False,"results":result}


def shard(out,start,stop):
    if (start,stop) not in SHARDS:
        raise ValueError("R92 invalid four-block science shard")
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
        raise ValueError("R92 requires all eight immutable original shards")
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
            or m["row_count"]!=(pair[1]-pair[0])*len(CONFIGS)*len(MECHANISMS)*ASSIGNMENT_REPLICATES*len(ASSIGNMENT_FRACTIONS)*len(SCENARIOS)):
            raise ValueError("R92 original source provenance/digest failure")
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
        parser.error("R92 --start requires --stop")


if __name__=="__main__":
    main()
