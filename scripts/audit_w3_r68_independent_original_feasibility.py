"""R68-A independently audit immutable 8-primitive-block numerical feasibility evidence.

This auditor uses independent R66-A scalar REML/KKT verification functions,
not the R68 Gaussian source generator, optimizer, or aggregate.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

from scripts.audit_w3_r66_original_positive_slope_independent import _nested

STUDY="W3_R68_PROSPECTIVE_NEW_SOURCE_NUMERICAL_FEASIBILITY_ONLY"
MASTER_SEED=202610196868
DRAW_SEED=202610196869
BLOCKS=8
B=4
SUPPORT=("ordinary_dependent","extreme_dependent")
LEVELS=("zero","half","full")
CASES=48
DRAWS=192
MODEL_POSITIONS=480
START_SLOTS=1440
KKT=.001
NLL=.001
NEST=.00001


def _same(a,b,label):
    if a is None or b is None:
        if a is not None or b is not None:
            raise ValueError("R68-A missing-value mismatch: "+label)
        return
    if isinstance(a,(int,float)) and isinstance(b,(int,float)):
        if not math.isclose(float(a),float(b),rel_tol=1e-8,abs_tol=2e-7):
            raise ValueError("R68-A numeric mismatch: "+label)
    elif a!=b:
        raise ValueError("R68-A mismatch: "+label)


def sha_audit(folder:Path):
    names=("cases.json","summary.json","source-commit.txt")
    hashed=(folder/"SHA256SUMS").read_text().splitlines()
    expected=[hashlib.sha256((folder/n).read_bytes()).hexdigest()+"  "+n
              for n in names]
    if hashed!=expected:
        raise ValueError("R68-A immutable three-member SHA256 archive mismatch")
    checkout=(folder/"source-commit.txt").read_text().strip()
    if len(checkout)!=40 or any(ch not in "0123456789abcdef" for ch in checkout):
        raise ValueError("R68-A missing exact original Git checkout SHA")
    return checkout


def numerical_diagnostic(nested):
    """Scalar independent recorded-start diagnostics, no original R68 import."""
    h1=nested["alternative_fit"]
    starts=h1["original_starts"]
    raw=[x for x in starts if x.get("negative_loglik") is not None and
         math.isfinite(float(x["negative_loglik"]))]
    eligible=[x for x in raw if x["status"]=="ok" and x.get("optimizer_success") is True
              and x.get("objective_reconstruction_error") is not None
              and float(x["objective_reconstruction_error"])<=1e-6
              and x.get("physical_projected_KKT") is not None and
              float(x["physical_projected_KKT"])<=KKT]
    best=min((float(x["negative_loglik"]) for x in raw),default=None)
    good=min((float(x["negative_loglik"]) for x in eligible),default=None)
    gap=good-best if best is not None and good is not None else None
    best_start=next((x for x in raw if float(x["negative_loglik"])==best),None)
    if nested["null_fit"]["status"]=="accepted" and h1["status"]=="accepted":
        dev=2*(float(nested["null_fit"]["selected_NLL"])-float(h1["selected_NLL"]))
    else:
        dev=nested.get("raw_deviance")
    return {
        "H1_gap":gap,
        "H1_raw_best_KKT":None if best_start is None else best_start.get("physical_projected_KKT"),
        "raw_nested_deviance":dev,
        "H1_gap_above":gap is not None and gap>NLL,
        "negative_nested":dev is not None and dev<-NEST,
        "null_status":nested["null_fit"]["status"],
        "alternative_status":h1["status"],
        "error":nested.get("error"),
    }


def audit_original(folder:Path,*,expected_checkout=None):
    checkout=sha_audit(folder)
    if expected_checkout is not None and checkout!=expected_checkout:
        raise ValueError("R68-A wrong original scientific source checkout")
    cases=json.loads((folder/"cases.json").read_bytes())
    archived=json.loads((folder/"summary.json").read_bytes())
    identities=[(x["block"],x["support"],x["level"]) for x in cases]
    expected={(i,s,l) for i in range(BLOCKS) for s in SUPPORT for l in LEVELS}
    if len(identities)!=CASES or set(identities)!=expected or len(set(identities))!=CASES:
        raise ValueError("R68-A incorrect 8-primitive-block original complete paired grid")
    for k,v in {
        "study":STUDY,"master_seed":MASTER_SEED,"draw_seed":DRAW_SEED,
        "new_independent_primitive_Gaussian_blocks":BLOCKS,
        "matched_original_source_cases":CASES,
        "conditional_Gaussian_draw_slots":DRAWS,
        "original_nested_H0_H1_model_positions":MODEL_POSITIONS,
        "original_optimizer_start_slots":START_SLOTS,
        "frozen_H1_KKT_threshold":KKT,
        "frozen_H1_multistart_NLL_threshold":NLL,
        "frozen_nested_negative_tolerance":-NEST,
        "num_new_5pct_test_calibrations":0,
        "no_statistical_candidate_p_or_power":True,
        "no_fitted_CR2_90pct_pointwise_or_simultaneous_qualification":True,
        "no_original_R66_refusal_repair_or_interval_recovery":True,
        "release_authorized":False,
    }.items():
        _same(archived.get(k),v,k)
    stats=Counter()
    failures=[]
    h1gaps=[]
    raw_deviances=[]
    starts=0
    seeds=set()
    all_draws=0
    for case in cases:
        block,support,level=case["block"],case["support"],case["level"]
        if (case["study"]!=STUDY or case["statistical_power_qualified"] is not False
            or case["fitted_CR2_90pct_qualified"] is not False
            or case["release_authorized"] is not False
            or case["candidate_rejection"] is not None
            or case["original_test_p_value"] is not None):
            raise ValueError("R68-A source claim or release status was changed")
        var=(("zero","half","full").index(level)*.5*.045)**2
        _same(case["true_slope_variance"],var,f"{block}/{support}/{level}/variance")
        dr=case["bootstrap"]
        if [x["draw"] for x in dr]!=list(range(B)):
            raise ValueError("R68-A missing original Gaussian draw index")
        for phase,nested,draw in [("observed",case["observed"],None)]+[
            ("conditional",q["nested"],q) for q in dr]:
            reconstructed=_nested(nested,f"R68/{block}/{support}/{level}/{phase}/{None if draw is None else draw['draw']}")
            starts+=reconstructed["slots"]
            stats[f"{phase}/{nested['status']}"]+=1
            d=numerical_diagnostic(nested)
            if draw is not None:
                all_draws+=1
                if draw["status"]!=nested["status"] and draw.get("error") is None:
                    raise ValueError("R68-A archived draw/nested mismatch without error")
                if draw["seed"] is not None:
                    actual=DRAW_SEED+100003*block+739*SUPPORT.index(support)+1009*LEVELS.index(level)+draw["draw"]
                    if draw["seed"]!=actual or actual in seeds:
                        raise ValueError("R68-A conditional Gaussian seed forged/duplicated")
                    seeds.add(actual)
            if d["H1_gap"] is not None:
                h1gaps.append(d["H1_gap"])
            if d["raw_nested_deviance"] is not None:
                raw_deviances.append(d["raw_nested_deviance"])
            if nested["status"]=="refused":
                stats[f"{phase}/H0_{d['null_status']}/H1_{d['alternative_status']}"]+=1
                failures.append({
                    "block":block,"support":support,"level":level,"phase":phase,
                    "draw":None if draw is None else draw["draw"],
                    "draw_seed":None if draw is None else draw["seed"],
                    "nested":{
                        "observed_nested_status":nested["status"],
                        "null_status":d["null_status"],
                        "alternative_status":d["alternative_status"],
                        "original_error":d["error"],
                        "H1_best_observed_NLL":None,
                        "H1_best_KKT_eligible_NLL":None,
                        "H1_eligible_minus_raw_best_NLL":d["H1_gap"],
                        "H1_raw_best_KKT":d["H1_raw_best_KKT"],
                        "H1_raw_best_label":None,
                        "H1_best_KKT_exceeds_original_001":None if d["H1_raw_best_KKT"] is None else d["H1_raw_best_KKT"]>KKT,
                        "H1_eligible_gap_exceeds_original_001":None if d["H1_gap"] is None else d["H1_gap"]>NLL,
                        "raw_nested_deviance":d["raw_nested_deviance"],
                        "negative_nested_deviance_beyond_original_tolerance":None if d["raw_nested_deviance"] is None else d["raw_nested_deviance"]<-NEST,
                    },
                })
            if d["H1_gap_above"]:
                stats[f"{phase}/H1_gap_above_001"]+=1
            if d["negative_nested"]:
                stats[f"{phase}/nested_negative_beyond_1e5"]+=1
    if (all_draws!=DRAWS or starts!=START_SLOTS):
        raise ValueError("R68-A original 192-draw/1440-start denominator altered")
    _same(archived["recorded_distinct_attempted_draw_seeds"],len(seeds),"seed count")
    _same(archived["recorded_source_case_identifiers"],CASES,"case count")
    if dict(sorted(stats.items()))!=archived["original_fit_status_counts"]:
        raise ValueError("R68-A original source failure ledger status counts altered")
    _same(archived["observed_max_H1_eligible_minus_best_NLL"],
          max(h1gaps,default=None),"max H1 multistart gap")
    _same(archived["observed_min_raw_nested_deviance"],
          min(raw_deviances,default=None),"min nested deviance")
    if len(failures)!=len(archived["source_and_draw_refusal_ledger"]):
        raise ValueError("R68-A original failure ledger length altered")
    for a,b in zip(failures,archived["source_and_draw_refusal_ledger"]):
        for field in ("block","support","level","phase","draw","draw_seed"):
            if a[field]!=b[field]:
                raise ValueError("R68-A original source refusal identity tampered")
        for field in ("observed_nested_status","null_status","alternative_status",
                      "original_error","H1_eligible_minus_raw_best_NLL",
                      "H1_raw_best_KKT","H1_best_KKT_exceeds_original_001",
                      "H1_eligible_gap_exceeds_original_001",
                      "raw_nested_deviance","negative_nested_deviance_beyond_original_tolerance"):
            _same(a["nested"][field],b["nested"][field],field)
    return {
        "study":"W3_R68_A_INDEPENDENT_ORIGINAL_NEW_SOURCE_NUMERICAL_AUDIT",
        "independent_original_archive_reproduced":True,
        "sha256_entries_verified":3,
        "original_source_checkout":checkout,
        "new_independent_primitive_blocks":BLOCKS,
        "matched_source_case_positions":CASES,
        "Gaussian_draw_positions":all_draws,
        "nested_model_positions":MODEL_POSITIONS,
        "optimizer_start_positions":starts,
        "accepted_conditional_numerical_fits":stats["conditional/accepted"],
        "refused_conditional_numerical_fits":stats["conditional/refused"],
        "unattempted_conditional_numerical_fits":stats["conditional/not_attempted"],
        "independent_original_fit_status_counts":dict(sorted(stats.items())),
        "independent_original_failure_identities":[
            {k:q[k] for k in ("block","support","level","phase","draw")}
            for q in failures],
        "max_H1_KKT_eligible_vs_raw_best_NLL_gap":max(h1gaps,default=None),
        "min_original_raw_nested_deviance":min(raw_deviances,default=None),
        "original_estimator_or_source_generator_called":False,
        "R66_missing_primary_confidence_interval_not_recomputed":True,
        "no_calibrated_test_size_or_power":True,
        "release_authorized":False,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--expected-checkout",default=None)
    a=p.parse_args()
    report=audit_original(a.original,expected_checkout=a.expected_checkout)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print(json.dumps(report,sort_keys=True))
if __name__=="__main__":
    main()
