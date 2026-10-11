"""W3 same-dataset sensitivity: bootstrap multiplier x draw budget.

This is a *computational sensitivity* of the first 16 generating blocks from
W3 fixed-truth pilot #288; it is NOT 16 new replications. Original fixed
datasets and scientific model, residuals, truth and HC1 SEs remain unchanged.
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

from eyetrajectoriespy.function_on_scalar import (
    bootstrap_function_on_scalar_coefficients,
    function_on_scalar_simultaneous_bands,
)
from eyetrajectoriespy.workflows import (
    FunctionOnScalarWorkflowConfig, run_function_on_scalar_workflow
)
from scripts.run_w3_fixed_truth_interval_pilot import (
    STUDY as SOURCE_STUDY, MASTER_SEED as SOURCE_SEED,
    CONFIDENCE, DESIGNS, ORACLE_ATOL, simulate, independent_hc1_oracle,
)

STUDY="W3_SAME_DATA_MULTIPLIER_BUDGET_SENSITIVITY_V1"
BLOCKS=tuple(range(16))
MULTIPLIERS=("rademacher","normal")
DRAWS=(199,999)


def bootstrap_seed(block,design,multiplier):
    offset=11 if design=="curve" else 29
    return SOURCE_SEED + block*317 + offset + (
        0 if multiplier=="rademacher" else 100_000
    )


def case(block: int, design: str):
    row={"study":STUDY,"block":block,"design":design,
         "source_study":SOURCE_STUDY,
         "reuses_source_generating_dataset":True,
         "new_independent_dataset":False,
         "status":"failed","exception":None,
         "independent_unit":"participant" if design=="participant" else "curve",
         "n_independent_units":36 if design=="participant" else 72,
         "n_source_curves":108 if design=="participant" else 72,
         "oracle_coef_max_delta":None,"oracle_se_max_delta":None,
         "truth_studentized_max_slope":None,
         "cells":{}, "same_multiplier_199_prefix_matches_999":{},
         "coverage_qualified":False,"release_authorized":False}
    try:
        if type(block) is not int or block not in BLOCKS or design not in DESIGNS:
            raise ValueError("cell outside prespecified same-dataset sensitivity")
        gaze,frame,truth,X,unit_y=simulate(block,design)
        config=FunctionOnScalarWorkflowConfig(
            predictors=("condition",),dimensions=("x","y"),unit=design,
            participant_column="participant_id" if design=="participant" else None)
        fit=run_function_on_scalar_workflow(gaze,frame,config=config).fit
        beta,se=independent_hc1_oracle(X,unit_y)
        beta_delta=float(np.max(np.abs(fit.coefficients-beta)))
        se_delta=float(np.max(np.abs(fit.standard_errors-se)))
        if beta_delta>ORACLE_ATOL or se_delta>ORACLE_ATOL:
            raise ValueError("independent coefficient or HC1 reference mismatch")
        if np.any(se[1] <= 0):
            raise ValueError("zero slope standard errors in sensitivity")
        truth_sup=float(np.max(np.abs((fit.coefficients[1]-truth[1])/se[1])))
        outcomes={}
        prefix={}
        for multiplier in MULTIPLIERS:
            boot={}
            for draws in DRAWS:
                seed=bootstrap_seed(block,design,multiplier)
                b=bootstrap_function_on_scalar_coefficients(
                    fit,n_bootstrap=draws,multiplier=multiplier,
                    random_state=seed)
                band=function_on_scalar_simultaneous_bands(
                    b,confidence_level=CONFIDENCE,simultaneous_scope="coefficient")
                max_stats=np.max(np.abs(
                    (b.bootstrap_coefficients[:,1]-fit.coefficients[1][None])
                    /se[1][None]),axis=(1,2))
                crit=float(np.quantile(max_stats,CONFIDENCE,method="higher"))
                if not np.isclose(crit,band.critical_values[1],atol=ORACLE_ATOL):
                    raise ValueError("independent bootstrap maximum reference mismatch")
                key=f"{multiplier}_{draws}"
                outcomes[key]={
                    "multiplier":multiplier,"draws":draws,
                    "slope_critical":crit,
                    "slope_truth_included":bool(truth_sup<=crit),
                    "n_multipliers_independent_units":b.multipliers.shape[1],
                    "conditional_same_data_reference":True,
                }
                boot[draws]=b.multipliers
            prefix[multiplier]=bool(np.array_equal(
                boot[199],boot[999][:199]))
            if not prefix[multiplier]:
                raise ValueError("failed common-random-number bootstrap prefix")
        row.update(status="ok",oracle_coef_max_delta=beta_delta,
            oracle_se_max_delta=se_delta,
            truth_studentized_max_slope=truth_sup,
            cells=outcomes,same_multiplier_199_prefix_matches_999=prefix)
    except Exception as exc:
        row["exception"]={"type":type(exc).__name__,"message":str(exc)[:900]}
    return row


def audit(rows):
    keys=[(r["block"],r["design"]) for r in rows]
    expected={(b,d) for b in BLOCKS for d in DESIGNS}
    if len(keys)!=len(set(keys)) or not set(keys).issubset(expected):
        raise ValueError("duplicated or unplanned source design")
    missing=sorted(f"{b}:{d}" for b,d in expected-set(keys))
    completed=[r for r in rows if r["status"]=="ok"]
    by_design={}
    for design in DESIGNS:
        group=[r for r in completed if r["design"]==design]
        cases={}
        for m in MULTIPLIERS:
            for n in DRAWS:
                name=f"{m}_{n}"
                yes=sum(r["cells"][name]["slope_truth_included"] for r in group)
                cases[name]={"truth_inclusion":int(yes),
                    "completed_denominator":len(group),
                    "planned_denominator":len(BLOCKS),
                    "mean_critical":float(np.mean(
                        [r["cells"][name]["slope_critical"] for r in group])
                    ) if group else None}
        changes={}
        for m in MULTIPLIERS:
            short=f"{m}_199";long=f"{m}_999"
            flips=sum(
                r["cells"][short]["slope_truth_included"]!=
                r["cells"][long]["slope_truth_included"] for r in group)
            changes[m]={"199_to_999_inclusion_flips":int(flips),
                        "mean_999_minus_199_critical":float(np.mean([
                            r["cells"][long]["slope_critical"]-
                            r["cells"][short]["slope_critical"] for r in group
                        ])) if group else None}
        by_design[design]={"completed":len(group),
                           "multiplier_budget_cells":cases,
                           "within_multiplier_budget_sensitivity":changes}
    return {
        "study":STUDY,"source_study":SOURCE_STUDY,
        "reused_original_block_indices":list(BLOCKS),
        "same_datasets_as_first_16_blocks_in_prior_64_block_study":True,
        "fresh_independent_replication":False,
        "planned_source_datasets":len(expected),
        "planned_bootstrap_comparisons":len(expected)*len(DRAWS)*len(MULTIPLIERS),
        "completed_datasets":len(completed),
        "exception_cases":len(rows)-len(completed),
        "missing_datasets":missing,
        "per_design":by_design,
        "nominal_interval":CONFIDENCE,"bootstrap_multiplers":list(MULTIPLIERS),
        "bootstrap_draws":list(DRAWS),
        "no_method_winner_selected":True,"coverage_qualified":False,
        "release_authorized":False
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    out=args.out
    out.mkdir(parents=True,exist_ok=True)
    rows=[case(block,design) for block in BLOCKS for design in DESIGNS]
    summary=audit(rows)
    for name,content in [("case-ledger.json",rows),("evidence.json",summary)]:
        (out/name).write_text(json.dumps(content,sort_keys=True,indent=2)+"\n")
    (out/"source-commit.txt").write_text(os.environ.get("GITHUB_SHA","unverified-local")+"\n")
    files=("case-ledger.json","evidence.json","source-commit.txt")
    (out/"SHA256SUMS").write_text("".join(sha256((out/f).read_bytes()).hexdigest()+f"  {f}\n" for f in files))
    print("W3 SAME-DATA BOOTSTRAP SENSITIVITY AUDIT:",json.dumps(summary,sort_keys=True))
    if summary["missing_datasets"] or summary["exception_cases"] or summary["completed_datasets"]!=len(rows):
        raise SystemExit("failed case(s) retained in original evidence")
    # Critical/inclusion differences are the research outcome, never a pass condition.


if __name__=="__main__":
    main()
