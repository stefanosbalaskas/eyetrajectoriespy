"""R31 original-source Gaussian covariance estimation under observation loss.

Twelve new independent generating blocks. Native irregular trajectories remain
unaltered except for explicit sample deletion or trial dropout; NO resampling,
interpolation or synthetic observed values. The original complete source is
paired with outcome-independent MCAR sample loss, observed-time-dependent MAR
sample loss, and predictor-dependent MAR trial dropout. Both fitted covariance
methods use only remaining observed responses/times/labels. Generator variances
are accessed only after fitting for scientific component recovery diagnostics.

Research-only: no 90% pointwise coverage, simultaneous bands, fitted-covariance
Satterthwaite qualification, public API or release decision.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts import run_w3_r16_leverage_covariance_factorial as r16
from scripts import run_w3_r17_fresh_feasibility as fresh
from scripts.w3_r20_estimated_working_target import (
    COMPONENTS, observed_weighted_rows, estimate_feasible_working_target)
from scripts.w3_r25_gaussian_reml_components import estimate_reml_components
from scripts import run_w3_r26_independent_reml_recovery as r26

STUDY="W3_R31_NEW_SOURCE_OBSERVATION_PROCESS_COVARIANCE_RECOVERY"
MASTER_SEED=202610153131
MASK_SEED=202610153132
BOOTSTRAP_SEED=202610153133
BLOCKS=12
SIZES=(24,96)
SUPPORT=("ordinary_independent","ordinary_dependent")
OBSERVATION=("complete","mcar_20","time_mar_20","predictor_mar_trial_dropout")
METHODS=("leverage_adjusted_nnls","gaussian_reml")
BASIS="legendre5"
TRUE_COMPONENTS=r26.TRUE_COMPONENTS
BOOTSTRAP_DRAWS=2000
PLANNED=BLOCKS*len(SIZES)*len(SUPPORT)*len(OBSERVATION)


def _native_observation_transform(source,mode,*,block,support):
    if mode not in OBSERVATION:
        raise ValueError("unregistered source observation process")
    raw,gaze,x,participants,trials,means=source
    participants=np.asarray(participants)
    x=np.asarray(x,float)
    trials=np.asarray(trials)
    keep_curves=[]
    native_times=[]
    native_values=[]
    native_means=[]
    retained_pred=[]
    retained_person=[]
    retained_trial=[]
    index_maps=[]
    for participant in np.unique(participants):
        indices=np.flatnonzero(participants==participant)
        suppress_trial=None
        if mode=="predictor_mar_trial_dropout" and len(indices)>1:
            # Conditionally MAR given observed participant predictor and trial.
            local=np.random.default_rng(
                MASK_SEED+block*101003+int(participant)*101+
                SUPPORT.index(support)*1000003+701)
            prob=.35+(.25 if x[indices[0]]>0 else 0.)
            if local.uniform()<prob:
                suppress_trial=int(local.choice(indices[1:]))
        for j in indices:
            j=int(j)
            if j==suppress_trial:
                continue
            time=np.asarray(gaze.time[j],float)
            value=np.asarray(gaze.values[j],float)
            if mode in ("mcar_20","time_mar_20"):
                rng=np.random.default_rng(
                    MASK_SEED+block*101003+int(participant)*101+
                    SUPPORT.index(support)*1000003+
                    int(trials[j]%3)*17+int(mode=="time_mar_20")*1907)
                u=rng.uniform(size=len(time))
                if mode=="mcar_20":
                    propensity=np.full(len(time),.20)
                else:
                    relative=(time-time.min())/(time.max()-time.min())
                    propensity=.05+.30*relative
                keep=np.flatnonzero(u>=propensity)
                if len(keep)<8:
                    raise ValueError("predeclared native sample mask left <8 points")
            else:
                keep=np.arange(len(time))
            if not len(keep) or not np.all(np.diff(time[keep])>0):
                raise ValueError("source native-time preservation failed")
            keep_curves.append(j)
            index_maps.append(keep.tolist())
            native_times.append(time[keep].copy())
            native_values.append(value[keep].copy())
            native_means.append(np.asarray(means[j])[keep].copy())
            retained_pred.append(float(x[j]))
            retained_person.append(int(participants[j]))
            retained_trial.append(int(trials[j]))
    if len(np.unique(retained_person))!=len(np.unique(participants)):
        raise ValueError("observation process removed an independent participant")
    result=r16.IrregularTrajectorySet(
        time=tuple(native_times),
        values=tuple(native_values),
        curve_ids=tuple(gaze.curve_ids[j] for j in keep_curves),
        dimension_names=gaze.dimension_names,
        time_unit=gaze.time_unit,
        coordinate_system=gaze.coordinate_system,
        metadata=gaze.metadata.iloc[keep_curves].reset_index(drop=True).copy(),
        provenance={**gaze.provenance,
            "research_study":STUDY,"observation_regime":mode,
            "original_values_replaced":False,
            "native_points_only_deleted":True,
            "interpolation_performed":False,
            "all_recordings_complete":bool(mode=="complete")})
    retained=(None,result,np.asarray(retained_pred,float),
              np.asarray(retained_person,int),np.asarray(retained_trial,int),
              tuple(native_means))
    metadata={
        "original_native_points":int(sum(len(t) for t in gaze.time)),
        "retained_native_points":int(sum(len(t) for t in native_times)),
        "original_native_trials":len(gaze.time),
        "retained_native_trials":len(native_times),
        "missing_point_fraction":float(1-sum(len(t) for t in native_times)/
                                         sum(len(t) for t in gaze.time)),
        "dropped_trial_fraction":float(1-len(native_times)/len(gaze.time)),
        "retained_curve_indices":keep_curves,
        "retained_native_index_maps":index_maps,
        "missing_observed_outcomes_used_to_select_samples":False,
    }
    return retained,metadata


def evaluate(block,n,support,mode):
    record={"study":STUDY,"block":block,"participants":n,"support":support,
        "observation_process":mode,"source_generated":False,
        "source_failure":None,"methods":{},
        "postfit_generator_oracle_only":True,
        "no_pointwise_coverage_calculated":True,"release_authorized":False}
    try:
        original=fresh.fresh_source(
            block,support,n=n,master_seed=MASTER_SEED,
            n_blocks=BLOCKS,max_n=max(SIZES))
        observed,meta=_native_observation_transform(
            original,mode,block=block,support=support)
        X,y,w,g,t,tr,x=observed_weighted_rows(
            (None,observed[1],observed[2],observed[3],observed[4],None),BASIS)
        record["source_generated"]=True
        record["source_accounting"]={k:v for k,v in meta.items()
                                    if k not in ("retained_curve_indices",
                                                 "retained_native_index_maps")}
        record["native_source_unmodified"]=True
        record["matched_predeclared_family"]=(
            "predictor_scaled_slope" if support.endswith("_dependent")
            else "shared_slope")
    except Exception as exc:
        record["source_failure"]={"type":type(exc).__name__,
            "message":str(exc)[:600]}
        return record
    family=record["matched_predeclared_family"]
    nnls=None
    try:
        nnls=estimate_feasible_working_target(X,y,w,g,t,tr,x,slope=family)
        record["methods"]["leverage_adjusted_nnls"]={
            "status":"ok","component_estimates":nnls["variance_components"],
            "sensor_floor_applied":nnls["sensor_floor_applied"],
            "moment_operator_condition":nnls["component_condition_number"]}
    except Exception as exc:
        record["methods"]["leverage_adjusted_nnls"]={
            "status":"failed","error":{"type":type(exc).__name__,
                "message":str(exc)[:500]}}
    try:
        fit=estimate_reml_components(
            X,y,w,g,t,tr,x,slope=family,
            initializer=(nnls["variance_components"] if nnls else None))
        record["methods"]["gaussian_reml"]={
            "status":fit["status"],
            "component_estimates":fit["variance_components"],
            "optimizer_success":fit["optimizer_success"],
            "optimizer_message":fit["optimizer_message"],
            "active_lower_bound":fit["active_lower_box_components"]}
    except Exception as exc:
        record["methods"]["gaussian_reml"]={
            "status":"failed","error":{"type":type(exc).__name__,
                "message":str(exc)[:500]}}
    for method in METHODS:
        item=record["methods"][method]
        if item["status"]=="ok":
            vals=item["component_estimates"]
            item["postfit_component_absolute_relative_errors"]={
                key:float(abs(vals[key]/TRUE_COMPONENTS[key]-1))
                for key in COMPONENTS}
            item["postfit_below_5pct_positive_truth"]={
                key:bool(vals[key]<.05*TRUE_COMPONENTS[key])
                for key in COMPONENTS}
        else:
            item["postfit_component_absolute_relative_errors"]=None
            item["postfit_below_5pct_positive_truth"]=None
    return record


def block_paired_change(rows,n,support,mode,method,component):
    grouped={}
    for row in rows:
        if row["participants"]==n and row["support"]==support:
            grouped.setdefault(row["block"],{})[row["observation_process"]]=row
    values=[]
    for block in range(BLOCKS):
        trials=grouped.get(block,{})
        if mode not in trials or "complete" not in trials:
            continue
        a=trials["complete"]["methods"].get(method,{})
        b=trials[mode]["methods"].get(method,{})
        if a.get("status")=="ok" and b.get("status")=="ok":
            values.append(
                b["postfit_component_absolute_relative_errors"][component]-
                a["postfit_component_absolute_relative_errors"][component])
    if not values:
        return {"paired_independent_blocks":0,
                "mean_loss_minus_complete_error":None,
                "whole_block_bootstrap_95pct":None}
    values=np.asarray(values)
    rng=np.random.default_rng(
        BOOTSTRAP_SEED+SIZES.index(n)*1000+SUPPORT.index(support)*200+
        OBSERVATION.index(mode)*20+METHODS.index(method)*5+
        COMPONENTS.index(component))
    bs=rng.choice(values,size=(BOOTSTRAP_DRAWS,len(values)),replace=True).mean(axis=1)
    return {"paired_independent_blocks":len(values),
            "mean_loss_minus_complete_error":float(np.mean(values)),
            "whole_block_bootstrap_95pct":np.quantile(bs,[.025,.975]).tolist()}


def summarize(rows):
    expected={(b,n,s,m) for b in range(BLOCKS) for n in SIZES
              for s in SUPPORT for m in OBSERVATION}
    ids=[(r["block"],r["participants"],r["support"],r["observation_process"])
          for r in rows]
    if len(ids)!=len(set(ids)) or not set(ids).issubset(expected):
        raise ValueError("duplicate or unplanned R31 source identity")
    strata={}
    for n in SIZES:
        for support in SUPPORT:
            for mode in OBSERVATION:
                cell=[r for r in rows if r["participants"]==n
                    and r["support"]==support and r["observation_process"]==mode]
                methods={}
                for method in METHODS:
                    good=[r["methods"][method] for r in cell if
                          r["source_generated"] and
                          r["methods"].get(method,{}).get("status")=="ok"]
                    methods[method]={
                        "accepted_estimator_fits":len(good),
                        "failed_or_nonconverged":len(cell)-len(good),
                        "near_zero_slope":sum(
                            r["postfit_below_5pct_positive_truth"]["participant_slope"]
                            for r in good),
                        "near_zero_trial":sum(
                            r["postfit_below_5pct_positive_truth"]["trial"]
                            for r in good),
                        "median_slope_absolute_relative_error":(
                            float(np.median([r["postfit_component_absolute_relative_errors"][
                                "participant_slope"] for r in good])) if good else None),
                        "median_trial_absolute_relative_error":(
                            float(np.median([r["postfit_component_absolute_relative_errors"][
                                "trial"] for r in good])) if good else None),
                    }
                active=[r for r in cell if r["source_generated"]]
                strata[f"n{n}/{support}/{mode}"]={
                    "independent_original_blocks":len(cell),
                    "missing_point_fraction_mean":(
                        float(np.mean([r["source_accounting"]["missing_point_fraction"]
                             for r in active])) if active else None),
                    "dropped_trial_fraction_mean":(
                        float(np.mean([r["source_accounting"]["dropped_trial_fraction"]
                             for r in active])) if active else None),
                    "methods":methods,
                    "source_outcomes_never_imputed":True}
    contrasts={f"n{n}/{support}/{mode}/{method}":block_paired_change(
        rows,n,support,mode,method,"participant_slope")
        for n in SIZES for support in SUPPORT for mode in OBSERVATION
        if mode!="complete" for method in METHODS}
    return {"study":STUDY,"master_seed":MASTER_SEED,
        "independent_generating_blocks":BLOCKS,"sizes":SIZES,
        "source_covariance_mechanisms":SUPPORT,
        "observation_processes":OBSERVATION,
        "planned_evaluations":PLANNED,"recorded_evaluations":len(rows),
        "missing_evaluations":len(expected-set(ids)),
        "source_failures":sum(not r["source_generated"] for r in rows),
        "fit_failures":{method:sum(
            r["methods"].get(method,{}).get("status")!="ok" for r in rows)
            for method in METHODS},
        "strata":strata,
        "paired_slope_error_loss_minus_complete":contrasts,
        "whole_block_bootstrap_draws":BOOTSTRAP_DRAWS,
        "within_block_masks_not_independent_sources":True,
        "no_fitted_target_cr2_calibration":True,
        "no_nominal_pointwise_coverage":True,
        "no_simultaneous_bands_qualified":True,
        "release_authorized":False}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    cases=[evaluate(b,n,s,m) for b in range(BLOCKS) for n in SIZES
           for s in SUPPORT for m in OBSERVATION]
    report=summarize(cases)
    for path,obj in (("case-ledger.json",cases),("summary.json",report)):
        (args.out/path).write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")
    (args.out/"source-commit.txt").write_text(os.getenv("GITHUB_SHA","unverified-local")+"\n")
    names=("case-ledger.json","summary.json","source-commit.txt")
    (args.out/"SHA256SUMS").write_text("".join(
        hashlib.sha256((args.out/name).read_bytes()).hexdigest()+"  "+name+"\n"
        for name in names))
    print("R31 OBSERVATION SOURCE AUDIT:",json.dumps(
        {k:v for k,v in report.items() if k!="strata"},sort_keys=True))
    for key,v in report["strata"].items():
        print("R31 OBSERVATION CELL:",json.dumps({"cell":key,**v},sort_keys=True))
    if report["source_failures"] or report["missing_evaluations"]:
        raise SystemExit("Prespecified original observation source incomplete; retain failures")


if __name__=="__main__":
    main()
