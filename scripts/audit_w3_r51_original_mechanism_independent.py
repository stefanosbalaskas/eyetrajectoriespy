"""Read-only *independent* verifier for completed W3 R51 original evidence.

Does not import or call R51's fitting/simulation/reporting implementation.
Validates original SHA256s, source identities, full frozen denominators,
physical two-start REML acceptance, numerical refused intermediate starts,
same-seed Gaussian pairing, absolute-pivot quantile, observed-focal interval
widths and all independent block-level truth inclusion. Inputs are untrusted
original JSON evidence; audited output is a NEW derived report.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from scipy.stats import norm

BLOCKS=8
SUPPORT=("ordinary_dependent","extreme_dependent")
DRAW_TYPES=("fitted_generation","oracle_generation")
METHODS=(
    "known_covariance_oracle_conditional_CR2",
    "fitted_covariance_conditional_CR2",
    "fitted_generation_fixed_nuisance_bootstrap_t",
    "fitted_generation_refit_nuisance_bootstrap_t",
    "oracle_generation_refit_nuisance_diagnostic_t",
)
N_DRAW=63
SEED=202610165151
DRAW_SEED=202610165152
KKT_TOL=.001
NLL_TOL=.001
RECON_TOL=1e-6
ABS_TOL=1e-9
REL_TOL=1e-8


def must_close(actual,expected,name):
    if not(math.isfinite(float(actual)) and math.isfinite(float(expected))
           and math.isclose(float(actual),float(expected),
                            abs_tol=ABS_TOL,rel_tol=REL_TOL)):
        raise ValueError(f"R51 independent recomputation mismatch {name}: {actual} vs {expected}")


def sha_checks(directory):
    lines=(directory/"SHA256SUMS").read_text().splitlines()
    expected={"cases.json","summary.json","source-commit.txt"}
    if len(lines)!=3:
        raise ValueError("R51 incomplete original SHA256 manifest")
    reported={}
    for line in lines:
        digest,sep,name=line.partition("  ")
        if not sep or len(digest)!=64 or name not in expected or name in reported:
            raise ValueError("R51 malformed, duplicated or unrecognized SHA entry")
        recorded=hashlib.sha256((directory/name).read_bytes()).hexdigest()
        if recorded!=digest:
            raise ValueError(f"R51 original source SHA256 mismatch: {name}")
        reported[name]=digest
    if set(reported)!=expected:
        raise ValueError("R51 original manifest missing required source file")
    return reported


def accept_two_start_nuisance(starts,fit_status,label,selection=None):
    if len(starts)!=2 or tuple(s.get("label") for s in starts)!=("interior","spread"):
        raise ValueError(f"R51 missing frozen two-start identities: {label}")
    finite=[]
    over_kkt=[]
    for item in starts:
        state=item.get("status")
        if state not in ("ok","nonconverged","failed","not_attempted"):
            raise ValueError(f"R51 unregistered numerical stage state: {label}")
        raw=item.get("negative_loglik")
        if raw is None:
            if state=="ok":
                raise ValueError(f"R51 nominally successful optimizer missing objective: {label}")
            continue
        nll=float(raw)
        if not math.isfinite(nll):
            raise ValueError(f"R51 nonfinite original Gaussian REML objective: {label}")
        finite.append(item)
        if state=="ok":
            if item.get("optimizer_success") is not True:
                raise ValueError(f"R51 accepted optimizer missing success flag: {label}")
            recon=float(item["objective_reconstruction_error"])
            if not math.isfinite(recon) or recon>RECON_TOL+1e-10:
                raise ValueError(f"R51 reconstructed objective failed: {label}")
            ratios=item.get("ratios") or ()
            if len(ratios)!=4 or any(
                not math.isfinite(float(v)) or float(v)<=0 for v in ratios
            ):
                raise ValueError(f"R51 nonphysical Gaussian ratios: {label}")
            kkt=float(item["physical_projected_KKT"])
            if not math.isfinite(kkt) or kkt<0:
                raise ValueError(f"R51 invalid physical projected gradient: {label}")
            if kkt>KKT_TOL+1e-10:
                over_kkt.append({
                    "label":item["label"],
                    "physical_projected_KKT":kkt,
                    "negative_loglik":nll,
                })
    admissible=[]
    if finite:
        best=min(float(s["negative_loglik"]) for s in finite)
        admissible=[
            s for s in finite if s["status"]=="ok"
            and float(s["physical_projected_KKT"])<=KKT_TOL+1e-10
            and float(s["negative_loglik"])-best<=NLL_TOL+1e-10
        ]
    if fit_status in ("accepted","ok"):
        if not admissible:
            raise ValueError(f"R51 accepted fit with no KKT/NLL eligible start: {label}")
        if selection is not None:
            selected_nll=float(selection["selected_NLL"])
            selected_kkt=float(selection["physical_projected_KKT"])
            must_close(selected_nll,
                       min(float(s["negative_loglik"]) for s in admissible),
                       label+"/selected NLL")
            if not any(
                math.isclose(float(s["negative_loglik"]),selected_nll,
                             rel_tol=REL_TOL,abs_tol=ABS_TOL)
                and math.isclose(float(s["physical_projected_KKT"]),selected_kkt,
                                 rel_tol=REL_TOL,abs_tol=ABS_TOL)
                for s in admissible
            ):
                raise ValueError(f"R51 selected nuisance not eligible: {label}")
    return over_kkt


def independently_calculated_wilson(success,n):
    z=float(norm.ppf(.975))
    p=success/n
    denominator=1+z*z/n
    midpoint=(p+z*z/(2*n))/denominator
    half=z/denominator*np.sqrt(p*(1-p)/n+z*z/(4*n*n))
    return [float(midpoint-half),float(midpoint+half)]


def audit(directory):
    directory=Path(directory)
    digests=sha_checks(directory)
    original=json.loads((directory/"cases.json").read_text())
    published=json.loads((directory/"summary.json").read_text())
    checkout=(directory/"source-commit.txt").read_text().strip()
    expected={(i,s) for i in range(BLOCKS) for s in SUPPORT}
    if len(original)!=16 or {(r["block"],r["support"]) for r in original}!=expected:
        raise ValueError("R51 duplicate/missing source identity")
    if (published["master_seed"]!=SEED or published["independent_draw_seed"]!=DRAW_SEED
        or published["full_original_failure_inclusive_ledger"] is not True
        or published["recorded_source_cases"]!=16
        or published["recorded_interval_records"]!=80
        or published["recorded_Gaussian_draw_and_refit_records"]!=2016
        or published["recorded_nuisance_two_start_outcomes"]!=4064):
        raise ValueError("R51 original source, denominator or seed ledger inconsistent")
    exceptional_starts=[]
    row_summary={}
    checked_draws=0
    checked_starts=0
    for row in original:
        block,support=row["block"],row["support"]
        key=f"{block}:{support}"
        if row["source_status"]!="ok":
            raise ValueError(f"R51 source refused in completed original artifact: {key}")
        true=float(row["projected_focal_truth"])
        org=row["original_fitted_nuisance"]
        if org["status"]!="accepted":
            raise ValueError(f"R51 original Gaussian REML refused: {key}")
        for x in accept_two_start_nuisance(
            org["numerical_starts"],"accepted",key+"/original",selection=org
        ):
            exceptional_starts.append({"source":key,"stage":"original",**x})
        checked_starts+=2
        intervals=row["intervals"]
        if len(intervals)!=5 or tuple(v["method"] for v in intervals)!=METHODS:
            raise ValueError(f"R51 original interval arms missing: {key}")
        for item in intervals:
            if item["status"]!="ok":
                raise ValueError(f"R51 original interval failed: {key}/{item['method']}")
            if not math.isfinite(float(item["half_width"])) or item["half_width"]<=0:
                raise ValueError(f"R51 invalid original pointwise width: {key}")
            if bool(abs(item["point"]-true)<=item["half_width"])!=item["truth_included"]:
                raise ValueError(f"R51 incorrect truth inclusion: {key}/{item['method']}")
        all_draws=row["draws"]
        if len(all_draws)!=126:
            raise ValueError(f"R51 not all Gaussian draws preserved: {key}")
        fitted,oracle=[],[]
        for i,draw in enumerate(all_draws):
            if (draw["replicate"],draw["draw_type"])!=(
                i//2,DRAW_TYPES[i%2]):
                raise ValueError(f"R51 original paired draw order mismatch: {key}/{i}")
            expected_seed=(DRAW_SEED+100003*block+
                           711*SUPPORT.index(support)+draw["replicate"])
            if draw.get("seed")!=expected_seed:
                raise ValueError(f"R51 mismatched Gaussian pairing seed: {key}/{i}")
            if draw["status"]!="ok":
                raise ValueError(f"R51 incomplete Gaussian draw: {key}/{i}")
            if not math.isfinite(float(draw["pivot_refit"])):
                raise ValueError(f"R51 nonfinite refit pivotal value: {key}/{i}")
            for x in accept_two_start_nuisance(
                draw["numerical_starts"],"ok",f"{key}/draw/{i}"
            ):
                exceptional_starts.append({
                    "source":key,"stage":draw["draw_type"],
                    "replicate":draw["replicate"],**x
                })
            checked_starts+=2
            checked_draws+=1
            if draw["draw_type"]==DRAW_TYPES[0]:
                if not math.isfinite(float(draw["pivot_fixed"])):
                    raise ValueError(f"R51 nonfinite fixed-nuisance pivotal value: {key}")
                fitted.append(draw)
            else:
                if draw["pivot_fixed"] is not None:
                    raise ValueError(f"R51 oracle diagnostic falsely has fixed pivotal: {key}")
                oracle.append(draw)
        if len(fitted)!=N_DRAW or len(oracle)!=N_DRAW or any(
            a["seed"]!=b["seed"] for a,b in zip(fitted,oracle)
        ):
            raise ValueError(f"R51 missing common-noise fit/oracle pairing: {key}")
        qs=[
            float(np.quantile(np.abs([v["pivot_fixed"] for v in fitted]),
                              .90,method="linear")),
            float(np.quantile(np.abs([v["pivot_refit"] for v in fitted]),
                              .90,method="linear")),
            float(np.quantile(np.abs([v["pivot_refit"] for v in oracle]),
                              .90,method="linear")),
        ]
        fitted_orig=intervals[1]
        se=float(fitted_orig["half_width"])/float(fitted_orig["critical_value"])
        for j,q in enumerate(qs,2):
            must_close(intervals[j]["critical_value"],q,key+f"/q{j}")
            must_close(intervals[j]["half_width"],se*q,key+f"/width{j}")
            if bool(abs(intervals[j]["point"]-true)<=se*q)!=intervals[j]["truth_included"]:
                raise ValueError(f"R51 independent bootstrap inclusion conflict: {key}")
        row_summary[key]={
            "hits":[bool(x["truth_included"]) for x in intervals],
            "half_widths":[float(x["half_width"]) for x in intervals],
            "criticals":[float(x["critical_value"]) for x in intervals],
        }
    if checked_draws!=2016 or checked_starts!=4064:
        raise ValueError("R51 original Gaussian/REML-start denominator mismatch")
    strata={}
    for support in SUPPORT:
        batch=[row_summary[f"{b}:{support}"] for b in range(BLOCKS)]
        methods={}
        for i,name in enumerate(METHODS):
            count=sum(r["hits"][i] for r in batch)
            width=float(np.mean([r["half_widths"][i] for r in batch]))
            record=published["strata"][support]["methods"][name]
            if count!=record["included_truth"] or record["recorded"]!=BLOCKS:
                raise ValueError(f"R51 independent method denominator/inclusion mismatch: {support}/{name}")
            must_close(width,record["mean_half_width_success_only"],support+"/"+name)
            for x,y in zip(independently_calculated_wilson(count,BLOCKS),
                           record["wilson95_MC"]):
                must_close(x,y,support+"/"+name+"/Wilson95")
            methods[name]={"hits":int(count),"mean_half_width":width}
        a=[r["criticals"] for r in batch]
        ratios={
            "refit_over_fixed_fitted_generation":float(np.median(
                [v[3]/v[2] for v in a])),
            "refit_oracle_over_fitted_generation":float(np.median(
                [v[4]/v[3] for v in a])),
            "refit_fitted_generation_over_conditional_t":float(np.median(
                [v[3]/v[1] for v in a])),
        }
        summary=published["strata"][support]
        must_close(ratios["refit_over_fixed_fitted_generation"],
                   summary["median_refit_over_fixed_critical_fitted_generation"],
                   support+"/refit-fixed")
        must_close(ratios["refit_oracle_over_fitted_generation"],
                   summary["median_oracle_over_fitted_generation_refit_critical"],
                   support+"/oracle-fitted")
        disagreements=sum(r["hits"][2]!=r["hits"][3] for r in batch)
        if disagreements!=summary["paired_refit_vs_fixed_inclusion_disagreements"]:
            raise ValueError("R51 incorrect paired inclusion disagreements")
        strata[support]={
            "methods":methods,
            "paired_median_critical_ratios":ratios,
            "refit_vs_fixed_disagreements":disagreements,
        }
    return {
        "independent_source_audit_passed":True,
        "original_checkout_sha":checkout,
        "original_sha256":digests,
        "independent_primitive_blocks":BLOCKS,
        "paired_leverage_source_records":len(original),
        "verified_gaussian_draw_refits":checked_draws,
        "verified_nuisance_optimizer_starts":checked_starts,
        "numerically_accepted_original_and_draw_fits":checked_draws+len(original),
        "individual_optimizer_start_above_KKT_tolerance":exceptional_starts,
        "all_eligible_fits_passed_frozen_KKT_and_NLL":True,
        "strata":strata,
        "oracle_generator_not_empirically_implementable":True,
        "no_pointwise_90pct_coverage_qualification":True,
        "no_simultaneous_band_or_release":True,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original-artifact-dir",type=Path,required=True)
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    report=audit(args.original_artifact_dir)
    payload=json.dumps(report,indent=2,sort_keys=True)+"\n"
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(payload)
    else:
        print(payload,end="")


if __name__=="__main__":
    main()
