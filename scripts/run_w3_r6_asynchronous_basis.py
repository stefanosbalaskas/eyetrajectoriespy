"""W3 R6: genuinely asynchronous native-time basis-function research, not public API.

Each curve has its own jittered time stamps; observed data are never
interpolated, regridded, zero-filled or fitted by existing common-grid W3.
One explicitly assumed degree-5 Legendre time basis creates fitted
*model predictions* on a common evaluation grid, not reconstructed samples.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd

from eyetrajectoriespy import IrregularTrajectorySet
from eyetrajectoriespy.workflows import (
    FunctionOnScalarWorkflowConfig, run_function_on_scalar_workflow,
)
from scripts.run_w3_known_truth_workflow_validation import (
    TIME, DIMS, truth_coefficients,
)

STUDY="W3_R6_ASYNCHRONOUS_NATIVE_BASIS_20261012"
MASTER_SEED=202610121613
BLOCKS=96
N_CURVES=96
MECHANISMS=("mcar","mar_x","latent_mnar")
DROPOUT_WINDOW=slice(11,19)
DEGREE=5
MIN_CURVES=8
MIDPOINT=15
NUMERICAL_TOL=2e-8
MC_BOOTSTRAP_DRAWS=2000


def expit(x):
    return 1/(1+np.exp(-np.clip(x,-35,35)))


def source(block,mechanism):
    if type(block) is not int or not 0<=block<BLOCKS:
        raise ValueError("generating block outside preregistered ledger")
    if mechanism not in MECHANISMS:
        raise ValueError("unplanned observation-loss mechanism")
    rng=np.random.default_rng(MASTER_SEED+10429*block)
    x=rng.uniform(-.95,.95,size=N_CURVES)
    jitter=np.clip(rng.normal(0,.006,size=(N_CURVES,len(TIME))),-.010,.010)
    jitter[:,0]=0.
    jitter[:,-1]=0.
    t=TIME[None,:]+jitter
    if not (np.diff(t,axis=1)>0).all():
        raise ValueError("nonmonotone jittered native timestamps")

    baseline=np.empty((N_CURVES,len(TIME),len(DIMS)))
    individual=rng.normal(0,.065,size=(N_CURVES,1,len(DIMS)))
    epsilon=rng.normal(0,.055,size=baseline.shape)
    for i in range(N_CURVES):
        true=truth_coefficients(t[i])
        baseline[i]=true[0]+x[i]*true[1]
    y=baseline + individual*(1+.3*t[:,:,None]) + epsilon
    uniforms=rng.uniform(size=N_CURVES)
    if mechanism=="mcar":
        p=np.full(N_CURVES,.35)
    elif mechanism=="mar_x":
        p=expit(-.62+1.3*x)
    else:
        hidden=y[:,MIDPOINT,0]-baseline[:,MIDPOINT,0]
        p=expit(-.62+1.3*x+2.7*hidden/.105)
    lost=uniforms<p
    if not lost.any():
        raise ValueError("no actual recording gaps generated")
    masks=np.ones((N_CURVES,len(TIME)),dtype=bool)
    masks[lost,DROPOUT_WINDOW]=False
    ids=tuple(f"C{i:03d}" for i in range(N_CURVES))
    meta=pd.DataFrame({"participant_id":ids,"trial_id":0})
    full=IrregularTrajectorySet(
        time=tuple(t[i].copy() for i in range(N_CURVES)),
        values=tuple(y[i].copy() for i in range(N_CURVES)),
        curve_ids=ids,dimension_names=DIMS,metadata=meta,
        coordinate_system="normalized",time_unit="s",
        provenance={"study":STUDY,"source_block":block,
                    "jittered_async":True,"simulated":True,
                    "recording_loss":"none"},
    )
    native=IrregularTrajectorySet(
        time=tuple(t[i,masks[i]].copy() for i in range(N_CURVES)),
        values=tuple(y[i,masks[i]].copy() for i in range(N_CURVES)),
        curve_ids=ids,dimension_names=DIMS,metadata=meta,
        coordinate_system="normalized",time_unit="s",
        provenance={"study":STUDY,"source_block":block,
                    "jittered_async":True,"simulated":True,
                    "recording_loss":mechanism,
                    "no_silent_interpolation":True},
    )
    return full,native,x,lost,p,t,y,masks


def basis(t):
    """Fixed predeclared polynomial basis; prediction != measured data."""
    t=np.asarray(t,float)
    return np.polynomial.legendre.legvander(2*t-1,DEGREE)


def stack_observed(native,x,*,unit_balanced):
    if not isinstance(native,IrregularTrajectorySet):
        raise TypeError("native irregular source object required")
    x=np.asarray(x,float)
    if len(x)!=len(native.time):
        raise ValueError("condition must map once per independent source curve")
    Z,Y,S=[],[],[]
    for i,(t,v) in enumerate(zip(native.time,native.values)):
        if len(t)<2 or not np.all(np.diff(t)>0) or not np.isfinite(v).all():
            raise ValueError("insufficient finite, strictly monotone native observations")
        B=basis(t)
        Z.append(np.concatenate((B,B*x[i]),axis=1))
        Y.append(np.asarray(v,float))
        # unit-balanced objective: each *independent curve* has total
        # weight one, rather than allowing high-sample curves to dominate.
        S.append(np.full(len(t),1/np.sqrt(len(t)) if unit_balanced else 1.))
    return np.vstack(Z),np.vstack(Y),np.concatenate(S)


def fit_native_basis(native,x,*,unit_balanced):
    """Explicitly model-based prediction on TIME; not timepoint interpolation."""
    if len(native.curve_ids)<MIN_CURVES:
        raise ValueError("not enough independent curves to identify functional slope")
    Z,Y,S=stack_observed(native,x,unit_balanced=unit_balanced)
    Zw=Z*S[:,None]
    Yw=Y*S[:,None]
    if np.linalg.matrix_rank(Zw)<Z.shape[1]:
        raise ValueError("rank-deficient declared time-basis design")
    theta=np.linalg.lstsq(Zw,Yw,rcond=None)[0]
    # Independent QR numerical reference, with the same declared basis
    # and weights but not the least-squares routine.
    q,r=np.linalg.qr(Zw,mode="reduced")
    oracle=np.linalg.solve(r,q.T@Yw)
    delta=float(np.max(np.abs(theta-oracle)))
    if delta>NUMERICAL_TOL:
        raise ValueError("native QR numerical oracle disagreement")
    B0=basis(TIME)
    coefficients=np.stack((B0@theta[:DEGREE+1],B0@theta[DEGREE+1:]))
    return coefficients,delta,len(Z),int(np.linalg.matrix_rank(Zw))


def block_mc_ci(values,*,seed):
    if not values:
        return None
    x=np.asarray(values,float)
    rng=np.random.default_rng(seed)
    inds=rng.integers(0,len(x),size=(MC_BOOTSTRAP_DRAWS,len(x)))
    return [float(v) for v in np.quantile(x[inds].mean(axis=1),[.025,.975])]


def evaluate(block,mechanism):
    row={"study":STUDY,"block":block,"mechanism":mechanism,
         "status":"failed","exception":None,
         "n_source_curves":N_CURVES,"n_source_observations":N_CURVES*len(TIME),
         "n_native_observations":None,"n_lost_curves":None,
         "native_async_jitter_verified":False,
         "original_values_and_timestamps_preserved":False,
         "current_common_grid_W3_refused":False,
         "reference_degree":DEGREE,
         "full_source_basis_rmse":None,
         "observed_basis_unit_balanced_rmse":None,
         "observed_basis_sample_weighted_rmse":None,
         "balanced_mid_slope_shift_vs_full":None,
         "sample_weighted_mid_slope_shift_vs_full":None,
         "full_qr_max_delta":None,
         "observed_unit_balanced_qr_max_delta":None,
         "observed_sample_weighted_qr_max_delta":None,
         "irregular_method_qualified":False,
         "interval_calibration_qualified":False,
         "release_authorized":False}
    try:
        full,native,x,lost,p,t,y,masks=source(block,mechanism)
        if np.allclose(t,TIME[None,:],atol=1e-12):
            raise ValueError("timestamps are not genuinely asynchronous")
        if np.allclose(t[0],t[1],atol=1e-12):
            raise ValueError("independent curves are not asynchronous")
        saved=[(times.copy(),values.copy()) for times,values in zip(native.time,native.values)]
        for i in range(N_CURVES):
            if not np.array_equal(native.time[i],t[i,masks[i]]) or not np.array_equal(native.values[i],y[i,masks[i]]):
                raise ValueError("native sample values differ from true recorded data")

        frame=pd.DataFrame({"curve_id":native.curve_ids,"condition":x})
        try:
            run_function_on_scalar_workflow(
                native,frame,config=FunctionOnScalarWorkflowConfig(
                    predictors=("condition",),dimensions=DIMS,unit="curve")
            )
        except TypeError as exc:
            if "IrregularTrajectorySet" not in str(exc):
                raise
        else:
            raise ValueError("supported dense W3 mistakenly fitted native asynchronous data")

        full_fit,full_delta,_,_=fit_native_basis(full,x,unit_balanced=True)
        balanced,b_delta,n_obs,rank=fit_native_basis(native,x,unit_balanced=True)
        sample_weighted,sw_delta,n_obs2,rank2=fit_native_basis(
            native,x,unit_balanced=False
        )
        if n_obs!=n_obs2:
            raise ValueError("regression weights changed actual observed source count")
        if rank!=2*(DEGREE+1) or rank2!=rank:
            raise ValueError("time basis regression lost scientific identification rank")
        for (old_t,old_y),tt,v in zip(saved,native.time,native.values):
            if not np.array_equal(old_t,tt) or not np.array_equal(old_y,v):
                raise ValueError("source observed timestamps or coordinates mutated")

        truth=truth_coefficients(TIME)
        err=lambda fit:float(np.sqrt(np.mean((fit[1]-truth[1])**2)))
        row.update({
            "status":"ok",
            "n_native_observations":int(n_obs),
            "n_lost_curves":int(np.sum(lost)),
            "native_async_jitter_verified":True,
            "original_values_and_timestamps_preserved":True,
            "current_common_grid_W3_refused":True,
            "full_source_basis_rmse":err(full_fit),
            "observed_basis_unit_balanced_rmse":err(balanced),
            "observed_basis_sample_weighted_rmse":err(sample_weighted),
            "balanced_mid_slope_shift_vs_full":float(
                balanced[1,MIDPOINT,0]-full_fit[1,MIDPOINT,0]
            ),
            "sample_weighted_mid_slope_shift_vs_full":float(
                sample_weighted[1,MIDPOINT,0]-full_fit[1,MIDPOINT,0]
            ),
            "full_qr_max_delta":full_delta,
            "observed_unit_balanced_qr_max_delta":b_delta,
            "observed_sample_weighted_qr_max_delta":sw_delta,
        })
    except Exception as exc:
        row["exception"]={"type":type(exc).__name__,"message":str(exc)[:900]}
    return row


def audit(rows):
    expected={(b,m) for b in range(BLOCKS) for m in MECHANISMS}
    ids=[(r["block"],r["mechanism"]) for r in rows]
    if len(ids)!=len(set(ids)) or not set(ids).issubset(expected):
        raise ValueError("duplicate or unplanned original source case")
    missing=sorted(f"{b}:{m}" for b,m in expected-set(ids))
    completed=[r for r in rows if r["status"]=="ok"]
    grouped={}
    fields=("n_native_observations","n_lost_curves",
            "full_source_basis_rmse","observed_basis_unit_balanced_rmse",
            "observed_basis_sample_weighted_rmse",
            "balanced_mid_slope_shift_vs_full",
            "sample_weighted_mid_slope_shift_vs_full")
    for mi,m in enumerate(MECHANISMS):
        found=[r for r in completed if r["mechanism"]==m]
        vals={}
        for field in fields:
            data=[r[field] for r in found]
            vals[field]={
                "mean":float(np.mean(data)) if data else None,
                "independent_block_bootstrap95":block_mc_ci(
                    data,seed=MASTER_SEED+673*mi+sum(map(ord,field))
                ),
                "completed_denominator":len(data),
                "planned_denominator":BLOCKS,
            }
        grouped[m]={
            "completed":len(found),"attempted":BLOCKS,
            "reference_oracles_and_native_integrity_passed":sum(
                r["current_common_grid_W3_refused"] and
                r["original_values_and_timestamps_preserved"] and
                r["native_async_jitter_verified"] and
                max(r["full_qr_max_delta"],
                    r["observed_unit_balanced_qr_max_delta"],
                    r["observed_sample_weighted_qr_max_delta"])<=NUMERICAL_TOL
                for r in found
            ),
            "outcomes":vals,
        }
    return {"study":STUDY,
            "source_seed":MASTER_SEED,
            "independent_generating_blocks":BLOCKS,
            "mechanisms_are_paired_within_source":True,
            "n_independent_curves_per_block":N_CURVES,
            "degree_fixed_without_tuning":DEGREE,
            "prediction_on_grid_not_observed_gaze_interpolation":True,
            "planned_cases":len(expected),"recorded_cases":len(rows),
            "completed_cases":len(completed),
            "failures":len(rows)-len(completed),
            "missing_cases":missing,"groups":grouped,
            "model_based_asynchronous_estimator_qualified":False,
            "missing_data_correction_qualified":False,
            "interval_calibration_qualified":False,
            "release_authorized":False}


def original_plot(result,path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    keys=("full_source_basis_rmse","observed_basis_unit_balanced_rmse",
          "observed_basis_sample_weighted_rmse")
    titles=("Complete jittered observations","Native observed, unit-balanced",
            "Native observed, sample-weighted")
    fig,ax=plt.subplots(figsize=(9.5,4.2))
    x=np.arange(len(MECHANISMS))
    for name,title in zip(keys,titles):
        vals=[result["groups"][m]["outcomes"][name]["mean"] for m in MECHANISMS]
        ax.plot(x,vals,marker="o",label=title)
    ax.set_xticks(x,("MCAR","MAR on condition","Latent MNAR"))
    ax.set_ylabel("Mean estimated slope RMSE relative to known truth")
    ax.set_title("W3 R6: genuinely asynchronous native observed-time basis")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path,format="svg",metadata={"Date":None})
    plt.close(fig)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    rows=[evaluate(b,m) for b in range(BLOCKS) for m in MECHANISMS]
    evidence=audit(rows)
    for name,obj in (("case-ledger.json",rows),("evidence.json",evidence)):
        (args.out/name).write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")
    original_plot(evidence,args.out/"source-async-basis.svg")
    (args.out/"source-commit.txt").write_text(os.getenv("GITHUB_SHA","unverified-local")+"\n")
    files=("case-ledger.json","evidence.json","source-async-basis.svg","source-commit.txt")
    (args.out/"SHA256SUMS").write_text("".join(
        sha256((args.out/n).read_bytes()).hexdigest()+f"  {n}\n" for n in files))
    print("W3 R6 ASYNCHRONOUS TIME BASIS AUDIT:",json.dumps(evidence,sort_keys=True))
    if evidence["failures"] or evidence["missing_cases"]:
        raise SystemExit("original asynchronous W3 source audit incomplete")
    # Do not choose a method or qualify inference based on RMSE or CI outcome.


if __name__=="__main__":
    main()
