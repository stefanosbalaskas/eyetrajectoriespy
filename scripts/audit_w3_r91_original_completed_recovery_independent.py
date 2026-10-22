"""Independent R91-A actual-source audit of guaranteed randomized completed retrieval.

Does not import R91 source or package. Verifies all original 6144 records,
conditional finite-population HT arithmetic and oracle variance from the
frozen immutable original archive, without claiming interval coverage.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

ORIGINAL_STUDY="W3_R91_RANDOM_COMPLETE_RECOVERY_DESIGN"
ORIGINAL_CHECKOUT="eb65592307e1c7bc70d5cd31794bae46996bc656"
SOURCE_SEEDS={"source":202610229100,"mask":202610229101,
              "secondary":202610229102,"guarantee":202610229103}
CONFIGS=("independent_curves","repeated_trial_participants")
MECHANISMS=("MAR","MNAR")
GUARANTEE_FRACTIONS=(.10,.25,.50)
REPETITIONS=16
BLOCKS=32
EXPECTED_ROWS=6144
T=np.arange(31,dtype=float)/30.


def seed(block,config,domain):
    if block not in range(BLOCKS) or config not in CONFIGS or domain not in SOURCE_SEEDS:
        raise ValueError("R91-A invalid frozen source domain or block")
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
        raise ValueError("R91-A unknown first-stage law")
    return U<np.broadcast_to(logistic(v),Y.shape)


def secondary_success(Y,mu,missing,V):
    return missing&(V<logistic(-1.+.8*np.tanh((Y-mu)/.35)))



def sha_float(arr):
    return sha256(np.round(np.asarray(arr,float),9).astype("<f8")
                  .tobytes(order="C")).hexdigest()


def sha_bool(arr):
    return sha256(np.asarray(arr,np.uint8).tobytes(order="C")).hexdigest()


def bounded(y):
    return np.minimum(1.,np.maximum(0.,(.5+.5*np.asarray(y,float))))


def random_recovery(block,config,rep,shape):
    if rep not in range(REPETITIONS):
        raise ValueError("R91-A invalid source-assignment repeat")
    return np.random.default_rng(seed(block,config,"guarantee")+7919*(rep+1)).random(shape)


def design_based_ht(visible,initial_missing,secondary,completed,g):
    """Independent observed-only finite-population HT and design-variance audit."""
    if not (0<g<=1):
        raise ValueError("R91-A inclusion probability invalid")
    if visible.shape!=initial_missing.shape or visible.shape!=secondary.shape or visible.shape!=completed.shape:
        raise ValueError("R91-A observed source shape mismatch")
    if np.any(secondary&~initial_missing) or np.any(completed&(~initial_missing|secondary)):
        raise ValueError("R91-A invalid completed retrieval provenance")
    measured=secondary|completed
    if not np.all(np.isfinite(visible[measured])) or not np.all(np.isnan(visible[initial_missing&~measured])):
        raise ValueError("R91-A hidden outcome leaked into observed data")
    N=int(initial_missing.sum())
    if not N:
        raise ValueError("R91-A empty target")
    z_sec=bounded(visible[secondary])
    z_ret=bounded(visible[completed])
    estimate=(float(z_sec.sum())+float(z_ret.sum())/g)/N
    vhat=(1-g)/g**2*float(np.dot(z_ret,z_ret))/(N*N)
    naive=float(np.mean(bounded(visible[measured])))
    lo=float((z_sec.sum()+z_ret.sum())/N)
    hi=float((z_sec.sum()+z_ret.sum()+N-int(measured.sum()))/N)
    return {"ht":estimate,"vhat":vhat,"naive":naive,"lo":lo,"hi":hi,"width":hi-lo,
            "missing_n":N,"secondary_n":int(secondary.sum()),
            "completed_n":int(completed.sum()),"measured_n":int(measured.sum())}


def same(a,b,where,tol=1e-10):
    if isinstance(a,bool) or isinstance(b,bool):
        if a is not b:
            raise ValueError("R91-A audit flag disagreement "+where)
    elif isinstance(a,(int,float)) and isinstance(b,(int,float)):
        if not np.isfinite(a) or not np.isfinite(b) or abs(a-b)>tol:
            raise ValueError("R91-A numerical mismatch "+where)
    elif a!=b:
        raise ValueError("R91-A metadata mismatch "+where)


def verify_row(row,b,c,m,rep,g,x,Y,mu,missing,secondary,recovered):
    key=f"{b}/{c}/{m}/{rep}/{g}"
    measured=secondary|recovered
    observed=np.where(measured,Y,np.nan)
    fitted=design_based_ht(observed,missing,secondary,recovered,g)
    oracle=float(np.mean(bounded(Y[missing])))
    pending=missing&~secondary
    zpending=bounded(Y[pending])
    conditional_var=(1-g)/g*float(np.dot(zpending,zpending))/(fitted["missing_n"]**2)
    expected={
       "study":ORIGINAL_STUDY,"block":b,"config":c,"mechanism":m,
       "assignment_rep":rep,"guarantee_fraction":g,
       "source_seed":seed(b,c,"source"),
       "guarantee_seed":seed(b,c,"guarantee")+7919*(rep+1),
       "original_X_digest":sha_float(x),"original_Y_digest":sha_float(Y),
       "initial_missing_digest":sha_bool(missing),
       "secondary_digest":sha_bool(secondary),
       "guaranteed_digest":sha_bool(recovered),
       "actually_measured_digest":sha_bool(measured),
       "ht_estimate":fitted["ht"],
       "estimated_design_variance":fitted["vhat"],
       "oracle_conditional_design_variance_only":conditional_var,
       "oracle_source_true_mean_only":oracle,
       "ht_signed_error_diagnostic":fitted["ht"]-oracle,
       "naive_measured_only_estimate":fitted["naive"],
       "naive_signed_error_diagnostic":fitted["naive"]-oracle,
       "sharp_bound_lower":fitted["lo"],"sharp_bound_upper":fitted["hi"],
       "sharp_bound_width":fitted["width"],
       "initially_missing_n":fitted["missing_n"],
       "secondary_n":fitted["secondary_n"],
       "actual_guaranteed_returned_n":fitted["completed_n"],
       "measured_n":fitted["measured_n"],
       "all_guaranteed_selected_y_actually_returned":True,
       "estimator_uses_only_observed_outcomes":True,
       "theory_unbiased_conditional_on_fixed_source":True,
       "finite_replicate_mean_exact_unbiased_claim":False,
       "nominal_confidence_interval_claim":False,
       "conditional_oracle_variance_is_not_a_fitted_CI":True,
       "public_package_unchanged":True,"release_authorized":False
    }
    if set(row)!=set(expected):
        raise ValueError("R91-A unexpected original row schema "+key)
    for field,value in expected.items():
        same(row[field],value,key+"/"+field)
    if fitted["lo"]-1e-12>oracle or fitted["hi"]+1e-12<oracle:
        raise ValueError("R91-A original finite sharp bound excluded full-source truth")
    return {"ht_error":fitted["ht"]-oracle,
            "naive_error":fitted["naive"]-oracle,
            "oracle_var":conditional_var,"vhat":fitted["vhat"],
            "width":fitted["width"],"recovered":fitted["completed_n"],
            "missing_n":fitted["missing_n"]}


def verify_original(original):
    members=("cases.json","summary.json","source-commit.txt")
    if any(not (original/n).is_file() for n in (*members,"SHA256SUMS")):
        raise ValueError("R91-A immutable original archive incomplete")
    proofs={}
    for line in (original/"SHA256SUMS").read_text().splitlines():
        digest,sep,filename=line.partition("  ")
        if sep!="  " or filename not in members or filename in proofs:
            raise ValueError("R91-A manifest format invalid")
        if sha256((original/filename).read_bytes()).hexdigest()!=digest:
            raise ValueError("R91-A immutable original source member modified")
        proofs[filename]=digest
    if set(proofs)!=set(members):
        raise ValueError("R91-A source manifest incomplete")
    if (original/"source-commit.txt").read_text().strip()!=ORIGINAL_CHECKOUT:
        raise ValueError("R91-A original archive checkout mismatch")
    cases=json.loads((original/"cases.json").read_text())
    summary=json.loads((original/"summary.json").read_text())
    if len(cases)!=EXPECTED_ROWS:
        raise ValueError("R91-A full 6144 original cases mandatory")
    original_lookup={}
    for row in cases:
        key=(row["block"],row["config"],row["mechanism"],
             row["assignment_rep"],row["guarantee_fraction"])
        if key in original_lookup:
            raise ValueError("R91-A duplicated source method record")
        original_lookup[key]=row
    expected={(b,c,m,rep,g) for b in range(BLOCKS)
              for c in CONFIGS for m in MECHANISMS
              for rep in range(REPETITIONS) for g in GUARANTEE_FRACTIONS}
    if set(original_lookup)!=expected:
        raise ValueError("R91-A original factorial incomplete")
    verified={}
    for b in range(BLOCKS):
      for c in CONFIGS:
        x,Y,mu=source(b,c)
        mask_u=uniform(b,c,"mask",Y.shape)
        secondary_u=uniform(b,c,"secondary",Y.shape)
        for m in MECHANISMS:
          missing=stage_one(x,Y,mu,mask_u,m)
          secondary=secondary_success(Y,mu,missing,secondary_u)
          pending=missing&~secondary
          for rep in range(REPETITIONS):
            random_u=random_recovery(b,c,rep,Y.shape)
            for g in GUARANTEE_FRACTIONS:
              completed=pending&(random_u<g)
              key=(b,c,m,rep,g)
              verified[key]=verify_row(original_lookup[key],b,c,m,rep,g,
                                       x,Y,mu,missing,secondary,completed)
    for field,value in {
       "study":ORIGINAL_STUDY,
       "independent_complete_source_conditions":64,
       "paired_first_stage_masks":128,
       "guaranteed_randomization_replicates_per_source_mask":16,
       "repeated_source_method_rows_not_independent":6144,
       "guarantee_grid":list(GUARANTEE_FRACTIONS),
       "HT_requires_known_probability_and_actual_guaranteed_complete_response":True,
       "HT_design_unbiasedness_is_analytic_not_16_draw_Monte_Carlo_evidence":True,
       "oracle_variance_not_an_interval_calibration":True,
       "no_missingness_model_or_MNAR_identification":True,
       "no_functional_slope_or_simultaneous_band_claim":True,
       "release_authorized":False
    }.items():
        if summary.get(field)!=value:
            raise ValueError("R91-A independent original summary boundary "+field)
    for c in CONFIGS:
      for m in MECHANISMS:
        for g in GUARANTEE_FRACTIONS:
          cell=[verified[(b,c,m,rep,g)] for b in range(BLOCKS)
                for rep in range(REPETITIONS)]
          archive=summary["results"][c][m][str(g)]
          expectations={
             "independent_primitive_source_blocks":BLOCKS,
             "within_source_assignment_replicates":REPETITIONS,
             "paired_source_method_records":len(cell),
             "mean_ht_signed_error_descriptive":float(np.mean([v["ht_error"] for v in cell])),
             "rms_ht_error_descriptive":float(np.sqrt(np.mean([v["ht_error"]**2 for v in cell]))),
             "mean_naive_measured_only_signed_error_descriptive":float(np.mean([v["naive_error"] for v in cell])),
             "rms_naive_error_descriptive":float(np.sqrt(np.mean([v["naive_error"]**2 for v in cell]))),
             "mean_oracle_design_variance":float(np.mean([v["oracle_var"] for v in cell])),
             "mean_unbiased_design_variance_estimator":float(np.mean([v["vhat"] for v in cell])),
             "mean_sharp_bound_width":float(np.mean([v["width"] for v in cell])),
             "mean_actually_guaranteed_recovered":float(np.mean([v["recovered"] for v in cell])),
             "mean_initially_missing_target_n":float(np.mean([v["missing_n"] for v in cell])),
             "source_refusals":0
          }
          if set(archive)!=set(expectations):
              raise ValueError("R91-A original aggregate schema invalid")
          for field,val in expectations.items():
              same(archive[field],val,f"summary/{c}/{m}/{g}/{field}")
    return {"study":"W3_R91_A_INDEPENDENT_ORIGINAL_COMPLETED_RECOVERY",
            "original_frozen_checkout":ORIGINAL_CHECKOUT,
            "verified_original_sha256_members":proofs,
            "independent_full_source_conditions":64,
            "independently_replayed_records":len(verified),
            "analytical_design_unbiasedness_not_finite_draw_perfect_calibration":True,
            "empirical_90pct_functional_coverage_not_established":True,
            "independent_original_numerical_audit_passed":True,
            "release_authorized":False}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--original",required=True,type=Path)
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args()
    evidence=verify_original(args.original)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(evidence,indent=2,sort_keys=True)+"\n")
    print(json.dumps(evidence,sort_keys=True))


if __name__=="__main__":
    main()
