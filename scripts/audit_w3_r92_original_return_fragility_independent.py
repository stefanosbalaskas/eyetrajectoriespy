"""Independent R92-A actual-source audit of guaranteed randomized completed retrieval.

Does not import R92 source or package. Verifies all original 6144 records,
conditional finite-population HT arithmetic and oracle variance from the
frozen immutable original archive, without claiming interval coverage.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

ORIGINAL_STUDY="W3_R92_NEAR_COMPLETE_AUDIT_RETURN_FRAGILITY"
ORIGINAL_CHECKOUT="2b0c29cbe342919c204c445be4f80639b2261efb"
SOURCE_SEEDS={"source":202610229200,"mask":202610229201,
              "secondary":202610229202,"assignment":202610229203,
              "return":202610229204}
CONFIGS=("independent_curves","repeated_trial_participants")
MECHANISMS=("MAR","MNAR")
ASSIGNMENT_FRACTIONS=(.25,.50)
FAILURES=(.01,.05,.15)
SCENARIOS=(("complete",0.),)+tuple((law,d) for law in ("uniform","outcome_selective") for d in FAILURES)
REPETITIONS=8
BLOCKS=32
EXPECTED_ROWS=14336
T=np.arange(31,dtype=float)/30.


def seed(block,config,domain):
    if block not in range(BLOCKS) or config not in CONFIGS or domain not in SOURCE_SEEDS:
        raise ValueError("R92-A invalid frozen source domain or block")
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
        raise ValueError("R92-A unknown first-stage law")
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



def paired_uniforms(block,config,rep,shape):
    if rep not in range(REPETITIONS):
        raise ValueError("R92-A invalid randomized repeat")
    return tuple(np.random.default_rng(seed(block,config,domain)+7919*(rep+1)).random(shape)
                 for domain in ("assignment","return"))

def return_chance(Y,law,d):
    if (law,d) not in SCENARIOS:
        raise ValueError("R92-A unknown response experiment")
    if law=="complete":
        return np.ones_like(Y)
    if law=="uniform":
        return np.full_like(Y,1.-d)
    return 1.-d*(.5+bounded(Y))

def visible_ht(y,M,S,R,g,d):
    if not (0<g<=1 and 0<=d<1):
        raise ValueError("R92-A invalid nominal weighting")
    if y.shape!=M.shape or y.shape!=S.shape or y.shape!=R.shape:
        raise ValueError("R92-A mismatched mask shapes")
    if np.any(S&~M) or np.any(R&(~M|S)):
        raise ValueError("R92-A invalid source measurement provenance")
    observed=S|R
    if not np.all(np.isfinite(y[observed])) or not np.all(np.isnan(y[M&~observed])):
        raise ValueError("R92-A hidden unreturned outcome leaked")
    N=int(M.sum())
    if not N:
        raise ValueError("R92-A empty target")
    sec=float(bounded(y[S]).sum()); ret=float(bounded(y[R]).sum())
    return (sec+ret/g)/N, (sec+ret/(g*(1.-d)))/N, (N-int(observed.sum()))/N

def equal(a,b,k,tol=1e-10):
    if isinstance(a,bool) or isinstance(b,bool):
        if a is not b: raise ValueError("R92-A boolean disagreement "+k)
    elif isinstance(a,(float,int)) and isinstance(b,(float,int)):
        if not np.isfinite(a) or not np.isfinite(b) or abs(a-b)>tol:
            raise ValueError("R92-A source numerical mismatch "+k)
    elif a!=b: raise ValueError("R92-A source identifier mismatch "+k)

def validate_record(row,key,x,Y,M,S,A,R,c):
    b,config,m,rep,g,law,d=key
    seen=S|R
    observed=np.where(seen,Y,np.nan)
    h,n,w=visible_ht(observed,M,S,R,g,d)
    N=int(M.sum())
    truth=float(bounded(Y[M]).mean())
    Z=bounded(Y[M&~S])
    ba=-float(np.dot(1.-c[M&~S],Z))/N
    bn=float(np.dot(c[M&~S]/(1.-d)-1.,Z))/N
    expected={
      "study":ORIGINAL_STUDY,"block":b,"config":config,"mechanism":m,
      "rep":rep,"g":g,"return_law":law,"nominal_failure":d,
      "source_seed":seed(b,config,"source"),
      "assignment_seed":seed(b,config,"assignment")+7919*(rep+1),
      "return_seed":seed(b,config,"return")+7919*(rep+1),
      "X_digest":sha_float(x),"Y_digest":sha_float(Y),
      "initial_missing_digest":sha_bool(M),
      "secondary_digest":sha_bool(S),"assigned_digest":sha_bool(A),
      "actually_returned_digest":sha_bool(R),
      "actually_measured_digest":sha_bool(seen),
      "assigned_n":int(A.sum()),"return_n":int(R.sum()),
      "failure_n":int((A&~R).sum()),"target_n":N,
      "actual_return_probability_mean_simulator_only":float(c[A].mean()) if A.any() else 1.,
      "true_target_mean_simulator_only":truth,
      "assignment_only_ht":h,"nominal_uniform_correction_ht":n,
      "assignment_only_realized_error":h-truth,
      "nominal_correction_realized_error":n-truth,
      "oracle_design_assignment_bias_simulator_only":ba,
      "oracle_design_nominal_bias_simulator_only":bn,
      "oracle_mean_initially_unobserved_Z_simulator_only":float(Z.mean()),
      "sharp_finite_bounds_width":w,
      "nominal_is_not_true_selective_response_propensity":law=="outcome_selective",
      "no_nominal_confidence_coverage":True,
      "no_field_MNAR_or_slope_identification":True,
      "data_fitting_did_not_receive_hidden_return_probability":True,
      "research_only":True,"release_authorized":False
    }
    if set(row)!=set(expected): raise ValueError("R92-A full-source row schema differs "+str(key))
    for k,v in expected.items(): equal(row[k],v,str(key)+"/"+k)
    lo=float(bounded(observed[seen]).sum())/N
    if not lo-1e-12<=truth<=lo+w+1e-12:
        raise ValueError("R92-A oracle full-source outside sharp observed bound")
    return (h-truth,n-truth,ba,bn,int((A&~R).sum()),int(R.sum()),w)

def audit(path):
    members=("cases.json","summary.json","source-commit.txt")
    if any(not (path/k).is_file() for k in (*members,"SHA256SUMS")):
        raise ValueError("R92-A mandatory actual original archive incomplete")
    proof={}
    for line in (path/"SHA256SUMS").read_text().splitlines():
        checksum,sep,name=line.partition("  ")
        if not sep or name not in members or name in proof:
            raise ValueError("R92-A source checksum manifest invalid")
        if sha256((path/name).read_bytes()).hexdigest()!=checksum:
            raise ValueError("R92-A original source checksum failure")
        proof[name]=checksum
    if set(proof)!=set(members):
        raise ValueError("R92-A original SHA256 member missing")
    if (path/"source-commit.txt").read_text().strip()!=ORIGINAL_CHECKOUT:
        raise ValueError("R92-A original checkout identity mismatch")
    rows=json.loads((path/"cases.json").read_text())
    report=json.loads((path/"summary.json").read_text())
    if len(rows)!=EXPECTED_ROWS:
        raise ValueError("R92-A require all original 14336 source records")
    keyed={}
    for row in rows:
        key=(row["block"],row["config"],row["mechanism"],row["rep"],row["g"],row["return_law"],row["nominal_failure"])
        if key in keyed: raise ValueError("R92-A duplicate case")
        keyed[key]=row
    expected={(b,c,m,r,g,l,d) for b in range(BLOCKS) for c in CONFIGS
              for m in MECHANISMS for r in range(REPETITIONS)
              for g in ASSIGNMENT_FRACTIONS for l,d in SCENARIOS}
    if set(keyed)!=expected: raise ValueError("R92-A factorial archive missing cases")
    checked={}
    for b in range(BLOCKS):
      for config in CONFIGS:
        x,Y,mu=source(b,config)
        u_mask=uniform(b,config,"mask",Y.shape)
        u_secondary=uniform(b,config,"secondary",Y.shape)
        for m in MECHANISMS:
          M=stage_one(x,Y,mu,u_mask,m)
          S=secondary_success(Y,mu,M,u_secondary)
          for rep in range(REPETITIONS):
            Ua,Ur=paired_uniforms(b,config,rep,Y.shape)
            for g in ASSIGNMENT_FRACTIONS:
              A=(M&~S)&(Ua<g)
              for law,d in SCENARIOS:
                c=return_chance(Y,law,d)
                R=A&(Ur<c)
                key=(b,config,m,rep,g,law,d)
                checked[key]=validate_record(keyed[key],key,x,Y,M,S,A,R,c)
    metadata={"study":ORIGINAL_STUDY,"new_independent_complete_source_conditions":64,
              "paired_source_first_stage_masks":128,
              "assignment_replicates_per_source_mask":8,
              "method_records_not_independent":14336,
              "assignment_probability_grid":list(ASSIGNMENT_FRACTIONS),
              "nominal_failure_grid":list(FAILURES),
              "laws":["complete","uniform","outcome_selective"],
              "known_random_audit_assignment_does_not_guarantee_random_return":True,
              "nominal_completion_adjustment_requires_true_uniform_response":True,
              "selective_completion_propensity_not_observed_or_estimable_from_sources":True,
              "privileged_oracle_bias_not_an_observed_estimator":True,
              "uncertainty_interval_coverage_not_established":True,
              "release_authorized":False}
    for k,v in metadata.items(): equal(report.get(k),v,"summary/"+k)
    fields=("mean_empirical_assignment_only_signed_error",
            "mean_empirical_nominal_corrected_signed_error",
            "mean_oracle_assignment_design_bias","mean_oracle_nominal_design_bias",
            "mean_actual_failed_eligible_audits","mean_actual_returned_audits",
            "mean_sharp_finite_bound_width")
    for config in CONFIGS:
      for m in MECHANISMS:
       for g in ASSIGNMENT_FRACTIONS:
        for law,d in SCENARIOS:
          block=[checked[(b,config,m,rep,g,law,d)] for b in range(BLOCKS)
                 for rep in range(REPETITIONS)]
          values=np.asarray(block,float)
          original=report["results"][config][m][str(g)][f"{law}:{d}"]
          for j,k in enumerate(fields): equal(original[k],float(values[:,j].mean()),f"summary/{config}/{m}/{g}/{law}/{d}/{k}")
          equal(original["rmse_assignment_only"],float(np.sqrt(np.mean(values[:,0]**2))),"rmse-assignment")
          equal(original["rmse_nominal_corrected"],float(np.sqrt(np.mean(values[:,1]**2))),"rmse-nominal")
          equal(original["independent_sources"],32,"sources")
          equal(original["conditional_retrieval_repetitions"],8,"repetitions")
          equal(original["repeated_method_records"],256,"rows-per-cell")
          equal(original["source_refusals"],0,"no-excluded-sources")
    return {"study":"W3_R92_A_INDEPENDENT_REAL_ORIGINAL_REPLAY",
            "original_frozen_checkout":ORIGINAL_CHECKOUT,
            "SHA256SUMS_members":proof,"independent_complete_source_conditions":64,
            "independently_replayed_original_records":len(checked),
            "independent_analytic_bias_and_source_masks_verified":True,
            "real_MNAR_return_propensity_identified":False,
            "nominal_confidence_calibration_claim":False,
            "release_authorized":False}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--original",required=True,type=Path)
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args()
    result=audit(args.original)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))

if __name__=="__main__":
    main()
