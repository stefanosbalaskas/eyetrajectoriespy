"""W3 functional regression: independent numerical oracle and known truth.

24 independent generating seeds; two *within-seed* designs are not 48
independent simulation blocks. No interval calibration or hypothesis-test
qualification is inferred from agreement with least squares.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd

from eyetrajectoriespy import TrajectorySet
from eyetrajectoriespy.function_on_scalar import fit_function_on_scalar_regression
from eyetrajectoriespy.workflows import FunctionOnScalarWorkflowConfig, run_function_on_scalar_workflow

STUDY="W3_FUNCTION_ON_SCALAR_KNOWN_TRUTH_V1"
MASTER_SEED=202611027
BLOCKS=24
DESIGNS=("curve","participant")
TIME=np.linspace(0.0,1.0,31)
DIMS=("x","y")
ORACLE_TOLERANCE=2e-10
RECOVERY_RMSE_THRESHOLD=0.12


def truth_coefficients(time: np.ndarray = TIME) -> np.ndarray:
    t=np.asarray(time,float)
    intercept=np.column_stack((.35+.08*t, .25-.04*t))
    slope=np.column_stack((.40+.11*np.cos(np.pi*t), -.28+.13*np.sin(np.pi*t)))
    return np.stack((intercept,slope))


def generate_block(block: int, design: str, *, no_noise: bool=False) -> tuple[TrajectorySet,pd.DataFrame,np.ndarray,np.ndarray]:
    if not isinstance(block,int) or not 0<=block<BLOCKS or design not in DESIGNS:
        raise ValueError("unknown prespecified generating block or design")
    seed=MASTER_SEED+10007*block+(0 if design=="curve" else 1)
    rng=np.random.default_rng(seed)
    n=72 if design=="curve" else 36
    trials=1 if design=="curve" else 3
    x=rng.uniform(-.95,.95,size=n)
    truth=truth_coefficients()
    signal=truth[0][None,:,:]+x[:,None,None]*truth[1][None,:,:]
    participant_shift=np.zeros_like(signal)
    if design=="participant" and not no_noise:
        shifts=rng.normal(0,.065,size=(n,1,2))
        participant_shift=shifts*(1+.35*TIME[None,:,None])
    participant_y=signal+participant_shift
    noise=np.zeros((n,trials,len(TIME),2)) if no_noise else rng.normal(
        0,.04,size=(n,trials,len(TIME),2))
    observed=participant_y[:,None,:,:]+noise
    values=observed.reshape(n*trials,len(TIME),2)
    curve_ids=tuple(f"P{i:03d}-T{j:02d}" for i in range(n) for j in range(trials))
    metadata=pd.DataFrame({"participant_id":[f"P{i:03d}" for i in range(n) for _ in range(trials)],
                           "trial_id":[j for _ in range(n) for j in range(trials)]})
    gaze=TrajectorySet(time=TIME.copy(),values=values,curve_ids=curve_ids,
        dimension_names=DIMS,coordinate_system="normalized",time_unit="s",
        metadata=metadata,provenance={"study":STUDY,"block":block,"design":design,
            "simulation":True,"unit_of_independence":"curve" if trials==1 else "participant"})
    data=pd.DataFrame({"curve_id":curve_ids,"condition":np.repeat(x,trials)})
    y_unit=observed.mean(axis=1)
    X=np.column_stack((np.ones(n),x))
    return gaze,data,truth,np.linalg.lstsq(X,y_unit.reshape(n,-1),rcond=None)[0].reshape(2,len(TIME),2)


def evaluate(block: int, design: str, *, no_noise: bool=False) -> dict:
    row={"study":STUDY,"block":block,"design":design,"status":"failed",
         "exception":None,"n_source_curves":None,"n_inference_units":None,
         "n_trials_per_unit":None,"unit_is_participant_when_repeated":None,
         "max_abs_workflow_oracle_difference":None,
         "max_abs_workflow_primitive_difference":None,
         "slope_truth_rmse":None,"known_truth_recovery_target_met":None,
         "oracle_agreement_met":None,"posterior_calibration_qualified":False,
         "confidence_interval_coverage_qualified":False,"release_authorized":False}
    try:
        gaze,data,truth,oracle=generate_block(block,design,no_noise=no_noise)
        cfg=FunctionOnScalarWorkflowConfig(
            predictors=("condition",),dimensions=DIMS,
            unit=design,participant_column="participant_id" if design=="participant" else None)
        workflow=run_function_on_scalar_workflow(gaze,data,config=cfg)
        primitive=fit_function_on_scalar_regression(gaze,data,("condition",),
            dimensions=DIMS,unit=design,
            participant_column="participant_id" if design=="participant" else None)
        fit=workflow.fit
        n=36 if design=="participant" else 72
        if fit.coefficients.shape!=truth.shape or fit.design_rank!=2:
            raise ValueError("unexpected coefficient shape or design rank")
        if fit.coefficient_names!=("Intercept","condition"):
            raise ValueError("regressor order differs from independent oracle")
        if fit.unit!=design or fit.design_matrix.shape!=(n,2):
            raise ValueError("invalid independent-unit accounting")
        if not np.allclose(fit.design_matrix[:,0],1.0):
            raise ValueError("intercept not preserved")
        if workflow.decisions["unit"].value!=design or workflow.provenance[
            "automatic_model_selection_performed"] is not False:
            raise ValueError("scientific decision provenance changed")
        a=float(np.max(np.abs(fit.coefficients-oracle)))
        b=float(np.max(np.abs(fit.coefficients-primitive.coefficients)))
        rmse=float(np.sqrt(np.mean((fit.coefficients[1]-truth[1])**2)))
        oracle_pass=bool(a<=ORACLE_TOLERANCE and b<=ORACLE_TOLERANCE)
        recovery_pass=bool(rmse<=RECOVERY_RMSE_THRESHOLD)
        row.update(status="ok",n_source_curves=gaze.n_curves,n_inference_units=n,
            n_trials_per_unit=3 if design=="participant" else 1,
            unit_is_participant_when_repeated=(fit.unit=="participant" if design=="participant" else True),
            max_abs_workflow_oracle_difference=a,
            max_abs_workflow_primitive_difference=b,slope_truth_rmse=rmse,
            known_truth_recovery_target_met=recovery_pass,
            oracle_agreement_met=oracle_pass)
    except Exception as exc:
        row.update(exception={"class":type(exc).__name__,"message":str(exc)[:1000]})
    return row


def audit(rows: list[dict], blocks: int) -> dict:
    if not isinstance(blocks,int) or not 1<=blocks<=BLOCKS:
        raise ValueError("blocks outside prespecified ledger")
    ids=[(r["block"],r["design"]) for r in rows]
    if len(ids)!=len(set(ids)):
        raise ValueError("duplicate simulation case")
    expected={(b,d) for b in range(blocks) for d in DESIGNS}
    if not set(ids).issubset(expected):
        raise ValueError("undeclared simulation case")
    missing=sorted([f"{b}:{d}" for b,d in expected-set(ids)])
    completed=[r for r in rows if r["status"]=="ok"]
    by_design={}
    for d in DESIGNS:
        vals=[r for r in completed if r["design"]==d]
        by_design[d]={"completed":len(vals),
            "known_truth_slope_rmse_mean":(float(np.mean([v["slope_truth_rmse"] for v in vals])) if vals else None),
            "known_truth_slope_rmse_max":(float(np.max([v["slope_truth_rmse"] for v in vals])) if vals else None),
            "oracle_max_difference":(max(v["max_abs_workflow_oracle_difference"] for v in vals) if vals else None),
            "oracle_passes":sum(v["oracle_agreement_met"] for v in vals),
            "recovery_target_passes":sum(v["known_truth_recovery_target_met"] for v in vals)}
    return {"study":STUDY,"planned_independent_generating_blocks":blocks,
        "planned_cases":len(expected),"present_cases":len(rows),"missing_cases":missing,
        "completed_fits":len(completed),"fitting_or_contract_failures":len(rows)-len(completed),
        "simulation_cases_not_independent_blocks":True,
        "per_design":by_design,"simulation_known_truth":True,
        "posterior_calibration_qualified":False,"interval_coverage_qualified":False,
        "release_authorized":False}


def create_original_plot(rows: list[dict], path: Path) -> None:
    """Plot actual source-run coefficient recovery errors (not invented figures)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(7.5,4.0))
    for design,marker in (("curve","o"),("participant","s")):
        data=[r for r in rows if r["design"]==design and r["status"]=="ok"]
        ax.scatter([r["block"] for r in data],[r["slope_truth_rmse"] for r in data],
                   label=f"{design}: observed-grid OLS",marker=marker,s=22,alpha=.8)
    ax.axhline(RECOVERY_RMSE_THRESHOLD,color="black",linestyle="--",
               label="Prespecified exploratory RMSE target")
    ax.set_xlabel("Independent generating block (0-based)")
    ax.set_ylabel("Slope coefficient RMSE across time and dimensions")
    ax.set_title("W3 known-truth workflow recovery (simulated data)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    path.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(path,format="svg",metadata={"Date":None})
    plt.close(fig)


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--blocks",type=int,default=BLOCKS)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    if not 1<=args.blocks<=BLOCKS:
        p.error("blocks must be within the prespecified 1..24 range")
    out=args.out
    out.mkdir(parents=True,exist_ok=True)
    rows=[evaluate(block,d) for block in range(args.blocks) for d in DESIGNS]
    summary=audit(rows,args.blocks)
    for name,obj in (("case-ledger.json",rows),("evidence.json",summary)):
        (out/name).write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")
    create_original_plot(rows,out/"source-truth-recovery.svg")
    source_sha=os.environ.get("GITHUB_SHA","unverified-local")
    (out/"source-sha.txt").write_text(source_sha+"\n")
    names=("case-ledger.json","evidence.json","source-truth-recovery.svg","source-sha.txt")
    (out/"SHA256SUMS").write_text("".join(
        sha256((out/name).read_bytes()).hexdigest()+f"  {name}\n" for name in names))
    print("W3 KNOWN TRUTH ORIGINAL EVIDENCE:",json.dumps(summary,sort_keys=True))
    if summary["missing_cases"] or summary["fitting_or_contract_failures"]:
        raise SystemExit("missing or failed simulation cases: original source evidence retained")
    if any(x["oracle_passes"]!=args.blocks or x["recovery_target_passes"]!=args.blocks
           for x in summary["per_design"].values()):
        raise SystemExit("prespecified scientific recovery or oracle criterion not met")


if __name__=="__main__":
    main()
