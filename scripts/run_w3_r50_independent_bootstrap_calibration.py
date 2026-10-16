"""W3 R50: prespecified larger independent Gaussian nuisance-bootstrap audit.

24 NEW independent primitive blocks, n24, true positive predictor-scaled
participant random slope, two paired ordinary/extreme leverage conditions.
63 frozen Gaussian parametric bootstrap-t draws per case, each refitting ALL
FOUR observed-data REML variance components under 2 positive-physical
initializations and a projected-KKT ≤0.001 / observed-NLL ≤0.001 gate.
Compare oracle conditional CR2, fitted conditional CR2, first 31 vs all 63
fully refitted studentized pivot quantiles, and a deliberately WRONG shared-
slope working covariance with the SAME physical solver/KKT gates.
This is an exploratory *calibration and quantile-budget stress*, NOT a valid
nuisance-estimation-aware 90% coverage claim or a global REML certificate.

Three fixed nonoverlapping eight-primitive-block GitHub Actions shards.
Each original source, covariance fit, bootstrap attempt and both optimizer
starts remain recorded even if a numerical stage refuses. Aggregate refuses
missing/duplicate shards and verifies original SHA256 case manifest.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np
from scipy.optimize import minimize
from scipy.stats import t as student_t

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts import run_w3_r17_fresh_feasibility as fresh
from scripts import run_w3_r48_independent_fitted_cr2 as r48
from scripts import run_w3_r49_nuisance_refit_bootstrap_t as r49
from scripts.w3_r25_gaussian_reml_components import prepare_reml_design
from scripts.w3_r20_estimated_working_target import COMPONENTS

STUDY="W3_R50_LARGER_INDEPENDENT_NUISANCE_REFIT_GAUSSIAN_QUANTILE_AUDIT"
SOURCE_SEED=202610165050
DRAW_SEED=202610165051
BLOCKS=24
PARTICIPANTS=24
SUPPORT=("ordinary_dependent","extreme_dependent")
FAMILIES=("predictor_scaled_slope","shared_slope")
N_BOOT=63
PREFIX_BOOT=31
SHARD_SIZE=8
KKT_TOL=1e-3
NLL_TOL=1e-3
NOMINAL=.90
METHODS=(
    "generating_covariance_oracle_conditional_CR2",
    "correct_family_fitted_conditional_CR2",
    "correct_family_refit_bootstrap_t_31_prefix",
    "correct_family_refit_bootstrap_t_63",
    "wrong_shared_slope_fitted_conditional_CR2",
)
N_CASES=BLOCKS*len(SUPPORT)
N_INTERVALS=N_CASES*len(METHODS)
N_BOOT_ATTEMPTS=N_CASES*N_BOOT
N_NUISANCE_CALLS=N_CASES*(2+N_BOOT)
N_SOLVER_STARTS=N_NUISANCE_CALLS*len(r49.START_RATIOS)


def original_source(block,support):
    if type(block) is not int or block not in range(BLOCKS) or support not in SUPPORT:
        raise ValueError("R50 source outside predeclared design")
    return fresh.fresh_source(
        block,support,n=PARTICIPANTS,master_seed=SOURCE_SEED,
        n_blocks=BLOCKS,max_n=PARTICIPANTS
    )


def native_problem(block,support):
    src=original_source(block,support)
    X,y,w,g,t,tr,x,c,truth,raw_truth=r48.native_data(src)
    oracle=r48.r32.known_gaussian_blocks(g,t,tr,x,w,FAMILIES[0])
    return {
        "X":X,"y":y,"w":w,"group":g,"time":t,"trial":tr,"x":x,
        "contrast":c,"truth":truth,"raw_truth":raw_truth,
        "oracle_covariance":oracle,
    }


def four_component_physical_fit(data,family):
    """Original R49 physical-restricted likelihood with family as argument.

    Fitted likelihood score, box, two frozen starts, strict KKT and
    within-start NLL tolerance identical to R49. The generating covariance
    family is never passed as an oracle parameter into this fitting routine.
    """
    if family not in FAMILIES:
        raise ValueError("unregistered R50 Gaussian covariance family")
    if family==FAMILIES[0]:
        return r49.fit_nuisance(data)
    starts=[]
    try:
        X,y,w,g,t,tr,x=(data[k] for k in
                       ("X","y","w","group","time","trial","x"))
        prepared=prepare_reml_design(
            X,y,w,g,t,tr,x,slope=family)
        Z=X*np.sqrt(w)[:,None]
        coeff=np.linalg.lstsq(Z,y*np.sqrt(w),rcond=None)[0]
        reference=max(float(np.mean((y-X@coeff)**2)),1e-8)
    except Exception as exc:
        return {
            "status":"refused","reason":"source_preparation",
            "error":repr(exc)[:350],
            "numerical_starts":[
                {"label":name,"status":"not_attempted"}
                for name,_ in r49.START_RATIOS],
            "working_blocks":None,
        }
    for label,initial in r49.START_RATIOS:
        row={
            "label":label,"status":"failed","optimizer_success":False,
            "negative_loglik":None,"physical_projected_KKT":None,
            "ratios":None,"error":None,
        }
        try:
            opt=minimize(
                r49._objective,x0=np.asarray(initial,float),
                args=(prepared,reference),jac=True,
                method="L-BFGS-B",
                bounds=[(r49.BOUND_LOW,r49.BOUND_HIGH)]*len(COMPONENTS),
                options={"maxiter":450,"ftol":0.,"gtol":1e-10,
                         "maxls":80,"maxfun":2400},
            )
            row["optimizer_success"]=bool(opt.success)
            row["iterations"]=int(opt.nit)
            row["message"]=str(opt.message)
            row["ratios"]=[float(v) for v in opt.x]
            if np.isfinite(opt.x).all() and np.isfinite(opt.fun):
                f,grad=r49._objective(opt.x,prepared,reference)
                kkt=float(np.max(abs(r49._physical_kkt(grad,opt.x))))
                row.update(
                    negative_loglik=float(f),
                    physical_projected_KKT=kkt,
                    objective_reconstruction_error=float(abs(f-opt.fun)),
                    status=("ok" if opt.success and
                        abs(f-opt.fun)<=r49.RECONSTRUCTION_TOL
                        else "nonconverged"),
                )
        except Exception as exc:
            row["error"]=repr(exc)[:350]
        starts.append(row)
    finite=[v for v in starts if v["negative_loglik"] is not None
            and np.isfinite(v["negative_loglik"])]
    best=min((v["negative_loglik"] for v in finite),default=None)
    accepted=([v for v in finite if v["status"]=="ok" and
              v["physical_projected_KKT"] is not None and
              v["physical_projected_KKT"]<=KKT_TOL and
              v["negative_loglik"]-best<=NLL_TOL]
              if best is not None else [])
    if not accepted:
        return {
            "status":"refused","reason":"physical_KKT_or_NLL_or_solver",
            "numerical_starts":starts,"best_observed_NLL":best,
            "working_blocks":None,
        }
    picked=min(accepted,key=lambda v:v["negative_loglik"])
    theta=reference*np.asarray(picked["ratios"],float)
    try:
        matrices=[]
        for _,_,kernels in prepared:
            V=sum(float(theta[k])*kernels[k] for k in range(len(COMPONENTS)))
            V=(V+V.T)*.5
            np.linalg.cholesky(V)
            matrices.append(V)
    except Exception as exc:
        return {
            "status":"refused","reason":"non_SPD_fitted_working_covariance",
            "error":repr(exc)[:350],
            "numerical_starts":starts,"working_blocks":None,
        }
    return {
        "status":"accepted","reason":None,
        "family":family,"numerical_starts":starts,
        "selected_start":picked["label"],
        "selected_NLL":float(picked["negative_loglik"]),
        "physical_projected_KKT":float(picked["physical_projected_KKT"]),
        "components":{k:float(theta[j]) for j,k in enumerate(COMPONENTS)},
        "working_blocks":matrices,
        "global_optimum_proven":False,
        "nuisance_estimated_from_observed_outcome":True,
    }


def draw_from_observed_fit(data,fitted_cov,block,support,rep):
    """Gaussian model-based pseudodata; oracle remains inaccessible."""
    if "oracle_covariance" not in data:
        pass
    X,y,w=data["X"],data["y"],data["w"]
    Z=X*np.sqrt(w)[:,None]
    beta=np.linalg.lstsq(Z,y*np.sqrt(w),rcond=None)[0]
    new_y=(X@beta).copy()
    unique=np.unique(data["group"])
    if len(unique)!=len(fitted_cov):
        raise ValueError("observed fitted covariance block-count mismatch")
    seed=(DRAW_SEED+100003*block
          +711*SUPPORT.index(support)+rep)
    rng=np.random.default_rng(seed)
    for who,V in zip(unique,fitted_cov):
        idx=np.flatnonzero(data["group"]==who)
        eps=np.linalg.cholesky(V)@rng.normal(size=len(idx))
        new_y[idx]+=eps/np.sqrt(w[idx])
    if not np.isfinite(new_y).all():
        raise ValueError("nonfinite Gaussian parametric pseudodata")
    return new_y,seed


def method_interval(method,point,se,critical,truth):
    if not all(np.isfinite(x) and x>0 for x in (se,critical)):
        raise ValueError("nonfinite or nonpositive CR2 interval quantities")
    half=float(se*critical)
    return {
        "method":method,"status":"ok","point":float(point),
        "critical_value":float(critical),"half_width":half,
        "truth_included":bool(abs(float(point)-truth)<=half),
        "no_90pct_qualification":True,
    }


def refused_method(method,reason):
    return {
        "method":method,"status":"refused","reason":str(reason)[:350],
        "truth_included":False,"no_90pct_qualification":True,
    }


def _conditional_interval(method,data,cov):
    fitted=r49.cr2_on(data,cov)
    critical=float(student_t.ppf(.95,fitted["satterthwaite_df"]))
    return method_interval(
        method,fitted["point"],fitted["cr2_se"],critical,data["truth"]
    )


def evaluate(block,support):
    row={
        "study":STUDY,"block":block,"support":support,
        "source_status":"failed","source_error":None,
        "independent_primitive_block":True,
        "support_is_paired_within_original_block":True,
        "participants":PARTICIPANTS,
        "intervals":[],
        "original_correct_nuisance":None,
        "original_wrong_nuisance":None,
        "bootstrap_refit_attempts":[],
        "release_authorized":False,
    }
    data=None
    try:
        data=native_problem(block,support)
        row["source_status"]="ok"
        row["projected_focal_truth"]=float(data["truth"])
        row["projection_minus_raw_truth"]=float(data["truth"]-data["raw_truth"])
        row["intervals"].append(_conditional_interval(
            METHODS[0],data,data["oracle_covariance"]))
    except Exception as exc:
        row["source_error"]=repr(exc)[:350]
        row["intervals"].append(refused_method(METHODS[0],row["source_error"]))
    correct=None
    wrong=None
    if data is not None:
        correct=four_component_physical_fit(data,FAMILIES[0])
        wrong=four_component_physical_fit(data,FAMILIES[1])
        row["original_correct_nuisance"]={
            k:v for k,v in correct.items() if k!="working_blocks"}
        row["original_wrong_nuisance"]={
            k:v for k,v in wrong.items() if k!="working_blocks"}
    else:
        for name in ("original_correct_nuisance","original_wrong_nuisance"):
            row[name]={
                "status":"not_attempted",
                "numerical_starts":[{"label":s,"status":"not_attempted"}
                                    for s,_ in r49.START_RATIOS],
            }
    fitCR2=None
    if correct is not None and correct["status"]=="accepted":
        try:
            fitCR2=r49.cr2_on(data,correct["working_blocks"])
            q=float(student_t.ppf(.95,fitCR2["satterthwaite_df"]))
            row["intervals"].append(method_interval(
                METHODS[1],fitCR2["point"],fitCR2["cr2_se"],
                q,data["truth"]))
        except Exception as exc:
            row["intervals"].append(refused_method(METHODS[1],repr(exc)))
            fitCR2=None
    else:
        row["intervals"].append(refused_method(
            METHODS[1],"correct family original nuisance refusal"))
    pivots=[]
    for rep in range(N_BOOT):
        item={
            "replicate":rep,"status":"not_attempted",
            "seed":None,"signed_studentized_pivot":None,
            "failure":None,
            "numerical_starts":[
                {"label":name,"status":"not_attempted"}
                for name,_ in r49.START_RATIOS],
        }
        if correct is not None and correct["status"]=="accepted" and fitCR2 is not None:
            try:
                pseudo,seed=draw_from_observed_fit(
                    data,correct["working_blocks"],block,support,rep)
                item["seed"]=seed
                copied={k:v for k,v in data.items() if k!="oracle_covariance"}
                copied["y"]=pseudo
                refit=four_component_physical_fit(copied,FAMILIES[0])
                item["numerical_starts"]=refit["numerical_starts"]
                if refit["status"]!="accepted":
                    raise ValueError("R50 physical KKT/NLL nuisance-refit refusal")
                reCR2=r49.cr2_on(copied,refit["working_blocks"])
                pivot=float((reCR2["point"]-fitCR2["point"])/
                            reCR2["cr2_se"])
                if not np.isfinite(pivot):
                    raise ValueError("nonfinite studentized bootstrap pivot")
                item.update(status="ok",signed_studentized_pivot=pivot)
                pivots.append(pivot)
            except Exception as exc:
                item["status"]="refused"
                item["failure"]=repr(exc)[:350]
        row["bootstrap_refit_attempts"].append(item)
    for method,n in (
        (METHODS[2],PREFIX_BOOT),
        (METHODS[3],N_BOOT),
    ):
        if len(pivots)==N_BOOT and fitCR2 is not None:
            try:
                q=float(np.quantile(
                    np.abs(np.asarray(pivots[:n])),NOMINAL,method="linear"))
                row["intervals"].append(method_interval(
                    method,fitCR2["point"],fitCR2["cr2_se"],
                    q,data["truth"]))
            except Exception as exc:
                row["intervals"].append(refused_method(method,repr(exc)))
        else:
            row["intervals"].append(refused_method(
                method,f"missing original complete refits:{len(pivots)}/{N_BOOT}"))
    if wrong is not None and wrong["status"]=="accepted":
        try:
            row["intervals"].append(
                _conditional_interval(METHODS[4],data,wrong["working_blocks"]))
        except Exception as exc:
            row["intervals"].append(refused_method(METHODS[4],repr(exc)))
    else:
        row["intervals"].append(refused_method(
            METHODS[4],"wrong covariance family original nuisance refusal"))
    return row


def summary(rows):
    keys=[(r["block"],r["support"]) for r in rows]
    expected={(i,s) for i in range(BLOCKS) for s in SUPPORT}
    if len(keys)!=len(set(keys)) or not set(keys).issubset(expected):
        raise ValueError("duplicate/unregistered R50 independent Gaussian sources")
    for r in rows:
        if (tuple(v["method"] for v in r["intervals"])!=METHODS or
                len(r["bootstrap_refit_attempts"])!=N_BOOT or
                {b["replicate"] for b in r["bootstrap_refit_attempts"]}!=
                set(range(N_BOOT)) or
                any(len(r[n]["numerical_starts"])!=len(r49.START_RATIOS)
                    for n in ("original_correct_nuisance",
                              "original_wrong_nuisance")) or
                any(len(b["numerical_starts"])!=len(r49.START_RATIOS)
                    for b in r["bootstrap_refit_attempts"])):
            raise ValueError("missing original interval, propensity, or start slots")
    intervals=[v for r in rows for v in r["intervals"]]
    boots=[b for r in rows for b in r["bootstrap_refit_attempts"]]
    starts=sum(
        len(r[name]["numerical_starts"])
        for r in rows for name in ("original_correct_nuisance",
                                   "original_wrong_nuisance")
    )+sum(len(b["numerical_starts"]) for b in boots)
    all_complete=(len(rows)==N_CASES and
                  len(intervals)==N_INTERVALS and
                  len(boots)==N_BOOT_ATTEMPTS and
                  starts==N_SOLVER_STARTS)
    strata={}
    for support in SUPPORT:
        subset=[r for r in rows if r["support"]==support]
        methods={}
        for method in METHODS:
            records=[v for r in subset for v in r["intervals"]
                     if v["method"]==method]
            ok=[v for v in records if v["status"]=="ok"]
            count=sum(v["truth_included"] for v in ok)
            methods[method]={
                "planned_independent_blocks":BLOCKS,
                "recorded":len(records),
                "accepted":len(ok),
                "failed_or_refused":len(records)-len(ok),
                "truth_inclusion_numerator":count,
                "truth_inclusion_full_planned_denominator":BLOCKS,
                "all_block_coverage_fraction":count/BLOCKS,
                "Wilson95_MC":r48.wilson(int(count),BLOCKS),
                "mean_half_width_success_only":(
                    float(np.mean([v["half_width"] for v in ok]))
                    if ok else None),
                "nominal_pointwise_90_NOT_qualified":True,
            }
        c=[r["original_correct_nuisance"] for r in subset]
        m=[r["original_wrong_nuisance"] for r in subset]
        bst=[b for r in subset for b in r["bootstrap_refit_attempts"]]
        paired=[r for r in subset if all(
            v["status"]=="ok" for v in r["intervals"][2:4])]
        median_quantile_ratio=(
            float(np.median([
                r["intervals"][3]["critical_value"]/
                r["intervals"][2]["critical_value"]
                for r in paired])) if paired else None)
        changed=sum(
            r["intervals"][2]["truth_included"]!=
            r["intervals"][3]["truth_included"] for r in paired)
        strata[support]={
            "independent_primitive_blocks_planned":BLOCKS,
            "recorded_source_cases":len(subset),
            "original_correct_nuisance_accepted":sum(
                r["status"]=="accepted" for r in c),
            "original_wrong_nuisance_accepted":sum(
                r["status"]=="accepted" for r in m),
            "bootstrap_refit_attempts":len(bst),
            "bootstrap_refit_successes":sum(b["status"]=="ok" for b in bst),
            "bootstrap_refit_refused":sum(b["status"]=="refused" for b in bst),
            "bootstrap_refit_not_attempted":sum(
                b["status"]=="not_attempted" for b in bst),
            "prefix63_shared_paired_cases":len(paired),
            "31_vs_63_critical_ratio_median":median_quantile_ratio,
            "31_vs_63_truth_inclusion_disagreements":changed,
            "methods":methods,
        }
    return {
        "study":STUDY,"source_seed":SOURCE_SEED,
        "bootstrap_draw_seed":DRAW_SEED,
        "new_independent_primitive_blocks":BLOCKS,
        "participants_per_block":PARTICIPANTS,
        "paired_leverage_not_independent_replications":True,
        "source_covariance_family":FAMILIES[0],
        "wrong_fitted_covariance_family":FAMILIES[1],
        "frozen_bootstrap_draws_per_source":N_BOOT,
        "frozen_prefix_crit_sample":PREFIX_BOOT,
        "physical_projected_KKT_limit":KKT_TOL,
        "within_observed_NLL_limit":NLL_TOL,
        "planned_source_cases":N_CASES,
        "recorded_source_cases":len(rows),
        "planned_interval_slots":N_INTERVALS,
        "recorded_interval_slots":len(intervals),
        "planned_bootstrap_attempts":N_BOOT_ATTEMPTS,
        "recorded_bootstrap_attempts":len(boots),
        "planned_nuisance_optimizer_start_slots":N_SOLVER_STARTS,
        "recorded_nuisance_optimizer_start_slots":starts,
        "complete_original_failure_inclusive_design":all_complete,
        "source_generation_failures":sum(r["source_status"]!="ok"
                                         for r in rows),
        "strata":strata,
        "bootstrap_distribution_refits_four_nuisance_components":True,
        "bootstrap_generation_uses_observed_fitted_target_not_oracle":True,
        "no_global_optimum_proof":True,
        "too_few_independent_sources_for_90pct_qualification":True,
        "not_nominal_90pct_pointwise_or_simultaneous_band_qualification":True,
        "no_MNAR_or_participant_latent_selection_identification":True,
        "no_boundary_variance_test_typeI_qualification":True,
        "release_authorized":False,
    }


def _write_json(path,object):
    path.write_text(json.dumps(object,sort_keys=True,indent=2,allow_nan=False)+"\n")


def write_shard(out,start,stop):
    if ((start,stop) not in ((0,8),(8,16),(16,24))):
        raise ValueError("outside original fixed three-shard source schedule")
    out.mkdir(parents=True,exist_ok=True)
    cases=[evaluate(b,s) for b in range(start,stop) for s in SUPPORT]
    _write_json(out/"cases.json",cases)
    manifest={
        "study":STUDY,"start":start,"stop":stop,"block_count":stop-start,
        "source_cases":len(cases),
        "source_seed":SOURCE_SEED,
        "source_commit":os.environ.get("GITHUB_SHA","unverified-local"),
        "cases_sha256":hashlib.sha256((out/"cases.json").read_bytes()).hexdigest(),
    }
    _write_json(out/"manifest.json",manifest)
    print(f"R50 shard {start}:{stop}: {len(cases)} records")
    if len(cases)!=(stop-start)*len(SUPPORT):
        raise SystemExit("R50 shard lost source rows")


def aggregate(out,parts):
    expected_segments={(0,8),(8,16),(16,24)}
    found=set()
    cases=[]
    paths=sorted(parts.glob("*/manifest.json"))
    if len(paths)!=len(expected_segments):
        raise ValueError("R50 expected exactly three original shard manifests")
    for path in paths:
        m=json.loads(path.read_text())
        seg=(m["start"],m["stop"])
        if seg not in expected_segments or seg in found:
            raise ValueError("R50 missing/duplicate/unregistered source shard")
        found.add(seg)
        if (m["study"]!=STUDY or m["source_seed"]!=SOURCE_SEED or
            m["source_cases"]!=(seg[1]-seg[0])*len(SUPPORT)):
            raise ValueError("R50 original source/shard manifest mismatch")
        if m["source_commit"]!=os.environ.get("GITHUB_SHA","unverified-local"):
            raise ValueError("R50 original source checkout inconsistent")
        blob=(path.parent/"cases.json").read_bytes()
        if hashlib.sha256(blob).hexdigest()!=m["cases_sha256"]:
            raise ValueError("R50 original shard case ledger hash mismatched")
        group=json.loads(blob)
        if (len(group)!=m["source_cases"] or
            {(r["block"],r["support"]) for r in group}!=
            {(b,s) for b in range(*seg) for s in SUPPORT}):
            raise ValueError("R50 original source IDs do not cover shard")
        cases.extend(group)
    if found!=expected_segments:
        raise ValueError("R50 incomplete frozen original source blocks")
    cases.sort(key=lambda r:(r["block"],SUPPORT.index(r["support"])))
    record=summary(cases)
    out.mkdir(parents=True,exist_ok=True)
    _write_json(out/"cases.json",cases)
    _write_json(out/"summary.json",record)
    (out/"source-commit.txt").write_text(
        os.environ.get("GITHUB_SHA","unverified-local")+"\n")
    files=("cases.json","summary.json","source-commit.txt")
    (out/"SHA256SUMS").write_text("".join(
        hashlib.sha256((out/f).read_bytes()).hexdigest()+"  "+f+"\n"
        for f in files))
    print("R50 NEW SOURCE ORIGINAL AGGREGATE:",json.dumps(
        record,sort_keys=True))
    if not record["complete_original_failure_inclusive_design"]:
        raise SystemExit("R50 source/interval/bootstrap/solver records missing")


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--start",type=int)
    group.add_argument("--merge-parts",type=Path)
    parser.add_argument("--stop",type=int)
    arg=parser.parse_args()
    if arg.merge_parts is not None:
        aggregate(arg.out,arg.merge_parts)
    elif arg.stop is not None:
        write_shard(arg.out,arg.start,arg.stop)
    else:
        raise SystemExit("R50 shard requires --stop")


if __name__=="__main__":
    main()
