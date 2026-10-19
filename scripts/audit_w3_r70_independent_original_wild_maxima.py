"""R70-A independently reconstruct all original 999-draw wild maximum quantiles.

Reads immutable archived source cases and exact drawn max-statistic arrays.
No original R70 source generator, fitter, bootstrap or aggregate imported.
Does not reconstruct raw missing Gaussian innovations or bootstrap coefficients.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path

STUDY="W3_R70_NEW_FIXED_TRUTH_LEVERAGE_HC3_SIMULTANEOUS_DIAGNOSTIC"
AUDIT="W3_R70_A_INDEPENDENT_ORIGINAL_999DRAW_WILD_MAXIMUM_AUDIT"
SOURCE_SEED=202610197070
DRAW_SEED=202610197071
BLOCKS=32
DESIGNS=("curve","participant")
SUPPORT=("ordinary","extreme")
ADJUSTMENTS=("unadjusted","hc3_residual")
STUDENTIZATIONS=("hc1","hc3")
CELLS=tuple(f"{a}/{s}" for a in ADJUSTMENTS for s in STUDENTIZATIONS)
B=999
NOMINAL=.90
SOURCES=128
ORACLE_TOL=2e-10
MAX_ATTEMPTED_MULTIPLIER_VECTORS=SOURCES*B
DERIVED_REPLICATES=SOURCES*B*len(CELLS)


def _same(a,b,label,*,tol=1e-10):
    if a is None or b is None:
        if a is not None or b is not None:
            raise ValueError("R70-A missing-value mismatch "+label)
        return
    if isinstance(a,(int,float)) and not isinstance(a,bool) and isinstance(b,(int,float)) and not isinstance(b,bool):
        if not math.isclose(float(a),float(b),rel_tol=1e-9,abs_tol=tol):
            raise ValueError("R70-A independently reconstructed numerical mismatch "+label)
    elif a!=b:
        raise ValueError("R70-A independently reconstructed source mismatch "+label)


def _wilson(k,n,z=1.95996398454):
    if n==0:
        return None
    p=k/n
    den=1+z*z/n
    mean=(p+z*z/(2*n))/den
    delta=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [max(0.,min(p,mean-delta)),min(1.,max(p,mean+delta))]


def _higher_quantile(array):
    if len(array)!=B or any(type(x) not in (int,float) or not math.isfinite(x) or x<0 for x in array):
        raise ValueError("R70-A all 999 archived wild max statistics required and nonnegative")
    # Pure-Python independent reference for NumPy quantile(method='higher')
    index=math.ceil((B-1)*NOMINAL)
    return float(sorted(float(x) for x in array)[index])


def verify_archive(folder:Path,expected_checkout:str):
    filenames=("cases.json","summary.json","source-commit.txt")
    original=(folder/"SHA256SUMS").read_text().splitlines()
    expected=[sha256((folder/name).read_bytes()).hexdigest()+"  "+name
              for name in filenames]
    if original!=expected:
        raise ValueError("R70-A original 3-member SHA256 checksum evidence mismatch")
    checkout=(folder/"source-commit.txt").read_text().strip()
    if checkout!=expected_checkout or len(checkout)!=40:
        raise ValueError("R70-A exact original scientific checkout unverified")
    rows=json.loads((folder/"cases.json").read_bytes())
    report=json.loads((folder/"summary.json").read_bytes())
    identity=[(x["block"],x["design"],x["support"]) for x in rows]
    expected_ids={(b,d,s) for b in range(BLOCKS) for d in DESIGNS for s in SUPPORT}
    if len(identity)!=SOURCES or set(identity)!=expected_ids or len(set(identity))!=SOURCES:
        raise ValueError("R70-A incomplete or duplicated 32 independent primitive source block grid")
    expected_summary={
        "study":STUDY,"source_seed":SOURCE_SEED,"draw_seed":DRAW_SEED,
        "independent_primitive_generating_blocks":BLOCKS,
        "paired_dataset_cases":SOURCES,
        "independent_curve_units":72,
        "independent_participant_units":36,
        "conditional_rademacher_multiplier_vectors":MAX_ATTEMPTED_MULTIPLIER_VECTORS,
        "derived_crossed_bootstrap_coefficient_replicates":DERIVED_REPLICATES,
        "original_wild_maxima_archived":True,
        "confidence_level":NOMINAL,
        "wild_draw_count_per_case":B,
        "original_W3_OLS_HC1_numerical_oracle":True,
        "SE_adjustments":list(STUDENTIZATIONS),
        "residual_adjustments":list(ADJUSTMENTS),
        "no_calibrated_90pct_pointwise_or_simultaneous_claim":True,
        "no_response_dependent_dropout_experiment":True,
        "release_authorized":False,
    }
    for k,val in expected_summary.items():
        _same(report.get(k),val,k)
    newly_recomputed=0
    truth_reconstructed=0
    family_reconstructed=0
    source_failure=[]
    observed_raw_maxima=0
    for row in rows:
        b,design,support=row["block"],row["design"],row["support"]
        seed=DRAW_SEED+100003*b+10007*DESIGNS.index(design)+739*SUPPORT.index(support)
        n=72 if design=="curve" else 36
        if (row["study"]!=STUDY or row["source_seed"]!=SOURCE_SEED+10007*b+DESIGNS.index(design)
            or row["draw_seed"]!=seed or row["independent_units"]!=n
            or row["observed_curves"]!=(72 if design=="curve" else 108)
            or row["raw_999_draws_archived_for_independent_max_quantiles"] is not True
            or row["no_calibrated_90pct_band_claim"] is not True
            or row["release_authorized"] is not False):
            raise ValueError("R70-A original source, unit, RNG or scientific qualification changed")
        if row["completed"]:
            if row["exception"] is not None or set(row["cells"])!=set(CELLS):
                raise ValueError("R70-A fitted source without four original crossed cells")
            for field in (
                "maximum_original_HC1_coefficient_oracle_error",
                "maximum_original_HC1_SE_oracle_error",
                "maximum_original_wild_999_coefficient_oracle_error",
            ):
                val=row[field]
                if val is None or val<0 or val>ORACLE_TOL:
                    raise ValueError("R70-A original package/analytic W3 reference was not accepted")
            if not (0<row["min_hat"]<=row["max_hat"]<1):
                raise ValueError("R70-A original independent-unit hat diagonal invalid")
            if not math.isfinite(row["hc3_to_hc1_median_se_ratio"]) or row["hc3_to_hc1_median_se_ratio"]<=0:
                raise ValueError("R70-A original residual studentization ratio invalid")
            for cell_name in CELLS:
                original_cell=row["cells"][cell_name]
                adjustment,studentization=cell_name.split("/")
                if (original_cell["adjustment"]!=adjustment
                    or original_cell["studentization"]!=studentization
                    or original_cell["draw_count"]!=B
                    or original_cell["quantile_method"]!="higher"
                    or original_cell["same_fitted_source_and_wild_multiplier_vectors"] is not True):
                    raise ValueError("R70-A crossed original wild cell identity/draw reuse altered")
                slope=original_cell["slope_wild_max_draws"]
                family=original_cell["family_wild_max_draws"]
                sc=_higher_quantile(slope)
                fc=_higher_quantile(family)
                if any(f+1e-11<s for s,f in zip(slope,family)):
                    raise ValueError("R70-A family raw bootstrap max must contain slope raw max")
                _same(original_cell["slope_critical"],sc,f"{b}/{design}/{support}/{cell_name}/slope critical")
                _same(original_cell["family_critical"],fc,f"{b}/{design}/{support}/{cell_name}/family critical")
                if (original_cell["observed_slope_truth_max_pivot"] is None
                    or original_cell["observed_family_truth_max_pivot"] is None):
                    raise ValueError("R70-A original observed truth pivots missing")
                slope_in=original_cell["observed_slope_truth_max_pivot"]<=sc
                family_in=original_cell["observed_family_truth_max_pivot"]<=fc
                if (original_cell["slope_simultaneous_truth_included"] is not slope_in
                    or original_cell["joint_family_truth_included"] is not family_in):
                    raise ValueError("R70-A original source truth inclusion not reproducible from archived maxima")
                newly_recomputed+=2
                truth_reconstructed+=int(slope_in)
                family_reconstructed+=int(family_in)
                observed_raw_maxima+=2*B
        elif row["exception"] is None or row["cells"]:
            raise ValueError("R70-A original refused source silently dropped or filled with synthetic evidence")
        else:
            source_failure.append({"block":b,"design":design,"support":support,"exception":row["exception"]})
    independent_results={}
    independent_pairs={}
    for design in DESIGNS:
        independent_results[design]={}
        for support in SUPPORT:
            complete=[q for q in rows if q["design"]==design and q["support"]==support and q["completed"]]
            r=report["results"][design][support]
            for name,want in {
                "attempted":BLOCKS,"completed":len(complete),"refused":BLOCKS-len(complete),
                "maximum_hat_mean":sum(x["max_hat"] for x in complete)/len(complete) if complete else None,
                "mean_hc3_to_hc1_SE_ratio":sum(x["hc3_to_hc1_median_se_ratio"] for x in complete)/len(complete) if complete else None,
            }.items():
                _same(r.get(name),want,f"{design}/{support}/{name}")
            independent_results[design][support]={}
            for c in CELLS:
                k=sum(q["cells"][c]["slope_simultaneous_truth_included"] for q in complete)
                family=sum(q["cells"][c]["joint_family_truth_included"] for q in complete)
                mean_critical=sum(q["cells"][c]["slope_critical"] for q in complete)/len(complete) if complete else None
                expect={
                    "successful_source_inclusions":k,"family_source_inclusions":family,
                    "independent_blocks_planned":BLOCKS,"source_cases_complete":len(complete),
                    "source_cases_failed":BLOCKS-len(complete),
                    "full_denominator_lower":k/BLOCKS,
                    "full_denominator_upper":(k+BLOCKS-len(complete))/BLOCKS,
                    "wilson95_complete_only":_wilson(k,len(complete)),
                    "mean_slope_critical":mean_critical,
                }
                published=r["cells"][c]
                for field,value in expect.items():
                    if isinstance(value,list):
                        if not isinstance(published[field],list) or len(published[field])!=len(value):
                            raise ValueError("R70-A independent Wilson source interval list mismatch")
                        for a,b in zip(published[field],value):
                            _same(a,b,f"{design}/{support}/{c}/Wilson")
                    else:
                        _same(published[field],value,f"{design}/{support}/{c}/{field}")
                independent_results[design][support][c]={
                    "included":k,"complete":len(complete),"attempted":BLOCKS,
                    "family_included":family,"average_critical":mean_critical,
                }
            diffs=[
                int(x["cells"]["hc3_residual/hc3"]["slope_simultaneous_truth_included"])-
                int(x["cells"]["unadjusted/hc1"]["slope_simultaneous_truth_included"])
                for x in complete
            ]
            missing=BLOCKS-len(complete)
            pair={
                "independent_primitive_blocks_complete":len(complete),
                "source_refusals":missing,
                "HC3_only_included":sum(v==1 for v in diffs),
                "HC1_only_included":sum(v==-1 for v in diffs),
                "same_status":sum(v==0 for v in diffs),
                "complete_source_change":sum(diffs)/len(complete) if complete else None,
                "full_denominator_change_lower":(sum(diffs)-missing)/BLOCKS,
                "full_denominator_change_upper":(sum(diffs)+missing)/BLOCKS,
                "not_statistical_method_superiority":True,
            }
            pairkey=f"{design}/{support}/HC3_full_minus_HC1_original"
            original_pair=report["matched_diagnostics"][pairkey]
            for name,value in pair.items():
                _same(original_pair[name],value,pairkey+"/"+name)
            independent_pairs[pairkey]=pair
    return {
        "study":AUDIT,
        "original_scientific_checkout":checkout,
        "original_archive_SHA256_verified":3,
        "independent_primitive_source_blocks":BLOCKS,
        "original_source_cases":SOURCES,
        "original_failure_cases":source_failure,
        "original_wild_max_draw_statistics_rechecked":observed_raw_maxima,
        "independent_999draw_slope_and_family_criticals_recomputed":newly_recomputed,
        "source_truth_inclusion_recomputed":truth_reconstructed,
        "source_joint_family_inclusion_recomputed":family_reconstructed,
        "full_source_coverage":independent_results,
        "within_source_HC3_vs_HC1_paired_contrasts":independent_pairs,
        "source_raw_Gaussian_innovations_not_archived":True,
        "raw_bootstrap_coefficient_curves_not_archived":True,
        "unqualified_90pct_coverage":True,
        "release_authorized":False,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original",type=Path,required=True)
    p.add_argument("--expected-checkout",required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=verify_archive(a.original,a.expected_checkout)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "study":AUDIT,
        "original_checkout":result["original_scientific_checkout"],
        "original_wild_maxima":result["original_wild_max_draw_statistics_rechecked"],
        "source_failures":len(result["original_failure_cases"]),
        "full_source_coverage":result["full_source_coverage"],
        "source_paired_contrasts":result["within_source_HC3_vs_HC1_paired_contrasts"],
        "release_authorized":False,
    },sort_keys=True))
if __name__=="__main__":
    main()
